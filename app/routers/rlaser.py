"""Reference Laser (RLaser) configuration endpoints for CTP10."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10
from app.models import RLaserConfig, RLaserStatus

router = APIRouter(prefix="/rlaser", tags=["RLaser"])
logger = logging.getLogger(__name__)


@router.get("/{laser_number}/config", response_model=RLaserStatus)
async def get_rlaser_config(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10, description="Reference laser number (1-10)")
):
    """
    Get complete reference laser configuration.

    Returns ID, wavelength, power, and state.
    """
    try:
        logger.debug(f"Getting RLaser{laser_number} config")
        laser = ctp.rlaser[laser_number]

        laser_id = laser.idn
        logger.debug(f"Got ID: {laser_id} (type: {type(laser_id)})")

        # Handle both string and list formats for ID
        if isinstance(laser_id, list):
            id_string = ','.join(str(p) for p in laser_id)
        else:
            id_string = str(laser_id)

        wavelength = laser.wavelength_nm
        logger.debug(f"Got wavelength: {wavelength}")

        power = laser.power_dbm
        logger.debug(f"Got power: {power}")

        state = laser.power_state_enabled
        logger.debug(f"Got state: {state}")

        return RLaserStatus(
            laser_number=laser_number,
            id=id_string,
            wavelength_nm=wavelength,
            power_dbm=power,
            is_on=bool(state)
        )
    except Exception as e:
        logger.error(f"Failed to get laser config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get laser config: {str(e)}"
        )


@router.post("/{laser_number}/config")
async def set_rlaser_config(
    config: RLaserConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Set reference laser configuration.

    Updates power, wavelength, and/or state. Only provided parameters will be updated.
    """
    try:
        laser = ctp.rlaser[laser_number]

        if config.power_dbm is not None:
            laser.power_dbm = config.power_dbm

        if config.wavelength_nm is not None:
            laser.wavelength_nm = config.wavelength_nm

        if config.power_state is not None:
            laser.power_state_enabled = config.power_state

        return {
            "success": True,
            "message": f"Reference laser {laser_number} configured successfully",
            "config": config.model_dump(exclude_none=True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure laser: {str(e)}"
        )


@router.get("/{laser_number}/id")
async def get_rlaser_id(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Get reference laser identification.

    Returns manufacturer, model, serial, and firmware version.
    Example: "EXFO,T100S-HP,0,6.06" or ['EXFO', 'T200S-O-M', 'EO241510155', '4.6.3.0']
    """
    try:
        laser_id = ctp.rlaser[laser_number].idn

        # Handle both string and list formats
        if isinstance(laser_id, list):
            parts = laser_id
            id_string = ','.join(str(p) for p in parts)
        else:
            # Parse the ID string (format: manufacturer,model,serial,firmware)
            id_string = str(laser_id)
            parts = id_string.split(',')

        return {
            "laser_number": laser_number,
            "id": id_string,
            "manufacturer": parts[0] if len(parts) > 0 else None,
            "model": parts[1] if len(parts) > 1 else None,
            "serial": parts[2] if len(parts) > 2 else None,
            "firmware": parts[3] if len(parts) > 3 else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get laser ID: {str(e)}"
        )


@router.get("/{laser_number}/power")
async def get_rlaser_power(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """Get reference laser power setting in dBm."""
    try:
        power_dbm = ctp.rlaser[laser_number].power_dbm

        return {
            "laser_number": laser_number,
            "power_dbm": power_dbm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get power: {str(e)}"
        )


@router.post("/{laser_number}/power")
async def set_rlaser_power(
    power_dbm: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Set reference laser output power in dBm.

    Power range depends on laser model (typically -10 to 13 dBm).
    """
    try:
        ctp.rlaser[laser_number].power_dbm = power_dbm

        return {
            "success": True,
            "message": f"Power set to {power_dbm} dBm for laser {laser_number}",
            "laser_number": laser_number,
            "power_dbm": power_dbm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set power: {str(e)}"
        )


@router.get("/{laser_number}/wavelength")
async def get_rlaser_wavelength(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """Get reference laser wavelength in nm."""
    try:
        wavelength_nm = ctp.rlaser[laser_number].wavelength_nm

        return {
            "laser_number": laser_number,
            "wavelength_nm": wavelength_nm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get wavelength: {str(e)}"
        )


@router.post("/{laser_number}/wavelength")
async def set_rlaser_wavelength(
    wavelength_nm: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Set reference laser wavelength in nm.

    Sets the laser emission wavelength (static control).
    """
    try:
        ctp.rlaser[laser_number].wavelength_nm = wavelength_nm

        return {
            "success": True,
            "message": f"Wavelength set to {wavelength_nm} nm for laser {laser_number}",
            "laser_number": laser_number,
            "wavelength_nm": wavelength_nm
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set wavelength: {str(e)}"
        )


@router.get("/{laser_number}/state")
async def get_rlaser_state(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Get reference laser output state.

    Returns True/1 if laser is ON, False/0 if OFF.
    """
    try:
        state = ctp.rlaser[laser_number].power_state_enabled

        return {
            "laser_number": laser_number,
            "is_on": bool(state),
            "state": state
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get laser state: {str(e)}"
        )


@router.post("/{laser_number}/on")
async def turn_on_rlaser(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Turn on reference laser output.

    Enables the laser optical output. This operation can take time.
    """
    try:
        ctp.rlaser[laser_number].power_state_enabled = True

        return {
            "success": True,
            "message": f"Laser {laser_number} turned ON",
            "laser_number": laser_number,
            "is_on": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to turn on laser: {str(e)}"
        )


@router.post("/{laser_number}/off")
async def turn_off_rlaser(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    laser_number: int = Path(ge=1, le=10)
):
    """
    Turn off reference laser output.

    Disables the laser optical output. This operation can take time.
    """
    try:
        ctp.rlaser[laser_number].power_state_enabled = False

        return {
            "success": True,
            "message": f"Laser {laser_number} turned OFF",
            "laser_number": laser_number,
            "is_on": False
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to turn off laser: {str(e)}"
        )
