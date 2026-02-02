# Alpha CLI Commands Quick Reference

**Version**: v1.0.0
**Last Updated**: 2026-02-02

---

## 🚀 Server Management

### Start/Stop Server

```bash
# Start server (recommended - uses scripts)
./scripts/start_server.sh [host] [port]    # Default: 0.0.0.0 8080

# Stop server
./scripts/stop_server.sh

# Check server status
ps aux | grep "alpha.api.server"
```

### Server Logs

```bash
# View server logs
tail -f logs/alpha-api.log

# View all logs
tail -f logs/alpha.log
```

---

## 💬 Chat Client

### Connect to Server

```bash
# Start chat client (default: localhost:8080)
./scripts/start_client.sh

# Connect to remote server
./scripts/start_client.sh --server ws://HOST:PORT/api/v1/ws/chat

# Connect with specific port
./scripts/start_client.sh --port 9000
```

### Chat Commands

```
quit, exit          - Disconnect from server
clear               - Clear screen
help                - Show available commands
```

---

## 🎯 Task Management

### Task Decomposition Commands

```bash
# Manual task decomposition
alpha> decompose <task_description>

# View task status
alpha> task status <task_id>

# View task history
alpha> task history [limit]

# Cancel running task
alpha> task cancel <task_id>
```

**Examples**:
```bash
alpha> decompose Build a Python web scraper for news articles
alpha> task status task_12345
alpha> task history 10
```

---

## 🤖 Agent Skills

### Skill Discovery & Management

```bash
# Search for skills
alpha> skill search <keyword>

# List installed skills
alpha> skill list

# Install skill
alpha> skill install <skill_name>

# Remove skill
alpha> skill remove <skill_name>

# Skill info
alpha> skill info <skill_name>
```

**Examples**:
```bash
alpha> skill search weather
alpha> skill install weather-query
alpha> skill list
```

---

## 👤 User Profile & Personalization

### Profile Commands

```bash
# View your profile
alpha> profile show

# View specific preference
alpha> profile get <preference_name>

# Override preference
alpha> profile set <preference_name> <value>

# Reset preference to learned value
alpha> profile reset <preference_name>

# Clear all overrides
alpha> profile clear

# Export profile
alpha> profile export <file_path>

# Import profile
alpha> profile import <file_path>
```

**Examples**:
```bash
alpha> profile show
alpha> profile get verbosity
alpha> profile set verbosity detailed
alpha> profile reset verbosity
alpha> profile export my_profile.json
```

### Available Preferences

- `verbosity`: concise | balanced | detailed
- `language_mix`: english | chinese | mixed
- `tone`: formal | casual | friendly
- `technical_level`: beginner | intermediate | expert

---

## 🖼️ Multimodal (Image Analysis)

### Image Commands

```bash
# Analyze image
alpha> analyze <image_path>

# Ask specific question about image
alpha> image <image_path> "<question>"

# Compare multiple images
alpha> compare <image1> <image2> "<question>"
```

**Examples**:
```bash
alpha> analyze error_screenshot.png
alpha> image diagram.png "Explain this architecture"
alpha> compare design_v1.png design_v2.png "Which is better?"
```

**Supported Formats**: PNG, JPEG, GIF, WebP, BMP

---

## 🔄 Workflow Management

### Workflow Commands

```bash
# List workflows
alpha> workflow list

# Create workflow
alpha> workflow create <name>

# Run workflow
alpha> workflow run <workflow_name> [params]

# View workflow
alpha> workflow show <workflow_name>

# Delete workflow
alpha> workflow delete <workflow_name>
```

**Examples**:
```bash
alpha> workflow list
alpha> workflow run daily-backup
alpha> workflow show morning-routine
```

---

## 🔧 System Commands

### Health & Status

```bash
# Check system health
curl http://localhost:8080/api/health

# View API documentation
# Browser: http://localhost:8080/api/docs
```

### Configuration

```bash
# Configuration file location
config.yaml

# Environment variables
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

---

## 🛠️ Troubleshooting

### Common Issues

**Server won't start**:
```bash
# Check port availability
netstat -tlnp | grep 8080

# Check logs
tail -f logs/alpha-api.log

# Kill existing process
pkill -f "alpha.api.server"
```

**Client can't connect**:
```bash
# Test server
curl http://localhost:8080/

# Disable proxy (if needed)
unset http_proxy https_proxy

# Check server status
ps aux | grep alpha
```

**Missing dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Advanced Usage

### API Endpoints

```bash
# Health check
GET http://localhost:8080/api/health

# Submit task
POST http://localhost:8080/api/tasks

# Get task status
GET http://localhost:8080/api/tasks/{task_id}

# WebSocket chat
ws://localhost:8080/api/v1/ws/chat
```

### Daemon Mode (systemd)

```bash
# Install as system service
sudo ./scripts/install_daemon.sh

# Start service
sudo systemctl start alpha

# Enable auto-start
sudo systemctl enable alpha

# View service logs
sudo journalctl -u alpha -f
```

---

## 💡 Quick Tips

1. **Server runs 24/7** - Start once, connect anytime
2. **Chat history persists** - Conversation saved on server
3. **Remote access** - Connect from any machine via WebSocket
4. **Skill auto-install** - Skills download automatically when needed
5. **Proactive assistance** - Alpha suggests helpful actions
6. **Multi-model optimization** - Auto-selects best model for each task

---

## 📚 Additional Resources

- **Full Documentation**: `docs/manual/`
- **User Guide**: `USAGE.md`
- **Quick Start**: `QUICKSTART.md`
- **Release Notes**: `RELEASE_NOTES_v1.0.0.md`
- **Changelog**: `CHANGELOG.md`

---

## 🆘 Getting Help

**In Chat**:
```bash
alpha> help
alpha> skill search <topic>
```

**Documentation**:
```bash
# English docs
ls docs/manual/en/

# Chinese docs
ls docs/manual/zh/
```

**Logs**:
```bash
tail -f logs/alpha-api.log    # Server logs
tail -f logs/alpha.log        # General logs
```

---

**Master Reference**: This document provides quick access to Alpha's CLI commands.
For detailed explanations, see full documentation in `docs/manual/`.
