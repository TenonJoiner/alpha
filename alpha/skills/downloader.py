"""
Automatic Skill Downloader

Downloads and installs skills using npx skills CLI.
"""

import logging
import asyncio
from typing import Optional, Dict, List
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)


class SkillDownloader:
    """
    Automatic skill downloader and installer.

    Features:
    - Check if skill is already installed
    - Install skills using npx skills CLI
    - Handle installation errors
    - Track installed skills
    """

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or Path("skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def is_installed(self, skill_name: str) -> bool:
        """Check if a skill is already installed."""
        skill_path = self.skills_dir / skill_name
        return skill_path.exists() and (skill_path / "SKILL.md").exists()

    async def install_skill(
        self,
        repo: str,
        skill_name: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, any]:
        """
        Install a skill from GitHub repository.

        Args:
            repo: Repository in format "owner/repo"
            skill_name: Specific skill name to install (optional)
            force: Force reinstall even if already installed

        Returns:
            Result dictionary with status and messages
        """
        # Check if already installed
        if skill_name and not force and self.is_installed(skill_name):
            logger.info(f"Skill '{skill_name}' already installed")
            return {
                "success": True,
                "already_installed": True,
                "skill_name": skill_name,
                "message": f"Skill '{skill_name}' is already installed"
            }

        try:
            logger.info(f"Installing skill from {repo}{f' (skill: {skill_name})' if skill_name else ''}...")

            # Build command
            cmd = ["npx", "skills", "add", repo, "--yes"]
            if skill_name:
                cmd.extend(["--skill", skill_name])

            # Run installation
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully installed skill from {repo}")
                return {
                    "success": True,
                    "already_installed": False,
                    "skill_name": skill_name,
                    "repo": repo,
                    "message": f"Successfully installed skill from {repo}",
                    "output": stdout.decode('utf-8') if stdout else ""
                }
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Failed to install skill from {repo}: {error_msg}")
                return {
                    "success": False,
                    "skill_name": skill_name,
                    "repo": repo,
                    "error": error_msg,
                    "message": f"Failed to install skill: {error_msg}"
                }

        except Exception as e:
            logger.error(f"Error installing skill from {repo}: {e}", exc_info=True)
            return {
                "success": False,
                "skill_name": skill_name,
                "repo": repo,
                "error": str(e),
                "message": f"Error during installation: {e}"
            }

    async def install_skill_by_id(self, skill_id: str, source: str) -> Dict[str, any]:
        """
        Install a skill by its ID and source repository.

        Args:
            skill_id: Skill ID (name)
            source: Source repository (e.g., "vercel-labs/agent-skills")

        Returns:
            Result dictionary
        """
        return await self.install_skill(repo=source, skill_name=skill_id)

    def list_installed_skills(self) -> List[str]:
        """List all installed skills."""
        if not self.skills_dir.exists():
            return []

        installed = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                installed.append(item.name)

        return sorted(installed)

    async def ensure_skill_installed(self, skill_name: str, source: str) -> bool:
        """
        Ensure a skill is installed, install if not.

        Args:
            skill_name: Skill name
            source: Source repository

        Returns:
            True if skill is available (was installed or already exists)
        """
        if self.is_installed(skill_name):
            logger.info(f"Skill '{skill_name}' is already installed")
            return True

        logger.info(f"Skill '{skill_name}' not found, installing...")
        result = await self.install_skill_by_id(skill_name, source)

        return result.get("success", False)
