"""FastAPI dependency injection for CTP10 manager and instrument."""

from fastapi import HTTPException, Request
from pymeasure.instruments.exfo import CTP10

from app.manager import CTP10Manager


def get_ctp10_manager(request: Request) -> CTP10Manager:
    """
    Dependency to get CTP10 manager from app state.

    Returns the manager instance regardless of connection status.
    Use this when you need to access connection control methods.

    Raises:
        HTTPException: If manager is not initialized in app state
    """
    manager = getattr(request.app.state, "ctp10_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=500,
            detail="CTP10 manager not initialized"
        )
    return manager


def get_ctp10(request: Request) -> CTP10:
    """
    Dependency to get connected CTP10 instrument instance.

    Returns the CTP10 instrument directly for use in endpoints.
    This is the primary dependency to use in most endpoints.

    Raises:
        HTTPException: If not connected to CTP10
    """
    manager = get_ctp10_manager(request)

    if not manager.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Not connected to CTP10. Use POST /connection/connect first."
        )

    return manager.ctp


def get_ctp10_optional(request: Request) -> CTP10 | None:
    """
    Dependency to get CTP10 instance if connected, None otherwise.

    Use this for endpoints that should work whether connected or not
    (e.g., connection status endpoints).
    """
    manager = get_ctp10_manager(request)

    if not manager.is_connected:
        return None

    return manager.ctp
