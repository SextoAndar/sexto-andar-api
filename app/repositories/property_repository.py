# app/repositories/property_repository.py
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.property import Property, PropertyTypeEnum, SalesTypeEnum
from app.models.address import Address


class PropertyRepository:
    """Repository for Property operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, property_id: str) -> Optional[Property]:
        """Get property by ID with address"""
        return (
            self.db.query(Property)
            .options(joinedload(Property.address))
            .filter(Property.id == property_id)
            .first()
        )
    
    def get_by_owner(self, owner_id: str, page: int = 1, size: int = 10) -> Tuple[List[Property], int]:
        """Get properties by owner with pagination"""
        query = (
            self.db.query(Property)
            .options(joinedload(Property.address))
            .filter(Property.idPropertyOwner == owner_id)
        )
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        offset = (page - 1) * size
        properties = query.offset(offset).limit(size).all()
        
        return properties, total
    
    def get_all_paginated(
        self, 
        page: int = 1, 
        size: int = 10,
        property_type: Optional[PropertyTypeEnum] = None,
        sales_type: Optional[SalesTypeEnum] = None,
        active_only: bool = True
    ) -> Tuple[List[Property], int]:
        """Get all properties with pagination and filters"""
        query = (
            self.db.query(Property)
            .options(joinedload(Property.address))
        )
        
        # Apply filters
        if active_only:
            query = query.filter(Property.is_active == True)
        
        if property_type:
            query = query.filter(Property.propertyType == property_type)
        
        if sales_type:
            query = query.filter(Property.salesType == sales_type)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        offset = (page - 1) * size
        properties = query.offset(offset).limit(size).all()
        
        return properties, total
    
    def create(self, property_obj: Property) -> Property:
        """Create new property"""
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj
    
    def update(self, property_obj: Property) -> Property:
        """Update existing property"""
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj
    
    def delete(self, property_obj: Property) -> None:
        """Delete property (hard delete)"""
        self.db.delete(property_obj)
        self.db.commit()
    
    def deactivate(self, property_obj: Property) -> Property:
        """Deactivate property (soft delete)"""
        property_obj.is_active = False
        return self.update(property_obj)
    
    def activate(self, property_obj: Property) -> Property:
        """Activate property"""
        property_obj.is_active = True
        return self.update(property_obj)
    
    def count_by_owner(self, owner_id: str) -> int:
        """Count total properties by owner"""
        return (
            self.db.query(Property)
            .filter(Property.idPropertyOwner == owner_id)
            .count()
        )
    
    def count_active_by_owner(self, owner_id: str) -> int:
        """Count active properties by owner"""
        return (
            self.db.query(Property)
            .filter(Property.idPropertyOwner == owner_id, Property.is_active == True)
            .count()
        )
