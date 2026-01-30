"""
Automatic Skill Matcher

Analyzes user requests and finds relevant skills from local installed skills.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    Lightweight skill matcher that finds relevant skills from local installations.

    Features:
    - Local-only matching (no network calls)
    - Keyword-based matching
    - Fast metadata scanning
    - Lazy loading of skill content
    """

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or Path("skills")
        self.skills_cache: List[Dict] = []
        self.cache_loaded = False

    async def load_skills_cache(self) -> bool:
        """Load available skills from local directory (metadata only)."""
        try:
            if not self.skills_dir.exists():
                logger.info(f"Skills directory not found: {self.skills_dir}")
                self.cache_loaded = True
                return True

            logger.info(f"Scanning local skills from {self.skills_dir}...")
            self.skills_cache = []

            # Scan for SKILL.md files
            for skill_dir in self.skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue

                # Extract metadata only (first few lines)
                metadata = self._extract_metadata(skill_file)
                if metadata:
                    self.skills_cache.append({
                        'id': skill_dir.name,
                        'name': skill_dir.name,
                        'description': metadata.get('description', ''),
                        'keywords': metadata.get('keywords', []),
                        'path': str(skill_dir)
                    })

            self.cache_loaded = True
            logger.info(f"Loaded {len(self.skills_cache)} local skills")
            return True

        except Exception as e:
            logger.error(f"Error loading local skills: {e}")
            self.cache_loaded = True  # Set to true to avoid retries
            return False

    def _extract_metadata(self, skill_file: Path) -> Optional[Dict]:
        """Extract metadata from SKILL.md frontmatter (fast read)."""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                # Read only first 50 lines for metadata
                lines = []
                for _ in range(50):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            content = ''.join(lines)

            # Quick parse of YAML frontmatter
            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 2:
                return None

            # Simple key-value extraction (avoid full YAML parse for speed)
            metadata = {}
            for line in parts[1].split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    if key in ['name', 'description', 'keywords']:
                        metadata[key] = value

            return metadata

        except Exception as e:
            logger.warning(f"Failed to extract metadata from {skill_file}: {e}")
            return None

    def match_skills(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Match skills based on query.

        Args:
            query: User query or task description
            max_results: Maximum number of results to return

        Returns:
            List of matching skills with relevance scores
        """
        if not self.cache_loaded:
            logger.warning("Skills cache not loaded")
            return []

        if not self.skills_cache:
            logger.debug("No local skills available")
            return []

        query_lower = query.lower()

        # Extract keywords from query
        keywords = self._extract_keywords(query_lower)

        # Score each skill
        scored_skills = []
        for skill in self.skills_cache:
            score = self._calculate_relevance(skill, keywords, query_lower)
            if score > 0:
                scored_skills.append({
                    'id': skill['id'],
                    'name': skill['name'],
                    'description': skill.get('description', ''),
                    'path': skill.get('path', ''),
                    'score': score,
                    'source': 'local'  # Mark as local skill
                })

        # Sort by score (descending)
        scored_skills.sort(key=lambda x: x['score'], reverse=True)

        return scored_skills[:max_results]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from query."""
        # Common task keywords
        keywords = []

        # Development keywords
        if any(word in query for word in ['react', 'next.js', 'nextjs', 'frontend', 'ui', 'component']):
            keywords.append('react')
        if any(word in query for word in ['design', 'ui', 'ux', 'interface', 'layout']):
            keywords.append('design')
        if any(word in query for word in ['test', 'testing', 'qa']):
            keywords.append('test')
        if any(word in query for word in ['pdf', 'document', 'doc']):
            keywords.append('pdf')
        if any(word in query for word in ['excel', 'spreadsheet', 'xlsx']):
            keywords.append('excel')
        if any(word in query for word in ['powerpoint', 'presentation', 'pptx', 'slides']):
            keywords.append('presentation')
        if any(word in query for word in ['word', 'docx', 'document']):
            keywords.append('word')
        if any(word in query for word in ['seo', 'search engine', 'optimization']):
            keywords.append('seo')
        if any(word in query for word in ['database', 'postgres', 'postgresql', 'sql', 'supabase', 'query', 'queries']):
            keywords.append('database')
        if any(word in query for word in ['auth', 'authentication', 'login', 'user']):
            keywords.append('auth')
        if any(word in query for word in ['mobile', 'react native', 'ios', 'android']):
            keywords.append('mobile')
        if any(word in query for word in ['video', 'animation', 'remotion']):
            keywords.append('video')
        if any(word in query for word in ['browse', 'browser', 'web scraping', 'automation']):
            keywords.append('browser')
        if any(word in query for word in ['audit', 'review', 'analyze', 'check']):
            keywords.append('audit')
        if any(word in query for word in ['copy', 'copywriting', 'content', 'writing']):
            keywords.append('copywriting')

        return keywords

    def _calculate_relevance(self, skill: Dict, keywords: List[str], query: str) -> float:
        """Calculate relevance score for a skill."""
        score = 0.0
        skill_name = skill['name'].lower()
        skill_desc = skill.get('description', '').lower()

        # Exact name match
        if query in skill_name or skill_name in query:
            score += 10.0

        # Name substring match
        query_words = query.split()
        for word in query_words:
            if len(word) > 3 and word in skill_name:
                score += 3.0

        # Keyword matches in name
        for keyword in keywords:
            if keyword in skill_name:
                score += 5.0
            # Check in description too
            if keyword in skill_desc:
                score += 2.0

        # Special mappings for common mismatches
        keyword_to_skill = {
            'database': ['postgres', 'supabase', 'sql'],
            'presentation': ['pptx', 'powerpoint'],
            'excel': ['xlsx'],
            'word': ['docx'],
        }

        for keyword in keywords:
            if keyword in keyword_to_skill:
                for skill_keyword in keyword_to_skill[keyword]:
                    if skill_keyword in skill_name:
                        score += 5.0

        return score

    async def find_best_skill(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching skill for a query.

        Args:
            query: User query or task description

        Returns:
            Best matching skill or None
        """
        if not self.cache_loaded:
            await self.load_skills_cache()

        matches = self.match_skills(query, max_results=1)
        return matches[0] if matches else None

    async def find_skills(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Find multiple matching skills for a query.

        Args:
            query: User query or task description
            max_results: Maximum number of results

        Returns:
            List of matching skills
        """
        if not self.cache_loaded:
            await self.load_skills_cache()

        return self.match_skills(query, max_results=max_results)
