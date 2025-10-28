# app/controllers/admin_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.services.account_service import AccountService
from app.dtos.account_dto import AccountListResponse, AccountResponse, UpdateAccountRequest, ChangePasswordRequest
from app.auth.dependencies import get_current_admin_user
from app.models.account import Account

# Prefix é definido no main.py via settings
router = APIRouter(tags=["admin"])

@router.get("/users", response_model=AccountListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_admin: Account = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all users and property owners.
    
    Excludes admin accounts from results.
    Requires ADMIN role.
    """
    account_service = AccountService(db)
    return account_service.get_all_non_admin_accounts(page, size)

@router.get("/users/{user_id}", response_model=AccountResponse)
async def get_user_by_id(
    user_id: str,
    current_admin: Account = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed user information by ID.
    
    Requires ADMIN role.
    """
    account_service = AccountService(db)
    return account_service.get_account_by_id(user_id)

@router.put("/users/{user_id}", response_model=AccountResponse)
async def update_user(
    user_id: str,
    update_data: UpdateAccountRequest,
    current_admin: Account = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information.
    
    Can modify name, email, and phone number.
    Requires ADMIN role.
    """
    account_service = AccountService(db)
    return account_service.update_account(user_id, update_data)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_admin: Account = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Permanently delete user account.
    
    Action cannot be undone.
    Requires ADMIN role.
    """
    account_service = AccountService(db)
    account_service.delete_account(user_id)
    return None

@router.put("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    current_admin: Account = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Change user password with current password verification.
    
    Requires current password for security.
    Requires ADMIN role.
    """
    account_service = AccountService(db)
    account_service.change_user_password(user_id, password_data)
    return None
