"""
Retry Strategy Component

Manages intelligent retry logic with exponential backoff, jitter, and circuit breaker patterns.
"""

import asyncio
import random
import logging
from enum import Enum
from typing import Callable, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorType(Enum):
    """Error classification for retry decisions"""
    NETWORK = "network"
    AUTHENTICATION = "auth"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server"
    CLIENT_ERROR = "client"
    LOGIC_ERROR = "logic"
    DATA_ERROR = "data"
    RESOURCE_EXHAUSTED = "resource"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class RetryResult(Generic[T]):
    """Result of retry execution"""
    success: bool
    value: Optional[T] = None
    error: Optional[Exception] = None
    attempts: int = 0
    total_time: float = 0.0
    error_type: Optional[ErrorType] = None


class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests fail fast
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"

    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.debug("Circuit breaker: success recorded, state CLOSED")

    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN: {self.failure_count} consecutive failures")

    def can_attempt(self) -> bool:
        """Check if attempt should be allowed"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker: HALF_OPEN (testing recovery)")
                    return True
            return False

        # HALF_OPEN state: allow one attempt
        return True

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"


class RetryStrategy:
    """
    Intelligent retry strategy with exponential backoff.

    Features:
    - Exponential backoff with configurable factor
    - Random jitter to prevent thundering herd
    - Circuit breaker for failing services
    - Error classification for retry decisions
    - Maximum delay cap
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            self.config.circuit_breaker_threshold,
            self.config.circuit_breaker_timeout
        )

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error to determine retry strategy.

        Args:
            error: Exception that occurred

        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()

        # Server errors (check first before generic timeout)
        if any(keyword in error_str for keyword in
               ['500 ', '502 ', '503 ', '504 ', 'internal server error', 'bad gateway',
                'service unavailable', 'gateway timeout']):
            return ErrorType.SERVER_ERROR

        # Network errors
        if any(keyword in error_str for keyword in
               ['connection', 'timeout', 'dns', 'network', 'unreachable']):
            return ErrorType.NETWORK

        # Authentication errors
        if any(keyword in error_str for keyword in
               ['auth', 'unauthorized', 'forbidden', 'permission', 'api key']):
            return ErrorType.AUTHENTICATION

        # Rate limiting
        if any(keyword in error_str for keyword in
               ['rate limit', 'too many requests', '429', 'quota']):
            return ErrorType.RATE_LIMIT

        # Server errors (5xx)
        if any(keyword in error_str for keyword in
               ['500', '502', '503', '504', 'server error', 'internal server']):
            return ErrorType.SERVER_ERROR

        # Client errors (4xx)
        if any(keyword in error_str for keyword in
               ['400', '404', '422', 'bad request', 'not found', 'invalid']):
            return ErrorType.CLIENT_ERROR

        # Resource exhaustion
        if any(keyword in error_str for keyword in
               ['memory', 'disk', 'space', 'resource']):
            return ErrorType.RESOURCE_EXHAUSTED

        # Data/parsing errors
        if any(keyword in error_type_name for keyword in
               ['parse', 'json', 'decode', 'value', 'type']):
            return ErrorType.DATA_ERROR

        # Logic errors
        if any(keyword in error_type_name for keyword in
               ['assert', 'attribute', 'key', 'index']):
            return ErrorType.LOGIC_ERROR

        return ErrorType.UNKNOWN

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if error should trigger retry.

        Retryable:
        - Network errors
        - Server errors (5xx)
        - Rate limits
        - Unknown errors (be optimistic)

        Non-retryable:
        - Authentication errors (need different credentials)
        - Client errors (bad request won't succeed on retry)
        - Logic errors (code issue, not transient)

        Args:
            error: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        error_type = self.classify_error(error)

        retryable_types = {
            ErrorType.NETWORK,
            ErrorType.SERVER_ERROR,
            ErrorType.RATE_LIMIT,
            ErrorType.RESOURCE_EXHAUSTED,
            ErrorType.UNKNOWN
        }

        return error_type in retryable_types

    def get_next_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Uses exponential backoff: delay = base_delay * (backoff_factor ^ attempt)
        Adds jitter to prevent thundering herd
        Caps at max_delay

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate base exponential backoff
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)

        # Apply max delay cap
        delay = min(delay, self.config.max_delay)

        # Add jitter (randomize ±25%)
        if self.config.jitter:
            jitter_range = delay * 0.25
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)

        return delay

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> RetryResult:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            RetryResult with success status and value/error
        """
        start_time = datetime.now()
        last_error: Optional[Exception] = None
        last_error_type: Optional[ErrorType] = None

        for attempt in range(self.config.max_attempts):
            # Check circuit breaker
            if not self.circuit_breaker.can_attempt():
                logger.warning(f"Circuit breaker OPEN, failing fast")
                return RetryResult(
                    success=False,
                    error=last_error,
                    attempts=attempt,
                    total_time=(datetime.now() - start_time).total_seconds(),
                    error_type=last_error_type
                )

            try:
                logger.debug(f"Attempt {attempt + 1}/{self.config.max_attempts}")

                # Execute function
                result = await func(*args, **kwargs)

                # Success!
                self.circuit_breaker.record_success()

                total_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Success after {attempt + 1} attempts ({total_time:.2f}s)")

                return RetryResult(
                    success=True,
                    value=result,
                    attempts=attempt + 1,
                    total_time=total_time
                )

            except Exception as e:
                last_error = e
                last_error_type = self.classify_error(e)

                logger.warning(
                    f"Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)[:100]}"
                )

                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                # Check if should retry
                if not self.should_retry(e):
                    logger.info(f"Error not retryable: {last_error_type}")
                    break

                # Check if this was last attempt
                if attempt >= self.config.max_attempts - 1:
                    logger.warning(f"Max attempts ({self.config.max_attempts}) reached")
                    break

                # Calculate delay
                delay = self.get_next_delay(attempt)

                # Special handling for rate limits
                if last_error_type == ErrorType.RATE_LIMIT:
                    delay = max(delay, 10.0)  # Minimum 10s for rate limits

                logger.info(f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)

        # All attempts failed
        total_time = (datetime.now() - start_time).total_seconds()

        return RetryResult(
            success=False,
            error=last_error,
            attempts=self.config.max_attempts,
            total_time=total_time,
            error_type=last_error_type
        )

    def reset(self):
        """Reset retry strategy state"""
        self.circuit_breaker.reset()
