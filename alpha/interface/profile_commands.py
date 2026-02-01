"""
Profile Management CLI Commands

Provides user commands to view and manage personalization:
- View current profile and learned preferences
- Override specific preferences manually
- Reset profile to defaults
- Export/import profile
- View preference learning history
- Enable/disable adaptive features

Usage:
    profile show                    # View current profile
    profile preferences             # View all preferences
    profile set verbosity concise   # Override verbosity
    profile set language mixed      # Override language
    profile set tone casual         # Override tone
    profile history                 # View learning history
    profile reset                   # Reset to defaults
    profile export <file>           # Export profile
    profile import <file>           # Import profile
    profile adaptive enable         # Enable adaptive features
    profile adaptive disable        # Disable adaptive features
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from alpha.personalization.profile_storage import ProfileStorage
from alpha.personalization.user_profile import UserProfile
from alpha.personalization.communication_adapter import CommunicationAdapter


class ProfileCommands:
    """
    CLI commands for profile management

    Provides user interface to view and manage personalization settings.
    """

    def __init__(
        self,
        profile_storage: ProfileStorage,
        profile_id: str = 'default'
    ):
        """
        Initialize profile commands

        Args:
            profile_storage: Storage for user profiles
            profile_id: ID of user profile to manage
        """
        self.storage = profile_storage
        self.profile_id = profile_id
        self.console = Console()

        # Load profile
        self.profile = self.storage.load_profile(profile_id)
        if not self.profile:
            # Create default profile
            self.profile = UserProfile(id=profile_id)
            self.storage.save_profile(self.profile)

        # Initialize adapter for statistics
        self.adapter = CommunicationAdapter(
            profile_storage=self.storage,
            profile_id=profile_id
        )

        # Adaptive features enabled by default
        self.adaptive_enabled = True

    def show_profile(self) -> str:
        """
        Display current profile summary

        Returns:
            Formatted profile summary
        """
        # Create rich table
        table = Table(title="User Profile", show_header=True)
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="green", width=30)
        table.add_column("Confidence", style="yellow", width=15)

        # Add rows
        table.add_row(
            "Profile ID",
            self.profile.id,
            "-"
        )
        table.add_row(
            "Verbosity Level",
            self.profile.verbosity_level,
            f"{self.profile.confidence_score:.2%}"
        )
        table.add_row(
            "Language",
            self.profile.language_preference,
            f"{self.profile.confidence_score:.2%}"
        )
        table.add_row(
            "Technical Level",
            self.profile.technical_level,
            "-"
        )
        table.add_row(
            "Tone",
            self.profile.tone_preference,
            "-"
        )
        table.add_row(
            "Active Hours",
            f"{self.profile.active_hours_start:02d}:00 - {self.profile.active_hours_end:02d}:00",
            "-"
        )
        table.add_row(
            "Timezone",
            self.profile.timezone,
            "-"
        )
        table.add_row(
            "Interactions",
            str(self.profile.interaction_count),
            "-"
        )
        table.add_row(
            "Adaptive Features",
            "Enabled" if self.adaptive_enabled else "Disabled",
            "-"
        )

        created = self.profile.created_at.strftime("%Y-%m-%d %H:%M") if self.profile.created_at else "Unknown"
        updated = self.profile.updated_at.strftime("%Y-%m-%d %H:%M") if self.profile.updated_at else "Unknown"

        table.add_row("Created", created, "-")
        table.add_row("Last Updated", updated, "-")

        self.console.print(table)
        return "Profile displayed"

    def show_preferences(self) -> str:
        """
        Display detailed preferences

        Returns:
            Formatted preferences summary
        """
        panel_content = []

        # Communication preferences
        panel_content.append("[bold cyan]Communication Preferences[/bold cyan]")
        panel_content.append(f"  Verbosity: [green]{self.profile.verbosity_level}[/green]")
        panel_content.append(f"  Language: [green]{self.profile.language_preference}[/green]")
        panel_content.append(f"  Technical Level: [green]{self.profile.technical_level}[/green]")
        panel_content.append(f"  Tone: [green]{self.profile.tone_preference}[/green]")

        # Task preferences
        panel_content.append("\n[bold cyan]Task Preferences[/bold cyan]")
        if self.profile.preferred_tools:
            tools = ", ".join(self.profile.preferred_tools[:5])
            panel_content.append(f"  Preferred Tools: [green]{tools}[/green]")
        else:
            panel_content.append("  Preferred Tools: [dim]Not learned yet[/dim]")

        if self.profile.frequent_tasks:
            tasks = ", ".join(self.profile.frequent_tasks[:5])
            panel_content.append(f"  Frequent Tasks: [green]{tasks}[/green]")
        else:
            panel_content.append("  Frequent Tasks: [dim]Not learned yet[/dim]")

        # Learning status
        panel_content.append("\n[bold cyan]Learning Status[/bold cyan]")
        panel_content.append(f"  Confidence: [green]{self.profile.confidence_score:.2%}[/green]")
        panel_content.append(f"  Interactions: [green]{self.profile.interaction_count}[/green]")

        panel = Panel(
            "\n".join(panel_content),
            title="User Preferences",
            border_style="blue"
        )

        self.console.print(panel)
        return "Preferences displayed"

    def set_preference(
        self,
        preference: str,
        value: str
    ) -> str:
        """
        Set a specific preference

        Args:
            preference: Preference name (verbosity, language, tone, technical)
            value: New value

        Returns:
            Success message
        """
        preference_lower = preference.lower()

        # Validate and set preference
        if preference_lower in ['verbosity', 'verbosity_level']:
            if value not in ['concise', 'balanced', 'detailed']:
                return f"Invalid verbosity value. Use: concise, balanced, or detailed"
            self.profile.verbosity_level = value

        elif preference_lower in ['language', 'lang']:
            if value not in ['en', 'zh', 'mixed']:
                return f"Invalid language value. Use: en, zh, or mixed"
            self.profile.language_preference = value

        elif preference_lower == 'tone':
            if value not in ['casual', 'professional', 'formal']:
                return f"Invalid tone value. Use: casual, professional, or formal"
            self.profile.tone_preference = value

        elif preference_lower in ['technical', 'technical_level']:
            if value not in ['beginner', 'intermediate', 'expert']:
                return f"Invalid technical level. Use: beginner, intermediate, or expert"
            self.profile.technical_level = value

        else:
            return f"Unknown preference: {preference}. Use: verbosity, language, tone, or technical"

        # Save updated profile
        self.profile.updated_at = datetime.now()
        self.storage.save_profile(self.profile)

        self.console.print(f"[green]✓[/green] Set {preference} to: [bold]{value}[/bold]")
        return f"Preference updated: {preference} = {value}"

    def show_history(self, limit: int = 20) -> str:
        """
        Display preference learning history

        Args:
            limit: Maximum number of history entries to show

        Returns:
            Success message
        """
        history = self.storage.get_preference_history(self.profile.id, limit=limit)

        if not history:
            self.console.print("[dim]No preference history available yet[/dim]")
            return "No history"

        # Create table
        table = Table(title="Preference Learning History", show_header=True)
        table.add_column("Date", style="cyan", width=16)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Change", style="green", width=30)
        table.add_column("Confidence", style="magenta", width=10)

        for entry in history:
            date_str = entry.learned_at.strftime("%Y-%m-%d %H:%M")
            change = f"{entry.old_value or 'None'} → {entry.new_value}"

            table.add_row(
                date_str,
                entry.preference_type,
                change,
                f"{entry.confidence:.2%}"
            )

        self.console.print(table)
        return f"Displayed {len(history)} history entries"

    def reset_profile(self, confirm: bool = False) -> str:
        """
        Reset profile to default settings

        Args:
            confirm: Confirmation flag (safety check)

        Returns:
            Success message
        """
        if not confirm:
            self.console.print(
                "[yellow]⚠[/yellow] This will reset all learned preferences. "
                "Use [bold]profile reset --confirm[/bold] to proceed."
            )
            return "Reset cancelled (needs confirmation)"

        # Reset to defaults
        self.profile.verbosity_level = 'balanced'
        self.profile.language_preference = 'en'
        self.profile.technical_level = 'intermediate'
        self.profile.tone_preference = 'professional'
        self.profile.preferred_tools = []
        self.profile.frequent_tasks = []
        self.profile.workflow_patterns = {}
        self.profile.interaction_count = 0
        self.profile.confidence_score = 0.0
        self.profile.updated_at = datetime.now()

        # Save
        self.storage.save_profile(self.profile)

        self.console.print("[green]✓[/green] Profile reset to default settings")
        return "Profile reset complete"

    def export_profile(self, file_path: str) -> str:
        """
        Export profile to JSON file

        Args:
            file_path: Path to export file

        Returns:
            Success message
        """
        try:
            # Convert profile to dict
            profile_data = {
                'id': self.profile.id,
                'created_at': self.profile.created_at.isoformat() if self.profile.created_at else None,
                'updated_at': self.profile.updated_at.isoformat() if self.profile.updated_at else None,
                'verbosity_level': self.profile.verbosity_level,
                'technical_level': self.profile.technical_level,
                'language_preference': self.profile.language_preference,
                'tone_preference': self.profile.tone_preference,
                'active_hours_start': self.profile.active_hours_start,
                'active_hours_end': self.profile.active_hours_end,
                'timezone': self.profile.timezone,
                'preferred_tools': self.profile.preferred_tools,
                'frequent_tasks': self.profile.frequent_tasks,
                'workflow_patterns': self.profile.workflow_patterns,
                'interaction_count': self.profile.interaction_count,
                'confidence_score': self.profile.confidence_score
            }

            # Write to file
            path = Path(file_path).expanduser()
            with open(path, 'w') as f:
                json.dump(profile_data, f, indent=2)

            self.console.print(f"[green]✓[/green] Profile exported to: {path}")
            return f"Profile exported to {file_path}"

        except Exception as e:
            error_msg = f"Export failed: {e}"
            self.console.print(f"[red]✗[/red] {error_msg}")
            return error_msg

    def import_profile(self, file_path: str) -> str:
        """
        Import profile from JSON file

        Args:
            file_path: Path to import file

        Returns:
            Success message
        """
        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return f"File not found: {file_path}"

            # Read file
            with open(path, 'r') as f:
                profile_data = json.load(f)

            # Update profile
            self.profile.verbosity_level = profile_data.get('verbosity_level', 'balanced')
            self.profile.technical_level = profile_data.get('technical_level', 'intermediate')
            self.profile.language_preference = profile_data.get('language_preference', 'en')
            self.profile.tone_preference = profile_data.get('tone_preference', 'professional')
            self.profile.active_hours_start = profile_data.get('active_hours_start', 9)
            self.profile.active_hours_end = profile_data.get('active_hours_end', 18)
            self.profile.timezone = profile_data.get('timezone', 'UTC')
            self.profile.preferred_tools = profile_data.get('preferred_tools', [])
            self.profile.frequent_tasks = profile_data.get('frequent_tasks', [])
            self.profile.workflow_patterns = profile_data.get('workflow_patterns', {})
            self.profile.confidence_score = profile_data.get('confidence_score', 0.0)
            self.profile.updated_at = datetime.now()

            # Save
            self.storage.save_profile(self.profile)

            self.console.print(f"[green]✓[/green] Profile imported from: {path}")
            return f"Profile imported from {file_path}"

        except Exception as e:
            error_msg = f"Import failed: {e}"
            self.console.print(f"[red]✗[/red] {error_msg}")
            return error_msg

    def set_adaptive(self, enabled: bool) -> str:
        """
        Enable or disable adaptive features

        Args:
            enabled: True to enable, False to disable

        Returns:
            Success message
        """
        self.adaptive_enabled = enabled
        status = "enabled" if enabled else "disabled"

        self.console.print(
            f"[green]✓[/green] Adaptive features [bold]{status}[/bold]"
        )

        return f"Adaptive features {status}"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get profile statistics

        Returns:
            Dict with statistics
        """
        stats = {
            'profile_id': self.profile.id,
            'interaction_count': self.profile.interaction_count,
            'confidence_score': self.profile.confidence_score,
            'preferences_learned': 0,
            'adaptive_enabled': self.adaptive_enabled
        }

        # Count learned preferences (non-default values)
        if self.profile.verbosity_level != 'balanced':
            stats['preferences_learned'] += 1
        if self.profile.language_preference != 'en':
            stats['preferences_learned'] += 1
        if self.profile.technical_level != 'intermediate':
            stats['preferences_learned'] += 1
        if self.profile.tone_preference != 'professional':
            stats['preferences_learned'] += 1

        return stats
