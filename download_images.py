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
from typing import List, Dict, Optional, Any, Tuple
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime

console = Console()

# 配置文件路径
CONFIG_FILE = "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "threads": 30,
    "max_retries": 5,
    "timeout": 20,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    
    "proxy_pool": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https",
    "proxy_auth": None,
    "proxy_country": "US",
    
    "db_config": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_password",
        "db": "image_downloader",
        "charset": "utf8mb4"
    },
    
    "content_filter": {
        "min_size": [1200, 800],
        "max_size": [3840, 2160],
        "content_types": [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]
    },
    
    "logging": {
        "level": "INFO",
        "file": "logs/image_downloader.log",
        "backup_count": 7,
        "max_bytes": 10485760  # 10MB
    }
}

class ContentTypeNotAllowed(Exception):
    """自定义异常：不允许的内容类型"""
    pass

class ImageDownloader:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config = self.load_config(config_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)
        self.db_pool: Optional[aiomysql.Pool] = None
        self.proxy_pool = self.load_proxy_pool()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.config["headers"],
            timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
        )
        self.db_pool = await aiomysql.create_pool(**self.config["db_config"])
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.db_pool.close()
        await self.db_pool.wait_closed()
        self.executor.shutdown(wait=True)
        console.print("\n[bold]Resources released successfully[/bold]")
    
    async def save_image_record(self, url: str, path: str, status: str):
        """异步保存图片记录（使用连接池）"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO images (url, path, status)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status)
                """, (url, path, status))
                await conn.commit()
    
    async def download_image(self, url: str, folder: str, sem: asyncio.Semaphore):
        """优化重试逻辑和错误处理"""
        async with sem:
            retry_delay = 1
            for attempt in range(1, self.config["max_retries"] + 1):
                try:
                    async with self.session.get(
                        url,
                        headers=self.config["headers"],
                        proxy=await self.get_proxy(),
                        timeout=self.config["timeout"]
                    ) as response:
                        
                        if response.status == 206 and self.config["auto_resume"]:
                            total = int(response.headers.get("Content-Length", 0))
                            resume_byte = self.get_resume_byte(url)
                            if resume_byte > 0:
                                headers = self.config["headers"].copy()
                                headers["Range"] = f"bytes={resume_byte}-"
                                continue
                        
                        response.raise_for_status()
                        
                        content_type = response.headers.get("Content-Type", "")
                        if content_type not in self.config["valid_content_types"]:
                            raise ContentTypeNotAllowed(content_type)
                        
                        content_length = int(response.headers.get("Content-Length", 0))
                        if content_length < self.config["content_filter"]["min_size"][0] * 1024:
                            raise ValueError(f"Image too small ({content_length/1024:.1f}KB)")
                        
                        filename = f"{hashlib.md5(url.encode()).hexdigest()[:8]}_{os.path.basename(urlparse(url).path)}"
                        filepath = os.path.join(folder, filename)
                        
                        mode = "ab" if self.config["auto_resume"] and resume_byte > 0 else "wb"
                        async with aiofiles.open(filepath, mode) as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        if content_type.startswith("image/"):
                            await self.process_image(filepath)
                        
                        await self.save_image_record(url, filepath, "completed")
                        console.print(f"[green]Downloaded: {url}[/green]")
                        return
                    
                except ContentTypeNotAllowed as e:
                    console.print(f"[red]{e}[/red]")
                    await self.save_image_record(url, "", "blocked")
                    break
                except aiohttp.ClientError as e:
                    if attempt == self.config["max_retries"]:
                        console.print(f"[red]Max retries exceeded: {str(e)}[/red]")
                        await self.save_image_record(url, "", "failed")
                    else:
                        console.print(f"[yellow]Retry {attempt}/{self.config['max_retries']}: {str(e)}[/yellow]")
                        await asyncio.sleep(retry_delay * 2 ** (attempt - 1))
                        retry_delay = min(retry_delay * 2, 30)
                except ValueError as e:
                    console.print(f"[red]{str(e)}[/red]")
                    await self.save_image_record(url, "", "invalid")
                    break
                except Exception as e:
                    console.print(f"[red]Unexpected error: {str(e)}[/red]")
                    await self.save_image_record(url, "", "error")
                    break
    
    def get_resume_byte(self, url: str) -> int:
        """获取已下载字节数（示例占位，需根据实际情况实现）"""
        return 0
    
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
            
            img_tags = soup.find_all("img")
            direct_urls = [
                urljoin(url, img.get("src") or img.get("data-src"))
                for img in img_tags
                if img.get("src") or img.get("data-src")
            ]
            
            link_tags = soup.find_all("a", href=True)
            link_urls = [urljoin(url, link["href"]) for link in link_tags if link["href"]]
            
            seen = set()
            all_urls = []
            for url in direct_urls + link_urls:
                parsed = urlparse(url)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if normalized not in seen and self.is_valid_url(url):
                    seen.add(normalized)
                    all_urls.append(normalized)
            
            os.makedirs(folder, exist_ok=True)
            
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
            self.setup_logging()
            await self.crawl_images(start_url, output_folder)
        except Exception as e:
            console.print(f"[red]Fatal error: {str(e)}[/red]")
        finally:
            await self.session.close()
            self.conn.close()
            console.print("\n[bold]Download completed![/bold]")
    
    def setup_logging(self):
        """配置日志系统"""
        log_config = self.config["logging"]
        log_level = getattr(logging, log_config["level"].upper())
        
        log_dir = os.path.dirname(log_config["file"])
        os.makedirs(log_dir, exist_ok=True)
        
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        file_handler = TimedRotatingFileHandler(
            filename=log_config["file"],
            when='D',
            interval=1,
            backupCount=log_config["backup_count"],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Loaded config from {CONFIG_FILE}")

    def load_config(self, path: str) -> dict:
        """加载配置文件"""
        if not os.path.exists(path):
            self.save_config(DEFAULT_CONFIG, path)
            console.print(f"[yellow]Config file created: {path}[/yellow]")
            return DEFAULT_CONFIG
        
        with open(path, "r") as f:
            user_config = json.load(f)
        
        # 验证配置完整性
        self.validate_config(user_config)
        return user_config
    
    def validate_config(self, config: dict):
        """增强配置验证"""
        schema = {
            "threads": {"type": int, "min": 1},
            "max_retries": {"type": int, "min": 0},
            "timeout": {"type": int, "min": 1},
            "proxy_pool": {"type": str},
            "proxy_auth": {"type": str, "nullable": True},
            "proxy_country": {"type": str, "nullable": True},
            "db_config": {
                "type": dict,
                "schema": {
                    "host": {"type": str},
                    "port": {"type": int},
                    "user": {"type": str},
                    "password": {"type": str},
                    "db": {"type": str},
                    "charset": {"type": str}
                }
            },
            "content_filter": {
                "type": dict,
                "schema": {
                    "min_size": {"type": list, "len": 2, "schema": {"type": int, "min": 0}},
                    "max_size": {"type": list, "len": 2, "schema": {"type": int, "min": 0}},
                    "content_types": {"type": list, "schema": {"type": str}}
                }
            },
            "logging": {
                "type": dict,
                "schema": {
                    "level": {"type": str, "allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                    "file": {"type": str},
                    "backup_count": {"type": int, "min": 1},
                    "max_bytes": {"type": int, "min": 1024}
                }
            }
        }
        validator = Schema(schema)
        validator.validate(config)
    
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

if __name__ == "__main__":
    asyncio.run(main())

# 需要安装的依赖包：
# pip install aiohttp aiomysql beautifulsoup4 Pillow rich sqlalchemy
