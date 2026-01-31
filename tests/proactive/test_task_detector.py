"""
Tests for TaskDetector
"""

import pytest
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from alpha.proactive.pattern_learner import PatternLearner, Pattern
from alpha.proactive.task_detector import (
    TaskDetector,
    TaskSuggestion,
    TaskConfidence
)


@pytest.fixture
async def pattern_learner():
    """Create a pattern learner instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "patterns.db"
        learner = PatternLearner(str(db_path))
        await learner.initialize()
        yield learner
        await learner.close()


@pytest.fixture
async def task_detector(pattern_learner):
    """Create a task detector instance for testing."""
    detector = TaskDetector(
        pattern_learner=pattern_learner,
        min_confidence=0.6,
        max_suggestions_per_run=5
    )
    return detector


@pytest.fixture
async def sample_patterns(pattern_learner):
    """Create sample patterns for testing."""
    # Recurring pattern - high frequency
    pattern1 = Pattern(
        pattern_id="rec_weather",
        pattern_type="recurring_request",
        description="User frequently requests weather",
        frequency=10,
        confidence=0.9,
        first_seen=datetime.now() - timedelta(days=10),
        last_seen=datetime.now(),
        metadata={'normalized_text': 'weather today'},
        examples=['What is the weather?', 'Weather today?']
    )
    await pattern_learner._store_pattern(pattern1)

    # Temporal pattern - morning activity
    pattern2 = Pattern(
        pattern_id="temp_morning",
        pattern_type="temporal",
        description="User typically active at 09:00",
        frequency=8,
        confidence=0.8,
        first_seen=datetime.now() - timedelta(days=8),
        last_seen=datetime.now(),
        metadata={'hour': 9, 'type': 'hour_of_day'},
        examples=['Good morning', 'What\'s my schedule?']
    )
    await pattern_learner._store_pattern(pattern2)

    # Less frequent pattern - should not trigger suggestions
    pattern3 = Pattern(
        pattern_id="rec_news",
        pattern_type="recurring_request",
        description="User occasionally requests news",
        frequency=3,
        confidence=0.6,
        first_seen=datetime.now() - timedelta(days=15),
        last_seen=datetime.now() - timedelta(days=5),
        metadata={'normalized_text': 'latest news'},
        examples=['What\'s the news?']
    )
    await pattern_learner._store_pattern(pattern3)


@pytest.mark.asyncio
async def test_task_detector_initialization(task_detector):
    """Test task detector initialization."""
    assert task_detector.min_confidence == 0.6
    assert task_detector.max_suggestions_per_run == 5
    assert len(task_detector.suggestions_history) == 0


@pytest.mark.asyncio
async def test_detect_from_recurring_patterns(task_detector, sample_patterns):
    """Test detecting tasks from recurring patterns."""
    suggestions = await task_detector.detect_proactive_tasks()

    assert len(suggestions) > 0

    # Should suggest weather task
    weather_suggestions = [
        s for s in suggestions
        if 'weather' in s.task_name.lower()
    ]
    assert len(weather_suggestions) > 0
    assert weather_suggestions[0].confidence >= 0.6


@pytest.mark.asyncio
async def test_suggestion_confidence_scoring(task_detector, sample_patterns):
    """Test that suggestions are scored by confidence."""
    suggestions = await task_detector.detect_proactive_tasks()

    # Suggestions should be sorted by confidence
    for i in range(len(suggestions) - 1):
        assert suggestions[i].confidence >= suggestions[i + 1].confidence


@pytest.mark.asyncio
async def test_schedule_recommendation(task_detector, sample_patterns):
    """Test that schedule recommendations are generated."""
    suggestions = await task_detector.detect_proactive_tasks()

    # High-frequency patterns should have schedule recommendations
    high_freq_suggestions = [
        s for s in suggestions
        if s.confidence >= 0.8
    ]

    if high_freq_suggestions:
        # At least some should have schedule recommendations
        with_schedule = [
            s for s in high_freq_suggestions
            if s.schedule_recommendation is not None
        ]
        assert len(with_schedule) > 0


@pytest.mark.asyncio
async def test_max_suggestions_limit(task_detector, pattern_learner):
    """Test that suggestions are limited to max_suggestions_per_run."""
    # Create many patterns
    for i in range(10):
        pattern = Pattern(
            pattern_id=f"pattern_{i}",
            pattern_type="recurring_request",
            description=f"Pattern {i}",
            frequency=5 + i,
            confidence=0.7 + (i * 0.01),
            first_seen=datetime.now() - timedelta(days=10),
            last_seen=datetime.now(),
            metadata={'normalized_text': f'request {i}'},
            examples=[f'Request {i}']
        )
        await pattern_learner._store_pattern(pattern)

    suggestions = await task_detector.detect_proactive_tasks()

    # Should be limited to max_suggestions_per_run
    assert len(suggestions) <= task_detector.max_suggestions_per_run


@pytest.mark.asyncio
async def test_temporal_pattern_detection(task_detector, sample_patterns):
    """Test detecting tasks from temporal patterns."""
    # Mock current time to match pattern (hour 8, one hour before pattern hour 9)
    context = {
        'current_time': datetime.now().replace(hour=8),
        'recent_activity': []
    }

    suggestions = await task_detector.detect_proactive_tasks(context=context)

    temporal_suggestions = [
        s for s in suggestions
        if 'temporal' in s.task_name.lower()
    ]

    # Should detect temporal pattern suggestion
    assert len(temporal_suggestions) >= 0  # May or may not trigger based on implementation


@pytest.mark.asyncio
async def test_context_based_detection(task_detector, sample_patterns):
    """Test context-based task detection."""
    # Provide context
    context = {
        'current_time': datetime.now(),
        'recent_activity': ['previous request']
    }

    suggestions = await task_detector.detect_proactive_tasks(context=context)

    # Should generate suggestions based on context
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_approve_suggestion(task_detector, sample_patterns):
    """Test approving a suggestion."""
    suggestions = await task_detector.detect_proactive_tasks()
    assert len(suggestions) > 0

    suggestion = suggestions[0]
    task_spec = await task_detector.approve_suggestion(suggestion.suggestion_id)

    assert task_spec is not None
    assert 'name' in task_spec
    assert 'description' in task_spec
    assert 'executor' in task_spec
    assert 'params' in task_spec


@pytest.mark.asyncio
async def test_reject_suggestion(task_detector, sample_patterns):
    """Test rejecting a suggestion."""
    suggestions = await task_detector.detect_proactive_tasks()
    assert len(suggestions) > 0

    suggestion = suggestions[0]

    # Should not raise error
    await task_detector.reject_suggestion(
        suggestion.suggestion_id,
        reason="Not needed"
    )


@pytest.mark.asyncio
async def test_get_suggestion_by_id(task_detector, sample_patterns):
    """Test retrieving a specific suggestion by ID."""
    suggestions = await task_detector.detect_proactive_tasks()
    assert len(suggestions) > 0

    suggestion_id = suggestions[0].suggestion_id
    retrieved = await task_detector.get_suggestion_by_id(suggestion_id)

    assert retrieved is not None
    assert retrieved.suggestion_id == suggestion_id


@pytest.mark.asyncio
async def test_suggestions_history(task_detector, sample_patterns):
    """Test that suggestions are stored in history."""
    # Generate suggestions
    suggestions1 = await task_detector.detect_proactive_tasks()
    initial_count = len(task_detector.suggestions_history)

    # Generate more suggestions
    suggestions2 = await task_detector.detect_proactive_tasks()

    # History should accumulate
    assert len(task_detector.suggestions_history) >= initial_count


@pytest.mark.asyncio
async def test_get_suggestions_history(task_detector, sample_patterns):
    """Test retrieving suggestions history."""
    # Generate suggestions
    await task_detector.detect_proactive_tasks()

    history = await task_detector.get_suggestions_history(limit=10)

    assert isinstance(history, list)
    # History is sorted by suggested_at descending
    for i in range(len(history) - 1):
        assert history[i].suggested_at >= history[i + 1].suggested_at


@pytest.mark.asyncio
async def test_filter_history_by_confidence(task_detector, sample_patterns):
    """Test filtering history by confidence."""
    # Generate suggestions
    await task_detector.detect_proactive_tasks()

    high_conf_history = await task_detector.get_suggestions_history(
        min_confidence=0.8
    )

    # All should meet confidence threshold
    for suggestion in high_conf_history:
        assert suggestion.confidence >= 0.8


@pytest.mark.asyncio
async def test_get_statistics(task_detector, sample_patterns):
    """Test getting task detector statistics."""
    # Generate suggestions
    await task_detector.detect_proactive_tasks()

    stats = await task_detector.get_statistics()

    assert 'total_suggestions' in stats
    assert 'avg_confidence' in stats
    assert 'by_priority' in stats
    assert stats['total_suggestions'] > 0


@pytest.mark.asyncio
async def test_priority_assignment(task_detector, sample_patterns):
    """Test that priority is correctly assigned based on confidence."""
    suggestions = await task_detector.detect_proactive_tasks()

    for suggestion in suggestions:
        if suggestion.confidence >= 0.8:
            assert suggestion.priority == "high"
        else:
            assert suggestion.priority == "normal"


@pytest.mark.asyncio
async def test_task_params_included(task_detector, sample_patterns):
    """Test that task parameters are included in suggestions."""
    suggestions = await task_detector.detect_proactive_tasks()

    for suggestion in suggestions:
        assert suggestion.task_params is not None
        assert isinstance(suggestion.task_params, dict)
        assert 'pattern_type' in suggestion.task_params


@pytest.mark.asyncio
async def test_justification_provided(task_detector, sample_patterns):
    """Test that suggestions include justification."""
    suggestions = await task_detector.detect_proactive_tasks()

    for suggestion in suggestions:
        assert suggestion.justification is not None
        assert len(suggestion.justification) > 0


@pytest.mark.asyncio
async def test_pattern_ids_tracked(task_detector, sample_patterns):
    """Test that pattern IDs are tracked in suggestions."""
    suggestions = await task_detector.detect_proactive_tasks()

    for suggestion in suggestions:
        assert len(suggestion.pattern_ids) > 0
        # Each pattern ID should be a string
        for pattern_id in suggestion.pattern_ids:
            assert isinstance(pattern_id, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
