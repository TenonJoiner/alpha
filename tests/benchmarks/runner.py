"""
Automated benchmark test runner.

Executes benchmark test suites and collects results.
"""

import asyncio
import logging
from typing import List, Optional, Callable, Awaitable, Any
from datetime import datetime
from pathlib import Path
import traceback

from .framework import BenchmarkFramework, BenchmarkConfig, TaskComplexity, EvaluationDimensions
from .tasks import BenchmarkTask, TaskResult
from .metrics import MetricsCalculator, BenchmarkScore
from .reporter import BenchmarkReporter

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Automated benchmark runner for executing test suites.

    Features:
    - Parallel and sequential execution
    - Progress tracking and reporting
    - Timeout handling
    - Detailed logging
    - Result aggregation
    """

    def __init__(
        self,
        framework: BenchmarkFramework,
        executor_fn: Callable[[BenchmarkTask], Awaitable[TaskResult]],
        config: Optional[BenchmarkConfig] = None
    ):
        """
        Initialize benchmark runner.

        Args:
            framework: Benchmark framework instance
            executor_fn: Async function to execute a single task
            config: Benchmark configuration
        """
        self.framework = framework
        self.executor_fn = executor_fn
        self.config = config or BenchmarkConfig()
        self.metrics_calculator = MetricsCalculator()
        self.reporter = BenchmarkReporter()

        self._execution_start: Optional[datetime] = None
        self._execution_end: Optional[datetime] = None

    async def run_all(self) -> BenchmarkScore:
        """
        Run all registered benchmark tasks.

        Returns:
            Benchmark score with comprehensive metrics
        """
        if not self.framework.tasks:
            logger.warning("No benchmark tasks registered")
            return BenchmarkScore()

        logger.info(f"Starting benchmark execution: {len(self.framework.tasks)} tasks")
        self._execution_start = datetime.now()

        try:
            if self.config.parallel_execution:
                await self._run_parallel()
            else:
                await self._run_sequential()

            self._execution_end = datetime.now()

            # Calculate and return score
            score = self.metrics_calculator.calculate_score(self.framework.results)

            logger.info(
                f"Benchmark execution completed: {score.overall_score:.1f}/100 "
                f"({score.completed_tasks}/{score.total_tasks} tasks)"
            )

            return score

        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            logger.error(traceback.format_exc())
            raise

    async def run_complexity_level(self, complexity: TaskComplexity) -> List[TaskResult]:
        """
        Run tasks of a specific complexity level.

        Args:
            complexity: Task complexity level

        Returns:
            List of task results
        """
        tasks = self.framework.get_tasks_by_complexity(complexity)
        if not tasks:
            logger.warning(f"No tasks found for complexity: {complexity.value}")
            return []

        logger.info(f"Running {len(tasks)} tasks for complexity: {complexity.value}")

        results = []
        for task in tasks:
            result = await self._execute_task(task)
            results.append(result)
            self.framework.add_result(result)

        return results

    async def _run_parallel(self) -> None:
        """Execute tasks in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(self.config.max_parallel_tasks)

        async def execute_with_limit(task: BenchmarkTask):
            async with semaphore:
                result = await self._execute_task(task)
                self.framework.add_result(result)
                return result

        tasks = [execute_with_limit(task) for task in self.framework.tasks]

        # Execute with progress reporting
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            await coro
            logger.info(f"Progress: {i}/{len(tasks)} tasks completed")

    async def _run_sequential(self) -> None:
        """Execute tasks sequentially."""
        for i, task in enumerate(self.framework.tasks, 1):
            logger.info(f"Executing task {i}/{len(self.framework.tasks)}: {task.name}")
            result = await self._execute_task(task)
            self.framework.add_result(result)

    async def _execute_task(self, task: BenchmarkTask) -> TaskResult:
        """
        Execute a single benchmark task.

        Args:
            task: Benchmark task to execute

        Returns:
            Task execution result
        """
        start_time = datetime.now()
        execution_log = []

        try:
            execution_log.append(f"[{start_time.isoformat()}] Starting task: {task.name}")

            # Get timeout based on complexity
            from .framework import PerformanceTargets
            targets = PerformanceTargets.for_complexity(task.complexity)
            timeout = targets.max_response_time * self.config.timeout_multiplier

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self.executor_fn(task),
                    timeout=timeout
                )
                end_time = datetime.now()

                # Update timing
                result.start_time = start_time
                result.end_time = end_time
                result.evaluation.response_time = (end_time - start_time).total_seconds()

                execution_log.append(f"[{end_time.isoformat()}] Task completed successfully")
                result.execution_log = execution_log

                logger.debug(
                    f"Task {task.task_id} completed: "
                    f"success={result.success}, time={result.evaluation.response_time:.2f}s"
                )

                return result

            except asyncio.TimeoutError:
                end_time = datetime.now()
                execution_log.append(f"[{end_time.isoformat()}] Task timed out after {timeout:.1f}s")

                logger.warning(f"Task {task.task_id} timed out after {timeout:.1f}s")

                return TaskResult(
                    task_id=task.task_id,
                    task_name=task.name,
                    complexity=task.complexity,
                    category=task.category,
                    success=False,
                    error_message=f"Task timed out after {timeout:.1f}s",
                    execution_log=execution_log,
                    start_time=start_time,
                    end_time=end_time,
                    evaluation=EvaluationDimensions(
                        task_completion=False,
                        response_time=(end_time - start_time).total_seconds(),
                    )
                )

        except Exception as e:
            end_time = datetime.now()
            error_msg = f"Execution error: {str(e)}"
            execution_log.append(f"[{end_time.isoformat()}] {error_msg}")

            logger.error(f"Task {task.task_id} failed: {error_msg}")
            logger.error(traceback.format_exc())

            return TaskResult(
                task_id=task.task_id,
                task_name=task.name,
                complexity=task.complexity,
                category=task.category,
                success=False,
                error_message=error_msg,
                execution_log=execution_log,
                start_time=start_time,
                end_time=end_time,
                evaluation=EvaluationDimensions(
                    task_completion=False,
                    response_time=(end_time - start_time).total_seconds(),
                )
            )

    def generate_report(self, format: str = "all", save: bool = True) -> dict:
        """
        Generate benchmark report.

        Args:
            format: Report format ('json', 'markdown', 'console', 'all')
            save: Whether to save reports to files

        Returns:
            Dictionary mapping format to report content
        """
        score = self.metrics_calculator.calculate_score(self.framework.results)
        return self.reporter.generate_report(score, self.framework.results, format, save)

    def print_summary(self) -> None:
        """Print benchmark summary to console."""
        score = self.metrics_calculator.calculate_score(self.framework.results)
        self.reporter.print_summary(score)

    @property
    def execution_duration(self) -> Optional[float]:
        """Get total execution duration in seconds."""
        if self._execution_start and self._execution_end:
            return (self._execution_end - self._execution_start).total_seconds()
        return None
