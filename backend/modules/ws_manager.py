"""
WebSocket manager for spectator connections.

This module handles real-time communication with frontend clients,
broadcasting game state updates, phase changes, and round results.
"""

import logging
import json
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for spectators."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Spectator connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Spectator disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, data: dict) -> None:
        """
        Broadcast JSON data to all connected spectators.

        Args:
            data: Dictionary to serialize and send to all clients
        """
        if not self.active_connections:
            return

        message = json.dumps(data, default=str)
        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to spectator: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for conn in dead_connections:
            self.disconnect(conn)

        if dead_connections:
            logger.info(f"Removed {len(dead_connections)} dead connections")

    @property
    def connection_count(self) -> int:
        """Get current number of active connections."""
        return len(self.active_connections)
