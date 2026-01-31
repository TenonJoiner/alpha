"""
Core benchmark framework for Alpha Agent evaluation.

Implements multi-dimensional evaluation inspired by:
- AgentBench: Multi-environment agent evaluation
- GAIA: Complexity-stratified general assistant benchmarking
- τ-Bench: Real-world task evaluation with policies
- SWE-bench: Software engineering task benchmarking
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels aligned with GAIA benchmark methodology."""
    LEVEL_1_SIMPLE = "level_1_simple"  # 1-2 steps, 1-2 tools, minimal reasoning
    LEVEL_2_MEDIUM = "level_2_medium"  # 3-5 steps, 3-5 tools, moderate reasoning
    LEVEL_3_COMPLEX = "level_3_complex"  # 6-10 steps, 6-10 tools, advanced reasoning
    LEVEL_4_EXPERT = "level_4_expert"  # 10+ steps, 10+ tools, deep reasoning


class TaskCategory(Enum):
    """Categories of tasks covering Alpha's core capabilities."""
    FILE_SYSTEM = "file_system"
    DATA_PROCESSING = "data_processing"
    WEB_API = "web_api"
    INFORMATION_RETRIEVAL = "information_retrieval"
    CODE_GENERATION = "code_generation"
    TASK_SCHEDULING = "task_scheduling"
    SKILL_INTEGRATION = "skill_integration"
    MODEL_SELECTION = "model_selection"


@dataclass
class PerformanceTargets:
    """Performance targets for each complexity level."""
    success_rate: float  # Expected success rate (0.0-1.0)
    max_response_time: float  # Maximum acceptable response time in seconds

    @classmethod
    def for_complexity(cls, complexity: TaskComplexity) -> 'PerformanceTargets':
        """Get performance targets for a given complexity level."""
        targets = {
            TaskComplexity.LEVEL_1_SIMPLE: cls(success_rate=0.95, max_response_time=1.0),
            TaskComplexity.LEVEL_2_MEDIUM: cls(success_rate=0.85, max_response_time=10.0),
            TaskComplexity.LEVEL_3_COMPLEX: cls(success_rate=0.70, max_response_time=60.0),
            TaskComplexity.LEVEL_4_EXPERT: cls(success_rate=0.50, max_response_time=300.0),
        }
        return targets[complexity]


@dataclass
class EvaluationDimensions:
    """Multi-dimensional evaluation metrics for benchmark tasks."""
    task_completion: bool = False  # Task completed successfully
    partial_completion: bool = False  # Task partially completed
    reasoning_quality: float = 0.0  # Quality of reasoning (0.0-1.0)
    tool_usage_accuracy: float = 0.0  # Correct tool selection and usage (0.0-1.0)
    response_time: float = 0.0  # Time to completion in seconds
    api_cost: float = 0.0  # Estimated API cost
    error_recovery_attempts: int = 0  # Number of recovery attempts made
    error_recovery_success: bool = False  # Successfully recovered from errors
    consistency_score: float = 0.0  # Multi-step task consistency (0.0-1.0)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""
    parallel_execution: bool = True
    max_parallel_tasks: int = 5
    timeout_multiplier: float = 1.5  # Multiply target response time for timeout
    enable_detailed_logging: bool = True
    save_execution_traces: bool = True
    compare_with_baseline: bool = False
    baseline_results_path: Optional[str] = None


class BenchmarkFramework:
    """
    Main benchmark framework for evaluating Alpha Agent.

    Provides infrastructure for:
    - Multi-dimensional evaluation
    - Complexity-stratified testing
    - Performance metrics calculation
    - Result aggregation and analysis
    """

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize benchmark framework.

        Args:
            config: Benchmark configuration settings
        """
        self.config = config or BenchmarkConfig()
        self.tasks: List['BenchmarkTask'] = []
        self.results: List['TaskResult'] = []

    def register_task(self, task: 'BenchmarkTask') -> None:
        """
        Register a benchmark task for execution.

        Args:
            task: Benchmark task to register
        """
        self.tasks.append(task)
        logger.debug(f"Registered task: {task.task_id} ({task.complexity.value})")

    def register_task_suite(self, tasks: List['BenchmarkTask']) -> None:
        """
        Register multiple benchmark tasks.

        Args:
            tasks: List of benchmark tasks to register
        """
        for task in tasks:
            self.register_task(task)

    def get_tasks_by_complexity(self, complexity: TaskComplexity) -> List['BenchmarkTask']:
        """
        Get all tasks of a specific complexity level.

        Args:
            complexity: Task complexity level

        Returns:
            List of tasks matching the complexity level
        """
        return [task for task in self.tasks if task.complexity == complexity]

    def get_tasks_by_category(self, category: TaskCategory) -> List['BenchmarkTask']:
        """
        Get all tasks of a specific category.

        Args:
            category: Task category

        Returns:
            List of tasks matching the category
        """
        return [task for task in self.tasks if task.category == category]

    def clear_results(self) -> None:
        """Clear all benchmark results."""
        self.results.clear()
        logger.info("Benchmark results cleared")

    def add_result(self, result: 'TaskResult') -> None:
        """
        Add a task execution result.

        Args:
            result: Task execution result
        """
        self.results.append(result)
        logger.debug(f"Added result for task: {result.task_id}")

    def get_results_by_complexity(self, complexity: TaskComplexity) -> List['TaskResult']:
        """
        Get results for a specific complexity level.

        Args:
            complexity: Task complexity level

        Returns:
            List of results for tasks of the given complexity
        """
        return [r for r in self.results if r.complexity == complexity]

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all benchmark results.

        Returns:
            Dictionary with summary statistics
        """
        if not self.results:
            return {"total_tasks": 0, "completed": 0, "success_rate": 0.0}

        total = len(self.results)
        completed = sum(1 for r in self.results if r.evaluation.task_completion)
        partial = sum(1 for r in self.results if r.evaluation.partial_completion)

        avg_response_time = sum(r.evaluation.response_time for r in self.results) / total
        total_cost = sum(r.evaluation.api_cost for r in self.results)

        recovery_attempts = sum(r.evaluation.error_recovery_attempts for r in self.results)
        recovery_successes = sum(1 for r in self.results if r.evaluation.error_recovery_success)

        return {
            "total_tasks": total,
            "completed": completed,
            "partial_completion": partial,
            "success_rate": completed / total if total > 0 else 0.0,
            "partial_success_rate": (completed + partial) / total if total > 0 else 0.0,
            "avg_response_time": avg_response_time,
            "total_api_cost": total_cost,
            "error_recovery_attempts": recovery_attempts,
            "error_recovery_rate": recovery_successes / recovery_attempts if recovery_attempts > 0 else 0.0,
        }
