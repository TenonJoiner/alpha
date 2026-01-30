"""
Benchmark test scenarios for Alpha Agent.

Defines comprehensive test suites organized by complexity level and category.
"""

from tests.benchmarks import BenchmarkTask, TaskComplexity, TaskCategory
from tests.benchmarks.tasks import TaskBuilder


def create_level1_scenarios() -> list[BenchmarkTask]:
    """
    Level 1 (Simple Tasks): 1-2 steps, minimal reasoning, 1-2 tool uses.
    Expected success rate: ≥95%, Response time: ≤1s
    """
    return [
        # File System tasks
        TaskBuilder()
        .with_name("Create Simple Text File")
        .with_description("Create a text file with given content")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.FILE_SYSTEM)
        .with_input({"filename": "test.txt", "content": "Hello, World!"})
        .with_expected_output("File created successfully")
        .build(),

        TaskBuilder()
        .with_name("Read Existing File")
        .with_description("Read content from an existing file")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.FILE_SYSTEM)
        .with_input({"filename": "README.md"})
        .build(),

        TaskBuilder()
        .with_name("List Directory Files")
        .with_description("List all files in the current directory")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.FILE_SYSTEM)
        .with_input({"path": "."})
        .build(),

        # Data Processing tasks
        TaskBuilder()
        .with_name("Simple Calculation")
        .with_description("Calculate the result of 15% of 2500")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({"expression": "0.15 * 2500"})
        .with_expected_output(375.0)
        .build(),

        TaskBuilder()
        .with_name("Convert Units")
        .with_description("Convert 10 kilometers to miles")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({"value": 10, "from_unit": "km", "to_unit": "miles"})
        .build(),

        TaskBuilder()
        .with_name("Parse JSON String")
        .with_description("Parse a JSON string and extract a specific field")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({"json_str": '{"name": "Alpha", "version": "0.4.0"}', "field": "version"})
        .with_expected_output("0.4.0")
        .build(),

        # Information Retrieval tasks
        TaskBuilder()
        .with_name("Get Current Time")
        .with_description("Get the current system time")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.INFORMATION_RETRIEVAL)
        .with_input({})
        .build(),

        TaskBuilder()
        .with_name("Check System Status")
        .with_description("Check if Alpha is running properly")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.INFORMATION_RETRIEVAL)
        .with_input({})
        .build(),
    ]


def create_level2_scenarios() -> list[BenchmarkTask]:
    """
    Level 2 (Medium Tasks): 3-5 steps, moderate reasoning, 3-5 tool uses.
    Expected success rate: ≥85%, Response time: ≤10s
    """
    return [
        # File System tasks
        TaskBuilder()
        .with_name("Create and Organize Multiple Files")
        .with_description("Create multiple files in a new directory structure")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.FILE_SYSTEM)
        .with_input({
            "directory": "test_project",
            "files": {
                "README.md": "# Test Project",
                "src/main.py": "print('Hello')",
                "tests/test_main.py": "def test(): pass"
            }
        })
        .build(),

        TaskBuilder()
        .with_name("Search and Filter Files")
        .with_description("Find all Python files modified in the last 7 days")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.FILE_SYSTEM)
        .with_input({"pattern": "*.py", "days": 7})
        .build(),

        # Data Processing tasks
        TaskBuilder()
        .with_name("CSV Data Analysis")
        .with_description("Read CSV file, calculate statistics, and create summary")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({
            "csv_content": "name,age,score\nAlice,25,90\nBob,30,85\nCarol,28,95",
            "operations": ["mean_score", "max_age", "count"]
        })
        .build(),

        TaskBuilder()
        .with_name("JSON Transformation")
        .with_description("Transform JSON structure from one format to another")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({
            "input_json": {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]},
            "output_format": {"user_list": ["name: {name}, id: {id}"]}
        })
        .build(),

        # Web & API tasks
        TaskBuilder()
        .with_name("Make HTTP GET Request")
        .with_description("Make an HTTP GET request and parse the response")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.WEB_API)
        .with_input({
            "url": "https://api.github.com/repos/python/cpython",
            "extract_fields": ["name", "stargazers_count", "language"]
        })
        .build(),

        # Task Scheduling tasks
        TaskBuilder()
        .with_name("Create Simple Scheduled Task")
        .with_description("Create a task that runs every hour")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.TASK_SCHEDULING)
        .with_input({
            "task_name": "hourly_backup",
            "schedule": "0 * * * *",  # Every hour
            "command": "echo 'Backup completed'"
        })
        .build(),

        # Code Generation tasks
        TaskBuilder()
        .with_name("Generate Simple Python Function")
        .with_description("Generate a Python function to calculate factorial")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.CODE_GENERATION)
        .with_input({
            "function_name": "factorial",
            "description": "Calculate factorial of a number recursively",
            "parameters": ["n: int"],
            "return_type": "int"
        })
        .build(),
    ]


