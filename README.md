1. 核心依赖（不安装会死）

|库名|	版本要求	|作用|	安装命令|
|-----|----------|---|----------|
| aiohttp| 	>=3.8.0	|异步HTTP客户端，用于高效下载	| pip install aiohttp 
| aiomysql |	>=0.1.0|	异步MySQL客户端，支持数据库操作	 |pip install aiomysql 
| beautifulsoup4 	|>=4.12.0|	HTML/XML解析库，用于网页内容提取|	 pip install beautifulsoup4 
 |Pillow| 	>=9.3.0	图片处理库|（必须安装，支持WebP需升级）|	 pip install Pillow 
 |rich |	>=13.0.0|	终端富文本输出，美化日志和进度条	| pip install rich

2. 可选扩展依赖

|库名	|版本要求	|作用|	安装命令|
|-----|--------|-----|---------|
 |aiosqlite 	|>=0.17.0	|SQLite异步支持（替代MySQL）|	 pip install aiosqlite |
| pysocks 	|>=1.7.0|	SOCKS5代理支持	| pip install pysocks |
| requests| 	>=2.28.0|	同步HTTP备用库（非必须，但某些场景可能用到）|	 pip install requests|
| webptools| 	>=0.1.0	|WebP格式优化工具（可选）	| pip install webptools |
 |imageio 	|>=2.25.0	|动态图片（GIF）处理|	 pip install imageio|
| pyopenssl 	|>=23.0.0|	SSL证书验证（解决证书错误）	| pip install pyopenssl |
| tqdm| 	>=4.64.0|	进度条增强（替代Rich）	| pip install tqdm|
| redis 	|>=4.4.0	|Redis支持（分布式任务队列）|	 pip install redis |
| rq| 	>=1.13.0	|任务队列管理	| pip install rq|
| torch |	>=1.13.0	|PyTorch框架（AI过滤/图像分析）|	 pip install torch torchvision |
| tensorflow |	>=2.10.0	|TensorFlow框架（可选替代PyTorch）|	 pip install tensorflow|
| cryptography 	|>=40.0.0	加密支持|（代理认证/SSL）	| pip install cryptography |
 |python-socks |	>=1.2.0	|Socks协议支持|	 pip install python-socks |
| lxml 	|>=4.9.0	|高性能XML/HTML解析（可选替代BeautifulSoup）|	 pip install lxml |
 |ffmpeg-python |	>=0.2.0	|视频/动图处理（实验性功能）	| pip install ffmpeg-python |

3. 安装建议
### 基础安装
```bash
pip install aiohttp aiomysql beautifulsoup4 Pillow rich
```
### 完整安装
```bash
pip install aiohttp aiomysql beautifulsoup4 Pillow rich \
           aiosqlite pysocks requests webptools imageio \
           redis rq torch torchvision cryptography python-socks \
           lxml ffmpeg-python
```
4. 基础用法
### 交互模式
python image_downloader.py
### 命令行模式
python image_downloader.py [目标URL] [保存目录] [选项]
5. 核心参数设置

|参数	|默认值	|说明|
|-----|-------|----|
| --threads N |	20|	下载线程数（建议 CPU核心数×2）|
| --max-retries N 	|5	|单张图片最大重试次数|
| --timeout S |	15	|请求超时时间（秒）|
| --auto-resume |	False|	启用断点续传（需数据库支持）|
| --no-redirect 	|False|	禁用自动重定向（调试403错误）|
| --proxy PROXY_URL| 	-	|代理地址（如  http://host:port ）|
| --proxy-auth USER:PASS| 	-	|代理认证（格式：用户名:密码）|
| --proxy-country ISO_CODE 	|-	|代理国家过滤（如  US ）|
| --single-proxy |	-	|强制使用单个代理（禁用轮换）|
| --min-size KB |	0|	最小文件尺寸（KB）|
| --max-size KB |	0	|最大文件尺寸（KB）|
| --content-types MIME_TYPES| 	 image/* 	|允许的MIME类型（如  image/jpeg,image/png ）|
| --compression-format FORMAT 	| webp |	输出格式（ jpeg / png / webp ）|
| --compression-quality N |	85|	压缩质量（1-100，WebP支持无损）|
| --lossless |	False|	WebP无损压缩（仅限WebP）|

# 写烦了，不想写了
# •͈ ₃ •͈ᐝ