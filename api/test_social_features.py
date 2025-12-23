"""
Property-based tests for social features in gamification system.

Tests cover leaderboards, achievement sharing, and group challenges.
Feature: gamified-finance-habits
"""

import pytest
import sys
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import logging

# Add the api directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models.gamification import (
    UserGamificationProfile,
    Achievement,
    UserAchievement,
    AchievementShare,
    Leaderboard,
    GroupChallenge,
    GroupChallengeParticipant,
    UserChallenge,
    Challenge,
    AchievementCategory,
    AchievementDifficulty,
    ChallengeType,
    HabitType
)
from core.models.models_per_tenant import User
from core.services.social_features_manager import SocialFeaturesManager
from core.models.database import SessionLocal

logger = logging.getLogger(__name__)


@pytest.fixture
def db():
    """Create a test database session."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_profile(db: Session, test_user: User) -> UserGamificationProfile:
    """Create a test gamification profile with social features enabled."""
    profile = UserGamificationProfile(
        user_id=test_user.id,
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
                "social": True,
                "notifications": True
            },
            "privacy": {
                "shareAchievements": True,
                "showOnLeaderboard": True,
                "allowFriendRequests": False
            },
            "notifications": {
                "streakReminders": True,
                "achievementCelebrations": True,
                "challengeUpdates": True,
                "frequency": "daily"
            }
        },
        statistics={
            "totalActionsCompleted": 0,
            "expensesTracked": 0,
            "invoicesCreated": 0,
            "receiptsUploaded": 0,
            "budgetReviews": 0,
            "longestStreak": 0,
            "achievementsUnlocked": 0,
            "challengesCompleted": 0
        }
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def test_achievement(db: Session) -> Achievement:
    """Create a test achievement."""
    achievement = Achievement(
        achievement_id="test_achievement_1",
        name="Test Achievement",
        description="A test achievement",
        category=AchievementCategory.EXPENSE_TRACKING,
        difficulty=AchievementDifficulty.BRONZE,
        requirements=[{"type": "expense_count", "target": 10}],
        reward_xp=100,
        is_hidden=False,
        is_active=True
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


@pytest.fixture
def test_user_achievement(db: Session, test_profile: UserGamificationProfile, test_achievement: Achievement) -> UserAchievement:
    """Create a test user achievement."""
    user_achievement = UserAchievement(
        profile_id=test_profile.id,
        achievement_id=test_achievement.id,
        progress=100.0,
        is_completed=True,
        unlocked_at=datetime.now(timezone.utc)
    )
    db.add(user_achievement)
    db.commit()
    db.refresh(user_achievement)
    return user_achievement


@pytest.fixture
def test_challenge(db: Session) -> Challenge:
    """Create a test challenge."""
    challenge = Challenge(
        challenge_id="test_challenge_1",
        name="Test Challenge",
        description="A test challenge",
        challenge_type=ChallengeType.PERSONAL,
        duration_days=7,
        requirements=[{"type": "track_expenses", "target": 7, "period": "daily"}],
        reward_xp=50,
        is_active=True
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


class TestSocialFeaturesStatusCheck:
    """Test social features status checking."""

    async def test_social_features_enabled_when_enabled(self, db: Session, test_profile: UserGamificationProfile):
        """
        Property 23: Social Features Conditional Availability
        For any user with social features enabled, the system should report social features as available.
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        test_profile.preferences["features"]["social"] = True
        db.commit()
        
        manager = SocialFeaturesManager(db)
        result = await manager.check_social_features_enabled(test_profile.user_id)
        
        assert result is True

    async def test_social_features_disabled_when_disabled(self, db: Session, test_profile: UserGamificationProfile):
        """
        Property 23: Social Features Conditional Availability
        For any user with social features disabled, the system should report social features as unavailable.
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        test_profile.preferences["features"]["social"] = False
        db.commit()
        
        manager = SocialFeaturesManager(db)
        result = await manager.check_social_features_enabled(test_profile.user_id)
        
        assert result is False

    async def test_social_features_disabled_when_module_disabled(self, db: Session, test_profile: UserGamificationProfile):
        """Test that social features are disabled when gamification module is disabled."""
        test_profile.module_enabled = False
        db.commit()
        
        manager = SocialFeaturesManager(db)
        result = await manager.check_social_features_enabled(test_profile.user_id)
        
        assert result is False


class TestAchievementSharing:
    """Test achievement sharing functionality."""

    async def test_share_achievement_success(self, db: Session, test_profile: UserGamificationProfile, test_user_achievement: UserAchievement):
        """Test successful achievement sharing."""
        manager = SocialFeaturesManager(db)
        
        share = await manager.share_achievement(
            user_id=test_profile.user_id,
            user_achievement_id=test_user_achievement.id,
            share_message="Check out my achievement!",
            is_public=True
        )
        
        assert share is not None
        assert share.shared_by_user_id == test_profile.user_id
        assert share.user_achievement_id == test_user_achievement.id
        assert share.share_message == "Check out my achievement!"
        assert share.is_public is True

    async def test_share_achievement_fails_when_social_disabled(self, db: Session, test_profile: UserGamificationProfile, test_user_achievement: UserAchievement):
        """Test that achievement sharing fails when social features are disabled."""
        test_profile.preferences["features"]["social"] = False
        db.commit()
        
        manager = SocialFeaturesManager(db)
        share = await manager.share_achievement(
            user_id=test_profile.user_id,
            user_achievement_id=test_user_achievement.id,
            share_message="Check out my achievement!",
            is_public=True
        )
        
        assert share is None

    async def test_share_achievement_fails_with_invalid_achievement(self, db: Session, test_profile: UserGamificationProfile):
        """Test that achievement sharing fails with invalid achievement ID."""
        manager = SocialFeaturesManager(db)
        
        share = await manager.share_achievement(
            user_id=test_profile.user_id,
            user_achievement_id=99999,
            share_message="Check out my achievement!",
            is_public=True
        )
        
        assert share is None

    async def test_share_achievement_public(self, db: Session, test_profile: UserGamificationProfile, test_user_achievement: UserAchievement):
        """
        Property 24: Social Privacy Controls
        For any achievement share, the user should be able to make it public.
        **Validates: Requirements 10.4, 10.5**
        """
        manager = SocialFeaturesManager(db)
        
        share = await manager.share_achievement(
            user_id=test_profile.user_id,
            user_achievement_id=test_user_achievement.id,
            share_message="Check out my achievement!",
            is_public=True
        )
        
        assert share is not None
        assert share.is_public is True

    async def test_share_achievement_private(self, db: Session, test_profile: UserGamificationProfile, test_user_achievement: UserAchievement):
        """
        Property 24: Social Privacy Controls
        For any achievement share, the user should be able to make it private.
        **Validates: Requirements 10.4, 10.5**
        """
        manager = SocialFeaturesManager(db)
        
        share = await manager.share_achievement(
            user_id=test_profile.user_id,
            user_achievement_id=test_user_achievement.id,
            share_message="Check out my achievement!",
            is_public=False
        )
        
        assert share is not None
        assert share.is_public is False


class TestLeaderboardManagement:
    """Test leaderboard functionality."""

    async def test_get_global_leaderboard(self, db: Session, test_profile: UserGamificationProfile):
        """Test retrieving global leaderboard."""
        leaderboard = Leaderboard(
            profile_id=test_profile.id,
            leaderboard_type="global",
            scope_id=None,
            rank=1,
            experience_points=1000,
            level=5,
            is_visible=True,
            is_anonymous=False
        )
        db.add(leaderboard)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        leaderboard_data = await manager.get_leaderboard(
            leaderboard_type="global",
            limit=100,
            offset=0
        )
        
        assert leaderboard_data is not None
        assert len(leaderboard_data["entries"]) > 0
        assert leaderboard_data["total_entries"] > 0

    async def test_get_user_leaderboard_position(self, db: Session, test_profile: UserGamificationProfile):
        """Test retrieving user's leaderboard position."""
        leaderboard = Leaderboard(
            profile_id=test_profile.id,
            leaderboard_type="global",
            scope_id=None,
            rank=5,
            experience_points=500,
            level=3,
            is_visible=True,
            is_anonymous=False
        )
        db.add(leaderboard)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        position = await manager.get_user_leaderboard_position(
            user_id=test_profile.user_id,
            leaderboard_type="global"
        )
        
        assert position is not None
        assert position["rank"] == 5
        assert position["experience_points"] == 500
        assert position["level"] == 3

    async def test_update_leaderboard_visibility_public(self, db: Session, test_profile: UserGamificationProfile):
        """
        Property 24: Social Privacy Controls
        For any user, the system should allow updating leaderboard visibility to public.
        **Validates: Requirements 10.4, 10.5**
        """
        leaderboard = Leaderboard(
            profile_id=test_profile.id,
            leaderboard_type="global",
            scope_id=None,
            rank=1,
            experience_points=1000,
            level=5,
            is_visible=False,
            is_anonymous=True
        )
        db.add(leaderboard)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        success = await manager.update_leaderboard_visibility(
            user_id=test_profile.user_id,
            is_visible=True,
            is_anonymous=False
        )
        
        assert success is True
        
        updated_leaderboard = db.query(Leaderboard).filter(
            Leaderboard.profile_id == test_profile.id
        ).first()
        
        assert updated_leaderboard.is_visible is True
        assert updated_leaderboard.is_anonymous is False

    async def test_update_leaderboard_visibility_private(self, db: Session, test_profile: UserGamificationProfile):
        """
        Property 24: Social Privacy Controls
        For any user, the system should allow updating leaderboard visibility to private.
        **Validates: Requirements 10.4, 10.5**
        """
        leaderboard = Leaderboard(
            profile_id=test_profile.id,
            leaderboard_type="global",
            scope_id=None,
            rank=1,
            experience_points=1000,
            level=5,
            is_visible=True,
            is_anonymous=False
        )
        db.add(leaderboard)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        success = await manager.update_leaderboard_visibility(
            user_id=test_profile.user_id,
            is_visible=False,
            is_anonymous=True
        )
        
        assert success is True
        
        updated_leaderboard = db.query(Leaderboard).filter(
            Leaderboard.profile_id == test_profile.id
        ).first()
        
        assert updated_leaderboard.is_visible is False
        assert updated_leaderboard.is_anonymous is True


