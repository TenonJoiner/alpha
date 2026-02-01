# ✅ Alpha Client-Server 架构使用指南

## 🚀 快速开始

### 1. 启动服务器

```bash
cd /home/zhang/bot/alpha

# 启动服务器（后台运行）
./scripts/start_server.sh
```

输出示例：
```
Alpha Server Startup
Project: /home/zhang/bot/alpha

Starting Alpha server...

✓ Alpha server started (PID: 3474546)
  API: http://0.0.0.0:8080
  WebSocket: ws://0.0.0.0:8080/api/v1/ws/chat

Connect with: ./scripts/start_client.sh
Logs: tail -f logs/alpha-api.log
```

### 2. 连接聊天

**在新终端中**：

```bash
cd /home/zhang/bot/alpha

# 连接到服务器聊天
./scripts/start_client.sh
```

### 3. 停止服务器

```bash
./scripts/stop_server.sh
```

---

## 💬 使用示例

连接成功后的聊天界面：

```
╭──────────────────────────────────────────╮
│  Alpha AI Assistant - Client             │
│  Connected to server for real-time chat  │
╰──────────────────────────────────────────╯

Connecting to Alpha server at ws://localhost:8080/api/v1/ws/chat...
✓ Connected to Alpha
Type your message to start chatting. Type 'quit' or 'exit' to disconnect.

You> 你好Alpha
Alpha> 你好主人！我是Alpha，您的个人AI助手。有什么我可以帮助您的吗？

You> 帮我查询北京的天气
Analyzing task for relevant skills...
🎯 Using skill: weather-query (relevance: 8.5/10)
Thinking...
Alpha> 正在为您查询北京的天气...

You> quit
Disconnected from Alpha
```

**退出客户端后，服务器继续运行！**下次连接，对话历史还在。

---

## 🔧 常用命令

### 查看服务器状态

```bash
# 检查进程
ps aux | grep "alpha.api.server" | grep -v grep

# 查看日志
tail -f logs/alpha-api.log

# 检查端口
netstat -tlnp | grep 8080
```

### 测试API

```bash
# 取消代理（如果环境有代理设置）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 测试根路径
curl http://localhost:8080/

# 测试健康检查
curl http://localhost:8080/api/health

# 查看API文档
浏览器访问: http://localhost:8080/api/docs
```

### 远程连接

如果服务器在远程机器上：

```bash
# 客户端连接到远程服务器
./scripts/start_client.sh --server ws://远程IP:8080/api/v1/ws/chat
```

---

## ⚠️ 注意事项

### HTTP代理问题

如果您的环境设置了HTTP代理，可能影响localhost连接。解决方法：

```bash
# 临时取消代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 或在 ~/.bashrc 中添加localhost例外
export no_proxy="localhost,127.0.0.1"
```

### 依赖安装

确保所有依赖已安装：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

特别需要的库：
- `websockets` - 客户端WebSocket连接
- `fastapi` - API服务器
- `uvicorn` - ASGI服务器

---

## 📊 架构说明

```
┌─────────────────────────────────────┐
│  Alpha Server (后台进程)             │
│  ┌──────────────────────────────┐   │
│  │  AlphaEngine                 │   │
│  │  - 定时任务                   │   │
│  │  - 主动学习                   │   │
│  │  - 对话历史                   │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  FastAPI + WebSocket         │   │
│  │  0.0.0.0:8080                │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              ↑
              │ WebSocket连接
              │
    ┌─────────┴──────────┐
    │                    │
┌───┴────┐         ┌─────┴─────┐
│ CLI客户端│        │  远程客户端 │
│(本地终端)│        │  (未来)    │
└────────┘         └───────────┘
```

**核心优势**：
1. ✅ 服务器24小时运行
2. ✅ 客户端随时连接/断开
3. ✅ 对话历史保留在服务器
4. ✅ 支持远程访问
5. ✅ 统一的AlphaEngine实例

---

## 🎯 对比旧方式

### 旧方式 (./start.sh)
```bash
./start.sh
# ❌ 关闭终端 = 停止服务
# ❌ 无法远程访问
# ❌ 每次都是新会话
```

### 新方式 (Client-Server)
```bash
./scripts/start_server.sh  # 启动一次
./scripts/start_client.sh  # 随时连接
# ✅ 服务器持续运行
# ✅ 随时断开/重连
# ✅ 历史记录保留
# ✅ 支持远程访问
```

---

## 📝 文件说明

- `scripts/start_server.sh` - 启动服务器（使用nohup后台运行）
- `scripts/start_client.sh` - 启动CLI客户端
- `scripts/stop_server.sh` - 停止服务器
- `alpha/api/server.py` - API服务器主程序
- `alpha/api/chat_handler.py` - 聊天处理逻辑
- `alpha/api/routes/websocket.py` - WebSocket路由
- `alpha/client/cli.py` - CLI客户端程序
- `data/alpha.pid` - 服务器进程ID文件
- `logs/alpha-api.log` - API服务器日志

---

## 🐛 故障排查

### 服务器无法启动

```bash
# 1. 检查端口是否被占用
netstat -tlnp | grep 8080

# 2. 查看日志
tail -100 logs/alpha-api.log

# 3. 检查虚拟环境
source venv/bin/activate
python3 -c "import fastapi; print('FastAPI OK')"
```

### 客户端无法连接

```bash
# 1. 确认服务器正在运行
ps aux | grep "alpha.api.server"

# 2. 测试WebSocket端口
curl http://localhost:8080/

# 3. 检查代理设置
echo $http_proxy
unset http_proxy https_proxy
```

### 日志位置

- 服务器日志: `logs/alpha-api.log`
- 旧CLI日志: `logs/alpha.log`

---

## 🎉 总结

主人，现在Alpha已经是真正的Client-Server应用了！

**启动流程**：
```bash
# 1. 启动服务器（一次）
./scripts/start_server.sh

# 2. 连接聊天（随时）
./scripts/start_client.sh

# 3. 随时退出，服务器继续运行
exit

# 4. 再次连接（历史保留）
./scripts/start_client.sh
```

享受24小时不间断的Alpha服务吧！🚀
