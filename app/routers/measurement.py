"""Sweep control for CTP10."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10, get_ctp10_manager
from app.manager import CTP10Manager
from app.models import SweepStatus

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
