"""
Tests for Skill Optimizer

Validates skill exploration, optimization, and pruning logic.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import asyncio
from datetime import datetime, timedelta
from alpha.skills.optimizer import (
    SkillOptimizer,
    OptimizationAction,
    OptimizationRecommendation,
    ExplorationResult,
    PruningResult
)
from alpha.skills.performance_tracker import PerformanceTracker
from alpha.skills.evaluator import SmartEvaluator
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.registry import SkillRegistry
from alpha.learning.learning_store import LearningStore
from alpha.skills.base import SkillMetadata


class MockMarketplace:
    """Mock marketplace for testing."""

    async def search(self, query: str, limit: int = 10):
        """Return mock skill metadata."""
        skills = []
        for i in range(min(limit, 3)):
            skills.append(SkillMetadata(
                name=f"mock_skill_{i}",
                version="1.0.0",
                description=f"Mock skill {i} for testing",
                author="Test Author",
                category="testing",
                tags=["test", "mock"]
            ))
        return skills


class MockRegistry:
    """Mock registry for testing."""

    def __init__(self):
        self.skills = {}

    async def unregister(self, skill_id: str):
        """Mock unregister."""
        if skill_id in self.skills:
            del self.skills[skill_id]


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
    return PerformanceTracker(learning_store)


@pytest.fixture
async def evaluator():
    """Create test evaluator."""
    config = {
        "evaluation": {
            "min_quality_score": 0.6,
            "min_compatibility_score": 0.7
        }
    }
    return SmartEvaluator(config)


@pytest.fixture
async def marketplace():
    """Create mock marketplace."""
    return MockMarketplace()


@pytest.fixture
async def registry():
    """Create mock registry."""
    return MockRegistry()


@pytest.fixture
async def optimizer(tracker, evaluator, marketplace, registry):
    """Create test optimizer."""
    config = {
        "exploration": {
            "enabled": True,
            "interval_hours": 24,
            "max_skills_per_exploration": 10
        },
        "pruning": {
            "enabled": True,
            "interval_hours": 168,
            "min_uses_before_prune": 5,
            "max_unused_days": 30,
            "min_success_rate": 0.5,
            "min_overall_score": 0.4
        },
        "optimization": {
            "enabled": True,
            "interval_hours": 24,
            "top_performers_count": 10
        }
    }

    optimizer = SkillOptimizer(
        performance_tracker=tracker,
        skill_evaluator=evaluator,
        marketplace=marketplace,
        registry=registry,
        config=config
    )

    yield optimizer
    await optimizer.stop()


@pytest.mark.asyncio
async def test_optimizer_initialization(optimizer):
    """Test optimizer initializes correctly."""
    assert optimizer.exploration_enabled is True
    assert optimizer.pruning_enabled is True
    assert optimizer.optimization_enabled is True
    assert optimizer.exploration_interval_hours == 24


@pytest.mark.asyncio
async def test_explore_marketplace(optimizer):
    """Test marketplace exploration."""
    result = await optimizer.explore_marketplace()

    assert isinstance(result, ExplorationResult)
    assert result.skills_discovered >= 0
    assert result.skills_evaluated >= 0
    assert isinstance(result.recommendations, list)


@pytest.mark.asyncio
async def test_exploration_discovers_new_skills(optimizer):
    """Test that exploration discovers new skills."""
    result = await optimizer.explore_marketplace()

    # Should discover mock skills
    assert result.skills_discovered > 0
    assert len(optimizer.known_skills) > 0


@pytest.mark.asyncio
async def test_exploration_deduplicates_skills(optimizer):
    """Test that known skills are not re-evaluated."""
    # First exploration
    result1 = await optimizer.explore_marketplace()
    discovered1 = result1.skills_discovered

    # Second exploration (should not rediscover same skills)
    result2 = await optimizer.explore_marketplace()
    discovered2 = result2.skills_discovered

    # Second exploration should discover fewer or same (already known)
    assert discovered2 <= discovered1


@pytest.mark.asyncio
async def test_generate_recommendation_high_quality(optimizer, evaluator):
    """Test recommendation for high quality skill."""
    # Create high-quality evaluation
    metadata = {
        "name": "test_skill",
        "version": "1.0.0",
        "description": "Test skill",
        "author": "Test",
        "category": "development"
    }

    evaluation = await evaluator.evaluate_skill(metadata)

    # Manually set high scores
    evaluation.overall_score = 0.8
    evaluation.compatibility_score = 0.8

    recommendation = optimizer._generate_recommendation("test_skill", evaluation)

    assert recommendation.action == OptimizationAction.ACTIVATE
    assert recommendation.priority > 0.5


@pytest.mark.asyncio
async def test_generate_recommendation_moderate_quality(optimizer, evaluator):
    """Test recommendation for moderate quality skill."""
    metadata = {
        "name": "test_skill",
        "version": "1.0.0",
        "description": "Test",
        "author": "Test",
        "category": "general"
    }

    evaluation = await evaluator.evaluate_skill(metadata)

    # Set moderate scores
    evaluation.overall_score = 0.6
    evaluation.compatibility_score = 0.6

    recommendation = optimizer._generate_recommendation("test_skill", evaluation)

    assert recommendation.action == OptimizationAction.MONITOR


@pytest.mark.asyncio
async def test_generate_recommendation_low_quality(optimizer, evaluator):
    """Test recommendation for low quality skill."""
    metadata = {
        "name": "test_skill",
        "version": "0.1.0",
        "description": "",
        "author": "",
        "category": ""
    }

    evaluation = await evaluator.evaluate_skill(metadata)

    # Set low scores
    evaluation.overall_score = 0.3
    evaluation.compatibility_score = 0.3

    recommendation = optimizer._generate_recommendation("test_skill", evaluation)

    assert recommendation.action == OptimizationAction.NO_ACTION


@pytest.mark.asyncio
async def test_optimize_skills(optimizer, tracker):
    """Test skill optimization."""
    # Add some performance data
    for i in range(3):
        for _ in range(5):
            await tracker.record_execution(
                f"skill_{i}", True, 1.0,
                cost_estimate=0.001
            )

    # Run optimization
    await optimizer.optimize_skills()

    # Should complete without errors
    assert True


@pytest.mark.asyncio
async def test_prune_skills_dry_run(optimizer, tracker):
    """Test pruning in dry-run mode."""
    # Create underperforming skill
    for _ in range(10):
        await tracker.record_execution("bad_skill", False, 5.0)

    result = await optimizer.prune_skills(dry_run=True)

    assert isinstance(result, PruningResult)
    assert result.skills_evaluated >= 0


@pytest.mark.asyncio
async def test_prune_skills_low_success_rate(optimizer, tracker):
    """Test pruning skill with low success rate."""
    # Create skill with low success rate (< 50%)
    for i in range(20):
        await tracker.record_execution(
            "low_success_skill",
            success=(i < 5),  # 25% success rate
            execution_time=1.0
        )

    result = await optimizer.prune_skills(dry_run=True)

    # Should identify for pruning
    assert "low_success_skill" in result.pruned_skills


@pytest.mark.asyncio
async def test_prune_skills_inactive(optimizer, tracker):
    """Test pruning inactive skill."""
    # Create skill and mark it as old
    await tracker.record_execution("inactive_skill", True, 1.0)

    stats = tracker.stats_cache["inactive_skill"]
    stats.last_used = datetime.now() - timedelta(days=35)
    stats.total_executions = 10  # Enough data

    result = await optimizer.prune_skills(dry_run=True)

    # Should identify for pruning
    assert "inactive_skill" in result.pruned_skills


@pytest.mark.asyncio
async def test_prune_skills_skips_insufficient_data(optimizer, tracker):
    """Test pruning skips skills without enough data."""
    # Create skill with insufficient executions
    await tracker.record_execution("new_skill", True, 1.0)

    result = await optimizer.prune_skills(dry_run=True)

    # Should not prune (not enough data)
    assert "new_skill" not in result.pruned_skills


@pytest.mark.asyncio
async def test_get_recommendations(optimizer):
    """Test getting recommendations."""
    # Run exploration to generate recommendations
    await optimizer.explore_marketplace()

    recommendations = optimizer.get_recommendations()

    assert isinstance(recommendations, list)


@pytest.mark.asyncio
async def test_get_recommendations_filtered_by_action(optimizer):
    """Test filtering recommendations by action type."""
    await optimizer.explore_marketplace()

    activate_recs = optimizer.get_recommendations(
        action_type=OptimizationAction.ACTIVATE
    )

    assert isinstance(activate_recs, list)
    # All should be ACTIVATE action
    for rec in activate_recs:
        assert rec.action == OptimizationAction.ACTIVATE


@pytest.mark.asyncio
async def test_get_recommendations_filtered_by_priority(optimizer):
    """Test filtering recommendations by priority."""
    await optimizer.explore_marketplace()

    high_priority = optimizer.get_recommendations(min_priority=0.7)

    assert isinstance(high_priority, list)
    # All should have priority >= 0.7
    for rec in high_priority:
        assert rec.priority >= 0.7


@pytest.mark.asyncio
async def test_optimization_summary(optimizer):
    """Test optimization summary."""
    # Run some operations
    await optimizer.explore_marketplace()

    summary = await optimizer.get_optimization_summary()

    assert "exploration" in summary
    assert "pruning" in summary
    assert "recommendations" in summary
    assert summary["exploration"]["total_explorations"] >= 0


@pytest.mark.asyncio
async def test_start_stop_processes(optimizer):
    """Test starting and stopping background processes."""
    await optimizer.start()

    # Processes should be created
    assert optimizer._running is True

    await optimizer.stop()

    # Should be stopped
    assert optimizer._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
