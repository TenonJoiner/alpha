"""
Workflow Executor Module

Executes workflow definitions with parameter injection, error handling,
and parallel step execution.
"""

import re
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .definition import (
    WorkflowDefinition,
    WorkflowStep,
    StepErrorStrategy,
    RetryConfig,
)


@dataclass
class ExecutionContext:
    """
    Execution context for workflow

    Maintains state during workflow execution including step outputs,
    parameters, and execution metadata.
    """

    workflow_id: str
    execution_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context (parameters or step outputs)"""
        if key in self.step_outputs:
            return self.step_outputs[key]
        return self.parameters.get(key, default)

    def set_step_output(self, step_id: str, output: Any):
        """Set output for a step"""
        self.step_outputs[step_id] = output

    def get_step_output(self, step_id: str, field: Optional[str] = None) -> Any:
        """Get output from a step"""
        if step_id not in self.step_outputs:
            return None

        output = self.step_outputs[step_id]

        if field and isinstance(output, dict):
            return output.get(field)

        return output


@dataclass
class ExecutionResult:
    """Result of workflow execution"""

    workflow_id: str
    execution_id: str
    status: str  # completed, failed, partial
    outputs: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    steps_completed: int = 0
    steps_failed: int = 0
    steps_total: int = 0


class WorkflowExecutor:
    """
    Workflow executor

    Executes workflow steps with parameter injection, error handling,
    and support for parallel execution.
    """

    def __init__(self, tool_registry=None):
        """
        Initialize executor

        Args:
            tool_registry: Optional tool registry for executing tool calls
        """
        self.tool_registry = tool_registry

    async def execute(
        self,
        workflow: WorkflowDefinition,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute workflow

        Args:
            workflow: WorkflowDefinition to execute
            parameters: Runtime parameters

        Returns:
            ExecutionResult
        """
        # Create execution context
        context = ExecutionContext(
            workflow_id=workflow.id,
            execution_id=str(uuid.uuid4()),
            parameters=parameters or {},
            started_at=datetime.now(),
            status="running",
        )

        # Validate workflow
        is_valid, errors = workflow.validate()
        if not is_valid:
            return ExecutionResult(
                workflow_id=workflow.id,
                execution_id=context.execution_id,
                status="failed",
                error=f"Invalid workflow: {', '.join(errors)}",
                started_at=context.started_at,
                completed_at=datetime.now(),
                steps_total=len(workflow.steps),
            )

        # Merge default parameters
        context.parameters = self._merge_parameters(workflow, parameters or {})

        try:
            # Get execution order (for parallel execution)
            execution_order = workflow.get_independent_steps()

            steps_completed = 0
            steps_failed = 0

            # Execute steps in order
            for step_group in execution_order:
                # Execute steps in group concurrently
                if len(step_group) == 1:
                    # Single step - execute directly
                    step = workflow.get_step(step_group[0])
                    success = await self._execute_step(step, context, workflow)
                    if success:
                        steps_completed += 1
                    else:
                        steps_failed += 1
                        # Check if we should abort
                        if step.on_error == StepErrorStrategy.ABORT:
                            break
                else:
                    # Multiple steps - execute in parallel
                    tasks = [
                        self._execute_step(workflow.get_step(step_id), context, workflow)
                        for step_id in step_group
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, Exception):
                            steps_failed += 1
                        elif result:
                            steps_completed += 1
                        else:
                            steps_failed += 1

            # Evaluate outputs
            outputs = self._evaluate_outputs(workflow.outputs, context)

            # Complete execution
            context.completed_at = datetime.now()
            context.status = "completed" if steps_failed == 0 else "partial"

            return ExecutionResult(
                workflow_id=workflow.id,
                execution_id=context.execution_id,
                status=context.status,
                outputs=outputs,
                started_at=context.started_at,
                completed_at=context.completed_at,
                steps_completed=steps_completed,
                steps_failed=steps_failed,
                steps_total=len(workflow.steps),
            )

        except Exception as e:
            return ExecutionResult(
                workflow_id=workflow.id,
                execution_id=context.execution_id,
                status="failed",
                error=str(e),
                started_at=context.started_at,
                completed_at=datetime.now(),
                steps_total=len(workflow.steps),
            )

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        workflow: WorkflowDefinition,
    ) -> bool:
        """
        Execute a single step

        Args:
            step: WorkflowStep to execute
            context: ExecutionContext
            workflow: Parent WorkflowDefinition

        Returns:
            True if successful, False otherwise
        """
        # Check condition
        if step.condition and not self._evaluate_condition(step.condition, context):
            # Skip step
            return True

        # Inject parameters
        parameters = self._inject_parameters(step.parameters, context)

        # Execute with error handling
        try:
            # Execute step (mock implementation for now)
            output = await self._execute_tool_call(step.tool, step.action, parameters)

            # Store output
            context.set_step_output(step.id, output)

            return True

        except Exception as e:
            # Handle error based on strategy
            if step.on_error == StepErrorStrategy.ABORT:
                raise

            elif step.on_error == StepErrorStrategy.RETRY:
                # Retry with backoff
                if step.retry:
                    return await self._retry_step(step, context, parameters)
                else:
                    return False

            elif step.on_error == StepErrorStrategy.CONTINUE:
                # Log and continue
                print(f"Step {step.id} failed: {e}, continuing...")
                return False

            elif step.on_error == StepErrorStrategy.FALLBACK:
                # Execute fallback step
                if step.fallback_step:
                    fallback = workflow.get_step(step.fallback_step)
                    if fallback:
                        return await self._execute_step(fallback, context, workflow)
                return False

            return False

    async def _retry_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        parameters: Dict[str, Any],
    ) -> bool:
        """
        Retry step with backoff

        Args:
            step: WorkflowStep to retry
            context: ExecutionContext
            parameters: Injected parameters

        Returns:
            True if successful, False otherwise
        """
        retry_config = step.retry or RetryConfig()

        delay = retry_config.initial_delay

        for attempt in range(retry_config.max_attempts):
            try:
                output = await self._execute_tool_call(
                    step.tool, step.action, parameters
                )
                context.set_step_output(step.id, output)
                return True

            except Exception as e:
                if attempt < retry_config.max_attempts - 1:
                    # Wait before retry
                    await asyncio.sleep(delay)

                    # Calculate next delay
                    if retry_config.backoff == "exponential":
                        delay = min(delay * 2, retry_config.max_delay)
                    elif retry_config.backoff == "linear":
                        delay = min(
                            delay + retry_config.initial_delay,
                            retry_config.max_delay,
                        )
                    # constant: delay stays the same
                else:
                    print(f"Step {step.id} failed after {retry_config.max_attempts} attempts")
                    return False

        return False

    async def _execute_tool_call(
        self, tool: str, action: str, parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute tool call

        Args:
            tool: Tool name
            action: Action name
            parameters: Action parameters

        Returns:
            Tool output
        """
        # Mock implementation - in real system, would call tool registry
        if self.tool_registry:
            # Use tool registry to execute
            tool_instance = self.tool_registry.get(tool)
            if tool_instance and hasattr(tool_instance, action):
                method = getattr(tool_instance, action)
                return await method(**parameters) if asyncio.iscoroutinefunction(method) else method(**parameters)

        # Mock response for testing
        return {
            "tool": tool,
            "action": action,
            "parameters": parameters,
            "result": "success",
        }

    def _merge_parameters(
        self, workflow: WorkflowDefinition, runtime_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge runtime parameters with defaults

        Args:
            workflow: WorkflowDefinition
            runtime_params: Runtime parameters

        Returns:
            Merged parameters
        """
        merged = {}

        # Start with defaults
        for param in workflow.parameters:
            if param.default is not None:
                merged[param.name] = param.default

        # Override with runtime parameters
        merged.update(runtime_params)

        return merged

    def _inject_parameters(
        self, template: Dict[str, Any], context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Inject parameters into template

        Replaces {{variable}} with actual values from context.

        Args:
            template: Parameter template
            context: ExecutionContext

        Returns:
            Parameters with injected values
        """
        result = {}

        for key, value in template.items():
            if isinstance(value, str):
                result[key] = self._interpolate_string(value, context)
            elif isinstance(value, dict):
                result[key] = self._inject_parameters(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._interpolate_string(item, context) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _interpolate_string(self, template: str, context: ExecutionContext) -> Any:
        """
        Interpolate string template

        Replaces {{variable}} or {{step_id.field}} with actual values.

        Args:
            template: String template
            context: ExecutionContext

        Returns:
            Interpolated value
        """
        # Pattern: {{variable}} or {{step_id.field}}
        pattern = r"\{\{([^}]+)\}\}"

        def replace(match):
            expr = match.group(1).strip()

            # Check if it's a step output reference
            if "." in expr:
                parts = expr.split(".", 1)
                step_id = parts[0]
                field = parts[1] if len(parts) > 1 else None
                value = context.get_step_output(step_id, field)
            else:
                # Check parameters or step outputs
                value = context.get(expr)

            return str(value) if value is not None else ""

        result = re.sub(pattern, replace, template)

        # If the entire string was a variable reference, return the actual type
        if template.startswith("{{") and template.endswith("}}"):
            expr = template[2:-2].strip()
            if "." in expr:
                parts = expr.split(".", 1)
                return context.get_step_output(parts[0], parts[1] if len(parts) > 1 else None)
            else:
                return context.get(expr)

        return result

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """
        Evaluate condition expression

        Args:
            condition: Condition expression
            context: ExecutionContext

        Returns:
            True if condition is met, False otherwise
        """
        # Simple condition evaluation (can be enhanced)
        # For now, just interpolate and evaluate as Python expression
        try:
            interpolated = self._interpolate_string(condition, context)
            # Note: In production, use a safe expression evaluator
            return bool(eval(interpolated))
        except Exception:
            return False

    def _evaluate_outputs(
        self, output_template: Dict[str, str], context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Evaluate workflow outputs

        Args:
            output_template: Output template
            context: ExecutionContext

        Returns:
            Evaluated outputs
        """
        outputs = {}

        for name, template in output_template.items():
            if isinstance(template, str):
                outputs[name] = self._interpolate_string(template, context)
            else:
                outputs[name] = template

        return outputs

    def execute_sync(
        self,
        workflow: WorkflowDefinition,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Synchronous wrapper for execute()

        Args:
            workflow: WorkflowDefinition to execute
            parameters: Runtime parameters

        Returns:
            ExecutionResult
        """
        return asyncio.run(self.execute(workflow, parameters))
