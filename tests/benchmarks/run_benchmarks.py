"""
Main benchmark test execution script.

Run comprehensive benchmark tests for Alpha Agent.

Usage:
    python -m tests.benchmarks.run_benchmarks
    python -m tests.benchmarks.run_benchmarks --level level_1_simple
    python -m tests.benchmarks.run_benchmarks --category file_system
    python -m tests.benchmarks.run_benchmarks --parallel --max-tasks 10
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.benchmarks import (
    BenchmarkFramework,
    BenchmarkRunner,
    TaskComplexity,
    TaskCategory,
    BenchmarkConfig,
    BenchmarkTask,
    TaskResult,
    EvaluationDimensions,
)
from tests.benchmarks.scenarios import create_all_scenarios
from alpha.core.engine import AlphaEngine
from alpha.events.bus import EventBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlphaBenchmarkExecutor:
    """Execute benchmark tasks using Alpha Agent."""

    def __init__(self):
        """Initialize benchmark executor."""
        self.engine = None
        self.event_bus = None

    async def initialize(self):
        """Initialize Alpha engine for testing."""
        try:
            logger.info("Initializing Alpha engine for benchmark testing...")
            self.event_bus = EventBus()
            await self.event_bus.initialize()

            self.engine = AlphaEngine(self.event_bus)
            await self.engine.initialize()

            logger.info("Alpha engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Alpha engine: {e}")
            raise

    async def execute_task(self, task: BenchmarkTask) -> TaskResult:
        """
        Execute a single benchmark task using Alpha.

        Args:
            task: Benchmark task to execute

        Returns:
            Task execution result with evaluation metrics
        """
        logger.info(f"Executing task: {task.name} ({task.complexity.value})")

        start_time = datetime.now()
        execution_log = []

        try:
            # Prepare task prompt based on task type
            prompt = self._prepare_prompt(task)
            execution_log.append(f"Task prompt: {prompt}")

            # Execute task with Alpha
            response = await self.engine.process_request(prompt)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Evaluate result
            evaluation = self._evaluate_result(task, response, duration)

            # Determine success
            success = evaluation.task_completion

            logger.info(
                f"Task completed: {task.name} - Success: {success}, "
                f"Time: {duration:.2f}s"
            )

            return TaskResult(
                task_id=task.task_id,
                task_name=task.name,
                complexity=task.complexity,
                category=task.category,
                success=success,
                actual_output=response,
                evaluation=evaluation,
                execution_log=execution_log,
                start_time=start_time,
                end_time=end_time,
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"Task execution failed: {task.name} - {str(e)}")

            return TaskResult(
                task_id=task.task_id,
                task_name=task.name,
                complexity=task.complexity,
                category=task.category,
                success=False,
                error_message=str(e),
                evaluation=EvaluationDimensions(
                    task_completion=False,
                    response_time=duration,
                ),
                execution_log=execution_log,
                start_time=start_time,
                end_time=end_time,
            )

    def _prepare_prompt(self, task: BenchmarkTask) -> str:
        """
        Prepare prompt for Alpha based on task definition.

        Args:
            task: Benchmark task

        Returns:
            Formatted prompt string
        """
        prompt_parts = [task.description]

        if task.input_data:
            prompt_parts.append("\nInput:")
            for key, value in task.input_data.items():
                prompt_parts.append(f"  {key}: {value}")

        return "\n".join(prompt_parts)

    def _evaluate_result(
        self,
        task: BenchmarkTask,
        response: str,
        duration: float
    ) -> EvaluationDimensions:
        """
        Evaluate task execution result.

        Args:
            task: Original benchmark task
            response: Alpha's response
            duration: Execution duration in seconds

        Returns:
            Evaluation metrics
        """
        evaluation = EvaluationDimensions()
        evaluation.response_time = duration

        # Basic completion check
        if response and len(response) > 0:
            evaluation.task_completion = True
            evaluation.partial_completion = False
        else:
            evaluation.task_completion = False
            evaluation.partial_completion = False

        # Check for error indicators
        error_indicators = ["error", "failed", "exception", "cannot", "unable"]
        if any(indicator in response.lower() for indicator in error_indicators):
            evaluation.task_completion = False
            evaluation.partial_completion = True

        # Custom validation if provided
        if task.validation_fn and task.expected_output:
            try:
                is_valid = task.validation_fn(response, task.expected_output)
                evaluation.task_completion = is_valid
            except Exception as e:
                logger.warning(f"Validation function failed: {e}")

        # Estimate tool usage accuracy (simplified - would need actual tool logs)
        evaluation.tool_usage_accuracy = 0.8 if evaluation.task_completion else 0.3

        # Estimate reasoning quality
        evaluation.reasoning_quality = 0.9 if evaluation.task_completion else 0.4

        # Estimate API cost (simplified - would need actual tracking)
        # Assuming average cost based on response length
        estimated_tokens = len(response.split())
        evaluation.api_cost = estimated_tokens * 0.000001  # Rough estimate

        return evaluation

    async def cleanup(self):
        """Cleanup resources."""
        if self.engine:
            await self.engine.close()
        if self.event_bus:
            await self.event_bus.close()


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run Alpha Agent benchmarks")
    parser.add_argument(
        "--level",
        choices=["level_1_simple", "level_2_medium", "level_3_complex", "level_4_expert"],
        help="Run only specific complexity level"
    )
    parser.add_argument(
        "--category",
        choices=[c.value for c in TaskCategory],
        help="Run only specific category"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tasks in parallel"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="Maximum parallel tasks (default: 5)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "console", "all"],
        default="all",
        help="Report format (default: all)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save reports to files"
    )

    args = parser.parse_args()

    # Create benchmark configuration
    config = BenchmarkConfig(
        parallel_execution=args.parallel,
        max_parallel_tasks=args.max_tasks,
    )

    # Initialize framework
    framework = BenchmarkFramework(config)

    # Load scenarios
    logger.info("Loading benchmark scenarios...")
    all_scenarios = create_all_scenarios()

    # Filter scenarios if specified
    scenarios = all_scenarios
    if args.level:
        complexity = TaskComplexity(args.level)
        scenarios = [s for s in scenarios if s.complexity == complexity]
        logger.info(f"Filtered to {len(scenarios)} tasks for level: {args.level}")

    if args.category:
        category = TaskCategory(args.category)
        scenarios = [s for s in scenarios if s.category == category]
        logger.info(f"Filtered to {len(scenarios)} tasks for category: {args.category}")

    # Register scenarios
    framework.register_task_suite(scenarios)
    logger.info(f"Registered {len(scenarios)} benchmark tasks")

    # Initialize executor
    executor = AlphaBenchmarkExecutor()
    await executor.initialize()

    try:
        # Create runner
        runner = BenchmarkRunner(framework, executor.execute_task, config)

        # Run benchmarks
        logger.info("=" * 80)
        logger.info("Starting benchmark execution")
        logger.info("=" * 80)

        score = await runner.run_all()

        # Generate reports
        logger.info("Generating reports...")
        reports = runner.generate_report(
            format=args.format,
            save=not args.no_save
        )

        # Print console summary
        if 'console' in reports:
            print(reports['console'])

        logger.info("=" * 80)
        logger.info(f"Benchmark completed: Overall score {score.overall_score:.1f}/100")
        logger.info("=" * 80)

        # Return success if score meets minimum threshold
        min_threshold = 60.0
        if score.overall_score >= min_threshold:
            logger.info(f"✓ Benchmark passed (score >= {min_threshold})")
            return 0
        else:
            logger.warning(f"✗ Benchmark failed (score < {min_threshold})")
            return 1

    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await executor.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
