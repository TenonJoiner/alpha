"""
Resilience Package - Never Give Up System

This package implements Alpha's core "Never Give Up" resilience principle,
ensuring tasks are completed successfully through intelligent retry strategies,
alternative exploration, failure analysis, and creative problem-solving.

Components:
    - RetryStrategy: Exponential backoff retry with circuit breaker
    - FailureAnalyzer: Pattern recognition and root cause analysis
    - ResilienceEngine: Core orchestration engine
    - AlternativeExplorer: Multi-strategy exploration
    - CreativeSolver: Creative workaround generation
    - ProgressTracker: State management and metrics

Usage:
    from alpha.core.resilience import ResilienceEngine, ResilienceConfig

    # Create resilience engine
    config = ResilienceConfig(max_attempts=5, max_total_time=300.0)
    engine = ResilienceEngine(config)

    # Execute with resilience
    result = await engine.execute(
        my_function,
        arg1, arg2,
        operation_name="my_operation",
        kwarg1=value1
    )

    if result.success:
        print(f"Success: {result.value}")
    else:
        print(f"Failed: {result.error}")
        print(f"Recommendations: {result.recommendations}")
"""

# Import core components
from .retry import (
    RetryStrategy,
    RetryConfig,
    RetryResult,
    ErrorType,
    CircuitBreaker
)

from .analyzer import (
    FailureAnalyzer,
    Failure,
    FailurePattern,
    FailureAnalysis,
    RootCause
)

from .engine import (
    ResilienceEngine,
    ResilienceConfig,
    Strategy,
    ResilienceResult
)

from .explorer import (
    AlternativeExplorer,
    StrategyType,
    StrategyTemplate
)

from .creative import (
    CreativeSolver,
    CreativeSolution,
    SolutionType,
    SubTask,
    WorkaroundSolution,
    MultiStepPlan
)

from .tracker import (
    ProgressTracker,
    Attempt,
    TaskState
)

# Public API
__all__ = [
    # Core Engine
    "ResilienceEngine",
    "ResilienceConfig",
    "Strategy",
    "ResilienceResult",

    # Retry System
    "RetryStrategy",
    "RetryConfig",
    "RetryResult",
    "ErrorType",
    "CircuitBreaker",

    # Failure Analysis
    "FailureAnalyzer",
    "Failure",
    "FailurePattern",
    "FailureAnalysis",
    "RootCause",

    # Alternative Exploration
    "AlternativeExplorer",
    "StrategyType",
    "StrategyTemplate",

    # Creative Problem Solving
    "CreativeSolver",
    "CreativeSolution",
    "SolutionType",
    "SubTask",
    "WorkaroundSolution",
    "MultiStepPlan",

    # Progress Tracking
    "ProgressTracker",
    "Attempt",
    "TaskState",
]

__version__ = "1.0.0"
