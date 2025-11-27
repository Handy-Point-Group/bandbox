"""
Supabase Client Utility
Provides a centralized Supabase client for authentication and database operations
"""

import streamlit as st
from st_supabase_connection import SupabaseConnection
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper class for Supabase operations"""
    
    def __init__(self):
        """Initialize Supabase connection"""
        try:
            self.conn = st.connection("supabase", type=SupabaseConnection)
            self.client = self.conn.client
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    # ==================== User Operations ====================
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information by email
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            response = self.client.from_("users").select("*").eq("email", email).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information by Google ID
        
        Args:
            google_id: User's Google ID
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            response = self.client.from_("users").select("*").eq("google_id", google_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching user by Google ID: {e}")
            return None
    
    def create_user(
        self, 
        email: str, 
        full_name: str, 
        organization_id: str,
        google_id: Optional[str] = None,
        role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user in the database
        
        Args:
            email: User's email address
            full_name: User's full name
            organization_id: UUID of the organization
            google_id: User's Google ID (optional)
            role: User's role (default: 'user')
            
        Returns:
            Created user data or None if failed
        """
        try:
            user_data = {
                "email": email,
                "full_name": full_name,
                "primary_organization_id": organization_id,
                "google_id": google_id,
                "role": role,
                "is_active": True
            }
            
            response = self.client.from_("users").insert(user_data).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Created new user: {email}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def update_user_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.from_("users").update(
                {"last_login": datetime.utcnow().isoformat()}
            ).eq("id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False
    
    def update_user_role(self, user_id: str, role: str) -> bool:
        """
        Update user's role
        
        Args:
            user_id: User's UUID
            role: New role (admin, coach, player, user)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.from_("users").update(
                {"role": role}
            ).eq("id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.from_("users").update(
                {"is_active": False}
            ).eq("id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.from_("users").update(
                {"is_active": True}
            ).eq("id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            return False
    
    # ==================== Organization Operations ====================
    
    def get_organization(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve organization information
        
        Args:
            organization_id: Organization's UUID
            
        Returns:
            Organization data dictionary or None if not found
        """
        try:
            response = self.client.from_("organizations").select("*").eq("id", organization_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching organization: {e}")
            return None
    
    def get_all_organizations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all organizations
        
        Returns:
            List of organization data dictionaries
        """
        try:
            response = self.client.from_("organizations").select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching organizations: {e}")
            return []
    
    def create_organization(self, name: str, settings: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new organization
        
        Args:
            name: Organization name
            settings: Optional settings dictionary
            
        Returns:
            Created organization data or None if failed
        """
        try:
            org_data = {
                "name": name,
                "settings": settings or {},
                "is_active": True
            }
            
            response = self.client.from_("organizations").insert(org_data).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Created new organization: {name}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return None
    
    # ==================== User List Operations ====================
    
    def get_users_by_organization(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get all users in an organization
        
        Args:
            organization_id: Organization's UUID
            
        Returns:
            List of user data dictionaries
        """
        try:
            response = self.client.from_("users").select("*").eq("primary_organization_id", organization_id).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching users by organization: {e}")
            return []
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users (for admin purposes)
        
        Returns:
            List of user data dictionaries
        """
        try:
            response = self.client.from_("users").select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
    
    # ==================== Permission Operations ====================
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user
        
        Args:
            user_id: User's UUID
            
        Returns:
            List of permission names
        """
        try:
            response = self.client.table("role_permissions").select(
                "permission_id, permissions(name)"
            ).eq("user_id", user_id).execute()
            
            if response.data:
                return [item['permissions']['name'] for item in response.data if item.get('permissions')]
            return []
        except Exception as e:
            logger.error(f"Error fetching user permissions: {e}")
            return []
    
    def grant_permission(self, user_id: str, permission_name: str, granted_by: Optional[str] = None) -> bool:
        """
        Grant a permission to a user
        
        Args:
            user_id: User's UUID
            permission_name: Name of the permission
            granted_by: UUID of user granting permission (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First get permission ID
            perm_response = self.client.table("permissions").select("id").eq("name", permission_name).execute()
            if not perm_response.data:
                logger.error(f"Permission not found: {permission_name}")
                return False
            
            permission_id = perm_response.data[0]['id']
            
            # Grant permission
            data = {
                "user_id": user_id,
                "permission_id": permission_id,
                "granted_by": granted_by
            }
            
            response = self.client.table("role_permissions").insert(data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            return False


# Singleton instance
_supabase_client = None


def get_supabase_client() -> SupabaseClient:
    """
    Get or create the Supabase client singleton
    
    Returns:
        SupabaseClient instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

