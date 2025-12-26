"""
Preference Hierarchy Resolver Service

This service implements the preference hierarchy system that respects:
User Privacy > Organization Policy > System Defaults

The hierarchy ensures that user privacy choices always override organizational settings,
while organizational policies can override system defaults.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from core.models.gamification import (
    UserGamificationProfile,
    OrganizationGamificationConfig
)
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)


class PreferenceHierarchyResolver:
    """
    Service for resolving user preferences respecting the hierarchy:
    User Privacy > Organization Policy > System Defaults
    """

    def __init__(self, db: Session):
        self.db = db

    # System Defaults
    SYSTEM_DEFAULTS = {
        "point_values": {
            "expenseTracking": 10,
            "invoiceCreation": 15,
            "budgetReview": 20,
            "receiptUpload": 3,
            "categoryAccuracy": 5,
            "timelyReminders": 8,
            "promptPaymentMarking": 12
        },
        "achievement_thresholds": {
            "expenseMilestones": [10, 50, 100, 500],
            "invoiceMilestones": [1, 10, 100],
            "streakMilestones": [7, 30, 90, 365],
            "budgetAdherenceThreshold": 90
        },
        "enabled_features": {
            "points": True,
            "achievements": True,
            "streaks": True,
            "challenges": True,
            "leaderboards": False,
            "teamChallenges": False,
            "socialSharing": False,
            "notifications": True
        },
        "privacy_settings": {
            "shareAchievements": False,
            "showOnLeaderboard": False,
            "allowFriendRequests": False
        },
        "notification_settings": {
            "streakReminders": True,
            "achievementCelebrations": True,
            "challengeUpdates": True,
            "frequency": "daily"
        }
    }

    async def resolve_user_preferences(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resolve user preferences respecting the hierarchy:
        User Privacy > Organization Policy > System Defaults

        Returns a complete preferences object with all settings resolved.
        """
        try:
            # Start with system defaults
            resolved = self._deep_copy_defaults()

            # Apply organization settings if organization_id is provided
            if organization_id:
                org_config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

                if org_config and org_config.enabled:
                    # Apply organization point values
                    if org_config.custom_point_values:
                        resolved["point_values"] = {
                            **resolved["point_values"],
                            **org_config.custom_point_values
                        }

                    # Apply organization achievement thresholds
                    if org_config.achievement_thresholds:
                        resolved["achievement_thresholds"] = {
                            **resolved["achievement_thresholds"],
                            **org_config.achievement_thresholds
                        }

                    # Apply organization enabled features
                    if org_config.enabled_features:
                        resolved["enabled_features"] = {
                            **resolved["enabled_features"],
                            **org_config.enabled_features
                        }

            # Apply user preferences (always override for privacy settings)
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if user_profile and user_profile.preferences:
                user_prefs = user_profile.preferences

                # User can override feature settings
                if "features" in user_prefs:
                    resolved["enabled_features"] = {
                        **resolved["enabled_features"],
                        **user_prefs["features"]
                    }

                # User privacy settings ALWAYS override organization settings
                if "privacy" in user_prefs:
                    resolved["privacy_settings"] = user_prefs["privacy"]

                # User notification settings override organization settings
                if "notifications" in user_prefs:
                    resolved["notification_settings"] = {
                        **resolved["notification_settings"],
                        **user_prefs["notifications"]
                    }

            return {
                "user_id": user_id,
                "organization_id": organization_id,
                "resolved_preferences": resolved,
                "hierarchy_applied": True
            }

        except Exception as e:
            logger.error(f"Error resolving user preferences for user {user_id}: {str(e)}")
            # Return system defaults on error
            return {
                "user_id": user_id,
                "organization_id": organization_id,
                "resolved_preferences": self._deep_copy_defaults(),
                "hierarchy_applied": False,
                "error": str(e)
            }

    async def get_effective_point_values(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get the effective point values for a user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["point_values"]
        except Exception as e:
            logger.error(f"Error getting effective point values: {str(e)}")
            return self.SYSTEM_DEFAULTS["point_values"]

    async def get_effective_achievement_thresholds(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get the effective achievement thresholds for a user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["achievement_thresholds"]
        except Exception as e:
            logger.error(f"Error getting effective achievement thresholds: {str(e)}")
            return self.SYSTEM_DEFAULTS["achievement_thresholds"]

    async def get_effective_enabled_features(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> Dict[str, bool]:
        """Get the effective enabled features for a user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["enabled_features"]
        except Exception as e:
            logger.error(f"Error getting effective enabled features: {str(e)}")
            return self.SYSTEM_DEFAULTS["enabled_features"]

    async def get_user_privacy_settings(self, user_id: int) -> Dict[str, bool]:
        """
        Get user privacy settings.
        These are ALWAYS user-controlled and never overridden by organization settings.
        """
        try:
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if user_profile and user_profile.preferences:
                privacy = user_profile.preferences.get("privacy", {})
                return {
                    **self.SYSTEM_DEFAULTS["privacy_settings"],
                    **privacy
                }

            return self.SYSTEM_DEFAULTS["privacy_settings"]

        except Exception as e:
            logger.error(f"Error getting user privacy settings: {str(e)}")
            return self.SYSTEM_DEFAULTS["privacy_settings"]

    async def is_feature_enabled_for_user(
        self,
        user_id: int,
        feature: str,
        organization_id: Optional[int] = None
    ) -> bool:
        """Check if a specific feature is enabled for a user"""
        try:
            enabled_features = await self.get_effective_enabled_features(user_id, organization_id)
            return enabled_features.get(feature, False)
        except Exception as e:
            logger.error(f"Error checking if feature {feature} is enabled: {str(e)}")
            return self.SYSTEM_DEFAULTS["enabled_features"].get(feature, False)

    async def can_user_share_achievements(self, user_id: int) -> bool:
        """Check if user has opted in to share achievements"""
        try:
            privacy_settings = await self.get_user_privacy_settings(user_id)
            return privacy_settings.get("shareAchievements", False)
        except Exception as e:
            logger.error(f"Error checking if user can share achievements: {str(e)}")
            return False

    async def can_user_appear_on_leaderboard(self, user_id: int) -> bool:
        """Check if user has opted in to appear on leaderboard"""
        try:
            privacy_settings = await self.get_user_privacy_settings(user_id)
            return privacy_settings.get("showOnLeaderboard", False)
        except Exception as e:
            logger.error(f"Error checking if user can appear on leaderboard: {str(e)}")
            return False

    async def get_notification_frequency(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> str:
        """Get the notification frequency for a user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["notification_settings"].get("frequency", "daily")
        except Exception as e:
            logger.error(f"Error getting notification frequency: {str(e)}")
            return "daily"

    async def should_send_streak_reminders(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> bool:
        """Check if streak reminders should be sent to the user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["notification_settings"].get("streakReminders", True)
        except Exception as e:
            logger.error(f"Error checking streak reminders setting: {str(e)}")
            return True

    async def should_send_achievement_celebrations(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> bool:
        """Check if achievement celebrations should be sent to the user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["notification_settings"].get("achievementCelebrations", True)
        except Exception as e:
            logger.error(f"Error checking achievement celebrations setting: {str(e)}")
            return True

    async def should_send_challenge_updates(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> bool:
        """Check if challenge updates should be sent to the user"""
        try:
            resolved = await self.resolve_user_preferences(user_id, organization_id)
            return resolved["resolved_preferences"]["notification_settings"].get("challengeUpdates", True)
        except Exception as e:
            logger.error(f"Error checking challenge updates setting: {str(e)}")
            return True

    async def validate_preference_override(
        self,
        user_id: int,
        setting_key: str,
        organization_id: Optional[int] = None
    ) -> bool:
        """
        Validate if a user can override a specific setting.
        Privacy settings can always be overridden by users.
        Other settings depend on organization policy.
        """
        try:
            # Privacy settings can always be overridden
            if setting_key.startswith("privacy_"):
                return True

            # Check if organization allows this override
            if organization_id:
                org_config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

                if org_config:
                    # For now, allow all overrides except for strict policy settings
                    # This can be extended based on organization policies
                    return True

            return True

        except Exception as e:
            logger.error(f"Error validating preference override: {str(e)}")
            return False

    async def get_preference_source(
        self,
        user_id: int,
        setting_key: str,
        organization_id: Optional[int] = None
    ) -> str:
        """
        Determine the source of a preference setting.
        Returns: "user", "organization", or "system"
        """
        try:
            # Check user preferences first
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if user_profile and user_profile.preferences:
                # Check if user has explicitly set this preference
                if self._has_user_preference(user_profile.preferences, setting_key):
                    return "user"

            # Check organization preferences
            if organization_id:
                org_config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

                if org_config and self._has_org_preference(org_config, setting_key):
                    return "organization"

            # Default to system
            return "system"

        except Exception as e:
            logger.error(f"Error getting preference source: {str(e)}")
            return "system"

    # Private Helper Methods
    def _deep_copy_defaults(self) -> Dict[str, Any]:
        """Create a deep copy of system defaults"""
        import copy
        return copy.deepcopy(self.SYSTEM_DEFAULTS)

    def _has_user_preference(self, user_prefs: Dict[str, Any], setting_key: str) -> bool:
        """Check if user has explicitly set a preference"""
        # This is a simplified check - can be extended based on needs
        if "features" in user_prefs and setting_key.startswith("feature_"):
            return True
        if "privacy" in user_prefs and setting_key.startswith("privacy_"):
            return True
        if "notifications" in user_prefs and setting_key.startswith("notification_"):
            return True
        return False

    def _has_org_preference(self, org_config: OrganizationGamificationConfig, setting_key: str) -> bool:
        """Check if organization has set a preference"""
        # This is a simplified check - can be extended based on needs
        if setting_key.startswith("point_") and org_config.custom_point_values:
            return True
        if setting_key.startswith("achievement_") and org_config.achievement_thresholds:
            return True
        if setting_key.startswith("feature_") and org_config.enabled_features:
            return True
        return False
