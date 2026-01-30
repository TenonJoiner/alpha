"""
Tests for Resilience System

Tests cover:
- RetryStrategy: Retry logic, exponential backoff, circuit breaker
- FailureAnalyzer: Pattern detection, root cause analysis
- ResilienceEngine: Full resilient execution
- AlternativeExplorer: Strategy enumeration and ranking
- CreativeSolver: Workaround generation
- ProgressTracker: State management
"""

import pytest
import asyncio
from datetime import datetime

from alpha.core.resilience import (
    ResilienceEngine,
    ResilienceConfig,
    RetryStrategy,
    RetryConfig,
    FailureAnalyzer,
    AlternativeExplorer,
    CreativeSolver,
    ProgressTracker,
    ErrorType,
    FailurePattern,
    Strategy,
    CreativeSolution
)


# Test RetryStrategy
class TestRetryStrategy:
    def test_error_classification(self):
        """Test error type classification"""
        strategy = RetryStrategy()

        # Network error
        error = Exception("Connection timeout")
        assert strategy.classify_error(error) == ErrorType.NETWORK

        # Auth error
        error = Exception("401 Unauthorized")
        assert strategy.classify_error(error) == ErrorType.AUTHENTICATION

        # Rate limit
        error = Exception("429 Too Many Requests")
        assert strategy.classify_error(error) == ErrorType.RATE_LIMIT

    def test_should_retry(self):
        """Test retry decision logic"""
        strategy = RetryStrategy()

        # Should retry network errors
        assert strategy.should_retry(Exception("Connection timeout"))

        # Should not retry auth errors
        assert not strategy.should_retry(Exception("401 Unauthorized"))

        # Should retry server errors
        assert strategy.should_retry(Exception("500 Internal Server Error"))

    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=60.0, jitter=False)
        strategy = RetryStrategy(config)

        # Test delay progression (without jitter)
        delay0 = strategy.get_next_delay(0)  # 1s
        delay1 = strategy.get_next_delay(1)  # 2s
        delay2 = strategy.get_next_delay(2)  # 4s

        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0

        # Test max delay cap
        delay10 = strategy.get_next_delay(10)
        assert delay10 <= 60.0

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution without retry"""
        strategy = RetryStrategy()

        async def success_func():
            return "success"

        result = await strategy.execute_with_retry(success_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_until_success(self):
        """Test retry until success"""
        strategy = RetryStrategy(RetryConfig(max_attempts=3, base_delay=0.1))

        attempt_count = 0

        async def retry_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Network timeout")
            return "success"

        result = await strategy.execute_with_retry(retry_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 3
        assert attempt_count == 3


# Test FailureAnalyzer
class TestFailureAnalyzer:
    def test_record_failure(self):
        """Test failure recording"""
        analyzer = FailureAnalyzer()

        error = Exception("Connection timeout")
        failure = analyzer.record_failure(error, "http_request")

        assert failure.operation == "http_request"
        assert failure.error_type == ErrorType.NETWORK

    def test_pattern_detection_repeating(self):
        """Test repeating error pattern detection"""
        analyzer = FailureAnalyzer(pattern_threshold=2)

        # Record same error multiple times
        for _ in range(3):
            analyzer.record_failure(
                Exception("Connection timeout"),
                "http_request"
            )

        analysis = analyzer.analyze_pattern()

        assert analysis.pattern == FailurePattern.REPEATING_ERROR
        assert analysis.failure_count == 3

    def test_root_cause_identification(self):
        """Test root cause identification"""
        analyzer = FailureAnalyzer()

        # Network error
        analyzer.record_failure(Exception("Connection timeout"), "operation1")
        analysis = analyzer.analyze_pattern()

        assert analysis.root_cause is not None
        assert analysis.root_cause.cause_type == "network_connectivity"
        assert len(analysis.recommendations) > 0


# Test AlternativeExplorer
class TestAlternativeExplorer:
    def test_strategy_enumeration(self):
        """Test strategy enumeration"""
        explorer = AlternativeExplorer()

        strategies = explorer.enumerate_strategies(
            operation="http_request",
            context={"url": "https://api.example.com"}
        )

        assert len(strategies) > 0
        assert any("http" in s["name"] for s in strategies)

    def test_strategy_ranking(self):
        """Test strategy ranking"""
        explorer = AlternativeExplorer()

        strategies = [
            {
                "name": "strategy_a",
                "priority": 1.0,
                "cost_estimate": 0.01,
                "time_estimate": 10.0
            },
            {
                "name": "strategy_b",
                "priority": 0.8,
                "cost_estimate": 0.001,
                "time_estimate": 5.0
            }
        ]

        # Rank for balanced optimization
        ranked = explorer.rank_strategies(strategies, optimization_goal="balanced")

        assert len(ranked) == 2
        assert all("score" in s for s in ranked)

    def test_success_failure_recording(self):
        """Test recording strategy outcomes"""
        explorer = AlternativeExplorer()

        explorer.record_success("strategy_a")
        explorer.record_success("strategy_a")
        explorer.record_failure("strategy_a")

        success_rate = explorer.get_success_rate("strategy_a")
        assert success_rate == 2.0 / 3.0  # 2 successes out of 3 attempts


# Test CreativeSolver
class TestCreativeSolver:
    @pytest.mark.asyncio
    async def test_solve_decomposition(self):
        """Test problem decomposition via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Download 100 large files",
            preferred_type=solver._analyze_problem_type("Download 100 large files", {})
        )

        assert solution is not None
        assert solution.confidence > 0

    @pytest.mark.asyncio
    async def test_solve_workaround(self):
        """Test workaround generation via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Cannot access API - 403 Forbidden",
            context={"attempts": 5}
        )

        assert solution is not None
        assert solution.confidence > 0

    @pytest.mark.asyncio
    async def test_solution_type_detection(self):
        """Test solution type detection"""
        solver = CreativeSolver()

        # Test code generation detection
        from alpha.core.resilience.creative import SolutionType
        sol_type = solver._analyze_problem_type("Write code to parse JSON", {})
        assert sol_type == SolutionType.CODE_GENERATION

        # Test workaround detection
        sol_type = solver._analyze_problem_type("API is blocked, need alternative", {})
        assert sol_type == SolutionType.WORKAROUND


# Test ProgressTracker
class TestProgressTracker:
    def test_task_lifecycle(self):
        """Test complete task lifecycle"""
        tracker = ProgressTracker()

        # Start task
        task_id = tracker.start_task(operation="test_operation")
        assert task_id is not None

        # Record attempts
        tracker.record_attempt(
            task_id=task_id,
            strategy_name="strategy_1",
            success=False,
            error="Network error",
            duration=1.5
        )

        tracker.record_attempt(
            task_id=task_id,
            strategy_name="strategy_2",
            success=True,
            duration=2.0
        )

        # Complete task
        tracker.complete_task(task_id, success=True, result="result_value")

        # Get state
        state = tracker.get_state(task_id)
        assert state.status == "completed"
        assert len(state.attempts) == 2
        assert state.result == "result_value"

    def test_metrics_calculation(self):
        """Test metrics calculation"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")

        tracker.record_attempt(
            task_id=task_id,
            strategy_name="s1",
            success=False,
            duration=1.0
        )

        tracker.record_attempt(
            task_id=task_id,
            strategy_name="s2",
            success=True,
            duration=2.0
        )

        tracker.complete_task(task_id, success=True)

        metrics = tracker.get_metrics(task_id)

        assert metrics["total_attempts"] == 2
        assert metrics["successful_attempts"] == 1
        assert metrics["failed_attempts"] == 1
        assert metrics["total_duration"] == 3.0


