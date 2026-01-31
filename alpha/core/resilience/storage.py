"""
FailureStore - SQLite Persistence for Failure History

Provides persistent storage for failure records to enable learning across restarts.
"""

import sqlite3
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FailureStore:
    """
    SQLite-based persistent storage for failure records.

    Features:
    - Persistent failure history across restarts
    - 30-day automatic retention policy
    - Strategy blacklist management
    - Analytics queries for failure patterns

    Database Schema:
        failures: Stores failure records
        strategy_blacklist: Tracks blacklisted strategies
    """

    def __init__(self, db_path: str = "data/failures.db"):
        """
        Initialize failure store with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

        logger.info(f"FailureStore initialized: {db_path}")

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Failures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    context TEXT,
                    stack_trace TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON failures(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_operation
                ON failures(operation)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_type
                ON failures(error_type)
            """)

            # Strategy blacklist table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT UNIQUE NOT NULL,
                    operation TEXT NOT NULL,
                    failure_count INTEGER DEFAULT 1,
                    first_failed_at TEXT NOT NULL,
                    last_failed_at TEXT NOT NULL,
                    reason TEXT,
                    blacklisted_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategy_name
                ON strategy_blacklist(strategy_name)
            """)

            conn.commit()

            logger.debug("Database schema initialized")

    def save_failure(
        self,
        timestamp: datetime,
        error_type: str,
        error_message: str,
        operation: str,
        context: Optional[Dict] = None,
        stack_trace: Optional[str] = None
    ) -> int:
        """
        Save failure record to database.

        Args:
            timestamp: When failure occurred
            error_type: Type of error
            error_message: Error message
            operation: Operation that failed
            context: Additional context (JSON serializable)
            stack_trace: Stack trace if available

        Returns:
            ID of saved failure record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            context_json = json.dumps(context) if context else None

            cursor.execute("""
                INSERT INTO failures
                (timestamp, error_type, error_message, operation, context, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                error_type,
                error_message,
                operation,
                context_json,
                stack_trace
            ))

            conn.commit()
            failure_id = cursor.lastrowid

            logger.debug(f"Saved failure record: {failure_id}")

            return failure_id

    def get_failures(
        self,
        operation: Optional[str] = None,
        error_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Query failure records.

        Args:
            operation: Filter by operation name
            error_type: Filter by error type
            since: Only failures after this timestamp
            limit: Maximum records to return

        Returns:
            List of failure records as dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM failures WHERE 1=1"
            params = []

            if operation:
                query += " AND operation = ?"
                params.append(operation)

            if error_type:
                query += " AND error_type = ?"
                params.append(error_type)

            if since:
                query += " AND timestamp >= ?"
                params.append(since.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            failures = []
            for row in cursor.fetchall():
                failure = dict(row)
                # Parse context JSON
                if failure['context']:
                    try:
                        failure['context'] = json.loads(failure['context'])
                    except json.JSONDecodeError:
                        failure['context'] = {}
                failures.append(failure)

            return failures

    def cleanup_old_failures(self, days: int = 30) -> int:
        """
        Remove failures older than specified days.

        Args:
            days: Keep failures from last N days

        Returns:
            Number of failures deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM failures
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"Cleaned up {deleted_count} old failure records (>{days} days)")

            return deleted_count

    def add_to_blacklist(
        self,
        strategy_name: str,
        operation: str,
        reason: str = "Repeated failures"
    ):
        """
        Add strategy to blacklist.

        Args:
            strategy_name: Name of strategy to blacklist
            operation: Operation context
            reason: Reason for blacklisting
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if already blacklisted
            cursor.execute("""
                SELECT failure_count FROM strategy_blacklist
                WHERE strategy_name = ? AND operation = ?
            """, (strategy_name, operation))

            row = cursor.fetchone()

            if row:
                # Update existing blacklist entry
                cursor.execute("""
                    UPDATE strategy_blacklist
                    SET failure_count = failure_count + 1,
                        last_failed_at = ?,
                        reason = ?
                    WHERE strategy_name = ? AND operation = ?
                """, (
                    datetime.now().isoformat(),
                    reason,
                    strategy_name,
                    operation
                ))
                logger.debug(f"Updated blacklist for {strategy_name}: {row[0] + 1} failures")
            else:
                # Insert new blacklist entry
                now = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO strategy_blacklist
                    (strategy_name, operation, failure_count, first_failed_at, last_failed_at, reason)
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (
                    strategy_name,
                    operation,
                    now,
                    now,
                    reason
                ))
                logger.info(f"Added {strategy_name} to blacklist for operation {operation}")

            conn.commit()

    def is_blacklisted(self, strategy_name: str, operation: str) -> bool:
        """
        Check if strategy is blacklisted for operation.

        Args:
            strategy_name: Strategy to check
            operation: Operation context

        Returns:
            True if blacklisted, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM strategy_blacklist
                WHERE strategy_name = ? AND operation = ?
            """, (strategy_name, operation))

            return cursor.fetchone() is not None

    def remove_from_blacklist(self, strategy_name: str, operation: str):
        """
        Remove strategy from blacklist.

        Args:
            strategy_name: Strategy to remove
            operation: Operation context
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM strategy_blacklist
                WHERE strategy_name = ? AND operation = ?
            """, (strategy_name, operation))

            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                logger.info(f"Removed {strategy_name} from blacklist")

            return deleted > 0

    def get_blacklist(self) -> List[Dict]:
        """
        Get all blacklisted strategies.

        Returns:
            List of blacklisted strategy records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM strategy_blacklist
                ORDER BY failure_count DESC, last_failed_at DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

    def get_failure_analytics(self) -> Dict:
        """
        Generate analytics on failure patterns.

        Returns:
            Dictionary with analytics data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Most common error types
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM failures
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 10
            """)
            most_common_errors = [dict(row) for row in cursor.fetchall()]

            # Most problematic operations
            cursor.execute("""
                SELECT operation, COUNT(*) as failure_count
                FROM failures
                GROUP BY operation
                ORDER BY failure_count DESC
                LIMIT 10
            """)
            problematic_operations = [dict(row) for row in cursor.fetchall()]

            # Failure trends (last 7 days)
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM failures
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """)
            daily_trends = [dict(row) for row in cursor.fetchall()]

            # Total failures
            cursor.execute("SELECT COUNT(*) as total FROM failures")
            total_failures = cursor.fetchone()[0]

            # Blacklisted strategies count
            cursor.execute("SELECT COUNT(*) as total FROM strategy_blacklist")
            blacklisted_count = cursor.fetchone()[0]

            return {
                "total_failures": total_failures,
                "blacklisted_strategies": blacklisted_count,
                "most_common_errors": most_common_errors,
                "problematic_operations": problematic_operations,
                "daily_trends": daily_trends
            }

    def clear_all(self):
        """Clear all failure records and blacklist (for testing)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM failures")
            cursor.execute("DELETE FROM strategy_blacklist")
            conn.commit()
            logger.warning("Cleared all failure data")
