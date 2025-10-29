# app/models/proposal.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.database.connection import BaseModel
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import enum



class ProposalStatusEnum(enum.Enum):
    """Enum for proposal status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class Proposal(BaseModel):
    """
    Proposal class for property purchase/rental proposals
    """
    __tablename__ = "proposals"
    
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
        ForeignKey('accounts.id'),
        nullable=False,
        index=True
    )
    
    # Proposal attributes
    proposalDate = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    proposalValue = Column(
        Numeric(10, 2),
        nullable=False
    )
    
    # Proposal status
    status = Column(
        Enum(ProposalStatusEnum),
        default=ProposalStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    
    # Additional fields
    message = Column(
        String(1000),
        nullable=True
    )
    
    response_message = Column(
        String(500),
        nullable=True
    )
    
    response_date = Column(
        DateTime,
        nullable=True
    )
    
    # Proposal validity (default 30 days)
    expires_at = Column(
        DateTime,
        nullable=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at = Column(
        DateTime,
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
    @validates('proposalValue')
    def validate_proposal_value(self, key, value):
        """Proposal value validation"""
        if not value:
            raise ValueError("Proposal value is required")
        
        if value <= 0:
            raise ValueError("Proposal value must be greater than zero")
        
        if value > Decimal('99999999.99'):  # 100 million
            raise ValueError("Proposal value too high")
        
        return value

    @validates('message')
    def validate_message(self, key, message):
        """Message validation"""
        if message and len(message) > 1000:
            raise ValueError("Message must have at most 1000 characters")
        
        return message.strip() if message else message

    @validates('response_message')
    def validate_response_message(self, key, message):
        """Response message validation"""
        if message and len(message) > 500:
            raise ValueError("Response message must have at most 500 characters")
        
        return message.strip() if message else message

    @validates('expires_at')
    def validate_expires_at(self, key, expires_at):
        """Expiration date validation"""
        if expires_at and expires_at <= datetime.now(timezone.utc):
            raise ValueError("Expiration date must be in the future")
        
        return expires_at

    def __init__(self, **kwargs):
        """Constructor with automatic expiration setup"""
        super().__init__(**kwargs)
        
        # If no expiration defined, set to 30 days
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    # Convenience methods
    def is_pending(self) -> bool:
        """Check if proposal is pending"""
        return self.status == ProposalStatusEnum.PENDING
    
    def is_accepted(self) -> bool:
        """Check if proposal was accepted"""
        return self.status == ProposalStatusEnum.ACCEPTED
    
    def is_rejected(self) -> bool:
        """Check if proposal was rejected"""
        return self.status == ProposalStatusEnum.REJECTED
    
    def is_withdrawn(self) -> bool:
        """Check if proposal was withdrawn"""
        return self.status == ProposalStatusEnum.WITHDRAWN
    
    def is_expired(self) -> bool:
        """Check if proposal has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_active(self) -> bool:
        """Check if proposal is active (pending and not expired)"""
        return self.is_pending() and not self.is_expired()
    
    def can_be_accepted(self) -> bool:
        """Check if proposal can be accepted"""
        return self.is_active()
    
    def can_be_rejected(self) -> bool:
        """Check if proposal can be rejected"""
        return self.is_active()
    
    def can_be_withdrawn(self) -> bool:
        """Check if proposal can be withdrawn by user"""
        return self.is_active()
    
    def accept(self, response_message: str = None):
        """Accept proposal"""
        if not self.can_be_accepted():
            raise ValueError("Proposal cannot be accepted")
        
        self.status = ProposalStatusEnum.ACCEPTED
        self.response_message = response_message
        self.response_date = datetime.now(timezone.utc)
    
    def reject(self, response_message: str = None):
        """Reject proposal"""
        if not self.can_be_rejected():
            raise ValueError("Proposal cannot be rejected")
        
        self.status = ProposalStatusEnum.REJECTED
        self.response_message = response_message
        self.response_date = datetime.now(timezone.utc)
    
    def withdraw(self):
        """Withdraw proposal (by user)"""
        if not self.can_be_withdrawn():
            raise ValueError("Proposal cannot be withdrawn")
        
        self.status = ProposalStatusEnum.WITHDRAWN
        self.response_date = datetime.now(timezone.utc)
    
    def calculate_difference_percentage(self) -> float:
        """Calculate percentage difference with original property value"""
        if not hasattr(self, 'property') or not self.property:
            return 0.0
        
        original_value = float(self.property.propertyValue)
        proposed_value = float(self.proposalValue)
        
        if original_value == 0:
            return 0.0
        
        return ((proposed_value - original_value) / original_value) * 100
    
    def get_difference_amount(self) -> Decimal:
        """Calculate absolute value difference with original price"""
        if not hasattr(self, 'property') or not self.property:
            return Decimal('0.00')
        
        return self.proposalValue - self.property.propertyValue
    
    def get_status_display(self) -> str:
        """Returns proposal status for display"""
        status_names = {
            ProposalStatusEnum.PENDING: "Pending",
            ProposalStatusEnum.ACCEPTED: "Accepted",
            ProposalStatusEnum.REJECTED: "Rejected",
            ProposalStatusEnum.WITHDRAWN: "Withdrawn"
        }
        return status_names.get(self.status, "Unknown")
    
    def days_until_expiry(self) -> int:
        """Returns days until expiration"""
        if not self.expires_at:
            return -1
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def extend_expiry(self, days: int):
        """Extend expiration deadline"""
        if not self.is_pending():
            raise ValueError("Can only extend pending proposal")
        
        if days <= 0:
            raise ValueError("Number of days must be positive")
        
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc)
        
        self.expires_at += timedelta(days=days)
    
    def __repr__(self):
        return f"<Proposal(id={self.id}, property_id={self.idProperty}, user_id={self.idUser}, value={self.proposalValue}, status='{self.status.value}')>"
    
    def __str__(self):
        status = self.get_status_display()
        return f"Proposal {status} - $ {self.proposalValue}"