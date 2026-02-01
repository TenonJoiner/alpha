"""
Proactive Screenshot Assistance System

This module provides proactive detection and guidance for screenshot capture
when users describe visual issues or debugging scenarios.

Components:
- ScreenshotDetector: Detect when screenshots would be helpful
- ScreenshotSuggestionGenerator: Generate context-aware screenshot suggestions
- ScreenshotCaptureGuide: Provide platform-specific screenshot instructions
"""

import re
import platform
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class ScreenshotTriggerType(Enum):
    """Types of scenarios that trigger screenshot suggestions."""
    ERROR_DESCRIPTION = "error_description"  # User describes an error
    UI_ISSUE = "ui_issue"  # User describes UI problem
    DEBUG_SESSION = "debug_session"  # Active debugging
    VISUAL_COMPARISON = "visual_comparison"  # Comparing designs/layouts
    UNCLEAR_DESCRIPTION = "unclear_description"  # Ambiguous visual description


@dataclass
class ScreenshotSuggestion:
    """Suggestion to capture a screenshot."""
    suggestion_id: str
    trigger_type: ScreenshotTriggerType
    message: str  # Suggestion message to display to user
    reason: str  # Why screenshot would help
    priority: int  # 1-5, higher = more urgent
    guidance_steps: List[str]  # Platform-specific capture instructions
    created_at: datetime
    context: Dict[str, Any]  # Additional context


class ScreenshotDetector:
    """
    Detects when user input suggests a screenshot would be helpful.

    Uses pattern matching and contextual analysis to identify scenarios
    where visual confirmation would improve assistance quality.
    """

    # Error-related keywords and patterns
    ERROR_PATTERNS = [
        r'\b(error|exception|traceback|stack trace)\b',
        r'\b(crash|freeze|hang|stuck)\b',
        r'\b(fail|failed|failing|failure)\b',
        r'\b(bug|issue|problem|broken)\b',
        r'\b(warning|alert)\b',
    ]

    # UI/Visual issue patterns
    UI_PATTERNS = [
        r'\b(button|link|menu|page|screen|window)\s+(looks?|appears?|shows?)\b',
        r'\b(layout|design|style|css)\s+(issue|problem|wrong|broken)\b',
        r'\b(alignment|spacing|margin|padding)\b',
        r'\b(color|font|size|position)\s+(is|looks|seems)\b',
        r'\b(overlap|cutoff|hidden|missing)\b',
    ]

    # Visual description patterns (ambiguous without image)
    VISUAL_PATTERNS = [
        r'\b(see|seeing|shows?|showing|displays?|appears?)\b',
        r'\b(looks? like|seems? like)\b',
        r'\b(weird|strange|odd|unusual|unexpected)\b',
    ]

    # Comparison/review patterns
    COMPARISON_PATTERNS = [
        r'\b(compare|difference|versus|vs)\b',
        r'\b(review|check|verify|validate)\s+(this|the)\b',
    ]

    def __init__(self):
        """Initialize screenshot detector with compiled regex patterns."""
        self.error_regex = re.compile('|'.join(self.ERROR_PATTERNS), re.IGNORECASE)
        self.ui_regex = re.compile('|'.join(self.UI_PATTERNS), re.IGNORECASE)
        self.visual_regex = re.compile('|'.join(self.VISUAL_PATTERNS), re.IGNORECASE)
        self.comparison_regex = re.compile('|'.join(self.COMPARISON_PATTERNS), re.IGNORECASE)

    def detect_screenshot_need(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ScreenshotTriggerType]:
        """
        Detect if user message suggests a screenshot would be helpful.

        Args:
            user_message: User's input message
            context: Optional conversation context

        Returns:
            ScreenshotTriggerType if screenshot detected, None otherwise
        """
        # Check for error descriptions
        if self.error_regex.search(user_message):
            # Strong signal: user describing error
            if re.search(r'\b(I|I\'m|I am)\s+(seeing|getting|receiving)', user_message, re.IGNORECASE):
                return ScreenshotTriggerType.ERROR_DESCRIPTION

        # Check for UI issues
        if self.ui_regex.search(user_message):
            return ScreenshotTriggerType.UI_ISSUE

        # Check for comparison requests
        if self.comparison_regex.search(user_message):
            # Check if comparing visual elements
            if re.search(r'\b(design|layout|page|screenshot|image)\b', user_message, re.IGNORECASE):
                return ScreenshotTriggerType.VISUAL_COMPARISON

        # Check for visual descriptions (lower priority)
        if self.visual_regex.search(user_message):
            # Count visual keywords
            visual_count = len(self.visual_regex.findall(user_message))
            if visual_count >= 2:  # Multiple visual references
                return ScreenshotTriggerType.UNCLEAR_DESCRIPTION

        # Check context for debug session
        if context:
            if context.get('is_debugging') or context.get('recent_error'):
                return ScreenshotTriggerType.DEBUG_SESSION

        return None

    def calculate_priority(
        self,
        trigger_type: ScreenshotTriggerType,
        user_message: str
    ) -> int:
        """
        Calculate priority level for screenshot suggestion (1-5).

        Higher priority for errors and critical issues.
        """
        base_priority = {
            ScreenshotTriggerType.ERROR_DESCRIPTION: 5,
            ScreenshotTriggerType.DEBUG_SESSION: 4,
            ScreenshotTriggerType.UI_ISSUE: 3,
            ScreenshotTriggerType.VISUAL_COMPARISON: 2,
            ScreenshotTriggerType.UNCLEAR_DESCRIPTION: 1,
        }

        priority = base_priority.get(trigger_type, 1)

        # Boost priority for urgent keywords
        if re.search(r'\b(urgent|critical|production|down)\b', user_message, re.IGNORECASE):
            priority = min(5, priority + 1)

        return priority


