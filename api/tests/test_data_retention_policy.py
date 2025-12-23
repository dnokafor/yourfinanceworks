"""
Property-based tests for data retention policy system.

This test suite validates the correctness properties of the data retention system:
- Property 30: Data Retention Control
- Validates: Requirements 13.3, 13.4

Tests cover:
1. Preserve policy - data remains accessible after disable/enable
2. Archive policy - data is archived and can be restored
3. Delete policy - data is permanently removed
4. Policy transitions - changing policies handles data correctly
5. Data consistency - data state matches retention policy
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.orm import Session

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.services.data_retention_manager import DataRetentionManager
from core.services.gamification_module_manager import GamificationModuleManager
from core.models.gamification import (
    UserGamificationProfile,
    UserAchievement,
    UserStreak,
    UserChallenge,
    PointHistory,
    Achievement,
    Challenge,
    HabitType,
    AchievementCategory,
    AchievementDifficulty,
    ChallengeType,
    DataRetentionPolicy
)
from core.schemas.gamification import (
    EnableGamificationRequest,
    DisableGamificationRequest,
    GamificationPreferences,
    DataRetentionPolicy as SchemaDataRetentionPolicy
)
from core.models.models import Tenant, User


@pytest.fixture
def tenant_db():
    """Get a tenant database session for testing"""
    master_db = next(get_master_db())
    tenant = master_db.query(Tenant).filter(Tenant.is_active == True).first()
    
    if not tenant:
        pytest.skip("No active tenant found")
    
    session = tenant_db_manager.get_tenant_session(tenant.id)
    db = session()
    
    yield db
    
    db.close()


@pytest.fixture
def test_user(tenant_db: Session) -> User:
    """Create a test user"""
    user = User(
        email=f"test_retention_{datetime.now(timezone.utc).timestamp()}@example.com",
        password_hash="test_hash",
        is_active=True
    )
    tenant_db.add(user)
    tenant_db.commit()
    tenant_db.refresh(user)
    return user


@pytest.fixture
def gamification_profile(tenant_db: Session, test_user: User) -> UserGamificationProfile:
    """Create a gamification profile for testing"""
    profile = UserGamificationProfile(
        user_id=test_user.id,
        module_enabled=True,
        level=5,
        total_experience_points=1000,
        current_level_progress=50.0,
        financial_health_score=75.0,
        preferences={
            "features": {"points": True, "achievements": True},
            "privacy": {"shareAchievements": False}
        },
        statistics={
            "totalActionsCompleted": 100,
            "expensesTracked": 50,
            "achievementsUnlocked": 5
        }
    )
    tenant_db.add(profile)
    tenant_db.commit()
    tenant_db.refresh(profile)
    return profile


@pytest.fixture
def achievement_with_user(tenant_db: Session, gamification_profile: UserGamificationProfile) -> UserAchievement:
    """Create an achievement for testing"""
    achievement = Achievement(
        achievement_id="test_achievement",
        name="Test Achievement",
        description="Test",
        category=AchievementCategory.EXPENSE_TRACKING,
        difficulty=AchievementDifficulty.BRONZE,
        requirements=[{"type": "expense_count", "target": 10}],
        reward_xp=100
    )
    tenant_db.add(achievement)
    tenant_db.commit()
    tenant_db.refresh(achievement)
    
    user_achievement = UserAchievement(
        profile_id=gamification_profile.id,
        achievement_id=achievement.id,
        progress=100.0,
        is_completed=True,
        unlocked_at=datetime.now(timezone.utc)
    )
    tenant_db.add(user_achievement)
    tenant_db.commit()
    tenant_db.refresh(user_achievement)
    return user_achievement


@pytest.fixture
def streak_with_user(tenant_db: Session, gamification_profile: UserGamificationProfile) -> UserStreak:
    """Create a streak for testing"""
    streak = UserStreak(
        profile_id=gamification_profile.id,
        habit_type=HabitType.DAILY_EXPENSE_TRACKING,
        current_length=15,
        longest_length=30,
        last_activity_date=datetime.now(timezone.utc),
        is_active=True
    )
    tenant_db.add(streak)
    tenant_db.commit()
    tenant_db.refresh(streak)
    return streak


@pytest.fixture
def challenge_with_user(tenant_db: Session, gamification_profile: UserGamificationProfile) -> UserChallenge:
    """Create a challenge for testing"""
    challenge = Challenge(
        challenge_id="test_challenge",
        name="Test Challenge",
        description="Test",
        challenge_type=ChallengeType.PERSONAL,
        duration_days=7,
        requirements=[{"type": "track_expenses", "target": 7}],
        reward_xp=200
    )
    tenant_db.add(challenge)
    tenant_db.commit()
    tenant_db.refresh(challenge)
    
    user_challenge = UserChallenge(
        profile_id=gamification_profile.id,
        challenge_id=challenge.id,
        progress=50.0,
        is_completed=False,
        opted_in=True
    )
    tenant_db.add(user_challenge)
    tenant_db.commit()
    tenant_db.refresh(user_challenge)
    return user_challenge


@pytest.fixture
def point_history_entry(tenant_db: Session, gamification_profile: UserGamificationProfile) -> PointHistory:
    """Create a point history entry for testing"""
    history = PointHistory(
        profile_id=gamification_profile.id,
        action_type="expense_added",
        points_awarded=10,
        base_points=10,
        streak_multiplier=1.0
    )
    tenant_db.add(history)
    tenant_db.commit()
    tenant_db.refresh(history)
    return history


class TestDataRetentionPreservePolicy:
    """Tests for PRESERVE retention policy"""
    
    @pytest.mark.asyncio
    async def test_preserve_policy_keeps_data_on_disable(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement,
        streak_with_user: UserStreak
    ):
        """
        Property 30: Data Retention Control - PRESERVE
        
        For any user with PRESERVE policy, disabling gamification should keep all data
        """
        manager = DataRetentionManager(tenant_db)
        
        # Apply PRESERVE policy on disable
        success = await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.PRESERVE,
            action="disable"
        )
        
        assert success
        
        # Verify data still exists
        achievements = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).all()
        assert len(achievements) > 0
        
        streaks = tenant_db.query(UserStreak).filter(
            UserStreak.profile_id == gamification_profile.id
        ).all()
        assert len(streaks) > 0
    
    @pytest.mark.asyncio
    async def test_preserve_policy_restores_on_enable(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any user with PRESERVE policy, re-enabling should restore all data
        """
        manager = DataRetentionManager(tenant_db)
        
        # Store original data
        original_level = gamification_profile.level
        original_xp = gamification_profile.total_experience_points
        
        # Disable with PRESERVE
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.PRESERVE,
            action="disable"
        )
        
        # Re-enable with PRESERVE
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.PRESERVE,
            action="enable"
        )
        
        # Verify data is still there
        tenant_db.refresh(gamification_profile)
        assert gamification_profile.level == original_level
        assert gamification_profile.total_experience_points == original_xp


