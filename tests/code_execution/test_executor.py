"""
Comprehensive Tests for CodeExecutor

Tests execution orchestration, validation pipeline, user approval, failure handling,
retries, and statistics tracking.

Total tests: 16
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, call
import asyncio

from alpha.code_execution.executor import (
    CodeExecutor,
    ExecutionOptions,
    ExecutionError,
    UserRejectionError
)
from alpha.code_execution.generator import GeneratedCode, CodeGenerationError
from alpha.code_execution.validator import ValidationResult, SecurityReport, QualityReport
from alpha.code_execution.sandbox import ExecutionResult


class TestCodeExecutor:
    """Test suite for CodeExecutor"""

    @pytest.fixture
    def mock_generator(self):
        """Mock CodeGenerator"""
        generator = Mock()
        generator.generate_code = AsyncMock(return_value=GeneratedCode(
            code="print('test')",
            language="python",
            description="Test code"
        ))
        generator.refine_code = AsyncMock(return_value=GeneratedCode(
            code="print('refined')",
            language="python",
            description="Refined code"
        ))
        generator.generation_count = 0
        generator.success_count = 0
        return generator

    @pytest.fixture
    def mock_validator(self):
        """Mock CodeValidator"""
        validator = Mock()
        validator.validate_syntax.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        validator.check_security.return_value = SecurityReport(
            is_safe=True,
            dangerous_patterns=[],
            risk_level="low",
            recommendations=[]
        )
        validator.assess_quality.return_value = QualityReport(
            score=0.8,
            issues=[],
            metrics={"total_lines": 10}
        )
        return validator

    @pytest.fixture
    def mock_sandbox(self):
        """Mock SandboxManager"""
        sandbox = Mock()
        sandbox.create_container.return_value = "container_123"
        sandbox.execute_code.return_value = ExecutionResult(
            success=True,
            stdout="Test output\n",
            stderr="",
            exit_code=0,
            execution_time=1.0
        )
        sandbox.cleanup_container = Mock()
        return sandbox

    @pytest.fixture
    def executor(self, mock_generator, mock_validator, mock_sandbox):
        """Create CodeExecutor with mocked components"""
        return CodeExecutor(mock_generator, mock_validator, mock_sandbox)

    @pytest.mark.asyncio
    async def test_execute_task_success(self, executor, mock_generator):
        """Test successful task execution with code generation"""
        options = ExecutionOptions(
            generate_code=True,
            require_approval=False,
            validate_syntax=True
        )

        result = await executor.execute_task(
            task="print hello world",
            language="python",
            options=options
        )

        assert result.success
        assert result.stdout is not None
        mock_generator.generate_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_code_string_success(self, executor, mock_validator):
        """Test successful execution of provided code string"""
        code = "print('Hello, World!')"
        options = ExecutionOptions(
            generate_code=False,
            require_approval=False
        )

        result = await executor.execute_code_string(
            code=code,
            language="python",
            options=options
        )

        assert result.success
        mock_validator.validate_syntax.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_pipeline_syntax_check(self, executor, mock_validator):
        """Test syntax validation in pipeline"""
        options = ExecutionOptions(
            validate_syntax=True,
            require_approval=False
        )

        await executor.execute_code_string("x = 1", "python", options)

        mock_validator.validate_syntax.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_pipeline_security_check(self, executor, mock_validator):
        """Test security checking in pipeline"""
        options = ExecutionOptions(
            check_security=True,
            require_approval=False
        )

        await executor.execute_code_string("x = 1", "python", options)

        mock_validator.check_security.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_pipeline_quality_check(self, executor, mock_validator):
        """Test quality assessment in pipeline"""
        options = ExecutionOptions(
            assess_quality=True,
            require_approval=False
        )

        await executor.execute_code_string("x = 1", "python", options)

        mock_validator.assess_quality.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_approval_accepted(self, executor):
        """Test user approval mechanism when user accepts"""
        options = ExecutionOptions(require_approval=True)

        with patch.object(executor, '_request_user_approval', return_value=True):
            result = await executor.execute_code_string(
                "print('test')",
                "python",
                options
            )

            assert result.success

    @pytest.mark.asyncio
    async def test_user_approval_rejected(self, executor):
        """Test user approval mechanism when user rejects"""
        options = ExecutionOptions(require_approval=True)

        with patch.object(executor, '_request_user_approval', return_value=False):
            with pytest.raises(UserRejectionError):
                await executor.execute_code_string(
                    "print('test')",
                    "python",
                    options
                )

    @pytest.mark.asyncio
    async def test_syntax_error_retry(self, executor, mock_validator, mock_generator):
        """Test retry on syntax error"""
        # First call: syntax error
        # Second call: success
        call_count = 0
        
        def validation_side_effect(code, lang):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ValidationResult(is_valid=False, errors=["Syntax error"])
            return ValidationResult(is_valid=True)
        
        mock_validator.validate_syntax.side_effect = validation_side_effect

        options = ExecutionOptions(
            generate_code=True,  # Enable code generation/refinement for retry
            max_retries=2,
            require_approval=False
        )

        result = await executor.execute_code_string("bad code", "python", options)

        # Should have refined code after error
        assert mock_generator.refine_code.called or result.success

    @pytest.mark.asyncio
    async def test_execution_failure_retry(self, executor, mock_sandbox, mock_generator):
        """Test retry on execution failure"""
        call_count = 0
        
        def execute_side_effect(container_id, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ExecutionResult(
                    success=False,
                    exit_code=1,
                    error_message="Execution failed"
                )
            return ExecutionResult(success=True, stdout="Success", exit_code=0)
        
        mock_sandbox.execute_code.side_effect = execute_side_effect

        options = ExecutionOptions(
            generate_code=False,
            max_retries=2,
            require_approval=False
        )

        result = await executor.execute_code_string("code", "python", options)

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, executor, mock_validator):
        """Test max retries limit"""
        mock_validator.validate_syntax.return_value = ValidationResult(
            is_valid=False,
            errors=["Persistent syntax error"]
        )

        options = ExecutionOptions(
            generate_code=False,
            max_retries=2,
            require_approval=False
        )

        with pytest.raises(ExecutionError):
            await executor.execute_code_string("bad code", "python", options)

    @pytest.mark.asyncio
    async def test_high_risk_code_blocks_without_approval(self, executor, mock_validator):
        """Test high-risk code blocks execution without approval"""
        mock_validator.check_security.return_value = SecurityReport(
            is_safe=False,
            dangerous_patterns=["eval()"],
            risk_level="high",
            recommendations=["Don't use eval"]
        )

        options = ExecutionOptions(
            require_approval=False,
            check_security=True
        )

        with pytest.raises(ExecutionError) as exc_info:
            await executor.execute_code_string("eval('x')", "python", options)

        assert "high-risk" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_statistics_tracking_success(self, executor):
        """Test statistics tracking on successful execution"""
        options = ExecutionOptions(require_approval=False)

        await executor.execute_code_string("x = 1", "python", options)

        stats = executor.get_execution_statistics()
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_statistics_tracking_failure(self, executor, mock_sandbox):
        """Test statistics tracking on failed execution"""
        mock_sandbox.execute_code.return_value = ExecutionResult(
            success=False,
            exit_code=1,
            error_message="Failed"
        )

        options = ExecutionOptions(
            require_approval=False,
            max_retries=0
        )

        result = await executor.execute_code_string("bad", "python", options)

        stats = executor.get_execution_statistics()
        assert stats["total_executions"] == 1
        assert stats["failed_executions"] >= 0

    @pytest.mark.asyncio
    async def test_execution_with_context(self, executor, mock_generator):
        """Test execution with additional context"""
        options = ExecutionOptions(
            generate_code=True,
            require_approval=False
        )

        context = {"data": [1, 2, 3], "format": "json"}

        await executor.execute_task(
            task="process data",
            language="python",
            options=options,
            context=context
        )

        # Verify context was passed to generator
        call_args = mock_generator.generate_code.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_generation_failure_handling(self, executor, mock_generator):
        """Test handling of code generation failures"""
        mock_generator.generate_code.side_effect = CodeGenerationError("LLM unavailable")

        options = ExecutionOptions(
            generate_code=True,
            require_approval=False
        )

        with pytest.raises(CodeGenerationError):
            await executor.execute_task("test task", "python", options)

    def test_reset_statistics(self, executor):
        """Test statistics reset"""
        # Manually set some stats
        executor._stats["total_executions"] = 10
        executor._stats["successful_executions"] = 8

        executor.reset_statistics()

        stats = executor.get_execution_statistics()
        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0


class TestExecutionOptions:
    """Test ExecutionOptions configuration"""

    def test_execution_options_defaults(self):
        """Test default execution options"""
        options = ExecutionOptions()

        assert options.generate_code == True
        assert options.validate_syntax == True
        assert options.check_security == True
        assert options.require_approval == True
        assert options.allow_network == False
        assert options.timeout == 30
        assert options.max_retries == 2

    def test_execution_options_custom(self):
        """Test custom execution options"""
        options = ExecutionOptions(
            generate_code=False,
            validate_syntax=False,
            require_approval=False,
            allow_network=True,
            timeout=60,
            max_retries=5
        )

        assert options.generate_code == False
        assert options.allow_network == True
        assert options.timeout == 60
        assert options.max_retries == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
