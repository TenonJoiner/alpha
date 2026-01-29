# Alpha: an AI-defined and implemented robot
build by `cat make_alpha.md | claude --dangerously-skip-permissions`

English | [简体中文](README.zh.md)

A personal super AI assistant that runs 24/7 to help you accomplish various tasks.

## What is Alpha?

Alpha is your intelligent personal assistant powered by advanced AI models. It can:

- 💬 **Chat naturally** - Have conversations and get help with daily tasks
- 🔧 **Execute tasks** - Run shell commands, manage files, make HTTP requests
- 📅 **Schedule tasks** - Set up automated tasks with cron-like scheduling
- 🧮 **Calculate & convert** - Solve math problems and convert units
- 🌐 **Search the web** - Find information online
- ⏰ **Handle dates/times** - Work with dates, times, and timezones
- 🤖 **Multi-AI support** - Choose from DeepSeek, Claude, or GPT-4
- 🧠 **Intelligent Model Selection** - Automatic task analysis and optimal model routing
- 🎯 **Dynamic Skills** - Expand capabilities with auto-installable skills
- ⚡ **Builtin Skills** - 3 preinstalled skills ready to use (text, JSON, data processing)

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/alpha.git
cd alpha

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data
```

### 2. Configure API Key

Choose one AI provider (DeepSeek is recommended for cost-effectiveness):

```bash
# Option 1: DeepSeek (Recommended - Most cost-effective)
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Option 2: Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Option 3: OpenAI GPT
export OPENAI_API_KEY="your-openai-api-key"
```

**Get API Keys:**
- DeepSeek: https://platform.deepseek.com/api_keys
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

### 3. Start Alpha

```bash
# Quick start
./start.sh

# Or manually
python -m alpha.interface.cli
```

## Usage Examples

### Basic Conversation

```
You> What's the weather in Beijing?
Alpha> I'll search for the current weather in Beijing for you.
[Shows weather information]

You> Calculate 15% of 2500
Alpha> The result is: 375.0

