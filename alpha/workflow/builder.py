"""
Workflow Builder Module

Creates workflow definitions from natural language, interactive prompts,
or task history.
"""

from typing import List, Dict, Any, Optional
import uuid

from .definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParameter,
    WorkflowTrigger,
    ParameterType,
    TriggerType,
    StepErrorStrategy,
    RetryConfig,
)


class WorkflowBuilder:
    """
    Workflow builder

    Creates workflow definitions from various sources:
    - Natural language descriptions
    - Interactive CLI prompts
    - Manual YAML/JSON definitions
    - Task execution history
    """

    def __init__(self):
        """Initialize workflow builder"""
        pass

    def build(
        self,
        name: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        triggers: Optional[List[Dict[str, Any]]] = None,
        version: str = "1.0.0",
        author: str = "user",
        tags: Optional[List[str]] = None,
    ) -> WorkflowDefinition:
        """
        Build workflow from components

        Args:
            name: Workflow name
            description: Workflow description
            steps: List of step definitions
            parameters: List of parameter definitions
            triggers: List of trigger definitions
            version: Workflow version
            author: Workflow author
            tags: Workflow tags

        Returns:
            WorkflowDefinition
        """
        # Convert steps
        workflow_steps = []
        if steps:
            for step_data in steps:
                workflow_steps.append(self._build_step(step_data))

        # Convert parameters
        workflow_params = []
        if parameters:
            for param_data in parameters:
                workflow_params.append(self._build_parameter(param_data))

        # Convert triggers
        workflow_triggers = []
        if triggers:
            for trigger_data in triggers:
                workflow_triggers.append(self._build_trigger(trigger_data))

        return WorkflowDefinition(
            name=name,
            version=version,
            description=description,
            author=author,
            tags=tags or [],
            parameters=workflow_params,
            triggers=workflow_triggers,
            steps=workflow_steps,
        )

    def build_from_tasks(
        self,
        name: str,
        task_history: List[Dict[str, Any]],
        description: str = "",
        version: str = "1.0.0",
    ) -> WorkflowDefinition:
        """
        Build workflow from task execution history

        Analyzes task history to extract common patterns and create
        a reusable workflow.

        Args:
            name: Workflow name
            task_history: List of task execution records
            description: Workflow description
            version: Workflow version

        Returns:
            WorkflowDefinition
        """
        # Extract steps from task history
        steps = []
        parameters = []
        param_values = {}

        for i, task in enumerate(task_history):
            # Create step from task
            step_id = f"step_{i + 1}"
            tool = task.get("tool", "unknown")
            action = task.get("action", "execute")
            task_params = task.get("parameters", {})

            # Identify potential parameters (values that might vary)
            step_params = {}
            for key, value in task_params.items():
                if self._is_parameterizable(value):
                    # Create parameter
                    param_name = f"{key}_{i + 1}"
                    param_values[param_name] = value

                    # Add to parameters if not already present
                    if not any(p["name"] == param_name for p in parameters):
                        parameters.append(
                            {
                                "name": param_name,
                                "type": self._infer_type(value),
                                "default": value,
                                "description": f"Parameter for {key} in {tool}",
                            }
                        )

                    step_params[key] = f"{{{{{param_name}}}}}"
                else:
                    step_params[key] = value

            steps.append(
                {
                    "id": step_id,
                    "tool": tool,
                    "action": action,
                    "parameters": step_params,
                    "on_error": "abort",
                }
            )

        return self.build(
            name=name,
            description=description or f"Workflow created from {len(task_history)} tasks",
            steps=steps,
            parameters=parameters,
            version=version,
            tags=["auto-generated"],
        )

    def build_simple(
        self,
        name: str,
        tool_actions: List[tuple],
        description: str = "",
    ) -> WorkflowDefinition:
        """
        Build simple workflow from tool-action pairs

        Args:
            name: Workflow name
            tool_actions: List of (tool, action, parameters) tuples
            description: Workflow description

        Returns:
            WorkflowDefinition
        """
        steps = []

        for i, (tool, action, params) in enumerate(tool_actions):
            steps.append(
                {
                    "id": f"step_{i + 1}",
                    "tool": tool,
                    "action": action,
                    "parameters": params or {},
                    "on_error": "abort",
                }
            )

        return self.build(
            name=name,
            description=description or f"Simple workflow with {len(steps)} steps",
            steps=steps,
        )

    def _build_step(self, step_data: Dict[str, Any]) -> WorkflowStep:
        """Build WorkflowStep from dictionary"""
        retry = None
        if "retry" in step_data:
            retry = RetryConfig(**step_data["retry"])

        return WorkflowStep(
            id=step_data["id"],
            tool=step_data["tool"],
            action=step_data["action"],
            parameters=step_data.get("parameters", {}),
            on_error=StepErrorStrategy(step_data.get("on_error", "abort")),
            retry=retry,
            depends_on=step_data.get("depends_on", []),
            condition=step_data.get("condition"),
            fallback_step=step_data.get("fallback_step"),
        )

    def _build_parameter(self, param_data: Dict[str, Any]) -> WorkflowParameter:
        """Build WorkflowParameter from dictionary"""
        param_type = param_data.get("type", "string")
        if isinstance(param_type, str):
            param_type = ParameterType(param_type)

        return WorkflowParameter(
            name=param_data["name"],
            type=param_type,
            default=param_data.get("default"),
            description=param_data.get("description", ""),
            required=param_data.get("required", False),
        )

    def _build_trigger(self, trigger_data: Dict[str, Any]) -> WorkflowTrigger:
        """Build WorkflowTrigger from dictionary"""
        trigger_type = trigger_data.get("type", "manual")
        if isinstance(trigger_type, str):
            trigger_type = TriggerType(trigger_type)

        return WorkflowTrigger(
            type=trigger_type, config=trigger_data.get("config", {})
        )

    def _is_parameterizable(self, value: Any) -> bool:
        """Check if value should be parameterized"""
        # Simple heuristic - parameterize strings and numbers
        # but not very short strings (likely constants)
        if isinstance(value, str):
            return len(value) > 3 and not value.startswith("{{")
        return isinstance(value, (int, float))

    def _infer_type(self, value: Any) -> str:
        """Infer parameter type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, dict):
            return "dict"
        else:
            return "string"


class InteractiveWorkflowBuilder:
    """
    Interactive workflow builder for CLI

    Guides user through workflow creation with prompts.
    """

    def __init__(self, workflow_builder: Optional[WorkflowBuilder] = None):
        """Initialize interactive builder"""
        self.builder = workflow_builder or WorkflowBuilder()

    def build_interactive(self) -> WorkflowDefinition:
        """
        Build workflow interactively through CLI prompts

        Returns:
            WorkflowDefinition

        Note: This is a mock implementation. In real system,
        would use input() prompts.
        """
        print("Interactive workflow creation")
        print("=" * 50)

        # Get basic info
        name = input("Workflow name: ").strip()
        description = input("Description: ").strip()
        tags = input("Tags (comma-separated): ").strip().split(",")
        tags = [t.strip() for t in tags if t.strip()]

        # Collect steps
        steps = []
        step_count = 1

        while True:
            print(f"\nStep {step_count}:")
            tool = input("  Tool name: ").strip()
            if not tool:
                break

            action = input("  Action: ").strip()
            on_error = input("  Error handling [abort/retry/continue]: ").strip() or "abort"

            steps.append(
                {
                    "id": f"step_{step_count}",
                    "tool": tool,
                    "action": action,
                    "parameters": {},
                    "on_error": on_error,
                }
            )

            step_count += 1

            if input("\nAdd another step? (y/n): ").strip().lower() != "y":
                break

        # Build workflow
        return self.builder.build(
            name=name, description=description, steps=steps, tags=tags
        )
