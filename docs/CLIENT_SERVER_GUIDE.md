# Alpha Client-Server 架构使用指南

Alpha现在采用Client-Server架构，实现真正的24小时服务 + 随时连接的客户端。

## 架构概述

```
┌─────────────────────────────────────┐
│  服务器（24小时运行）                 │
│  ┌──────────────────────────────┐   │
│  │  AlphaEngine                 │   │
│  │  - 定时任务                   │   │
│  │  - 主动学习                   │   │
│  │  - 对话历史                   │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  HTTP API + WebSocket        │   │
│  │  端口: 8080                   │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              ↑
              │ 连接
              │
    ┌─────────┴──────────┐
    │                    │
┌───┴────┐         ┌─────┴─────┐
│ CLI客户端│        │  Web浏览器 │
│ (终端)  │        │   (未来)   │
└────────┘         └───────────┘
```

## 快速开始

### 1. 安装依赖

```bash
# 安装websockets库（客户端需要）
pip install websockets

# 或更新所有依赖
pip install -r requirements.txt
```

### 2. 启动服务器

有两种方式启动服务器：

#### 方式1：使用alpha命令（推荐）

```bash
# 将bin/alpha添加到PATH
export PATH="$PATH:$(pwd)/bin"

# 启动服务器
alpha start

# 输出：
# Starting Alpha server...
# ✓ Alpha server started
#   API: http://0.0.0.0:8080
#   WebSocket: ws://0.0.0.0:8080/api/v1/ws/chat
#
# Connect with: alpha chat
```

#### 方式2：使用systemd（生产环境）

```bash
# 安装systemd服务
sudo ./scripts/install_daemon.sh

# 配置API密钥
sudo nano /etc/alpha/environment

# 启动服务
sudo systemctl start alpha

# 开机自启
sudo systemctl enable alpha
```

#### 方式3：手动启动

```bash
python -m alpha.main --daemon --api-host 0.0.0.0 --api-port 8080
```

### 3. 连接聊天

启动服务器后，使用客户端连接：

```bash
# 使用alpha命令
alpha chat

# 或直接运行客户端
python -m alpha.client.cli
```

**聊天界面**：

```
╭──────────────────────────────────────────╮
│  Alpha AI Assistant - Client             │
│  Connected to server for real-time chat  │
╰──────────────────────────────────────────╯

Connecting to Alpha server at ws://localhost:8080/api/v1/ws/chat...
✓ Connected to Alpha
Type your message to start chatting. Type 'quit' or 'exit' to disconnect.

You> 你好
Alpha> 你好！我是Alpha，您的个人AI助手。有什么我可以帮助您的吗？

You> 帮我查今天北京的天气
Analyzing task for relevant skills...
🎯 Using skill: weather-query (relevance: 8.5/10)
Thinking...
Alpha> 正在为您查询北京今天的天气...
[查询结果...]

You> quit
Disconnected from Alpha
```

### 4. 管理服务器

```bash
# 查看状态
alpha status
# 输出：
# Alpha server: RUNNING (PID: 12345)
#   Status: operational
#   Uptime: 3600.5s
#   Tasks: 0 running, 15 completed

# 停止服务器
alpha stop

# 重启服务器
alpha stop && alpha start
```

### 5. 提交任务（异步）

除了实时聊天，还可以提交异步任务：

```bash
# 提交任务
alpha task "帮我整理今天的日程"

# 输出：
# Submitting task: 帮我整理今天的日程
# ✓ Task submitted: task_abc123
#   Check status: alpha task-status task_abc123

# 查询任务状态
alpha task-status task_abc123

# 输出：
# Task: task_abc123
#   Status: completed
#   Created: 2026-02-01T10:30:00
#   Result: [任务结果...]
```

## 客户端命令

在聊天界面中，支持以下命令：

- `help` - 显示帮助信息
- `clear` - 清空对话历史（服务器端）
- `quit` / `exit` - 断开连接

## API端点

服务器提供以下API端点：

### WebSocket

- `ws://localhost:8080/api/v1/ws/chat` - 实时聊天

### HTTP REST API

- `GET /api/health` - 健康检查
- `GET /api/v1/status` - 系统状态
- `POST /api/v1/tasks` - 提交任务
- `GET /api/v1/tasks/{id}` - 查询任务
- `GET /api/v1/tasks` - 列出所有任务
- `DELETE /api/v1/tasks/{id}` - 取消任务

### API文档

启动服务器后，访问：

- Swagger UI: http://localhost:8080/api/docs
- ReDoc: http://localhost:8080/api/redoc

## 配置选项

### 服务器配置

```bash
# 自定义主机和端口
alpha start --host 0.0.0.0 --port 9000

# 使用自定义配置文件
alpha start --config /path/to/config.yaml
```

### 客户端配置

```bash
# 连接到远程服务器
alpha chat --host 192.168.1.100 --port 9000

# 或使用完整URL
python -m alpha.client.cli --server ws://192.168.1.100:9000/api/v1/ws/chat
```

## 使用场景

### 场景1：本地开发

```bash
# Terminal 1 - 启动服务器
alpha start

# Terminal 2 - 连接聊天
alpha chat

# 随时退出聊天，服务器继续运行
# 需要时再连接
```

### 场景2：服务器部署

```bash
# 服务器上安装并启动
sudo systemctl start alpha

# 本地电脑连接
alpha chat --host your-server.com --port 8080
```

### 场景3：定时任务 + 按需聊天

```bash
# 启动服务器（后台运行定时任务）
alpha start

# 需要时连接聊天
alpha chat

# 退出聊天后，定时任务继续运行
```

## 优势对比

### 旧架构（start.sh）

```bash
./start.sh
# - 启动新的AlphaEngine实例
# - 关闭终端 = 停止服务
# - 无法远程访问
# - 每次启动是新的会话
```

### 新架构（Client-Server）

```bash
alpha start    # 启动一次，持续运行
alpha chat     # 随时连接
# - 服务器24小时运行
# - 关闭客户端不影响服务器
# - 可远程访问
# - 对话历史保留
# - 定时任务持续运行
```

## 故障排查

### 无法连接到服务器

```bash
# 1. 检查服务器是否运行
alpha status

# 2. 检查端口是否被占用
sudo lsof -i :8080

# 3. 查看服务器日志
tail -f logs/alpha.log

# 4. 检查防火墙（如果远程连接）
sudo ufw allow 8080
```

### 服务器启动失败

```bash
# 查看详细日志
tail -f logs/alpha.log

# 检查配置文件
cat config.yaml

# 检查API密钥
echo $DEEPSEEK_API_KEY
```

### WebSocket连接断开

客户端会自动显示错误信息。常见原因：

1. 服务器停止运行
2. 网络中断
3. 服务器重启

解决方法：重新连接即可（对话历史保留在服务器）

## 下一步

- [ ] Web聊天界面（浏览器访问）
- [ ] 多用户支持（独立会话）
- [ ] 对话历史管理
- [ ] 用户认证

## 总结

新架构的核心优势：

1. ✅ **真正的24小时服务** - 服务器持续运行
2. ✅ **随时连接断开** - 客户端灵活连接
3. ✅ **对话历史保留** - 重连后继续之前的对话
4. ✅ **远程访问** - 可从任何机器连接
5. ✅ **统一管理** - 一个服务器实例，多种访问方式

主人，现在Alpha是真正的服务端应用了！🎉
