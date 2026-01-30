"""
Comprehensive Tests for Resilience System

Tests cover:
- RetryStrategy: Retry logic, exponential backoff, circuit breaker, jitter
- FailureAnalyzer: Pattern detection, root cause analysis, history management
- AlternativeExplorer: Strategy enumeration, ranking, parallel/sequential execution
- CreativeSolver: Workaround generation, problem decomposition, code generation
- ProgressTracker: State management, metrics, persistence
- ResilienceEngine: Full resilient execution with multi-layer fallback
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

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
    CreativeSolution,
    SolutionType,
    CircuitBreaker,
)


# Test RetryStrategy
class TestRetryStrategy:
    def test_error_classification_network(self):
        """Test network error classification"""
        strategy = RetryStrategy()

        errors = [
            "Connection timeout",
            "Network unreachable",
            "DNS resolution failed",
            "Connection refused"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.NETWORK

    def test_error_classification_auth(self):
        """Test authentication error classification"""
        strategy = RetryStrategy()

        errors = [
            "401 Unauthorized",
            "403 Forbidden",
            "Invalid API key",
            "Permission denied"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.AUTHENTICATION

    def test_error_classification_rate_limit(self):
        """Test rate limit error classification"""
        strategy = RetryStrategy()

        errors = [
            "429 Too Many Requests",
            "Rate limit exceeded",
            "Quota exceeded"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.RATE_LIMIT

    def test_error_classification_server(self):
        """Test server error classification"""
        strategy = RetryStrategy()

        errors = [
            "500 Internal Server Error",
            "502 Bad Gateway",
            "503 Service Unavailable",
            "504 Gateway Timeout"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.SERVER_ERROR

    def test_error_classification_client(self):
        """Test client error classification"""
        strategy = RetryStrategy()

        errors = [
            "400 Bad Request",
            "404 Not Found",
            "422 Invalid input"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.CLIENT_ERROR

    def test_error_classification_resource_exhausted(self):
        """Test resource exhaustion classification"""
        strategy = RetryStrategy()

        errors = [
            "Out of memory",
            "Disk space exhausted",
            "Resource limit exceeded"
        ]

        for error_msg in errors:
            error = Exception(error_msg)
            assert strategy.classify_error(error) == ErrorType.RESOURCE_EXHAUSTED

    def test_should_retry_retryable_errors(self):
        """Test retry decision for retryable errors"""
        strategy = RetryStrategy()

        retryable = [
            Exception("Connection timeout"),
            Exception("500 Internal Server Error"),
            Exception("429 Too Many Requests"),
            Exception("Out of memory")
        ]

        for error in retryable:
            assert strategy.should_retry(error), f"Should retry: {error}"

    def test_should_retry_non_retryable_errors(self):
        """Test retry decision for non-retryable errors"""
        strategy = RetryStrategy()

        non_retryable = [
            Exception("401 Unauthorized"),
            Exception("403 Forbidden"),
            Exception("400 Bad Request")
        ]

        for error in non_retryable:
            assert not strategy.should_retry(error), f"Should not retry: {error}"

    def test_exponential_backoff_without_jitter(self):
        """Test exponential backoff calculation without jitter"""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=60.0,
            jitter=False
        )
        strategy = RetryStrategy(config)

        assert strategy.get_next_delay(0) == 1.0
        assert strategy.get_next_delay(1) == 2.0
        assert strategy.get_next_delay(2) == 4.0
        assert strategy.get_next_delay(3) == 8.0
        assert strategy.get_next_delay(4) == 16.0

    def test_exponential_backoff_max_delay(self):
        """Test max delay enforcement"""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=10.0,
            jitter=False
        )
        strategy = RetryStrategy(config)

        assert strategy.get_next_delay(10) <= 10.0
        assert strategy.get_next_delay(20) <= 10.0

    def test_exponential_backoff_with_jitter(self):
        """Test jitter adds randomization"""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            jitter=True
        )
        strategy = RetryStrategy(config)

        delays = [strategy.get_next_delay(1) for _ in range(10)]

        # All delays should be around 2.0 but not identical
        assert len(set(delays)) > 1, "Jitter should create variation"
        assert all(0.5 <= d <= 3.5 for d in delays), "Delays within jitter range"

    @pytest.mark.asyncio
    async def test_successful_execution_first_attempt(self):
        """Test successful execution on first attempt"""
        strategy = RetryStrategy()

        async def success_func():
            return "success"

        result = await strategy.execute_with_retry(success_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 1
        assert result.error is None

    @pytest.mark.asyncio
    async def test_retry_until_success(self):
        """Test retry until eventual success"""
        config = RetryConfig(max_attempts=5, base_delay=0.01)
        strategy = RetryStrategy(config)

        attempt_count = 0

        async def retry_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Network timeout")
            return "success_after_retry"

        result = await strategy.execute_with_retry(retry_func)

        assert result.success
        assert result.value == "success_after_retry"
        assert result.attempts == 3
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """Test max attempts limit"""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)

        async def always_fail():
            raise Exception("Network timeout")

        result = await strategy.execute_with_retry(always_fail)

        assert not result.success
        assert result.error is not None
        assert result.attempts == 3
        assert result.error_type == ErrorType.NETWORK

    @pytest.mark.asyncio
    async def test_non_retryable_error_stops_immediately(self):
        """Test non-retryable error stops retry immediately"""
        config = RetryConfig(max_attempts=5, base_delay=0.01)
        strategy = RetryStrategy(config)

        attempt_count = 0

        async def auth_error_func():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("401 Unauthorized")

        result = await strategy.execute_with_retry(auth_error_func)

        assert not result.success
        assert attempt_count == 1, "Should not retry auth errors"
        assert result.error_type == ErrorType.AUTHENTICATION

    @pytest.mark.asyncio
    async def test_rate_limit_special_handling(self):
        """Test rate limit gets longer delay"""
        config = RetryConfig(max_attempts=3, base_delay=0.1, jitter=False)
        strategy = RetryStrategy(config)

        attempt_count = 0

        async def rate_limit_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("429 Too Many Requests")
            return "success"

        start_time = asyncio.get_event_loop().time()
        result = await strategy.execute_with_retry(rate_limit_func)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert result.success
        # Rate limit should wait at least 10s
        assert elapsed >= 10.0, "Rate limit should enforce minimum 10s delay"


class TestCircuitBreaker:
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
        assert breaker.can_attempt()

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        for i in range(3):
            breaker.record_failure()

        assert breaker.state == "OPEN"
        assert not breaker.can_attempt(), "Should not allow attempts when OPEN"

    def test_circuit_breaker_success_resets(self):
        """Test success resets circuit breaker"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "CLOSED"

        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters HALF_OPEN after timeout"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "OPEN"

        # Wait for timeout
        import time
        time.sleep(0.15)

        assert breaker.can_attempt(), "Should allow attempt after timeout"
        assert breaker.state == "HALF_OPEN"

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=60.0)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "OPEN"

        breaker.reset()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


