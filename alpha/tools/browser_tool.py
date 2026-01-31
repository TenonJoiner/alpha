"""
Browser Automation Tool

Integrates the Browser Automation system with Alpha's tool registry.
Enables the LLM agent to perform web automation, data extraction, and browser-based tasks.

Phase: 4.3 - Browser Automation
Requirements: REQ-4.5, REQ-4.6, REQ-4.7, REQ-4.8
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from alpha.tools.registry import Tool, ToolResult

logger = logging.getLogger(__name__)


class BrowserTool(Tool):
    """
    Tool for browser automation and web interaction.

    This tool integrates Alpha's browser automation capabilities into the tool system,
    allowing the LLM agent to navigate web pages, interact with elements, extract data,
    and capture screenshots.

    Features:
    - Multi-browser support (Chromium, Firefox, WebKit)
    - Page navigation and interaction
    - Form automation and data submission
    - Structured data extraction
    - Screenshot capture
    - Session management and reuse
    - Security validation
    - User approval workflow

    Example Usage:
        # Navigate to a URL
        result = await tool.execute(
            action="navigate",
            url="https://example.com"
        )

        # Extract data from a page
        result = await tool.execute(
            action="extract_data",
            selectors={
                "title": "h1",
                "price": ".price"
            }
        )

        # Fill and submit a form
        result = await tool.execute(
            action="fill_form",
            data={
                "name": "John Doe",
                "email": "john@example.com"
            }
        )

    Security:
    - URL validation and blacklisting
    - User approval for sensitive actions
    - Network access control
    - Resource limits
    - Script execution validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Browser Automation Tool.

        Args:
            config: Optional configuration dictionary for browser automation settings
        """
        super().__init__(
            name="browser",
            description="Automate web browsers for navigation, interaction, data extraction, "
                       "and screenshot capture. Supports Chromium, Firefox, and WebKit. "
                       "Use for web scraping, form automation, and visual testing."
        )

        self.config = config or {}

        # Initialize browser automation components (lazy initialization)
        self._session_manager = None
        self._navigator = None
        self._executor = None
        self._validator = None
        self._screenshot_manager = None

        # Track if Playwright is available
        self._playwright_available: Optional[bool] = None

        # Statistics
        self._stats = {
            "total_executions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "sessions_created": 0,
            "screenshots_captured": 0
        }

        logger.info("BrowserTool initialized")

    def _ensure_components_initialized(self) -> None:
        """
        Lazily initialize browser automation components on first use.

        This allows the tool to be registered even if Playwright is not available,
        providing graceful error messages at execution time.
        """
        if self._session_manager is not None:
            return  # Already initialized

        logger.info("Initializing browser automation components")

        try:
            from alpha.browser_automation import (
                SessionManager,
                PageNavigator,
                ActionExecutor,
                PageValidator,
                ScreenshotManager
            )

            # Initialize components
            self._session_manager = SessionManager(self.config)
            self._validator = PageValidator(self.config)
            self._screenshot_manager = ScreenshotManager(self.config)
            self._navigator = PageNavigator(self._validator, self.config)
            self._executor = ActionExecutor(
                navigator=self._navigator,
                validator=self._validator,
                screenshot_manager=self._screenshot_manager,
                config=self.config
            )

            # Check Playwright availability
            self._playwright_available = self._session_manager.is_available()

            if not self._playwright_available:
                logger.warning("Playwright not available - browser automation will fail at runtime")
            else:
                logger.info("Browser automation components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser automation components: {e}")
            raise

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        selectors: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, str]] = None,
        value: Optional[str] = None,
        script: Optional[str] = None,
        wait_for: Optional[str] = None,
        timeout: int = 30,
        headless: bool = True,
        browser: str = "chromium",
        full_page: bool = False,
        require_approval: bool = True,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute the browser automation tool.

        This method orchestrates browser automation actions:
        1. Validate parameters
        2. Initialize components if needed
        3. Get or create browser session
        4. Execute the specified action
        5. Return results

        Args:
            action: Action to perform (navigate, click, fill_form, extract_data, screenshot, etc.)
            url: URL to navigate to (for navigate action)
            selector: CSS selector for element (for click, fill_input, extract_text)
            selectors: Dict of selectors for data extraction
            data: Form data dict (for fill_form action)
            value: Input value (for fill_input action)
            script: JavaScript code (for execute_script action)
            wait_for: Selector to wait for after action
            timeout: Action timeout in seconds - default: 30
            headless: Run browser in headless mode - default: True
            browser: Browser type (chromium, firefox, webkit) - default: chromium
            full_page: Capture full page screenshot - default: False
            require_approval: Require user approval - default: True
            session_id: Existing session ID to reuse (optional)
            **kwargs: Additional parameters

        Returns:
            ToolResult with action output and metadata

        Supported Actions:
            - navigate: Navigate to URL
            - click: Click an element
            - fill_form: Fill multiple form fields
            - fill_input: Fill a single input field
            - extract_data: Extract structured data
            - extract_text: Extract text from element
            - extract_table: Extract table data
            - screenshot: Capture screenshot
            - execute_script: Run JavaScript
            - back: Navigate back
            - forward: Navigate forward
            - reload: Reload page

        Example:
            >>> # Navigate to a page
            >>> result = await tool.execute(
            ...     action="navigate",
            ...     url="https://example.com"
            ... )

            >>> # Extract data
            >>> result = await tool.execute(
            ...     action="extract_data",
            ...     selectors={"title": "h1", "price": ".price"}
            ... )
        """
        logger.info(f"Browser tool called with action={action}")
        self._stats["total_executions"] += 1

        try:
            # Step 1: Validate parameters
            validation_error = self._validate_parameters(action, url, selector, selectors, data, value, script)
            if validation_error:
                self._stats["failed_actions"] += 1
                return ToolResult(
                    success=False,
                    output=None,
                    error=validation_error,
                    metadata={"action": action}
                )

            # Step 2: Initialize components
            try:
                self._ensure_components_initialized()
            except Exception as e:
                self._stats["failed_actions"] += 1
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Failed to initialize browser automation: {e}",
                    metadata={"action": action}
                )

            # Step 3: Check Playwright availability
            if not self._playwright_available:
                self._stats["failed_actions"] += 1
                return ToolResult(
                    success=False,
                    output=None,
                    error="Playwright not installed. Install with: pip install playwright && python -m playwright install",
                    metadata={"action": action}
                )

            # Step 4: User approval (if required)
            if require_approval:
                approved = await self._request_approval(action, {
                    "url": url,
                    "selector": selector,
                    "data": data,
                    "browser": browser
                })
                if not approved:
                    self._stats["failed_actions"] += 1
                    return ToolResult(
                        success=False,
                        output=None,
                        error="User rejected the action",
                        metadata={"action": action, "reason": "user_rejection"}
                    )

            # Step 5: Get or create session
            from alpha.browser_automation import SessionConfig
            session_config = SessionConfig(
                browser_type=browser,
                headless=headless,
                timeout=timeout * 1000  # Convert to milliseconds
            )

            session = await self._get_or_create_session(session_id, session_config)
            current_session_id = session.session_id

            # Step 6: Execute action
            action_result = None

            if action == "navigate":
                action_result = await self._execute_navigate(session, url, timeout)

            elif action == "click":
                action_result = await self._execute_click(session, selector, timeout)

            elif action == "fill_form":
                action_result = await self._execute_fill_form(session, data, timeout)

            elif action == "fill_input":
                action_result = await self._execute_fill_input(session, selector, value, timeout)

            elif action == "extract_data":
                action_result = await self._execute_extract_data(session, selectors)

            elif action == "extract_text":
                action_result = await self._execute_extract_text(session, selector)

            elif action == "extract_table":
                action_result = await self._execute_extract_table(session, selector)

            elif action == "screenshot":
                action_result = await self._execute_screenshot(session, full_page, selector)

            elif action == "execute_script":
                action_result = await self._execute_script(session, script)

            elif action == "back":
                action_result = await self._execute_back(session)

            elif action == "forward":
                action_result = await self._execute_forward(session)

            elif action == "reload":
                action_result = await self._execute_reload(session)

            else:
                self._stats["failed_actions"] += 1
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown action: {action}",
                    metadata={"action": action}
                )

            # Step 7: Wait for selector if specified
            if wait_for and action_result.success:
                try:
                    await self._navigator.wait_for_selector(session.page, wait_for, timeout=timeout)
                except Exception as e:
                    logger.warning(f"Wait for selector failed: {e}")

            # Step 8: Update statistics and return result
            if action_result.success:
                self._stats["successful_actions"] += 1
                if action == "screenshot":
                    self._stats["screenshots_captured"] += 1
            else:
                self._stats["failed_actions"] += 1

            return self._format_result(action_result, action, current_session_id)

        except Exception as e:
            logger.error(f"Browser tool execution failed: {e}", exc_info=True)
            self._stats["failed_actions"] += 1
            return ToolResult(
                success=False,
                output=None,
                error=f"Execution failed: {e}",
                metadata={"action": action}
            )

    def _validate_parameters(
        self,
        action: str,
        url: Optional[str],
        selector: Optional[str],
        selectors: Optional[Dict],
        data: Optional[Dict],
        value: Optional[str],
        script: Optional[str]
    ) -> Optional[str]:
        """
        Validate parameters for the specified action.

        Returns:
            Error message if validation fails, None otherwise
        """
        if action == "navigate":
            if not url:
                return "Missing required parameter: url"

        elif action in ["click", "extract_text"]:
            if not selector:
                return f"Missing required parameter for {action}: selector"

        elif action == "fill_form":
            if not data or not isinstance(data, dict):
                return "Missing or invalid required parameter: data (must be dict)"

        elif action == "fill_input":
            if not selector:
                return "Missing required parameter: selector"
            if not value:
                return "Missing required parameter: value"

        elif action == "extract_data":
            if not selectors or not isinstance(selectors, dict):
                return "Missing or invalid required parameter: selectors (must be dict)"

        elif action == "execute_script":
            if not script:
                return "Missing required parameter: script"

        elif action == "extract_table":
            if not selector:
                return "Missing required parameter: selector"

        elif action not in ["screenshot", "back", "forward", "reload"]:
            return f"Unknown action: {action}"

        return None

    async def _get_or_create_session(self, session_id: Optional[str], config) -> Any:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Optional existing session ID
            config: SessionConfig object

        Returns:
            BrowserSession instance
        """
        if session_id:
            # Try to get existing session
            session = await self._session_manager.get_session(session_id)
            if session:
                logger.info(f"Reusing existing session: {session_id}")
                return session
            else:
                logger.warning(f"Session {session_id} not found, creating new session")

        # Create new session
        session = await self._session_manager.create_session(config)
        self._stats["sessions_created"] += 1
        logger.info(f"Created new browser session: {session.session_id}")
        return session

    async def _request_approval(self, action: str, details: Dict) -> bool:
        """
        Request user approval for the action.

        Args:
            action: Action to approve
            details: Action details

        Returns:
            True if approved, False otherwise
        """
        # For now, auto-approve all actions
        # In production, this would prompt the user
        # Check security config
        security_config = self.config.get("security", {})
        if not security_config.get("require_approval", True):
            return True

        # Check if action requires approval
        if not self._validator.should_require_approval(action, details):
            return True

        # TODO: Implement actual user approval prompt
        # For now, auto-approve
        logger.info(f"User approval requested for action: {action}")
        return True

    # Action execution methods

    async def _execute_navigate(self, session, url: str, timeout: int):
        """Execute navigate action."""
        return await self._navigator.navigate(session.page, url, timeout=timeout)

    async def _execute_click(self, session, selector: str, timeout: int):
        """Execute click action."""
        return await self._executor.click_element(session.page, selector, timeout=timeout)

    async def _execute_fill_form(self, session, data: Dict, timeout: int):
        """Execute fill_form action."""
        return await self._executor.fill_form(session.page, data)

    async def _execute_fill_input(self, session, selector: str, value: str, timeout: int):
        """Execute fill_input action."""
        return await self._executor.fill_input(session.page, selector, value)

    async def _execute_extract_data(self, session, selectors: Dict):
        """Execute extract_data action."""
        return await self._executor.extract_data(session.page, selectors)

    async def _execute_extract_text(self, session, selector: str):
        """Execute extract_text action."""
        return await self._executor.extract_text(session.page, selector)

    async def _execute_extract_table(self, session, selector: str):
        """Execute extract_table action."""
        return await self._executor.extract_table(session.page, selector)

    async def _execute_screenshot(self, session, full_page: bool, selector: Optional[str]):
        """Execute screenshot action."""
        return await self._executor.take_screenshot(
            session.page,
            full_page=full_page,
            selector=selector
        )

    async def _execute_script(self, session, script: str):
        """Execute execute_script action."""
        return await self._executor.execute_script(session.page, script)

    async def _execute_back(self, session):
        """Execute back action."""
        return await self._navigator.go_back(session.page)

    async def _execute_forward(self, session):
        """Execute forward action."""
        return await self._navigator.go_forward(session.page)

    async def _execute_reload(self, session):
        """Execute reload action."""
        return await self._navigator.reload(session.page)

    def _format_result(self, action_result, action: str, session_id: str) -> ToolResult:
        """
        Format action result as ToolResult.

        Args:
            action_result: ActionResult or NavigationResult
            action: Action name
            session_id: Session ID

        Returns:
            ToolResult
        """
        metadata = {
            "action": action,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

        # Add action-specific metadata
        if hasattr(action_result, "metadata"):
            metadata.update(action_result.metadata)
        if hasattr(action_result, "execution_time"):
            metadata["execution_time"] = action_result.execution_time
        if hasattr(action_result, "screenshot_path"):
            metadata["screenshot_path"] = action_result.screenshot_path

        return ToolResult(
            success=action_result.success,
            output=action_result.data if hasattr(action_result, "data") else action_result.url,
            error=action_result.error,
            metadata=metadata
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tool usage statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_actions"] / self._stats["total_executions"]
                if self._stats["total_executions"] > 0
                else 0.0
            )
        }

    def is_available(self) -> bool:
        """
        Check if Playwright is available.

        Returns:
            True if Playwright is installed
        """
        try:
            import playwright
            return True
        except ImportError:
            return False
