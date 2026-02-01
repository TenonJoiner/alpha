"""
Tests for WorkflowPatternDetector

Tests pattern detection from task execution history.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from alpha.workflow.pattern_detector import (
    WorkflowPatternDetector,
    WorkflowPattern
)


@pytest.fixture
def test_db():
    """Create temporary test database."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = temp_file.name
    temp_file.close()

    # Create task_manager table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_manager (
            id TEXT PRIMARY KEY,
            description TEXT,
            created_at TEXT,
            status TEXT,
            result TEXT
        )
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def detector(test_db):
    """Create WorkflowPatternDetector instance."""
    return WorkflowPatternDetector(
        database_path=test_db,
        min_frequency=3,
        min_sequence_length=2,
        max_interval_days=7,
        min_confidence=0.5  # Lowered for testing
    )


class TestNormalization:
    """Test task description normalization."""

    def test_normalize_removes_dates(self, detector):
        """Test that dates are removed from descriptions."""
        result = detector.normalize_task_description(
            "Deploy to staging on 2026-01-15"
        )
        assert "2026-01-15" not in result
        assert "deploy to staging" in result

    def test_normalize_removes_times(self, detector):
        """Test that times are removed."""
        result = detector.normalize_task_description(
            "Backup files at 23:45:30"
        )
        assert "23:45" not in result
        assert "backup files" in result

    def test_normalize_removes_file_paths(self, detector):
        """Test that file paths are simplified."""
        result = detector.normalize_task_description(
            "Run tests on /home/user/project/test_file.py"
        )
        assert "/home/user/project" not in result
        assert "test_file.py" in result

    def test_normalize_keeps_semantic_numbers(self, detector):
        """Test that semantic numbers like 'step 1' are kept."""
        result = detector.normalize_task_description(
            "Execute step 1 of deployment"
        )
        assert "step 1" in result

    def test_normalize_removes_standalone_numbers(self, detector):
        """Test that standalone numbers are removed."""
        result = detector.normalize_task_description(
            "Process 42 items from queue"
        )
        assert "42" not in result
        assert "process" in result
        assert "items from queue" in result

    def test_normalize_lowercase(self, detector):
        """Test that descriptions are converted to lowercase."""
        result = detector.normalize_task_description(
            "Deploy To PRODUCTION"
        )
        assert result == "deploy to production"

    def test_normalize_whitespace(self, detector):
        """Test that extra whitespace is removed."""
        result = detector.normalize_task_description(
            "Run   tests    with    coverage"
        )
        assert result == "run tests with coverage"


