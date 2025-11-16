"""
GOLD STANDARD: WebSocket Health Check with Heartbeat
Industry-standard health monitoring endpoint for connection status
"""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import Set

router = APIRouter(prefix="/ws", tags=["WebSocket Health"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with heartbeat monitoring.
    
    Features:
    - Track all active connections
    - Broadcast messages to all clients
    - Automatic heartbeat/ping-pong
    - Stale connection cleanup
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._heartbeat_task = None
        
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total active: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")
        
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send message to client: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                disconnected.add(connection)
                
        # Clean up failed connections
        for conn in disconnected:
            self.disconnect(conn)
            
    async def heartbeat_loop(self, interval: int = 30):
        """
        Send periodic heartbeat to detect stale connections.
        
        WebSocket ping/pong is automatic in FastAPI/Starlette,
        but we send explicit heartbeat messages for application-level monitoring.
        """
        while True:
            try:
                await asyncio.sleep(interval)
                await self.broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": len(self.active_connections)
                })
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/health")
async def websocket_health_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for health monitoring with heartbeat.
    
    Sends periodic status updates and heartbeat messages.
    Clients should implement reconnection logic with exponential backoff.
    
    Message types:
    - "heartbeat": Periodic ping (every 30s)
    - "status": Connection status update
    - "error": Error notification
    
    Example client usage (see frontend implementation below).
    """
    await manager.connect(websocket)
    
    try:
        # Send initial status
        await manager.send_personal({
            "type": "status",
            "connected": True,
            "timestamp": datetime.now().isoformat(),
            "message": "WebSocket health monitor connected"
        }, websocket)
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (can be used for client-initiated ping)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Echo back or handle client messages
                if data == "ping":
                    await manager.send_personal({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except asyncio.TimeoutError:
                # No message received, but connection is still alive
                # Send heartbeat
                await manager.send_personal({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)


# Start heartbeat loop when router is included
@router.on_event("startup")
async def start_heartbeat():
    """Start the global heartbeat loop."""
    asyncio.create_task(manager.heartbeat_loop(interval=30))
