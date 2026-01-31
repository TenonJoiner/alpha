"""
Alpha - Action Executor

Executes browser actions with validation, error handling, and screenshot capture.
"""

import logging
import asyncio
import time
from typing import Dict, Optional, Any, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """
    Result of a browser action execution.

    Attributes:
        success: Whether the action succeeded
        action: Action name that was executed
        data: Action result data
        error: Error message if action failed
        screenshot_path: Path to screenshot if captured
        execution_time: Time taken to execute action in seconds
        metadata: Additional metadata about the action
    """
    success: bool
    action: str
    data: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure metadata is a dictionary."""
        if self.metadata is None:
            self.metadata = {}


class ActionExecutor:
    """
    Executes browser actions with comprehensive error handling.

    Features:
    - Element interaction (click, fill, select, upload)
    - Data extraction (text, structured data, tables)
    - Advanced actions (script execution, hover, drag-and-drop)
    - Pre-action validation
    - Automatic error screenshot capture
    - Execution time tracking
    - Comprehensive error context

    Example:
        >>> executor = ActionExecutor(navigator, validator, screenshot_manager)
        >>> result = await executor.click_element("button.submit")
        >>> if result.success:
        ...     print("Button clicked successfully")
    """

    def __init__(
        self,
        page_navigator,
        page_validator,
        screenshot_manager,
        config: Optional[Dict] = None
    ):
        """
        Initialize action executor.

        Args:
            page_navigator: PageNavigator instance for page access
            page_validator: PageValidator instance for validation
            screenshot_manager: ScreenshotManager instance for screenshots
            config: Browser automation configuration
        """
        self.page_navigator = page_navigator
        self.validator = page_validator
        self.screenshot_manager = screenshot_manager
        self.config = config or {}

        # Action settings
        self.action_config = self.config.get("actions", {})
        self.default_timeout = self.action_config.get("timeout", 30) * 1000  # Convert to ms
        self.screenshot_on_error = self.action_config.get("screenshot_on_error", True)
        self.validate_before_action = self.action_config.get("validate_before_action", True)

        logger.info("ActionExecutor initialized")

    async def click_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        button: str = "left",
        click_count: int = 1,
        force: bool = False
    ) -> ActionResult:
        """
        Click an element on the page.

        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds (default: config timeout)
            button: Mouse button to click (left, right, middle)
            click_count: Number of clicks (1=single, 2=double, 3=triple)
            force: Force click even if element not ready

        Returns:
            ActionResult with click outcome

        Example:
            >>> # Single click on submit button
            >>> result = await executor.click_element("button.submit")
            >>>
            >>> # Double click with custom timeout
            >>> result = await executor.click_element(
            ...     "div.item",
            ...     click_count=2,
            ...     timeout=5000
            ... )
        """
        start_time = time.time()
        action = "click_element"

        # Validate selector
        if self.validate_before_action:
            validation = self.validator.validate_selector(selector)
            if not validation.valid:
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Selector validation failed: {validation.reason}",
                    execution_time=time.time() - start_time,
                    metadata={"selector": selector}
                )

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"Element not found: {selector}")

            # Click element
            click_options = {
                "button": button,
                "click_count": click_count,
                "force": force,
                "timeout": timeout
            }

            await element.click(**click_options)

            execution_time = time.time() - start_time
            logger.info(f"Clicked element: {selector} (count={click_count}, {execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={"selector": selector, "clicked": True},
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "button": button,
                    "click_count": click_count
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to click element '{selector}': {str(e)}"
            logger.error(error_msg)

            # Capture error screenshot
            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def fill_input(
        self,
        selector: str,
        value: str,
        timeout: Optional[int] = None,
        clear_first: bool = True
    ) -> ActionResult:
        """
        Fill an input field with text.

        Args:
            selector: CSS selector for the input element
            value: Text value to fill
            timeout: Timeout in milliseconds
            clear_first: Clear existing value before filling

        Returns:
            ActionResult with fill outcome

        Example:
            >>> result = await executor.fill_input("input[name='email']", "user@example.com")
        """
        start_time = time.time()
        action = "fill_input"

        # Validate selector
        if self.validate_before_action:
            validation = self.validator.validate_selector(selector)
            if not validation.valid:
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Selector validation failed: {validation.reason}",
                    execution_time=time.time() - start_time,
                    metadata={"selector": selector}
                )

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"Input element not found: {selector}")

            # Clear if requested
            if clear_first:
                await element.clear()

            # Fill input
            await element.fill(value, timeout=timeout)

            execution_time = time.time() - start_time
            logger.info(f"Filled input: {selector} ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={"selector": selector, "value": value, "filled": True},
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "value_length": len(value),
                    "cleared_first": clear_first
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to fill input '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def fill_form(
        self,
        form_data: Dict[str, str],
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Fill multiple form fields at once.

        Args:
            form_data: Dictionary mapping selectors to values
            timeout: Timeout in milliseconds for each field

        Returns:
            ActionResult with form fill outcome

        Example:
            >>> result = await executor.fill_form({
            ...     "input[name='username']": "johndoe",
            ...     "input[name='email']": "john@example.com",
            ...     "textarea[name='bio']": "Software developer"
            ... })
        """
        start_time = time.time()
        action = "fill_form"

        # Validate form data
        if self.validate_before_action:
            validation = self.validator.validate_action(action, {"data": form_data})
            if not validation.valid:
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Form validation failed: {validation.reason}",
                    execution_time=time.time() - start_time,
                    metadata={"field_count": len(form_data)}
                )

        try:
            page = self.page_navigator.page
            filled_fields = []
            failed_fields = []

            # Fill each field
            for selector, value in form_data.items():
                try:
                    element = await self._find_element(page, selector, timeout or self.default_timeout)
                    if element:
                        await element.fill(value)
                        filled_fields.append(selector)
                    else:
                        failed_fields.append({"selector": selector, "reason": "Element not found"})
                except Exception as e:
                    failed_fields.append({"selector": selector, "reason": str(e)})

            execution_time = time.time() - start_time

            # Check if any fields failed
            if failed_fields:
                error_msg = f"Failed to fill {len(failed_fields)} field(s)"
                logger.warning(f"{error_msg}: {failed_fields}")

                screenshot_path = await self._capture_error_screenshot(
                    page, action, {"failed_fields": failed_fields}
                )

                return ActionResult(
                    success=False,
                    action=action,
                    error=error_msg,
                    data={
                        "filled_fields": filled_fields,
                        "failed_fields": failed_fields
                    },
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    metadata={
                        "total_fields": len(form_data),
                        "filled_count": len(filled_fields),
                        "failed_count": len(failed_fields)
                    }
                )

            logger.info(f"Filled form: {len(filled_fields)} fields ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={"filled_fields": filled_fields, "count": len(filled_fields)},
                execution_time=execution_time,
                metadata={"field_count": len(filled_fields)}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to fill form: {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"form_data": form_data}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"exception_type": type(e).__name__}
            )

    async def select_option(
        self,
        selector: str,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Select an option from a dropdown.

        Args:
            selector: CSS selector for the select element
            value: Option value to select
            label: Option label/text to select
            index: Option index to select (0-based)
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with select outcome

        Example:
            >>> # Select by value
            >>> result = await executor.select_option("select[name='country']", value="US")
            >>>
            >>> # Select by label
            >>> result = await executor.select_option("select[name='country']", label="United States")
            >>>
            >>> # Select by index
            >>> result = await executor.select_option("select[name='country']", index=0)
        """
        start_time = time.time()
        action = "select_option"

        # Validate at least one selection method provided
        if not any([value, label, index is not None]):
            return ActionResult(
                success=False,
                action=action,
                error="Must provide value, label, or index for selection",
                execution_time=time.time() - start_time,
                metadata={"selector": selector}
            )

        # Validate selector
        if self.validate_before_action:
            validation = self.validator.validate_selector(selector)
            if not validation.valid:
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Selector validation failed: {validation.reason}",
                    execution_time=time.time() - start_time,
                    metadata={"selector": selector}
                )

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find select element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"Select element not found: {selector}")

            # Select option
            if value:
                selected = await element.select_option(value=value, timeout=timeout)
            elif label:
                selected = await element.select_option(label=label, timeout=timeout)
            else:  # index
                selected = await element.select_option(index=index, timeout=timeout)

            execution_time = time.time() - start_time
            logger.info(f"Selected option: {selector} ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={
                    "selector": selector,
                    "selected_values": selected,
                    "method": "value" if value else "label" if label else "index"
                },
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "value": value,
                    "label": label,
                    "index": index
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to select option '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def upload_file(
        self,
        selector: str,
        file_path: Union[str, Path, List[Union[str, Path]]],
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Upload file(s) to a file input element.

        Args:
            selector: CSS selector for the file input element
            file_path: Path to file or list of paths for multiple files
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with upload outcome

        Example:
            >>> # Upload single file
            >>> result = await executor.upload_file(
            ...     "input[type='file']",
            ...     "/path/to/document.pdf"
            ... )
            >>>
            >>> # Upload multiple files
            >>> result = await executor.upload_file(
            ...     "input[type='file'][multiple]",
            ...     ["/path/to/file1.jpg", "/path/to/file2.jpg"]
            ... )
        """
        start_time = time.time()
        action = "upload_file"

        # Normalize file paths
        if isinstance(file_path, (str, Path)):
            file_paths = [str(file_path)]
        else:
            file_paths = [str(p) for p in file_path]

        # Validate files exist
        for path in file_paths:
            if not Path(path).exists():
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"File not found: {path}",
                    execution_time=time.time() - start_time,
                    metadata={"selector": selector, "file_path": path}
                )

        # Validate selector
        if self.validate_before_action:
            validation = self.validator.validate_selector(selector)
            if not validation.valid:
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Selector validation failed: {validation.reason}",
                    execution_time=time.time() - start_time,
                    metadata={"selector": selector}
                )

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find file input element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"File input element not found: {selector}")

            # Upload file(s)
            await element.set_input_files(file_paths, timeout=timeout)

            execution_time = time.time() - start_time
            logger.info(f"Uploaded {len(file_paths)} file(s): {selector} ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={
                    "selector": selector,
                    "file_count": len(file_paths),
                    "files": file_paths
                },
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "file_count": len(file_paths)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to upload file to '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector, "files": file_paths}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def extract_text(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Extract text content from an element.

        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with extracted text

        Example:
            >>> result = await executor.extract_text("h1.title")
            >>> if result.success:
            ...     print(f"Title: {result.data['text']}")
        """
        start_time = time.time()
        action = "extract_text"

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"Element not found: {selector}")

            # Extract text
            text = await element.inner_text()

            execution_time = time.time() - start_time
            logger.info(f"Extracted text from: {selector} ({len(text)} chars, {execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={
                    "selector": selector,
                    "text": text,
                    "length": len(text)
                },
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "text_length": len(text)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to extract text from '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def extract_data(
        self,
        selectors: Dict[str, str],
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Extract data from multiple elements.

        Args:
            selectors: Dictionary mapping field names to CSS selectors
            timeout: Timeout in milliseconds for each element

        Returns:
            ActionResult with extracted data

        Example:
            >>> result = await executor.extract_data({
            ...     "title": "h1.title",
            ...     "price": "span.price",
            ...     "description": "div.description"
            ... })
            >>> if result.success:
            ...     data = result.data['extracted_data']
            ...     print(f"Title: {data['title']}")
        """
        start_time = time.time()
        action = "extract_data"

        try:
            page = self.page_navigator.page
            extracted_data = {}
            missing_fields = []

            # Extract each field
            for field_name, selector in selectors.items():
                try:
                    element = await self._find_element(page, selector, timeout or self.default_timeout)
                    if element:
                        text = await element.inner_text()
                        extracted_data[field_name] = text
                    else:
                        missing_fields.append(field_name)
                        extracted_data[field_name] = None
                except Exception as e:
                    logger.warning(f"Failed to extract field '{field_name}': {e}")
                    missing_fields.append(field_name)
                    extracted_data[field_name] = None

            execution_time = time.time() - start_time
            logger.info(
                f"Extracted data: {len(extracted_data)} fields "
                f"({len(missing_fields)} missing, {execution_time:.2f}s)"
            )

            return ActionResult(
                success=True,
                action=action,
                data={
                    "extracted_data": extracted_data,
                    "missing_fields": missing_fields,
                    "field_count": len(extracted_data)
                },
                execution_time=execution_time,
                metadata={
                    "total_fields": len(selectors),
                    "extracted_count": len(extracted_data) - len(missing_fields),
                    "missing_count": len(missing_fields)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to extract data: {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selectors": selectors}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"exception_type": type(e).__name__}
            )

    async def extract_table(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Extract data from an HTML table.

        Args:
            selector: CSS selector for the table element
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with table data as list of dictionaries

        Example:
            >>> result = await executor.extract_table("table.data-table")
            >>> if result.success:
            ...     for row in result.data['rows']:
            ...         print(row)
        """
        start_time = time.time()
        action = "extract_table"

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find table element
            table = await self._find_element(page, selector, timeout)
            if not table:
                raise RuntimeError(f"Table element not found: {selector}")

            # Extract headers
            headers = []
            header_elements = await table.query_selector_all("thead th, thead td")
            for header in header_elements:
                text = await header.inner_text()
                headers.append(text.strip())

            # If no headers in thead, try first row
            if not headers:
                first_row = await table.query_selector("tr:first-child")
                if first_row:
                    cells = await first_row.query_selector_all("th, td")
                    for cell in cells:
                        text = await cell.inner_text()
                        headers.append(text.strip())

            # Extract rows
            rows = []
            row_elements = await table.query_selector_all("tbody tr, tr")

            for row_element in row_elements:
                # Skip header rows
                if await row_element.query_selector("th"):
                    continue

                cells = await row_element.query_selector_all("td")
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        text = await cell.inner_text()
                        # Use header name if available, otherwise use index
                        key = headers[i] if i < len(headers) else f"column_{i}"
                        row_data[key] = text.strip()
                    rows.append(row_data)

            execution_time = time.time() - start_time
            logger.info(
                f"Extracted table: {len(headers)} columns, {len(rows)} rows ({execution_time:.2f}s)"
            )

            return ActionResult(
                success=True,
                action=action,
                data={
                    "selector": selector,
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "column_count": len(headers)
                },
                execution_time=execution_time,
                metadata={
                    "selector": selector,
                    "row_count": len(rows),
                    "column_count": len(headers)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to extract table from '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def execute_script(
        self,
        script: str,
        args: Optional[List] = None
    ) -> ActionResult:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute
            args: Optional arguments to pass to the script

        Returns:
            ActionResult with script execution result

        Example:
            >>> # Get page title
            >>> result = await executor.execute_script("return document.title")
            >>>
            >>> # Scroll to bottom
            >>> result = await executor.execute_script(
            ...     "window.scrollTo(0, document.body.scrollHeight)"
            ... )
            >>>
            >>> # Execute with arguments
            >>> result = await executor.execute_script(
            ...     "return arguments[0] + arguments[1]",
            ...     args=[5, 10]
            ... )
        """
        start_time = time.time()
        action = "execute_script"

        # Validate script
        if self.validate_before_action:
            validation = self.validator.validate_action(action, {"script": script})
            if not validation.valid:
                logger.warning(f"Script validation warning: {validation.reason}")
                # Continue with warning but don't fail

        try:
            page = self.page_navigator.page

            # Execute script
            result = await page.evaluate(script, args or [])

            execution_time = time.time() - start_time
            logger.info(f"Executed script ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={"result": result, "script": script[:100]},
                execution_time=execution_time,
                metadata={
                    "script_length": len(script),
                    "args_count": len(args) if args else 0
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to execute script: {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"script": script[:200]}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={
                    "script_length": len(script),
                    "exception_type": type(e).__name__
                }
            )

    async def hover(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Hover over an element.

        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with hover outcome

        Example:
            >>> result = await executor.hover("button.menu-trigger")
        """
        start_time = time.time()
        action = "hover"

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find element
            element = await self._find_element(page, selector, timeout)
            if not element:
                raise RuntimeError(f"Element not found: {selector}")

            # Hover over element
            await element.hover(timeout=timeout)

            execution_time = time.time() - start_time
            logger.info(f"Hovered over element: {selector} ({execution_time:.2f}s)")

            return ActionResult(
                success=True,
                action=action,
                data={"selector": selector, "hovered": True},
                execution_time=execution_time,
                metadata={"selector": selector}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to hover over '{selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {"selector": selector}
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={"selector": selector, "exception_type": type(e).__name__}
            )

    async def drag_and_drop(
        self,
        source_selector: str,
        target_selector: str,
        timeout: Optional[int] = None
    ) -> ActionResult:
        """
        Drag and drop an element to another element.

        Args:
            source_selector: CSS selector for the element to drag
            target_selector: CSS selector for the drop target
            timeout: Timeout in milliseconds

        Returns:
            ActionResult with drag-and-drop outcome

        Example:
            >>> result = await executor.drag_and_drop(
            ...     "div.draggable-item",
            ...     "div.drop-zone"
            ... )
        """
        start_time = time.time()
        action = "drag_and_drop"

        try:
            page = self.page_navigator.page
            timeout = timeout or self.default_timeout

            # Find source element
            source = await self._find_element(page, source_selector, timeout)
            if not source:
                raise RuntimeError(f"Source element not found: {source_selector}")

            # Find target element
            target = await self._find_element(page, target_selector, timeout)
            if not target:
                raise RuntimeError(f"Target element not found: {target_selector}")

            # Perform drag and drop
            await source.drag_to(target, timeout=timeout)

            execution_time = time.time() - start_time
            logger.info(
                f"Dragged '{source_selector}' to '{target_selector}' ({execution_time:.2f}s)"
            )

            return ActionResult(
                success=True,
                action=action,
                data={
                    "source": source_selector,
                    "target": target_selector,
                    "completed": True
                },
                execution_time=execution_time,
                metadata={
                    "source_selector": source_selector,
                    "target_selector": target_selector
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to drag '{source_selector}' to '{target_selector}': {str(e)}"
            logger.error(error_msg)

            screenshot_path = await self._capture_error_screenshot(
                page, action, {
                    "source": source_selector,
                    "target": target_selector
                }
            )

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                screenshot_path=screenshot_path,
                execution_time=execution_time,
                metadata={
                    "source_selector": source_selector,
                    "target_selector": target_selector,
                    "exception_type": type(e).__name__
                }
            )

    async def take_screenshot(
        self,
        full_page: bool = False,
        selector: Optional[str] = None,
        filename: Optional[str] = None
    ) -> ActionResult:
        """
        Take a screenshot of the page or element.

        Args:
            full_page: Capture full scrollable page
            selector: Capture specific element by selector
            filename: Custom filename (without extension)

        Returns:
            ActionResult with screenshot information

        Example:
            >>> # Full page screenshot
            >>> result = await executor.take_screenshot(full_page=True)
            >>>
            >>> # Element screenshot
            >>> result = await executor.take_screenshot(selector="div.chart")
        """
        start_time = time.time()
        action = "take_screenshot"

        try:
            page = self.page_navigator.page

            # Capture screenshot
            screenshot_info = await self.screenshot_manager.capture_screenshot(
                page,
                full_page=full_page,
                selector=selector,
                filename=filename
            )

            execution_time = time.time() - start_time

            if screenshot_info.get("success"):
                logger.info(f"Screenshot captured: {screenshot_info.get('path')} ({execution_time:.2f}s)")

                return ActionResult(
                    success=True,
                    action=action,
                    data=screenshot_info,
                    screenshot_path=screenshot_info.get("path"),
                    execution_time=execution_time,
                    metadata={
                        "full_page": full_page,
                        "selector": selector
                    }
                )
            else:
                error_msg = screenshot_info.get("error", "Unknown error")
                return ActionResult(
                    success=False,
                    action=action,
                    error=f"Screenshot failed: {error_msg}",
                    execution_time=execution_time,
                    metadata={
                        "full_page": full_page,
                        "selector": selector
                    }
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to take screenshot: {str(e)}"
            logger.error(error_msg)

            return ActionResult(
                success=False,
                action=action,
                error=error_msg,
                execution_time=execution_time,
                metadata={"exception_type": type(e).__name__}
            )

    async def _find_element(
        self,
        page,
        selector: str,
        timeout: int
    ):
        """
        Find an element with timeout and error handling.

        Args:
            page: Playwright Page instance
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            Element or None if not found
        """
        try:
            # Wait for element to be visible and ready
            await page.wait_for_selector(
                selector,
                state="visible",
                timeout=timeout
            )

            # Query the element
            element = await page.query_selector(selector)
            return element

        except Exception as e:
            logger.debug(f"Element not found '{selector}': {e}")
            return None

    async def _capture_error_screenshot(
        self,
        page,
        action: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Capture a screenshot when an error occurs.

        Args:
            page: Playwright Page instance
            action: Action name that failed
            context: Additional context about the error

        Returns:
            Screenshot path or None if capture failed
        """
        if not self.screenshot_on_error:
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{action}_{timestamp}"

            screenshot_info = await self.screenshot_manager.capture_screenshot(
                page,
                full_page=False,
                filename=filename
            )

            if screenshot_info.get("success"):
                screenshot_path = screenshot_info.get("path")
                logger.info(f"Error screenshot captured: {screenshot_path}")
                return screenshot_path

        except Exception as e:
            logger.warning(f"Failed to capture error screenshot: {e}")

        return None
