from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user, AuthUser

router = APIRouter(tags=["auth"])

@router.get("/auth/me", summary="Get current authenticated user")
async def get_me(current_user: AuthUser = Depends(get_current_user)):
    """
    Returns the authenticated user's info (id, username, role).
    Requires valid access_token cookie.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }
