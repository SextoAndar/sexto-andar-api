# app/dtos/visit_dto.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID


class CreateVisitRequest(BaseModel):
    """Request model for creating a new visit"""
    idProperty: UUID = Field(..., description="Property ID to visit")
    visitDate: datetime = Field(..., description="Desired visit date and time")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @field_validator('visitDate')
    @classmethod
    def validate_visit_date(cls, v):
        if v < datetime.now():
            raise ValueError('Visit date must be in the future')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "idProperty": "123e4567-e89b-12d3-a456-426614174000",
                "visitDate": "2024-12-20T14:00:00",
                "notes": "Interested in the kitchen and backyard"
            }
        }


class UpdateVisitRequest(BaseModel):
    """Request model for updating a visit"""
    visitDate: Optional[datetime] = Field(None, description="New visit date and time")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "visitDate": "2024-12-21T15:00:00",
                "notes": "Updated: Prefer afternoon visits"
            }
        }


class CompleteVisitRequest(BaseModel):
    """Request model for marking visit as completed"""
    notes: Optional[str] = Field(None, max_length=500, description="Visit completion notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Visit completed successfully. Property is as described."
            }
        }


class CancelVisitRequest(BaseModel):
    """Request model for cancelling a visit"""
    cancellation_reason: Optional[str] = Field(None, max_length=200, description="Reason for cancellation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cancellation_reason": "Schedule conflict"
            }
        }


class VisitResponse(BaseModel):
    """Response model for visit details"""
    id: UUID
    idProperty: UUID
    idUser: UUID
    visitDate: datetime
    isVisitCompleted: bool
    cancelled: bool
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    status: str = Field(description="Visit status display")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "idProperty": "123e4567-e89b-12d3-a456-426614174001",
                "idUser": "123e4567-e89b-12d3-a456-426614174002",
                "visitDate": "2024-12-20T14:00:00",
                "isVisitCompleted": False,
                "cancelled": False,
                "notes": "Interested in the property",
                "cancellation_reason": None,
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-01T10:00:00",
                "status": "Scheduled"
            }
        }
    
    @classmethod
    def from_visit(cls, visit):
        """Create response from Visit model"""
        return cls(
            id=visit.id,
            idProperty=visit.idProperty,
            idUser=visit.idUser,
            visitDate=visit.visitDate,
            isVisitCompleted=visit.isVisitCompleted,
            cancelled=visit.cancelled,
            notes=visit.notes,
            cancellation_reason=visit.cancellation_reason,
            created_at=visit.created_at,
            updated_at=visit.updated_at,
            status=visit.get_status_display()
        )


class VisitListResponse(BaseModel):
    """Response model for paginated visit list"""
    visits: list[VisitResponse]
    total: int
    page: int
    size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "visits": [],
                "total": 50,
                "page": 1,
                "size": 10,
                "total_pages": 5
            }
        }
