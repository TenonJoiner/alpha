# Alpha AI Assistant - Features & Usage Guide

## Current Version: 0.4.0

## Core Features

### 1. Intelligent Multi-Model Selection
- ✅ Automatic task analysis and optimal model routing
- ✅ Support for deepseek-chat, deepseek-coder, deepseek-reasoner
- ✅ Task difficulty classification (simple, medium, complex, expert)
- ✅ Cost optimization through smart model matching

**Usage**:
```yaml
# config.yaml
llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      auto_select_model: true  # Enable automatic selection
      default_model: "deepseek-chat"
      models:
        deepseek-chat:
          difficulty_range: ["simple", "medium"]
        deepseek-coder:
          difficulty_range: ["medium", "complex"]
        deepseek-reasoner:
          difficulty_range: ["complex", "expert"]
```

**How It Works**:
- **Task Analysis**: Analyzes user messages for coding keywords, reasoning requirements, expert topics
- **Priority-Based Selection**:
  1. Expert/complex reasoning tasks → deepseek-reasoner
  2. Coding tasks → deepseek-coder
  3. General tasks → deepseek-chat

**See Also**: [Model Selection Guide](model_selection.md)

### 2. Agent Skill System
- ✅ Dynamic skill discovery and installation
- ✅ Skill marketplace integration
- ✅ Version management and dependencies
- ✅ Community-contributed skills

**Usage**:
```bash
# In Alpha CLI
skills                    # List installed skills
search skill text        # Search for skills
```

**In Conversation**:
```
You: Convert "hello world" to uppercase

Alpha: I'll use the text-processing skill for this.

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Alpha: The result is "HELLO WORLD"
```

**Architecture**:
- **AgentSkill**: Base class for creating skills
- **SkillRegistry**: Manages installed skills
- **SkillMarketplace**: Discovers and downloads skills
- **SkillInstaller**: Installs skills and dependencies
- **SkillExecutor**: Executes skills with auto-install

**See Also**: [Skills Usage Guide](skills_guide.md)

### 3. Builtin Skills
- ✅ 3 preinstalled skills ready to use immediately
- ✅ Zero dependencies, pure Python
- ✅ Automatic loading at startup

**Available Builtin Skills**:

**text-processing** - 20+ text operations
- Case transformations: uppercase, lowercase, titlecase, capitalize
- String operations: reverse, trim, strip
- Split and join operations
- Extraction: emails, URLs, numbers
- Formatting: truncate, pad

**json-processor** - 8 JSON operations
- parse, stringify, format, minify
- validate, extract (by path), merge, filter

**data-analyzer** - 17 statistical operations
- Basic stats: mean, median, mode, min, max, range, sum, count
- Advanced stats: variance, stdev, percentile, quartiles
- Data ops: group_by, aggregate, sort, filter, summary

**Usage**:
```python
# Automatically available, no installation needed
# Skills are loaded at startup
```

### 4. 24/7 Continuous Operation
- ✅ Asyncio-based async event loop
- ✅ Graceful startup and shutdown process
- ✅ Automatic error recovery mechanism
- ✅ Health monitoring and status reporting

**Usage**:
```python
from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config

config = load_config('config.yaml')
engine = AlphaEngine(config)
await engine.startup()
await engine.run()  # Continuous operation
```

### 2. LLM Integration
- ✅ Support for OpenAI (GPT-4, GPT-3.5)
- ✅ Support for Anthropic (Claude)
- ✅ Streaming responses
- ✅ Automatic multi-provider switching

**Usage**:
```python
from alpha.llm.service import LLMService, Message

llm = LLMService.from_config(config.llm)

messages = [
    Message(role="user", content="Hello!")
]

# Regular completion
response = await llm.complete(messages)
print(response.content)

# Streaming response
async for chunk in llm.stream_complete(messages):
    print(chunk, end='')
```

### 3. Tool System
- ✅ Shell command execution
- ✅ File operations (read/write/delete/list)
- ✅ Web search (DuckDuckGo API integration)
- ✅ HTTP requests (GET/POST/PUT/DELETE/PATCH)
- ✅ DateTime operations (format/parse/timezone conversion)
- ✅ Calculator (math expressions/unit conversions)
- ✅ Extensible plugin architecture

