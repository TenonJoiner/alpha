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

__all__ = [
    "UserProfile",
    "PreferenceHistory",
    "InteractionPattern",
    "ProfileStorage",
    "ProfileLearner",
]
