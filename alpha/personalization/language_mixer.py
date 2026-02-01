"""
Language Mixer - Smart EN/CN Language Switching

Intelligently mixes English and Chinese based on:
- User's language patterns in conversation
- Topic context (technical vs. casual)
- Code/technical content preservation
- User's explicit language preference

Mixing Strategies:
1. Mirror: Match user's language for current message
2. Topic-based: Technical content in EN, casual in CN
3. Hybrid: Mix languages naturally based on context
4. Fixed: Always use user's preferred language
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LanguageSignal:
    """
    Signal indicating language preference

    Attributes:
        language: Detected language ('en', 'zh', or 'mixed')
        confidence: Detection confidence (0.0 to 1.0)
        context: Context of detection (topic, message, etc.)
        timestamp: When detected
    """
    language: str  # 'en', 'zh', 'mixed'
    confidence: float  # 0.0 to 1.0
    context: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LanguageMixer:
    """
    Smart language mixer for EN/CN bilingual communication

    Features:
    - Detects user's language preference from conversation
    - Adapts language based on topic (technical vs. casual)
    - Preserves code and technical terms in original language
    - Supports multiple mixing strategies

    Usage:
        mixer = LanguageMixer()

        # Detect user's language preference
        pref, conf = mixer.detect_language_preference(messages)

        # Get mixing strategy for response
        strategy = mixer.get_mixing_strategy(user_message, topic='technical')
    """

    # Language detection patterns
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]+')  # Chinese characters
    ENGLISH_PATTERN = re.compile(r'[a-zA-Z]+')

    # Technical keywords (keep in English)
    TECHNICAL_KEYWORDS = {
        'code', 'function', 'class', 'method', 'api', 'error', 'bug',
        'database', 'query', 'server', 'client', 'http', 'json', 'xml',
        'git', 'commit', 'branch', 'merge', 'python', 'javascript',
        'algorithm', 'data structure', 'optimization', 'performance',
        'test', 'debug', 'deploy', 'build', 'compile', 'runtime'
    }

    def __init__(self, default_preference: str = 'mixed'):
        """
        Initialize language mixer

        Args:
            default_preference: Default language preference
                              ('en', 'zh', 'mixed')
        """
        self.default_preference = default_preference
        self.detection_count = 0
        self.language_switches = 0

    def detect_language_preference(
        self,
        messages: List[Dict[str, str]],
        min_messages: int = 3
    ) -> Tuple[str, float]:
        """
        Detect user's language preference from conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            min_messages: Minimum messages for confident detection

        Returns:
            Tuple of (language_preference, confidence)
            - language_preference: 'en', 'zh', or 'mixed'
            - confidence: 0.0 to 1.0
        """
        user_messages = [m for m in messages if m.get('role') == 'user']

        if len(user_messages) < min_messages:
            return (self.default_preference, 0.0)

        # Analyze each message
        signals = []
        for msg in user_messages:
            content = msg.get('content', '')
            signal = self._detect_message_language(content)
            if signal:
                signals.append(signal)

        if not signals:
            return (self.default_preference, 0.0)

        # Calculate preference from signals
        return self._calculate_language_preference(signals)

    def _detect_message_language(self, message: str) -> Optional[LanguageSignal]:
        """
        Detect primary language of a message

        Args:
            message: Message text

        Returns:
            LanguageSignal or None
        """
        # Count characters
        chinese_chars = len(self.CHINESE_PATTERN.findall(message))
        english_words = len(self.ENGLISH_PATTERN.findall(message))

        # Skip very short messages
        if chinese_chars + english_words < 5:
            return None

        # Determine language
        total_chars = chinese_chars + english_words

        if chinese_chars == 0 and english_words > 0:
            # Pure English
            return LanguageSignal(
                language='en',
                confidence=1.0,
                context=f"{english_words} EN words, 0 CN chars"
            )
        elif english_words == 0 and chinese_chars > 0:
            # Pure Chinese
            return LanguageSignal(
                language='zh',
                confidence=1.0,
                context=f"0 EN words, {chinese_chars} CN chars"
            )
        else:
            # Mixed language
            cn_ratio = chinese_chars / total_chars

            if cn_ratio > 0.7:
                # Predominantly Chinese
                return LanguageSignal(
                    language='zh',
                    confidence=0.8,
                    context=f"{cn_ratio:.1%} Chinese"
                )
            elif cn_ratio < 0.3:
                # Predominantly English
                return LanguageSignal(
                    language='en',
                    confidence=0.8,
                    context=f"{1-cn_ratio:.1%} English"
                )
            else:
                # Truly mixed
                return LanguageSignal(
                    language='mixed',
                    confidence=0.9,
                    context=f"Mixed: {cn_ratio:.1%} CN, {1-cn_ratio:.1%} EN"
                )

    def _calculate_language_preference(
        self,
        signals: List[LanguageSignal]
    ) -> Tuple[str, float]:
        """
        Calculate overall language preference from signals

        Args:
            signals: List of language signals

        Returns:
            Tuple of (language, confidence)
        """
        if not signals:
            return (self.default_preference, 0.0)

        # Count language occurrences weighted by confidence
        lang_scores = {'en': 0.0, 'zh': 0.0, 'mixed': 0.0}

        for signal in signals:
            lang_scores[signal.language] += signal.confidence

        # Determine preference
        max_lang = max(lang_scores, key=lang_scores.get)
        total_score = sum(lang_scores.values())

        if total_score == 0:
            return (self.default_preference, 0.0)

        # Calculate confidence
        confidence = lang_scores[max_lang] / total_score

        # Boost confidence if consistent across many messages
        if len(signals) > 10:
            confidence = min(1.0, confidence * 1.2)

        return (max_lang, round(confidence, 2))

    def get_mixing_strategy(
        self,
        user_message: str,
        topic: str = 'general',
        preference: str = None
    ) -> Dict[str, any]:
        """
        Get recommended language mixing strategy for response

        Args:
            user_message: Current user message
            topic: Message topic ('technical', 'casual', 'general')
            preference: User's language preference (if known)

        Returns:
            Dict with mixing strategy:
            {
                'primary_language': 'en' or 'zh',
                'allow_mixing': bool,
                'preserve_technical_en': bool,
                'preserve_code': bool,
                'reasoning': str
            }
        """
        # Detect current message language
        current_signal = self._detect_message_language(user_message)
        current_lang = current_signal.language if current_signal else 'en'

        # Default strategy
        strategy = {
            'primary_language': 'en',
            'allow_mixing': False,
            'preserve_technical_en': True,
            'preserve_code': True,
            'reasoning': 'Default English response'
        }

        # 1. If user has explicit preference, follow it
        if preference:
            strategy['primary_language'] = preference
            strategy['allow_mixing'] = (preference == 'mixed')
            strategy['reasoning'] = f"Following user preference: {preference}"
            return strategy

        # 2. Mirror user's current message language
        if current_lang in ['en', 'zh']:
            strategy['primary_language'] = current_lang
            strategy['allow_mixing'] = False
            strategy['reasoning'] = f"Mirroring user's message language: {current_lang}"
            return strategy

        # 3. Topic-based strategy
        if topic == 'technical':
            strategy['primary_language'] = 'en'
            strategy['allow_mixing'] = True  # Allow CN explanations
            strategy['reasoning'] = "Technical topic - primary EN with CN support"
        elif topic == 'casual':
            # Use message language or default
            strategy['primary_language'] = current_lang if current_lang != 'mixed' else 'zh'
            strategy['allow_mixing'] = True
            strategy['reasoning'] = "Casual topic - flexible language mixing"
        else:  # general
            strategy['primary_language'] = current_lang if current_lang != 'mixed' else 'en'
            strategy['allow_mixing'] = True
            strategy['reasoning'] = "General topic - match message language"

        return strategy

    def is_technical_content(self, text: str) -> bool:
        """
        Check if text contains technical content

        Args:
            text: Text to check

        Returns:
            True if technical content detected
        """
        text_lower = text.lower()

        # Check for technical keywords
        keyword_matches = sum(
            1 for keyword in self.TECHNICAL_KEYWORDS
            if keyword in text_lower
        )

        # Check for code patterns
        code_patterns = [
            r'```[\s\S]*?```',  # Code blocks
            r'`[^`]+`',  # Inline code
            r'\w+\([^)]*\)',  # Function calls
            r'\w+\.\w+',  # Object.method
        ]

        code_matches = sum(
            1 for pattern in code_patterns
            if re.search(pattern, text)
        )

        # Technical if 3+ keywords or 2+ code patterns
        return keyword_matches >= 3 or code_matches >= 2

    def get_statistics(self) -> Dict[str, int]:
        """Get mixer statistics"""
        return {
            'detection_count': self.detection_count,
            'language_switches': self.language_switches
        }


class LanguageAdaptivePrompt:
    """
    Helper to create language-adaptive prompts

    Generates prompts that instruct LLM to use appropriate language
    based on mixing strategy.
    """

    @staticmethod
    def create_language_instruction(strategy: Dict[str, any]) -> str:
        """
        Create language instruction for LLM prompt

        Args:
            strategy: Mixing strategy from LanguageMixer.get_mixing_strategy()

        Returns:
            Instruction string to prepend to system prompt
        """
        lang = strategy['primary_language']
        allow_mix = strategy['allow_mixing']

        if lang == 'en' and not allow_mix:
            return "Respond in English only."
        elif lang == 'zh' and not allow_mix:
            return "Respond in Chinese (中文) only."
        elif lang == 'en' and allow_mix:
            return (
                "Respond primarily in English. "
                "You may use Chinese for explanations if helpful, "
                "but keep technical terms in English."
            )
        elif lang == 'zh' and allow_mix:
            return (
                "Respond primarily in Chinese (中文). "
                "Keep code, function names, and technical terms in English."
            )
        else:  # mixed
            return (
                "Respond in a natural mix of English and Chinese. "
                "Use English for technical content and Chinese for explanations. "
                "Always keep code in English."
            )
