"""CTP10 connection manager."""

import logging
from typing import Optional

from pymeasure.instruments.exfo import CTP10

logger = logging.getLogger(__name__)


class CTP10Manager:
    """
    Manager for CTP10 instrument connection.

    Handles connection lifecycle, timeout configuration, and provides
    access to the CTP10 instrument instance.
    """

    def __init__(self, address: str, timeout_ms: int = 120000):
        """
        Initialize CTP10 manager.

        Args:
            address: VISA address (e.g., "TCPIP::192.168.1.37::5025::SOCKET")
            timeout_ms: Connection timeout in milliseconds (default 2 minutes)
        """
        self.address = address
        self.timeout_ms = timeout_ms
        self._ctp: Optional[CTP10] = None
        self._connected = False

    def connect(self) -> CTP10:
        """
        Connect to CTP10 instrument.

        Returns:
            CTP10 instrument instance

        Raises:
            RuntimeError: If connection fails
        """
        if self._connected and self._ctp is not None:
            logger.info("Already connected to CTP10")
            return self._ctp

        try:
            logger.info(f"Connecting to CTP10 at {self.address}")
            self._ctp = CTP10(self.address)

            # Set timeout for large binary transfers
            if hasattr(self._ctp, 'adapter') and hasattr(self._ctp.adapter, 'connection'):
                self._ctp.adapter.connection.timeout = self.timeout_ms
                logger.debug(f"Set connection timeout to {self.timeout_ms}ms")

            # Verify connection with ID query
            instrument_id = self._ctp.id
            logger.info(f"Connected to: {instrument_id}")

            self._connected = True
            return self._ctp

        except Exception as e:
            logger.error(f"Failed to connect to CTP10: {e}")
            self._ctp = None
            self._connected = False
            raise RuntimeError(f"CTP10 connection failed: {e}")

    def disconnect(self):
        """Disconnect from CTP10 instrument."""
        if self._ctp is not None:
            try:
                logger.info("Disconnecting from CTP10")
                self._ctp.shutdown()
                logger.info("CTP10 disconnected")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._ctp = None
                self._connected = False
        else:
            logger.debug("No active CTP10 connection to disconnect")

    @property
    def is_connected(self) -> bool:
        """Check if connected to CTP10."""
        return self._connected and self._ctp is not None

    @property
    def ctp(self) -> CTP10:
        """
        Get CTP10 instrument instance.

        Returns:
            CTP10 instrument instance

        Raises:
            RuntimeError: If not connected
        """
        if not self.is_connected or self._ctp is None:
            raise RuntimeError("Not connected to CTP10. Call connect() first.")
        return self._ctp

    def __enter__(self):
        """Context manager entry - connect."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect."""
        self.disconnect()
