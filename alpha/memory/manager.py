"""
Alpha - Memory Manager

Persistent storage for conversations, tasks, and knowledge.
Enhanced with vector memory capabilities for semantic search.
"""

import asyncio
import logging
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages persistent storage using SQLite and vector memory.

    Features:
    - Conversation history (SQLite + Vector)
    - Task execution logs
    - System events
    - Knowledge base (SQLite + Vector with semantic search)
    - User preferences (long-term memory)
    - Context-aware retrieval
    """

    def __init__(
        self,
        database_path: str,
        vector_config: Optional[Dict] = None
    ):
        self.database_path = Path(database_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.vector_config = vector_config or {}

        # Vector memory components (initialized later)
        self.vector_store = None
        self.embedding_service = None
        self.knowledge_base = None
        self.context_retriever = None
        self.vector_enabled = False

    async def initialize(self):
        """Initialize database and create tables."""
        # Create database directory if needed
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.conn = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row

        # Create tables
        await self._create_tables()
        logger.info(f"Memory system initialized: {self.database_path}")

        # Initialize vector memory if configured
        await self._initialize_vector_memory()

    async def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority INTEGER,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                metadata TEXT
            )
        """)

        # System events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # Knowledge base table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.conn.commit()

    async def _initialize_vector_memory(self):
        """Initialize vector memory components."""
        if not self.vector_config.get('enabled', False):
            logger.info("Vector memory disabled in config")
            return

        try:
            from alpha.vector_memory import (
                VectorStore,
                EmbeddingService,
                KnowledgeBase,
                ContextRetriever,
            )
            from alpha.vector_memory.embeddings import ChromaEmbeddingFunction

            # Get configuration
            vector_db_path = self.vector_config.get(
                'path',
                str(self.database_path.parent / 'vectors')
            )
            embedding_provider = self.vector_config.get(
                'embedding_provider',
                'openai'
            )
            embedding_model = self.vector_config.get('embedding_model')
            max_context_tokens = self.vector_config.get(
                'max_context_tokens',
                4000
            )

            # Initialize embedding service
            self.embedding_service = EmbeddingService(
                provider=embedding_provider,
                model=embedding_model
            )

            # Create ChromaDB-compatible embedding function
            embedding_function = ChromaEmbeddingFunction(
                self.embedding_service
            )

            # Initialize vector store
            self.vector_store = VectorStore(
                persist_directory=vector_db_path,
                embedding_function=embedding_function
            )

            # Initialize knowledge base
            self.knowledge_base = KnowledgeBase(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service
            )

            # Initialize context retriever
            self.context_retriever = ContextRetriever(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                max_context_tokens=max_context_tokens
            )

            self.vector_enabled = True
            logger.info("Vector memory initialized successfully")

        except ImportError as e:
            logger.warning(f"Vector memory dependencies not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")

    async def add_conversation(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a conversation message.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (
                role,
                content,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            )
        )
        self.conn.commit()

        # Also add to vector memory if enabled
        if self.vector_enabled and self.context_retriever:
            try:
                self.context_retriever.add_conversation(
                    role=role,
                    content=content,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to add conversation to vector memory: {e}")

    async def get_conversation_history(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get conversation history.

        Args:
            limit: Maximum number of messages
            offset: Offset for pagination

        Returns:
            List of conversation messages
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM conversations
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def save_task(self, task):
        """Save or update a task."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO tasks
            (id, name, description, status, priority, created_at, started_at,
             completed_at, result, error, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.name,
                task.description,
                task.status.value,
                task.priority.value,
                task.created_at.isoformat(),
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                json.dumps(task.result) if task.result else None,
                task.error,
                json.dumps(task.metadata) if task.metadata else None
            )
        )
        self.conn.commit()

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get tasks with optional status filter."""
        cursor = self.conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT * FROM tasks WHERE status = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (status, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def add_system_event(self, event_type: str, data: Dict):
        """Add a system event."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_events (event_type, data, timestamp)
            VALUES (?, ?, ?)
            """,
            (
                event_type,
                json.dumps(data),
                datetime.now().isoformat()
            )
        )
        self.conn.commit()

    async def get_system_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get system events."""
        cursor = self.conn.cursor()

        if event_type:
            cursor.execute(
                """
                SELECT * FROM system_events WHERE event_type = ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (event_type, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def set_knowledge(self, key: str, value: Any, category: str = "general"):
        """Store knowledge."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge (key, value, category, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE((SELECT created_at FROM knowledge WHERE key = ?), ?), ?)
            """,
            (key, json.dumps(value), category, key, now, now)
        )
        self.conn.commit()

    async def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM knowledge WHERE key = ?", (key,))
        row = cursor.fetchone()

        if row:
            return json.loads(row['value'])
        return None

    async def search_knowledge(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search knowledge base."""
        cursor = self.conn.cursor()

        if category:
            cursor.execute(
                """
                SELECT * FROM knowledge WHERE category = ?
                ORDER BY updated_at DESC LIMIT ?
                """,
                (category, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM knowledge ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def retrieve_relevant_context(
        self,
        query: str,
        include_conversations: bool = True,
        include_knowledge: bool = True
    ) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            query: Search query
            include_conversations: Include relevant conversations
            include_knowledge: Include relevant knowledge

        Returns:
            Formatted context string
        """
        if not self.vector_enabled or not self.context_retriever:
            return ""

        try:
            context = self.context_retriever.build_context(
                query=query,
                include_conversations=include_conversations,
                include_knowledge=include_knowledge,
                knowledge_base=self.knowledge_base
            )
            return context
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return ""

    async def get_stats(self) -> Dict:
        """Get memory statistics."""
        cursor = self.conn.cursor()

        stats = {}

        # Count conversations
        cursor.execute("SELECT COUNT(*) as count FROM conversations")
        stats['conversations'] = cursor.fetchone()['count']

        # Count tasks
        cursor.execute("SELECT COUNT(*) as count FROM tasks")
        stats['tasks'] = cursor.fetchone()['count']

        # Count system events
        cursor.execute("SELECT COUNT(*) as count FROM system_events")
        stats['system_events'] = cursor.fetchone()['count']

        # Count knowledge items
        cursor.execute("SELECT COUNT(*) as count FROM knowledge")
        stats['knowledge'] = cursor.fetchone()['count']

        # Add vector memory stats if enabled
        if self.vector_enabled:
            try:
                if self.vector_store:
                    stats['vector_store'] = self.vector_store.get_stats()
                if self.knowledge_base:
                    stats['knowledge_base_vector'] = self.knowledge_base.get_stats()
                if self.context_retriever:
                    stats['context_retriever'] = self.context_retriever.get_stats()
            except Exception as e:
                logger.warning(f"Failed to get vector memory stats: {e}")

        return stats

    async def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Memory system closed")
