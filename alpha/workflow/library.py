"""
Workflow Library Module

Provides storage, retrieval, and management of workflow definitions.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .definition import WorkflowDefinition
from .schema import validate_workflow


class WorkflowLibrary:
    """
    Workflow library for storing and managing workflows

    Uses SQLite for persistent storage of workflow definitions and
    execution history.
    """

    def __init__(self, db_path: str = "data/workflows.db"):
        """
        Initialize workflow library

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create workflows table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT,
                tags TEXT,
                definition TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_count INTEGER DEFAULT 0,
                last_executed TIMESTAMP
            )
        """
        )

        # Create workflow_executions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                parameters TEXT,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT,
                error TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """
        )

        # Create indices
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows(tags)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_executions_workflow ON workflow_executions(workflow_id)"
        )

        conn.commit()
        conn.close()

    def save(self, workflow: WorkflowDefinition) -> bool:
        """
        Save workflow to library

        Args:
            workflow: WorkflowDefinition to save

        Returns:
            True if successful, False otherwise
        """
        # Validate workflow before saving
        is_valid, errors = validate_workflow(workflow)
        if not is_valid:
            raise ValueError(f"Invalid workflow: {', '.join(errors)}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Update timestamp
            workflow.updated_at = datetime.now()

            # Convert to JSON
            definition_json = json.dumps(workflow.to_dict())
            tags_json = json.dumps(workflow.tags)

            # Insert or replace
            cursor.execute(
                """
                INSERT OR REPLACE INTO workflows
                (id, name, version, description, author, tags, definition, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow.id,
                    workflow.name,
                    workflow.version,
                    workflow.description,
                    workflow.author,
                    tags_json,
                    definition_json,
                    workflow.created_at.isoformat() if workflow.created_at else None,
                    workflow.updated_at.isoformat(),
                ),
            )

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Error saving workflow: {e}")
            return False

        finally:
            conn.close()

    def get(self, name: str) -> Optional[WorkflowDefinition]:
        """
        Get workflow by name

        Args:
            name: Workflow name

        Returns:
            WorkflowDefinition or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT definition FROM workflows WHERE name = ?", (name,)
            )
            row = cursor.fetchone()

            if row:
                definition_json = json.loads(row[0])
                return WorkflowDefinition.from_dict(definition_json)

            return None

        finally:
            conn.close()

    def get_by_id(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get workflow by ID

        Args:
            workflow_id: Workflow ID

        Returns:
            WorkflowDefinition or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT definition FROM workflows WHERE id = ?", (workflow_id,)
            )
            row = cursor.fetchone()

            if row:
                definition_json = json.loads(row[0])
                return WorkflowDefinition.from_dict(definition_json)

            return None

        finally:
            conn.close()

    def list(
        self,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[WorkflowDefinition]:
        """
        List workflows with optional filtering

        Args:
            tags: Filter by tags (workflows matching any tag)
            search: Search in name and description
            limit: Maximum number of results

        Returns:
            List of WorkflowDefinition objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = "SELECT definition FROM workflows WHERE 1=1"
            params = []

            # Filter by tags
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                query += " AND (" + " OR ".join(tag_conditions) + ")"

            # Search in name and description
            if search:
                query += " AND (name LIKE ? OR description LIKE ?)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            workflows = []
            for row in rows:
                definition_json = json.loads(row[0])
                workflows.append(WorkflowDefinition.from_dict(definition_json))

            return workflows

        finally:
            conn.close()

    def delete(self, name: str) -> bool:
        """
        Delete workflow by name

        Args:
            name: Workflow name

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM workflows WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

        finally:
            conn.close()

    def exists(self, name: str) -> bool:
        """
        Check if workflow exists

        Args:
            name: Workflow name

        Returns:
            True if exists, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT 1 FROM workflows WHERE name = ?", (name,))
            return cursor.fetchone() is not None

        finally:
            conn.close()

    def count(self) -> int:
        """
        Get total number of workflows

        Returns:
            Number of workflows in library
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM workflows")
            return cursor.fetchone()[0]

        finally:
            conn.close()

    def export_workflow(self, name: str, file_path: str) -> bool:
        """
        Export workflow to YAML/JSON file

        Args:
            name: Workflow name
            file_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get(name)
        if not workflow:
            return False

        try:
            # Determine format from file extension
            file_path_obj = Path(file_path)
            workflow_dict = workflow.to_dict()

            if file_path_obj.suffix.lower() in [".yaml", ".yml"]:
                # Export as YAML
                import yaml

                with open(file_path, "w") as f:
                    yaml.dump(workflow_dict, f, default_flow_style=False)
            else:
                # Export as JSON
                with open(file_path, "w") as f:
                    json.dump(workflow_dict, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting workflow: {e}")
            return False

    def import_workflow(self, file_path: str) -> Optional[WorkflowDefinition]:
        """
        Import workflow from YAML/JSON file

        Args:
            file_path: Input file path

        Returns:
            Imported WorkflowDefinition or None if failed
        """
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                print(f"File not found: {file_path}")
                return None

            # Determine format from file extension
            if file_path_obj.suffix.lower() in [".yaml", ".yml"]:
                # Import from YAML
                import yaml

                with open(file_path, "r") as f:
                    workflow_dict = yaml.safe_load(f)
            else:
                # Import from JSON
                with open(file_path, "r") as f:
                    workflow_dict = json.load(f)

            # Create workflow from dict
            workflow = WorkflowDefinition.from_dict(workflow_dict)

            # Save to library
            self.save(workflow)

            return workflow

        except Exception as e:
            print(f"Error importing workflow: {e}")
            return None

    def log_execution(
        self,
        workflow_id: str,
        execution_id: str,
        parameters: Dict[str, Any],
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Log workflow execution

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
            parameters: Execution parameters
            status: Execution status (pending, running, completed, failed)
            started_at: Execution start time
            completed_at: Execution completion time
            result: Execution result
            error: Error message if failed

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO workflow_executions
                (id, workflow_id, parameters, status, started_at, completed_at, result, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    execution_id,
                    workflow_id,
                    json.dumps(parameters),
                    status,
                    started_at.isoformat(),
                    completed_at.isoformat() if completed_at else None,
                    json.dumps(result) if result else None,
                    error,
                ),
            )

            # Update workflow execution count and last executed time
            if status == "completed":
                cursor.execute(
                    """
                    UPDATE workflows
                    SET execution_count = execution_count + 1,
                        last_executed = ?
                    WHERE id = ?
                """,
                    (completed_at.isoformat() if completed_at else None, workflow_id),
                )

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Error logging execution: {e}")
            return False

        finally:
            conn.close()

    def get_execution_history(
        self, workflow_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for a workflow

        Args:
            workflow_name: Workflow name
            limit: Maximum number of results

        Returns:
            List of execution records
        """
        # First get workflow ID
        workflow = self.get(workflow_name)
        if not workflow:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, parameters, status, started_at, completed_at, result, error
                FROM workflow_executions
                WHERE workflow_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """,
                (workflow.id, limit),
            )

            rows = cursor.fetchall()
            executions = []

            for row in rows:
                executions.append(
                    {
                        "id": row[0],
                        "parameters": json.loads(row[1]) if row[1] else {},
                        "status": row[2],
                        "started_at": row[3],
                        "completed_at": row[4],
                        "result": json.loads(row[5]) if row[5] else None,
                        "error": row[6],
                    }
                )

            return executions

        finally:
            conn.close()
