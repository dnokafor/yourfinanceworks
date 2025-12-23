"""
Tests for User Preference Controls Service

Tests the granular user preference controls for gamification including:
- Feature enable/disable controls
- Personal goal setting
- Notification frequency controls
- Achievement category preferences
- Visual theme selection

Implements Requirement 12: Customization and Preferences
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.models.gamification import (
    UserGamificationProfile,
    DataRetentionPolicy
)
from core.services.user_preference_controls import UserPreferenceControls
from core.models.models_per_tenant import User


@pytest.fixture
def user_with_gamification_profile(db_session: Session):
    """Create a test user with gamification profile"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.flush()

    profile = UserGamificationProfile(
        user_id=user.id,
        module_enabled=True,
        level=1,
        total_experience_points=0,
        current_level_progress=0.0,
        financial_health_score=0.0,
        preferences={
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
            "achievement_categories": [
                "expense_tracking",
                "invoice_management",
                "habit_formation",
                "financial_health",
                "exploration"
            ],
            "visual_theme": "light"
        }
    )
    db_session.add(profile)
    db_session.commit()

    return user, profile


class TestUserPreferenceControls:
    """Test suite for user preference controls"""

    @pytest.mark.asyncio
    async def test_get_user_preferences(self, db_session: Session, user_with_gamification_profile):
        """Test retrieving user preferences"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        preferences = await preference_controls.get_user_preferences(user.id)

        assert preferences is not None
        assert preferences["user_id"] == user.id
        assert preferences["module_enabled"] is True
        assert "features" in preferences
        assert "privacy" in preferences
        assert "notifications" in preferences
        assert preferences["visual_theme"] == "light"

    @pytest.mark.asyncio
    async def test_get_user_preferences_not_found(self, db_session: Session):
        """Test getting preferences for non-existent user"""
        preference_controls = UserPreferenceControls(db_session)

        preferences = await preference_controls.get_user_preferences(99999)

        assert preferences is None

    @pytest.mark.asyncio
    async def test_update_feature_preferences(self, db_session: Session, user_with_gamification_profile):
        """Test updating feature preferences"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        # Disable social features
        features = {"social": False, "challenges": False}
        result = await preference_controls.update_feature_preferences(user.id, features)

        assert result is not None
        assert result["features"]["social"] == False
        assert result["features"]["challenges"] == False
        # Other features should remain unchanged
        assert result["features"]["points"] == True

    @pytest.mark.asyncio
    async def test_update_feature_preferences_invalid_feature(self, db_session: Session, user_with_gamification_profile):
        """Test updating with invalid feature name"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        # Try to set invalid feature
        features = {"invalid_feature": True}
        result = await preference_controls.update_feature_preferences(user.id, features)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_personal_goals(self, db_session: Session, user_with_gamification_profile):
        """Test setting personal goals"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        goals = {
            "daily_expense_target": 5,
            "weekly_budget_review_frequency": 1,
            "monthly_invoice_target": 10
        }
        result = await preference_controls.set_personal_goals(user.id, goals)

        assert result is not None
        assert result["personal_goals"]["daily_expense_target"] == 5
        assert result["personal_goals"]["weekly_budget_review_frequency"] == 1
        assert result["personal_goals"]["monthly_invoice_target"] == 10

    @pytest.mark.asyncio
    async def test_get_personal_goals(self, db_session: Session, user_with_gamification_profile):
        """Test retrieving personal goals"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        # Set goals first
        goals = {"daily_expense_target": 5}
        await preference_controls.set_personal_goals(user.id, goals)

        # Retrieve goals
        result = await preference_controls.get_personal_goals(user.id)

        assert result is not None
        assert result["personal_goals"]["daily_expense_target"] == 5

    @pytest.mark.asyncio
    async def test_update_notification_frequency(self, db_session: Session, user_with_gamification_profile):
        """Test updating notification frequency"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        result = await preference_controls.update_notification_frequency(user.id, "weekly")

        assert result is not None
        assert result["notification_frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_update_notification_frequency_invalid(self, db_session: Session, user_with_gamification_profile):
        """Test updating with invalid notification frequency"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        result = await preference_controls.update_notification_frequency(user.id, "invalid_frequency")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_notification_types(self, db_session: Session, user_with_gamification_profile):
        """Test updating notification types"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        notification_types = {
            "streakReminders": False,
            "achievementCelebrations": True,
            "challengeUpdates": False
        }
        result = await preference_controls.update_notification_types(user.id, notification_types)

        assert result is not None
        assert result["notification_types"]["streakReminders"] == False
        assert result["notification_types"]["achievementCelebrations"] == True
        assert result["notification_types"]["challengeUpdates"] == False

    @pytest.mark.asyncio
    async def test_update_notification_types_invalid(self, db_session: Session, user_with_gamification_profile):
        """Test updating with invalid notification type"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        notification_types = {"invalidType": True}
        result = await preference_controls.update_notification_types(user.id, notification_types)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_achievement_category_preferences(self, db_session: Session, user_with_gamification_profile):
        """Test setting achievement category preferences"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        categories = ["expense_tracking", "invoice_management"]
        result = await preference_controls.set_achievement_category_preferences(user.id, categories)

        assert result is not None
        assert result["achievement_categories"] == categories

    @pytest.mark.asyncio
    async def test_set_achievement_category_preferences_invalid(self, db_session: Session, user_with_gamification_profile):
        """Test setting with invalid achievement category"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        categories = ["invalid_category"]
        result = await preference_controls.set_achievement_category_preferences(user.id, categories)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_visual_theme(self, db_session: Session, user_with_gamification_profile):
        """Test setting visual theme"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        result = await preference_controls.set_visual_theme(user.id, "dark")

        assert result is not None
        assert result["visual_theme"] == "dark"

    @pytest.mark.asyncio
    async def test_set_visual_theme_invalid(self, db_session: Session, user_with_gamification_profile):
        """Test setting invalid visual theme"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        result = await preference_controls.set_visual_theme(user.id, "invalid_theme")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_available_themes(self, db_session: Session):
        """Test getting available themes"""
        preference_controls = UserPreferenceControls(db_session)

        themes = await preference_controls.get_available_themes()

        assert isinstance(themes, list)
        assert len(themes) > 0
        assert "light" in themes
        assert "dark" in themes

    @pytest.mark.asyncio
    async def test_get_available_achievement_categories(self, db_session: Session):
        """Test getting available achievement categories"""
        preference_controls = UserPreferenceControls(db_session)

        categories = await preference_controls.get_available_achievement_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "expense_tracking" in categories
        assert "invoice_management" in categories

    @pytest.mark.asyncio
    async def test_get_available_notification_frequencies(self, db_session: Session):
        """Test getting available notification frequencies"""
        preference_controls = UserPreferenceControls(db_session)

        frequencies = await preference_controls.get_available_notification_frequencies()

        assert isinstance(frequencies, list)
        assert len(frequencies) > 0
        assert "immediate" in frequencies
        assert "daily" in frequencies
        assert "weekly" in frequencies
        assert "disabled" in frequencies

    @pytest.mark.asyncio
    async def test_reset_preferences_to_defaults(self, db_session: Session, user_with_gamification_profile):
        """Test resetting preferences to defaults"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        # Modify preferences
        await preference_controls.set_visual_theme(user.id, "dark")
        await preference_controls.update_notification_frequency(user.id, "weekly")

        # Reset to defaults
        result = await preference_controls.reset_preferences_to_defaults(user.id)

        assert result is not None
        assert result["preferences"]["visual_theme"] == "light"
        assert result["preferences"]["notifications"]["frequency"] == "daily"

    @pytest.mark.asyncio
    async def test_validate_preferences_valid(self, db_session: Session):
        """Test validating valid preferences"""
        preference_controls = UserPreferenceControls(db_session)

        preferences = {
            "features": {
                "points": True,
                "achievements": True
            },
            "notifications": {
                "frequency": "daily"
            },
            "visual_theme": "light"
        }
        result = await preference_controls.validate_preferences(preferences)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_preferences_invalid_feature(self, db_session: Session):
        """Test validating preferences with invalid feature"""
        preference_controls = UserPreferenceControls(db_session)

        preferences = {
            "features": {
                "invalid_feature": True
            }
        }
        result = await preference_controls.validate_preferences(preferences)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_preferences_invalid_frequency(self, db_session: Session):
        """Test validating preferences with invalid frequency"""
        preference_controls = UserPreferenceControls(db_session)

        preferences = {
            "notifications": {
                "frequency": "invalid_frequency"
            }
        }
        result = await preference_controls.validate_preferences(preferences)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_preferences_invalid_theme(self, db_session: Session):
        """Test validating preferences with invalid theme"""
        preference_controls = UserPreferenceControls(db_session)

        preferences = {
            "visual_theme": "invalid_theme"
        }
        result = await preference_controls.validate_preferences(preferences)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_preference_update(self, db_session: Session, user_with_gamification_profile):
        """Test comprehensive preference update workflow"""
        user, profile = user_with_gamification_profile
        preference_controls = UserPreferenceControls(db_session)

        # Update multiple preferences
        await preference_controls.update_feature_preferences(user.id, {"social": True})
        await preference_controls.set_personal_goals(user.id, {"daily_target": 10})
        await preference_controls.update_notification_frequency(user.id, "weekly")
        await preference_controls.set_achievement_category_preferences(
            user.id,
            ["expense_tracking", "invoice_management"]
        )
        await preference_controls.set_visual_theme(user.id, "dark")

        # Retrieve all preferences
        preferences = await preference_controls.get_user_preferences(user.id)

        assert preferences["features"]["social"] == True
        assert preferences["personal_goals"]["daily_target"] == 10
        assert preferences["notifications"]["frequency"] == "weekly"
        assert preferences["achievement_categories"] == ["expense_tracking", "invoice_management"]
        assert preferences["visual_theme"] == "dark"
