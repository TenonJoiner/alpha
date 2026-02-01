"""
Tests for Proactive Screenshot Assistance System
"""

import pytest
from datetime import datetime
from alpha.multimodal.screenshot_assistant import (
    ProactiveScreenshotAssistant,
    ScreenshotDetector,
    ScreenshotSuggestionGenerator,
    ScreenshotCaptureGuide,
    ScreenshotSuggestion,
    ScreenshotTriggerType,
)


class TestScreenshotDetector:
    """Test suite for ScreenshotDetector."""

    def test_detect_error_description(self):
        """Test detection of error descriptions."""
        detector = ScreenshotDetector()

        # Strong error signals
        assert detector.detect_screenshot_need("I'm getting an error") == ScreenshotTriggerType.ERROR_DESCRIPTION
        assert detector.detect_screenshot_need("I see this exception") == ScreenshotTriggerType.ERROR_DESCRIPTION
        assert detector.detect_screenshot_need("The app crashed") == ScreenshotTriggerType.ERROR_DESCRIPTION

    def test_detect_ui_issue(self):
        """Test detection of UI issues."""
        detector = ScreenshotDetector()

        assert detector.detect_screenshot_need("The button looks weird") == ScreenshotTriggerType.UI_ISSUE
        assert detector.detect_screenshot_need("Layout is broken") == ScreenshotTriggerType.UI_ISSUE
        assert detector.detect_screenshot_need("Wrong alignment") == ScreenshotTriggerType.UI_ISSUE

    def test_detect_visual_comparison(self):
        """Test detection of comparison requests."""
        detector = ScreenshotDetector()

        assert detector.detect_screenshot_need("Compare these two designs") == ScreenshotTriggerType.VISUAL_COMPARISON
        assert detector.detect_screenshot_need("Check the difference between pages") == ScreenshotTriggerType.VISUAL_COMPARISON

    def test_detect_unclear_description(self):
        """Test detection of ambiguous visual descriptions."""
        detector = ScreenshotDetector()

        result = detector.detect_screenshot_need("It looks weird and seems strange")
        assert result == ScreenshotTriggerType.UNCLEAR_DESCRIPTION

    def test_no_detection_for_clear_text(self):
        """Test that clear text queries don't trigger screenshot."""
        detector = ScreenshotDetector()

        assert detector.detect_screenshot_need("What is Python?") is None
        assert detector.detect_screenshot_need("How do I install npm?") is None
        assert detector.detect_screenshot_need("Explain async/await") is None

    def test_debug_session_context(self):
        """Test detection from debug context."""
        detector = ScreenshotDetector()

        context = {"is_debugging": True}
        result = detector.detect_screenshot_need("What's happening?", context=context)
        assert result == ScreenshotTriggerType.DEBUG_SESSION

    def test_calculate_priority_error(self):
        """Test priority calculation for errors."""
        detector = ScreenshotDetector()

        priority = detector.calculate_priority(
            ScreenshotTriggerType.ERROR_DESCRIPTION,
            "I'm seeing an error"
        )
        assert priority == 5  # Highest priority

    def test_calculate_priority_urgent_boost(self):
        """Test priority boost for urgent messages."""
        detector = ScreenshotDetector()

        # Normal UI issue
        priority1 = detector.calculate_priority(
            ScreenshotTriggerType.UI_ISSUE,
            "The button looks odd"
        )
        assert priority1 == 3

        # Urgent UI issue
        priority2 = detector.calculate_priority(
            ScreenshotTriggerType.UI_ISSUE,
            "URGENT: Production site is down"
        )
        assert priority2 == 4  # Boosted by 1

    def test_case_insensitive_patterns(self):
        """Test that patterns are case-insensitive."""
        detector = ScreenshotDetector()

        assert detector.detect_screenshot_need("I'M GETTING AN ERROR") is not None
        assert detector.detect_screenshot_need("the BUTTON looks WEIRD") is not None


