# Image Downloader

A Python script to download images from a webpage.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Command-Line Mode](#command-line-mode)
- [Configuration File](#configuration-file)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Acknowledgments](#acknowledgments)

## Features
- Supports multiple image formats (JPEG, PNG, GIF, etc.)
- Multi-threaded downloading for faster performance
- Optional proxy support
- Database recording to avoid duplicate downloads
- Image compression to save space
- Interactive command-line interface
- Configurable via a JSON configuration file

## Prerequisites
- Python 3.x
- Required libraries: `requests`, `beautifulsoup4`, `tqdm`, `pillow`

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jiang10061/image-downloader.git
   ```
2. Navigate to the project directory:
   ```bash
   cd image-downloader
   ```
3. Install the required libraries:
   ```bash
   pip install requests beautifulsoup4 tqdm pillow
   ```
## Usage
Interactive Mode
Run the script without any arguments to enter interactive mode:
  ```bash
  python download_images.py
  ```
Follow the on-screen prompts to configure the script.
Command-Line Mode
You can also run the script directly with command-line arguments:
  ```bash
  python download_images.py https://example.com ./images --threads 10 --proxy http://user:password@host:port --user-agent "Mozilla/5.0" --config config.json --db images.db
  ```
## Configuration File
The script uses a JSON configuration file (config.json) for default settings. Example config.json:
  ```json
  {
  // 代理配置（支持自动验证/轮换）
  "proxy_pool": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=10000&country=US",
  "proxy_auth": "optional_username:optional_password", // 如需代理认证

  // 请求头配置（增强反反爬能力）
  "headers": {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept-Encoding": "gzip, deflate"
  },

  // 数据库配置（支持多种数据库类型）
  "database": {
    "type": "mysql", // 可选: mysql | mariadb | sqlite
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_secure_password",
    "database": "image_downloader",
    "charset": "utf8mb4"
  },

  // 下载控制
  "threads": 20, // 建议设置为CPU核心数的2-3倍
  "max_retries": 5,
  "timeout": 15,

  // 内容过滤
  "content_filter": {
    "min_size": [1920, 1080], // 最小尺寸（宽x高）
    "max_size": [4096, 4096], // 最大尺寸（可选）
    "content_types": [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/svg+xml"
    ]
  },

  // 高级功能
  "smart_retry": true, // 智能重试（根据HTTP状态码判断）
  "auto_resume": true, // 断点续传
  "image_compression": {
    "format": "webp", // 输出格式（jpeg/png/webp）
    "quality": 85,
    "lossless": false
  }
}
  ```
## Examples
Interactive Mode
  ```
  Welcome to the Image Downloader!
Enter the URL of the webpage: https://example.com
  Enter the folder to save the images: ./images
  Enter the path to the config file (optional, press Enter to use default): 
  Enter the number of threads to use (default: 5): 10
  Do you want to use a proxy? (yes/no): yes
  Enter the proxy server (e.g., http://user:password@host:port): http://user:password@host:port
  Do you want to use a database to record downloads? (yes/no): yes
  Enter the User-Agent string (optional): Mozilla/5.0
  ```
## Command-Line Mode
  ```bash
  python download_images.py https://example.com ./images --threads 10 --proxy http://user:password@host:port --user-agent "Mozilla/5.0" --config config.json --db images.db
  ```
## Troubleshooting
- SSL Certificate Problem: If you encounter SSL certificate issues, try updating your system's certificate library or use SSH instead of HTTPS.
- Network Issues: Ensure your network connection is stable. If you are behind a proxy, configure the proxy settings in the config.json file.
- Permission Issues: Ensure you have the necessary permissions to write to the specified folder.
- Database Issues: Ensure SQLite is installed if you are using database recording.
## Acknowledgments
- requests
- beautifulsoup4
- tqdm
- Pillow
- SQLite
