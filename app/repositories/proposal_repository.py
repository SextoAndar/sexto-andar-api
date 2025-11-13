# app/repositories/proposal_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.proposal import Proposal, ProposalStatusEnum
from app.models.property import Property
from typing import Optional, Tuple, List
from uuid import UUID


class ProposalRepository:
    """Repository for Proposal database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, proposal: Proposal) -> Proposal:
        """Create a new proposal"""
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal
    
    def get_by_id(self, proposal_id: UUID) -> Optional[Proposal]:
        """Get proposal by ID"""
        return self.db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    def get_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals made by a user with pagination"""
        query = self.db.query(Proposal).filter(Proposal.idUser == user_id)
        
        if status:
            try:
                status_enum = ProposalStatusEnum(status)
                query = query.filter(Proposal.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        proposals = query.order_by(desc(Proposal.proposalDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return proposals, total
    
    def get_by_property(
        self,
        property_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals for a property with pagination"""
        query = self.db.query(Proposal).filter(Proposal.idProperty == property_id)
        
        if status:
            try:
                status_enum = ProposalStatusEnum(status)
                query = query.filter(Proposal.status == status_enum)
            except ValueError:
                pass
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        proposals = query.order_by(desc(Proposal.proposalDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return proposals, total
    
    def get_by_property_owner(
        self,
        owner_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals for properties owned by a user"""
        query = self.db.query(Proposal)\
            .join(Property, Proposal.idProperty == Property.id)\
            .filter(Property.idPropertyOwner == owner_id)
        
        if status:
            try:
                status_enum = ProposalStatusEnum(status)
                query = query.filter(Proposal.status == status_enum)
            except ValueError:
                pass
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        proposals = query.order_by(desc(Proposal.proposalDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return proposals, total
    
    def get_pending_by_property(self, property_id: UUID) -> List[Proposal]:
        """Get all pending proposals for a property"""
        return self.db.query(Proposal)\
            .filter(
                and_(
                    Proposal.idProperty == property_id,
                    Proposal.status == ProposalStatusEnum.PENDING
                )
            )\
            .order_by(desc(Proposal.proposalDate))\
            .all()
    
    def check_duplicate_proposal(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> bool:
        """Check if user already has a pending proposal for this property"""
        existing = self.db.query(Proposal).filter(
            and_(
                Proposal.idUser == user_id,
                Proposal.idProperty == property_id,
                Proposal.status == ProposalStatusEnum.PENDING
            )
        ).first()
        
        return existing is not None
    
    def update(self, proposal: Proposal) -> Proposal:
        """Update proposal"""
        self.db.commit()
        self.db.refresh(proposal)
        return proposal
    
    def delete(self, proposal: Proposal) -> None:
        """Delete proposal (hard delete)"""
        self.db.delete(proposal)
        self.db.commit()
    
    def get_property_owner_id(self, property_id: UUID) -> Optional[UUID]:
        """Get the owner ID of a property"""
        property_obj = self.db.query(Property).filter(Property.id == property_id).first()
        return property_obj.idPropertyOwner if property_obj else None
