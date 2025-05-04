# Chat System

## 项目概述
这是一个基于Python的分布式聊天系统，支持以下核心功能：
- 双通信模式（服务端中转/P2P直连）
- AES-256-GCM端到端加密
- 心跳检测与自动重连
- 多环境配置支持

**重要警告**：默认配置文件包含测试密钥，**必须**在部署前替换为自定义密钥！

---

## 功能特性

### 通信模式

| 模式          | 工作原理                     | 适用场景               |
|---------------|------------------------------|------------------------|
| 服务端中转    | 所有消息经过中央服务器转发   | 局域网/互联网环境      |
| P2P直连       | 直接建立客户端间连接         | 需要绕过中转的场景     |

### 安全特性
- AES-256-GCM加密算法
- 消息完整性验证（GCM Tag）
- IV随机生成（每次加密不同）

---

## 技术栈

| 组件          | 技术选型                     |
|---------------|------------------------------|
| 加密库        | pycryptodome                 |
| 网络框架      | 原生Socket + Threading       |
| 配置管理      | JSON + Python-dotenv         |

---

## 安装要求
### 依赖项
```bash
pip install pycryptodome python-dotenv
```
### 系统要求
- Python 3.7+
- OpenSSL 1.1.1+
- 64位操作系统
## 快速开始
1. 生成安全密钥
```bash
# 生成256位(32字节)加密密钥
python -c "from Crypto.Random import get_random_bytes; print(get_random_bytes(32).hex())"
```
2. 配置系统
```bash
# 目录结构
.
├── server/
│   ├── config.json
│   └── server.py
└── client/
    ├── config.json
    └── client.py
```
3. 修改配置文件
服务端配置 ( server/config.json ):
```json
{
  "server": {
    "bind_address": "0.0.0.0",
    "port": 5555,
    "encryption_key": "YOUR_SERVER_KEY_HERE"  // 替换为生成的密钥
  }
}
```
客户端配置 ( client/config.json )：
```bash
{
  "client": {
    "server_address": "localhost",
    "encryption_key": "YOUR_CLIENT_KEY_HERE"  // 必须与服务端相同
  }
}
```
## 使用方法
### 启动服务端
```bash
cd server
python server.py
```
### 启动客户端
```bash
cd client
python client.py
```
### 交互命令
```bash
命令	功能说明
 /help 	显示帮助信息
 /users 	列出在线用户
 /exit 	安全退出程序
```
## 配置说明
### 服务端配置项
|参数	|类型	|默认值	|说明|
|-----|----|-------|-----|
|bind_address|	string|	0.0.0.0|	监听地址|
|port	|	int |5555	|服务端口|
|encryption_key|	string|	-	|AES-256加密密钥（hex格式）|

### 客户端配置项
|参数	|类型|	默认值|	说明|
|-----|-----|-----|-----|
|server_address	|string	|-	|服务端地址|
|server_port|	int|	5555	|服务端端口|
|encryption_key| string	|-	|必须与服务端完全一致|
## 安全警告
1. **必须替换默认密钥**：默认密钥仅用于测试，真实环境必须使用生成的256位密钥
2. **密钥保护**：不要将密钥提交到版本控制系统（.gitignore必须包含配置文件）
3. **传输安全**：建议配合TLS使用（需修改配置启用SSL）
## 目录结构
```
.
├── server/
│   ├── config.json      # 服务端配置
│   └── server.py        # 服务端主程序
├── client/
│   ├── config.json      # 客户端配置
│   └── client.py        # 客户端主程序
└── README.md            # 本说明文件
```
**重要提示**：本系统仍在开发中，生产环境使用前请进行充分测试。默认配置仅用于演示，实际部署必须修改所有敏感参数！