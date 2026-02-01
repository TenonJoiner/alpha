# Alpha Troubleshooting Guide

Comprehensive guide for diagnosing and fixing common Alpha issues.

---

## 📋 Quick Diagnostics Checklist

Run these commands first to identify issues:

```bash
# 1. Check API configuration
./check_api_config.sh

# 2. Verify Python environment
python3 --version  # Should be 3.8+
which python3

# 3. Check virtual environment
echo $VIRTUAL_ENV  # Should show venv path

# 4. Verify dependencies
pip list | grep -E "anthropic|openai|fastapi|chromadb"

# 5. Check data directory
ls -la data/

# 6. Check server status (if using client-server mode)
python3 bin/alpha status --port 9000

# 7. View recent logs
tail -50 data/alpha.log
```

---

## 🚨 Common Issues & Solutions

### 1. Installation & Setup Issues

#### Issue: `ModuleNotFoundError: No module named 'alpha'`

**Cause**: Not running from project directory or virtual environment not activated

**Solution**:
```bash
# Ensure you're in the project directory
cd /path/to/alpha

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify installation
pip list | grep alpha
python -c "import alpha; print('Success!')"
```

#### Issue: `pip install -r requirements.txt` fails

**Cause**: Missing system dependencies or conflicting packages

**Solution**:
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails (e.g., chromadb):
pip install chromadb --no-cache-dir

# For system dependency issues (Linux):
sudo apt-get install python3-dev build-essential

# For Mac:
brew install python@3.12
```

#### Issue: Permission denied when creating data directory

**Cause**: Insufficient permissions

**Solution**:
```bash
# Check current permissions
ls -la

# Create with proper permissions
mkdir -p data
chmod 755 data

# If owned by root, change ownership
sudo chown -R $USER:$USER data/
```

---

### 2. API Configuration Issues

#### Issue: `API key not configured` error

**Cause**: Environment variable not set or incorrect

**Solution**:
```bash
# Check if key is set
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Set temporarily (current session only)
export DEEPSEEK_API_KEY="sk-..."

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export DEEPSEEK_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc

# Verify with test script
python test_deepseek.py
```

#### Issue: API calls fail with authentication error

**Cause**: Invalid or expired API key

**Solution**:
```bash
# 1. Verify key format
echo $DEEPSEEK_API_KEY | head -c 10
# Should start with "sk-" for most providers

# 2. Test key with curl
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# 3. Regenerate key if needed
# Go to provider dashboard and create new key

# 4. Update config.yaml if using file-based config
cat config.yaml | grep api_key
```

#### Issue: Rate limit exceeded errors

**Cause**: Too many API requests in short time

**Solution**:
```bash
# 1. Check rate limits in provider dashboard

# 2. Add retry delays (config.yaml):
llm:
  retry_delay: 2.0  # seconds
  max_retries: 3

# 3. Use cheaper/faster model for simple tasks
llm:
  default_provider: "deepseek"
  default_model: "deepseek-chat"

# 4. Monitor API usage
# Check provider dashboard for rate limit status
```

---

### 3. Server & Connectivity Issues

#### Issue: Server won't start - "Address already in use"

**Cause**: Port 9000 already in use by another process

**Solution**:
```bash
# 1. Find process using port 9000
lsof -i :9000
netstat -tulpn | grep 9000

# 2. Kill the process
kill -9 <PID>

# 3. Or use a different port
./scripts/start_server.sh 0.0.0.0 9001

# 4. Update client connection
./scripts/start_client.sh --server ws://localhost:9001/api/v1/ws/chat
```

#### Issue: Client can't connect to server - WebSocket error

**Cause**: Server not running, firewall blocking, or wrong URL

**Solution**:
```bash
# 1. Verify server is running
python3 bin/alpha status --port 9000

# 2. Check if port is listening
netstat -tulpn | grep 9000
lsof -i :9000

# 3. Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:9000/api/v1/ws/chat

# 4. Check firewall (Linux)
sudo ufw status
sudo ufw allow 9000

# 5. If using proxy, bypass localhost
export NO_PROXY="localhost,127.0.0.1"
```

#### Issue: Server stops unexpectedly

**Cause**: Crash, OOM, or signal received

**Solution**:
```bash
# 1. Check logs for errors
tail -100 nohup.out
grep -i "error\|exception\|crash" nohup.out

# 2. Check system resources
free -h  # Memory
df -h    # Disk space

# 3. Increase memory limit (if needed)
# Edit systemd service or docker container config

# 4. Enable auto-restart (systemd)
sudo systemctl enable alpha
sudo systemctl restart alpha

# 5. Monitor server health
watch -n 5 'python3 bin/alpha status --port 9000'
```

---

### 4. Database Issues

#### Issue: `database is locked` error

**Cause**: Multiple processes accessing SQLite database simultaneously

**Solution**:
```bash
# 1. Stop all Alpha instances
pkill -f "python.*alpha"

# 2. Check for lock file
ls -la data/alpha.db-*

# 3. Remove stale locks (if safe)
rm data/alpha.db-shm data/alpha.db-wal

