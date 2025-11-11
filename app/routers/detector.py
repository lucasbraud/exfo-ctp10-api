"""Detector channel operations for CTP10."""

import io
import logging
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pymeasure.instruments.exfo import CTP10

from app.config import settings
from app.dependencies import get_ctp10
from app.models import DetectorConfig, DetectorPowerReading, TraceDataResponse, TraceMetadata

router = APIRouter(prefix="/detector", tags=["Detector"])
logger = logging.getLogger(__name__)


@router.get("/power", response_model=DetectorPowerReading)
async def read_power(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """
    Read instantaneous power from detector channel.

    Returns power in the currently configured unit (dBm or mW) and wavelength.
    """
    try:
        detector = ctp.detector(module=module, channel=channel)
        power = detector.power
        unit = detector.power_unit
        wavelength_nm = detector.wavelength_nm

        return DetectorPowerReading(
            module=module,
            channel=channel,
            power=power,
            unit=unit,
            wavelength_nm=wavelength_nm
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read power: {str(e)}")


@router.get("/config")
async def get_detector_config(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Get detector configuration (units, trigger)."""
    try:
        logger.debug(f"Getting detector config for module={module}, channel={channel}")
        detector = ctp.detector(module=module, channel=channel)
        logger.debug(f"Detector object created: {detector}")

        # Try to get each property, use None if not available
        config = {
            "module": module,
            "channel": channel,
        }

        try:
            config["power_unit"] = detector.power_unit
            logger.debug(f"Got power_unit: {config['power_unit']}")
        except Exception as e:
            logger.warning(f"Failed to get power_unit: {e}")
            config["power_unit"] = None

        try:
            config["spectral_unit"] = detector.spectral_unit
            logger.debug(f"Got spectral_unit: {config['spectral_unit']}")
        except Exception as e:
            logger.warning(f"Failed to get spectral_unit: {e}")
            config["spectral_unit"] = None

        return config
    except Exception as e:
        logger.error(f"Failed to get detector config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/config")
async def set_detector_config(
    config: DetectorConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Set detector configuration (units)."""
    try:
        detector = ctp.detector(module=module, channel=channel)

        if config.power_unit is not None:
            detector.power_unit = config.power_unit

        if config.spectral_unit is not None:
            detector.spectral_unit = config.spectral_unit

        return {
            "success": True,
            "message": f"Detector {module}/{channel} configured successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


@router.post("/reference")
async def create_reference(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
):
    """Create reference trace for detector channel."""
    try:
        detector = ctp.detector(module=module, channel=channel)
        detector.create_reference()

        return {
            "success": True,
            "message": f"Reference created for detector {module}/{channel}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create reference: {str(e)}")


@router.get("/trace/metadata", response_model=TraceMetadata)
async def get_trace_metadata(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    module: int = Query(default=settings.DEFAULT_MODULE, ge=1, le=20),
    channel: int = Query(default=settings.DEFAULT_CHANNEL, ge=1, le=6),
    trace_type: int = Query(default=1, ge=1, le=23, description="1=TF live, 11=Raw live, 12=Raw ref, 13=Quick ref"),
):
    """
    Get trace metadata without retrieving the full data.

    Use this to check trace information before downloading large datasets.
    """
    try:
        detector = ctp.detector(module=module, channel=channel)

        num_points = detector.length(trace_type=trace_type)
        sampling_pm = detector.sampling_pm(trace_type=trace_type)
        start_wavelength_nm = detector.start_wavelength_nm(trace_type=trace_type)
        unit = detector.power_unit

        return TraceMetadata(
            module=module,
            channel=channel,
            trace_type=trace_type,
            num_points=num_points,
            sampling_pm=sampling_pm,
            start_wavelength_nm=start_wavelength_nm,
            unit=unit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


@router.get("/trace/data", response_model=TraceDataResponse)
async def get_trace_data_json(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
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
        detector = ctp.detector(module=module, channel=channel)

        # Get metadata
        num_points = detector.length(trace_type=trace_type)
        sampling_pm = detector.sampling_pm(trace_type=trace_type)
        start_wavelength_nm = detector.start_wavelength_nm(trace_type=trace_type)
        unit = detector.power_unit

        # Get trace data (binary format for speed, convert to lists for JSON)
        wavelengths_m = detector.get_data_x(trace_type=trace_type, unit='M', format='BIN')
        values = detector.get_data_y(trace_type=trace_type, unit='DB', format='BIN')

        # Convert meters to nanometers and numpy arrays to lists
        wavelengths_nm = (wavelengths_m * 1e9).tolist()
        values_list = values.tolist()

        metadata = TraceMetadata(
            module=module,
            channel=channel,
            trace_type=trace_type,
            num_points=num_points,
            sampling_pm=sampling_pm,
            start_wavelength_nm=start_wavelength_nm,
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
        detector = ctp.detector(module=module, channel=channel)

        # Get trace data in binary format
        wavelengths_m = detector.get_data_x(trace_type=trace_type, unit='M', format='BIN')
        values = detector.get_data_y(trace_type=trace_type, unit='DB', format='BIN')

        # Convert meters to nanometers
        wavelengths_nm = wavelengths_m * 1e9

        # Create structured array with both datasets
        data = np.array(
            list(zip(wavelengths_nm, values)),
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
