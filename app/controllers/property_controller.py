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
    AddressResponse,
    PortfolioStatsResponse
)
from app.auth.dependencies import get_current_property_owner, get_current_user, AuthUser

router = APIRouter(tags=["properties"])


@router.post(
    "/houses",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a House"
)
async def create_house(
    house_data: CreateHouseRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Register a new house property in the system.
    
    **Authentication required:** Property Owner role
    
    **House-specific fields:**
    - `landPrice`: Price of the land/terrain (optional)
    - `isSingleHouse`: Whether it's a single house on the land (optional)
    
    **Required fields:**
    - `address`: Complete property address
      - `street`: Street name
      - `number`: Street number
      - `city`: City name
      - `postal_code`: ZIP/Postal code
      - `country`: Country name
    - `propertySize`: Size in square meters (decimal)
    - `description`: Property description (minimum 10 characters)
    - `propertyValue`: Property value/price
    - `salesType`: Type of sale - 'RENT' or 'SALE'
    
    **Returns:** Complete property details including generated ID and timestamps
    """
    property_service = PropertyService(db)
    house = property_service.create_house(house_data, current_owner.id)
    
    return PropertyResponse.model_validate(house)


@router.post(
    "/apartments",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an Apartment"
)
async def create_apartment(
    apartment_data: CreateApartmentRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Register a new apartment property in the system.
    
    **Authentication required:** Property Owner role
    
    **Apartment-specific fields:**
    - `condominiumFee`: Monthly condominium/HOA fee (optional)
    - `commonArea`: Whether building has common/recreational areas (required)
    - `floor`: Floor number - can be negative for basements (optional)
    - `isPetAllowed`: Whether pets are allowed in the unit (required)
    
    **Required fields:**
    - `address`: Complete property address
      - `street`: Street name
      - `number`: Street number
      - `city`: City name
      - `postal_code`: ZIP/Postal code
      - `country`: Country name
    - `propertySize`: Size in square meters (decimal)
    - `description`: Property description (minimum 10 characters)
    - `propertyValue`: Property value/price
    - `salesType`: Type of sale - 'RENT' or 'SALE'
    
    **Returns:** Complete property details including generated ID and timestamps
    """
    property_service = PropertyService(db)
    apartment = property_service.create_apartment(apartment_data, current_owner.id)
    
    return PropertyResponse.model_validate(apartment)



@router.get(
    "/owner/my-properties",
    response_model=PropertyListResponse,
    summary="View My Property Portfolio"
)
async def get_my_properties(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    property_type: Optional[str] = Query(None, description="Filter by type: 'HOUSE' or 'APARTMENT'"),
    sales_type: Optional[str] = Query(None, description="Filter by sales type: 'RENT' or 'SALE'"),
    active_only: bool = Query(True, description="Show only active properties"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    View and manage your complete property portfolio.
    
    **Authentication required:** Property Owner role
    
    Retrieve all properties you own with advanced filtering options to help
    you track and organize your real estate portfolio effectively.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Number of items per page (default: 10, max: 100)
    - `property_type`: Filter by property type
      - `HOUSE`: Show only your houses
      - `APARTMENT`: Show only your apartments
    - `sales_type`: Filter by sales type
      - `RENT`: Show only rental properties
      - `SALE`: Show only properties for sale
    - `active_only`: Show only active properties (default: true)
      - Set to `false` to include deactivated properties
    
    **Returns:** Paginated list with:
    - `properties`: Array of your property objects
    - `total`: Total number of your properties matching filters
    - `page`: Current page number
    - `size`: Items per page
    - `total_pages`: Total number of pages
    
    **Common Use Cases:**
    - View all properties: `GET /api/owner/my-properties`
    - View rental portfolio: `GET /api/owner/my-properties?sales_type=RENT`
    - View houses for sale: `GET /api/owner/my-properties?property_type=HOUSE&sales_type=SALE`
    - Include deactivated: `GET /api/owner/my-properties?active_only=false`
    """
    property_service = PropertyService(db)
    properties, total = property_service.get_properties_by_owner(
        owner_id=current_owner.id,
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
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get Property Details"
)
async def get_property(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed information about a specific property by its ID.
    
    **Public endpoint** - No authentication required
    
    **Parameters:**
    - `property_id`: UUID of the property
    
    **Returns:** Complete property details including:
    - Property type (house or apartment)
    - Sales type (rent or sale)
    - Price and size
    - Complete address
    - All property-specific attributes
    - Timestamps (creation and last update)
    
    **Error responses:**
    - `404 Not Found`: Property does not exist
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
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    property_type: Optional[str] = Query(None, description="Filter by type: 'HOUSE' or 'APARTMENT'"),
    sales_type: Optional[str] = Query(None, description="Filter by sales type: 'RENT' or 'SALE'"),
    active_only: bool = Query(True, description="Show only active properties"),
    db: Session = Depends(get_db)
):
    """
    List all properties with pagination and optional filters.
    
    **Public endpoint** - No authentication required
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Number of items per page (default: 10, max: 100)
    - `property_type`: Filter by property type
      - `HOUSE`: Only houses
      - `APARTMENT`: Only apartments
    - `sales_type`: Filter by sales type
      - `RENT`: Only properties for rent
      - `SALE`: Only properties for sale
    - `active_only`: Show only active properties (default: true)
    
    **Returns:** Paginated list with:
    - `properties`: Array of property objects
    - `total`: Total number of properties matching filters
    - `page`: Current page number
    - `size`: Items per page
    - `total_pages`: Total number of pages
    
    **Examples:**
    - All properties: `GET /api/properties`
    - Only houses: `GET /api/properties?property_type=HOUSE`
    - Houses for sale: `GET /api/properties?property_type=HOUSE&sales_type=SALE`
    - Page 2: `GET /api/properties?page=2&size=20`
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
    summary="View My Property Portfolio"
)
async def get_my_properties(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    property_type: Optional[str] = Query(None, description="Filter by type: 'HOUSE' or 'APARTMENT'"),
    sales_type: Optional[str] = Query(None, description="Filter by sales type: 'RENT' or 'SALE'"),
    active_only: bool = Query(True, description="Show only active properties"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    View and manage your complete property portfolio.
    
    **Authentication required:** Property Owner role
    
    Retrieve all properties you own with advanced filtering options to help
    you track and organize your real estate portfolio effectively.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Number of items per page (default: 10, max: 100)
    - `property_type`: Filter by property type
      - `HOUSE`: Show only your houses
      - `APARTMENT`: Show only your apartments
    - `sales_type`: Filter by sales type
      - `RENT`: Show only rental properties
      - `SALE`: Show only properties for sale
    - `active_only`: Show only active properties (default: true)
      - Set to `false` to include deactivated properties
    
    **Returns:** Paginated list with:
    - `properties`: Array of your property objects
    - `total`: Total number of your properties matching filters
    - `page`: Current page number
    - `size`: Items per page
    - `total_pages`: Total number of pages
    
    **Common Use Cases:**
    - View all properties: `GET /api/owner/my-properties`
    - View rental portfolio: `GET /api/owner/my-properties?sales_type=RENT`
    - View houses for sale: `GET /api/owner/my-properties?property_type=HOUSE&sales_type=SALE`
    - Include deactivated: `GET /api/owner/my-properties?active_only=false`
    """
    property_service = PropertyService(db)
    properties, total = property_service.get_properties_by_owner(
        owner_id=current_owner.id,
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
    "/owner/portfolio-stats",
    response_model=PortfolioStatsResponse,
    summary="Get Portfolio Statistics"
)
async def get_portfolio_stats(
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics and statistics about your property portfolio.
    
    **Authentication required:** Property Owner role
    
    This endpoint provides valuable insights to help you understand and manage
    your real estate investments effectively.
    
    **Returns statistical data including:**
    
    **Property Counts:**
    - `total_properties`: Total number of properties you own
    - `active_properties`: Number of currently active properties
    - `inactive_properties`: Number of deactivated properties
    
    **Distribution by Type:**
    - `total_houses`: Number of houses in your portfolio
    - `total_apartments`: Number of apartments in your portfolio
    
    **Distribution by Sales Type:**
    - `total_for_sale`: Number of properties listed for sale
    - `total_for_rent`: Number of properties available for rent
    
    **Financial Metrics:**
    - `total_portfolio_value`: Combined value of all your properties
    - `average_property_value`: Average value per property
    - `total_monthly_rent_potential`: Potential monthly income from rental properties
    
    **Use this data to:**
    - Track your investment portfolio growth
    - Understand asset distribution
    - Calculate potential rental income
    - Make informed business decisions
    - Monitor portfolio performance
    """
    property_service = PropertyService(db)
    stats = property_service.get_portfolio_stats(current_owner.id)
    
    return PortfolioStatsResponse(**stats)


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update Property Details"
)
async def update_property(
    property_id: str,
    update_data: UpdatePropertyRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Update details of an existing property.
    
    **Authentication required:** Property Owner role (must own the property)
    
    **Parameters:**
    - `property_id`: UUID of the property to update
    
    **Updatable fields:**
    - `description`: Property description
    - `propertyValue`: Property value/price
    - `propertySize`: Size in square meters
    - `salesType`: Change between 'RENT' and 'SALE'
    - And other property-specific fields
    
    **Security:**
    - Only the property owner can update their properties
    - Property ownership is verified before update
    
    **Returns:** Updated property details
    
    **Error responses:**
    - `403 Forbidden`: Not the property owner
    - `404 Not Found`: Property does not exist
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
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a property (soft delete).
    
    **Authentication required:** Property Owner (owns the property) OR Admin role
    
    **Parameters:**
    - `property_id`: UUID of the property to delete
    
    **Behavior:**
    - Performs a **soft delete** (marks property as inactive)
    - Property remains in database but is hidden from listings
    - Property owners can only delete their own properties
    - Administrators can delete any property
    - Deleted properties can be reactivated using the activate endpoint
    
    **Authorization rules:**
    - Property Owner: Can delete only their own properties
    - Admin: Can delete any property in the system
    
    **Returns:** 
    - `204 No Content` on success
    
    **Error responses:**
    - `403 Forbidden`: Not authorized to delete this property
    - `404 Not Found`: Property does not exist
    """
    property_service = PropertyService(db)
    property_service.delete_property(
        property_id=property_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin()
    )
    
    return None


@router.post(
    "/{property_id}/activate",
    response_model=PropertyResponse,
    summary="Reactivate Property"
)
async def activate_property(
    property_id: str,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Reactivate a previously deactivated property.
    
    **Authentication required:** Property Owner role (must own the property)
    
    **Parameters:**
    - `property_id`: UUID of the property to reactivate
    
    **Use case:**
    - Restore a soft-deleted property back to active status
    - Make the property visible in listings again
    - Resume property availability
    
    **Security:**
    - Only the property owner can reactivate their properties
    
    **Returns:** Reactivated property details
    
    **Error responses:**
    - `403 Forbidden`: Not the property owner
    - `404 Not Found`: Property does not exist
    - `400 Bad Request`: Property is already active
    """
    property_service = PropertyService(db)
    activated_property = property_service.activate_property(
        property_id=property_id,
        owner_id=current_owner.id
    )
    
    return PropertyResponse.model_validate(activated_property)
