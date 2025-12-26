"""
User Preference Controls Service

This service provides granular control over gamification preferences for users,
including feature toggles, personal goals, notification frequency, and visual themes.

Implements Requirement 12: Customization and Preferences
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from core.models.gamification import (
    UserGamificationProfile,
    NotificationFrequency
)
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)


class UserPreferenceControls:
    """
    Service for managing granular user preferences for gamification.
    
    Provides:
    - Feature enable/disable controls
    - Personal goal setting
    - Notification frequency controls
    - Achievement category preferences
    - Visual theme selection
    """

    # Available visual themes
    AVAILABLE_THEMES = [
        "light",
        "dark",
        "colorful",
        "minimal",
        "professional"
    ]

    # Available achievement categories for user selection
    AVAILABLE_ACHIEVEMENT_CATEGORIES = [
        "expense_tracking",
        "invoice_management",
        "habit_formation",
        "financial_health",
        "exploration"
    ]

    # Available notification frequencies
    AVAILABLE_NOTIFICATION_FREQUENCIES = [
        "immediate",
        "daily",
        "weekly",
        "disabled"
    ]

    def __init__(self, db: Session):
        self.db = db

    async def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get all user preferences for gamification.
        
        Returns:
            Dictionary containing all user preferences or None if user not found
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                return None

            return {
                "user_id": user_id,
                "module_enabled": profile.module_enabled,
                "features": profile.preferences.get("features", {}),
                "privacy": profile.preferences.get("privacy", {}),
                "notifications": profile.preferences.get("notifications", {}),
                "personal_goals": profile.preferences.get("personal_goals", {}),
                "achievement_categories": profile.preferences.get("achievement_categories", []),
                "visual_theme": profile.preferences.get("visual_theme", "light"),
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting user preferences for user {user_id}: {str(e)}")
            return None

    async def update_feature_preferences(
        self,
        user_id: int,
        features: Dict[str, bool]
    ) -> Optional[Dict[str, Any]]:
        """
        Update feature enable/disable preferences for a user.
        
        Allows users to enable or disable specific game mechanics:
        - points: Experience point system
        - achievements: Achievement unlocking
        - streaks: Streak tracking
        - challenges: Challenge participation
        - social: Social features (leaderboards, sharing)
        - notifications: Gamification notifications
        
        Args:
            user_id: User ID
            features: Dictionary of feature names to boolean values
            
        Returns:
            Updated preferences or None on error
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Validate feature names
            valid_features = {"points", "achievements", "streaks", "challenges", "social", "notifications"}
            invalid_features = set(features.keys()) - valid_features
            if invalid_features:
                logger.warning(f"Invalid features requested: {invalid_features}")
                return None

            # Update features in preferences
            if "features" not in profile.preferences:
                profile.preferences["features"] = {}

            profile.preferences["features"].update(features)
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated feature preferences for user {user_id}: {features}")

            return {
                "user_id": user_id,
                "features": profile.preferences.get("features", {}),
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating feature preferences for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def set_personal_goals(
        self,
        user_id: int,
        goals: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Set personal goals for the user.
        
        Allows users to define custom goals such as:
        - Daily expense tracking target
        - Weekly budget review frequency
        - Monthly invoice follow-up target
        - Habit formation milestones
        
        Args:
            user_id: User ID
            goals: Dictionary of goal names to target values
            
        Returns:
            Updated goals or None on error
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Validate goals structure
            if not isinstance(goals, dict):
                logger.warning(f"Invalid goals format for user {user_id}")
                return None

            # Initialize personal_goals if not present
            if "personal_goals" not in profile.preferences:
                profile.preferences["personal_goals"] = {}

            # Update goals
            profile.preferences["personal_goals"].update(goals)
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated personal goals for user {user_id}: {goals}")

            return {
                "user_id": user_id,
                "personal_goals": profile.preferences.get("personal_goals", {}),
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error setting personal goals for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def get_personal_goals(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get personal goals for a user.
        
        Returns:
            Dictionary of personal goals or None if user not found
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                return None

            return {
                "user_id": user_id,
                "personal_goals": profile.preferences.get("personal_goals", {}),
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting personal goals for user {user_id}: {str(e)}")
            return None

    async def update_notification_frequency(
        self,
        user_id: int,
        frequency: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update notification frequency preference for a user.
        
        Allows users to choose how often they receive gamification notifications:
        - immediate: Real-time notifications
        - daily: Daily digest
        - weekly: Weekly digest
        - disabled: No notifications
        
        Args:
            user_id: User ID
            frequency: Notification frequency (immediate, daily, weekly, disabled)
            
        Returns:
            Updated notification settings or None on error
        """
        try:
            # Validate frequency
            if frequency not in self.AVAILABLE_NOTIFICATION_FREQUENCIES:
                logger.warning(f"Invalid notification frequency: {frequency}")
                return None

            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Initialize notifications if not present
            if "notifications" not in profile.preferences:
                profile.preferences["notifications"] = {}

            # Update frequency
            profile.preferences["notifications"]["frequency"] = frequency
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated notification frequency for user {user_id}: {frequency}")

            return {
                "user_id": user_id,
                "notification_frequency": frequency,
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating notification frequency for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def update_notification_types(
        self,
        user_id: int,
        notification_types: Dict[str, bool]
    ) -> Optional[Dict[str, Any]]:
        """
        Update which types of notifications the user wants to receive.
        
        Allows users to enable/disable specific notification types:
        - streakReminders: Notifications when streaks are at risk
        - achievementCelebrations: Notifications when achievements are unlocked
        - challengeUpdates: Notifications about challenge progress
        
        Args:
            user_id: User ID
            notification_types: Dictionary of notification type names to boolean values
            
        Returns:
            Updated notification settings or None on error
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Validate notification types
            valid_types = {"streakReminders", "achievementCelebrations", "challengeUpdates"}
            invalid_types = set(notification_types.keys()) - valid_types
            if invalid_types:
                logger.warning(f"Invalid notification types: {invalid_types}")
                return None

            # Initialize notifications if not present
            if "notifications" not in profile.preferences:
                profile.preferences["notifications"] = {}

            # Update notification types
            profile.preferences["notifications"].update(notification_types)
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated notification types for user {user_id}: {notification_types}")

            return {
                "user_id": user_id,
                "notification_types": profile.preferences.get("notifications", {}),
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating notification types for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def set_achievement_category_preferences(
        self,
        user_id: int,
        categories: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Set preferred achievement categories for a user.
        
        Allows users to select which achievement categories they want to focus on:
        - expense_tracking
        - invoice_management
        - habit_formation
        - financial_health
        - exploration
        
        Args:
            user_id: User ID
            categories: List of achievement category names
            
        Returns:
            Updated achievement category preferences or None on error
        """
        try:
            # Validate categories
            invalid_categories = set(categories) - set(self.AVAILABLE_ACHIEVEMENT_CATEGORIES)
            if invalid_categories:
                logger.warning(f"Invalid achievement categories: {invalid_categories}")
                return None

            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Update achievement categories
            profile.preferences["achievement_categories"] = categories
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated achievement category preferences for user {user_id}: {categories}")

            return {
                "user_id": user_id,
                "achievement_categories": categories,
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error setting achievement category preferences for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def set_visual_theme(
        self,
        user_id: int,
        theme: str
    ) -> Optional[Dict[str, Any]]:
        """
        Set the visual theme for gamification interface.
        
        Available themes:
        - light: Light theme
        - dark: Dark theme
        - colorful: Colorful theme
        - minimal: Minimal theme
        - professional: Professional theme
        
        Args:
            user_id: User ID
            theme: Theme name
            
        Returns:
            Updated theme preference or None on error
        """
        try:
            # Validate theme
            if theme not in self.AVAILABLE_THEMES:
                logger.warning(f"Invalid theme: {theme}")
                return None

            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Update theme
            profile.preferences["visual_theme"] = theme
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Updated visual theme for user {user_id}: {theme}")

            return {
                "user_id": user_id,
                "visual_theme": theme,
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error setting visual theme for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def get_available_themes(self) -> List[str]:
        """Get list of available visual themes"""
        return self.AVAILABLE_THEMES

    async def get_available_achievement_categories(self) -> List[str]:
        """Get list of available achievement categories"""
        return self.AVAILABLE_ACHIEVEMENT_CATEGORIES

    async def get_available_notification_frequencies(self) -> List[str]:
        """Get list of available notification frequencies"""
        return self.AVAILABLE_NOTIFICATION_FREQUENCIES

    async def reset_preferences_to_defaults(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Reset all user preferences to system defaults.
        
        Args:
            user_id: User ID
            
        Returns:
            Reset preferences or None on error
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not profile:
                logger.warning(f"No gamification profile found for user {user_id}")
                return None

            # Reset to defaults
            profile.preferences = {
                "features": {
                    "points": True,
                    "achievements": True,
                    "streaks": True,
                    "challenges": True,
                    "social": False,
                    "notifications": True
                },
                "privacy": {
                    "shareAchievements": False,
                    "showOnLeaderboard": False,
                    "allowFriendRequests": False
                },
                "notifications": {
                    "streakReminders": True,
                    "achievementCelebrations": True,
                    "challengeUpdates": True,
                    "frequency": "daily"
                },
                "personal_goals": {},
                "achievement_categories": self.AVAILABLE_ACHIEVEMENT_CATEGORIES,
                "visual_theme": "light"
            }
            profile.updated_at = datetime.now(timezone.utc)
            
            # Mark the preferences column as modified for SQLAlchemy to detect changes
            flag_modified(profile, "preferences")

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Reset preferences to defaults for user {user_id}")

            return {
                "user_id": user_id,
                "preferences": profile.preferences,
                "updated_at": profile.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error resetting preferences for user {user_id}: {str(e)}")
            self.db.rollback()
            return None

    async def validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a preferences dictionary.
        
        Returns:
            Dictionary with validation results and any errors
        """
        errors = []
        warnings = []

        try:
            # Validate features
            if "features" in preferences:
                valid_features = {"points", "achievements", "streaks", "challenges", "social", "notifications"}
                invalid = set(preferences["features"].keys()) - valid_features
                if invalid:
                    errors.append(f"Invalid features: {invalid}")

            # Validate notification frequency
            if "notifications" in preferences:
                freq = preferences["notifications"].get("frequency")
                if freq and freq not in self.AVAILABLE_NOTIFICATION_FREQUENCIES:
                    errors.append(f"Invalid notification frequency: {freq}")

            # Validate achievement categories
            if "achievement_categories" in preferences:
                invalid = set(preferences["achievement_categories"]) - set(self.AVAILABLE_ACHIEVEMENT_CATEGORIES)
                if invalid:
                    errors.append(f"Invalid achievement categories: {invalid}")

            # Validate visual theme
            if "visual_theme" in preferences:
                if preferences["visual_theme"] not in self.AVAILABLE_THEMES:
                    errors.append(f"Invalid visual theme: {preferences['visual_theme']}")

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"Error validating preferences: {str(e)}")
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": []
            }
