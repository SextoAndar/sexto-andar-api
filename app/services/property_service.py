# app/services/property_service.py
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from decimal import Decimal

from app.models.property import Property, PropertyTypeEnum, SalesTypeEnum
from app.models.address import Address
from app.repositories.property_repository import PropertyRepository
from app.dtos.property_dto import (
    CreateHouseRequest,
    CreateApartmentRequest,
    UpdatePropertyRequest,
    PropertyResponse,
    AddressResponse
)

logger = logging.getLogger(__name__)


class PropertyService:
    """Service for property operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.property_repo = PropertyRepository(db)
    
    def create_house(self, house_data: CreateHouseRequest, owner_id: str) -> Property:
        """
        Create a new house property
        
        Args:
            house_data: House creation data
            owner_id: Property owner ID from auth service
            
        Returns:
            Created house property
        """
        try:
            # Create address
            address = Address(
                street=house_data.address.street,
                number=house_data.address.number,
                city=house_data.address.city,
                postal_code=house_data.address.postal_code,
                country=house_data.address.country
            )
            
            # Create house property
            house = Property(
                idPropertyOwner=owner_id,
                address=address,
                propertySize=house_data.propertySize,
                description=house_data.description,
                propertyValue=house_data.propertyValue,
                salesType=SalesTypeEnum(house_data.salesType),
                propertyType=PropertyTypeEnum.HOUSE,
                landPrice=house_data.landPrice,
                isSingleHouse=house_data.isSingleHouse,
                # House doesn't have apartment-specific fields
                condominiumFee=Decimal('0.00'),
                commonArea=False,
                floor=None,
                isPetAllowed=False
            )
            
            created_house = self.property_repo.create(house)
            logger.info(f"House created successfully: {created_house.id} by owner {owner_id}")
            
            return created_house
            
        except ValueError as e:
            logger.error(f"Validation error creating house: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            import traceback
            logger.error(f"Error creating house: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating house property: {str(e)}"
            )
    
    def create_apartment(self, apartment_data: CreateApartmentRequest, owner_id: str) -> Property:
        """
        Create a new apartment property
        
        Args:
            apartment_data: Apartment creation data
            owner_id: Property owner ID from auth service
            
        Returns:
            Created apartment property
        """
        try:
            # Create address
            address = Address(
                street=apartment_data.address.street,
                number=apartment_data.address.number,
                city=apartment_data.address.city,
                postal_code=apartment_data.address.postal_code,
                country=apartment_data.address.country
            )
            
            # Create apartment property
            apartment = Property(
                idPropertyOwner=owner_id,
                address=address,
                propertySize=apartment_data.propertySize,
                description=apartment_data.description,
                propertyValue=apartment_data.propertyValue,
                salesType=SalesTypeEnum(apartment_data.salesType),
                propertyType=PropertyTypeEnum.APARTMENT,
                condominiumFee=apartment_data.condominiumFee,
                commonArea=apartment_data.commonArea,
                floor=apartment_data.floor,
                isPetAllowed=apartment_data.isPetAllowed,
                # Apartment doesn't have house-specific fields
                landPrice=None,
                isSingleHouse=None
            )
            
            created_apartment = self.property_repo.create(apartment)
            logger.info(f"Apartment created successfully: {created_apartment.id} by owner {owner_id}")
            
            return created_apartment
            
        except ValueError as e:
            logger.error(f"Validation error creating apartment: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating apartment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating apartment property"
            )
    
    def get_property_by_id(self, property_id: str) -> Property:
        """Get property by ID"""
        property_obj = self.property_repo.get_by_id(property_id)
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return property_obj
    
    def get_properties_by_owner(
        self, 
        owner_id: str, 
        page: int = 1, 
        size: int = 10,
        property_type: Optional[str] = None,
        sales_type: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[Property], int]:
        """
        Get properties by owner with pagination and filters
        
        Args:
            owner_id: Property owner ID
            page: Page number
            size: Page size
            property_type: Filter by property type (HOUSE/APARTMENT)
            sales_type: Filter by sales type (RENT/SALE)
            active_only: Show only active properties
            
        Returns:
            Tuple of (properties list, total count)
        """
        return self.property_repo.get_by_owner(
            owner_id, 
            page, 
            size,
            property_type=property_type,
            sales_type=sales_type,
            active_only=active_only
        )
    
    def get_all_properties(
        self,
        page: int = 1,
        size: int = 10,
        property_type: Optional[str] = None,
        sales_type: Optional[str] = None,
        active_only: bool = True
    ) -> Tuple[List[Property], int]:
        """Get all properties with pagination and filters"""
        # Convert string to enum if provided
        property_type_enum = PropertyTypeEnum(property_type) if property_type else None
        sales_type_enum = SalesTypeEnum(sales_type) if sales_type else None
        
        return self.property_repo.get_all_paginated(
            page=page,
            size=size,
            property_type=property_type_enum,
            sales_type=sales_type_enum,
            active_only=active_only
        )
    
    def update_property(
        self, 
        property_id: str, 
        update_data: UpdatePropertyRequest, 
        owner_id: str
    ) -> Property:
        """Update property (only by owner)"""
        property_obj = self.get_property_by_id(property_id)
        
        # Check ownership
        if str(property_obj.idPropertyOwner) != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this property"
            )
        
        try:
            # Update fields if provided
            if update_data.propertySize is not None:
                property_obj.propertySize = update_data.propertySize
            
            if update_data.description is not None:
                property_obj.description = update_data.description
            
            if update_data.propertyValue is not None:
                property_obj.propertyValue = update_data.propertyValue
            
            if update_data.salesType is not None:
                property_obj.salesType = SalesTypeEnum(update_data.salesType)
            
            # Update apartment-specific fields
            if property_obj.is_apartment():
                if update_data.condominiumFee is not None:
                    property_obj.condominiumFee = update_data.condominiumFee
                
                if update_data.commonArea is not None:
                    property_obj.commonArea = update_data.commonArea
                
                if update_data.floor is not None:
                    property_obj.floor = update_data.floor
                
                if update_data.isPetAllowed is not None:
                    property_obj.isPetAllowed = update_data.isPetAllowed
            
            # Update house-specific fields
            if property_obj.is_house():
                if update_data.landPrice is not None:
                    property_obj.landPrice = update_data.landPrice
                
                if update_data.isSingleHouse is not None:
                    property_obj.isSingleHouse = update_data.isSingleHouse
            
            # Update address if provided
            if update_data.address is not None:
                property_obj.address.street = update_data.address.street
                property_obj.address.number = update_data.address.number
                property_obj.address.city = update_data.address.city
                property_obj.address.postal_code = update_data.address.postal_code
                property_obj.address.country = update_data.address.country
            
            updated_property = self.property_repo.update(property_obj)
            logger.info(f"Property updated successfully: {property_id}")
            
            return updated_property
            
        except ValueError as e:
            logger.error(f"Validation error updating property: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error updating property: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating property"
            )
    
    def delete_property(self, property_id: str, user_id: str, is_admin: bool = False) -> None:
        """
        Delete property (soft delete - deactivate)
        
        Args:
            property_id: Property ID to delete
            user_id: User ID requesting deletion
            is_admin: Whether the user is an admin
        
        Raises:
            HTTPException: If user is not the owner and not an admin
        """
        property_obj = self.get_property_by_id(property_id)
        
        # Check ownership (admins can delete any property)
        if not is_admin and str(property_obj.idPropertyOwner) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this property"
            )
        
        try:
            self.property_repo.deactivate(property_obj)
            if is_admin:
                logger.info(f"Property deactivated by ADMIN: {property_id}")
            else:
                logger.info(f"Property deactivated by owner: {property_id}")
            
        except Exception as e:
            logger.error(f"Error deleting property: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting property"
            )
    
    def activate_property(self, property_id: str, owner_id: str) -> Property:
        """Activate property"""
        property_obj = self.get_property_by_id(property_id)
        
        # Check ownership
        if str(property_obj.idPropertyOwner) != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to activate this property"
            )
        
        try:
            activated_property = self.property_repo.activate(property_obj)
            logger.info(f"Property activated successfully: {property_id}")
            
            return activated_property
            
        except Exception as e:
            logger.error(f"Error activating property: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error activating property"
            )
    
    def get_portfolio_stats(self, owner_id: str) -> dict:
        """
        Get comprehensive portfolio statistics for property owner
        
        Args:
            owner_id: Property owner ID
            
        Returns:
            Dictionary with portfolio statistics including counts,
            distribution by type/sales, and financial metrics
        """
        try:
            # Get all properties (including inactive)
            all_properties, total = self.property_repo.get_by_owner(
                owner_id, 
                page=1, 
                size=1000,  # Get all
                active_only=False
            )
            
            # Calculate statistics
            active_count = sum(1 for p in all_properties if p.is_active)
            inactive_count = total - active_count
            
            # By property type
            houses = [p for p in all_properties if p.is_house()]
            apartments = [p for p in all_properties if p.is_apartment()]
            
            # By sales type
            for_sale = [p for p in all_properties if p.salesType == SalesTypeEnum.SALE]
            for_rent = [p for p in all_properties if p.salesType == SalesTypeEnum.RENT]
            
            # Financial calculations
            total_value = sum(p.propertyValue for p in all_properties if p.is_active)
            avg_value = total_value / active_count if active_count > 0 else Decimal('0')
            
            # Calculate potential monthly rent (only for rent properties)
            rent_potential = sum(
                p.propertyValue * Decimal('0.006')  # Assuming 0.6% monthly rent
                for p in for_rent 
                if p.is_active
            )
            
            return {
                "total_properties": total,
                "active_properties": active_count,
                "inactive_properties": inactive_count,
                "total_houses": len(houses),
                "total_apartments": len(apartments),
                "total_for_sale": len(for_sale),
                "total_for_rent": len(for_rent),
                "total_portfolio_value": total_value,
                "average_property_value": avg_value,
                "total_monthly_rent_potential": rent_potential
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating portfolio statistics"
            )
