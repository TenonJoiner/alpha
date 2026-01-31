"""
Alpha - Pattern Learner

Learns from user behavior patterns and preferences.
Analyzes conversation history to detect:
- Recurring user requests (daily/weekly/monthly patterns)
- User preferences and communication style
- Task execution patterns
- Temporal patterns (time-of-day, day-of-week)
"""

import asyncio
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents a detected pattern."""
    pattern_id: str
    pattern_type: str  # "recurring_request", "preference", "temporal", "task_execution"
    description: str
    frequency: int
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    metadata: Dict[str, Any]
    examples: List[str]


@dataclass
class UserPreference:
    """Represents a learned user preference."""
    preference_id: str
    category: str  # "communication", "timing", "tool_usage", "response_style"
    key: str
    value: Any
    confidence: float
    learned_from: int  # number of observations
    last_updated: datetime


@dataclass
class TemporalPattern:
    """Represents a time-based pattern."""
    pattern_id: str
    task_type: str
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None
    frequency: int = 0
    confidence: float = 0.0


class PatternLearner:
    """
    Learn patterns from user behavior and conversation history.

    Features:
    - Analyze conversation history
    - Detect recurring requests
    - Learn user preferences
    - Identify temporal patterns
    - Track task execution patterns
    - Store learned patterns in database
    """

    def __init__(
        self,
        database_path: str,
        min_pattern_frequency: int = 3,
        min_confidence: float = 0.6
    ):
        """
        Initialize pattern learner.

        Args:
            database_path: Path to pattern database
            min_pattern_frequency: Minimum frequency to consider a pattern
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.database_path = Path(database_path)
        self.min_pattern_frequency = min_pattern_frequency
        self.min_confidence = min_confidence
        self.conn: Optional[sqlite3.Connection] = None

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
        logger.info(f"Pattern learner initialized: {self.database_path}")

    async def _create_tables(self):
        """Create database tables for pattern storage."""
        cursor = self.conn.cursor()

        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                confidence REAL NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                metadata TEXT,
                examples TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL NOT NULL,
                learned_from INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)

        # Temporal patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_patterns (
                pattern_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                day_of_month INTEGER,
                frequency INTEGER NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Request history for pattern detection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_hash TEXT NOT NULL,
                request_text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                hour INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                metadata TEXT
            )
        """)

        self.conn.commit()

    async def analyze_conversation_history(
        self,
        conversations: List[Dict[str, Any]],
        lookback_days: int = 30
    ) -> Dict[str, List[Pattern]]:
        """
        Analyze conversation history to detect patterns.

        Args:
            conversations: List of conversation messages
            lookback_days: How many days to analyze

        Returns:
            Dictionary of detected patterns by type
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Filter user messages within lookback period
        user_messages = [
            msg for msg in conversations
            if msg['role'] == 'user' and
            datetime.fromisoformat(msg['timestamp']) >= cutoff_date
        ]

        patterns = {
            'recurring_request': [],
            'temporal': [],
            'communication_style': []
        }

        # Detect recurring requests
        recurring = await self._detect_recurring_requests(user_messages)
        patterns['recurring_request'] = recurring

        # Detect temporal patterns
        temporal = await self._detect_temporal_patterns(user_messages)
        patterns['temporal'] = temporal

        # Detect communication style preferences
        style = await self._detect_communication_style(user_messages)
        patterns['communication_style'] = style

        return patterns

    async def _detect_recurring_requests(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """Detect recurring user requests."""
        patterns = []

        # Extract and normalize request texts
        requests = []
        for msg in messages:
            content = msg['content'].lower().strip()
            timestamp = datetime.fromisoformat(msg['timestamp'])

            # Simple normalization (can be enhanced with NLP)
            normalized = self._normalize_request(content)
            requests.append({
                'text': content,
                'normalized': normalized,
                'timestamp': timestamp
            })

        # Count normalized requests
        request_counts = Counter(r['normalized'] for r in requests)

        # Identify patterns
        for normalized_text, count in request_counts.items():
            if count >= self.min_pattern_frequency:
                # Find examples
                examples = [
                    r['text'] for r in requests
                    if r['normalized'] == normalized_text
                ][:5]

                # Calculate confidence based on frequency
                confidence = min(count / 10.0, 1.0)

                if confidence >= self.min_confidence:
                    # Get timestamps
                    timestamps = [
                        r['timestamp'] for r in requests
                        if r['normalized'] == normalized_text
                    ]

                    pattern = Pattern(
                        pattern_id=f"rec_{hash(normalized_text) & 0x7FFFFFFF}",
                        pattern_type="recurring_request",
                        description=f"User frequently requests: {normalized_text}",
                        frequency=count,
                        confidence=confidence,
                        first_seen=min(timestamps),
                        last_seen=max(timestamps),
                        metadata={'normalized_text': normalized_text},
                        examples=examples
                    )
                    patterns.append(pattern)

                    # Store in database
                    await self._store_pattern(pattern)

        return patterns

    async def _detect_temporal_patterns(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """Detect time-based patterns in user requests."""
        patterns = []

        # Group requests by hour and day of week
        hour_counts = defaultdict(list)
        day_counts = defaultdict(list)

        for msg in messages:
            timestamp = datetime.fromisoformat(msg['timestamp'])
            content = msg['content']

            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            hour_counts[hour].append(content)
            day_counts[day_of_week].append(content)

        # Detect hour-of-day patterns
        for hour, requests in hour_counts.items():
            if len(requests) >= self.min_pattern_frequency:
                confidence = min(len(requests) / 10.0, 1.0)

                if confidence >= self.min_confidence:
                    pattern = Pattern(
                        pattern_id=f"temp_hour_{hour}",
                        pattern_type="temporal",
                        description=f"User is typically active at {hour:02d}:00",
                        frequency=len(requests),
                        confidence=confidence,
                        first_seen=datetime.now() - timedelta(days=30),
                        last_seen=datetime.now(),
                        metadata={'hour': hour, 'type': 'hour_of_day'},
                        examples=requests[:5]
                    )
                    patterns.append(pattern)

        # Detect day-of-week patterns
        for day, requests in day_counts.items():
            if len(requests) >= self.min_pattern_frequency:
                confidence = min(len(requests) / 15.0, 1.0)

                if confidence >= self.min_confidence:
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                                'Friday', 'Saturday', 'Sunday']
                    pattern = Pattern(
                        pattern_id=f"temp_day_{day}",
                        pattern_type="temporal",
                        description=f"User is typically active on {day_names[day]}",
                        frequency=len(requests),
                        confidence=confidence,
                        first_seen=datetime.now() - timedelta(days=30),
                        last_seen=datetime.now(),
                        metadata={'day_of_week': day, 'type': 'day_of_week'},
                        examples=requests[:5]
                    )
                    patterns.append(pattern)

        return patterns

    async def _detect_communication_style(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """Detect user communication style preferences."""
        patterns = []

        if not messages:
            return patterns

        # Analyze message lengths
        lengths = [len(msg['content']) for msg in messages]
        avg_length = sum(lengths) / len(lengths)

        # Detect verbosity preference
        if avg_length < 50:
            style = "concise"
            description = "User prefers brief, concise messages"
        elif avg_length > 200:
            style = "detailed"
            description = "User provides detailed, verbose messages"
        else:
            style = "moderate"
            description = "User uses moderate-length messages"

        pattern = Pattern(
            pattern_id="style_verbosity",
            pattern_type="communication_style",
            description=description,
            frequency=len(messages),
            confidence=0.8,
            first_seen=datetime.fromisoformat(messages[-1]['timestamp']),
            last_seen=datetime.fromisoformat(messages[0]['timestamp']),
            metadata={'style': style, 'avg_length': avg_length},
            examples=[msg['content'][:100] for msg in messages[:3]]
        )
        patterns.append(pattern)

        return patterns

    def _normalize_request(self, text: str) -> str:
        """Normalize request text for pattern matching."""
        # Simple normalization - can be enhanced with NLP
        # Remove common variations
        text = text.lower().strip()

        # Remove punctuation
        import string
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Extract key words (simple approach)
        words = text.split()

        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'can', 'could',
                     'please', 'would', 'will', 'i', 'me', 'my', 'you', 'your'}
        keywords = [w for w in words if w not in stop_words]

        # Return normalized form
        return ' '.join(keywords[:5])  # First 5 keywords

    async def _store_pattern(self, pattern: Pattern):
        """Store detected pattern in database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO patterns
            (pattern_id, pattern_type, description, frequency, confidence,
             first_seen, last_seen, metadata, examples, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.description,
                pattern.frequency,
                pattern.confidence,
                pattern.first_seen.isoformat(),
                pattern.last_seen.isoformat(),
                json.dumps(pattern.metadata),
                json.dumps(pattern.examples),
                datetime.now().isoformat()
            )
        )
        self.conn.commit()

    async def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[Pattern]:
        """
        Retrieve stored patterns.

        Args:
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold

        Returns:
            List of patterns
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM patterns WHERE 1=1"
        params = []

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        if min_confidence:
            query += " AND confidence >= ?"
            params.append(min_confidence)

        query += " ORDER BY confidence DESC, frequency DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        patterns = []
        for row in rows:
            pattern = Pattern(
                pattern_id=row['pattern_id'],
                pattern_type=row['pattern_type'],
                description=row['description'],
                frequency=row['frequency'],
                confidence=row['confidence'],
                first_seen=datetime.fromisoformat(row['first_seen']),
                last_seen=datetime.fromisoformat(row['last_seen']),
                metadata=json.loads(row['metadata']),
                examples=json.loads(row['examples'])
            )
            patterns.append(pattern)

        return patterns

    async def learn_preference(
        self,
        category: str,
        key: str,
        value: Any,
        confidence: float = 0.8
    ):
        """
        Store a learned user preference.

        Args:
            category: Preference category
            key: Preference key
            value: Preference value
            confidence: Confidence level
        """
        cursor = self.conn.cursor()

        preference_id = f"{category}_{key}"

        # Check if preference exists
        cursor.execute(
            "SELECT learned_from FROM user_preferences WHERE preference_id = ?",
            (preference_id,)
        )
        row = cursor.fetchone()

        learned_from = 1
        if row:
            learned_from = row['learned_from'] + 1
            confidence = min(confidence + 0.1, 1.0)

        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences
            (preference_id, category, key, value, confidence, learned_from, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preference_id,
                category,
                key,
                json.dumps(value),
                confidence,
                learned_from,
                datetime.now().isoformat()
            )
        )
        self.conn.commit()

    async def get_preferences(
        self,
        category: Optional[str] = None
    ) -> List[UserPreference]:
        """
        Get learned user preferences.

        Args:
            category: Filter by category

        Returns:
            List of user preferences
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM user_preferences WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY confidence DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        preferences = []
        for row in rows:
            pref = UserPreference(
                preference_id=row['preference_id'],
                category=row['category'],
                key=row['key'],
                value=json.loads(row['value']),
                confidence=row['confidence'],
                learned_from=row['learned_from'],
                last_updated=datetime.fromisoformat(row['last_updated'])
            )
            preferences.append(pref)

        return preferences

    async def get_statistics(self) -> Dict[str, Any]:
        """Get pattern learning statistics."""
        cursor = self.conn.cursor()

        stats = {}

        # Count patterns by type
        cursor.execute(
            "SELECT pattern_type, COUNT(*) as count FROM patterns GROUP BY pattern_type"
        )
        stats['patterns_by_type'] = {row['pattern_type']: row['count']
                                    for row in cursor.fetchall()}

        # Count preferences by category
        cursor.execute(
            "SELECT category, COUNT(*) as count FROM user_preferences GROUP BY category"
        )
        stats['preferences_by_category'] = {row['category']: row['count']
                                           for row in cursor.fetchall()}

        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM patterns")
        stats['total_patterns'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM user_preferences")
        stats['total_preferences'] = cursor.fetchone()['count']

        return stats

    async def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Pattern learner closed")
