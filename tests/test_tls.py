"""Tests for TLS (Tunable Laser Source) endpoints."""

import pytest


class TestTLSConfig:
    """Test TLS configuration endpoints."""

    @pytest.mark.parametrize("channel", [1, 2, 3, 4])
    def test_get_tls_config(self, client, channel):
        """Test getting TLS configuration for all channels."""
        response = client.get(f"/tls/{channel}/config")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == channel
        assert "start_wavelength_nm" in data
        assert "stop_wavelength_nm" in data
        assert "sweep_speed_nmps" in data
        assert "laser_power_dbm" in data
        assert "trigin" in data

        # Validate data types
        assert isinstance(data["start_wavelength_nm"], (int, float))
        assert isinstance(data["stop_wavelength_nm"], (int, float))
        assert isinstance(data["sweep_speed_nmps"], int)
        assert isinstance(data["laser_power_dbm"], (int, float))
        assert isinstance(data["trigin"], int)

    def test_set_tls_config_full(self, client):
        """Test setting complete TLS configuration."""
        config_data = {
            "start_wavelength_nm": 1520.0,
            "stop_wavelength_nm": 1580.0,
            "sweep_speed_nmps": 40,
            "laser_power_dbm": 3.0,
            "trigin": 0
        }

        response = client.post("/tls/1/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "configured successfully" in data["message"]

        # Verify configuration was applied
        verify_response = client.get("/tls/1/config")
        verify_data = verify_response.json()
        assert verify_data["start_wavelength_nm"] == 1520.0
        assert verify_data["stop_wavelength_nm"] == 1580.0
        assert verify_data["sweep_speed_nmps"] == 40
        assert verify_data["laser_power_dbm"] == 3.0

    def test_set_tls_config_partial(self, client):
        """Test setting partial TLS configuration."""
        config_data = {
            "laser_power_dbm": 7.0
        }

        response = client.post("/tls/1/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify only power changed
        verify_response = client.get("/tls/1/config")
        verify_data = verify_response.json()
        assert verify_data["laser_power_dbm"] == 7.0


class TestTLSWavelength:
    """Test TLS wavelength endpoints."""

    def test_get_tls_wavelength(self, client):
        """Test getting TLS wavelength range."""
        response = client.get("/tls/1/wavelength")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == 1
        assert "start_wavelength_nm" in data
        assert "stop_wavelength_nm" in data

    def test_set_tls_wavelength(self, client):
        """Test setting TLS wavelength range."""
        response = client.post(
            "/tls/1/wavelength?start_nm=1510.0&stop_nm=1590.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["start_wavelength_nm"] == 1510.0
        assert data["stop_wavelength_nm"] == 1590.0

        # Verify wavelength was set
        verify_response = client.get("/tls/1/wavelength")
        verify_data = verify_response.json()
        assert verify_data["start_wavelength_nm"] == 1510.0
        assert verify_data["stop_wavelength_nm"] == 1590.0


class TestTLSPower:
    """Test TLS power endpoints."""

    def test_get_tls_power(self, client):
        """Test getting TLS laser power."""
        response = client.get("/tls/1/power")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == 1
        assert "laser_power_dbm" in data
        assert isinstance(data["laser_power_dbm"], (int, float))

    def test_set_tls_power(self, client):
        """Test setting TLS laser power."""
        response = client.post("/tls/1/power?power_dbm=6.5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["laser_power_dbm"] == 6.5

        # Verify power was set
        verify_response = client.get("/tls/1/power")
        verify_data = verify_response.json()
        assert verify_data["laser_power_dbm"] == 6.5


class TestTLSSpeed:
    """Test TLS sweep speed endpoints."""

    def test_get_tls_speed(self, client):
        """Test getting TLS sweep speed."""
        response = client.get("/tls/1/speed")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == 1
        assert "sweep_speed_nmps" in data
        assert isinstance(data["sweep_speed_nmps"], int)

    def test_set_tls_speed(self, client):
        """Test setting TLS sweep speed."""
        response = client.post("/tls/1/speed?speed_nmps=80")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sweep_speed_nmps"] == 80

        # Verify speed was set
        verify_response = client.get("/tls/1/speed")
        verify_data = verify_response.json()
        assert verify_data["sweep_speed_nmps"] == 80


class TestTLSTrigger:
    """Test TLS trigger endpoints."""

    def test_get_tls_trigger(self, client):
        """Test getting TLS trigger setting."""
        response = client.get("/tls/1/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == 1
        assert "trigin" in data
        assert "description" in data
        assert isinstance(data["trigin"], int)

    def test_set_tls_trigger_software(self, client):
        """Test setting TLS trigger to software (0)."""
        response = client.post("/tls/1/trigger?trigin=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trigin"] == 0

    def test_set_tls_trigger_hardware(self, client):
        """Test setting TLS trigger to hardware port."""
        response = client.post("/tls/1/trigger?trigin=1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trigin"] == 1

        # Verify trigger was set
        verify_response = client.get("/tls/1/trigger")
        verify_data = verify_response.json()
        assert verify_data["trigin"] == 1

    def test_set_tls_trigger_invalid(self, client):
        """Test setting invalid trigger value."""
        # Trigger out of range (must be 0-8)
        response = client.post("/tls/1/trigger?trigin=10")

        assert response.status_code == 400
        assert "Trigger must be 0-8" in response.json()["detail"]


class TestTLSValidation:
    """Test TLS parameter validation."""

    def test_invalid_channel_number(self, client):
        """Test with invalid channel number."""
        # Channel too high
        response = client.get("/tls/5/config")
        assert response.status_code == 422

        # Channel too low
        response = client.get("/tls/0/config")
        assert response.status_code == 422

    def test_wavelength_validation(self, client):
        """Test wavelength range validation."""
        # Test with valid values at boundaries
        config_data = {
            "start_wavelength_nm": 1460.0,
            "stop_wavelength_nm": 1640.0
        }
        response = client.post("/tls/1/config", json=config_data)
        assert response.status_code == 200

    def test_speed_validation(self, client):
        """Test sweep speed validation."""
        # Valid speed range (5-200)
        config_data = {"sweep_speed_nmps": 100}
        response = client.post("/tls/1/config", json=config_data)
        assert response.status_code == 200

    def test_power_validation(self, client):
        """Test laser power validation."""
        # Valid power range (-10 to 10)
        config_data = {"laser_power_dbm": 5.0}
        response = client.post("/tls/1/config", json=config_data)
        assert response.status_code == 200


class TestTLSNotConnected:
    """Test TLS endpoints when not connected."""

    def test_tls_config_not_connected(self, disconnected_client):
        """Test TLS config fails when not connected."""
        response = disconnected_client.get("/tls/1/config")

        assert response.status_code == 503
        assert "Not connected" in response.json()["detail"]

    def test_set_tls_config_not_connected(self, disconnected_client):
        """Test setting TLS config fails when not connected."""
        config_data = {"laser_power_dbm": 5.0}
        response = disconnected_client.post("/tls/1/config", json=config_data)

        assert response.status_code == 503
