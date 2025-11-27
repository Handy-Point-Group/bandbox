"""
Password Authentication Utilities
Handles password hashing, verification, and email/password authentication
"""

import bcrypt
import streamlit as st
from typing import Optional, Dict, Any
from .supabase_client import get_supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PasswordAuth:
    """Handles password-based authentication"""
    
    def __init__(self):
        """Initialize password authentication"""
        self.supabase = get_supabase_client()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def authenticate_with_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        try:
            # Get user by email
            user = self.supabase.get_user_by_email(email)
            
            if not user:
                logger.warning(f"User not found: {email}")
                return None
            
            # Check if user is active
            if not user.get('is_active', False):
                logger.warning(f"User account inactive: {email}")
                return None
            
            # Get password hash
            password_hash = user.get('password_hash')
            if not password_hash:
                logger.warning(f"No password set for user: {email}")
                return None
            
            # Verify password
            if not self.verify_password(password, password_hash):
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            # Check organization
            if user.get('organization_id'):
                org = self.supabase.get_organization(user['organization_id'])
                if org and not org.get('is_active', False):
                    logger.warning(f"Organization inactive for user: {email}")
                    return None
            
            # Update last login
            self.supabase.update_user_last_login(user['id'])
            
            logger.info(f"Password authentication successful: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error during password authentication: {e}")
            return None
    
    def create_user_with_password(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_id: str,
        role: str = 'player'
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user with email/password authentication
        
        Args:
            email: User's email
            password: Plain text password
            full_name: User's full name
            organization_id: Organization UUID
            role: User's role
            
        Returns:
            Created user data or None if failed
        """
        try:
            # Check if user already exists
            existing_user = self.supabase.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User already exists: {email}")
                return None
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user data
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "organization_id": organization_id,
                "role": role,
                "is_active": True
            }
            
            # Insert user
            response = self.supabase.client.from_("users").insert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"User created with password: {email}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user with password: {e}")
            return None
    
    def set_password(self, user_id: str, new_password: str) -> bool:
        """
        Set or update password for a user
        
        Args:
            user_id: User's UUID
            new_password: New plain text password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            password_hash = self.hash_password(new_password)
            
            response = self.supabase.client.from_("users").update(
                {"password_hash": password_hash}
            ).eq("id", user_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error setting password: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements
        
        Args:
            password: Plain text password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        return True, ""


# Singleton instance
_password_auth = None


def get_password_auth() -> PasswordAuth:
    """
    Get or create the PasswordAuth singleton
    
    Returns:
        PasswordAuth instance
    """
    global _password_auth
    if _password_auth is None:
        _password_auth = PasswordAuth()
    return _password_auth

