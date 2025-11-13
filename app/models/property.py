# app/models/property.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.database.connection import BaseModel
from datetime import datetime, timezone
import uuid
import enum

class SalesTypeEnum(enum.Enum):
    """Enum for sales type"""
    RENT = "RENT"
    SALE = "SALE"

class PropertyTypeEnum(enum.Enum):
    """Enum for property type"""
    APARTMENT = "APARTMENT"
    HOUSE = "HOUSE"

class Property(BaseModel):
    """
    Property class for real estate/properties in the system
    """
    __tablename__ = "properties"
    
    # Main attributes
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        nullable=False
    )
    
    # Foreign Key to PropertyOwner (Account with property_owner role)
    # NOTE: Foreign key constraint should be created manually in database
    # since accounts table is managed by sexto-andar-auth service
    idPropertyOwner = Column(
        UUID(as_uuid=True),
        # ForeignKey('accounts.id'),  # Commented out - table in different service
        nullable=False,
        index=True
    )
    
    # Foreign Key to Address (composition)
    address_id = Column(
        UUID(as_uuid=True),
        ForeignKey('addresses.id'),
        nullable=False
    )
    
    # Property attributes
    propertySize = Column(
        Numeric(10, 2),  # 10 digits total, 2 decimals (e.g., 99999999.99)
        nullable=False
    )
    
    description = Column(
        String(1000),
        nullable=False
    )
    
    propertyValue = Column(
        Numeric(10, 2),  # 10 digits, 2 decimals
        nullable=False
    )
    
    publishDate = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    condominiumFee = Column(
        Numeric(10, 2),
        nullable=True,
        default=0.00
    )
    
    commonArea = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    floor = Column(
        Integer,
        nullable=True
    )
    
    isPetAllowed = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # House-specific fields
    landPrice = Column(
        Numeric(10, 2),
        nullable=True  # Only for houses
    )
    
    isSingleHouse = Column(
        Boolean,
        default=True,
        nullable=True  # Only for houses
    )
    
    # Enums for sales type and property type
    salesType = Column(
        Enum(SalesTypeEnum),
        nullable=False
    )
    
    propertyType = Column(
        Enum(PropertyTypeEnum),
        nullable=False
    )
    
    # Property status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    # NOTE: Property owner (Account) is managed by sexto-andar-auth service
    # We only store the idPropertyOwner (foreign key) but don't create a relationship
    # since Account model is not in this service
    
    # Relationship with Address (1:1 composition)
    address = relationship(
        "Address",
        cascade="all, delete-orphan",
        single_parent=True
    )
    
    # Relationship with Visits
    visits = relationship(
        "Visit",
        cascade="all, delete-orphan"
    )
    
    # Relationship with Proposals
    proposals = relationship(
        "Proposal",
        cascade="all, delete-orphan"
    )
    
    # Validations
    @validates('propertySize')
    def validate_property_size(self, key, size):
        """Property size validation"""
        if not size:
            raise ValueError("Property size is required")
        
        if size <= 0:
            raise ValueError("Property size must be greater than zero")
        
        if size > 999999:  # 1 million m²
            raise ValueError("Property size too large")
        
        return size
    
    @validates('propertyValue')
    def validate_property_value(self, key, value):
        """Property value validation"""
        if not value:
            raise ValueError("Property value is required")
        
        if value <= 0:
            raise ValueError("Property value must be greater than zero")
        
        if value > 99999999.99:  # 100 million
            raise ValueError("Property value too high")
        
        return value
    
    @validates('condominiumFee')
    def validate_condominium_fee(self, key, fee):
        """Condominium fee validation"""
        if fee is not None and fee < 0:
            raise ValueError("Condominium fee cannot be negative")
        
        return fee
    
    @validates('description')
    def validate_description(self, key, description):
        """Description validation"""
        if not description or not description.strip():
            raise ValueError("Description is required")
        
        if len(description.strip()) < 10:
            raise ValueError("Description must have at least 10 characters")
        
        if len(description) > 1000:
            raise ValueError("Description must have at most 1000 characters")
        
        return description.strip()
    
    @validates('floor')
    def validate_floor(self, key, floor):
        """Floor validation"""
        if floor is not None:
            if floor < -10:  # Maximum basement -10
                raise ValueError("Floor too low")
            
            if floor > 200:  # Maximum 200 floors
                raise ValueError("Floor too high")
        
        return floor
    
    @validates('salesType')
    def validate_sales_type(self, key, sales_type):
        """Sales type validation"""
        if not sales_type:
            raise ValueError("Sales type is required")
        
        if isinstance(sales_type, str):
            try:
                return SalesTypeEnum(sales_type)
            except ValueError:
                raise ValueError(f"Sales type must be '{SalesTypeEnum.RENT.value}' or '{SalesTypeEnum.SALE.value}'")
        
        return sales_type
    
    @validates('propertyType')
    def validate_property_type(self, key, property_type):
        """Property type validation"""
        if not property_type:
            raise ValueError("Property type is required")
        
        if isinstance(property_type, str):
            try:
                return PropertyTypeEnum(property_type)
            except ValueError:
                raise ValueError(f"Property type must be '{PropertyTypeEnum.APARTMENT.value}' or '{PropertyTypeEnum.HOUSE.value}'")
        
        return property_type
    
    # Convenience methods
    def is_for_rent(self) -> bool:
        """Check if it's for rent"""
        return self.salesType == SalesTypeEnum.RENT
    
    def is_for_sale(self) -> bool:
        """Check if it's for sale"""
        return self.salesType == SalesTypeEnum.SALE
    
    def is_apartment(self) -> bool:
        """Check if it's an apartment"""
        return self.propertyType == PropertyTypeEnum.APARTMENT
    
    def is_house(self) -> bool:
        """Check if it's a house"""
        return self.propertyType == PropertyTypeEnum.HOUSE
    
    def get_total_cost(self) -> float:
        """Calculate total cost (value + condominium for rent)"""
        total = float(self.propertyValue)
        
        if self.is_for_rent() and self.condominiumFee:
            total += float(self.condominiumFee)
        
        return total
    
    def get_sales_type_display(self) -> str:
        """Returns the sales type name for display"""
        sales_names = {
            SalesTypeEnum.RENT: "Rent",
            SalesTypeEnum.SALE: "Sale"
        }
        return sales_names.get(self.salesType, "Unknown")
    
    def get_property_type_display(self) -> str:
        """Returns the property type name for display"""
        property_names = {
            PropertyTypeEnum.APARTMENT: "Apartment",
            PropertyTypeEnum.HOUSE: "House"
        }
        return property_names.get(self.propertyType, "Unknown")
    
    def get_full_address(self) -> str:
        """Returns full address if available"""
        if self.address:
            return f"{self.address.street}, {self.address.number} - {self.address.city}"
        return "Address not provided"
    
    def activate(self):
        """Activate property"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate property"""
        self.is_active = False
    
    def __repr__(self):
        return f"<Property(id={self.id}, type='{self.propertyType.value}', sales_type='{self.salesType.value}', value={self.propertyValue})>"
    
    def __str__(self):
        return f"{self.get_property_type_display()} - {self.get_sales_type_display()} - $ {self.propertyValue}"