# 4. Restart with single instance
./start.sh

# 5. For client-server mode, use server for all access
./scripts/start_server.sh 0.0.0.0 9000
```

#### Issue: Database corruption - malformed database error

**Cause**: Improper shutdown or disk corruption

**Solution**:
```bash
# 1. Backup existing database
cp data/alpha.db data/alpha.db.backup

# 2. Try to recover with SQLite
sqlite3 data/alpha.db ".recover" > recovered.sql
sqlite3 data/alpha_new.db < recovered.sql
mv data/alpha_new.db data/alpha.db

# 3. If recovery fails, recreate (WARNING: loses data)
rm data/alpha.db
python -m alpha.interface.cli  # Creates new DB

# 4. Restore from backup if available
cp data/alpha.db.backup data/alpha.db
```

#### Issue: Vector memory / ChromaDB errors

**Cause**: ChromaDB collection not initialized or corrupted

**Solution**:
```bash
# 1. Check ChromaDB data
ls -la data/chroma/

# 2. Reset vector memory (loses semantic search history)
rm -rf data/chroma/
# Restart Alpha to recreate

# 3. Test ChromaDB directly
python3 << EOF
from chromadb import Client
from chromadb.config import Settings
client = Client(Settings(persist_directory="data/chroma"))
print("ChromaDB OK")
EOF

# 4. Check embeddings provider config
grep -A 5 "embeddings:" config.yaml
```

---

### 5. LLM & Model Issues

#### Issue: Very slow responses from LLM

**Cause**: Network latency, large prompts, or slow model

**Solution**:
```bash
# 1. Test network to API endpoint
ping api.deepseek.com
curl -w "@curl-format.txt" -o /dev/null -s https://api.deepseek.com/v1/models

# 2. Switch to faster model
# Edit config.yaml:
llm:
  default_model: "deepseek-chat"  # Faster than deepseek-reasoner

# 3. Reduce conversation context
# In chat:
You> clear  # Clears history

# 4. Enable streaming for faster perceived response
llm:
  stream: true

# 5. Check model status
curl https://status.deepseek.com/
```

#### Issue: Model returns poor quality responses

**Cause**: Using wrong model for task type

**Solution**:
```bash
# 1. Enable intelligent model selection
llm:
  enable_model_selection: true

# 2. Manually specify model for task
You> Use deepseek-reasoner for this complex problem
You> Switch to deepseek-coder for this programming task

# 3. Adjust temperature for more focused responses
llm:
  temperature: 0.3  # Lower = more focused (default: 0.7)

# 4. Review model selection logs
grep "Model selected" data/alpha.log
```

#### Issue: Token limit exceeded errors

**Cause**: Conversation context too long

**Solution**:
```bash
# 1. Clear conversation history
You> clear

# 2. Reduce max_tokens in config
llm:
  max_tokens: 2000  # Lower limit

# 3. Enable conversation summarization (if available)
memory:
  enable_summarization: true

# 4. Use smaller context window model
llm:
  default_model: "deepseek-chat"  # 32K context vs 64K
```

---

### 6. Skill & Tool Issues

#### Issue: Skill installation fails

**Cause**: Network issues, invalid skill, or missing dependencies

**Solution**:
```bash
# 1. Check network connectivity
curl -I https://raw.githubusercontent.com

# 2. Manually install skill
cd skills/
git clone <skill-repo-url>
cd <skill-name>
pip install -r requirements.txt  # if exists

# 3. Verify skill structure
ls -la skills/<skill-name>/
cat skills/<skill-name>/SKILL.md

# 4. Check skill registry
python3 << EOF
from alpha.skills.registry import SkillRegistry
registry = SkillRegistry()
print(registry.list_skills())
EOF
```

#### Issue: Tool execution fails - timeout

**Cause**: Tool taking too long or hanging

**Solution**:
```bash
# 1. Increase timeout in config.yaml
tools:
  default_timeout: 60  # seconds (default: 30)

# 2. Check if command is actually hanging
# Run command manually to test

# 3. Use background execution for long tasks
You> Run this in the background: <long-running-command>

# 4. Cancel stuck task
# Ctrl+C in CLI
# Or kill process: pkill -f "<command>"
```

#### Issue: Code execution sandbox errors

**Cause**: Docker not available or not running

**Solution**:
```bash
# 1. Check Docker status
docker --version
docker ps

# 2. Start Docker
sudo systemctl start docker
# Or: sudo service docker start

# 3. Test Docker access
docker run hello-world

# 4. Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login

# 5. Disable sandbox if Docker unavailable (less secure)
# config.yaml:
code_execution:
  use_sandbox: false  # WARNING: Runs code without isolation
```

---

### 7. Performance Issues

#### Issue: High memory usage

**Cause**: Large conversation history, many cached skills, or memory leak

**Solution**:
```bash
# 1. Check memory usage
ps aux | grep python | grep alpha
free -h

# 2. Clear conversation history
You> clear

# 3. Reset skill cache
rm -rf skills/cache/

# 4. Restart server periodically
# Add cron job: 0 3 * * * /path/to/restart_alpha.sh

