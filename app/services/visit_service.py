# app/services/visit_service.py
from sqlalchemy.orm import Session
from app.models.visit import Visit
from app.repositories.visit_repository import VisitRepository
from app.dtos.visit_dto import CreateVisitRequest, UpdateVisitRequest
from fastapi import HTTPException, status
from typing import Optional, Tuple, List
from datetime import datetime
from uuid import UUID


class VisitService:
    """Service for Visit business logic"""
    
    def __init__(self, db: Session):
        self.repository = VisitRepository(db)
    
    def create_visit(
        self,
        visit_data: CreateVisitRequest,
        user_id: UUID
    ) -> Visit:
        """Create a new visit"""
        # Check if property exists
        owner_id = self.repository.get_property_owner_id(visit_data.idProperty)
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check for visit conflicts (optional - can allow multiple visits at same time)
        # If you want to prevent conflicts, uncomment:
        # if self.repository.check_visit_conflict(visit_data.idProperty, visit_data.visitDate):
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="Another visit is already scheduled at this time"
        #     )
        
        # Create visit
        visit = Visit(
            idProperty=visit_data.idProperty,
            idUser=user_id,
            visitDate=visit_data.visitDate,
            notes=visit_data.notes
        )
        
        return self.repository.create(visit)
    
    def get_visit_by_id(self, visit_id: UUID) -> Visit:
        """Get visit by ID"""
        visit = self.repository.get_by_id(visit_id)
        if not visit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visit not found"
            )
        return visit
    
    def get_user_visits(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        include_cancelled: bool = False,
        include_completed: bool = True
    ) -> Tuple[List[Visit], int]:
        """Get all visits for a user"""
        return self.repository.get_by_user(
            user_id=user_id,
            page=page,
            size=size,
            include_cancelled=include_cancelled,
            include_completed=include_completed
        )
    
    def get_property_visits(
        self,
        property_id: UUID,
        page: int = 1,
        size: int = 10,
        include_cancelled: bool = False
    ) -> Tuple[List[Visit], int]:
        """Get all visits for a property"""
        # Check if property exists
        owner_id = self.repository.get_property_owner_id(property_id)
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return self.repository.get_by_property(
            property_id=property_id,
            page=page,
            size=size,
            include_cancelled=include_cancelled
        )
    
    def get_upcoming_visits_by_user(self, user_id: UUID) -> List[Visit]:
        """Get upcoming visits for a user"""
        return self.repository.get_upcoming_by_user(user_id)
    
    def update_visit(
        self,
        visit_id: UUID,
        update_data: UpdateVisitRequest,
        user_id: UUID
    ) -> Visit:
        """Update a visit (reschedule or update notes)"""
        visit = self.get_visit_by_id(visit_id)
        
        # Only the user who created the visit can update it
        if visit.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own visits"
            )
        
        # Check if visit can be updated
        if visit.isVisitCompleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update completed visit"
            )
        
        if visit.cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update cancelled visit"
            )
        
        # Update fields
        if update_data.visitDate:
            # Check for conflicts if rescheduling
            if update_data.visitDate != visit.visitDate:
                if self.repository.check_visit_conflict(
                    visit.idProperty,
                    update_data.visitDate,
                    exclude_visit_id=visit_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Another visit is already scheduled at this time"
                    )
            
            visit.reschedule(update_data.visitDate)
        
        if update_data.notes is not None:
            visit.notes = update_data.notes
        
        return self.repository.update(visit)
    
    def complete_visit(
        self,
        visit_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> Visit:
        """Mark visit as completed"""
        visit = self.get_visit_by_id(visit_id)
        
        # Only the user who created the visit can complete it
        if visit.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only complete your own visits"
            )
        
        try:
            visit.complete_visit(notes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        return self.repository.update(visit)
    
    def cancel_visit(
        self,
        visit_id: UUID,
        user_id: UUID,
        cancellation_reason: Optional[str] = None
    ) -> Visit:
        """Cancel a visit"""
        visit = self.get_visit_by_id(visit_id)
        
        # Only the user who created the visit can cancel it
        if visit.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own visits"
            )
        
        try:
            visit.cancel_visit(cancellation_reason)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        return self.repository.update(visit)
    
    def delete_visit(
        self,
        visit_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete a visit"""
        visit = self.get_visit_by_id(visit_id)
        
        # Only the user who created the visit can delete it
        if visit.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own visits"
            )
        
        self.repository.delete(visit)
