"""
User Profile Data Models

Defines data structures for user personalization:
- UserProfile: Main user preferences and settings
- PreferenceHistory: Track preference changes over time
- InteractionPattern: Behavioral patterns detected
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


@dataclass
class UserProfile:
    """
    User profile containing learned preferences and settings

    Automatically learned from user interactions:
    - Communication preferences (verbosity, tone, language)
    - Behavioral patterns (active hours, timezone)
    - Task preferences (tools, workflows)
    """

    # Identity
    id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Communication Preferences
    verbosity_level: str = "balanced"  # concise, balanced, detailed
    technical_level: str = "intermediate"  # beginner, intermediate, expert
    language_preference: str = "en"  # en, zh, mixed
    tone_preference: str = "professional"  # casual, professional, formal

    # Behavioral Patterns
    active_hours_start: int = 9  # 24-hour format (0-23)
    active_hours_end: int = 18
    timezone: str = "UTC"

    # Task Preferences (stored as JSON strings, parsed to lists/dicts)
    preferred_tools: List[str] = field(default_factory=list)
    frequent_tasks: List[str] = field(default_factory=list)
    workflow_patterns: Dict[str, Any] = field(default_factory=dict)

    # Learning Metadata
    interaction_count: int = 0
    confidence_score: float = 0.0  # 0.0 to 1.0 (how confident we are about preferences)
    last_learned_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage"""
        data = asdict(self)

        # Convert datetime objects to ISO format strings
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        data["last_learned_at"] = self.last_learned_at.isoformat() if self.last_learned_at else None

        # Convert lists and dicts to JSON strings
        data["preferred_tools"] = json.dumps(self.preferred_tools)
        data["frequent_tasks"] = json.dumps(self.frequent_tasks)
        data["workflow_patterns"] = json.dumps(self.workflow_patterns)

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create profile from dictionary (from storage)"""
        # Parse datetime strings
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("last_learned_at") and isinstance(data["last_learned_at"], str):
            data["last_learned_at"] = datetime.fromisoformat(data["last_learned_at"])

        # Parse JSON strings to lists/dicts
        if isinstance(data.get("preferred_tools"), str):
            data["preferred_tools"] = json.loads(data["preferred_tools"])
        if isinstance(data.get("frequent_tasks"), str):
            data["frequent_tasks"] = json.loads(data["frequent_tasks"])
        if isinstance(data.get("workflow_patterns"), str):
            data["workflow_patterns"] = json.loads(data["workflow_patterns"])

        return cls(**data)

    def update_preference(
        self,
        preference_type: str,
        new_value: Any,
        confidence: float = 1.0
    ) -> None:
        """
        Update a specific preference

        Args:
            preference_type: Type of preference (verbosity_level, technical_level, etc.)
            new_value: New value for the preference
            confidence: Confidence in this update (0.0-1.0)
        """
        if hasattr(self, preference_type):
            setattr(self, preference_type, new_value)
            self.updated_at = datetime.now()
            self.last_learned_at = datetime.now()

            # Update overall confidence score (weighted average)
            self.confidence_score = (
                (self.confidence_score * self.interaction_count + confidence) /
                (self.interaction_count + 1)
            )

    def increment_interaction(self) -> None:
        """Increment interaction count"""
        self.interaction_count += 1
        self.updated_at = datetime.now()

    def is_active_time(self, hour: Optional[int] = None) -> bool:
        """
        Check if current time is within user's active hours

        Args:
            hour: Hour to check (0-23), defaults to current hour

        Returns:
            True if within active hours
        """
        if hour is None:
            hour = datetime.now().hour

        if self.active_hours_start <= self.active_hours_end:
            # Normal case: 9am-5pm
            return self.active_hours_start <= hour < self.active_hours_end
        else:
            # Wrap-around case: 10pm-2am
            return hour >= self.active_hours_start or hour < self.active_hours_end


@dataclass
class PreferenceHistory:
    """
    Track history of preference changes

    Records why and when preferences changed to enable
    transparency and learning analysis
    """

    id: Optional[int] = None
    profile_id: str = "default"
    preference_type: str = ""  # verbosity_level, tool_usage, task_type, etc.
    old_value: str = ""
    new_value: str = ""
    reason: str = ""  # Why preference changed
    confidence: float = 0.0  # Confidence in this change (0.0-1.0)
    learned_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "preference_type": self.preference_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "confidence": self.confidence,
            "learned_at": self.learned_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreferenceHistory":
        """Create from dictionary"""
        if isinstance(data.get("learned_at"), str):
            data["learned_at"] = datetime.fromisoformat(data["learned_at"])
        return cls(**data)


@dataclass
class InteractionPattern:
    """
    Detected behavioral pattern from user interactions

    Examples:
    - Time patterns: "User most active 9am-5pm weekdays"
    - Tool patterns: "User always runs 'git status' before 'git commit'"
    - Task patterns: "User checks email every morning at 9am"
    """

    id: Optional[int] = None
    profile_id: str = "default"
    pattern_type: str = ""  # time_of_day, tool_sequence, task_frequency, etc.
    pattern_data: Dict[str, Any] = field(default_factory=dict)  # JSON data
    occurrence_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "pattern_type": self.pattern_type,
            "pattern_data": json.dumps(self.pattern_data),
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionPattern":
        """Create from dictionary"""
        if isinstance(data.get("pattern_data"), str):
            data["pattern_data"] = json.loads(data["pattern_data"])
        if isinstance(data.get("first_seen"), str):
            data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        if isinstance(data.get("last_seen"), str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        return cls(**data)

    def increment_occurrence(self) -> None:
        """Increment occurrence count and update last seen"""
        self.occurrence_count += 1
        self.last_seen = datetime.now()

    def get_frequency(self, days: int = 7) -> float:
        """
        Calculate pattern frequency (occurrences per day)

        Args:
            days: Number of days to calculate over

        Returns:
            Average occurrences per day
        """
        time_span = (self.last_seen - self.first_seen).total_seconds() / 86400  # days
        if time_span < 1:
            time_span = 1  # Minimum 1 day

        return self.occurrence_count / min(time_span, days)

    def is_significant(self, min_occurrences: int = 3, min_days: int = 7) -> bool:
        """
        Check if pattern is statistically significant

        Args:
            min_occurrences: Minimum occurrences required
            min_days: Minimum time span required

        Returns:
            True if pattern is significant
        """
        time_span = (self.last_seen - self.first_seen).total_seconds() / 86400
        return (
            self.occurrence_count >= min_occurrences and
            time_span >= min_days
        )