You> What files are in this directory?
Alpha> [Lists all files in current directory]
```

### Available Commands

While chatting with Alpha, you can use these commands:

- `help` - Show available commands
- `status` - Check Alpha's system status
- `clear` - Clear conversation history
- `exit` or `quit` - Exit Alpha

## AI Provider Comparison

Alpha supports three AI providers. Choose based on your needs:

| Feature | DeepSeek | Claude | GPT-4 |
|---------|----------|--------|-------|
| **Cost** | 🏆 Best | Good | Expensive |
| **Speed** | Very Fast | Fast | Medium |
| **Chinese Support** | Excellent | Good | Fair |
| **Code Generation** | Very Good | Excellent | Very Good |
| **Reasoning** | Excellent | Excellent | Very Good |
| **Best For** | Daily use, cost-sensitive | Complex tasks, coding | General tasks |

### Pricing Comparison

Cost per 1 million tokens:

| Provider | Input | Output | **Total** |
|----------|-------|--------|-----------|
| **DeepSeek** | $0.14 | $0.28 | **$0.42** 🏆 |
| Claude Sonnet | $3.00 | $15.00 | $18.00 |
| GPT-4 | $5.00 | $15.00 | $20.00 |

💡 **DeepSeek saves you 40-50x on API costs!**

### Switching Providers

Edit `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"  # Change to: anthropic, openai, or deepseek
```

## Available Tools

Alpha comes with powerful built-in tools:

| Tool | What it does | Example Use |
|------|-------------|-------------|
| **Shell** | Execute terminal commands | `ls`, `git status`, `npm install` |
| **File** | Read/write/manage files | Create, edit, delete files |
| **HTTP** | Make web requests | Call APIs, download content |
| **Search** | Search the web | Find information online |
| **DateTime** | Handle dates/times | Convert timezones, calculate durations |
| **Calculator** | Math & unit conversion | `sqrt(144)`, convert 10km to miles |

## Task Scheduling

Schedule Alpha to run tasks automatically:

```
You> Schedule a task to check my email every morning at 9am
Alpha> I'll set up a scheduled task for you...
[Creates cron schedule: 0 9 * * *]
```

Scheduling formats:
- **Cron**: `0 9 * * *` (every day at 9am)
- **Interval**: Every 30 minutes, every 2 hours
- **One-time**: At specific date and time

## Release Notes

### v0.4.0 (Current) - Intelligent Multi-Model Selection
**Release Date**: 2026-01-29

**New Features:**
- ✨ **Intelligent Model Selection** - Automatic task analysis and optimal model routing
  - Support for deepseek-chat, deepseek-coder, deepseek-reasoner
  - Task difficulty analysis (simple, medium, complex, expert)
  - Automatic model matching based on task characteristics
  - Optimized for cost and performance
- 📊 **Task Analyzer** - Advanced task characteristic detection
  - Coding task detection
  - Reasoning requirement analysis
  - Expert-level topic identification
- 🎯 **Smart Model Routing** - Priority-based model selection
  - deepseek-reasoner for complex reasoning and expert-level tasks
  - deepseek-coder for programming tasks
  - deepseek-chat for general conversations

**Documentation:**
- [Multi-Model Selection Guide](docs/manual/en/model_selection.md)
- [Model Selection Configuration](DEEPSEEK_MODELS.md)

### v0.3.1 - Builtin Skills
**Release Date**: 2026-01-29

**New Features:**
- ✨ **3 Preinstalled Builtin Skills** - Ready to use immediately
  - **text-processing** - 20+ text operations (uppercase, lowercase, extract emails/URLs, etc.)
  - **json-processor** - 8 JSON operations (parse, format, validate, extract, merge)
  - **data-analyzer** - 17 statistical operations (mean, median, variance, group_by, etc.)
- ⚡ **Automatic Preinstallation** - Skills loaded at startup, no configuration needed
- 📦 **Zero Dependencies** - Pure Python implementations, work offline
- 🔄 **Visual Feedback** - Loading spinner and status display during execution

**Documentation:**
- [Builtin Skills Reference](docs/BUILTIN_SKILLS.md)
- Complete usage examples for all operations

### v0.3.0 - Agent Skill System
**Release Date**: 2026-01-29

**New Features:**
- ✨ **Dynamic Skill System** - Expand Alpha's capabilities on-demand
  - Auto-discovery and auto-installation of skills
  - Skill marketplace integration
  - Version management and dependencies
- 🔍 **Skill Discovery** - Search and browse available skills
- 📦 **Skill Management** - Install, update, and remove skills
- 🏪 **Skill Marketplace** - Access community-contributed skills
- 🎨 **CLI Integration** - New `skills` and `search skill` commands

**Architecture:**
- AgentSkill base class for creating custom skills
- SkillRegistry for lifecycle management
- SkillMarketplace for discovery
- SkillInstaller for dependencies
- SkillExecutor with auto-install support

**Documentation:**
- [Agent Skills Documentation](docs/AGENT_SKILLS.md)
- [Quick Start Guide](docs/AGENT_SKILLS_QUICKSTART.md)
- [Skills Usage Guide](docs/manual/en/skills_guide.md)

### v0.2.0 - Task Scheduling & Enhanced Tools
**Release Date**: 2026-01-29

**New Features:**
- ✨ **Task Scheduler** - Schedule tasks with cron expressions, intervals, or one-time execution
- ✨ **HTTP Tool** - Make API requests with full HTTP methods support (GET, POST, PUT, DELETE)
- ✨ **DateTime Tool** - Advanced date/time operations with timezone support
- ✨ **Calculator Tool** - Safe math evaluation with unit conversions (length, weight, temperature, data)
- 🔍 **Enhanced Search** - Real web search via DuckDuckGo API
- 🎨 **Cleaner Interface** - Tool execution details hidden from chat (shows only results)

**Improvements:**
- Multi-format parameter support (JSON and YAML)
- Better error handling and timeouts
- Improved API configuration with fallback support

### v0.1.1 - Multi-Provider Support
**Release Date**: 2026-01-29

**New Features:**
- ✨ **DeepSeek Integration** - Most cost-effective AI provider (40-50x cheaper)
- ✨ **Multi-Provider System** - Easy switching between DeepSeek, Claude, and GPT-4
- 🔧 **Custom API Endpoints** - Support for self-hosted or proxy APIs

**Improvements:**
- Environment variable fallback mechanism
- Improved configuration validation
- Better API error messages

### v0.1.0 - Initial Release
**Release Date**: 2026-01-28

**Core Features:**
- 💬 Interactive CLI chat interface
- 🤖 AI-powered task execution
- 🔧 Basic tools (Shell, File, Search)
- 🧠 Conversation memory
- ⚡ Async task management
- 📝 Configuration system

## Troubleshooting

### "Module not found" errors

Make sure you're in the virtual environment:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API key not configured" errors

Check if your API key is set:

```bash
# Check which keys are set
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# If empty, export your key
export DEEPSEEK_API_KEY="your-key-here"
```

### Test your configuration

```bash
# Check API configuration
./check_api_config.sh

