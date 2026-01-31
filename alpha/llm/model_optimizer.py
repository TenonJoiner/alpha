"""
Alpha - Model Optimizer

Dynamic model selection optimization based on performance tracking data.
Refines model routing decisions using actual performance metrics.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from alpha.llm.model_performance_tracker import (
    ModelPerformanceTracker,
    TaskType,
    ModelStats
)
from alpha.llm.model_selector import TaskCharacteristics, TaskDifficulty


logger = logging.getLogger(__name__)


@dataclass
class OptimizationStrategy:
    """Model optimization strategy configuration."""
    optimize_for: str = "balanced"  # speed, cost, quality, balanced
    min_sample_size: int = 5  # Minimum requests before considering a model
    min_success_rate: float = 0.8  # Minimum success rate threshold
    enable_learning: bool = True  # Use historical data for selection
    fallback_enabled: bool = True  # Allow fallback to rule-based selection


class ModelOptimizer:
    """
    Optimize model selection using performance tracking data.

    Features:
    - Learn from historical performance data
    - Dynamic model routing based on actual metrics
    - Cost-performance tradeoff optimization
    - Automatic refinement of selection strategy
    """

    def __init__(
        self,
        tracker: ModelPerformanceTracker,
        models_config: Dict,
        strategy: Optional[OptimizationStrategy] = None
    ):
        """
        Initialize model optimizer.

        Args:
            tracker: Performance tracker instance
            models_config: Dictionary of available models and their configs
            strategy: Optimization strategy (uses default if not provided)
        """
        self.tracker = tracker
        self.models_config = models_config
        self.strategy = strategy or OptimizationStrategy()

        # Cache for recent optimization decisions
        self._optimization_cache = {}

    def select_optimal_model(
        self,
        characteristics: TaskCharacteristics,
        default_model: str,
        available_models: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Select the optimal model based on task characteristics and performance data.

        Args:
            characteristics: Task characteristics from TaskAnalyzer
            default_model: Default model to use if optimization unavailable
            available_models: List of available models (uses all if not specified)

        Returns:
            Tuple of (selected_model, selection_reason)
        """
        # Map task characteristics to task type
        task_type = self._map_to_task_type(characteristics)

        # If learning is disabled, use rule-based selection
        if not self.strategy.enable_learning:
            logger.debug("Learning disabled, using rule-based selection")
            return default_model, "learning_disabled"

        # Get available models
        if available_models is None:
            available_models = list(self.models_config.keys())

        # Try to get performance-based recommendation
        recommended_model = self.tracker.get_best_model_for_task(
            task_type=task_type.value,
            optimize_for=self.strategy.optimize_for
        )

        if recommended_model and recommended_model in available_models:
            # Verify the model meets our quality thresholds
            stats = self.tracker.get_model_stats(recommended_model, task_type.value)

            if stats and self._meets_quality_threshold(stats):
                logger.info(
                    f"Selected {recommended_model} for {task_type.value} "
                    f"(optimized for {self.strategy.optimize_for})"
                )
                return recommended_model, f"optimized_for_{self.strategy.optimize_for}"

        # Fallback to rule-based selection
        if self.strategy.fallback_enabled:
            logger.debug(
                f"No performance-based recommendation available for {task_type.value}, "
                "using default"
            )
            return default_model, "insufficient_data_fallback"
        else:
            logger.warning("No optimal model found and fallback disabled")
            return default_model, "no_optimization_available"

    def _map_to_task_type(self, characteristics: TaskCharacteristics) -> TaskType:
        """
        Map task characteristics to a task type category.

        Args:
            characteristics: Task characteristics

        Returns:
            TaskType enum value
        """
        # Check for specific task types first
        if characteristics.is_coding and not characteristics.requires_reasoning:
            return TaskType.CODING

        if characteristics.requires_reasoning and not characteristics.is_coding:
            return TaskType.REASONING

        # Map by difficulty
        difficulty_map = {
            TaskDifficulty.SIMPLE: TaskType.SIMPLE,
            TaskDifficulty.MEDIUM: TaskType.MEDIUM,
            TaskDifficulty.COMPLEX: TaskType.COMPLEX,
            TaskDifficulty.EXPERT: TaskType.EXPERT
        }

        return difficulty_map.get(characteristics.difficulty, TaskType.GENERAL)

    def _meets_quality_threshold(self, stats: ModelStats) -> bool:
        """
        Check if model stats meet quality thresholds.

        Args:
            stats: Model statistics

        Returns:
            True if meets thresholds, False otherwise
        """
        # Check sample size
        if stats.total_requests < self.strategy.min_sample_size:
            logger.debug(
                f"Model {stats.model} has insufficient samples: "
                f"{stats.total_requests} < {self.strategy.min_sample_size}"
            )
            return False

        # Check success rate
        if stats.success_rate < self.strategy.min_success_rate:
            logger.debug(
                f"Model {stats.model} has low success rate: "
                f"{stats.success_rate} < {self.strategy.min_success_rate}"
            )
            return False

        return True

    def get_model_recommendations(
        self,
        task_types: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Get model recommendations for different task types.

        Args:
            task_types: List of task types to analyze (analyzes all if not specified)

        Returns:
            Dictionary mapping task types to recommended models and stats
        """
        if task_types is None:
            task_types = [t.value for t in TaskType]

        recommendations = {}

        for task_type in task_types:
            # Get all model stats for this task type
            all_stats = self.tracker.get_all_models_stats(task_type=task_type)

            # Filter by quality thresholds
            qualified_stats = [
                s for s in all_stats
                if self._meets_quality_threshold(s)
            ]

            if not qualified_stats:
                recommendations[task_type] = {
                    "recommended_model": None,
                    "reason": "insufficient_data",
                    "stats": []
                }
                continue

            # Get best model for each optimization strategy
            best_for_speed = min(qualified_stats, key=lambda x: x.avg_latency_ms)
            best_for_cost = min(qualified_stats, key=lambda x: x.avg_cost_per_request)
            best_for_quality = max(
                qualified_stats,
                key=lambda x: x.avg_quality_score or x.success_rate
            )

            # Get the recommended model based on current strategy
            recommended_model = self.tracker.get_best_model_for_task(
                task_type=task_type,
                optimize_for=self.strategy.optimize_for
            )

            recommendations[task_type] = {
                "recommended_model": recommended_model,
                "optimization_strategy": self.strategy.optimize_for,
                "best_for_speed": best_for_speed.model,
                "best_for_cost": best_for_cost.model,
                "best_for_quality": best_for_quality.model,
                "stats": [
                    {
                        "model": s.model,
                        "requests": s.total_requests,
                        "success_rate": s.success_rate,
                        "avg_latency_ms": s.avg_latency_ms,
                        "avg_cost": s.avg_cost_per_request,
                        "quality_score": s.avg_quality_score
                    }
                    for s in qualified_stats
                ]
            }

        return recommendations

    def analyze_cost_performance_tradeoff(
        self,
        task_type: str
    ) -> Dict:
        """
        Analyze cost vs. performance tradeoff for a task type.

        Args:
            task_type: Task type to analyze

        Returns:
            Analysis results with cost-performance curve
        """
        stats = self.tracker.get_all_models_stats(task_type=task_type)

        if not stats:
            return {
                "task_type": task_type,
                "models_analyzed": 0,
                "analysis": "insufficient_data"
            }

        # Calculate cost-performance ratio for each model
        # Lower ratio is better (less cost per unit of quality)
        analysis = []

        for s in stats:
            if not self._meets_quality_threshold(s):
                continue

            quality_metric = s.avg_quality_score or s.success_rate
            if quality_metric == 0:
                continue

            cost_per_quality = s.avg_cost_per_request / quality_metric

            analysis.append({
                "model": s.model,
                "avg_cost": s.avg_cost_per_request,
                "quality": quality_metric,
                "cost_per_quality": cost_per_quality,
                "avg_latency_ms": s.avg_latency_ms,
                "success_rate": s.success_rate,
                "total_requests": s.total_requests
            })

        # Sort by cost-performance ratio (best first)
        analysis.sort(key=lambda x: x["cost_per_quality"])

        return {
            "task_type": task_type,
            "models_analyzed": len(analysis),
            "best_value_model": analysis[0]["model"] if analysis else None,
            "models": analysis
        }

    def get_optimization_report(self) -> Dict:
        """
        Generate comprehensive optimization report.

        Returns:
            Detailed report on model performance and recommendations
        """
        # Get recommendations for all task types
        recommendations = self.get_model_recommendations()

        # Get overall statistics
        all_stats = self.tracker.get_all_models_stats()

        # Calculate total costs and usage
        total_cost = sum(s.total_cost for s in all_stats)
        total_requests = sum(s.total_requests for s in all_stats)

        # Identify most used and most costly models
        most_used = max(all_stats, key=lambda x: x.total_requests) if all_stats else None
        most_costly = max(all_stats, key=lambda x: x.total_cost) if all_stats else None

        # Cost-performance analysis for each task type
        tradeoff_analysis = {}
        for task_type in TaskType:
            analysis = self.analyze_cost_performance_tradeoff(task_type.value)
            if analysis["models_analyzed"] > 0:
                tradeoff_analysis[task_type.value] = analysis

        report = {
            "generated_at": ModelStats.__annotations__,
            "optimization_strategy": self.strategy.optimize_for,
            "overall_stats": {
                "total_requests": total_requests,
                "total_cost_usd": round(total_cost, 4),
                "models_tracked": len(all_stats),
                "most_used_model": most_used.model if most_used else None,
                "most_costly_model": most_costly.model if most_costly else None
            },
            "task_type_recommendations": recommendations,
            "cost_performance_analysis": tradeoff_analysis,
            "model_statistics": [
                {
                    "model": s.model,
                    "total_requests": s.total_requests,
                    "success_rate": s.success_rate,
                    "avg_latency_ms": s.avg_latency_ms,
                    "total_cost_usd": s.total_cost,
                    "avg_cost_per_request": s.avg_cost_per_request
                }
                for s in all_stats
            ]
        }

        return report

    def suggest_improvements(self) -> List[str]:
        """
        Suggest improvements based on performance data.

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Get all model stats
        all_stats = self.tracker.get_all_models_stats()

        if not all_stats:
            suggestions.append(
                "No performance data available yet. Continue using the system "
                "to collect performance metrics."
            )
            return suggestions

        # Check for underutilized but high-performing models
        for stats in all_stats:
            if (stats.total_requests < 10 and
                stats.success_rate > 0.9 and
                stats.avg_cost_per_request < 0.001):
                suggestions.append(
                    f"Consider using {stats.model} more frequently - "
                    f"it shows high success rate ({stats.success_rate:.1%}) "
                    f"and low cost (${stats.avg_cost_per_request:.6f} per request)"
                )

        # Check for high-cost, low-performance models
        for stats in all_stats:
            if (stats.total_requests > 20 and
                stats.success_rate < 0.85 and
                stats.avg_cost_per_request > 0.01):
                suggestions.append(
                    f"Model {stats.model} has high cost "
                    f"(${stats.avg_cost_per_request:.6f}) and low success rate "
                    f"({stats.success_rate:.1%}). Consider using alternatives."
                )

        # Check for slow models
        for stats in all_stats:
            if stats.avg_latency_ms > 10000:  # > 10 seconds
                suggestions.append(
                    f"Model {stats.model} has high average latency "
                    f"({stats.avg_latency_ms}ms). Consider faster alternatives "
                    "for time-sensitive tasks."
                )

        # Analyze task-specific optimization opportunities
        recommendations = self.get_model_recommendations()

        for task_type, rec in recommendations.items():
            if rec.get("recommended_model"):
                # Check if there's significant cost savings available
                stats_list = rec.get("stats", [])
                if len(stats_list) >= 2:
                    costs = [s["avg_cost"] for s in stats_list]
                    max_cost = max(costs)
                    min_cost = min(costs)

                    if max_cost > min_cost * 3:  # 3x cost difference
                        savings_pct = ((max_cost - min_cost) / max_cost) * 100
                        suggestions.append(
                            f"For {task_type} tasks: Using the most cost-effective "
                            f"model could save up to {savings_pct:.0f}% on API costs"
                        )

        if not suggestions:
            suggestions.append(
                "Current model selection appears well-optimized based on "
                f"available data ({sum(s.total_requests for s in all_stats)} requests analyzed)."
            )

        return suggestions
