# app/repositories/favorite_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from app.models.favorite import Favorite
from app.models.property import Property
from typing import Optional, List, Tuple
from uuid import UUID


class FavoriteRepository:
    """Repository for Favorite database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, favorite: Favorite) -> Favorite:
        """Add property to favorites"""
        self.db.add(favorite)
        self.db.commit()
        self.db.refresh(favorite)
        return favorite
    
    def get_by_user_and_property(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> Optional[Favorite]:
        """Check if property is favorited by user"""
        return self.db.query(Favorite).filter(
            and_(
                Favorite.idUser == user_id,
                Favorite.idProperty == property_id
            )
        ).first()
    
    def get_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        active_only: bool = True
    ) -> Tuple[List[Favorite], int]:
        """Get all favorites for a user with pagination"""
        query = self.db.query(Favorite)\
            .options(joinedload(Favorite.property).joinedload(Property.address))\
            .filter(Favorite.idUser == user_id)
        
        # Filter by active properties only
        if active_only:
            query = query.join(Property)\
                .filter(Property.is_active == True)
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering (most recent first)
        favorites = query.order_by(desc(Favorite.created_at))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return favorites, total
    
    def delete(self, favorite: Favorite) -> None:
        """Remove property from favorites"""
        self.db.delete(favorite)
        self.db.commit()
    
    def count_by_property(self, property_id: UUID) -> int:
        """Count how many users favorited a property"""
        return self.db.query(Favorite)\
            .filter(Favorite.idProperty == property_id)\
            .count()
    
    def count_by_user(self, user_id: UUID) -> int:
        """Count how many favorites a user has (US08)"""
        return self.db.query(Favorite)\
            .filter(Favorite.idUser == user_id)\
            .count()
    
    def is_favorited(self, user_id: UUID, property_id: UUID) -> bool:
        """Check if user has favorited a property"""
        return self.get_by_user_and_property(user_id, property_id) is not None
