import os
import sys
import json
import time
import hashlib
import requests
import asyncio
import aiomysql
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TimeRemainingColumn
from typing import List, Dict, Optional

console = Console()

# 配置文件路径
CONFIG_FILE = "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "threads": 10,
    "max_retries": 3,
    "timeout": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "proxy_pool": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "db_config": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "db": "image_downloader"
    },
    "min_size": (800, 600),
    "valid_content_types": ["image/jpeg", "image/png", "image/gif"]
}

class ImageDownloader:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.init_db()
        self.proxy_pool = self.load_proxy_pool()
    
    def load_config(self, path: str) -> dict:
        """加载配置文件"""
        if not os.path.exists(path):
            self.save_config(DEFAULT_CONFIG, path)
            console.print(f"[yellow]Config file created: {path}[/yellow]")
            return DEFAULT_CONFIG
        
        with open(path, "r") as f:
            config = json.load(f)
            # 合并默认配置
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    
    def save_config(self, config: dict, path: str):
        """保存配置文件"""
        with open(path, "w") as f:
            json.dump(config, f, indent=4)
    
    def init_db(self):
        """初始化数据库"""
        self.conn = aiomysql.connect(**self.config["db_config"])
        self.cursor = self.conn.cursor()
        await self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url VARCHAR(255) UNIQUE,
                path VARCHAR(255),
                status ENUM('pending', 'downloading', 'completed', 'failed'),
                retry_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.commit()
    
    async def load_proxy_pool(self):
        """加载代理池"""
        try:
            response = requests.get(self.config["proxy_pool"], timeout=10)
            return response.text.splitlines()
        except:
            console.print("[red]Proxy pool loading failed![/red]")
            return []
    
    async def get_proxy(self):
        """获取可用代理"""
        while self.proxy_pool:
            proxy = self.proxy_pool.pop(0)
            try:
                # 测试代理有效性
                test_url = "https://www.google.com"
                response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=5)
                if response.status_code == 200:
                    return proxy
            except:
                pass
        return None
    
    async def check_image_exists(self, url: str) -> bool:
        """检查图片是否已存在"""
        await self.cursor.execute("SELECT COUNT(*) FROM images WHERE url = %s", (url,))
        count = await self.cursor.fetchone()
        return count[0] > 0
    
    async def save_image_record(self, url: str, path: str, status: str):
        """保存图片记录"""
        await self.cursor.execute("""
            INSERT INTO images (url, path, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (url, path, status))
        await self.conn.commit()
    
    async def download_image(self, url: str, folder: str, sem: asyncio.Semaphore):
        """异步下载图片"""
        async with sem:
            try:
                # 检查是否存在
                exists = await self.check_image_exists(url)
                if exists:
                    console.print(f"[yellow]Skipped existing image: {url}[/yellow]")
                    return
                
                # 获取代理
                proxy = await self.get_proxy()
                headers = {"User-Agent": self.config["user_agent"]}
                
                # 发送HEAD请求检查
                head_response = requests.head(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=self.config["timeout"])
                if head_response.status_code != 200:
                    raise Exception(f"Head request failed: {head_response.status_code}")
                
                # 检查内容类型
                content_type = head_response.headers.get("Content-Type", "")
                if content_type not in self.config["valid_content_types"]:
                    raise Exception(f"Invalid content type: {content_type}")
                
                # 检查文件大小
                content_length = int(head_response.headers.get("Content-Length", 0))
                min_size = self.config["min_size"][0] * 1024 + self.config["min_size"][1] * 1024  # 转换为KB
                if content_length < min_size:
                    raise Exception(f"Image too small: {content_length/1024:.1f}KB < {min_size/1024:.1f}KB")
                
                # 开始下载
                async with self.session.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=self.config["timeout"]) as response:
                    response.raise_for_status()
                    
                    # 计算哈希
                    hash_md5 = hashlib.md5()
                    async for chunk in response.content.iter_chunked(8192):
                        hash_md5.update(chunk)
                    file_hash = hash_md5.hexdigest()
                    
                    # 文件保存
                    filename = f"{file_hash[:8]}_{os.path.basename(urlparse(url).path)}"
                    filepath = os.path.join(folder, filename)
                    
                    with open(filepath, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    # 压缩图片
                    self.compress_image(filepath)
                    
                    # 保存记录
                    await self.save_image_record(url, filepath, "completed")
                    console.print(f"[green]Downloaded: {url}[/green]")
            
            except Exception as e:
                retry_count = await self.handle_failure(url, str(e))
                if retry_count < self.config["max_retries"]:
                    console.print(f"[yellow]Retrying ({retry_count}/{self.config['max_retries']}): {url}[/yellow]")
                    await self.download_image(url, folder, sem)
                else:
                    await self.save_image_record(url, "", "failed")
                    console.print(f"[red]Failed after retries: {url}[/red]")
    
    async def handle_failure(self, url: str, error_msg: str) -> int:
        """处理下载失败"""
        await self.cursor.execute("UPDATE images SET retry_count = retry_count + 1 WHERE url = %s", (url,))
        await self.conn.commit()
        return await self.get_retry_count(url)
    
    async def get_retry_count(self, url: str) -> int:
        """获取重试次数"""
        await self.cursor.execute("SELECT retry_count FROM images WHERE url = %s", (url,))
        result = await self.cursor.fetchone()
        return result[0] if result else 0
    
    def compress_image(self, filepath: str):
        """图片压缩"""
        try:
            with Image.open(filepath) as img:
                img = img.convert("RGB")
                img.save(filepath, optimize=True, quality=85)
        except Exception as e:
            console.print(f"[yellow]Compression failed: {str(e)}[/yellow]")
    
    async def crawl_images(self, url: str, folder: str):
        """网页图片抓取"""
        try:
            response = requests.get(url, headers={"User-Agent": self.config["user_agent"]}, timeout=self.config["timeout"])
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 提取直接图片
            img_tags = soup.find_all("img")
            direct_urls = [urljoin(url, img.get("src") or img.get("data-src")) for img in img_tags if img.get("src") or img.get("data-src")]
            
            # 提取链接页面
            link_tags = soup.find_all("a", href=True)
            link_urls = [urljoin(url, link["href"]) for link in link_tags if link["href"]]
            
            # 去重
            seen = set()
            all_urls = []
            for url in direct_urls + link_urls:
                parsed = urlparse(url)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if normalized not in seen:
                    seen.add(normalized)
                    all_urls.append(normalized)
            
            # 过滤无效URL
            valid_urls = []
            for url in all_urls:
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code == 200 and response.headers.get("Content-Type") in self.config["valid_content_types"]:
                        valid_urls.append(url)
                except:
                    pass
            
            # 创建保存目录
            os.makedirs(folder, exist_ok=True)
            
            # 并发下载
            sem = asyncio.Semaphore(self.config["threads"])
            tasks = [self.download_image(url, folder, sem) for url in valid_urls]
            await asyncio.gather(*tasks)
        
        except Exception as e:
            console.print(f"[red]Crawling failed: {str(e)}[/red]")
    
    def run(self, start_url: str, output_folder: str):
        """运行程序"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.crawl_images(start_url, output_folder))
        loop.close()
        self.conn.close()

def main():
    console.rule("[bold red]Advanced Image Downloader[/bold red]")
    
    # 交互式配置
    console.print("[bold]1. Load Configuration[/bold]")
    config_path = input("Enter config path (leave blank for default): ").strip() or CONFIG_FILE
    downloader = ImageDownloader(config_path)
    
    console.print("\n[bold]2. Input Download Parameters[/bold]")
    start_url = input("Enter start URL: ").strip()
    output_folder = input("Enter output folder: ").strip()
    
    console.print("\n[bold]3. Start Downloading[/bold]")
    downloader.run(start_url, output_folder)
    console.print("\n[bold]Download completed![/bold]")

if __name__ == "__main__":
    main()
