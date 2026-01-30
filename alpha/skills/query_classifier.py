"""
Query Classifier

Classifies user queries to determine if skill matching is needed.
Fast, rule-based classification to avoid unnecessary overhead.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Lightweight query classifier for determining query type.

    Categories:
    - task: Action-oriented queries that may need skills
    - question: Information/conversational queries (no skills needed)
    - command: System commands (no skills needed)
    """

    # Task indicators (action verbs and task patterns)
    TASK_INDICATORS = [
        # Creation/Generation
        r'\b(create|generate|make|build|design|write|compose|draft)\b',
        # Modification
        r'\b(edit|modify|update|change|fix|refactor|improve|optimize)\b',
        # Analysis
        r'\b(analyze|audit|review|check|test|validate|inspect)\b',
        # Data operations
        r'\b(convert|transform|parse|extract|fetch|scrape|download)\b',
        # File operations
        r'\b(read|open|save|export|import)\s+.*\.(pdf|docx|xlsx|pptx|csv|json|xml)\b',
        # Development tasks
        r'\b(deploy|run|execute|install|setup|configure)\b',
        # Help with specific tools/technologies
        r'\b(help.*with|how.*to|show.*how)\s+\w+',
        # Chinese task verbs
        r'(帮我|帮忙|请|麻烦)(创建|生成|制作|写|编写|构建|设计)',
        r'(创建|生成|制作|构建|设计|编写|写一个|做一个)',
        r'(修改|更新|改|优化|重构)',
        r'(分析|审查|检查|测试|验证)',
        r'(转换|解析|提取|获取|下载)',
    ]

    # Question indicators (conversational, no action needed)
    QUESTION_INDICATORS = [
        r'^\s*(what|when|where|who|why|how)\s+(is|are|was|were|do|does|did|can|could|would|should)',
        r'^\s*(tell me|explain|describe|define)\b',
        r'\?$',  # Ends with question mark
        r'^\s*(是什么|为什么|怎么样|如何|哪里|什么时候)',  # Chinese questions
    ]

    # Command indicators (system commands)
    COMMAND_INDICATORS = [
        r'^\s*(help|status|clear|quit|exit|skills|search skill)\b',
    ]

    # Simple query patterns (single word, greetings, etc.)
    SIMPLE_PATTERNS = [
        r'^\s*\w{1,4}\s*$',  # Single short word
        r'^\s*(hi|hello|hey|thanks|ok|yes|no)\s*$',  # Greetings/responses
        r'^\s*(你好|谢谢|好的|是的|不)\s*$',  # Chinese greetings/responses
    ]

    def __init__(self):
        # Compile regex patterns for performance
        self.task_patterns = [re.compile(p, re.IGNORECASE) for p in self.TASK_INDICATORS]
        self.question_patterns = [re.compile(p, re.IGNORECASE) for p in self.QUESTION_INDICATORS]
        self.command_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INDICATORS]
        self.simple_patterns = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_PATTERNS]

    def classify(self, query: str) -> Dict[str, any]:
        """
        Classify a user query.

        Args:
            query: User input string

        Returns:
            Dict with classification results:
            {
                'type': 'task' | 'question' | 'command' | 'simple',
                'needs_skill_matching': bool,
                'confidence': float (0-1)
            }
        """
        if not query or not query.strip():
            return {
                'type': 'simple',
                'needs_skill_matching': False,
                'confidence': 1.0
            }

        query = query.strip()

        # Check for system commands first
        if self._matches_any(query, self.command_patterns):
            return {
                'type': 'command',
                'needs_skill_matching': False,
                'confidence': 1.0
            }

        # Check for simple queries
        if self._matches_any(query, self.simple_patterns):
            return {
                'type': 'simple',
                'needs_skill_matching': False,
                'confidence': 1.0
            }

        # Check for task indicators
        task_matches = sum(1 for p in self.task_patterns if p.search(query))

        # Check for question indicators
        question_matches = sum(1 for p in self.question_patterns if p.search(query))

        # Decision logic
        if task_matches > 0:
            # Strong task signals
            confidence = min(0.6 + (task_matches * 0.2), 1.0)
            return {
                'type': 'task',
                'needs_skill_matching': True,
                'confidence': confidence
            }

        if question_matches > 0:
            # Question pattern detected
            return {
                'type': 'question',
                'needs_skill_matching': False,
                'confidence': 0.8
            }

        # Default: treat as question if short, task if longer
        if len(query) < 30:
            return {
                'type': 'question',
                'needs_skill_matching': False,
                'confidence': 0.5
            }
        else:
            # Longer queries might be complex tasks
            return {
                'type': 'task',
                'needs_skill_matching': True,
                'confidence': 0.4
            }

    def _matches_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        """Check if text matches any pattern in list."""
        return any(p.search(text) for p in patterns)

    def is_task_query(self, query: str) -> bool:
        """Quick check if query is task-oriented."""
        result = self.classify(query)
        return result['needs_skill_matching']
