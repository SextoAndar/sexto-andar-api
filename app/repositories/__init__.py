# app/repositories/__init__.py
from .property_repository import PropertyRepository
from .favorite_repository import FavoriteRepository
from .property_image_repository import PropertyImageRepository
from .proposal_repository import ProposalRepository
from .visit_repository import VisitRepository

__all__ = [
    "PropertyRepository",
    "FavoriteRepository",
    "PropertyImageRepository",
    "ProposalRepository",
    "VisitRepository",
]
