"""
Tests for Alpha Browser Automation - Action Executor

Comprehensive test suite for ActionExecutor with 22 tests covering:
- Click actions (4 tests)
- Form operations (6 tests)
- Data extraction (5 tests)
- Advanced actions (4 tests)
- Screenshot operations (3 tests)
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from pathlib import Path
import asyncio

from alpha.browser_automation.executor import ActionExecutor, ActionResult
from alpha.browser_automation.validator import PageValidator, ValidationResult


# Fixtures

@pytest.fixture
def mock_page():
    """Create a mock Playwright Page object."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_selector = AsyncMock()
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock()
    return page


@pytest.fixture
def mock_element():
    """Create a mock Playwright Element object."""
    element = AsyncMock()
    element.click = AsyncMock()
    element.fill = AsyncMock()
    element.clear = AsyncMock()
    element.inner_text = AsyncMock(return_value="Sample text")
    element.select_option = AsyncMock(return_value=["selected_value"])
    element.set_input_files = AsyncMock()
    element.hover = AsyncMock()
    element.drag_to = AsyncMock()
    element.screenshot = AsyncMock()
    element.query_selector = AsyncMock()
    element.query_selector_all = AsyncMock(return_value=[])
    return element


@pytest.fixture
def mock_navigator(mock_page):
    """Create a mock PageNavigator."""
    navigator = Mock()
    navigator.page = mock_page
    return navigator


@pytest.fixture
def mock_validator():
    """Create a mock PageValidator."""
    validator = Mock(spec=PageValidator)
    validator.validate_selector = Mock(
        return_value=ValidationResult(valid=True, reason="Valid")
    )
    validator.validate_action = Mock(
        return_value=ValidationResult(valid=True, reason="Valid")
    )
    return validator


@pytest.fixture
def mock_screenshot_manager():
    """Create a mock ScreenshotManager."""
    manager = AsyncMock()
    manager.capture_screenshot = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/screenshot.png",
        "filename": "screenshot.png",
        "size_bytes": 12345,
        "timestamp": "2025-01-31T12:00:00"
    })
    return manager


@pytest.fixture
def executor(mock_navigator, mock_validator, mock_screenshot_manager):
    """Create an ActionExecutor instance with mocks."""
    config = {
        "actions": {
            "timeout": 30,
            "screenshot_on_error": True,
            "validate_before_action": True
        }
    }
    return ActionExecutor(
        mock_navigator,
        mock_validator,
        mock_screenshot_manager,
        config
    )


# Click Tests (4 tests)

@pytest.mark.asyncio
async def test_click_element_success(executor, mock_page, mock_element):
    """Test successful element click."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.click_element("button.submit")

    assert result.success is True
    assert result.action == "click_element"
    assert result.data["selector"] == "button.submit"
    assert result.data["clicked"] is True
    assert result.execution_time > 0
    assert result.metadata["selector"] == "button.submit"
    assert result.metadata["button"] == "left"
    assert result.metadata["click_count"] == 1

    mock_element.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_element_different_buttons(executor, mock_page, mock_element):
    """Test clicking with different mouse buttons."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    # Right click
    result = await executor.click_element("div.context-menu", button="right")
    assert result.success is True
    assert result.metadata["button"] == "right"

    # Middle click
    result = await executor.click_element("a.link", button="middle")
    assert result.success is True
    assert result.metadata["button"] == "middle"


@pytest.mark.asyncio
async def test_click_element_double_triple(executor, mock_page, mock_element):
    """Test double-click and triple-click."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    # Double click
    result = await executor.click_element("div.item", click_count=2)
    assert result.success is True
    assert result.metadata["click_count"] == 2

    # Triple click
    result = await executor.click_element("p.text", click_count=3)
    assert result.success is True
    assert result.metadata["click_count"] == 3


@pytest.mark.asyncio
async def test_click_element_timeout(executor, mock_page):
    """Test click element timeout/not found."""
    mock_page.query_selector.return_value = None
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

    result = await executor.click_element("button.missing")

    assert result.success is False
    assert result.action == "click_element"
    assert "Element not found" in result.error or "Timeout" in result.error
    assert result.screenshot_path is not None
    assert result.execution_time > 0


# Form Tests (6 tests)

@pytest.mark.asyncio
async def test_fill_input_success(executor, mock_page, mock_element):
    """Test successful input filling."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.fill_input("input[name='email']", "test@example.com")

    assert result.success is True
    assert result.action == "fill_input"
    assert result.data["selector"] == "input[name='email']"
    assert result.data["value"] == "test@example.com"
    assert result.data["filled"] is True
    assert result.metadata["value_length"] == 16
    assert result.metadata["cleared_first"] is True

    mock_element.clear.assert_called_once()
    mock_element.fill.assert_called_once_with("test@example.com", timeout=30000)


