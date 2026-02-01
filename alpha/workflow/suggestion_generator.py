"""
Alpha - Workflow Suggestion Generator

Generates workflow suggestions from detected patterns and creates workflow definitions.

Features:
- Generate workflow suggestions from patterns
- Auto-create workflow definitions from task history
- Detect workflow execution opportunities
- Track suggestion approval/rejection
- Prioritize suggestions by value
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

from alpha.workflow.pattern_detector import WorkflowPattern

logger = logging.getLogger(__name__)


@dataclass
class WorkflowSuggestion:
    """Suggestion to create a workflow."""
    suggestion_id: str
    pattern_id: str
    suggested_name: str
    description: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1-5, higher = more important
    steps: List[Dict[str, Any]]  # Auto-generated workflow steps
    parameters: Dict[str, str]  # Detected parameters
    triggers: List[str]  # Conditions for auto-execution
    created_at: datetime
    status: str  # "pending", "approved", "rejected", "auto_created"
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result


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
        database_path: str,
        workflow_library=None  # Optional WorkflowLibrary instance
    ):
        """
        Initialize suggestion generator.

        Args:
            database_path: Path to database for storing suggestions
            workflow_library: Optional WorkflowLibrary for checking existing workflows
        """
        self.db_path = database_path
        self.workflow_library = workflow_library
        self._init_database()

    def _init_database(self):
        """Initialize database tables for suggestions."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            pass

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_suggestions (
                    suggestion_id TEXT PRIMARY KEY,
                    pattern_id TEXT,
                    suggested_name TEXT,
                    description TEXT,
                    confidence REAL,
                    priority INTEGER,
                    steps TEXT,  -- JSON
                    parameters TEXT,  -- JSON
                    triggers TEXT,  -- JSON
                    created_at TEXT,
                    status TEXT,
                    metadata TEXT  -- JSON
                )
            """)

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize suggestion database: {e}")

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
            patterns: List of detected patterns
            max_suggestions: Maximum suggestions to return

        Returns:
            List of suggestions sorted by priority (high to low)
        """
        if not patterns:
            return []

        logger.info(f"Generating workflow suggestions from {len(patterns)} patterns")

        suggestions = []
        for pattern in patterns:
            # Skip if workflow already exists with this pattern
            if self._workflow_exists_for_pattern(pattern):
                logger.info(f"Skipping pattern {pattern.pattern_id} - workflow already exists")
                continue

            # Create suggestion
            suggestion = self._create_suggestion_from_pattern(pattern)
            suggestions.append(suggestion)

        # Sort by priority (desc) then confidence (desc)
        suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)

        # Limit to max_suggestions
        suggestions = suggestions[:max_suggestions]

        # Store suggestions
        for suggestion in suggestions:
            self._store_suggestion(suggestion)

        logger.info(f"Generated {len(suggestions)} workflow suggestions")
        return suggestions

    def _create_suggestion_from_pattern(
        self,
        pattern: WorkflowPattern
    ) -> WorkflowSuggestion:
        """
        Create a workflow suggestion from a pattern.

        Generates:
        - Suggested workflow name
        - Description
        - Priority based on frequency and confidence
        - Workflow steps
        - Parameters
        - Triggers
        """
        # Calculate priority (1-5)
        priority = self._calculate_priority(pattern)

        # Generate workflow steps
        steps = self._generate_workflow_steps(pattern)

        # Extract parameters
        parameters = self._extract_parameters(pattern)

        # Generate triggers
        triggers = self._generate_triggers(pattern)

        # Create description
        description = self._generate_description(pattern)

        suggestion = WorkflowSuggestion(
            suggestion_id=str(uuid.uuid4()),
            pattern_id=pattern.pattern_id,
            suggested_name=pattern.suggested_workflow_name,
            description=description,
            confidence=pattern.confidence,
            priority=priority,
            steps=steps,
            parameters=parameters,
            triggers=triggers,
            created_at=datetime.now(),
            status="pending",
            metadata={
                'pattern_frequency': pattern.frequency,
                'pattern_task_count': len(pattern.task_sequence),
                'pattern_avg_interval_days': pattern.avg_interval.days
            }
        )

        return suggestion

    def _calculate_priority(self, pattern: WorkflowPattern) -> int:
        """
        Calculate priority score 1-5.

        Factors:
        - Frequency: More = higher
        - Confidence: Higher = higher
        - Recency: Recent = higher
        """
        score = 0.0

        # Frequency factor (0-2 points)
        if pattern.frequency >= 10:
            score += 2.0
        elif pattern.frequency >= 5:
            score += 1.5
        elif pattern.frequency >= 3:
            score += 1.0

        # Confidence factor (0-2 points)
        score += pattern.confidence * 2.0

        # Recency factor (0-1 point)
        days_since_last = (datetime.now() - pattern.last_seen).days
        if days_since_last <= 3:
            score += 1.0
        elif days_since_last <= 7:
            score += 0.5

        # Convert to 1-5 scale
        priority = max(1, min(5, int(score + 0.5)))
        return priority

    def _generate_workflow_steps(
        self,
        pattern: WorkflowPattern
    ) -> List[Dict[str, Any]]:
        """
        Generate workflow step definitions from pattern.

        Each step:
        - action: normalized task description
        - on_error: "retry" (default)
        - depends_on: [] (sequential by default)
        """
        steps = []

        for i, task_desc in enumerate(pattern.task_sequence):
            step = {
                'name': f'Step {i+1}: {task_desc.capitalize()}',
                'action': task_desc,
                'on_error': 'retry',
                'depends_on': [i-1] if i > 0 else [],
                'metadata': {
                    'auto_generated': True,
                    'pattern_id': pattern.pattern_id
                }
            }
            steps.append(step)

        return steps

    def _extract_parameters(
        self,
        pattern: WorkflowPattern
    ) -> Dict[str, str]:
        """
        Extract potential parameters from pattern.

        Looks for:
        - Branch names (git patterns)
        - Environments (deploy patterns)
        - File paths
        - Common variables
        """
        parameters = {}

        # Analyze task sequence for common parameter patterns
        task_text = ' '.join(pattern.task_sequence).lower()

        # Git branch parameters
        if 'git' in task_text or 'branch' in task_text:
            parameters['branch'] = 'main'

        # Deployment environment
        if 'deploy' in task_text or 'staging' in task_text or 'production' in task_text:
            parameters['environment'] = 'staging'

        # Test parameters
        if 'test' in task_text:
            parameters['test_path'] = 'tests/'

        return parameters

    def _generate_triggers(
        self,
        pattern: WorkflowPattern
    ) -> List[str]:
        """
        Generate trigger conditions for workflow.

        Based on:
        - Temporal patterns (daily, weekly)
        - Contextual triggers (after certain events)
        """
        triggers = []

        # Temporal triggers
        if pattern.avg_interval.days == 1:
            triggers.append("schedule: daily at 9:00 AM")
        elif pattern.avg_interval.days == 7:
            triggers.append("schedule: weekly on Monday at 9:00 AM")

        # Event-based triggers (basic heuristics)
        task_text = ' '.join(pattern.task_sequence).lower()

        if 'git pull' in task_text:
            triggers.append("event: after morning startup")

        if 'backup' in task_text:
            triggers.append("event: end of day")

        return triggers

    def _generate_description(self, pattern: WorkflowPattern) -> str:
        """Generate human-readable description of the workflow."""
        tasks = pattern.task_sequence
        frequency = pattern.frequency

        if len(tasks) == 2:
            desc = f"Automate {tasks[0]} followed by {tasks[1]}."
        elif len(tasks) == 3:
            desc = f"Automate {tasks[0]}, {tasks[1]}, and {tasks[2]}."
        else:
            desc = f"Automate {len(tasks)}-step process: {tasks[0]} → ... → {tasks[-1]}."

        desc += f" Detected {frequency} times in recent history."

        return desc

    def _workflow_exists_for_pattern(self, pattern: WorkflowPattern) -> bool:
        """
        Check if a workflow already exists for this pattern.

        Uses workflow library if available.
        """
        if not self.workflow_library:
            return False

        # Check by workflow name similarity
        try:
            workflows = self.workflow_library.list_workflows()
            for workflow in workflows:
                if workflow.name.lower() == pattern.suggested_workflow_name.lower():
                    return True
        except Exception as e:
            logger.warning(f"Error checking existing workflows: {e}")

        return False

    def _store_suggestion(self, suggestion: WorkflowSuggestion):
        """Store suggestion in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO workflow_suggestions
                (suggestion_id, pattern_id, suggested_name, description, confidence,
                 priority, steps, parameters, triggers, created_at, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.suggestion_id,
                suggestion.pattern_id,
                suggestion.suggested_name,
                suggestion.description,
                suggestion.confidence,
                suggestion.priority,
                json.dumps(suggestion.steps),
                json.dumps(suggestion.parameters),
                json.dumps(suggestion.triggers),
                suggestion.created_at.isoformat(),
                suggestion.status,
                json.dumps(suggestion.metadata)
            ))

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to store suggestion: {e}")

    def get_pending_suggestions(self, limit: int = 10) -> List[WorkflowSuggestion]:
        """
        Get pending workflow suggestions.

        Args:
            limit: Maximum suggestions to return

        Returns:
            List of pending suggestions sorted by priority
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM workflow_suggestions
                WHERE status = 'pending'
                ORDER BY priority DESC, confidence DESC
                LIMIT ?
            """, (limit,))

            suggestions = []
            for row in cursor.fetchall():
                suggestion = WorkflowSuggestion(
                    suggestion_id=row['suggestion_id'],
                    pattern_id=row['pattern_id'],
                    suggested_name=row['suggested_name'],
                    description=row['description'],
                    confidence=row['confidence'],
                    priority=row['priority'],
                    steps=json.loads(row['steps']),
                    parameters=json.loads(row['parameters']),
                    triggers=json.loads(row['triggers']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    status=row['status'],
                    metadata=json.loads(row['metadata'])
                )
                suggestions.append(suggestion)

            conn.close()
            return suggestions

        except sqlite3.Error as e:
            logger.error(f"Failed to get pending suggestions: {e}")
            return []

    def approve_suggestion(self, suggestion_id: str) -> bool:
        """
        Approve a suggestion and mark for workflow creation.

        Args:
            suggestion_id: Suggestion ID to approve

        Returns:
            True if successful
        """
        return self._update_suggestion_status(suggestion_id, "approved")

    def reject_suggestion(self, suggestion_id: str) -> bool:
        """
        Reject a suggestion.

        Args:
            suggestion_id: Suggestion ID to reject

        Returns:
            True if successful
        """
        return self._update_suggestion_status(suggestion_id, "rejected")

    def _update_suggestion_status(self, suggestion_id: str, status: str) -> bool:
        """Update suggestion status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE workflow_suggestions
                SET status = ?
                WHERE suggestion_id = ?
            """, (status, suggestion_id))

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to update suggestion status: {e}")
            return False

    def create_workflow_from_suggestion(
        self,
        suggestion: WorkflowSuggestion
    ) -> Optional[Dict[str, Any]]:
        """
        Create workflow definition from suggestion.

        Returns workflow definition compatible with WorkflowLibrary.
        """
        workflow_def = {
            'name': suggestion.suggested_name,
            'description': suggestion.description,
            'version': '1.0.0',
            'tags': ['auto-generated', 'proactive'],
            'parameters': suggestion.parameters,
            'steps': suggestion.steps,
            'metadata': {
                'generated_from_pattern': suggestion.pattern_id,
                'generated_at': datetime.now().isoformat(),
                'confidence': suggestion.confidence,
                'priority': suggestion.priority
            }
        }

        return workflow_def

    def get_suggestion_by_id(self, suggestion_id: str) -> Optional[WorkflowSuggestion]:
        """Get suggestion by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM workflow_suggestions
                WHERE suggestion_id = ?
            """, (suggestion_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return WorkflowSuggestion(
                suggestion_id=row['suggestion_id'],
                pattern_id=row['pattern_id'],
                suggested_name=row['suggested_name'],
                description=row['description'],
                confidence=row['confidence'],
                priority=row['priority'],
                steps=json.loads(row['steps']),
                parameters=json.loads(row['parameters']),
                triggers=json.loads(row['triggers']),
                created_at=datetime.fromisoformat(row['created_at']),
                status=row['status'],
                metadata=json.loads(row['metadata'])
            )

        except sqlite3.Error as e:
            logger.error(f"Failed to get suggestion: {e}")
            return None
