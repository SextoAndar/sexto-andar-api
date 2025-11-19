# app/dtos/image_dto.py
from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, Union
from datetime import datetime
import uuid
import base64


class ImageUploadRequest(BaseModel):
    """Request DTO for uploading a single image"""
    image_data: str = Field(..., description="Base64 encoded image data")
    content_type: str = Field(..., description="Image content type (image/jpeg, image/png, image/webp)")
    display_order: int = Field(default=1, ge=1, le=15, description="Display order (1-15)")
    is_primary: bool = Field(default=False, description="Is this the primary/main image")
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type"""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('image_data')
    @classmethod
    def validate_image_data(cls, v: str) -> str:
        """Validate that image_data is valid base64 and not too large"""
        try:
            # Try to decode base64
            decoded = base64.b64decode(v)
            
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if len(decoded) > max_size:
                raise ValueError(f"Image size must not exceed 5MB (got {len(decoded) / 1024 / 1024:.2f}MB)")
            
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 image data: {str(e)}")


class ImageResponse(BaseModel):
    """Response DTO for image metadata"""
    id: Union[str, uuid.UUID]
    property_id: Union[str, uuid.UUID]
    content_type: str
    file_size: int
    display_order: int
    is_primary: bool
    created_at: Union[str, datetime]
    
    class Config:
        from_attributes = True
    
    @field_serializer('id', 'property_id')
    def serialize_uuid(self, value: Union[str, uuid.UUID]) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value) if isinstance(value, uuid.UUID) else value
    
    @field_serializer('created_at')
    def serialize_datetime(self, value: Union[str, datetime]) -> str:
        """Convert datetime to ISO string for JSON serialization"""
        return value.isoformat() if isinstance(value, datetime) else value
    
    @classmethod
    def from_model(cls, image):
        """Create response from PropertyImage model"""
        return cls(
            id=str(image.id),
            property_id=str(image.property_id),
            content_type=image.content_type,
            file_size=image.file_size,
            display_order=image.display_order,
            is_primary=image.is_primary,
            created_at=image.created_at.isoformat()
        )


class ImageDataResponse(BaseModel):
    """Response DTO for image with actual binary data"""
    id: str
    image_data: str = Field(..., description="Base64 encoded image data")
    content_type: str
    file_size: int
    display_order: int
    is_primary: bool
    
    @classmethod
    def from_model(cls, image):
        """Create response from PropertyImage model with base64 encoded data"""
        return cls(
            id=str(image.id),
            image_data=base64.b64encode(image.image_data).decode('utf-8'),
            content_type=image.content_type,
            file_size=image.file_size,
            display_order=image.display_order,
            is_primary=image.is_primary
        )


class ImagesListResponse(BaseModel):
    """Response DTO for list of images (metadata only)"""
    images: list[ImageResponse]
    total: int


class ReorderImagesRequest(BaseModel):
    """Request DTO for reordering images"""
    image_orders: list[dict[str, int]] = Field(
        ..., 
        description="List of {image_id: new_order} mappings",
        example=[{"id": "uuid1", "order": 1}, {"id": "uuid2", "order": 2}]
    )
    
    @field_validator('image_orders')
    @classmethod
    def validate_orders(cls, v: list) -> list:
        """Validate that all orders are between 1 and 15"""
        for item in v:
            if 'order' in item and not 1 <= item['order'] <= 15:
                raise ValueError("All display orders must be between 1 and 15")
        return v
