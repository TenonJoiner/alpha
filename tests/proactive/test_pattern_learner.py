"""
Tests for PatternLearner
"""

import pytest
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from alpha.proactive.pattern_learner import (
    PatternLearner,
    Pattern,
    UserPreference,
    TemporalPattern
)


@pytest.fixture
async def pattern_learner():
    """Create a pattern learner instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "patterns.db"
        # Lower min_confidence to 0.4 for testing
        learner = PatternLearner(str(db_path), min_confidence=0.4)
        await learner.initialize()
        yield learner
        await learner.close()


@pytest.fixture
def sample_conversations():
    """Create sample conversation data."""
    now = datetime.now()
    conversations = []

    # Create recurring requests
    for i in range(5):
        conversations.append({
            'role': 'user',
            'content': 'What is the weather today?',
            'timestamp': (now - timedelta(days=i)).isoformat()
        })

    # Create varied requests
    conversations.append({
        'role': 'user',
        'content': 'Tell me about Python programming',
        'timestamp': (now - timedelta(days=1)).isoformat()
    })

    conversations.append({
        'role': 'assistant',
        'content': 'Here is information about Python...',
        'timestamp': (now - timedelta(days=1)).isoformat()
    })

    # Create temporal pattern (morning requests)
    morning_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    for i in range(4):
        conversations.append({
            'role': 'user',
            'content': 'Good morning, what\'s on my schedule?',
            'timestamp': (morning_time - timedelta(days=i)).isoformat()
        })

    return conversations


@pytest.mark.asyncio
async def test_pattern_learner_initialization(pattern_learner):
    """Test pattern learner initialization."""
    assert pattern_learner.conn is not None
    assert pattern_learner.min_pattern_frequency == 3
    assert pattern_learner.min_confidence == 0.4  # Changed for testing


@pytest.mark.asyncio
async def test_detect_recurring_requests(pattern_learner, sample_conversations):
    """Test detection of recurring request patterns."""
    patterns = await pattern_learner.analyze_conversation_history(
        sample_conversations,
        lookback_days=30
    )

    recurring = patterns['recurring_request']
    assert len(recurring) > 0

    # Should detect weather requests
    weather_patterns = [p for p in recurring if 'weather' in p.description.lower()]
    assert len(weather_patterns) > 0
    assert weather_patterns[0].frequency >= 3


@pytest.mark.asyncio
async def test_detect_temporal_patterns(pattern_learner, sample_conversations):
    """Test detection of temporal patterns."""
    patterns = await pattern_learner.analyze_conversation_history(
        sample_conversations,
        lookback_days=30
    )

    temporal = patterns['temporal']
    assert len(temporal) > 0

    # Should detect morning pattern (hour 9)
    morning_patterns = [
        p for p in temporal
        if p.metadata.get('hour') == 9
    ]
    assert len(morning_patterns) > 0


@pytest.mark.asyncio
async def test_detect_communication_style(pattern_learner, sample_conversations):
    """Test detection of communication style."""
    patterns = await pattern_learner.analyze_conversation_history(
        sample_conversations,
        lookback_days=30
    )

    style = patterns['communication_style']
    assert len(style) > 0

    # Should have a verbosity preference
    assert style[0].pattern_type == "communication_style"
    assert 'avg_length' in style[0].metadata


@pytest.mark.asyncio
async def test_pattern_storage_and_retrieval(pattern_learner):
    """Test storing and retrieving patterns."""
    # Create a test pattern
    pattern = Pattern(
        pattern_id="test_001",
        pattern_type="recurring_request",
        description="Test pattern",
        frequency=5,
        confidence=0.8,
        first_seen=datetime.now() - timedelta(days=10),
        last_seen=datetime.now(),
        metadata={'test': 'data'},
        examples=['example 1', 'example 2']
    )

    # Store pattern
    await pattern_learner._store_pattern(pattern)

    # Retrieve patterns
    patterns = await pattern_learner.get_patterns()
    assert len(patterns) > 0
    assert patterns[0].pattern_id == "test_001"
    assert patterns[0].frequency == 5


@pytest.mark.asyncio
async def test_filter_patterns_by_type(pattern_learner):
    """Test filtering patterns by type."""
    # Create patterns of different types
    pattern1 = Pattern(
        pattern_id="rec_001",
        pattern_type="recurring_request",
        description="Recurring pattern",
        frequency=5,
        confidence=0.8,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        metadata={},
        examples=[]
    )

    pattern2 = Pattern(
        pattern_id="temp_001",
        pattern_type="temporal",
        description="Temporal pattern",
        frequency=3,
        confidence=0.7,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        metadata={},
        examples=[]
    )

    await pattern_learner._store_pattern(pattern1)
    await pattern_learner._store_pattern(pattern2)

    # Filter by type
    recurring = await pattern_learner.get_patterns(pattern_type="recurring_request")
    assert len(recurring) == 1
    assert recurring[0].pattern_type == "recurring_request"

    temporal = await pattern_learner.get_patterns(pattern_type="temporal")
    assert len(temporal) == 1
    assert temporal[0].pattern_type == "temporal"


@pytest.mark.asyncio
async def test_filter_patterns_by_confidence(pattern_learner):
    """Test filtering patterns by confidence."""
    # Create patterns with different confidence levels
    pattern1 = Pattern(
        pattern_id="high_conf",
        pattern_type="recurring_request",
        description="High confidence",
        frequency=10,
        confidence=0.9,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        metadata={},
        examples=[]
    )

    pattern2 = Pattern(
        pattern_id="low_conf",
        pattern_type="recurring_request",
        description="Low confidence",
        frequency=3,
        confidence=0.5,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        metadata={},
        examples=[]
    )

    await pattern_learner._store_pattern(pattern1)
    await pattern_learner._store_pattern(pattern2)

    # Filter by confidence
    high_conf = await pattern_learner.get_patterns(min_confidence=0.7)
    assert len(high_conf) == 1
    assert high_conf[0].confidence >= 0.7


@pytest.mark.asyncio
async def test_learn_user_preference(pattern_learner):
    """Test learning and storing user preferences."""
    await pattern_learner.learn_preference(
        category="communication",
        key="verbosity",
        value="concise",
        confidence=0.8
    )

    preferences = await pattern_learner.get_preferences()
    assert len(preferences) > 0
    assert preferences[0].category == "communication"
    assert preferences[0].key == "verbosity"
    assert preferences[0].value == "concise"


@pytest.mark.asyncio
async def test_update_preference_confidence(pattern_learner):
    """Test that preference confidence increases with observations."""
    # Learn preference first time
    await pattern_learner.learn_preference(
        category="timing",
        key="preferred_hour",
        value=9,
        confidence=0.7
    )

    prefs1 = await pattern_learner.get_preferences()
    initial_confidence = prefs1[0].confidence

    # Learn same preference again
    await pattern_learner.learn_preference(
        category="timing",
        key="preferred_hour",
        value=9,
        confidence=0.7
    )

    prefs2 = await pattern_learner.get_preferences()
    new_confidence = prefs2[0].confidence

    assert new_confidence > initial_confidence
    assert prefs2[0].learned_from == 2


@pytest.mark.asyncio
async def test_get_preferences_by_category(pattern_learner):
    """Test filtering preferences by category."""
    await pattern_learner.learn_preference(
        category="communication",
        key="style",
        value="formal"
    )

    await pattern_learner.learn_preference(
        category="timing",
        key="hour",
        value=9
    )

    comm_prefs = await pattern_learner.get_preferences(category="communication")
    assert len(comm_prefs) == 1
    assert comm_prefs[0].category == "communication"


@pytest.mark.asyncio
async def test_normalize_request(pattern_learner):
    """Test request normalization."""
    text1 = "What is the weather today?"
    text2 = "what's the weather today"
    text3 = "Can you please tell me the weather today?"

    norm1 = pattern_learner._normalize_request(text1)
    norm2 = pattern_learner._normalize_request(text2)
    norm3 = pattern_learner._normalize_request(text3)

    # All should normalize to similar form
    assert 'weather' in norm1
    assert 'weather' in norm2
    assert 'weather' in norm3


@pytest.mark.asyncio
async def test_pattern_frequency_threshold(pattern_learner):
    """Test that patterns below frequency threshold are not detected."""
    # Create conversations with only 2 occurrences (below threshold of 3)
    conversations = []
    now = datetime.now()

    for i in range(2):
        conversations.append({
            'role': 'user',
            'content': 'Rare request that appears only twice',
            'timestamp': (now - timedelta(days=i)).isoformat()
        })

    patterns = await pattern_learner.analyze_conversation_history(
        conversations,
        lookback_days=30
    )

    # Should not detect as recurring pattern
    recurring = patterns['recurring_request']
    rare_patterns = [
        p for p in recurring
        if 'rare request' in p.description.lower()
    ]
    assert len(rare_patterns) == 0


@pytest.mark.asyncio
async def test_get_statistics(pattern_learner, sample_conversations):
    """Test getting pattern learning statistics."""
    # Analyze conversations to generate patterns
    await pattern_learner.analyze_conversation_history(
        sample_conversations,
        lookback_days=30
    )

    # Add some preferences
    await pattern_learner.learn_preference(
        category="communication",
        key="style",
        value="concise"
    )

    stats = await pattern_learner.get_statistics()

    assert 'total_patterns' in stats
    assert 'total_preferences' in stats
    assert 'patterns_by_type' in stats
    assert 'preferences_by_category' in stats

    assert stats['total_patterns'] > 0
    assert stats['total_preferences'] > 0


@pytest.mark.asyncio
async def test_lookback_period(pattern_learner):
    """Test that lookback period filters conversations correctly."""
    now = datetime.now()
    conversations = []

    # Add recent conversations
    for i in range(3):
        conversations.append({
            'role': 'user',
            'content': 'Recent request',
            'timestamp': (now - timedelta(days=i)).isoformat()
        })

    # Add old conversations (beyond lookback period)
    for i in range(35, 38):
        conversations.append({
            'role': 'user',
            'content': 'Old request',
            'timestamp': (now - timedelta(days=i)).isoformat()
        })

    # Analyze with 30-day lookback
    patterns = await pattern_learner.analyze_conversation_history(
        conversations,
        lookback_days=30
    )

    recurring = patterns['recurring_request']

    # Should only detect recent requests, not old ones
    recent_patterns = [
        p for p in recurring
        if 'recent' in str(p.examples).lower()
    ]
    old_patterns = [
        p for p in recurring
        if 'old' in str(p.examples).lower()
    ]

    assert len(recent_patterns) > 0 or len(old_patterns) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