# Test DeepSeek connection
python test_deepseek.py
```

### Database errors

```bash
# Create data directory if missing
mkdir -p data

# Check permissions
ls -la data/
```

## Documentation

### User Guides
- [Quick Start Guide](docs/manual/en/quickstart.md) - Get started in 5 minutes
- [Features Guide](docs/manual/en/features.md) - Complete feature documentation
- [Model Selection Guide](docs/manual/en/model_selection.md) - Intelligent multi-model selection
- [Skills Usage Guide](docs/manual/en/skills_guide.md) - Dynamic skill system
- [API Setup Guide](docs/API_SETUP.md) - Configure AI providers
- [Tool Usage Guide](docs/TOOL_USAGE_GUIDE.md) - How to use each tool

### Technical Documentation
- [Agent Skills System](docs/AGENT_SKILLS.md) - Technical documentation
- [Builtin Skills Reference](docs/BUILTIN_SKILLS.md) - Preinstalled skills
- [Multi-Model Selection](DEEPSEEK_MODELS.md) - DeepSeek models configuration

### API Provider Guides
- [DeepSeek Setup](docs/DEEPSEEK_GUIDE.md) - DeepSeek configuration
- [Anthropic Setup](docs/manual/en/anthropic_config.md) - Claude configuration

### 中文文档
- [快速开始](docs/manual/zh/quickstart.md)
- [功能说明](docs/manual/zh/features.md)
- [模型选择指南](docs/manual/zh/model_selection.md)
- [技能使用指南](docs/manual/zh/skills_guide.md)
- [API配置](docs/API_SETUP.md)

## Frequently Asked Questions

**Q: Which AI provider should I choose?**
A: For most users, DeepSeek is recommended due to its excellent cost-effectiveness and Chinese language support. Use Claude for complex coding tasks.

**Q: Can I use Alpha without an internet connection?**
A: Alpha requires an internet connection to communicate with AI providers. Some tools (like Calculator and DateTime) work offline.

**Q: Is my data private?**
A: All conversations are stored locally in `data/alpha.db`. API providers (DeepSeek, Anthropic, OpenAI) process your messages according to their privacy policies.

**Q: Can I schedule recurring tasks?**
A: Yes! Use cron expressions or interval-based scheduling. Example: "Schedule this task to run every Monday at 10am"

**Q: How much does it cost to use Alpha?**
A: Alpha itself is free. You only pay for API usage:
- DeepSeek: ~$0.42 per million tokens
- Claude: ~$18 per million tokens
- GPT-4: ~$20 per million tokens

## Getting Help

- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/yourusername/alpha/issues)
- 💬 [Discussions](https://github.com/yourusername/alpha/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Current Version**: v0.4.0
**Status**: Production Ready
**Default AI Provider**: DeepSeek (Most Cost-Effective)
