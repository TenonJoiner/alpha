"""
Unit tests for workflow executor module
"""

import pytest
import asyncio

from alpha.workflow.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParameter,
    ParameterType,
    StepErrorStrategy,
    RetryConfig,
)
from alpha.workflow.executor import (
    WorkflowExecutor,
    ExecutionContext,
    ExecutionResult,
)


@pytest.fixture
def executor():
    """Create WorkflowExecutor instance"""
    return WorkflowExecutor()


@pytest.fixture
def simple_workflow():
    """Create simple workflow for testing"""
    return WorkflowDefinition(
        name="Simple Workflow",
        version="1.0.0",
        steps=[
            WorkflowStep(
                id="step1",
                tool="test",
                action="execute",
                parameters={"input": "hello"},
            ),
            WorkflowStep(
                id="step2",
                tool="test",
                action="execute",
                parameters={"input": "world"},
            ),
        ],
    )


@pytest.fixture
def parameterized_workflow():
    """Create workflow with parameters"""
    return WorkflowDefinition(
        name="Parameterized Workflow",
        version="1.0.0",
        parameters=[
            WorkflowParameter(
                name="message", type=ParameterType.STRING, default="default message"
            ),
            WorkflowParameter(name="count", type=ParameterType.INTEGER, default=1),
        ],
        steps=[
            WorkflowStep(
                id="step1",
                tool="test",
                action="execute",
                parameters={"message": "{{message}}", "count": "{{count}}"},
            )
        ],
    )


def test_execution_context_creation():
    """Test creating execution context"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"key": "value"}
    )

    assert context.workflow_id == "wf-123"
    assert context.execution_id == "exec-456"
    assert context.parameters["key"] == "value"


def test_execution_context_get_parameter():
    """Test getting parameter from context"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"param1": "value1"}
    )

    assert context.get("param1") == "value1"
    assert context.get("nonexistent") is None
    assert context.get("nonexistent", "default") == "default"


def test_execution_context_step_output():
    """Test storing and retrieving step output"""
    context = ExecutionContext(workflow_id="wf-123", execution_id="exec-456")

    context.set_step_output("step1", {"result": "success", "count": 42})

    assert context.get_step_output("step1") == {"result": "success", "count": 42}
    assert context.get_step_output("step1", "result") == "success"
    assert context.get_step_output("step1", "count") == 42


@pytest.mark.asyncio
async def test_execute_simple_workflow(executor, simple_workflow):
    """Test executing simple workflow"""
    result = await executor.execute(simple_workflow)

    assert result.status in ["completed", "partial"]
    assert result.workflow_id == simple_workflow.id
    assert result.steps_total == 2


@pytest.mark.asyncio
async def test_execute_with_parameters(executor, parameterized_workflow):
    """Test executing workflow with parameters"""
    result = await executor.execute(
        parameterized_workflow, parameters={"message": "test message", "count": 5}
    )

    assert result.status in ["completed", "partial"]


@pytest.mark.asyncio
async def test_execute_invalid_workflow(executor):
    """Test executing invalid workflow fails"""
    invalid_workflow = WorkflowDefinition(name="", version="1.0.0", steps=[])

    result = await executor.execute(invalid_workflow)

    assert result.status == "failed"
    assert "Invalid workflow" in result.error


def test_merge_parameters(executor):
    """Test merging runtime parameters with defaults"""
    workflow = WorkflowDefinition(
        name="Test",
        version="1.0.0",
        parameters=[
            WorkflowParameter(name="param1", type=ParameterType.STRING, default="default1"),
            WorkflowParameter(name="param2", type=ParameterType.STRING, default="default2"),
        ],
        steps=[],
    )

    merged = executor._merge_parameters(workflow, {"param1": "override"})

    assert merged["param1"] == "override"
    assert merged["param2"] == "default2"


def test_inject_parameters_simple(executor):
    """Test simple parameter injection"""
    context = ExecutionContext(
        workflow_id="wf-123",
        execution_id="exec-456",
        parameters={"name": "Alice", "age": 30},
    )

    template = {"greeting": "Hello, {{name}}!", "info": "Age: {{age}}"}

    result = executor._inject_parameters(template, context)

    assert result["greeting"] == "Hello, Alice!"
    assert result["info"] == "Age: 30"


def test_inject_parameters_step_output(executor):
    """Test injecting parameters from step outputs"""
    context = ExecutionContext(workflow_id="wf-123", execution_id="exec-456")
    context.set_step_output("step1", {"result": "success", "count": 42})

    template = {"message": "Result: {{step1.result}}", "total": "{{step1.count}}"}

    result = executor._inject_parameters(template, context)

    assert result["message"] == "Result: success"
    assert result["total"] == 42


def test_interpolate_string(executor):
    """Test string interpolation"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"name": "Bob"}
    )

    result = executor._interpolate_string("Hello, {{name}}!", context)

    assert result == "Hello, Bob!"


def test_interpolate_full_variable(executor):
    """Test interpolating full variable (returns actual type)"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"count": 42}
    )

    result = executor._interpolate_string("{{count}}", context)

    assert result == 42
    assert isinstance(result, int)


def test_evaluate_condition_true(executor):
    """Test condition evaluation returns True"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"count": 10}
    )

    # Note: This uses eval() which is not safe in production
    # In real implementation, use a safe expression evaluator
    result = executor._evaluate_condition("{{count}} > 5", context)

    assert result is True


def test_evaluate_condition_false(executor):
    """Test condition evaluation returns False"""
    context = ExecutionContext(
        workflow_id="wf-123", execution_id="exec-456", parameters={"count": 3}
    )

    result = executor._evaluate_condition("{{count}} > 5", context)

    assert result is False


def test_evaluate_outputs(executor):
    """Test evaluating workflow outputs"""
    context = ExecutionContext(workflow_id="wf-123", execution_id="exec-456")
    context.set_step_output("step1", {"result": "success"})
    context.set_step_output("step2", {"count": 42})

    output_template = {
        "final_result": "{{step1.result}}",
        "total_count": "{{step2.count}}",
    }

    outputs = executor._evaluate_outputs(output_template, context)

    assert outputs["final_result"] == "success"
    assert outputs["total_count"] == 42


def test_execute_sync(executor, simple_workflow):
    """Test synchronous execution wrapper"""
    result = executor.execute_sync(simple_workflow)

    assert result.status in ["completed", "partial"]
    assert result.workflow_id == simple_workflow.id


@pytest.mark.asyncio
async def test_execute_with_dependencies(executor):
    """Test executing workflow with step dependencies"""
    workflow = WorkflowDefinition(
        name="Dependency Workflow",
        version="1.0.0",
        steps=[
            WorkflowStep(id="step1", tool="test", action="run", parameters={}),
            WorkflowStep(id="step2", tool="test", action="run", parameters={}),
            WorkflowStep(
                id="step3",
                tool="test",
                action="run",
                parameters={},
                depends_on=["step1", "step2"],
            ),
        ],
    )

    result = await executor.execute(workflow)

    assert result.status in ["completed", "partial"]
    assert result.steps_total == 3


@pytest.mark.asyncio
async def test_execute_with_outputs(executor):
    """Test workflow execution with outputs"""
    workflow = WorkflowDefinition(
        name="Output Workflow",
        version="1.0.0",
        steps=[
            WorkflowStep(id="step1", tool="test", action="run", parameters={}),
        ],
        outputs={"result": "{{step1.result}}"},
    )

    result = await executor.execute(workflow)

    assert result.status in ["completed", "partial"]
    assert "result" in result.outputs
