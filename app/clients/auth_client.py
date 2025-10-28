"""Cliente HTTP para validação remota de tokens com o serviço de autenticação."""

import httpx
import logging
from typing import Optional, Dict, Any
from app.settings import settings

logger = logging.getLogger(__name__)


class AuthServiceClient:
    """Cliente para comunicação com o serviço remoto de autenticação (sexto-andar-auth)."""
    
    def __init__(self, base_url: str):
        """
        Inicializa o cliente do serviço de auth.
        
        Args:
            base_url: URL base do serviço de auth (ex: http://localhost:8001)
        """
        self.base_url = base_url.rstrip('/')
        self.introspect_url = f"{self.base_url}/api/v1/auth/introspect"
        self.timeout = 5.0  # 5 segundos
    
    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Valida um token JWT remotamente via o serviço de auth.
        
        Args:
            token: JWT token a validar
            
        Returns:
            Dict com {"active": bool, "claims": dict, "reason": str}
            
        Example:
            {
                "active": True,
                "claims": {"sub": "user-id", "role": "USER", "exp": 1234567890}
            }
            ou
            {
                "active": False,
                "reason": "invalid_or_expired"
            }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.introspect_url,
                    json={"token": token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Auth service returned {response.status_code}")
                    return {"active": False, "reason": "service_error"}
                    
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to auth service: {e}")
            return {"active": False, "reason": "connection_error"}
        except httpx.TimeoutException as e:
            logger.error(f"Auth service request timeout: {e}")
            return {"active": False, "reason": "timeout"}
        except Exception as e:
            logger.error(f"Unexpected error calling auth service: {e}")
            return {"active": False, "reason": "unknown_error"}


# Instância global do cliente (inicializada com URL da settings)
_auth_client: Optional[AuthServiceClient] = None


def get_auth_client() -> Optional[AuthServiceClient]:
    """Obtém a instância global do cliente de auth, se configurado."""
    global _auth_client
    
    if _auth_client is None and settings.AUTH_SERVICE_URL:
        _auth_client = AuthServiceClient(settings.AUTH_SERVICE_URL)
    
    return _auth_client