class TestDataRetentionArchivePolicy:
    """Tests for ARCHIVE retention policy"""
    
    @pytest.mark.asyncio
    async def test_archive_policy_creates_snapshot(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any user with ARCHIVE policy, disabling should create a data snapshot
        """
        manager = DataRetentionManager(tenant_db)
        
        # Apply ARCHIVE policy
        success = await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.ARCHIVE,
            action="disable"
        )
        
        assert success
        
        # Verify snapshot was created
        tenant_db.refresh(gamification_profile)
        assert gamification_profile.preferences is not None
        assert "archived_data" in gamification_profile.preferences
        
        archived_data = gamification_profile.preferences["archived_data"]
        assert "snapshot" in archived_data
        assert archived_data["snapshot"]["level"] == gamification_profile.level
    
    @pytest.mark.asyncio
    async def test_archive_policy_restores_snapshot(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile
    ):
        """
        For any user with ARCHIVE policy, enabling should restore the snapshot
        """
        manager = DataRetentionManager(tenant_db)
        
        # Store original data
        original_level = gamification_profile.level
        original_xp = gamification_profile.total_experience_points
        
        # Archive
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.ARCHIVE,
            action="disable"
        )
        
        # Modify profile to simulate different state
        gamification_profile.level = 1
        gamification_profile.total_experience_points = 0
        tenant_db.commit()
        
        # Restore
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.ARCHIVE,
            action="enable"
        )
        
        # Verify restoration
        tenant_db.refresh(gamification_profile)
        assert gamification_profile.level == original_level
        assert gamification_profile.total_experience_points == original_xp


class TestDataRetentionDeletePolicy:
    """Tests for DELETE retention policy"""
    
    @pytest.mark.asyncio
    async def test_delete_policy_removes_all_data(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement,
        streak_with_user: UserStreak,
        challenge_with_user: UserChallenge,
        point_history_entry: PointHistory
    ):
        """
        Property 30: Data Retention Control - DELETE
        
        For any user with DELETE policy, disabling should remove all gamification data
        """
        manager = DataRetentionManager(tenant_db)
        
        # Verify data exists before delete
        achievements_before = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).count()
        assert achievements_before > 0
        
        # Apply DELETE policy
        success = await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.DELETE,
            action="disable"
        )
        
        assert success
        
        # Verify all data is deleted
        achievements_after = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).count()
        assert achievements_after == 0
        
        streaks_after = tenant_db.query(UserStreak).filter(
            UserStreak.profile_id == gamification_profile.id
        ).count()
        assert streaks_after == 0
        
        challenges_after = tenant_db.query(UserChallenge).filter(
            UserChallenge.profile_id == gamification_profile.id
        ).count()
        assert challenges_after == 0
        
        point_history_after = tenant_db.query(PointHistory).filter(
            PointHistory.profile_id == gamification_profile.id
        ).count()
        assert point_history_after == 0
    
    @pytest.mark.asyncio
    async def test_delete_policy_resets_profile_stats(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile
    ):
        """
        For any user with DELETE policy, profile statistics should be reset
        """
        manager = DataRetentionManager(tenant_db)
        
        # Apply DELETE policy
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.DELETE,
            action="disable"
        )
        
        # Verify profile is reset
        tenant_db.refresh(gamification_profile)
        assert gamification_profile.level == 1
        assert gamification_profile.total_experience_points == 0
        assert gamification_profile.current_level_progress == 0.0
        assert gamification_profile.financial_health_score == 0.0


class TestDataRetentionStatusAndValidation:
    """Tests for data retention status and validation"""
    
    @pytest.mark.asyncio
    async def test_get_retention_status(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any profile, getting retention status should return accurate data counts
        """
        manager = DataRetentionManager(tenant_db)
        
        status = await manager.get_data_retention_status(gamification_profile.id)
        
        assert status["profile_found"]
        assert status["module_enabled"] == gamification_profile.module_enabled
        assert status["retention_policy"] == gamification_profile.data_retention_policy.value
        assert status["data_counts"]["achievements"] > 0
    
    @pytest.mark.asyncio
    async def test_validate_data_consistency_with_delete_policy(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any profile with DELETE policy and disabled module, validation should detect orphaned data
        """
        manager = DataRetentionManager(tenant_db)
        
        # Set DELETE policy but don't actually delete data
        gamification_profile.data_retention_policy = DataRetentionPolicy.DELETE
        gamification_profile.module_enabled = False
        tenant_db.commit()
        
        # Validate - should find inconsistency
        validation = await manager.validate_data_consistency(gamification_profile.id)
        
        assert not validation["valid"]
        assert len(validation["issues"]) > 0


class TestDataRetentionPolicyTransitions:
    """Tests for transitioning between retention policies"""
    
    @pytest.mark.asyncio
    async def test_migrate_from_archive_to_preserve(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile
    ):
        """
        For any profile transitioning from ARCHIVE to PRESERVE, data should be restored
        """
        manager = DataRetentionManager(tenant_db)
        
        # First archive
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.ARCHIVE,
            action="disable"
        )
        
        # Then migrate to PRESERVE
        success = await manager.migrate_data_on_policy_change(
            gamification_profile.id,
            DataRetentionPolicy.ARCHIVE,
            DataRetentionPolicy.PRESERVE
        )
        
        assert success
        
        # Verify archived data marker is removed
        tenant_db.refresh(gamification_profile)
        assert "archived_data" not in gamification_profile.preferences or \
               gamification_profile.preferences.get("archived_data") is None
    
    @pytest.mark.asyncio
    async def test_cannot_recover_deleted_data(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any profile with DELETE policy, transitioning to another policy cannot recover data
        """
        manager = DataRetentionManager(tenant_db)
        
        # Delete data
        await manager.apply_retention_policy(
            gamification_profile.id,
            DataRetentionPolicy.DELETE,
            action="disable"
        )
        
        # Try to migrate to PRESERVE
        success = await manager.migrate_data_on_policy_change(
            gamification_profile.id,
            DataRetentionPolicy.DELETE,
            DataRetentionPolicy.PRESERVE
        )
        
        # Should succeed but data remains deleted
        assert success
        
        # Verify data is still gone
        achievements = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).count()
        assert achievements == 0


class TestModuleManagerDataRetention:
    """Integration tests with module manager"""
    
    @pytest.mark.asyncio
    async def test_disable_with_preserve_policy(
        self,
        tenant_db: Session,
        test_user: User,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any user disabling gamification with PRESERVE policy, data should remain
        """
        module_manager = GamificationModuleManager(tenant_db)
        
        # Disable with PRESERVE
        request = DisableGamificationRequest(
            data_retention_policy=SchemaDataRetentionPolicy.PRESERVE
        )
        success = await module_manager.disable_gamification(test_user.id, request)
        
        assert success
        
        # Verify data exists
        achievements = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).count()
        assert achievements > 0
    
    @pytest.mark.asyncio
    async def test_disable_with_delete_policy(
        self,
        tenant_db: Session,
        test_user: User,
        gamification_profile: UserGamificationProfile,
        achievement_with_user: UserAchievement
    ):
        """
        For any user disabling gamification with DELETE policy, all data should be removed
        """
        module_manager = GamificationModuleManager(tenant_db)
        
        # Disable with DELETE
        request = DisableGamificationRequest(
            data_retention_policy=SchemaDataRetentionPolicy.DELETE
        )
        success = await module_manager.disable_gamification(test_user.id, request)
        
        assert success
        
        # Verify data is deleted
        achievements = tenant_db.query(UserAchievement).filter(
            UserAchievement.profile_id == gamification_profile.id
        ).count()
        assert achievements == 0


# Property-based tests using Hypothesis
class TestDataRetentionProperties:
    """Property-based tests for data retention system"""
    
    @given(
        policy=st.sampled_from([
            DataRetentionPolicy.PRESERVE,
            DataRetentionPolicy.ARCHIVE,
            DataRetentionPolicy.DELETE
        ])
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_retention_policy_application_idempotent(
        self,
        tenant_db: Session,
        gamification_profile: UserGamificationProfile,
        policy
    ):
        """
        Property: Applying the same retention policy twice should be idempotent
        
        For any retention policy, applying it twice should result in the same state
        """
        manager = DataRetentionManager(tenant_db)
        
        # Apply policy first time
        result1 = await manager.apply_retention_policy(
            gamification_profile.id,
            policy,
            action="disable"
        )
        
        # Get status after first application
        status1 = await manager.get_data_retention_status(gamification_profile.id)
        
        # Apply policy second time
        result2 = await manager.apply_retention_policy(
            gamification_profile.id,
            policy,
            action="disable"
        )
        
        # Get status after second application
        status2 = await manager.get_data_retention_status(gamification_profile.id)
        
        # Both applications should succeed
        assert result1
        assert result2
        
        # Status should be the same
        assert status1["retention_policy"] == status2["retention_policy"]
        assert status1["data_counts"] == status2["data_counts"]
