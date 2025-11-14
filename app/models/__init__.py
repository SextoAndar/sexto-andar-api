"""
Centralized model imports

NOTE: Account model is managed by the sexto-andar-auth service in the same database.
This repository only references user_id, not the Account model.
"""

from app.database.connection import BaseModel
from .property import Property
from .address import Address
from .visit import Visit
from .proposal import Proposal
from .favorite import Favorite
from .property_image import PropertyImage

# List of all models (useful for migrations and other scripts)
__all__ = ["BaseModel", "Property", "Address", "Visit", "Proposal", "Favorite", "PropertyImage"]
