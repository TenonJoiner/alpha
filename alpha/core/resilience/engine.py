"""
Resilience Engine - Core orchestration for "Never Give Up" principle

The ResilienceEngine coordinates all resilience components to ensure tasks
are completed successfully through intelligent retry, alternative exploration,
failure analysis, and creative problem-solving.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .retry import RetryStrategy, RetryConfig, RetryResult, ErrorType
from .analyzer import FailureAnalyzer, FailurePattern, FailureAnalysis

logger = logging.getLogger(__name__)


@dataclass
class ResilienceConfig:
    """Configuration for resilience engine behavior"""
    # Retry configuration
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0

    # Resource limits
    max_total_time: float = 300.0  # 5 minutes
    max_api_cost: float = 1.0  # $1
    max_total_attempts: int = 20  # Total attempts across all strategies

    # Alternative exploration
    max_parallel_strategies: int = 3
    strategy_timeout: float = 30.0
    enable_alternatives: bool = True
    enable_creative_solving: bool = True

    # Creative solver
    enable_custom_code: bool = True
    creative_solver_provider: str = "deepseek"

    # Failure analysis
    pattern_detection_threshold: int = 3
    enable_learning: bool = True

    # Progress tracking
    enable_progress_tracking: bool = True
    checkpoint_interval: float = 60.0  # seconds

    # Escalation
    escalate_after_failures: int = 10
    user_intervention_threshold: int = 15


@dataclass
class Strategy:
    """
    Represents an alternative strategy to accomplish a task.

    Attributes:
        name: Strategy identifier
        func: Async function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        priority: Priority score (higher = more preferred)
        cost_estimate: Estimated API cost in dollars
        time_estimate: Estimated execution time in seconds
        description: Human-readable description
    """
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: float = 1.0
    cost_estimate: float = 0.0
    time_estimate: float = 0.0
    description: str = ""

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class ResilienceResult:
    """
    Result of resilient execution.

    Attributes:
        success: Whether task completed successfully
        value: Result value if successful
        error: Final error if failed
        attempts: Number of attempts made
        strategies_tried: List of strategy names tried
        total_time: Total execution time
        total_cost: Total API cost in USD
        failure_analysis: Analysis of failures encountered
        creative_solution: Creative solution generated (if applicable)
        recommendations: List of recommendations for improvement
        resource_usage: Resource consumption summary
        escalation_needed: Whether user intervention is recommended
    """
    success: bool
    value: Optional[Any] = None
    error: Optional[Exception] = None
    attempts: int = 0
    strategies_tried: List[str] = field(default_factory=list)
    total_time: float = 0.0
    total_cost: float = 0.0
    failure_analysis: Optional[FailureAnalysis] = None
    creative_solution: Optional[Any] = None
    recommendations: List[str] = field(default_factory=list)
    resource_usage: Optional[Any] = None
    escalation_needed: bool = False


class ResilienceEngine:
    """
    Core resilience engine implementing "Never Give Up" principle.

    Orchestrates:
    - RetryStrategy: Intelligent retry with exponential backoff
    - FailureAnalyzer: Pattern recognition and root cause analysis
    - AlternativeExplorer: Multiple solution path exploration (future)
    - CreativeSolver: Creative workaround generation (future)
    - ProgressTracker: State management and metrics (future)

    Usage:
        config = ResilienceConfig(max_attempts=5)
        engine = ResilienceEngine(config)
        result = await engine.execute(my_func, arg1, arg2, kwarg=value)

        if result.success:
            print(f"Success: {result.value}")
        else:
            print(f"Failed after {result.attempts} attempts")
            print(f"Recommendations: {result.recommendations}")
    """

    def __init__(self, config: Optional[ResilienceConfig] = None):
        """
        Initialize resilience engine.

        Args:
            config: Resilience configuration (uses defaults if None)
        """
        self.config = config or ResilienceConfig()

        # Initialize components
        retry_config = RetryConfig(
            max_attempts=self.config.max_attempts,
            base_delay=self.config.base_delay,
            max_delay=self.config.max_delay,
            backoff_factor=self.config.backoff_factor
        )
        self.retry_strategy = RetryStrategy(retry_config)

        self.failure_analyzer = FailureAnalyzer(
            pattern_threshold=self.config.pattern_detection_threshold
        )

        logger.info(f"ResilienceEngine initialized with config: {self.config}")

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        operation_name: str = "unknown_operation",
        context: Optional[Dict] = None,
        **kwargs
    ) -> ResilienceResult:
        """
        Execute function with full resilience capabilities.

        This is the main entry point for resilient execution. It:
        1. Attempts execution with retry strategy
        2. Analyzes failures if they occur
        3. Returns comprehensive result with recommendations

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            operation_name: Name of operation (for logging/analysis)
            context: Additional context for failure analysis
            **kwargs: Keyword arguments for func

        Returns:
            ResilienceResult with execution outcome and analysis
        """
        start_time = datetime.now()
        strategies_tried = [operation_name]

        logger.info(f"Starting resilient execution: {operation_name}")

        # Check if this operation has failed before
        if self.failure_analyzer.has_attempted(operation_name):
            logger.warning(f"Operation '{operation_name}' has been attempted before")

        # Execute with retry strategy
        retry_result = await self.retry_strategy.execute_with_retry(
            func, *args, **kwargs
        )

        # Handle success
        if retry_result.success:
            total_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Resilient execution succeeded: {operation_name} "
                f"(attempts: {retry_result.attempts}, time: {total_time:.2f}s)"
            )

            return ResilienceResult(
                success=True,
                value=retry_result.value,
                attempts=retry_result.attempts,
                strategies_tried=strategies_tried,
                total_time=total_time
            )

        # Handle failure - Record and analyze
        if retry_result.error:
            self.failure_analyzer.record_failure(
                error=retry_result.error,
                operation=operation_name,
                context=context
            )

        # Analyze failure pattern
        failure_analysis = self.failure_analyzer.analyze_pattern()

        # Generate recommendations
        recommendations = self._generate_recommendations(
            retry_result,
            failure_analysis,
            operation_name
        )

        total_time = (datetime.now() - start_time).total_seconds()

        logger.error(
            f"Resilient execution failed: {operation_name} "
            f"(attempts: {retry_result.attempts}, time: {total_time:.2f}s, "
            f"error: {retry_result.error_type})"
        )

        return ResilienceResult(
            success=False,
            error=retry_result.error,
            attempts=retry_result.attempts,
            strategies_tried=strategies_tried,
            total_time=total_time,
            failure_analysis=failure_analysis,
            recommendations=recommendations
        )

    async def execute_with_alternatives(
        self,
        strategies: List[Strategy],
        operation_name: str = "unknown_operation",
        parallel: bool = False
    ) -> ResilienceResult:
        """
        Execute with multiple alternative strategies.

        Tries multiple approaches to accomplish the task:
        - Sequential: Try strategies in priority order until one succeeds
        - Parallel: Try multiple strategies concurrently (first success wins)

        Args:
            strategies: List of alternative strategies to try
            operation_name: Name of operation
            parallel: Whether to execute strategies in parallel

        Returns:
            ResilienceResult with execution outcome
        """
        start_time = datetime.now()
        strategies_tried = []
        last_error: Optional[Exception] = None

        # Sort strategies by priority (highest first)
        sorted_strategies = sorted(strategies, key=lambda s: s.priority, reverse=True)

        logger.info(
            f"Executing with {len(strategies)} alternative strategies "
            f"(parallel={parallel}): {operation_name}"
        )

        if parallel:
            # Parallel execution: Try multiple strategies at once
            result = await self._execute_parallel(sorted_strategies, operation_name)
        else:
            # Sequential execution: Try strategies one by one
            result = await self._execute_sequential(sorted_strategies, operation_name)

        return result

    async def _execute_sequential(
        self,
        strategies: List[Strategy],
        operation_name: str
    ) -> ResilienceResult:
        """Execute strategies sequentially"""
        start_time = datetime.now()
        strategies_tried = []
        last_error: Optional[Exception] = None

        for strategy in strategies:
            if (datetime.now() - start_time).total_seconds() >= self.config.max_total_time:
                logger.warning(f"Max total time exceeded: {self.config.max_total_time}s")
                break

            strategies_tried.append(strategy.name)
            logger.info(f"Trying strategy: {strategy.name} - {strategy.description}")

            try:
                # Execute strategy with resilience
                result = await self.execute(
                    strategy.func,
                    *strategy.args,
                    operation_name=f"{operation_name}::{strategy.name}",
                    **strategy.kwargs
                )

                if result.success:
                    total_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Strategy succeeded: {strategy.name} ({total_time:.2f}s)")

                    return ResilienceResult(
                        success=True,
                        value=result.value,
                        attempts=result.attempts,
                        strategies_tried=strategies_tried,
                        total_time=total_time
                    )
                else:
                    last_error = result.error
                    logger.warning(f"Strategy failed: {strategy.name}")

            except Exception as e:
                last_error = e
                logger.error(f"Strategy raised exception: {strategy.name}: {e}")
                self.failure_analyzer.record_failure(
                    error=e,
                    operation=f"{operation_name}::{strategy.name}"
                )

        # All strategies failed
        total_time = (datetime.now() - start_time).total_seconds()
        failure_analysis = self.failure_analyzer.analyze_pattern()
        recommendations = self._generate_recommendations(
            None, failure_analysis, operation_name
        )

        logger.error(
            f"All {len(strategies)} strategies failed for: {operation_name} "
            f"({total_time:.2f}s)"
        )

        return ResilienceResult(
            success=False,
            error=last_error,
            attempts=len(strategies_tried),
            strategies_tried=strategies_tried,
            total_time=total_time,
            failure_analysis=failure_analysis,
            recommendations=recommendations
        )

    async def _execute_parallel(
        self,
        strategies: List[Strategy],
        operation_name: str
    ) -> ResilienceResult:
        """Execute strategies in parallel (first success wins)"""
        start_time = datetime.now()

        # Limit concurrent strategies
        strategies_to_run = strategies[:self.config.max_parallel_strategies]

        logger.info(f"Running {len(strategies_to_run)} strategies in parallel")

        # Create tasks for each strategy
        tasks = []
        for strategy in strategies_to_run:
            task = asyncio.create_task(
                self.execute(
                    strategy.func,
                    *strategy.args,
                    operation_name=f"{operation_name}::{strategy.name}",
                    **strategy.kwargs
                )
            )
            tasks.append((strategy.name, task))

        # Wait for first success or all to complete
        strategies_tried = []
        successful_result = None

        while tasks:
            # Wait for first task to complete
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Check completed tasks
            for strategy_name, task in tasks[:]:
                if task in done:
                    strategies_tried.append(strategy_name)
                    result = await task

                    if result.success:
                        # Cancel remaining tasks
                        for _, pending_task in tasks:
                            if pending_task != task:
                                pending_task.cancel()

                        total_time = (datetime.now() - start_time).total_seconds()
                        logger.info(
                            f"Strategy succeeded (parallel): {strategy_name} "
                            f"({total_time:.2f}s)"
                        )

                        return ResilienceResult(
                            success=True,
                            value=result.value,
                            attempts=len(strategies_tried),
                            strategies_tried=strategies_tried,
                            total_time=total_time
                        )

                    # Remove completed task
                    tasks.remove((strategy_name, task))

        # All parallel strategies failed
        total_time = (datetime.now() - start_time).total_seconds()
        failure_analysis = self.failure_analyzer.analyze_pattern()
        recommendations = self._generate_recommendations(
            None, failure_analysis, operation_name
        )

        logger.error(f"All parallel strategies failed for: {operation_name}")

        return ResilienceResult(
            success=False,
            error=Exception("All parallel strategies failed"),
            attempts=len(strategies_tried),
            strategies_tried=strategies_tried,
            total_time=total_time,
            failure_analysis=failure_analysis,
            recommendations=recommendations
        )

    def _generate_recommendations(
        self,
        retry_result: Optional[RetryResult],
        failure_analysis: FailureAnalysis,
        operation_name: str
    ) -> List[str]:
        """
        Generate actionable recommendations based on failure analysis.

        Args:
            retry_result: Result from retry strategy (if available)
            failure_analysis: Analysis of failure patterns
            operation_name: Name of failed operation

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Include analyzer recommendations
        if failure_analysis.recommendations:
            recommendations.extend(failure_analysis.recommendations)

        # Add resilience-specific recommendations
        if retry_result:
            if retry_result.error_type == ErrorType.AUTHENTICATION:
                recommendations.append(
                    "Authentication error - verify API key configuration"
                )
            elif retry_result.error_type == ErrorType.NETWORK:
                recommendations.append(
                    "Network error - check connectivity and try alternative endpoints"
                )
            elif retry_result.error_type == ErrorType.RATE_LIMIT:
                recommendations.append(
                    "Rate limit - consider implementing request throttling"
                )

        # Pattern-specific recommendations
        if failure_analysis.pattern == FailurePattern.REPEATING_ERROR:
            recommendations.append(
                f"Operation '{operation_name}' repeatedly failing with same error - "
                "consider alternative approach"
            )
        elif failure_analysis.pattern == FailurePattern.UNSTABLE_SERVICE:
            recommendations.append(
                "Service appears unstable - implement fallback provider"
            )

        # General recommendations
        if failure_analysis.failure_count >= 3:
            recommendations.append(
                "Multiple failures detected - manual intervention may be required"
            )

        return recommendations

    def get_failure_summary(self) -> Dict:
        """
        Get summary of all failures encountered.

        Returns:
            Dictionary with failure statistics and patterns
        """
        return self.failure_analyzer.get_failure_summary()

    def reset(self):
        """Reset resilience engine state"""
        self.retry_strategy.reset()
        self.failure_analyzer.clear_history()
        logger.info("ResilienceEngine state reset")