# 5. Configure memory limits (systemd)
sudo systemctl edit alpha
# Add:
[Service]
MemoryMax=1G
```

#### Issue: Slow startup time

**Cause**: Large database, many skills, or slow disk

**Solution**:
```bash
# 1. Profile startup
time python -m alpha.interface.cli --help

# 2. Vacuum database
sqlite3 data/alpha.db "VACUUM;"

# 3. Disable unused skills
# Edit config.yaml:
skills:
  auto_install: false
  preload: false

# 4. Move data to faster disk (SSD)
mv data /mnt/ssd/alpha_data
ln -s /mnt/ssd/alpha_data data

# 5. Reduce ChromaDB collection size
# Clear old embeddings periodically
```

---

### 8. Workflow Issues

#### Issue: Workflow execution fails

**Cause**: Invalid YAML, missing tools, or step errors

**Solution**:
```bash
# 1. Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('workflow.yaml'))"

# 2. Check workflow definition
You> List all workflows
You> Show details for workflow: <name>

# 3. Test individual steps
# Run each step manually to identify issue

# 4. Check logs for detailed error
grep "workflow" data/alpha.log | tail -20

# 5. Fix common YAML issues
# - Use spaces, not tabs for indentation
# - Quote strings with special characters
# - Ensure proper nesting
```

---

## 🔍 Advanced Diagnostics

### Enable Debug Logging

```bash
# 1. Set environment variable
export ALPHA_LOG_LEVEL=DEBUG

# 2. Or edit config.yaml
logging:
  level: "DEBUG"
  file: "data/alpha.log"

# 3. Restart and check logs
tail -f data/alpha.log
```

### Capture Full Error Trace

```bash
# Run with Python traceback
python -m alpha.interface.cli --debug

# Or catch exceptions in code
try:
    # ... Alpha code ...
except Exception as e:
    import traceback
    traceback.print_exc()
```

### Profile Performance

```bash
# Profile with cProfile
python -m cProfile -o alpha.prof -m alpha.interface.cli

# Analyze results
python -m pstats alpha.prof
# Then: sort cumtime, stats 20

# Memory profiling
pip install memory_profiler
python -m memory_profiler -m alpha.interface.cli
```

---

## 🛠️ Recovery Procedures

### Complete Reset (Last Resort)

**WARNING: This will delete all data including conversation history, tasks, and configurations**

```bash
# 1. Stop all Alpha processes
pkill -9 -f "python.*alpha"

# 2. Backup important data
mkdir backup_$(date +%Y%m%d)
cp -r data/ backup_$(date +%Y%m%d)/
cp config.yaml backup_$(date +%Y%m%d)/

# 3. Remove data directory
rm -rf data/

# 4. Reset virtual environment (optional)
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Recreate data directory
mkdir -p data

# 6. Start fresh
./start.sh
```

### Restore from Backup

```bash
# 1. Stop Alpha
pkill -f "python.*alpha"

# 2. Restore data
cp -r backup_YYYYMMDD/data/ .
cp backup_YYYYMMDD/config.yaml .

# 3. Fix permissions
chmod -R 755 data/

# 4. Restart
./start.sh
```

---

## 📞 Getting Help

### Self-Service Resources

1. **Documentation**: Check [docs/](../docs/) directory
2. **Common Use Cases**: [COMMON_USE_CASES.md](../COMMON_USE_CASES.md)
3. **CLI Reference**: [CLI_COMMAND_REFERENCE.md](CLI_COMMAND_REFERENCE.md)
4. **API Docs**: [docs/API_SETUP.md](../docs/API_SETUP.md)

### Community Support

1. **GitHub Issues**: Report bugs at repository issues page
2. **Discussions**: Ask questions in GitHub Discussions
3. **Logs**: Always include relevant log snippets when asking for help

### Providing Debug Information

When reporting issues, include:

```bash
# 1. System info
uname -a
python3 --version
pip list | grep -E "alpha|anthropic|openai"

# 2. Configuration (redact API keys!)
cat config.yaml | grep -v "api_key"

# 3. Recent logs
tail -100 data/alpha.log

# 4. Error message
# Copy the full error message and stack trace

# 5. Steps to reproduce
# Describe what you did before the error occurred
```

---

## 🎯 Prevention Best Practices

1. **Regular Updates**: Keep Alpha and dependencies updated
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```

2. **Monitor Resources**: Check disk/memory regularly
   ```bash
   df -h data/
   du -sh data/
   ```

3. **Backup Important Data**: Schedule regular backups
   ```bash
   # Add to cron: daily backup
   0 2 * * * cp -r ~/alpha/data ~/backups/alpha_$(date +\%Y\%m\%d)
   ```

4. **Clean Old Data**: Periodically vacuum database
   ```bash
   sqlite3 data/alpha.db "VACUUM;"
   ```

5. **Use Systemd**: For production deployments
   ```bash
   sudo systemctl enable alpha
   sudo systemctl start alpha
   ```

---

**Version**: v1.0.0
**Last Updated**: 2026-02-02
**Maintainer**: Alpha Development Team
