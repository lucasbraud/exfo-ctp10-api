"""Factory for creating CTP10 manager (real or mock)."""

import logging
from app.manager import CTP10Manager
from app.config import settings

logger = logging.getLogger(__name__)


def create_ctp10_manager() -> CTP10Manager:
    """
    Create CTP10Manager with real or mock hardware based on configuration.

    Returns real CTP10Manager if MOCK_MODE=False (default)
    Returns mock CTP10Manager if MOCK_MODE=True

    This allows running the API without hardware for:
    - Development from home
    - CI/CD testing
    - Demos without lab access

    Usage:
        # Production (real hardware)
        fastapi dev app/main.py

        # Mock mode (no hardware)
        MOCK_MODE=true fastapi dev app/main.py

        # Or in .env file:
        MOCK_MODE=true
    """
    if settings.MOCK_MODE:
        # Mock mode - use FakeCTP10
        from app.mocks.mock_ctp10 import FakeCTP10

        logger.info("="*70)
        logger.info("🎭 MOCK MODE - Using FakeCTP10 (NO REAL HARDWARE)")
        logger.info("="*70)

        manager = CTP10Manager(
            address="MOCK::ADDRESS",
            timeout_ms=settings.CTP10_TIMEOUT_MS
        )

        # Inject mock CTP10
        mock_ctp10 = FakeCTP10()
        manager._ctp = mock_ctp10
        manager._connected = True

        logger.info(f"✅ Mock CTP10 connected: {mock_ctp10.id}")
        logger.info("💡 All endpoints work without real hardware")
        logger.info("="*70)

        return manager

    else:
        # Production mode - use real hardware
        logger.info("🔧 PRODUCTION MODE - Using real CTP10 hardware")
        logger.info(f"📡 CTP10 address: {settings.ctp10_address}")

        manager = CTP10Manager(
            address=settings.ctp10_address,
            timeout_ms=settings.CTP10_TIMEOUT_MS
        )

        return manager
