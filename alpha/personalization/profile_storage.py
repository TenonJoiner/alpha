"""
Profile Storage - SQLite persistence for user profiles

Manages:
- User profile storage and retrieval
- Preference history tracking
- Interaction pattern persistence
- Database schema creation and migrations
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .user_profile import UserProfile, PreferenceHistory, InteractionPattern


logger = logging.getLogger(__name__)


class ProfileStorage:
    """
    SQLite-based storage for user profiles and personalization data

    Features:
    - Local-only storage (privacy-preserving)
    - Automatic schema creation
    - Transaction support
    - Query optimization with indexes
    """

    def __init__(self, db_path: str = "data/alpha.db"):
        """
        Initialize profile storage

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()

    def _ensure_database_exists(self) -> None:
        """Ensure database file and directory exist"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self) -> None:
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        try:
            # User profile table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id TEXT PRIMARY KEY DEFAULT 'default',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    -- Communication Preferences
                    verbosity_level TEXT DEFAULT 'balanced',
                    technical_level TEXT DEFAULT 'intermediate',
                    language_preference TEXT DEFAULT 'en',
                    tone_preference TEXT DEFAULT 'professional',

                    -- Behavioral Patterns
                    active_hours_start INTEGER DEFAULT 9,
                    active_hours_end INTEGER DEFAULT 18,
                    timezone TEXT DEFAULT 'UTC',

                    -- Task Preferences (JSON)
                    preferred_tools TEXT DEFAULT '[]',
                    frequent_tasks TEXT DEFAULT '[]',
                    workflow_patterns TEXT DEFAULT '{}',

                    -- Learning Metadata
                    interaction_count INTEGER DEFAULT 0,
                    confidence_score REAL DEFAULT 0.0,
                    last_learned_at TEXT
                )
            """)

            # Preference history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preference_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT NOT NULL,
                    preference_type TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    confidence REAL DEFAULT 0.0,
                    learned_at TEXT NOT NULL,
                    FOREIGN KEY (profile_id) REFERENCES user_profile(id)
                )
            """)

            # Interaction patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    FOREIGN KEY (profile_id) REFERENCES user_profile(id)
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_preference_history_profile
                ON preference_history(profile_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_preference_history_type
                ON preference_history(preference_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_patterns_profile
                ON interaction_patterns(profile_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_patterns_type
                ON interaction_patterns(pattern_type)
            """)

            conn.commit()
            logger.info("Profile storage tables created successfully")

        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    # ==================== UserProfile Operations ====================

    def save_profile(self, profile: UserProfile) -> None:
        """
        Save or update user profile

        Args:
            profile: UserProfile to save
        """
        conn = self._get_connection()
        try:
            data = profile.to_dict()

            # Check if profile exists
            existing = conn.execute(
                "SELECT id FROM user_profile WHERE id = ?",
                (profile.id,)
            ).fetchone()

            if existing:
                # Update existing profile
                conn.execute("""
                    UPDATE user_profile SET
                        updated_at = ?,
                        verbosity_level = ?,
                        technical_level = ?,
                        language_preference = ?,
                        tone_preference = ?,
                        active_hours_start = ?,
                        active_hours_end = ?,
                        timezone = ?,
                        preferred_tools = ?,
                        frequent_tasks = ?,
                        workflow_patterns = ?,
                        interaction_count = ?,
                        confidence_score = ?,
                        last_learned_at = ?
                    WHERE id = ?
                """, (
                    data["updated_at"],
                    data["verbosity_level"],
                    data["technical_level"],
                    data["language_preference"],
                    data["tone_preference"],
                    data["active_hours_start"],
                    data["active_hours_end"],
                    data["timezone"],
                    data["preferred_tools"],
                    data["frequent_tasks"],
                    data["workflow_patterns"],
                    data["interaction_count"],
                    data["confidence_score"],
                    data["last_learned_at"],
                    profile.id
                ))
            else:
                # Insert new profile
                conn.execute("""
                    INSERT INTO user_profile (
                        id, created_at, updated_at,
                        verbosity_level, technical_level,
                        language_preference, tone_preference,
                        active_hours_start, active_hours_end, timezone,
                        preferred_tools, frequent_tasks, workflow_patterns,
                        interaction_count, confidence_score, last_learned_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["id"],
                    data["created_at"],
                    data["updated_at"],
                    data["verbosity_level"],
                    data["technical_level"],
                    data["language_preference"],
                    data["tone_preference"],
                    data["active_hours_start"],
                    data["active_hours_end"],
                    data["timezone"],
                    data["preferred_tools"],
                    data["frequent_tasks"],
                    data["workflow_patterns"],
                    data["interaction_count"],
                    data["confidence_score"],
                    data["last_learned_at"]
                ))

            conn.commit()
            logger.debug(f"Profile {profile.id} saved successfully")

        except sqlite3.Error as e:
            logger.error(f"Error saving profile: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def load_profile(self, profile_id: str = "default") -> Optional[UserProfile]:
        """
        Load user profile by ID

        Args:
            profile_id: Profile ID to load

        Returns:
            UserProfile if found, None otherwise
        """
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM user_profile WHERE id = ?",
                (profile_id,)
            ).fetchone()

            if row:
                return UserProfile.from_dict(dict(row))
            return None

        except sqlite3.Error as e:
            logger.error(f"Error loading profile: {e}")
            return None
        finally:
            conn.close()

    def delete_profile(self, profile_id: str = "default") -> bool:
        """
        Delete user profile and all associated data

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False otherwise
        """
        conn = self._get_connection()
        try:
            # Delete preference history
            conn.execute(
                "DELETE FROM preference_history WHERE profile_id = ?",
                (profile_id,)
            )

            # Delete interaction patterns
            conn.execute(
                "DELETE FROM interaction_patterns WHERE profile_id = ?",
                (profile_id,)
            )

            # Delete profile
            cursor = conn.execute(
                "DELETE FROM user_profile WHERE id = ?",
                (profile_id,)
            )

            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Profile {profile_id} deleted successfully")
            return deleted

        except sqlite3.Error as e:
            logger.error(f"Error deleting profile: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ==================== PreferenceHistory Operations ====================

    def add_preference_history(self, history: PreferenceHistory) -> int:
        """
        Add preference change to history

        Args:
            history: PreferenceHistory to add

        Returns:
            ID of inserted history record
        """
        conn = self._get_connection()
        try:
            data = history.to_dict()
            cursor = conn.execute("""
                INSERT INTO preference_history (
                    profile_id, preference_type, old_value, new_value,
                    reason, confidence, learned_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["profile_id"],
                data["preference_type"],
                data["old_value"],
                data["new_value"],
                data["reason"],
                data["confidence"],
                data["learned_at"]
            ))

            conn.commit()
            history_id = cursor.lastrowid
            logger.debug(f"Preference history {history_id} added")
            return history_id

        except sqlite3.Error as e:
            logger.error(f"Error adding preference history: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_preference_history(
        self,
        profile_id: str = "default",
        preference_type: Optional[str] = None,
        limit: int = 100
    ) -> List[PreferenceHistory]:
        """
        Get preference change history

        Args:
            profile_id: Profile ID
            preference_type: Filter by preference type (optional)
            limit: Maximum number of records

        Returns:
            List of PreferenceHistory records
        """
        conn = self._get_connection()
        try:
            if preference_type:
                rows = conn.execute("""
                    SELECT * FROM preference_history
                    WHERE profile_id = ? AND preference_type = ?
                    ORDER BY learned_at DESC
                    LIMIT ?
                """, (profile_id, preference_type, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM preference_history
                    WHERE profile_id = ?
                    ORDER BY learned_at DESC
                    LIMIT ?
                """, (profile_id, limit)).fetchall()

            return [PreferenceHistory.from_dict(dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting preference history: {e}")
            return []
        finally:
            conn.close()

    # ==================== InteractionPattern Operations ====================

    def save_interaction_pattern(self, pattern: InteractionPattern) -> int:
        """
        Save or update interaction pattern

        Args:
            pattern: InteractionPattern to save

        Returns:
            ID of saved pattern
        """
        conn = self._get_connection()
        try:
            data = pattern.to_dict()

            if pattern.id:
                # Update existing pattern
                conn.execute("""
                    UPDATE interaction_patterns SET
                        pattern_data = ?,
                        occurrence_count = ?,
                        last_seen = ?
                    WHERE id = ?
                """, (
                    data["pattern_data"],
                    data["occurrence_count"],
                    data["last_seen"],
                    pattern.id
                ))
                pattern_id = pattern.id
            else:
                # Insert new pattern
                cursor = conn.execute("""
                    INSERT INTO interaction_patterns (
                        profile_id, pattern_type, pattern_data,
                        occurrence_count, first_seen, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data["profile_id"],
                    data["pattern_type"],
                    data["pattern_data"],
                    data["occurrence_count"],
                    data["first_seen"],
                    data["last_seen"]
                ))
                pattern_id = cursor.lastrowid

            conn.commit()
            logger.debug(f"Interaction pattern {pattern_id} saved")
            return pattern_id

        except sqlite3.Error as e:
            logger.error(f"Error saving interaction pattern: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_interaction_patterns(
        self,
        profile_id: str = "default",
        pattern_type: Optional[str] = None,
        min_occurrences: int = 1
    ) -> List[InteractionPattern]:
        """
        Get interaction patterns

        Args:
            profile_id: Profile ID
            pattern_type: Filter by pattern type (optional)
            min_occurrences: Minimum occurrence count

        Returns:
            List of InteractionPattern records
        """
        conn = self._get_connection()
        try:
            if pattern_type:
                rows = conn.execute("""
                    SELECT * FROM interaction_patterns
                    WHERE profile_id = ? AND pattern_type = ?
                    AND occurrence_count >= ?
                    ORDER BY occurrence_count DESC, last_seen DESC
                """, (profile_id, pattern_type, min_occurrences)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM interaction_patterns
                    WHERE profile_id = ? AND occurrence_count >= ?
                    ORDER BY occurrence_count DESC, last_seen DESC
                """, (profile_id, min_occurrences)).fetchall()

            return [InteractionPattern.from_dict(dict(row)) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting interaction patterns: {e}")
            return []
        finally:
            conn.close()

    def find_similar_pattern(
        self,
        profile_id: str,
        pattern_type: str,
        pattern_data: Dict[str, Any]
    ) -> Optional[InteractionPattern]:
        """
        Find existing pattern similar to given data

        Args:
            profile_id: Profile ID
            pattern_type: Pattern type
            pattern_data: Pattern data to match

        Returns:
            Matching InteractionPattern if found
        """
        patterns = self.get_interaction_patterns(profile_id, pattern_type)

        # Simple exact match on pattern_data
        # TODO: Implement smarter similarity matching
        import json
        target_json = json.dumps(pattern_data, sort_keys=True)

        for pattern in patterns:
            pattern_json = json.dumps(pattern.pattern_data, sort_keys=True)
            if pattern_json == target_json:
                return pattern

        return None

    # ==================== Utility Operations ====================

    def get_profile_stats(self, profile_id: str = "default") -> Dict[str, Any]:
        """
        Get statistics about user profile

        Args:
            profile_id: Profile ID

        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        try:
            profile = self.load_profile(profile_id)
            if not profile:
                return {}

            preference_count = conn.execute(
                "SELECT COUNT(*) as count FROM preference_history WHERE profile_id = ?",
                (profile_id,)
            ).fetchone()["count"]

            pattern_count = conn.execute(
                "SELECT COUNT(*) as count FROM interaction_patterns WHERE profile_id = ?",
                (profile_id,)
            ).fetchone()["count"]

            return {
                "profile_id": profile_id,
                "interaction_count": profile.interaction_count,
                "confidence_score": profile.confidence_score,
                "preference_changes": preference_count,
                "detected_patterns": pattern_count,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            }

        except sqlite3.Error as e:
            logger.error(f"Error getting profile stats: {e}")
            return {}
        finally:
            conn.close()
