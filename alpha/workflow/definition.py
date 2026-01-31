"""
Workflow Definition Module

Defines the core data structures for workflow representation.
"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


class StepErrorStrategy(Enum):
    """Error handling strategies for workflow steps"""

    ABORT = "abort"  # Stop workflow execution immediately
    RETRY = "retry"  # Retry the step with backoff
    CONTINUE = "log_and_continue"  # Log error and continue to next step
    FALLBACK = "fallback"  # Execute fallback step


class ParameterType(Enum):
    """Supported parameter types"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


class TriggerType(Enum):
    """Workflow trigger types"""

    MANUAL = "manual"  # User-initiated
    SCHEDULE = "schedule"  # Cron-based
    EVENT = "event"  # Event-driven
    PROACTIVE = "proactive"  # Detected by proactive intelligence


@dataclass
class RetryConfig:
    """Retry configuration for steps"""

    max_attempts: int = 3
    backoff: str = "exponential"  # exponential, linear, constant
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds


@dataclass
class WorkflowParameter:
    """Workflow parameter definition"""

    name: str
    type: ParameterType
    default: Any = None
    description: str = ""
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type.value,
            "default": self.default,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowParameter":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            type=ParameterType(data["type"]),
            default=data.get("default"),
            description=data.get("description", ""),
            required=data.get("required", False),
        )


@dataclass
class WorkflowTrigger:
    """Workflow trigger definition"""

    type: TriggerType
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {"type": self.type.value, "config": self.config}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTrigger":
        """Create from dictionary"""
        return cls(type=TriggerType(data["type"]), config=data.get("config", {}))


@dataclass
class WorkflowStep:
    """Workflow step definition"""

    id: str
    tool: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    on_error: StepErrorStrategy = StepErrorStrategy.ABORT
    retry: Optional[RetryConfig] = None
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # Conditional execution expression
    fallback_step: Optional[str] = None  # ID of fallback step

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "tool": self.tool,
            "action": self.action,
            "parameters": self.parameters,
            "on_error": self.on_error.value,
        }

        if self.retry:
            result["retry"] = asdict(self.retry)

        if self.depends_on:
            result["depends_on"] = self.depends_on

        if self.condition:
            result["condition"] = self.condition

        if self.fallback_step:
            result["fallback_step"] = self.fallback_step

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create from dictionary"""
        retry_data = data.get("retry")
        retry = RetryConfig(**retry_data) if retry_data else None

        return cls(
            id=data["id"],
            tool=data["tool"],
            action=data["action"],
            parameters=data.get("parameters", {}),
            on_error=StepErrorStrategy(data.get("on_error", "abort")),
            retry=retry,
            depends_on=data.get("depends_on", []),
            condition=data.get("condition"),
            fallback_step=data.get("fallback_step"),
        )


@dataclass
class WorkflowDefinition:
    """
    Complete workflow definition

    Represents a reusable, multi-step task sequence with parameters,
    triggers, and error handling.
    """

    name: str
    version: str
    description: str = ""
    author: str = "user"
    tags: List[str] = field(default_factory=list)
    parameters: List[WorkflowParameter] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    steps: List[WorkflowStep] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "triggers": [t.to_dict() for t in self.triggers],
            "steps": [s.to_dict() for s in self.steps],
            "outputs": self.outputs,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        """Create from dictionary"""
        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", "user"),
            tags=data.get("tags", []),
            parameters=[
                WorkflowParameter.from_dict(p) for p in data.get("parameters", [])
            ],
            triggers=[
                WorkflowTrigger.from_dict(t) for t in data.get("triggers", [])
            ],
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            outputs=data.get("outputs", {}),
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_parameter(self, name: str) -> Optional[WorkflowParameter]:
        """Get parameter by name"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate workflow definition

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Validate basic fields
        if not self.name:
            errors.append("Workflow name is required")

        if not self.version:
            errors.append("Workflow version is required")

        if not self.steps:
            errors.append("Workflow must have at least one step")

        # Validate step IDs are unique
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique")

        # Validate step dependencies exist
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(
                        f"Step '{step.id}' depends on non-existent step '{dep}'"
                    )

        # Validate no circular dependencies
        if self._has_circular_dependencies():
            errors.append("Workflow has circular dependencies")

        # Validate fallback steps exist
        for step in self.steps:
            if step.fallback_step and step.fallback_step not in step_ids:
                errors.append(
                    f"Step '{step.id}' references non-existent fallback step '{step.fallback_step}'"
                )

        # Validate outputs reference valid steps
        for output_name, step_ref in self.outputs.items():
            # Parse step reference (e.g., "{{step_id.output}}")
            if step_ref.startswith("{{") and step_ref.endswith("}}"):
                ref = step_ref[2:-2]  # Remove {{ }}
                step_id = ref.split(".")[0]
                if step_id not in step_ids:
                    errors.append(
                        f"Output '{output_name}' references non-existent step '{step_id}'"
                    )

        return len(errors) == 0, errors

    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies in workflow steps"""
        # Build adjacency list
        graph = {step.id: step.depends_on for step in self.steps}

        # Track visiting and visited nodes
        visiting = set()
        visited = set()

        def has_cycle(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False

            visiting.add(node)
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    return True

        return False

    def get_independent_steps(self) -> List[List[str]]:
        """
        Get steps grouped by execution order (for parallel execution)

        Returns list of lists, where each inner list contains step IDs
        that can be executed in parallel.
        """
        # Build dependency map
        step_deps = {step.id: set(step.depends_on) for step in self.steps}
        all_steps = set(step_deps.keys())

        execution_order = []
        completed = set()

        while len(completed) < len(all_steps):
            # Find steps that can be executed now (all dependencies met)
            ready = []
            for step_id in all_steps - completed:
                if step_deps[step_id].issubset(completed):
                    ready.append(step_id)

            if not ready:
                # Should not happen if workflow is valid
                break

            execution_order.append(ready)
            completed.update(ready)

        return execution_order
