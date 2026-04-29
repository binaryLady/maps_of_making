import pytest
import json
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_validate_url_with_required_fields():
    """Test validation of URL with mom:required fields."""
    test_data = {
        "schema:name": "FabLab Brussels",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        }
    }
    # This test would require mocking the HTTP fetch, which is complex.
    # In practice, this would be an end-to-end test with a real endpoint.


def test_validate_url_with_card_fields():
    """Test validation of URL with mom:card fields."""
    test_data = {
        "schema:name": "FabLab Brussels",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "schema:url": "https://fablab.be",
        "schema:openingHours": "Mo-Fr 10:00-18:00"
    }
    # This test would require mocking the HTTP fetch


def test_raw_endpoint_returns_404_for_nonexistent_space():
    """Test that raw endpoint returns 404-style JSON for nonexistent space."""
    response = client.get("/api/space/nonexistent-space/raw")
    assert response.status_code == 200
    data = response.json()
    assert data.get("error") == "no_snapshot"
    assert "message" in data


def test_raw_endpoint_structure():
    """Test the structure of the raw endpoint response."""
    # We can't test success without data in Oxigraph,
    # but we can verify the error response structure is correct
    response = client.get("/api/space/test-space/raw")
    assert response.status_code == 200
    data = response.json()
    # Should have either 'raw' or 'error' field
    assert "raw" in data or "error" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_snapshots_endpoint_empty():
    """Test snapshots endpoint for nonexistent space."""
    response = client.get("/api/space/nonexistent-space/snapshots")
    assert response.status_code == 200
    # Should return empty list
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


