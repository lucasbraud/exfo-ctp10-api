"""Detector channel operations for CTP10."""

import asyncio
import io
import logging
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pymeasure.instruments.exfo import CTP10

from app.config import settings
from app.dependencies import get_ctp10, get_ctp10_manager
from app.manager import CTP10Manager
from app.models import DetectorConfig, DetectorSnapshot, TraceDataResponse, TraceMetadata, StabilizationConfig

router = APIRouter(prefix="/detector", tags=["Detector"])
logger = logging.getLogger(__name__)


async def _read_single_channel_power(ctp: CTP10, module: int, channel: int, lock: asyncio.Lock) -> tuple[int, float] | None:
    """
    Helper function to read power from a single channel (thread-safe and SCPI-safe).

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


@router.get("/snapshot", response_model=DetectorSnapshot)
async def get_detector_snapshot(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
):
    """
    Get a snapshot of all 4 detector channels at once.

    Returns a time-synchronized reading of all channels with module-level metadata.
    This is the primary endpoint for monitoring detector power.

    Channel mapping (IL RL OPM2 module):
    - ch1_power: Channel 1 (IN1)
    - ch2_power: Channel 2 (IN2)
    - ch3_power: Channel 3 (TLS IN)
    - ch4_power: Channel 4 (OUT TO DUT)

    Example response:
    {
        "timestamp": 1609175.828,
        "module": 4,
        "wavelength_nm": 1310.0,
        "unit": "dBm",
        "ch1_power": -17.85,
        "ch2_power": -21.56,
        "ch3_power": 6.94,
        "ch4_power": -60.12
    }
    """
    try:
        lock = manager.scpi_lock
        timestamp = asyncio.get_event_loop().time()

        # Read module-level properties once (shared by all channels)
        async with lock:
            detector_ref = await asyncio.to_thread(ctp.detector, module=module, channel=1)
            wavelength_nm = await asyncio.to_thread(lambda: detector_ref.wavelength_nm)
            unit = await asyncio.to_thread(lambda: detector_ref.power_unit)

        # Read all 4 channels concurrently with lock protection
        channels = [1, 2, 3, 4]
        tasks = [_read_single_channel_power(ctp, module, ch, lock) for ch in channels]
        results = await asyncio.gather(*tasks)

        # Build power dict
        powers = {ch: pwr for ch, pwr in results if results is not None}

        if len(powers) != 4:
            missing = set(channels) - set(powers.keys())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read all channels. Missing: {missing}"
            )

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detector snapshot: {str(e)}")


@router.get("/config")
async def get_detector_config(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Get detector configuration (units, resolution)."""
    try:
        logger.debug(f"Getting detector config for module={module}, channel={channel}")
        lock = manager.scpi_lock

        # All SCPI I/O must be in asyncio.to_thread() and inside lock
        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)
            logger.debug(f"Detector object created: {detector}")

            # Try to get each property, use None if not available
            config = {
                "module": module,
                "channel": channel,
            }

            try:
                config["power_unit"] = await asyncio.to_thread(lambda: detector.power_unit)
                logger.debug(f"Got power_unit: {config['power_unit']}")
            except Exception as e:
                logger.warning(f"Failed to get power_unit: {e}")
                config["power_unit"] = None

            try:
                config["spectral_unit"] = await asyncio.to_thread(lambda: detector.spectral_unit)
                logger.debug(f"Got spectral_unit: {config['spectral_unit']}")
            except Exception as e:
                logger.warning(f"Failed to get spectral_unit: {e}")
                config["spectral_unit"] = None

            try:
                config["resolution_pm"] = await asyncio.to_thread(lambda: ctp.resolution_pm)
                logger.debug(f"Got resolution_pm: {config['resolution_pm']}")
            except Exception as e:
                logger.warning(f"Failed to get resolution_pm: {e}")
                config["resolution_pm"] = None

        return config
    except Exception as e:
        logger.error(f"Failed to get detector config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/config")
