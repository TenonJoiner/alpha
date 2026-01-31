"""
CLI Workflow Commands

Provides command-line interface for workflow management.
"""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from alpha.workflow import (
    WorkflowLibrary,
    WorkflowExecutor,
    WorkflowBuilder,
    WorkflowDefinition,
)


class WorkflowCLI:
    """
    CLI handler for workflow commands

    Provides user-friendly interface for:
    - Listing workflows
    - Running workflows
    - Creating workflows
    - Managing workflows
    """

    def __init__(
        self,
        library: Optional[WorkflowLibrary] = None,
        executor: Optional[WorkflowExecutor] = None,
        builder: Optional[WorkflowBuilder] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize workflow CLI

        Args:
            library: WorkflowLibrary instance
            executor: WorkflowExecutor instance
            builder: WorkflowBuilder instance
            console: Rich Console instance
        """
        self.library = library or WorkflowLibrary()
        self.executor = executor or WorkflowExecutor()
        self.builder = builder or WorkflowBuilder()
        self.console = console or Console()

    async def handle_command(self, command: str) -> bool:
        """
        Handle workflow command

        Args:
            command: Command string (after 'workflow' prefix)

        Returns:
            True if command was handled, False otherwise
        """
        parts = command.strip().split(maxsplit=1)
        if not parts:
            self.show_help()
            return True

        subcommand = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if subcommand == "list":
            await self.list_workflows(args)
        elif subcommand == "show":
            await self.show_workflow(args)
        elif subcommand == "run":
            await self.run_workflow(args)
        elif subcommand == "create":
            await self.create_workflow(args)
        elif subcommand == "delete":
            await self.delete_workflow(args)
        elif subcommand == "history":
            await self.show_history(args)
        elif subcommand == "export":
            await self.export_workflow(args)
        elif subcommand == "import":
            await self.import_workflow(args)
        elif subcommand == "help":
            self.show_help()
        else:
            self.console.print(
                f"[red]Unknown workflow command:[/red] {subcommand}"
            )
            self.show_help()

        return True

    async def list_workflows(self, args: str):
        """List all workflows"""
        # Parse arguments
        tags = None
        search = None

        if args:
            # Simple parsing - can be enhanced
            if args.startswith("--tags"):
                tags = args.split("--tags")[1].strip().split(",")
            elif args.startswith("--search"):
                search = args.split("--search")[1].strip()

        workflows = self.library.list(tags=tags, search=search)

        if not workflows:
            self.console.print("[yellow]No workflows found[/yellow]")
            return

        table = Table(title="📋 Workflows")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="green")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="magenta")
        table.add_column("Steps", justify="right", style="blue")
        table.add_column("Executions", justify="right", style="yellow")

        for workflow in workflows:
            tags_str = ", ".join(workflow.tags) if workflow.tags else "-"
            table.add_row(
                workflow.name,
                workflow.version,
                workflow.description[:50] + "..."
                if len(workflow.description) > 50
                else workflow.description,
                tags_str,
                str(len(workflow.steps)),
                "-",  # TODO: Get execution count from library
            )

        self.console.print(table)

    async def show_workflow(self, name: str):
        """Show workflow details"""
        if not name:
            self.console.print("[red]Error:[/red] Workflow name required")
            return

        workflow = self.library.get(name.strip())

        if not workflow:
            self.console.print(f"[red]Workflow not found:[/red] {name}")
            return

        # Display workflow details
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]{workflow.name}[/bold cyan] v{workflow.version}",
                title="Workflow",
                expand=False,
            )
        )

        self.console.print(f"\n[bold]Description:[/bold] {workflow.description}")
        self.console.print(f"[bold]Author:[/bold] {workflow.author}")
        self.console.print(f"[bold]Tags:[/bold] {', '.join(workflow.tags)}")
        self.console.print(f"[bold]Created:[/bold] {workflow.created_at}")

        # Parameters
        if workflow.parameters:
            self.console.print("\n[bold]Parameters:[/bold]")
            for param in workflow.parameters:
                default_str = (
                    f" (default: {param.default})" if param.default else ""
                )
                required_str = " [red]*required*[/red]" if param.required else ""
                self.console.print(
                    f"  • {param.name} ({param.type.value}){default_str}{required_str}"
                )
                if param.description:
                    self.console.print(f"    {param.description}")

        # Steps
        self.console.print("\n[bold]Steps:[/bold]")
        for i, step in enumerate(workflow.steps, 1):
            deps_str = (
                f" (depends on: {', '.join(step.depends_on)})"
                if step.depends_on
                else ""
            )
            self.console.print(f"  {i}. [{step.id}] {step.tool}.{step.action}{deps_str}")
            self.console.print(
                f"     Error handling: {step.on_error.value}"
            )

        # Triggers
        if workflow.triggers:
            self.console.print("\n[bold]Triggers:[/bold]")
            for trigger in workflow.triggers:
                self.console.print(f"  • {trigger.type.value}")
                if trigger.config:
                    for key, value in trigger.config.items():
                        self.console.print(f"    {key}: {value}")

    async def run_workflow(self, args: str):
        """Run a workflow"""
        if not args:
            self.console.print("[red]Error:[/red] Workflow name required")
            return

        # Parse name and parameters
        parts = args.split()
        name = parts[0]

        # Parse parameters (key=value format)
        parameters = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                # Try to infer type
                if value.isdigit():
                    parameters[key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    parameters[key] = float(value)
                elif value.lower() in ["true", "false"]:
                    parameters[key] = value.lower() == "true"
                else:
                    parameters[key] = value

        # Get workflow
        workflow = self.library.get(name)

        if not workflow:
            self.console.print(f"[red]Workflow not found:[/red] {name}")
            return

        # Execute workflow
        self.console.print(f"\n[cyan]Executing workflow:[/cyan] [bold]{name}[/bold]")

        if parameters:
            self.console.print("[dim]Parameters:[/dim]")
            for key, value in parameters.items():
                self.console.print(f"  • {key} = {value}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Executing...", total=None)

            try:
                result = await self.executor.execute(workflow, parameters)

                progress.update(task, completed=True)

                # Show results
                self.console.print()
                if result.status == "completed":
                    self.console.print("[green]✓[/green] Workflow completed successfully!")
                    self.console.print(
                        f"  • Steps completed: {result.steps_completed}/{result.steps_total}"
                    )
                    self.console.print(
                        f"  • Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s"
                    )

                    if result.outputs:
                        self.console.print("\n[bold]Outputs:[/bold]")
                        for key, value in result.outputs.items():
                            self.console.print(f"  • {key}: {value}")

                elif result.status == "partial":
                    self.console.print(
                        "[yellow]⚠[/yellow] Workflow completed with errors"
                    )
                    self.console.print(
                        f"  • Steps completed: {result.steps_completed}/{result.steps_total}"
                    )
                    self.console.print(f"  • Steps failed: {result.steps_failed}")

                else:
                    self.console.print("[red]✗[/red] Workflow failed")
                    self.console.print(f"  • Error: {result.error}")

                # Log execution
                self.library.log_execution(
                    workflow_id=workflow.id,
                    execution_id=result.execution_id,
                    parameters=parameters,
                    status=result.status,
                    started_at=result.started_at,
                    completed_at=result.completed_at,
                    result=result.outputs,
                    error=result.error,
                )

            except Exception as e:
                progress.update(task, completed=True)
                self.console.print(f"\n[red]Error executing workflow:[/red] {e}")

    async def create_workflow(self, args: str):
        """Create a new workflow"""
        # Simple interactive creation
        self.console.print("\n[bold cyan]Create New Workflow[/bold cyan]")

        from rich.prompt import Prompt

        name = Prompt.ask("Workflow name")
        description = Prompt.ask("Description", default="")
        tags_str = Prompt.ask("Tags (comma-separated)", default="")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Collect steps
        steps = []
        step_count = 1

        self.console.print("\n[bold]Define Steps[/bold] (press Enter with no tool to finish)")

        while True:
            self.console.print(f"\n[cyan]Step {step_count}:[/cyan]")
            tool = Prompt.ask("  Tool name", default="")

            if not tool:
                break

            action = Prompt.ask("  Action", default="execute")
            on_error = Prompt.ask(
                "  Error handling", choices=["abort", "retry", "continue"], default="abort"
            )

            steps.append(
                {
                    "id": f"step_{step_count}",
                    "tool": tool,
                    "action": action,
                    "parameters": {},
                    "on_error": on_error,
                }
            )

            step_count += 1

        if not steps:
            self.console.print("[yellow]No steps defined. Workflow not created.[/yellow]")
            return

        # Build and save workflow
        workflow = self.builder.build(
            name=name, description=description, steps=steps, tags=tags
        )

        self.library.save(workflow)

        self.console.print(
            f"\n[green]✓[/green] Workflow '[bold]{name}[/bold]' created successfully!"
        )

    async def delete_workflow(self, name: str):
        """Delete a workflow"""
        if not name:
            self.console.print("[red]Error:[/red] Workflow name required")
            return

        name = name.strip()

        if not self.library.exists(name):
            self.console.print(f"[red]Workflow not found:[/red] {name}")
            return

        from rich.prompt import Confirm

        if Confirm.ask(f"Delete workflow '[bold]{name}[/bold]'?", default=False):
            self.library.delete(name)
            self.console.print(f"[green]✓[/green] Workflow deleted")
        else:
            self.console.print("[yellow]Cancelled[/yellow]")

    async def show_history(self, name: str):
        """Show workflow execution history"""
        if not name:
            self.console.print("[red]Error:[/red] Workflow name required")
            return

        name = name.strip()
        history = self.library.get_execution_history(name, limit=10)

        if not history:
            self.console.print(f"[yellow]No execution history for workflow:[/yellow] {name}")
            return

        table = Table(title=f"📜 Execution History: {name}")
        table.add_column("Execution ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="white")
        table.add_column("Duration", style="yellow")

        for execution in history:
            # Calculate duration if both timestamps exist
            duration = "-"
            if execution.get("started_at") and execution.get("completed_at"):
                from datetime import datetime

                start = datetime.fromisoformat(execution["started_at"])
                end = datetime.fromisoformat(execution["completed_at"])
                duration = f"{(end - start).total_seconds():.2f}s"

            status_color = (
                "green"
                if execution["status"] == "completed"
                else "red" if execution["status"] == "failed" else "yellow"
            )

            table.add_row(
                execution["id"][:8],
                f"[{status_color}]{execution['status']}[/{status_color}]",
                execution["started_at"],
                duration,
            )

        self.console.print(table)

    async def export_workflow(self, args: str):
        """Export workflow to file"""
        parts = args.split()
        if len(parts) < 1:
            self.console.print("[red]Error:[/red] Workflow name required")
            return

        name = parts[0]
        file_path = parts[1] if len(parts) > 1 else f"{name}.json"

        if self.library.export_workflow(name, file_path):
            self.console.print(f"[green]✓[/green] Workflow exported to: {file_path}")
        else:
            self.console.print(f"[red]Error exporting workflow:[/red] {name}")

    async def import_workflow(self, file_path: str):
        """Import workflow from file"""
        if not file_path:
            self.console.print("[red]Error:[/red] File path required")
            return

        workflow = self.library.import_workflow(file_path.strip())

        if workflow:
            self.console.print(
                f"[green]✓[/green] Workflow '[bold]{workflow.name}[/bold]' imported successfully"
            )
        else:
            self.console.print(f"[red]Error importing workflow from:[/red] {file_path}")

    def show_help(self):
        """Show workflow command help"""
        help_text = """
[bold cyan]Workflow Commands[/bold cyan]

[bold]List workflows:[/bold]
  workflow list [--tags TAG1,TAG2] [--search QUERY]

[bold]Show workflow details:[/bold]
  workflow show <name>

[bold]Run workflow:[/bold]
  workflow run <name> [param1=value1] [param2=value2] ...

[bold]Create workflow:[/bold]
  workflow create

[bold]Delete workflow:[/bold]
  workflow delete <name>

[bold]Show execution history:[/bold]
  workflow history <name>

[bold]Export workflow:[/bold]
  workflow export <name> [file_path]

[bold]Import workflow:[/bold]
  workflow import <file_path>

[bold]Examples:[/bold]
  workflow list --tags production
  workflow show "Deploy Pipeline"
  workflow run "Deploy Pipeline" environment=staging branch=main
  workflow create
  workflow export "Deploy Pipeline" deploy.json
"""

        self.console.print(Panel(help_text, title="Workflow Help", border_style="cyan"))