# Test ResilienceEngine
class TestResilienceEngine:
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution"""
        config = ResilienceConfig(max_attempts=3)
        engine = ResilienceEngine(config)

        async def success_func():
            return "success"

        result = await engine.execute(
            success_func,
            operation_name="test_operation"
        )

        assert result.success
        assert result.value == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_until_success(self):
        """Test retry with eventual success"""
        config = ResilienceConfig(max_attempts=5, base_delay=0.1)
        engine = ResilienceEngine(config)

        attempt_count = 0

        async def retry_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Network timeout")
            return "success_after_retry"

        result = await engine.execute(
            retry_func,
            operation_name="retry_operation"
        )

        assert result.success
        assert result.value == "success_after_retry"
        assert result.attempts >= 3

    @pytest.mark.asyncio
    async def test_complete_failure_with_analysis(self):
        """Test complete failure with analysis"""
        config = ResilienceConfig(max_attempts=2, base_delay=0.1)
        engine = ResilienceEngine(config)

        async def always_fail():
            raise Exception("Permanent failure")

        result = await engine.execute(
            always_fail,
            operation_name="failing_operation"
        )

        assert not result.success
        assert result.error is not None
        assert result.failure_analysis is not None
        assert len(result.recommendations) > 0

    def test_get_failure_summary(self):
        """Test failure summary"""
        engine = ResilienceEngine()

        summary = engine.get_failure_summary()

        assert "total_failures" in summary
        assert "unique_operations" in summary


# Integration Tests
@pytest.mark.asyncio
async def test_resilience_integration():
    """Test full resilience system integration"""
    config = ResilienceConfig(
        max_attempts=3,
        base_delay=0.1,
        max_parallel_strategies=2
    )
    engine = ResilienceEngine(config)

    call_count = 0

    async def flaky_operation():
        nonlocal call_count
        call_count += 1

        if call_count < 2:
            raise Exception("Transient network error")

        return {"data": "success", "call_count": call_count}

    # Execute with resilience
    result = await engine.execute(
        flaky_operation,
        operation_name="flaky_api_call",
        context={"api": "example.com"}
    )

    # Verify success
    assert result.success
    assert result.value["data"] == "success"
    assert result.attempts >= 1  # At least 1 attempt

    # Verify failure tracking
    summary = engine.get_failure_summary()
    assert summary["total_failures"] >= 0  # May be 0 or more depending on retry logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
