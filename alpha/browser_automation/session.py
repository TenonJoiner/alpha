"""
Alpha - Browser Session Manager

Manages browser lifecycle, context, and page creation/cleanup.
"""

import logging
import asyncio
import uuid
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuration for a browser session."""
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    timeout: int = 30000  # milliseconds
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: Optional[str] = None


@dataclass
class BrowserSession:
    """Represents an active browser session."""
    session_id: str
    browser: Any  # Playwright Browser instance
    context: Any  # Playwright BrowserContext instance
    page: Any  # Playwright Page instance
    created_at: float
    config: SessionConfig
    last_activity: float = field(default_factory=lambda: datetime.now().timestamp())

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now().timestamp()

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if session has expired."""
        return (datetime.now().timestamp() - self.last_activity) > timeout_seconds


class SessionManager:
    """
    Manages browser session lifecycle.

    Features:
    - Create and manage browser sessions
    - Multiple browser support (Chromium, Firefox, WebKit)
    - Session pooling and reuse
    - Automatic cleanup
    - Timeout handling
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize session manager.

        Args:
            config: Browser automation configuration
        """
        self.config = config or {}
        self.sessions: Dict[str, BrowserSession] = {}
        self._playwright = None
        self._browsers = {}  # Cache browser instances
        self._lock = asyncio.Lock()
        logger.info("SessionManager initialized")

    async def _get_playwright(self):
        """Get or initialize Playwright instance."""
        if self._playwright is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                logger.info("Playwright initialized")
            except ImportError:
                raise RuntimeError(
                    "Playwright not installed. Install with: pip install playwright && "
                    "python -m playwright install"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Playwright: {e}")
        return self._playwright

    async def _get_browser(self, browser_type: str, headless: bool = True):
        """
        Get or create a browser instance.

        Args:
            browser_type: Browser type (chromium, firefox, webkit)
            headless: Run in headless mode

        Returns:
            Browser instance
        """
        browser_key = f"{browser_type}_{headless}"

        if browser_key not in self._browsers:
            playwright = await self._get_playwright()

            # Get browser launcher
            if browser_type == "chromium":
                launcher = playwright.chromium
            elif browser_type == "firefox":
                launcher = playwright.firefox
            elif browser_type == "webkit":
                launcher = playwright.webkit
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

            # Launch browser
            try:
                browser = await launcher.launch(headless=headless)
                self._browsers[browser_key] = browser
                logger.info(f"Browser launched: {browser_type} (headless={headless})")
            except Exception as e:
                raise RuntimeError(f"Failed to launch browser {browser_type}: {e}")

        return self._browsers[browser_key]

    async def create_session(
        self,
        config: Optional[SessionConfig] = None
    ) -> BrowserSession:
        """
        Create a new browser session.

        Args:
            config: Session configuration

        Returns:
            BrowserSession instance
        """
        if config is None:
            defaults = self.config.get("defaults", {})
            config = SessionConfig(
                browser_type=defaults.get("browser", "chromium"),
                headless=defaults.get("headless", True),
                viewport=self.config.get("viewport", {"width": 1920, "height": 1080}),
                timeout=defaults.get("timeout", 30) * 1000  # Convert to ms
            )

        async with self._lock:
            # Check session limit
            max_sessions = self.config.get("limits", {}).get("max_sessions", 5)
            if len(self.sessions) >= max_sessions:
                # Clean up expired sessions
                await self._cleanup_expired_sessions()
                if len(self.sessions) >= max_sessions:
                    raise RuntimeError(f"Maximum sessions ({max_sessions}) reached")

            # Get browser
            browser = await self._get_browser(config.browser_type, config.headless)

            # Create context
            context_options = {
                "viewport": config.viewport,
                "user_agent": config.user_agent,
                "locale": config.locale,
                "timezone_id": config.timezone,
            }
            # Remove None values
            context_options = {k: v for k, v in context_options.items() if v is not None}

            try:
                context = await browser.new_context(**context_options)
                context.set_default_timeout(config.timeout)

                # Create page
                page = await context.new_page()

                # Create session
                session_id = str(uuid.uuid4())
                session = BrowserSession(
                    session_id=session_id,
                    browser=browser,
                    context=context,
                    page=page,
                    created_at=datetime.now().timestamp(),
                    config=config
                )

                self.sessions[session_id] = session
                logger.info(f"Session created: {session_id} ({config.browser_type})")

                return session

            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                try:
                    if 'context' in locals():
                        await context.close()
                except:
                    pass
                raise RuntimeError(f"Failed to create browser session: {e}")

    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """
        Get an existing session.

        Args:
            session_id: Session ID

        Returns:
            BrowserSession or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    async def close_session(self, session_id: str):
        """
        Close a browser session.

        Args:
            session_id: Session ID
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return

        try:
            # Close context (automatically closes pages)
            await session.context.close()
            del self.sessions[session_id]
            logger.info(f"Session closed: {session_id}")
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")
            # Remove from sessions even if close failed
            self.sessions.pop(session_id, None)

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        timeout = self.config.get("limits", {}).get("session_timeout", 300)
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(timeout)
        ]

        for session_id in expired:
            logger.info(f"Cleaning up expired session: {session_id}")
            await self.close_session(session_id)

    async def cleanup_all_sessions(self):
        """Close all browser sessions."""
        logger.info(f"Closing all sessions ({len(self.sessions)})")

        # Close all sessions
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)

        # Close browsers
        for browser_key, browser in self._browsers.items():
            try:
                await browser.close()
                logger.info(f"Browser closed: {browser_key}")
            except Exception as e:
                logger.error(f"Error closing browser {browser_key}: {e}")

        self._browsers.clear()

        # Stop playwright
        if self._playwright:
            try:
                await self._playwright.stop()
                self._playwright = None
                logger.info("Playwright stopped")
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")

    async def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about active sessions.

        Returns:
            Dictionary of session information
        """
        return {
            sid: {
                "browser_type": session.config.browser_type,
                "headless": session.config.headless,
                "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
                "age_seconds": datetime.now().timestamp() - session.created_at
            }
            for sid, session in self.sessions.items()
        }

    def is_available(self) -> bool:
        """Check if Playwright is available."""
        try:
            import playwright
            return True
        except ImportError:
            return False
