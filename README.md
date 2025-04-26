# Image Downloader

A Python script to download images from a webpage.

## Features
- Supports multiple image formats (JPEG, PNG, GIF, etc.)
- Multi-threaded downloading for faster performance
- Optional proxy support
- Database recording to avoid duplicate downloads
- Image compression to save space

## Usage
```bash
python download_images.py https://example.com ./images --threads 10 --proxy http://user:password@host:port --user-agent "Mozilla/5.0" --config config.json --db images.db
