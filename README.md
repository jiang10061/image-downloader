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
## 其他：
1. 代理相关(Proxy)
```bash
# 启用代理池(自动轮换)
--proxy-pool https://api.proxyscrape.com/v2/?request=getproxies&protocol=https
# 设置代理认证(格式：用户名:密码)
--proxy-auth username:password
# 指定代理国家(ISO国家代码)
--proxy-country US
# 强制使用单个代理(禁用轮换)
--single-proxy socks5://127.0.0.1:1080
```
2. 断点续传(Resume)
```bash
# 启用断点续传(需数据库支持)
--auto-resume
# 从指定字节位置开始下载
--resume-byte 1048576  # 从1MB处继续下载
```
3. 高级压缩(Compression)
```bash
# 输出为WebP格式(高质量)
--compression-format webp --compression-quality 95
# 无损压缩(仅限WebP)
--compression-lossless
# 输出为PNG(透明背景保留)
--compression-format png
```
4. 安全与验证(Security)
```bash
# 验证SSL证书(禁用自签名证书)
--verify-ssl
# 禁用自动重定向(调试403错误)
--no-redirect
# 设置最小文件尺寸过滤(单位：KB)
--min-size 1024  # 只下载≥1MB的图片
```
5. 调试与日志(Debugging)
```bash
# 启用详细日志(输出到文件)
--log-level DEBUG --log-file download.log
# 模拟慢速网络(测试超时)
--simulate-slow-connection 50kbps
# 禁用颜色输出(纯文本模式)
--no-color
```
6. 分布式任务(Distributed)
```bash
# 启用分布式模式(需Redis集群)
--distributed-mode --redis-host 192.168.1.100
# 任务优先级(high/normal/low)
--task-priority high
# 节点心跳检测间隔(秒)
--heartbeat-interval 30
```
7. 冷门协议支持(Protocols)
```bash
# 下载FTP资源(需账号密码)
--ftp-url ftp://user:pass@ftp.example.com/file.zip
# 支持SFTP协议(SSH密钥认证)
--sftp-key ~/.ssh/id_rsa
# 解析robots.txt规则(遵守网站爬虫协议)
--parse-robots
```
8. 实验性功能(Experimental)
```bash
# 启用AI图像识别过滤(需GPU)
--ai-filter --model-path /path/to/model.pt
# 自动提取缩略图(从HTML中)
--extract-thumbnails
# 动态调整线程池(根据CPU负载)
--dynamic-threads
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
## 关于Others
- 这个是因为我每一次用termux向GitHub推送代码时都会出现错误，整了半天才整成，所以就直接放这里面了