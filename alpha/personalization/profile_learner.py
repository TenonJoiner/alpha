"""
Profile Learner - Automatic preference learning from user interactions

Learns user preferences by analyzing:
- Message patterns (length, complexity, language)
- Tool usage frequency and sequences
- Task types and timing
- Communication style preferences
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, time
import re
import logging

from .user_profile import UserProfile, PreferenceHistory, InteractionPattern
from .profile_storage import ProfileStorage


logger = logging.getLogger(__name__)


class ProfileLearner:
    """
    Automatically learn user preferences from interactions

    Features:
    - Pattern detection from user messages
    - Preference inference with confidence scoring
    - Incremental learning (updates over time)
    - Privacy-preserving (all local)
    """

    def __init__(self, storage: ProfileStorage, profile_id: str = "default"):
        """
        Initialize profile learner

        Args:
            storage: ProfileStorage instance
            profile_id: User profile ID
        """
        self.storage = storage
        self.profile_id = profile_id

        # Load or create profile
        self.profile = self.storage.load_profile(profile_id)
        if not self.profile:
            self.profile = UserProfile(id=profile_id)
            self.storage.save_profile(self.profile)
            logger.info(f"Created new profile: {profile_id}")

    def record_interaction(
        self,
        user_message: str,
        assistant_response: str = "",
        tool_used: Optional[str] = None,
        task_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a user interaction and learn from it

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            tool_used: Tool that was used (if any)
            task_type: Type of task (if identified)
            metadata: Additional metadata
        """
        # Increment interaction count
        self.profile.increment_interaction()

        # Extract features from user message
        features = self._extract_message_features(user_message)

        # Learn verbosity preference
        self._learn_verbosity(user_message, assistant_response, features)

        # Learn technical level
        self._learn_technical_level(user_message, features)

        # Learn language preference
        self._learn_language_preference(user_message, features)

        # Track tool usage
        if tool_used:
            self._track_tool_usage(tool_used)

        # Track task type
        if task_type:
            self._track_task_type(task_type)

        # Detect time-based patterns
        self._detect_time_pattern()

        # Save updated profile
        self.storage.save_profile(self.profile)

    def _extract_message_features(self, message: str) -> Dict[str, Any]:
        """
        Extract features from user message

        Returns:
            Dictionary with message features:
            - word_count: Number of words
            - char_count: Number of characters
            - technical_terms: Count of technical terms
            - code_snippets: Number of code blocks
            - has_chinese: Whether message contains Chinese
            - has_english: Whether message contains English
            - question_words: Count of question words
            - politeness_level: 0-3 (none, low, medium, high)
        """
        features = {
            "word_count": len(message.split()),
            "char_count": len(message),
            "technical_terms": 0,
            "code_snippets": 0,
            "has_chinese": False,
            "has_english": False,
            "question_words": 0,
            "politeness_level": 0
        }

        # Detect Chinese characters
        features["has_chinese"] = bool(re.search(r'[\u4e00-\u9fff]', message))

        # Detect English characters
        features["has_english"] = bool(re.search(r'[a-zA-Z]', message))

        # Count code snippets (```...``` or `...`)
        features["code_snippets"] = len(re.findall(r'```[\s\S]*?```|`[^`]+`', message))

        # Count technical terms (basic heuristic)
        technical_keywords = [
            'function', 'class', 'method', 'variable', 'api', 'database',
            'server', 'client', 'error', 'debug', 'test', 'deploy',
            'algorithm', 'data', 'code', 'script', 'command'
        ]
        message_lower = message.lower()
        features["technical_terms"] = sum(
            1 for term in technical_keywords if term in message_lower
        )

        # Count question words
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', '什么', '怎么', '为什么']
        features["question_words"] = sum(
            1 for word in question_words if word in message_lower
        )

        # Detect politeness level
        polite_words = ['please', 'thanks', 'thank you', 'could you', 'would you', '请', '谢谢']
        features["politeness_level"] = min(3, sum(1 for word in polite_words if word in message_lower))

        return features

    def _learn_verbosity(
        self,
        user_message: str,
        assistant_response: str,
        features: Dict[str, Any]
    ) -> None:
        """
        Learn user's verbosity preference

        Signals:
        - Short user messages → prefer concise responses
        - "too long", "brief", "short answer" → prefer concise
        - "explain more", "details", "elaborate" → prefer detailed
        - Long, detailed user messages → prefer detailed responses
        """
        message_lower = user_message.lower()

        # Explicit signals
        concise_signals = [
            'too long', 'brief', 'short answer', 'be concise', 'tldr',
            'summarize', 'summary', '简短', '简洁', '太长'
        ]
        detailed_signals = [
            'explain more', 'more details', 'elaborate', 'tell me more',
            'in depth', 'comprehensive', '详细', '解释更多'
        ]

        old_verbosity = self.profile.verbosity_level
        new_verbosity = old_verbosity
        reason = ""
        confidence = 0.0

        # Check explicit signals (high confidence)
        if any(signal in message_lower for signal in concise_signals):
            new_verbosity = "concise"
            reason = "User explicitly requested brief responses"
            confidence = 0.9

        elif any(signal in message_lower for signal in detailed_signals):
            new_verbosity = "detailed"
            reason = "User explicitly requested detailed responses"
            confidence = 0.9

        # Check implicit signals (medium confidence)
        elif features["word_count"] < 10 and self.profile.interaction_count > 10:
            # Consistently short messages → prefer concise
            new_verbosity = "concise"
            reason = "User consistently sends short messages"
            confidence = 0.6

        elif features["word_count"] > 50:
            # Long, detailed questions → prefer detailed responses
            new_verbosity = "detailed"
            reason = "User sends detailed messages"
            confidence = 0.6

        # Update preference if changed with sufficient confidence
        if new_verbosity != old_verbosity and confidence >= 0.5:
            self.profile.update_preference("verbosity_level", new_verbosity, confidence)

            # Record preference change history
            history = PreferenceHistory(
                profile_id=self.profile_id,
                preference_type="verbosity_level",
                old_value=old_verbosity,
                new_value=new_verbosity,
                reason=reason,
                confidence=confidence
            )
            self.storage.add_preference_history(history)

            logger.info(f"Verbosity preference updated: {old_verbosity} → {new_verbosity} (confidence: {confidence:.2f})")

    def _learn_technical_level(self, user_message: str, features: Dict[str, Any]) -> None:
        """
        Learn user's technical proficiency level

        Signals:
        - High technical term usage → expert
        - Frequent code snippets → expert
        - "What does X mean?" questions → beginner
        - Mix of both → intermediate
        """
        old_level = self.profile.technical_level
        new_level = old_level
        reason = ""
        confidence = 0.0

        message_lower = user_message.lower()

        # Beginner signals
        beginner_signals = [
            'what does', 'what is', 'how do i', 'i don\'t understand',
            'explain', 'help me', '什么意思', '怎么做', '不懂'
        ]

        # Expert signals
        expert_signals = features["technical_terms"] >= 3 or features["code_snippets"] >= 1

        if any(signal in message_lower for signal in beginner_signals):
            new_level = "beginner"
            reason = "User asking for explanations of basic concepts"
            confidence = 0.7

        elif expert_signals and self.profile.interaction_count > 5:
            new_level = "expert"
            reason = "User frequently uses technical terms and code"
            confidence = 0.7

        # Update if changed with sufficient confidence
        if new_level != old_level and confidence >= 0.6:
            self.profile.update_preference("technical_level", new_level, confidence)

            history = PreferenceHistory(
                profile_id=self.profile_id,
                preference_type="technical_level",
                old_value=old_level,
                new_value=new_level,
                reason=reason,
                confidence=confidence
            )
            self.storage.add_preference_history(history)

            logger.info(f"Technical level updated: {old_level} → {new_level}")

    def _learn_language_preference(self, user_message: str, features: Dict[str, Any]) -> None:
        """
        Learn user's language preference

        Options:
        - 'en': English only
        - 'zh': Chinese only
        - 'mixed': Mixed English and Chinese
        """
        old_pref = self.profile.language_preference
        new_pref = old_pref

        has_chinese = features["has_chinese"]
        has_english = features["has_english"]

        if has_chinese and has_english:
            new_pref = "mixed"
        elif has_chinese and not has_english:
            new_pref = "zh"
        elif has_english and not has_chinese:
            new_pref = "en"

        # Update if changed (language detection is high confidence)
        if new_pref != old_pref:
            self.profile.update_preference("language_preference", new_pref, 0.9)

            history = PreferenceHistory(
                profile_id=self.profile_id,
                preference_type="language_preference",
                old_value=old_pref,
                new_value=new_pref,
                reason="Detected from message language",
                confidence=0.9
            )
            self.storage.add_preference_history(history)

            logger.debug(f"Language preference updated: {old_pref} → {new_pref}")

    def _track_tool_usage(self, tool_name: str) -> None:
        """
        Track tool usage frequency

        Args:
            tool_name: Name of tool used
        """
        # Find or create tool usage pattern
        pattern = self.storage.find_similar_pattern(
            self.profile_id,
            "tool_usage",
            {"tool": tool_name}
        )

        if pattern:
            # Increment existing pattern
            pattern.increment_occurrence()
            self.storage.save_interaction_pattern(pattern)
        else:
            # Create new pattern
            pattern = InteractionPattern(
                profile_id=self.profile_id,
                pattern_type="tool_usage",
                pattern_data={"tool": tool_name}
            )
            self.storage.save_interaction_pattern(pattern)

        # Update preferred_tools list (top 10 most used)
        tool_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            "tool_usage",
            min_occurrences=2
        )
        top_tools = [p.pattern_data["tool"] for p in tool_patterns[:10]]

        if top_tools != self.profile.preferred_tools:
            self.profile.preferred_tools = top_tools
            logger.debug(f"Updated preferred tools: {top_tools}")

    def _track_task_type(self, task_type: str) -> None:
        """
        Track task type frequency

        Args:
            task_type: Type of task
        """
        # Find or create task type pattern
        pattern = self.storage.find_similar_pattern(
            self.profile_id,
            "task_type",
            {"type": task_type}
        )

        if pattern:
            pattern.increment_occurrence()
            self.storage.save_interaction_pattern(pattern)
        else:
            pattern = InteractionPattern(
                profile_id=self.profile_id,
                pattern_type="task_type",
                pattern_data={"type": task_type}
            )
            self.storage.save_interaction_pattern(pattern)

        # Update frequent_tasks list
        task_patterns = self.storage.get_interaction_patterns(
            self.profile_id,
            "task_type",
            min_occurrences=2
        )
        frequent_tasks = [p.pattern_data["type"] for p in task_patterns[:10]]

        if frequent_tasks != self.profile.frequent_tasks:
            self.profile.frequent_tasks = frequent_tasks
            logger.debug(f"Updated frequent tasks: {frequent_tasks}")

    def _detect_time_pattern(self) -> None:
        """
        Detect user's active time patterns

        Updates active_hours_start and active_hours_end based on
        when user is most frequently active
        """
        current_hour = datetime.now().hour

        # Record time-of-day pattern
        pattern = self.storage.find_similar_pattern(
            self.profile_id,
            "time_of_day",
            {"hour": current_hour}
        )

        if pattern:
            pattern.increment_occurrence()
            self.storage.save_interaction_pattern(pattern)
        else:
            pattern = InteractionPattern(
                profile_id=self.profile_id,
                pattern_type="time_of_day",
                pattern_data={"hour": current_hour}
            )
            self.storage.save_interaction_pattern(pattern)

        # Update active hours if we have enough data
        if self.profile.interaction_count >= 20:
            time_patterns = self.storage.get_interaction_patterns(
                self.profile_id,
                "time_of_day",
                min_occurrences=2
            )

            if time_patterns:
                # Find hour range with most activity
                hours = sorted([p.pattern_data["hour"] for p in time_patterns])
                if hours:
                    # Simple heuristic: earliest and latest active hours
                    new_start = min(hours)
                    new_end = max(hours)

                    if (new_start != self.profile.active_hours_start or
                        new_end != self.profile.active_hours_end):

                        self.profile.active_hours_start = new_start
                        self.profile.active_hours_end = new_end

                        logger.info(f"Updated active hours: {new_start}:00 - {new_end}:00")

    def get_profile(self) -> UserProfile:
        """Get current user profile"""
        return self.profile

    def reset_profile(self) -> None:
        """Reset profile to default state"""
        self.storage.delete_profile(self.profile_id)
        self.profile = UserProfile(id=self.profile_id)
        self.storage.save_profile(self.profile)
        logger.info(f"Profile {self.profile_id} reset to defaults")
