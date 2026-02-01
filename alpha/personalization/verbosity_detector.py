"""
Verbosity Detector - Detect User's Preferred Response Detail Level

Analyzes user interactions to determine preferred verbosity:
- Concise: Short, to-the-point responses
- Balanced: Moderate detail (default)
- Detailed: Comprehensive explanations

Detection signals:
- User message length patterns
- Explicit signals ("be brief", "explain more")
- Follow-up question frequency
- Reading engagement patterns
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VerbositySignal:
    """
    A signal indicating verbosity preference

    Attributes:
        signal_type: Type of signal (explicit, message_length, followup, etc.)
        direction: 'concise' or 'detailed'
        strength: Signal strength (0.0 to 1.0)
        context: Additional context about the signal
        timestamp: When signal was detected
    """
    signal_type: str
    direction: str  # 'concise' or 'detailed'
    strength: float  # 0.0 to 1.0
    context: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class VerbosityDetector:
    """
    Detect user's preferred verbosity level from conversation patterns

    Analyzes:
    1. Explicit signals: "be brief", "explain in detail", "too long"
    2. Message length: Average user message length
    3. Follow-up questions: Asking for more/less detail
    4. Engagement: Whether user reads full responses

    Returns confidence-scored verbosity preference.
    """

    # Explicit signal patterns
    CONCISE_PATTERNS = [
        r'\b(be )?brief(ly)?\b',
        r'\bshort(er)? (answer|response|version)\b',
        r'\bquick(ly)?\b',
        r'\btoo (long|verbose|detailed|wordy)\b',
        r'\bTL;?DR\b',
        r'\bjust (tell|show) me\b',
        r'\bin (short|brief|summary)\b',
        r'\bsummarize\b',
        r'\bget to the point\b',
    ]

    DETAILED_PATTERNS = [
        r'\bexplain (in )?detail\b',
        r'\bmore detail(s|ed)?\b',
        r'\belaborate\b',
        r'\bcomprehensive\b',
        r'\btell me (everything|all|more)\b',
        r'\bwhat (exactly|specifically)\b',
        r'\b(deep|deeper) dive\b',
        r'\bstep[- ]by[- ]step\b',
        r'\btoo (short|brief|vague)\b',
    ]

    def __init__(self):
        """Initialize verbosity detector with compiled patterns"""
        self.concise_regex = [re.compile(p, re.IGNORECASE) for p in self.CONCISE_PATTERNS]
        self.detailed_regex = [re.compile(p, re.IGNORECASE) for p in self.DETAILED_PATTERNS]

        # Statistics
        self.signals_detected = 0
        self.explicit_signals = 0
        self.implicit_signals = 0

    def detect_from_message(self, message: str) -> List[VerbositySignal]:
        """
        Detect verbosity signals from a single user message

        Args:
            message: User message text

        Returns:
            List of detected verbosity signals
        """
        signals = []

        # 1. Check explicit signals
        signals.extend(self._detect_explicit_signals(message))

        # 2. Analyze message length (implicit signal)
        length_signal = self._analyze_message_length(message)
        if length_signal:
            signals.append(length_signal)

        self.signals_detected += len(signals)
        return signals

    def detect_from_history(
        self,
        messages: List[Dict[str, str]],
        min_messages: int = 5
    ) -> Tuple[str, float]:
        """
        Detect verbosity preference from conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            min_messages: Minimum messages needed for confident detection

        Returns:
            Tuple of (verbosity_level, confidence_score)
            - verbosity_level: 'concise', 'balanced', or 'detailed'
            - confidence_score: 0.0 to 1.0
        """
        if len(messages) < min_messages:
            # Not enough data - return default
            return ('balanced', 0.0)

        # Collect all signals from user messages
        all_signals = []
        user_messages = [m for m in messages if m.get('role') == 'user']

        for msg in user_messages:
            content = msg.get('content', '')
            signals = self.detect_from_message(content)
            all_signals.extend(signals)

        if not all_signals:
            # No signals detected - analyze overall patterns
            return self._analyze_overall_patterns(user_messages)

        # Calculate weighted preference
        return self._calculate_preference(all_signals, len(user_messages))

    def _detect_explicit_signals(self, message: str) -> List[VerbositySignal]:
        """Detect explicit verbosity signals in message"""
        signals = []

        # Check concise patterns
        for pattern in self.concise_regex:
            if pattern.search(message):
                signals.append(VerbositySignal(
                    signal_type='explicit',
                    direction='concise',
                    strength=0.9,  # Explicit signals are strong
                    context=f"Matched pattern: {pattern.pattern}"
                ))
                self.explicit_signals += 1
                break  # One explicit signal is enough

        # Check detailed patterns
        for pattern in self.detailed_regex:
            if pattern.search(message):
                signals.append(VerbositySignal(
                    signal_type='explicit',
                    direction='detailed',
                    strength=0.9,
                    context=f"Matched pattern: {pattern.pattern}"
                ))
                self.explicit_signals += 1
                break

        return signals

    def _analyze_message_length(self, message: str) -> Optional[VerbositySignal]:
        """Analyze message length as implicit verbosity signal"""
        words = message.split()
        word_count = len(words)

        # Very short messages (< 10 words) suggest preference for brevity
        if word_count < 10:
            return VerbositySignal(
                signal_type='message_length',
                direction='concise',
                strength=0.3,  # Weak signal
                context=f"{word_count} words"
            )

        # Long messages (> 50 words) suggest comfort with detail
        elif word_count > 50:
            return VerbositySignal(
                signal_type='message_length',
                direction='detailed',
                strength=0.4,
                context=f"{word_count} words"
            )

        return None

    def _analyze_overall_patterns(
        self,
        user_messages: List[Dict[str, str]]
    ) -> Tuple[str, float]:
        """
        Analyze overall conversation patterns when no explicit signals

        Looks at:
        - Average message length
        - Question complexity
        """
        if not user_messages:
            return ('balanced', 0.0)

        # Calculate average message length
        total_words = 0
        for msg in user_messages:
            content = msg.get('content', '')
            total_words += len(content.split())

        avg_words = total_words / len(user_messages)

        # Infer preference from average length
        if avg_words < 15:
            # Short messages → likely prefers concise responses
            confidence = min(0.6, len(user_messages) / 20)  # Max 0.6 confidence
            return ('concise', confidence)
        elif avg_words > 40:
            # Long messages → likely comfortable with detail
            confidence = min(0.6, len(user_messages) / 20)
            return ('detailed', confidence)
        else:
            # Medium length → balanced preference
            confidence = min(0.5, len(user_messages) / 30)
            return ('balanced', confidence)

    def _calculate_preference(
        self,
        signals: List[VerbositySignal],
        total_messages: int
    ) -> Tuple[str, float]:
        """
        Calculate verbosity preference from collected signals

        Args:
            signals: All detected verbosity signals
            total_messages: Total number of user messages analyzed

        Returns:
            Tuple of (verbosity_level, confidence_score)
        """
        if not signals:
            return ('balanced', 0.0)

        # Calculate weighted scores for each direction
        concise_score = sum(
            s.strength for s in signals if s.direction == 'concise'
        )
        detailed_score = sum(
            s.strength for s in signals if s.direction == 'detailed'
        )

        # Determine preference
        if concise_score > detailed_score * 1.5:
            preference = 'concise'
            raw_confidence = concise_score / len(signals)
        elif detailed_score > concise_score * 1.5:
            preference = 'detailed'
            raw_confidence = detailed_score / len(signals)
        else:
            preference = 'balanced'
            raw_confidence = 0.5

        # Adjust confidence based on number of messages
        # More messages = higher confidence
        message_factor = min(1.0, total_messages / 20)  # Cap at 20 messages
        confidence = raw_confidence * message_factor

        # Explicit signals boost confidence
        explicit_count = sum(1 for s in signals if s.signal_type == 'explicit')
        if explicit_count > 0:
            confidence = min(1.0, confidence + 0.2 * explicit_count)

        return (preference, round(confidence, 2))

    def get_statistics(self) -> Dict[str, int]:
        """Get detector statistics"""
        return {
            'signals_detected': self.signals_detected,
            'explicit_signals': self.explicit_signals,
            'implicit_signals': self.implicit_signals
        }
