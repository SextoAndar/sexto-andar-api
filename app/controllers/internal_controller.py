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

logger = logging.getLogger(__name__)
router = APIRouter(tags=["internal"])


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
