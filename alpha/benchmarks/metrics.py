"""
Performance metrics calculation and benchmark scoring.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import statistics

from .benchmark_framework import TaskComplexity, TaskCategory, PerformanceTargets
from .tasks import TaskResult


@dataclass
class ComplexityMetrics:
    """Metrics for a specific complexity level."""
    complexity: TaskComplexity
    total_tasks: int = 0
    completed_tasks: int = 0
    partial_completions: int = 0
    success_rate: float = 0.0
    partial_success_rate: float = 0.0
    avg_response_time: float = 0.0
    avg_cost: float = 0.0
    tool_usage_accuracy: float = 0.0
    error_recovery_rate: float = 0.0
    target_success_rate: float = 0.0
    target_response_time: float = 0.0
    meets_targets: bool = False


@dataclass
class CategoryMetrics:
    """Metrics for a specific task category."""
    category: TaskCategory
    total_tasks: int = 0
    completed_tasks: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    avg_cost: float = 0.0


@dataclass
class BenchmarkScore:
    """
    Overall benchmark score and detailed metrics.

    Weighted composite score (0-100) considering all evaluation dimensions.
    """
    overall_score: float = 0.0  # Composite score 0-100
    success_rate_score: float = 0.0  # Weighted success rate score
    performance_score: float = 0.0  # Response time performance score
    cost_efficiency_score: float = 0.0  # Cost efficiency score
    tool_usage_score: float = 0.0  # Tool usage accuracy score
    resilience_score: float = 0.0  # Error recovery score

    complexity_breakdown: Dict[str, ComplexityMetrics] = field(default_factory=dict)
    category_breakdown: Dict[str, CategoryMetrics] = field(default_factory=dict)

    total_tasks: int = 0
    completed_tasks: int = 0
    total_cost: float = 0.0
    total_time: float = 0.0

    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class MetricsCalculator:
    """
    Calculate performance metrics and benchmark scores.

    Implements comprehensive scoring system based on:
    - Task completion rates across complexity levels
    - Response time performance vs. targets
    - Cost efficiency
    - Tool usage accuracy
    - Error recovery capabilities
    """

    # Scoring weights for different dimensions
    WEIGHTS = {
        'success_rate': 0.35,  # 35% - Most important
        'performance': 0.25,   # 25% - Response time matters
        'cost_efficiency': 0.15,  # 15% - Cost optimization
        'tool_usage': 0.15,    # 15% - Tool proficiency
        'resilience': 0.10,    # 10% - Error recovery
    }

    # Complexity level weights (harder levels weighted higher)
    COMPLEXITY_WEIGHTS = {
        TaskComplexity.LEVEL_1_SIMPLE: 0.15,
        TaskComplexity.LEVEL_2_MEDIUM: 0.25,
        TaskComplexity.LEVEL_3_COMPLEX: 0.35,
        TaskComplexity.LEVEL_4_EXPERT: 0.25,
    }

    def __init__(self):
        """Initialize metrics calculator."""
        pass

    def calculate_score(self, results: List[TaskResult]) -> BenchmarkScore:
        """
        Calculate comprehensive benchmark score from results.

        Args:
            results: List of task execution results

        Returns:
            Benchmark score with detailed metrics
        """
        if not results:
            return BenchmarkScore()

        score = BenchmarkScore()
        score.total_tasks = len(results)
        score.completed_tasks = sum(1 for r in results if r.evaluation.task_completion)
        score.total_cost = sum(r.evaluation.api_cost for r in results)
        score.total_time = sum(r.evaluation.response_time for r in results)

        # Calculate dimension scores
        score.success_rate_score = self._calculate_success_rate_score(results)
        score.performance_score = self._calculate_performance_score(results)
        score.cost_efficiency_score = self._calculate_cost_efficiency_score(results)
        score.tool_usage_score = self._calculate_tool_usage_score(results)
        score.resilience_score = self._calculate_resilience_score(results)

        # Calculate overall weighted score
        score.overall_score = (
            score.success_rate_score * self.WEIGHTS['success_rate'] +
            score.performance_score * self.WEIGHTS['performance'] +
            score.cost_efficiency_score * self.WEIGHTS['cost_efficiency'] +
            score.tool_usage_score * self.WEIGHTS['tool_usage'] +
            score.resilience_score * self.WEIGHTS['resilience']
        )

        # Calculate complexity breakdown
        score.complexity_breakdown = self._calculate_complexity_metrics(results)

        # Calculate category breakdown
        score.category_breakdown = self._calculate_category_metrics(results)

        # Analyze strengths and weaknesses
        score.strengths, score.weaknesses, score.recommendations = self._analyze_performance(score)

        return score

    def _calculate_success_rate_score(self, results: List[TaskResult]) -> float:
        """Calculate weighted success rate score across complexity levels."""
        complexity_scores = {}

        for complexity in TaskComplexity:
            level_results = [r for r in results if r.complexity == complexity]
            if not level_results:
                continue

            targets = PerformanceTargets.for_complexity(complexity)
            completed = sum(1 for r in level_results if r.evaluation.task_completion)
            success_rate = completed / len(level_results)

            # Score based on target achievement
            score = min(success_rate / targets.success_rate, 1.0) * 100
            complexity_scores[complexity] = score

        # Weighted average
        if not complexity_scores:
            return 0.0

        weighted_score = sum(
            score * self.COMPLEXITY_WEIGHTS[complexity]
            for complexity, score in complexity_scores.items()
        )

        return weighted_score

    def _calculate_performance_score(self, results: List[TaskResult]) -> float:
        """Calculate response time performance score."""
        complexity_scores = {}

        for complexity in TaskComplexity:
            level_results = [r for r in results if r.complexity == complexity]
            if not level_results:
                continue

            targets = PerformanceTargets.for_complexity(complexity)
            avg_time = statistics.mean(r.evaluation.response_time for r in level_results)

            # Score: 100 if under target, decreasing if over
            if avg_time <= targets.max_response_time:
                score = 100.0
            else:
                # Penalize proportionally to how much over target
                ratio = targets.max_response_time / avg_time
                score = max(ratio * 100, 0)

            complexity_scores[complexity] = score

        if not complexity_scores:
            return 0.0

        weighted_score = sum(
            score * self.COMPLEXITY_WEIGHTS[complexity]
            for complexity, score in complexity_scores.items()
        )

        return weighted_score

    def _calculate_cost_efficiency_score(self, results: List[TaskResult]) -> float:
        """Calculate cost efficiency score."""
        if not results:
            return 0.0

        # Calculate cost per successful task
        successful = [r for r in results if r.evaluation.task_completion]
        if not successful:
            return 0.0

        avg_cost = statistics.mean(r.evaluation.api_cost for r in successful)

        # Define cost targets (lower is better)
        # These are example thresholds - adjust based on actual costs
        excellent_cost = 0.01  # $0.01 per task
        acceptable_cost = 0.05  # $0.05 per task

        if avg_cost <= excellent_cost:
            return 100.0
        elif avg_cost <= acceptable_cost:
            # Linear scale between excellent and acceptable
            return 100 - (avg_cost - excellent_cost) / (acceptable_cost - excellent_cost) * 50
        else:
            # Exponential decay after acceptable threshold
            return max(50 * (acceptable_cost / avg_cost), 0)

    def _calculate_tool_usage_score(self, results: List[TaskResult]) -> float:
        """Calculate tool usage accuracy score."""
        if not results:
            return 0.0

        avg_accuracy = statistics.mean(r.evaluation.tool_usage_accuracy for r in results)
        return avg_accuracy * 100

    def _calculate_resilience_score(self, results: List[TaskResult]) -> float:
        """Calculate error recovery and resilience score."""
        if not results:
            return 0.0

        # Consider tasks that had errors
        tasks_with_errors = [r for r in results if r.evaluation.error_recovery_attempts > 0]

        if not tasks_with_errors:
            # No errors encountered - perfect score
            return 100.0

        # Calculate recovery rate
        recovery_successes = sum(1 for r in tasks_with_errors if r.evaluation.error_recovery_success)
        recovery_rate = recovery_successes / len(tasks_with_errors)

        return recovery_rate * 100

    def _calculate_complexity_metrics(self, results: List[TaskResult]) -> Dict[str, ComplexityMetrics]:
        """Calculate detailed metrics for each complexity level."""
        metrics = {}

        for complexity in TaskComplexity:
            level_results = [r for r in results if r.complexity == complexity]
            if not level_results:
                continue

            targets = PerformanceTargets.for_complexity(complexity)
            completed = sum(1 for r in level_results if r.evaluation.task_completion)
            partial = sum(1 for r in level_results if r.evaluation.partial_completion)

            success_rate = completed / len(level_results)
            avg_time = statistics.mean(r.evaluation.response_time for r in level_results)

            m = ComplexityMetrics(
                complexity=complexity,
                total_tasks=len(level_results),
                completed_tasks=completed,
                partial_completions=partial,
                success_rate=success_rate,
                partial_success_rate=(completed + partial) / len(level_results),
                avg_response_time=avg_time,
                avg_cost=statistics.mean(r.evaluation.api_cost for r in level_results),
                tool_usage_accuracy=statistics.mean(r.evaluation.tool_usage_accuracy for r in level_results),
                error_recovery_rate=sum(1 for r in level_results if r.evaluation.error_recovery_success) /
                                    max(sum(r.evaluation.error_recovery_attempts for r in level_results), 1),
                target_success_rate=targets.success_rate,
                target_response_time=targets.max_response_time,
                meets_targets=(success_rate >= targets.success_rate and avg_time <= targets.max_response_time)
            )

            metrics[complexity.value] = m

        return metrics

    def _calculate_category_metrics(self, results: List[TaskResult]) -> Dict[str, CategoryMetrics]:
        """Calculate detailed metrics for each task category."""
        metrics = {}

        for category in TaskCategory:
            cat_results = [r for r in results if r.category == category]
            if not cat_results:
                continue

            completed = sum(1 for r in cat_results if r.evaluation.task_completion)

            m = CategoryMetrics(
                category=category,
                total_tasks=len(cat_results),
                completed_tasks=completed,
                success_rate=completed / len(cat_results),
                avg_response_time=statistics.mean(r.evaluation.response_time for r in cat_results),
                avg_cost=statistics.mean(r.evaluation.api_cost for r in cat_results),
            )

            metrics[category.value] = m

        return metrics

    def _analyze_performance(self, score: BenchmarkScore) -> tuple[List[str], List[str], List[str]]:
        """Analyze performance and generate insights."""
        strengths = []
        weaknesses = []
        recommendations = []

        # Analyze overall score
        if score.overall_score >= 80:
            strengths.append("Excellent overall performance")
        elif score.overall_score >= 60:
            strengths.append("Good overall performance with room for improvement")
        else:
            weaknesses.append("Overall performance below expectations")
            recommendations.append("Focus on improving fundamental capabilities")

        # Analyze dimension scores
        if score.success_rate_score >= 80:
            strengths.append("High task completion rate")
        else:
            weaknesses.append("Task completion rate needs improvement")
            recommendations.append("Review failed tasks and improve error handling")

        if score.performance_score >= 80:
            strengths.append("Excellent response time performance")
        else:
            weaknesses.append("Response times exceed targets")
            recommendations.append("Optimize slow operations and reduce unnecessary steps")

        if score.cost_efficiency_score >= 80:
            strengths.append("Excellent cost efficiency")
        else:
            weaknesses.append("Higher than expected API costs")
            recommendations.append("Improve model selection to use cost-effective models where appropriate")

        if score.tool_usage_score >= 80:
            strengths.append("Strong tool usage proficiency")
        else:
            weaknesses.append("Tool usage accuracy needs improvement")
            recommendations.append("Enhance tool selection logic and parameter validation")

        if score.resilience_score >= 80:
            strengths.append("Excellent error recovery capabilities")
        else:
            weaknesses.append("Error recovery needs improvement")
            recommendations.append("Implement more robust fallback strategies and alternative approaches")

        # Analyze complexity level performance
        for complexity_key, metrics in score.complexity_breakdown.items():
            if not metrics.meets_targets:
                weaknesses.append(f"{complexity_key} tasks not meeting performance targets")
                recommendations.append(f"Focus on improving {complexity_key} task handling")

        return strengths, weaknesses, recommendations
