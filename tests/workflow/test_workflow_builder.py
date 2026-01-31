"""
Unit tests for workflow builder module
"""

import pytest

from alpha.workflow.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParameter,
    ParameterType,
    TriggerType,
    StepErrorStrategy,
)
from alpha.workflow.builder import WorkflowBuilder


@pytest.fixture
def builder():
    """Create WorkflowBuilder instance"""
    return WorkflowBuilder()


def test_build_simple_workflow(builder):
    """Test building simple workflow"""
    workflow = builder.build(
        name="Test Workflow",
        description="A test workflow",
        version="1.0.0",
        steps=[
            {
                "id": "step1",
                "tool": "shell",
                "action": "execute",
                "parameters": {"command": "echo hello"},
            }
        ],
    )

    assert workflow.name == "Test Workflow"
    assert workflow.version == "1.0.0"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].tool == "shell"


def test_build_with_parameters(builder):
    """Test building workflow with parameters"""
    workflow = builder.build(
        name="Parameterized Workflow",
        version="1.0.0",
        parameters=[
            {
                "name": "message",
                "type": "string",
                "default": "hello",
                "description": "Message to display",
            }
        ],
        steps=[
            {
                "id": "step1",
                "tool": "test",
                "action": "run",
                "parameters": {"message": "{{message}}"},
            }
        ],
    )

    assert len(workflow.parameters) == 1
    assert workflow.parameters[0].name == "message"
    assert workflow.parameters[0].type == ParameterType.STRING


def test_build_with_triggers(builder):
    """Test building workflow with triggers"""
    workflow = builder.build(
        name="Triggered Workflow",
        version="1.0.0",
        triggers=[{"type": "schedule", "config": {"cron": "0 9 * * *"}}],
        steps=[
            {"id": "step1", "tool": "test", "action": "run", "parameters": {}}
        ],
    )

    assert len(workflow.triggers) == 1
    assert workflow.triggers[0].type == TriggerType.SCHEDULE
    assert workflow.triggers[0].config["cron"] == "0 9 * * *"


def test_build_with_tags(builder):
    """Test building workflow with tags"""
    workflow = builder.build(
        name="Tagged Workflow",
        version="1.0.0",
        tags=["production", "critical"],
        steps=[
            {"id": "step1", "tool": "test", "action": "run", "parameters": {}}
        ],
    )

    assert "production" in workflow.tags
    assert "critical" in workflow.tags


def test_build_with_retry(builder):
    """Test building workflow with retry configuration"""
    workflow = builder.build(
        name="Retry Workflow",
        version="1.0.0",
        steps=[
            {
                "id": "step1",
                "tool": "test",
                "action": "run",
                "parameters": {},
                "on_error": "retry",
                "retry": {
                    "max_attempts": 5,
                    "backoff": "exponential",
                    "initial_delay": 1.0,
                    "max_delay": 60.0,
                },
            }
        ],
    )

    assert workflow.steps[0].on_error == StepErrorStrategy.RETRY
    assert workflow.steps[0].retry.max_attempts == 5
    assert workflow.steps[0].retry.backoff == "exponential"


def test_build_with_dependencies(builder):
    """Test building workflow with step dependencies"""
    workflow = builder.build(
        name="Dependency Workflow",
        version="1.0.0",
        steps=[
            {"id": "step1", "tool": "test", "action": "run", "parameters": {}},
            {
                "id": "step2",
                "tool": "test",
                "action": "run",
                "parameters": {},
                "depends_on": ["step1"],
            },
        ],
    )

    assert workflow.steps[1].depends_on == ["step1"]


def test_build_from_tasks(builder):
    """Test building workflow from task history"""
    task_history = [
        {
            "tool": "git",
            "action": "pull",
            "parameters": {"repository": "/path/to/repo"},
        },
        {"tool": "shell", "action": "execute", "parameters": {"command": "pytest"}},
    ]

    workflow = builder.build_from_tasks(
        name="Git and Test",
        task_history=task_history,
        description="Pull code and run tests",
    )

    assert workflow.name == "Git and Test"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].tool == "git"
    assert workflow.steps[1].tool == "shell"


def test_build_from_tasks_with_parameters(builder):
    """Test building workflow from tasks extracts parameters"""
    task_history = [
        {
            "tool": "http",
            "action": "get",
            "parameters": {"url": "https://api.example.com", "timeout": 30},
        }
    ]

    workflow = builder.build_from_tasks(
        name="API Call", task_history=task_history
    )

    # Should create parameters for URL and timeout
    assert len(workflow.parameters) > 0


def test_build_simple(builder):
    """Test building simple workflow from tool-action pairs"""
    tool_actions = [
        ("git", "pull", {"repository": "/path/to/repo"}),
        ("shell", "execute", {"command": "pytest"}),
    ]

    workflow = builder.build_simple(
        name="Simple Workflow",
        tool_actions=tool_actions,
        description="Pull and test",
    )

    assert workflow.name == "Simple Workflow"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].tool == "git"
    assert workflow.steps[1].tool == "shell"


def test_infer_parameter_type(builder):
    """Test parameter type inference"""
    assert builder._infer_type("hello") == "string"
    assert builder._infer_type(42) == "integer"
    assert builder._infer_type(3.14) == "float"
    assert builder._infer_type(True) == "boolean"
    assert builder._infer_type([1, 2, 3]) == "list"
    assert builder._infer_type({"key": "value"}) == "dict"


def test_is_parameterizable(builder):
    """Test parameterizability check"""
    assert builder._is_parameterizable("long string value") is True
    assert builder._is_parameterizable("abc") is False  # Too short
    assert builder._is_parameterizable(42) is True
    assert builder._is_parameterizable(3.14) is True
    assert builder._is_parameterizable("{{var}}") is False  # Already a template


def test_build_step(builder):
    """Test building individual step"""
    step_data = {
        "id": "test_step",
        "tool": "shell",
        "action": "execute",
        "parameters": {"command": "ls -la"},
        "on_error": "retry",
        "retry": {"max_attempts": 3},
    }

    step = builder._build_step(step_data)

    assert step.id == "test_step"
    assert step.tool == "shell"
    assert step.on_error == StepErrorStrategy.RETRY
    assert step.retry.max_attempts == 3


def test_build_parameter(builder):
    """Test building individual parameter"""
    param_data = {
        "name": "timeout",
        "type": "integer",
        "default": 30,
        "description": "Request timeout",
        "required": True,
    }

    param = builder._build_parameter(param_data)

    assert param.name == "timeout"
    assert param.type == ParameterType.INTEGER
    assert param.default == 30
    assert param.required is True


def test_build_trigger(builder):
    """Test building individual trigger"""
    trigger_data = {"type": "schedule", "config": {"cron": "0 */2 * * *"}}

    trigger = builder._build_trigger(trigger_data)

    assert trigger.type == TriggerType.SCHEDULE
    assert trigger.config["cron"] == "0 */2 * * *"
