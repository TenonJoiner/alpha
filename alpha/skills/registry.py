"""
Agent Skill Registry

Manages installed skills and their lifecycle.
"""

import logging
from typing import Dict, Optional, List
from pathlib import Path
import asyncio

from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Skill registry for managing installed skills.

    Features:
    - Skill registration and discovery
    - Skill lifecycle management (initialize, execute, cleanup)
    - Version management
    - Error handling
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills: Dict[str, AgentSkill] = {}
        # Use project-local skills directory (non-hidden for visibility)
        self.skills_dir = skills_dir or Path("skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def register(self, skill: AgentSkill, initialize: bool = True) -> bool:
        """
        Register a skill.

        Args:
            skill: AgentSkill instance
            initialize: Whether to initialize the skill immediately

        Returns:
            True if registration successful
        """
        skill_name = skill.metadata.name

        # Check if skill already registered
        if skill_name in self.skills:
            existing_version = self.skills[skill_name].metadata.version
            new_version = skill.metadata.version
            logger.warning(
                f"Skill {skill_name} already registered "
                f"(existing: v{existing_version}, new: v{new_version})"
            )

            # Allow override if new version is higher
            if self._compare_versions(new_version, existing_version) <= 0:
                return False

        # Initialize if requested
        if initialize and not skill.initialized:
            try:
                success = await skill.initialize()
                if not success:
                    logger.error(f"Failed to initialize skill: {skill_name}")
                    return False
                skill.initialized = True
            except Exception as e:
                logger.error(f"Error initializing skill {skill_name}: {e}", exc_info=True)
                return False

        self.skills[skill_name] = skill
        logger.info(f"Registered skill: {skill_name} v{skill.metadata.version}")
        return True

    async def unregister(self, skill_name: str):
        """
        Unregister a skill.

        Args:
            skill_name: Skill name
        """
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            try:
                await skill.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up skill {skill_name}: {e}", exc_info=True)

            del self.skills[skill_name]
            logger.info(f"Unregistered skill: {skill_name}")

    def get_skill(self, skill_name: str) -> Optional[AgentSkill]:
        """
        Get skill by name.

        Args:
            skill_name: Skill name

        Returns:
            AgentSkill instance or None
        """
        return self.skills.get(skill_name)

    def list_skills(self) -> List[Dict[str, str]]:
        """
        List all registered skills.

        Returns:
            List of skill metadata dicts
        """
        return [
            {
                "name": skill.metadata.name,
                "version": skill.metadata.version,
                "description": skill.metadata.description,
                "category": skill.metadata.category,
                "author": skill.metadata.author,
            }
            for skill in self.skills.values()
        ]

    async def execute_skill(
        self,
        skill_name: str,
        **kwargs
    ) -> SkillResult:
        """
        Execute a skill by name.

        Args:
            skill_name: Skill name
            **kwargs: Skill parameters

        Returns:
            Skill execution result
        """
        skill = self.get_skill(skill_name)

        if not skill:
            return SkillResult(
                success=False,
                output=None,
                error=f"Skill not found: {skill_name}"
            )

        if not skill.initialized:
            # Try to initialize
            try:
                success = await skill.initialize()
                if not success:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Failed to initialize skill: {skill_name}"
                    )
                skill.initialized = True
            except Exception as e:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Error initializing skill: {str(e)}"
                )

        try:
            import time
            start_time = time.time()
            result = await skill.execute(**kwargs)
            result.execution_time = time.time() - start_time
            logger.info(
                f"Skill {skill_name} executed: success={result.success}, "
                f"time={result.execution_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Skill execution failed: {e}", exc_info=True)
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup_all(self):
        """Clean up all registered skills."""
        for skill_name in list(self.skills.keys()):
            await self.unregister(skill_name)

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        def parse_version(v: str) -> List[int]:
            return [int(x) for x in v.split('.') if x.isdigit()]

        parts1 = parse_version(v1)
        parts2 = parse_version(v2)

        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0

            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1

        return 0
