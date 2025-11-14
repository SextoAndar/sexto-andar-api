# app/controllers/favorite_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import math

from app.database.connection import get_db
from app.services.favorite_service import FavoriteService
from app.dtos.favorite_dto import (
    FavoriteResponse,
    FavoriteListResponse,
    FavoriteStatusResponse,
    FavoritesCountResponse
)
from app.auth.dependencies import get_current_user, AuthUser

router = APIRouter(tags=["favorites"])


@router.post(
    "/{property_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Property to Favorites (US05)"
)
async def add_to_favorites(
    property_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a property to your favorites list.
    
    **Authentication required:** Any authenticated user
    
    **US05 Implementation:** Como usuário, quero favoritar imóveis para salvá-los 
    em minha lista de interesse.
    
    **Business rules:**
    - Property must exist and be active
    - Cannot favorite the same property twice
    - Only regular users can favorite properties
    
    **Returns:** Confirmation message with property ID
    
    **Error responses:**
    - `404 Not Found`: Property does not exist
    - `400 Bad Request`: Property is not active
    - `409 Conflict`: Property already in favorites
    """
    favorite_service = FavoriteService(db)
    favorite = favorite_service.add_favorite(
        user_id=current_user.id,
        property_id=property_id
    )
    
    return FavoriteStatusResponse(
        message="Property added to favorites",
        property_id=favorite.idProperty,
        is_favorited=True
    )


@router.delete(
    "/{property_id}",
    response_model=FavoriteStatusResponse,
    summary="Remove Property from Favorites (US06)"
)
async def remove_from_favorites(
    property_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a property from your favorites list.
    
    **Authentication required:** Any authenticated user
    
    **US06 Implementation:** Como usuário, quero desfavoritar imóveis que 
    não me interessam mais.
    
    **Returns:** Confirmation message with property ID
    
    **Error responses:**
    - `404 Not Found`: Property is not in your favorites
    """
    favorite_service = FavoriteService(db)
    favorite_service.remove_favorite(
        user_id=current_user.id,
        property_id=property_id
    )
    
    return FavoriteStatusResponse(
        message="Property removed from favorites",
        property_id=property_id,
        is_favorited=False
    )


@router.get(
    "/",
    response_model=FavoriteListResponse,
    summary="View My Favorite Properties (US07)"
)
async def get_my_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Show only active properties"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View all your favorite properties with pagination.
    
    **Authentication required:** Any authenticated user
    
    **US07 Implementation:** Como usuário, quero visualizar meus imóveis favoritos 
    e realizar ações rápidas (visita, proposta) sobre eles.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 10, max: 100)
    - `active_only`: Show only active properties (default: true)
    
    **Returns:** Paginated list of favorite properties with full details
    
    **Quick Actions Available:**
    Each property in the response includes full details, allowing you to:
    - Schedule a visit: `POST /api/visits/` with the property ID
    - Make a proposal: `POST /api/proposals/` with the property ID
    - View property details: `GET /api/properties/{property_id}`
    
    **Property Details Included:**
    - Property type (HOUSE/APARTMENT)
    - Sales type (RENT/SALE)
    - Price and size
    - Description
    - Full address
    - Amenities (pet allowed, floor, etc.)
    """
    favorite_service = FavoriteService(db)
    favorites, total = favorite_service.get_user_favorites(
        user_id=current_user.id,
        page=page,
        size=size,
        active_only=active_only
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return FavoriteListResponse(
        favorites=[FavoriteResponse.from_favorite(f) for f in favorites],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get(
    "/{property_id}/status",
    response_model=FavoriteStatusResponse,
    summary="Check if Property is Favorited"
)
async def check_favorite_status(
    property_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a property is in your favorites list.
    
    **Authentication required:** Any authenticated user
    
    **Returns:** Status indicating if property is favorited
    """
    favorite_service = FavoriteService(db)
    is_favorited = favorite_service.is_favorited(
        user_id=current_user.id,
        property_id=property_id
    )
    
    return FavoriteStatusResponse(
        message="Property is favorited" if is_favorited else "Property is not favorited",
        property_id=property_id,
        is_favorited=is_favorited
    )


@router.get(
    "/count/total",
    response_model=FavoritesCountResponse,
    summary="Get Favorites Count (US08)"
)
async def get_favorites_count(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the total count of favorited properties for the current user.
    
    **Authentication required:** Any authenticated user
    
    **US08 Implementation:** Como usuário, quero ver a quantidade de imóveis 
    favoritados no meu perfil.
    
    **Returns:** Count of favorited properties
    
    **Use case:** Display this count in the user's profile page or navigation menu
    to show how many properties they have saved.
    """
    favorite_service = FavoriteService(db)
    count = favorite_service.get_favorites_count(current_user.id)
    
    return FavoritesCountResponse(
        count=count,
        message=f"You have {count} favorite {'property' if count == 1 else 'properties'}"
    )
