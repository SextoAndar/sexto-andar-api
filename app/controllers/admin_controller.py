# app/controllers/admin_controller.py
"""
Admin endpoints for system-wide management.
All endpoints require ADMIN role.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import math

from app.database.connection import get_db
from app.services.property_service import PropertyService
from app.dtos.property_dto import PropertyResponse, PropertyListResponse
from app.auth.dependencies import get_current_admin, AuthUser

router = APIRouter(tags=["admin"], prefix="/admin")


@router.get(
    "/properties",
    response_model=PropertyListResponse,
    summary="View All Properties in System (Admin Only)"
)
async def get_all_properties_admin(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    randomize: bool = Query(True, description="Randomize order (shuffle results)"),
    include_inactive: bool = Query(False, description="Include inactive properties"),
    current_admin: AuthUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    View all properties in the system with pagination and optional randomization.
    
    **Authentication required:** ADMIN role only
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Number of items per page (default: 10, max: 100)
    - `randomize`: Shuffle results for randomized order (default: true)
    - `include_inactive`: Include deactivated properties (default: false)
    
    **Features:**
    - Pagination for easy navigation through large datasets
    - Optional randomization to shuffle property order
    - View both active and inactive properties
    - Access to all properties regardless of owner
    
    **Returns:** Paginated list with:
    - `properties`: Array of all property objects
    - `total`: Total number of properties in system
    - `page`: Current page number
    - `size`: Items per page
    - `total_pages`: Total number of pages
    
    **Use Cases:**
    - Monitor all properties in the platform
    - Audit property listings
    - Discover properties for moderation
    - Review inactive/deactivated properties
    
    **Error responses:**
    - `403 Forbidden`: User is not an admin
    """
    property_service = PropertyService(db)
    
    # Get all properties with optional randomization
    properties, total = property_service.get_all_properties_admin(
        page=page,
        size=size,
        randomize=randomize,
        include_inactive=include_inactive
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return PropertyListResponse(
        properties=[PropertyResponse.model_validate(p) for p in properties],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
