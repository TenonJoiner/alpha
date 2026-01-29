"""
Alpha - Schedule Storage

Provides persistent storage for scheduled tasks using SQLite.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import asdict


logger = logging.getLogger(__name__)


class ScheduleStorage:
    """
    Persistent storage for task schedules.

    Uses SQLite database to store:
    - Schedule configurations
    - Execution history
    - Schedule metadata
    """

    def __init__(self, db_path: str):
        """
        Initialize schedule storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        """Initialize database connection and create tables."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Schedule storage initialized: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                task_description TEXT,
                task_params TEXT,
                schedule_type TEXT NOT NULL,
                schedule_config TEXT,
                enabled INTEGER DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                metadata TEXT
            )
        """)

        # Schedule execution history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_runs (
                id TEXT PRIMARY KEY,
                schedule_id TEXT NOT NULL,
                task_id TEXT,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT,
                FOREIGN KEY(schedule_id) REFERENCES schedules(id)
            )
        """)

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_enabled
            ON schedules(enabled)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_next_run
            ON schedules(next_run)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_id
            ON schedule_runs(schedule_id)
        """)

        self.conn.commit()

    def add_schedule(self, schedule_data: Dict[str, Any]) -> str:
        """
        Add a new schedule to storage.

        Args:
            schedule_data: Schedule data dictionary

        Returns:
            Schedule ID
        """
        cursor = self.conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO schedules (
                id, task_name, task_description, task_params,
                schedule_type, schedule_config, enabled,
                last_run, next_run, run_count,
                created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule_data["id"],
            schedule_data["task_name"],
            schedule_data.get("task_description", ""),
            json.dumps(schedule_data.get("task_params", {})),
            schedule_data["schedule_type"],
            json.dumps(schedule_data.get("schedule_config", {})),
            schedule_data.get("enabled", True),
            schedule_data.get("last_run"),
            schedule_data.get("next_run"),
            schedule_data.get("run_count", 0),
            now,
            now,
            json.dumps(schedule_data.get("metadata", {}))
        ))

        self.conn.commit()
        logger.info(f"Added schedule: {schedule_data['id']}")
        return schedule_data["id"]

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            Schedule data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules WHERE id = ?
        """, (schedule_id,))

        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    def list_schedules(
        self,
        enabled: Optional[bool] = None,
        schedule_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List schedules with optional filtering.

        Args:
            enabled: Filter by enabled status
            schedule_type: Filter by schedule type
            limit: Maximum number of results

        Returns:
            List of schedule data
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM schedules WHERE 1=1"
        params = []

        if enabled is not None:
            query += " AND enabled = ?"
            params.append(int(enabled))

        if schedule_type:
            query += " AND schedule_type = ?"
            params.append(schedule_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_due_schedules(self, now: datetime) -> List[Dict[str, Any]]:
        """
        Get schedules that are due to run.

        Args:
            now: Current datetime

        Returns:
            List of due schedule data
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules
            WHERE enabled = 1
            AND (next_run IS NULL OR next_run <= ?)
            ORDER BY next_run ASC
        """, (now.isoformat(),))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update schedule fields.

        Args:
            schedule_id: Schedule ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        if not updates:
            return False

        cursor = self.conn.cursor()

        # Build UPDATE query dynamically
        set_parts = []
        params = []

        for key, value in updates.items():
            if key in ["task_params", "schedule_config", "metadata"]:
                value = json.dumps(value)
            set_parts.append(f"{key} = ?")
            params.append(value)

        # Always update updated_at
        set_parts.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        # Add schedule_id to params
        params.append(schedule_id)

        query = f"""
            UPDATE schedules
            SET {', '.join(set_parts)}
            WHERE id = ?
        """

        cursor.execute(query, params)
        self.conn.commit()

        updated = cursor.rowcount > 0
        if updated:
            logger.info(f"Updated schedule: {schedule_id}")
        return updated

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete schedule and its history.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()

        # Delete history first
        cursor.execute("""
            DELETE FROM schedule_runs WHERE schedule_id = ?
        """, (schedule_id,))

        # Delete schedule
        cursor.execute("""
            DELETE FROM schedules WHERE id = ?
        """, (schedule_id,))

        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted schedule: {schedule_id}")
        return deleted

    def add_run_history(self, run_data: Dict[str, Any]) -> str:
        """
        Add schedule execution history entry.

        Args:
            run_data: Run history data

        Returns:
            Run history ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO schedule_runs (
                id, schedule_id, task_id, started_at,
                completed_at, status, result, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_data["id"],
            run_data["schedule_id"],
            run_data.get("task_id"),
            run_data["started_at"],
            run_data.get("completed_at"),
            run_data["status"],
            json.dumps(run_data.get("result")),
            run_data.get("error")
        ))

        self.conn.commit()
        return run_data["id"]

    def get_run_history(
        self,
        schedule_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for a schedule.

        Args:
            schedule_id: Schedule ID
            limit: Maximum number of results

        Returns:
            List of run history data
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM schedule_runs
            WHERE schedule_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (schedule_id, limit))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get schedule statistics.

        Returns:
            Statistics dictionary
        """
        cursor = self.conn.cursor()

        # Total schedules
        cursor.execute("SELECT COUNT(*) as count FROM schedules")
        total = cursor.fetchone()["count"]

        # Enabled schedules
        cursor.execute("SELECT COUNT(*) as count FROM schedules WHERE enabled = 1")
        enabled = cursor.fetchone()["count"]

        # By type
        cursor.execute("""
            SELECT schedule_type, COUNT(*) as count
            FROM schedules
            GROUP BY schedule_type
        """)
        by_type = {row["schedule_type"]: row["count"] for row in cursor.fetchall()}

        # Total runs
        cursor.execute("SELECT COUNT(*) as count FROM schedule_runs")
        total_runs = cursor.fetchone()["count"]

        # Successful runs
        cursor.execute("""
            SELECT COUNT(*) as count FROM schedule_runs
            WHERE status = 'completed'
        """)
        successful_runs = cursor.fetchone()["count"]

        return {
            "total_schedules": total,
            "enabled_schedules": enabled,
            "by_type": by_type,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (
                successful_runs / total_runs if total_runs > 0 else 0
            )
        }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary with JSON parsing."""
        data = dict(row)

        # Parse JSON fields
        for field in ["task_params", "schedule_config", "metadata", "result"]:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = {}

        # Convert integer boolean
        if "enabled" in data:
            data["enabled"] = bool(data["enabled"])

        return data

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Schedule storage closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
