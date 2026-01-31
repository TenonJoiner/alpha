"""
Comprehensive Tests for CodeExecutionTool

Tests tool interface compliance, parameter validation, execution flows,
error handling, and configuration management.

Total tests: 12
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from alpha.tools.code_tool import CodeExecutionTool
from alpha.tools.registry import ToolResult
from alpha.code_execution.sandbox import ExecutionResult
from alpha.code_execution.generator import GeneratedCode


class TestCodeExecutionTool:
    """Test suite for CodeExecutionTool"""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service"""
        service = Mock()
        service.generate = AsyncMock(return_value=Mock(
            text='{"code": "print(\\"test\\")", "description": "Test"}'
        ))
        return service

    @pytest.fixture
    def tool(self, mock_llm_service):
        """Create CodeExecutionTool instance"""
        config = {
            "code_execution": {
                "defaults": {},
                "security": {"scan_code": True, "require_approval": False},
                "limits": {"max_execution_time": 300}
            }
        }
        return CodeExecutionTool(mock_llm_service, config)

    @pytest.fixture
    def mock_executor(self):
        """Mock CodeExecutor"""
        executor = Mock()
        executor.execute_task = AsyncMock(return_value=ExecutionResult(
            success=True,
            stdout="Output",
            stderr="",
            exit_code=0,
            execution_time=1.0
        ))
        executor.execute_code_string = AsyncMock(return_value=ExecutionResult(
            success=True,
            stdout="Output",
            stderr="",
            exit_code=0,
            execution_time=1.0
        ))
        executor.get_execution_statistics.return_value = {
            "total_executions": 0,
            "successful_executions": 0,
            "success_rate": 0.0
        }
        return executor

    # Tool Interface Compliance Tests

    def test_tool_initialization(self, mock_llm_service):
        """Test tool initialization"""
        tool = CodeExecutionTool(mock_llm_service)

        assert tool.name == "code_execution"
        assert tool.description is not None
        assert "safe" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_with_task_parameter(self, tool, mock_executor):
        """Test execute() with task parameter"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._executor = mock_executor
            tool._docker_available = True

            result = await tool.execute(
                task="Calculate factorial of 5",
                language="python"
            )

            assert isinstance(result, ToolResult)
            mock_executor.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_code_parameter(self, tool, mock_executor):
        """Test execute() with code parameter"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._executor = mock_executor
            tool._docker_available = True

            result = await tool.execute(
                code="print('Hello')",
                language="python"
            )

            assert isinstance(result, ToolResult)
            mock_executor.execute_code_string.assert_called_once()

    # Parameter Validation Tests

    @pytest.mark.asyncio
    async def test_validate_missing_task_and_code(self, tool):
        """Test validation when both task and code are missing"""
        result = await tool.execute(language="python")

        assert not result.success
        assert "must be provided" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_both_task_and_code_provided(self, tool):
        """Test validation when both task and code are provided"""
        result = await tool.execute(
            task="Do something",
            code="print('test')",
            language="python"
        )

        assert not result.success
        assert "either" in result.error.lower() and "or" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_invalid_language(self, tool):
        """Test validation with unsupported language"""
        result = await tool.execute(
            task="Test task",
            language="ruby"
        )

        assert not result.success
        assert "unsupported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_empty_task(self, tool):
        """Test validation with empty task"""
        result = await tool.execute(
            task="   ",
            language="python"
        )

        assert not result.success
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_empty_code(self, tool):
        """Test validation with empty code"""
        result = await tool.execute(
            code="   ",
            language="python"
        )

        assert not result.success
        assert "empty" in result.error.lower()

    # Docker Availability Tests

    @pytest.mark.asyncio
    async def test_docker_not_available_error(self, tool):
        """Test error when Docker is not available"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._docker_available = False

            result = await tool.execute(
                code="print('test')",
                language="python"
            )

            assert not result.success
            assert "docker" in result.error.lower()
            assert "not available" in result.error.lower()

    # Configuration Tests

    def test_configuration_reading(self, mock_llm_service):
        """Test configuration reading from config dict"""
        config = {
            "code_execution": {
                "defaults": {"timeout": 60},
                "security": {"require_approval": False},
                "limits": {"max_execution_time": 120}
            }
        }

        tool = CodeExecutionTool(mock_llm_service, config)
        assert tool.config == config

    # ToolResult Format Tests

    @pytest.mark.asyncio
    async def test_tool_result_format_success(self, tool, mock_executor):
        """Test ToolResult format for successful execution"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._executor = mock_executor
            tool._docker_available = True

            result = await tool.execute(
                code="print('test')",
                language="python"
            )

            assert result.success
            assert result.output is not None
            assert result.error is None
            assert "language" in result.metadata

    @pytest.mark.asyncio
    async def test_tool_result_format_failure(self, tool, mock_executor):
        """Test ToolResult format for failed execution"""
        mock_executor.execute_code_string.return_value = ExecutionResult(
            success=False,
            stdout="",
            stderr="Error occurred",
            exit_code=1,
            error_message="Execution failed"
        )

        with patch.object(tool, '_ensure_components_initialized'):
            tool._executor = mock_executor
            tool._docker_available = True

            result = await tool.execute(
                code="bad code",
                language="python"
            )

            assert not result.success
            assert result.error is not None
            assert "failed" in result.error.lower()

    # Statistics Tests

    def test_get_statistics(self, tool, mock_executor):
        """Test statistics retrieval"""
        tool._executor = mock_executor

        stats = tool.get_statistics()

        assert "total_executions" in stats
        assert "success_rate" in stats

    def test_get_statistics_before_initialization(self, tool):
        """Test statistics before executor initialization"""
        stats = tool.get_statistics()

        assert stats["total_executions"] == 0
        assert stats["success_rate"] == 0.0

    # Availability Check Tests

    def test_is_available_true(self, tool):
        """Test availability check when Docker is available"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._docker_available = True
            assert tool.is_available()

    def test_is_available_false(self, tool):
        """Test availability check when Docker is not available"""
        with patch.object(tool, '_ensure_components_initialized'):
            tool._docker_available = False
            assert not tool.is_available()


class TestCodeExecutionToolIntegration:
    """Integration tests for CodeExecutionTool"""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service"""
        service = Mock()
        service.generate = AsyncMock(return_value=Mock(
            text='{"code": "import sys\\nprint(sys.version)", "description": "Print Python version"}'
        ))
        return service

    @pytest.mark.asyncio
    async def test_full_execution_flow_with_task(self, mock_llm_service):
        """Test complete execution flow from task to result"""
        tool = CodeExecutionTool(mock_llm_service)

        # Mock SandboxManager to avoid Docker dependency
        with patch('alpha.tools.code_tool.SandboxManager') as mock_sandbox_cls:
            mock_sandbox = Mock()
            mock_sandbox.is_docker_available.return_value = True
            mock_sandbox.create_container.return_value = "test_container_123"
            mock_sandbox.execute_code.return_value = Mock(
                success=True,
                stdout="3.12.0\n",
                stderr="",
                exit_code=0,
                execution_time=0.1
            )
            mock_sandbox_cls.return_value = mock_sandbox

            result = await tool.execute(
                task="Print Python version",
                language="python",
                require_approval=False
            )

            # Result should be successful
            assert isinstance(result, ToolResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
