"""
Service for handling user attribution logic across the application.

This service provides common functionality for tracking who created records
and who performed approval/rejection actions.
"""
from typing import Dict, Any, Optional
from core.models.models import User
import logging

logger = logging.getLogger(__name__)


class AttributionService:
    """Service for handling user attribution logic"""
    
    @staticmethod
    def get_user_from_context(current_user: User) -> int:
        """
        Extract user ID from authenticated context.
        
        Args:
            current_user: The authenticated user from the session
            
        Returns:
            The user's ID
            
        Raises:
            ValueError: If current_user is None or has no ID
        """
        if current_user is None:
            raise ValueError("User context is required for attribution")
        
        if not hasattr(current_user, 'id') or current_user.id is None:
            raise ValueError("User must have a valid ID")
        
        return current_user.id
    
    @staticmethod
    def format_user_info(user: User) -> Dict[str, Any]:
        """
        Format user information for API responses.
        
        Args:
            user: The user object to format
            
        Returns:
            Dictionary containing user_id, username, and email
            
        Raises:
            ValueError: If user is None
        """
        if user is None:
            raise ValueError("User cannot be None")
        
        # Build username from available fields
        username = None
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            if user.first_name and user.last_name:
                username = f"{user.first_name} {user.last_name}".strip()
            elif user.first_name:
                username = user.first_name.strip()
            elif user.last_name:
                username = user.last_name.strip()
        
        # Fallback to email if no name available
        if not username and hasattr(user, 'email') and user.email:
            username = user.email
        
        return {
            "user_id": user.id if hasattr(user, 'id') else None,
            "username": username,
            "email": user.email if hasattr(user, 'email') else None
        }
    
    @staticmethod
    def get_display_name(user: Optional[User]) -> str:
        """
        Get display name for user, handling None gracefully.
        
        This method is designed to handle legacy records where the user
        may have been deleted or attribution was never set.
        
        Args:
            user: The user object (may be None)
            
        Returns:
            Display name string, or "Unknown" if user is None or has no identifiable info
        """
        if user is None:
            return "Unknown"
        
        # Try to build a name from first_name and last_name
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            # Check if first_name is not None and not just whitespace
            first_name_valid = user.first_name and user.first_name.strip()
            last_name_valid = user.last_name and user.last_name.strip()
            
            if first_name_valid and last_name_valid:
                return f"{user.first_name.strip()} {user.last_name.strip()}"
            elif first_name_valid:
                return user.first_name.strip()
            elif last_name_valid:
                return user.last_name.strip()
        
        # Fallback to email
        if hasattr(user, 'email') and user.email:
            return user.email
        
        # If we still have nothing, return Unknown
        return "Unknown"
