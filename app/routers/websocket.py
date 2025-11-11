"""WebSocket endpoints for real-time CTP10 data streaming."""

import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10_manager
from app.manager import CTP10Manager
from app.config import settings
from app.models import DetectorSnapshot

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


async def _read_channel_power(ctp: CTP10, module: int, channel: int, lock: asyncio.Lock) -> tuple[int, float] | None:
    """
    Read power from a single channel (thread-safe and SCPI-safe).

    The lock ensures SCPI communication is serialized to prevent response mixing.

    Returns:
        Tuple of (channel, power) or None if read failed
    """
    try:
        async with lock:
            # All SCPI communication happens within the lock
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)
            power = await asyncio.to_thread(lambda: detector.power)

        return (channel, power)
    except Exception as e:
        logger.warning(f"Failed to read channel {channel}: {e}")
        return None


@router.websocket("/power")
async def websocket_power_stream(
    websocket: WebSocket,
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    interval: float = Query(default=0.1, ge=0.01, le=10.0, description="Update interval in seconds"),
):
    """
    WebSocket endpoint for streaming all 4 detector channel power readings.

    Streams snapshots of channels 1-4 at the requested interval.
    All channels are read with SCPI lock protection for data integrity.

    Parameters:
    - module: Detector module number (1-20, default: 4)
    - interval: Update interval in seconds (0.01-10.0, default: 0.1)

    Message format matches GET /detector/snapshot (JSON):
    {
        "timestamp": 1234567890.123,
        "module": 4,
        "wavelength_nm": 1310.0,
        "unit": "dBm",
        "ch1_power": -17.85,
        "ch2_power": -21.56,
        "ch3_power": 6.94,
        "ch4_power": -60.12
    }

    Channel mapping (IL RL OPM2 module):
    - ch1_power: Channel 1 (IN1)
    - ch2_power: Channel 2 (IN2)
    - ch3_power: Channel 3 (TLS IN)
    - ch4_power: Channel 4 (OUT TO DUT)

    Example usage (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8002/ws/power?module=4&interval=0.1');
    ws.onmessage = (event) => {
        const snapshot = JSON.parse(event.data);
        console.log(`IN1: ${snapshot.ch1_power} ${snapshot.unit}`);
        console.log(`IN2: ${snapshot.ch2_power} ${snapshot.unit}`);
        console.log(`TLS IN: ${snapshot.ch3_power} ${snapshot.unit}`);
        console.log(`OUT TO DUT: ${snapshot.ch4_power} ${snapshot.unit}`);
    };
    ```
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: module={module}, interval={interval}")

    # Get manager from app state
    manager: CTP10Manager = websocket.app.state.ctp10_manager

    # Always read channels 1-4
    channels = [1, 2, 3, 4]

    try:
        while True:
            # Check if still connected to CTP10
            if not manager.is_connected:
                await websocket.send_json({
                    "error": "Not connected to CTP10",
                    "timestamp": asyncio.get_event_loop().time()
                })
                await asyncio.sleep(interval)
                continue

            ctp = manager.ctp
            lock = manager.scpi_lock

            # Read module-level properties once (wavelength and unit are shared by all channels)
            timestamp = asyncio.get_event_loop().time()

            try:
                async with lock:
                    detector_ref = await asyncio.to_thread(ctp.detector, module=module, channel=1)
                    wavelength_nm = await asyncio.to_thread(lambda: detector_ref.wavelength_nm)
                    unit = await asyncio.to_thread(lambda: detector_ref.power_unit)
            except Exception as e:
                logger.warning(f"Failed to read module properties: {e}")
                await asyncio.sleep(interval)
                continue

            # Read all 4 channel powers concurrently with lock protection
            # The lock serializes SCPI communication to prevent response mixing,
            # while asyncio.gather() provides concurrent task structure
            tasks = [_read_channel_power(ctp, module, ch, lock) for ch in channels]
            results = await asyncio.gather(*tasks)

            # Build power dict
            powers = {ch: pwr for ch, pwr in results if results is not None}

            if len(powers) != 4:
                logger.warning(f"Failed to read all channels: got {len(powers)}/4")
                await asyncio.sleep(interval)
                continue

            # Send snapshot to client (matches GET /detector/snapshot format)
            snapshot = DetectorSnapshot(
                timestamp=timestamp,
                module=module,
                wavelength_nm=wavelength_nm,
                unit=unit,
                ch1_power=powers[1],
                ch2_power=powers[2],
                ch3_power=powers[3],
                ch4_power=powers[4],
            )
            await websocket.send_json(snapshot.model_dump())

            # Wait for next interval
            await asyncio.sleep(interval)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason=str(e))
