"""
Utils package for BandBox application
"""

from .auth import (
    get_auth_manager,
    require_auth,
    require_role,
    require_permission,
    get_current_user,
    get_current_organization,
    has_role,
    has_permission
)

from .supabase_client import get_supabase_client, SupabaseClient
from .password_auth import get_password_auth, PasswordAuth

__all__ = [
    'get_auth_manager',
    'require_auth',
    'require_role',
    'require_permission',
    'get_current_user',
    'get_current_organization',
    'has_role',
    'has_permission',
    'get_supabase_client',
    'SupabaseClient',
    'get_password_auth',
    'PasswordAuth'
]

