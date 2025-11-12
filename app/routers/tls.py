"""TLS (Tunable Laser Source) configuration endpoints for CTP10."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10
from app.models import TLSConfig

router = APIRouter(prefix="/tls", tags=["TLS"])


def _get_tls_channel(ctp: CTP10, channel: int):
    """Helper to get TLS channel object."""
    if channel == 1:
        return ctp.tls1
    elif channel == 2:
        return ctp.tls2
    elif channel == 3:
        return ctp.tls3
    elif channel == 4:
        return ctp.tls4
    else:
        raise ValueError(f"Invalid TLS channel: {channel}")


@router.get("/{channel}/config")
async def get_tls_config(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4, description="TLS channel (1-4)")
):
    """
    Get TLS channel configuration.

    Returns wavelength range, sweep speed, power, trigger, and identifier for TLS channel (1-4).
    """
    try:
        tls = _get_tls_channel(ctp, channel)

        return {
            "channel": channel,
            "start_wavelength_nm": tls.start_wavelength_nm,
            "stop_wavelength_nm": tls.stop_wavelength_nm,
            "sweep_speed_nmps": tls.sweep_speed_nmps,
            "laser_power_dbm": tls.laser_power_dbm,
            "trigin": tls.trigin,
            "identifier": tls.identifier
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get TLS config: {str(e)}"
        )


@router.post("/{channel}/config")
async def set_tls_config(
    config: TLSConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """
    Configure TLS channel parameters.

    Sets wavelength range, sweep speed, power, trigger, and identifier for TLS channel (1-4).
    Only provided parameters will be updated.
    """
    try:
        tls = _get_tls_channel(ctp, channel)

        # Update only provided parameters
        if config.start_wavelength_nm is not None:
            tls.start_wavelength_nm = config.start_wavelength_nm

        if config.stop_wavelength_nm is not None:
            tls.stop_wavelength_nm = config.stop_wavelength_nm

        if config.sweep_speed_nmps is not None:
            tls.sweep_speed_nmps = config.sweep_speed_nmps

        if config.laser_power_dbm is not None:
            tls.laser_power_dbm = config.laser_power_dbm

        if config.trigin is not None:
            tls.trigin = config.trigin

        if config.identifier is not None:
            tls.identifier = config.identifier

        return {
            "success": True,
            "message": f"TLS channel {channel} configured successfully",
            "config": config.model_dump(exclude_none=True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure TLS: {str(e)}"
        )


@router.get("/{channel}/wavelength")
async def get_tls_wavelength(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Get start and stop wavelength for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        return {
            "channel": channel,
            "start_wavelength_nm": tls.start_wavelength_nm,
            "stop_wavelength_nm": tls.stop_wavelength_nm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get wavelength: {str(e)}"
        )


@router.post("/{channel}/wavelength")
async def set_tls_wavelength(
    start_nm: float,
    stop_nm: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Set start and stop wavelength for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        tls.start_wavelength_nm = start_nm
        tls.stop_wavelength_nm = stop_nm

        return {
            "success": True,
            "message": f"Wavelength range set for TLS {channel}",
            "start_wavelength_nm": start_nm,
            "stop_wavelength_nm": stop_nm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set wavelength: {str(e)}"
        )


@router.get("/{channel}/power")
async def get_tls_power(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Get laser power setting for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        return {
            "channel": channel,
            "laser_power_dbm": tls.laser_power_dbm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get power: {str(e)}"
        )


@router.post("/{channel}/power")
async def set_tls_power(
    power_dbm: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Set laser power for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        tls.laser_power_dbm = power_dbm

        return {
            "success": True,
            "message": f"Power set for TLS {channel}",
            "laser_power_dbm": power_dbm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set power: {str(e)}"
        )


@router.get("/{channel}/speed")
async def get_tls_speed(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Get sweep speed for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        return {
            "channel": channel,
            "sweep_speed_nmps": tls.sweep_speed_nmps
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get speed: {str(e)}"
        )


@router.post("/{channel}/speed")
async def set_tls_speed(
    speed_nmps: int,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Set sweep speed for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        tls.sweep_speed_nmps = speed_nmps

        return {
            "success": True,
            "message": f"Speed set for TLS {channel}",
            "sweep_speed_nmps": speed_nmps
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set speed: {str(e)}"
        )


@router.get("/{channel}/trigger")
async def get_tls_trigger(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """Get trigger input for TLS channel."""
    try:
        tls = _get_tls_channel(ctp, channel)

        return {
            "channel": channel,
            "trigin": tls.trigin,
            "description": "Software trigger" if tls.trigin == 0 else f"TRIG IN port {tls.trigin}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trigger: {str(e)}"
        )


@router.post("/{channel}/trigger")
async def set_tls_trigger(
    trigin: int,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    channel: int = Path(ge=1, le=4)
):
    """
    Set trigger input for TLS channel.

    Args:
        trigin: 0 for software trigger, 1-8 for TRIG IN port number
    """
    if trigin < 0 or trigin > 8:
        raise HTTPException(status_code=400, detail="Trigger must be 0-8")

    try:
        tls = _get_tls_channel(ctp, channel)

        tls.trigin = trigin

        return {
            "success": True,
            "message": f"Trigger set for TLS {channel}",
            "trigin": trigin
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set trigger: {str(e)}"
        )
