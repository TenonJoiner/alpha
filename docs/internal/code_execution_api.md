# Code Execution API Reference

**Version:** 0.7.0
**Phase:** 4.1 - Code Generation & Safe Execution
**Last Updated:** 2026-01-30

---

## Table of Contents

1. [Overview](#overview)
2. [Core Classes](#core-classes)
3. [Data Classes](#data-classes)
4. [Language Handlers](#language-handlers)
5. [Exceptions](#exceptions)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)

---

## Overview

The Code Execution API provides a complete system for generating, validating, and executing code safely in isolated environments. The API is organized into several modules:

- **`generator`** - LLM-powered code generation
- **`validator`** - Syntax, security, and quality validation
- **`sandbox`** - Docker-based sandboxed execution
- **`executor`** - Orchestration and pipeline management
- **`languages`** - Language-specific handlers

### Module Structure

```python
from alpha.code_execution import (
    # Core classes
    CodeGenerator,
    CodeValidator,
    SandboxManager,
    CodeExecutor,

    # Data classes
    GeneratedCode,
    ValidationResult,
    SecurityReport,
    QualityReport,
    SandboxConfig,
    ExecutionResult,
    ExecutionOptions,

    # Exceptions
    CodeGenerationError,
    DockerNotAvailableError,
    ContainerCreationError,
    ExecutionTimeoutError,
    ExecutionError,
    UserRejectionError,
)
```

---

## Core Classes

### CodeGenerator

LLM-powered code generation engine that creates executable code from natural language task descriptions.

**Location:** `alpha/code_execution/generator.py`

#### Constructor

```python
def __init__(self, llm_service)
```

**Parameters:**
- `llm_service`: Alpha's LLM service instance for code generation

**Example:**
```python
from alpha.llm.service import LLMService
from alpha.code_execution import CodeGenerator

llm = LLMService.from_config(config.llm)
generator = CodeGenerator(llm)
```

#### Methods

##### `generate_code()`

Generate code from a task description.

```python
async def generate_code(
    self,
    task: str,
    language: str = "python",
    context: Optional[Dict[str, Any]] = None
) -> GeneratedCode
```

**Parameters:**
- `task` (str): Natural language description of what the code should do
- `language` (str): Target programming language ("python", "javascript", "bash")
- `context` (dict, optional): Additional context information (variables, data, constraints)

**Returns:**
- `GeneratedCode`: Generated code with metadata

**Raises:**
- `CodeGenerationError`: If generation fails

**Example:**
```python
result = await generator.generate_code(
    task="Calculate the factorial of a number",
    language="python",
    context={"input": 10}
)
print(result.code)
```

##### `generate_with_tests()`

Generate code with accompanying test cases.

```python
async def generate_with_tests(
    self,
    task: str,
    language: str = "python",
    context: Optional[Dict[str, Any]] = None
) -> GeneratedCode
```

**Parameters:**
- `task` (str): Task description
- `language` (str): Target language
- `context` (dict, optional): Optional context

**Returns:**
- `GeneratedCode`: Code with both implementation and tests

**Example:**
```python
result = await generator.generate_with_tests(
    task="Sort a list of numbers",
    language="python"
)
print("Code:", result.code)
print("Tests:", result.tests)
```

##### `refine_code()`

Refine existing code based on feedback or error messages.

```python
async def refine_code(
    self,
    code: str,
    feedback: str,
    language: str = "python"
) -> GeneratedCode
```

**Parameters:**
- `code` (str): Existing code to refine
- `feedback` (str): User feedback or error messages
- `language` (str): Programming language

**Returns:**
- `GeneratedCode`: Refined code

**Example:**
```python
refined = await generator.refine_code(
    code=original_code,
    feedback="The function should handle negative numbers",
    language="python"
)
```

##### `get_statistics()`

Get code generation statistics.

```python
def get_statistics(self) -> Dict[str, Any]
```

**Returns:**
- Dictionary with statistics:
  - `total_generations`: Total generation attempts
  - `successful_generations`: Successful generations
  - `success_rate`: Success percentage

**Example:**
```python
stats = generator.get_statistics()
print(f"Success rate: {stats['success_rate']}%")
```

---

### CodeValidator

Comprehensive code validator for syntax, security, and quality checks.

**Location:** `alpha/code_execution/validator.py`

#### Constructor

```python
def __init__(self)
```

**Example:**
```python
from alpha.code_execution import CodeValidator

validator = CodeValidator()
```

#### Methods

##### `validate_syntax()`

Validate code syntax using language-specific parsing.

```python
def validate_syntax(
    self,
    code: str,
    language: str
) -> ValidationResult
```

**Parameters:**
- `code` (str): Source code to validate
- `language` (str): Programming language ("python", "javascript", "bash")

**Returns:**
- `ValidationResult`: Validation status with errors, warnings, and suggestions

**Example:**
```python
result = validator.validate_syntax(
    code="def foo():\n    print('hi')",
    language="python"
)

if result.is_valid:
    print("Code is valid")
else:
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)
```

##### `check_security()`

Perform security analysis on code.

```python
def check_security(
    self,
    code: str,
    language: str
) -> SecurityReport
```

**Parameters:**
- `code` (str): Source code to analyze
- `language` (str): Programming language

**Returns:**
- `SecurityReport`: Security analysis with risk level and recommendations

**Example:**
```python
report = validator.check_security(
    code="import os\nos.system('ls')",
    language="python"
)

print(f"Safe: {report.is_safe}")
print(f"Risk Level: {report.risk_level}")
print(f"Dangerous Patterns: {report.dangerous_patterns}")
for rec in report.recommendations:
    print(f"  - {rec}")
```

##### `assess_quality()`

Assess code quality based on various metrics.

```python
def assess_quality(
    self,
    code: str,
    language: str
) -> QualityReport
```

**Parameters:**
- `code` (str): Source code to assess
- `language` (str): Programming language

**Returns:**
- `QualityReport`: Quality score, issues, and metrics

**Example:**
```python
report = validator.assess_quality(
    code="def add(a, b):\n    return a + b",
    language="python"
)

print(f"Quality Score: {report.score:.2f}")
print(f"Metrics: {report.metrics}")
print(f"Issues: {report.issues}")
```

---

### SandboxManager

Manages Docker-based sandboxed code execution with resource limits.

**Location:** `alpha/code_execution/sandbox.py`

#### Constructor

```python
def __init__(
    self,
    config: Optional[SandboxConfig] = None
)
```

**Parameters:**
- `config` (SandboxConfig, optional): Default configuration for sandbox

**Example:**
```python
from alpha.code_execution import SandboxManager, SandboxConfig

config = SandboxConfig(
    language="python",
    docker_image="python:3.12-slim",
    timeout=30,
    memory="256m"
)
manager = SandboxManager(config)
```

#### Methods

##### `is_docker_available()`

Check if Docker is installed and running.

```python
def is_docker_available(self) -> bool
```

**Returns:**
- `bool`: True if Docker is available, False otherwise

**Example:**
```python
if manager.is_docker_available():
    print("Docker is ready")
else:
    print("Docker is not available")
```

##### `create_container()`

Create Docker container for code execution.

```python
def create_container(
    self,
    language: str,
    code: str,
    config: Optional[SandboxConfig] = None
) -> str
```

**Parameters:**
- `language` (str): Programming language
- `code` (str): Code to execute
- `config` (SandboxConfig, optional): Execution configuration

**Returns:**
- `str`: Container ID

**Raises:**
- `DockerNotAvailableError`: If Docker is not available
- `ContainerCreationError`: If container creation fails

**Example:**
```python
container_id = manager.create_container(
    language="python",
    code="print('Hello, World!')",
    config=config
)
print(f"Container created: {container_id}")
```

##### `execute_code()`

Execute code in container with timeout.

```python
def execute_code(
    self,
    container_id: str,
    timeout: Optional[int] = None
) -> ExecutionResult
```

**Parameters:**
- `container_id` (str): Container ID from `create_container()`
- `timeout` (int, optional): Execution timeout in seconds

**Returns:**
- `ExecutionResult`: Execution output and status

**Raises:**
- `ValueError`: If container_id is not found
- `ExecutionTimeoutError`: If execution exceeds timeout

**Example:**
```python
result = manager.execute_code(
    container_id=container_id,
    timeout=30
)

if result.success:
    print("Output:", result.stdout)
else:
    print("Error:", result.error_message)
    print("Stderr:", result.stderr)
```

##### `cleanup_container()`

Clean up container and associated resources.

```python
def cleanup_container(
    self,
    container_id: str
) -> None
```

**Parameters:**
- `container_id` (str): Container ID to clean up

**Example:**
```python
manager.cleanup_container(container_id)
```

##### `cleanup_all()`

Clean up all active containers.

```python
def cleanup_all(self) -> None
```

**Example:**
```python
# Emergency cleanup
manager.cleanup_all()
```

#### Context Manager Support

`SandboxManager` can be used as a context manager for automatic cleanup.

**Example:**
```python
with SandboxManager(config) as manager:
    container_id = manager.create_container("python", code)
    result = manager.execute_code(container_id)
    print(result.stdout)
# Automatic cleanup on exit
```

#### Convenience Function

##### `execute_code_sandboxed()`

High-level convenience function for simple execution.

```python
def execute_code_sandboxed(
    language: str,
    code: str,
    timeout: int = 30,
    memory: str = "256m",
    network_enabled: bool = False
) -> ExecutionResult
```

**Parameters:**
- `language` (str): Programming language
- `code` (str): Code to execute
- `timeout` (int): Maximum execution time
- `memory` (str): Memory limit
- `network_enabled` (bool): Whether to enable network access

**Returns:**
- `ExecutionResult`: Execution result

**Example:**
```python
from alpha.code_execution.sandbox import execute_code_sandboxed

result = execute_code_sandboxed(
    language="python",
    code="print('Hello!')",
    timeout=10
)
print(result.stdout)
```

---

### CodeExecutor

Main orchestrator for code generation, validation, and execution.

**Location:** `alpha/code_execution/executor.py`

#### Constructor

```python
def __init__(
    self,
    generator: CodeGenerator,
    validator: CodeValidator,
    sandbox: SandboxManager
)
```

**Parameters:**
- `generator` (CodeGenerator): Code generator instance
- `validator` (CodeValidator): Code validator instance
- `sandbox` (SandboxManager): Sandbox manager instance

**Example:**
```python
from alpha.code_execution import CodeExecutor

executor = CodeExecutor(
    generator=generator,
    validator=validator,
    sandbox=sandbox
)
```

#### Methods

##### `execute_task()`

Execute a task by generating and running code.

```python
async def execute_task(
    self,
    task: str,
    language: str = "python",
    options: Optional[ExecutionOptions] = None,
    context: Optional[Dict[str, Any]] = None
) -> ExecutionResult
```

**Parameters:**
- `task` (str): Natural language task description
- `language` (str): Programming language
- `options` (ExecutionOptions, optional): Execution options
- `context` (dict, optional): Context for code generation

**Returns:**
- `ExecutionResult`: Execution result

**Raises:**
- `CodeGenerationError`: If code generation fails
- `UserRejectionError`: If user rejects code execution
- `ExecutionError`: If execution fails after retries

**Example:**
```python
result = await executor.execute_task(
    task="Calculate the first 10 prime numbers",
    language="python",
    options=ExecutionOptions(
        require_approval=True,
        timeout=30
    )
)
print(result.stdout)
```

##### `execute_code_string()`

Execute provided code string.

```python
async def execute_code_string(
    self,
    code: str,
    language: str = "python",
    options: Optional[ExecutionOptions] = None
) -> ExecutionResult
```

**Parameters:**
- `code` (str): Source code to execute
- `language` (str): Programming language
- `options` (ExecutionOptions, optional): Execution options

**Returns:**
- `ExecutionResult`: Execution result

**Example:**
```python
result = await executor.execute_code_string(
    code="print('Hello, World!')",
    language="python",
    options=ExecutionOptions(
        require_approval=False,
        validate_syntax=True
    )
)
```

##### `get_execution_statistics()`

Get execution statistics.

```python
def get_execution_statistics(self) -> Dict[str, Any]
```

**Returns:**
- Dictionary with statistics:
  - `total_executions`: Total executions
  - `successful_executions`: Successful executions
  - `failed_executions`: Failed executions
  - `success_rate`: Success percentage
  - `avg_execution_time`: Average execution time
  - `code_generation_attempts`: Generation attempts
  - `refinement_attempts`: Refinement attempts
  - `user_rejections`: User rejections
  - `security_blocks`: Security blocks
  - `syntax_errors`: Syntax errors
  - `execution_errors`: Execution errors

**Example:**
```python
stats = executor.get_execution_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Average time: {stats['avg_execution_time']:.2f}s")
```

##### `reset_statistics()`

Reset all execution statistics.

```python
def reset_statistics(self) -> None
```

**Example:**
```python
executor.reset_statistics()
```

---

## Data Classes

### GeneratedCode

Container for generated code and metadata.

**Location:** `alpha/code_execution/generator.py`

```python
@dataclass
class GeneratedCode:
    code: str                           # Generated code
    language: str                       # Programming language
    description: str                    # Description of what code does
    tests: Optional[str] = None        # Test code (if generated)
    dependencies: Optional[List[str]] = None  # Required packages
    complexity: str = "simple"          # Complexity level
    estimated_runtime: Optional[int] = None   # Estimated seconds
```

**Example:**
```python
generated = GeneratedCode(
    code="def add(a, b):\n    return a + b",
    language="python",
    description="Function to add two numbers",
    complexity="simple",
    estimated_runtime=1
)
```

---

### ValidationResult

Result of syntax validation.

**Location:** `alpha/code_execution/validator.py`

```python
@dataclass
class ValidationResult:
    is_valid: bool                      # Whether code is valid
    errors: List[str] = field(default_factory=list)      # Syntax errors
    warnings: List[str] = field(default_factory=list)    # Warnings
    suggestions: List[str] = field(default_factory=list)  # Suggestions
```

**Methods:**
- `__str__()`: String representation of validation result

**Example:**
```python
result = ValidationResult(
    is_valid=False,
    errors=["SyntaxError: unexpected EOF while parsing"],
    warnings=["Code is very short"],
    suggestions=["Add error handling"]
)
print(result)  # Formatted output
```

---

### SecurityReport

Security analysis report for code.

**Location:** `alpha/code_execution/validator.py`

```python
@dataclass
class SecurityReport:
    is_safe: bool                       # Whether code passes security checks
    dangerous_patterns: List[str] = field(default_factory=list)  # Detected patterns
    risk_level: str = "low"            # Risk level: "low", "medium", "high"
    recommendations: List[str] = field(default_factory=list)     # Security recommendations
```

**Methods:**
- `__str__()`: String representation of security report

**Example:**
```python
report = SecurityReport(
    is_safe=False,
    dangerous_patterns=["subprocess.call()", "eval()"],
    risk_level="high",
    recommendations=[
        "Avoid subprocess.call() - validate all inputs",
        "Never use eval() on user input"
    ]
)
print(report)
```

---

### QualityReport

Code quality assessment report.

**Location:** `alpha/code_execution/validator.py`

```python
@dataclass
class QualityReport:
    score: float                        # Quality score (0.0 to 1.0)
    issues: List[str] = field(default_factory=list)      # Quality issues
    metrics: Dict[str, Any] = field(default_factory=dict) # Quality metrics
```

**Methods:**
- `__str__()`: String representation of quality report

**Metrics Dictionary:**
```python
{
    'total_lines': int,          # Total lines of code
    'code_lines': int,           # Non-empty lines
    'comment_lines': int,        # Comment lines
    'comment_ratio': float,      # Comment to code ratio
    'has_error_handling': bool,  # Has try/catch or error checks
    'has_documentation': bool,   # Has docstrings/comments
    'avg_line_length': float,    # Average line length
}
```

**Example:**
```python
report = QualityReport(
    score=0.75,
    issues=["Missing documentation"],
    metrics={
        'total_lines': 20,
        'code_lines': 15,
        'comment_lines': 2,
        'comment_ratio': 0.13,
        'has_error_handling': True,
        'has_documentation': False,
        'avg_line_length': 42.5
    }
)
print(f"Score: {report.score:.2f}")
```

---

### SandboxConfig

Configuration for sandbox execution environment.

**Location:** `alpha/code_execution/sandbox.py`

```python
@dataclass
class SandboxConfig:
    language: str                       # Programming language
    docker_image: str                   # Docker image to use
    timeout: int = 30                   # Maximum execution time (seconds)
    memory: str = "256m"                # Memory limit
    cpu_quota: int = 50000              # CPU quota (50000 = 50% of 1 CPU)
    network_mode: str = "none"          # Network mode: "none", "bridge", "host"
    working_dir: str = "/workspace"     # Working directory in container
    read_only_rootfs: bool = True       # Mount root filesystem as read-only
    user: Optional[str] = None          # User to run as (e.g., "1000:1000")
```

**Example:**
```python
config = SandboxConfig(
    language="python",
    docker_image="python:3.12-slim",
    timeout=60,
    memory="512m",
    cpu_quota=100000,  # 100% of one CPU
    network_mode="bridge",  # Enable network
    read_only_rootfs=True
)
```

---

### ExecutionResult

Result of code execution in sandbox.

**Location:** `alpha/code_execution/sandbox.py`

```python
@dataclass
class ExecutionResult:
    success: bool                       # Whether execution succeeded
    stdout: str = ""                    # Standard output
    stderr: str = ""                    # Standard error
    exit_code: int = 0                  # Process exit code
    execution_time: float = 0.0         # Execution time (seconds)
    error_message: Optional[str] = None # Error message if failed
    timed_out: bool = False            # Whether execution timed out
    container_id: Optional[str] = None  # Container ID (for debugging)
```

**Example:**
```python
result = ExecutionResult(
    success=True,
    stdout="Hello, World!\n",
    stderr="",
    exit_code=0,
    execution_time=0.523,
    timed_out=False
)

if result.success:
    print(f"Output: {result.stdout}")
    print(f"Time: {result.execution_time:.3f}s")
```

---

### ExecutionOptions

Configuration options for code execution.

**Location:** `alpha/code_execution/executor.py`

```python
@dataclass
class ExecutionOptions:
    generate_code: bool = True          # Whether to generate code
    validate_syntax: bool = True        # Enable syntax validation
    check_security: bool = True         # Enable security scanning
    assess_quality: bool = False        # Enable quality assessment
    require_approval: bool = True       # Require user approval
    allow_network: bool = False         # Allow network access
    timeout: int = 30                   # Maximum execution time (seconds)
    max_retries: int = 2                # Maximum retry attempts
```

**Example:**
```python
options = ExecutionOptions(
    generate_code=True,
    validate_syntax=True,
    check_security=True,
    assess_quality=True,
    require_approval=False,  # Skip approval for automation
    allow_network=False,
    timeout=60,
    max_retries=3
)
```

---

## Language Handlers

Language handlers provide language-specific configuration and validation logic.

### LanguageHandler Interface

**Location:** `alpha/code_execution/languages/__init__.py`

```python
class LanguageHandler:
    """Base interface for language handlers"""

    def validate_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate code syntax.

        Args:
            code: Source code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    def get_dangerous_patterns(self) -> List[str]:
        """
        Get list of dangerous code patterns for security scanning.

        Returns:
            List of dangerous pattern strings
        """
        pass

    def get_security_recommendations(self) -> Dict[str, str]:
        """
        Get security recommendations for detected patterns.

        Returns:
            Dictionary mapping pattern types to recommendations
        """
        pass

    def get_execution_config(self) -> Dict[str, Any]:
        """
        Get Docker execution configuration for this language.

        Returns:
            Dictionary with:
                - docker_image: Docker image name
                - command: Execution command list
                - file_extension: Source file extension
        """
        pass
```

### Getting a Handler

```python
from alpha.code_execution.languages import get_handler

# Get Python handler
handler = get_handler("python")

# Validate syntax
is_valid, error = handler.validate_syntax("print('hello')")

# Get dangerous patterns
patterns = handler.get_dangerous_patterns()

# Get execution config
config = handler.get_execution_config()
```

### Supported Handlers

#### Python Handler

```python
from alpha.code_execution.languages.python import PythonHandler

handler = PythonHandler()

# Dangerous patterns
patterns = handler.get_dangerous_patterns()
# Returns: ['eval(', 'exec(', '__import__', 'compile(', ...]

# Execution config
config = handler.get_execution_config()
# Returns: {
#     'docker_image': 'python:3.12-slim',
#     'command': ['python', '-u', '/workspace/code.py'],
#     'file_extension': 'py'
# }
```

#### JavaScript Handler

```python
from alpha.code_execution.languages.javascript import JavaScriptHandler

handler = JavaScriptHandler()

# Dangerous patterns
patterns = handler.get_dangerous_patterns()
# Returns: ['eval(', 'Function(', 'child_process', ...]

# Execution config
config = handler.get_execution_config()
# Returns: {
#     'docker_image': 'node:20-slim',
#     'command': ['node', '/workspace/code.js'],
#     'file_extension': 'js'
# }
```

#### Bash Handler

```python
from alpha.code_execution.languages.bash import BashHandler

handler = BashHandler()

# Dangerous patterns
patterns = handler.get_dangerous_patterns()
# Returns: ['rm -rf /', 'mkfs', 'fdisk', 'curl | bash', ...]

# Execution config
config = handler.get_execution_config()
# Returns: {
#     'docker_image': 'bash:5.2-alpine',
#     'command': ['/bin/bash', '/workspace/code.sh'],
#     'file_extension': 'sh'
# }
```

---

## Exceptions

### CodeGenerationError

Raised when code generation fails.

**Location:** `alpha/code_execution/generator.py`

```python
class CodeGenerationError(Exception):
    """Raised when code generation fails"""
    pass
```

**Example:**
```python
try:
    code = await generator.generate_code(task="invalid task", language="python")
except CodeGenerationError as e:
    print(f"Generation failed: {e}")
```

---

### DockerNotAvailableError

Raised when Docker is not available or not running.

**Location:** `alpha/code_execution/sandbox.py`

```python
class DockerNotAvailableError(Exception):
    """Raised when Docker is not available or not running"""
    pass
```

**Example:**
```python
try:
    manager = SandboxManager()
    if not manager.is_docker_available():
        raise DockerNotAvailableError("Docker is required")
except DockerNotAvailableError as e:
    print(f"Docker error: {e}")
```

---

### ContainerCreationError

Raised when container creation fails.

**Location:** `alpha/code_execution/sandbox.py`

```python
class ContainerCreationError(Exception):
    """Raised when container creation fails"""
    pass
```

**Example:**
```python
try:
    container_id = manager.create_container("python", code)
except ContainerCreationError as e:
    print(f"Container creation failed: {e}")
```

---

### ExecutionTimeoutError

Raised when code execution exceeds timeout.

**Location:** `alpha/code_execution/sandbox.py`

```python
class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds timeout"""
    pass
```

**Example:**
```python
try:
    result = manager.execute_code(container_id, timeout=5)
except ExecutionTimeoutError as e:
    print(f"Execution timed out: {e}")
```

---

### ExecutionError

Raised when code execution fails after all retries.

**Location:** `alpha/code_execution/executor.py`

```python
class ExecutionError(Exception):
    """Raised when code execution fails after all retries"""
    pass
```

**Example:**
```python
try:
    result = await executor.execute_task("invalid task")
except ExecutionError as e:
    print(f"Execution failed: {e}")
```

---

### UserRejectionError

Raised when user rejects code execution.

**Location:** `alpha/code_execution/executor.py`

```python
class UserRejectionError(Exception):
    """Raised when user rejects code execution"""
    pass
```

**Example:**
```python
try:
    result = await executor.execute_task(
        "dangerous task",
        options=ExecutionOptions(require_approval=True)
    )
except UserRejectionError as e:
    print(f"User rejected: {e}")
```

---

## Usage Examples

### Example 1: Simple Code Generation and Execution

```python
from alpha.llm.service import LLMService
from alpha.code_execution import (
    CodeGenerator,
    CodeValidator,
    SandboxManager,
    CodeExecutor,
    ExecutionOptions,
    SandboxConfig
)

# Initialize components
llm = LLMService.from_config(config.llm)
generator = CodeGenerator(llm)
validator = CodeValidator()
sandbox = SandboxManager()
executor = CodeExecutor(generator, validator, sandbox)

# Execute a task
result = await executor.execute_task(
    task="Calculate the sum of numbers from 1 to 100",
    language="python",
    options=ExecutionOptions(
        require_approval=False,
        timeout=30
    )
)

if result.success:
    print(f"Output: {result.stdout}")
else:
    print(f"Error: {result.error_message}")
```

### Example 2: Direct Code Execution

```python
# Execute code directly (skip generation)
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print([fibonacci(i) for i in range(10)])
"""

result = await executor.execute_code_string(
    code=code,
    language="python",
    options=ExecutionOptions(
        generate_code=False,
        validate_syntax=True,
        check_security=True,
        require_approval=False
    )
)

print(result.stdout)
```

### Example 3: Manual Pipeline Control

```python
# Step 1: Generate code
generated = await generator.generate_code(
    task="Sort a list of numbers",
    language="python"
)
print(f"Generated code:\n{generated.code}")

# Step 2: Validate syntax
validation = validator.validate_syntax(generated.code, "python")
if not validation.is_valid:
    print(f"Syntax errors: {validation.errors}")
    exit(1)

# Step 3: Check security
security = validator.check_security(generated.code, "python")
print(f"Risk level: {security.risk_level}")
if not security.is_safe:
    print(f"Dangerous patterns: {security.dangerous_patterns}")
    # Decide whether to proceed...

# Step 4: Assess quality (optional)
quality = validator.assess_quality(generated.code, "python")
print(f"Quality score: {quality.score:.2f}")

# Step 5: Execute in sandbox
config = SandboxConfig(
    language="python",
    docker_image="python:3.12-slim",
    timeout=30
)

container_id = sandbox.create_container("python", generated.code, config)
try:
    result = sandbox.execute_code(container_id, timeout=30)
    print(f"Output: {result.stdout}")
finally:
    sandbox.cleanup_container(container_id)
```

### Example 4: Error Handling and Retry

```python
from alpha.code_execution import ExecutionError, UserRejectionError

try:
    result = await executor.execute_task(
        task="Complex mathematical operation",
        language="python",
        options=ExecutionOptions(
            max_retries=3,
            require_approval=True,
            timeout=60
        )
    )
    print(f"Success: {result.stdout}")

except CodeGenerationError as e:
    print(f"Code generation failed: {e}")

except UserRejectionError:
    print("User rejected code execution")

except ExecutionError as e:
    print(f"Execution failed after retries: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Example 5: Statistics Tracking

```python
# Execute multiple tasks
tasks = [
    "Calculate factorial of 10",
    "Sort array [5, 2, 8, 1, 9]",
    "Find prime numbers up to 50"
]

for task in tasks:
    try:
        result = await executor.execute_task(
            task=task,
            language="python",
            options=ExecutionOptions(require_approval=False)
        )
        print(f"Task: {task}")
        print(f"Success: {result.success}")
    except Exception as e:
        print(f"Task failed: {e}")

# Get statistics
stats = executor.get_execution_statistics()
print("\nExecution Statistics:")
print(f"Total: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Average time: {stats['avg_execution_time']:.2f}s")
print(f"Syntax errors: {stats['syntax_errors']}")
print(f"Security blocks: {stats['security_blocks']}")
```

### Example 6: Custom Configuration

```python
# Custom sandbox configuration
custom_config = SandboxConfig(
    language="python",
    docker_image="python:3.12-slim",
    timeout=120,                # 2 minutes
    memory="512m",              # 512 MB RAM
    cpu_quota=100000,           # 100% of one CPU
    network_mode="bridge",      # Enable network
    read_only_rootfs=True,
    user="1000:1000"            # Non-root user
)

sandbox = SandboxManager(custom_config)

# Execute with custom config
result = await executor.execute_task(
    task="Fetch data from API and process it",
    language="python",
    options=ExecutionOptions(
        allow_network=True,     # Allow network access
        timeout=120,
        require_approval=True
    )
)
```

---

## Configuration

### Configuration File

Code execution configuration in `config.yaml`:

```yaml
code_execution:
  enabled: true

  defaults:
    language: python
    timeout: 30
    network_access: false

  limits:
    cpu_quota: 50000
    memory: "256m"
    max_execution_time: 300

  security:
    require_approval: true
    scan_code: true
    allow_dangerous_operations: false

  docker:
    enabled: true
    images:
      python: "python:3.12-slim"
      javascript: "node:20-slim"
      bash: "bash:5.2-alpine"
    network_mode: "none"
    read_only_rootfs: true

  logging:
    log_generated_code: true
    log_execution_output: true
    log_errors: true
```

### Loading Configuration

```python
from alpha.utils.config import load_config

config = load_config('config.yaml')

# Access code execution config
code_exec_config = config.get('code_execution', {})
enabled = code_exec_config.get('enabled', False)
defaults = code_exec_config.get('defaults', {})
limits = code_exec_config.get('limits', {})
```

---

## Best Practices

### 1. Resource Management

Always use context managers or ensure cleanup:

```python
# Good: Context manager
with SandboxManager(config) as manager:
    container_id = manager.create_container("python", code)
    result = manager.execute_code(container_id)

# Good: Try-finally
manager = SandboxManager(config)
container_id = manager.create_container("python", code)
try:
    result = manager.execute_code(container_id)
finally:
    manager.cleanup_container(container_id)
```

### 2. Error Handling

Handle specific exceptions appropriately:

```python
try:
    result = await executor.execute_task(task, language)
except CodeGenerationError:
    # Handle generation failure
    pass
except UserRejectionError:
    # Handle user rejection
    pass
except ExecutionError:
    # Handle execution failure
    pass
except Exception:
    # Handle unexpected errors
    pass
```

### 3. Security

Always validate and scan code:

```python
options = ExecutionOptions(
    validate_syntax=True,      # Always validate
    check_security=True,       # Always scan
    require_approval=True,     # Require approval for sensitive ops
    allow_network=False        # Disable network by default
)
```

### 4. Performance

Monitor and optimize execution:

```python
# Track statistics
stats = executor.get_execution_statistics()
if stats['success_rate'] < 80:
    # Investigate failures
    pass

# Adjust timeouts based on task complexity
options = ExecutionOptions(
    timeout=60 if complex_task else 30
)
```

---

**API Documentation Version:** 1.0
**Code Version:** 0.7.0
**Last Updated:** 2026-01-30
**Status:** ✅ Complete
