# app/controllers/__init__.py
from .admin_controller import router as admin_router
from .favorite_controller import router as favorite_router
from .image_controller import router as image_router
from .internal_controller import router as internal_router
from .property_controller import router as property_router
from .proposal_controller import router as proposal_router
from .visit_controller import router as visit_router

__all__ = [
    "admin_router",
    "favorite_router",
    "image_router",
    "internal_router",
    "property_router",
    "proposal_router",
    "visit_router",
]
