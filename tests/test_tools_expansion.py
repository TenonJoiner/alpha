"""
Tests for Alpha Tools Expansion (v0.2.0)

Tests new tools: HTTPTool, DateTimeTool, CalculatorTool, and enhanced SearchTool
"""

import pytest
import asyncio
from datetime import datetime
import pytz

from alpha.tools.registry import (
    HTTPTool,
    DateTimeTool,
    CalculatorTool,
    SearchTool,
    ToolResult
)


class TestHTTPTool:
    """Tests for HTTPTool"""

    @pytest.fixture
    def http_tool(self):
        return HTTPTool()

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_http_get_success(self, http_tool):
        """Test successful GET request"""
        result = await http_tool.execute(
            url="https://httpbin.org/get",
            method="GET"
        )

        assert result.success
        assert result.output is not None
        assert result.output["status_code"] == 200
        assert "body" in result.output

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_http_get_with_params(self, http_tool):
        """Test GET with query parameters"""
        result = await http_tool.execute(
            url="https://httpbin.org/get",
            method="GET",
            params={"test": "value", "foo": "bar"}
        )

        assert result.success
        assert result.output["status_code"] == 200

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_http_post_json(self, http_tool):
        """Test POST with JSON body"""
        result = await http_tool.execute(
            url="https://httpbin.org/post",
            method="POST",
            json={"key": "value", "number": 42}
        )

        assert result.success
        assert result.output["status_code"] == 200

    @pytest.mark.asyncio
    async def test_http_invalid_url(self, http_tool):
        """Test invalid URL handling"""
        result = await http_tool.execute(
            url="not-a-valid-url",
            method="GET"
        )

        assert not result.success
        assert "Invalid URL" in result.error

    @pytest.mark.asyncio
    async def test_http_invalid_method(self, http_tool):
        """Test invalid HTTP method"""
        result = await http_tool.execute(
            url="https://httpbin.org/get",
            method="INVALID"
        )

        assert not result.success
        assert "Unsupported HTTP method" in result.error

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_http_timeout(self, http_tool):
        """Test request timeout"""
        result = await http_tool.execute(
            url="https://httpbin.org/delay/10",
            method="GET",
            timeout=1
        )

        assert not result.success
        assert "timed out" in result.error.lower()

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_http_404(self, http_tool):
        """Test 404 response handling"""
        result = await http_tool.execute(
            url="https://httpbin.org/status/404",
            method="GET"
        )

        assert not result.success
        assert result.output["status_code"] == 404


class TestDateTimeTool:
    """Tests for DateTimeTool"""

    @pytest.fixture
    def datetime_tool(self):
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_datetime_now(self, datetime_tool):
        """Test getting current datetime"""
        result = await datetime_tool.execute(operation="now")

        assert result.success
        assert result.output is not None
        # Verify it's a valid ISO format datetime
        datetime.fromisoformat(result.output.replace('Z', '+00:00'))

    @pytest.mark.asyncio
    async def test_datetime_now_with_timezone(self, datetime_tool):
        """Test getting current datetime in specific timezone"""
        result = await datetime_tool.execute(
            operation="now",
            timezone="Asia/Shanghai"
        )

        assert result.success
        assert result.metadata["timezone"] == "Asia/Shanghai"

    @pytest.mark.asyncio
    async def test_datetime_parse(self, datetime_tool):
        """Test datetime parsing"""
        result = await datetime_tool.execute(
            operation="parse",
            datetime_str="2026-01-29T10:00:00Z"
        )

        assert result.success
        assert "iso" in result.output
        assert "timestamp" in result.output
        assert "timezone" in result.output

    @pytest.mark.asyncio
    async def test_datetime_format(self, datetime_tool):
        """Test datetime formatting"""
        result = await datetime_tool.execute(
            operation="format",
            datetime_str="2026-01-29T10:00:00Z",
            format="%Y-%m-%d"
        )

        assert result.success
        assert result.output == "2026-01-29"

    @pytest.mark.asyncio
    async def test_datetime_add(self, datetime_tool):
        """Test adding duration to datetime"""
        result = await datetime_tool.execute(
            operation="add",
            datetime_str="2026-01-29T10:00:00Z",
            duration={"days": 1, "hours": 2, "minutes": 30}
        )

        assert result.success
        # Result should be 2026-01-30T12:30:00+00:00
        assert "2026-01-30" in result.output

    @pytest.mark.asyncio
    async def test_datetime_subtract(self, datetime_tool):
        """Test subtracting duration from datetime"""
        result = await datetime_tool.execute(
            operation="subtract",
            datetime_str="2026-01-29T10:00:00Z",
            duration={"days": 1}
        )

        assert result.success
        assert "2026-01-28" in result.output

    @pytest.mark.asyncio
    async def test_datetime_diff(self, datetime_tool):
        """Test calculating difference between datetimes"""
        result = await datetime_tool.execute(
            operation="diff",
            datetime1="2026-01-29T10:00:00Z",
            datetime2="2026-01-30T10:00:00Z"
        )

        assert result.success
        assert result.output["days"] == 1
        assert result.output["total_seconds"] == 86400

    @pytest.mark.asyncio
    async def test_datetime_timezone_convert(self, datetime_tool):
        """Test timezone conversion"""
        result = await datetime_tool.execute(
            operation="timezone_convert",
            datetime_str="2026-01-29T10:00:00Z",
            timezone="Asia/Shanghai"
        )

        assert result.success
        # Shanghai is UTC+8, so 10:00 UTC should be 18:00 CST
        assert "18:00:00" in result.output


