"""
Image Memory Module

Stores and manages image analysis history for deduplication and context retrieval.
"""

import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ImageRecord:
    """
    Image metadata and analysis record.

    Attributes:
        id: Unique record ID
        file_path: Local file path (if applicable)
        url: Image URL (if from web)
        hash: Content hash for deduplication
        format: Image format (PNG, JPEG, etc.)
        size_bytes: File size in bytes
        width: Image width in pixels
        height: Image height in pixels
        analyzed_at: Timestamp when analyzed
        analysis_result: JSON analysis result
        conversation_id: Associated conversation ID
    """
    id: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    hash: str = ""
    format: str = ""
    size_bytes: int = 0
    width: int = 0
    height: int = 0
    analyzed_at: str = ""
    analysis_result: str = "{}"  # JSON string
    conversation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ImageRecord":
        """Create from dictionary"""
        return cls(**data)


class ImageMemory:
    """
    Image memory and history storage.

    Features:
    - SQLite storage for image metadata
    - Content hash deduplication
    - Analysis result caching
    - Image history tracking
    - Conversation context
    """

    def __init__(self, db_path: str = "data/image_memory.db"):
        """
        Initialize ImageMemory.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Create image_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_history (
                id TEXT PRIMARY KEY,
                file_path TEXT,
                url TEXT,
                hash TEXT UNIQUE,
                format TEXT,
                size_bytes INTEGER,
                width INTEGER,
                height INTEGER,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analysis_result TEXT,
                conversation_id TEXT
            )
        """)

        # Create indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_hash
            ON image_history(hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_conversation
            ON image_history(conversation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_analyzed_at
            ON image_history(analyzed_at DESC)
        """)

        self.conn.commit()

        logger.info(f"ImageMemory initialized at {self.db_path}")

    def calculate_content_hash(self, image_data: bytes) -> str:
        """
        Calculate SHA256 hash of image content.

        Args:
            image_data: Image binary data

        Returns:
            Hex digest of content hash
        """
        return hashlib.sha256(image_data).hexdigest()

    def store_image(
        self,
        image_id: str,
        image_hash: str,
        metadata: Dict[str, Any],
        analysis_result: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        Store image metadata and analysis result.

        Args:
            image_id: Unique image ID
            image_hash: Content hash
            metadata: Image metadata (format, size, dimensions, etc.)
            analysis_result: Analysis result dictionary
            conversation_id: Associated conversation ID

        Returns:
            True if stored successfully, False if duplicate
        """
        # Check if already exists
        if self.get_by_hash(image_hash):
            logger.debug(f"Image with hash {image_hash} already exists")
            return False

        cursor = self.conn.cursor()

        # Prepare analysis result JSON
        analysis_json = json.dumps(analysis_result) if analysis_result else "{}"

        cursor.execute("""
            INSERT INTO image_history (
                id, file_path, url, hash, format,
                size_bytes, width, height,
                analysis_result, conversation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            image_id,
            metadata.get("file_path"),
            metadata.get("url"),
            image_hash,
            metadata.get("format", ""),
            metadata.get("size_bytes", 0),
            metadata.get("width", 0),
            metadata.get("height", 0),
            analysis_json,
            conversation_id
        ))

        self.conn.commit()

        logger.info(f"Stored image {image_id} with hash {image_hash[:8]}...")
        return True

    def get_by_hash(self, image_hash: str) -> Optional[ImageRecord]:
        """
        Get image record by content hash.

        Args:
            image_hash: Content hash to lookup

        Returns:
            ImageRecord if found, None otherwise
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM image_history
            WHERE hash = ?
        """, (image_hash,))

        row = cursor.fetchone()

        if row:
            return ImageRecord(**dict(row))

        return None

    def get_by_id(self, image_id: str) -> Optional[ImageRecord]:
        """
        Get image record by ID.

        Args:
            image_id: Image ID to lookup

        Returns:
            ImageRecord if found, None otherwise
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM image_history
            WHERE id = ?
        """, (image_id,))

        row = cursor.fetchone()

        if row:
            return ImageRecord(**dict(row))

        return None

    def get_recent(self, limit: int = 10, conversation_id: Optional[str] = None) -> List[ImageRecord]:
        """
        Get recent image records.

        Args:
            limit: Maximum number of records to return
            conversation_id: Filter by conversation ID

        Returns:
            List of ImageRecord objects
        """
        cursor = self.conn.cursor()

        if conversation_id:
            cursor.execute("""
                SELECT * FROM image_history
                WHERE conversation_id = ?
                ORDER BY analyzed_at DESC
                LIMIT ?
            """, (conversation_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM image_history
                ORDER BY analyzed_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()

        return [ImageRecord(**dict(row)) for row in rows]

    def search_by_format(self, format: str, limit: int = 10) -> List[ImageRecord]:
        """
        Search images by format.

        Args:
            format: Image format (PNG, JPEG, etc.)
            limit: Maximum number of results

        Returns:
            List of matching ImageRecord objects
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM image_history
            WHERE format = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (format.upper(), limit))

        rows = cursor.fetchall()

        return [ImageRecord(**dict(row)) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get image memory statistics.

        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()

        # Total images
        cursor.execute("SELECT COUNT(*) FROM image_history")
        total = cursor.fetchone()[0]

        # Format distribution
        cursor.execute("""
            SELECT format, COUNT(*) as count
            FROM image_history
            GROUP BY format
            ORDER BY count DESC
        """)
        formats = {row[0]: row[1] for row in cursor.fetchall()}

        # Total size
        cursor.execute("SELECT SUM(size_bytes) FROM image_history")
        total_size = cursor.fetchone()[0] or 0

        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM image_history
            WHERE analyzed_at >= datetime('now', '-7 days')
        """)
        recent_count = cursor.fetchone()[0]

        return {
            "total_images": total,
            "formats": formats,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "recent_7_days": recent_count
        }

    def clear_old_records(self, days: int = 30) -> int:
        """
        Clear records older than specified days.

        Args:
            days: Number of days to retain

        Returns:
            Number of records deleted
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            DELETE FROM image_history
            WHERE analyzed_at < datetime('now', ? || ' days')
        """, (f'-{days}',))

        deleted_count = cursor.rowcount
        self.conn.commit()

        logger.info(f"Cleared {deleted_count} old image records (>{days} days)")
        return deleted_count

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("ImageMemory connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
