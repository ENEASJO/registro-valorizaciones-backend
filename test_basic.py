import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test that the root endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data

def test_health_endpoint():
    """Test that the health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_debug_headers_endpoint():
    """Test that the debug headers endpoint returns 200"""
    response = client.get("/debug/headers")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "headers" in data

def test_obras_endpoint():
    """Test that the obras endpoint returns 200"""
    response = client.get("/obras")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

def test_valorizaciones_endpoint():
    """Test that the valorizaciones endpoint returns 200"""
    response = client.get("/valorizaciones")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data