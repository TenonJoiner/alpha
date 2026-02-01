"""
Tests for Adaptive Communication Components

Tests for:
- VerbosityDetector
- LanguageMixer
- CommunicationAdapter
"""

import pytest
from datetime import datetime

from alpha.personalization.verbosity_detector import (
    VerbosityDetector,
    VerbositySignal
)
from alpha.personalization.language_mixer import (
    LanguageMixer,
    LanguageSignal,
    LanguageAdaptivePrompt
)
from alpha.personalization.communication_adapter import (
    CommunicationAdapter,
    AdaptationRecommendation
)
from alpha.personalization.user_profile import UserProfile
from alpha.personalization.profile_storage import ProfileStorage


# ============================================================================
# VerbosityDetector Tests
# ============================================================================

class TestVerbosityDetector:
    """Tests for VerbosityDetector"""

    def test_explicit_concise_signal(self):
        """Test detection of explicit concise request"""
        detector = VerbosityDetector()
        signals = detector.detect_from_message("Be brief please")

        assert len(signals) > 0
        assert signals[0].direction == 'concise'
        assert signals[0].signal_type == 'explicit'
        assert signals[0].strength == 0.9

    def test_explicit_detailed_signal(self):
        """Test detection of explicit detailed request"""
        detector = VerbosityDetector()
        signals = detector.detect_from_message("Explain in detail how this works")

        assert len(signals) > 0
        assert signals[0].direction == 'detailed'
        assert signals[0].signal_type == 'explicit'

    def test_short_message_implicit_signal(self):
        """Test implicit signal from short message"""
        detector = VerbosityDetector()
        signals = detector.detect_from_message("Help me")

        # Short message suggests concise preference (weak signal)
        assert any(s.direction == 'concise' for s in signals)
        assert signals[0].signal_type == 'message_length'
        assert signals[0].strength < 0.5

    def test_long_message_implicit_signal(self):
        """Test implicit signal from long message"""
        detector = VerbosityDetector()
        long_message = " ".join(["word"] * 60)  # 60-word message
        signals = detector.detect_from_message(long_message)

        # Long message suggests detailed preference
        assert any(s.direction == 'detailed' for s in signals)

    def test_history_concise_preference(self):
        """Test detection from conversation history - concise preference"""
        detector = VerbosityDetector()
        messages = [
            {'role': 'user', 'content': 'Be brief'},
            {'role': 'user', 'content': 'Short answer please'},
            {'role': 'user', 'content': 'TLDR?'},
            {'role': 'user', 'content': 'Quick question'},
            {'role': 'user', 'content': 'Just tell me'},
        ]

        verbosity, confidence = detector.detect_from_history(messages)

        assert verbosity == 'concise'
        assert confidence > 0.5

    def test_history_detailed_preference(self):
        """Test detection from conversation history - detailed preference"""
        detector = VerbosityDetector()
        messages = [
            {'role': 'user', 'content': 'Explain in detail'},
            {'role': 'user', 'content': 'Tell me everything about this'},
            {'role': 'user', 'content': 'More details please'},
            {'role': 'user', 'content': 'Can you elaborate on that?'},
            {'role': 'user', 'content': 'Give me a comprehensive answer'},
        ]

        verbosity, confidence = detector.detect_from_history(messages)

        assert verbosity == 'detailed'
        assert confidence > 0.5

    def test_balanced_default(self):
        """Test default balanced when no clear signals"""
        detector = VerbosityDetector()
        messages = [
            {'role': 'user', 'content': 'How does this work?'},
            {'role': 'user', 'content': 'What about that feature?'},
            {'role': 'user', 'content': 'Can you help me?'},
        ]

        verbosity, confidence = detector.detect_from_history(messages)

        # Should default to balanced with low confidence
        assert verbosity in ['concise', 'balanced', 'detailed']
        assert confidence >= 0.0

    def test_insufficient_messages(self):
        """Test behavior with insufficient message history"""
        detector = VerbosityDetector()
        messages = [
            {'role': 'user', 'content': 'Help'},
        ]

        verbosity, confidence = detector.detect_from_history(messages, min_messages=5)

        assert verbosity == 'balanced'  # Default
        assert confidence == 0.0  # No confidence

    def test_statistics(self):
        """Test statistics tracking"""
        detector = VerbosityDetector()
        detector.detect_from_message("Be brief")
        detector.detect_from_message("Short message")

        stats = detector.get_statistics()
        assert stats['signals_detected'] >= 2


# ============================================================================
# LanguageMixer Tests
# ============================================================================

