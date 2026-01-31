"""
Unit tests for Model Performance Tracking system.

Tests ModelPerformanceTracker and ModelOptimizer functionality.
"""

import unittest
import tempfile
import time
import os
from pathlib import Path

from alpha.llm.model_performance_tracker import (
    ModelPerformanceTracker,
    PerformanceMetrics,
    TaskType,
    ModelStats
)
from alpha.llm.model_optimizer import (
    ModelOptimizer,
    OptimizationStrategy
)
from alpha.llm.model_selector import (
    TaskCharacteristics,
    TaskDifficulty
)
from alpha.utils.config import ModelConfig


class TestModelPerformanceTracker(unittest.TestCase):
    """Test ModelPerformanceTracker functionality."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_performance.db")
        self.tracker = ModelPerformanceTracker(self.db_path)

    def tearDown(self):
        """Clean up test database."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_initialization(self):
        """Test database is properly initialized."""
        self.assertTrue(Path(self.db_path).exists())

    def test_calculate_cost(self):
        """Test cost calculation for different models."""
        # Test DeepSeek Chat
        cost = self.tracker.calculate_cost("deepseek-chat", 1000, 500)
        expected = (1000 * 0.14 + 500 * 0.28) / 1_000_000
        self.assertAlmostEqual(cost, expected, places=8)

        # Test with cache hits
        cost_with_cache = self.tracker.calculate_cost("deepseek-chat", 1000, 500, 500)
        self.assertLess(cost_with_cache, cost)

        # Test unknown model (uses default pricing)
        cost_unknown = self.tracker.calculate_cost("unknown-model", 1000, 500)
        self.assertGreater(cost_unknown, 0)

    def test_record_and_retrieve_metrics(self):
        """Test recording and retrieving performance metrics."""
        # Record a successful request
        metrics = PerformanceMetrics(
            model="deepseek-chat",
            task_type=TaskType.SIMPLE.value,
            timestamp=time.time(),
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=self.tracker.calculate_cost("deepseek-chat", 100, 50),
            latency_ms=250,
            success=True,
            finish_reason="stop",
            quality_score=0.9
        )

        self.tracker.record_request(metrics)

        # Retrieve stats
        stats = self.tracker.get_model_stats("deepseek-chat", TaskType.SIMPLE.value)

        self.assertIsNotNone(stats)
        self.assertEqual(stats.model, "deepseek-chat")
        self.assertEqual(stats.total_requests, 1)
        self.assertEqual(stats.successful_requests, 1)
        self.assertEqual(stats.success_rate, 1.0)

    def test_record_multiple_requests(self):
        """Test recording multiple requests and aggregated stats."""
        # Record 10 requests with varying performance
        for i in range(10):
            metrics = PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.MEDIUM.value,
                timestamp=time.time(),
                input_tokens=100 + i * 10,
                output_tokens=50 + i * 5,
                total_tokens=150 + i * 15,
                estimated_cost=self.tracker.calculate_cost(
                    "deepseek-chat", 100 + i * 10, 50 + i * 5
                ),
                latency_ms=200 + i * 50,
                success=i < 9,  # 1 failure
                finish_reason="stop" if i < 9 else "error",
                quality_score=0.8 + i * 0.02
            )
            self.tracker.record_request(metrics)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Get stats
        stats = self.tracker.get_model_stats("deepseek-chat", TaskType.MEDIUM.value)

        self.assertEqual(stats.total_requests, 10)
        self.assertEqual(stats.successful_requests, 9)
        self.assertEqual(stats.failed_requests, 1)
        self.assertEqual(stats.success_rate, 0.9)
        self.assertGreater(stats.avg_latency_ms, 200)
        self.assertGreater(stats.p95_latency_ms, stats.avg_latency_ms)

    def test_update_quality_score(self):
        """Test updating quality score after initial recording."""
        timestamp = time.time()

        metrics = PerformanceMetrics(
            model="deepseek-chat",
            task_type=TaskType.SIMPLE.value,
            timestamp=timestamp,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.0001,
            latency_ms=250,
            success=True,
            finish_reason="stop",
            quality_score=None
        )

        self.tracker.record_request(metrics)

        # Update quality score (e.g., based on user feedback)
        self.tracker.update_quality_score("deepseek-chat", timestamp, 0.95)

        # Verify update
        stats = self.tracker.get_model_stats("deepseek-chat", TaskType.SIMPLE.value)
        self.assertIsNotNone(stats.avg_quality_score)
        self.assertAlmostEqual(stats.avg_quality_score, 0.95, places=2)

    def test_get_all_models_stats(self):
        """Test retrieving stats for all models."""
        # Record requests for multiple models
        models = ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]

        for model in models:
            for i in range(5):
                metrics = PerformanceMetrics(
                    model=model,
                    task_type=TaskType.COMPLEX.value,
                    timestamp=time.time(),
                    input_tokens=200,
                    output_tokens=100,
                    total_tokens=300,
                    estimated_cost=self.tracker.calculate_cost(model, 200, 100),
                    latency_ms=500,
                    success=True,
                    finish_reason="stop"
                )
                self.tracker.record_request(metrics)
                time.sleep(0.01)

        # Get all stats
        all_stats = self.tracker.get_all_models_stats(TaskType.COMPLEX.value)

        self.assertEqual(len(all_stats), 3)
        self.assertTrue(all(s.total_requests == 5 for s in all_stats))

    def test_get_best_model_for_task(self):
        """Test finding the best model for a task type."""
        # Create models with different characteristics
        # Model 1: Fast but expensive
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="fast-model",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.01,  # Expensive
                latency_ms=100,  # Fast
                success=True,
                finish_reason="stop",
                quality_score=0.85
            ))
            time.sleep(0.01)

        # Model 2: Slow but cheap
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="cheap-model",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.001,  # Cheap
                latency_ms=1000,  # Slow
                success=True,
                finish_reason="stop",
                quality_score=0.85
            ))
            time.sleep(0.01)

        # Model 3: Balanced
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="balanced-model",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.005,
                latency_ms=500,
                success=True,
                finish_reason="stop",
                quality_score=0.9  # Higher quality
            ))
            time.sleep(0.01)

        # Test different optimization strategies
        best_for_speed = self.tracker.get_best_model_for_task(
            TaskType.SIMPLE.value, "speed"
        )
        self.assertEqual(best_for_speed, "fast-model")

        best_for_cost = self.tracker.get_best_model_for_task(
            TaskType.SIMPLE.value, "cost"
        )
        self.assertEqual(best_for_cost, "cheap-model")

        best_for_quality = self.tracker.get_best_model_for_task(
            TaskType.SIMPLE.value, "quality"
        )
        self.assertEqual(best_for_quality, "balanced-model")

    def test_cleanup_old_data(self):
        """Test cleaning up old performance data."""
        # Record old data
        old_timestamp = time.time() - (40 * 24 * 3600)  # 40 days ago

        self.tracker.record_request(PerformanceMetrics(
            model="deepseek-chat",
            task_type=TaskType.SIMPLE.value,
            timestamp=old_timestamp,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.0001,
            latency_ms=250,
            success=True,
            finish_reason="stop"
        ))

        # Record recent data
        self.tracker.record_request(PerformanceMetrics(
            model="deepseek-chat",
            task_type=TaskType.SIMPLE.value,
            timestamp=time.time(),
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.0001,
            latency_ms=250,
            success=True,
            finish_reason="stop"
        ))

        # Clean up data older than 30 days
        self.tracker.cleanup_old_data(days_to_keep=30)

        # Verify only recent data remains
        stats = self.tracker.get_model_stats("deepseek-chat", TaskType.SIMPLE.value)
        self.assertEqual(stats.total_requests, 1)

    def test_export_stats(self):
        """Test exporting statistics to JSON."""
        # Record some data
        for i in range(5):
            self.tracker.record_request(PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.0001,
                latency_ms=250,
                success=True,
                finish_reason="stop"
            ))
            time.sleep(0.01)

        # Export stats
        export_path = os.path.join(self.temp_dir, "stats.json")
        self.tracker.export_stats(export_path)

        # Verify file exists and contains data
        self.assertTrue(Path(export_path).exists())

        import json
        with open(export_path) as f:
            data = json.load(f)

        self.assertIn("models", data)
        self.assertGreater(len(data["models"]), 0)