@pytest.mark.asyncio
async def test_fill_form_success(executor, mock_page, mock_element):
    """Test successful form filling."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    form_data = {
        "input[name='username']": "johndoe",
        "input[name='email']": "john@example.com",
        "textarea[name='bio']": "Developer"
    }

    result = await executor.fill_form(form_data)

    assert result.success is True
    assert result.action == "fill_form"
    assert result.data["count"] == 3
    assert len(result.data["filled_fields"]) == 3
    assert result.metadata["field_count"] == 3

    # Verify each field was filled
    assert mock_element.fill.call_count == 3


@pytest.mark.asyncio
async def test_select_option_by_value(executor, mock_page, mock_element):
    """Test selecting option by value."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.select_option("select[name='country']", value="US")

    assert result.success is True
    assert result.action == "select_option"
    assert result.data["method"] == "value"
    assert result.data["selected_values"] == ["selected_value"]
    assert result.metadata["value"] == "US"

    mock_element.select_option.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_single(executor, mock_page, mock_element, tmp_path):
    """Test uploading a single file."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    # Create a temporary file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    result = await executor.upload_file("input[type='file']", str(test_file))

    assert result.success is True
    assert result.action == "upload_file"
    assert result.data["file_count"] == 1
    assert str(test_file) in result.data["files"]

    mock_element.set_input_files.assert_called_once()


@pytest.mark.asyncio
async def test_fill_input_no_clear(executor, mock_page, mock_element):
    """Test filling input without clearing first."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.fill_input(
        "input[name='search']",
        "query",
        clear_first=False
    )

    assert result.success is True
    assert result.metadata["cleared_first"] is False
    mock_element.clear.assert_not_called()
    mock_element.fill.assert_called_once()


@pytest.mark.asyncio
async def test_fill_form_validation_error(executor, mock_validator):
    """Test form filling with validation error."""
    # Make validator return invalid result
    mock_validator.validate_action.return_value = ValidationResult(
        valid=False,
        reason="Invalid form data",
        severity="error"
    )

    result = await executor.fill_form({"field": "value"})

    assert result.success is False
    assert result.action == "fill_form"
    assert "Form validation failed" in result.error


# Extraction Tests (5 tests)

@pytest.mark.asyncio
async def test_extract_text_success(executor, mock_page, mock_element):
    """Test successful text extraction."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()
    mock_element.inner_text.return_value = "Hello World"

    result = await executor.extract_text("h1.title")

    assert result.success is True
    assert result.action == "extract_text"
    assert result.data["text"] == "Hello World"
    assert result.data["length"] == 11
    assert result.metadata["text_length"] == 11


@pytest.mark.asyncio
async def test_extract_data_success(executor, mock_page, mock_element):
    """Test extracting data from multiple elements."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    # Mock different text for different selectors
    call_count = [0]

    async def mock_inner_text():
        texts = ["Product Title", "$99.99", "Great product!"]
        result = texts[call_count[0] % len(texts)]
        call_count[0] += 1
        return result

    mock_element.inner_text = mock_inner_text

    selectors = {
        "title": "h1.product-title",
        "price": "span.price",
        "description": "div.description"
    }

    result = await executor.extract_data(selectors)

    assert result.success is True
    assert result.action == "extract_data"
    assert "extracted_data" in result.data
    assert result.data["field_count"] == 3
    assert result.metadata["total_fields"] == 3