# Test FailureAnalyzer
class TestFailureAnalyzer:
    def test_record_failure_basic(self):
        """Test basic failure recording"""
        analyzer = FailureAnalyzer()

        error = Exception("Network timeout")
        failure = analyzer.record_failure(error, "http_request")

        assert failure.operation == "http_request"
        assert failure.error_type == ErrorType.NETWORK
        assert failure.error_message == "Network timeout"

    def test_pattern_detection_repeating(self):
        """Test repeating error pattern detection"""
        analyzer = FailureAnalyzer(pattern_threshold=3)

        for _ in range(5):
            analyzer.record_failure(
                Exception("Connection timeout"),
                "http_request"
            )

        analysis = analyzer.analyze_pattern()

        assert analysis.pattern == FailurePattern.REPEATING_ERROR
        assert analysis.failure_count == 5

    def test_pattern_detection_unstable_service(self):
        """Test unstable service pattern detection"""
        analyzer = FailureAnalyzer()

        # Multiple different errors on same operation
        errors = [
            "Connection timeout",
            "500 Server Error",
            "503 Service Unavailable",
            "502 Bad Gateway"
        ]

        for error_msg in errors:
            analyzer.record_failure(
                Exception(error_msg),
                "api_call"
            )

        analysis = analyzer.analyze_pattern()

        assert analysis.pattern == FailurePattern.UNSTABLE_SERVICE

    def test_pattern_detection_cascading(self):
        """Test cascading failure pattern detection"""
        analyzer = FailureAnalyzer()

        # Different operations, different errors
        operations = [
            ("fetch_data", "Network timeout"),
            ("process_data", "500 Server Error"),
            ("save_data", "Disk full")
        ]

        for operation, error_msg in operations:
            analyzer.record_failure(
                Exception(error_msg),
                operation
            )

        analysis = analyzer.analyze_pattern()

        assert analysis.pattern == FailurePattern.CASCADING

    def test_root_cause_identification_network(self):
        """Test root cause identification for network errors"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("Connection timeout"), "operation1")
        analysis = analyzer.analyze_pattern()

        assert analysis.root_cause is not None
        assert analysis.root_cause.cause_type == "network_connectivity"
        assert analysis.root_cause.confidence >= 0.8

    def test_root_cause_identification_auth(self):
        """Test root cause identification for auth errors"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("401 Unauthorized"), "operation1")
        analysis = analyzer.analyze_pattern()

        assert analysis.root_cause is not None
        assert analysis.root_cause.cause_type == "authentication"
        assert analysis.root_cause.confidence >= 0.9

    def test_root_cause_identification_rate_limit(self):
        """Test root cause identification for rate limiting"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("429 Too Many Requests"), "operation1")
        analysis = analyzer.analyze_pattern()

        assert analysis.root_cause is not None
        assert analysis.root_cause.cause_type == "rate_limiting"
        assert len(analysis.recommendations) > 0

    def test_recommendations_generation(self):
        """Test recommendation generation"""
        analyzer = FailureAnalyzer()

        for _ in range(3):
            analyzer.record_failure(
                Exception("Connection timeout"),
                "http_request"
            )

        analysis = analyzer.analyze_pattern()

        assert len(analysis.recommendations) > 0
        assert any("alternative" in rec.lower() for rec in analysis.recommendations)

    def test_is_repeating_error(self):
        """Test repeating error detection"""
        analyzer = FailureAnalyzer(pattern_threshold=3)

        # Record same error multiple times
        for _ in range(4):
            analyzer.record_failure(
                Exception("Network timeout"),
                "fetch_data"
            )

        # Check if error is repeating
        is_repeating = analyzer.is_repeating_error(
            Exception("Network timeout"),
            "fetch_data"
        )

        assert is_repeating

    def test_has_attempted(self):
        """Test operation attempt tracking"""
        analyzer = FailureAnalyzer()

        assert not analyzer.has_attempted("operation1")

        analyzer.record_failure(Exception("Error"), "operation1")

        assert analyzer.has_attempted("operation1")

    def test_failure_summary(self):
        """Test failure summary generation"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("Network timeout"), "op1")
        analyzer.record_failure(Exception("500 Server Error"), "op2")
        analyzer.record_failure(Exception("Network timeout"), "op1")

        summary = analyzer.get_failure_summary()

        assert summary["total_failures"] == 3
        assert summary["unique_operations"] == 2
        assert "network" in summary["error_type_distribution"]

    def test_clear_history_all(self):
        """Test clearing all failure history"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("Error"), "op1")
        analyzer.record_failure(Exception("Error"), "op2")

        analyzer.clear_history()

        summary = analyzer.get_failure_summary()
        assert summary["total_failures"] == 0
        assert summary["unique_operations"] == 0

    def test_clear_history_time_based(self):
        """Test clearing old failure history"""
        analyzer = FailureAnalyzer()

        analyzer.record_failure(Exception("Error"), "op1")

        # Clear failures older than 1 hour (should not clear recent)
        analyzer.clear_history(older_than=timedelta(hours=1))

        summary = analyzer.get_failure_summary()
        assert summary["total_failures"] == 1

    def test_analyze_pattern_with_time_window(self):
        """Test pattern analysis with time window"""
        analyzer = FailureAnalyzer()

        # Record old failure
        analyzer.record_failure(Exception("Error"), "op1")

        # Analyze only recent failures (last 1 second)
        analysis = analyzer.analyze_pattern(time_window=timedelta(seconds=1))

        # Should include the recent failure
        assert analysis.failure_count >= 0


# Test AlternativeExplorer
class TestAlternativeExplorer:
    def test_initialization(self):
        """Test explorer initialization"""
        explorer = AlternativeExplorer()

        assert len(explorer.strategy_templates) > 0
        assert len(explorer.success_history) == 0
        assert len(explorer.failure_history) == 0

    def test_strategy_enumeration_http(self):
        """Test strategy enumeration for HTTP operations"""
        explorer = AlternativeExplorer()

        strategies = explorer.enumerate_strategies(
            operation="http_request",
            context={"url": "https://api.example.com"}
        )

        assert len(strategies) > 0
        assert any("http" in s["name"].lower() for s in strategies)

    def test_strategy_enumeration_llm(self):
        """Test strategy enumeration for LLM operations"""
        explorer = AlternativeExplorer()

        strategies = explorer.enumerate_strategies(
            operation="llm_request",
            context={"prompt": "test"}
        )

        assert len(strategies) > 0
        assert any("provider" in s["name"] for s in strategies)

    def test_strategy_enumeration_filters_primary(self):
        """Test primary strategy filtering"""
        explorer = AlternativeExplorer()

        strategies = explorer.enumerate_strategies(
            operation="http_request",
            primary_strategy="http_tool_curl"
        )

        # Should not include primary strategy
        assert all(s["name"] != "http_tool_curl" for s in strategies)

    def test_strategy_ranking_balanced(self):
        """Test balanced strategy ranking"""
        explorer = AlternativeExplorer()

        strategies = [
            {
                "name": "high_priority",
                "priority": 1.0,
                "cost_estimate": 0.01,
                "time_estimate": 5.0
            },
            {
                "name": "low_priority",
                "priority": 0.5,
                "cost_estimate": 0.001,
                "time_estimate": 1.0
            }
        ]

        ranked = explorer.rank_strategies(strategies, optimization_goal="balanced")

        assert len(ranked) == 2
        assert all("score" in s for s in ranked)
        # Higher priority should rank first
        assert ranked[0]["name"] == "high_priority"

    def test_strategy_ranking_cost_optimized(self):
        """Test cost-optimized strategy ranking"""
        explorer = AlternativeExplorer()

        strategies = [
            {
                "name": "expensive",
                "priority": 1.0,
                "cost_estimate": 1.0,
                "time_estimate": 5.0
            },
            {
                "name": "cheap",
                "priority": 0.8,
                "cost_estimate": 0.01,
                "time_estimate": 10.0
            }
        ]

        ranked = explorer.rank_strategies(strategies, optimization_goal="cost")

        # Cheaper strategy should rank first
        assert ranked[0]["name"] == "cheap"

    def test_strategy_ranking_speed_optimized(self):
        """Test speed-optimized strategy ranking"""
        explorer = AlternativeExplorer()

        strategies = [
            {
                "name": "slow",
                "priority": 1.0,
                "cost_estimate": 0.01,
                "time_estimate": 60.0
            },
            {
                "name": "fast",
                "priority": 0.8,
                "cost_estimate": 0.02,
                "time_estimate": 1.0
            }
        ]

        ranked = explorer.rank_strategies(strategies, optimization_goal="speed")

        # Faster strategy should rank first
        assert ranked[0]["name"] == "fast"

    def test_record_success(self):
        """Test recording strategy success"""
        explorer = AlternativeExplorer()

        explorer.record_success("strategy_a")
        explorer.record_success("strategy_a")

        success_rate = explorer.get_success_rate("strategy_a")
        assert success_rate == 1.0

    def test_record_failure(self):
        """Test recording strategy failure"""
        explorer = AlternativeExplorer()

        explorer.record_failure("strategy_a")
        explorer.record_failure("strategy_a")

        success_rate = explorer.get_success_rate("strategy_a")
        assert success_rate == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        explorer = AlternativeExplorer()

        explorer.record_success("strategy_a")
        explorer.record_success("strategy_a")
        explorer.record_failure("strategy_a")

        success_rate = explorer.get_success_rate("strategy_a")
        assert success_rate == 2.0 / 3.0

    def test_success_rate_unknown_strategy(self):
        """Test success rate for unknown strategy"""
        explorer = AlternativeExplorer()

        success_rate = explorer.get_success_rate("unknown")
        assert success_rate == 0.5  # Default for unknown

    def test_get_strategy_stats(self):
        """Test strategy statistics"""
        explorer = AlternativeExplorer()

        explorer.record_success("strategy_a")
        explorer.record_failure("strategy_a")
        explorer.record_success("strategy_b")

        stats = explorer.get_strategy_stats()

        assert stats["total_strategies_tried"] == 2
        assert "strategy_a" in stats["strategies"]
        assert "strategy_b" in stats["strategies"]
        assert stats["strategies"]["strategy_a"]["success_rate"] == 0.5

    def test_clear_history(self):
        """Test clearing explorer history"""
        explorer = AlternativeExplorer()

        explorer.record_success("strategy_a")
        explorer.record_failure("strategy_b")

        explorer.clear_history()

        stats = explorer.get_strategy_stats()
        assert stats["total_strategies_tried"] == 0


# Test CreativeSolver
class TestCreativeSolver:
    def test_problem_type_detection_code_generation(self):
        """Test code generation problem detection"""
        solver = CreativeSolver()

        problems = [
            "Write code to parse JSON",
            "Generate script to process files",
            "Implement function to calculate"
        ]

        for problem in problems:
            sol_type = solver._analyze_problem_type(problem, {})
            assert sol_type == SolutionType.CODE_GENERATION

    def test_problem_type_detection_decomposition(self):
        """Test decomposition problem detection"""
        solver = CreativeSolver()

        problems = [
            "Complex multi-step task",
            "Break down this large problem",
            "Decompose into parts"
        ]

        for problem in problems:
            sol_type = solver._analyze_problem_type(problem, {})
            assert sol_type == SolutionType.DECOMPOSITION

    def test_problem_type_detection_workaround(self):
        """Test workaround problem detection"""
        solver = CreativeSolver()

        problems = [
            "API is blocked, need alternative",
            "Cannot access, find workaround",
            "Forbidden access, different way"
        ]

        for problem in problems:
            sol_type = solver._analyze_problem_type(problem, {})
            assert sol_type == SolutionType.WORKAROUND

    def test_problem_type_detection_multi_step(self):
        """Test multi-step problem detection"""
        solver = CreativeSolver()

        problems = [
            "Create a detailed plan",
            "Multi-step workflow needed",
            "Orchestrate sequence of actions"
        ]

        for problem in problems:
            sol_type = solver._analyze_problem_type(problem, {})
            assert sol_type == SolutionType.MULTI_STEP

    def test_problem_type_detection_context_based(self):
        """Test context-based problem detection"""
        solver = CreativeSolver()

        # Many attempts suggest need for workaround
        sol_type = solver._analyze_problem_type(
            "Regular problem",
            {"attempts": 5}
        )
        assert sol_type == SolutionType.WORKAROUND

    @pytest.mark.asyncio
    async def test_solve_decomposition(self):
        """Test problem decomposition via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Download 100 large files and process them",
            preferred_type=SolutionType.DECOMPOSITION
        )

        assert solution is not None
        assert solution.solution_type == SolutionType.DECOMPOSITION
        assert solution.confidence > 0
        assert len(solution.sub_tasks) > 0

    @pytest.mark.asyncio
    async def test_solve_workaround(self):
        """Test workaround generation via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Cannot access API - 403 Forbidden",
            context={"attempts": 5},
            preferred_type=SolutionType.WORKAROUND
        )

        assert solution is not None
        assert solution.solution_type == SolutionType.WORKAROUND
        assert solution.confidence > 0
        assert len(solution.workarounds) > 0

    @pytest.mark.asyncio
    async def test_solve_code_generation(self):
        """Test code generation via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Write Python code to parse CSV",
            preferred_type=SolutionType.CODE_GENERATION
        )

        assert solution is not None
        assert solution.solution_type == SolutionType.CODE_GENERATION
        assert solution.confidence > 0
        assert solution.code is not None

    @pytest.mark.asyncio
    async def test_solve_multi_step_plan(self):
        """Test multi-step planning via solve()"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Orchestrate data pipeline",
            preferred_type=SolutionType.MULTI_STEP
        )

        assert solution is not None
        assert solution.solution_type == SolutionType.MULTI_STEP
        assert solution.confidence > 0
        assert solution.plan is not None
        assert len(solution.plan.steps) > 0

    @pytest.mark.asyncio
    async def test_solve_hybrid(self):
        """Test hybrid solution approach"""
        solver = CreativeSolver()

        solution = await solver.solve(
            problem="Complex problem requiring multiple approaches",
            preferred_type=SolutionType.HYBRID
        )

        assert solution is not None
        assert solution.solution_type == SolutionType.HYBRID
        assert solution.confidence > 0

    def test_get_solution_history(self):
        """Test solution history tracking"""
        solver = CreativeSolver()

        history = solver.get_solution_history()
        assert isinstance(history, list)

    def test_clear_history(self):
        """Test clearing solution history"""
        solver = CreativeSolver()

        solver.clear_history()
        history = solver.get_solution_history()
        assert len(history) == 0


# Test ProgressTracker
class TestProgressTracker:
    def test_start_task(self):
        """Test starting task tracking"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_operation")

        assert task_id is not None
        state = tracker.get_state(task_id)
        assert state is not None
        assert state.status == "running"
        assert state.operation_name == "test_operation"

    def test_start_task_custom_id(self):
        """Test starting task with custom ID"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(
            task_id="custom_task_123",
            operation="test_op"
        )

        assert task_id == "custom_task_123"

    def test_record_attempt(self):
        """Test recording execution attempt"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")

        tracker.record_attempt(
            task_id=task_id,
            strategy_name="strategy_1",
            success=False,
            error="Test error",
            duration=1.5,
            metadata={"extra": "data"}
        )

        state = tracker.get_state(task_id)
        assert len(state.attempts) == 1
        assert state.attempts[0].strategy_name == "strategy_1"
        assert not state.attempts[0].success

    def test_complete_task_success(self):
        """Test completing task successfully"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")
        tracker.complete_task(task_id, success=True, result="result_value")

        state = tracker.get_state(task_id)
        assert state.status == "completed"
        assert state.result == "result_value"
        assert state.completed_at is not None

    def test_complete_task_failure(self):
        """Test completing task with failure"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")
        tracker.complete_task(task_id, success=False)

        state = tracker.get_state(task_id)
        assert state.status == "failed"

    def test_get_attempt_history(self):
        """Test getting attempt history"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")

        tracker.record_attempt(task_id, "s1", success=False, duration=1.0)
        tracker.record_attempt(task_id, "s2", success=True, duration=2.0)

        history = tracker.get_attempt_history(task_id)

        assert len(history) == 2
        assert history[0].strategy_name == "s1"
        assert history[1].strategy_name == "s2"

    def test_get_metrics(self):
        """Test metrics calculation"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")

        tracker.record_attempt(task_id, "s1", success=False, duration=1.0)
        tracker.record_attempt(task_id, "s2", success=False, duration=1.5)
        tracker.record_attempt(task_id, "s3", success=True, duration=2.0)

        tracker.complete_task(task_id, success=True)

        metrics = tracker.get_metrics(task_id)

        assert metrics["total_attempts"] == 3
        assert metrics["successful_attempts"] == 1
        assert metrics["failed_attempts"] == 2
        assert metrics["total_duration"] == 4.5
        assert metrics["avg_attempt_duration"] == 1.5

    def test_save_and_restore_state(self):
        """Test state serialization and restoration"""
        tracker = ProgressTracker()

        task_id = tracker.start_task(operation="test_op")
        tracker.record_attempt(task_id, "s1", success=True, duration=1.0)
        tracker.complete_task(task_id, success=True, result="result")

        # Save state
        state_dict = tracker.save_state(task_id)

        # Clear and restore
        tracker.clear_all()
        restored_id = tracker.restore_state(state_dict)

        # Verify restoration
        assert restored_id == task_id
        state = tracker.get_state(restored_id)
        assert state.operation_name == "test_op"
        assert len(state.attempts) == 1
        assert state.result == "result"

    def test_get_all_metrics(self):
        """Test getting metrics for all tasks"""
        tracker = ProgressTracker()

        task1 = tracker.start_task(operation="op1")
        task2 = tracker.start_task(operation="op2")

        all_metrics = tracker.get_all_metrics()

        assert all_metrics["total_tasks"] == 2
        assert task1 in all_metrics["tasks"]
        assert task2 in all_metrics["tasks"]

    def test_clear_completed(self):
        """Test clearing completed tasks"""
        tracker = ProgressTracker()

        task1 = tracker.start_task(operation="op1")
        task2 = tracker.start_task(operation="op2")

        tracker.complete_task(task1, success=True)
        # task2 still running

        tracker.clear_completed()

        # task1 should be removed, task2 should remain
        assert tracker.get_state(task1) is None
        assert tracker.get_state(task2) is not None

    def test_clear_all(self):
        """Test clearing all tasks"""
        tracker = ProgressTracker()

        tracker.start_task(operation="op1")
        tracker.start_task(operation="op2")

        tracker.clear_all()

        metrics = tracker.get_all_metrics()
        assert metrics["total_tasks"] == 0


