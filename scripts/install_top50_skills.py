#!/usr/bin/env python3
"""
Install Top 50 Most Popular Skills from skills.sh

Downloads the top 50 most installed skills to skills/
"""

import asyncio
import aiohttp
import logging
import sys
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_top_skills(limit=50):
    """Fetch top skills from skills.sh API"""
    api_url = "https://skills.sh/api/skills"

    logger.info(f"Fetching top {limit} skills from skills.sh...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    skills = data.get('skills', [])

                    # Sort by installs (popularity)
                    skills.sort(key=lambda s: s.get('installs', 0), reverse=True)

                    return skills[:limit]
                else:
                    logger.error(f"Failed to fetch skills: HTTP {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        return []


async def install_skill(skill_name, source, index, total):
    """Install a single skill using npx skills"""
    logger.info(f"[{index}/{total}] Installing: {skill_name}")

    try:
        # Check if already installed
        skill_path = Path(f"skills/{skill_name}")
        if skill_path.exists() and (skill_path / "SKILL.md").exists():
            logger.info(f"  ✓ Already installed: {skill_name}")
            return True

        # Install using npx skills
        cmd = ["npx", "skills", "add", source, "--skill", skill_name, "-y"]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"  ✓ Installed: {skill_name}")
            return True
        else:
            error = stderr.decode('utf-8') if stderr else "Unknown error"
            logger.warning(f"  ✗ Failed: {skill_name} - {error.strip()[:100]}")
            return False

    except Exception as e:
        logger.error(f"  ✗ Error installing {skill_name}: {e}")
        return False


async def main():
    # Check for --yes flag
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv

    print("=" * 80)
    print("Installing Top 50 Most Popular Skills")
    print("=" * 80)
    print()

    # Fetch top skills
    skills = await fetch_top_skills(limit=50)

    if not skills:
        logger.error("Failed to fetch skills from API")
        sys.exit(1)

    print(f"Found {len(skills)} popular skills")
    print()

    # Show top 10
    print("Top 10 Most Popular Skills:")
    print("-" * 80)
    for i, skill in enumerate(skills[:10], 1):
        name = skill['name']
        installs = skill.get('installs', 0)
        source = skill.get('topSource', 'N/A')
        print(f"{i:2}. {name:40} {installs:>8,} installs")
    print()

    # Confirm installation
    if not auto_yes:
        try:
            response = input(f"Install top 50 skills to skills/? (y/n): ").strip().lower()
            if response != 'y':
                print("Installation cancelled.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nInstallation cancelled.")
            sys.exit(0)

    print()
    print("Starting installation...")
    print("=" * 80)

    # Install skills
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, skill in enumerate(skills, 1):
        skill_name = skill['name']
        skill_source = skill.get('topSource', '')

        if not skill_source:
            logger.warning(f"[{i}/{len(skills)}] No source for: {skill_name}, skipping")
            skipped_count += 1
            continue

        result = await install_skill(skill_name, skill_source, i, len(skills))

        if result:
            success_count += 1
        else:
            failed_count += 1

        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    print()
    print("=" * 80)
    print("Installation Complete!")
    print("=" * 80)
    print(f"✓ Successfully installed: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"⊘ Skipped: {skipped_count}")
    print(f"📂 Skills directory: {Path('skills').absolute()}")
    print()
    print("Next steps:")
    print("  1. Run 'npx skills list' to verify installations")
    print("  2. Run './start.sh' to start Alpha")
    print("  3. Commit to git: git add skills && git commit -m 'Add top 50 skills'")
    print()


if __name__ == "__main__":
    asyncio.run(main())
