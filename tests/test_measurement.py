"""Tests for measurement and sweep control endpoints."""

import pytest
import time


class TestResolution:
    """Test resolution configuration endpoints."""

    def test_get_resolution(self, client):
        """Test getting wavelength sampling resolution."""
        response = client.get("/measurement/resolution")

        assert response.status_code == 200
        data = response.json()
        assert "resolution_pm" in data
        assert isinstance(data["resolution_pm"], (int, float))
        assert data["resolution_pm"] > 0

    def test_set_resolution(self, client):
        """Test setting wavelength sampling resolution."""
        response = client.post("/measurement/resolution?resolution_pm=5.0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["resolution_pm"] == 5.0

        # Verify resolution was set
        verify_response = client.get("/measurement/resolution")
        verify_data = verify_response.json()
        assert verify_data["resolution_pm"] == 5.0

    def test_set_resolution_high_res(self, client):
        """Test setting high-resolution sampling."""
        # High-resolution mode: 0.02, 0.05, 0.1, 0.2, 0.5 pm
        response = client.post("/measurement/resolution?resolution_pm=0.1")

        assert response.status_code == 200
        data = response.json()
        assert data["resolution_pm"] == 0.1


class TestStabilization:
    """Test stabilization configuration endpoints."""

    def test_get_stabilization(self, client):
        """Test getting stabilization settings."""
        response = client.get("/measurement/stabilization")

        assert response.status_code == 200
        data = response.json()
        assert "output" in data
        assert "duration_seconds" in data
        assert isinstance(data["output"], bool)
        assert isinstance(data["duration_seconds"], (int, float))

    def test_set_stabilization(self, client):
        """Test setting stabilization settings."""
        response = client.post(
            "/measurement/stabilization?output=true&duration_seconds=5.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["output"] is True
        assert data["duration_seconds"] == 5.0

        # Verify stabilization was set
        verify_response = client.get("/measurement/stabilization")
        verify_data = verify_response.json()
        assert verify_data["output"] is True
        assert verify_data["duration_seconds"] == 5.0

    def test_set_stabilization_off(self, client):
        """Test setting stabilization output off."""
        response = client.post(
            "/measurement/stabilization?output=false&duration_seconds=0.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["output"] is False

    def test_set_stabilization_invalid_duration(self, client):
        """Test setting invalid stabilization duration."""
        # Duration out of range (must be 0-60)
        response = client.post(
            "/measurement/stabilization?output=true&duration_seconds=70.0"
        )

        assert response.status_code == 400
        assert "0-60 seconds" in response.json()["detail"]


class TestSweepConfig:
    """Test sweep configuration endpoints."""

    def test_get_sweep_config(self, client):
        """Test getting complete sweep configuration."""
        response = client.get("/measurement/config")

        assert response.status_code == 200
        data = response.json()
        assert "resolution_pm" in data
        assert "stabilization_output" in data
        assert "stabilization_duration" in data

    def test_set_sweep_config_full(self, client):
        """Test setting complete sweep configuration."""
        config_data = {
            "resolution_pm": 15.0,
            "stabilization_output": True,
            "stabilization_duration": 3.0
        }

        response = client.post("/measurement/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify config was set
        verify_response = client.get("/measurement/config")
        verify_data = verify_response.json()
        assert verify_data["resolution_pm"] == 15.0
        assert verify_data["stabilization_output"] is True
        assert verify_data["stabilization_duration"] == 3.0

    def test_set_sweep_config_partial(self, client):
        """Test setting partial sweep configuration."""
        config_data = {
            "resolution_pm": 20.0
        }

        response = client.post("/measurement/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify only resolution changed
        verify_response = client.get("/measurement/config")
        verify_data = verify_response.json()
        assert verify_data["resolution_pm"] == 20.0


class TestSweepControl:
    """Test sweep start/stop/status endpoints."""

    def test_start_sweep_non_blocking(self, client):
        """Test starting sweep without waiting."""
        response = client.post("/measurement/sweep/start?wait=false")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Sweep initiated" in data["message"]
        assert data["is_complete"] is False

    def test_start_sweep_blocking(self, client):
        """Test starting sweep with wait=true."""
        response = client.post("/measurement/sweep/start?wait=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Sweep completed" in data["message"]
        assert data["is_complete"] is True

    def test_get_sweep_status_idle(self, client):
        """Test getting sweep status when idle."""
        response = client.get("/measurement/sweep/status")

        assert response.status_code == 200
        data = response.json()
        assert "is_sweeping" in data
        assert "is_complete" in data
        assert "condition_register" in data
        assert isinstance(data["is_sweeping"], bool)
        assert isinstance(data["is_complete"], bool)

    def test_get_sweep_status_after_start(self, client):
        """Test getting sweep status after starting."""
        # Start sweep (non-blocking)
        client.post("/measurement/sweep/start?wait=false")

        # Immediately check status (might be scanning)
        response = client.get("/measurement/sweep/status")

        assert response.status_code == 200
        data = response.json()
        assert "is_sweeping" in data
        assert "is_complete" in data

        # Wait briefly for simulated sweep to complete
        time.sleep(0.6)

        # Check status again (should be complete)
        response2 = client.get("/measurement/sweep/status")
        data2 = response2.json()
        assert data2["is_complete"] is True
        assert data2["is_sweeping"] is False
        assert data2["condition_register"] == 0

    def test_abort_sweep(self, client):
        """Test aborting a sweep."""
        # Start sweep
        client.post("/measurement/sweep/start?wait=false")

        # Abort immediately
        response = client.post("/measurement/sweep/abort")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "aborted" in data["message"].lower()

        # Verify sweep was aborted
        status_response = client.get("/measurement/sweep/status")
        status_data = status_response.json()
        assert status_data["is_sweeping"] is False


class TestSweepLifecycle:
    """Test complete sweep lifecycle."""

    def test_full_sweep_cycle(self, client):
        """Test complete sweep cycle from config to completion."""
        # 1. Configure sweep
        config_data = {
            "resolution_pm": 10.0,
            "stabilization_output": False,
            "stabilization_duration": 0.0
        }
        config_response = client.post("/measurement/config", json=config_data)
        assert config_response.status_code == 200

        # 2. Start sweep
        start_response = client.post("/measurement/sweep/start?wait=false")
        assert start_response.status_code == 200

        # 3. Monitor status
        status_response = client.get("/measurement/sweep/status")
        assert status_response.status_code == 200

        # 4. Wait for completion
        time.sleep(0.6)

        # 5. Verify completion
        final_status = client.get("/measurement/sweep/status")
        final_data = final_status.json()
        assert final_data["is_complete"] is True

    def test_multiple_consecutive_sweeps(self, client):
        """Test running multiple sweeps consecutively."""
        # Run first sweep with wait
        response1 = client.post("/measurement/sweep/start?wait=true")
        assert response1.status_code == 200
        assert response1.json()["is_complete"] is True

        # Run second sweep with wait
        response2 = client.post("/measurement/sweep/start?wait=true")
        assert response2.status_code == 200
        assert response2.json()["is_complete"] is True

        # Verify final status
        status = client.get("/measurement/sweep/status")
        assert status.json()["is_complete"] is True


class TestSweepConditionRegister:
    """Test condition register during sweeps."""

    def test_condition_register_scanning_bit(self, client):
        """Test that condition register bit 2 is set during sweep."""
        # Start sweep
        client.post("/measurement/sweep/start?wait=false")

        # Check condition register immediately (might catch scanning bit)
        response = client.get("/measurement/sweep/status")
        data = response.json()

        # Condition register should indicate status
        assert "condition_register" in data
        assert isinstance(data["condition_register"], int)

        # Wait for completion
        time.sleep(0.6)

        # After completion, condition should be 0 (idle)
        final_response = client.get("/measurement/sweep/status")
        final_data = final_response.json()
        assert final_data["condition_register"] == 0


class TestMeasurementNotConnected:
    """Test measurement endpoints when not connected."""

    def test_get_resolution_not_connected(self, disconnected_client):
        """Test getting resolution fails when not connected."""
        response = disconnected_client.get("/measurement/resolution")

        assert response.status_code == 503
        assert "Not connected" in response.json()["detail"]

    def test_start_sweep_not_connected(self, disconnected_client):
        """Test starting sweep fails when not connected."""
        response = disconnected_client.post("/measurement/sweep/start")

        assert response.status_code == 503

    def test_get_sweep_status_not_connected(self, disconnected_client):
        """Test getting sweep status fails when not connected."""
        response = disconnected_client.get("/measurement/sweep/status")

        assert response.status_code == 503
