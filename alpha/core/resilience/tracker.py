"""
Progress Tracker Component

Tracks progress across attempts and maintains state for resilient execution.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Attempt:
    """
    Record of a single execution attempt.

    Attributes:
        timestamp: When attempt was made
        strategy_name: Strategy/approach used
        success: Whether attempt succeeded
        error: Error if failed
        duration: Execution time in seconds
        metadata: Additional context
    """
    timestamp: datetime
    strategy_name: str
    success: bool
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class TaskState:
    """
    Current state of a task.

    Attributes:
        task_id: Unique task identifier
        operation_name: Operation being performed
        status: Current status (pending, running, completed, failed)
        attempts: List of all attempts
        started_at: When task started
        completed_at: When task completed (if finished)
        result: Result value (if successful)
        total_cost: Total API cost incurred
    """
    task_id: str
    operation_name: str
    status: str = "pending"  # pending, running, completed, failed
    attempts: List[Attempt] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    total_cost: float = 0.0


class ProgressTracker:
    """
    Tracks execution progress and maintains state across attempts.

    Features:
    - Attempt history (what was tried, when, result)
    - State persistence (resume after interruption)
    - Success metrics (track what works)
    - Resource consumption (API costs, time spent)

    Usage:
        tracker = ProgressTracker()

        # Start tracking task
        task_id = tracker.start_task("fetch_data", operation="http_request")

        # Record attempt
        tracker.record_attempt(
            task_id=task_id,
            strategy_name="primary_api",
            success=False,
            error="Connection timeout",
            duration=5.2
        )

        # Get progress
        state = tracker.get_state(task_id)
        print(f"Attempts so far: {len(state.attempts)}")
    """

    def __init__(self):
        """Initialize progress tracker"""
        self.tasks: Dict[str, TaskState] = {}
        self._next_id = 1

        logger.info("ProgressTracker initialized")

    def start_task(
        self,
        task_id: Optional[str] = None,
        operation: str = "unknown"
    ) -> str:
        """
        Start tracking a new task.

        Args:
            task_id: Optional task identifier (auto-generated if not provided)
            operation: Operation name

        Returns:
            Task ID
        """
        if task_id is None:
            task_id = f"task_{self._next_id}"
            self._next_id += 1

        state = TaskState(
            task_id=task_id,
            operation_name=operation,
            status="running",
            started_at=datetime.now()
        )

        self.tasks[task_id] = state

        logger.info(f"Started tracking task: {task_id} (operation: {operation})")

        return task_id

    def record_attempt(
        self,
        task_id: str,
        strategy_name: str,
        success: bool,
        error: Optional[str] = None,
        duration: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        """
        Record an execution attempt.

        Args:
            task_id: Task identifier
            strategy_name: Strategy/approach used
            success: Whether attempt succeeded
            error: Error message if failed
            duration: Execution time
            metadata: Additional context
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}, creating new")
            self.start_task(task_id)

        attempt = Attempt(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            success=success,
            error=error,
            duration=duration,
            metadata=metadata or {}
        )

        self.tasks[task_id].attempts.append(attempt)

        logger.debug(
            f"Recorded attempt for {task_id}: {strategy_name} "
            f"({'success' if success else 'failed'})"
        )

    def complete_task(
        self,
        task_id: str,
        success: bool,
        result: Optional[Any] = None
    ):
        """
        Mark task as completed.

        Args:
            task_id: Task identifier
            success: Whether task succeeded overall
            result: Result value if successful
        """
        if task_id not in self.tasks:
            logger.error(f"Cannot complete unknown task: {task_id}")
            return

        task = self.tasks[task_id]
        task.status = "completed" if success else "failed"
        task.completed_at = datetime.now()
        task.result = result

        total_time = (task.completed_at - task.started_at).total_seconds()
        attempt_count = len(task.attempts)

        logger.info(
            f"Task {task_id} {task.status}: {attempt_count} attempts, "
            f"{total_time:.2f}s total"
        )

    def get_state(self, task_id: str) -> Optional[TaskState]:
        """
        Get current state of task.

        Args:
            task_id: Task identifier

        Returns:
            TaskState if found, None otherwise
        """
        return self.tasks.get(task_id)

    def get_attempt_history(self, task_id: str) -> List[Attempt]:
        """
        Get attempt history for task.

        Args:
            task_id: Task identifier

        Returns:
            List of attempts
        """
        task = self.tasks.get(task_id)
        return task.attempts if task else []

    def save_state(self, task_id: str) -> Dict:
        """
        Serialize task state to dictionary.

        Args:
            task_id: Task identifier

        Returns:
            Serialized state dictionary
        """
        task = self.tasks.get(task_id)
        if not task:
            return {}

        return {
            "task_id": task.task_id,
            "operation_name": task.operation_name,
            "status": task.status,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "total_cost": task.total_cost,
            "attempts": [
                {
                    "timestamp": attempt.timestamp.isoformat(),
                    "strategy_name": attempt.strategy_name,
                    "success": attempt.success,
                    "error": attempt.error,
                    "duration": attempt.duration,
                    "metadata": attempt.metadata
                }
                for attempt in task.attempts
            ]
        }

    def restore_state(self, state_dict: Dict) -> str:
        """
        Restore task state from dictionary.

        Args:
            state_dict: Serialized state

        Returns:
            Task ID
        """
        task_id = state_dict["task_id"]

        attempts = [
            Attempt(
                timestamp=datetime.fromisoformat(a["timestamp"]),
                strategy_name=a["strategy_name"],
                success=a["success"],
                error=a.get("error"),
                duration=a.get("duration", 0.0),
                metadata=a.get("metadata", {})
            )
            for a in state_dict.get("attempts", [])
        ]

        task = TaskState(
            task_id=task_id,
            operation_name=state_dict["operation_name"],
            status=state_dict["status"],
            attempts=attempts,
            started_at=datetime.fromisoformat(state_dict["started_at"]) if state_dict.get("started_at") else None,
            completed_at=datetime.fromisoformat(state_dict["completed_at"]) if state_dict.get("completed_at") else None,
            total_cost=state_dict.get("total_cost", 0.0)
        )

        self.tasks[task_id] = task

        logger.info(f"Restored task state: {task_id}")

        return task_id

    def get_metrics(self, task_id: str) -> Dict:
        """
        Get metrics for task.

        Args:
            task_id: Task identifier

        Returns:
            Dictionary with metrics
        """
        task = self.tasks.get(task_id)
        if not task:
            return {}

        successful_attempts = sum(1 for a in task.attempts if a.success)
        failed_attempts = sum(1 for a in task.attempts if not a.success)
        total_duration = sum(a.duration for a in task.attempts)

        metrics = {
            "task_id": task_id,
            "operation": task.operation_name,
            "status": task.status,
            "total_attempts": len(task.attempts),
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "total_duration": total_duration,
            "avg_attempt_duration": total_duration / len(task.attempts) if task.attempts else 0,
            "total_cost": task.total_cost
        }

        if task.started_at and task.completed_at:
            metrics["total_time"] = (task.completed_at - task.started_at).total_seconds()

        return metrics

    def get_all_metrics(self) -> Dict:
        """
        Get metrics for all tasks.

        Returns:
            Dictionary with overall metrics
        """
        return {
            "total_tasks": len(self.tasks),
            "tasks": {
                task_id: self.get_metrics(task_id)
                for task_id in self.tasks
            }
        }

    def clear_completed(self, max_age_seconds: Optional[int] = None):
        """
        Clear completed tasks from memory.

        Args:
            max_age_seconds: Only clear tasks older than this (None = all completed)
        """
        now = datetime.now()
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed"]:
                if max_age_seconds is None or (
                    task.completed_at and
                    (now - task.completed_at).total_seconds() >= max_age_seconds
                ):
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        logger.debug(f"Cleared {len(to_remove)} completed tasks")

    def clear_all(self):
        """Clear all tracked tasks"""
        self.tasks.clear()
        self._next_id = 1
        logger.debug("Cleared all tracked tasks")
