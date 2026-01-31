"""
Alpha - Skill Performance Tracker

Tracks skill performance metrics for continuous improvement and evolution.
Stores data in database for historical analysis and trend detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class SkillExecutionMetrics:
    """Metrics for a single skill execution."""
    skill_id: str
    execution_id: str
    timestamp: datetime
    success: bool
    execution_time: float  # seconds
    tokens_used: int = 0  # LLM tokens
    cost_estimate: float = 0.0  # USD
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillPerformanceStats:
    """Aggregated performance statistics for a skill."""
    skill_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0

    # Timing metrics
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0

    # Cost metrics
    total_tokens: int = 0
    avg_tokens: float = 0.0
    total_cost: float = 0.0
    avg_cost: float = 0.0

    # ROI metrics (value / cost)
    roi_score: float = 0.0
    value_score: float = 0.0  # Based on usage frequency and success

    # Temporal metrics
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None
    days_active: int = 0
    usage_frequency: float = 0.0  # Uses per day

    # Trend analysis
    recent_success_rate: float = 0.0  # Last 10 executions
    is_improving: bool = False
    is_degrading: bool = False

    # Additional metadata
    last_error: Optional[str] = None
    error_count_last_24h: int = 0


@dataclass
class SkillGap:
    """Represents a detected skill gap (task failed due to missing skill)."""
    gap_id: str
    detected_at: datetime
    task_description: str
    missing_capability: str
    failure_count: int = 1
    priority_score: float = 0.0
    suggested_skills: List[str] = field(default_factory=list)


class PerformanceTracker:
    """
    Tracks skill performance metrics and stores them in database.

    Features:
    - Per-skill execution tracking
    - Success rate and timing metrics
    - Cost tracking (LLM tokens)
    - ROI calculation
    - Trend analysis (improving vs degrading)
    - Skill gap detection
    """

    def __init__(self, learning_store: Any, data_dir: Path = Path("data/skill_performance")):
        """
        Initialize performance tracker.

        Args:
            learning_store: LearningStore instance for persistence
            data_dir: Directory for additional data storage
        """
        self.learning_store = learning_store
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for fast access
        self.stats_cache: Dict[str, SkillPerformanceStats] = {}
        self.recent_executions: List[SkillExecutionMetrics] = []
        self.skill_gaps: Dict[str, SkillGap] = {}

        # Load existing stats
        self._load_stats()

        logger.info("PerformanceTracker initialized")

    async def record_execution(
        self,
        skill_id: str,
        success: bool,
        execution_time: float,
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record a skill execution.

        Args:
            skill_id: Skill identifier
            success: Whether execution succeeded
            execution_time: Execution time in seconds
            tokens_used: Number of LLM tokens used
            cost_estimate: Estimated cost in USD
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            Execution ID
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"

        # Create execution record
        execution = SkillExecutionMetrics(
            skill_id=skill_id,
            execution_id=execution_id,
            timestamp=datetime.now(),
            success=success,
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            error_message=error_message,
            metadata=metadata or {}
        )

        # Add to recent executions (keep last 1000)
        self.recent_executions.append(execution)
        if len(self.recent_executions) > 1000:
            self.recent_executions.pop(0)

        # Update stats
        await self._update_stats(execution)

        # Store in database
        await self._store_execution(execution)

        logger.debug(
            f"Recorded execution for {skill_id}: "
            f"success={success}, time={execution_time:.2f}s"
        )

        return execution_id

    async def _update_stats(self, execution: SkillExecutionMetrics):
        """Update performance statistics based on execution."""
        skill_id = execution.skill_id

        # Get or create stats
        if skill_id not in self.stats_cache:
            self.stats_cache[skill_id] = SkillPerformanceStats(
                skill_id=skill_id,
                first_used=execution.timestamp
            )

        stats = self.stats_cache[skill_id]

        # Update counters
        stats.total_executions += 1
        if execution.success:
            stats.successful_executions += 1
        else:
            stats.failed_executions += 1
            stats.last_error = execution.error_message

        # Update success rate
        stats.success_rate = (
            stats.successful_executions / stats.total_executions
            if stats.total_executions > 0 else 0.0
        )

        # Update timing metrics
        stats.total_execution_time += execution.execution_time
        stats.avg_execution_time = stats.total_execution_time / stats.total_executions
        stats.min_execution_time = min(stats.min_execution_time, execution.execution_time)
        stats.max_execution_time = max(stats.max_execution_time, execution.execution_time)

        # Update cost metrics
        stats.total_tokens += execution.tokens_used
        stats.avg_tokens = stats.total_tokens / stats.total_executions
        stats.total_cost += execution.cost_estimate
        stats.avg_cost = stats.total_cost / stats.total_executions

        # Update temporal metrics
        stats.last_used = execution.timestamp
        if stats.first_used:
            stats.days_active = (execution.timestamp - stats.first_used).days
            stats.usage_frequency = (
                stats.total_executions / max(1, stats.days_active)
            )

        # Calculate ROI
        stats.value_score = self._calculate_value_score(stats)
        stats.roi_score = self._calculate_roi(stats)

        # Analyze trends
        await self._analyze_trends(stats)

        # Count recent errors
        stats.error_count_last_24h = self._count_recent_errors(skill_id)

        # Persist to database
        await self._store_stats(stats)

    def _calculate_value_score(self, stats: SkillPerformanceStats) -> float:
        """
        Calculate value score based on usage and success.

        Value = (usage_frequency * success_rate) normalized to 0-1
        """
        # Assume 5 uses/day is very high value
        frequency_score = min(1.0, stats.usage_frequency / 5.0)
        return frequency_score * stats.success_rate

    def _calculate_roi(self, stats: SkillPerformanceStats) -> float:
        """
        Calculate ROI score.

        ROI = value_score / (cost + maintenance)
        Higher is better
        """
        if stats.total_cost == 0:
            # Free skill, high ROI if valuable
            return stats.value_score * 10.0

        # Maintenance cost estimate (very simple)
        maintenance_cost = 0.01  # $0.01 per execution

        total_cost = stats.total_cost + (stats.total_executions * maintenance_cost)

        return stats.value_score / total_cost if total_cost > 0 else 0.0

    async def _analyze_trends(self, stats: SkillPerformanceStats):
        """Analyze performance trends (improving vs degrading)."""
        skill_id = stats.skill_id

        # Get recent executions (last 10)
        recent = [
            e for e in self.recent_executions[-50:]
            if e.skill_id == skill_id
        ][-10:]

        if len(recent) < 5:
            # Not enough data
            stats.is_improving = False
            stats.is_degrading = False
            return

        # Calculate recent success rate
        recent_successes = sum(1 for e in recent if e.success)
        stats.recent_success_rate = recent_successes / len(recent)

        # Compare with overall success rate
        improvement_threshold = 0.1  # 10% improvement
        degradation_threshold = -0.1  # 10% degradation

        delta = stats.recent_success_rate - stats.success_rate

        stats.is_improving = delta >= improvement_threshold
        stats.is_degrading = delta <= degradation_threshold

        if stats.is_improving:
            logger.info(f"Skill {skill_id} is improving: {delta:+.1%}")
        elif stats.is_degrading:
            logger.warning(f"Skill {skill_id} is degrading: {delta:+.1%}")

    def _count_recent_errors(self, skill_id: str) -> int:
        """Count errors in last 24 hours."""
        cutoff = datetime.now() - timedelta(hours=24)
        return sum(
            1 for e in self.recent_executions
            if e.skill_id == skill_id
            and not e.success
            and e.timestamp >= cutoff
        )

    async def record_skill_gap(
        self,
        task_description: str,
        missing_capability: str,
        suggested_skills: Optional[List[str]] = None
    ) -> str:
        """
        Record a detected skill gap.

        Args:
            task_description: Description of the failed task
            missing_capability: What capability was missing
            suggested_skills: List of suggested skills to fill gap

        Returns:
            Gap ID
        """
        gap_id = f"gap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Check if similar gap exists
        for existing_gap in self.skill_gaps.values():
            if existing_gap.missing_capability == missing_capability:
                existing_gap.failure_count += 1
                existing_gap.priority_score = self._calculate_gap_priority(existing_gap)
                logger.info(f"Updated existing skill gap: {existing_gap.gap_id}")
                return existing_gap.gap_id

        # Create new gap
        gap = SkillGap(
            gap_id=gap_id,
            detected_at=datetime.now(),
            task_description=task_description,
            missing_capability=missing_capability,
            suggested_skills=suggested_skills or []
        )

        gap.priority_score = self._calculate_gap_priority(gap)
        self.skill_gaps[gap_id] = gap

        # Store in database
        await self.learning_store.store_metric(
            metric_type="skill_gap",
            metric_name=missing_capability,
            value=gap.priority_score,
            period_start=gap.detected_at,
            period_end=gap.detected_at,
            metadata={
                "gap_id": gap_id,
                "task_description": task_description,
                "suggested_skills": suggested_skills or []
            }
        )

        logger.info(f"Recorded skill gap: {missing_capability} (priority: {gap.priority_score:.2f})")

        return gap_id

    def _calculate_gap_priority(self, gap: SkillGap) -> float:
        """Calculate priority score for a skill gap (0-1)."""
        # Priority based on failure frequency
        # More failures = higher priority
        return min(1.0, gap.failure_count / 10.0)

    def get_skill_stats(self, skill_id: str) -> Optional[SkillPerformanceStats]:
        """Get performance statistics for a skill."""
        return self.stats_cache.get(skill_id)

    def get_top_performers(self, limit: int = 10) -> List[SkillPerformanceStats]:
        """Get top performing skills by ROI."""
        return sorted(
            self.stats_cache.values(),
            key=lambda s: s.roi_score,
            reverse=True
        )[:limit]

    def get_degrading_skills(self) -> List[SkillPerformanceStats]:
        """Get list of degrading skills."""
        return [s for s in self.stats_cache.values() if s.is_degrading]

    def get_improving_skills(self) -> List[SkillPerformanceStats]:
        """Get list of improving skills."""
        return [s for s in self.stats_cache.values() if s.is_improving]

    def get_skill_gaps(self, min_priority: float = 0.3) -> List[SkillGap]:
        """Get skill gaps above priority threshold."""
        return sorted(
            [g for g in self.skill_gaps.values() if g.priority_score >= min_priority],
            key=lambda g: g.priority_score,
            reverse=True
        )

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        total_executions = sum(s.total_executions for s in self.stats_cache.values())
        total_successes = sum(s.successful_executions for s in self.stats_cache.values())
        total_cost = sum(s.total_cost for s in self.stats_cache.values())

        return {
            "total_skills_tracked": len(self.stats_cache),
            "total_executions": total_executions,
            "overall_success_rate": total_successes / total_executions if total_executions > 0 else 0.0,
            "total_cost": total_cost,
            "avg_cost_per_execution": total_cost / total_executions if total_executions > 0 else 0.0,
            "top_performers": len([s for s in self.stats_cache.values() if s.roi_score > 1.0]),
            "degrading_skills": len(self.get_degrading_skills()),
            "improving_skills": len(self.get_improving_skills()),
            "skill_gaps": len(self.skill_gaps),
            "high_priority_gaps": len(self.get_skill_gaps(min_priority=0.5))
        }

    async def _store_execution(self, execution: SkillExecutionMetrics):
        """Store execution in database."""
        await self.learning_store.store_metric(
            metric_type="skill_execution",
            metric_name=execution.skill_id,
            value=1.0 if execution.success else 0.0,
            period_start=execution.timestamp,
            period_end=execution.timestamp,
            metadata={
                "execution_id": execution.execution_id,
                "execution_time": execution.execution_time,
                "tokens_used": execution.tokens_used,
                "cost_estimate": execution.cost_estimate,
                "error_message": execution.error_message
            }
        )

    async def _store_stats(self, stats: SkillPerformanceStats):
        """Store aggregated stats in database."""
        await self.learning_store.store_metric(
            metric_type="skill_performance",
            metric_name=stats.skill_id,
            value=stats.roi_score,
            period_start=stats.first_used or datetime.now(),
            period_end=stats.last_used or datetime.now(),
            metadata=asdict(stats)
        )

    def _save_stats(self):
        """Save stats to JSON file."""
        try:
            stats_file = self.data_dir / "performance_stats.json"

            data = {
                skill_id: {
                    **asdict(stats),
                    "first_used": stats.first_used.isoformat() if stats.first_used else None,
                    "last_used": stats.last_used.isoformat() if stats.last_used else None
                }
                for skill_id, stats in self.stats_cache.items()
            }

            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} skill stats")

        except Exception as e:
            logger.error(f"Error saving stats: {e}", exc_info=True)

    def _load_stats(self):
        """Load stats from JSON file."""
        try:
            stats_file = self.data_dir / "performance_stats.json"

            if not stats_file.exists():
                return

            with open(stats_file, 'r') as f:
                data = json.load(f)

            for skill_id, stats_dict in data.items():
                # Parse datetimes
                if stats_dict.get("first_used"):
                    stats_dict["first_used"] = datetime.fromisoformat(stats_dict["first_used"])
                if stats_dict.get("last_used"):
                    stats_dict["last_used"] = datetime.fromisoformat(stats_dict["last_used"])

                self.stats_cache[skill_id] = SkillPerformanceStats(**stats_dict)

            logger.info(f"Loaded {len(self.stats_cache)} skill stats")

        except Exception as e:
            logger.error(f"Error loading stats: {e}", exc_info=True)

    async def cleanup(self):
        """Cleanup and persist data."""
        self._save_stats()
        logger.info("PerformanceTracker cleaned up")
