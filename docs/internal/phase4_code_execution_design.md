# Phase 4.1: Code Generation and Safe Execution System
## Design Document

**Date**: 2026-01-30
**Status**: In Development
**Requirements**: REQ-4.1, REQ-4.2, REQ-4.3

---

## Overview

Implement autonomous code generation and safe execution capability, enabling Alpha to write, test, and execute custom code when existing tools are insufficient.

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Alpha Code Execution System                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │     LLM      │──▶│    Code      │──▶│   Syntax     │   │
│  │  Generator   │   │  Generator   │   │  Validator   │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│         │                                      │            │
│         ▼                                      ▼            │
│  ┌──────────────────────────────────────────────────┐      │
│  │          Code Execution Sandbox                   │      │
│  │  ┌────────────────────────────────────────────┐  │      │
│  │  │       Docker Container (Isolated)          │  │      │
│  │  │  ┌────────────────────────────────────┐   │  │      │
│  │  │  │  Python / JavaScript / Bash        │   │  │      │
│  │  │  │  Resource Limits (CPU/Mem/Time)    │   │  │      │
│  │  │  │  Network Isolation                 │   │  │      │
│  │  │  │  File System Restrictions          │   │  │      │
│  │  │  └────────────────────────────────────┘   │  │      │
│  │  └────────────────────────────────────────────┘  │      │
│  └──────────────────────────────────────────────────┘      │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │       Output Capture & Error Handling             │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## REQ-4.1: Code Generation Engine

### Purpose
LLM-powered code generation with quality validation

### Features
1. **Multi-Language Support**
   - Python 3.12+
   - JavaScript (Node.js)
   - Bash shell scripts

2. **Generation Pipeline**
   - Task analysis and requirements extraction
   - Code generation via LLM
   - Automatic syntax validation
   - Test case generation
   - Documentation generation

3. **Quality Checks**
   - Syntax validation (AST parsing)
   - Security checks (no dangerous imports/commands)
   - Code complexity analysis
   - Best practices validation

### Implementation

**File**: `alpha/core/code_generation/generator.py`

```python
class CodeGenerator:
    async def generate(
        self,
        task: str,
        language: str,
        context: Dict[str, Any]
    ) -> CodeResult:
        """
        Generate code for given task

        Args:
            task: Task description
            language: Target language (python, javascript, bash)
            context: Additional context

        Returns:
            CodeResult with generated code and metadata
        """
```

---

## REQ-4.2: Safe Code Execution Sandbox

### Purpose
Isolated execution environment using Docker containers

### Security Model

**Isolation Layers**:
1. **Process Isolation** - Docker container
2. **Resource Limits** - cgroups (CPU, memory, time)
3. **Network Isolation** - Optional network access
4. **File System** - Read-only except /tmp

### Resource Limits

| Resource | Default Limit | Max Limit |
|----------|---------------|-----------|
| CPU | 1 core | 2 cores |
| Memory | 512 MB | 2 GB |
| Execution Time | 30s | 300s (5min) |
| Disk Space | 100 MB | 500 MB |

### Docker Configuration

**Base Images**:
- Python: `python:3.12-slim`
- JavaScript: `node:20-slim`
- Bash: `ubuntu:22.04`

**Security Settings**:
```yaml
security_opt:
  - no-new-privileges
  - seccomp=default
cap_drop:
  - ALL
cap_add:
  - NET_ADMIN (only if network needed)
read_only_rootfs: true
tmpfs:
  - /tmp
  - /var/tmp
```

### Implementation

**File**: `alpha/core/code_generation/sandbox.py`

```python
class CodeSandbox:
    def __init__(
        self,
        cpu_limit: float = 1.0,
        memory_limit: str = "512m",
        timeout: int = 30,
        network: bool = False
    ):
        """Initialize sandbox with resource limits"""

    async def execute(
        self,
        code: str,
        language: str,
        input_data: Optional[str] = None
    ) -> ExecutionResult:
        """Execute code in isolated container"""
```

---

## REQ-4.3: Code Execution Tool

### Purpose
Integrate code execution into Alpha's tool system

### Tool Interface

**File**: `alpha/tools/code_execution.py`

```python
class CodeExecutionTool(Tool):
    name = "code_execution"
    description = """
    Execute custom code in a secure sandbox.
    Supports Python, JavaScript, and Bash.
    """

    async def execute(
        self,
        language: str,
        task: str,
        auto_generate: bool = True,
        code: Optional[str] = None,
        timeout: int = 30
    ) -> ToolResult:
        """
        Execute code or generate and execute

        Args:
            language: Programming language
            task: What to accomplish
            auto_generate: Auto-generate code if not provided
            code: Pre-written code (optional)
            timeout: Max execution time

        Returns:
            ToolResult with output or error
        """
```

### Usage Examples

**Example 1: Auto-generate and execute**
```python
result = await code_tool.execute(
    language="python",
    task="Calculate fibonacci numbers up to 100"
)
```

**Example 2: Execute existing code**
```python
result = await code_tool.execute(
    language="python",
    code="print(sum(range(1, 101)))",
    auto_generate=False
)
```

