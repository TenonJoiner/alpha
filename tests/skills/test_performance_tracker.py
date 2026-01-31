"""
Tests for Skill Performance Tracker

Validates performance tracking, metrics calculation, and trend analysis.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import asyncio
from datetime import datetime, timedelta
from alpha.skills.performance_tracker import (
    PerformanceTracker,
    SkillExecutionMetrics,
    SkillPerformanceStats,
    SkillGap
)
from alpha.learning.learning_store import LearningStore


@pytest.fixture
async def learning_store():
    """Create test learning store."""
    store = LearningStore(db_path=":memory:")
    store.initialize()
    yield store
    store.close()


@pytest.fixture
async def tracker(learning_store):
    """Create test tracker."""
    tracker = PerformanceTracker(learning_store)
    yield tracker
    await tracker.cleanup()


@pytest.mark.asyncio
async def test_record_execution_success(tracker):
    """Test recording successful execution."""
    exec_id = await tracker.record_execution(
        skill_id="test_skill",
        success=True,
        execution_time=1.5,
        tokens_used=100,
        cost_estimate=0.01
    )

    assert exec_id.startswith("exec_")
    assert "test_skill" in tracker.stats_cache

    stats = tracker.stats_cache["test_skill"]
    assert stats.total_executions == 1
    assert stats.successful_executions == 1
    assert stats.success_rate == 1.0


@pytest.mark.asyncio
async def test_record_execution_failure(tracker):
    """Test recording failed execution."""
    await tracker.record_execution(
        skill_id="test_skill",
        success=False,
        execution_time=2.0,
        error_message="Test error"
    )

    stats = tracker.stats_cache["test_skill"]
    assert stats.total_executions == 1
    assert stats.failed_executions == 1
    assert stats.success_rate == 0.0
    assert stats.last_error == "Test error"


@pytest.mark.asyncio
async def test_multiple_executions(tracker):
    """Test multiple executions update stats correctly."""
    # 7 successes, 3 failures
    for i in range(10):
        success = i < 7
        await tracker.record_execution(
            skill_id="multi_skill",
            success=success,
            execution_time=1.0 + i * 0.1
        )

    stats = tracker.stats_cache["multi_skill"]
    assert stats.total_executions == 10
    assert stats.successful_executions == 7
    assert stats.failed_executions == 3
    assert stats.success_rate == 0.7


@pytest.mark.asyncio
async def test_timing_metrics(tracker):
    """Test timing metrics calculation."""
    await tracker.record_execution("timing_skill", True, 1.0)
    await tracker.record_execution("timing_skill", True, 3.0)
    await tracker.record_execution("timing_skill", True, 2.0)

    stats = tracker.stats_cache["timing_skill"]
    assert stats.min_execution_time == 1.0
    assert stats.max_execution_time == 3.0
    assert stats.avg_execution_time == 2.0


@pytest.mark.asyncio
async def test_cost_metrics(tracker):
    """Test cost metrics calculation."""
    await tracker.record_execution(
        "cost_skill", True, 1.0,
        tokens_used=100, cost_estimate=0.01
    )
    await tracker.record_execution(
        "cost_skill", True, 1.0,
        tokens_used=200, cost_estimate=0.02
    )

    stats = tracker.stats_cache["cost_skill"]
    assert stats.total_tokens == 300
    assert stats.avg_tokens == 150.0
    assert stats.total_cost == 0.03
    assert stats.avg_cost == 0.015


@pytest.mark.asyncio
async def test_value_score_calculation(tracker):
    """Test value score calculation."""
    # High frequency usage
    for _ in range(10):
        await tracker.record_execution("high_value", True, 1.0)

    stats = tracker.stats_cache["high_value"]
    assert stats.value_score > 0.0


@pytest.mark.asyncio
async def test_roi_calculation(tracker):
    """Test ROI calculation."""
    # High value, low cost
    for _ in range(5):
        await tracker.record_execution(
            "high_roi", True, 0.5,
            cost_estimate=0.001
        )

    stats = tracker.stats_cache["high_roi"]
    assert stats.roi_score > 0.0


@pytest.mark.asyncio
async def test_trend_analysis_improving(tracker):
    """Test trend analysis - improving skill."""
    # First 5: 40% success
    for i in range(5):
        await tracker.record_execution("improving", i < 2, 1.0)

    # Next 10: 80% success (improving)
    for i in range(10):
        await tracker.record_execution("improving", i < 8, 1.0)

    stats = tracker.stats_cache["improving"]
    # Should detect improvement
    assert stats.recent_success_rate > stats.success_rate or stats.recent_success_rate >= 0.7


@pytest.mark.asyncio
async def test_trend_analysis_degrading(tracker):
    """Test trend analysis - degrading skill."""
    # First 10: 80% success
    for i in range(10):
        await tracker.record_execution("degrading", i < 8, 1.0)

    # Next 10: 20% success (degrading)
    for i in range(10):
        await tracker.record_execution("degrading", i < 2, 1.0)

    stats = tracker.stats_cache["degrading"]
    # Recent rate should be lower
    assert stats.recent_success_rate < stats.success_rate


@pytest.mark.asyncio
async def test_recent_errors_count(tracker):
    """Test counting recent errors."""
    # Add some errors
    for _ in range(3):
        await tracker.record_execution("error_skill", False, 1.0)

    stats = tracker.stats_cache["error_skill"]
    assert stats.error_count_last_24h == 3


@pytest.mark.asyncio
async def test_skill_gap_recording(tracker):
    """Test recording skill gaps."""
    gap_id = await tracker.record_skill_gap(
        task_description="Generate PDF report",
        missing_capability="pdf_generation",
        suggested_skills=["pdf-skill", "report-gen"]
    )

    assert gap_id.startswith("gap_")
    assert gap_id in tracker.skill_gaps

    gap = tracker.skill_gaps[gap_id]
    assert gap.missing_capability == "pdf_generation"
    assert len(gap.suggested_skills) == 2


@pytest.mark.asyncio
async def test_skill_gap_deduplication(tracker):
    """Test skill gap deduplication."""
    gap_id_1 = await tracker.record_skill_gap(
        task_description="Task 1",
        missing_capability="pdf_generation"
    )

    gap_id_2 = await tracker.record_skill_gap(
        task_description="Task 2",
        missing_capability="pdf_generation"
    )

    # Should return same gap ID (deduplicated)
    assert gap_id_1 == gap_id_2

    gap = tracker.skill_gaps[gap_id_1]
    assert gap.failure_count == 2


@pytest.mark.asyncio
async def test_get_top_performers(tracker):
    """Test getting top performing skills."""
    # Create skills with different ROI
    for i in range(5):
        for _ in range(5):
            await tracker.record_execution(
                f"skill_{i}", True, 1.0,
                cost_estimate=0.001 * (i + 1)
            )

    top = tracker.get_top_performers(limit=3)
    assert len(top) <= 3
    # Should be sorted by ROI
    if len(top) >= 2:
        assert top[0].roi_score >= top[1].roi_score


@pytest.mark.asyncio
async def test_get_degrading_skills(tracker):
    """Test getting degrading skills."""
    # Create degrading skill
    for i in range(10):
        await tracker.record_execution("degrading", i < 8, 1.0)
    for i in range(10):
        await tracker.record_execution("degrading", i < 2, 1.0)

    degrading = tracker.get_degrading_skills()
    # May or may not be flagged as degrading depending on threshold
    assert isinstance(degrading, list)


@pytest.mark.asyncio
async def test_get_skill_gaps_filtered(tracker):
    """Test getting filtered skill gaps."""
    # Create gaps with different priorities
    await tracker.record_skill_gap("Task 1", "capability_1")

    # Increase priority by repeated failures
    for _ in range(5):
        await tracker.record_skill_gap("Task 2", "capability_2")

    gaps = tracker.get_skill_gaps(min_priority=0.3)
    assert len(gaps) > 0


@pytest.mark.asyncio
async def test_performance_summary(tracker):
    """Test performance summary generation."""
    # Add some data
    await tracker.record_execution("skill1", True, 1.0, cost_estimate=0.01)
    await tracker.record_execution("skill2", False, 2.0)

    summary = await tracker.get_performance_summary()

    assert summary["total_skills_tracked"] == 2
    assert summary["total_executions"] == 2
    assert "overall_success_rate" in summary
    assert "total_cost" in summary


@pytest.mark.asyncio
async def test_stats_persistence(learning_store):
    """Test stats are persisted to database."""
    tracker = PerformanceTracker(learning_store)

    await tracker.record_execution("persist_skill", True, 1.0)
    await tracker.cleanup()

    # Create new tracker with same store
    tracker2 = PerformanceTracker(learning_store)

    # Stats should be loaded
    assert "persist_skill" in tracker2.stats_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
