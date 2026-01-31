"""
Alpha Agent Benchmark Testing Framework

Industry-standard benchmark testing for evaluating Alpha's capabilities across
different task complexity levels, inspired by AgentBench, GAIA, τ-Bench, and SWE-bench.
"""

from .benchmark_framework import BenchmarkFramework, TaskComplexity, TaskCategory, EvaluationDimensions, BenchmarkConfig
from .tasks import BenchmarkTask, TaskResult
from .runner import BenchmarkRunner
from .metrics import MetricsCalculator, BenchmarkScore
from .reporter import BenchmarkReporter

__version__ = '1.0.0'

__all__ = [
    'BenchmarkFramework',
    'TaskComplexity',
    'TaskCategory',
    'EvaluationDimensions',
    'BenchmarkConfig',
    'BenchmarkTask',
    'TaskResult',
    'BenchmarkRunner',
    'MetricsCalculator',
    'BenchmarkScore',
    'BenchmarkReporter',
]
