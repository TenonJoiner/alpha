"""
Alpha - Smart Skill Evaluator

Multi-criteria skill evaluation system with A/B testing and learning capabilities.
Evaluates skills based on utility, quality, compatibility, and cost.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json
import sys
import re

logger = logging.getLogger(__name__)


class EvaluationCriterion(Enum):
    """Evaluation criteria."""
    UTILITY = "utility"
    QUALITY = "quality"
    COMPATIBILITY = "compatibility"
    COST = "cost"


@dataclass
class CriterionScore:
    """Score for a single evaluation criterion."""
    criterion: EvaluationCriterion
    score: float  # 0-1
    weight: float  # 0-1
    details: str
    sub_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a skill."""
    skill_id: str
    evaluated_at: datetime

    # Individual criterion scores
    utility_score: float
    quality_score: float
    compatibility_score: float
    cost_score: float

    # Weighted overall score
    overall_score: float

    # Detailed scores
    criterion_scores: List[CriterionScore]

    # Recommendation
    recommendation: str  # "activate", "monitor", "reject"
    confidence: float  # 0-1

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class ABTestConfig:
    """Configuration for A/B testing."""
    skill_a_id: str
    skill_b_id: str
    test_duration_days: int = 7
    min_samples: int = 10
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    winner: Optional[str] = None


