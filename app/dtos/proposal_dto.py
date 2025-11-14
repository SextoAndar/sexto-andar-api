# app/dtos/proposal_dto.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal


class CreateProposalRequest(BaseModel):
    """Request model for creating a new proposal"""
    idProperty: UUID = Field(..., description="Property ID for the proposal")
    proposalValue: Decimal = Field(..., gt=0, description="Proposed value/price")
    message: Optional[str] = Field(None, max_length=1000, description="Message to property owner")
    
    @field_validator('proposalValue')
    @classmethod
    def validate_value(cls, v):
        if v <= 0:
            raise ValueError('Proposal value must be greater than zero')
        if v > Decimal('99999999.99'):
            raise ValueError('Proposal value too high')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "idProperty": "123e4567-e89b-12d3-a456-426614174000",
                "proposalValue": 250000.00,
                "message": "Very interested in this property. Can we negotiate?"
            }
        }


class RespondProposalRequest(BaseModel):
    """Request model for accepting/rejecting a proposal"""
    response_message: Optional[str] = Field(None, max_length=500, description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response_message": "Thank you for your proposal. We accept your offer."
            }
        }


class ProposalResponse(BaseModel):
    """Response model for proposal details"""
    id: UUID
    idProperty: UUID
    idUser: UUID
    proposalDate: datetime
    proposalValue: Decimal
    status: str
    message: Optional[str] = None
    response_message: Optional[str] = None
    response_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_active: bool = Field(description="Whether proposal is active")
    days_until_expiry: int = Field(description="Days until expiration")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "idProperty": "123e4567-e89b-12d3-a456-426614174001",
                "idUser": "123e4567-e89b-12d3-a456-426614174002",
                "proposalDate": "2024-12-01T10:00:00",
                "proposalValue": 250000.00,
                "status": "pending",
                "message": "Interested in buying",
                "response_message": None,
                "response_date": None,
                "expires_at": "2024-12-31T10:00:00",
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-01T10:00:00",
                "is_active": True,
                "days_until_expiry": 30
            }
        }
    
    @classmethod
    def from_proposal(cls, proposal):
        """Create response from Proposal model"""
        return cls(
            id=proposal.id,
            idProperty=proposal.idProperty,
            idUser=proposal.idUser,
            proposalDate=proposal.proposalDate,
            proposalValue=proposal.proposalValue,
            status=proposal.status.value,
            message=proposal.message,
            response_message=proposal.response_message,
            response_date=proposal.response_date,
            expires_at=proposal.expires_at,
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
            is_active=proposal.is_active(),
            days_until_expiry=proposal.days_until_expiry()
        )


class ProposalListResponse(BaseModel):
    """Response model for paginated proposal list"""
    proposals: list[ProposalResponse]
    total: int
    page: int
    size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "proposals": [],
                "total": 25,
                "page": 1,
                "size": 10,
                "total_pages": 3
            }
        }


class UserInfoDTO(BaseModel):
    """User information for proposal responses"""
    id: UUID
    username: str
    fullName: str
    email: str
    phoneNumber: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "fullName": "John Doe",
                "email": "john.doe@email.com",
                "phoneNumber": "+5511999999999"
            }
        }


class PropertyInfoDTO(BaseModel):
    """Property basic information for proposal responses"""
    id: UUID
    title: str
    address: str
    propertyValue: Decimal
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Beautiful Apartment",
                "address": "Main Street, 123 - São Paulo",
                "propertyValue": 300000.00
            }
        }


class ProposalWithUserResponse(BaseModel):
    """Response model for proposal with user and property details"""
    id: UUID
    idProperty: UUID
    idUser: UUID
    proposalDate: datetime
    proposalValue: Decimal
    status: str
    message: Optional[str] = None
    response_message: Optional[str] = None
    response_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    days_until_expiry: int
    
    # Additional info
    user: Optional[UserInfoDTO] = None
    property: Optional[PropertyInfoDTO] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "idProperty": "123e4567-e89b-12d3-a456-426614174001",
                "idUser": "123e4567-e89b-12d3-a456-426614174002",
                "proposalDate": "2024-12-01T10:00:00",
                "proposalValue": 250000.00,
                "status": "pending",
                "message": "Interested in buying",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174002",
                    "username": "johndoe",
                    "fullName": "John Doe",
                    "email": "john.doe@email.com",
                    "phoneNumber": "+5511999999999"
                },
                "property": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "title": "Beautiful Apartment",
                    "address": "Main Street, 123 - São Paulo",
                    "propertyValue": 300000.00
                },
                "is_active": True,
                "days_until_expiry": 30
            }
        }
    
    @classmethod
    def from_proposal(cls, proposal, user_info: Optional[dict] = None, property_info: Optional[dict] = None):
        """Create response from Proposal model with user and property info"""
        return cls(
            id=proposal.id,
            idProperty=proposal.idProperty,
            idUser=proposal.idUser,
            proposalDate=proposal.proposalDate,
            proposalValue=proposal.proposalValue,
            status=proposal.status.value,
            message=proposal.message,
            response_message=proposal.response_message,
            response_date=proposal.response_date,
            expires_at=proposal.expires_at,
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
            is_active=proposal.is_active(),
            days_until_expiry=proposal.days_until_expiry(),
            user=UserInfoDTO(**user_info) if user_info else None,
            property=PropertyInfoDTO(**property_info) if property_info else None
        )


class ProposalWithUserListResponse(BaseModel):
    """Response model for paginated proposal list with user details"""
    proposals: list[ProposalWithUserResponse]
    total: int
    page: int
    size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "proposals": [],
                "total": 25,
                "page": 1,
                "size": 10,
                "total_pages": 3
            }
        }
