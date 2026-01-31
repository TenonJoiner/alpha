"""
Code Executor Module

Orchestrates the complete code execution pipeline: generation → validation →
user approval → execution → failure handling. This is the main integration layer
that ties together CodeGenerator, CodeValidator, and SandboxManager.

The CodeExecutor handles:
- Code generation with context awareness
- Multi-stage validation (syntax, security, quality)
- User approval workflow with detailed information display
- Safe sandboxed execution
- Intelligent failure handling with retry logic
- Execution statistics tracking

Phase: 4.1 - Code Generation & Safe Execution
Requirements: REQ-4.1, REQ-4.2, REQ-4.3
Day 4: Code Execution Coordinator
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from .generator import CodeGenerator, GeneratedCode, CodeGenerationError
from .validator import CodeValidator, ValidationResult, SecurityReport, QualityReport
from .sandbox import SandboxManager, SandboxConfig, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionOptions:
    """
    Configuration options for code execution.

    This dataclass controls the behavior of the execution pipeline,
    determining which validation steps to perform, whether to generate
    code or use provided code, and execution environment settings.

    Attributes:
        generate_code: Whether to generate code or use provided code
        validate_syntax: Enable syntax validation before execution
        check_security: Enable security scanning before execution
        assess_quality: Enable quality assessment (optional, for insights)
        require_approval: Require user approval before executing code
        allow_network: Allow network access in sandbox (disabled by default for safety)
        timeout: Maximum execution time in seconds
        max_retries: Maximum attempts for code generation/refinement
    """
    generate_code: bool = True
    validate_syntax: bool = True
    check_security: bool = True
    assess_quality: bool = False
    require_approval: bool = True
    allow_network: bool = False
    timeout: int = 30
    max_retries: int = 2


class ExecutionError(Exception):
    """Raised when code execution fails after all retries."""
    pass


class UserRejectionError(Exception):
    """Raised when user rejects code execution."""
    pass


class CodeExecutor:
    """
    Main orchestrator for code generation, validation, and execution.

    This class coordinates the complete lifecycle of code execution:
    1. Generate code (optional, if not provided)
    2. Validate syntax
    3. Check security
    4. Assess quality (optional)
    5. Request user approval
    6. Execute in sandbox
    7. Handle failures with intelligent retry

    The executor maintains statistics about executions and provides
    detailed feedback to users at each step of the process.

    Example:
        >>> executor = CodeExecutor(generator, validator, sandbox)
        >>> options = ExecutionOptions(
        ...     generate_code=True,
        ...     require_approval=True,
        ...     timeout=30
        ... )
        >>> result = await executor.execute_task(
        ...     task="Calculate factorial of 10",
        ...     language="python",
        ...     options=options
        ... )
        >>> print(result.stdout)
    """

    def __init__(
        self,
        generator: CodeGenerator,
        validator: CodeValidator,
        sandbox: SandboxManager
    ):
        """
        Initialize code executor with required components.

        Args:
            generator: CodeGenerator instance for generating code
            validator: CodeValidator instance for validation checks
            sandbox: SandboxManager instance for safe execution
        """
        self.generator = generator
        self.validator = validator
        self.sandbox = sandbox

        # Statistics tracking
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "code_generation_attempts": 0,
            "refinement_attempts": 0,
            "user_rejections": 0,
            "security_blocks": 0,
            "syntax_errors": 0,
            "execution_errors": 0,
        }

        logger.info("CodeExecutor initialized")

    async def execute_task(
        self,
        task: str,
        language: str = "python",
        options: Optional[ExecutionOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a task by generating and running code.

        This is the main entry point for task-based code execution.
        It follows the complete pipeline:
        1. Generate code from task description (if options.generate_code)
        2. Validate syntax (if options.validate_syntax)
        3. Check security (if options.check_security)
        4. Assess quality (if options.assess_quality)
        5. Request user approval (if options.require_approval)
        6. Execute in sandbox
        7. Handle failures with retry logic

        Args:
            task: Natural language description of what the code should do
            language: Programming language (python, javascript, bash)
            options: Execution options (uses defaults if not provided)
            context: Optional context for code generation

        Returns:
            ExecutionResult with output and execution details

        Raises:
            CodeGenerationError: If code generation fails after retries
            UserRejectionError: If user rejects code execution
            ExecutionError: If execution fails after retries

        Example:
            >>> result = await executor.execute_task(
            ...     task="Sort a list of numbers",
            ...     language="python",
            ...     options=ExecutionOptions(require_approval=False)
            ... )
        """
        if options is None:
            options = ExecutionOptions()

        logger.info(f"Starting task execution: {task[:100]}...")
        logger.info(f"Language: {language}, Options: {options}")

        start_time = time.time()
        self._stats["total_executions"] += 1

        try:
            # Step 1: Generate code (if requested)
            if options.generate_code:
                logger.info("Step 1: Generating code")
                generated_code = await self._generate_code_with_retry(
                    task=task,
                    language=language,
                    context=context,
                    max_retries=options.max_retries
                )
                code = generated_code.code
                logger.info(f"Code generated successfully ({len(code)} chars)")
            else:
                raise ValueError("execute_task requires generate_code=True. Use execute_code_string() for provided code.")

            # Step 2-6: Execute the generated code
            result = await self.execute_code_string(
                code=code,
                language=language,
                options=options
            )

            # Update statistics
            execution_time = time.time() - start_time
            self._stats["total_execution_time"] += execution_time

            if result.success:
                self._stats["successful_executions"] += 1
                logger.info(f"Task execution completed successfully in {execution_time:.2f}s")
            else:
                self._stats["failed_executions"] += 1
                logger.warning(f"Task execution failed after {execution_time:.2f}s")

            return result

        except UserRejectionError:
            self._stats["user_rejections"] += 1
            self._stats["failed_executions"] += 1
            raise
        except CodeGenerationError:
            self._stats["failed_executions"] += 1
            raise
        except Exception as e:
            self._stats["failed_executions"] += 1
            logger.error(f"Task execution error: {str(e)}")
            raise ExecutionError(f"Task execution failed: {str(e)}") from e

    async def execute_code_string(
        self,
        code: str,
        language: str = "python",
        options: Optional[ExecutionOptions] = None
    ) -> ExecutionResult:
        """
        Execute provided code string.

        This method executes code provided directly by the user or caller,
        skipping the generation step but performing all validation steps
        before execution.

        Pipeline:
        1. Validate syntax (if options.validate_syntax)
        2. Check security (if options.check_security)
        3. Assess quality (if options.assess_quality)
        4. Request user approval (if options.require_approval)
        5. Execute in sandbox
        6. Handle failures with retry logic

        Args:
            code: Source code to execute
            language: Programming language (python, javascript, bash)
            options: Execution options (uses defaults if not provided)

        Returns:
            ExecutionResult with output and execution details

        Raises:
            UserRejectionError: If user rejects code execution
            ExecutionError: If execution fails after retries

        Example:
            >>> result = await executor.execute_code_string(
            ...     code="print('Hello, World!')",
            ...     language="python"
            ... )
        """
        if options is None:
            options = ExecutionOptions(generate_code=False)

        logger.info(f"Executing provided {language} code ({len(code)} chars)")

        start_time = time.time()
        self._stats["total_executions"] += 1

        retry_count = 0
        last_error = None
        current_code = code

        while retry_count <= options.max_retries:
            try:
                # Step 2: Validate syntax
                if options.validate_syntax:
                    logger.info("Step 2: Validating syntax")
                    validation_result = self.validator.validate_syntax(current_code, language)

                    if not validation_result.is_valid:
                        self._stats["syntax_errors"] += 1
                        error_msg = f"Syntax validation failed:\n{validation_result}"

                        if retry_count < options.max_retries and options.generate_code:
                            # Try to refine the code
                            logger.warning(f"Syntax error on attempt {retry_count + 1}, refining code...")
                            current_code = await self._refine_code_on_error(
                                code=current_code,
                                error=validation_result.errors[0] if validation_result.errors else "Syntax error",
                                language=language
                            )
                            retry_count += 1
                            continue
                        else:
                            # No retries left or refinement not allowed
                            raise ExecutionError(error_msg)

                    logger.info("Syntax validation passed")

                # Step 3: Check security
                security_report = None
                if options.check_security:
                    logger.info("Step 3: Checking security")
                    security_report = self.validator.check_security(current_code, language)

                    if not security_report.is_safe:
                        logger.warning(f"Security check detected risk level: {security_report.risk_level}")

                        # High risk code requires explicit approval or blocks execution
                        if security_report.risk_level == "high" and not options.require_approval:
                            self._stats["security_blocks"] += 1
                            raise ExecutionError(
                                f"High-risk code detected and approval is disabled:\n{security_report}"
                            )

                    logger.info(f"Security check completed: {security_report.risk_level} risk")

                # Step 4: Assess quality (optional)
                quality_report = None
                if options.assess_quality:
                    logger.info("Step 4: Assessing code quality")
                    quality_report = self.validator.assess_quality(current_code, language)
                    logger.info(f"Quality score: {quality_report.score:.2f}")

                # Step 5: Request user approval
                if options.require_approval:
                    logger.info("Step 5: Requesting user approval")
                    approved = self._request_user_approval(
                        code=current_code,
                        language=language,
                        security_report=security_report,
                        quality_report=quality_report
                    )

                    if not approved:
                        self._stats["user_rejections"] += 1
                        raise UserRejectionError("User rejected code execution")

                    logger.info("User approved execution")

                # Step 6: Execute in sandbox
                logger.info("Step 6: Executing in sandbox")
                result = await self._execute_in_sandbox(
                    code=current_code,
                    language=language,
                    timeout=options.timeout,
                    allow_network=options.allow_network
                )

                if not result.success:
                    self._stats["execution_errors"] += 1

                    # Handle execution failure with retry
                    if retry_count < options.max_retries and options.generate_code:
                        logger.warning(f"Execution failed on attempt {retry_count + 1}, refining code...")
                        error_feedback = self._build_error_feedback(result)
                        current_code = await self._refine_code_on_error(
                            code=current_code,
                            error=error_feedback,
                            language=language
                        )
                        retry_count += 1
                        continue
                    else:
                        # No retries left
                        self._stats["failed_executions"] += 1
                        logger.error(f"Execution failed after {retry_count + 1} attempts")
                        return result

                # Success!
                logger.info("Execution completed successfully")
                self._stats["successful_executions"] += 1
                execution_time = time.time() - start_time
                self._stats["total_execution_time"] += execution_time
                return result

            except (UserRejectionError, ExecutionError):
                # Don't retry on user rejection or final execution errors
                raise
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {retry_count + 1}: {str(e)}")

                if retry_count < options.max_retries:
                    retry_count += 1
                    continue
                else:
                    raise ExecutionError(f"Execution failed after {retry_count + 1} attempts: {str(e)}") from e

        # Should not reach here, but handle gracefully
        raise ExecutionError(f"Execution failed after maximum retries: {last_error}")

    async def _generate_code_with_retry(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]],
        max_retries: int
    ) -> GeneratedCode:
        """
        Generate code with retry logic.

        Args:
            task: Task description
            language: Programming language
            context: Optional context
            max_retries: Maximum retry attempts

        Returns:
            GeneratedCode object

        Raises:
            CodeGenerationError: If generation fails after retries
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                self._stats["code_generation_attempts"] += 1
                logger.info(f"Code generation attempt {attempt + 1}/{max_retries + 1}")

                generated = await self.generator.generate_code(
                    task=task,
                    language=language,
                    context=context
                )

                logger.info(f"Code generated successfully on attempt {attempt + 1}")
                return generated

            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries:
                    logger.info(f"Retrying code generation... ({attempt + 1}/{max_retries})")
                    continue

        # All retries exhausted
        raise CodeGenerationError(
            f"Code generation failed after {max_retries + 1} attempts: {last_error}"
        )

    async def _refine_code_on_error(
        self,
        code: str,
        error: str,
        language: str
    ) -> str:
        """
        Refine code based on error feedback.

        Args:
            code: Original code
            error: Error message or feedback
            language: Programming language

        Returns:
            Refined code string

        Raises:
            CodeGenerationError: If refinement fails
        """
        self._stats["refinement_attempts"] += 1
        logger.info("Refining code based on error feedback")

        try:
            refined = await self.generator.refine_code(
                code=code,
                feedback=error,
                language=language
            )
            logger.info("Code refined successfully")
            return refined.code
        except Exception as e:
            logger.error(f"Code refinement failed: {str(e)}")
            raise CodeGenerationError(f"Failed to refine code: {str(e)}") from e

    async def _execute_in_sandbox(
        self,
        code: str,
        language: str,
        timeout: int,
        allow_network: bool
    ) -> ExecutionResult:
        """
        Execute code in sandboxed environment.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Execution timeout in seconds
            allow_network: Whether to allow network access

        Returns:
            ExecutionResult with output and status
        """
        logger.info(f"Creating sandbox for {language} execution")

        try:
            # Create sandbox configuration
            from .languages import get_handler
            handler = get_handler(language)
            lang_config = handler.get_execution_config()

            sandbox_config = SandboxConfig(
                language=language,
                docker_image=lang_config["docker_image"],
                timeout=timeout,
                network_mode="bridge" if allow_network else "none",
                memory="256m",
                cpu_quota=50000
            )

            # Create container
            container_id = self.sandbox.create_container(language, code, sandbox_config)

            try:
                # Execute code
                result = self.sandbox.execute_code(container_id, timeout=timeout)
                return result
            finally:
                # Always cleanup container
                self.sandbox.cleanup_container(container_id)

        except Exception as e:
            logger.error(f"Sandbox execution error: {str(e)}")
            return ExecutionResult(
                success=False,
                error_message=f"Sandbox execution failed: {str(e)}",
                stderr=str(e)
            )

    def _request_user_approval(
        self,
        code: str,
        language: str,
        security_report: Optional[SecurityReport],
        quality_report: Optional[QualityReport]
    ) -> bool:
        """
        Request user approval for code execution.

        This method displays the code, security analysis, and quality metrics
        to the user and asks for approval before execution.

        Args:
            code: Code to display
            language: Programming language
            security_report: Security analysis (if available)
            quality_report: Quality assessment (if available)

        Returns:
            True if user approves, False if user rejects
        """
        print("\n" + "=" * 80)
        print("CODE EXECUTION APPROVAL REQUIRED")
        print("=" * 80)

        # Display code
        print(f"\nGenerated {language.upper()} Code:")
        print("-" * 80)
        self._print_code_with_line_numbers(code)
        print("-" * 80)

        # Display security report
        if security_report:
            print(f"\nSecurity Analysis:")
            print("-" * 80)
            print(security_report)
            print("-" * 80)

        # Display quality report
        if quality_report:
            print(f"\nQuality Assessment:")
            print("-" * 80)
            print(quality_report)
            print("-" * 80)

        # Request approval
        print("\n" + "=" * 80)

        while True:
            try:
                response = input("Execute this code? [y/N]: ").strip().lower()

                if response in ['y', 'yes']:
                    print("✓ Execution approved by user")
                    return True
                elif response in ['n', 'no', '']:
                    print("✗ Execution rejected by user")
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except (EOFError, KeyboardInterrupt):
                print("\n✗ Execution cancelled by user")
                return False

    def _print_code_with_line_numbers(self, code: str) -> None:
        """
        Print code with line numbers for better readability.

        Args:
            code: Code to print
        """
        lines = code.split('\n')
        max_line_num_width = len(str(len(lines)))

        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_line_num_width)
            print(f"{line_num} | {line}")

    def _build_error_feedback(self, result: ExecutionResult) -> str:
        """
        Build error feedback message from execution result.

        Args:
            result: ExecutionResult with error information

        Returns:
            Formatted error feedback string
        """
        feedback_parts = []

        if result.error_message:
            feedback_parts.append(f"Error: {result.error_message}")

        if result.stderr:
            feedback_parts.append(f"Standard Error:\n{result.stderr}")

        if result.timed_out:
            feedback_parts.append("Execution timed out - code may have infinite loop or be too slow")

        if result.exit_code != 0:
            feedback_parts.append(f"Exit code: {result.exit_code}")

        return "\n\n".join(feedback_parts) if feedback_parts else "Execution failed with unknown error"

    def handle_execution_failure(
        self,
        error: Exception,
        retry: int,
        context: Dict[str, Any]
    ) -> Optional[ExecutionResult]:
        """
        Handle execution failure with contextual information.

        This method provides a hook for custom failure handling logic.
        It can be overridden by subclasses to implement custom retry
        or error recovery strategies.

        Args:
            error: Exception that caused the failure
            retry: Current retry attempt number
            context: Context information (code, language, options, etc.)

        Returns:
            Optional ExecutionResult if recovery is possible, None otherwise

        Example:
            Override this method to implement custom failure handling:

            >>> class CustomExecutor(CodeExecutor):
            ...     def handle_execution_failure(self, error, retry, context):
            ...         # Custom logic here
            ...         return None
        """
        logger.warning(
            f"Handling execution failure (attempt {retry + 1}): {str(error)}"
        )

        # Log context for debugging
        logger.debug(f"Failure context: {context}")

        # Default behavior: return None (no recovery)
        # Subclasses can override to implement custom recovery
        return None

    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns a dictionary containing various execution metrics including:
        - Total executions
        - Successful vs failed executions
        - Average execution time
        - Code generation and refinement attempts
        - Error counts by type

        Returns:
            Dictionary with execution statistics

        Example:
            >>> stats = executor.get_execution_statistics()
            >>> print(f"Success rate: {stats['success_rate']}%")
            >>> print(f"Average time: {stats['avg_execution_time']:.2f}s")
        """
        total = self._stats["total_executions"]
        successful = self._stats["successful_executions"]

        # Calculate derived metrics
        success_rate = (successful / total * 100) if total > 0 else 0.0
        avg_execution_time = (
            self._stats["total_execution_time"] / total
        ) if total > 0 else 0.0

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": self._stats["failed_executions"],
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 2),
            "code_generation_attempts": self._stats["code_generation_attempts"],
            "refinement_attempts": self._stats["refinement_attempts"],
            "user_rejections": self._stats["user_rejections"],
            "security_blocks": self._stats["security_blocks"],
            "syntax_errors": self._stats["syntax_errors"],
            "execution_errors": self._stats["execution_errors"],
        }

    def reset_statistics(self) -> None:
        """
        Reset all execution statistics.

        This is useful for testing or when starting a new execution session.
        """
        logger.info("Resetting execution statistics")
        for key in self._stats:
            self._stats[key] = 0

    def __repr__(self) -> str:
        """String representation of executor."""
        stats = self.get_execution_statistics()
        return (
            f"CodeExecutor("
            f"executions={stats['total_executions']}, "
            f"success_rate={stats['success_rate']}%)"
        )
