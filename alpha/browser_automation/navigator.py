"""
Alpha - Page Navigator

Handles browser page navigation with validation, waiting strategies, and error handling.
Provides comprehensive navigation control with timeout protection and state tracking.

Phase: 4.3 - Browser Automation
"""

import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from urllib.parse import urlparse

from .validator import PageValidator, ValidationResult

logger = logging.getLogger(__name__)


# Type alias for wait_until parameter
WaitUntilState = Literal["load", "domcontentloaded", "networkidle", "commit"]


@dataclass
class NavigationResult:
    """
    Result of a page navigation operation.

    Attributes:
        success: Whether navigation completed successfully
        url: Final URL after navigation (may differ from requested if redirected)
        title: Page title after navigation
        status_code: HTTP status code (e.g., 200, 404, 500)
        load_time: Time taken to load the page in seconds
        error: Error message if navigation failed
        metadata: Additional information about the navigation
    """
    success: bool
    url: Optional[str] = None
    title: Optional[str] = None
    status_code: Optional[int] = None
    load_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NavigationError(Exception):
    """Raised when navigation fails."""
    pass


class NavigationTimeoutError(NavigationError):
    """Raised when navigation times out."""
    pass


class InvalidURLError(NavigationError):
    """Raised when URL validation fails."""
    pass