class TestScreenshotSuggestionGenerator:
    """Test suite for ScreenshotSuggestionGenerator."""

    def test_generate_suggestion_error(self):
        """Test generating suggestion for error."""
        generator = ScreenshotSuggestionGenerator()

        suggestion = generator.generate_suggestion(
            trigger_type=ScreenshotTriggerType.ERROR_DESCRIPTION,
            priority=5,
            user_message="I see an error"
        )

        assert suggestion.trigger_type == ScreenshotTriggerType.ERROR_DESCRIPTION
        assert suggestion.priority == 5
        assert "screenshot" in suggestion.message.lower()
        assert len(suggestion.guidance_steps) > 0
        assert "error" in suggestion.reason.lower()

    def test_generate_suggestion_ui_issue(self):
        """Test generating suggestion for UI issue."""
        generator = ScreenshotSuggestionGenerator()

        suggestion = generator.generate_suggestion(
            trigger_type=ScreenshotTriggerType.UI_ISSUE,
            priority=3,
            user_message="Button looks broken"
        )

        assert suggestion.trigger_type == ScreenshotTriggerType.UI_ISSUE
        assert "ui" in suggestion.reason.lower() or "layout" in suggestion.reason.lower()

    def test_suggestion_includes_context(self):
        """Test that suggestions preserve context."""
        generator = ScreenshotSuggestionGenerator()

        context = {"session_id": "test123", "user_id": "user456"}
        suggestion = generator.generate_suggestion(
            trigger_type=ScreenshotTriggerType.DEBUG_SESSION,
            priority=4,
            user_message="What's wrong?",
            context=context
        )

        assert suggestion.context == context

    def test_unique_suggestion_ids(self):
        """Test that each suggestion gets unique ID."""
        generator = ScreenshotSuggestionGenerator()

        s1 = generator.generate_suggestion(
            ScreenshotTriggerType.ERROR_DESCRIPTION, 5, "error 1"
        )
        s2 = generator.generate_suggestion(
            ScreenshotTriggerType.ERROR_DESCRIPTION, 5, "error 2"
        )

        assert s1.suggestion_id != s2.suggestion_id


class TestScreenshotCaptureGuide:
    """Test suite for ScreenshotCaptureGuide."""

    def test_get_guidance_returns_list(self):
        """Test that guidance returns non-empty list."""
        guidance = ScreenshotCaptureGuide.get_guidance()

        assert isinstance(guidance, list)
        assert len(guidance) > 0
        assert all(isinstance(step, str) for step in guidance)

    def test_get_quick_tip_returns_string(self):
        """Test that quick tip returns string."""
        tip = ScreenshotCaptureGuide.get_quick_tip()

        assert isinstance(tip, str)
        assert len(tip) > 0
        assert "screenshot" in tip.lower() or "capture" in tip.lower()

    def test_platform_specific_guidance(self):
        """Test that guidance includes platform keywords."""
        guidance = ScreenshotCaptureGuide.get_guidance()
        all_text = " ".join(guidance).lower()

        # Should mention at least one platform-specific keyword
        platform_keywords = ["cmd", "win", "prtscn", "shift", "screenshot"]
        assert any(keyword in all_text for keyword in platform_keywords)


