# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status, Cookie
from typing import Optional, Annotated, Dict, Any
import logging

from app.auth.auth_client import auth_client

logger = logging.getLogger(__name__)


class AuthUser:
    """Represents an authenticated user from auth service"""
    
    def __init__(self, claims: Dict[str, Any]):
        self.id = claims.get("sub")  # User ID
        self.username = claims.get("username")
        self.role = claims.get("role")
    
    def is_property_owner(self) -> bool:
        """Check if user is a property owner"""
        return self.role == "PROPERTY_OWNER"
    
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == "ADMIN"
    
    def is_user(self) -> bool:
        """Check if user is a regular user"""
        return self.role == "USER"


async def get_current_user(
    access_token: Annotated[Optional[str], Cookie()] = None
) -> AuthUser:
    """
    Get current authenticated user by validating token with auth service
    
    Args:
        access_token: JWT token from cookie
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Validate token with auth service
    claims = await auth_client.introspect_token(access_token)
    
    return AuthUser(claims)


async def get_current_property_owner(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Get current property owner user (requires PROPERTY_OWNER role)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current property owner user
        
    Raises:
        HTTPException: If user is not a property owner
    """
    if not current_user.is_property_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property owner permission required"
        )
    return current_user


async def get_current_admin(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
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
            detail="Admin permission required"
        )
    return current_user
