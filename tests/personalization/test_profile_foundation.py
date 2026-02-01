"""
Unit tests for User Personalization - Profile Foundation (Phase 1)

Tests:
- UserProfile data model
- ProfileStorage operations
- ProfileLearner learning logic
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from alpha.personalization.user_profile import UserProfile, PreferenceHistory, InteractionPattern
from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.profile_learner import ProfileLearner


# ==================== UserProfile Tests ====================

class TestUserProfile:
    """Test UserProfile data model"""

    def test_profile_creation_defaults(self):
        """Test profile created with default values"""
        profile = UserProfile()

        assert profile.id == "default"
        assert profile.verbosity_level == "balanced"
        assert profile.technical_level == "intermediate"
        assert profile.language_preference == "en"
        assert profile.tone_preference == "professional"
        assert profile.active_hours_start == 9
        assert profile.active_hours_end == 18
        assert profile.interaction_count == 0
        assert profile.confidence_score == 0.0

    def test_profile_to_dict(self):
        """Test profile serialization to dictionary"""
        profile = UserProfile(
            id="test_user",
            verbosity_level="concise",
            preferred_tools=["git", "shell"],
            frequent_tasks=["coding", "review"]
        )

        data = profile.to_dict()

        assert data["id"] == "test_user"
        assert data["verbosity_level"] == "concise"
        assert '"git"' in data["preferred_tools"]  # JSON string
        assert '"coding"' in data["frequent_tasks"]

    def test_profile_from_dict(self):
        """Test profile deserialization from dictionary"""
        data = {
            "id": "test_user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "verbosity_level": "detailed",
            "technical_level": "expert",
            "language_preference": "zh",
            "tone_preference": "casual",
            "active_hours_start": 10,
            "active_hours_end": 22,
            "timezone": "Asia/Shanghai",
            "preferred_tools": '["python", "docker"]',
            "frequent_tasks": '["debug", "test"]',
            "workflow_patterns": '{"daily_standup": true}',
            "interaction_count": 100,
            "confidence_score": 0.85,
            "last_learned_at": datetime.now().isoformat()
        }

        profile = UserProfile.from_dict(data)

        assert profile.id == "test_user"
        assert profile.verbosity_level == "detailed"
        assert profile.technical_level == "expert"
        assert profile.language_preference == "zh"
        assert profile.preferred_tools == ["python", "docker"]
        assert profile.frequent_tasks == ["debug", "test"]
        assert profile.workflow_patterns == {"daily_standup": True}
        assert profile.interaction_count == 100
        assert profile.confidence_score == 0.85

    def test_update_preference(self):
        """Test updating specific preference"""
        profile = UserProfile()
        old_verbosity = profile.verbosity_level
        old_count = profile.interaction_count

        profile.update_preference("verbosity_level", "concise", 0.9)

        assert profile.verbosity_level == "concise"
        assert profile.verbosity_level != old_verbosity
        assert profile.last_learned_at is not None
        assert profile.confidence_score > 0.0

    def test_increment_interaction(self):
        """Test incrementing interaction count"""
        profile = UserProfile()
        old_count = profile.interaction_count

        profile.increment_interaction()

        assert profile.interaction_count == old_count + 1
        assert profile.updated_at is not None

    def test_is_active_time(self):
        """Test active time checking"""
        profile = UserProfile(active_hours_start=9, active_hours_end=17)

        assert profile.is_active_time(10) is True  # 10am - active
        assert profile.is_active_time(9) is True   # 9am - start (inclusive)
        assert profile.is_active_time(17) is False # 5pm - end (exclusive)
        assert profile.is_active_time(20) is False # 8pm - inactive

    def test_is_active_time_wraparound(self):
        """Test active time with wrap-around (night shift)"""
        profile = UserProfile(active_hours_start=22, active_hours_end=6)

        assert profile.is_active_time(23) is True  # 11pm - active
        assert profile.is_active_time(2) is True   # 2am - active
        assert profile.is_active_time(10) is False # 10am - inactive


class TestPreferenceHistory:
    """Test PreferenceHistory model"""

    def test_preference_history_creation(self):
        """Test creating preference history record"""
        history = PreferenceHistory(
            profile_id="test_user",
            preference_type="verbosity_level",
            old_value="balanced",
            new_value="concise",
            reason="User requested brief responses",
            confidence=0.9
        )

        assert history.profile_id == "test_user"
        assert history.preference_type == "verbosity_level"
        assert history.old_value == "balanced"
        assert history.new_value == "concise"
        assert history.confidence == 0.9

    def test_preference_history_serialization(self):
        """Test preference history to/from dict"""
        history = PreferenceHistory(
            profile_id="test",
            preference_type="technical_level",
            old_value="beginner",
            new_value="intermediate",
            reason="User shows increased technical proficiency",
            confidence=0.7
        )

        data = history.to_dict()
        restored = PreferenceHistory.from_dict(data)

        assert restored.profile_id == history.profile_id
        assert restored.preference_type == history.preference_type
        assert restored.confidence == history.confidence


class TestInteractionPattern:
    """Test InteractionPattern model"""

    def test_interaction_pattern_creation(self):
        """Test creating interaction pattern"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool": "git"}
        )

        assert pattern.profile_id == "test_user"
        assert pattern.pattern_type == "tool_usage"
        assert pattern.pattern_data == {"tool": "git"}
        assert pattern.occurrence_count == 1

    def test_increment_occurrence(self):
        """Test incrementing pattern occurrence"""
        pattern = InteractionPattern(
            pattern_type="task_type",
            pattern_data={"type": "coding"}
        )

        old_count = pattern.occurrence_count
        old_last_seen = pattern.last_seen

        pattern.increment_occurrence()

        assert pattern.occurrence_count == old_count + 1
        assert pattern.last_seen > old_last_seen

    def test_get_frequency(self):
        """Test calculating pattern frequency"""
        pattern = InteractionPattern(
            pattern_type="time_of_day",
            pattern_data={"hour": 9},
            occurrence_count=10
        )

        # Simulate 5 days of data
        pattern.first_seen = datetime.now() - timedelta(days=5)

        frequency = pattern.get_frequency(days=7)

        # Should be ~2 occurrences per day (10 / 5)
        assert 1.8 <= frequency <= 2.2

    def test_is_significant(self):
        """Test pattern significance detection"""
        pattern = InteractionPattern(
            pattern_type="workflow",
            pattern_data={"name": "daily_standup"},
            occurrence_count=5
        )

        # Pattern from 10 days ago
        pattern.first_seen = datetime.now() - timedelta(days=10)

        # Should be significant (≥3 occurrences, ≥7 days)
        assert pattern.is_significant(min_occurrences=3, min_days=7) is True

        # Should not be significant with higher thresholds
        assert pattern.is_significant(min_occurrences=10, min_days=7) is False


