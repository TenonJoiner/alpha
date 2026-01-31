"""
Unit tests for workflow definition module
"""

import pytest
from datetime import datetime

from alpha.workflow.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParameter,
    WorkflowTrigger,
    ParameterType,
    TriggerType,
    StepErrorStrategy,
    RetryConfig,
)


def test_workflow_parameter_creation():
    """Test WorkflowParameter creation"""
    param = WorkflowParameter(
        name="email_account",
        type=ParameterType.STRING,
        default="primary",
        description="Email account to check",
        required=False,
    )

    assert param.name == "email_account"
    assert param.type == ParameterType.STRING
    assert param.default == "primary"
    assert param.required is False


def test_workflow_parameter_to_dict():
    """Test WorkflowParameter serialization"""
    param = WorkflowParameter(
        name="count", type=ParameterType.INTEGER, default=10
    )

    param_dict = param.to_dict()

    assert param_dict["name"] == "count"
    assert param_dict["type"] == "integer"
    assert param_dict["default"] == 10


def test_workflow_parameter_from_dict():
    """Test WorkflowParameter deserialization"""
    param_dict = {
        "name": "enabled",
        "type": "boolean",
        "default": True,
        "description": "Enable feature",
        "required": False,
    }

    param = WorkflowParameter.from_dict(param_dict)

    assert param.name == "enabled"
    assert param.type == ParameterType.BOOLEAN
    assert param.default is True


def test_workflow_trigger_creation():
    """Test WorkflowTrigger creation"""
    trigger = WorkflowTrigger(
        type=TriggerType.SCHEDULE, config={"cron": "0 9 * * *"}
    )

    assert trigger.type == TriggerType.SCHEDULE
    assert trigger.config["cron"] == "0 9 * * *"


def test_workflow_step_creation():
    """Test WorkflowStep creation"""
    step = WorkflowStep(
        id="fetch_data",
        tool="http",
        action="get",
        parameters={"url": "https://api.example.com"},
        on_error=StepErrorStrategy.RETRY,
        retry=RetryConfig(max_attempts=3, backoff="exponential"),
    )

    assert step.id == "fetch_data"
    assert step.tool == "http"
    assert step.action == "get"
    assert step.on_error == StepErrorStrategy.RETRY
    assert step.retry.max_attempts == 3


def test_workflow_step_to_dict():
    """Test WorkflowStep serialization"""
    step = WorkflowStep(
        id="step1",
        tool="shell",
        action="execute",
        parameters={"command": "ls -la"},
        on_error=StepErrorStrategy.ABORT,
    )

    step_dict = step.to_dict()

    assert step_dict["id"] == "step1"
    assert step_dict["tool"] == "shell"
    assert step_dict["on_error"] == "abort"


def test_workflow_step_from_dict():
    """Test WorkflowStep deserialization"""
    step_dict = {
        "id": "step2",
        "tool": "email",
        "action": "send",
        "parameters": {"to": "user@example.com"},
        "on_error": "retry",
        "retry": {"max_attempts": 5, "backoff": "linear"},
    }

    step = WorkflowStep.from_dict(step_dict)

    assert step.id == "step2"
    assert step.tool == "email"
    assert step.on_error == StepErrorStrategy.RETRY
    assert step.retry.max_attempts == 5


def test_workflow_definition_creation():
    """Test WorkflowDefinition creation"""
    workflow = WorkflowDefinition(
        name="Test Workflow",
        version="1.0.0",
        description="A test workflow",
        author="tester",
        tags=["test", "demo"],
    )

    assert workflow.name == "Test Workflow"
    assert workflow.version == "1.0.0"
    assert "test" in workflow.tags
    assert workflow.created_at is not None


def test_workflow_definition_with_steps():
    """Test WorkflowDefinition with steps"""
    steps = [
        WorkflowStep(
            id="step1", tool="shell", action="execute", parameters={"command": "echo hello"}
        ),
        WorkflowStep(
            id="step2", tool="file", action="write", parameters={"path": "output.txt"}
        ),
    ]

    workflow = WorkflowDefinition(
        name="Multi-step Workflow", version="1.0.0", steps=steps
    )

    assert len(workflow.steps) == 2
    assert workflow.get_step("step1").tool == "shell"


def test_workflow_validation_valid():
    """Test workflow validation for valid workflow"""
    workflow = WorkflowDefinition(
        name="Valid Workflow",
        version="1.0.0",
        steps=[
            WorkflowStep(id="step1", tool="test", action="run", parameters={})
        ],
    )

    is_valid, errors = workflow.validate()

    assert is_valid is True
    assert len(errors) == 0


