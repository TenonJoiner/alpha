"""
Alpha - Task Detector

Automatically identify and suggest proactive tasks.
Detects:
- Repetitive tasks from history
- Context-based task opportunities
- Scheduled task recommendations
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from alpha.proactive.pattern_learner import Pattern, PatternLearner

logger = logging.getLogger(__name__)


class TaskConfidence(Enum):
    """Task suggestion confidence levels."""
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9


@dataclass
class TaskSuggestion:
    """Represents a proactive task suggestion."""
    suggestion_id: str
    task_name: str
    description: str
    justification: str
    confidence: float
    suggested_at: datetime
    pattern_ids: List[str]
    task_params: Dict[str, Any]
    priority: str  # "low", "normal", "high"
    schedule_recommendation: Optional[Dict[str, Any]] = None
    auto_execute: bool = False


class TaskDetector:
    """
    Detect and suggest proactive tasks based on learned patterns.

    Features:
    - Identify repetitive tasks
    - Suggest proactive scheduling
    - Detect context-based opportunities
    - Score suggestions by confidence
    - Generate task proposals with justifications
    """

    def __init__(
        self,
        pattern_learner: PatternLearner,
        min_confidence: float = 0.6,
        max_suggestions_per_run: int = 5
    ):
        """
        Initialize task detector.

        Args:
            pattern_learner: PatternLearner instance
            min_confidence: Minimum confidence for suggestions
            max_suggestions_per_run: Max suggestions to generate per analysis
        """
        self.pattern_learner = pattern_learner
        self.min_confidence = min_confidence
        self.max_suggestions_per_run = max_suggestions_per_run
        self.suggestions_history: List[TaskSuggestion] = []

    async def detect_proactive_tasks(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> List[TaskSuggestion]:
        """
        Detect and suggest proactive tasks.

        Args:
            context: Current context (time, recent activity, etc.)

        Returns:
            List of task suggestions
        """
        suggestions = []

        # Get learned patterns
        patterns = await self.pattern_learner.get_patterns(
            min_confidence=self.min_confidence
        )

        if not patterns:
            logger.info("No patterns available for task detection")
            return suggestions

        # Detect tasks from recurring patterns
        recurring_suggestions = await self._detect_from_recurring_patterns(patterns)
        suggestions.extend(recurring_suggestions)

        # Detect tasks from temporal patterns
        temporal_suggestions = await self._detect_from_temporal_patterns(patterns, context)
        suggestions.extend(temporal_suggestions)

        # Detect context-based opportunities
        if context:
            context_suggestions = await self._detect_context_opportunities(
                patterns, context
            )
            suggestions.extend(context_suggestions)

        # Sort by confidence and limit
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        suggestions = suggestions[:self.max_suggestions_per_run]

        # Store suggestions
        self.suggestions_history.extend(suggestions)

        return suggestions

    async def _detect_from_recurring_patterns(
        self,
        patterns: List[Pattern]
    ) -> List[TaskSuggestion]:
        """Detect tasks from recurring request patterns."""
        suggestions = []

        recurring_patterns = [
            p for p in patterns
            if p.pattern_type == "recurring_request" and p.frequency >= 5
        ]

        for pattern in recurring_patterns:
            # Calculate confidence boost based on frequency
            confidence = min(pattern.confidence + (pattern.frequency / 20.0), 1.0)

            if confidence < self.min_confidence:
                continue

            # Determine schedule recommendation
            days_between = (pattern.last_seen - pattern.first_seen).days
            if days_between > 0:
                frequency_days = days_between / pattern.frequency

                if frequency_days <= 1.5:
                    schedule = {"type": "daily", "time": "09:00"}
                elif frequency_days <= 8:
                    schedule = {"type": "weekly", "weekday": 1, "time": "09:00"}
                else:
                    schedule = {"type": "interval", "interval": int(frequency_days * 86400)}
            else:
                schedule = None

            suggestion = TaskSuggestion(
                suggestion_id=str(uuid.uuid4()),
                task_name=f"Recurring: {pattern.metadata.get('normalized_text', 'Unknown')}",
                description=f"Schedule recurring task: {pattern.description}",
                justification=f"Detected {pattern.frequency} occurrences with {pattern.confidence:.1%} confidence",
                confidence=confidence,
                suggested_at=datetime.now(),
                pattern_ids=[pattern.pattern_id],
                task_params={
                    "pattern_type": "recurring",
                    "original_requests": pattern.examples
                },
                priority="normal" if confidence < 0.8 else "high",
                schedule_recommendation=schedule,
                auto_execute=False
            )
            suggestions.append(suggestion)

        return suggestions

    async def _detect_from_temporal_patterns(
        self,
        patterns: List[Pattern],
        context: Optional[Dict[str, Any]]
    ) -> List[TaskSuggestion]:
        """Detect tasks from temporal patterns."""
        suggestions = []

        temporal_patterns = [
            p for p in patterns
            if p.pattern_type == "temporal"
        ]

        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()

        for pattern in temporal_patterns:
            metadata = pattern.metadata

            # Check if pattern matches current context
            is_relevant = False
            schedule_recommendation = None

            if metadata.get('type') == 'hour_of_day':
                hour = metadata.get('hour')
                # Suggest tasks 1 hour before typical activity
                if (hour - 1) % 24 == current_hour:
                    is_relevant = True
                    schedule_recommendation = {
                        "type": "daily",
                        "time": f"{hour:02d}:00"
                    }

            elif metadata.get('type') == 'day_of_week':
                day = metadata.get('day_of_week')
                # Suggest on the actual day
                if day == current_day:
                    is_relevant = True
                    schedule_recommendation = {
                        "type": "weekly",
                        "weekday": day,
                        "time": "09:00"
                    }

            if is_relevant:
                suggestion = TaskSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    task_name=f"Temporal: {pattern.description}",
                    description=f"Based on activity patterns: {pattern.description}",
                    justification=f"User typically active at this time ({pattern.frequency} times observed)",
                    confidence=pattern.confidence,
                    suggested_at=datetime.now(),
                    pattern_ids=[pattern.pattern_id],
                    task_params={
                        "pattern_type": "temporal",
                        "temporal_metadata": metadata
                    },
                    priority="normal",
                    schedule_recommendation=schedule_recommendation,
                    auto_execute=False
                )
                suggestions.append(suggestion)

        return suggestions

    async def _detect_context_opportunities(
        self,
        patterns: List[Pattern],
        context: Dict[str, Any]
    ) -> List[TaskSuggestion]:
        """Detect task opportunities based on current context."""
        suggestions = []

        # Example: If user frequently asks about weather at certain times
        # and it's that time, suggest weather check

        # Get context info
        current_time = context.get('current_time', datetime.now())
        recent_activity = context.get('recent_activity', [])

        # Look for patterns that match current context
        for pattern in patterns:
            if pattern.pattern_type == "recurring_request":
                # Check if pattern is time-appropriate
                if self._is_time_appropriate(pattern, current_time):
                    confidence = pattern.confidence * 0.8  # Slightly lower for context

                    if confidence >= self.min_confidence:
                        suggestion = TaskSuggestion(
                            suggestion_id=str(uuid.uuid4()),
                            task_name=f"Context-based: {pattern.metadata.get('normalized_text', 'Task')}",
                            description=f"Proactive suggestion based on your patterns",
                            justification=f"You typically do this around this time",
                            confidence=confidence,
                            suggested_at=datetime.now(),
                            pattern_ids=[pattern.pattern_id],
                            task_params={
                                "pattern_type": "context",
                                "context": context
                            },
                            priority="low",
                            auto_execute=False
                        )
                        suggestions.append(suggestion)

        return suggestions

    def _is_time_appropriate(
        self,
        pattern: Pattern,
        current_time: datetime
    ) -> bool:
        """Check if current time is appropriate for a pattern."""
        # Simple heuristic: check if pattern was typically executed around this time
        last_seen = pattern.last_seen
        hour_diff = abs(current_time.hour - last_seen.hour)

        # Consider it appropriate if within 2 hours
        return hour_diff <= 2

    async def get_suggestion_by_id(
        self,
        suggestion_id: str
    ) -> Optional[TaskSuggestion]:
        """Get a specific suggestion by ID."""
        for suggestion in self.suggestions_history:
            if suggestion.suggestion_id == suggestion_id:
                return suggestion
        return None

    async def approve_suggestion(
        self,
        suggestion_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Approve a suggestion and prepare it for execution.

        Args:
            suggestion_id: Suggestion ID to approve

        Returns:
            Task specification for scheduler, or None if not found
        """
        suggestion = await self.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return None

        # Prepare task specification for scheduler
        task_spec = {
            "name": suggestion.task_name,
            "description": suggestion.description,
            "executor": "proactive_task_executor",
            "params": suggestion.task_params,
            "priority": suggestion.priority
        }

        # Include schedule recommendation if available
        if suggestion.schedule_recommendation:
            task_spec["schedule"] = suggestion.schedule_recommendation

        return task_spec

    async def reject_suggestion(
        self,
        suggestion_id: str,
        reason: Optional[str] = None
    ):
        """
        Reject a suggestion and learn from the rejection.

        Args:
            suggestion_id: Suggestion ID to reject
            reason: Optional rejection reason
        """
        suggestion = await self.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return

        # TODO: Update pattern learner to reduce confidence in these patterns
        logger.info(f"Suggestion rejected: {suggestion_id}, reason: {reason}")

        # Could implement learning here to avoid similar suggestions

    async def get_suggestions_history(
        self,
        limit: int = 20,
        min_confidence: Optional[float] = None
    ) -> List[TaskSuggestion]:
        """
        Get historical suggestions.

        Args:
            limit: Maximum number to return
            min_confidence: Optional confidence filter

        Returns:
            List of suggestions
        """
        suggestions = self.suggestions_history

        if min_confidence:
            suggestions = [s for s in suggestions if s.confidence >= min_confidence]

        suggestions.sort(key=lambda s: s.suggested_at, reverse=True)
        return suggestions[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get task detection statistics."""
        total = len(self.suggestions_history)
        if total == 0:
            return {
                "total_suggestions": 0,
                "avg_confidence": 0.0,
                "by_priority": {}
            }

        avg_confidence = sum(s.confidence for s in self.suggestions_history) / total

        # Count by priority
        by_priority = {}
        for suggestion in self.suggestions_history:
            by_priority[suggestion.priority] = by_priority.get(suggestion.priority, 0) + 1

        return {
            "total_suggestions": total,
            "avg_confidence": avg_confidence,
            "by_priority": by_priority,
            "latest_suggestion": self.suggestions_history[-1].suggested_at.isoformat() if total > 0 else None
        }
