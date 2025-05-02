import os
import sys
import json
import time
import hashlib
import asyncio
import aiomysql
import aiohttp
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TimeRemainingColumn
from typing import List, Dict, Optional, Any

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
    "proxy_auth": None,
    "db_config": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "db": "image_downloader",
        "charset": "utf8mb4"
    },
    "min_size": (800, 600),
    "valid_content_types": ["image/jpeg", "image/png", "image/gif"],
    "headers": {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.google.com/"
    },
    "content_filter": {
        "min_size": [1920, 1080],
        "max_size": [4096, 4096],
        "content_types": [
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/svg+xml"
        ]
    },
    "smart_retry": True,
    "auto_resume": True,
    "image_compression": {
        "format": "webp",
        "quality": 85,
        "lossless": False
    }
}

class ImageDownloader:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config = self.load_config(config_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.init_db()
        self.proxy_pool = self.load_proxy_pool()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.config["headers"],
            timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    def load_config(self, path: str) -> dict:
        """加载配置文件"""
        if not os.path.exists(path):
            self.save_config(DEFAULT_CONFIG, path)
            console.print(f"[yellow]Config file created: {path}[/yellow]")
            return DEFAULT_CONFIG
        
        with open(path, "r") as f:
            user_config = json.load(f)
        
        # 递归合并配置
        def merge(a, b):
            for k, v in b.items():
                if isinstance(v, dict) and k in a:
                    a[k] = merge(a[k], v)
                else:
                    a[k] = v
            return a
        
        config = merge(DEFAULT_CONFIG, user_config)
        self.validate_config(config)
        return config
    
    def validate_config(self, config: dict):
        """验证配置完整性"""
        required_keys = ["db_config", "threads", "max_retries"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration: {key}")
        
        if config["threads"] < 1:
            raise ValueError("Threads must be at least 1")
        
        if config["max_retries"] < 0:
            raise ValueError("Max retries cannot be negative")
    
    def save_config(self, config: dict, path: str):
        """保存配置文件"""
        with open(path, "w") as f:
            json.dump(config, f, indent=4, sort_keys=True)
    
    async def load_proxy_pool(self):
        """异步加载代理池"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config["proxy_pool"],
                    proxy=self.config.get("proxy_auth"),
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.text().splitlines()
        except Exception as e:
            console.print(f"[red]Proxy pool loading failed: {str(e)}[/red]")
        return []
    
    async def get_proxy(self):
        """获取可用代理"""
        while self.proxy_pool:
            proxy = self.proxy_pool.pop(0)
            try:
                async with self.session.get(
                    "https://www.google.com",
                    proxy=proxy,
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return proxy
            except Exception as e:
                console.print(f"[yellow]Proxy invalid: {str(e)}[/yellow]")
        return None
    
    async def check_image_exists(self, url: str) -> bool:
        """检查图片是否已存在"""
        async with self.session.get(url, allow_redirects=False) as response:
            if response.status == 200:
                cursor = self.conn.cursor()
                await cursor.execute(
                    "SELECT COUNT(*) FROM images WHERE url = %s",
                    (url,)
                )
                count = await cursor.fetchone()
                return count[0] > 0
            return False
    
    async def save_image_record(self, url: str, path: str, status: str):
        """保存图片记录"""
        cursor = self.conn.cursor()
        await cursor.execute("""
            INSERT INTO images (url, path, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (url, path, status))
        await self.conn.commit()
    
    async def download_image(self, url: str, folder: str, sem: asyncio.Semaphore):
        """异步下载图片"""
        async with sem:
            try:
                if await self.check_image_exists(url):
                    console.print(f"[yellow]Skipped existing image: {url}[/yellow]")
                    return
                
                headers = self.config["headers"].copy()
                headers["User-Agent"] = self.config["user_agent"]
                
                # 智能重试逻辑
                retry_count = 0
                while retry_count <= self.config["max_retries"]:
                    try:
                        async with self.session.get(
                            url,
                            headers=headers,
                            proxy=await self.get_proxy(),
                            timeout=self.config["timeout"]
                        ) as response:
                            
                            # 自动恢复检查
                            if self.config["auto_resume"] and response.status == 206:
                                total = int(response.headers.get("Content-Length", 0))
                                resume_byte = self.get_resume_byte(url)
                                if resume_byte > 0:
                                    headers["Range"] = f"bytes={resume_byte}-"
                                    continue
                            
                            response.raise_for_status()
                            
                            # 内容验证
                            content_type = response.headers.get("Content-Type", "")
                            if content_type not in self.config["valid_content_types"]:
                                raise ValueError(f"Invalid content type: {content_type}")
                            
                            # 文件大小验证
                            content_length = int(response.headers.get("Content-Length", 0))
                            min_size = self.config["content_filter"]["min_size"][0] * 1024 + \
                                       self.config["content_filter"]["min_size"][1] * 1024
                            if content_length < min_size:
                                raise ValueError(f"Image too small: {content_length/1024:.1f}KB < {min_size/1024:.1f}KB")
                            
                            # 文件保存
                            filename = f"{hashlib.md5(url.encode()).hexdigest()[:8]}_{os.path.basename(urlparse(url).path)}"
                            filepath = os.path.join(folder, filename)
                            
                            # 断点续传
                            if self.config["auto_resume"]:
                                resume_byte = self.get_resume_byte(url)
                                if resume_byte > 0:
                                    headers["Range"] = f"bytes={resume_byte}-"
                                    mode = "ab"
                                else:
                                    mode = "wb"
                            else:
                                mode = "wb"
                            
                            async with aiofiles.open(filepath, mode) as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            
                            # 图片处理
                            if content_type.startswith("image/"):
                                await self.process_image(filepath)
                            
                            # 保存记录
                            await self.save_image_record(url, filepath, "completed")
                            console.print(f"[green]Downloaded: {url}[/green]")
                            return
                    
                    except (aiohttp.ClientError, ValueError) as e:
                        retry_count += 1
                        if self.config["smart_retry"] and retry_count > self.config["max_retries"]:
                            raise
                        await asyncio.sleep(2 ** retry_count)
                        console.print(f"[yellow]Retry {retry_count}/{self.config['max_retries']}: {str(e)}[/yellow]")
                
                await self.save_image_record(url, "", "failed")
                console.print(f"[red]Failed after retries: {url}[/red]")
            
            except Exception as e:
                console.print(f"[red]Unexpected error: {str(e)}[/red]")
    
    def get_resume_byte(self, url: str) -> int:
        """获取已下载字节数"""
        # 实现断点续传逻辑（需结合数据库或文件记录）
        return 0  # 示例占位
    
    async def process_image(self, filepath: str):
        """异步图片处理"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            self.executor,
            self._sync_process_image,
            filepath
        )
    
    def _sync_process_image(self, filepath: str):
        """同步图片处理"""
        try:
            with Image.open(filepath) as img:
                img = img.convert("RGB")
                img.save(
                    filepath,
                    format=self.config["image_compression"]["format"],
                    quality=self.config["image_compression"]["quality"],
                    lossless=self.config["image_compression"]["lossless"]
                )
        except Exception as e:
            console.print(f"[yellow]Compression failed: {str(e)}[/yellow]")
    
    async def crawl_images(self, url: str, folder: str):
        """网页图片抓取"""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
            
            soup = BeautifulSoup(html, "html.parser")
            
            # 提取直接图片
            img_tags = soup.find_all("img")
            direct_urls = [
                urljoin(url, img.get("src") or img.get("data-src"))
                for img in img_tags
                if img.get("src") or img.get("data-src")
            ]
            
            # 提取链接页面
            link_tags = soup.find_all("a", href=True)
            link_urls = [urljoin(url, link["href"]) for link in link_tags if link["href"]]
            
            # 去重和过滤
            seen = set()
            all_urls = []
            for url in direct_urls + link_urls:
                parsed = urlparse(url)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if normalized not in seen and self.is_valid_url(url):
                    seen.add(normalized)
                    all_urls.append(normalized)
            
            # 创建保存目录
            os.makedirs(folder, exist_ok=True)
            
            # 并发下载
            sem = asyncio.Semaphore(self.config["threads"])
            tasks = [self.download_image(url, folder, sem) for url in all_urls]
            await asyncio.gather(*tasks)
        
        except Exception as e:
            console.print(f"[red]Crawling failed: {str(e)}[/red]")
    
    def is_valid_url(self, url: str) -> bool:
        """URL有效性检查"""
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    
    async def run(self, start_url: str, output_folder: str):
        """运行程序"""
        try:
            self.conn = await aiomysql.connect(**self.config["db_config"])
            await self.crawl_images(start_url, output_folder)
        except Exception as e:
            console.print(f"[red]Fatal error: {str(e)}[/red]")
        finally:
            await self.session.close()
            self.conn.close()
            console.print("\n[bold]Download completed![/bold]")

async def main():
    console.rule("[bold red]Advanced Image Downloader[/bold red]")
    
    # 交互式配置
    console.print("[bold]1. Load Configuration[/bold]")
    config_path = input("Enter config path (leave blank for default): ").strip() or CONFIG_FILE
    downloader = ImageDownloader(config_path)
    
    console.print("\n[bold]2. Input Download Parameters[/bold]")
    start_url = input("Enter start URL: ").strip()
    output_folder = input("Enter output folder: ").strip()
    
    console.print("\n[bold]3. Start Downloading[/bold]")
    await downloader.run(start_url, output_folder)

if __name__ == "__main__":
    asyncio.run(main())
