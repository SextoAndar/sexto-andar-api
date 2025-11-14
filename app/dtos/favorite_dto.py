# app/dtos/favorite_dto.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal


class FavoriteResponse(BaseModel):
    """Response model for favorite with property details"""
    id: UUID
    idUser: UUID
    idProperty: UUID
    created_at: datetime
    
    # Property details
    property: Optional['PropertyDetailsDTO'] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "idUser": "123e4567-e89b-12d3-a456-426614174001",
                "idProperty": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2024-12-01T10:00:00",
                "property": {
                    "id": "123e4567-e89b-12d3-a456-426614174002",
                    "propertyType": "APARTMENT",
                    "salesType": "RENT",
                    "propertyValue": 3500.00,
                    "propertySize": 85.0,
                    "description": "Beautiful apartment",
                    "address": "Main Street, 123 - São Paulo",
                    "is_active": True
                }
            }
        }
    
    @classmethod
    def from_favorite(cls, favorite):
        """Create response from Favorite model"""
        property_dto = None
        if favorite.property:
            prop = favorite.property
            # Get address
            address_str = None
            if prop.address:
                address_str = f"{prop.address.street}, {prop.address.number} - {prop.address.city}"
            
            property_dto = PropertyDetailsDTO(
                id=prop.id,
                propertyType=prop.propertyType.value,
                salesType=prop.salesType.value,
                propertyValue=prop.propertyValue,
                propertySize=prop.propertySize,
                description=prop.description,
                address=address_str,
                is_active=prop.is_active,
                condominiumFee=prop.condominiumFee,
                floor=prop.floor,
                isPetAllowed=prop.isPetAllowed
            )
        
        return cls(
            id=favorite.id,
            idUser=favorite.idUser,
            idProperty=favorite.idProperty,
            created_at=favorite.created_at,
            property=property_dto
        )


class PropertyDetailsDTO(BaseModel):
    """Property details for favorite response"""
    id: UUID
    propertyType: str
    salesType: str
    propertyValue: Decimal
    propertySize: Decimal
    description: str
    address: Optional[str] = None
    is_active: bool
    condominiumFee: Optional[Decimal] = None
    floor: Optional[int] = None
    isPetAllowed: bool
    
    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """Response model for paginated favorite list"""
    favorites: list[FavoriteResponse]
    total: int
    page: int
    size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorites": [],
                "total": 10,
                "page": 1,
                "size": 10,
                "total_pages": 1
            }
        }


class FavoriteStatusResponse(BaseModel):
    """Response for favorite/unfavorite actions"""
    message: str
    property_id: UUID
    is_favorited: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Property added to favorites",
                "property_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_favorited": True
            }
        }


class FavoritesCountResponse(BaseModel):
    """Response for user's favorites count (US08)"""
    count: int
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "count": 5,
                "message": "You have 5 favorite properties"
            }
        }
