"""
WebSocket Power Streaming - Production
Production-ready implementation with:
- Connection manager for multi-client support
- Heartbeat/ping-pong for connection health
- Graceful degradation on hardware errors
- Backpressure handling
- Proper cleanup and reconnection support
"""

import asyncio
import logging
from typing import Set, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pymeasure.instruments.exfo import CTP10

from app.config import settings
from app.manager import CTP10Manager
from app.models import DetectorSnapshot

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


class PowerStreamManager:
    """
    Manages multiple WebSocket clients for power streaming.
    
    Features:
    - Multi-client support with independent streams
    - Automatic heartbeat
    - Graceful degradation on hardware errors
    - Connection health monitoring
    """
    
    def __init__(self):
        self.active_streams: dict[WebSocket, dict] = {}
        self._heartbeat_interval = 30  # seconds
        
    async def add_stream(
        self, 
        websocket: WebSocket, 
        module: int, 
        interval: float,
        manager: CTP10Manager
    ):
        """Register a new power stream."""
        await websocket.accept()
        
        self.active_streams[websocket] = {
            "module": module,
            "interval": interval,
            "manager": manager,
            "last_heartbeat": datetime.now(),
            "error_count": 0
        }
        
        logger.info(
            f"Power stream added: module={module}, interval={interval}s. "
            f"Active streams: {len(self.active_streams)}"
        )
        
    def remove_stream(self, websocket: WebSocket):
        """Remove a power stream."""
        if websocket in self.active_streams:
            del self.active_streams[websocket]
            logger.info(f"Power stream removed. Active streams: {len(self.active_streams)}")
            
    async def send_message(self, websocket: WebSocket, message: dict, timeout: float = 1.0):
        """
        Send message to a specific client with error handling and timeout.

        Args:
            websocket: WebSocket connection
            message: Message dict to send
            timeout: Timeout in seconds (default 1.0s for 10Hz streaming)

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            await asyncio.wait_for(websocket.send_json(message), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Client send timeout after {timeout}s, dropping frame")
            # Don't remove stream - just drop this frame and continue
            # For 10Hz power data, dropping occasional frames is acceptable
            return True
        except Exception as e:
            logger.warning(f"Send failed [{type(e).__name__}]: {e or 'connection closed'}")
            self.remove_stream(websocket)
            return False


# Global stream manager
stream_manager = PowerStreamManager()


async def _read_channel_power(
    ctp: CTP10, 
    module: int, 
    channel: int, 
    lock: asyncio.Lock
) -> tuple[int, float] | None:
    """Read power from a single channel with lock protection."""
    try:
        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)
            power = await asyncio.to_thread(lambda: detector.power)
        return (channel, power)
    except Exception as e:
        logger.warning(f"Failed to read channel {channel}: {e}")
        return None


async def _get_power_snapshot(
    manager: CTP10Manager,
    module: int,
    channels: list[int] = [1, 2, 3, 4]
) -> DetectorSnapshot | None:
    """
    Get a complete power snapshot for all channels.
    
    Returns None if hardware is unavailable (graceful degradation).
    """
    if not manager.is_connected:
        return None
        
    try:
        ctp = manager.ctp
        lock = manager.scpi_lock
        timestamp = asyncio.get_event_loop().time()
        
        # Read module properties
        async with lock:
            detector_ref = await asyncio.to_thread(ctp.detector, module=module, channel=1)
            wavelength_nm = await asyncio.to_thread(lambda: detector_ref.wavelength_nm)
            unit = await asyncio.to_thread(lambda: detector_ref.power_unit)
            
        # Read all channel powers
        tasks = [_read_channel_power(ctp, module, ch, lock) for ch in channels]
        results = await asyncio.gather(*tasks)
        
        powers = {ch: pwr for ch, pwr in results if results is not None}
        
        if len(powers) != len(channels):
            logger.warning(f"Incomplete channel read: {len(powers)}/{len(channels)}")
            return None
            
        return DetectorSnapshot(
            timestamp=timestamp,
            module=module,
            wavelength_nm=wavelength_nm,
            unit=unit,
            ch1_power=powers[1],
            ch2_power=powers[2],
            ch3_power=powers[3],
            ch4_power=powers[4],
        )
        
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        return None


@router.websocket("/power")
async def websocket_power_stream(
    websocket: WebSocket,
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    interval: float = Query(default=0.1, ge=0.01, le=10.0),
):
    """
    WebSocket power streaming with production features.
    
    Features:
    - Automatic reconnection support (client-side)
    - Heartbeat every 30s to detect stale connections
    - Graceful degradation on hardware errors
    - Multi-client support via ConnectionManager
    - Proper error recovery
    
    Message Types:
    ------------------
    1. "data": Power snapshot (normal operation)
       {
           "type": "data",
           "timestamp": 1234567890.123,
           "module": 4,
           "wavelength_nm": 1310.0,
           "unit": "dBm",
           "ch1_power": -17.85,
           ...
       }
       
    2. "heartbeat": Connection health check (every 30s)
       {
           "type": "heartbeat",
           "timestamp": "2024-01-01T12:00:00"
       }
       
    3. "error": Temporary error (hardware unavailable)
       {
           "type": "error",
           "message": "Not connected to CTP10",
           "timestamp": "2024-01-01T12:00:00",
           "recoverable": true
       }
       
    4. "reconnect": Request client reconnection
       {
           "type": "reconnect",
           "reason": "Server maintenance",
           "retry_after": 5
       }
    
    Client should implement exponential backoff reconnection.
    See frontend implementation for example.
    """
    manager: CTP10Manager = websocket.app.state.ctp10_manager
    
    await stream_manager.add_stream(websocket, module, interval, manager)
    
    last_heartbeat = datetime.now()
    error_count = 0
    max_errors = 10  # Disconnect after 10 consecutive errors
    
    try:
        while True:
            # Send heartbeat if needed
            if (datetime.now() - last_heartbeat).seconds >= 30:
                await stream_manager.send_message(websocket, {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "active_streams": len(stream_manager.active_streams)
                })
                last_heartbeat = datetime.now()
            
            # Get power snapshot
            snapshot = await _get_power_snapshot(manager, module)
            
            if snapshot is None:
                # Graceful degradation - send error but keep connection
                error_count += 1
                
                await stream_manager.send_message(websocket, {
                    "type": "error",
                    "message": "Hardware temporarily unavailable",
                    "timestamp": datetime.now().isoformat(),
                    "recoverable": True,
                    "error_count": error_count
                })
                
                # Disconnect if too many errors
                if error_count >= max_errors:
                    await stream_manager.send_message(websocket, {
                        "type": "reconnect",
                        "reason": "Too many consecutive errors",
                        "retry_after": 5
                    })
                    break
                    
                await asyncio.sleep(interval)
                continue
            
            # Reset error count on success
            error_count = 0
            
            # Send data to client
            success = await stream_manager.send_message(websocket, {
                "type": "data",
                **snapshot.model_dump()
            })
            
            if not success:
                break
                
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: module={module}")
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        stream_manager.remove_stream(websocket)


@router.websocket("/health")
async def websocket_health_check(websocket: WebSocket):
    """
    Lightweight health check WebSocket.
    
    Sends heartbeat every 10s.
    Used for connection health monitoring without data streaming overhead.
    """
    await websocket.accept()
    logger.info("Health check WebSocket connected")
    
    try:
        while True:
            # Send heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_streams": len(stream_manager.active_streams)
            })
            
            # Wait for next heartbeat or client message
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                # Normal - no client message, just continue heartbeat
                pass
                
    except WebSocketDisconnect:
        logger.info("Health check WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health check error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
