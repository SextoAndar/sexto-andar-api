# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status, Cookie
from typing import Optional, Annotated
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db
from app.models.account import Account, RoleEnum
from app.auth.jwt_handler import verify_token
from app.clients.auth_client import get_auth_client
from app.settings import settings

logger = logging.getLogger(__name__)

async def get_current_user(
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: Session = Depends(get_db)
) -> Account:
    """
    Get current authenticated user from JWT cookie.
    
    Valida o token de duas formas:
    1. Se AUTH_SERVICE_URL está configurado, valida remotamente
    2. Caso contrário, valida localmente
    
    Args:
        access_token: JWT token from cookie
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token:
        raise credentials_exception
    
    # Tentar validar remotamente se configurado
    auth_client = get_auth_client()
    if auth_client:
        logger.info("Validando token remotamente via serviço de auth")
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
                logger.warning("Token válido mas sem user_id")
                raise credentials_exception
                
        except Exception as e:
            logger.error(f"Erro ao validar token remotamente: {e}")
            raise credentials_exception
    else:
        # Validação local (fallback)
        logger.info("Validando token localmente (sem serviço remoto)")
        payload = verify_token(access_token)
        
        if not payload:
            raise credentials_exception
        
        user_id = payload.get("sub")
        
        if not user_id:
            raise credentials_exception
    
    # Buscar usuário no banco de dados
    user = db.query(Account).filter(Account.id == user_id).first()
    if not user:
        logger.warning(f"Usuário {user_id} não encontrado no banco")
        raise credentials_exception
    
    return user

async def get_current_admin_user(
    current_user: Account = Depends(get_current_user)
) -> Account:
    """
    Get current admin user (requires ADMIN role)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_active_user(
    current_user: Account = Depends(get_current_user)
) -> Account:
    """
    Get current active user (any authenticated user)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
    """
    return current_user
