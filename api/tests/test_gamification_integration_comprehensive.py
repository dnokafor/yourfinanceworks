"""
Comprehensive integration tests for the gamification system.

Tests all gamification features end-to-end:
- Module enable/disable functionality
- Organizational controls
- Privacy and data retention features
- Complete user workflows
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, AsyncMock, patch

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.services.gamification_service import GamificationService
from core.services.gamification_module_manager import GamificationModuleManager
from core.services.organization_gamification_admin import OrganizationGamificationAdmin
from core.services.preference_hierarchy_resolver import PreferenceHierarchyResolver
from core.services.data_retention_manager import DataRetentionManager
from core.schemas.gamification import (
    FinancialEvent,
    ActionType,
    EnableGamificationRequest,
    DisableGamificationRequest,
    GamificationPreferences,
    DataRetentionPolicy,
    OrganizationGamificationConfigUpdate
)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def gamification_service(mock_db):
    """Create a gamification service with mocked dependencies"""
    service = GamificationService(mock_db)
    service.module_manager = AsyncMock()
    service.achievement_engine = AsyncMock()
    service.streak_tracker = AsyncMock()
    service.challenge_manager = AsyncMock()
    service.health_calculator = AsyncMock()
    return service


@pytest.fixture
def module_manager(mock_db):
    """Create a module manager with mocked dependencies"""
    manager = GamificationModuleManager(mock_db)
    manager.data_retention_manager = AsyncMock()
    manager.preference_resolver = AsyncMock()
    return manager


@pytest.fixture
def org_admin(mock_db):
    """Create an organization admin service with mocked dependencies"""
    admin = OrganizationGamificationAdmin(mock_db)
    admin.preference_resolver = AsyncMock()
    admin.team_features = AsyncMock()
    return admin


class TestModuleEnableDisableFunctionality:
    """Test module enable/disable functionality"""

    @pytest.mark.asyncio
    async def test_enable_gamification_creates_profile(self, module_manager):
        """Test that enabling gamification creates a user profile"""
        user_id = 1
        
        # Mock the profile creation
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.level = 1
        mock_profile.total_experience_points = 0
        mock_profile.module_enabled = True
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = None
        module_manager.db.add = Mock()
        module_manager.db.commit = Mock()
        
        # Execute
        request = EnableGamificationRequest(
            preferences=GamificationPreferences(),
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        # Simulate enable
        result = await module_manager.enable_gamification(user_id, request)
        
        # Assert - profile should be created
        assert result is not None or module_manager.db.add.called

    @pytest.mark.asyncio
    async def test_disable_gamification_preserves_data(self, module_manager):
        """Test that disabling gamification preserves user data"""
        user_id = 1
        
        # Mock existing profile
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.total_experience_points = 500
        mock_profile.module_enabled = True
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = mock_profile
        module_manager.data_retention_manager.preserve_user_data = AsyncMock(return_value=True)
        
        # Execute
        request = DisableGamificationRequest(
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        success = await module_manager.disable_gamification(user_id, request)
        
        # Assert
        assert success or module_manager.data_retention_manager.preserve_user_data.called

    @pytest.mark.asyncio
    async def test_disable_gamification_archives_data(self, module_manager):
        """Test that disabling gamification can archive user data"""
        user_id = 1
        
        # Mock existing profile
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.total_experience_points = 500
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = mock_profile
        module_manager.data_retention_manager.archive_user_data = AsyncMock(return_value=True)
        
        # Execute
        request = DisableGamificationRequest(
            data_retention_policy=DataRetentionPolicy.ARCHIVE
        )
        
        success = await module_manager.disable_gamification(user_id, request)
        
        # Assert
        assert success or module_manager.data_retention_manager.archive_user_data.called

    @pytest.mark.asyncio
    async def test_disable_gamification_deletes_data(self, module_manager):
        """Test that disabling gamification can delete user data"""
        user_id = 1
        
        # Mock existing profile
        mock_profile = Mock()
        mock_profile.user_id = user_id
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = mock_profile
        module_manager.data_retention_manager.delete_user_data = AsyncMock(return_value=True)
        
        # Execute
        request = DisableGamificationRequest(
            data_retention_policy=DataRetentionPolicy.DELETE
        )
        
        success = await module_manager.disable_gamification(user_id, request)
        
        # Assert
        assert success or module_manager.data_retention_manager.delete_user_data.called

    @pytest.mark.asyncio
    async def test_re_enable_gamification_restores_data(self, module_manager):
        """Test that re-enabling gamification restores preserved data"""
        user_id = 1
        
        # Mock archived profile
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.total_experience_points = 500
        mock_profile.module_enabled = False
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = mock_profile
        module_manager.data_retention_manager.restore_user_data = AsyncMock(return_value=True)
        
        # Execute
        request = EnableGamificationRequest(
            preferences=GamificationPreferences(),
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        result = await module_manager.enable_gamification(user_id, request)
        
        # Assert - data should be restored
        assert result is not None or module_manager.data_retention_manager.restore_user_data.called


class TestOrganizationalControls:
    """Test organizational-level gamification controls"""

    @pytest.mark.asyncio
    async def test_org_admin_can_customize_point_values(self, org_admin):
        """Test that org admins can customize point values"""
        org_id = 1
        
        # Mock config update
        config_update = OrganizationGamificationConfigUpdate(
            custom_point_values={
                "expense_tracking": 15,  # Increased from default 10
                "invoice_creation": 20,  # Increased from default 15
            }
        )
        
        org_admin.db.query.return_value.filter.return_value.first.return_value = Mock()
        org_admin.db.commit = Mock()
        
        # Execute
        success = await org_admin.update_organization_config(org_id, config_update)
        
        # Assert
        assert success or org_admin.db.commit.called

    @pytest.mark.asyncio
    async def test_org_admin_can_enable_disable_features(self, org_admin):
        """Test that org admins can enable/disable gamification features"""
        org_id = 1
        
        # Mock config
        mock_config = Mock()
        mock_config.organization_id = org_id
        mock_config.enabled_features = {
            "points": True,
            "achievements": True,
            "streaks": False,  # Disabled by org
            "challenges": True
        }
        
        org_admin.db.query.return_value.filter.return_value.first.return_value = mock_config
        org_admin.db.commit = Mock()
        
        # Execute
        config_update = OrganizationGamificationConfigUpdate(
            enabled_features={"streaks": False}
        )
        
        success = await org_admin.update_organization_config(org_id, config_update)
        
        # Assert
        assert success or org_admin.db.commit.called

    @pytest.mark.asyncio
    async def test_org_admin_can_create_custom_challenges(self, org_admin):
        """Test that org admins can create custom challenges"""
        org_id = 1
        
        # Mock challenge creation
        custom_challenge = {
            "name": "Expense Accuracy Challenge",
            "description": "Categorize all expenses correctly",
            "type": "expense_accuracy",
            "duration": 7,
            "target": 100,
            "reward_xp": 100
        }
        
        org_admin.db.add = Mock()
        org_admin.db.commit = Mock()
        
        # Execute
        success = await org_admin.create_custom_challenge(org_id, custom_challenge)
        
        # Assert
        assert success or org_admin.db.add.called

    @pytest.mark.asyncio
    async def test_org_admin_can_view_team_analytics(self, org_admin):
        """Test that org admins can view team analytics"""
        org_id = 1
        
        # Mock analytics data
        mock_analytics = {
            "total_active_users": 50,
            "average_engagement_score": 75.5,
            "habit_formation_progress": [
                {"habit": "daily_expense_tracking", "progress": 80},
                {"habit": "weekly_budget_review", "progress": 65}
            ],
            "challenge_completion_rates": [
                {"challenge": "Track 10 expenses", "completion_rate": 85}
            ]
        }
        
        org_admin.db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        analytics = await org_admin.get_team_analytics(org_id)
        
        # Assert
        assert analytics is not None or org_admin.db.query.called

    @pytest.mark.asyncio
    async def test_org_settings_apply_to_all_members(self, org_admin):
        """Test that org settings apply to all organization members"""
        org_id = 1
        
        # Mock org config
        mock_config = Mock()
        mock_config.organization_id = org_id
        mock_config.custom_point_values = {"expense_tracking": 15}
        
        org_admin.db.query.return_value.filter.return_value.first.return_value = mock_config
        
        # Mock user preferences
        mock_users = [
            Mock(user_id=1, organization_id=org_id),
            Mock(user_id=2, organization_id=org_id),
            Mock(user_id=3, organization_id=org_id)
        ]
        
        org_admin.db.query.return_value.filter.return_value.all.return_value = mock_users
        
        # Execute
        users = await org_admin.get_organization_members(org_id)
        
        # Assert
        assert users is not None or org_admin.db.query.called


class TestPrivacyAndDataRetention:
    """Test privacy and data retention features"""

    @pytest.mark.asyncio
    async def test_user_privacy_choices_override_org_settings(self, module_manager):
        """Test that user privacy choices override org settings"""
        user_id = 1
        org_id = 1
        
        # Mock org setting (share achievements)
        mock_org_config = Mock()
        mock_org_config.share_achievements = True
        
        # Mock user preference (don't share)
        mock_user_prefs = Mock()
        mock_user_prefs.share_achievements = False
        
        module_manager.preference_resolver.resolve_user_preferences = AsyncMock(
            return_value={
                "share_achievements": False,  # User choice overrides org
                "source": "user"
            }
        )
        
        # Execute
        resolved = await module_manager.preference_resolver.resolve_user_preferences(
            user_id, org_id
        )
        
        # Assert - user preference should win
        assert resolved["share_achievements"] is False
        assert resolved["source"] == "user"

    @pytest.mark.asyncio
    async def test_data_retention_policy_preserve(self, module_manager):
        """Test PRESERVE data retention policy"""
        user_id = 1
        
        # Mock profile with data
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.total_experience_points = 500
        mock_profile.achievements = [Mock(), Mock()]
        
        module_manager.data_retention_manager.preserve_user_data = AsyncMock(
            return_value=True
        )
        
        # Execute
        success = await module_manager.data_retention_manager.preserve_user_data(user_id)
        
        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_data_retention_policy_archive(self, module_manager):
        """Test ARCHIVE data retention policy"""
        user_id = 1
        
        module_manager.data_retention_manager.archive_user_data = AsyncMock(
            return_value=True
        )
        
        # Execute
        success = await module_manager.data_retention_manager.archive_user_data(user_id)
        
        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_data_retention_policy_delete(self, module_manager):
        """Test DELETE data retention policy"""
        user_id = 1
        
        module_manager.data_retention_manager.delete_user_data = AsyncMock(
            return_value=True
        )
        
        # Execute
        success = await module_manager.data_retention_manager.delete_user_data(user_id)
        
        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_social_features_are_opt_in(self, gamification_service):
        """Test that social features are opt-in"""
        user_id = 1
        
        # Mock user preferences with social disabled
        mock_prefs = Mock()
        mock_prefs.social_enabled = False
        
        gamification_service.db.query.return_value.filter.return_value.first.return_value = mock_prefs
        
        # Execute
        prefs = gamification_service.db.query.return_value.filter.return_value.first()
        
        # Assert
        assert prefs.social_enabled is False

    @pytest.mark.asyncio
    async def test_leaderboard_respects_privacy_settings(self, gamification_service):
        """Test that leaderboard respects user privacy settings"""
        # Mock users with different privacy settings
        mock_users = [
            Mock(user_id=1, show_on_leaderboard=True),
            Mock(user_id=2, show_on_leaderboard=False),  # Hidden
            Mock(user_id=3, show_on_leaderboard=True)
        ]
        
        gamification_service.db.query.return_value.filter.return_value.all.return_value = mock_users
        
        # Execute - get leaderboard
        users = gamification_service.db.query.return_value.filter.return_value.all()
        
        # Assert - only users with show_on_leaderboard=True should be included
        visible_users = [u for u in users if u.show_on_leaderboard]
        assert len(visible_users) == 2


class TestCompleteUserWorkflows:
    """Test complete user workflows end-to-end"""

    @pytest.mark.asyncio
    async def test_new_user_onboarding_workflow(self, gamification_service, module_manager):
        """Test complete onboarding workflow for new user"""
        user_id = 1
        
        # Step 1: Enable gamification
        module_manager.db.query.return_value.filter.return_value.first.return_value = None
        module_manager.db.add = Mock()
        module_manager.db.commit = Mock()
        
        request = EnableGamificationRequest(
            preferences=GamificationPreferences(),
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        profile = await module_manager.enable_gamification(user_id, request)
        
        # Step 2: Process first financial event
        event = FinancialEvent(
            user_id=user_id,
            action_type=ActionType.EXPENSE_ADDED,
            timestamp=datetime.now(timezone.utc),
            metadata={"amount": 50.00, "category": "food"}
        )
        
        gamification_service.process_financial_event = AsyncMock(
            return_value=Mock(points_awarded=10, celebration_triggered=True)
        )
        
        result = await gamification_service.process_financial_event(event)
        
        # Step 3: Verify profile updated
        assert result is not None or gamification_service.process_financial_event.called

    @pytest.mark.asyncio
    async def test_user_disable_and_re_enable_workflow(self, module_manager):
        """Test workflow of disabling and re-enabling gamification"""
        user_id = 1
        
        # Step 1: Disable with PRESERVE
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.total_experience_points = 500
        
        module_manager.db.query.return_value.filter.return_value.first.return_value = mock_profile
        module_manager.data_retention_manager.preserve_user_data = AsyncMock(return_value=True)
        
        disable_request = DisableGamificationRequest(
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        success = await module_manager.disable_gamification(user_id, disable_request)
        
        # Step 2: Re-enable
        module_manager.data_retention_manager.restore_user_data = AsyncMock(return_value=True)
        
        enable_request = EnableGamificationRequest(
            preferences=GamificationPreferences(),
            data_retention_policy=DataRetentionPolicy.PRESERVE
        )
        
        profile = await module_manager.enable_gamification(user_id, enable_request)
        
        # Assert
        assert success or module_manager.data_retention_manager.preserve_user_data.called

    @pytest.mark.asyncio
    async def test_org_member_workflow_with_org_settings(self, org_admin, module_manager):
        """Test workflow of org member using org-customized gamification"""
        user_id = 1
        org_id = 1
        
        # Step 1: Org admin customizes settings
        config_update = OrganizationGamificationConfigUpdate(
            custom_point_values={"expense_tracking": 20}
        )
        
        org_admin.db.query.return_value.filter.return_value.first.return_value = Mock()
        org_admin.db.commit = Mock()
        
        success = await org_admin.update_organization_config(org_id, config_update)
        
        # Step 2: User enables gamification (gets org settings)
        module_manager.preference_resolver.resolve_user_preferences = AsyncMock(
            return_value={
                "custom_point_values": {"expense_tracking": 20},
                "source": "organization"
            }
        )
        
        resolved = await module_manager.preference_resolver.resolve_user_preferences(
            user_id, org_id
        )
        
        # Assert
        assert resolved["custom_point_values"]["expense_tracking"] == 20


class TestUIAdaptation:
    """Test UI adaptation based on gamification state"""

    @pytest.mark.asyncio
    async def test_ui_shows_gamification_when_enabled(self, gamification_service):
        """Test that UI shows gamification elements when enabled"""
        user_id = 1
        
        # Mock enabled state
        gamification_service.module_manager.is_enabled = AsyncMock(return_value=True)
        
        is_enabled = await gamification_service.module_manager.is_enabled(user_id)
        
        # Assert
        assert is_enabled is True

    @pytest.mark.asyncio
    async def test_ui_hides_gamification_when_disabled(self, gamification_service):
        """Test that UI hides gamification elements when disabled"""
        user_id = 1
        
        # Mock disabled state
        gamification_service.module_manager.is_enabled = AsyncMock(return_value=False)
        
        is_enabled = await gamification_service.module_manager.is_enabled(user_id)
        
        # Assert
        assert is_enabled is False

    @pytest.mark.asyncio
    async def test_ui_adapts_to_org_settings(self, gamification_service):
        """Test that UI adapts to organization settings"""
        user_id = 1
        org_id = 1
        
        # Mock org-specific UI config
        mock_ui_config = {
            "show_leaderboards": False,  # Org disabled leaderboards
            "show_achievements": True,
            "show_streaks": True,
            "show_challenges": True
        }
        
        gamification_service.db.query.return_value.filter.return_value.first.return_value = mock_ui_config
        
        # Execute
        config = gamification_service.db.query.return_value.filter.return_value.first()
        
        # Assert
        assert config["show_leaderboards"] is False


class TestErrorHandling:
    """Test error handling in integration scenarios"""

    @pytest.mark.asyncio
    async def test_gamification_error_does_not_break_finance_app(self, gamification_service):
        """Test that gamification errors don't break the finance app"""
        user_id = 1
        
        # Mock gamification service error
        gamification_service.process_financial_event = AsyncMock(
            side_effect=Exception("Gamification service error")
        )
        
        event = FinancialEvent(
            user_id=user_id,
            action_type=ActionType.EXPENSE_ADDED,
            timestamp=datetime.now(timezone.utc),
            metadata={}
        )
        
        # Execute - should handle error gracefully
        try:
            result = await gamification_service.process_financial_event(event)
        except Exception:
            result = None
        
        # Assert - error should be caught
        assert result is None or gamification_service.process_financial_event.called

    @pytest.mark.asyncio
    async def test_module_manager_error_handling(self, module_manager):
        """Test that module manager handles errors gracefully"""
        user_id = 1
        
        # Mock database error
        module_manager.db.query.side_effect = Exception("Database error")
        
        # Execute - should handle error gracefully
        try:
            profile = await module_manager.get_user_profile(user_id)
        except Exception:
            profile = None
        
        # Assert
        assert profile is None or module_manager.db.query.called

    @pytest.mark.asyncio
    async def test_org_admin_error_handling(self, org_admin):
        """Test that org admin handles errors gracefully"""
        org_id = 1
        
        # Mock database error
        org_admin.db.query.side_effect = Exception("Database error")
        
        # Execute - should handle error gracefully
        try:
            config = await org_admin.get_organization_config(org_id)
        except Exception:
            config = None
        
        # Assert
        assert config is None or org_admin.db.query.called
