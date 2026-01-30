# CodeExecutionTool - Quick Reference

## Installation & Setup

### 1. Prerequisites
```bash
# Docker must be installed and running
docker --version

# Pull required images
docker pull python:3.12-slim
docker pull node:20-slim
docker pull bash:5.2-alpine
```

### 2. Configuration (`config.yaml`)
```yaml
code_execution:
  enabled: true
  defaults:
    language: python
    timeout: 30
    network_access: false
  security:
    require_approval: true
    scan_code: true
```

## Usage

### From LLM (Automatic)

The LLM can call the tool directly:

```
TOOL: code_execution
PARAMS:
  task: "Calculate factorial of 10"
  language: "python"
```

### From Python Code

```python
from alpha.tools.code_tool import CodeExecutionTool
from alpha.llm.service import LLMService
from alpha.utils.config import load_config

# Initialize
config = load_config()
llm_service = LLMService.from_config(config.llm)
tool = CodeExecutionTool(llm_service, config.dict())

# Execute task
result = await tool.execute(
    task="Calculate the factorial of 10",
    language="python"
)

# Execute code
result = await tool.execute(
    code="print('Hello, World!')",
    language="python",
    require_approval=False
)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | str | None | Task description (required if code not provided) |
| `code` | str | None | Code to execute (required if task not provided) |
| `language` | str | "python" | Programming language (python, javascript, bash) |
| `timeout` | int | 30 | Execution timeout in seconds |
| `allow_network` | bool | False | Enable network access in sandbox |
| `validate` | bool | True | Run validation and security checks |
| `require_approval` | bool | True | Require user approval before execution |

## Examples

### Python
```python
result = await tool.execute(
    task="Calculate the first 10 Fibonacci numbers",
    language="python"
)
```

### JavaScript
```python
result = await tool.execute(
    code="console.log([1,2,3].map(x => x * 2));",
    language="javascript",
    require_approval=False
)
```

### Bash
```python
result = await tool.execute(
    code="echo 'System: ' && uname -a",
    language="bash",
    require_approval=False
)
```

## Return Value

### Success
```python
ToolResult(
    success=True,
    output="Code executed successfully\n\nOutput:\n[execution output]",
    error=None,
    metadata={
        "language": "python",
        "execution_time": 0.123,
        "exit_code": 0,
        "timed_out": False
    }
)
```

### Failure
```python
ToolResult(
    success=False,
    output=None,
    error="Code execution failed: [error message]",
    metadata={
        "language": "python",
        "execution_time": 0.456,
        "exit_code": 1,
        "timed_out": False
    }
)
```

## Troubleshooting

### Docker not available
```
Error: Docker is not available. Code execution requires Docker.
Solution: Install Docker from https://docs.docker.com/get-docker/
```

### Missing parameters
```
Error: Either 'task' or 'code' parameter must be provided
Solution: Provide either task description or code string
```

### Timeout
```
Error: Execution timed out
Solution: Increase timeout parameter or optimize code
```

### Permission denied
```
Error: Permission denied accessing Docker
Solution: Add user to docker group: sudo usermod -aG docker $USER
```

## Security

- Code runs in isolated Docker containers
- Network access disabled by default
- Resource limits enforced (CPU: 50%, Memory: 256MB)
- User approval required by default
- Security scanning enabled by default

## Files

- Implementation: `/alpha/tools/code_tool.py`
- Examples: `/alpha/tools/code_tool_example.py`
- Documentation: `/docs/internal/code_execution_tool_implementation.md`
- Configuration: `/config.yaml`

## Statistics

```python
# Get execution statistics
stats = tool.get_statistics()

print(f"Total Executions: {stats['total_executions']}")
print(f"Success Rate: {stats['success_rate']}%")
```

## Integration

The tool is automatically registered when Alpha starts if:
- `code_execution.enabled` is `true` in config.yaml
- Docker is available on the system

## More Information

- Full documentation: `/docs/internal/code_execution_tool_implementation.md`
- Examples: `/alpha/tools/code_tool_example.py`
- Phase 4 plan: `/docs/internal/phase4_code_execution_implementation_plan.md`
