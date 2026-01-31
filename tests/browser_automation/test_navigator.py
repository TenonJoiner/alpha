"""
Comprehensive Tests for PageNavigator

Tests navigation operations, waiting strategies, page information retrieval,
and error handling.

Total tests: 18
- 10 navigation tests
- 5 waiting tests
- 3 page info tests
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime

from alpha.browser_automation.navigator import (
    PageNavigator,
    NavigationResult,
    NavigationError,
    NavigationTimeoutError,
    InvalidURLError
)
from alpha.browser_automation.validator import PageValidator, ValidationResult


class TestPageNavigator:
    """Test suite for PageNavigator"""

    @pytest.fixture
    def mock_validator(self):
        """Mock PageValidator"""
        validator = Mock(spec=PageValidator)
        validator.validate_url.return_value = ValidationResult(
            valid=True,
            reason="URL validation passed"
        )
        validator.validate_selector.return_value = ValidationResult(
            valid=True,
            reason="Selector validation passed"
        )
        return validator

    @pytest.fixture
    def mock_page(self):
        """Mock Playwright page object"""
        page = Mock()
        page.url = "https://example.com"
        page.title = AsyncMock(return_value="Example Domain")
        page.viewport_size = {"width": 1280, "height": 720}

        # Mock navigation methods
        mock_response = Mock()
        mock_response.status = 200
        page.goto = AsyncMock(return_value=mock_response)
        page.go_back = AsyncMock()
        page.go_forward = AsyncMock()
        page.reload = AsyncMock(return_value=mock_response)

        # Mock waiting methods
        page.wait_for_selector = AsyncMock()
        page.wait_for_url = AsyncMock()
        page.expect_navigation = AsyncMock()

        # Mock evaluation
        page.evaluate = AsyncMock(return_value="Mozilla/5.0")

        return page

    @pytest.fixture
    def navigator(self, mock_validator):
        """Create PageNavigator with mocked validator"""
        config = {
            "navigation": {
                "timeout": 30000,
                "wait_until": "load"
            }
        }
        return PageNavigator(mock_validator, config)

    # ========== Navigation Tests (10 tests) ==========

    @pytest.mark.asyncio
    async def test_navigate_valid_url(self, navigator, mock_page, mock_validator):
        """Test successful navigation to valid URL"""
        result = await navigator.navigate(
            mock_page,
            "https://example.com",
            wait_until="load"
        )

        assert result.success is True
        assert result.url == "https://example.com"
        assert result.title == "Example Domain"
        assert result.status_code == 200
        assert result.load_time > 0
        assert result.error is None

        # Verify URL was validated
        mock_validator.validate_url.assert_called_once_with("https://example.com")

        # Verify navigation was called with correct parameters
        mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until="load",
            timeout=30000
        )

        # Verify navigation history updated
        assert navigator.current_url == "https://example.com"
        assert "https://example.com" in navigator.navigation_history

    @pytest.mark.asyncio
    async def test_navigate_different_wait_until_states(
        self, navigator, mock_page, mock_validator
    ):
        """Test navigation with different wait_until states"""
        wait_states = ["load", "domcontentloaded", "networkidle", "commit"]

        for state in wait_states:
            result = await navigator.navigate(
                mock_page,
                f"https://example.com/{state}",
                wait_until=state
            )

            assert result.success is True
            assert result.metadata["wait_until"] == state

    @pytest.mark.asyncio
    async def test_navigate_timeout(self, navigator, mock_page, mock_validator):
        """Test navigation timeout handling"""
        # Configure page.goto to raise TimeoutError
        mock_page.goto = AsyncMock(side_effect=asyncio.TimeoutError("Navigation timeout"))

        with pytest.raises(NavigationTimeoutError) as exc_info:
            await navigator.navigate(
                mock_page,
                "https://slow-site.com",
                timeout=5000
            )

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_navigate_invalid_url(self, navigator, mock_page, mock_validator):
        """Test navigation with invalid URL"""
        # Configure validator to reject URL
        mock_validator.validate_url.return_value = ValidationResult(
            valid=False,
            reason="Invalid URL format",
            severity="error"
        )

        with pytest.raises(InvalidURLError) as exc_info:
            await navigator.navigate(
                mock_page,
                "not-a-valid-url"
            )

        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_navigate_blacklisted_url(self, navigator, mock_page, mock_validator):
        """Test navigation with blacklisted URL"""
        # Configure validator to reject blacklisted URL
        mock_validator.validate_url.return_value = ValidationResult(
            valid=False,
            reason="URL matches blacklist pattern",
            severity="error"
        )

        with pytest.raises(InvalidURLError):
            await navigator.navigate(
                mock_page,
                "https://blocked-site.onion"
            )

    @pytest.mark.asyncio
    async def test_navigate_ssl_error(self, navigator, mock_page, mock_validator):
        """Test navigation with SSL error"""
        # Configure page.goto to raise SSL error
        mock_page.goto = AsyncMock(
            side_effect=Exception("SSL certificate verification failed")
        )

        result = await navigator.navigate(
            mock_page,
            "https://bad-ssl.com"
        )

        assert result.success is False
        assert result.error is not None
        assert "SSL" in result.error or "certificate" in result.error.lower()

    @pytest.mark.asyncio
    async def test_navigate_with_redirect(self, navigator, mock_page, mock_validator):
        """Test navigation that redirects to different URL"""
        # Simulate redirect by changing page.url after goto
        async def goto_with_redirect(*args, **kwargs):
            mock_page.url = "https://example.com/redirected"
            mock_response = Mock()
            mock_response.status = 200
            return mock_response

        mock_page.goto = AsyncMock(side_effect=goto_with_redirect)

        result = await navigator.navigate(
            mock_page,
            "https://example.com/original"
        )

        assert result.success is True
        assert result.url == "https://example.com/redirected"
        assert result.metadata["redirected"] is True
        assert result.metadata["original_url"] == "https://example.com/original"

    @pytest.mark.asyncio
    async def test_go_back(self, navigator, mock_page):
        """Test go_back navigation"""
        result = await navigator.go_back(mock_page, wait_until="load")

        assert result.success is True
        assert result.url == mock_page.url
        assert result.title == "Example Domain"
        assert result.metadata["action"] == "go_back"

        mock_page.go_back.assert_called_once_with(
            wait_until="load",
            timeout=30000
        )

    @pytest.mark.asyncio
    async def test_go_forward(self, navigator, mock_page):
        """Test go_forward navigation"""
        result = await navigator.go_forward(mock_page, wait_until="domcontentloaded")

        assert result.success is True
        assert result.url == mock_page.url
        assert result.title == "Example Domain"
        assert result.metadata["action"] == "go_forward"

        mock_page.go_forward.assert_called_once_with(
            wait_until="domcontentloaded",
            timeout=30000
        )

    @pytest.mark.asyncio
    async def test_reload(self, navigator, mock_page):
        """Test page reload"""
        result = await navigator.reload(mock_page, wait_until="networkidle")

        assert result.success is True
        assert result.url == mock_page.url
        assert result.title == "Example Domain"
        assert result.status_code == 200
        assert result.metadata["action"] == "reload"

        mock_page.reload.assert_called_once_with(
            wait_until="networkidle",
            timeout=30000
        )

    # ========== Waiting Tests (5 tests) ==========

    @pytest.mark.asyncio
    async def test_wait_for_selector_visible(self, navigator, mock_page, mock_validator):
        """Test waiting for selector to become visible"""
        result = await navigator.wait_for_selector(
            mock_page,
            "#submit-button",
            state="visible",
            timeout=5000
        )

        assert result is True

        # Verify selector was validated
        mock_validator.validate_selector.assert_called_once_with("#submit-button")

        # Verify wait was called with correct parameters
        mock_page.wait_for_selector.assert_called_once_with(
            "#submit-button",
            state="visible",
            timeout=5000
        )

    @pytest.mark.asyncio
    async def test_wait_for_selector_hidden(self, navigator, mock_page, mock_validator):
        """Test waiting for selector to become hidden"""
        result = await navigator.wait_for_selector(
            mock_page,
            ".loading-spinner",
            state="hidden"
        )

        assert result is True

        mock_page.wait_for_selector.assert_called_once_with(
            ".loading-spinner",
            state="hidden",
            timeout=30000
        )

    @pytest.mark.asyncio
    async def test_wait_for_selector_attached(self, navigator, mock_page, mock_validator):
        """Test waiting for selector to be attached to DOM"""
        result = await navigator.wait_for_selector(
            mock_page,
            "div.content",
            state="attached"
        )

        assert result is True

        mock_page.wait_for_selector.assert_called_once_with(
            "div.content",
            state="attached",
            timeout=30000
        )

    @pytest.mark.asyncio
    async def test_wait_for_selector_timeout(self, navigator, mock_page, mock_validator):
        """Test waiting for selector that times out"""
        # Configure wait_for_selector to timeout
        mock_page.wait_for_selector = AsyncMock(
            side_effect=asyncio.TimeoutError("Selector not found")
        )

        result = await navigator.wait_for_selector(
            mock_page,
            "#non-existent",
            timeout=1000
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_url(self, navigator, mock_page):
        """Test waiting for URL pattern"""
        result = await navigator.wait_for_url(
            mock_page,
            "**/dashboard",
            timeout=10000
        )

        assert result is True

        mock_page.wait_for_url.assert_called_once_with(
            "**/dashboard",
            timeout=10000
        )

    # Note: wait_for_navigation is tested through context manager usage
    # Additional tests would require more complex mocking

    # ========== Page Info Tests (3 tests) ==========

    @pytest.mark.asyncio
    async def test_get_page_info(self, navigator, mock_page):
        """Test getting comprehensive page information"""
        # Configure mock page state
        mock_page.url = "https://example.com/page"
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.viewport_size = {"width": 1920, "height": 1080}
        mock_page.evaluate = AsyncMock(side_effect=[
            "Mozilla/5.0 Chrome/91.0",  # User agent
            "complete"  # Document ready state
        ])

        info = await navigator.get_page_info(mock_page)

        assert info["url"] == "https://example.com/page"
        assert info["title"] == "Test Page"
        assert info["viewport"] == {"width": 1920, "height": 1080}
        assert info["user_agent"] == "Mozilla/5.0 Chrome/91.0"
        assert "is_loaded" in info
        assert "navigation_history_count" in info

    @pytest.mark.asyncio
    async def test_is_page_loaded_complete(self, navigator, mock_page):
        """Test checking if page is loaded (complete state)"""
        mock_page.evaluate = AsyncMock(return_value="complete")

        is_loaded = await navigator.is_page_loaded(mock_page)

        assert is_loaded is True

        # Verify document.readyState was checked
        mock_page.evaluate.assert_called_once_with("() => document.readyState")

    @pytest.mark.asyncio
    async def test_is_page_loaded_interactive(self, navigator, mock_page):
        """Test checking if page is loaded (interactive state)"""
        mock_page.evaluate = AsyncMock(return_value="interactive")

        is_loaded = await navigator.is_page_loaded(mock_page)

        assert is_loaded is True

    # ========== Additional Edge Case Tests ==========

    @pytest.mark.asyncio
    async def test_navigate_custom_timeout(self, navigator, mock_page, mock_validator):
        """Test navigation with custom timeout"""
        result = await navigator.navigate(
            mock_page,
            "https://example.com",
            timeout=60000
        )

        assert result.success is True

        # Verify custom timeout was used
        mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until="load",
            timeout=60000
        )

    @pytest.mark.asyncio
    async def test_navigation_state_tracking(self, navigator, mock_page, mock_validator):
        """Test that navigation state is properly tracked"""
        # Perform multiple navigations with URL updates
        mock_page.url = "https://example.com/page1"
        await navigator.navigate(mock_page, "https://example.com/page1")

        mock_page.url = "https://example.com/page2"
        await navigator.navigate(mock_page, "https://example.com/page2")

        mock_page.url = "https://example.com/page3"
        await navigator.navigate(mock_page, "https://example.com/page3")

        # Verify state tracking
        assert navigator.current_url == "https://example.com/page3"
        assert len(navigator.navigation_history) == 3
        assert navigator.navigation_history[0] == "https://example.com/page1"
        assert navigator.navigation_history[1] == "https://example.com/page2"
        assert navigator.navigation_history[2] == "https://example.com/page3"

    @pytest.mark.asyncio
    async def test_wait_for_selector_invalid_selector(
        self, navigator, mock_page, mock_validator
    ):
        """Test waiting for invalid selector raises error"""
        # Configure validator to reject selector
        mock_validator.validate_selector.return_value = ValidationResult(
            valid=False,
            reason="Empty selector",
            severity="error"
        )

        with pytest.raises(NavigationError) as exc_info:
            await navigator.wait_for_selector(mock_page, "")

        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reload_with_error(self, navigator, mock_page):
        """Test reload that fails with error"""
        # Configure reload to fail
        mock_page.reload = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await navigator.reload(mock_page)

        assert result.success is False
        assert result.error is not None
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_get_page_info_with_error(self, navigator, mock_page):
        """Test getting page info when page has errors"""
        # Configure page methods to fail
        mock_page.title = AsyncMock(side_effect=Exception("Page closed"))

        info = await navigator.get_page_info(mock_page)

        assert info["url"] is None
        assert info["title"] is None
        assert info["is_loaded"] is False
        assert "error" in info


class TestNavigationResult:
    """Test NavigationResult dataclass"""

    def test_navigation_result_success(self):
        """Test creating successful NavigationResult"""
        result = NavigationResult(
            success=True,
            url="https://example.com",
            title="Example",
            status_code=200,
            load_time=1.5
        )

        assert result.success is True
        assert result.url == "https://example.com"
        assert result.title == "Example"
        assert result.status_code == 200
        assert result.load_time == 1.5
        assert result.error is None
        assert result.metadata == {}

    def test_navigation_result_failure(self):
        """Test creating failed NavigationResult"""
        result = NavigationResult(
            success=False,
            error="Network timeout",
            load_time=30.0,
            metadata={"error_type": "TimeoutError"}
        )

        assert result.success is False
        assert result.error == "Network timeout"
        assert result.load_time == 30.0
        assert result.metadata["error_type"] == "TimeoutError"

    def test_navigation_result_with_metadata(self):
        """Test NavigationResult with custom metadata"""
        result = NavigationResult(
            success=True,
            url="https://example.com",
            metadata={
                "redirected": True,
                "original_url": "https://example.org",
                "timestamp": "2024-01-01T00:00:00"
            }
        )

        assert result.metadata["redirected"] is True
        assert result.metadata["original_url"] == "https://example.org"
        assert "timestamp" in result.metadata
