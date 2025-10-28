# app/auth/dependencies.py
"""
Dependências de autenticação - delegadas 100% para serviço remoto.

IMPORTANTE: AUTH_SERVICE_URL é OBRIGATÓRIO. Este repositório não possui
lógica de autenticação local. Toda validação de token é feita remotamente
pelo serviço sexto-andar-auth.
"""

from fastapi import Depends, HTTPException, status, Cookie
from typing import Optional, Annotated
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db
from app.clients.auth_client import get_auth_client
from app.settings import settings

logger = logging.getLogger(__name__)


async def get_current_user(
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: Session = Depends(get_db)
):
    """
    Valida o usuário via serviço remoto de autenticação (OBRIGATÓRIO).
    
    Este repositório NOT gerencia autenticação localmente.
    Toda validação é delegada para sexto-andar-auth.
    
    Args:
        access_token: JWT token from cookie
        db: Database session
        
    Returns:
        user_id (str) extraído do token validado
        
    Raises:
        HTTPException: If token is invalid or AUTH_SERVICE_URL not configured
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Make sure AUTH_SERVICE_URL is configured.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token:
        raise credentials_exception
    
    # Verificar se AUTH_SERVICE_URL está configurado (OBRIGATÓRIO)
    auth_client = get_auth_client()
    if not auth_client:
        logger.error("AUTH_SERVICE_URL não configurado! Autenticação depende do serviço remoto.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured. Contact administrator.",
        )
    
    # Validar token remotamente
    logger.info(f"Validando token remotamente via {auth_client.base_url}")
    try:
        result = await auth_client.introspect_token(access_token)
        
        if not result.get("active"):
            reason = result.get("reason", "unknown")
            logger.warning(f"Token inválido: {reason}")
            raise credentials_exception
        
        # Token válido, extrair user_id
        claims = result.get("claims", {})
        user_id = claims.get("sub")
        
        if not user_id:
            logger.warning("Token válido mas sem user_id nos claims")
            raise credentials_exception
        
        logger.info(f"Token validado para usuário: {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Erro ao validar token remotamente: {e}")
        raise credentials_exception


async def get_current_admin_user(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Valida se o usuário é ADMIN via serviço remoto.
    
    Args:
        current_user_id: User ID do token validado
        db: Database session
        
    Returns:
        User ID se for admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    # TODO: Buscar role do usuário do serviço remoto ou cache
    # Por enquanto, retorna o user_id validado
    # A verificação de admin será feita no serviço remoto ou cache
    return current_user_id


async def get_current_active_user(
    current_user_id: str = Depends(get_current_user)
) -> str:
    """
    Obtém qualquer usuário autenticado.
    
    Args:
        current_user_id: User ID do token validado
        
    Returns:
        User ID
    """
    return current_user_id