---

## File Structure

```
alpha/
├── core/
│   └── code_generation/
│       ├── __init__.py
│       ├── generator.py          # REQ-4.1: Code generation
│       ├── sandbox.py             # REQ-4.2: Docker sandbox
│       ├── validator.py           # Syntax & security validation
│       └── models.py              # Data models
├── tools/
│   └── code_execution.py          # REQ-4.3: Tool integration
└── tests/
    └── code_generation/
        ├── test_generator.py
        ├── test_sandbox.py
        └── test_code_execution_tool.py
```

---

## Data Models

```python
@dataclass
class CodeResult:
    code: str
    language: str
    tests: List[str]
    documentation: str
    quality_score: float
    warnings: List[str]

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: Optional[str]
    exit_code: int
    execution_time: float
    resource_usage: ResourceMetrics
```

---

## Security Considerations

### Code Generation Security

**Dangerous Patterns to Block**:
- Python: `__import__`, `eval()`, `exec()`, `compile()`
- Bash: `rm -rf`, `curl | bash`, `wget -O - | sh`
- JavaScript: `eval()`, `Function()`, `require('child_process')`

### Execution Security

**Sandbox Escape Prevention**:
- Read-only root filesystem
- No privileged operations
- Dropped capabilities
- Seccomp filtering
- AppArmor/SELinux profiles

### Network Access

**Default**: No network access

**When Enabled** (user confirmation required):
- Outbound only (no incoming)
- Rate limiting
- DNS resolution allowed
- Common ports only (80, 443)

---

## Testing Strategy

### Unit Tests
- Code generation for each language
- Syntax validation
- Security checks
- Sandbox creation and cleanup

### Integration Tests
- End-to-end code generation + execution
- Resource limit enforcement
- Error handling
- Timeout handling

### Security Tests
- Attempt sandbox escape
- Test dangerous code blocking
- Resource exhaustion tests
- Network isolation verification

---

## Success Criteria

**REQ-4.1: Code Generation**
- [ ] Generate syntactically correct Python code
- [ ] Generate valid JavaScript code
- [ ] Generate safe Bash scripts
- [ ] Block dangerous patterns
- [ ] Quality score >0.8 for common tasks

**REQ-4.2: Sandbox**
- [ ] Docker container isolation working
- [ ] CPU limit enforced
- [ ] Memory limit enforced
- [ ] Timeout enforced
- [ ] File system restrictions working
- [ ] Network isolation working

**REQ-4.3: Tool Integration**
- [ ] Integrated with Alpha tool registry
- [ ] Auto-generation working
- [ ] Manual code execution working
- [ ] Error messages clear
- [ ] Clean resource cleanup

**Overall**:
- [ ] >90% test coverage
- [ ] All security tests passing
- [ ] Complete documentation (EN + CN)
- [ ] Performance benchmarks met

---

## Implementation Timeline

### Day 1: Code Generator
- Implement CodeGenerator class
- Add syntax validators
- Add security checks
- Unit tests

### Day 2: Sandbox
- Docker integration
- Resource limit configuration
- Execution wrapper
- Cleanup logic

### Day 3: Tool Integration
- CodeExecutionTool class
- Tool registry integration
- End-to-end testing
- Error handling

### Day 4: Testing & Security
- Comprehensive test suite
- Security testing
- Performance testing
- Bug fixes

### Day 5: Documentation & Polish
- User documentation
- API documentation
- Example usage
- Final integration testing

---

## Dependencies

### Python Packages
```
docker>=7.0.0          # Docker SDK for Python
ast (stdlib)           # Python syntax validation
subprocess (stdlib)    # Process execution
```

### System Requirements
- Docker Engine 20.10+
- Docker SDK for Python
- 2GB disk space for images

### Optional
- Container runtime: Docker or Podman

---

## Configuration

**config.yaml additions**:
```yaml
code_execution:
  enabled: true

  sandbox:
    cpu_limit: 1.0
    memory_limit: "512m"
    timeout: 30
    network_enabled: false

  security:
    block_dangerous_imports: true
    max_code_length: 10000
    allowed_languages:
      - python
      - javascript
      - bash

  docker:
    pull_images: true
    remove_containers: true
    auto_cleanup: true
```

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Sandbox escape | High | Low | Multi-layer security, regular updates |
| Resource exhaustion | Medium | Medium | Strict limits, monitoring |
| Docker not installed | Medium | Medium | Clear error messages, installation guide |
| Generated code quality | Low | Medium | Quality scoring, user review |

---

## Future Enhancements (Phase 4.2+)

1. **More Languages**: Go, Rust, Java
2. **Persistent Environments**: Reuse containers for related tasks
3. **GPU Support**: For ML/AI code
4. **Distributed Execution**: Run on remote workers
5. **Code Optimization**: Auto-optimize generated code
6. **Test Generation**: Auto-generate comprehensive tests

---

**Document Version**: 1.0
**Status**: 📋 Design Complete - Ready for Implementation
**Next**: Begin Day 1 Implementation