def test_workflow_validation_no_name():
    """Test workflow validation fails without name"""
    workflow = WorkflowDefinition(name="", version="1.0.0", steps=[])

    is_valid, errors = workflow.validate()

    assert is_valid is False
    assert any("name" in err.lower() for err in errors)


def test_workflow_validation_no_steps():
    """Test workflow validation fails without steps"""
    workflow = WorkflowDefinition(name="Empty Workflow", version="1.0.0", steps=[])

    is_valid, errors = workflow.validate()

    assert is_valid is False
    assert any("step" in err.lower() for err in errors)


def test_workflow_validation_duplicate_step_ids():
    """Test workflow validation fails with duplicate step IDs"""
    steps = [
        WorkflowStep(id="step1", tool="test", action="run", parameters={}),
        WorkflowStep(id="step1", tool="test", action="run", parameters={}),
    ]

    workflow = WorkflowDefinition(
        name="Duplicate Steps", version="1.0.0", steps=steps
    )

    is_valid, errors = workflow.validate()

    assert is_valid is False
    assert any("unique" in err.lower() for err in errors)


def test_workflow_validation_invalid_dependency():
    """Test workflow validation fails with invalid dependency"""
    steps = [
        WorkflowStep(
            id="step1",
            tool="test",
            action="run",
            parameters={},
            depends_on=["nonexistent"],
        )
    ]

    workflow = WorkflowDefinition(
        name="Invalid Dependency", version="1.0.0", steps=steps
    )

    is_valid, errors = workflow.validate()

    assert is_valid is False
    assert any("depend" in err.lower() for err in errors)


def test_workflow_validation_circular_dependency():
    """Test workflow validation detects circular dependencies"""
    steps = [
        WorkflowStep(
            id="step1", tool="test", action="run", parameters={}, depends_on=["step2"]
        ),
        WorkflowStep(
            id="step2", tool="test", action="run", parameters={}, depends_on=["step1"]
        ),
    ]

    workflow = WorkflowDefinition(
        name="Circular Dependency", version="1.0.0", steps=steps
    )

    is_valid, errors = workflow.validate()

    assert is_valid is False
    assert any("circular" in err.lower() for err in errors)


def test_workflow_to_dict():
    """Test workflow serialization to dictionary"""
    workflow = WorkflowDefinition(
        name="Serialize Test",
        version="1.0.0",
        description="Test serialization",
        steps=[
            WorkflowStep(id="step1", tool="test", action="run", parameters={})
        ],
    )

    workflow_dict = workflow.to_dict()

    assert workflow_dict["name"] == "Serialize Test"
    assert workflow_dict["version"] == "1.0.0"
    assert len(workflow_dict["steps"]) == 1
    assert "created_at" in workflow_dict


def test_workflow_from_dict():
    """Test workflow deserialization from dictionary"""
    workflow_dict = {
        "id": "test-id",
        "name": "Deserialize Test",
        "version": "1.0.0",
        "description": "Test deserialization",
        "author": "tester",
        "tags": ["test"],
        "parameters": [],
        "triggers": [],
        "steps": [
            {
                "id": "step1",
                "tool": "test",
                "action": "run",
                "parameters": {},
                "on_error": "abort",
            }
        ],
        "outputs": {},
    }

    workflow = WorkflowDefinition.from_dict(workflow_dict)

    assert workflow.name == "Deserialize Test"
    assert workflow.version == "1.0.0"
    assert len(workflow.steps) == 1


def test_workflow_get_independent_steps():
    """Test getting independent steps for parallel execution"""
    steps = [
        WorkflowStep(id="step1", tool="test", action="run", parameters={}),
        WorkflowStep(id="step2", tool="test", action="run", parameters={}),
        WorkflowStep(
            id="step3",
            tool="test",
            action="run",
            parameters={},
            depends_on=["step1", "step2"],
        ),
    ]

    workflow = WorkflowDefinition(
        name="Parallel Steps", version="1.0.0", steps=steps
    )

    execution_order = workflow.get_independent_steps()

    # First group should have step1 and step2 (can run in parallel)
    assert len(execution_order) == 2
    assert set(execution_order[0]) == {"step1", "step2"}
    assert execution_order[1] == ["step3"]


def test_retry_config():
    """Test RetryConfig"""
    retry = RetryConfig(
        max_attempts=5, backoff="linear", initial_delay=2.0, max_delay=30.0
    )

    assert retry.max_attempts == 5
    assert retry.backoff == "linear"
    assert retry.initial_delay == 2.0
    assert retry.max_delay == 30.0
