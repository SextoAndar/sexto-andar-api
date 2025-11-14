# app/repositories/property_image_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional
import base64

from app.models.property_image import PropertyImage


class PropertyImageRepository:
    """Repository for PropertyImage operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, property_image: PropertyImage) -> PropertyImage:
        """Create a new property image"""
        self.db.add(property_image)
        self.db.commit()
        self.db.refresh(property_image)
        return property_image
    
    def create_many(self, images: List[PropertyImage]) -> List[PropertyImage]:
        """Create multiple property images in batch"""
        self.db.add_all(images)
        self.db.commit()
        for image in images:
            self.db.refresh(image)
        return images
    
    def get_by_id(self, image_id: str) -> Optional[PropertyImage]:
        """Get image by ID"""
        return (
            self.db.query(PropertyImage)
            .filter(PropertyImage.id == image_id)
            .first()
        )
    
    def get_by_property(self, property_id: str) -> List[PropertyImage]:
        """Get all images for a property, ordered by display_order"""
        return (
            self.db.query(PropertyImage)
            .filter(PropertyImage.property_id == property_id)
            .order_by(PropertyImage.display_order)
            .all()
        )
    
    def get_primary_image(self, property_id: str) -> Optional[PropertyImage]:
        """Get the primary/main image for a property"""
        return (
            self.db.query(PropertyImage)
            .filter(
                PropertyImage.property_id == property_id,
                PropertyImage.is_primary == True
            )
            .first()
        )
    
    def update(self, property_image: PropertyImage) -> PropertyImage:
        """Update existing property image"""
        self.db.commit()
        self.db.refresh(property_image)
        return property_image
    
    def delete(self, property_image: PropertyImage) -> None:
        """Delete a property image"""
        self.db.delete(property_image)
        self.db.commit()
    
    def delete_by_property(self, property_id: str) -> int:
        """Delete all images for a property. Returns count of deleted images."""
        count = (
            self.db.query(PropertyImage)
            .filter(PropertyImage.property_id == property_id)
            .delete()
        )
        self.db.commit()
        return count
    
    def count_by_property(self, property_id: str) -> int:
        """Count images for a property"""
        return (
            self.db.query(PropertyImage)
            .filter(PropertyImage.property_id == property_id)
            .count()
        )
    
    def reorder_images(self, property_id: str, image_orders: dict) -> List[PropertyImage]:
        """
        Reorder images for a property
        
        Args:
            property_id: Property ID
            image_orders: Dict mapping image_id to new display_order
            
        Returns:
            Updated list of images
        """
        images = self.get_by_property(property_id)
        
        for image in images:
            image_id_str = str(image.id)
            if image_id_str in image_orders:
                image.display_order = image_orders[image_id_str]
        
        self.db.commit()
        
        # Refresh and return ordered
        for image in images:
            self.db.refresh(image)
        
        return sorted(images, key=lambda x: x.display_order)
    
    def set_primary_image(self, property_id: str, image_id: str) -> PropertyImage:
        """
        Set an image as primary for a property.
        Unsets any other primary images for the same property.
        
        Args:
            property_id: Property ID
            image_id: Image ID to set as primary
            
        Returns:
            Updated primary image
        """
        # Unset all primary flags for this property
        self.db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.is_primary == True
        ).update({"is_primary": False})
        
        # Set the new primary image
        image = self.get_by_id(image_id)
        if image and str(image.property_id) == property_id:
            image.is_primary = True
            image.display_order = 1  # Primary image should be first
            self.db.commit()
            self.db.refresh(image)
            return image
        
        return None
