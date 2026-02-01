"""
Tests for Profile Management CLI Commands

Tests ProfileCommands functionality:
- Profile display
- Preference management
- History viewing
- Export/import
- Adaptive control
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from alpha.interface.profile_commands import ProfileCommands
from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.user_profile import UserProfile


class TestProfileCommands:
    """Tests for ProfileCommands"""

    @pytest.fixture
    def storage(self):
        """Create in-memory storage for testing"""
        return ProfileStorage(':memory:')

    @pytest.fixture
    def commands(self, storage):
        """Create ProfileCommands instance"""
        return ProfileCommands(profile_storage=storage, profile_id='test_user')

    def test_initialization(self, commands):
        """Test commands initialization"""
        assert commands.profile is not None
        assert commands.profile.id == 'test_user'
        assert commands.adaptive_enabled is True

    def test_show_profile(self, commands):
        """Test profile display"""
        result = commands.show_profile()
        assert "Profile displayed" in result

    def test_show_preferences(self, commands):
        """Test preferences display"""
        result = commands.show_preferences()
        assert "Preferences displayed" in result

    def test_set_verbosity_valid(self, commands):
        """Test setting verbosity to valid value"""
        result = commands.set_preference('verbosity', 'concise')
        assert "updated" in result.lower()
        assert commands.profile.verbosity_level == 'concise'

    def test_set_verbosity_invalid(self, commands):
        """Test setting verbosity to invalid value"""
        result = commands.set_preference('verbosity', 'invalid')
        assert "Invalid" in result

    def test_set_language_valid(self, commands):
        """Test setting language to valid value"""
        result = commands.set_preference('language', 'zh')
        assert "updated" in result.lower()
        assert commands.profile.language_preference == 'zh'

    def test_set_language_invalid(self, commands):
        """Test setting language to invalid value"""
        result = commands.set_preference('language', 'invalid')
        assert "Invalid" in result

    def test_set_tone_valid(self, commands):
        """Test setting tone to valid value"""
        result = commands.set_preference('tone', 'casual')
        assert "updated" in result.lower()
        assert commands.profile.tone_preference == 'casual'

    def test_set_technical_level_valid(self, commands):
        """Test setting technical level to valid value"""
        result = commands.set_preference('technical', 'expert')
        assert "updated" in result.lower()
        assert commands.profile.technical_level == 'expert'

    def test_set_unknown_preference(self, commands):
        """Test setting unknown preference"""
        result = commands.set_preference('unknown', 'value')
        assert "Unknown preference" in result

    def test_show_history_empty(self, commands):
        """Test showing history when empty"""
        result = commands.show_history()
        assert "No history" in result

    def test_show_history_with_data(self, storage):
        """Test showing history with data"""
        # Create profile with history
        storage.add_preference_change(
            profile_id='test_user',
            preference_type='verbosity',
            old_value='balanced',
            new_value='concise',
            reason='User preference',
            confidence=0.8
        )

        commands = ProfileCommands(profile_storage=storage, profile_id='test_user')
        result = commands.show_history()

        assert "history entries" in result.lower()

    def test_reset_profile_without_confirmation(self, commands):
        """Test reset without confirmation"""
        # Set some non-default values
        commands.set_preference('verbosity', 'concise')
        commands.set_preference('language', 'zh')

        result = commands.reset_profile(confirm=False)

        # Should not reset
        assert "cancelled" in result.lower()
        assert commands.profile.verbosity_level == 'concise'

    def test_reset_profile_with_confirmation(self, commands):
        """Test reset with confirmation"""
        # Set some non-default values
        commands.set_preference('verbosity', 'concise')
        commands.set_preference('language', 'zh')

        result = commands.reset_profile(confirm=True)

        # Should reset to defaults
        assert "reset complete" in result.lower()
        assert commands.profile.verbosity_level == 'balanced'
        assert commands.profile.language_preference == 'en'
        assert commands.profile.technical_level == 'intermediate'
        assert commands.profile.tone_preference == 'professional'

    def test_export_profile(self, commands, tmp_path):
        """Test profile export"""
        export_file = tmp_path / "profile.json"

        result = commands.export_profile(str(export_file))

        assert "exported" in result.lower()
        assert export_file.exists()

        # Verify file content
        with open(export_file) as f:
            data = json.load(f)

        assert data['id'] == 'test_user'
        assert 'verbosity_level' in data
        assert 'language_preference' in data

    def test_import_profile(self, commands, tmp_path):
        """Test profile import"""
        # Create export file
        export_file = tmp_path / "profile.json"
        profile_data = {
            'verbosity_level': 'detailed',
            'language_preference': 'zh',
            'tone_preference': 'casual',
            'technical_level': 'expert'
        }

        with open(export_file, 'w') as f:
            json.dump(profile_data, f)

        # Import
        result = commands.import_profile(str(export_file))

        assert "imported" in result.lower()
        assert commands.profile.verbosity_level == 'detailed'
        assert commands.profile.language_preference == 'zh'
        assert commands.profile.tone_preference == 'casual'
        assert commands.profile.technical_level == 'expert'

    def test_import_nonexistent_file(self, commands):
        """Test importing from nonexistent file"""
        result = commands.import_profile("/nonexistent/file.json")
        assert "not found" in result.lower()

    def test_export_import_roundtrip(self, commands, tmp_path):
        """Test export → import roundtrip"""
        # Set custom preferences
        commands.set_preference('verbosity', 'concise')
        commands.set_preference('language', 'mixed')
        commands.set_preference('tone', 'formal')

        # Export
        export_file = tmp_path / "profile_roundtrip.json"
        commands.export_profile(str(export_file))

        # Reset profile
        commands.reset_profile(confirm=True)
        assert commands.profile.verbosity_level == 'balanced'

        # Import
        commands.import_profile(str(export_file))

        # Verify restored
        assert commands.profile.verbosity_level == 'concise'
        assert commands.profile.language_preference == 'mixed'
        assert commands.profile.tone_preference == 'formal'

    def test_set_adaptive_enable(self, commands):
        """Test enabling adaptive features"""
        commands.adaptive_enabled = False
        result = commands.set_adaptive(True)

        assert "enabled" in result.lower()
        assert commands.adaptive_enabled is True

    def test_set_adaptive_disable(self, commands):
        """Test disabling adaptive features"""
        result = commands.set_adaptive(False)

        assert "disabled" in result.lower()
        assert commands.adaptive_enabled is False

    def test_get_statistics(self, commands):
        """Test statistics retrieval"""
        stats = commands.get_statistics()

        assert 'profile_id' in stats
        assert 'interaction_count' in stats
        assert 'confidence_score' in stats
        assert 'preferences_learned' in stats
        assert 'adaptive_enabled' in stats

    def test_statistics_count_learned(self, commands):
        """Test statistics count of learned preferences"""
        # Set preferences
        commands.set_preference('verbosity', 'concise')
        commands.set_preference('language', 'zh')

        stats = commands.get_statistics()

        # Should count non-default preferences
        assert stats['preferences_learned'] >= 2

    def test_profile_persistence(self, storage):
        """Test profile persists across command instances"""
        # Create first instance and set preference
        commands1 = ProfileCommands(profile_storage=storage, profile_id='persist_test')
        commands1.set_preference('verbosity', 'detailed')

        # Create second instance - should load saved profile
        commands2 = ProfileCommands(profile_storage=storage, profile_id='persist_test')

        assert commands2.profile.verbosity_level == 'detailed'

    def test_multiple_profiles(self, storage):
        """Test managing multiple separate profiles"""
        # Create two profiles
        commands1 = ProfileCommands(profile_storage=storage, profile_id='user1')
        commands2 = ProfileCommands(profile_storage=storage, profile_id='user2')

        # Set different preferences
        commands1.set_preference('verbosity', 'concise')
        commands2.set_preference('verbosity', 'detailed')

        # Verify independence
        assert commands1.profile.verbosity_level == 'concise'
        assert commands2.profile.verbosity_level == 'detailed'

    def test_preference_validation_all_types(self, commands):
        """Test validation for all preference types"""
        # Verbosity
        assert "Invalid" in commands.set_preference('verbosity', 'bad_value')

        # Language
        assert "Invalid" in commands.set_preference('language', 'bad_value')

        # Tone
        assert "Invalid" in commands.set_preference('tone', 'bad_value')

        # Technical
        assert "Invalid" in commands.set_preference('technical', 'bad_value')

    def test_case_insensitive_preference_names(self, commands):
        """Test case-insensitive preference names"""
        # Uppercase
        result = commands.set_preference('VERBOSITY', 'concise')
        assert "updated" in result.lower()

        # Mixed case
        result = commands.set_preference('Language', 'zh')
        assert "updated" in result.lower()
