"""
Workflow Schema Validation Module

Provides schema validation for workflow definitions using JSON Schema.
"""

import json
from typing import Dict, Any, List, Tuple
from .definition import WorkflowDefinition


class WorkflowSchema:
    """Workflow schema validator"""

    # JSON Schema for workflow definition
    WORKFLOW_SCHEMA = {
        "type": "object",
        "required": ["name", "version", "steps"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "minLength": 1, "maxLength": 100},
            "version": {
                "type": "string",
                "pattern": r"^\d+\.\d+\.\d+$",  # Semantic versioning
            },
            "description": {"type": "string", "maxLength": 500},
            "author": {"type": "string", "maxLength": 100},
            "tags": {"type": "array", "items": {"type": "string"}},
            "parameters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": [
                                "string",
                                "integer",
                                "float",
                                "boolean",
                                "list",
                                "dict",
                            ],
                        },
                        "default": {},
                        "description": {"type": "string"},
                        "required": {"type": "boolean"},
                    },
                },
            },
            "triggers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["manual", "schedule", "event", "proactive"],
                        },
                        "config": {"type": "object"},
                    },
                },
            },
            "steps": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "tool", "action"],
                    "properties": {
                        "id": {"type": "string"},
                        "tool": {"type": "string"},
                        "action": {"type": "string"},
                        "parameters": {"type": "object"},
                        "on_error": {
                            "type": "string",
                            "enum": [
                                "abort",
                                "retry",
                                "log_and_continue",
                                "fallback",
                            ],
                        },
                        "retry": {
                            "type": "object",
                            "properties": {
                                "max_attempts": {"type": "integer", "minimum": 1},
                                "backoff": {
                                    "type": "string",
                                    "enum": ["exponential", "linear", "constant"],
                                },
                                "initial_delay": {"type": "number", "minimum": 0},
                                "max_delay": {"type": "number", "minimum": 0},
                            },
                        },
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "condition": {"type": "string"},
                        "fallback_step": {"type": "string"},
                    },
                },
            },
            "outputs": {"type": "object"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
        },
    }

    @staticmethod
    def validate_dict(workflow_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate workflow dictionary against schema

        Args:
            workflow_dict: Workflow definition as dictionary

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Basic structure validation
        if not isinstance(workflow_dict, dict):
            return False, ["Workflow definition must be a dictionary"]

        # Required fields
        required = ["name", "version", "steps"]
        for field in required:
            if field not in workflow_dict:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate name
        name = workflow_dict.get("name")
        if not name or not isinstance(name, str):
            errors.append("Workflow name must be a non-empty string")
        elif len(name) > 100:
            errors.append("Workflow name must be <= 100 characters")

        # Validate version
        version = workflow_dict.get("version")
        if not version or not isinstance(version, str):
            errors.append("Workflow version must be a non-empty string")
        else:
            # Check semantic versioning format
            parts = version.split(".")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                errors.append(
                    "Workflow version must follow semantic versioning (e.g., 1.0.0)"
                )

        # Validate steps
        steps = workflow_dict.get("steps")
        if not isinstance(steps, list):
            errors.append("Workflow steps must be a list")
        elif len(steps) == 0:
            errors.append("Workflow must have at least one step")
        else:
            # Validate each step
            step_ids = set()
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"Step {i} must be a dictionary")
                    continue

                # Required step fields
                for field in ["id", "tool", "action"]:
                    if field not in step:
                        errors.append(f"Step {i}: Missing required field '{field}'")

                step_id = step.get("id")
                if step_id:
                    if step_id in step_ids:
                        errors.append(
                            f"Step {i}: Duplicate step ID '{step_id}'"
                        )
                    step_ids.add(step_id)

                # Validate on_error
                on_error = step.get("on_error", "abort")
                if on_error not in ["abort", "retry", "log_and_continue", "fallback"]:
                    errors.append(
                        f"Step {i}: Invalid on_error value '{on_error}'"
                    )

                # Validate retry config
                if "retry" in step:
                    retry = step["retry"]
                    if not isinstance(retry, dict):
                        errors.append(f"Step {i}: retry must be a dictionary")
                    else:
                        if "max_attempts" in retry:
                            if (
                                not isinstance(retry["max_attempts"], int)
                                or retry["max_attempts"] < 1
                            ):
                                errors.append(
                                    f"Step {i}: retry.max_attempts must be >= 1"
                                )

        # Validate parameters
        if "parameters" in workflow_dict:
            params = workflow_dict["parameters"]
            if not isinstance(params, list):
                errors.append("Workflow parameters must be a list")
            else:
                param_names = set()
                for i, param in enumerate(params):
                    if not isinstance(param, dict):
                        errors.append(f"Parameter {i} must be a dictionary")
                        continue

                    if "name" not in param:
                        errors.append(f"Parameter {i}: Missing 'name' field")
                    elif param["name"] in param_names:
                        errors.append(
                            f"Parameter {i}: Duplicate parameter name '{param['name']}'"
                        )
                    else:
                        param_names.add(param["name"])

                    if "type" not in param:
                        errors.append(f"Parameter {i}: Missing 'type' field")
                    elif param["type"] not in [
                        "string",
                        "integer",
                        "float",
                        "boolean",
                        "list",
                        "dict",
                    ]:
                        errors.append(
                            f"Parameter {i}: Invalid type '{param['type']}'"
                        )

        # Validate triggers
        if "triggers" in workflow_dict:
            triggers = workflow_dict["triggers"]
            if not isinstance(triggers, list):
                errors.append("Workflow triggers must be a list")
            else:
                for i, trigger in enumerate(triggers):
                    if not isinstance(trigger, dict):
                        errors.append(f"Trigger {i} must be a dictionary")
                        continue

                    if "type" not in trigger:
                        errors.append(f"Trigger {i}: Missing 'type' field")
                    elif trigger["type"] not in [
                        "manual",
                        "schedule",
                        "event",
                        "proactive",
                    ]:
                        errors.append(
                            f"Trigger {i}: Invalid type '{trigger['type']}'"
                        )

        return len(errors) == 0, errors

    @staticmethod
    def validate_workflow(workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
        """
        Validate workflow definition object

        Args:
            workflow: WorkflowDefinition object

        Returns:
            (is_valid, error_messages)
        """
        # First validate the workflow using its own validation
        is_valid, errors = workflow.validate()

        if not is_valid:
            return False, errors

        # Then validate using schema
        workflow_dict = workflow.to_dict()
        schema_valid, schema_errors = WorkflowSchema.validate_dict(workflow_dict)

        if not schema_valid:
            errors.extend(schema_errors)

        return len(errors) == 0, errors


def validate_workflow(workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate workflow

    Args:
        workflow: WorkflowDefinition object

    Returns:
        (is_valid, error_messages)
    """
    return WorkflowSchema.validate_workflow(workflow)
