"""
Benchmark reporting and result visualization.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging

from .metrics import BenchmarkScore, ComplexityMetrics, CategoryMetrics
from .tasks import TaskResult
from .framework import TaskComplexity, TaskCategory

logger = logging.getLogger(__name__)


class BenchmarkReporter:
    """
    Generate comprehensive benchmark reports with analysis and visualizations.

    Supports multiple output formats:
    - JSON: Machine-readable structured data
    - Markdown: Human-readable report with tables
    - Console: Formatted console output
    """

    def __init__(self, output_dir: str = "tests/benchmarks/reports"):
        """
        Initialize benchmark reporter.

        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        score: BenchmarkScore,
        results: List[TaskResult],
        format: str = "all",
        save: bool = True
    ) -> Dict[str, str]:
        """
        Generate benchmark report in specified format(s).

        Args:
            score: Calculated benchmark score
            results: Task execution results
            format: Report format ('json', 'markdown', 'console', 'all')
            save: Whether to save reports to files

        Returns:
            Dictionary mapping format to report content
        """
        reports = {}

        if format in ('json', 'all'):
            json_report = self._generate_json_report(score, results)
            reports['json'] = json_report
            if save:
                self._save_report(json_report, 'benchmark_report.json')

        if format in ('markdown', 'all'):
            md_report = self._generate_markdown_report(score, results)
            reports['markdown'] = md_report
            if save:
                self._save_report(md_report, 'benchmark_report.md')

        if format in ('console', 'all'):
            console_report = self._generate_console_report(score, results)
            reports['console'] = console_report

        return reports

    def _generate_json_report(self, score: BenchmarkScore, results: List[TaskResult]) -> str:
        """Generate JSON format report."""
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_tasks": score.total_tasks,
                "completed_tasks": score.completed_tasks,
                "total_cost": score.total_cost,
                "total_time": score.total_time,
            },
            "overall_score": {
                "composite_score": round(score.overall_score, 2),
                "success_rate_score": round(score.success_rate_score, 2),
                "performance_score": round(score.performance_score, 2),
                "cost_efficiency_score": round(score.cost_efficiency_score, 2),
                "tool_usage_score": round(score.tool_usage_score, 2),
                "resilience_score": round(score.resilience_score, 2),
            },
            "complexity_breakdown": {
                k: {
                    "total_tasks": v.total_tasks,
                    "completed_tasks": v.completed_tasks,
                    "success_rate": round(v.success_rate * 100, 2),
                    "avg_response_time": round(v.avg_response_time, 2),
                    "avg_cost": round(v.avg_cost, 4),
                    "tool_usage_accuracy": round(v.tool_usage_accuracy * 100, 2),
                    "meets_targets": v.meets_targets,
                }
                for k, v in score.complexity_breakdown.items()
            },
            "category_breakdown": {
                k: {
                    "total_tasks": v.total_tasks,
                    "completed_tasks": v.completed_tasks,
                    "success_rate": round(v.success_rate * 100, 2),
                    "avg_response_time": round(v.avg_response_time, 2),
                }
                for k, v in score.category_breakdown.items()
            },
            "analysis": {
                "strengths": score.strengths,
                "weaknesses": score.weaknesses,
                "recommendations": score.recommendations,
            },
            "detailed_results": [r.to_dict() for r in results],
        }

        return json.dumps(report_data, indent=2)

    def _generate_markdown_report(self, score: BenchmarkScore, results: List[TaskResult]) -> str:
        """Generate Markdown format report."""
        lines = [
            "# Alpha Agent Benchmark Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"**Overall Benchmark Score:** {score.overall_score:.1f}/100",
            "",
            f"- Total Tasks: {score.total_tasks}",
            f"- Completed Tasks: {score.completed_tasks}",
            f"- Success Rate: {(score.completed_tasks / score.total_tasks * 100):.1f}%",
            f"- Total API Cost: ${score.total_cost:.4f}",
            f"- Total Execution Time: {score.total_time:.2f}s",
            "",
            "---",
            "",
            "## Dimension Scores",
            "",
            "| Dimension | Score | Status |",
            "|-----------|-------|--------|",
            f"| Success Rate | {score.success_rate_score:.1f}/100 | {self._get_status(score.success_rate_score)} |",
            f"| Performance | {score.performance_score:.1f}/100 | {self._get_status(score.performance_score)} |",
            f"| Cost Efficiency | {score.cost_efficiency_score:.1f}/100 | {self._get_status(score.cost_efficiency_score)} |",
            f"| Tool Usage | {score.tool_usage_score:.1f}/100 | {self._get_status(score.tool_usage_score)} |",
            f"| Resilience | {score.resilience_score:.1f}/100 | {self._get_status(score.resilience_score)} |",
            "",
            "---",
            "",
            "## Performance by Complexity Level",
            "",
            "| Level | Tasks | Completed | Success Rate | Avg Time | Meets Target |",
            "|-------|-------|-----------|--------------|----------|--------------|",
        ]

        for complexity_key in sorted(score.complexity_breakdown.keys()):
            metrics = score.complexity_breakdown[complexity_key]
            lines.append(
                f"| {complexity_key} | {metrics.total_tasks} | {metrics.completed_tasks} | "
                f"{metrics.success_rate * 100:.1f}% | {metrics.avg_response_time:.2f}s | "
                f"{'✓' if metrics.meets_targets else '✗'} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Performance by Category",
            "",
            "| Category | Tasks | Completed | Success Rate | Avg Time |",
            "|----------|-------|-----------|--------------|----------|",
        ])

        for category_key in sorted(score.category_breakdown.keys()):
            metrics = score.category_breakdown[category_key]
            lines.append(
                f"| {category_key} | {metrics.total_tasks} | {metrics.completed_tasks} | "
                f"{metrics.success_rate * 100:.1f}% | {metrics.avg_response_time:.2f}s |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Analysis",
            "",
            "### Strengths",
            "",
        ])

        for strength in score.strengths:
            lines.append(f"- ✓ {strength}")

        lines.extend([
            "",
            "### Weaknesses",
            "",
        ])

        for weakness in score.weaknesses:
            lines.append(f"- ✗ {weakness}")

        lines.extend([
            "",
            "### Recommendations",
            "",
        ])

        for recommendation in score.recommendations:
            lines.append(f"- → {recommendation}")

        lines.extend([
            "",
            "---",
            "",
            "## Detailed Task Results",
            "",
        ])

        # Group results by complexity
        for complexity in TaskComplexity:
            level_results = [r for r in results if r.complexity == complexity]
            if not level_results:
                continue

            lines.extend([
                f"### {complexity.value}",
                "",
            ])

            for result in level_results:
                status_icon = "✓" if result.success else "✗"
                lines.extend([
                    f"**{status_icon} {result.task_name}**",
                    "",
                    f"- Category: {result.category.value}",
                    f"- Duration: {result.evaluation.response_time:.2f}s",
                    f"- Cost: ${result.evaluation.api_cost:.4f}",
                    f"- Tool Usage Accuracy: {result.evaluation.tool_usage_accuracy * 100:.1f}%",
                ])

                if result.error_message:
                    lines.append(f"- Error: {result.error_message}")

                if result.evaluation.error_recovery_attempts > 0:
                    lines.append(
                        f"- Recovery Attempts: {result.evaluation.error_recovery_attempts} "
                        f"({'successful' if result.evaluation.error_recovery_success else 'failed'})"
                    )

                lines.append("")

        lines.extend([
            "---",
            "",
            "*Report generated by Alpha Agent Benchmark Framework*",
        ])

        return "\n".join(lines)

    def _generate_console_report(self, score: BenchmarkScore, results: List[TaskResult]) -> str:
        """Generate console-friendly report."""
        lines = [
            "",
            "=" * 80,
            "ALPHA AGENT BENCHMARK REPORT".center(80),
            "=" * 80,
            "",
            f"Overall Score: {score.overall_score:.1f}/100",
            "",
            "Dimension Scores:",
            f"  Success Rate:     {score.success_rate_score:.1f}/100",
            f"  Performance:      {score.performance_score:.1f}/100",
            f"  Cost Efficiency:  {score.cost_efficiency_score:.1f}/100",
            f"  Tool Usage:       {score.tool_usage_score:.1f}/100",
            f"  Resilience:       {score.resilience_score:.1f}/100",
            "",
            "-" * 80,
            "",
            "Summary:",
            f"  Total Tasks:      {score.total_tasks}",
            f"  Completed:        {score.completed_tasks}",
            f"  Success Rate:     {(score.completed_tasks / score.total_tasks * 100):.1f}%",
            f"  Total Cost:       ${score.total_cost:.4f}",
            f"  Total Time:       {score.total_time:.2f}s",
            "",
            "-" * 80,
            "",
        ]

        # Complexity breakdown
        if score.complexity_breakdown:
            lines.append("Performance by Complexity:")
            for complexity_key in sorted(score.complexity_breakdown.keys()):
                metrics = score.complexity_breakdown[complexity_key]
                target_status = "✓" if metrics.meets_targets else "✗"
                lines.append(
                    f"  {target_status} {complexity_key:20s}: "
                    f"{metrics.completed_tasks}/{metrics.total_tasks} "
                    f"({metrics.success_rate * 100:.1f}%) "
                    f"@ {metrics.avg_response_time:.2f}s"
                )
            lines.append("")

        # Strengths and weaknesses
        if score.strengths:
            lines.append("Strengths:")
            for strength in score.strengths:
                lines.append(f"  ✓ {strength}")
            lines.append("")

        if score.weaknesses:
            lines.append("Weaknesses:")
            for weakness in score.weaknesses:
                lines.append(f"  ✗ {weakness}")
            lines.append("")

        if score.recommendations:
            lines.append("Recommendations:")
            for rec in score.recommendations:
                lines.append(f"  → {rec}")
            lines.append("")

        lines.extend([
            "=" * 80,
            ""
        ])

        return "\n".join(lines)

    def _get_status(self, score: float) -> str:
        """Get status emoji/text for a score."""
        if score >= 80:
            return "✓ Excellent"
        elif score >= 60:
            return "○ Good"
        else:
            return "✗ Needs Improvement"

    def _save_report(self, content: str, filename: str) -> None:
        """Save report to file."""
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Report saved to: {filepath}")

    def print_summary(self, score: BenchmarkScore) -> None:
        """Print summary to console."""
        console_report = self._generate_console_report(score, [])
        print(console_report)
