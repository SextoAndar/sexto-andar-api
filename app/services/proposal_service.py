# app/services/proposal_service.py
from sqlalchemy.orm import Session
from app.models.proposal import Proposal
from app.repositories.proposal_repository import ProposalRepository
from app.dtos.proposal_dto import CreateProposalRequest
from fastapi import HTTPException, status
from typing import Optional, Tuple, List
from uuid import UUID


class ProposalService:
    """Service for Proposal business logic"""
    
    def __init__(self, db: Session):
        self.repository = ProposalRepository(db)
    
    def create_proposal(
        self,
        proposal_data: CreateProposalRequest,
        user_id: UUID
    ) -> Proposal:
        """Create a new proposal"""
        # Check if property exists
        owner_id = self.repository.get_property_owner_id(proposal_data.idProperty)
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check if user is trying to make proposal on their own property
        if owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot make a proposal on your own property"
            )
        
        # Check for duplicate pending proposals
        if self.repository.check_duplicate_proposal(user_id, proposal_data.idProperty):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending proposal for this property"
            )
        
        # Create proposal
        proposal = Proposal(
            idProperty=proposal_data.idProperty,
            idUser=user_id,
            proposalValue=proposal_data.proposalValue,
            message=proposal_data.message
        )
        
        return self.repository.create(proposal)
    
    def get_proposal_by_id(self, proposal_id: UUID) -> Proposal:
        """Get proposal by ID"""
        proposal = self.repository.get_by_id(proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        return proposal
    
    def get_user_proposals(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals made by a user"""
        return self.repository.get_by_user(
            user_id=user_id,
            page=page,
            size=size,
            status=status
        )
    
    def get_property_proposals(
        self,
        property_id: UUID,
        owner_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals for a property (only by owner)"""
        # Check if property exists and user is the owner
        actual_owner_id = self.repository.get_property_owner_id(property_id)
        if actual_owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        if actual_owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view proposals for your own properties"
            )
        
        return self.repository.get_by_property(
            property_id=property_id,
            page=page,
            size=size,
            status=status
        )
    
    def get_received_proposals(
        self,
        owner_id: UUID,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None
    ) -> Tuple[List[Proposal], int]:
        """Get all proposals received for properties owned by user"""
        return self.repository.get_by_property_owner(
            owner_id=owner_id,
            page=page,
            size=size,
            status=status
        )
    
    def accept_proposal(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        response_message: Optional[str] = None
    ) -> Proposal:
        """Accept a proposal (only by property owner)"""
        proposal = self.get_proposal_by_id(proposal_id)
        
        # Check if user is the property owner
        actual_owner_id = self.repository.get_property_owner_id(proposal.idProperty)
        if actual_owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the property owner can accept proposals"
            )
        
        try:
            proposal.accept(response_message)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        return self.repository.update(proposal)
    
    def reject_proposal(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        response_message: Optional[str] = None
    ) -> Proposal:
        """Reject a proposal (only by property owner)"""
        proposal = self.get_proposal_by_id(proposal_id)
        
        # Check if user is the property owner
        actual_owner_id = self.repository.get_property_owner_id(proposal.idProperty)
        if actual_owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the property owner can reject proposals"
            )
        
        try:
            proposal.reject(response_message)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        return self.repository.update(proposal)
    
    def withdraw_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> Proposal:
        """Withdraw a proposal (only by user who made it)"""
        proposal = self.get_proposal_by_id(proposal_id)
        
        # Only the user who made the proposal can withdraw it
        if proposal.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only withdraw your own proposals"
            )
        
        try:
            proposal.withdraw()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        return self.repository.update(proposal)
    
    def delete_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete a proposal (only by user who made it)"""
        proposal = self.get_proposal_by_id(proposal_id)
        
        # Only the user who made the proposal can delete it
        if proposal.idUser != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own proposals"
            )
        
        self.repository.delete(proposal)
