# Image Downloader
高级图片下载工具，支持多线程下载、代理验证、断点续传、智能重试、图片压缩等功能。

## 核心功能
- 全异步下载引擎（基于aiohttp + aiomysql）
- 智能代理系统（自动验证代理有效性）
- 断点续传（需配合数据库使用）
- 智能重试策略（根据HTTP状态码自动判断）
- 多格式图片处理（JPEG/PNG/GIF/WebP/SVG）
- 响应式配置验证系统
- 插件式架构设计
## 安装依赖
```bash
pip install aiohttp aiomysql beautifulsoup4 Pillow rich
```
## 使用方法
- 交互式模式：
```bash
  python downloader.py
```
- 命令行模式：
```bash
  python downloader.py [目标URL] [保存目录] [选项]
```
## 常用选项：
```bash
  --threads N          下载线程数（默认20）
  --proxy PROXY_URL    设置HTTP代理（格式：http://host:port）
  --proxy-auth USER:PASS  代理认证（需与代理池配置匹配）
  --db-type TYPE       数据库类型（mysql/mariadb/sqlite，默认mysql）
  --db-user USER       数据库用户名
  --db-password PASS   数据库密码
  --compression-format FORMAT  输出图片格式（jpeg/png/webp，默认webp）
  --compression-quality N  压缩质量（1-100，WebP支持无损压缩）
  --smart-retry        启用智能重试（根据HTTP状态码自动判断）
  --auto-resume        启用断点续传（需配合数据库使用）
```
## 配置文件示例
```json
{
  "threads": 20,
  "max_retries": 5,
  "timeout": 15,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",

  "proxy_pool": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https",
  "proxy_auth": "user:pass",
  "proxy_country": "US",

  "database": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "secret",
    "database": "image_downloader",
    "charset": "utf8mb4"
  },

  "content_filter": {
    "min_size": [1920, 1080],
    "max_size": [4096, 4096],
    "content_types": [
      "image/jpeg",
      "image/png",
      "image/webp"
    ]
  },

  "image_compression": {
    "format": "webp",
    "quality": 85,
    "lossless": false
  }
}
```
## 注意事项
1. 依赖安装：
- 需Python 3.7+环境
- WebP压缩需额外安装Pillow支持：
```bash
pip install Pillow --upgrade --no-cache-dir
```
2. 代理配置：
- 代理池地址需支持HTTPS协议
- 代理认证格式： username:password 
3. 断点续传：
- 首次运行需手动创建数据库表：
```sql
CREATE TABLE images (
  id INT AUTO_INCREMENT PRIMARY KEY,
  url VARCHAR(255) UNIQUE,
  path VARCHAR(255),
  status ENUM('pending','downloading','completed','failed'),
  retry_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
3. 性能调优：
- 推荐配置： threads=CPU核心数×2 
- 大规模下载建议使用SQLite内存数据库：
```bash
python downloader.py https://example.com ./images --db sqlite:///:memory:
```