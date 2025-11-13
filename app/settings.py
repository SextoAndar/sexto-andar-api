import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Settings:
    """
    Application configuration - reads environment variables with base defaults.
    
    IMPORTANT: AUTH_SERVICE_URL is REQUIRED for the application to function.
    This repository delegates 100% of authentication to sexto-andar-auth.
    """
    
    # Base values (defaults)
    _API_BASE_PATH: str = "/api"
    _API_VERSION: str = "v1"
    _ALLOW_ORIGINS: List[str] = ["*"]
    _DEBUG: bool = False
    
    def __init__(self):
        """Initialize configuration by reading from .env if available."""
        # API
        self.API_BASE_PATH: str = os.getenv("API_BASE_PATH", self._API_BASE_PATH)
        self.API_VERSION: str = os.getenv("API_VERSION", self._API_VERSION)
        
        # CORS - parse comma-separated string or use default
        origins_str = os.getenv("ALLOW_ORIGINS", "*")
        self.ALLOW_ORIGINS: List[str] = [o.strip() for o in origins_str.split(",")] if origins_str else self._ALLOW_ORIGINS
        
        # Debug
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # Remote authentication service - REQUIRED
        self.AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "").strip()
        
        if not self.AUTH_SERVICE_URL:
            raise ValueError(
                "❌ AUTH_SERVICE_URL not configured!\n"
                "This service delegates 100% of authentication to sexto-andar-auth.\n"
                "Set the AUTH_SERVICE_URL environment variable.\n"
                "Example: AUTH_SERVICE_URL=http://localhost:8001"
            )
        
        # JWT Secret - must match auth service
        self.JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
        
        # Internal API secret for inter-service communication
        self.INTERNAL_API_SECRET: str = os.getenv("INTERNAL_API_SECRET", "")
        
        if not self.INTERNAL_API_SECRET:
            import secrets
            # Generate a random secret if not configured (dev only)
            self.INTERNAL_API_SECRET = secrets.token_urlsafe(32)
            if self.DEBUG:
                print(f"⚠️  Generated temporary INTERNAL_API_SECRET: {self.INTERNAL_API_SECRET}")
                print("   Set INTERNAL_API_SECRET in .env for production!")
    
    @property
    def root_prefix(self) -> str:
        """Returns the base API prefix, e.g., /api/v1"""
        base = self.API_BASE_PATH.rstrip('/')
        version = self.API_VERSION.strip('/')
        return f"{base}/{version}"
    
    def api_route(self, route: str) -> str:
        """Compose a full route combining root_prefix + route."""
        if not route:
            return self.root_prefix
        return f"{self.root_prefix.rstrip('/')}/{route.lstrip('/')}"


# Global instance
settings = Settings()
