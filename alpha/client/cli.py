"""
Alpha CLI Client

Connects to Alpha server via WebSocket for real-time chat.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from typing import Optional

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    print("Error: websockets library not installed")
    print("Install it with: pip install websockets")
    sys.exit(1)

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()
logger = logging.getLogger(__name__)


class AlphaClient:
    """
    CLI client for Alpha server.

    Connects via WebSocket for real-time streaming chat.
    """

    def __init__(self, server_url: str = "ws://localhost:8080/api/v1/ws/chat"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.running = False

    async def connect(self):
        """Connect to Alpha server."""
        try:
            console.print(f"[blue]Connecting to Alpha server at {self.server_url}...[/blue]")
            self.websocket = await websockets.connect(self.server_url)
            self.running = True
            console.print("[green]✓ Connected to Alpha[/green]")
            console.print("[dim]Type your message to start chatting. Type 'quit' or 'exit' to disconnect.[/dim]")
            console.print()
        except Exception as e:
            console.print(f"[bold red]Failed to connect to server:[/bold red] {e}")
            console.print()
            console.print("[yellow]Make sure Alpha server is running:[/yellow]")
            console.print("  sudo systemctl start alpha")
            console.print("  # or")
            console.print("  python -m alpha.main --daemon")
            sys.exit(1)

    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
            self.running = False
            console.print("\n[yellow]Disconnected from Alpha[/yellow]")

    async def send_message(self, content: str):
        """Send a message to server."""
        if not self.websocket:
            raise RuntimeError("Not connected to server")

        message = {
            "type": "message",
            "content": content
        }
        await self.websocket.send(json.dumps(message))

    async def receive_responses(self):
        """Receive and display streaming responses from server."""
        if not self.websocket:
            raise RuntimeError("Not connected to server")

        response_text = ""
        console.print("[bold blue]Alpha[/bold blue]: ", end="")

        async for message in self.websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "system":
                # System message (welcome, etc.)
                console.print(f"[dim]{data.get('content', '')}[/dim]")

            elif msg_type == "status":
                # Status update (Thinking..., etc.)
                console.print(f"[dim]{data.get('content', '')}[/dim]")

            elif msg_type == "skill_loaded":
                # Skill loaded notification
                skill_name = data.get("name", "")
                score = data.get("score", 0)
                console.print(f"[cyan]🎯 Using skill: {skill_name} (relevance: {score:.1f}/10)[/cyan]")

            elif msg_type == "text":
                # Streaming text chunk
                chunk = data.get("content", "")
                response_text += chunk
                console.print(chunk, end="", flush=True)

            elif msg_type == "done":
                # Response complete
                console.print()  # New line
                console.print()  # Spacing
                break

            elif msg_type == "error":
                # Error message
                error = data.get("content", "Unknown error")
                console.print(f"\n[bold red]Error:[/bold red] {error}")
                console.print()
                break

    async def chat_loop(self):
        """Main chat loop."""
        await self.connect()

        try:
            while self.running:
                # Get user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: Prompt.ask("\n[bold green]You[/bold green]")
                )

                # Handle special commands
                if user_input.lower() in ['quit', 'exit']:
                    break

                elif user_input.lower() == 'clear':
                    # Send clear command to server
                    await self.websocket.send(json.dumps({"type": "clear"}))
                    response = await self.websocket.recv()
                    data = json.loads(response)
                    console.print(f"[dim]{data.get('content', '')}[/dim]")
                    continue

                elif user_input.lower() == 'help':
                    self._show_help()
                    continue

                elif user_input.strip() == '':
                    continue

                # Send message and receive response
                await self.send_message(user_input)
                await self.receive_responses()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        except websockets.exceptions.ConnectionClosed:
            console.print("\n[bold red]Connection to server lost[/bold red]")
        finally:
            await self.disconnect()

    def _show_help(self):
        """Show help message."""
        help_text = """
# Alpha Client Commands

- **help** - Show this help message
- **clear** - Clear conversation history on server
- **quit/exit** - Disconnect from server

# Usage

Just type your message and press Enter. Alpha will respond with streaming output.

# Examples

```
You> What's the weather in Beijing?
Alpha> I'll search for the current weather in Beijing...

You> Help me schedule a task for tomorrow
Alpha> I can help you with that...
```
        """
        console.print(Markdown(help_text))


async def main():
    """Main entry point for CLI client."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Alpha CLI Client")
    parser.add_argument(
        '--server',
        type=str,
        default='ws://localhost:8080/api/v1/ws/chat',
        help='WebSocket server URL (default: ws://localhost:8080/api/v1/ws/chat)'
    )
    args = parser.parse_args()

    # Show welcome banner
    console.print(Panel.fit(
        "[bold cyan]Alpha AI Assistant - Client[/bold cyan]\n"
        "[dim]Connected to server for real-time chat[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Create and run client
    client = AlphaClient(server_url=args.server)
    await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
