"""
WebSocket Chat Routes - Real-time chat API
"""

import logging
import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from ..dependencies import get_engine, get_chat_handler
from ..chat_handler import ChatHandler

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Protocol:
    Client sends: {"type": "message", "content": "user message"}
    Server sends: {"type": "text", "content": "chunk"} (streaming)
                  {"type": "status", "content": "Thinking..."}
                  {"type": "skill_loaded", "name": "...", "score": 8.5}
                  {"type": "done"}
                  {"type": "error", "content": "error message"}

    Special commands:
    - {"type": "clear"} - Clear conversation history
    - {"type": "history"} - Get conversation history
    - {"type": "stats"} - Get session statistics
    """
    # Generate client ID (timestamp-based for simplicity)
    client_id = f"client_{datetime.now().timestamp()}"

    await manager.connect(websocket, client_id)

    # Get or create chat handler for this client
    # For now, we use a shared handler (single-user)
    # TODO: Support multiple users with separate handlers
    chat_handler = get_chat_handler()

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": "Connected to Alpha. Type your message to start chatting."
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            msg_type = data.get("type", "message")
            content = data.get("content", "")

            # Handle special commands
            if msg_type == "clear":
                await chat_handler.clear_history()
                await websocket.send_json({
                    "type": "system",
                    "content": "Conversation history cleared."
                })
                continue

            elif msg_type == "history":
                history = await chat_handler.get_conversation_history()
                await websocket.send_json({
                    "type": "history",
                    "content": history
                })
                continue

            elif msg_type == "stats":
                stats = chat_handler.get_stats()
                await websocket.send_json({
                    "type": "stats",
                    "content": stats
                })
                continue

            elif msg_type == "message":
                # Process chat message
                if not content or not content.strip():
                    await websocket.send_json({
                        "type": "error",
                        "content": "Empty message"
                    })
                    continue

                # Stream response chunks
                async for chunk in chat_handler.process_message(content, stream=True):
                    await websocket.send_json(chunk)

            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}"
            })
        except:
            pass


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Connection stats
    """
    return {
        "active_connections": len(manager.active_connections),
        "client_ids": list(manager.active_connections.keys())
    }
