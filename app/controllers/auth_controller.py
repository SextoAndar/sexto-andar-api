# app/controllers/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.dtos.auth_dto import LoginRequest, LoginResponse, RegisterUserRequest, RegisterPropertyOwnerRequest, AuthUser
from app.auth.jwt_handler import get_token_expiry

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    
    Authenticates user and sets JWT cookie
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create JWT token
    access_token = auth_service.create_user_token(user)
    
    # Set HTTP-only cookie with JWT token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevent XSS attacks
        secure=False,   # Set to True in production with HTTPS
        samesite="lax", # CSRF protection
        max_age=int(get_token_expiry().total_seconds())
    )
    
    # Return response
    user_data = AuthUser.model_validate(user)
    return LoginResponse(
        access_token=access_token,
        user=user_data.model_dump()
    )

@router.post("/register/user", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
async def register_user(
    register_data: RegisterUserRequest,
    db: Session = Depends(get_db)
):
    """
    User registration endpoint
    
    Creates a new USER account
    """
    auth_service = AuthService(db)
    user = auth_service.register_user(register_data)
    return AuthUser.model_validate(user)

@router.post("/register/property-owner", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
async def register_property_owner(
    register_data: RegisterPropertyOwnerRequest,
    db: Session = Depends(get_db)
):
    """
    Property owner registration endpoint
    
    Creates a new PROPERTY_OWNER account
    """
    auth_service = AuthService(db)
    owner = auth_service.register_property_owner(register_data)
    return AuthUser.model_validate(owner)

@router.post("/logout")
async def logout(response: Response):
    """
    User logout endpoint
    
    Clears the JWT cookie
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return {"message": "Successfully logged out"}
