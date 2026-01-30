"""
Skill Loader

Loads SKILL.md files and extracts their content for use as context.
"""

import logging
import yaml
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Loads and parses SKILL.md files.

    SKILL.md format:
    ---
    name: skill-name
    description: Skill description
    ---

    # Skill Content
    Markdown instructions...
    """

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or Path("skills")

    def load_skill(self, skill_name: str) -> Optional[Dict[str, any]]:
        """
        Load a skill's SKILL.md file.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with metadata and content, or None if not found
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"

        if not skill_path.exists():
            logger.warning(f"Skill file not found: {skill_path}")
            return None

        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter and content
            metadata, instructions = self._parse_skill_md(content)

            return {
                "name": skill_name,
                "metadata": metadata,
                "instructions": instructions,
                "full_content": content,
                "path": str(skill_path)
            }

        except Exception as e:
            logger.error(f"Error loading skill '{skill_name}': {e}", exc_info=True)
            return None

    def _parse_skill_md(self, content: str) -> tuple:
        """
        Parse SKILL.md file into frontmatter and instructions.

        Args:
            content: Full file content

        Returns:
            Tuple of (metadata dict, instructions string)
        """
        # Check if content starts with frontmatter
        if not content.startswith('---'):
            return {}, content

        # Find end of frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        try:
            # Parse YAML frontmatter
            metadata = yaml.safe_load(parts[1])
            instructions = parts[2].strip()
            return metadata or {}, instructions
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            return {}, content

    def get_skill_context(self, skill_name: str) -> Optional[str]:
        """
        Get skill content formatted for LLM context.

        Args:
            skill_name: Name of the skill

        Returns:
            Formatted context string, or None if skill not found
        """
        skill = self.load_skill(skill_name)
        if not skill:
            return None

        metadata = skill.get('metadata', {})
        instructions = skill.get('instructions', '')

        # Format for LLM context
        context = f"""# ACTIVE SKILL: {skill_name}

**Description**: {metadata.get('description', 'No description')}

**Instructions**:
{instructions}

---
You should follow the instructions above when responding to the user's request.
"""
        return context

    def list_available_skills(self) -> list:
        """List all available skills in the skills directory (lightweight scan)."""
        if not self.skills_dir.exists():
            return []

        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                # Lazy load: only load metadata when needed
                # For now, just return basic info
                try:
                    # Quick metadata extraction (first few lines only)
                    skill_file = item / "SKILL.md"
                    description = self._quick_extract_description(skill_file)
                    skills.append({
                        'name': item.name,
                        'description': description
                    })
                except Exception as e:
                    logger.warning(f"Failed to scan skill {item.name}: {e}")
                    skills.append({
                        'name': item.name,
                        'description': 'No description'
                    })

        return skills

    def _quick_extract_description(self, skill_file: Path) -> str:
        """Quick extraction of description from SKILL.md (first 20 lines only)."""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                lines = []
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    if 'description:' in line.lower():
                        # Extract description value
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('"\'')
            return 'No description'
        except Exception:
            return 'No description'
