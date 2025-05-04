#!/bin/bash

# 生成随机密钥
generate_key() {
    head -c 32 /dev/urandom | base64
}

# 创建环境文件
echo "Generating environment files..."

# 服务端密钥
SERVER_KEY=$(generate_key)
echo "CHAT_SERVER_ENCRYPTION_KEY=$SERVER_KEY" > .env.server

# 客户端密钥（生产环境应使用不同密钥）
CLIENT_KEY=$(generate_key)
echo "CHAT_CLIENT_ENCRYPTION_KEY=$CLIENT_KEY" > .env.client

# 生成配置文件
mkdir -p config/dev config/prod
cp config.json config/dev/
cp config.json config/prod/

echo "Environment files generated:"
ls -la .env.*
echo "Configuration files generated in config/"