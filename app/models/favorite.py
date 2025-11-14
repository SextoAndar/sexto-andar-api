# app/models/favorite.py
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import BaseModel
from datetime import datetime, timezone
import uuid


class Favorite(BaseModel):
    """
    Favorite class for user's favorite properties (wishlist)
    """
    __tablename__ = "favorites"
    
    # Composite primary key (user_id + property_id)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Foreign Key to User (in auth service)
    idUser = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    # Foreign Key to Property
    idProperty = Column(
        UUID(as_uuid=True),
        ForeignKey('properties.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    property = relationship(
        "Property",
        backref="favorites"
    )
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (
        UniqueConstraint('idUser', 'idProperty', name='uq_user_property_favorite'),
    )
    
    def __repr__(self):
        return f"<Favorite(user={self.idUser}, property={self.idProperty})>"
