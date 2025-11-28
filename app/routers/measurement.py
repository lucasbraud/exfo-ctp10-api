"""Sweep control for CTP10."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10, get_ctp10_manager
from app.manager import CTP10Manager
from app.models import SweepStatus, SweepWavelengthConfig

router = APIRouter(prefix="/measurement", tags=["Measurement"])


# ============================================================================
# Sweep Control
# ============================================================================


@router.post("/sweep/start")
async def start_sweep(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    wait: bool = Query(default=False, description="Wait for sweep to complete before returning")
):
    """
    Initiate a sweep.

    This starts the scan using the currently configured TLS parameters.
    Use GET /measurement/sweep/status to monitor progress, or set wait=true to block until complete.
    """
    try:
        lock = manager.scpi_lock

        async with lock:
            await asyncio.to_thread(ctp.initiate_sweep)

            if wait:
                # Wait for sweep to complete (can take 30-60 seconds)
                await asyncio.to_thread(ctp.wait_for_sweep_complete)

        if wait:
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
async def abort_sweep(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """
    Abort the current sweep operation.

    Sends SCPI ABORt command to stop the scan.
    """
    try:
        lock = manager.scpi_lock

        async with lock:
            await asyncio.to_thread(ctp.write, ':ABORt')

        return {"success": True, "message": "Sweep aborted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to abort sweep: {str(e)}")


@router.get("/sweep/status", response_model=SweepStatus)
async def get_sweep_status(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """
    Get sweep status.

    Check if sweep is complete and get condition register.
    Condition register bit 2 (value 4) indicates scanning.
    """
    try:
        lock = manager.scpi_lock

        async with lock:
            is_complete = await asyncio.to_thread(lambda: ctp.sweep_complete)
            condition = await asyncio.to_thread(lambda: ctp.condition_register)

        # Condition register bit 2 (value 4) indicates scanning
        is_sweeping = bool(condition & 4)

        return SweepStatus(
            is_sweeping=is_sweeping,
            is_complete=is_complete,
            condition_register=condition
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/status/referencing")
async def get_referencing_status(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """
    Get referencing operation status.

    Checks if the system is currently performing a reference operation.
    This reads bit 6 (weight 64) of the Operational Status Condition Register.

    Returns:
        - is_referencing: True if referencing in progress, False otherwise
        - condition_register: Full condition register value for debugging

    Use this endpoint to monitor reference creation progress after calling
    POST /detector/reference.
    """
    try:
        lock = manager.scpi_lock

        async with lock:
            is_referencing = await asyncio.to_thread(lambda: ctp.referencing)
            condition = await asyncio.to_thread(lambda: ctp.condition_register)

        return {
            "is_referencing": is_referencing,
            "condition_register": condition
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get referencing status: {str(e)}")


# ============================================================================
# Global Sweep Wavelength Configuration (Instrument-Level, NOT TLS channel)
# ============================================================================


@router.get("/sweep/wavelengths", response_model=SweepWavelengthConfig)
async def get_sweep_wavelengths(
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """Get global sweep start and stop wavelengths (nm).

    These are instrument-level sweep boundaries distinct from TLS channel
    configuration. Values are returned in nanometers.
    """
    try:
        lock = manager.scpi_lock
        async with lock:
            start_nm = await asyncio.to_thread(lambda: ctp.start_wavelength_nm)
            stop_nm = await asyncio.to_thread(lambda: ctp.stop_wavelength_nm)
        return SweepWavelengthConfig(start_wavelength_nm=start_nm, stop_wavelength_nm=stop_nm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sweep wavelengths: {str(e)}")


@router.post("/sweep/wavelengths", response_model=SweepWavelengthConfig)
async def set_sweep_wavelengths(
    config: SweepWavelengthConfig,
    ctp: Annotated[CTP10, Depends(get_ctp10)],
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """Set global sweep start/stop wavelengths; returns effective values.

    If both start and stop wavelengths are provided they are applied in order:
    start then stop. The instrument may internally adjust one after the other
    to maintain valid span constraints; the returned values reflect the final
    effective configuration after any firmware normalization.
    """
    try:
        if config.start_wavelength_nm is None and config.stop_wavelength_nm is None:
            raise HTTPException(status_code=400, detail="Provide at least one of start_wavelength_nm or stop_wavelength_nm")

        lock = manager.scpi_lock
        async with lock:
            # Apply in deterministic order
            if config.start_wavelength_nm is not None:
                await asyncio.to_thread(setattr, ctp, 'start_wavelength_nm', config.start_wavelength_nm)
            if config.stop_wavelength_nm is not None:
                await asyncio.to_thread(setattr, ctp, 'stop_wavelength_nm', config.stop_wavelength_nm)

            # Re-query to get effective values
            effective_start = await asyncio.to_thread(lambda: ctp.start_wavelength_nm)
            effective_stop = await asyncio.to_thread(lambda: ctp.stop_wavelength_nm)

        return SweepWavelengthConfig(start_wavelength_nm=effective_start, stop_wavelength_nm=effective_stop)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set sweep wavelengths: {str(e)}")
