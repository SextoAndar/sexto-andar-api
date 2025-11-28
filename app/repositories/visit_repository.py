# app/repositories/visit_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from app.models.visit import Visit
from app.models.property import Property
from typing import Optional, Tuple, List
from datetime import datetime
from uuid import UUID


class VisitRepository:
    """Repository for Visit database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, visit: Visit) -> Visit:
        """Create a new visit"""
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)
        return visit
    
    def get_by_id(self, visit_id: UUID) -> Optional[Visit]:
        """Get visit by ID"""
        return self.db.query(Visit).filter(Visit.id == visit_id).first()
    
    def get_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        include_cancelled: bool = False,
        include_completed: bool = True
    ) -> Tuple[List[Visit], int]:
        """Get all visits for a user with pagination"""
        query = self.db.query(Visit).filter(Visit.idUser == user_id)
        
        if not include_cancelled:
            query = query.filter(Visit.cancelled == False)
        
        if not include_completed:
            query = query.filter(Visit.isVisitCompleted == False)
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        visits = query.order_by(desc(Visit.visitDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return visits, total
    
    def get_by_property(
        self,
        property_id: UUID,
        page: int = 1,
        size: int = 10,
        include_cancelled: bool = False,
        include_completed: bool = True
    ) -> Tuple[List[Visit], int]:
        """Get all visits for a property with pagination"""
        query = self.db.query(Visit).filter(Visit.idProperty == property_id)
        
        if not include_cancelled:
            query = query.filter(Visit.cancelled == False)
        
        if not include_completed:
            query = query.filter(Visit.isVisitCompleted == False)
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        visits = query.order_by(desc(Visit.visitDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return visits, total
    
    def get_upcoming_by_user(self, user_id: UUID) -> List[Visit]:
        """Get upcoming visits for a user"""
        now = datetime.utcnow()
        return self.db.query(Visit)\
            .filter(
                and_(
                    Visit.idUser == user_id,
                    Visit.visitDate > now,
                    Visit.cancelled == False,
                    Visit.isVisitCompleted == False
                )
            )\
            .order_by(Visit.visitDate)\
            .all()
    
    def get_upcoming_by_property(self, property_id: UUID) -> List[Visit]:
        """Get upcoming visits for a property"""
        now = datetime.utcnow()
        return self.db.query(Visit)\
            .filter(
                and_(
                    Visit.idProperty == property_id,
                    Visit.visitDate > now,
                    Visit.cancelled == False,
                    Visit.isVisitCompleted == False
                )
            )\
            .order_by(Visit.visitDate)\
            .all()
    
    def check_visit_conflict(
        self,
        property_id: UUID,
        visit_date: datetime,
        exclude_visit_id: Optional[UUID] = None
    ) -> bool:
        """Check if there's a visit conflict at the same time"""
        query = self.db.query(Visit).filter(
            and_(
                Visit.idProperty == property_id,
                Visit.visitDate == visit_date,
                Visit.cancelled == False
            )
        )
        
        if exclude_visit_id:
            query = query.filter(Visit.id != exclude_visit_id)
        
        return query.first() is not None
    
    def update(self, visit: Visit) -> Visit:
        """Update visit"""
        self.db.commit()
        self.db.refresh(visit)
        return visit
    
    def delete(self, visit: Visit) -> None:
        """Delete a visit by object"""
        self.db.delete(visit)
        self.db.commit()

    def delete_by_property_id(self, property_id: str) -> int:
        """Delete all visits for a given property ID and return the count."""
        num_deleted = self.db.query(Visit).filter(Visit.idProperty == property_id).delete(synchronize_session=False)
        self.db.commit()
        return num_deleted
    
    def get_property_owner_id(self, property_id: UUID) -> Optional[UUID]:
        """Get the owner ID of a property"""
        property_obj = self.db.query(Property).filter(Property.id == property_id).first()
        return property_obj.idPropertyOwner if property_obj else None
    
    def delete_all_visits_by_user_id(self, user_id: UUID) -> int:
        """Delete all visit records permanently for a given user ID. Returns count of deleted visits."""
        count = (
            self.db.query(Visit)
            .filter(Visit.idUser == user_id)
            .delete(synchronize_session='fetch')
        )
        self.db.commit()
        return count

    def delete_all_visits_for_owner_properties(self, owner_id: UUID) -> int:
        """Delete all visit records permanently for properties owned by a given owner ID. Returns count of deleted visits."""
        # First, get the IDs of properties owned by this owner
        property_ids_tuple = self.db.query(Property.id).filter(Property.idPropertyOwner == owner_id).all()
        property_ids = [pid[0] for pid in property_ids_tuple] # Extract UUIDs from tuples

        if not property_ids:
            return 0
        
        count = (
            self.db.query(Visit)
            .filter(Visit.idProperty.in_(property_ids))
            .delete(synchronize_session='fetch')
        )
        self.db.commit()
        return count

    def get_by_owner(
        self,
        owner_id: UUID,
        page: int = 1,
        size: int = 10,
        include_cancelled: bool = False,
        include_completed: bool = True
    ) -> Tuple[List[Visit], int]:
        """Get all visits for properties owned by a specific owner with pagination"""
        # Join with Property to filter by owner and eager load property and address
        query = self.db.query(Visit)\
            .join(Property, Visit.idProperty == Property.id)\
            .filter(Property.idPropertyOwner == owner_id)\
            .options(joinedload(Visit.property).joinedload(Property.address))
        
        if not include_cancelled:
            query = query.filter(Visit.cancelled == False)
        
        if not include_completed:
            query = query.filter(Visit.isVisitCompleted == False)
        
        # Count total
        total = query.count()
        
        # Apply pagination and ordering
        visits = query.order_by(desc(Visit.visitDate))\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        return visits, total
