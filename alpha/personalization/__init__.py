"""
User Personalization System

Provides deep personalization capabilities:
- Automatic preference learning from user interactions
- Adaptive communication style and tone
- Personalized task suggestions and workflows
- Privacy-preserving local storage
"""

from .user_profile import UserProfile, PreferenceHistory, InteractionPattern
from .profile_storage import ProfileStorage
from .profile_learner import ProfileLearner
from .preference_inferrer import PreferenceInferrer
from .communication_adapter import CommunicationAdapter, AdaptationRecommendation
from .verbosity_detector import VerbosityDetector, VerbositySignal
from .language_mixer import LanguageMixer, LanguageSignal, LanguageAdaptivePrompt

__all__ = [
    "UserProfile",
    "PreferenceHistory",
    "InteractionPattern",
    "ProfileStorage",
    "ProfileLearner",
    "PreferenceInferrer",
    "CommunicationAdapter",
    "AdaptationRecommendation",
    "VerbosityDetector",
    "VerbositySignal",
    "LanguageMixer",
    "LanguageSignal",
    "LanguageAdaptivePrompt",
]
