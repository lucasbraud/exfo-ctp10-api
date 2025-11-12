"""Tests for detector endpoints."""

import pytest


class TestDetectorSnapshot:
    """Test detector snapshot endpoint (all 4 channels)."""

    def test_get_detector_snapshot_default_module(self, client):
        """Test getting detector snapshot with default module."""
        response = client.get("/detector/snapshot")

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "timestamp" in data
        assert data["module"] == 4  # Default module
        assert data["wavelength_nm"] == 1310.0
        assert data["unit"] in ["dBm", "mW"]

        # Check all 4 channels present
        assert "ch1_power" in data
        assert "ch2_power" in data
        assert "ch3_power" in data
        assert "ch4_power" in data

        # Power values should be floats
        assert isinstance(data["ch1_power"], (int, float))
        assert isinstance(data["ch2_power"], (int, float))
        assert isinstance(data["ch3_power"], (int, float))
        assert isinstance(data["ch4_power"], (int, float))

    def test_get_detector_snapshot_custom_module(self, client):
        """Test getting detector snapshot with custom module."""
        response = client.get("/detector/snapshot?module=5")

        assert response.status_code == 200
        data = response.json()
        assert data["module"] == 5

    def test_get_detector_snapshot_not_connected(self, disconnected_client):
        """Test detector snapshot fails when not connected."""
        response = disconnected_client.get("/detector/snapshot")

        assert response.status_code == 503
        assert "Not connected" in response.json()["detail"]


class TestDetectorConfig:
    """Test detector configuration endpoints."""

    def test_get_detector_config(self, client):
        """Test getting detector configuration."""
        response = client.get("/detector/config?module=4&channel=1")

        assert response.status_code == 200
        data = response.json()
        assert data["module"] == 4
        assert data["channel"] == 1
        assert "power_unit" in data
        assert "spectral_unit" in data

    def test_set_detector_config(self, client):
        """Test setting detector configuration."""
        config_data = {
            "power_unit": "DBM",
            "spectral_unit": "WAV"
        }

        response = client.post(
            "/detector/config?module=4&channel=1",
            json=config_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_set_detector_config_partial(self, client):
        """Test setting partial detector configuration."""
        config_data = {
            "power_unit": "DBM"
        }

        response = client.post(
            "/detector/config?module=4&channel=1",
            json=config_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDetectorReference:
    """Test detector reference creation."""

    def test_create_reference(self, client):
        """Test creating reference trace."""
        response = client.post("/detector/reference?module=4&channel=1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Reference created" in data["message"]


class TestTraceMetadata:
    """Test trace metadata endpoint."""

    def test_get_trace_metadata(self, client):
        """Test getting trace metadata."""
        response = client.get(
            "/detector/trace/metadata?module=4&channel=1&trace_type=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["module"] == 4
        assert data["channel"] == 1
        assert data["trace_type"] == 1
        assert "num_points" in data
        assert "sampling_pm" in data
        assert "start_wavelength_nm" in data
        assert "unit" in data
        assert data["num_points"] > 0

    def test_get_trace_metadata_different_types(self, client):
        """Test getting metadata for different trace types."""
        trace_types = [1, 11, 12, 13]  # TF live, Raw live, Raw ref, Quick ref

        for trace_type in trace_types:
            response = client.get(
                f"/detector/trace/metadata?module=4&channel=1&trace_type={trace_type}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["trace_type"] == trace_type


class TestTraceData:
    """Test trace data retrieval endpoints."""

    def test_get_trace_data_json(self, client):
        """Test getting trace data in JSON format."""
        response = client.get(
            "/detector/trace/data?module=4&channel=1&trace_type=1"
        )

        assert response.status_code == 200
        data = response.json()

        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["module"] == 4
        assert data["metadata"]["channel"] == 1

        # Check data arrays
        assert "wavelengths" in data
        assert "values" in data
        assert isinstance(data["wavelengths"], list)
        assert isinstance(data["values"], list)
        assert len(data["wavelengths"]) > 0
        assert len(data["wavelengths"]) == len(data["values"])

    def test_get_trace_data_binary(self, client):
        """Test getting trace data in binary format."""
        response = client.get(
            "/detector/trace/binary?module=4&channel=1&trace_type=1"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "Content-Disposition" in response.headers
        assert "trace_m4_c1_t1.npy" in response.headers["Content-Disposition"]
        assert len(response.content) > 0

    def test_get_trace_data_invalid_module(self, client):
        """Test trace data with invalid module number."""
        response = client.get(
            "/detector/trace/data?module=25&channel=1&trace_type=1"
        )

        # Should fail validation (module must be 1-20)
        assert response.status_code == 422


class TestDetectorValidation:
    """Test parameter validation for detector endpoints."""

    def test_module_out_of_range(self, client):
        """Test module parameter validation."""
        # Module too high
        response = client.get("/detector/snapshot?module=21")
        assert response.status_code == 422

        # Module too low
        response = client.get("/detector/snapshot?module=0")
        assert response.status_code == 422

    def test_channel_out_of_range(self, client):
        """Test channel parameter validation."""
        # Channel too high
        response = client.get("/detector/config?module=4&channel=7")
        assert response.status_code == 422

        # Channel too low
        response = client.get("/detector/config?module=4&channel=0")
        assert response.status_code == 422

    def test_trace_type_out_of_range(self, client):
        """Test trace_type parameter validation."""
        # Trace type too high
        response = client.get(
            "/detector/trace/metadata?module=4&channel=1&trace_type=25"
        )
        assert response.status_code == 422

        # Trace type too low
        response = client.get(
            "/detector/trace/metadata?module=4&channel=1&trace_type=0"
        )
        assert response.status_code == 422