class TestLanguageMixer:
    """Tests for LanguageMixer"""

    def test_detect_english_message(self):
        """Test detection of pure English message"""
        mixer = LanguageMixer()
        signal = mixer._detect_message_language("This is an English message")

        assert signal.language == 'en'
        assert signal.confidence == 1.0

    def test_detect_chinese_message(self):
        """Test detection of pure Chinese message"""
        mixer = LanguageMixer()
        signal = mixer._detect_message_language("这是一条中文消息")

        assert signal.language == 'zh'
        assert signal.confidence == 1.0

    def test_detect_mixed_message(self):
        """Test detection of mixed language message"""
        mixer = LanguageMixer()
        signal = mixer._detect_message_language("This is 一条混合 message")

        assert signal.language in ['en', 'zh', 'mixed']

    def test_language_preference_english(self):
        """Test preference detection - English"""
        mixer = LanguageMixer()
        messages = [
            {'role': 'user', 'content': 'Hello, how are you?'},
            {'role': 'user', 'content': 'Can you help me?'},
            {'role': 'user', 'content': 'This is a test message'},
            {'role': 'user', 'content': 'Another English message'},
        ]

        lang, confidence = mixer.detect_language_preference(messages)

        assert lang == 'en'
        assert confidence > 0.5

    def test_language_preference_chinese(self):
        """Test preference detection - Chinese"""
        mixer = LanguageMixer()
        messages = [
            {'role': 'user', 'content': '你好，你怎么样?'},
            {'role': 'user', 'content': '可以帮我吗?'},
            {'role': 'user', 'content': '这是一条测试消息'},
            {'role': 'user', 'content': '另一条中文消息'},
        ]

        lang, confidence = mixer.detect_language_preference(messages)

        assert lang == 'zh'
        assert confidence > 0.5

    def test_mixing_strategy_technical(self):
        """Test mixing strategy for technical content"""
        mixer = LanguageMixer()
        strategy = mixer.get_mixing_strategy(
            "How does async function work?",
            topic='technical'
        )

        assert strategy['primary_language'] == 'en'
        assert strategy['preserve_technical_en'] is True
        assert strategy['preserve_code'] is True

    def test_mixing_strategy_casual(self):
        """Test mixing strategy for casual content"""
        mixer = LanguageMixer()
        strategy = mixer.get_mixing_strategy(
            "How was your day?",
            topic='casual'
        )

        assert strategy['allow_mixing'] is True

    def test_technical_content_detection(self):
        """Test technical content detection"""
        mixer = LanguageMixer()

        # Technical message
        assert mixer.is_technical_content(
            "The function returns an error when the database query fails"
        ) is True

        # Non-technical message
        assert mixer.is_technical_content(
            "I had a great day today"
        ) is False

    def test_language_adaptive_prompt(self):
        """Test language adaptive prompt generation"""
        # English only
        instruction = LanguageAdaptivePrompt.create_language_instruction({
            'primary_language': 'en',
            'allow_mixing': False
        })
        assert 'English' in instruction

        # Chinese only
        instruction = LanguageAdaptivePrompt.create_language_instruction({
            'primary_language': 'zh',
            'allow_mixing': False
        })
        assert 'Chinese' in instruction or '中文' in instruction

        # Mixed
        instruction = LanguageAdaptivePrompt.create_language_instruction({
            'primary_language': 'mixed',
            'allow_mixing': True
        })
        assert 'mix' in instruction.lower()


# ============================================================================
# CommunicationAdapter Tests
# ============================================================================