# ==================== ProfileStorage Tests ====================

class TestProfileStorage:
    """Test ProfileStorage operations"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_alpha.db")
            yield db_path

    @pytest.fixture
    def storage(self, temp_db):
        """Create ProfileStorage instance"""
        return ProfileStorage(db_path=temp_db)

    def test_create_tables(self, storage):
        """Test database tables creation"""
        # Tables should be created on init
        import sqlite3
        conn = sqlite3.connect(storage.db_path)

        # Check user_profile table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'"
        )
        assert cursor.fetchone() is not None

        # Check preference_history table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='preference_history'"
        )
        assert cursor.fetchone() is not None

        # Check interaction_patterns table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='interaction_patterns'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_save_and_load_profile(self, storage):
        """Test saving and loading user profile"""
        profile = UserProfile(
            id="test_user",
            verbosity_level="concise",
            technical_level="expert",
            preferred_tools=["git", "docker"],
            confidence_score=0.8
        )

        # Save profile
        storage.save_profile(profile)

        # Load profile
        loaded = storage.load_profile("test_user")

        assert loaded is not None
        assert loaded.id == "test_user"
        assert loaded.verbosity_level == "concise"
        assert loaded.technical_level == "expert"
        assert loaded.preferred_tools == ["git", "docker"]
        assert loaded.confidence_score == 0.8

    def test_update_profile(self, storage):
        """Test updating existing profile"""
        profile = UserProfile(id="test_user", verbosity_level="balanced")
        storage.save_profile(profile)

        # Update profile
        profile.verbosity_level = "detailed"
        profile.interaction_count = 50
        storage.save_profile(profile)

        # Load and verify
        loaded = storage.load_profile("test_user")

        assert loaded.verbosity_level == "detailed"
        assert loaded.interaction_count == 50

    def test_delete_profile(self, storage):
        """Test deleting user profile"""
        profile = UserProfile(id="test_user")
        storage.save_profile(profile)

        # Add some history
        history = PreferenceHistory(
            profile_id="test_user",
            preference_type="verbosity",
            old_value="a",
            new_value="b"
        )
        storage.add_preference_history(history)

        # Delete profile
        deleted = storage.delete_profile("test_user")
        assert deleted is True

        # Verify profile deleted
        loaded = storage.load_profile("test_user")
        assert loaded is None

        # Verify history deleted
        history_records = storage.get_preference_history("test_user")
        assert len(history_records) == 0

    def test_add_preference_history(self, storage):
        """Test adding preference history"""
        # Create profile first
        profile = UserProfile(id="test_user")
        storage.save_profile(profile)

        history = PreferenceHistory(
            profile_id="test_user",
            preference_type="verbosity_level",
            old_value="balanced",
            new_value="concise",
            reason="Test reason",
            confidence=0.9
        )

        history_id = storage.add_preference_history(history)

        assert history_id > 0

        # Retrieve and verify
        records = storage.get_preference_history("test_user")
        assert len(records) == 1
        assert records[0].preference_type == "verbosity_level"
        assert records[0].new_value == "concise"

    def test_get_preference_history_filtered(self, storage):
        """Test getting filtered preference history"""
        profile = UserProfile(id="test_user")
        storage.save_profile(profile)

        # Add multiple history records
        storage.add_preference_history(PreferenceHistory(
            profile_id="test_user",
            preference_type="verbosity_level",
            old_value="a", new_value="b"
        ))
        storage.add_preference_history(PreferenceHistory(
            profile_id="test_user",
            preference_type="technical_level",
            old_value="x", new_value="y"
        ))

        # Get all history
        all_history = storage.get_preference_history("test_user")
        assert len(all_history) == 2

        # Get filtered history
        verbosity_history = storage.get_preference_history(
            "test_user",
            preference_type="verbosity_level"
        )
        assert len(verbosity_history) == 1
        assert verbosity_history[0].preference_type == "verbosity_level"

    def test_save_interaction_pattern(self, storage):
        """Test saving interaction pattern"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool": "git"}
        )

        pattern_id = storage.save_interaction_pattern(pattern)

        assert pattern_id > 0

        # Retrieve and verify
        patterns = storage.get_interaction_patterns("test_user")
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "tool_usage"
        assert patterns[0].pattern_data == {"tool": "git"}

    def test_get_interaction_patterns_filtered(self, storage):
        """Test getting filtered interaction patterns"""
        # Add multiple patterns
        storage.save_interaction_pattern(InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool": "git"},
            occurrence_count=5
        ))
        storage.save_interaction_pattern(InteractionPattern(
            profile_id="test_user",
            pattern_type="task_type",
            pattern_data={"type": "coding"},
            occurrence_count=3
        ))

        # Get all patterns
        all_patterns = storage.get_interaction_patterns("test_user")
        assert len(all_patterns) == 2

        # Get filtered by type
        tool_patterns = storage.get_interaction_patterns(
            "test_user",
            pattern_type="tool_usage"
        )
        assert len(tool_patterns) == 1

        # Get filtered by min occurrences
        frequent_patterns = storage.get_interaction_patterns(
            "test_user",
            min_occurrences=4
        )
        assert len(frequent_patterns) == 1

    def test_find_similar_pattern(self, storage):
        """Test finding similar pattern"""
        pattern = InteractionPattern(
            profile_id="test_user",
            pattern_type="tool_usage",
            pattern_data={"tool": "git", "action": "status"}
        )
        storage.save_interaction_pattern(pattern)

        # Find exact match
        found = storage.find_similar_pattern(
            "test_user",
            "tool_usage",
            {"tool": "git", "action": "status"}
        )

        assert found is not None
        assert found.pattern_data == {"tool": "git", "action": "status"}

        # No match for different data
        not_found = storage.find_similar_pattern(
            "test_user",
            "tool_usage",
            {"tool": "docker"}
        )

        assert not_found is None

    def test_get_profile_stats(self, storage):
        """Test getting profile statistics"""
        profile = UserProfile(id="test_user", interaction_count=25, confidence_score=0.75)
        storage.save_profile(profile)

        # Add some history
        storage.add_preference_history(PreferenceHistory(
            profile_id="test_user",
            preference_type="verbosity",
            old_value="a", new_value="b"
        ))

        # Add pattern
        storage.save_interaction_pattern(InteractionPattern(
            profile_id="test_user",
            pattern_type="tool",
            pattern_data={}
        ))

        stats = storage.get_profile_stats("test_user")

        assert stats["profile_id"] == "test_user"
        assert stats["interaction_count"] == 25
        assert stats["confidence_score"] == 0.75
        assert stats["preference_changes"] == 1
        assert stats["detected_patterns"] == 1