def create_level3_scenarios() -> list[BenchmarkTask]:
    """
    Level 3 (Complex Tasks): 6-10 steps, advanced reasoning, 6-10 tool uses.
    Expected success rate: ≥70%, Response time: ≤60s
    """
    return [
        # File System + Data Processing
        TaskBuilder()
        .with_name("Log File Analysis and Reporting")
        .with_description("Analyze log files, extract errors, and generate summary report")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.DATA_PROCESSING)
        .with_input({
            "log_dir": "logs/",
            "patterns": ["ERROR", "WARNING", "CRITICAL"],
            "output_format": "markdown",
            "group_by": "timestamp_hour"
        })
        .build(),

        # Multi-API orchestration
        TaskBuilder()
        .with_name("Multi-Source Data Integration")
        .with_description("Fetch data from multiple APIs, combine, and analyze")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.WEB_API)
        .with_input({
            "sources": [
                {"url": "https://api.github.com/repos/python/cpython", "type": "github"},
                {"url": "https://pypi.org/pypi/requests/json", "type": "pypi"}
            ],
            "merge_on": "name",
            "output_fields": ["name", "description", "stars", "downloads"]
        })
        .build(),

        # Code Generation + Testing
        TaskBuilder()
        .with_name("Generate Class with Tests")
        .with_description("Generate a Python class with unit tests and documentation")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.CODE_GENERATION)
        .with_input({
            "class_name": "BankAccount",
            "methods": ["deposit", "withdraw", "get_balance"],
            "include_tests": True,
            "include_docstrings": True,
            "test_framework": "pytest"
        })
        .build(),

        # Skill Integration
        TaskBuilder()
        .with_name("Text Processing with Skills")
        .with_description("Use text-processing skill for advanced text operations")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.SKILL_INTEGRATION)
        .with_input({
            "text": "Contact us at support@example.com or sales@test.org. Visit https://example.com",
            "operations": ["extract_emails", "extract_urls", "word_count", "to_uppercase"]
        })
        .build(),

        # Task Scheduling + Automation
        TaskBuilder()
        .with_name("Complex Scheduled Workflow")
        .with_description("Create multi-step scheduled workflow with dependencies")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.TASK_SCHEDULING)
        .with_input({
            "workflow_name": "daily_data_pipeline",
            "steps": [
                {"name": "fetch_data", "schedule": "0 1 * * *"},
                {"name": "process_data", "depends_on": "fetch_data"},
                {"name": "generate_report", "depends_on": "process_data"},
                {"name": "send_email", "depends_on": "generate_report"}
            ]
        })
        .build(),

        # Model Selection
        TaskBuilder()
        .with_name("Adaptive Model Selection")
        .with_description("Test if appropriate models are selected for different task types")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.MODEL_SELECTION)
        .with_input({
            "tasks": [
                {"type": "simple_chat", "expected_model": "deepseek-chat"},
                {"type": "complex_reasoning", "expected_model": "deepseek-reasoner"},
                {"type": "code_generation", "expected_model": "deepseek-coder"}
            ]
        })
        .build(),
    ]


