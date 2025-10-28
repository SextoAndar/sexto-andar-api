"""
Centralized model imports

NOTA: Account model é gerenciado pelo serviço sexto-andar-auth no mesmo banco.
Este repositório apenas referencia user_id, não o modelo Account.
"""

from app.database.connection import BaseModel
from .property import Property
from .address import Address
from .visit import Visit
from .proposal import Proposal

# List of all models (useful for migrations and other scripts)
__all__ = ["BaseModel", "Property", "Address", "Visit", "Proposal"]