class TestProactiveScreenshotAssistant:
    """Test suite for ProactiveScreenshotAssistant."""

    def test_analyze_message_with_error(self):
        """Test analyzing message containing error."""
        assistant = ProactiveScreenshotAssistant()

        suggestion = assistant.analyze_message("I'm seeing this error message")

        assert suggestion is not None
        assert suggestion.trigger_type == ScreenshotTriggerType.ERROR_DESCRIPTION
        assert suggestion.priority >= 4

    def test_analyze_message_with_ui_issue(self):
        """Test analyzing message with UI problem."""
        assistant = ProactiveScreenshotAssistant()

        suggestion = assistant.analyze_message("The button looks misaligned")

        assert suggestion is not None
        assert suggestion.trigger_type == ScreenshotTriggerType.UI_ISSUE

    def test_analyze_message_no_trigger(self):
        """Test message that shouldn't trigger screenshot."""
        assistant = ProactiveScreenshotAssistant()

        suggestion = assistant.analyze_message("What is Python?")

        assert suggestion is None

    def test_analyze_with_context(self):
        """Test analyzing with debug context."""
        assistant = ProactiveScreenshotAssistant()

        context = {"is_debugging": True}
        suggestion = assistant.analyze_message("What's happening?", context=context)

        assert suggestion is not None
        assert suggestion.trigger_type == ScreenshotTriggerType.DEBUG_SESSION

    def test_format_suggestion_message(self):
        """Test formatting suggestion as message."""
        assistant = ProactiveScreenshotAssistant()

        suggestion = assistant.analyze_message("I see an error")
        formatted = assistant.format_suggestion_message(suggestion)

        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "💡" in formatted  # Emoji indicator
        assert "How to capture" in formatted
        assert any(str(i) in formatted for i in range(1, 6))  # Numbered steps

    def test_statistics_tracking(self):
        """Test statistics collection."""
        assistant = ProactiveScreenshotAssistant()

        # No suggestions yet
        stats = assistant.get_statistics()
        assert stats["total_suggestions"] == 0

        # Make some suggestions
        assistant.analyze_message("I see an error")
        assistant.analyze_message("Button looks wrong")
        assistant.analyze_message("App crashed")

        stats = assistant.get_statistics()
        assert stats["total_suggestions"] == 3
        assert len(stats["by_trigger_type"]) > 0
        assert stats["avg_priority"] > 0

    def test_multiple_suggestions_tracked(self):
        """Test that multiple suggestions are tracked."""
        assistant = ProactiveScreenshotAssistant()

        assistant.analyze_message("Error 1")
        assistant.analyze_message("Error 2")
        assistant.analyze_message("UI issue")

        assert len(assistant.suggestions_made) == 3

    def test_suggestion_priority_levels(self):
        """Test different priority levels."""
        assistant = ProactiveScreenshotAssistant()

        # High priority: error
        s1 = assistant.analyze_message("I'm getting an error")
        # Medium priority: UI issue
        s2 = assistant.analyze_message("The layout looks odd")

        assert s1.priority > s2.priority


class TestScreenshotSuggestion:
    """Test ScreenshotSuggestion dataclass."""

    def test_create_suggestion(self):
        """Test creating a screenshot suggestion."""
        suggestion = ScreenshotSuggestion(
            suggestion_id="test123",
            trigger_type=ScreenshotTriggerType.ERROR_DESCRIPTION,
            message="Please share a screenshot",
            reason="To diagnose the error",
            priority=5,
            guidance_steps=["Step 1", "Step 2"],
            created_at=datetime.now(),
            context={"test": "data"}
        )

        assert suggestion.suggestion_id == "test123"
        assert suggestion.trigger_type == ScreenshotTriggerType.ERROR_DESCRIPTION
        assert suggestion.priority == 5
        assert len(suggestion.guidance_steps) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_message(self):
        """Test handling empty message."""
        assistant = ProactiveScreenshotAssistant()

        suggestion = assistant.analyze_message("")
        assert suggestion is None

    def test_very_long_message(self):
        """Test handling very long messages."""
        assistant = ProactiveScreenshotAssistant()

        long_message = "I see an error " * 100
        suggestion = assistant.analyze_message(long_message)

        assert suggestion is not None  # Should still detect "error"

    def test_special_characters(self):
        """Test handling special characters."""
        assistant = ProactiveScreenshotAssistant()

        message = "I'm seeing this @#$% error!!!"
        suggestion = assistant.analyze_message(message)

        assert suggestion is not None

    def test_mixed_triggers(self):
        """Test message with multiple potential triggers."""
        assistant = ProactiveScreenshotAssistant()

        # Contains both error and UI keywords
        message = "The button shows an error message"
        suggestion = assistant.analyze_message(message)

        # Should prioritize error over UI
        assert suggestion is not None
        assert suggestion.trigger_type == ScreenshotTriggerType.ERROR_DESCRIPTION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