def create_level4_scenarios() -> list[BenchmarkTask]:
    """
    Level 4 (Expert Tasks): 10+ steps, deep reasoning, 10+ tool uses, adaptive replanning.
    Expected success rate: ≥50%, Response time: ≤300s
    """
    return [
        # End-to-end Feature Development
        TaskBuilder()
        .with_name("Complete Feature Implementation")
        .with_description("Implement a complete feature with code, tests, and documentation")
        .with_complexity(TaskComplexity.LEVEL_4_EXPERT)
        .with_category(TaskCategory.CODE_GENERATION)
        .with_input({
            "feature_name": "user_authentication",
            "requirements": [
                "User registration with email validation",
                "Login/logout functionality",
                "Password hashing and security",
                "Session management"
            ],
            "deliverables": ["source_code", "unit_tests", "integration_tests", "API_docs", "user_guide"]
        })
        .build(),

        # Complex Debugging
        TaskBuilder()
        .with_name("Debug Complex System Issue")
        .with_description("Investigate and fix a complex multi-component system issue")
        .with_complexity(TaskComplexity.LEVEL_4_EXPERT)
        .with_category(TaskCategory.CODE_GENERATION)
        .with_input({
            "symptoms": "Application crashes intermittently under load",
            "logs_path": "logs/error.log",
            "codebase_path": "alpha/",
            "expected_actions": [
                "analyze_logs",
                "identify_root_cause",
                "propose_fix",
                "implement_fix",
                "create_tests",
                "verify_fix"
            ]
        })
        .build(),

        # System Integration
        TaskBuilder()
        .with_name("Multi-Service Integration")
        .with_description("Integrate multiple external services with error handling and fallbacks")
        .with_complexity(TaskComplexity.LEVEL_4_EXPERT)
        .with_category(TaskCategory.WEB_API)
        .with_input({
            "services": [
                {"name": "payment_gateway", "priority": 1, "fallback": "secondary_payment"},
                {"name": "email_service", "priority": 1, "fallback": "backup_email"},
                {"name": "sms_service", "priority": 2, "fallback": None}
            ],
            "requirements": [
                "implement_retry_logic",
                "implement_circuit_breaker",
                "add_comprehensive_logging",
                "create_monitoring_dashboard",
                "write_integration_tests"
            ]
        })
        .build(),

        # Autonomous Problem Solving
        TaskBuilder()
        .with_name("Adaptive Problem Resolution")
        .with_description("Solve a problem by trying multiple approaches until success")
        .with_complexity(TaskComplexity.LEVEL_4_EXPERT)
        .with_category(TaskCategory.CODE_GENERATION)
        .with_input({
            "problem": "Create a data pipeline that works despite API limitations",
            "constraints": [
                "Primary API has rate limits",
                "Secondary API has incomplete data",
                "Must deliver results within time window"
            ],
            "expected_behavior": "Try multiple strategies until successful",
            "success_criteria": "Complete data pipeline delivering accurate results"
        })
        .build(),

        # Complete Workflow Automation
        TaskBuilder()
        .with_name("End-to-End Workflow Automation")
        .with_description("Design and implement complete automated workflow")
        .with_complexity(TaskComplexity.LEVEL_4_EXPERT)
        .with_category(TaskCategory.TASK_SCHEDULING)
        .with_input({
            "workflow_description": "Automated CI/CD pipeline for Python project",
            "components": [
                "code_quality_checks",
                "automated_testing",
                "security_scanning",
                "build_and_package",
                "deployment_staging",
                "integration_tests_staging",
                "deployment_production",
                "monitoring_setup",
                "rollback_capability"
            ],
            "error_handling": "automatic_rollback_on_failure",
            "notifications": ["email", "slack"]
        })
        .build(),
    ]


def create_all_scenarios() -> list[BenchmarkTask]:
    """Create complete benchmark test suite with all complexity levels."""
    scenarios = []
    scenarios.extend(create_level1_scenarios())
    scenarios.extend(create_level2_scenarios())
    scenarios.extend(create_level3_scenarios())
    scenarios.extend(create_level4_scenarios())
    return scenarios
