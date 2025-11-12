"""Tests for connection endpoints."""

import pytest


class TestConnectionEndpoints:
    """Test connection and status endpoints."""

    def test_get_connection_status_connected(self, client):
        """Test getting connection status when connected."""
        response = client.get("/connection/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["instrument_id"] == "EXFO,CTP10,12345678,1.2.3"
        assert "address" in data

    def test_get_connection_status_disconnected(self, disconnected_client):
        """Test getting connection status when not connected."""
        response = disconnected_client.get("/connection/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["instrument_id"] is None

    def test_disconnect(self, client):
        """Test disconnecting from instrument."""
        response = client.post("/connection/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Disconnected successfully" in data["message"]

    def test_get_condition_register_idle(self, client):
        """Test getting condition register when idle."""
        response = client.get("/connection/condition")

        assert response.status_code == 200
        data = response.json()
        assert data["register_value"] == 0
        assert data["is_idle"] is True
        assert data["bits"]["zeroing"] is False
        assert data["bits"]["scanning"] is False
        assert "bits" in data

    def test_get_condition_register_not_connected(self, disconnected_client):
        """Test condition register fails when not connected."""
        response = disconnected_client.get("/connection/condition")

        assert response.status_code == 503
        assert "Not connected" in response.json()["detail"]

    def test_check_errors_no_errors(self, client):
        """Test error checking when no errors present."""
        response = client.post("/connection/check_errors")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "No errors" in data["message"]

    def test_check_errors_not_connected(self, disconnected_client):
        """Test error checking fails when not connected."""
        response = disconnected_client.post("/connection/check_errors")

        assert response.status_code == 503


class TestRootEndpoints:
    """Test root and health endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "EXFO CTP10 Vector Analyzer API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    def test_health_check_connected(self, client):
        """Test health check when connected."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is True
        assert "timestamp" in data

    def test_health_check_disconnected(self, disconnected_client):
        """Test health check when disconnected."""
        response = disconnected_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is False
        assert "timestamp" in data
