"""
Benchmark task definitions and result structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime
import uuid

from .benchmark_framework import TaskComplexity, TaskCategory, EvaluationDimensions


@dataclass
class BenchmarkTask:
    """
    Definition of a single benchmark task.

    Attributes:
        task_id: Unique identifier for the task
        name: Human-readable task name
        description: Detailed task description
        complexity: Task complexity level
        category: Task category
        input_data: Input data for the task
        expected_output: Expected output or validation criteria
        validation_fn: Optional custom validation function
        metadata: Additional task metadata
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    complexity: TaskComplexity = TaskComplexity.LEVEL_1_SIMPLE
    category: TaskCategory = TaskCategory.FILE_SYSTEM
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[Any] = None
    validation_fn: Optional[Callable[[Any, Any], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task definition."""
        if not self.name:
            raise ValueError("Task name is required")
        if not self.description:
            raise ValueError("Task description is required")


@dataclass
class TaskResult:
    """
    Result of a benchmark task execution.

    Attributes:
        task_id: ID of the executed task
        task_name: Name of the executed task
        complexity: Task complexity level
        category: Task category
        success: Overall task success status
        actual_output: Actual output produced
        evaluation: Multi-dimensional evaluation metrics
        execution_log: Detailed execution log
        error_message: Error message if task failed
        start_time: Task execution start time
        end_time: Task execution end time
        metadata: Additional result metadata
    """
    task_id: str
    task_name: str
    complexity: TaskComplexity
    category: TaskCategory
    success: bool
    actual_output: Optional[Any] = None
    evaluation: EvaluationDimensions = field(default_factory=EvaluationDimensions)
    execution_log: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get task execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "complexity": self.complexity.value,
            "category": self.category.value,
            "success": self.success,
            "actual_output": str(self.actual_output) if self.actual_output else None,
            "evaluation": {
                "task_completion": self.evaluation.task_completion,
                "partial_completion": self.evaluation.partial_completion,
                "reasoning_quality": self.evaluation.reasoning_quality,
                "tool_usage_accuracy": self.evaluation.tool_usage_accuracy,
                "response_time": self.evaluation.response_time,
                "api_cost": self.evaluation.api_cost,
                "error_recovery_attempts": self.evaluation.error_recovery_attempts,
                "error_recovery_success": self.evaluation.error_recovery_success,
                "consistency_score": self.evaluation.consistency_score,
            },
            "execution_log": self.execution_log,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": self.duration,
            "metadata": self.metadata,
        }


class TaskBuilder:
    """Builder for creating benchmark tasks with fluent API."""

    def __init__(self):
        """Initialize task builder."""
        self._task_data = {}

    def with_id(self, task_id: str) -> 'TaskBuilder':
        """Set task ID."""
        self._task_data['task_id'] = task_id
        return self

    def with_name(self, name: str) -> 'TaskBuilder':
        """Set task name."""
        self._task_data['name'] = name
        return self

    def with_description(self, description: str) -> 'TaskBuilder':
        """Set task description."""
        self._task_data['description'] = description
        return self

    def with_complexity(self, complexity: TaskComplexity) -> 'TaskBuilder':
        """Set task complexity."""
        self._task_data['complexity'] = complexity
        return self

    def with_category(self, category: TaskCategory) -> 'TaskBuilder':
        """Set task category."""
        self._task_data['category'] = category
        return self

    def with_input(self, input_data: Dict[str, Any]) -> 'TaskBuilder':
        """Set task input data."""
        self._task_data['input_data'] = input_data
        return self

    def with_expected_output(self, expected: Any) -> 'TaskBuilder':
        """Set expected output."""
        self._task_data['expected_output'] = expected
        return self

    def with_validation(self, validation_fn: Callable[[Any, Any], bool]) -> 'TaskBuilder':
        """Set custom validation function."""
        self._task_data['validation_fn'] = validation_fn
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'TaskBuilder':
        """Set task metadata."""
        self._task_data['metadata'] = metadata
        return self

    def build(self) -> BenchmarkTask:
        """Build the benchmark task."""
        return BenchmarkTask(**self._task_data)
