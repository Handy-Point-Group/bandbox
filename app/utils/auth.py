"""
Authentication Module
Handles Google OIDC authentication + Email/Password authentication + Supabase user validation
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from .supabase_client import get_supabase_client
from .password_auth import get_password_auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthManager:
    """Manages user authentication and session state"""
    
    def __init__(self):
        """Initialize authentication manager"""
        self.supabase = get_supabase_client()
        self.password_auth = get_password_auth()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for authentication"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'organization_data' not in st.session_state:
            st.session_state.organization_data = None
        if 'permissions' not in st.session_state:
            st.session_state.permissions = []
        if 'auth_method' not in st.session_state:
            st.session_state.auth_method = None  # 'google' or 'password'
        if 'selected_organization_id' not in st.session_state:
            st.session_state.selected_organization_id = None
        if 'user_organizations' not in st.session_state:
            st.session_state.user_organizations = []
    
    def check_authentication(self) -> bool:
        """
        Check if user is authenticated via session state (password) or Google OIDC
        
        Returns:
            True if authenticated and validated, False otherwise
        """
        # Ensure session state is initialized
        self._initialize_session_state()
        
        # First check if already authenticated in session (password-based auth)
        if st.session_state.get('authenticated', False) and st.session_state.get('user_data'):
            return True
        
        # Try to check Google OIDC authentication
        try:
            # Check if user is logged in via Google OIDC
            if hasattr(st, 'user') and hasattr(st.user, 'is_logged_in') and st.user.is_logged_in:
                # Validate user against Supabase database
                user_email = st.user.email
                google_id = st.user.sub  # Google's unique user ID
                return self._validate_user(user_email, google_id)
        except (AttributeError, Exception) as e:
            # st.user not configured or not available, that's ok
            logger.debug(f"Google OIDC not available: {e}")
        
        # Not authenticated via any method
        return False
    
    def _validate_user(self, email: str, google_id: str) -> bool:
        """
        Validate user exists in Supabase and is active
        
        Args:
            email: User's email from Google
            google_id: User's Google ID
            
        Returns:
            True if user is valid and active, False otherwise
        """
        try:
            # Try to find user by email
            user = self.supabase.get_user_by_email(email)
            
            # If user doesn't exist, check if we should auto-create (optional)
            if not user:
                logger.warning(f"User not found in database: {email}")
                st.session_state.authenticated = False
                st.session_state.user_data = None
                return False
            
            # Check if user is active
            if not user.get('is_active', False):
                logger.warning(f"User account is inactive: {email}")
                st.session_state.authenticated = False
                st.session_state.user_data = None
                return False
            
            # Update Google ID if not set
            if not user.get('google_id') and google_id:
                self.supabase.client.from_("users").update(
                    {"google_id": google_id}
                ).eq("id", user['id']).execute()
                user['google_id'] = google_id
            
            # Update last login
            self.supabase.update_user_last_login(user['id'])
            
            # Load organization data
            org_data = None
            if user.get('primary_organization_id'):
                org_data = self.supabase.get_organization(user['primary_organization_id'])
                
                # Check if organization is active (only if user is assigned to one)
                # Users without organizations can still login
                if org_data and not org_data.get('is_active', False):
                    logger.warning(f"Organization is inactive for user: {email}")
                    st.session_state.authenticated = False
                    return False
            
            # Load user permissions
            permissions = self.supabase.get_user_permissions(user['id'])
            
            # Set session state
            st.session_state.authenticated = True
            st.session_state.user_data = user
            st.session_state.organization_data = org_data
            st.session_state.permissions = permissions
            st.session_state.auth_method = 'google'
            
            logger.info(f"User authenticated via Google: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating user: {e}")
            st.session_state.authenticated = False
            st.session_state.user_data = None
            return False
    
    def require_auth(self, provider: str = None):
        """
        Require authentication - redirect to login if not authenticated
        
        Args:
            provider: OIDC provider name (e.g., 'google'). If None, uses default config
        """
        if not self.check_authentication():
            st.warning("⚠️ You must be logged in and have a valid account to access this application.")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if provider:
                    if st.button("🔐 Log in with Google", use_container_width=True):
                        st.login(provider)
                else:
                    if st.button("🔐 Log in with Google", use_container_width=True):
                        st.login()
            
            st.stop()
    
    def login_with_password(self, email: str, password: str) -> bool:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            True if authentication successful, False otherwise
        """
        user = self.password_auth.authenticate_with_password(email, password)
        
        if not user:
            return False
        
        # Load organization data (optional - users can login without an organization)
        org_data = None
        if user.get('primary_organization_id'):
            org_data = self.supabase.get_organization(user['primary_organization_id'])
        
        # Load permissions
        permissions = self.supabase.get_user_permissions(user['id'])
        
        # Set session state
        st.session_state.authenticated = True
        st.session_state.user_data = user
        st.session_state.organization_data = org_data
        st.session_state.permissions = permissions
        st.session_state.auth_method = 'password'
        
        return True
    
    def logout(self):
        """Logout the current user"""
        auth_method = st.session_state.get('auth_method', None)
        
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.organization_data = None
        st.session_state.permissions = []
        st.session_state.auth_method = None
        
        # Only call st.logout() if using Google auth
        if auth_method == 'google':
            st.logout()
        else:
            st.rerun()
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user data
        
        Returns:
            User data dictionary or None
        """
        self._initialize_session_state()
        return st.session_state.get('user_data') if st.session_state.get('authenticated', False) else None
    
    def get_current_organization(self) -> Optional[Dict[str, Any]]:
        """
        Get current user's selected organization data
        
        Returns:
            Organization data dictionary or None
        """
        self._initialize_session_state()
        if not st.session_state.get('authenticated', False):
            return None
        
        # If user has selected a different org, load that one
        if st.session_state.get('selected_organization_id'):
            return self.supabase.get_organization(st.session_state.selected_organization_id)
        
        # Otherwise return the primary org
        return st.session_state.get('organization_data')
    
    def get_user_organizations(self) -> List[Dict[str, Any]]:
        """
        Get all organizations the user belongs to
        
        Returns:
            List of organization dictionaries
        """
        self._initialize_session_state()
        if not st.session_state.get('authenticated', False) or not st.session_state.get('user_data'):
            return []
        
        user = st.session_state.get('user_data')
        orgs = []
        
        # Add primary organization
        if user.get('primary_organization_id'):
            primary_org = self.supabase.get_organization(user['primary_organization_id'])
            if primary_org:
                orgs.append(primary_org)
        
        # Add additional organizations if multi_org is enabled
        if user.get('multi_org') and user.get('organization_ids'):
            for org_id in user['organization_ids']:
                # Skip if it's the primary (already added)
                if org_id == user.get('primary_organization_id'):
                    continue
                org = self.supabase.get_organization(org_id)
                if org:
                    orgs.append(org)
        
        return orgs
    
    def switch_organization(self, organization_id: str):
        """
        Switch to a different organization
        
        Args:
            organization_id: UUID of organization to switch to
        """
        self._initialize_session_state()
        user = st.session_state.get('user_data')
        if not user:
            return
        
        # Verify user has access to this organization
        user_org_ids = [user.get('primary_organization_id')]
        if user.get('multi_org') and user.get('organization_ids'):
            user_org_ids.extend(user['organization_ids'])
        
        if organization_id in user_org_ids:
            st.session_state.selected_organization_id = organization_id
            st.session_state.organization_data = self.supabase.get_organization(organization_id)
            st.rerun()
    
    def has_role(self, required_role: str) -> bool:
        """
        Check if current user has a specific role
        
        Args:
            required_role: Role to check (super_admin, organization_admin, team_admin, coach, player)
            
        Returns:
            True if user has role, False otherwise
        """
        self._initialize_session_state()
        if not st.session_state.get('authenticated', False) or not st.session_state.get('user_data'):
            return False
        
        user_role = st.session_state.get('user_data', {}).get('role', 'player')
        
        # Role hierarchy: superadmin > admin-org > admin-team > admin > coach > player > user
        role_hierarchy = {
            'superadmin': 7,
            'super_admin': 7,  # Alias for compatibility
            'admin-org': 6,
            'organization_admin': 6,  # Alias for compatibility
            'admin-team': 5,
            'team_admin': 5,  # Alias for compatibility
            'admin': 4,
            'coach': 3,
            'player': 2,
            'user': 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if current user has a specific permission
        
        Args:
            permission: Permission name to check
            
        Returns:
            True if user has permission, False otherwise
        """
        self._initialize_session_state()
        if not st.session_state.get('authenticated', False):
            return False
        
        # Admins have all permissions
        if self.has_role('admin'):
            return True
        
        return permission in st.session_state.get('permissions', [])
    
    def require_role(self, required_role: str):
        """
        Require a specific role - show error if user doesn't have it
        
        Args:
            required_role: Role to require (super_admin, organization_admin, team_admin, coach, player)
        """
        if not self.has_role(required_role):
            role_names = {
                'superadmin': 'Superadmin',
                'super_admin': 'Super Admin',
                'admin-org': 'Organization Admin',
                'organization_admin': 'Organization Admin',
                'admin-team': 'Team Admin',
                'team_admin': 'Team Admin',
                'admin': 'Admin',
                'coach': 'Coach',
                'player': 'Player',
                'user': 'User'
            }
            display_name = role_names.get(required_role, required_role.replace('_', ' ').replace('-', ' ').title())
            st.error(f"🚫 Access Denied: This page requires '{display_name}' role or higher.")
            st.stop()
    
    def require_permission(self, permission: str):
        """
        Require a specific permission - show error if user doesn't have it
        
        Args:
            permission: Permission to require
        """
        if not self.has_permission(permission):
            st.error(f"🚫 Access Denied: You don't have the '{permission}' permission.")
            st.stop()
    
    def display_user_info(self):
        """Display current user information in sidebar with organization switcher"""
        self._initialize_session_state()
        if st.session_state.get('authenticated', False) and st.session_state.get('user_data'):
            user = st.session_state.get('user_data')
            current_org = self.get_current_organization()
            
            with st.sidebar:
                st.divider()
                st.write("**Logged in as:**")
                st.write(f"👤 {user.get('full_name', 'Unknown')}")
                st.write(f"✉️ {user.get('email', '')}")
                
                # Organization switcher for multi-org users
                user_orgs = self.get_user_organizations()
                
                if len(user_orgs) > 1:
                    # User belongs to multiple organizations - show switcher
                    org_names = {org['name']: org['id'] for org in user_orgs}
                    current_org_name = current_org['name'] if current_org else list(org_names.keys())[0]
                    
                    selected_org_name = st.selectbox(
                        "🏢 Organization:",
                        options=list(org_names.keys()),
                        index=list(org_names.keys()).index(current_org_name) if current_org_name in org_names else 0,
                        key="org_switcher"
                    )
                    
                    # If user changed selection, switch organization
                    if selected_org_name != current_org_name:
                        self.switch_organization(org_names[selected_org_name])
                elif len(user_orgs) == 1:
                    # User belongs to one organization
                    st.write(f"🏢 {user_orgs[0].get('name', 'No Organization')}")
                else:
                    # User has no organizations
                    st.write("🏢 No Organization")
                
                st.write(f"👔 Role: {user.get('role', 'user').title()}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()


# Singleton instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """
    Get or create the AuthManager singleton
    
    Returns:
        AuthManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# Convenience functions
def require_auth(provider: str = None):
    """Require authentication"""
    auth = get_auth_manager()
    auth.require_auth(provider)


def require_role(role: str):
    """Require specific role"""
    auth = get_auth_manager()
    auth.require_role(role)


def require_permission(permission: str):
    """Require specific permission"""
    auth = get_auth_manager()
    auth.require_permission(permission)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user data"""
    auth = get_auth_manager()
    return auth.get_current_user()


def get_current_organization() -> Optional[Dict[str, Any]]:
    """Get current organization data"""
    auth = get_auth_manager()
    return auth.get_current_organization()


def has_role(role: str) -> bool:
    """Check if user has role"""
    auth = get_auth_manager()
    return auth.has_role(role)


def has_permission(permission: str) -> bool:
    """Check if user has permission"""
    auth = get_auth_manager()
    return auth.has_permission(permission)

