# Alpha AI Assistant - Features & Usage Guide

## Current Version: 0.4.0

## 核心功能

### 1. 智能多模型选择
- ✅ 自动任务分析和最优模型路由
- ✅ 支持deepseek-chat、deepseek-coder、deepseek-reasoner
- ✅ 任务难度分类(简单、中等、复杂、专家级)
- ✅ 通过智能模型匹配优化成本

**使用方式**:
```yaml
# config.yaml
llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      auto_select_model: true  # 启用自动选择
      default_model: "deepseek-chat"
      models:
        deepseek-chat:
          difficulty_range: ["simple", "medium"]
        deepseek-coder:
          difficulty_range: ["medium", "complex"]
        deepseek-reasoner:
          difficulty_range: ["complex", "expert"]
```

**工作原理**:
- **任务分析**: 分析用户消息中的编程关键词、推理需求、专家主题
- **基于优先级的选择**:
  1. 专家级/复杂推理任务 → deepseek-reasoner
  2. 编程任务 → deepseek-coder
  3. 一般任务 → deepseek-chat

**另见**: [模型选择指南](model_selection.md)

### 2. Agent技能系统
- ✅ 动态技能发现和安装
- ✅ 技能市场集成
- ✅ 版本管理和依赖处理
- ✅ 社区贡献的技能

**使用方式**:
```bash
# 在Alpha CLI中
skills                    # 列出已安装的技能
search skill text        # 搜索技能
```

**在对话中**:
```
You: 将"hello world"转换为大写

Alpha: 我将使用text-processing技能。

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Alpha: 结果是"HELLO WORLD"
```

**架构**:
- **AgentSkill**: 创建技能的基类
- **SkillRegistry**: 管理已安装的技能
- **SkillMarketplace**: 发现和下载技能
- **SkillInstaller**: 安装技能和依赖
- **SkillExecutor**: 执行技能并支持自动安装

**另见**: [技能使用指南](skills_guide.md)

### 3. 内置技能
- ✅ 3个预装技能即开即用
- ✅ 零依赖,纯Python
- ✅ 启动时自动加载

**可用内置技能**:

**text-processing** - 20+文本操作
- 大小写转换: uppercase, lowercase, titlecase, capitalize
- 字符串操作: reverse, trim, strip
- 分割和合并操作
- 提取: 邮箱、网址、数字
- 格式化: truncate, pad

**json-processor** - 8种JSON操作
- parse, stringify, format, minify
- validate, extract(按路径), merge, filter

**data-analyzer** - 17种统计操作
- 基础统计: mean, median, mode, min, max, range, sum, count
- 高级统计: variance, stdev, percentile, quartiles
- 数据操作: group_by, aggregate, sort, filter, summary

**使用方式**:
```python
# 自动可用,无需安装
# 技能在启动时加载
```

### 4. 24/7 持续运行
- ✅ 基于asyncio的异步事件循环
- ✅ 优雅的启动和关闭流程
- ✅ 自动错误恢复机制
- ✅ 健康监控和状态报告

**使用方式**:
```python
from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config

config = load_config('config.yaml')
engine = AlphaEngine(config)
await engine.startup()
await engine.run()  # 持续运行
```

### 2. LLM大模型集成
- ✅ 支持 OpenAI (GPT-4, GPT-3.5)
- ✅ 支持 Anthropic (Claude)
- ✅ 流式响应
- ✅ 多provider自动切换

**使用方式**:
```python
from alpha.llm.service import LLMService, Message

llm = LLMService.from_config(config.llm)

messages = [
    Message(role="user", content="Hello!")
]

# 普通完成
response = await llm.complete(messages)
print(response.content)

# 流式响应
async for chunk in llm.stream_complete(messages):
    print(chunk, end='')
```

### 3. 工具调用系统
- ✅ Shell命令执行
- ✅ 文件操作 (读/写/删除/列表)
- ✅ Web搜索 (DuckDuckGo API集成)
- ✅ HTTP请求 (GET/POST/PUT/DELETE/PATCH)
- ✅ 日期时间操作 (格式化/解析/时区转换)
- ✅ 计算器 (数学表达式/单位转换)
- ✅ 可扩展的插件架构