class ScreenshotSuggestionGenerator:
    """
    Generates context-aware screenshot suggestions.

    Creates appropriate suggestion messages and guidance based on
    the detected trigger type and user context.
    """

    SUGGESTION_TEMPLATES = {
        ScreenshotTriggerType.ERROR_DESCRIPTION: [
            "A screenshot of the error would help me understand the issue better. Can you share one?",
            "I'd be able to help more effectively if you could share a screenshot of the error.",
            "Could you capture a screenshot of the error? It'll help me provide a more accurate solution.",
        ],
        ScreenshotTriggerType.UI_ISSUE: [
            "A screenshot would help me see exactly what you're describing. Can you share one?",
            "I can better diagnose this UI issue with a screenshot. Would you mind sharing your screen?",
            "Visual confirmation would be helpful here. Could you take a screenshot?",
        ],
        ScreenshotTriggerType.DEBUG_SESSION: [
            "Let's take a screenshot of the current state to better understand what's happening.",
            "A screenshot would help us document this debugging step. Can you capture one?",
        ],
        ScreenshotTriggerType.VISUAL_COMPARISON: [
            "Screenshots of both options would help me provide a detailed comparison.",
            "I can give you a more thorough analysis if you share screenshots of what you want to compare.",
        ],
        ScreenshotTriggerType.UNCLEAR_DESCRIPTION: [
            "I'm having trouble visualizing this from the description. A screenshot would clarify things.",
            "Could you share a screenshot? It'll help me understand exactly what you're referring to.",
        ],
    }

    def __init__(self):
        """Initialize suggestion generator."""
        self.suggestion_count = 0

    def generate_suggestion(
        self,
        trigger_type: ScreenshotTriggerType,
        priority: int,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ScreenshotSuggestion:
        """
        Generate a screenshot suggestion.

        Args:
            trigger_type: Type of trigger that prompted suggestion
            priority: Priority level (1-5)
            user_message: Original user message
            context: Optional context

        Returns:
            ScreenshotSuggestion with message and guidance
        """
        self.suggestion_count += 1
        suggestion_id = f"screenshot_suggestion_{self.suggestion_count}_{datetime.now().timestamp()}"

        # Select appropriate template
        templates = self.SUGGESTION_TEMPLATES.get(trigger_type, [
            "A screenshot would be helpful here. Can you share one?"
        ])
        message = templates[0]  # Use first template (could randomize)

        # Generate reason
        reason = self._generate_reason(trigger_type, user_message)

        # Get capture guidance
        guidance = ScreenshotCaptureGuide.get_guidance()

        return ScreenshotSuggestion(
            suggestion_id=suggestion_id,
            trigger_type=trigger_type,
            message=message,
            reason=reason,
            priority=priority,
            guidance_steps=guidance,
            created_at=datetime.now(),
            context=context or {}
        )

    def _generate_reason(self, trigger_type: ScreenshotTriggerType, user_message: str) -> str:
        """Generate explanation for why screenshot would help."""
        reasons = {
            ScreenshotTriggerType.ERROR_DESCRIPTION:
                "Visual confirmation of error messages helps identify root cause faster",
            ScreenshotTriggerType.UI_ISSUE:
                "Seeing the actual UI helps diagnose layout and styling issues accurately",
            ScreenshotTriggerType.DEBUG_SESSION:
                "Screenshots document debugging steps and current system state",
            ScreenshotTriggerType.VISUAL_COMPARISON:
                "Side-by-side visual comparison provides clearer analysis",
            ScreenshotTriggerType.UNCLEAR_DESCRIPTION:
                "Visual context clarifies ambiguous descriptions",
        }
        return reasons.get(trigger_type, "Visual confirmation improves assistance quality")


class ScreenshotCaptureGuide:
    """
    Provides platform-specific screenshot capture instructions.

    Detects user's operating system and provides appropriate shortcuts
    and guidance for taking screenshots.
    """

    @staticmethod
    def get_guidance() -> List[str]:
        """
        Get screenshot capture instructions for user's platform.

        Returns:
            List of step-by-step instructions
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            return [
                "Press Cmd + Shift + 4 to capture a selected area",
                "Press Cmd + Shift + 3 to capture entire screen",
                "Press Cmd + Shift + 5 for screenshot options",
                "Screenshots save to Desktop by default",
            ]
        elif system == "Windows":
            return [
                "Press Win + Shift + S to open Snipping Tool",
                "Press PrtScn to capture entire screen",
                "Press Alt + PrtScn to capture active window",
                "Press Win + G to open Xbox Game Bar (for recording)",
            ]
        elif system == "Linux":
            return [
                "Press PrtScn to capture entire screen",
                "Press Shift + PrtScn to capture selected area",
                "Press Alt + PrtScn to capture active window",
                "Or use: gnome-screenshot, flameshot, or scrot command",
            ]
        else:
            # Generic instructions
            return [
                "Use your system's screenshot tool",
                "Usually PrtScn key or Cmd+Shift+4 (Mac)",
                "Or use Snipping Tool / Screenshot app",
            ]

    @staticmethod
    def get_quick_tip() -> str:
        """Get a quick one-liner screenshot tip for current platform."""
        system = platform.system()

        tips = {
            "Darwin": "Quick tip: Cmd + Shift + 4 to capture a region",
            "Windows": "Quick tip: Win + Shift + S to open Snipping Tool",
            "Linux": "Quick tip: PrtScn to capture screen",
        }

        return tips.get(system, "Use your system's screenshot tool (usually PrtScn key)")


class ProactiveScreenshotAssistant:
    """
    Main coordinator for proactive screenshot assistance.

    Combines detection, suggestion generation, and guidance to
    proactively help users capture screenshots when beneficial.
    """

    def __init__(self):
        """Initialize proactive screenshot assistant."""
        self.detector = ScreenshotDetector()
        self.generator = ScreenshotSuggestionGenerator()
        self.suggestions_made = []

    def analyze_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ScreenshotSuggestion]:
        """
        Analyze user message and generate screenshot suggestion if appropriate.

        Args:
            user_message: User's input message
            context: Optional conversation context

        Returns:
            ScreenshotSuggestion if screenshot would help, None otherwise
        """
        # Detect if screenshot needed
        trigger_type = self.detector.detect_screenshot_need(user_message, context)

        if not trigger_type:
            return None

        # Calculate priority
        priority = self.detector.calculate_priority(trigger_type, user_message)

        # Generate suggestion
        suggestion = self.generator.generate_suggestion(
            trigger_type=trigger_type,
            priority=priority,
            user_message=user_message,
            context=context
        )

        # Track suggestion
        self.suggestions_made.append(suggestion)

        return suggestion

    def format_suggestion_message(self, suggestion: ScreenshotSuggestion) -> str:
        """
        Format screenshot suggestion as user-friendly message.

        Args:
            suggestion: Screenshot suggestion to format

        Returns:
            Formatted message string
        """
        lines = [
            f"💡 {suggestion.message}",
            "",
            f"Why: {suggestion.reason}",
            "",
            "How to capture:",
        ]

        for i, step in enumerate(suggestion.guidance_steps, 1):
            lines.append(f"  {i}. {step}")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about screenshot suggestions."""
        if not self.suggestions_made:
            return {
                "total_suggestions": 0,
                "by_trigger_type": {},
                "avg_priority": 0
            }

        # Count by trigger type
        by_type = {}
        total_priority = 0

        for suggestion in self.suggestions_made:
            trigger_name = suggestion.trigger_type.value
            by_type[trigger_name] = by_type.get(trigger_name, 0) + 1
            total_priority += suggestion.priority

        return {
            "total_suggestions": len(self.suggestions_made),
            "by_trigger_type": by_type,
            "avg_priority": total_priority / len(self.suggestions_made)
        }