# ==================== ProfileLearner Tests ====================

class TestProfileLearner:
    """Test ProfileLearner learning logic"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_alpha.db")
            yield db_path

    @pytest.fixture
    def storage(self, temp_db):
        """Create ProfileStorage instance"""
        return ProfileStorage(db_path=temp_db)

    @pytest.fixture
    def learner(self, storage):
        """Create ProfileLearner instance"""
        return ProfileLearner(storage, profile_id="test_user")

    def test_learner_initialization(self, learner):
        """Test learner initializes profile"""
        assert learner.profile is not None
        assert learner.profile.id == "test_user"

    def test_extract_message_features(self, learner):
        """Test message feature extraction"""
        message = "How do I use the git command? Please help me understand."

        features = learner._extract_message_features(message)

        assert features["word_count"] > 0
        assert features["char_count"] > 0
        assert features["has_english"] is True
        assert features["has_chinese"] is False
        assert features["question_words"] >= 1  # "How"
        assert features["politeness_level"] >= 1  # "Please"

    def test_extract_features_chinese(self, learner):
        """Test feature extraction for Chinese text"""
        message = "请帮我解释一下这个Python错误"

        features = learner._extract_message_features(message)

        assert features["has_chinese"] is True
        assert features["question_words"] >= 1  # "什么" patterns

    def test_extract_features_code(self, learner):
        """Test feature extraction with code"""
        message = "Here's my code: ```python\ndef hello():\n    pass\n```"

        features = learner._extract_message_features(message)

        assert features["code_snippets"] >= 1

    def test_learn_verbosity_explicit_concise(self, learner):
        """Test learning verbosity from explicit signal"""
        learner.record_interaction(
            user_message="Too long. Please be brief.",
            assistant_response=""
        )

        assert learner.profile.verbosity_level == "concise"

    def test_learn_verbosity_explicit_detailed(self, learner):
        """Test learning verbosity preference for detailed"""
        learner.record_interaction(
            user_message="Please explain more. I need more details.",
            assistant_response=""
        )

        assert learner.profile.verbosity_level == "detailed"

    def test_learn_language_mixed(self, learner):
        """Test learning mixed language preference"""
        learner.record_interaction(
            user_message="Help me debug this Python error: 这个错误是什么意思?",
            assistant_response=""
        )

        assert learner.profile.language_preference == "mixed"

    def test_learn_language_chinese(self, learner):
        """Test learning Chinese language preference"""
        learner.record_interaction(
            user_message="帮我分析这个代码",
            assistant_response=""
        )

        assert learner.profile.language_preference == "zh"

    def test_track_tool_usage(self, learner):
        """Test tracking tool usage"""
        # Record git usage multiple times
        for _ in range(5):
            learner.record_interaction(
                user_message="test",
                tool_used="git"
            )

        # Git should be in preferred tools
        assert "git" in learner.profile.preferred_tools

    def test_track_task_type(self, learner):
        """Test tracking task types"""
        for _ in range(3):
            learner.record_interaction(
                user_message="test",
                task_type="coding"
            )

        assert "coding" in learner.profile.frequent_tasks

    def test_increment_interaction_count(self, learner):
        """Test interaction count increments"""
        old_count = learner.profile.interaction_count

        learner.record_interaction(
            user_message="Hello",
            assistant_response="Hi"
        )

        assert learner.profile.interaction_count == old_count + 1

    def test_reset_profile(self, learner):
        """Test resetting profile to defaults"""
        # Modify profile
        learner.profile.verbosity_level = "concise"
        learner.profile.interaction_count = 100

        # Reset
        learner.reset_profile()

        # Should be back to defaults
        assert learner.profile.verbosity_level == "balanced"
        assert learner.profile.interaction_count == 0


# ==================== Integration Tests ====================

class TestPersonalizationIntegration:
    """Integration tests for complete personalization flow"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_alpha.db")
            yield db_path

    def test_end_to_end_learning(self, temp_db):
        """Test complete learning flow from interactions to adapted profile"""
        storage = ProfileStorage(db_path=temp_db)
        learner = ProfileLearner(storage, profile_id="end_to_end_user")

        # Simulate user interactions
        interactions = [
            ("Please be brief", ""),
            ("git status", ""),
            ("git commit", ""),
            ("coding task", ""),
            ("帮我写代码", ""),  # Chinese
        ]

        for user_msg, assistant_msg in interactions:
            learner.record_interaction(
                user_message=user_msg,
                assistant_response=assistant_msg,
                tool_used="git" if "git" in user_msg else None,
                task_type="coding" if "coding" in user_msg or "代码" in user_msg else None
            )

        # Verify learned preferences
        profile = learner.get_profile()

        # Should prefer concise (from "be brief")
        assert profile.verbosity_level == "concise"

        # Should detect language preference
        # (Will be "mixed" or "zh" depending on last message)
        assert profile.language_preference in ["en", "zh", "mixed"]

        # Should track git usage
        assert "git" in profile.preferred_tools or profile.interaction_count >= 5

        # Should track coding tasks
        assert "coding" in profile.frequent_tasks or profile.interaction_count >= 3

        # Should have multiple interactions
        assert profile.interaction_count == len(interactions)

    def test_preference_persistence(self, temp_db):
        """Test that preferences persist across learner instances"""
        storage = ProfileStorage(db_path=temp_db)

        # First learner instance
        learner1 = ProfileLearner(storage, profile_id="persistent_user")
        learner1.record_interaction(
            user_message="Be concise please",
            assistant_response=""
        )

        # Create new learner instance (simulates restart)
        learner2 = ProfileLearner(storage, profile_id="persistent_user")

        # Should load previous preference
        assert learner2.profile.verbosity_level == "concise"
        assert learner2.profile.interaction_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
