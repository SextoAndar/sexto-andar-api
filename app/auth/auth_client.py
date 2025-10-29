# app/auth/auth_client.py
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging

from app.settings import settings

logger = logging.getLogger(__name__)


class AuthClient:
    """Client to communicate with sexto-andar-auth service"""
    
    def __init__(self):
        self.auth_service_url = settings.AUTH_SERVICE_URL
        self.timeout = 10.0  # 10 seconds timeout
    
    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Validate token with auth service
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token introspection response with user claims
            
        Raises:
            HTTPException: If token is invalid or service is unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/auth/introspect",
                    json={"token": token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("active"):
                        return data.get("claims", {})
                    else:
                        reason = data.get("reason", "Token is not active")
                        logger.warning(f"Token validation failed: {reason}")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid token: {reason}"
                        )
                else:
                    logger.error(f"Auth service returned status {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token validation failed"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to auth service")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to auth service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating token"
            )


# Global auth client instance
auth_client = AuthClient()
