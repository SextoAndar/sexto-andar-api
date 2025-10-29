# app/controllers/property_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.connection import get_db
from app.services.property_service import PropertyService
from app.dtos.property_dto import (
    CreateHouseRequest,
    CreateApartmentRequest,
    UpdatePropertyRequest,
    PropertyResponse,
    PropertyListResponse,
    AddressResponse
)
from app.auth.dependencies import get_current_property_owner, get_current_user, AuthUser

router = APIRouter(tags=["properties"])


@router.post(
    "/houses",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register House (US14)"
)
async def create_house(
    house_data: CreateHouseRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Register a new **house** property (US14).
    
    **Required role:** PROPERTY_OWNER
    
    **House-specific fields:**
    - `landPrice`: Price of the land/terrain
    - `isSingleHouse`: Whether it's a single house on the land
    
    **Common fields:**
    - `address`: Complete property address (street, number, city, postal_code, country)
    - `propertySize`: Size in square meters
    - `description`: Property description (min 10 chars)
    - `propertyValue`: Property value/price
    - `salesType`: 'rent' or 'sale'
    """
    property_service = PropertyService(db)
    house = property_service.create_house(house_data, current_owner.id)
    
    return PropertyResponse.model_validate(house)


@router.post(
    "/apartments",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Apartment (US15)"
)
async def create_apartment(
    apartment_data: CreateApartmentRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Register a new **apartment** property (US15).
    
    **Required role:** PROPERTY_OWNER
    
    **Apartment-specific fields:**
    - `condominiumFee`: Monthly condominium fee
    - `commonArea`: Whether it has common/recreational areas
    - `floor`: Floor number (can be negative for basements)
    - `isPetAllowed`: Whether pets are allowed
    
    **Common fields:**
    - `address`: Complete property address (street, number, city, postal_code, country)
    - `propertySize`: Size in square meters
    - `description`: Property description (min 10 chars)
    - `propertyValue`: Property value/price
    - `salesType`: 'rent' or 'sale'
    """
    property_service = PropertyService(db)
    apartment = property_service.create_apartment(apartment_data, current_owner.id)
    
    return PropertyResponse.model_validate(apartment)


@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get Property by ID"
)
async def get_property(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Get property details by ID.
    
    **Public endpoint** - no authentication required.
    """
    property_service = PropertyService(db)
    property_obj = property_service.get_property_by_id(property_id)
    
    return PropertyResponse.model_validate(property_obj)


@router.get(
    "/",
    response_model=PropertyListResponse,
    summary="List All Properties"
)
async def list_properties(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    property_type: Optional[str] = Query(None, description="Filter by type: 'house' or 'apartment'"),
    sales_type: Optional[str] = Query(None, description="Filter by sales type: 'rent' or 'sale'"),
    active_only: bool = Query(True, description="Show only active properties"),
    db: Session = Depends(get_db)
):
    """
    List all properties with pagination and filters.
    
    **Public endpoint** - no authentication required.
    
    **Filters:**
    - `property_type`: Filter by 'house' or 'apartment'
    - `sales_type`: Filter by 'rent' or 'sale'
    - `active_only`: Show only active properties (default: true)
    """
    property_service = PropertyService(db)
    properties, total = property_service.get_all_properties(
        page=page,
        size=size,
        property_type=property_type,
        sales_type=sales_type,
        active_only=active_only
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return PropertyListResponse(
        properties=[PropertyResponse.model_validate(p) for p in properties],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/owner/my-properties",
    response_model=PropertyListResponse,
    summary="Get My Properties"
)
async def get_my_properties(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Get all properties owned by the authenticated property owner.
    
    **Required role:** PROPERTY_OWNER
    """
    property_service = PropertyService(db)
    properties, total = property_service.get_properties_by_owner(
        owner_id=current_owner.id,
        page=page,
        size=size
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return PropertyListResponse(
        properties=[PropertyResponse.model_validate(p) for p in properties],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update Property"
)
async def update_property(
    property_id: str,
    update_data: UpdatePropertyRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Update property details.
    
    **Required role:** PROPERTY_OWNER (must be the property owner)
    
    **Note:** Only the property owner can update their properties.
    """
    property_service = PropertyService(db)
    updated_property = property_service.update_property(
        property_id=property_id,
        update_data=update_data,
        owner_id=current_owner.id
    )
    
    return PropertyResponse.model_validate(updated_property)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Property"
)
async def delete_property(
    property_id: str,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) property.
    
    **Required role:** PROPERTY_OWNER (must be the property owner)
    
    **Note:** This performs a soft delete (deactivates the property).
    Only the property owner can delete their properties.
    """
    property_service = PropertyService(db)
    property_service.delete_property(
        property_id=property_id,
        owner_id=current_owner.id
    )
    
    return None


@router.post(
    "/{property_id}/activate",
    response_model=PropertyResponse,
    summary="Activate Property"
)
async def activate_property(
    property_id: str,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Activate a deactivated property.
    
    **Required role:** PROPERTY_OWNER (must be the property owner)
    """
    property_service = PropertyService(db)
    activated_property = property_service.activate_property(
        property_id=property_id,
        owner_id=current_owner.id
    )
    
    return PropertyResponse.model_validate(activated_property)
