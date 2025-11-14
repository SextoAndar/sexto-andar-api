# app/controllers/image_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.repositories.property_image_repository import PropertyImageRepository
from app.repositories.property_repository import PropertyRepository
from app.dtos.image_dto import (
    ImageUploadRequest,
    ImageResponse,
    ImageDataResponse,
    ImagesListResponse,
    ReorderImagesRequest
)
from app.auth.dependencies import get_current_property_owner, AuthUser
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["images"])


@router.post(
    "/properties/{property_id}/images",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Image to Property"
)
async def add_property_image(
    property_id: str,
    image_data: ImageUploadRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Add a new image to an existing property.
    
    **Authentication required:** Property Owner role
    
    **Requirements:**
    - Property must have between 1-15 images total
    - Image must be base64 encoded
    - Max file size: 5MB
    - Accepted formats: JPEG, PNG, WebP
    
    **Returns:** Image metadata
    """
    property_repo = PropertyRepository(db)
    image_repo = PropertyImageRepository(db)
    
    # Get property and verify ownership
    property_obj = property_repo.get_by_id(property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if str(property_obj.idPropertyOwner) != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add images to your own properties"
        )
    
    # Check image count limit
    current_count = image_repo.count_by_property(property_id)
    if current_count >= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property already has maximum of 15 images"
        )
    
    # Decode and create image
    import base64
    from app.models.property_image import PropertyImage
    
    try:
        image_bytes = base64.b64decode(image_data.image_data)
        
        property_image = PropertyImage(
            property_id=property_id,
            image_data=image_bytes,
            content_type=image_data.content_type,
            file_size=len(image_bytes),
            display_order=image_data.display_order,
            is_primary=image_data.is_primary
        )
        
        created_image = image_repo.create(property_image)
        
        return ImageResponse.from_model(created_image)
        
    except Exception as e:
        logger.error(f"Error adding image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )


@router.get(
    "/properties/{property_id}/images",
    response_model=ImagesListResponse,
    summary="List Property Images"
)
async def list_property_images(
    property_id: str,
    db: Session = Depends(get_db)
):
    """
    Get metadata for all images of a property.
    
    **Public endpoint** - No authentication required
    
    Returns list of image metadata (without actual image data).
    Use GET /images/{image_id} to download actual image.
    """
    property_repo = PropertyRepository(db)
    image_repo = PropertyImageRepository(db)
    
    # Verify property exists
    property_obj = property_repo.get_by_id(property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    images = image_repo.get_by_property(property_id)
    
    return ImagesListResponse(
        images=[ImageResponse.from_model(img) for img in images],
        total=len(images)
    )


@router.get(
    "/images/{image_id}",
    summary="Download Property Image",
    responses={
        200: {
            "content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}},
            "description": "Image binary data"
        }
    }
)
async def get_image(
    image_id: str,
    db: Session = Depends(get_db)
):
    """
    Download actual image binary data.
    
    **Public endpoint** - No authentication required
    
    Returns the image as binary data with appropriate content-type header.
    """
    image_repo = PropertyImageRepository(db)
    
    image = image_repo.get_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return Response(
        content=image.image_data,
        media_type=image.content_type
    )


@router.get(
    "/images/{image_id}/metadata",
    response_model=ImageResponse,
    summary="Get Image Metadata"
)
async def get_image_metadata(
    image_id: str,
    db: Session = Depends(get_db)
):
    """
    Get image metadata without downloading the actual image data.
    
    **Public endpoint** - No authentication required
    """
    image_repo = PropertyImageRepository(db)
    
    image = image_repo.get_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return ImageResponse.from_model(image)


@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Property Image"
)
async def delete_image(
    image_id: str,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Delete a property image.
    
    **Authentication required:** Property Owner role
    
    **Note:** Property must maintain at least 1 image.
    You cannot delete the last remaining image.
    """
    property_repo = PropertyRepository(db)
    image_repo = PropertyImageRepository(db)
    
    # Get image
    image = image_repo.get_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify property ownership
    property_obj = property_repo.get_by_id(str(image.property_id))
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if str(property_obj.idPropertyOwner) != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete images from your own properties"
        )
    
    # Check minimum image count
    current_count = image_repo.count_by_property(str(image.property_id))
    if current_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last image. Property must have at least 1 image."
        )
    
    # Delete image
    image_repo.delete(image)
    logger.info(f"Image {image_id} deleted from property {image.property_id}")


@router.put(
    "/properties/{property_id}/images/reorder",
    response_model=ImagesListResponse,
    summary="Reorder Property Images"
)
async def reorder_images(
    property_id: str,
    reorder_data: ReorderImagesRequest,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Reorder property images by updating their display_order.
    
    **Authentication required:** Property Owner role
    
    **Request body example:**
    ```json
    {
        "image_orders": [
            {"id": "uuid1", "order": 1},
            {"id": "uuid2", "order": 2},
            {"id": "uuid3", "order": 3}
        ]
    }
    ```
    """
    property_repo = PropertyRepository(db)
    image_repo = PropertyImageRepository(db)
    
    # Verify property ownership
    property_obj = property_repo.get_by_id(property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if str(property_obj.idPropertyOwner) != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reorder images of your own properties"
        )
    
    # Create order mapping
    order_map = {item["id"]: item["order"] for item in reorder_data.image_orders}
    
    # Reorder images
    updated_images = image_repo.reorder_images(property_id, order_map)
    
    return ImagesListResponse(
        images=[ImageResponse.from_model(img) for img in updated_images],
        total=len(updated_images)
    )


@router.put(
    "/properties/{property_id}/images/{image_id}/set-primary",
    response_model=ImageResponse,
    summary="Set Primary Image"
)
async def set_primary_image(
    property_id: str,
    image_id: str,
    current_owner: AuthUser = Depends(get_current_property_owner),
    db: Session = Depends(get_db)
):
    """
    Set an image as the primary/main image for a property.
    
    **Authentication required:** Property Owner role
    
    This will unset any other primary images for the property.
    """
    property_repo = PropertyRepository(db)
    image_repo = PropertyImageRepository(db)
    
    # Verify property ownership
    property_obj = property_repo.get_by_id(property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if str(property_obj.idPropertyOwner) != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify images of your own properties"
        )
    
    # Set primary image
    updated_image = image_repo.set_primary_image(property_id, image_id)
    
    if not updated_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or does not belong to this property"
        )
    
    return ImageResponse.from_model(updated_image)
