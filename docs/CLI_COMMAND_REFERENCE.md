# Alpha CLI Command Reference

Quick reference card for all Alpha CLI commands and usage patterns.

---

## 🚀 Getting Started

### Start Alpha

```bash
# Interactive mode (traditional - stops when terminal closes)
./start.sh
# or
python -m alpha.interface.cli

# Client-Server mode (recommended for 24/7 operation)
./scripts/start_server.sh 0.0.0.0 9000
./scripts/start_client.sh --server ws://localhost:9000/api/v1/ws/chat
```

### Server Management

```bash
# Check server status
python3 bin/alpha status --port 9000

# Stop server
python3 bin/alpha stop

# View server logs
tail -f nohup.out
```

---

## 💬 Chat Commands

While chatting with Alpha, use these built-in commands:

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show available commands | `help` |
| `status` | Check Alpha's system status | `status` |
| `clear` | Clear conversation history | `clear` |
| `exit` or `quit` | Exit Alpha | `exit` |
| `skills` | List installed skills | `skills` |
| `search skill <query>` | Search for skills in marketplace | `search skill pdf` |
| `workflows` | List available workflows | `workflows` |
| `workflow run <name>` | Execute a workflow | `workflow run daily-briefing` |

---

## 🛠️ Task Management

### Execute Commands

```bash
# Ask Alpha to run shell commands
You> List all Python files in this directory
You> Check my git status
You> Install npm dependencies
```

### Schedule Tasks

```bash
# Cron-based scheduling
You> Schedule a task to run every day at 9am
Alpha> I'll set up a cron schedule: 0 9 * * *

# Interval-based
You> Run this script every 30 minutes
You> Execute this task every 2 hours

# One-time scheduled
You> Remind me to check emails at 3pm today
```

---

## 🔧 Tool Usage

Alpha has built-in tools that are automatically invoked:

### Shell Commands

```bash
You> Run ls -la
You> Execute git status
You> Check disk space with df -h
```

### File Operations

```bash
You> Read the contents of config.yaml
You> Create a new file called notes.txt
You> Delete old_file.log
```

### HTTP Requests

```bash
You> Fetch data from https://api.example.com/users
You> Make a POST request to create a new resource
You> Check if website is up: https://example.com
```

### Web Search

```bash
You> Search for Python async best practices
You> Find the latest React documentation
You> What's the weather in Tokyo?
```

### Calculator

```bash
You> Calculate 15% of 2500
You> Convert 10 kilometers to miles
You> What is sqrt(144)?
```

### Date/Time

```bash
You> What time is it in New York?
You> Convert UTC to PST timezone
You> Calculate days between 2024-01-01 and today
```

### Code Execution

```bash
You> Write a Python script to sort this JSON file
You> Generate JavaScript code to validate email addresses
You> Create a Bash script to backup my documents folder
```

### Browser Automation

```bash
You> Open https://example.com and take a screenshot
You> Fill out the login form on this website
You> Extract all links from this page
```

---

## 🎯 Agent Skills

### Manage Skills

```bash
# List installed skills
You> Show me all installed skills
You> What skills are available?

# Search marketplace
You> Search for PDF skills
You> Find skills related to data analysis

# Use skills
You> Use text-processing to convert this to uppercase
You> Parse this JSON with json-processor
You> Analyze these numbers with data-analyzer
```

### Builtin Skills

Alpha comes with 3 preinstalled skills:

1. **text-processing** - 20+ text operations
   ```bash
   You> Convert this text to uppercase
   You> Extract all email addresses from this file
   You> Count words in document.txt
   ```

2. **json-processor** - JSON manipulation
   ```bash
   You> Parse this JSON string
   You> Format this JSON for readability
   You> Extract the "users" field from this JSON
   ```

3. **data-analyzer** - Statistical analysis
   ```bash
   You> Calculate the mean of these numbers: 10, 20, 30, 40
   You> Find the median and variance
   You> Group this data by category
   ```

---

## 🔄 Workflows

### Create Workflows

```bash
# YAML format
workflow:
  name: "daily-briefing"
  trigger:
    type: "schedule"
    cron: "0 9 * * *"
  steps:
    - tool: "search"
      params:
        query: "tech news today"
    - tool: "shell"
      params:
        command: "echo 'Briefing complete'"
```

