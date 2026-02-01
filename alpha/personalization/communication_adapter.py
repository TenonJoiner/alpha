"""
Communication Adapter - Main Coordinator for Adaptive Communication

Orchestrates adaptive communication by:
- Combining verbosity detection and language mixing
- Integrating with user profile system
- Providing response adaptation recommendations
- Learning from user feedback

Main entry point for personalized communication adaptation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .verbosity_detector import VerbosityDetector, VerbositySignal
from .language_mixer import LanguageMixer, LanguageSignal, LanguageAdaptivePrompt
from .user_profile import UserProfile
from .profile_storage import ProfileStorage


@dataclass
class AdaptationRecommendation:
    """
    Recommendation for how to adapt communication

    Attributes:
        verbosity_level: Recommended verbosity ('concise', 'balanced', 'detailed')
        primary_language: Primary language for response ('en', 'zh', 'mixed')
        language_mixing_allowed: Whether to mix languages
        technical_level: Technical terminology level ('beginner', 'intermediate', 'expert')
        tone: Communication tone ('casual', 'professional', 'formal')
        confidence: Confidence in recommendation (0.0 to 1.0)
        reasoning: Why these recommendations were made
        system_prompt_addition: Text to add to system prompt
    """
    verbosity_level: str = 'balanced'
    primary_language: str = 'en'
    language_mixing_allowed: bool = False
    technical_level: str = 'intermediate'
    tone: str = 'professional'
    confidence: float = 0.5
    reasoning: Dict[str, str] = None
    system_prompt_addition: str = ""

    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = {}


class CommunicationAdapter:
    """
    Main coordinator for adaptive communication

    Analyzes user interactions to provide personalized communication
    recommendations. Integrates:
    - VerbosityDetector: Detect preferred detail level
    - LanguageMixer: Smart language selection
    - UserProfile: Persist learned preferences

    Usage:
        adapter = CommunicationAdapter(profile_storage)

        # Get adaptation recommendation for current message
        recommendation = adapter.get_adaptation(
            user_message="Explain how async works",
            conversation_history=messages,
            topic='technical'
        )

        # Apply to system prompt
        adapted_prompt = recommendation.system_prompt_addition
    """

    def __init__(
        self,
        profile_storage: Optional[ProfileStorage] = None,
        profile_id: str = 'default'
    ):
        """
        Initialize communication adapter

        Args:
            profile_storage: Storage for user profiles (optional)
            profile_id: ID of user profile to use
        """
        self.profile_storage = profile_storage
        self.profile_id = profile_id

        # Initialize detectors
        self.verbosity_detector = VerbosityDetector()
        self.language_mixer = LanguageMixer()

        # Load user profile if storage available
        self.profile: Optional[UserProfile] = None
        if profile_storage:
            self.profile = profile_storage.load_profile(profile_id)

        # Statistics
        self.adaptations_generated = 0
        self.profile_updates = 0

    def get_adaptation(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        topic: str = 'general',
        force_update_profile: bool = False
    ) -> AdaptationRecommendation:
        """
        Get communication adaptation recommendation

        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            topic: Message topic ('technical', 'casual', 'general')
            force_update_profile: Force profile update even if low confidence

        Returns:
            AdaptationRecommendation with personalized settings
        """
        if conversation_history is None:
            conversation_history = []

        recommendation = AdaptationRecommendation()
        reasoning = {}

        # 1. Get verbosity preference
        verbosity, v_confidence = self._get_verbosity_preference(
            user_message,
            conversation_history
        )
        recommendation.verbosity_level = verbosity
        reasoning['verbosity'] = (
            f"{verbosity} (confidence: {v_confidence:.2f})"
        )

        # 2. Get language preference
        language, lang_strategy = self._get_language_preference(
            user_message,
            conversation_history,
            topic
        )
        recommendation.primary_language = language
        recommendation.language_mixing_allowed = lang_strategy.get('allow_mixing', False)
        reasoning['language'] = lang_strategy.get('reasoning', 'Default')

        # 3. Get technical level (from profile or infer)
        tech_level = self._get_technical_level(user_message, conversation_history)
        recommendation.technical_level = tech_level
        reasoning['technical_level'] = f"{tech_level} (from profile or inference)"

        # 4. Get tone preference (from profile or default)
        tone = self._get_tone_preference()
        recommendation.tone = tone
        reasoning['tone'] = f"{tone} (from profile)"

        # 5. Calculate overall confidence
        recommendation.confidence = (v_confidence + 0.5) / 2  # Average with lang confidence

        # 6. Build system prompt addition
        recommendation.system_prompt_addition = self._build_system_prompt(
            recommendation
        )

        # 7. Store reasoning
        recommendation.reasoning = reasoning

        # 8. Update profile if confident enough
        if force_update_profile or recommendation.confidence > 0.6:
            self._update_profile(recommendation)

        self.adaptations_generated += 1
        return recommendation

    def _get_verbosity_preference(
        self,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> Tuple[str, float]:
        """Get verbosity preference (from profile or detect)"""

        # 1. Check profile first
        if self.profile and self.profile.confidence_score > 0.7:
            return (self.profile.verbosity_level, self.profile.confidence_score)

        # 2. Detect from conversation
        all_messages = history + [{'role': 'user', 'content': user_message}]
        detected_verbosity, confidence = self.verbosity_detector.detect_from_history(
            all_messages
        )

        # 3. Blend with profile if exists but low confidence
        if self.profile and confidence < 0.7:
            # Use profile as fallback
            if confidence < 0.3:
                return (self.profile.verbosity_level, 0.5)

        return (detected_verbosity, confidence)

    def _get_language_preference(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        topic: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Get language preference and mixing strategy"""

        # 1. Check profile first
        profile_lang = None
        if self.profile:
            profile_lang = self.profile.language_preference

        # 2. Get mixing strategy
        strategy = self.language_mixer.get_mixing_strategy(
            user_message,
            topic=topic,
            preference=profile_lang
        )

        return (strategy['primary_language'], strategy)

    def _get_technical_level(
        self,
        user_message: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Get technical level (from profile or infer)"""

        # 1. Check profile
        if self.profile:
            return self.profile.technical_level

        # 2. Infer from message content
        if self.language_mixer.is_technical_content(user_message):
            # User uses technical terms → likely intermediate+
            return 'intermediate'

        # 3. Default
        return 'intermediate'

    def _get_tone_preference(self) -> str:
        """Get tone preference from profile"""
        if self.profile:
            return self.profile.tone_preference
        return 'professional'

    def _build_system_prompt(
        self,
        recommendation: AdaptationRecommendation
    ) -> str:
        """
        Build system prompt addition based on recommendations

        Args:
            recommendation: Adaptation recommendations

        Returns:
            Text to add to system prompt
        """
        parts = []

        # 1. Language instruction
        lang_instruction = LanguageAdaptivePrompt.create_language_instruction({
            'primary_language': recommendation.primary_language,
            'allow_mixing': recommendation.language_mixing_allowed
        })
        parts.append(lang_instruction)

        # 2. Verbosity instruction
        if recommendation.verbosity_level == 'concise':
            parts.append(
                "Keep responses brief and to the point. "
                "Avoid lengthy explanations unless asked."
            )
        elif recommendation.verbosity_level == 'detailed':
            parts.append(
                "Provide detailed, comprehensive responses. "
                "Include examples and thorough explanations."
            )
        else:  # balanced
            parts.append(
                "Provide balanced responses - detailed enough to be helpful, "
                "but concise enough to be efficient."
            )

        # 3. Technical level instruction
        if recommendation.technical_level == 'beginner':
            parts.append(
                "Use simple language and explain technical terms. "
                "Assume limited technical background."
            )
        elif recommendation.technical_level == 'expert':
            parts.append(
                "Use technical terminology freely. "
                "Assume advanced technical knowledge."
            )
        # intermediate: no special instruction (default)

        # 4. Tone instruction
        if recommendation.tone == 'casual':
            parts.append("Maintain a friendly, casual tone.")
        elif recommendation.tone == 'formal':
            parts.append("Maintain a formal, professional tone.")
        # professional: no special instruction (default)

        return " ".join(parts)

    def _update_profile(self, recommendation: AdaptationRecommendation):
        """
        Update user profile with learned preferences

        Args:
            recommendation: Current recommendations to save
        """
        if not self.profile_storage:
            return  # No storage configured

        if not self.profile:
            self.profile = UserProfile(id=self.profile_id)

        # Update preferences
        self.profile.verbosity_level = recommendation.verbosity_level
        self.profile.language_preference = recommendation.primary_language
        self.profile.technical_level = recommendation.technical_level
        self.profile.tone_preference = recommendation.tone
        self.profile.confidence_score = recommendation.confidence
        self.profile.updated_at = datetime.now()

        # Save to storage
        self.profile_storage.save_profile(self.profile)
        self.profile_updates += 1

    def reset_to_defaults(self):
        """Reset profile to default preferences"""
        if self.profile:
            self.profile.verbosity_level = 'balanced'
            self.profile.language_preference = 'en'
            self.profile.technical_level = 'intermediate'
            self.profile.tone_preference = 'professional'
            self.profile.confidence_score = 0.0

            if self.profile_storage:
                self.profile_storage.save_profile(self.profile)

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        Get summary of current profile and preferences

        Returns:
            Dict with profile information
        """
        if not self.profile:
            return {
                'profile_id': self.profile_id,
                'status': 'No profile loaded',
                'preferences': {}
            }

        return {
            'profile_id': self.profile.id,
            'preferences': {
                'verbosity': self.profile.verbosity_level,
                'language': self.profile.language_preference,
                'technical_level': self.profile.technical_level,
                'tone': self.profile.tone_preference
            },
            'confidence': self.profile.confidence_score,
            'interaction_count': self.profile.interaction_count,
            'last_updated': self.profile.updated_at.isoformat() if self.profile.updated_at else None
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            'adaptations_generated': self.adaptations_generated,
            'profile_updates': self.profile_updates,
            'verbosity_detector': self.verbosity_detector.get_statistics(),
            'language_mixer': self.language_mixer.get_statistics()
        }