async def set_detector_config(
    config: DetectorConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Set detector configuration (units, resolution)."""
    try:
        lock = manager.scpi_lock

        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)

            if config.power_unit is not None:
                await asyncio.to_thread(setattr, detector, 'power_unit', config.power_unit)

            if config.spectral_unit is not None:
                await asyncio.to_thread(setattr, detector, 'spectral_unit', config.spectral_unit)

            if config.resolution_pm is not None:
                # Resolution is a global setting on the CTP10
                await asyncio.to_thread(setattr, ctp, 'resolution_pm', config.resolution_pm)

        return {
            "success": True,
            "message": f"Detector {module}/{channel} configured successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


# ============================================================================
# Stabilization (Device-Level Configuration)
# ============================================================================


@router.get("/stabilization")
async def get_stabilization(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """Get laser stabilization settings (output state, duration)."""
    try:
        lock = manager.scpi_lock

        async with lock:
            output, duration = await asyncio.to_thread(lambda: ctp.stabilization)

        # Convert integer to boolean (0=False, 1=True)
        output_bool = bool(output)
        return {
            "output": output_bool,
            "duration_seconds": duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stabilization: {str(e)}")


@router.post("/stabilization")
async def set_stabilization(
    config: StabilizationConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """Set laser stabilization settings."""
    if not (0 <= config.duration_seconds <= 60):
        raise HTTPException(status_code=400, detail="Duration must be 0-60 seconds")

    try:
        lock = manager.scpi_lock

        # Convert boolean to integer (0 or 1) for the device
        output_int = 1 if config.output else 0

        async with lock:
            await asyncio.to_thread(setattr, ctp, 'stabilization', (output_int, config.duration_seconds))

        return {
            "success": True,
            "output": config.output,
            "duration_seconds": config.duration_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set stabilization: {str(e)}")


@router.post("/reference")
async def create_reference(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Create reference trace for detector channel."""
    try:
        lock = manager.scpi_lock

        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)
            await asyncio.to_thread(detector.create_reference)

        return {
            "success": True,
            "message": f"Reference created for detector {module}/{channel}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create reference: {str(e)}")


@router.get("/trace/metadata", response_model=TraceMetadata)
async def get_trace_metadata(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
    trace_type: int = Query(default=1, ge=1, le=23, description="1=TF live, 11=Raw live, 12=Raw ref, 13=Quick ref"),
):
    """
    Get trace metadata without retrieving the full data.

    Use this to check trace information before downloading large datasets.
    """
    try:
        lock = manager.scpi_lock

        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)
            num_points = await asyncio.to_thread(detector.length, trace_type=trace_type)
            unit = await asyncio.to_thread(lambda: detector.power_unit)

        return TraceMetadata(
            module=module,
            channel=channel,
            trace_type=trace_type,
            num_points=num_points,
            unit=unit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


@router.get("/trace/data", response_model=TraceDataResponse)
async def get_trace_data_json(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
    trace_type: int = Query(default=1, ge=1, le=23),
):
    """
    Get trace data in JSON format.

    Warning: For large traces (~940k points), this can be 3-4MB of JSON.
    Consider using /trace/binary for better performance.
    """
    try:
        lock = manager.scpi_lock

        # All SCPI I/O inside lock
        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)

            # Get metadata
            num_points = await asyncio.to_thread(detector.length, trace_type=trace_type)
            unit = await asyncio.to_thread(lambda: detector.power_unit)

            # Get trace data (binary format for speed, convert to lists for JSON)
            wavelengths_m = await asyncio.to_thread(
                detector.get_data_x, trace_type=trace_type, unit='M', format='BIN'
            )
            values = await asyncio.to_thread(
                detector.get_data_y, trace_type=trace_type, unit='DB', format='BIN'
            )

        # Data processing (outside lock - no SCPI I/O)
        wavelengths_nm = (wavelengths_m * 1e9).tolist()
        values_list = values.tolist()

        metadata = TraceMetadata(
            module=module,
            channel=channel,
            trace_type=trace_type,
            num_points=num_points,
            unit=unit
        )

        return TraceDataResponse(
            metadata=metadata,
            wavelengths=wavelengths_nm,
            values=values_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trace data: {str(e)}")


@router.get("/trace/binary")
async def get_trace_data_binary(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
    trace_type: int = Query(default=1, ge=1, le=23),
):
    """
    Get trace data in binary NPY format.

    Returns a numpy array file containing both wavelengths and values.
    Much more efficient than JSON for large datasets (~940k points).

    Use numpy.load() to read the returned file:
    ```python
    response = requests.get("/detector/trace/binary?module=4&channel=1")
    with open("trace.npy", "wb") as f:
        f.write(response.content)
    data = np.load("trace.npy")
    wavelengths = data['wavelengths']
    values = data['values']
    ```
    """
    try:
        lock = manager.scpi_lock

        # All SCPI I/O must be in asyncio.to_thread() and inside lock
        async with lock:
            detector = await asyncio.to_thread(ctp.detector, module=module, channel=channel)

            # Get trace data in binary format
            wavelengths_m = await asyncio.to_thread(
                detector.get_data_x, trace_type=trace_type, unit='M', format='BIN'
            )
            values = await asyncio.to_thread(
                detector.get_data_y, trace_type=trace_type, unit='DB', format='BIN'
            )

        # Data processing (outside lock - no SCPI I/O, CPU-bound work)
        # Convert meters to nanometers
        wavelengths_nm = wavelengths_m * 1e9

        # Create structured array - more efficient than list(zip(...))
        data = np.core.records.fromarrays(
            [wavelengths_nm, values],
            dtype=[('wavelengths', 'f8'), ('values', 'f8')]
        )

        # Save to bytes buffer
        buffer = io.BytesIO()
        np.save(buffer, data)
        buffer.seek(0)

        # Return as binary response
        return Response(
            content=buffer.getvalue(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=trace_m{module}_c{channel}_t{trace_type}.npy"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get binary trace: {str(e)}")