class SmartEvaluator:
    """
    Multi-criteria skill evaluator with learning capabilities.

    Features:
    - Utility score (how useful for common tasks)
    - Quality score (code quality, documentation, maintenance)
    - Compatibility score (dependencies, requirements)
    - Cost score (execution cost, installation size)
    - Weighted composite scoring
    - A/B testing framework
    - Learning from performance over time
    """

    def __init__(
        self,
        config: Dict[str, Any],
        data_dir: Path = Path("data/skill_evaluation")
    ):
        """
        Initialize smart evaluator.

        Args:
            config: Configuration dictionary
            data_dir: Data directory for storage
        """
        self.config = config
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Evaluation weights (configurable)
        self.weights = {
            EvaluationCriterion.UTILITY: 0.35,
            EvaluationCriterion.QUALITY: 0.30,
            EvaluationCriterion.COMPATIBILITY: 0.25,
            EvaluationCriterion.COST: 0.10
        }

        # Minimum thresholds
        self.min_quality_score = config.get("evaluation", {}).get("min_quality_score", 0.6)
        self.min_compatibility_score = config.get("evaluation", {}).get("min_compatibility_score", 0.7)

        # Evaluation history
        self.evaluation_history: Dict[str, List[EvaluationResult]] = {}

        # A/B tests
        self.ab_tests: Dict[str, ABTestConfig] = {}

        # Learning data (skill_id -> learned insights)
        self.learned_insights: Dict[str, Dict[str, Any]] = {}

        logger.info("SmartEvaluator initialized")

    async def evaluate_skill(self, skill_metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate a skill using multi-criteria analysis.

        Args:
            skill_metadata: Skill metadata dictionary

        Returns:
            EvaluationResult with scores and recommendation
        """
        skill_id = skill_metadata.get("name", skill_metadata.get("id", "unknown"))

        logger.info(f"Evaluating skill: {skill_id}")

        # Evaluate each criterion
        utility_score = await self._evaluate_utility(skill_metadata)
        quality_score = await self._evaluate_quality(skill_metadata)
        compatibility_score = await self._evaluate_compatibility(skill_metadata)
        cost_score = await self._evaluate_cost(skill_metadata)

        # Build criterion scores
        criterion_scores = [
            CriterionScore(
                criterion=EvaluationCriterion.UTILITY,
                score=utility_score.score,
                weight=self.weights[EvaluationCriterion.UTILITY],
                details=utility_score.details,
                sub_scores=utility_score.sub_scores
            ),
            CriterionScore(
                criterion=EvaluationCriterion.QUALITY,
                score=quality_score.score,
                weight=self.weights[EvaluationCriterion.QUALITY],
                details=quality_score.details,
                sub_scores=quality_score.sub_scores
            ),
            CriterionScore(
                criterion=EvaluationCriterion.COMPATIBILITY,
                score=compatibility_score.score,
                weight=self.weights[EvaluationCriterion.COMPATIBILITY],
                details=compatibility_score.details,
                sub_scores=compatibility_score.sub_scores
            ),
            CriterionScore(
                criterion=EvaluationCriterion.COST,
                score=cost_score.score,
                weight=self.weights[EvaluationCriterion.COST],
                details=cost_score.details,
                sub_scores=cost_score.sub_scores
            )
        ]

        # Calculate weighted overall score
        overall_score = sum(
            cs.score * cs.weight for cs in criterion_scores
        )

        # Generate recommendation
        recommendation, confidence = self._generate_recommendation(
            overall_score,
            compatibility_score.score,
            quality_score.score
        )

        # Create result
        result = EvaluationResult(
            skill_id=skill_id,
            evaluated_at=datetime.now(),
            utility_score=utility_score.score,
            quality_score=quality_score.score,
            compatibility_score=compatibility_score.score,
            cost_score=cost_score.score,
            overall_score=overall_score,
            criterion_scores=criterion_scores,
            recommendation=recommendation,
            confidence=confidence,
            metadata=skill_metadata
        )

        # Store in history
        if skill_id not in self.evaluation_history:
            self.evaluation_history[skill_id] = []
        self.evaluation_history[skill_id].append(result)

        logger.info(
            f"Evaluation complete for {skill_id}: "
            f"overall={overall_score:.2f}, recommendation={recommendation}"
        )

        return result

    async def _evaluate_utility(self, metadata: Dict[str, Any]) -> CriterionScore:
        """Evaluate skill utility (how useful for common tasks)."""
        sub_scores = {}

        # Category relevance
        category = metadata.get("category", "").lower()
        category_scores = {
            "development": 0.9,
            "productivity": 0.8,
            "data": 0.85,
            "automation": 0.85,
            "testing": 0.7,
            "general": 0.5
        }
        sub_scores["category"] = category_scores.get(category, 0.5)

        # Tags relevance (check for popular/useful tags)
        tags = metadata.get("tags", [])
        useful_tags = [
            "ai", "automation", "productivity", "testing", "data",
            "web", "api", "database", "cloud", "security"
        ]
        matching_tags = sum(1 for tag in tags if tag.lower() in useful_tags)
        sub_scores["tags"] = min(1.0, matching_tags / 3.0)  # 3+ useful tags = 1.0

        # Description quality (longer, detailed descriptions suggest utility)
        description = metadata.get("description", "")
        desc_length = len(description)
        sub_scores["description"] = min(1.0, desc_length / 200.0)  # 200+ chars = 1.0

        # Installation count (if available)
        installs = metadata.get("installs", 0)
        if installs > 1000:
            sub_scores["popularity"] = 1.0
        elif installs > 100:
            sub_scores["popularity"] = 0.7
        elif installs > 10:
            sub_scores["popularity"] = 0.5
        else:
            sub_scores["popularity"] = 0.3

        # Calculate weighted average
        score = sum(sub_scores.values()) / len(sub_scores)

        return CriterionScore(
            criterion=EvaluationCriterion.UTILITY,
            score=score,
            weight=self.weights[EvaluationCriterion.UTILITY],
            details=f"Category: {category}, Tags: {len(tags)}, Installs: {installs}",
            sub_scores=sub_scores
        )

    async def _evaluate_quality(self, metadata: Dict[str, Any]) -> CriterionScore:
        """Evaluate skill quality (code quality, documentation, maintenance)."""
        sub_scores = {}

        # Documentation
        has_description = bool(metadata.get("description"))
        has_homepage = bool(metadata.get("homepage"))
        has_repository = bool(metadata.get("repository"))
        sub_scores["documentation"] = (
            (0.4 if has_description else 0.0) +
            (0.3 if has_homepage else 0.0) +
            (0.3 if has_repository else 0.0)
        )

        # Versioning (proper semantic versioning)
        version = metadata.get("version", "0.0.0")
        if re.match(r'^\d+\.\d+\.\d+', version):
            sub_scores["versioning"] = 0.8
        else:
            sub_scores["versioning"] = 0.3

        # Maintenance (recent version or well-established)
        # If created_at or updated_at available
        updated_at = metadata.get("updated_at")
        if updated_at:
            try:
                update_date = datetime.fromisoformat(updated_at)
                days_since_update = (datetime.now() - update_date).days
                if days_since_update < 30:
                    sub_scores["maintenance"] = 1.0
                elif days_since_update < 90:
                    sub_scores["maintenance"] = 0.7
                elif days_since_update < 365:
                    sub_scores["maintenance"] = 0.5
                else:
                    sub_scores["maintenance"] = 0.3
            except:
                sub_scores["maintenance"] = 0.5
        else:
            sub_scores["maintenance"] = 0.5

        # Author credibility (if author metadata available)
        author = metadata.get("author", "")
        if author:
            sub_scores["author"] = 0.6  # Base credibility
        else:
            sub_scores["author"] = 0.3

        # License (proper open source license)
        license_type = metadata.get("license", "").lower()
        if any(l in license_type for l in ["mit", "apache", "bsd", "gpl"]):
            sub_scores["license"] = 0.8
        elif license_type:
            sub_scores["license"] = 0.5
        else:
            sub_scores["license"] = 0.3

        # Calculate weighted average
        score = sum(sub_scores.values()) / len(sub_scores)

        return CriterionScore(
            criterion=EvaluationCriterion.QUALITY,
            score=score,
            weight=self.weights[EvaluationCriterion.QUALITY],
            details=f"Version: {version}, Author: {author}, License: {license_type}",
            sub_scores=sub_scores
        )

    async def _evaluate_compatibility(self, metadata: Dict[str, Any]) -> CriterionScore:
        """Evaluate compatibility (dependencies, requirements)."""
        sub_scores = {}

        # Python version compatibility
        python_version = metadata.get("python_version", ">=3.8")
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Check if current Python version is compatible
        if "3.8" in python_version or "3.9" in python_version or \
           "3.10" in python_version or "3.11" in python_version or \
           "3.12" in python_version or ">=" in python_version:
            sub_scores["python_version"] = 1.0
        else:
            sub_scores["python_version"] = 0.5

        # Dependencies (fewer is better for compatibility)
        dependencies = metadata.get("dependencies", [])
        dep_count = len(dependencies)
        if dep_count == 0:
            sub_scores["dependencies"] = 1.0
        elif dep_count <= 3:
            sub_scores["dependencies"] = 0.8
        elif dep_count <= 10:
            sub_scores["dependencies"] = 0.6
        else:
            sub_scores["dependencies"] = 0.4

        # Platform compatibility (assume cross-platform unless specified)
        platform = metadata.get("platform", "any")
        if platform.lower() in ["any", "all", "cross-platform"]:
            sub_scores["platform"] = 1.0
        else:
            sub_scores["platform"] = 0.7

        # Installation size (if available)
        size_mb = metadata.get("size_mb", 0)
        if size_mb == 0:
            sub_scores["size"] = 0.8  # Unknown size
        elif size_mb < 10:
            sub_scores["size"] = 1.0
        elif size_mb < 50:
            sub_scores["size"] = 0.7
        else:
            sub_scores["size"] = 0.5

        # Calculate weighted average
        score = sum(sub_scores.values()) / len(sub_scores)

        return CriterionScore(
            criterion=EvaluationCriterion.COMPATIBILITY,
            score=score,
            weight=self.weights[EvaluationCriterion.COMPATIBILITY],
            details=f"Python: {python_version}, Deps: {dep_count}, Platform: {platform}",
            sub_scores=sub_scores
        )

    async def _evaluate_cost(self, metadata: Dict[str, Any]) -> CriterionScore:
        """Evaluate cost (execution cost, installation size)."""
        sub_scores = {}

        # Installation cost (size)
        size_mb = metadata.get("size_mb", 0)
        if size_mb == 0:
            sub_scores["installation"] = 0.8
        elif size_mb < 10:
            sub_scores["installation"] = 1.0
        elif size_mb < 50:
            sub_scores["installation"] = 0.7
        elif size_mb < 100:
            sub_scores["installation"] = 0.5
        else:
            sub_scores["installation"] = 0.3

        # Execution cost (estimated based on dependencies and complexity)
        dependencies = metadata.get("dependencies", [])
        has_ml_deps = any(
            dep.lower() for dep in dependencies
            if any(ml in dep.lower() for ml in ["tensorflow", "torch", "transformers"])
        )

        if has_ml_deps:
            sub_scores["execution"] = 0.3  # ML models are expensive
        elif len(dependencies) > 10:
            sub_scores["execution"] = 0.6
        else:
            sub_scores["execution"] = 0.9

        # Maintenance cost (based on dependency count)
        if len(dependencies) == 0:
            sub_scores["maintenance"] = 1.0
        elif len(dependencies) <= 5:
            sub_scores["maintenance"] = 0.8
        else:
            sub_scores["maintenance"] = 0.6

        # Calculate weighted average
        score = sum(sub_scores.values()) / len(sub_scores)

        return CriterionScore(
            criterion=EvaluationCriterion.COST,
            score=score,
            weight=self.weights[EvaluationCriterion.COST],
            details=f"Size: {size_mb}MB, Dependencies: {len(dependencies)}",
            sub_scores=sub_scores
        )

    def _generate_recommendation(
        self,
        overall_score: float,
        compatibility_score: float,
        quality_score: float
    ) -> Tuple[str, float]:
        """
        Generate recommendation based on scores.

        Returns:
            Tuple of (recommendation, confidence)
        """
        # High overall score and good compatibility
        if overall_score >= 0.7 and compatibility_score >= self.min_compatibility_score:
            return "activate", 0.9

        # Good quality but compatibility concerns
        elif overall_score >= 0.6 and quality_score >= self.min_quality_score:
            return "monitor", 0.7

        # Moderate scores
        elif overall_score >= 0.5:
            return "monitor", 0.5

        # Low scores
        else:
            return "reject", 0.8

    async def start_ab_test(
        self,
        skill_a_id: str,
        skill_b_id: str,
        test_duration_days: int = 7,
        min_samples: int = 10
    ) -> str:
        """
        Start an A/B test between two skills.

        Args:
            skill_a_id: First skill ID
            skill_b_id: Second skill ID
            test_duration_days: Duration of test in days
            min_samples: Minimum samples required

        Returns:
            Test ID
        """
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        test_config = ABTestConfig(
            skill_a_id=skill_a_id,
            skill_b_id=skill_b_id,
            test_duration_days=test_duration_days,
            min_samples=min_samples,
            started_at=datetime.now()
        )

        self.ab_tests[test_id] = test_config

        logger.info(
            f"Started A/B test {test_id}: {skill_a_id} vs {skill_b_id} "
            f"(duration: {test_duration_days} days)"
        )

        return test_id

    async def analyze_ab_test(
        self,
        test_id: str,
        performance_tracker: Any
    ) -> Dict[str, Any]:
        """
        Analyze A/B test results.

        Args:
            test_id: Test ID
            performance_tracker: PerformanceTracker instance

        Returns:
            Analysis results
        """
        if test_id not in self.ab_tests:
            raise ValueError(f"A/B test not found: {test_id}")

        test = self.ab_tests[test_id]

        # Get performance stats for both skills
        stats_a = performance_tracker.get_skill_stats(test.skill_a_id)
        stats_b = performance_tracker.get_skill_stats(test.skill_b_id)

        if not stats_a or not stats_b:
            return {
                "status": "insufficient_data",
                "message": "One or both skills have no performance data"
            }

        # Compare metrics
        comparison = {
            "skill_a": {
                "id": test.skill_a_id,
                "success_rate": stats_a.success_rate,
                "avg_execution_time": stats_a.avg_execution_time,
                "roi_score": stats_a.roi_score,
                "total_uses": stats_a.total_executions
            },
            "skill_b": {
                "id": test.skill_b_id,
                "success_rate": stats_b.success_rate,
                "avg_execution_time": stats_b.avg_execution_time,
                "roi_score": stats_b.roi_score,
                "total_uses": stats_b.total_executions
            }
        }

        # Determine winner
        score_a = (
            stats_a.success_rate * 0.5 +
            stats_a.roi_score * 0.3 +
            (1.0 - min(1.0, stats_a.avg_execution_time / 10.0)) * 0.2
        )

        score_b = (
            stats_b.success_rate * 0.5 +
            stats_b.roi_score * 0.3 +
            (1.0 - min(1.0, stats_b.avg_execution_time / 10.0)) * 0.2
        )

        if abs(score_a - score_b) < 0.05:
            winner = "tie"
        elif score_a > score_b:
            winner = test.skill_a_id
        else:
            winner = test.skill_b_id

        test.winner = winner
        test.ended_at = datetime.now()

        result = {
            "status": "complete",
            "test_id": test_id,
            "started_at": test.started_at.isoformat(),
            "ended_at": test.ended_at.isoformat(),
            "winner": winner,
            "comparison": comparison,
            "scores": {
                "skill_a": score_a,
                "skill_b": score_b
            }
        }

        logger.info(f"A/B test {test_id} complete: winner = {winner}")

        return result

    async def learn_from_performance(
        self,
        skill_id: str,
        performance_stats: Any
    ):
        """
        Learn insights from skill performance over time.

        Args:
            skill_id: Skill ID
            performance_stats: SkillPerformanceStats instance
        """
        insights = {}

        # Learn optimal use cases
        if performance_stats.success_rate >= 0.8:
            insights["optimal_use"] = "High success rate - suitable for production use"
        elif performance_stats.success_rate >= 0.6:
            insights["optimal_use"] = "Moderate success - suitable for non-critical tasks"
        else:
            insights["optimal_use"] = "Low success - needs improvement or replacement"

        # Learn performance characteristics
        if performance_stats.avg_execution_time < 1.0:
            insights["performance"] = "Fast execution - suitable for real-time use"
        elif performance_stats.avg_execution_time < 5.0:
            insights["performance"] = "Moderate speed - suitable for background tasks"
        else:
            insights["performance"] = "Slow execution - use sparingly"

        # Learn cost effectiveness
        if performance_stats.roi_score > 1.0:
            insights["cost_effectiveness"] = "Excellent ROI - prioritize this skill"
        elif performance_stats.roi_score > 0.5:
            insights["cost_effectiveness"] = "Good ROI - useful skill"
        else:
            insights["cost_effectiveness"] = "Poor ROI - consider alternatives"

        self.learned_insights[skill_id] = insights

        logger.info(f"Learned insights for {skill_id}: {insights}")

    def get_evaluation_history(self, skill_id: str) -> List[EvaluationResult]:
        """Get evaluation history for a skill."""
        return self.evaluation_history.get(skill_id, [])

    async def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get evaluation summary."""
        total_evaluations = sum(len(evals) for evals in self.evaluation_history.values())

        recommendations = {
            "activate": 0,
            "monitor": 0,
            "reject": 0
        }

        for evals in self.evaluation_history.values():
            if evals:
                latest = evals[-1]
                recommendations[latest.recommendation] += 1

        return {
            "total_skills_evaluated": len(self.evaluation_history),
            "total_evaluations": total_evaluations,
            "recommendations": recommendations,
            "active_ab_tests": len([t for t in self.ab_tests.values() if not t.ended_at]),
            "completed_ab_tests": len([t for t in self.ab_tests.values() if t.ended_at]),
            "learned_insights": len(self.learned_insights)
        }

    async def cleanup(self):
        """Cleanup and persist data."""
        logger.info("SmartEvaluator cleaned up")
