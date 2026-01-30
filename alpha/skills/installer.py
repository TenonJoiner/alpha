"""
Agent Skill Installer

Install and manage skill dependencies and lifecycle.
"""

import logging
import subprocess
import sys
from typing import Optional
from pathlib import Path
import importlib.util
import yaml

from alpha.skills.base import AgentSkill, SkillMetadata

logger = logging.getLogger(__name__)


class SkillInstaller:
    """
    Skill installer for installing and loading skills.

    Features:
    - Install skill dependencies
    - Load skill modules dynamically
    - Validate skill structure
    - Handle skill lifecycle
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        # Use project-local skills directory (non-hidden for visibility)
        self.skills_dir = skills_dir or Path("skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def install(
        self,
        skill_dir: Path,
        install_deps: bool = True
    ) -> Optional[AgentSkill]:
        """
        Install a skill from a directory.

        Args:
            skill_dir: Path to skill directory
            install_deps: Whether to install dependencies

        Returns:
            AgentSkill instance or None if installation failed
        """
        logger.info(f"Installing skill from: {skill_dir}")

        # Validate skill structure
        if not self._validate_skill_structure(skill_dir):
            logger.error(f"Invalid skill structure: {skill_dir}")
            return None

        # Load skill metadata
        metadata = self._load_metadata(skill_dir)
        if not metadata:
            logger.error(f"Failed to load skill metadata: {skill_dir}")
            return None

        # Install dependencies
        if install_deps:
            success = await self._install_dependencies(skill_dir)
            if not success:
                logger.error(f"Failed to install dependencies for: {metadata.name}")
                return None

        # Load skill module
        skill_instance = self._load_skill_module(skill_dir, metadata)
        if not skill_instance:
            logger.error(f"Failed to load skill module: {metadata.name}")
            return None

        # Set installation path
        skill_instance.installed_at = skill_dir

        logger.info(f"Successfully installed skill: {metadata.name} v{metadata.version}")
        return skill_instance

    def _validate_skill_structure(self, skill_dir: Path) -> bool:
        """
        Validate skill directory structure.

        Required files:
        - skill.yaml (metadata)
        - skill.py (implementation)

        Args:
            skill_dir: Path to skill directory

        Returns:
            True if valid
        """
        required_files = ["skill.yaml", "skill.py"]

        for filename in required_files:
            file_path = skill_dir / filename
            if not file_path.exists():
                logger.error(f"Missing required file: {filename}")
                return False

        return True

    def _load_metadata(self, skill_dir: Path) -> Optional[SkillMetadata]:
        """
        Load skill metadata from skill.yaml.

        Args:
            skill_dir: Path to skill directory

        Returns:
            SkillMetadata or None if failed
        """
        metadata_file = skill_dir / "skill.yaml"

        try:
            with open(metadata_file, 'r') as f:
                data = yaml.safe_load(f)

            metadata = SkillMetadata(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data["author"],
                category=data.get("category", "general"),
                tags=data.get("tags", []),
                dependencies=data.get("dependencies", []),
                python_version=data.get("python_version", ">=3.8"),
                homepage=data.get("homepage"),
                repository=data.get("repository"),
                license=data.get("license"),
            )

            return metadata

        except Exception as e:
            logger.error(f"Error loading skill metadata: {e}", exc_info=True)
            return None

    async def _install_dependencies(self, skill_dir: Path) -> bool:
        """
        Install skill dependencies.

        Args:
            skill_dir: Path to skill directory

        Returns:
            True if successful
        """
        requirements_file = skill_dir / "requirements.txt"

        if not requirements_file.exists():
            logger.info("No requirements.txt found, skipping dependency installation")
            return True

        logger.info("Installing skill dependencies...")

        try:
            # Install using pip
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_file),
                "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("Dependencies installed successfully")
                return True
            else:
                logger.error(f"Failed to install dependencies: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error installing dependencies: {e}", exc_info=True)
            return False

    def _load_skill_module(
        self,
        skill_dir: Path,
        metadata: SkillMetadata
    ) -> Optional[AgentSkill]:
        """
        Dynamically load skill module.

        Args:
            skill_dir: Path to skill directory
            metadata: Skill metadata

        Returns:
            AgentSkill instance or None if failed
        """
        skill_file = skill_dir / "skill.py"

        try:
            # Load module from file
            module_name = f"alpha_skill_{metadata.name.replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, skill_file)

            if not spec or not spec.loader:
                logger.error(f"Failed to load module spec: {skill_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find AgentSkill subclass in module
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, AgentSkill) and
                    attr is not AgentSkill):
                    skill_class = attr
                    break

            if not skill_class:
                logger.error(f"No AgentSkill subclass found in: {skill_file}")
                return None

            # Instantiate skill
            skill_instance = skill_class(metadata)
            logger.info(f"Loaded skill class: {skill_class.__name__}")

            return skill_instance

        except Exception as e:
            logger.error(f"Error loading skill module: {e}", exc_info=True)
            return None

    async def uninstall(self, skill_dir: Path):
        """
        Uninstall a skill.

        Args:
            skill_dir: Path to skill directory
        """
        logger.info(f"Uninstalling skill from: {skill_dir}")

        try:
            # Remove skill directory
            import shutil
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
                logger.info(f"Removed skill directory: {skill_dir}")

        except Exception as e:
            logger.error(f"Error uninstalling skill: {e}", exc_info=True)


# Fix: Add missing asyncio import
import asyncio
