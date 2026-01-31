"""
Alpha - Model Performance Tracker

Track performance metrics for LLM models to optimize model selection.
Stores metrics in SQLite database for persistence and historical analysis.
"""

import sqlite3
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task type categories for performance tracking."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"
    CODING = "coding"
    REASONING = "reasoning"
    GENERAL = "general"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a model execution."""
    model: str
    task_type: str
    timestamp: float

    # Token usage and costs
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float  # USD

    # Performance metrics
    latency_ms: int  # Response time in milliseconds
    success: bool
    finish_reason: str

    # Quality indicators
    quality_score: Optional[float] = None  # 0.0-1.0, based on feedback
    retry_required: bool = False
    error_type: Optional[str] = None


@dataclass
class ModelStats:
    """Aggregated statistics for a model."""
    model: str
    task_type: str

    # Count metrics
    total_requests: int
    successful_requests: int
    failed_requests: int

    # Performance metrics
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Cost metrics
    total_cost: float
    avg_cost_per_request: float
    total_input_tokens: int
    total_output_tokens: int

    # Quality metrics
    success_rate: float
    avg_quality_score: float
    retry_rate: float

    # Time range
    first_request: str
    last_request: str
    request_count_24h: int


class ModelPerformanceTracker:
    """
    Track and analyze model performance metrics.

    Features:
    - Track per-request metrics (tokens, latency, success/failure)
    - Calculate aggregated statistics per model and task type
    - Store historical data in SQLite
    - Support querying and analysis
    """

    def __init__(self, db_path: str = "data/model_performance.db"):
        """
        Initialize performance tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create data directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Pricing information (USD per 1M tokens)
        # Based on DeepSeek pricing as of 2024
        self.pricing = {
            "deepseek-chat": {"input": 0.14, "output": 0.28, "cache_hit": 0.014},
            "deepseek-reasoner": {"input": 0.55, "output": 2.19},
            "deepseek-coder": {"input": 0.14, "output": 0.28},
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
        }

    def _init_database(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    estimated_cost REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    success INTEGER NOT NULL,
                    finish_reason TEXT,
                    quality_score REAL,
                    retry_required INTEGER DEFAULT 0,
                    error_type TEXT
                )
            """)

            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_task
                ON performance_metrics(model, task_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON performance_metrics(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_timestamp
                ON performance_metrics(model, timestamp)
            """)

            conn.commit()

        logger.info(f"Initialized performance tracking database: {self.db_path}")

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int,
                      cache_hits: int = 0) -> float:
        """
        Calculate estimated API cost for a request.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_hits: Number of cache hit tokens (for models supporting cache)

        Returns:
            Estimated cost in USD
        """
        if model not in self.pricing:
            logger.warning(f"No pricing data for model: {model}, using default")
            # Default pricing estimate
            return (input_tokens * 0.5 + output_tokens * 1.5) / 1_000_000

        pricing = self.pricing[model]

        # Calculate cost
        cost = (input_tokens * pricing["input"] +
                output_tokens * pricing["output"]) / 1_000_000

        # Apply cache discount if applicable
        if cache_hits > 0 and "cache_hit" in pricing:
            cache_discount = (cache_hits *
                            (pricing["input"] - pricing["cache_hit"])) / 1_000_000
            cost -= cache_discount

        return cost

    def record_request(self, metrics: PerformanceMetrics):
        """
        Record a model request and its performance metrics.

        Args:
            metrics: Performance metrics to record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO performance_metrics (
                    model, task_type, timestamp,
                    input_tokens, output_tokens, total_tokens, estimated_cost,
                    latency_ms, success, finish_reason,
                    quality_score, retry_required, error_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model,
                metrics.task_type,
                metrics.timestamp,
                metrics.input_tokens,
                metrics.output_tokens,
                metrics.total_tokens,
                metrics.estimated_cost,
                metrics.latency_ms,
                1 if metrics.success else 0,
                metrics.finish_reason,
                metrics.quality_score,
                1 if metrics.retry_required else 0,
                metrics.error_type
            ))

            conn.commit()

        logger.debug(f"Recorded metrics for {metrics.model} - "
                    f"task: {metrics.task_type}, success: {metrics.success}")

    def update_quality_score(self, model: str, timestamp: float, quality_score: float):
        """
        Update quality score for a specific request (e.g., based on user feedback).

        Args:
            model: Model name
            timestamp: Request timestamp
            quality_score: Quality score (0.0-1.0)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE performance_metrics
                SET quality_score = ?
                WHERE model = ? AND timestamp = ?
            """, (quality_score, model, timestamp))

            conn.commit()

        logger.debug(f"Updated quality score for {model} at {timestamp}: {quality_score}")

    def get_model_stats(self, model: str, task_type: Optional[str] = None,
                       time_window_hours: int = 168) -> Optional[ModelStats]:
        """
        Get aggregated statistics for a model.

        Args:
            model: Model name
            task_type: Optional task type filter
            time_window_hours: Time window in hours (default: 7 days)

        Returns:
            ModelStats object or None if no data
        """
        cutoff_time = time.time() - (time_window_hours * 3600)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query with optional task type filter
            where_clause = "WHERE model = ? AND timestamp > ?"
            params = [model, cutoff_time]

            if task_type:
                where_clause += " AND task_type = ?"
                params.append(task_type)

            # Get aggregated stats
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests,
                    AVG(latency_ms) as avg_latency_ms,
                    SUM(estimated_cost) as total_cost,
                    AVG(estimated_cost) as avg_cost_per_request,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    AVG(quality_score) as avg_quality_score,
                    SUM(CASE WHEN retry_required = 1 THEN 1 ELSE 0 END) as retry_count,
                    MIN(timestamp) as first_request,
                    MAX(timestamp) as last_request
                FROM performance_metrics
                {where_clause}
            """, params)

            row = cursor.fetchone()

            if row['total_requests'] == 0:
                return None

            # Get percentile latencies
            cursor.execute(f"""
                SELECT latency_ms
                FROM performance_metrics
                {where_clause}
                ORDER BY latency_ms
            """, params)

            latencies = [r[0] for r in cursor.fetchall()]
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)
            p95_latency = latencies[p95_idx] if p95_idx < len(latencies) else latencies[-1]
            p99_latency = latencies[p99_idx] if p99_idx < len(latencies) else latencies[-1]

            # Get 24h request count
            cutoff_24h = time.time() - (24 * 3600)
            cursor.execute(f"""
                SELECT COUNT(*) as count_24h
                FROM performance_metrics
                WHERE model = ? AND timestamp > ?
                {' AND task_type = ?' if task_type else ''}
            """, [model, cutoff_24h] + ([task_type] if task_type else []))

            count_24h = cursor.fetchone()['count_24h']

            # Calculate derived metrics
            success_rate = row['successful_requests'] / row['total_requests']
            retry_rate = row['retry_count'] / row['total_requests']

            return ModelStats(
                model=model,
                task_type=task_type or "all",
                total_requests=row['total_requests'],
                successful_requests=row['successful_requests'],
                failed_requests=row['failed_requests'],
                avg_latency_ms=round(row['avg_latency_ms'], 2),
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                total_cost=round(row['total_cost'], 6),
                avg_cost_per_request=round(row['avg_cost_per_request'], 6),
                total_input_tokens=row['total_input_tokens'],
                total_output_tokens=row['total_output_tokens'],
                success_rate=round(success_rate, 4),
                avg_quality_score=round(row['avg_quality_score'] or 0.0, 4),
                retry_rate=round(retry_rate, 4),
                first_request=datetime.fromtimestamp(row['first_request']).isoformat(),
                last_request=datetime.fromtimestamp(row['last_request']).isoformat(),
                request_count_24h=count_24h
            )

    def get_all_models_stats(self, task_type: Optional[str] = None,
                           time_window_hours: int = 168) -> List[ModelStats]:
        """
        Get statistics for all models.

        Args:
            task_type: Optional task type filter
            time_window_hours: Time window in hours

        Returns:
            List of ModelStats objects
        """
        cutoff_time = time.time() - (time_window_hours * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get unique models
            where_clause = "WHERE timestamp > ?"
            params = [cutoff_time]

            if task_type:
                where_clause += " AND task_type = ?"
                params.append(task_type)

            cursor.execute(f"""
                SELECT DISTINCT model FROM performance_metrics
                {where_clause}
            """, params)

            models = [row[0] for row in cursor.fetchall()]

        # Get stats for each model
        stats = []
        for model in models:
            model_stats = self.get_model_stats(model, task_type, time_window_hours)
            if model_stats:
                stats.append(model_stats)

        # Sort by total requests (most used first)
        stats.sort(key=lambda x: x.total_requests, reverse=True)

        return stats

    def get_best_model_for_task(self, task_type: str,
                               optimize_for: str = "balanced") -> Optional[str]:
        """
        Get the best performing model for a specific task type.

        Args:
            task_type: Task type to optimize for
            optimize_for: Optimization strategy:
                - "speed": Minimize latency
                - "cost": Minimize cost
                - "quality": Maximize quality score
                - "balanced": Balance all factors

        Returns:
            Best model name or None if no data
        """
        stats = self.get_all_models_stats(task_type=task_type)

        if not stats:
            return None

        # Filter out models with low sample size (< 5 requests)
        stats = [s for s in stats if s.total_requests >= 5]

        if not stats:
            return None

        # Filter out models with low success rate (< 80%)
        stats = [s for s in stats if s.success_rate >= 0.8]

        if not stats:
            return None

        # Select based on optimization strategy
        if optimize_for == "speed":
            return min(stats, key=lambda x: x.avg_latency_ms).model

        elif optimize_for == "cost":
            return min(stats, key=lambda x: x.avg_cost_per_request).model

        elif optimize_for == "quality":
            # Prioritize quality score, fallback to success rate
            return max(stats, key=lambda x: (x.avg_quality_score or x.success_rate)).model

        else:  # balanced
            # Score based on normalized metrics
            # Lower is better for latency and cost, higher is better for quality

            # Normalize metrics to 0-1 range
            latencies = [s.avg_latency_ms for s in stats]
            costs = [s.avg_cost_per_request for s in stats]
            qualities = [s.avg_quality_score or s.success_rate for s in stats]

            min_latency, max_latency = min(latencies), max(latencies)
            min_cost, max_cost = min(costs), max(costs)
            min_quality, max_quality = min(qualities), max(qualities)

            def normalize(value, min_val, max_val, invert=False):
                if max_val == min_val:
                    return 0.5
                norm = (value - min_val) / (max_val - min_val)
                return 1 - norm if invert else norm

            # Calculate composite scores
            scored_stats = []
            for s in stats:
                latency_score = normalize(s.avg_latency_ms, min_latency, max_latency, invert=True)
                cost_score = normalize(s.avg_cost_per_request, min_cost, max_cost, invert=True)
                quality_score = normalize(s.avg_quality_score or s.success_rate,
                                        min_quality, max_quality)

                # Weight: 30% speed, 20% cost, 50% quality
                composite_score = (0.3 * latency_score +
                                 0.2 * cost_score +
                                 0.5 * quality_score)

                scored_stats.append((s.model, composite_score))

            # Return model with highest composite score
            return max(scored_stats, key=lambda x: x[1])[0]

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Clean up old performance data.

        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM performance_metrics
                WHERE timestamp < ?
            """, (cutoff_time,))

            deleted = cursor.rowcount
            conn.commit()

        logger.info(f"Cleaned up {deleted} old performance records (>{days_to_keep} days)")

    def export_stats(self, output_path: str, time_window_hours: int = 168):
        """
        Export performance statistics to JSON file.

        Args:
            output_path: Path to output JSON file
            time_window_hours: Time window for statistics
        """
        import json

        stats = self.get_all_models_stats(time_window_hours=time_window_hours)

        # Convert to dict
        stats_dict = {
            "generated_at": datetime.now().isoformat(),
            "time_window_hours": time_window_hours,
            "models": [asdict(s) for s in stats]
        }

        with open(output_path, 'w') as f:
            json.dump(stats_dict, f, indent=2)

        logger.info(f"Exported performance stats to {output_path}")
