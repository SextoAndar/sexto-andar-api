"""
Tests for settings configuration
"""
import pytest
import os


class TestSettings:
    """Test application settings"""
    
    def test_settings_loads_from_env(self):
        """Test that settings loads from environment variables"""
        from app.settings import settings
        
        assert settings.API_BASE_PATH is not None
        assert settings.AUTH_SERVICE_URL is not None
    
    def test_api_base_path_default(self):
        """Test API_BASE_PATH default value"""
        from app.settings import settings
        
        assert settings.API_BASE_PATH == "/api"
    
    def test_auth_service_url_required(self):
        """Test that AUTH_SERVICE_URL is required"""
        # This is tested in conftest where we set it
        from app.settings import settings
        
        assert settings.AUTH_SERVICE_URL == "http://localhost:8001"
