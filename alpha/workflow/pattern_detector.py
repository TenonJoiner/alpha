"""
Alpha - Workflow Pattern Detector

Detects recurring task sequences from execution history that are worthy of workflow automation.

Features:
- Analyze task execution history
- Detect recurring task sequences
- Normalize task descriptions for pattern matching
- Calculate pattern confidence scores
- Filter patterns by frequency and temporal proximity
"""

import re
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPattern:
    """Detected workflow pattern from task history."""
    pattern_id: str
    task_sequence: List[str]  # Normalized task descriptions
    frequency: int  # Number of times this sequence occurred
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    avg_interval: timedelta  # Average time between occurrences
    task_ids: List[str]  # Original task IDs for tracing
    suggested_workflow_name: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['first_seen'] = self.first_seen.isoformat()
        result['last_seen'] = self.last_seen.isoformat()
        result['avg_interval'] = self.avg_interval.total_seconds()
        return result


class WorkflowPatternDetector:
    """
    Analyzes task execution history to detect workflow-worthy patterns.

    Detection Algorithm:
    1. Fetch recent task executions (configurable lookback)
    2. Normalize task descriptions (remove dates, specific values)
    3. Find recurring sequences using sliding window
    4. Filter by frequency threshold (≥3 occurrences)
    5. Filter by temporal proximity (within configurable days)
    6. Calculate confidence score based on multiple factors
    7. Generate suggested workflow names
    """

    def __init__(
        self,
        database_path: str,
        min_frequency: int = 3,
        min_sequence_length: int = 2,
        max_interval_days: int = 7,
        min_confidence: float = 0.7
    ):
        """
        Initialize pattern detector.

        Args:
            database_path: Path to Alpha's database
            min_frequency: Minimum occurrences to consider a pattern
            min_sequence_length: Minimum number of tasks in a sequence
            max_interval_days: Maximum days between pattern occurrences
            min_confidence: Minimum confidence to return pattern
        """
        self.db_path = database_path
        self.min_frequency = min_frequency
        self.min_sequence_length = min_sequence_length
        self.max_interval_days = max_interval_days
        self.min_confidence = min_confidence

        # Ensure database directory exists (only if path is writable)
        try:
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # Database path not writable - will handle errors during queries
            pass

    def detect_workflow_patterns(
        self,
        lookback_days: int = 30
    ) -> List[WorkflowPattern]:
        """
        Detect workflow patterns from task execution history.

        Args:
            lookback_days: Number of days to look back in history

        Returns:
            List of detected patterns sorted by (confidence DESC, frequency DESC)
        """
        logger.info(f"Detecting workflow patterns from last {lookback_days} days")

        # Fetch task history
        tasks = self._fetch_task_history(lookback_days)
        if len(tasks) < self.min_sequence_length:
            logger.info("Insufficient task history for pattern detection")
            return []

        logger.info(f"Analyzing {len(tasks)} tasks for patterns")

        # Normalize task descriptions
        normalized_tasks = []
        for task in tasks:
            normalized = self.normalize_task_description(task['description'])
            normalized_tasks.append({
                **task,
                'normalized_description': normalized
            })

        # Find recurring sequences
        patterns = self._find_recurring_sequences(normalized_tasks)

        # Filter and score patterns
        filtered_patterns = []
        for pattern in patterns:
            confidence = self.calculate_pattern_confidence(pattern, normalized_tasks)
            pattern.confidence = confidence

            if (pattern.frequency >= self.min_frequency and
                confidence >= self.min_confidence):
                filtered_patterns.append(pattern)

        # Sort by confidence (desc) then frequency (desc)
        filtered_patterns.sort(key=lambda p: (p.confidence, p.frequency), reverse=True)

        logger.info(f"Found {len(filtered_patterns)} high-confidence patterns")
        return filtered_patterns

    def normalize_task_description(self, description: str) -> str:
        """
        Normalize task description for pattern matching.

        Normalization rules:
        - Remove dates (YYYY-MM-DD, MM/DD/YYYY, etc.)
        - Remove times (HH:MM, HH:MM:SS)
        - Remove numbers (except semantic ones like "step 1")
        - Remove file paths (keep just filenames)
        - Convert to lowercase
        - Remove extra whitespace

        Examples:
            "Deploy to staging on 2026-01-15" → "deploy to staging"
            "Backup files at 23:45" → "backup files"
            "Pull branch feature/auth" → "pull branch"
            "Run tests on /path/to/file.py" → "run tests on file.py"
        """
        if not description:
            return ""

        text = description.lower()

        # Remove dates (various formats)
        text = re.sub(r'\d{4}-\d{2}-\d{2}', '', text)  # YYYY-MM-DD
        text = re.sub(r'\d{2}/\d{2}/\d{4}', '', text)  # MM/DD/YYYY
        text = re.sub(r'\d{2}-\d{2}-\d{4}', '', text)  # DD-MM-YYYY

        # Remove times
        text = re.sub(r'\d{2}:\d{2}(:\d{2})?', '', text)  # HH:MM or HH:MM:SS

        # Remove file paths (keep just filename)
        text = re.sub(r'[/\\][\w/\\.-]+[/\\](\w+\.\w+)', r'\1', text)

        # Remove most numbers (but keep semantic ones)
        text = re.sub(r'(?<!step )\b\d+\b', '', text)

        # Remove common time indicators
        text = re.sub(r'\b(on|at|in|every|daily|weekly|monthly)\s+\d+', '', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        # Remove common prepositions at start/end
        text = re.sub(r'^(on|at|in|from|to)\s+', '', text)
        text = re.sub(r'\s+(on|at|in|from|to)$', '', text)

        return text.strip()

    def _fetch_task_history(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Fetch task execution history from database.

        Returns tasks with: id, description, created_at, status, result
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch from task_manager table
            cursor.execute("""
                SELECT
                    id,
                    description,
                    created_at,
                    status,
                    result
                FROM task_manager
                WHERE created_at >= ?
                    AND status IN ('completed', 'running')
                ORDER BY created_at ASC
            """, (cutoff_date.isoformat(),))

            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row['id'],
                    'description': row['description'] or '',
                    'created_at': datetime.fromisoformat(row['created_at']),
                    'status': row['status'],
                    'result': row['result']
                })

            conn.close()
            return tasks

        except sqlite3.Error as e:
            logger.error(f"Database error fetching task history: {e}")
            return []

    def _find_recurring_sequences(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkflowPattern]:
        """
        Find recurring task sequences using time-based clustering.

        Algorithm:
        1. Group tasks into sessions based on time proximity (≤1 hour gap)
        2. Extract task sequences from each session
        3. Find recurring sequences across sessions
        4. Filter by frequency and temporal proximity
        """
        if len(tasks) < self.min_sequence_length:
            return []

        # Step 1: Cluster tasks into sessions (tasks ≤1 hour apart)
        sessions = self._cluster_tasks_into_sessions(tasks)
        logger.info(f"Clustered {len(tasks)} tasks into {len(sessions)} sessions")

        if len(sessions) < self.min_frequency:
            logger.info(f"Insufficient sessions ({len(sessions)}) for pattern detection")
            return []

        # Step 2: Extract sequences from each session
        session_sequences = []
        for session in sessions:
            if len(session['tasks']) >= self.min_sequence_length:
                normalized_seq = tuple(t['normalized_description'] for t in session['tasks'])
                session_sequences.append({
                    'sequence': normalized_seq,
                    'tasks': session['tasks'],
                    'timestamp': session['timestamp']
                })

        # Step 3: Group identical sequences
        sequence_groups = defaultdict(list)
        for seq_data in session_sequences:
            sequence_groups[seq_data['sequence']].append(seq_data)

        # Step 4: Convert to WorkflowPattern objects
        patterns = []
        pattern_id = 0

        for normalized_seq, occurrences in sequence_groups.items():
            if len(occurrences) < self.min_frequency:
                continue

            # Check temporal proximity
            timestamps = [occ['timestamp'] for occ in occurrences]
            if not self._check_temporal_proximity(timestamps):
                continue

            # Calculate average interval
            if len(timestamps) > 1:
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds()
                           for i in range(len(timestamps) - 1)]
                avg_interval = timedelta(seconds=sum(intervals) / len(intervals))
            else:
                avg_interval = timedelta(0)

            # Collect task IDs
            task_ids = []
            for occ in occurrences:
                task_ids.extend([t['id'] for t in occ['tasks']])

            # Generate suggested workflow name
            suggested_name = self._generate_workflow_name(list(normalized_seq))

            pattern = WorkflowPattern(
                pattern_id=f"pattern_{pattern_id}",
                task_sequence=list(normalized_seq),
                frequency=len(occurrences),
                confidence=0.0,  # Will be calculated later
                first_seen=min(timestamps),
                last_seen=max(timestamps),
                avg_interval=avg_interval,
                task_ids=task_ids,
                suggested_workflow_name=suggested_name,
                metadata={
                    'sequence_length': len(normalized_seq),
                    'timestamps': [ts.isoformat() for ts in timestamps],
                    'sessions': len(occurrences)
                }
            )

            patterns.append(pattern)
            pattern_id += 1

        logger.info(f"Found {len(patterns)} patterns before confidence filtering")
        return patterns

    def _cluster_tasks_into_sessions(
        self,
        tasks: List[Dict[str, Any]],
        max_gap_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Cluster tasks into sessions based on time proximity.

        Args:
            tasks: List of tasks sorted by created_at
            max_gap_minutes: Maximum gap between tasks in same session

        Returns:
            List of sessions, each with timestamp and list of tasks
        """
        if not tasks:
            return []

        sessions = []
        current_session = {
            'timestamp': tasks[0]['created_at'],
            'tasks': [tasks[0]]
        }

        for i in range(1, len(tasks)):
            gap = (tasks[i]['created_at'] - current_session['tasks'][-1]['created_at']).total_seconds() / 60

            if gap <= max_gap_minutes:
                # Same session
                current_session['tasks'].append(tasks[i])
            else:
                # New session
                if len(current_session['tasks']) >= self.min_sequence_length:
                    sessions.append(current_session)

                current_session = {
                    'timestamp': tasks[i]['created_at'],
                    'tasks': [tasks[i]]
                }

        # Add last session
        if len(current_session['tasks']) >= self.min_sequence_length:
            sessions.append(current_session)

        return sessions

    def _check_temporal_proximity(self, timestamps: List[datetime]) -> bool:
        """
        Check if pattern occurrences are temporally close enough.

        Returns True if at least 2 occurrences are within max_interval_days.
        """
        if len(timestamps) < 2:
            return False

        max_interval = timedelta(days=self.max_interval_days)

        for i in range(len(timestamps) - 1):
            if (timestamps[i + 1] - timestamps[i]) <= max_interval:
                return True

        return False

    def calculate_pattern_confidence(
        self,
        pattern: WorkflowPattern,
        all_tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for a pattern.

        Confidence factors:
        1. Frequency: More occurrences = higher confidence (30%)
        2. Regularity: Consistent intervals = higher confidence (25%)
        3. Sequence length: Longer sequences = more specific = higher confidence (20%)
        4. Task success rate: Higher success = higher confidence (15%)
        5. Recency: Recent patterns = higher confidence (10%)

        Returns: Confidence score 0.0 to 1.0
        """
        scores = []

        # 1. Frequency score (0-1, normalized by max reasonable frequency = 20)
        frequency_score = min(pattern.frequency / 20.0, 1.0)
        scores.append(frequency_score * 0.30)

        # 2. Regularity score (coefficient of variation of intervals)
        timestamps = [datetime.fromisoformat(ts) for ts in pattern.metadata['timestamps']]
        if len(timestamps) > 2:
            intervals = [(timestamps[i+1] - timestamps[i]).total_seconds()
                        for i in range(len(timestamps) - 1)]
            mean_interval = sum(intervals) / len(intervals)
            std_interval = (sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5

            # Lower coefficient of variation = more regular = higher score
            cv = std_interval / mean_interval if mean_interval > 0 else 1.0
            regularity_score = max(0, 1.0 - cv)  # Invert so low CV = high score
            scores.append(regularity_score * 0.25)
        else:
            scores.append(0.5 * 0.25)  # Neutral score for insufficient data

        # 3. Sequence length score (normalize by max reasonable length = 10)
        length_score = min(pattern.metadata['sequence_length'] / 10.0, 1.0)
        scores.append(length_score * 0.20)

        # 4. Success rate score (would require checking task execution results)
        # For now, assume 0.8 success rate as we filter to completed/running tasks
        success_score = 0.8
        scores.append(success_score * 0.15)

        # 5. Recency score (patterns seen in last week score higher)
        days_since_last = (datetime.now() - pattern.last_seen).days
        recency_score = max(0, 1.0 - (days_since_last / 30.0))  # Decay over 30 days
        scores.append(recency_score * 0.10)

        # Total confidence
        confidence = sum(scores)
        return round(confidence, 2)

    def _generate_workflow_name(self, task_sequence: List[str]) -> str:
        """
        Generate a suggested workflow name from task sequence.

        Strategy:
        - Extract key verbs and nouns
        - Limit to 3-4 words
        - Capitalize properly
        """
        # Extract first 3 tasks (most descriptive)
        first_tasks = task_sequence[:3]

        # Extract first verb from each task
        verbs = []
        for task in first_tasks:
            words = task.split()
            if words:
                # First word is often the verb
                verbs.append(words[0])

        # Combine verbs
        if len(verbs) >= 2:
            name = f"{verbs[0].capitalize()} and {verbs[1].capitalize()}"
        elif len(verbs) == 1:
            name = verbs[0].capitalize() + " Workflow"
        else:
            name = "Automated Workflow"

        # Add context from last task if available
        if len(task_sequence) > 2:
            last_task = task_sequence[-1]
            last_words = last_task.split()
            if len(last_words) > 1:
                context = last_words[-1]
                name = f"{name} - {context.capitalize()}"

        # Limit length
        if len(name) > 50:
            name = name[:47] + "..."

        return name

    def get_pattern_details(self, pattern_id: str) -> Optional[WorkflowPattern]:
        """
        Get detailed information about a specific pattern.

        This could fetch from a cache or re-detect if needed.
        """
        # For now, this would require storing patterns
        # Implementation would depend on storage strategy
        logger.warning(f"get_pattern_details not yet implemented for {pattern_id}")
        return None
