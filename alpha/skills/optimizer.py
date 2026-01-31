"""
Alpha - Skill Optimizer

Skill evolution and optimization loop for continuous improvement.
Handles proactive exploration, quality assessment, automatic pruning,
and skill prioritization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json

logger = logging.getLogger(__name__)


class OptimizationAction(Enum):
    """Types of optimization actions."""
    ACTIVATE = "activate"
    MONITOR = "monitor"
    PRUNE = "prune"
    UPGRADE = "upgrade"
    DEPRIORITIZE = "deprioritize"
    NO_ACTION = "no_action"


@dataclass
class OptimizationRecommendation:
    """Recommendation from optimization analysis."""
    skill_id: str
    action: OptimizationAction
    priority: float  # 0-1, higher is more urgent
    reason: str
    expected_benefit: str
    estimated_cost: float = 0.0  # USD
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorationResult:
    """Result from marketplace exploration."""
    explored_at: datetime
    skills_discovered: int
    skills_evaluated: int
    recommendations: List[OptimizationRecommendation]
    errors: List[str] = field(default_factory=list)


@dataclass
class PruningResult:
    """Result from pruning operation."""
    pruned_at: datetime
    skills_evaluated: int
    skills_pruned: int
    pruned_skills: List[str]
    space_saved_mb: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillOptimizer:
    """
    Skill optimization system for continuous evolution.

    Features:
    - Proactive skill exploration from marketplace
    - Quality and compatibility assessment
    - Automatic pruning of underperforming skills
    - Skill prioritization and ranking
    - Cost-effectiveness analysis
    """

    def __init__(
        self,
        performance_tracker: Any,  # PerformanceTracker
        skill_evaluator: Any,  # SmartEvaluator
        marketplace: Any,  # SkillMarketplace
        registry: Any,  # SkillRegistry
        config: Dict[str, Any],
        data_dir: Path = Path("data/skill_optimization")
    ):
        """
        Initialize skill optimizer.

        Args:
            performance_tracker: PerformanceTracker instance
            skill_evaluator: SmartEvaluator instance
            marketplace: SkillMarketplace instance
            registry: SkillRegistry instance
            config: Configuration dictionary
            data_dir: Data directory for storage
        """
        self.performance_tracker = performance_tracker
        self.evaluator = skill_evaluator
        self.marketplace = marketplace
        self.registry = registry
        self.config = config
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Exploration settings
        self.exploration_enabled = config.get("exploration", {}).get("enabled", True)
        self.exploration_interval_hours = config.get("exploration", {}).get("interval_hours", 24)
        self.max_skills_per_exploration = config.get("exploration", {}).get("max_skills_per_exploration", 10)

        # Pruning settings
        self.pruning_enabled = config.get("pruning", {}).get("enabled", True)
        self.pruning_interval_hours = config.get("pruning", {}).get("interval_hours", 168)  # Weekly
        self.min_uses_before_prune = config.get("pruning", {}).get("min_uses_before_prune", 5)
        self.max_unused_days = config.get("pruning", {}).get("max_unused_days", 30)
        self.min_success_rate = config.get("pruning", {}).get("min_success_rate", 0.5)
        self.min_overall_score = config.get("pruning", {}).get("min_overall_score", 0.4)

        # Optimization settings
        self.optimization_enabled = config.get("optimization", {}).get("enabled", True)
        self.optimization_interval_hours = config.get("optimization", {}).get("interval_hours", 24)
        self.top_performers_count = config.get("optimization", {}).get("top_performers_count", 10)

        # State
        self.exploration_history: List[ExplorationResult] = []
        self.pruning_history: List[PruningResult] = []
        self.known_skills: Set[str] = set()

        # Background tasks
        self._exploration_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._pruning_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("SkillOptimizer initialized")

    async def start(self):
        """Start background optimization processes."""
        self._running = True
        logger.info("Starting skill optimization processes...")

        if self.exploration_enabled:
            self._exploration_task = asyncio.create_task(self._exploration_loop())
            logger.info("Exploration loop started")

        if self.optimization_enabled:
            self._optimization_task = asyncio.create_task(self._optimization_loop())
            logger.info("Optimization loop started")

        if self.pruning_enabled:
            self._pruning_task = asyncio.create_task(self._pruning_loop())
            logger.info("Pruning loop started")

    async def stop(self):
        """Stop background processes."""
        self._running = False
        logger.info("Stopping skill optimization processes...")

        tasks = [self._exploration_task, self._optimization_task, self._pruning_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("Skill optimization processes stopped")

    async def _exploration_loop(self):
        """Continuous skill exploration loop."""
        logger.info("Skill exploration loop started")

        while self._running:
            try:
                await self.explore_marketplace()
                await asyncio.sleep(self.exploration_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in exploration loop: {e}", exc_info=True)
                await asyncio.sleep(3600)  # Retry after 1 hour

    async def _optimization_loop(self):
        """Continuous optimization loop."""
        logger.info("Skill optimization loop started")

        while self._running:
            try:
                await self.optimize_skills()
                await asyncio.sleep(self.optimization_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}", exc_info=True)
                await asyncio.sleep(3600)

    async def _pruning_loop(self):
        """Continuous pruning loop."""
        logger.info("Skill pruning loop started")

        while self._running:
            try:
                await self.prune_skills()
                await asyncio.sleep(self.pruning_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pruning loop: {e}", exc_info=True)
                await asyncio.sleep(3600)

    async def explore_marketplace(self) -> ExplorationResult:
        """
        Proactively explore marketplace for new skills.

        Returns:
            ExplorationResult with discoveries and recommendations
        """
        logger.info("Exploring skill marketplace...")

        result = ExplorationResult(
            explored_at=datetime.now(),
            skills_discovered=0,
            skills_evaluated=0,
            recommendations=[]
        )

        try:
            # Search marketplace for trending/popular skills
            # Empty query returns all/trending skills
            discovered_skills = await self.marketplace.search(
                query="",
                limit=self.max_skills_per_exploration
            )

            result.skills_discovered = len(discovered_skills)

            for skill_metadata in discovered_skills:
                skill_id = skill_metadata.name

                # Skip if already known
                if skill_id in self.known_skills:
                    continue

                # Mark as known
                self.known_skills.add(skill_id)

                # Evaluate quality and compatibility
                evaluation = await self.evaluator.evaluate_skill(
                    skill_metadata.__dict__
                )

                result.skills_evaluated += 1

                # Generate recommendation based on evaluation
                recommendation = self._generate_recommendation(
                    skill_id,
                    evaluation
                )

                if recommendation.action != OptimizationAction.NO_ACTION:
                    result.recommendations.append(recommendation)
                    logger.info(
                        f"Recommendation for {skill_id}: "
                        f"{recommendation.action.value} (priority: {recommendation.priority:.2f})"
                    )

            # Analyze skill gaps and suggest skills to fill them
            await self._analyze_skill_gaps(result)

            self.exploration_history.append(result)

            logger.info(
                f"Exploration complete: {result.skills_discovered} discovered, "
                f"{result.skills_evaluated} evaluated, "
                f"{len(result.recommendations)} recommendations"
            )

        except Exception as e:
            error_msg = f"Exploration error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg, exc_info=True)

        return result

    def _generate_recommendation(
        self,
        skill_id: str,
        evaluation: Any  # EvaluationResult
    ) -> OptimizationRecommendation:
        """Generate optimization recommendation from evaluation."""

        # High quality and compatible - activate
        if (evaluation.overall_score >= 0.7 and
            evaluation.compatibility_score >= 0.7):
            return OptimizationRecommendation(
                skill_id=skill_id,
                action=OptimizationAction.ACTIVATE,
                priority=evaluation.overall_score,
                reason="High quality and compatible skill",
                expected_benefit="Expand capabilities with proven skill",
                estimated_cost=0.0
            )

        # Moderate quality - monitor
        elif evaluation.overall_score >= 0.5:
            return OptimizationRecommendation(
                skill_id=skill_id,
                action=OptimizationAction.MONITOR,
                priority=evaluation.overall_score * 0.5,
                reason="Moderate quality, needs monitoring",
                expected_benefit="Potential capability expansion",
                estimated_cost=0.0
            )

        # Low quality - ignore
        else:
            return OptimizationRecommendation(
                skill_id=skill_id,
                action=OptimizationAction.NO_ACTION,
                priority=0.0,
                reason="Quality below threshold",
                expected_benefit="None",
                estimated_cost=0.0
            )

    async def _analyze_skill_gaps(self, result: ExplorationResult):
        """Analyze skill gaps and add recommendations."""
        skill_gaps = self.performance_tracker.get_skill_gaps(min_priority=0.3)

        for gap in skill_gaps[:5]:  # Top 5 gaps
            # Check if any discovered skills match the gap
            for skill_metadata in await self.marketplace.search(
                query=gap.missing_capability,
                limit=3
            ):
                skill_id = skill_metadata.name

                recommendation = OptimizationRecommendation(
                    skill_id=skill_id,
                    action=OptimizationAction.ACTIVATE,
                    priority=gap.priority_score,
                    reason=f"Addresses skill gap: {gap.missing_capability}",
                    expected_benefit=f"Fill gap for: {gap.task_description}",
                    metadata={"gap_id": gap.gap_id}
                )

                result.recommendations.append(recommendation)

    async def optimize_skills(self):
        """
        Optimize skill selection and prioritization.

        Analyzes performance data and adjusts skill priorities.
        """
        logger.info("Optimizing skill library...")

        # Get top performers
        top_performers = self.performance_tracker.get_top_performers(
            limit=self.top_performers_count
        )

        if top_performers:
            logger.info(f"Top {len(top_performers)} performing skills:")
            for stats in top_performers:
                logger.info(
                    f"  {stats.skill_id}: "
                    f"ROI={stats.roi_score:.2f}, "
                    f"uses={stats.total_executions}, "
                    f"success_rate={stats.success_rate:.1%}"
                )

        # Identify degrading skills
        degrading = self.performance_tracker.get_degrading_skills()
        if degrading:
            logger.warning(f"Found {len(degrading)} degrading skills:")
            for stats in degrading:
                logger.warning(
                    f"  {stats.skill_id}: "
                    f"success_rate={stats.success_rate:.1%} "
                    f"(recent: {stats.recent_success_rate:.1%})"
                )

        # Identify improving skills
        improving = self.performance_tracker.get_improving_skills()
        if improving:
            logger.info(f"Found {len(improving)} improving skills:")
            for stats in improving:
                logger.info(
                    f"  {stats.skill_id}: "
                    f"success_rate={stats.success_rate:.1%} "
                    f"(recent: {stats.recent_success_rate:.1%})"
                )

        # TODO: Implement skill combination experiments
        # TODO: Adjust skill priorities in registry

        logger.info("Optimization complete")

    async def prune_skills(self, dry_run: bool = False) -> PruningResult:
        """
        Prune underperforming and unused skills.

        Args:
            dry_run: If True, only simulate pruning

        Returns:
            PruningResult with pruning details
        """
        logger.info(f"Pruning skill library (dry_run={dry_run})...")

        result = PruningResult(
            pruned_at=datetime.now(),
            skills_evaluated=0,
            skills_pruned=0,
            pruned_skills=[]
        )

        now = datetime.now()

        # Get all tracked skills
        for skill_id in list(self.performance_tracker.stats_cache.keys()):
            stats = self.performance_tracker.get_skill_stats(skill_id)
            if not stats:
                continue

            result.skills_evaluated += 1

            should_prune = False
            reason = ""

            # Skip if not enough data
            if stats.total_executions < self.min_uses_before_prune:
                continue

            # Check for low performance
            if stats.success_rate < self.min_success_rate:
                should_prune = True
                reason = f"Low success rate: {stats.success_rate:.1%}"

            # Check for low ROI
            elif stats.roi_score < self.min_overall_score:
                should_prune = True
                reason = f"Low ROI score: {stats.roi_score:.2f}"

            # Check for inactivity
            elif stats.last_used:
                days_unused = (now - stats.last_used).days
                if days_unused > self.max_unused_days:
                    should_prune = True
                    reason = f"Unused for {days_unused} days"

            if should_prune:
                logger.info(f"Pruning candidate: {skill_id} - {reason}")
                result.pruned_skills.append(skill_id)
                result.skills_pruned += 1

                if not dry_run:
                    # Actually remove/disable the skill
                    await self._prune_skill(skill_id)
                    logger.info(f"Pruned skill: {skill_id}")

        self.pruning_history.append(result)

        logger.info(
            f"Pruning complete: {result.skills_pruned} skills pruned "
            f"out of {result.skills_evaluated} evaluated"
        )

        return result

    async def _prune_skill(self, skill_id: str):
        """Actually prune a skill (unregister, delete files)."""
        try:
            # Unregister from registry
            await self.registry.unregister(skill_id)

            # TODO: Delete skill files if needed
            # TODO: Mark in database as pruned

            logger.info(f"Successfully pruned skill: {skill_id}")

        except Exception as e:
            logger.error(f"Error pruning skill {skill_id}: {e}", exc_info=True)

    def get_recommendations(
        self,
        action_type: Optional[OptimizationAction] = None,
        min_priority: float = 0.3
    ) -> List[OptimizationRecommendation]:
        """
        Get optimization recommendations.

        Args:
            action_type: Filter by action type
            min_priority: Minimum priority threshold

        Returns:
            List of recommendations
        """
        recommendations = []

        for exploration in self.exploration_history:
            for rec in exploration.recommendations:
                if rec.priority < min_priority:
                    continue

                if action_type and rec.action != action_type:
                    continue

                recommendations.append(rec)

        return sorted(
            recommendations,
            key=lambda r: r.priority,
            reverse=True
        )

    async def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        return {
            "exploration": {
                "enabled": self.exploration_enabled,
                "interval_hours": self.exploration_interval_hours,
                "total_explorations": len(self.exploration_history),
                "last_exploration": (
                    self.exploration_history[-1].explored_at.isoformat()
                    if self.exploration_history else None
                ),
                "skills_discovered": sum(e.skills_discovered for e in self.exploration_history),
                "skills_evaluated": sum(e.skills_evaluated for e in self.exploration_history)
            },
            "pruning": {
                "enabled": self.pruning_enabled,
                "interval_hours": self.pruning_interval_hours,
                "total_prunings": len(self.pruning_history),
                "last_pruning": (
                    self.pruning_history[-1].pruned_at.isoformat()
                    if self.pruning_history else None
                ),
                "total_pruned": sum(p.skills_pruned for p in self.pruning_history)
            },
            "recommendations": {
                "total": len(self.get_recommendations()),
                "high_priority": len(self.get_recommendations(min_priority=0.7)),
                "activate": len(self.get_recommendations(action_type=OptimizationAction.ACTIVATE)),
                "prune": len(self.get_recommendations(action_type=OptimizationAction.PRUNE))
            },
            "known_skills": len(self.known_skills)
        }

    async def cleanup(self):
        """Cleanup and save state."""
        await self.stop()
        logger.info("SkillOptimizer cleaned up")