**使用方式**:
```python
from alpha.tools.registry import create_default_registry

registry = create_default_registry()

# 执行shell命令
result = await registry.execute_tool(
    "shell",
    command="ls -la"
)
print(result.output)

# 文件操作
result = await registry.execute_tool(
    "file",
    operation="write",
    path="/tmp/test.txt",
    content="Hello World"
)
```

**可用工具**:
| 工具名 | 功能 | 参数 |
|--------|------|------|
| shell | 执行shell命令 | command, timeout |
| file | 文件操作 | operation(read/write/append/delete/list), path, content |
| search | Web搜索 (DuckDuckGo) | query, limit |
| http | HTTP请求 | url, method, headers, params, json, timeout |
| datetime | 日期时间操作 | operation(now/format/parse/add/subtract/diff/timezone_convert), datetime_str, timezone, format, duration |
| calculator | 数学计算和单位转换 | operation(calculate/convert_unit), expression, value, from_unit, to_unit |

#### 工具使用示例

**HTTP工具 - API请求**:
```python
# GET请求
result = await registry.execute_tool(
    "http",
    url="https://api.github.com/users/octocat",
    method="GET"
)

# POST JSON数据
result = await registry.execute_tool(
    "http",
    url="https://httpbin.org/post",
    method="POST",
    json={"key": "value"}
)
```

**DateTime工具 - 时间操作**:
```python
# 获取当前时间
result = await registry.execute_tool(
    "datetime",
    operation="now",
    timezone="Asia/Shanghai"
)

# 时区转换
result = await registry.execute_tool(
    "datetime",
    operation="timezone_convert",
    datetime_str="2026-01-29T10:00:00Z",
    timezone="America/New_York"
)

# 计算日期差
result = await registry.execute_tool(
    "datetime",
    operation="diff",
    datetime1="2026-01-01",
    datetime2="2026-01-29"
)
```

**Calculator工具 - 计算**:
```python
# 数学表达式
result = await registry.execute_tool(
    "calculator",
    operation="calculate",
    expression="sqrt(16) + pi * 2"
)

# 单位转换
result = await registry.execute_tool(
    "calculator",
    operation="convert_unit",
    value=100,
    from_unit="km",
    to_unit="mi"
)
```

### 4. 任务管理
- ✅ 异步任务执行
- ✅ 优先级调度 (LOW/NORMAL/HIGH/URGENT)
- ✅ 任务状态跟踪
- ✅ 并发任务支持

**使用方式**:
```python
from alpha.tasks.manager import TaskManager, TaskPriority

manager = TaskManager(event_bus)
await manager.initialize()

# 创建任务
task = await manager.create_task(
    name="Download File",
    description="Download report.pdf",
    priority=TaskPriority.HIGH
)

# 执行任务
async def executor(task):
    # 执行具体逻辑
    return "completed"

await manager.execute_task(task.id, executor)
```

### 5. 记忆系统
- ✅ 对话历史记录
- ✅ 任务执行日志
- ✅ 系统事件记录
- ✅ 知识库存储

**使用方式**:
```python
from alpha.memory.manager import MemoryManager

memory = MemoryManager("data/alpha.db")
await memory.initialize()

# 存储对话
await memory.add_conversation(
    role="user",
    content="Hello"
)

# 获取历史
history = await memory.get_conversation_history(limit=10)

# 知识库
await memory.set_knowledge("user_name", "Alice")
name = await memory.get_knowledge("user_name")
```

### 6. 事件系统
- ✅ Pub-Sub模式
- ✅ 异步事件处理
- ✅ 多个handler支持
- ✅ 错误隔离

**使用方式**:
```python
from alpha.events.bus import EventBus, EventType

bus = EventBus()
await bus.initialize()

# 订阅事件
async def on_task_completed(event):
    print(f"Task {event.data['task_id']} completed")

bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)

# 发布事件
await bus.publish_event(
    EventType.TASK_COMPLETED,
    {"task_id": "123", "result": "success"}
)
```

### 7. CLI交互界面
- ✅ 交互式对话
- ✅ 流式响应显示
- ✅ Rich终端UI
- ✅ 命令支持 (help/status/clear/quit)

**使用方式**:
```bash
python -m alpha.interface.cli
```

**支持的命令**:
- `help` - 显示帮助信息
- `status` - 显示系统状态
- `clear` - 清空对话历史
- `quit/exit` - 退出程序

## 配置说明

### config.yaml 结构

