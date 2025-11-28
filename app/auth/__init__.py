# app/auth/__init__.py
from .dependencies import (
    AuthUser as AuthUser,
    get_current_user as get_current_user,
    get_current_property_owner as get_current_property_owner,
    get_current_admin as get_current_admin,
)
from .auth_client import AuthClient as AuthClient, auth_client as auth_client