**Usage**:
```python
from alpha.tools.registry import create_default_registry

registry = create_default_registry()

# Execute shell command
result = await registry.execute_tool(
    "shell",
    command="ls -la"
)
print(result.output)

# File operations
result = await registry.execute_tool(
    "file",
    operation="write",
    path="/tmp/test.txt",
    content="Hello World"
)
```

**Available Tools**:
| Tool | Function | Parameters |
|------|----------|------------|
| shell | Execute shell commands | command, timeout |
| file | File operations | operation(read/write/append/delete/list), path, content |
| search | Web search (DuckDuckGo) | query, limit |
| http | HTTP requests | url, method, headers, params, json, timeout |
| datetime | DateTime operations | operation(now/format/parse/add/subtract/diff/timezone_convert), datetime_str, timezone, format, duration |
| calculator | Math calculations and unit conversions | operation(calculate/convert_unit), expression, value, from_unit, to_unit |

#### Tool Usage Examples

**HTTP Tool - API Requests**:
```python
# GET request
result = await registry.execute_tool(
    "http",
    url="https://api.github.com/users/octocat",
    method="GET"
)

# POST JSON data
result = await registry.execute_tool(
    "http",
    url="https://httpbin.org/post",
    method="POST",
    json={"key": "value"}
)
```

**DateTime Tool - Time Operations**:
```python
# Get current time
result = await registry.execute_tool(
    "datetime",
    operation="now",
    timezone="Asia/Shanghai"
)

# Timezone conversion
result = await registry.execute_tool(
    "datetime",
    operation="timezone_convert",
    datetime_str="2026-01-29T10:00:00Z",
    timezone="America/New_York"
)

# Calculate date difference
result = await registry.execute_tool(
    "datetime",
    operation="diff",
    datetime1="2026-01-01",
    datetime2="2026-01-29"
)
```

**Calculator Tool - Calculations**:
```python
# Math expression
result = await registry.execute_tool(
    "calculator",
    operation="calculate",
    expression="sqrt(16) + pi * 2"
)

# Unit conversion
result = await registry.execute_tool(
    "calculator",
    operation="convert_unit",
    value=100,
    from_unit="km",
    to_unit="mi"
)
```

### 4. Task Management
- ✅ Async task execution
- ✅ Priority scheduling (LOW/NORMAL/HIGH/URGENT)
- ✅ Task status tracking
- ✅ Concurrent task support

**Usage**:
```python
from alpha.tasks.manager import TaskManager, TaskPriority

manager = TaskManager(event_bus)
await manager.initialize()

# Create task
task = await manager.create_task(
    name="Download File",
    description="Download report.pdf",
    priority=TaskPriority.HIGH
)

# Execute task
async def executor(task):
    # Implement specific logic
    return "completed"

await manager.execute_task(task.id, executor)
```

### 5. Memory System
- ✅ Conversation history logging
- ✅ Task execution logs
- ✅ System event recording
- ✅ Knowledge base storage

**Usage**:
```python
from alpha.memory.manager import MemoryManager

memory = MemoryManager("data/alpha.db")
await memory.initialize()

# Store conversation
await memory.add_conversation(
    role="user",
    content="Hello"
)

# Get history
history = await memory.get_conversation_history(limit=10)

# Knowledge base
await memory.set_knowledge("user_name", "Alice")
name = await memory.get_knowledge("user_name")
```

### 6. Event System
- ✅ Pub-Sub pattern
- ✅ Async event processing
- ✅ Multiple handler support
- ✅ Error isolation

**Usage**:
```python
from alpha.events.bus import EventBus, EventType

bus = EventBus()
await bus.initialize()

# Subscribe to events
async def on_task_completed(event):
    print(f"Task {event.data['task_id']} completed")

bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)

# Publish events
await bus.publish_event(
    EventType.TASK_COMPLETED,
    {"task_id": "123", "result": "success"}
)
```

### 7. CLI Interactive Interface
- ✅ Interactive conversation
- ✅ Streaming response display
- ✅ Rich terminal UI
- ✅ Command support (help/status/clear/quit)

**Usage**:
```bash
python -m alpha.interface.cli
```

**Supported Commands**:
- `help` - Display help information
- `status` - Show system status
- `clear` - Clear conversation history
- `quit/exit` - Exit program

## Configuration

### config.yaml Structure