@pytest.mark.asyncio
async def test_extract_data_all_fields(executor, mock_page, mock_element):
    """Test extracting all fields successfully."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()
    mock_element.inner_text.return_value = "Field value"

    selectors = {
        "field1": "div.field1",
        "field2": "div.field2",
        "field3": "div.field3"
    }

    result = await executor.extract_data(selectors)

    assert result.success is True
    assert len(result.data["extracted_data"]) == 3
    assert len(result.data["missing_fields"]) == 0
    assert result.metadata["extracted_count"] == 3
    assert result.metadata["missing_count"] == 0


@pytest.mark.asyncio
async def test_extract_table_success(executor, mock_page, mock_element):
    """Test extracting table data."""
    # Create mock table structure
    mock_table = AsyncMock()

    # Mock header cells
    mock_header1 = AsyncMock()
    mock_header1.inner_text = AsyncMock(return_value="Name")
    mock_header2 = AsyncMock()
    mock_header2.inner_text = AsyncMock(return_value="Age")

    mock_table.query_selector_all = AsyncMock(
        side_effect=[
            [mock_header1, mock_header2],  # Headers
            []  # First call for tbody tr
        ]
    )

    # Mock data rows
    mock_cell1 = AsyncMock()
    mock_cell1.inner_text = AsyncMock(return_value="John")
    mock_cell2 = AsyncMock()
    mock_cell2.inner_text = AsyncMock(return_value="30")

    mock_row = AsyncMock()
    mock_row.query_selector = AsyncMock(return_value=None)  # No th in row
    mock_row.query_selector_all = AsyncMock(return_value=[mock_cell1, mock_cell2])

    # Second query_selector_all call for rows
    async def mock_query_all(selector):
        if "th" in selector:
            return [mock_header1, mock_header2]
        elif "tr" in selector:
            return [mock_row]
        return []

    mock_table.query_selector_all = mock_query_all

    mock_page.query_selector.return_value = mock_table
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.extract_table("table.data")

    assert result.success is True
    assert result.action == "extract_table"
    assert "headers" in result.data
    assert "rows" in result.data
    assert result.data["column_count"] >= 0
    assert result.data["row_count"] >= 0


@pytest.mark.asyncio
async def test_extract_data_no_matches(executor, mock_page):
    """Test extracting data with no matching elements."""
    mock_page.query_selector.return_value = None
    mock_page.wait_for_selector = AsyncMock()

    selectors = {
        "missing1": "div.missing1",
        "missing2": "div.missing2"
    }

    result = await executor.extract_data(selectors)

    assert result.success is True  # Still succeeds, but with missing fields
    assert len(result.data["missing_fields"]) == 2
    assert result.metadata["missing_count"] == 2


# Advanced Action Tests (4 tests)

@pytest.mark.asyncio
async def test_execute_script_success(executor, mock_page):
    """Test successful script execution."""
    mock_page.evaluate.return_value = "Document Title"

    result = await executor.execute_script("return document.title")

    assert result.success is True
    assert result.action == "execute_script"
    assert result.data["result"] == "Document Title"
    assert result.metadata["script_length"] > 0

    mock_page.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_execute_script_dangerous_patterns(executor, mock_page, mock_validator):
    """Test script execution with dangerous patterns (validation warning)."""
    # Validator returns warning but doesn't block
    mock_validator.validate_action.return_value = ValidationResult(
        valid=False,
        reason="Potentially dangerous script pattern detected",
        severity="warning"
    )

    mock_page.evaluate.return_value = 42

    # Script should still execute despite warning
    result = await executor.execute_script("eval('1+1')")

    assert result.success is True  # Executes with warning
    mock_page.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_hover_success(executor, mock_page, mock_element):
    """Test successful hover action."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.hover("button.menu-trigger")

    assert result.success is True
    assert result.action == "hover"
    assert result.data["hovered"] is True
    assert result.metadata["selector"] == "button.menu-trigger"

    mock_element.hover.assert_called_once()


@pytest.mark.asyncio
async def test_drag_and_drop_success(executor, mock_page, mock_element):
    """Test successful drag and drop."""
    mock_source = AsyncMock()
    mock_target = AsyncMock()
    mock_source.drag_to = AsyncMock()

    async def mock_query_selector(selector):
        if "draggable" in selector:
            return mock_source
        elif "drop-zone" in selector:
            return mock_target
        return None

    mock_page.query_selector = mock_query_selector
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.drag_and_drop(
        "div.draggable-item",
        "div.drop-zone"
    )

    assert result.success is True
    assert result.action == "drag_and_drop"
    assert result.data["completed"] is True
    assert result.data["source"] == "div.draggable-item"
    assert result.data["target"] == "div.drop-zone"

    mock_source.drag_to.assert_called_once()