class PageNavigator:
    """
    Manages browser page navigation with security validation and state tracking.

    Features:
    - URL validation before navigation
    - Multiple wait strategies (load, domcontentloaded, networkidle)
    - Timeout protection
    - Navigation history (back/forward)
    - Page reload functionality
    - Selector and URL waiting
    - Page state inspection

    Example:
        >>> navigator = PageNavigator(validator, config)
        >>> result = await navigator.navigate(page, "https://example.com")
        >>> if result.success:
        ...     print(f"Loaded {result.title} in {result.load_time}s")
    """

    def __init__(
        self,
        validator: PageValidator,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize page navigator.

        Args:
            validator: PageValidator instance for URL validation
            config: Browser automation configuration
        """
        self.validator = validator
        self.config = config or {}
        self.navigation_config = self.config.get("navigation", {})

        # Default timeouts
        self.default_timeout = self.navigation_config.get("timeout", 30000)  # milliseconds
        self.default_wait_until = self.navigation_config.get("wait_until", "load")

        # Track navigation state
        self.navigation_history: list[str] = []
        self.current_url: Optional[str] = None

        logger.info(
            f"PageNavigator initialized with timeout={self.default_timeout}ms, "
            f"wait_until={self.default_wait_until}"
        )

    async def navigate(
        self,
        page: Any,  # playwright.async_api.Page
        url: str,
        wait_until: WaitUntilState = "load",
        timeout: Optional[int] = None
    ) -> NavigationResult:
        """
        Navigate to a URL with validation and timeout protection.

        Args:
            page: Playwright page object
            url: Target URL
            wait_until: When to consider navigation succeeded
                - "load": Wait for load event
                - "domcontentloaded": Wait for DOMContentLoaded event
                - "networkidle": Wait for network to be idle
                - "commit": Wait for navigation to commit
            timeout: Timeout in milliseconds (uses default if None)

        Returns:
            NavigationResult with success status and page information

        Raises:
            InvalidURLError: If URL validation fails
            NavigationTimeoutError: If navigation times out
            NavigationError: If navigation fails for other reasons
        """
        start_time = datetime.now()
        timeout_ms = timeout or self.default_timeout

        logger.info(f"Navigating to {url} with wait_until={wait_until}, timeout={timeout_ms}ms")

        # Validate URL
        validation = self.validator.validate_url(url)
        if not validation.valid:
            error_msg = f"URL validation failed: {validation.reason}"
            logger.error(error_msg)
            raise InvalidURLError(error_msg)

        try:
            # Perform navigation
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout_ms
            )

            # Calculate load time
            end_time = datetime.now()
            load_time = (end_time - start_time).total_seconds()

            # Get page information
            final_url = page.url
            title = await page.title()
            status_code = response.status if response else None

            # Update navigation state
            self.current_url = final_url
            self.navigation_history.append(final_url)

            # Check for redirects
            redirected = final_url != url
            if redirected:
                logger.info(f"Navigation redirected: {url} -> {final_url}")

            result = NavigationResult(
                success=True,
                url=final_url,
                title=title,
                status_code=status_code,
                load_time=load_time,
                metadata={
                    "redirected": redirected,
                    "original_url": url,
                    "wait_until": wait_until,
                    "timestamp": start_time.isoformat()
                }
            )

            logger.info(
                f"Navigation successful: {title} ({status_code}) in {load_time:.2f}s"
            )
            return result

        except asyncio.TimeoutError as e:
            load_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Navigation timeout after {load_time:.2f}s"
            logger.error(f"{error_msg}: {url}")
            raise NavigationTimeoutError(error_msg) from e

        except Exception as e:
            load_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(f"{error_msg}: {url}")

            # Return failure result instead of raising for certain errors
            return NavigationResult(
                success=False,
                url=url,
                load_time=load_time,
                error=error_msg,
                metadata={
                    "error_type": type(e).__name__,
                    "timestamp": start_time.isoformat()
                }
            )

    async def go_back(
        self,
        page: Any,
        wait_until: WaitUntilState = "load",
        timeout: Optional[int] = None
    ) -> NavigationResult:
        """
        Navigate back in browser history.

        Args:
            page: Playwright page object
            wait_until: When to consider navigation succeeded
            timeout: Timeout in milliseconds

        Returns:
            NavigationResult

        Raises:
            NavigationError: If navigation fails
        """
        start_time = datetime.now()
        timeout_ms = timeout or self.default_timeout

        logger.info("Navigating back in history")

        try:
            await page.go_back(wait_until=wait_until, timeout=timeout_ms)

            load_time = (datetime.now() - start_time).total_seconds()
            final_url = page.url
            title = await page.title()

            self.current_url = final_url

            result = NavigationResult(
                success=True,
                url=final_url,
                title=title,
                load_time=load_time,
                metadata={
                    "action": "go_back",
                    "timestamp": start_time.isoformat()
                }
            )

            logger.info(f"Navigate back successful: {title} in {load_time:.2f}s")
            return result

        except Exception as e:
            load_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Navigate back failed: {str(e)}"
            logger.error(error_msg)

            return NavigationResult(
                success=False,
                load_time=load_time,
                error=error_msg,
                metadata={
                    "action": "go_back",
                    "error_type": type(e).__name__
                }
            )

    async def go_forward(
        self,
        page: Any,
        wait_until: WaitUntilState = "load",
        timeout: Optional[int] = None
    ) -> NavigationResult:
        """
        Navigate forward in browser history.

        Args:
            page: Playwright page object
            wait_until: When to consider navigation succeeded
            timeout: Timeout in milliseconds

        Returns:
            NavigationResult

        Raises:
            NavigationError: If navigation fails
        """
        start_time = datetime.now()
        timeout_ms = timeout or self.default_timeout

        logger.info("Navigating forward in history")

        try:
            await page.go_forward(wait_until=wait_until, timeout=timeout_ms)

            load_time = (datetime.now() - start_time).total_seconds()
            final_url = page.url
            title = await page.title()

            self.current_url = final_url

            result = NavigationResult(
                success=True,
                url=final_url,
                title=title,
                load_time=load_time,
                metadata={
                    "action": "go_forward",
                    "timestamp": start_time.isoformat()
                }
            )

            logger.info(f"Navigate forward successful: {title} in {load_time:.2f}s")
            return result

        except Exception as e:
            load_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Navigate forward failed: {str(e)}"
            logger.error(error_msg)

            return NavigationResult(
                success=False,
                load_time=load_time,
                error=error_msg,
                metadata={
                    "action": "go_forward",
                    "error_type": type(e).__name__
                }
            )

    async def reload(
        self,
        page: Any,
        wait_until: WaitUntilState = "load",
        timeout: Optional[int] = None
    ) -> NavigationResult:
        """
        Reload the current page.

        Args:
            page: Playwright page object
            wait_until: When to consider navigation succeeded
            timeout: Timeout in milliseconds

        Returns:
            NavigationResult

        Raises:
            NavigationError: If reload fails
        """
        start_time = datetime.now()
        timeout_ms = timeout or self.default_timeout

        logger.info("Reloading page")

        try:
            response = await page.reload(wait_until=wait_until, timeout=timeout_ms)

            load_time = (datetime.now() - start_time).total_seconds()
            final_url = page.url
            title = await page.title()
            status_code = response.status if response else None

            result = NavigationResult(
                success=True,
                url=final_url,
                title=title,
                status_code=status_code,
                load_time=load_time,
                metadata={
                    "action": "reload",
                    "timestamp": start_time.isoformat()
                }
            )

            logger.info(f"Reload successful: {title} in {load_time:.2f}s")
            return result

        except Exception as e:
            load_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Reload failed: {str(e)}"
            logger.error(error_msg)

            return NavigationResult(
                success=False,
                load_time=load_time,
                error=error_msg,
                metadata={
                    "action": "reload",
                    "error_type": type(e).__name__
                }
            )

    async def wait_for_selector(
        self,
        page: Any,
        selector: str,
        state: Literal["attached", "detached", "visible", "hidden"] = "visible",
        timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for a selector to reach a specific state.

        Args:
            page: Playwright page object
            selector: CSS selector
            state: State to wait for (attached, detached, visible, hidden)
            timeout: Timeout in milliseconds

        Returns:
            True if selector reached the state, False if timeout

        Raises:
            NavigationError: If waiting fails
        """
        timeout_ms = timeout or self.default_timeout

        # Validate selector
        validation = self.validator.validate_selector(selector)
        if not validation.valid:
            error_msg = f"Selector validation failed: {validation.reason}"
            logger.error(error_msg)
            raise NavigationError(error_msg)

        logger.info(f"Waiting for selector '{selector}' to be {state} (timeout={timeout_ms}ms)")

        try:
            await page.wait_for_selector(selector, state=state, timeout=timeout_ms)
            logger.info(f"Selector '{selector}' reached state: {state}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for selector '{selector}' to be {state}")
            return False

        except Exception as e:
            error_msg = f"Error waiting for selector: {str(e)}"
            logger.error(error_msg)
            raise NavigationError(error_msg) from e

    async def wait_for_url(
        self,
        page: Any,
        url_pattern: str,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for the page URL to match a pattern.

        Args:
            page: Playwright page object
            url_pattern: URL pattern to match (can be string or regex)
            timeout: Timeout in milliseconds

        Returns:
            True if URL matched, False if timeout

        Raises:
            NavigationError: If waiting fails
        """
        timeout_ms = timeout or self.default_timeout

        logger.info(f"Waiting for URL to match '{url_pattern}' (timeout={timeout_ms}ms)")

        try:
            await page.wait_for_url(url_pattern, timeout=timeout_ms)
            logger.info(f"URL matched pattern: {url_pattern}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for URL pattern '{url_pattern}'")
            return False

        except Exception as e:
            error_msg = f"Error waiting for URL: {str(e)}"
            logger.error(error_msg)
            raise NavigationError(error_msg) from e

    async def wait_for_navigation(
        self,
        page: Any,
        url_pattern: Optional[str] = None,
        wait_until: WaitUntilState = "load",
        timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for a navigation event to complete.

        Useful when triggering navigation through clicks or form submissions.

        Args:
            page: Playwright page object
            url_pattern: Optional URL pattern to wait for
            wait_until: When to consider navigation succeeded
            timeout: Timeout in milliseconds

        Returns:
            True if navigation completed, False if timeout

        Raises:
            NavigationError: If waiting fails
        """
        timeout_ms = timeout or self.default_timeout

        logger.info(f"Waiting for navigation (timeout={timeout_ms}ms)")

        try:
            async with page.expect_navigation(
                url=url_pattern,
                wait_until=wait_until,
                timeout=timeout_ms
            ):
                # Navigation is triggered by caller
                pass

            logger.info("Navigation completed")
            return True

        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for navigation")
            return False

        except Exception as e:
            error_msg = f"Error waiting for navigation: {str(e)}"
            logger.error(error_msg)
            raise NavigationError(error_msg) from e

    async def get_page_info(self, page: Any) -> Dict[str, Any]:
        """
        Get comprehensive information about the current page.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with page information including:
            - url: Current page URL
            - title: Page title
            - is_loaded: Whether page is fully loaded
            - viewport: Viewport size
            - user_agent: User agent string
        """
        try:
            url = page.url
            title = await page.title()

            # Get viewport size
            viewport = page.viewport_size

            # Get user agent
            user_agent = await page.evaluate("() => navigator.userAgent")

            # Check if page is loaded
            is_loaded = await self.is_page_loaded(page)

            info = {
                "url": url,
                "title": title,
                "is_loaded": is_loaded,
                "viewport": viewport,
                "user_agent": user_agent,
                "current_navigation_url": self.current_url,
                "navigation_history_count": len(self.navigation_history)
            }

            logger.debug(f"Page info retrieved: {url}")
            return info

        except Exception as e:
            logger.error(f"Error getting page info: {str(e)}")
            return {
                "url": None,
                "title": None,
                "is_loaded": False,
                "error": str(e)
            }

    async def is_page_loaded(self, page: Any) -> bool:
        """
        Check if the page is fully loaded.

        Args:
            page: Playwright page object

        Returns:
            True if page is loaded, False otherwise
        """
        try:
            # Check document.readyState
            ready_state = await page.evaluate("() => document.readyState")
            is_loaded = ready_state in ["complete", "interactive"]

            logger.debug(f"Page loaded state: {ready_state} -> {is_loaded}")
            return is_loaded

        except Exception as e:
            logger.error(f"Error checking page loaded state: {str(e)}")
            return False