class TestCalculatorTool:
    """Tests for CalculatorTool"""

    @pytest.fixture
    def calculator_tool(self):
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculator_basic_arithmetic(self, calculator_tool):
        """Test basic arithmetic operations"""
        result = await calculator_tool.execute(
            operation="calculate",
            expression="2 + 2"
        )

        assert result.success
        assert result.output == 4.0

    @pytest.mark.asyncio
    async def test_calculator_complex_expression(self, calculator_tool):
        """Test complex mathematical expression"""
        result = await calculator_tool.execute(
            operation="calculate",
            expression="(10 + 5) * 2 - 8 / 4"
        )

        assert result.success
        assert result.output == 28.0

    @pytest.mark.asyncio
    async def test_calculator_functions(self, calculator_tool):
        """Test mathematical functions"""
        result = await calculator_tool.execute(
            operation="calculate",
            expression="sqrt(16)"
        )

        assert result.success
        assert result.output == 4.0

    @pytest.mark.asyncio
    async def test_calculator_constants(self, calculator_tool):
        """Test pi and e constants"""
        result = await calculator_tool.execute(
            operation="calculate",
            expression="pi * 2"
        )

        assert result.success
        assert abs(result.output - 6.283185307179586) < 0.0001

    @pytest.mark.asyncio
    async def test_calculator_unit_conversion_length(self, calculator_tool):
        """Test length unit conversion"""
        result = await calculator_tool.execute(
            operation="convert_unit",
            value=1000.0,
            from_unit="m",
            to_unit="km"
        )

        assert result.success
        assert result.output == 1.0

    @pytest.mark.asyncio
    async def test_calculator_unit_conversion_weight(self, calculator_tool):
        """Test weight unit conversion"""
        result = await calculator_tool.execute(
            operation="convert_unit",
            value=1.0,
            from_unit="kg",
            to_unit="g"
        )

        assert result.success
        assert result.output == 1000.0

    @pytest.mark.asyncio
    async def test_calculator_temperature_conversion(self, calculator_tool):
        """Test temperature conversion"""
        result = await calculator_tool.execute(
            operation="convert_unit",
            value=0.0,
            from_unit="C",
            to_unit="F"
        )

        assert result.success
        assert result.output == 32.0

    @pytest.mark.asyncio
    async def test_calculator_data_conversion(self, calculator_tool):
        """Test data unit conversion"""
        result = await calculator_tool.execute(
            operation="convert_unit",
            value=1.0,
            from_unit="GB",
            to_unit="MB"
        )

        assert result.success
        assert result.output == 1024.0

    @pytest.mark.asyncio
    async def test_calculator_invalid_expression(self, calculator_tool):
        """Test invalid expression handling"""
        result = await calculator_tool.execute(
            operation="calculate",
            expression="import os"
        )

        assert not result.success
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_calculator_invalid_unit_conversion(self, calculator_tool):
        """Test invalid unit conversion"""
        result = await calculator_tool.execute(
            operation="convert_unit",
            value=1.0,
            from_unit="m",
            to_unit="kg"
        )

        assert not result.success
        assert "Cannot convert" in result.error


class TestSearchTool:
    """Tests for enhanced SearchTool - Network integration tests"""

    @pytest.fixture
    def search_tool(self):
        return SearchTool()

    @pytest.mark.network
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_search_basic(self, search_tool):
        """Test basic search functionality"""
        result = await search_tool.execute(query="Python programming")

        assert result.success
        assert "results" in result.output
        assert isinstance(result.output["results"], list)

    @pytest.mark.network
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_search_with_limit(self, search_tool):
        """Test search with result limit"""
        result = await search_tool.execute(
            query="AI technology",
            limit=3
        )

        assert result.success
        assert len(result.output["results"]) <= 3

    @pytest.mark.network
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_search_result_structure(self, search_tool):
        """Test search result structure"""
        result = await search_tool.execute(query="test query")

        assert result.success
        if result.output["results"]:
            first_result = result.output["results"][0]
            assert "title" in first_result
            assert "url" in first_result
            # snippet is optional for placeholder
            assert "source" in first_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
