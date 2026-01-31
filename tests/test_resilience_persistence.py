"""
Tests for SQLite Persistence Layer (FailureStore)

Tests the FailureStore class and its integration with FailureAnalyzer.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from alpha.core.resilience.storage import FailureStore
from alpha.core.resilience.analyzer import FailureAnalyzer
from alpha.core.resilience.retry import ErrorType


class TestFailureStore:
    """Test cases for FailureStore"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_failures.db")
            yield db_path

    @pytest.fixture
    def store(self, temp_db):
        """Create FailureStore instance"""
        return FailureStore(temp_db)

    def test_initialization(self, store, temp_db):
        """Test database initialization"""
        assert os.path.exists(temp_db)
        assert store.db_path == temp_db

    def test_save_failure(self, store):
        """Test saving failure record"""
        failure_id = store.save_failure(
            timestamp=datetime.now(),
            error_type="NETWORK",
            error_message="Connection timeout",
            operation="http_request",
            context={"url": "https://example.com"},
            stack_trace=None
        )

        assert failure_id > 0

    def test_get_failures(self, store):
        """Test retrieving failure records"""
        # Save multiple failures
        now = datetime.now()
        for i in range(3):
            store.save_failure(
                timestamp=now - timedelta(hours=i),
                error_type="NETWORK",
                error_message=f"Error {i}",
                operation="test_op",
                context={"index": i}
            )

        # Retrieve all failures
        failures = store.get_failures()
        assert len(failures) == 3

        # Most recent first
        assert failures[0]['error_message'] == "Error 0"

    def test_get_failures_filtered_by_operation(self, store):
        """Test filtering failures by operation"""
        now = datetime.now()

        store.save_failure(now, "NETWORK", "Error A", "op_a")
        store.save_failure(now, "NETWORK", "Error B", "op_b")
        store.save_failure(now, "NETWORK", "Error A2", "op_a")

        failures = store.get_failures(operation="op_a")
        assert len(failures) == 2

    def test_get_failures_filtered_by_error_type(self, store):
        """Test filtering failures by error type"""
        now = datetime.now()

        store.save_failure(now, "NETWORK", "Error 1", "test_op")
        store.save_failure(now, "AUTHENTICATION", "Error 2", "test_op")
        store.save_failure(now, "NETWORK", "Error 3", "test_op")

        failures = store.get_failures(error_type="NETWORK")
        assert len(failures) == 2

    def test_get_failures_filtered_by_time(self, store):
        """Test filtering failures by time window"""
        now = datetime.now()
        old_time = now - timedelta(days=10)

        store.save_failure(old_time, "NETWORK", "Old error", "test_op")
        store.save_failure(now, "NETWORK", "Recent error", "test_op")

        # Get failures from last 5 days
        since = now - timedelta(days=5)
        failures = store.get_failures(since=since)
        assert len(failures) == 1
        assert failures[0]['error_message'] == "Recent error"

    def test_cleanup_old_failures(self, store):
        """Test cleaning up old failure records"""
        now = datetime.now()
        old_time = now - timedelta(days=40)

        # Save old and recent failures
        store.save_failure(old_time, "NETWORK", "Old error", "test_op")
        store.save_failure(now, "NETWORK", "Recent error", "test_op")

        # Cleanup failures older than 30 days
        deleted = store.cleanup_old_failures(days=30)
        assert deleted == 1

        # Verify only recent failure remains
        failures = store.get_failures()
        assert len(failures) == 1
        assert failures[0]['error_message'] == "Recent error"

    def test_add_to_blacklist(self, store):
        """Test adding strategy to blacklist"""
        store.add_to_blacklist(
            strategy_name="provider_openai",
            operation="llm_request",
            reason="Repeated timeout errors"
        )

        assert store.is_blacklisted("provider_openai", "llm_request")

    def test_is_blacklisted_returns_false_for_non_blacklisted(self, store):
        """Test checking non-blacklisted strategy"""
        assert not store.is_blacklisted("strategy_x", "operation_y")

    def test_blacklist_update_on_duplicate(self, store):
        """Test updating blacklist entry on duplicate add"""
        # Add strategy to blacklist
        store.add_to_blacklist("strategy_a", "op_a")

        # Add again
        store.add_to_blacklist("strategy_a", "op_a", "More failures")

        # Should still be blacklisted
        assert store.is_blacklisted("strategy_a", "op_a")

        # Check failure count incremented
        blacklist = store.get_blacklist()
        entry = next(b for b in blacklist if b['strategy_name'] == "strategy_a")
        assert entry['failure_count'] == 2

    def test_remove_from_blacklist(self, store):
        """Test removing strategy from blacklist"""
        store.add_to_blacklist("strategy_b", "op_b")
        assert store.is_blacklisted("strategy_b", "op_b")

        removed = store.remove_from_blacklist("strategy_b", "op_b")
        assert removed is True
        assert not store.is_blacklisted("strategy_b", "op_b")

    def test_remove_non_existent_from_blacklist(self, store):
        """Test removing non-existent entry from blacklist"""
        removed = store.remove_from_blacklist("nonexistent", "op")
        assert removed is False

    def test_get_blacklist(self, store):
        """Test retrieving all blacklisted strategies"""
        store.add_to_blacklist("strategy_1", "op_1")
        store.add_to_blacklist("strategy_2", "op_2")

        blacklist = store.get_blacklist()
        assert len(blacklist) >= 2

        names = [b['strategy_name'] for b in blacklist]
        assert "strategy_1" in names
        assert "strategy_2" in names

    def test_get_failure_analytics(self, store):
        """Test analytics generation"""
        now = datetime.now()

        # Create various failures
        store.save_failure(now, "NETWORK", "Error 1", "op_a")
        store.save_failure(now, "NETWORK", "Error 2", "op_a")
        store.save_failure(now, "AUTHENTICATION", "Error 3", "op_b")
        store.add_to_blacklist("strategy_x", "op_a")

        analytics = store.get_failure_analytics()

        assert analytics['total_failures'] == 3
        assert analytics['blacklisted_strategies'] == 1
        assert len(analytics['most_common_errors']) > 0
        assert analytics['most_common_errors'][0]['error_type'] == "NETWORK"
        assert analytics['most_common_errors'][0]['count'] == 2

    def test_context_json_serialization(self, store):
        """Test complex context serialization"""
        context = {
            "url": "https://example.com",
            "headers": {"Authorization": "Bearer token"},
            "retry_count": 3,
            "nested": {"key": "value"}
        }

        failure_id = store.save_failure(
            timestamp=datetime.now(),
            error_type="NETWORK",
            error_message="Test error",
            operation="test_op",
            context=context
        )

        failures = store.get_failures()
        assert len(failures) > 0
        retrieved = failures[0]
        assert retrieved['context'] == context

    def test_clear_all(self, store):
        """Test clearing all data"""
        # Add some data
        store.save_failure(datetime.now(), "NETWORK", "Error", "op")
        store.add_to_blacklist("strategy", "op")

        # Clear all
        store.clear_all()

        # Verify empty
        assert len(store.get_failures()) == 0
        assert len(store.get_blacklist()) == 0