### Run Workflows

```bash
You> Run the daily-briefing workflow
You> Execute my morning-routine workflow
You> List all available workflows
```

---

## 🧠 Memory & Personalization

Alpha learns from your interactions:

```bash
# Alpha automatically remembers:
- Your preferences (communication style, tool choices)
- Common tasks and patterns
- Frequently used commands
- Behavioral patterns

# Query memory
You> What did we discuss yesterday about the deployment?
You> Show me my recent tasks
You> What are my preferences for model selection?
```

---

## 📊 System Monitoring

### Check Status

```bash
You> Show system status
You> What's the performance metrics?
You> Display task queue

# Returns:
- Active tasks
- Memory usage
- LLM API costs
- Skill usage statistics
- Model performance metrics
```

### Performance Tracking

```bash
You> Show model performance statistics
You> What's the cost breakdown by model?
You> Display skill usage analytics
```

---

## ⚙️ Configuration

### Model Selection

```bash
# Configured in config.yaml
llm:
  default_provider: "deepseek"  # or "anthropic", "openai"

# Model routing (automatic)
- deepseek-chat: General conversations
- deepseek-coder: Programming tasks
- deepseek-reasoner: Complex reasoning

# Manual override (in chat)
You> Use Claude for this complex analysis task
You> Switch to GPT-4 for this response
```

### Environment Variables

```bash
# Set API keys
export DEEPSEEK_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Configure behavior
export ALPHA_LOG_LEVEL="INFO"
export ALPHA_DATA_DIR="./data"
```

---

## 🆘 Troubleshooting

### Common Issues

```bash
# Check API configuration
./check_api_config.sh

# Test DeepSeek connection
python test_deepseek.py

# Verify database
ls -la data/alpha.db

# Check server status
python3 bin/alpha status

# View logs
tail -f data/alpha.log
journalctl -u alpha -f  # For daemon mode
```

### Reset & Recovery

```bash
# Clear conversation history (in chat)
You> clear

# Reset skill cache
rm -rf skills/cache/

# Recreate database (WARNING: loses history)
rm data/alpha.db
python -m alpha.interface.cli  # Recreates DB
```

---

## 🔐 Security

### Safe Operations

```bash
# Code execution requires approval by default
You> Write and run a Python script
Alpha> [Shows generated code for review]
Alpha> Do you approve execution? (yes/no)

# Disable approval (config.yaml)
code_execution:
  require_approval: false  # Use with caution!
```

### Sandbox Configuration

```bash
# Resource limits (config.yaml)
code_execution:
  timeout: 30  # seconds
  memory_limit: "256m"
  cpu_limit: "0.5"  # 50% of one core
  network_enabled: false  # Disable network access
```

---

## 📚 Additional Resources

- **Full Documentation**: [docs/](docs/)
- **User Guides**: [docs/manual/en/](docs/manual/en/)
- **API Reference**: [docs/API_SETUP.md](docs/API_SETUP.md)
- **Common Use Cases**: [COMMON_USE_CASES.md](COMMON_USE_CASES.md)
- **Troubleshooting**: [README.md#troubleshooting](README.md#troubleshooting)

---

## 🎓 Pro Tips

### Efficiency Hacks

```bash
# 1. Use natural language - Alpha understands context
You> Check if the server is running and restart it if needed

# 2. Combine multiple operations
You> Search for React tutorials, summarize the top 3, and save to notes.txt

# 3. Reference previous context
You> Do the same thing for Vue.js

# 4. Chain tasks with workflows
You> Create a workflow to backup my code, run tests, and deploy if all pass

# 5. Let Alpha learn your style
# Just use it naturally - personalization happens automatically
```

### Power User Features

```bash
# Proactive suggestions
# Alpha learns patterns and suggests tasks:
Alpha> I noticed you usually run tests at 5pm. Should I schedule that?

# Multi-model optimization
# Alpha automatically picks the cheapest model that can handle the task

# Self-healing resilience
# Alpha retries failures with alternative approaches automatically

# Skill evolution
# Alpha discovers and integrates new skills based on your task patterns
```

---

**Version**: v1.0.0
**Last Updated**: 2026-02-02
**Maintainer**: Alpha Development Team