class TestGroupChallenges:
    """Test group challenge functionality."""

    async def test_create_group_challenge(self, db: Session, test_challenge: Challenge):
        """Test creating a group challenge."""
        manager = SocialFeaturesManager(db)
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)
        
        group_challenge = await manager.create_group_challenge(
            challenge_id=test_challenge.id,
            group_type="organization",
            group_id=1,
            group_name="Test Organization Challenge",
            start_date=start_date,
            end_date=end_date,
            description="A test group challenge",
            max_participants=50,
            group_reward_xp=100,
            individual_reward_xp=50
        )
        
        assert group_challenge is not None
        assert group_challenge.group_name == "Test Organization Challenge"
        assert group_challenge.current_participants == 0

    async def test_join_group_challenge(self, db: Session, test_profile: UserGamificationProfile, test_challenge: Challenge):
        """Test joining a group challenge."""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)
        
        group_challenge = GroupChallenge(
            challenge_id=test_challenge.id,
            group_type="organization",
            group_id=1,
            group_name="Test Challenge",
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            current_participants=0
        )
        db.add(group_challenge)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        participant = await manager.join_group_challenge(
            user_id=test_profile.user_id,
            group_challenge_id=group_challenge.id
        )
        
        assert participant is not None
        assert participant.is_active is True
        
        db.refresh(group_challenge)
        assert group_challenge.current_participants == 1

    async def test_leave_group_challenge(self, db: Session, test_profile: UserGamificationProfile, test_challenge: Challenge):
        """Test leaving a group challenge."""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)
        
        group_challenge = GroupChallenge(
            challenge_id=test_challenge.id,
            group_type="organization",
            group_id=1,
            group_name="Test Challenge",
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            current_participants=1
        )
        db.add(group_challenge)
        db.flush()
        
        user_challenge = UserChallenge(
            profile_id=test_profile.id,
            challenge_id=test_challenge.id,
            progress=0.0,
            is_completed=False,
            opted_in=True
        )
        db.add(user_challenge)
        db.flush()
        
        participant = GroupChallengeParticipant(
            group_challenge_id=group_challenge.id,
            user_challenge_id=user_challenge.id,
            is_active=True
        )
        db.add(participant)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        success = await manager.leave_group_challenge(
            user_id=test_profile.user_id,
            group_challenge_id=group_challenge.id
        )
        
        assert success is True
        
        db.refresh(participant)
        assert participant.is_active is False
        assert participant.left_at is not None
        
        db.refresh(group_challenge)
        assert group_challenge.current_participants == 0

    async def test_get_group_challenge_details(self, db: Session, test_profile: UserGamificationProfile, test_challenge: Challenge):
        """Test retrieving group challenge details."""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)
        
        group_challenge = GroupChallenge(
            challenge_id=test_challenge.id,
            group_type="organization",
            group_id=1,
            group_name="Test Challenge",
            description="Test description",
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            current_participants=0
        )
        db.add(group_challenge)
        db.commit()
        
        manager = SocialFeaturesManager(db)
        details = await manager.get_group_challenge_details(group_challenge.id)
        
        assert details is not None
        assert details["group_name"] == "Test Challenge"
        assert details["description"] == "Test description"
        assert details["current_participants"] == 0


class TestLeaderboardRankingUpdates:
    """Test leaderboard ranking update functionality."""

    async def test_update_leaderboard_rankings(self, db: Session, test_profile: UserGamificationProfile):
        """Test updating leaderboard rankings."""
        test_profile.total_experience_points = 1000
        test_profile.level = 5
        db.commit()
        
        manager = SocialFeaturesManager(db)
        success = await manager.update_leaderboard_rankings()
        
        assert success is True
        
        leaderboard = db.query(Leaderboard).filter(
            Leaderboard.profile_id == test_profile.id,
            Leaderboard.leaderboard_type == "global"
        ).first()
        
        assert leaderboard is not None
        assert leaderboard.experience_points == 1000
        assert leaderboard.level == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
