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

from .org_team_switcher import (
    render_org_team_switcher,
    get_active_organization,
    get_active_team,
    get_active_organization_id,
    get_active_team_id,
    get_user_organizations,
    get_user_teams,
    init_org_team_session
)

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
    'PasswordAuth',
    # Org/Team Switcher
    'render_org_team_switcher',
    'get_active_organization',
    'get_active_team',
    'get_active_organization_id',
    'get_active_team_id',
    'get_user_organizations',
    'get_user_teams',
    'init_org_team_session'
]