class TestPatternDetection:
    """Test pattern detection from task history."""

    def _insert_tasks(self, db_path, tasks):
        """Helper to insert tasks into database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for task in tasks:
            cursor.execute("""
                INSERT INTO task_manager (id, description, created_at, status, result)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task['id'],
                task['description'],
                task['created_at'].isoformat(),
                task.get('status', 'completed'),
                task.get('result', 'success')
            ))
        conn.commit()
        conn.close()

    def test_detect_simple_recurring_pattern(self, detector, test_db):
        """Test detection of simple recurring pattern."""
        # Create pattern: git pull → run tests (repeated 3 times)
        base_time = datetime.now() - timedelta(days=10)
        tasks = []

        for i in range(3):
            offset = timedelta(days=i * 2)
            tasks.extend([
                {
                    'id': f'task_{i}_1',
                    'description': f'git pull on {(base_time + offset).strftime("%Y-%m-%d")}',
                    'created_at': base_time + offset
                },
                {
                    'id': f'task_{i}_2',
                    'description': 'run tests',
                    'created_at': base_time + offset + timedelta(minutes=5)
                }
            ])

        self._insert_tasks(test_db, tasks)

        # Detect patterns
        patterns = detector.detect_workflow_patterns(lookback_days=15)

        # Should find the git pull → run tests pattern
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.frequency >= 3
        assert len(pattern.task_sequence) == 2
        assert 'git pull' in pattern.task_sequence[0]
        assert 'run tests' in pattern.task_sequence[1]

    def test_no_pattern_insufficient_frequency(self, detector, test_db):
        """Test that patterns with insufficient frequency are filtered."""
        base_time = datetime.now() - timedelta(days=5)
        tasks = [
            {
                'id': 'task_1',
                'description': 'deploy to staging',
                'created_at': base_time
            },
            {
                'id': 'task_2',
                'description': 'run smoke tests',
                'created_at': base_time + timedelta(minutes=10)
            },
            # Only 1 occurrence - should not be detected
        ]

        self._insert_tasks(test_db, tasks)

        patterns = detector.detect_workflow_patterns(lookback_days=10)

        # Should not find any patterns (frequency < 3)
        assert len(patterns) == 0

    def test_pattern_with_different_dates_normalized(self, detector, test_db):
        """Test that patterns with different dates are recognized as same."""
        base_time = datetime.now() - timedelta(days=10)
        tasks = []

        # Same tasks on different days
        for i in range(4):
            day = base_time + timedelta(days=i)
            tasks.extend([
                {
                    'id': f'task_{i}_1',
                    'description': f'backup data on {day.strftime("%Y-%m-%d")}',
                    'created_at': day
                },
                {
                    'id': f'task_{i}_2',
                    'description': f'sync to cloud at {day.strftime("%H:%M")}',
                    'created_at': day + timedelta(minutes=5)
                }
            ])

        self._insert_tasks(test_db, tasks)

        patterns = detector.detect_workflow_patterns(lookback_days=15)

        # Should recognize all as same pattern
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.frequency == 4
        assert 'backup data' in pattern.task_sequence[0]
        assert 'sync to cloud' in pattern.task_sequence[1]

    def test_confidence_scoring(self, detector, test_db):
        """Test confidence score calculation."""
        base_time = datetime.now() - timedelta(days=10)
        tasks = []

        # Create high-confidence pattern (frequent, regular intervals)
        for i in range(5):
            offset = timedelta(days=i * 2)  # Regular 2-day intervals
            tasks.extend([
                {
                    'id': f'task_{i}_1',
                    'description': 'git pull',
                    'created_at': base_time + offset
                },
                {
                    'id': f'task_{i}_2',
                    'description': 'run tests',
                    'created_at': base_time + offset + timedelta(minutes=2)
                },
                {
                    'id': f'task_{i}_3',
                    'description': 'check coverage',
                    'created_at': base_time + offset + timedelta(minutes=5)
                }
            ])

        self._insert_tasks(test_db, tasks)

        patterns = detector.detect_workflow_patterns(lookback_days=15)

        assert len(patterns) > 0
        pattern = patterns[0]

        # High frequency (5), regular intervals, longer sequence (3)
        # Should have high confidence
        assert pattern.confidence >= 0.6

    def test_temporal_proximity_filter(self, detector, test_db):
        """Test that patterns outside max_interval are filtered."""
        # Create tasks far apart in time
        base_time = datetime.now() - timedelta(days=30)
        tasks = []

        for i in range(3):
            # 20-day intervals (exceeds max_interval_days=7)
            offset = timedelta(days=i * 20)
            tasks.extend([
                {
                    'id': f'task_{i}_1',
                    'description': 'task A',
                    'created_at': base_time + offset
                },
                {
                    'id': f'task_{i}_2',
                    'description': 'task B',
                    'created_at': base_time + offset + timedelta(hours=1)
                }
            ])

        self._insert_tasks(test_db, tasks)

        patterns = detector.detect_workflow_patterns(lookback_days=70)

        # Should not detect pattern (intervals too large)
        assert len(patterns) == 0


class TestWorkflowNameGeneration:
    """Test workflow name generation."""

    def test_generate_name_from_verbs(self, detector):
        """Test name generation extracts verbs."""
        sequence = ['deploy to staging', 'run tests', 'verify deployment']
        name = detector._generate_workflow_name(sequence)

        # Should extract main verbs
        assert 'Deploy' in name or 'Run' in name

    def test_generate_name_max_length(self, detector):
        """Test that generated names respect max length."""
        sequence = [
            'this is a very long task description that goes on and on',
            'another extremely verbose task description',
            'yet another overly detailed task'
        ]
        name = detector._generate_workflow_name(sequence)

        assert len(name) <= 50

    def test_generate_name_single_task(self, detector):
        """Test name generation for single task."""
        sequence = ['backup files']
        name = detector._generate_workflow_name(sequence)

        assert 'Backup' in name or 'Workflow' in name


