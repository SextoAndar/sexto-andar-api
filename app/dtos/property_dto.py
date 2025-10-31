# app/dtos/property_dto.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal
import uuid


class AddressRequest(BaseModel):
    """Address request DTO"""
    street: str = Field(..., min_length=3, max_length=200, description="Street name")
    number: str = Field(..., min_length=1, max_length=20, description="Street number")
    city: str = Field(..., min_length=2, max_length=100, description="City name")
    postal_code: str = Field(..., min_length=8, max_length=20, description="Postal code (CEP)")
    country: str = Field(default="Brazil", max_length=100, description="Country")
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Validate postal code format"""
        import re
        clean_cep = re.sub(r'\D', '', v)
        if len(clean_cep) != 8:
            raise ValueError("Postal code must have 8 digits")
        return v


class AddressResponse(BaseModel):
    """Address response DTO"""
    id: Union[str, uuid.UUID]
    street: str
    number: str
    city: str
    postal_code: str
    country: str
    
    class Config:
        from_attributes = True
        
    def model_dump(self, **kwargs):
        """Override model_dump to convert UUID to string"""
        data = super().model_dump(**kwargs)
        if isinstance(data.get('id'), uuid.UUID):
            data['id'] = str(data['id'])
        return data


class CreateHouseRequest(BaseModel):
    """Create house request DTO (US14)"""
    # Address
    address: AddressRequest
    
    # Property attributes
    propertySize: Decimal = Field(..., gt=0, description="Property size in square meters")
    description: str = Field(..., min_length=10, max_length=1000, description="Property description")
    propertyValue: Decimal = Field(..., gt=0, description="Property value")
    salesType: str = Field(..., description="Sales type: 'rent' or 'sale'")
    
    # House-specific attributes (US14)
    landPrice: Decimal = Field(..., gt=0, description="Land/terrain price")
    isSingleHouse: bool = Field(default=True, description="Is it a single house on the land?")
    
    @field_validator('salesType')
    @classmethod
    def validate_sales_type(cls, v: str) -> str:
        """Validate sales type"""
        if v not in ['rent', 'sale']:
            raise ValueError("Sales type must be 'rent' or 'sale'")
        return v


class CreateApartmentRequest(BaseModel):
    """Create apartment request DTO (US15)"""
    # Address
    address: AddressRequest
    
    # Property attributes
    propertySize: Decimal = Field(..., gt=0, description="Property size in square meters")
    description: str = Field(..., min_length=10, max_length=1000, description="Property description")
    propertyValue: Decimal = Field(..., gt=0, description="Property value")
    salesType: str = Field(..., description="Sales type: 'rent' or 'sale'")
    
    # Apartment-specific attributes (US15)
    condominiumFee: Decimal = Field(..., ge=0, description="Condominium fee")
    commonArea: bool = Field(default=False, description="Has common area?")
    floor: int = Field(..., ge=-10, le=200, description="Floor number")
    isPetAllowed: bool = Field(default=False, description="Allows pets?")
    
    @field_validator('salesType')
    @classmethod
    def validate_sales_type(cls, v: str) -> str:
        """Validate sales type"""
        if v not in ['rent', 'sale']:
            raise ValueError("Sales type must be 'rent' or 'sale'")
        return v


class UpdatePropertyRequest(BaseModel):
    """Update property request DTO"""
    propertySize: Optional[Decimal] = Field(None, gt=0, description="Property size in square meters")
    description: Optional[str] = Field(None, min_length=10, max_length=1000, description="Property description")
    propertyValue: Optional[Decimal] = Field(None, gt=0, description="Property value")
    salesType: Optional[str] = Field(None, description="Sales type: 'rent' or 'sale'")
    
    # Apartment-specific (optional)
    condominiumFee: Optional[Decimal] = Field(None, ge=0, description="Condominium fee")
    commonArea: Optional[bool] = Field(None, description="Has common area?")
    floor: Optional[int] = Field(None, ge=-10, le=200, description="Floor number")
    isPetAllowed: Optional[bool] = Field(None, description="Allows pets?")
    
    # House-specific (optional)
    landPrice: Optional[Decimal] = Field(None, gt=0, description="Land/terrain price")
    isSingleHouse: Optional[bool] = Field(None, description="Is it a single house on the land?")
    
    # Address update
    address: Optional[AddressRequest] = None
    
    @field_validator('salesType')
    @classmethod
    def validate_sales_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate sales type"""
        if v is not None and v not in ['rent', 'sale']:
            raise ValueError("Sales type must be 'rent' or 'sale'")
        return v


class PropertyResponse(BaseModel):
    """Property response DTO"""
    id: Union[str, uuid.UUID]
    idPropertyOwner: Union[str, uuid.UUID]
    address: AddressResponse
    propertySize: Decimal
    description: str
    propertyValue: Decimal
    publishDate: datetime
    condominiumFee: Optional[Decimal]
    commonArea: bool
    floor: Optional[int]
    isPetAllowed: bool
    landPrice: Optional[Decimal]
    isSingleHouse: Optional[bool]
    salesType: str
    propertyType: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    def model_dump(self, **kwargs):
        """Override model_dump to convert UUIDs to strings"""
        data = super().model_dump(**kwargs)
        if isinstance(data.get('id'), uuid.UUID):
            data['id'] = str(data['id'])
        if isinstance(data.get('idPropertyOwner'), uuid.UUID):
            data['idPropertyOwner'] = str(data['idPropertyOwner'])
        return data


class PropertyListResponse(BaseModel):
    """Property list response DTO"""
    properties: list[PropertyResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PortfolioStatsResponse(BaseModel):
    """Portfolio statistics response DTO (US16)"""
    total_properties: int = Field(description="Total number of properties")
    active_properties: int = Field(description="Number of active properties")
    inactive_properties: int = Field(description="Number of inactive properties")
    
    # By property type
    total_houses: int = Field(description="Total houses")
    total_apartments: int = Field(description="Total apartments")
    
    # By sales type
    total_for_sale: int = Field(description="Properties for sale")
    total_for_rent: int = Field(description="Properties for rent")
    
    # Financial
    total_portfolio_value: Decimal = Field(description="Sum of all property values")
    average_property_value: Decimal = Field(description="Average property value")
    total_monthly_rent_potential: Decimal = Field(description="Potential monthly rent income")
    
    class Config:
        from_attributes = True
