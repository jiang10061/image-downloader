import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
import json
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
import sqlite3
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化数据库
def init_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            filepath TEXT,
            downloaded BOOLEAN DEFAULT 0,
            hash TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 检查图片是否已下载
def is_downloaded(db_path, url):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT downloaded FROM images WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

# 记录图片下载状态
def record_download(db_path, url, filepath, downloaded=True, hash=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO images (url, filepath, downloaded, hash)
        VALUES (?, ?, ?, ?)
    ''', (url, filepath, downloaded, hash))
    conn.commit()
    conn.close()

def calculate_hash(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return hashlib.md5(image_data).hexdigest()

def download_image(url, folder, index, session, proxies=None, headers=None, db_path=None):
    try:
        if db_path and is_downloaded(db_path, url):
            logging.info(f"Skipping already downloaded image: {url}")
            return True

        response = session.get(url, proxies=proxies, headers=headers, timeout=10)
        response.raise_for_status()

        # 获取文件扩展名
        ext = url.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            ext = 'jpg'  # 默认保存为jpg格式

        # 保存图片
        filename = f'image_{index}.{ext}'
        filepath = os.path.join(folder, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # 压缩图片
        compress_image(filepath)

        # 计算图片哈希值
        image_hash = calculate_hash(filepath)

        logging.info(f"Downloaded {url} to {filepath}")
        
        if db_path:
            record_download(db_path, url, filepath, hash=image_hash)
        return True
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return False

def compress_image(filepath):
    try:
        with Image.open(filepath) as img:
            img = img.convert('RGB')
            img.save(filepath, optimize=True, quality=85)
        logging.info(f"Compressed {filepath}")
    except Exception as e:
        logging.error(f"Failed to compress {filepath}: {e}")

def urljoin(base, url):
    return urljoin(base, url)

def get_all_image_urls(url, session, proxies=None, headers=None):
    try:
        response = session.get(url, proxies=proxies, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')
        image_urls = [img.get('src') or img.get('data-src') for img in images]
        image_urls = [urljoin(url, img_url) for img_url in image_urls if img_url]

        # 递归获取更多图片
        links = soup.find_all('a', href=True)
        for link in links:
            link_url = urljoin(url, link['href'])
            if urlparse(link_url).netloc == urlparse(url).netloc:
                image_urls.extend(get_all_image_urls(link_url, session, proxies, headers))

        return image_urls
    except Exception as e:
        logging.error(f"Failed to get image URLs from {url}: {e}")
        return []

def download_images(url, folder, max_threads=5, proxies=None, headers=None, db_path=None):
    # 创建保存图片的文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 初始化会话
    session = requests.Session()

    # 获取所有图片链接
    image_urls = get_all_image_urls(url, session, proxies, headers)
    image_urls = list(set(image_urls))  # 去重

    # 使用多线程下载图片
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for i, img_url in enumerate(image_urls):
            futures.append(executor.submit(download_image, img_url, folder, i + 1, session, proxies, headers, db_path))

        # 显示进度条
        for future in tqdm(futures, desc="Downloading images"):
            future.result()

def main():
    print("Welcome to the Image Downloader!")
    url = input("Enter the URL of the webpage: ")
    folder = input("Enter the folder to save the images: ")
    max_threads = int(input("Enter the number of threads to use (default: 5): ") or 5)
    use_proxy = input("Do you want to use a proxy? (yes/no): ").strip().lower() == 'yes'
    use_db = input("Do you want to use a database to record downloads? (yes/no): ").strip().lower() == 'yes'
    db_path = "images.db" if use_db else None

    if use_proxy:
        proxy = input("Enter the proxy server (e.g., http://user:password@host:port): ")
        proxies = {
            'http': proxy,
            'https': proxy
        }
    else:
        proxies = None

    user_agent = input("Enter the User-Agent string (optional): ").strip()
    headers = {
        'User-Agent': user_agent
    } if user_agent else None

    if use_db:
        init_database(db_path)

    try:
        download_images(url, folder, max_threads, proxies, headers, db_path)
        logging.info("All images have been downloaded.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