class TestPatternModel:
    """Test WorkflowPattern data model."""

    def test_pattern_to_dict(self):
        """Test pattern serialization to dict."""
        pattern = WorkflowPattern(
            pattern_id="test_1",
            task_sequence=["task A", "task B"],
            frequency=3,
            confidence=0.85,
            first_seen=datetime(2026, 1, 1, 10, 0),
            last_seen=datetime(2026, 1, 5, 10, 0),
            avg_interval=timedelta(days=2),
            task_ids=["id1", "id2", "id3"],
            suggested_workflow_name="Test Workflow",
            metadata={"key": "value"}
        )

        result = pattern.to_dict()

        assert result['pattern_id'] == "test_1"
        assert result['frequency'] == 3
        assert result['confidence'] == 0.85
        assert isinstance(result['first_seen'], str)  # ISO format
        assert isinstance(result['last_seen'], str)
        assert isinstance(result['avg_interval'], (int, float))  # Seconds


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_database(self, detector, test_db):
        """Test detection with empty database."""
        patterns = detector.detect_workflow_patterns()
        assert patterns == []

    def test_insufficient_tasks(self, detector, test_db):
        """Test with fewer tasks than min_sequence_length."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO task_manager (id, description, created_at, status, result)
            VALUES ('task_1', 'single task', ?, 'completed', 'success')
        """, (datetime.now().isoformat(),))
        conn.commit()
        conn.close()

        patterns = detector.detect_workflow_patterns()
        assert patterns == []

    def test_tasks_with_empty_descriptions(self, detector, test_db):
        """Test handling of tasks with empty descriptions."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        base_time = datetime.now()

        for i in range(5):
            cursor.execute("""
                INSERT INTO task_manager (id, description, created_at, status, result)
                VALUES (?, ?, ?, 'completed', 'success')
            """, (f'task_{i}', '', (base_time + timedelta(hours=i)).isoformat()))

        conn.commit()
        conn.close()

        # Should handle gracefully
        patterns = detector.detect_workflow_patterns()
        # Empty descriptions normalized to empty strings, won't form patterns
        assert patterns == []

    def test_database_error_handling(self):
        """Test handling of database errors."""
        # Non-existent database
        detector = WorkflowPatternDetector(
            database_path="/nonexistent/path/db.db"
        )

        # Should not crash, return empty list
        patterns = detector.detect_workflow_patterns()
        assert patterns == []


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_daily_development_workflow_pattern(self, detector, test_db):
        """Test detection of typical daily development workflow."""
        base_time = datetime.now() - timedelta(days=7)
        tasks = []

        # Simulate daily routine: git pull → run tests → check coverage
        for day in range(5):  # 5 weekdays
            day_start = base_time + timedelta(days=day)
            tasks.extend([
                {
                    'id': f'day{day}_pull',
                    'description': f'git pull origin main on {day_start.strftime("%Y-%m-%d")}',
                    'created_at': day_start.replace(hour=9, minute=0)
                },
                {
                    'id': f'day{day}_test',
                    'description': 'pytest tests/',
                    'created_at': day_start.replace(hour=9, minute=5)
                },
                {
                    'id': f'day{day}_coverage',
                    'description': 'coverage report',
                    'created_at': day_start.replace(hour=9, minute=10)
                }
            ])

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        for task in tasks:
            cursor.execute("""
                INSERT INTO task_manager (id, description, created_at, status, result)
                VALUES (?, ?, ?, 'completed', 'success')
            """, (task['id'], task['description'], task['created_at'].isoformat()))
        conn.commit()
        conn.close()

        patterns = detector.detect_workflow_patterns(lookback_days=10)

        # Should detect daily workflow pattern
        assert len(patterns) > 0

        # Find the 3-task pattern
        three_task_patterns = [p for p in patterns if len(p.task_sequence) == 3]
        assert len(three_task_patterns) > 0

        pattern = three_task_patterns[0]
        assert pattern.frequency == 5  # 5 occurrences
        assert pattern.confidence >= 0.55  # Good confidence
        assert 'git pull' in pattern.task_sequence[0]
        assert 'pytest' in pattern.task_sequence[1] or 'test' in pattern.task_sequence[1]
        assert 'coverage' in pattern.task_sequence[2]
