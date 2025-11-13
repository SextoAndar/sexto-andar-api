# app/models/visit.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.database.connection import BaseModel
from datetime import datetime, timedelta, timezone
import uuid



class Visit(BaseModel):
    """
    Visit class for property visit scheduling
    """
    __tablename__ = "visits"
    
    # Main attributes
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Foreign Keys
    idProperty = Column(
        UUID(as_uuid=True),
        ForeignKey('properties.id'),
        nullable=False,
        index=True
    )
    
    idUser = Column(
        UUID(as_uuid=True),
        # ForeignKey('accounts.id'),  # Commented out - table in different service
        nullable=False,
        index=True
    )
    
    # Visit attributes
    visitDate = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    isVisitCompleted = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Additional useful fields
    notes = Column(
        String(500),
        nullable=True
    )
    
    cancelled = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    cancellation_reason = Column(
        String(200),
        nullable=True
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
    property = relationship(
        "Property"
    )
    
    # NOTE: User (Account) is managed by sexto-andar-auth service
    # We only store idUser (foreign key) but don't create relationship
    
    # Validations
    @validates('visitDate')
    def validate_visit_date(self, key, visit_date):
        """Visit date validation"""
        if not visit_date:
            raise ValueError("Visit date is required")
        
        # Don't allow scheduling in the past (with 1 hour margin)
        now = datetime.now(timezone.utc)
        if visit_date < (now - timedelta(hours=1)):
            raise ValueError("Cannot schedule visit in the past")
        
        # Don't allow scheduling too far in the future (6 months)
        max_future = now + timedelta(days=180)
        if visit_date > max_future:
            raise ValueError("Cannot schedule visit more than 6 months in advance")
        
        return visit_date
    
    @validates('notes')
    def validate_notes(self, key, notes):
        """Notes validation"""
        if notes and len(notes) > 500:
            raise ValueError("Notes must have at most 500 characters")
        
        return notes.strip() if notes else notes
    
    @validates('cancellation_reason')
    def validate_cancellation_reason(self, key, reason):
        """Cancellation reason validation"""
        if reason and len(reason) > 200:
            raise ValueError("Cancellation reason must have at most 200 characters")
        
        return reason.strip() if reason else reason
    
    # Convenience methods
    def is_upcoming(self) -> bool:
        """Check if visit is scheduled for the future"""
        return self.visitDate > datetime.now(timezone.utc) and not self.cancelled
    
    def is_past(self) -> bool:
        """Check if visit has already passed"""
        return self.visitDate < datetime.now(timezone.utc)
    
    def is_today(self) -> bool:
        """Check if visit is today"""
        today = datetime.now(timezone.utc).date()
        return self.visitDate.date() == today
    
    def can_be_completed(self) -> bool:
        """Check if visit can be marked as completed"""
        return (
            not self.cancelled and 
            not self.isVisitCompleted and 
            self.visitDate <= datetime.now(timezone.utc)
        )
    
    def can_be_cancelled(self) -> bool:
        """Check if visit can be cancelled"""
        return (
            not self.cancelled and 
            not self.isVisitCompleted and
            self.is_upcoming()
        )
    
    def complete_visit(self, notes: str = None):
        """Mark visit as completed"""
        if not self.can_be_completed():
            raise ValueError("Visit cannot be marked as completed")
        
        self.isVisitCompleted = True
        if notes:
            self.notes = notes
    
    def cancel_visit(self, reason: str = None):
        """Cancel visit"""
        if not self.can_be_cancelled():
            raise ValueError("Visit cannot be cancelled")
        
        self.cancelled = True
        self.cancellation_reason = reason
    
    def reschedule(self, new_date: datetime):
        """Reschedule visit"""
        if self.isVisitCompleted:
            raise ValueError("Cannot reschedule completed visit")
        
        if self.cancelled:
            raise ValueError("Cannot reschedule cancelled visit")
        
        # Validate new date
        self.validate_visit_date('visitDate', new_date)
        self.visitDate = new_date
    
    def get_status_display(self) -> str:
        """Returns visit status for display"""
        if self.cancelled:
            return "Cancelled"
        elif self.isVisitCompleted:
            return "Completed"
        elif self.is_past() and not self.isVisitCompleted:
            return "Missed"
        elif self.is_today():
            return "Today"
        elif self.is_upcoming():
            return "Scheduled"
        else:
            return "Undefined"
    
    def time_until_visit(self) -> str:
        """Returns time until visit"""
        if self.cancelled or self.isVisitCompleted:
            return "N/A"
        
        now = datetime.now(timezone.utc)
        delta = self.visitDate - now
        
        if delta.days > 0:
            return f"In {delta.days} days"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"In {hours} hours"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"In {minutes} minutes"
        else:
            return "Now"
    
    def __repr__(self):
        return f"<Visit(id={self.id}, property_id={self.idProperty}, user_id={self.idUser}, date='{self.visitDate}', completed={self.isVisitCompleted})>"
    
    def __str__(self):
        status = self.get_status_display()
        return f"Visit {status} - {self.visitDate.strftime('%m/%d/%Y %H:%M')}"