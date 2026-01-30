"""
Unit tests for the benchmark framework itself.

These tests verify that the benchmark infrastructure works correctly
before running actual Alpha agent benchmarks.
"""

import pytest
import asyncio
from datetime import datetime

from tests.benchmarks import (
    BenchmarkFramework,
    BenchmarkRunner,
    TaskComplexity,
    TaskCategory,
    BenchmarkConfig,
    BenchmarkTask,
    TaskResult,
    EvaluationDimensions,
    MetricsCalculator,
    BenchmarkReporter,
)
from tests.benchmarks.tasks import TaskBuilder


@pytest.fixture
def sample_tasks():
    """Create sample benchmark tasks for testing."""
    return [
        TaskBuilder()
        .with_name("Simple Task 1")
        .with_description("A simple test task")
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE)
        .with_category(TaskCategory.FILE_SYSTEM)
        .build(),

        TaskBuilder()
        .with_name("Medium Task 1")
        .with_description("A medium complexity task")
        .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
        .with_category(TaskCategory.DATA_PROCESSING)
        .build(),

        TaskBuilder()
        .with_name("Complex Task 1")
        .with_description("A complex task")
        .with_complexity(TaskComplexity.LEVEL_3_COMPLEX)
        .with_category(TaskCategory.WEB_API)
        .build(),
    ]


@pytest.fixture
def sample_results():
    """Create sample task results for testing."""
    return [
        TaskResult(
            task_id="task1",
            task_name="Simple Task 1",
            complexity=TaskComplexity.LEVEL_1_SIMPLE,
            category=TaskCategory.FILE_SYSTEM,
            success=True,
            evaluation=EvaluationDimensions(
                task_completion=True,
                response_time=0.5,
                api_cost=0.001,
                tool_usage_accuracy=0.9,
            ),
        ),
        TaskResult(
            task_id="task2",
            task_name="Medium Task 1",
            complexity=TaskComplexity.LEVEL_2_MEDIUM,
            category=TaskCategory.DATA_PROCESSING,
            success=True,
            evaluation=EvaluationDimensions(
                task_completion=True,
                response_time=5.0,
                api_cost=0.005,
                tool_usage_accuracy=0.85,
            ),
        ),
        TaskResult(
            task_id="task3",
            task_name="Complex Task 1",
            complexity=TaskComplexity.LEVEL_3_COMPLEX,
            category=TaskCategory.WEB_API,
            success=False,
            evaluation=EvaluationDimensions(
                task_completion=False,
                partial_completion=True,
                response_time=45.0,
                api_cost=0.01,
                tool_usage_accuracy=0.6,
                error_recovery_attempts=2,
                error_recovery_success=False,
            ),
        ),
    ]


def test_task_builder():
    """Test TaskBuilder creates tasks correctly."""
    task = TaskBuilder() \
        .with_name("Test Task") \
        .with_description("Test description") \
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE) \
        .with_category(TaskCategory.FILE_SYSTEM) \
        .with_input({"key": "value"}) \
        .with_expected_output("expected") \
        .build()

    assert task.name == "Test Task"
    assert task.description == "Test description"
    assert task.complexity == TaskComplexity.LEVEL_1_SIMPLE
    assert task.category == TaskCategory.FILE_SYSTEM
    assert task.input_data == {"key": "value"}
    assert task.expected_output == "expected"


def test_benchmark_framework_registration(sample_tasks):
    """Test benchmark framework task registration."""
    framework = BenchmarkFramework()

    # Register tasks
    framework.register_task_suite(sample_tasks)

    assert len(framework.tasks) == 3

    # Test filtering by complexity
    simple_tasks = framework.get_tasks_by_complexity(TaskComplexity.LEVEL_1_SIMPLE)
    assert len(simple_tasks) == 1
    assert simple_tasks[0].name == "Simple Task 1"

    # Test filtering by category
    file_tasks = framework.get_tasks_by_category(TaskCategory.FILE_SYSTEM)
    assert len(file_tasks) == 1


def test_benchmark_framework_results(sample_results):
    """Test benchmark framework result management."""
    framework = BenchmarkFramework()

    # Add results
    for result in sample_results:
        framework.add_result(result)

    assert len(framework.results) == 3

    # Test summary stats
    stats = framework.get_summary_stats()
    assert stats["total_tasks"] == 3
    assert stats["completed"] == 2
    assert stats["partial_completion"] == 1
    assert stats["success_rate"] == pytest.approx(2/3, 0.01)


def test_metrics_calculator(sample_results):
    """Test metrics calculator scoring."""
    calculator = MetricsCalculator()

    score = calculator.calculate_score(sample_results)

    # Verify score structure
    assert 0 <= score.overall_score <= 100
    assert 0 <= score.success_rate_score <= 100
    assert 0 <= score.performance_score <= 100

    # Verify breakdowns exist
    assert len(score.complexity_breakdown) > 0
    assert len(score.category_breakdown) > 0

    # Verify analysis
    assert isinstance(score.strengths, list)
    assert isinstance(score.weaknesses, list)
    assert isinstance(score.recommendations, list)


def test_benchmark_reporter(sample_results):
    """Test benchmark reporter generation."""
    calculator = MetricsCalculator()
    reporter = BenchmarkReporter(output_dir="tests/benchmarks/reports/test")

    score = calculator.calculate_score(sample_results)

    # Generate reports
    reports = reporter.generate_report(score, sample_results, format="all", save=False)

    # Verify all formats generated
    assert "json" in reports
    assert "markdown" in reports
    assert "console" in reports

    # Verify JSON is valid
    import json
    json_data = json.loads(reports["json"])
    assert "overall_score" in json_data
    assert "complexity_breakdown" in json_data

    # Verify markdown has expected sections
    assert "# Alpha Agent Benchmark Report" in reports["markdown"]
    assert "## Executive Summary" in reports["markdown"]
    assert "## Analysis" in reports["markdown"]


@pytest.mark.asyncio
async def test_benchmark_runner():
    """Test benchmark runner execution."""
    framework = BenchmarkFramework()

    # Create simple test tasks
    task = TaskBuilder() \
        .with_name("Test Task") \
        .with_description("Simple test") \
        .with_complexity(TaskComplexity.LEVEL_1_SIMPLE) \
        .with_category(TaskCategory.FILE_SYSTEM) \
        .build()

    framework.register_task(task)

    # Mock executor
    async def mock_executor(task: BenchmarkTask) -> TaskResult:
        await asyncio.sleep(0.1)  # Simulate work
        return TaskResult(
            task_id=task.task_id,
            task_name=task.name,
            complexity=task.complexity,
            category=task.category,
            success=True,
            evaluation=EvaluationDimensions(
                task_completion=True,
                response_time=0.1,
                api_cost=0.001,
                tool_usage_accuracy=0.9,
            ),
        )

    # Create runner
    config = BenchmarkConfig(parallel_execution=False)
    runner = BenchmarkRunner(framework, mock_executor, config)

    # Run benchmarks
    score = await runner.run_all()

    # Verify execution
    assert len(framework.results) == 1
    assert framework.results[0].success
    assert score.overall_score > 0


def test_task_result_serialization():
    """Test task result can be serialized to dict."""
    result = TaskResult(
        task_id="test123",
        task_name="Test Task",
        complexity=TaskComplexity.LEVEL_1_SIMPLE,
        category=TaskCategory.FILE_SYSTEM,
        success=True,
    )

    result_dict = result.to_dict()

    assert result_dict["task_id"] == "test123"
    assert result_dict["task_name"] == "Test Task"
    assert result_dict["success"] is True
    assert "evaluation" in result_dict
    assert "duration" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
