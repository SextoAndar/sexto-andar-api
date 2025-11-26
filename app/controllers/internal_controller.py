# app/controllers/internal_controller.py
"""
Internal API endpoints for inter-service communication.
These endpoints are not exposed publicly and require internal authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.models.visit import Visit
from app.models.proposal import Proposal
from app.models.property import Property
from app.settings import settings
import logging
from pydantic import BaseModel, Field
from uuid import UUID # Adicionar a importação para UUID aqui

from app.services.property_service import PropertyService
from app.services.favorite_service import FavoriteService
from app.services.visit_service import VisitService
from app.services.proposal_service import ProposalService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["internal"])


class UserDeletedWebhookRequest(BaseModel):
    """Request body for user deleted webhook"""
    user_id: UUID = Field(..., description="UUID of the user that was deleted")


@router.post(
    "/internal/user-deleted-webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook for User Deletion from Auth Service"
)
async def user_deleted_webhook(
    request: UserDeletedWebhookRequest,
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
    db: Session = Depends(get_db)
):
    """
    **INTERNAL ENDPOINT** - Receives notification from the Auth Service when a user is deleted.
    
    This endpoint triggers the cascading deletion of user-related data within this service.
    
    **Authentication**: Requires X-Internal-Secret header matching configured secret.
    
    **Request Body:**
    - `user_id`: UUID of the user that was deleted.
    
    **Returns:**
    - `200 OK`: If the webhook is successfully processed.
    - `401 Unauthorized`: If the X-Internal-Secret is invalid.
    """
    if x_internal_secret != settings.INTERNAL_API_SECRET:
        logger.warning(f"Invalid internal secret attempt for user_id={request.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API secret"
        )
    
    logger.info(f"Received user deleted webhook for user_id: {request.user_id}")
    
    # Instantiate services
    property_service = PropertyService(db)
    favorite_service = FavoriteService(db)
    visit_service = VisitService(db)
    proposal_service = ProposalService(db)
    
    try:
        # Delete properties and their images first (assuming user is also a property owner)
        property_service.delete_all_owner_properties_permanently(request.user_id)
        logger.info(f"Properties and images deleted for owner {request.user_id}.")
        
        # Delete all favorites made by this user
        deleted_favorites_count = favorite_service.delete_all_user_favorites(request.user_id)
        logger.info(f"Deleted {deleted_favorites_count} favorites for user {request.user_id}.")
        
        # Delete all visits made by this user
        deleted_user_visits_count = visit_service.delete_all_user_visits(request.user_id)
        logger.info(f"Deleted {deleted_user_visits_count} user visits for user {request.user_id}.")
        
        # Delete all visits for properties owned by this user
        deleted_owner_prop_visits_count = visit_service.delete_all_visits_for_owner_properties(request.user_id)
        logger.info(f"Deleted {deleted_owner_prop_visits_count} visits for properties of owner {request.user_id}.")
        
        # Delete all proposals made by this user
        deleted_user_proposals_count = proposal_service.delete_all_user_proposals(request.user_id)
        logger.info(f"Deleted {deleted_user_proposals_count} user proposals for user {request.user_id}.")
        
        # Delete all proposals for properties owned by this user
        deleted_owner_prop_proposals_count = proposal_service.delete_all_proposals_for_owner_properties(request.user_id)
        logger.info(f"Deleted {deleted_owner_prop_proposals_count} proposals for properties of owner {request.user_id}.")
        
        logger.info(f"Cascading deletion completed successfully for user_id: {request.user_id}")
        
    except HTTPException as e:
        logger.error(f"Error during cascading deletion for user_id {request.user_id}: {e.detail}")
        raise # Re-raise the HTTPException
    except Exception as e:
        logger.error(f"Unhandled error during cascading deletion for user_id {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user data cleanup: {str(e)}"
        )
    
    return {"message": f"Webhook processed and cascading deletion initiated for user_id: {request.user_id}"}


@router.get(
    "/internal/check-user-property-relation",
    summary="Check if User has Relation with Property Owner (Internal)"
)
async def check_user_property_relation(
    user_id: UUID,
    owner_id: UUID,
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
    db: Session = Depends(get_db)
):
    """
    **INTERNAL ENDPOINT** - For inter-service communication only.
    
    Checks if a user has any relationship with a property owner's properties.
    Used by auth service to validate access control for property owners.
    
    **Authentication**: Requires X-Internal-Secret header matching configured secret.
    
    **Returns:**
    - `has_relation`: True if user has visits or proposals on owner's properties
    - `has_visit`: True if user has scheduled visits
    - `has_proposal`: True if user has made proposals
    
    **Security Note**: This endpoint must NOT be publicly accessible.
    Only internal services (auth) should be able to call it.
    """
    # Validate internal secret
    logger.debug(f"Received secret: {repr(x_internal_secret)}")
    logger.debug(f"Expected secret: {repr(settings.INTERNAL_API_SECRET)}")
    logger.debug(f"Secrets match: {x_internal_secret == settings.INTERNAL_API_SECRET}")
    
    if x_internal_secret != settings.INTERNAL_API_SECRET:
        logger.warning(f"Invalid internal secret attempt from user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API secret"
        )
    
    # Check if user has visits on owner's properties
    has_visit = db.query(Visit)\
        .join(Property, Visit.idProperty == Property.id)\
        .filter(Visit.idUser == user_id)\
        .filter(Property.idPropertyOwner == owner_id)\
        .first() is not None
    
    # Check if user has proposals on owner's properties
    has_proposal = db.query(Proposal)\
        .join(Property, Proposal.idProperty == Property.id)\
        .filter(Proposal.idUser == user_id)\
        .filter(Property.idPropertyOwner == owner_id)\
        .first() is not None
    
    return {
        "has_relation": has_visit or has_proposal,
        "has_visit": has_visit,
        "has_proposal": has_proposal,
        "user_id": str(user_id),
        "owner_id": str(owner_id)
    }
