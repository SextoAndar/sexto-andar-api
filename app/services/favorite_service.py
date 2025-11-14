# app/services/favorite_service.py
from sqlalchemy.orm import Session
from app.models.favorite import Favorite
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.property_repository import PropertyRepository
from fastapi import HTTPException, status
from typing import Tuple, List
from uuid import UUID


class FavoriteService:
    """Service for Favorite business logic"""
    
    def __init__(self, db: Session):
        self.repository = FavoriteRepository(db)
        self.property_repo = PropertyRepository(db)
    
    def add_favorite(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> Favorite:
        """Add property to user's favorites (US05)"""
        # Check if property exists and is active
        property_obj = self.property_repo.get_by_id(property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        if not property_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot favorite an inactive property"
            )
        
        # Check if already favorited
        existing = self.repository.get_by_user_and_property(user_id, property_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Property is already in your favorites"
            )
        
        # Create favorite
        favorite = Favorite(
            idUser=user_id,
            idProperty=property_id
        )
        
        return self.repository.create(favorite)
    
    def remove_favorite(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> None:
        """Remove property from user's favorites (US06)"""
        favorite = self.repository.get_by_user_and_property(user_id, property_id)
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property is not in your favorites"
            )
        
        self.repository.delete(favorite)
    
    def get_user_favorites(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        active_only: bool = True
    ) -> Tuple[List[Favorite], int]:
        """Get all favorites for a user (US07)"""
        return self.repository.get_by_user(
            user_id=user_id,
            page=page,
            size=size,
            active_only=active_only
        )
    
    def is_favorited(self, user_id: UUID, property_id: UUID) -> bool:
        """Check if property is favorited by user"""
        return self.repository.is_favorited(user_id, property_id)