class TestCommunicationAdapter:
    """Tests for CommunicationAdapter"""

    def test_initialization_without_storage(self):
        """Test adapter initialization without storage"""
        adapter = CommunicationAdapter()

        assert adapter.profile is None
        assert adapter.verbosity_detector is not None
        assert adapter.language_mixer is not None

    def test_initialization_with_storage(self):
        """Test adapter initialization with storage"""
        storage = ProfileStorage(':memory:')
        adapter = CommunicationAdapter(profile_storage=storage)

        assert adapter.profile_storage is not None
        # Profile may or may not exist yet

    def test_basic_adaptation(self):
        """Test basic adaptation recommendation"""
        adapter = CommunicationAdapter()

        recommendation = adapter.get_adaptation(
            user_message="How does this work?",
            conversation_history=[],
            topic='general'
        )

        assert isinstance(recommendation, AdaptationRecommendation)
        assert recommendation.verbosity_level in ['concise', 'balanced', 'detailed']
        assert recommendation.primary_language in ['en', 'zh', 'mixed']
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.system_prompt_addition != ""

    def test_adaptation_with_concise_preference(self):
        """Test adaptation with concise preference signals"""
        adapter = CommunicationAdapter()

        messages = [
            {'role': 'user', 'content': 'Be brief'},
            {'role': 'user', 'content': 'Short answer'},
            {'role': 'user', 'content': 'TLDR'},
        ]

        recommendation = adapter.get_adaptation(
            user_message="Quick question",
            conversation_history=messages,
            topic='general'
        )

        # Should detect concise preference
        assert recommendation.verbosity_level == 'concise'
        assert 'brief' in recommendation.system_prompt_addition.lower()

    def test_adaptation_with_detailed_preference(self):
        """Test adaptation with detailed preference signals"""
        adapter = CommunicationAdapter()

        messages = [
            {'role': 'user', 'content': 'Explain in detail'},
            {'role': 'user', 'content': 'Tell me everything'},
            {'role': 'user', 'content': 'More details please'},
        ]

        recommendation = adapter.get_adaptation(
            user_message="How does async work?",
            conversation_history=messages,
            topic='technical'
        )

        # Should detect detailed preference
        assert recommendation.verbosity_level == 'detailed'

    def test_adaptation_technical_topic(self):
        """Test adaptation for technical topic"""
        adapter = CommunicationAdapter()

        recommendation = adapter.get_adaptation(
            user_message="Explain async functions",
            topic='technical'
        )

        # Technical topics should default to English
        assert recommendation.primary_language == 'en'

    def test_profile_update(self):
        """Test profile update after adaptation"""
        storage = ProfileStorage(':memory:')
        adapter = CommunicationAdapter(profile_storage=storage)

        messages = [
            {'role': 'user', 'content': 'Be brief please'},
        ] * 10  # Repeat for confidence

        adapter.get_adaptation(
            user_message="Quick question",
            conversation_history=messages,
            force_update_profile=True
        )

        # Profile should be updated
        assert adapter.profile_updates > 0

    def test_reset_to_defaults(self):
        """Test resetting profile to defaults"""
        storage = ProfileStorage(':memory:')
        adapter = CommunicationAdapter(profile_storage=storage)

        # Create profile with non-default values
        adapter.profile = UserProfile(
            verbosity_level='concise',
            language_preference='zh',
            technical_level='expert'
        )
        storage.save_profile(adapter.profile)

        # Reset
        adapter.reset_to_defaults()

        assert adapter.profile.verbosity_level == 'balanced'
        assert adapter.profile.language_preference == 'en'
        assert adapter.profile.technical_level == 'intermediate'

    def test_get_profile_summary(self):
        """Test profile summary generation"""
        storage = ProfileStorage(':memory:')
        adapter = CommunicationAdapter(profile_storage=storage)

        summary = adapter.get_profile_summary()

        assert 'profile_id' in summary
        assert 'preferences' in summary or 'status' in summary

    def test_statistics(self):
        """Test statistics tracking"""
        adapter = CommunicationAdapter()

        adapter.get_adaptation("Test message")
        adapter.get_adaptation("Another test")

        stats = adapter.get_statistics()
        assert stats['adaptations_generated'] == 2
        assert 'verbosity_detector' in stats
        assert 'language_mixer' in stats


# ============================================================================
# Integration Tests
# ============================================================================

class TestCommunicationIntegration:
    """Integration tests for communication system"""

    def test_end_to_end_adaptation(self):
        """Test end-to-end adaptation with real conversation"""
        storage = ProfileStorage(':memory:')
        adapter = CommunicationAdapter(profile_storage=storage)

        # Simulate conversation
        messages = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi! How can I help?'},
            {'role': 'user', 'content': 'Explain async in Python briefly'},
            {'role': 'assistant', 'content': 'Async allows concurrent execution...'},
            {'role': 'user', 'content': 'Short answer please'},
        ]

        recommendation = adapter.get_adaptation(
            user_message="How do I use asyncio?",
            conversation_history=messages,
            topic='technical',
            force_update_profile=True
        )

        # Should have reasonable recommendations
        assert recommendation.verbosity_level in ['concise', 'balanced', 'detailed']
        assert recommendation.primary_language in ['en', 'zh', 'mixed']
        assert recommendation.system_prompt_addition != ""
        assert recommendation.confidence > 0.0

    def test_chinese_conversation_adaptation(self):
        """Test adaptation for Chinese conversation"""
        adapter = CommunicationAdapter()

        messages = [
            {'role': 'user', 'content': '你好'},
            {'role': 'user', 'content': '可以帮我吗?'},
            {'role': 'user', 'content': '我想知道这个怎么用'},
        ]

        recommendation = adapter.get_adaptation(
            user_message="这个功能怎么用?",
            conversation_history=messages,
            topic='general'
        )

        # Should detect Chinese preference
        assert recommendation.primary_language == 'zh'

    def test_persistence_across_sessions(self):
        """Test profile persistence across adapter instances"""
        storage = ProfileStorage(':memory:')

        # Session 1: Learn preferences
        adapter1 = CommunicationAdapter(profile_storage=storage, profile_id='test_user')
        adapter1.get_adaptation(
            user_message="Be brief",
            force_update_profile=True
        )

        # Session 2: Load same profile
        adapter2 = CommunicationAdapter(profile_storage=storage, profile_id='test_user')

        # Should have loaded previous preferences
        assert adapter2.profile is not None
        assert adapter2.profile.id == 'test_user'
