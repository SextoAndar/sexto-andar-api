# app/controllers/visit_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.connection import get_db
from app.services.visit_service import VisitService
from app.dtos.visit_dto import (
    CreateVisitRequest,
    UpdateVisitRequest,
    CompleteVisitRequest,
    CancelVisitRequest,
    VisitResponse,
    VisitListResponse,
    VisitWithUserResponse,
    VisitWithUserListResponse
)
from app.auth.dependencies import get_current_user, get_current_property_owner, AuthUser
from app.auth.auth_client import auth_client

router = APIRouter(tags=["visits"])


@router.post(
    "/",
    response_model=VisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a Property Visit"
)
async def create_visit(
    visit_data: CreateVisitRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule a new visit to a property.
    
    **Authentication required:** Any authenticated user
    
    **Required fields:**
    - `idProperty`: UUID of the property to visit
    - `visitDate`: Desired visit date and time (must be in the future)
    - `notes`: Optional notes about the visit
    
    **Business rules:**
    - Visit date must be in the future
    - Visit date cannot be more than 6 months in advance
    
    **Returns:** Complete visit details including unique ID for tracking
    
    **Example:**
    ```json
    {
        "idProperty": "123e4567-e89b-12d3-a456-426614174000",
        "visitDate": "2024-12-20T14:00:00",
        "notes": "Interested in the kitchen and backyard"
    }
    ```
    """
    visit_service = VisitService(db)
    visit = visit_service.create_visit(visit_data, current_user.id)
    
    return VisitResponse.from_visit(visit)


@router.get(
    "/my-visits",
    response_model=VisitListResponse,
    summary="View My Scheduled Visits"
)
async def get_my_visits(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    include_cancelled: bool = Query(False, description="Include cancelled visits"),
    include_completed: bool = Query(True, description="Include completed visits"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View all your scheduled visits with pagination and filters.
    
    **Authentication required:** Any authenticated user
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 10, max: 100)
    - `include_cancelled`: Include cancelled visits (default: false)
    - `include_completed`: Include completed visits (default: true)
    
    **Returns:** Paginated list of your visits with status information
    """
    visit_service = VisitService(db)
    visits, total = visit_service.get_user_visits(
        user_id=current_user.id,
        page=page,
        size=size,
        include_cancelled=include_cancelled,
        include_completed=include_completed
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return VisitListResponse(
        visits=[VisitResponse.from_visit(v) for v in visits],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/upcoming",
    response_model=list[VisitResponse],
    summary="Get Upcoming Visits"
)
async def get_upcoming_visits(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all your upcoming (scheduled, non-cancelled) visits.
    
    **Authentication required:** Any authenticated user
    
    **Returns:** List of upcoming visits ordered by date
    """
    visit_service = VisitService(db)
    visits = visit_service.get_upcoming_visits_by_user(current_user.id)
    
    return [VisitResponse.from_visit(v) for v in visits]


@router.get(
    "/{visit_id}",
    response_model=VisitResponse,
    summary="Get Visit Details"
)
async def get_visit(
    visit_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific visit.
    
    **Authentication required:** User must own the visit
    
    **Returns:** Complete visit details
    
    **Error responses:**
    - `404 Not Found`: Visit does not exist
    - `403 Forbidden`: Not your visit
    """
    visit_service = VisitService(db)
    visit = visit_service.get_visit_by_id(visit_id)
    
    # Check ownership
    if visit.idUser != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own visits"
        )
    
    return VisitResponse.from_visit(visit)


@router.put(
    "/{visit_id}",
    response_model=VisitResponse,
    summary="Update Visit (Reschedule or Update Notes)"
)
async def update_visit(
    visit_id: str,
    update_data: UpdateVisitRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update visit details (reschedule or update notes).
    
    **Authentication required:** User must own the visit
    
    **Updatable fields:**
    - `visitDate`: Reschedule to a new date/time
    - `notes`: Update visit notes
    
    **Business rules:**
    - Cannot update completed visits
    - Cannot update cancelled visits
    - New date must be in the future
    
    **Returns:** Updated visit details
    """
    visit_service = VisitService(db)
    visit = visit_service.update_visit(visit_id, update_data, current_user.id)
    
    return VisitResponse.from_visit(visit)


@router.post(
    "/{visit_id}/complete",
    response_model=VisitResponse,
    summary="Mark Visit as Completed"
)
async def complete_visit(
    visit_id: str,
    completion_data: CompleteVisitRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a visit as completed.
    
    **Authentication required:** User must own the visit
    
    **Business rules:**
    - Visit must not be cancelled
    - Visit must not already be completed
    - Visit date must have passed (or be today)
    
    **Returns:** Updated visit with completed status
    """
    visit_service = VisitService(db)
    visit = visit_service.complete_visit(
        visit_id,
        current_user.id,
        completion_data.notes
    )
    
    return VisitResponse.from_visit(visit)


@router.post(
    "/{visit_id}/cancel",
    response_model=VisitResponse,
    summary="Cancel a Visit"
)
async def cancel_visit(
    visit_id: str,
    cancellation_data: CancelVisitRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a scheduled visit.
    
    **Authentication required:** User must own the visit
    
    **Business rules:**
    - Visit must not be completed
    - Visit must not already be cancelled
    - Visit must be scheduled for the future
    
    **Returns:** Updated visit with cancelled status
    """
    visit_service = VisitService(db)
    visit = visit_service.cancel_visit(
        visit_id,
        current_user.id,
        cancellation_data.cancellation_reason
    )
    
    return VisitResponse.from_visit(visit)


@router.delete(
    "/{visit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Visit"
)
async def delete_visit(
    visit_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a visit permanently.
    
    **Authentication required:** User must own the visit
    
    **Returns:** 204 No Content on success
    """
    visit_service = VisitService(db)
    visit_service.delete_visit(visit_id, current_user.id)
    
    return None


@router.get(
    "/property/{property_id}/visits",
    response_model=VisitListResponse,
    summary="Get Visits for a Property (Public)"
)
async def get_property_visits(
    property_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all scheduled visits for a property.
    
    **Public endpoint** - No authentication required
    
    This allows property owners and interested users to see when visits are scheduled.
    Cancelled visits are not included by default.
    
    **Returns:** Paginated list of visits for the property
    """
    visit_service = VisitService(db)
    visits, total = visit_service.get_property_visits(
        property_id=property_id,
        page=page,
        size=size,
        include_cancelled=False
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return VisitListResponse(
        visits=[VisitResponse.from_visit(v) for v in visits],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/my-properties/visits",
    response_model=VisitWithUserListResponse,
    summary="View All Visits for My Properties (Property Owners)"
)
async def get_my_properties_visits(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    include_cancelled: bool = Query(False, description="Include cancelled visits"),
    include_completed: bool = Query(True, description="Include completed visits"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    View all visits scheduled for your properties with detailed user information.
    
    **Authentication required:** Property Owner role
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 10, max: 100)
    - `include_cancelled`: Include cancelled visits (default: false)
    - `include_completed`: Include completed visits (default: true)
    
    **Returns:** Paginated list of visits with complete user details
    
    **US21 Implementation:** This endpoint allows property owners to view all
    scheduled visits for their properties along with detailed visitor information:
    - User ID
    - Username
    - Full Name
    - Email
    - Phone Number
    
    **Security:** The auth service validates that property owners can only access
    information of users who have scheduled visits or made proposals on their properties.
    This is enforced via the internal validation endpoint in the properties API.
    """
    visit_service = VisitService(db)
    visits, total = visit_service.get_owner_visits(
        owner_id=current_owner.id,
        page=page,
        size=size,
        include_cancelled=include_cancelled,
        include_completed=include_completed
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    # Extract access token from cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found"
        )
    
    # Fetch user information for each visit
    visit_responses = []
    for visit in visits:
        user_info = await auth_client.get_user_info(str(visit.idUser), access_token)
        visit_response = VisitWithUserResponse.from_visit(visit, user_info)
        visit_responses.append(visit_response)
    
    return VisitWithUserListResponse(
        visits=visit_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
