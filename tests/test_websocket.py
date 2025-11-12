"""Tests for WebSocket endpoints."""

import pytest
import json
import time


class TestWebSocketPowerStream:
    """Test WebSocket power streaming endpoint."""

    def test_websocket_connect_and_receive(self, client):
        """Test WebSocket connection and data reception."""
        with client.websocket_connect("/ws/power?module=4&interval=0.1") as websocket:
            # Receive first message
            data = websocket.receive_json()

            # Validate structure matches DetectorSnapshot
            assert "timestamp" in data
            assert data["module"] == 4
            assert "wavelength_nm" in data
            assert "unit" in data
            assert "ch1_power" in data
            assert "ch2_power" in data
            assert "ch3_power" in data
            assert "ch4_power" in data

            # Validate data types
            assert isinstance(data["timestamp"], (int, float))
            assert isinstance(data["wavelength_nm"], (int, float))
            assert isinstance(data["ch1_power"], (int, float))
            assert isinstance(data["ch2_power"], (int, float))
            assert isinstance(data["ch3_power"], (int, float))
            assert isinstance(data["ch4_power"], (int, float))

    def test_websocket_multiple_messages(self, client):
        """Test receiving multiple WebSocket messages."""
        with client.websocket_connect("/ws/power?module=4&interval=0.05") as websocket:
            messages = []

            # Receive 3 messages
            for _ in range(3):
                data = websocket.receive_json()
                messages.append(data)

            # Verify we got 3 messages
            assert len(messages) == 3

            # Verify timestamps increase
            assert messages[1]["timestamp"] >= messages[0]["timestamp"]
            assert messages[2]["timestamp"] >= messages[1]["timestamp"]

    def test_websocket_custom_module(self, client):
        """Test WebSocket with custom module parameter."""
        with client.websocket_connect("/ws/power?module=5&interval=0.1") as websocket:
            data = websocket.receive_json()

            assert data["module"] == 5

    def test_websocket_custom_interval(self, client):
        """Test WebSocket with custom interval parameter."""
        # Use a longer interval
        with client.websocket_connect("/ws/power?module=4&interval=0.2") as websocket:
            start_time = time.time()
            data1 = websocket.receive_json()
            data2 = websocket.receive_json()
            elapsed = time.time() - start_time

            # Should take at least 0.2 seconds to receive 2 messages
            assert elapsed >= 0.15  # Allow some tolerance

    def test_websocket_data_structure(self, client):
        """Test that WebSocket data has correct structure."""
        # Get data via WebSocket
        with client.websocket_connect("/ws/power?module=4&interval=0.1") as websocket:
            ws_data = websocket.receive_json()

            # Check structure matches DetectorSnapshot
            assert ws_data["module"] == 4
            assert "wavelength_nm" in ws_data
            assert "unit" in ws_data

            # Power values should be present and numeric
            assert isinstance(ws_data["ch1_power"], (int, float))
            assert isinstance(ws_data["ch2_power"], (int, float))
            assert isinstance(ws_data["ch3_power"], (int, float))
            assert isinstance(ws_data["ch4_power"], (int, float))


class TestWebSocketValidation:
    """Test WebSocket parameter validation."""

    def test_websocket_invalid_module(self, client):
        """Test WebSocket with invalid module number."""
        # Module out of range should fail
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/power?module=21&interval=0.1"):
                pass

    def test_websocket_invalid_interval(self, client):
        """Test WebSocket with invalid interval."""
        # Interval too small
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/power?module=4&interval=0.005"):
                pass

        # Interval too large
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/power?module=4&interval=15.0"):
                pass

    def test_websocket_default_parameters(self, client):
        """Test WebSocket with default parameters."""
        with client.websocket_connect("/ws/power") as websocket:
            data = websocket.receive_json()

            # Should use default module (4)
            assert data["module"] == 4


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    def test_websocket_disconnected_hardware(self, disconnected_client):
        """Test WebSocket behavior when hardware is disconnected."""
        with disconnected_client.websocket_connect("/ws/power?module=4&interval=0.1") as websocket:
            # Should receive error message
            data = websocket.receive_json()

            # Error message should indicate not connected
            assert "error" in data
            assert "Not connected" in data["error"]
            assert "timestamp" in data
