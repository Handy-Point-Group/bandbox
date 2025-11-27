"""
Authentication Module
Handles Google OIDC authentication + Email/Password authentication + Supabase user validation
"""

import streamlit as st
from typing import Optional, Dict, Any
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
    
    def check_authentication(self) -> bool:
        """
        Check if user is authenticated via Google OIDC and validated in Supabase
        
        Returns:
            True if authenticated and validated, False otherwise
        """
        # Check if user is logged in via Google OIDC
        if not st.user.is_logged_in:
            return False
        
        # If already authenticated in session, return True
        if st.session_state.authenticated and st.session_state.user_data:
            return True
        
        # Validate user against Supabase database
        user_email = st.user.email
        google_id = st.user.sub  # Google's unique user ID
        
        return self._validate_user(user_email, google_id)
    
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
                self.supabase.client.table("users").update(
                    {"google_id": google_id}
                ).eq("id", user['id']).execute()
                user['google_id'] = google_id
            
            # Update last login
            self.supabase.update_user_last_login(user['id'])
            
            # Load organization data
            org_data = None
            if user.get('organization_id'):
                org_data = self.supabase.get_organization(user['organization_id'])
                
                # Check if organization is active
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
        
        # Load organization data
        org_data = None
        if user.get('organization_id'):
            org_data = self.supabase.get_organization(user['organization_id'])
        
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
        return st.session_state.user_data if st.session_state.authenticated else None
    
    def get_current_organization(self) -> Optional[Dict[str, Any]]:
        """
        Get current user's organization data
        
        Returns:
            Organization data dictionary or None
        """
        return st.session_state.organization_data if st.session_state.authenticated else None
    
    def has_role(self, required_role: str) -> bool:
        """
        Check if current user has a specific role
        
        Args:
            required_role: Role to check (super_admin, organization_admin, team_admin, coach, player)
            
        Returns:
            True if user has role, False otherwise
        """
        if not st.session_state.authenticated or not st.session_state.user_data:
            return False
        
        user_role = st.session_state.user_data.get('role', 'player')
        
        # Role hierarchy: super_admin > organization_admin > team_admin > coach > player
        role_hierarchy = {
            'super_admin': 5,
            'organization_admin': 4,
            'team_admin': 3,
            'coach': 2,
            'player': 1
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
        if not st.session_state.authenticated:
            return False
        
        # Admins have all permissions
        if self.has_role('admin'):
            return True
        
        return permission in st.session_state.permissions
    
    def require_role(self, required_role: str):
        """
        Require a specific role - show error if user doesn't have it
        
        Args:
            required_role: Role to require (super_admin, organization_admin, team_admin, coach, player)
        """
        if not self.has_role(required_role):
            role_names = {
                'super_admin': 'Super Admin',
                'organization_admin': 'Organization Admin',
                'team_admin': 'Team Admin',
                'coach': 'Coach',
                'player': 'Player'
            }
            display_name = role_names.get(required_role, required_role)
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
        """Display current user information in sidebar"""
        if st.session_state.authenticated and st.session_state.user_data:
            user = st.session_state.user_data
            org = st.session_state.organization_data
            
            with st.sidebar:
                st.divider()
                st.write("**Logged in as:**")
                st.write(f"👤 {user.get('full_name', 'Unknown')}")
                st.write(f"✉️ {user.get('email', '')}")
                st.write(f"🏢 {org.get('name', 'No Organization') if org else 'No Organization'}")
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