```yaml
alpha:
  name: "Alpha Assistant"
  version: "0.1.0"

llm:
  default_provider: "openai"  # Default provider to use
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"  # Read from environment variable
      model: "gpt-4"
      max_tokens: 4096
      temperature: 0.7
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-3-sonnet-20240229"

memory:
  database: "data/alpha.db"      # SQLite database path
  vector_db: "data/vectors"      # Vector database path (future)

tools:
  enabled:
    - shell
    - file
    - search
  sandbox: true  # Sandbox mode (future)

interface:
  cli:
    enabled: true
  api:
    enabled: false
    host: "0.0.0.0"
    port: 8000
```

## Usage Scenarios

### Scenario 1: File Processing
```
You> Create a file named notes.txt with content "Meeting at 3pm"

Alpha> TOOL: file
PARAMS: {"operation": "write", "path": "notes.txt", "content": "Meeting at 3pm"}

Executing tool: file
Tool succeeded: Written 15 bytes to notes.txt

Done! I've created notes.txt with your meeting reminder.
```

### Scenario 2: System Commands
```
You> Check disk usage of current directory

Alpha> TOOL: shell
PARAMS: {"command": "du -sh ."}

Executing tool: shell
Tool succeeded: 2.4M    .

The current directory is using 2.4 megabytes of disk space.
```

### Scenario 3: Information Search
```
You> Search for Python async programming best practices

Alpha> TOOL: search
PARAMS: {"query": "Python asyncio best practices"}

[Search results displayed]

Based on the search results, here are the key best practices for Python asyncio:
1. Use async/await syntax instead of callbacks
2. Avoid blocking operations in async functions
...
```

## Data Storage

### Database Structure (SQLite)

**conversations** - Conversation history
- id, role, content, timestamp, metadata

**tasks** - Task records
- id, name, description, status, priority, created_at, started_at, completed_at, result, error, metadata

**system_events** - System events
- id, event_type, data, timestamp

**knowledge** - Knowledge base
- id, key, value, category, created_at, updated_at

### Data Directory
```
data/
├── alpha.db        # SQLite database
└── vectors/        # Vector database (future)

logs/
└── alpha.log       # Log files
```

## Extension Development

### Creating Custom Tools

```python
from alpha.tools.registry import Tool, ToolResult

class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom",
            description="My custom tool"
        )

    async def execute(self, **kwargs) -> ToolResult:
        # Implement tool logic
        result = do_something()

        return ToolResult(
            success=True,
            output=result
        )

# Register tool
registry.register(CustomTool())
```

### Adding Event Handlers

```python
async def my_handler(event):
    # Handle event
    pass

event_bus.subscribe(EventType.CUSTOM_EVENT, my_handler)
```

## Performance Metrics

- **Startup Time**: < 2 seconds
- **LLM Response Latency**: Depends on provider (typically 1-5 seconds)
- **Shell Tool Execution**: < 1 second (simple commands)
- **Database Queries**: < 100ms
- **Memory Usage**: ~50-100MB (base operation)

## Security Considerations

⚠️ **Important**: Security limitations in current version
1. Shell tool executes with current user permissions, no sandbox isolation
2. File operations can access entire file system
3. API keys stored in configuration files
4. No user authentication mechanism

**Recommendations**:
- Use only in trusted environments
- Limit file and shell access permissions
- Use environment variables to store sensitive information
- Regularly review execution logs

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**2. API Key Errors**
```bash
# Check environment variables
echo $OPENAI_API_KEY

# Or set directly in config.yaml
```

**3. Database Locked**
```bash
# Delete locked database
rm data/alpha.db
# Restart alpha
```

**4. Port in Use (API mode)**
```bash
# Modify port in config.yaml
interface:
  api:
    port: 8001
```

## Future Plans (Phase 2+)

### Upcoming Features

- [ ] Browser automation (Playwright)
- [ ] Code execution sandbox
- [ ] Vector database integration
- [ ] Semantic search
- [ ] RESTful API interface
- [ ] WebSocket real-time communication
- [ ] Scheduled task scheduling
- [ ] Autonomous task planning
- [ ] Multi-user support
- [ ] Web interface

---

**Version**: v0.4.0
**Last Updated**: 2026-01-29
**Status**: Production Ready - Intelligent Multi-Model Selection ✅
