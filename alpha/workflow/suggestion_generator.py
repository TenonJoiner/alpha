"""
Workflow Suggestion Generator

Generates workflow suggestions from detected patterns and auto-creates workflows.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .pattern_detector import WorkflowPattern

logger = logging.getLogger(__name__)


@dataclass
class WorkflowSuggestion:
    """Suggestion to create a workflow."""
    suggestion_id: str
    pattern_id: str
    suggested_name: str
    description: str
    confidence: float
    priority: int  # 1-5, higher = more important
    steps: List[Dict[str, Any]]  # Auto-generated workflow steps
    parameters: Dict[str, Any]  # Detected parameters
    triggers: List[str]  # Conditions for auto-execution
    created_at: datetime
    status: str  # "pending", "approved", "rejected", "auto_created"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion_id": self.suggestion_id,
            "pattern_id": self.pattern_id,
            "suggested_name": self.suggested_name,
            "description": self.description,
            "confidence": self.confidence,
            "priority": self.priority,
            "steps": self.steps,
            "parameters": self.parameters,
            "triggers": self.triggers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "metadata": self.metadata
        }


class WorkflowSuggestionGenerator:
    """
    Generates workflow suggestions from detected patterns.

    Features:
    - Create workflow suggestions from patterns
    - Auto-generate workflow definitions
    - Detect execution opportunities for existing workflows
    - Track suggestion approval/rejection
    """

    def __init__(
        self,
        suggestion_store: Optional[Any] = None,
        workflow_library: Optional[Any] = None
    ):
        """
        Initialize suggestion generator.

        Args:
            suggestion_store: Storage for workflow suggestions
            workflow_library: Library of existing workflows
        """
        self.suggestion_store = suggestion_store
        self.workflow_library = workflow_library

    def generate_workflow_suggestions(
        self,
        patterns: List[WorkflowPattern],
        max_suggestions: int = 5
    ) -> List[WorkflowSuggestion]:
        """
        Generate workflow suggestions from patterns.

        Prioritization:
        - High frequency + high confidence → priority 5
        - Medium frequency + medium confidence → priority 3
        - Low frequency OR low confidence → priority 1

        Args:
            patterns: List of detected workflow patterns
            max_suggestions: Maximum number of suggestions to generate

        Returns:
            List of workflow suggestions, sorted by priority (DESC)
        """
        if not patterns:
            logger.info("No patterns provided for suggestion generation")
            return []

        suggestions = []

        for pattern in patterns[:max_suggestions]:
            try:
                # Generate workflow definition
                workflow_def = self.create_workflow_from_pattern(pattern)

                # Calculate priority
                priority = self._calculate_priority(pattern)

                # Generate description
                description = self._generate_description(pattern)

                # Detect triggers
                triggers = self._detect_triggers(pattern)

                # Create suggestion
                suggestion = WorkflowSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    pattern_id=pattern.pattern_id,
                    suggested_name=pattern.suggested_workflow_name,
                    description=description,
                    confidence=pattern.confidence,
                    priority=priority,
                    steps=workflow_def.get("steps", []),
                    parameters=workflow_def.get("parameters", {}),
                    triggers=triggers,
                    created_at=datetime.now(),
                    status="pending",
                    metadata={
                        "pattern_frequency": pattern.frequency,
                        "pattern_length": len(pattern.task_sequence),
                        "first_seen": pattern.first_seen.isoformat() if pattern.first_seen else None,
                        "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None
                    }
                )

                suggestions.append(suggestion)
                logger.info(f"Generated suggestion: {suggestion.suggested_name} (priority={priority}, confidence={pattern.confidence})")

            except Exception as e:
                logger.error(f"Error generating suggestion for pattern {pattern.pattern_id}: {e}")
                continue

        # Sort by priority (DESC), then confidence (DESC)
        suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)

        logger.info(f"Generated {len(suggestions)} workflow suggestions")
        return suggestions

    def create_workflow_from_pattern(
        self,
        pattern: WorkflowPattern
    ) -> Dict[str, Any]:
        """
        Auto-generate workflow definition from pattern.

        Steps:
        1. Extract task sequence
        2. Identify common parameters
        3. Generate step definitions
        4. Add error handling
        5. Create workflow schema

        Args:
            pattern: Workflow pattern

        Returns:
            Workflow definition dict with steps, parameters, metadata
        """
        steps = []
        parameters = {}

        for i, task_desc in enumerate(pattern.task_sequence):
            # Parse task description and create step
            step = self._create_step_from_task(task_desc, step_index=i)
            steps.append(step)

            # Extract parameters from task
            task_params = self._extract_parameters_from_task(task_desc)
            parameters.update(task_params)

        # Create workflow definition
        workflow_def = {
            "name": pattern.suggested_workflow_name,
            "description": f"Auto-generated from pattern {pattern.pattern_id}",
            "steps": steps,
            "parameters": parameters,
            "metadata": {
                "auto_generated": True,
                "pattern_id": pattern.pattern_id,
                "pattern_frequency": pattern.frequency,
                "pattern_confidence": pattern.confidence,
                "created_at": datetime.now().isoformat()
            }
        }

        return workflow_def

    def _create_step_from_task(
        self,
        task_description: str,
        step_index: int
    ) -> Dict[str, Any]:
        """
        Create a workflow step from a task description.

        Args:
            task_description: Normalized task description
            step_index: Index of this step in the workflow

        Returns:
            Step definition dict
        """
        # Generate step name
        step_name = f"step_{step_index + 1}"

        # Try to infer step type from task description
        step_type = self._infer_step_type(task_description)

        # Create step definition
        step = {
            "name": step_name,
            "type": step_type,
            "description": task_description,
            "config": {},
            "error_handling": {
                "retry_count": 2,
                "retry_delay": 5,
                "on_failure": "stop"
            }
        }

        return step

    def _infer_step_type(self, task_description: str) -> str:
        """
        Infer step type from task description.

        Returns one of: "command", "script", "http_request", "file_operation", "generic"
        """
        task_lower = task_description.lower()

        # Check for common patterns
        if any(word in task_lower for word in ["git", "clone", "commit", "push", "pull"]):
            return "command"
        elif any(word in task_lower for word in ["backup", "copy", "move", "delete"]):
            return "file_operation"
        elif any(word in task_lower for word in ["deploy", "build", "test", "run"]):
            return "command"
        elif any(word in task_lower for word in ["http", "api", "request", "fetch"]):
            return "http_request"
        elif any(word in task_lower for word in ["script", "python", "bash"]):
            return "script"
        else:
            return "generic"

    def _extract_parameters_from_task(
        self,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Extract parameters from task description.

        Looks for tokens (DATETOKEN, PATHTOKEN, etc.) and creates parameters for them.

        Args:
            task_description: Task description with tokens

        Returns:
            Dict of parameter name -> parameter definition
        """
        parameters = {}

        # Check for each token type
        token_map = {
            "DATETOKEN": {"type": "string", "format": "date", "description": "Date parameter"},
            "TIMETOKEN": {"type": "string", "format": "time", "description": "Time parameter"},
            "NUMTOKEN": {"type": "integer", "description": "Numeric parameter"},
            "PATHTOKEN": {"type": "string", "format": "path", "description": "File path parameter"},
            "BRANCHTOKEN": {"type": "string", "description": "Git branch name"}
        }

        for token, param_def in token_map.items():
            if token in task_description:
                # Create parameter name from token
                param_name = token.replace("TOKEN", "").lower()
                parameters[param_name] = param_def

        return parameters

    def _calculate_priority(self, pattern: WorkflowPattern) -> int:
        """
        Calculate suggestion priority (1-5).

        Priority levels:
        - 5: High frequency (≥7) AND high confidence (≥0.85)
        - 4: High frequency OR high confidence
        - 3: Medium frequency (≥5) AND medium confidence (≥0.7)
        - 2: Medium frequency OR medium confidence
        - 1: Low frequency OR low confidence

        Args:
            pattern: Workflow pattern

        Returns:
            Priority level (1-5)
        """
        freq = pattern.frequency
        conf = pattern.confidence

        if freq >= 7 and conf >= 0.85:
            return 5
        elif freq >= 7 or conf >= 0.85:
            return 4
        elif freq >= 5 and conf >= 0.7:
            return 3
        elif freq >= 5 or conf >= 0.7:
            return 2
        else:
            return 1

    def _generate_description(self, pattern: WorkflowPattern) -> str:
        """
        Generate human-readable description for workflow suggestion.

        Args:
            pattern: Workflow pattern

        Returns:
            Description string
        """
        task_count = len(pattern.task_sequence)
        freq = pattern.frequency

        # Time period description
        time_span = (pattern.last_seen - pattern.first_seen).days if pattern.first_seen and pattern.last_seen else 0
        if time_span <= 7:
            period = "in the last week"
        elif time_span <= 30:
            period = "in the last month"
        else:
            period = f"over {time_span} days"

        # Generate description
        description = (
            f"Detected recurring workflow with {task_count} steps, "
            f"executed {freq} times {period}. "
            f"Confidence: {pattern.confidence:.0%}."
        )

        return description

    def _detect_triggers(self, pattern: WorkflowPattern) -> List[str]:
        """
        Detect potential triggers for workflow execution.

        Analyzes pattern intervals and task content to suggest triggers.

        Args:
            pattern: Workflow pattern

        Returns:
            List of trigger descriptions
        """
        triggers = []

        # Check temporal patterns
        if pattern.avg_interval:
            interval_days = pattern.avg_interval.total_seconds() / 86400

            if 0.9 <= interval_days <= 1.1:  # ~daily
                triggers.append("daily at detected time")
            elif 6.5 <= interval_days <= 7.5:  # ~weekly
                triggers.append("weekly on detected day")
            elif interval_days < 0.5:  # Multiple times per day
                triggers.append("on demand (frequent pattern)")

        # Check for contextual triggers in task descriptions
        task_text = " ".join(pattern.task_sequence).lower()

        if "git" in task_text or "deploy" in task_text:
            triggers.append("after git push")
        if "backup" in task_text:
            triggers.append("scheduled backup time")
        if "test" in task_text:
            triggers.append("before deployment")

        # Default trigger
        if not triggers:
            triggers.append("manual execution")

        return triggers

    def detect_workflow_execution_opportunities(
        self,
        current_context: Dict[str, Any]
    ) -> List[WorkflowSuggestion]:
        """
        Detect when saved workflows should be executed.

        Checks:
        - Temporal patterns (e.g., daily at 9am)
        - Contextual triggers (e.g., after git push)
        - User behavior patterns

        Args:
            current_context: Dict with keys like:
                - "time": current datetime
                - "recent_actions": list of recent user actions
                - "git_status": git repository status
                - etc.

        Returns:
            List of workflow suggestions for current context
        """
        opportunities = []

        if not self.workflow_library:
            return opportunities

        try:
            # Get all workflows
            workflows = self.workflow_library.list_workflows() if hasattr(self.workflow_library, 'list_workflows') else []

            current_time = current_context.get("time", datetime.now())
            recent_actions = current_context.get("recent_actions", [])

            for workflow in workflows:
                # Check temporal triggers
                if self._check_temporal_trigger(workflow, current_time):
                    opportunities.append(self._create_execution_suggestion(workflow, "temporal"))

                # Check contextual triggers
                elif self._check_contextual_trigger(workflow, current_context):
                    opportunities.append(self._create_execution_suggestion(workflow, "contextual"))

        except Exception as e:
            logger.error(f"Error detecting execution opportunities: {e}")

        return opportunities

    def _check_temporal_trigger(
        self,
        workflow: Any,
        current_time: datetime
    ) -> bool:
        """
        Check if workflow should be triggered based on time.

        Args:
            workflow: Workflow object
            current_time: Current datetime

        Returns:
            True if temporal trigger matches
        """
        # Placeholder - would check workflow schedule/triggers
        # In real implementation:
        # - Check if workflow has daily/weekly/monthly schedule
        # - Check if current time matches schedule
        # - Check last execution time to avoid duplicates

        return False  # Placeholder

    def _check_contextual_trigger(
        self,
        workflow: Any,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if workflow should be triggered based on context.

        Args:
            workflow: Workflow object
            context: Current context dict

        Returns:
            True if contextual trigger matches
        """
        # Placeholder - would check contextual triggers
        # In real implementation:
        # - Check if recent actions match workflow triggers
        # - Check if git status matches triggers (e.g., "after git push")
        # - Check if file changes match triggers

        return False  # Placeholder

    def _create_execution_suggestion(
        self,
        workflow: Any,
        trigger_type: str
    ) -> WorkflowSuggestion:
        """
        Create a suggestion to execute a workflow.

        Args:
            workflow: Workflow to execute
            trigger_type: Type of trigger ("temporal" or "contextual")

        Returns:
            WorkflowSuggestion for execution
        """
        # Extract workflow details
        workflow_name = getattr(workflow, 'name', 'Unknown Workflow')
        workflow_id = getattr(workflow, 'id', str(uuid.uuid4()))

        return WorkflowSuggestion(
            suggestion_id=str(uuid.uuid4()),
            pattern_id="",  # Not from pattern
            suggested_name=f"Execute: {workflow_name}",
            description=f"Workflow '{workflow_name}' is ready to run ({trigger_type} trigger)",
            confidence=0.8,
            priority=3,
            steps=[],  # Steps already in workflow
            parameters={},
            triggers=[trigger_type],
            created_at=datetime.now(),
            status="pending",
            metadata={
                "trigger_type": trigger_type,
                "workflow_id": workflow_id
            }
        )

    async def store_suggestion(self, suggestion: WorkflowSuggestion) -> bool:
        """
        Store a workflow suggestion for later review.

        Args:
            suggestion: Workflow suggestion to store

        Returns:
            True if stored successfully
        """
        if not self.suggestion_store:
            logger.warning("No suggestion store available")
            return False

        try:
            # Store suggestion (implementation depends on suggestion_store interface)
            # Placeholder: self.suggestion_store.save(suggestion.to_dict())
            logger.info(f"Stored suggestion: {suggestion.suggested_name}")
            return True

        except Exception as e:
            logger.error(f"Error storing suggestion: {e}")
            return False