class TestModelOptimizer(unittest.TestCase):
    """Test ModelOptimizer functionality."""

    def setUp(self):
        """Set up test optimizer."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_performance.db")
        self.tracker = ModelPerformanceTracker(self.db_path)

        # Mock models config
        self.models_config = {
            "deepseek-chat": ModelConfig(
                max_tokens=4096,
                temperature=0.7,
                difficulty_range=["simple", "medium"]
            ),
            "deepseek-coder": ModelConfig(
                max_tokens=8192,
                temperature=0.3,
                difficulty_range=["medium", "complex"]
            ),
            "deepseek-reasoner": ModelConfig(
                max_tokens=8192,
                temperature=0.5,
                difficulty_range=["complex", "expert"]
            )
        }

        self.optimizer = ModelOptimizer(
            tracker=self.tracker,
            models_config=self.models_config,
            strategy=OptimizationStrategy(optimize_for="balanced")
        )

    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_select_optimal_model_no_data(self):
        """Test model selection with no performance data."""
        characteristics = TaskCharacteristics(
            difficulty=TaskDifficulty.SIMPLE,
            is_coding=False,
            requires_reasoning=False,
            message_count=1,
            estimated_tokens=100
        )

        model, reason = self.optimizer.select_optimal_model(
            characteristics,
            default_model="deepseek-chat"
        )

        # Should fall back to default
        self.assertEqual(model, "deepseek-chat")
        self.assertEqual(reason, "insufficient_data_fallback")

    def test_select_optimal_model_with_data(self):
        """Test model selection with performance data."""
        # Populate performance data
        for i in range(20):
            self.tracker.record_request(PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.0001,
                latency_ms=250,
                success=True,
                finish_reason="stop",
                quality_score=0.95
            ))
            time.sleep(0.01)

        # Create task characteristics
        characteristics = TaskCharacteristics(
            difficulty=TaskDifficulty.SIMPLE,
            is_coding=False,
            requires_reasoning=False,
            message_count=1,
            estimated_tokens=100
        )

        # Select model
        model, reason = self.optimizer.select_optimal_model(
            characteristics,
            default_model="deepseek-coder"
        )

        # Should select deepseek-chat based on performance data
        self.assertEqual(model, "deepseek-chat")
        self.assertIn("optimized", reason)

    def test_get_model_recommendations(self):
        """Test getting model recommendations for task types."""
        # Add performance data for multiple models and task types
        models = ["deepseek-chat", "deepseek-coder"]
        task_types = [TaskType.SIMPLE.value, TaskType.CODING.value]

        for model in models:
            for task_type in task_types:
                for i in range(10):
                    self.tracker.record_request(PerformanceMetrics(
                        model=model,
                        task_type=task_type,
                        timestamp=time.time(),
                        input_tokens=100,
                        output_tokens=50,
                        total_tokens=150,
                        estimated_cost=0.0001,
                        latency_ms=300,
                        success=True,
                        finish_reason="stop",
                        quality_score=0.9
                    ))
                    time.sleep(0.01)

        # Get recommendations
        recommendations = self.optimizer.get_model_recommendations(task_types)

        self.assertEqual(len(recommendations), len(task_types))
        for task_type in task_types:
            self.assertIn(task_type, recommendations)
            self.assertIn("recommended_model", recommendations[task_type])

    def test_analyze_cost_performance_tradeoff(self):
        """Test cost-performance tradeoff analysis."""
        # Add data for models with different cost-performance profiles
        # Expensive but high quality
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="expensive-model",
                task_type=TaskType.COMPLEX.value,
                timestamp=time.time(),
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                estimated_cost=0.1,  # Expensive
                latency_ms=500,
                success=True,
                finish_reason="stop",
                quality_score=0.98  # High quality
            ))
            time.sleep(0.01)

        # Cheap but lower quality
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="cheap-model",
                task_type=TaskType.COMPLEX.value,
                timestamp=time.time(),
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                estimated_cost=0.01,  # Cheap
                latency_ms=500,
                success=True,
                finish_reason="stop",
                quality_score=0.85  # Lower quality
            ))
            time.sleep(0.01)

        # Analyze tradeoff
        analysis = self.optimizer.analyze_cost_performance_tradeoff(
            TaskType.COMPLEX.value
        )

        self.assertEqual(analysis["models_analyzed"], 2)
        self.assertIsNotNone(analysis["best_value_model"])
        self.assertEqual(len(analysis["models"]), 2)

        # Verify cost-per-quality calculation
        for model_data in analysis["models"]:
            self.assertIn("cost_per_quality", model_data)
            self.assertGreater(model_data["cost_per_quality"], 0)

    def test_optimization_strategy(self):
        """Test different optimization strategies."""
        # Add performance data
        for i in range(15):
            self.tracker.record_request(PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.0001,
                latency_ms=200,
                success=True,
                finish_reason="stop",
                quality_score=0.9
            ))
            time.sleep(0.01)

        # Test with learning enabled
        optimizer_learning = ModelOptimizer(
            tracker=self.tracker,
            models_config=self.models_config,
            strategy=OptimizationStrategy(enable_learning=True)
        )

        characteristics = TaskCharacteristics(
            difficulty=TaskDifficulty.SIMPLE,
            is_coding=False,
            requires_reasoning=False,
            message_count=1,
            estimated_tokens=100
        )

        model, reason = optimizer_learning.select_optimal_model(
            characteristics,
            default_model="deepseek-coder"
        )
        self.assertIn("optimized", reason)

        # Test with learning disabled
        optimizer_no_learning = ModelOptimizer(
            tracker=self.tracker,
            models_config=self.models_config,
            strategy=OptimizationStrategy(enable_learning=False)
        )

        model, reason = optimizer_no_learning.select_optimal_model(
            characteristics,
            default_model="deepseek-coder"
        )
        self.assertEqual(reason, "learning_disabled")

    def test_suggest_improvements(self):
        """Test improvement suggestions."""
        # Add some performance data
        for i in range(20):
            self.tracker.record_request(PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.0001,
                latency_ms=250,
                success=True,
                finish_reason="stop",
                quality_score=0.9
            ))
            time.sleep(0.01)

        suggestions = self.optimizer.suggest_improvements()

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_get_optimization_report(self):
        """Test comprehensive optimization report generation."""
        # Add performance data
        for i in range(10):
            self.tracker.record_request(PerformanceMetrics(
                model="deepseek-chat",
                task_type=TaskType.SIMPLE.value,
                timestamp=time.time(),
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.0001,
                latency_ms=250,
                success=True,
                finish_reason="stop",
                quality_score=0.9
            ))
            time.sleep(0.01)

        report = self.optimizer.get_optimization_report()

        # Verify report structure
        self.assertIn("optimization_strategy", report)
        self.assertIn("overall_stats", report)
        self.assertIn("task_type_recommendations", report)
        self.assertIn("cost_performance_analysis", report)
        self.assertIn("model_statistics", report)

        # Verify overall stats
        self.assertEqual(report["overall_stats"]["total_requests"], 10)
        self.assertGreater(report["overall_stats"]["total_cost_usd"], 0)


if __name__ == "__main__":
    unittest.main()
