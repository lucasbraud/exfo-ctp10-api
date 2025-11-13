"""Tests for RLaser (Reference Laser) endpoints."""

import pytest


class TestRLaserConfig:
    """Test reference laser configuration endpoints."""

    @pytest.mark.parametrize("laser_number", [1, 2, 5, 10])
    def test_get_rlaser_config(self, client, laser_number):
        """Test getting RLaser configuration for various laser numbers."""
        response = client.get(f"/rlaser/{laser_number}/config")

        assert response.status_code == 200
        data = response.json()
        assert data["laser_number"] == laser_number
        assert "id" in data
        assert "wavelength_nm" in data
        assert "power_dbm" in data
        assert "is_on" in data

        # Validate data types
        assert isinstance(data["id"], str)
        assert isinstance(data["wavelength_nm"], (int, float))
        assert isinstance(data["power_dbm"], (int, float))
        assert isinstance(data["is_on"], bool)

    def test_set_rlaser_config_full(self, client):
        """Test setting complete RLaser configuration."""
        config_data = {
            "wavelength_nm": 1550.5,
            "power_dbm": 8.0,
            "power_state": True
        }

        response = client.post("/rlaser/1/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "configured successfully" in data["message"]

        # Verify configuration was applied
        verify_response = client.get("/rlaser/1/config")
        verify_data = verify_response.json()
        assert verify_data["wavelength_nm"] == 1550.5
        assert verify_data["power_dbm"] == 8.0
        assert verify_data["is_on"] is True

    def test_set_rlaser_config_partial(self, client):
        """Test setting partial RLaser configuration."""
        config_data = {
            "power_dbm": 6.5
        }

        response = client.post("/rlaser/1/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify only power changed
        verify_response = client.get("/rlaser/1/config")
        verify_data = verify_response.json()
        assert verify_data["power_dbm"] == 6.5


class TestRLaserID:
    """Test reference laser identification endpoints."""

    def test_get_rlaser_id(self, client):
        """Test getting RLaser identification."""
        response = client.get("/rlaser/1/id")

        assert response.status_code == 200
        data = response.json()
        assert data["laser_number"] == 1
        assert "id" in data
        assert "manufacturer" in data
        assert "model" in data
        assert "serial" in data
        assert "firmware" in data

        # ID should contain EXFO
        assert "EXFO" in data["id"]

    def test_get_rlaser_id_parsed(self, client):
        """Test that RLaser ID is properly parsed."""
        response = client.get("/rlaser/1/id")

        assert response.status_code == 200
        data = response.json()

        # Check parsed components
        assert data["manufacturer"] == "EXFO"
        assert data["model"] is not None
        assert len(data["model"]) > 0


class TestRLaserPower:
    """Test reference laser power endpoints."""

    def test_get_rlaser_power(self, client):
        """Test getting RLaser power setting."""
        response = client.get("/rlaser/1/power")

        assert response.status_code == 200
        data = response.json()
        assert data["laser_number"] == 1
        assert "power_dbm" in data
        assert isinstance(data["power_dbm"], (int, float))

    def test_set_rlaser_power(self, client):
        """Test setting RLaser power."""
        response = client.post("/rlaser/1/power?power_dbm=7.5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["laser_number"] == 1
        assert data["power_dbm"] == 7.5

        # Verify power was set
        verify_response = client.get("/rlaser/1/power")
        verify_data = verify_response.json()
        assert verify_data["power_dbm"] == 7.5


class TestRLaserWavelength:
    """Test reference laser wavelength endpoints."""

    def test_get_rlaser_wavelength(self, client):
        """Test getting RLaser wavelength."""
        response = client.get("/rlaser/1/wavelength")

        assert response.status_code == 200
        data = response.json()
        assert data["laser_number"] == 1
        assert "wavelength_nm" in data
        assert isinstance(data["wavelength_nm"], (int, float))

    def test_set_rlaser_wavelength(self, client):
        """Test setting RLaser wavelength."""
        response = client.post("/rlaser/1/wavelength?wavelength_nm=1550.123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["laser_number"] == 1
        assert data["wavelength_nm"] == 1550.123

        # Verify wavelength was set
        verify_response = client.get("/rlaser/1/wavelength")
        verify_data = verify_response.json()
        assert verify_data["wavelength_nm"] == 1550.123


class TestRLaserState:
    """Test reference laser state (on/off) endpoints."""

    def test_get_rlaser_state(self, client):
        """Test getting RLaser state."""
        response = client.get("/rlaser/1/state")

        assert response.status_code == 200
        data = response.json()
        assert data["laser_number"] == 1
        assert "is_on" in data
        assert "state" in data
        assert isinstance(data["is_on"], bool)

    def test_turn_on_rlaser(self, client):
        """Test turning on RLaser."""
        response = client.post("/rlaser/1/on")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["laser_number"] == 1
        assert data["is_on"] is True

        # Verify laser is on
        verify_response = client.get("/rlaser/1/state")
        verify_data = verify_response.json()
        assert verify_data["is_on"] is True

    def test_turn_off_rlaser(self, client):
        """Test turning off RLaser."""
        # First turn it on
        client.post("/rlaser/1/on")

        # Then turn it off
        response = client.post("/rlaser/1/off")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["laser_number"] == 1
        assert data["is_on"] is False

        # Verify laser is off
        verify_response = client.get("/rlaser/1/state")
        verify_data = verify_response.json()
        assert verify_data["is_on"] is False

    def test_rlaser_state_toggle(self, client):
        """Test toggling RLaser state multiple times."""
        # Initial state
        initial_response = client.get("/rlaser/1/state")
        initial_state = initial_response.json()["is_on"]

        # Turn on
        client.post("/rlaser/1/on")
        verify1 = client.get("/rlaser/1/state")
        assert verify1.json()["is_on"] is True

        # Turn off
        client.post("/rlaser/1/off")
        verify2 = client.get("/rlaser/1/state")
        assert verify2.json()["is_on"] is False

        # Turn on again
        client.post("/rlaser/1/on")
        verify3 = client.get("/rlaser/1/state")
        assert verify3.json()["is_on"] is True


class TestRLaserValidation:
    """Test RLaser parameter validation."""

    def test_invalid_laser_number_low(self, client):
        """Test with laser number too low."""
        response = client.get("/rlaser/0/config")
        assert response.status_code == 422

    def test_invalid_laser_number_high(self, client):
        """Test with laser number too high."""
        response = client.get("/rlaser/11/config")
        assert response.status_code == 422

    def test_valid_laser_number_boundaries(self, client):
        """Test valid laser numbers at boundaries."""
        # Laser 1 (minimum)
        response1 = client.get("/rlaser/1/config")
        assert response1.status_code == 200

        # Laser 10 (maximum)
        response10 = client.get("/rlaser/10/config")
        assert response10.status_code == 200


class TestRLaserMultipleLasers:
    """Test operations with multiple lasers."""

    def test_configure_multiple_lasers(self, client):
        """Test configuring multiple lasers independently."""
        # Configure laser 1
        config1 = {"wavelength_nm": 1530.0, "power_dbm": 5.0}
        client.post("/rlaser/1/config", json=config1)

        # Configure laser 2
        config2 = {"wavelength_nm": 1550.0, "power_dbm": 7.0}
        client.post("/rlaser/2/config", json=config2)

        # Verify laser 1
        verify1 = client.get("/rlaser/1/config")
        data1 = verify1.json()
        assert data1["wavelength_nm"] == 1530.0
        assert data1["power_dbm"] == 5.0

        # Verify laser 2
        verify2 = client.get("/rlaser/2/config")
        data2 = verify2.json()
        assert data2["wavelength_nm"] == 1550.0
        assert data2["power_dbm"] == 7.0

    def test_different_states_multiple_lasers(self, client):
        """Test different states for multiple lasers."""
        # Turn on laser 1
        client.post("/rlaser/1/on")

        # Turn off laser 2
        client.post("/rlaser/2/off")

        # Verify states are independent
        state1 = client.get("/rlaser/1/state").json()
        state2 = client.get("/rlaser/2/state").json()

        assert state1["is_on"] is True
        assert state2["is_on"] is False


class TestRLaserNotConnected:
    """Test RLaser endpoints when not connected."""

    def test_rlaser_config_not_connected(self, disconnected_client):
        """Test RLaser config fails when not connected."""
        response = disconnected_client.get("/rlaser/1/config")

        assert response.status_code == 503
        assert "Not connected" in response.json()["detail"]

    def test_set_rlaser_power_not_connected(self, disconnected_client):
        """Test setting RLaser power fails when not connected."""
        response = disconnected_client.post("/rlaser/1/power?power_dbm=5.0")

        assert response.status_code == 503