```yaml
alpha:
  name: "Alpha Assistant"
  version: "0.1.0"

llm:
  default_provider: "openai"  # 默认使用的provider
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"  # 从环境变量读取
      model: "gpt-4"
      max_tokens: 4096
      temperature: 0.7
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-3-sonnet-20240229"

memory:
  database: "data/alpha.db"      # SQLite数据库路径
  vector_db: "data/vectors"      # 向量数据库路径(未来)

tools:
  enabled:
    - shell
    - file
    - search
  sandbox: true  # 沙箱模式(未来)

interface:
  cli:
    enabled: true
  api:
    enabled: false
    host: "0.0.0.0"
    port: 8000
```

## 使用场景示例

### 场景1: 文件处理
```
You> 帮我创建一个名为notes.txt的文件,内容是"Meeting at 3pm"

Alpha> TOOL: file
PARAMS: {"operation": "write", "path": "notes.txt", "content": "Meeting at 3pm"}

Executing tool: file
Tool succeeded: Written 15 bytes to notes.txt

Done! I've created notes.txt with your meeting reminder.
```

### 场景2: 系统命令
```
You> 检查当前目录的磁盘使用情况

Alpha> TOOL: shell
PARAMS: {"command": "du -sh ."}

Executing tool: shell
Tool succeeded: 2.4M    .

The current directory is using 2.4 megabytes of disk space.
```

### 场景3: 信息查询
```
You> 搜索Python异步编程的最佳实践

Alpha> TOOL: search
PARAMS: {"query": "Python asyncio best practices"}

[Search results displayed]

Based on the search results, here are the key best practices for Python asyncio:
1. Use async/await syntax instead of callbacks
2. Avoid blocking operations in async functions
...
```

## 数据存储

### 数据库结构 (SQLite)

**conversations** - 对话历史
- id, role, content, timestamp, metadata

**tasks** - 任务记录
- id, name, description, status, priority, created_at, started_at, completed_at, result, error, metadata

**system_events** - 系统事件
- id, event_type, data, timestamp

**knowledge** - 知识库
- id, key, value, category, created_at, updated_at

### 数据目录
```
data/
├── alpha.db        # SQLite数据库
└── vectors/        # 向量数据库(未来)

logs/
└── alpha.log       # 日志文件
```

## 扩展开发

### 创建自定义工具

```python
from alpha.tools.registry import Tool, ToolResult

class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom",
            description="My custom tool"
        )

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        result = do_something()

        return ToolResult(
            success=True,
            output=result
        )

# 注册工具
registry.register(CustomTool())
```

### 添加事件处理器

```python
async def my_handler(event):
    # 处理事件
    pass

event_bus.subscribe(EventType.CUSTOM_EVENT, my_handler)
```

## 性能指标

- **启动时间**: < 2秒
- **LLM响应延迟**: 取决于provider (通常1-5秒)
- **Shell工具执行**: < 1秒(简单命令)
- **数据库查询**: < 100ms
- **内存占用**: ~50-100MB (基础运行)

## 安全注意事项

⚠️ **重要**: 当前版本的安全限制
1. Shell工具在当前用户权限下执行,无沙箱隔离
2. 文件操作可访问整个文件系统
3. API密钥存储在配置文件中
4. 无用户认证机制

**建议**:
- 仅在受信任环境中使用
- 限制文件和shell访问权限
- 使用环境变量存储敏感信息
- 定期审查执行日志

## 故障排查

### 常见问题

**1. ModuleNotFoundError**
```bash
# 确保在虚拟环境中
source venv/bin/activate
pip install -r requirements.txt
```

**2. API密钥错误**
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 或在config.yaml中直接设置
```

**3. 数据库锁定**
```bash
# 删除锁定的数据库
rm data/alpha.db
# 重新启动alpha
```

**4. 端口占用 (API模式)**
```bash
# 修改config.yaml中的端口
interface:
  api:
    port: 8001
```

## 后续规划 (Phase 2+)

### 即将推出的功能

- [ ] 浏览器自动化 (Playwright)
- [ ] 代码执行沙箱
- [ ] 向量数据库集成
- [ ] 语义搜索
- [ ] RESTful API接口
- [ ] WebSocket实时通信
- [ ] 定时任务调度
- [ ] 自主任务规划
- [ ] 多用户支持
- [ ] Web界面

---

**版本**: v0.4.0
**更新日期**: 2026-01-29
**状态**: 生产就绪 - 智能多模型选择 ✅
