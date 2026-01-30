"""
Automatic Skill Manager

Coordinates skill matching, downloading, and loading.
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path

from alpha.skills.matcher import SkillMatcher
from alpha.skills.downloader import SkillDownloader
from alpha.skills.loader import SkillLoader

logger = logging.getLogger(__name__)


class AutoSkillManager:
    """
    Automatic skill management system.

    Features:
    - Analyze user queries for skill relevance
    - Find matching skills from marketplace
    - Auto-install skills when needed
    - Load skill context for LLM
    - Track skill usage
    """

    def __init__(
        self,
        skills_dir: Path = None,
        auto_install: bool = False,  # Disabled by default for performance
        auto_load: bool = True
    ):
        """
        Initialize auto-skill manager.

        Args:
            skills_dir: Directory for installed skills
            auto_install: Automatically install missing skills (disabled for performance)
            auto_load: Automatically load skill context
        """
        self.skills_dir = skills_dir or Path(".agents/skills")
        self.auto_install = auto_install
        self.auto_load = auto_load

        # Initialize components
        self.matcher = SkillMatcher(skills_dir=self.skills_dir)
        self.downloader = SkillDownloader(skills_dir=self.skills_dir)
        self.loader = SkillLoader(skills_dir=self.skills_dir)

        # Skill usage tracking
        self.usage_stats: Dict[str, int] = {}

        logger.info(f"AutoSkillManager: auto_install={auto_install}, local_only mode")

    async def initialize(self):
        """Initialize the manager (load skill cache)."""
        await self.matcher.load_skills_cache()
        logger.info("AutoSkillManager initialized")

    async def process_query(self, query: str) -> Optional[Dict[str, any]]:
        """
        Process a user query and find/load relevant skill from local installations.

        Args:
            query: User query or request

        Returns:
            Dict with skill info and context, or None
        """
        # Find matching skills (local only, fast)
        matches = await self.matcher.find_skills(query, max_results=3)

        if not matches:
            logger.debug("No matching local skills found for query")
            return None

        best_match = matches[0]
        logger.info(f"Best skill match: {best_match['name']} (score: {best_match['score']})")

        # Check if we should use this skill (threshold)
        if best_match['score'] < 3.0:
            logger.debug(f"Skill score too low ({best_match['score']}), skipping")
            return None

        skill_name = best_match['name']

        # Load skill context (already installed locally)
        if self.auto_load:
            context = self.loader.get_skill_context(skill_name)
            if not context:
                logger.warning(f"Failed to load skill context: {skill_name}")
                return None

            # Track usage
            self.usage_stats[skill_name] = self.usage_stats.get(skill_name, 0) + 1

            return {
                'skill_name': skill_name,
                'skill_source': 'local',
                'context': context,
                'matches': matches,  # All matches for reference
                'score': best_match['score']
            }

        return {
            'skill_name': skill_name,
            'skill_source': 'local',
            'matches': matches
        }

    async def get_skill_context(self, skill_name: str) -> Optional[str]:
        """
        Get context for a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill context string, or None
        """
        # Check if installed
        if not self.downloader.is_installed(skill_name):
            if self.auto_install:
                logger.info(f"Skill not installed, searching marketplace...")
                # Try to find and install
                matches = await self.matcher.find_skills(skill_name, max_results=1)
                if matches:
                    skill = matches[0]
                    install_result = await self.downloader.install_skill_by_id(
                        skill['name'],
                        skill['source']
                    )
                    if not install_result.get('success'):
                        logger.error(f"Failed to install skill: {skill_name}")
                        return None
                else:
                    logger.warning(f"Skill not found in marketplace: {skill_name}")
                    return None
            else:
                logger.warning(f"Skill not installed and auto_install is disabled: {skill_name}")
                return None

        # Load and return context
        return self.loader.get_skill_context(skill_name)

    def list_installed_skills(self) -> List[Dict[str, str]]:
        """List all installed skills with descriptions."""
        return self.loader.list_available_skills()

    def get_usage_stats(self) -> Dict[str, int]:
        """Get skill usage statistics."""
        return self.usage_stats.copy()

    async def suggest_skills(self, query: str, max_suggestions: int = 5) -> List[Dict[str, any]]:
        """
        Suggest relevant skills for a query without installing.

        Args:
            query: User query
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested skills
        """
        matches = await self.matcher.find_skills(query, max_results=max_suggestions)

        suggestions = []
        for match in matches:
            is_installed = self.downloader.is_installed(match['name'])
            suggestions.append({
                'name': match['name'],
                'source': match['source'],
                'installs': match['installs'],
                'score': match['score'],
                'installed': is_installed
            })

        return suggestions
