"""Integration tests for Health API route."""

from __future__ import annotations

from fastapi.testclient import TestClient

def test_health_check_healthy(test_client: TestClient, mock_driver):
    mock_driver.verify_connectivity.return_value = None
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
