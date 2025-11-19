# app/controllers/proposal_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.connection import get_db
from app.services.proposal_service import ProposalService
from app.dtos.proposal_dto import (
    CreateProposalRequest,
    RespondProposalRequest,
    ProposalResponse,
    ProposalListResponse,
    ProposalWithUserListResponse,
    ProposalWithUserResponse
)
from app.auth.dependencies import get_current_user, get_current_property_owner, AuthUser
from app.auth.auth_client import auth_client

router = APIRouter(tags=["proposals"])


@router.post(
    "/",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a Property Proposal"
)
async def create_proposal(
    proposal_data: CreateProposalRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a proposal for a property (purchase or rental offer).
    
    **Authentication required:** Any authenticated user
    
    **Required fields:**
    - `idProperty`: UUID of the property
    - `proposalValue`: Your proposed value/price
    - `message`: Optional message to the property owner
    
    **Business rules:**
    - Cannot make proposal on your own property
    - Cannot have duplicate pending proposals for same property
    - Proposal value must be greater than zero
    - Proposals expire after 30 days by default
    
    **Returns:** Complete proposal details including unique ID for tracking
    
    **Example:**
    ```json
    {
        "idProperty": "123e4567-e89b-12d3-a456-426614174000",
        "proposalValue": 250000.00,
        "message": "Very interested. Can we negotiate?"
    }
    ```
    """
    proposal_service = ProposalService(db)
    proposal = proposal_service.create_proposal(proposal_data, current_user.id)
    
    return ProposalResponse.from_proposal(proposal)


@router.get(
    "/my-proposals",
    response_model=ProposalListResponse,
    summary="View My Submitted Proposals"
)
async def get_my_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, rejected, withdrawn"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View all proposals you have submitted with pagination and filters.
    
    **Authentication required:** Any authenticated user
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 10, max: 100)
    - `status`: Filter by proposal status
      - `pending`: Active proposals awaiting response
      - `accepted`: Proposals that were accepted
      - `rejected`: Proposals that were rejected
      - `withdrawn`: Proposals you withdrew
    
    **Returns:** Paginated list of your proposals with status and tracking information
    """
    proposal_service = ProposalService(db)
    proposals, total = proposal_service.get_user_proposals(
        user_id=current_user.id,
        page=page,
        size=size,
        status=status
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return ProposalListResponse(
        proposals=[ProposalResponse.from_proposal(p) for p in proposals],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/received",
    response_model=ProposalWithUserListResponse,
    summary="View Received Proposals (Property Owners)"
)
async def get_received_proposals(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    View all proposals received for your properties with detailed user information.
    
    **Authentication required:** Property Owner role
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 10, max: 100)
    - `status`: Filter by proposal status
    
    **Returns:** Paginated list of proposals with complete user details including:
    - User ID
    - Username
    - Full Name
    - Email
    - Phone Number
    - Property Title and Address
    
    **Security:** The auth service validates that property owners can only access
    information of users who have made proposals on their properties.
    """
    proposal_service = ProposalService(db)
    proposals, total = proposal_service.get_received_proposals(
        owner_id=current_owner.id,
        page=page,
        size=size,
        status=status
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    # Extract access token from cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found"
        )
    
    # Fetch user information and property info for each proposal
    proposal_responses = []
    for proposal in proposals:
        # Get user info from auth service
        user_info = await auth_client.get_user_info(str(proposal.idUser), access_token)
        
        # Get property info from database
        from app.models.property import Property
        property_obj = db.query(Property).filter(Property.id == proposal.idProperty).first()
        
        property_info = None
        if property_obj:
            # Get address from relationship
            address_str = f"{property_obj.address.street}, {property_obj.address.number} - {property_obj.address.city}" if property_obj.address else "Address not available"
            
            # Create title from property type and sales type
            property_title = f"{property_obj.propertyType.value.title()} for {property_obj.salesType.value.title()}"
            
            property_info = {
                "id": str(property_obj.id),
                "title": property_title,
                "address": address_str,
                "propertyValue": property_obj.propertyValue
            }
        
        proposal_response = ProposalWithUserResponse.from_proposal(proposal, user_info, property_info)
        proposal_responses.append(proposal_response)
    
    return ProposalWithUserListResponse(
        proposals=proposal_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse,
    summary="Get Proposal Details"
)
async def get_proposal(
    proposal_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific proposal.
    
    **Authentication required:** User must be the proposal creator or property owner
    
    **Returns:** Complete proposal details with tracking ID
    
    **Error responses:**
    - `404 Not Found`: Proposal does not exist
    - `403 Forbidden`: Not authorized to view this proposal
    """
    proposal_service = ProposalService(db)
    proposal = proposal_service.get_proposal_by_id(proposal_id)
    
    # Check if user is either the proposal creator or property owner
    from app.repositories.proposal_repository import ProposalRepository
    repo = ProposalRepository(db)
    property_owner_id = repo.get_property_owner_id(proposal.idProperty)
    
    if proposal.idUser != current_user.id and property_owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own proposals or proposals for your properties"
        )
    
    return ProposalResponse.from_proposal(proposal)


@router.get(
    "/property/{property_id}/proposals",
    response_model=ProposalListResponse,
    summary="Get Proposals for a Property"
)
async def get_property_proposals(
    property_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Get all proposals for a specific property.
    
    **Authentication required:** Property Owner (must own the property)
    
    **Query Parameters:**
    - `page`: Page number
    - `size`: Items per page
    - `status`: Filter by proposal status
    
    **Returns:** Paginated list of proposals for the property
    """
    proposal_service = ProposalService(db)
    proposals, total = proposal_service.get_property_proposals(
        property_id=property_id,
        owner_id=current_owner.id,
        page=page,
        size=size,
        status=status
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return ProposalListResponse(
        proposals=[ProposalResponse.from_proposal(p) for p in proposals],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.post(
    "/{proposal_id}/accept",
    response_model=ProposalResponse,
    summary="Accept a Proposal"
)
async def accept_proposal(
    proposal_id: str,
    response_data: RespondProposalRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Accept a proposal for your property.
    
    **Authentication required:** Property Owner (must own the property)
    
    **Business rules:**
    - Proposal must be in pending status
    - Proposal must not be expired
    - Only property owner can accept
    
    **Returns:** Updated proposal with accepted status
    """
    proposal_service = ProposalService(db)
    proposal = proposal_service.accept_proposal(
        proposal_id=proposal_id,
        owner_id=current_owner.id,
        response_message=response_data.response_message
    )
    
    return ProposalResponse.from_proposal(proposal)


@router.post(
    "/{proposal_id}/reject",
    response_model=ProposalResponse,
    summary="Reject a Proposal"
)
async def reject_proposal(
    proposal_id: str,
    response_data: RespondProposalRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Reject a proposal for your property.
    
    **Authentication required:** Property Owner (must own the property)
    
    **Business rules:**
    - Proposal must be in pending status
    - Proposal must not be expired
    - Only property owner can reject
    
    **Returns:** Updated proposal with rejected status
    """
    proposal_service = ProposalService(db)
    proposal = proposal_service.reject_proposal(
        proposal_id=proposal_id,
        owner_id=current_owner.id,
        response_message=response_data.response_message
    )
    
    return ProposalResponse.from_proposal(proposal)


@router.post(
    "/{proposal_id}/withdraw",
    response_model=ProposalResponse,
    summary="Withdraw Your Proposal"
)
async def withdraw_proposal(
    proposal_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Withdraw a proposal you submitted.
    
    **Authentication required:** User must own the proposal
    
    **Business rules:**
    - Proposal must be in pending status
    - Proposal must not be expired
    - Only proposal creator can withdraw
    
    **Returns:** Updated proposal with withdrawn status
    """
    proposal_service = ProposalService(db)
    proposal = proposal_service.withdraw_proposal(
        proposal_id=proposal_id,
        user_id=current_user.id
    )
    
    return ProposalResponse.from_proposal(proposal)


@router.delete(
    "/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Proposal"
)
async def delete_proposal(
    proposal_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a proposal permanently.
    
    **Authentication required:** User must own the proposal
    
    **Returns:** 204 No Content on success
    """
    proposal_service = ProposalService(db)
    proposal_service.delete_proposal(proposal_id, current_user.id)
    
    return None