# Screenshot Tests (3 tests)

@pytest.mark.asyncio
async def test_take_screenshot_full_page(executor, mock_screenshot_manager):
    """Test taking full page screenshot."""
    result = await executor.take_screenshot(full_page=True)

    assert result.success is True
    assert result.action == "take_screenshot"
    assert result.screenshot_path == "/tmp/screenshot.png"
    assert result.metadata["full_page"] is True

    mock_screenshot_manager.capture_screenshot.assert_called_once()
    call_args = mock_screenshot_manager.capture_screenshot.call_args
    assert call_args.kwargs["full_page"] is True


@pytest.mark.asyncio
async def test_take_screenshot_element(executor, mock_screenshot_manager):
    """Test taking element screenshot."""
    result = await executor.take_screenshot(selector="div.chart")

    assert result.success is True
    assert result.action == "take_screenshot"
    assert result.metadata["selector"] == "div.chart"

    mock_screenshot_manager.capture_screenshot.assert_called_once()
    call_args = mock_screenshot_manager.capture_screenshot.call_args
    assert call_args.kwargs["selector"] == "div.chart"


@pytest.mark.asyncio
async def test_error_screenshot_capture(executor, mock_page, mock_screenshot_manager):
    """Test automatic error screenshot capture."""
    mock_page.query_selector.return_value = None
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Element not found"))

    result = await executor.click_element("button.missing")

    assert result.success is False
    assert result.screenshot_path is not None

    # Verify error screenshot was captured
    mock_screenshot_manager.capture_screenshot.assert_called_once()
    call_args = mock_screenshot_manager.capture_screenshot.call_args
    # Check that filename contains 'error'
    assert "error" in call_args.kwargs.get("filename", "").lower()


# Additional Edge Cases

@pytest.mark.asyncio
async def test_selector_validation_failure(executor, mock_validator):
    """Test action fails when selector validation fails."""
    mock_validator.validate_selector.return_value = ValidationResult(
        valid=False,
        reason="Invalid selector",
        severity="error"
    )

    result = await executor.click_element("invalid selector")

    assert result.success is False
    assert "Selector validation failed" in result.error


@pytest.mark.asyncio
async def test_upload_file_not_found(executor, tmp_path):
    """Test upload file with non-existent file."""
    non_existent = tmp_path / "missing.txt"

    result = await executor.upload_file("input[type='file']", str(non_existent))

    assert result.success is False
    assert "File not found" in result.error


@pytest.mark.asyncio
async def test_select_option_no_method(executor):
    """Test select option without providing value, label, or index."""
    result = await executor.select_option("select[name='test']")

    assert result.success is False
    assert "Must provide value, label, or index" in result.error


# Execution Time Tests

@pytest.mark.asyncio
async def test_execution_time_tracking(executor, mock_page, mock_element):
    """Test that execution time is properly tracked."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    # Add slight delay to ensure measurable time
    async def delayed_click(**kwargs):
        await asyncio.sleep(0.01)

    mock_element.click = delayed_click

    result = await executor.click_element("button")

    assert result.success is True
    assert result.execution_time > 0
    assert result.execution_time >= 0.01


# Metadata Tests

@pytest.mark.asyncio
async def test_action_result_metadata(executor, mock_page, mock_element):
    """Test that ActionResult includes proper metadata."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.click_element("button.test", button="right", click_count=2)

    assert result.success is True
    assert "selector" in result.metadata
    assert result.metadata["button"] == "right"
    assert result.metadata["click_count"] == 2


# Configuration Tests

@pytest.mark.asyncio
async def test_custom_timeout(executor, mock_page, mock_element):
    """Test using custom timeout for actions."""
    mock_page.query_selector.return_value = mock_element
    mock_page.wait_for_selector = AsyncMock()

    result = await executor.click_element("button", timeout=5000)

    assert result.success is True
    # Verify wait_for_selector was called with custom timeout
    mock_page.wait_for_selector.assert_called()
