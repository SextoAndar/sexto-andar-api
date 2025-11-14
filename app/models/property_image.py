# app/models/property_image.py
from sqlalchemy import Column, String, Integer, ForeignKey, LargeBinary, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
import uuid

from app.models.base import BaseModel


class PropertyImage(BaseModel):
    """
    PropertyImage model for storing property images in database
    Each property must have 1 to 15 images
    Images are stored as BYTEA in PostgreSQL
    """
    __tablename__ = "property_images"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Foreign Key to Property
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Image data stored as binary (BYTEA in PostgreSQL)
    image_data = Column(
        LargeBinary,
        nullable=False
    )
    
    # Content type (e.g., 'image/jpeg', 'image/png', 'image/webp')
    content_type = Column(
        String(50),
        nullable=False
    )
    
    # File size in bytes
    file_size = Column(
        Integer,
        nullable=False
    )
    
    # Display order (1 = main/primary image, 2-15 = additional images)
    display_order = Column(
        Integer,
        nullable=False,
        default=1
    )
    
    # Flag to indicate if this is the primary/main image
    is_primary = Column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Relationship back to Property
    property = relationship("Property", back_populates="images")
    
    @validates('content_type')
    def validate_content_type(self, key, value):
        """Validate that content type is an accepted image format"""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        return value
    
    @validates('file_size')
    def validate_file_size(self, key, value):
        """Validate that file size doesn't exceed 5MB"""
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value > max_size:
            raise ValueError(f"File size must not exceed 5MB (got {value / 1024 / 1024:.2f}MB)")
        return value
    
    @validates('display_order')
    def validate_display_order(self, key, value):
        """Validate display order is between 1 and 15"""
        if not 1 <= value <= 15:
            raise ValueError("Display order must be between 1 and 15")
        return value
    
    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, order={self.display_order}, primary={self.is_primary})>"
