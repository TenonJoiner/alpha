"""
Alpha - Browser Automation Module

Provides browser automation capabilities using Playwright.

Components:
- SessionManager: Browser session lifecycle management
- PageNavigator: High-level navigation operations
- ActionExecutor: Browser action execution engine
- PageValidator: Security validation for URLs and actions
- ScreenshotManager: Screenshot capture and storage

Phase: 4.3 - Browser Automation
Requirements: REQ-4.5, REQ-4.6, REQ-4.7, REQ-4.8
"""

from alpha.browser_automation.session import (
    SessionConfig,
    BrowserSession,
    SessionManager
)
from alpha.browser_automation.validator import (
    ValidationResult,
    PageValidator
)
from alpha.browser_automation.screenshot import (
    ScreenshotManager
)

# These will be available after agents complete their work
try:
    from alpha.browser_automation.navigator import (
        NavigationResult,
        PageNavigator
    )
    from alpha.browser_automation.executor import (
        ActionResult,
        ActionExecutor
    )
    _navigator_available = True
except ImportError:
    _navigator_available = False
    NavigationResult = None
    PageNavigator = None
    ActionResult = None
    ActionExecutor = None

__all__ = [
    # Session management
    "SessionConfig",
    "BrowserSession",
    "SessionManager",
    # Validation
    "ValidationResult",
    "PageValidator",
    # Screenshots
    "ScreenshotManager",
    # Navigation (when available)
    "NavigationResult",
    "PageNavigator",
    # Actions (when available)
    "ActionResult",
    "ActionExecutor",
]
