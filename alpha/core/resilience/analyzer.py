"""
Failure Analyzer Component

Analyzes failure patterns to avoid repeating failed approaches.
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
from enum import Enum

from .retry import ErrorType

logger = logging.getLogger(__name__)


class FailurePattern(Enum):
    """Types of failure patterns"""
    REPEATING_ERROR = "repeating"       # Same error multiple times
    CASCADING = "cascading"             # Different errors from same operation
    INTERMITTENT = "intermittent"       # Alternating success/failure
    PERMANENT = "permanent"             # Consistent failure
    UNSTABLE_SERVICE = "unstable"       # Service showing multiple error types


@dataclass
class Failure:
    """Record of a single failure"""
    timestamp: datetime
    error_type: ErrorType
    error_message: str
    operation: str
    context: Dict = field(default_factory=dict)
    stack_trace: Optional[str] = None


@dataclass
class RootCause:
    """Identified root cause of failure"""
    cause_type: str
    description: str
    suggested_action: str
    confidence: float  # 0.0 to 1.0


@dataclass
class FailureAnalysis:
    """
    Analysis result of failure patterns.

    Attributes:
        pattern: Detected failure pattern
        root_cause: Identified root cause
        failure_count: Number of failures analyzed
        time_span: Time range of failures
        recommendations: List of recommended actions
    """
    pattern: FailurePattern
    root_cause: Optional[RootCause]
    failure_count: int
    time_span: timedelta
    recommendations: List[str] = field(default_factory=list)


class FailureAnalyzer:
    """
    Analyzes failures to identify patterns and root causes.

    Features:
    - Error classification and categorization
    - Pattern recognition (repeating, cascading, intermittent)
    - Root cause analysis
    - Failure memory to avoid repetition
    - Recommendation generation
    """

    def __init__(self, pattern_threshold: int = 3):
        """
        Initialize failure analyzer.

        Args:
            pattern_threshold: Number of failures to detect pattern
        """
        self.pattern_threshold = pattern_threshold
        self.failure_history: List[Failure] = []
        self.attempted_operations: Set[str] = set()

    def record_failure(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict] = None
    ) -> Failure:
        """
        Record a failure for analysis.

        Args:
            error: Exception that occurred
            operation: Operation that failed
            context: Additional context information

        Returns:
            Failure record
        """
        from .retry import RetryStrategy

        # Classify error
        retry_strategy = RetryStrategy()
        error_type = retry_strategy.classify_error(error)

        failure = Failure(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=str(error),
            operation=operation,
            context=context or {},
            stack_trace=None  # Could be enhanced to capture stack
        )

        self.failure_history.append(failure)
        self.attempted_operations.add(operation)

        logger.debug(f"Recorded failure: {error_type} for {operation}")

        return failure

    def analyze_pattern(
        self,
        failures: Optional[List[Failure]] = None,
        time_window: Optional[timedelta] = None
    ) -> FailureAnalysis:
        """
        Analyze failure pattern.

        Args:
            failures: List of failures to analyze (default: all history)
            time_window: Time window to consider (default: last hour)

        Returns:
            FailureAnalysis with detected pattern and recommendations
        """
        if failures is None:
            failures = self.failure_history

        if not failures:
            return FailureAnalysis(
                pattern=FailurePattern.PERMANENT,
                root_cause=None,
                failure_count=0,
                time_span=timedelta(0)
            )

        # Apply time window filter
        if time_window:
            cutoff_time = datetime.now() - time_window
            failures = [f for f in failures if f.timestamp >= cutoff_time]

        if not failures:
            return FailureAnalysis(
                pattern=FailurePattern.PERMANENT,
                root_cause=None,
                failure_count=0,
                time_span=timedelta(0)
            )

        # Calculate time span
        time_span = failures[-1].timestamp - failures[0].timestamp

        # Detect pattern
        pattern = self._detect_pattern(failures)

        # Identify root cause
        root_cause = self._identify_root_cause(failures, pattern)

        # Generate recommendations
        recommendations = self._generate_recommendations(failures, pattern, root_cause)

        return FailureAnalysis(
            pattern=pattern,
            root_cause=root_cause,
            failure_count=len(failures),
            time_span=time_span,
            recommendations=recommendations
        )

    def _detect_pattern(self, failures: List[Failure]) -> FailurePattern:
        """
        Detect failure pattern from history.

        Args:
            failures: List of failures

        Returns:
            Detected FailurePattern
        """
        if len(failures) < 2:
            return FailurePattern.PERMANENT

        # Count error types
        error_types = [f.error_type for f in failures]
        error_counter = Counter(error_types)

        # Check for repeating error
        most_common_error, count = error_counter.most_common(1)[0]
        if count == len(failures):
            return FailurePattern.REPEATING_ERROR

        # Check for multiple different errors on same operation
        operations = [f.operation for f in failures]
        if len(set(operations)) == 1 and len(error_counter) >= 2:
            return FailurePattern.UNSTABLE_SERVICE

        # Check for cascading failures
        unique_operations = len(set(operations))
        if unique_operations > 1 and len(error_counter) >= unique_operations:
            return FailurePattern.CASCADING

        # Default to permanent failure
        return FailurePattern.PERMANENT

    def _identify_root_cause(
        self,
        failures: List[Failure],
        pattern: FailurePattern
    ) -> Optional[RootCause]:
        """
        Identify root cause of failures.

        Args:
            failures: List of failures
            pattern: Detected pattern

        Returns:
            RootCause if identified, None otherwise
        """
        if not failures:
            return None

        # Analyze error types
        error_types = [f.error_type for f in failures]
        most_common_error = Counter(error_types).most_common(1)[0][0]

        # Root cause mapping
        root_cause_map = {
            ErrorType.NETWORK: RootCause(
                cause_type="network_connectivity",
                description="Network connectivity issues or service unreachable",
                suggested_action="Check network connection, try alternative endpoints, or wait for service recovery",
                confidence=0.9
            ),
            ErrorType.AUTHENTICATION: RootCause(
                cause_type="authentication",
                description="Authentication credentials invalid or expired",
                suggested_action="Verify API key, check permissions, or refresh credentials",
                confidence=0.95
            ),
            ErrorType.RATE_LIMIT: RootCause(
                cause_type="rate_limiting",
                description="API rate limit exceeded",
                suggested_action="Implement exponential backoff, reduce request rate, or upgrade API plan",
                confidence=0.95
            ),
            ErrorType.SERVER_ERROR: RootCause(
                cause_type="server_issues",
                description="Remote server experiencing errors",
                suggested_action="Wait for server recovery, try alternative providers, or implement fallback",
                confidence=0.85
            ),
            ErrorType.CLIENT_ERROR: RootCause(
                cause_type="invalid_request",
                description="Request is malformed or invalid",
                suggested_action="Validate request parameters, check API documentation, or adjust input format",
                confidence=0.9
            ),
            ErrorType.DATA_ERROR: RootCause(
                cause_type="data_validation",
                description="Data parsing or validation failed",
                suggested_action="Verify data format, implement robust parsing, or sanitize inputs",
                confidence=0.85
            ),
            ErrorType.LOGIC_ERROR: RootCause(
                cause_type="code_logic",
                description="Logic error in implementation",
                suggested_action="Review code logic, fix algorithm, or adjust business rules",
                confidence=0.8
            ),
            ErrorType.RESOURCE_EXHAUSTED: RootCause(
                cause_type="resource_limits",
                description="System resource limits exceeded",
                suggested_action="Optimize resource usage, increase limits, or implement batching",
                confidence=0.9
            )
        }

        root_cause = root_cause_map.get(most_common_error)

        # Adjust confidence based on pattern
        if root_cause and pattern == FailurePattern.REPEATING_ERROR:
            root_cause.confidence = min(1.0, root_cause.confidence + 0.1)

        return root_cause

    def _generate_recommendations(
        self,
        failures: List[Failure],
        pattern: FailurePattern,
        root_cause: Optional[RootCause]
    ) -> List[str]:
        """
        Generate actionable recommendations.

        Args:
            failures: List of failures
            pattern: Detected pattern
            root_cause: Identified root cause

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Pattern-based recommendations
        if pattern == FailurePattern.REPEATING_ERROR:
            recommendations.append("Same error recurring - consider alternative approach")
            recommendations.append("Try different tool or method to achieve goal")

        elif pattern == FailurePattern.UNSTABLE_SERVICE:
            recommendations.append("Service appears unstable - implement fallback provider")
            recommendations.append("Add circuit breaker to fail fast")

        elif pattern == FailurePattern.CASCADING:
            recommendations.append("Cascading failures detected - check dependencies")
            recommendations.append("Consider breaking operation into smaller steps")

        elif pattern == FailurePattern.PERMANENT:
            recommendations.append("Consistent failure - fundamental issue with approach")
            recommendations.append("Rethink strategy or seek user intervention")

        # Root cause-based recommendations
        if root_cause:
            recommendations.append(root_cause.suggested_action)

        # Error-specific recommendations
        error_types = {f.error_type for f in failures}

        if ErrorType.RATE_LIMIT in error_types:
            recommendations.append("Implement request throttling or batching")

        if ErrorType.NETWORK in error_types:
            recommendations.append("Consider caching or offline fallback")

        if ErrorType.AUTHENTICATION in error_types:
            recommendations.append("Stop retrying - credentials need update")

        return recommendations

    def is_repeating_error(self, error: Exception, operation: str) -> bool:
        """
        Check if error is repeating for given operation.

        Args:
            error: Current error
            operation: Operation being attempted

        Returns:
            True if error has occurred multiple times for this operation
        """
        from .retry import RetryStrategy

        retry_strategy = RetryStrategy()
        current_error_type = retry_strategy.classify_error(error)

        # Count recent failures for this operation with same error type
        recent_failures = [
            f for f in self.failure_history[-10:]  # Last 10 failures
            if f.operation == operation and f.error_type == current_error_type
        ]

        return len(recent_failures) >= self.pattern_threshold

    def has_attempted(self, operation: str) -> bool:
        """
        Check if operation has been attempted before.

        Args:
            operation: Operation identifier

        Returns:
            True if operation was previously attempted
        """
        return operation in self.attempted_operations

    def get_failure_summary(self) -> Dict:
        """
        Get summary of failure history.

        Returns:
            Dictionary with failure statistics
        """
        if not self.failure_history:
            return {
                "total_failures": 0,
                "unique_operations": 0,
                "error_type_distribution": {},
                "most_common_error": None
            }

        error_types = [f.error_type.value for f in self.failure_history]
        error_counter = Counter(error_types)

        return {
            "total_failures": len(self.failure_history),
            "unique_operations": len(self.attempted_operations),
            "error_type_distribution": dict(error_counter),
            "most_common_error": error_counter.most_common(1)[0][0] if error_counter else None,
            "time_span": (
                self.failure_history[-1].timestamp - self.failure_history[0].timestamp
            ).total_seconds()
        }

    def clear_history(self, older_than: Optional[timedelta] = None):
        """
        Clear failure history.

        Args:
            older_than: Only clear failures older than this timedelta
        """
        if older_than:
            cutoff_time = datetime.now() - older_than
            self.failure_history = [
                f for f in self.failure_history
                if f.timestamp >= cutoff_time
            ]
        else:
            self.failure_history.clear()
            self.attempted_operations.clear()

        logger.debug(f"Cleared failure history (remaining: {len(self.failure_history)})")