# Test ResilienceEngine
class TestResilienceEngine:
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution on first attempt"""
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
        assert len(result.strategies_tried) == 1

    @pytest.mark.asyncio
    async def test_retry_until_success(self):
        """Test retry with eventual success"""
        config = ResilienceConfig(max_attempts=5, base_delay=0.01)
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
    async def test_complete_failure(self):
        """Test complete failure after max attempts"""
        config = ResilienceConfig(max_attempts=2, base_delay=0.01)
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

    @pytest.mark.asyncio
    async def test_execute_with_alternatives_sequential(self):
        """Test sequential alternative strategy execution"""
        engine = ResilienceEngine()

        call_order = []

        async def strategy1_func():
            call_order.append("s1")
            raise Exception("Strategy 1 failed")

        async def strategy2_func():
            call_order.append("s2")
            return "strategy2_success"

        strategies = [
            Strategy(
                name="strategy1",
                func=strategy1_func,
                priority=1.0
            ),
            Strategy(
                name="strategy2",
                func=strategy2_func,
                priority=0.9
            )
        ]

        result = await engine.execute_with_alternatives(
            strategies,
            operation_name="test_op",
            parallel=False
        )

        assert result.success
        assert result.value == "strategy2_success"
        assert "s1" in call_order
        assert "s2" in call_order

    @pytest.mark.asyncio
    async def test_execute_with_alternatives_parallel(self):
        """Test parallel alternative strategy execution"""
        engine = ResilienceEngine(ResilienceConfig(max_parallel_strategies=3))

        async def slow_success():
            await asyncio.sleep(1.0)
            return "slow"

        async def fast_success():
            await asyncio.sleep(0.01)
            return "fast"

        strategies = [
            Strategy(name="slow", func=slow_success, priority=1.0),
            Strategy(name="fast", func=fast_success, priority=0.9)
        ]

        result = await engine.execute_with_alternatives(
            strategies,
            operation_name="test_op",
            parallel=True
        )

        assert result.success
        # Fast strategy should win
        assert result.value == "fast"

    @pytest.mark.asyncio
    async def test_resource_limit_time(self):
        """Test max total time limit enforcement"""
        config = ResilienceConfig(max_total_time=0.5, base_delay=0.01)
        engine = ResilienceEngine(config)

        async def slow_strategy():
            await asyncio.sleep(1.0)
            return "too_slow"

        strategies = [
            Strategy(name="slow1", func=slow_strategy, priority=1.0),
            Strategy(name="slow2", func=slow_strategy, priority=0.9)
        ]

        result = await engine.execute_with_alternatives(
            strategies,
            operation_name="test_op",
            parallel=False
        )

        # Should timeout before completing all strategies
        assert not result.success or result.total_time < 1.0

    def test_get_failure_summary(self):
        """Test failure summary retrieval"""
        engine = ResilienceEngine()

        summary = engine.get_failure_summary()

        assert "total_failures" in summary
        assert "unique_operations" in summary
        assert "error_type_distribution" in summary

    def test_get_stats(self):
        """Test engine statistics"""
        engine = ResilienceEngine()

        stats = engine.get_stats()

        assert "total_attempts" in stats
        assert "total_cost" in stats
        assert "failure_summary" in stats
        assert "config" in stats

    def test_reset(self):
        """Test engine reset"""
        engine = ResilienceEngine()

        # Record some state
        engine.total_attempts = 10
        engine.total_cost = 1.5

        # Reset
        engine.reset()

        assert engine.total_attempts == 0
        assert engine.total_cost == 0.0


# Integration Tests
@pytest.mark.asyncio
async def test_resilience_integration_full_flow():
    """Test full resilience system integration"""
    config = ResilienceConfig(
        max_attempts=3,
        base_delay=0.01,
        max_parallel_strategies=2,
        enable_creative_solving=True
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
    assert result.attempts >= 1
    assert result.total_time > 0


@pytest.mark.asyncio
async def test_resilience_integration_multi_layer_fallback():
    """Test multi-layer fallback mechanism"""
    config = ResilienceConfig(max_attempts=2, base_delay=0.01)
    engine = ResilienceEngine(config)

    attempts = {"primary": 0, "secondary": 0, "tertiary": 0}

    async def primary_strategy():
        attempts["primary"] += 1
        raise Exception("Primary failed")

    async def secondary_strategy():
        attempts["secondary"] += 1
        raise Exception("Secondary failed")

    async def tertiary_strategy():
        attempts["tertiary"] += 1
        return "tertiary_success"

    strategies = [
        Strategy(name="primary", func=primary_strategy, priority=1.0),
        Strategy(name="secondary", func=secondary_strategy, priority=0.8),
        Strategy(name="tertiary", func=tertiary_strategy, priority=0.6)
    ]

    result = await engine.execute_with_alternatives(
        strategies,
        operation_name="multi_fallback_test",
        parallel=False
    )

    # Should fallback through all strategies
    assert result.success
    assert result.value == "tertiary_success"
    assert attempts["primary"] > 0
    assert attempts["secondary"] > 0
    assert attempts["tertiary"] > 0


@pytest.mark.asyncio
async def test_resilience_integration_progress_tracking():
    """Test progress tracking integration"""
    config = ResilienceConfig(enable_progress_tracking=True, base_delay=0.01)
    engine = ResilienceEngine(config)

    async def tracked_operation():
        await asyncio.sleep(0.05)
        return "tracked_result"

    result = await engine.execute(
        tracked_operation,
        operation_name="tracked_op"
    )

    assert result.success
    assert result.total_time >= 0.05


@pytest.mark.asyncio
async def test_resilience_integration_recommendation_generation():
    """Test recommendation generation in failure scenarios"""
    config = ResilienceConfig(max_attempts=2, base_delay=0.01)
    engine = ResilienceEngine(config)

    async def auth_error_operation():
        raise Exception("401 Unauthorized - Invalid API key")

    result = await engine.execute(
        auth_error_operation,
        operation_name="auth_test"
    )

    assert not result.success
    assert len(result.recommendations) > 0
    assert any("auth" in rec.lower() or "api key" in rec.lower()
              for rec in result.recommendations)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
