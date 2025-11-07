"""
Tests for health check endpoints
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.controllers
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["message"] == "Real Estate Management API"
    
    def test_health_check_basic(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_health_check_detailed(self, client: TestClient):
        """Test detailed health check endpoint"""
        response = client.get("/api/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "database" in data
        assert "api" in data
        assert "checks" in data
        assert data["api"] == "running"