class TestFailureAnalyzerWithPersistence:
    """Test FailureAnalyzer with SQLite persistence enabled"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_analyzer.db")
            yield db_path

    @pytest.fixture
    def analyzer(self, temp_db):
        """Create FailureAnalyzer with persistence"""
        return FailureAnalyzer(
            pattern_threshold=3,
            enable_persistence=True,
            db_path=temp_db
        )

    def test_persistence_initialization(self, analyzer, temp_db):
        """Test analyzer initializes with persistence"""
        assert analyzer.enable_persistence is True
        assert analyzer.store is not None
        assert os.path.exists(temp_db)

    def test_record_failure_persists(self, analyzer):
        """Test failures are persisted to database"""
        error = Exception("Test error")
        analyzer.record_failure(error, "test_operation")

        # Check in-memory
        assert len(analyzer.failure_history) == 1

        # Check database
        db_failures = analyzer.store.get_failures()
        assert len(db_failures) >= 1

    def test_load_recent_failures(self, temp_db):
        """Test loading failures from database on initialization"""
        # Create analyzer and record failure
        analyzer1 = FailureAnalyzer(enable_persistence=True, db_path=temp_db)
        analyzer1.record_failure(Exception("Error 1"), "op1")
        analyzer1.record_failure(Exception("Error 2"), "op2")

        # Create new analyzer instance (simulates restart)
        analyzer2 = FailureAnalyzer(enable_persistence=True, db_path=temp_db)

        # Should have loaded failures from database
        assert len(analyzer2.failure_history) >= 2

    def test_blacklist_integration(self, analyzer):
        """Test blacklist functionality"""
        # Add to blacklist
        analyzer.add_to_blacklist("failing_strategy", "test_op", "Too many failures")

        # Check blacklist
        assert analyzer.is_strategy_blacklisted("failing_strategy", "test_op")

        # Remove from blacklist
        analyzer.remove_from_blacklist("failing_strategy", "test_op")
        assert not analyzer.is_strategy_blacklisted("failing_strategy", "test_op")

    def test_get_blacklist(self, analyzer):
        """Test retrieving blacklist"""
        analyzer.add_to_blacklist("strategy_a", "op_a")
        analyzer.add_to_blacklist("strategy_b", "op_b")

        blacklist = analyzer.get_blacklist()
        assert len(blacklist) >= 2

    def test_get_analytics(self, analyzer):
        """Test analytics with persistence"""
        # Record multiple failures
        for i in range(5):
            analyzer.record_failure(Exception(f"Error {i}"), "test_op")

        analytics = analyzer.get_analytics()

        assert 'total_failures' in analytics
        assert analytics['total_failures'] >= 5
        assert 'in_memory_failures' in analytics

    def test_cleanup_old_failures(self, analyzer, temp_db):
        """Test cleanup of old failures"""
        # Manually add old failure to database
        old_time = datetime.now() - timedelta(days=40)
        analyzer.store.save_failure(old_time, "NETWORK", "Old error", "test_op")

        # Add recent failure
        analyzer.record_failure(Exception("Recent error"), "test_op")

        # Cleanup
        deleted = analyzer.cleanup_old_failures(days=30)
        assert deleted >= 1

        # Verify old failure removed
        all_failures = analyzer.store.get_failures(limit=1000)
        old_failures = [f for f in all_failures if f['error_message'] == "Old error"]
        assert len(old_failures) == 0

    def test_persistence_disabled_fallback(self):
        """Test analyzer works without persistence"""
        analyzer = FailureAnalyzer(enable_persistence=False)

        assert analyzer.enable_persistence is False
        assert analyzer.store is None

        # Should still work in memory
        analyzer.record_failure(Exception("Test"), "op")
        assert len(analyzer.failure_history) == 1

        # Blacklist operations should fail gracefully
        analyzer.add_to_blacklist("strategy", "op")  # Should log warning
        assert not analyzer.is_strategy_blacklisted("strategy", "op")

    def test_persistence_with_invalid_path_fallsback(self):
        """Test analyzer falls back to memory-only if DB path invalid"""
        analyzer = FailureAnalyzer(
            enable_persistence=True,
            db_path="/invalid/path/failures.db"
        )

        # Should have fallen back to memory-only
        assert analyzer.enable_persistence is False
        assert analyzer.store is None

        # Should still work
        analyzer.record_failure(Exception("Test"), "op")
        assert len(analyzer.failure_history) == 1
