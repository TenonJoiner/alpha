# Alpha CLI Command Reference
## Quick Reference Guide for Alpha Commands

**Version**: v1.0.0
**Last Updated**: 2026-02-02

---

## Table of Contents

- [Server Management](#server-management)
- [Interactive Chat](#interactive-chat)
- [Task Management](#task-management)
- [Workflow Commands](#workflow-commands)
- [Profile & Personalization](#profile--personalization)
- [Skills Management](#skills-management)
- [System Information](#system-information)

---

## Server Management

### Start Server
```bash
# Start Alpha server in background (daemon mode)
./scripts/start_server.sh [host] [port]

# Default: 0.0.0.0:9000
./scripts/start_server.sh
```

### Check Status
```bash
# Check if server is running
python3 bin/alpha status [--port PORT]

# Example
python3 bin/alpha status --port 9000
```

### Stop Server
```bash
# Gracefully stop the server
python3 bin/alpha stop [--port PORT]

# Example
python3 bin/alpha stop --port 9000
```

---

## Interactive Chat

### Connect to Server
```bash
# WebSocket client connection
./scripts/start_client.sh --server ws://localhost:9000/api/v1/ws/chat

# Using alpha command (if in PATH)
export PATH="$PATH:$(pwd)/bin"
alpha chat --port 9000
```

### Traditional CLI Mode
```bash
# Direct CLI without server
./start.sh

# Or manually
source venv/bin/activate
python -m alpha.interface.cli
```

### Chat Commands

While in chat mode, use these special commands:

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `status` | Check Alpha's system status |
| `clear` | Clear conversation history |
| `exit` or `quit` | Exit Alpha |
| `skills` | Show available skills |
| `profile` | Show user profile |
| `workflows` | List saved workflows |

---

## Task Management

### Task Decomposition

```bash
# Decompose a complex task
You> decompose "Build a weather dashboard with React"

# Check task status
You> task status

# Cancel running task
You> task cancel

# View task history
You> task history
```

**Auto-Detection**: Alpha automatically detects complex tasks and offers decomposition.

---

## Workflow Commands

### Create Workflow

```bash
# Natural language workflow creation
You> create workflow "Daily standup automation"

# Interactive builder
You> workflow builder
```

### List Workflows

```bash
You> workflows list
You> workflows               # Short form
```

### Execute Workflow

```bash
# Execute by name
You> workflow run "daily-standup"

# Execute with parameters
You> workflow run "send-report" --to="team@example.com"
```

### Manage Workflows

```bash
# Show workflow details
You> workflow show "workflow-name"

# Edit workflow
You> workflow edit "workflow-name"

# Delete workflow
You> workflow delete "workflow-name"

# Export workflow
You> workflow export "workflow-name" --file="backup.yaml"

# Import workflow
You> workflow import --file="backup.yaml"
```

---

## Profile & Personalization

### View Profile

```bash
You> profile
You> profile show           # Detailed view
```

### Override Preferences

```bash
# Set verbosity level
You> profile set verbosity detailed
You> profile set verbosity concise

# Set language preference
You> profile set language en
You> profile set language zh
You> profile set language mixed

# Set technical level
You> profile set technical_level expert
You> profile set technical_level beginner
You> profile set technical_level intermediate
```

### Reset Profile

```bash
# Reset specific preference
You> profile reset verbosity

# Reset all preferences
You> profile reset all
```

### Export/Import Profile

```bash
# Export profile
You> profile export --file="my_profile.json"

# Import profile
You> profile import --file="my_profile.json"
```

---

## Skills Management

### List Skills

```bash
You> skills list
You> skills                 # Short form
```

### Search Skills

```bash
You> skills search "data processing"
You> search skill "web scraping"
```

### Skill Details

```bash
You> skills show text-processing
```

### Install/Uninstall Skills

```bash
# Install skill
You> skills install weather-forecast

# Uninstall skill
You> skills uninstall weather-forecast

# Update skill
You> skills update weather-forecast
```

**Note**: Alpha auto-installs skills when needed if `auto_install` is enabled.

---

## System Information

### System Status

```bash
You> status

# Example output:
# ✅ Alpha Server Status
# - Version: v1.0.0
# - Uptime: 2 days, 14 hours
# - Memory: 245 MB / 512 MB
# - Active Tasks: 3
# - Skills Loaded: 12
# - LLM Provider: deepseek-chat
```

### Performance Metrics

```bash
# Show model performance
You> metrics models

# Show skill performance
You> metrics skills

# Show resilience stats
You> metrics resilience
```

### Logs

```bash
# View recent logs
You> logs

# View error logs
You> logs errors

# View specific component
You> logs llm
You> logs tools
You> logs skills
```

---

## Image & Multimodal Commands

### Image Analysis

```bash
# Analyze image
You> analyze error_screenshot.png

# Image with question
You> image diagram.png "Explain this architecture"

# Compare images
You> compare design_a.png design_b.png "Which is better?"
```

### Inline Image Upload

```bash
You> I'm seeing this error [uploads screenshot]. Can you help?
```

**Supported Formats**: PNG, JPEG, GIF, WebP, BMP

---

## Code Execution

### Execute Code

```bash
# Generate and execute code from task
You> execute "calculate fibonacci sequence up to n=20"

# Execute provided code
You> code python "print('Hello, Alpha!')"

# Specify language
You> code javascript "console.log('Hello')"
You> code bash "ls -la"
```

**Security**: Alpha validates and sandboxes all code execution.

---

## Browser Automation

### Navigate & Extract

```bash
# Navigate to URL
You> browse "https://example.com"

# Extract data
You> scrape "https://example.com/products" extract "price, title"

# Fill form
You> browse "https://form.example.com" fill {"name": "Alpha", "email": "alpha@example.com"}

# Take screenshot
You> screenshot "https://example.com" save "screenshot.png"
```

---

## Advanced Features

### Proactive Intelligence

```bash
# Enable/disable proactive suggestions
You> proactive enable
You> proactive disable

# View suggestions
You> suggestions

# View learned patterns
You> patterns
```

### Self-Improvement

```bash
# View learning insights
You> insights

# View improvement suggestions
You> improvements

# Apply improvement
You> apply improvement 1
```

---

## Configuration

### Update Configuration

```bash
# View current config
You> config show

# Set configuration value
You> config set llm.default_provider anthropic
You> config set resilience.enabled true

# Reload configuration
You> config reload
```

---

## Keyboard Shortcuts

When in interactive CLI mode:

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Interrupt current operation |
| `Ctrl+D` | Exit Alpha |
| `↑` / `↓` | Navigate command history |
| `Tab` | Auto-complete (if available) |

---

## Environment Variables

### Required API Keys

```bash
# At least one required
export DEEPSEEK_API_KEY="sk-..."      # Recommended (cost-effective)
export ANTHROPIC_API_KEY="sk-ant-..."  # For Claude models
export OPENAI_API_KEY="sk-..."         # For GPT models
```

### Optional Configuration

```bash
export ALPHA_CONFIG_PATH="./custom_config.yaml"
export ALPHA_DATA_DIR="./custom_data"
export ALPHA_LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

---

## Tips & Best Practices

### 1. Use Task Decomposition for Complex Tasks
```bash
# Instead of:
You> Create a full-stack application with authentication

# Better:
You> decompose "Create a full-stack application with authentication"
# Alpha will break it down into manageable steps
```

### 2. Leverage Workflows for Repetitive Tasks
```bash
# Create once, reuse forever
You> create workflow "Morning routine"
# Then simply:
You> workflow run "morning-routine"
```

### 3. Let Alpha Learn Your Preferences
```bash
# Alpha automatically learns from your interactions
# No need to manually configure preferences
# Just use Alpha naturally, and it adapts!
```

### 4. Use Image Analysis for Debugging
```bash
# When stuck on visual issues:
You> analyze error_screenshot.png "What's wrong with this UI?"
```

### 5. Monitor Performance
```bash
# Regular health checks
You> status
You> metrics models  # See which model is most cost-effective
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check if port is already in use
lsof -i :9000

# Check logs
tail -f logs/alpha-api.log
```

### Can't Connect to Server

```bash
# Verify server is running
python3 bin/alpha status

# Check WebSocket URL
# Should be: ws://localhost:9000/api/v1/ws/chat (not http://)
```

### Skills Not Loading

```bash
# Check skills directory
ls -la skills/

# Reinstall skills
You> skills install --force text-processing
```

### High API Costs

```bash
# Check model usage
You> metrics models

# Switch to cost-effective model
You> config set llm.default_provider deepseek
```

---

## Getting Help

### In-App Help

```bash
You> help              # General help
You> help workflows    # Workflow-specific help
You> help skills       # Skills-specific help
```

### Documentation

- [User Guide](./manual/en/features.md)
- [Workflow Guide](./manual/en/workflow_guide.md)
- [Skills Guide](./manual/en/skills_guide.md)
- [API Documentation](./API_SERVER.md)

### Community

- GitHub Issues: https://github.com/flashspy/alpha/issues
- Discussions: https://github.com/flashspy/alpha/discussions

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v1.0.0 | 2026-02-02 | Production release, 128 features complete |
| v0.10.1 | 2026-02-01 | Client-server architecture, WebSocket API |
| v0.10.0 | 2026-01-31 | Proactive intelligence, benchmarks |
| v0.9.0 | 2026-01-31 | Self-improvement loop |
| v0.8.0 | 2026-01-31 | Browser automation |

---

**Quick Start**: `./scripts/start_server.sh && ./scripts/start_client.sh`

**Need Help?**: Type `help` in Alpha chat or check [documentation](./manual/)

**Report Issues**: https://github.com/flashspy/alpha/issues
