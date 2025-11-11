"""Connection and status endpoints for CTP10."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pymeasure.instruments.exfo import CTP10

from app.dependencies import get_ctp10, get_ctp10_manager, get_ctp10_optional
from app.manager import CTP10Manager
from app.models import ConditionRegister, ConnectionStatus, ConnectRequest

router = APIRouter(prefix="/connection", tags=["Connection"])


@router.post("/connect", response_model=ConnectionStatus)
async def connect_to_ctp10(
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    request: ConnectRequest | None = None
):
    """
    Connect to CTP10 instrument.

    Optionally override connection address and timeout.
    """
    # Override address/timeout if provided
    if request and request.address:
        manager.address = request.address
    if request and request.timeout_ms:
        manager.timeout_ms = request.timeout_ms

    try:
        ctp = manager.connect()
        return ConnectionStatus(
            connected=True,
            instrument_id=ctp.id,
            address=manager.address
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to CTP10: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_from_ctp10(
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)]
):
    """Disconnect from CTP10 instrument."""
    manager.disconnect()
    return {"success": True, "message": "Disconnected successfully"}


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status(
    manager: Annotated[CTP10Manager, Depends(get_ctp10_manager)],
    ctp: Annotated[CTP10 | None, Depends(get_ctp10_optional)]
):
    """Get current connection status."""
    instrument_id = None
    if ctp is not None:
        try:
            instrument_id = ctp.id
        except Exception:
            pass

    return ConnectionStatus(
        connected=manager.is_connected,
        instrument_id=instrument_id,
        address=manager.address
    )


@router.get("/condition", response_model=ConditionRegister)
async def get_condition_register(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """
    Get the Operational Status Condition Register value.

    Returns bit values indicating current instrument state:
    - Bit 0 (1): Zeroing
    - Bit 1 (2): Calibrating
    - Bit 2 (4): Scanning
    - Bit 3 (8): Analyzing
    - Bit 4 (16): Aborting
    - Bit 5 (32): Armed
    - Bit 6 (64): Referencing
    - Bit 7 (128): Quick referencing

    Zero value indicates idle state.
    """
    try:
        condition = ctp.condition_register

        # Decode common bits
        bits = {
            "zeroing": bool(condition & 1),
            "calibrating": bool(condition & 2),
            "scanning": bool(condition & 4),
            "analyzing": bool(condition & 8),
            "aborting": bool(condition & 16),
            "armed": bool(condition & 32),
            "referencing": bool(condition & 64),
            "quick_referencing": bool(condition & 128),
        }

        return ConditionRegister(
            register_value=condition,
            is_idle=(condition == 0),
            bits=bits
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get condition register: {str(e)}"
        )


@router.post("/check_errors")
async def check_errors(ctp: Annotated[CTP10, Depends(get_ctp10)]):
    """
    Check for errors in the instrument error queue.

    Uses SCPI error checking to query any errors from the instrument.
    Raises an exception if errors are found.
    """
    try:
        ctp.check_errors()
        return {"success": True, "message": "No errors found"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error check failed or errors found: {str(e)}"
        )
