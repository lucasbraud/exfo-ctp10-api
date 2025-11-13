"""Pytest configuration and fixtures for CTP10 API tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.manager import CTP10Manager
from app.dependencies import get_ctp10_manager, get_ctp10, get_ctp10_optional
from app.config import Settings
from app.mocks.mock_ctp10 import FakeCTP10


@pytest.fixture
def test_settings():
    """Test settings with AUTO_CONNECT disabled."""
    return Settings(
        CTP10_IP="192.168.1.37",
        CTP10_PORT=5025,
        AUTO_CONNECT=False,  # Don't auto-connect during tests
        DEFAULT_MODULE=4,
        DEFAULT_CHANNEL=1,
        DEFAULT_WAVELENGTH_NM=1310.0,
        LOG_LEVEL="INFO",
    )


@pytest.fixture
def mock_ctp10_instrument():
    """Fixture providing a FakeCTP10 instrument."""
    return FakeCTP10()


@pytest.fixture
def mock_manager(mock_ctp10_instrument):
    """
    Fixture providing a CTP10Manager with mocked hardware.

    The manager is pre-connected to the fake instrument.
    """
    manager = CTP10Manager(
        address="MOCK::ADDRESS",
        timeout_ms=120000
    )

    # Replace the actual connection with our mock
    manager._ctp = mock_ctp10_instrument
    manager._connected = True

    return manager


@pytest.fixture
def client(mock_manager):
    """
    Fixture providing a FastAPI TestClient with dependency overrides.

    This client has all hardware dependencies replaced with mocks,
    allowing tests to run without real CTP10 hardware.
    """
    # Store the mock manager in app state
    app.state.ctp10_manager = mock_manager

    # Override dependencies to return mock objects
    app.dependency_overrides[get_ctp10_manager] = lambda: mock_manager
    app.dependency_overrides[get_ctp10] = lambda: mock_manager.ctp
    app.dependency_overrides[get_ctp10_optional] = lambda: mock_manager.ctp

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup: Clear dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def disconnected_client(test_settings):
    """
    Fixture providing a TestClient with disconnected hardware.

    Useful for testing connection endpoints and error handling.
    """
    # Create a manager that is not connected
    manager = CTP10Manager(
        address="MOCK::ADDRESS",
        timeout_ms=120000
    )

    # Store in app state
    app.state.ctp10_manager = manager

    # Override dependencies
    app.dependency_overrides[get_ctp10_manager] = lambda: manager

    def get_disconnected_ctp():
        if not manager.is_connected:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Not connected to CTP10. Use POST /connection/connect first.")
        return manager.ctp

    app.dependency_overrides[get_ctp10] = get_disconnected_ctp
    app.dependency_overrides[get_ctp10_optional] = lambda: None

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()
