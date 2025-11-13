"""Measurement and sweep control for CTP10."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pymeasure.instruments.exfo import CTP10

from app.config import settings
from app.dependencies import get_ctp10
from app.models import SweepConfig, SweepStatus

router = APIRouter(prefix="/measurement", tags=["Measurement"])


# ============================================================================
# Global Sweep Configuration
# ============================================================================


@router.get("/resolution")
async def get_resolution(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """Get wavelength sampling resolution in picometers."""
    try:
        return {
            "resolution_pm": ctp.resolution_pm
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resolution: {str(e)}")


@router.post("/resolution")
async def set_resolution(
    resolution_pm: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)]
):
    """
    Set wavelength sampling resolution in picometers.

    Standard resolution: 1-250 pm (integers)
    High-resolution: 0.02, 0.05, 0.1, 0.2, 0.5 pm
    """
    try:
        ctp.resolution_pm = resolution_pm
        return {
            "success": True,
            "resolution_pm": resolution_pm
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set resolution: {str(e)}")


@router.get("/stabilization")
async def get_stabilization(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """Get laser stabilization settings (output state, duration)."""
    try:
        output, duration = ctp.stabilization
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
    output: bool,
    duration_seconds: float,
    ctp: Annotated[CTP10, Depends(get_ctp10)]
):
    """
    Set laser stabilization settings.

    Args:
        output: False=OFF, True=ON (laser output after scan)
        duration_seconds: 0-60 seconds
    """
    if not (0 <= duration_seconds <= 60):
        raise HTTPException(status_code=400, detail="Duration must be 0-60 seconds")

    try:
        # Convert boolean to integer (0 or 1) for the device
        output_int = 1 if output else 0
        ctp.stabilization = (output_int, duration_seconds)
        return {
            "success": True,
            "output": output,
            "duration_seconds": duration_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set stabilization: {str(e)}")


@router.get("/config")
async def get_sweep_config(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """Get current sweep configuration (stabilization settings only)."""
    try:
        # Get stabilization settings (returns tuple)
        try:
            stab_output, stab_duration = ctp.stabilization
            # Convert stabilization_output to boolean (0=OFF, 1=ON)
            stab_output_bool = bool(stab_output) if stab_output is not None else None
        except Exception:
            stab_output_bool, stab_duration = None, None

        return {
            "stabilization_output": stab_output_bool,
            "stabilization_duration": stab_duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/config")
async def set_sweep_config(
    config: SweepConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)]
):
    """
    Set sweep configuration (stabilization only).

    All parameters are optional - only provided values will be updated.
    Note: Resolution is now configured via /detector/config endpoint.
    """
    try:
        if config.stabilization_output is not None and config.stabilization_duration is not None:
            # Convert boolean to integer (0 or 1) for the device
            stab_output_int = 1 if config.stabilization_output else 0
            ctp.stabilization = (stab_output_int, config.stabilization_duration)

        return {
            "success": True,
            "message": "Sweep configuration updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


# ============================================================================
# Sweep Control
# ============================================================================


@router.post("/sweep/start")
async def start_sweep(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    wait: bool = Query(default=False, description="Wait for sweep to complete before returning")
):
    """
    Initiate a sweep.

    This starts the scan using the currently configured TLS parameters.
    Use GET /measurement/sweep/status to monitor progress, or set wait=true to block until complete.
    """
    try:
        ctp.initiate_sweep()

        if wait:
            # Wait for sweep to complete (blocking)
            ctp.wait_for_sweep_complete()
            return {
                "success": True,
                "message": "Sweep completed",
                "is_complete": True
            }
        else:
            return {
                "success": True,
                "message": "Sweep initiated",
                "is_complete": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sweep: {str(e)}")


@router.post("/sweep/abort")
async def abort_sweep(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """
    Abort the current sweep operation.

    Sends SCPI ABORt command to stop the scan.
    """
    try:
        ctp.write(':ABORt')
        return {"success": True, "message": "Sweep aborted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to abort sweep: {str(e)}")


@router.get("/sweep/status", response_model=SweepStatus)
async def get_sweep_status(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """
    Get sweep status.

    Check if sweep is complete and get condition register.
    Condition register bit 2 (value 4) indicates scanning.
    """
    try:
        is_complete = ctp.sweep_complete
        condition = ctp.condition_register

        # Condition register bit 2 (value 4) indicates scanning
        is_sweeping = bool(condition & 4)

        return SweepStatus(
            is_sweeping=is_sweeping,
            is_complete=is_complete,
            condition_register=condition
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
