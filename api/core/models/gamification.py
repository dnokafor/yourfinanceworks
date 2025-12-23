"""
Gamification database models for the finance application.

This module contains all database models related to the gamification system,
including user profiles, achievements, streaks, challenges, and organizational settings.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum

from core.models.models_per_tenant import Base
from core.utils.column_encryptor import EncryptedColumn, EncryptedJSON


# Enums for gamification system
class DataRetentionPolicy(str, PyEnum):
    """Policy for handling gamification data when module is disabled"""
    PRESERVE = "preserve"  # Keep data when disabled, restore when re-enabled
    ARCHIVE = "archive"    # Archive data when disabled, can be restored
    DELETE = "delete"      # Delete data when disabled (user choice)


class HabitType(str, PyEnum):
    """Types of financial habits tracked by the system"""
    DAILY_EXPENSE_TRACKING = "daily_expense_tracking"
    WEEKLY_BUDGET_REVIEW = "weekly_budget_review"
    INVOICE_FOLLOW_UP = "invoice_follow_up"
    RECEIPT_DOCUMENTATION = "receipt_documentation"


class AchievementCategory(str, PyEnum):
    """Categories for organizing achievements"""
    EXPENSE_TRACKING = "expense_tracking"
    INVOICE_MANAGEMENT = "invoice_management"
    HABIT_FORMATION = "habit_formation"
    FINANCIAL_HEALTH = "financial_health"
    EXPLORATION = "exploration"


class AchievementDifficulty(str, PyEnum):
    """Difficulty levels for achievements"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class ChallengeType(str, PyEnum):
    """Types of challenges available"""
    PERSONAL = "personal"
    COMMUNITY = "community"
    SEASONAL = "seasonal"


class NotificationFrequency(str, PyEnum):
    """Frequency for gamification notifications"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"


# Database Models
class UserGamificationProfile(Base):
    """
    Main gamification profile for each user.
    Contains level, XP, and overall gamification settings.
    """
    __tablename__ = "user_gamification_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Module status
    module_enabled = Column(Boolean, default=True, nullable=False)
    enabled_at = Column(DateTime(timezone=True), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    data_retention_policy = Column(SQLEnum(DataRetentionPolicy), default=DataRetentionPolicy.PRESERVE, nullable=False)
    
    # Progress tracking
    level = Column(Integer, default=1, nullable=False)
    total_experience_points = Column(Integer, default=0, nullable=False)
    current_level_progress = Column(Float, default=0.0, nullable=False)  # Percentage to next level
    
    # Financial health score
    financial_health_score = Column(Float, default=0.0, nullable=False)  # 0-100 scale
    
    # Preferences stored as JSON
    preferences = Column(JSON, nullable=False, default={
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
        }
    })
    
    # Statistics stored as JSON
    statistics = Column(JSON, nullable=False, default={
        "totalActionsCompleted": 0,
        "expensesTracked": 0,
        "invoicesCreated": 0,
        "receiptsUploaded": 0,
        "budgetReviews": 0,
        "longestStreak": 0,
        "achievementsUnlocked": 0,
        "challengesCompleted": 0
    })
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User")
    achievements = relationship("UserAchievement", back_populates="profile", cascade="all, delete-orphan")
    streaks = relationship("UserStreak", back_populates="profile", cascade="all, delete-orphan")
    challenges = relationship("UserChallenge", back_populates="profile", cascade="all, delete-orphan")
    point_history = relationship("PointHistory", back_populates="profile", cascade="all, delete-orphan")


class Achievement(Base):
    """
    Master list of all available achievements in the system.
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    achievement_id = Column(String, unique=True, nullable=False, index=True)  # Unique identifier
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(AchievementCategory), nullable=False, index=True)
    difficulty = Column(SQLEnum(AchievementDifficulty), nullable=False, index=True)
    
    # Requirements stored as JSON
    requirements = Column(JSON, nullable=False)  # e.g., {"type": "expense_count", "target": 100}
    
    # Rewards
    reward_xp = Column(Integer, nullable=False, default=0)
    reward_badge_url = Column(String, nullable=True)
    
    # Visibility
    is_hidden = Column(Boolean, default=False, nullable=False)  # Hidden until unlocked
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """
    Tracks which achievements each user has unlocked and their progress.
    """
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_gamification_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    progress = Column(Float, default=0.0, nullable=False)  # Percentage complete (0-100)
    is_completed = Column(Boolean, default=False, nullable=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    profile = relationship("UserGamificationProfile", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class UserStreak(Base):
    """
    Tracks user streaks for different habit types.
    """
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_gamification_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    habit_type = Column(SQLEnum(HabitType), nullable=False, index=True)
    current_length = Column(Integer, default=0, nullable=False)
    longest_length = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Streak metadata
    streak_start_date = Column(DateTime(timezone=True), nullable=True)
    times_broken = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    profile = relationship("UserGamificationProfile", back_populates="streaks")


class Challenge(Base):
    """
    Master list of all available challenges.
    """
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    challenge_type = Column(SQLEnum(ChallengeType), nullable=False, index=True)
    
    # Duration in days
    duration_days = Column(Integer, nullable=False)
    
    # Requirements stored as JSON
    requirements = Column(JSON, nullable=False)  # e.g., {"type": "track_expenses", "target": 7, "period": "daily"}
    
    # Rewards
    reward_xp = Column(Integer, nullable=False, default=0)
    reward_badge_url = Column(String, nullable=True)
    
    # Availability
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Organization-specific challenge
    organization_id = Column(Integer, nullable=True)  # NULL for system-wide challenges
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user_challenges = relationship("UserChallenge", back_populates="challenge")


class UserChallenge(Base):
    """
    Tracks user participation and progress in challenges.
    """
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_gamification_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    
    progress = Column(Float, default=0.0, nullable=False)  # Percentage complete (0-100)
    is_completed = Column(Boolean, default=False, nullable=False)
    opted_in = Column(Boolean, default=True, nullable=False)
    
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Milestones achieved stored as JSON array
    milestones = Column(JSON, nullable=False, default=[])
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    profile = relationship("UserGamificationProfile", back_populates="challenges")
    challenge = relationship("Challenge", back_populates="user_challenges")


class PointHistory(Base):
    """
    Tracks all point awards for audit and analytics.
    """
    __tablename__ = "point_history"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_gamification_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type = Column(String, nullable=False, index=True)  # e.g., "expense_added", "invoice_created"
    points_awarded = Column(Integer, nullable=False)
    
    # Context about the action
    action_metadata = Column(JSON, nullable=True)  # Additional context about what earned the points
    
    # Multipliers applied
    base_points = Column(Integer, nullable=False)
    streak_multiplier = Column(Float, default=1.0, nullable=False)
    accuracy_bonus = Column(Integer, default=0, nullable=False)
    completeness_bonus = Column(Integer, default=0, nullable=False)
    timeliness_bonus = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    profile = relationship("UserGamificationProfile", back_populates="point_history")


class OrganizationGamificationConfig(Base):
    """
    Organization-level gamification configuration.
    Allows admins to customize gamification for their organization.
    """
    __tablename__ = "organization_gamification_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, unique=True, index=True)  # References master tenant table
    
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Custom point values stored as JSON
    custom_point_values = Column(JSON, nullable=False, default={
        "expenseTracking": 10,
        "invoiceCreation": 15,
        "budgetReview": 20,
        "receiptUpload": 3,
        "categoryAccuracy": 5,
        "timelyReminders": 8,
        "promptPaymentMarking": 12
    })
    
    # Achievement thresholds stored as JSON
    achievement_thresholds = Column(JSON, nullable=False, default={
        "expenseMilestones": [10, 50, 100, 500],
        "invoiceMilestones": [1, 10, 100],
        "streakMilestones": [7, 30, 90, 365],
        "budgetAdherenceThreshold": 90
    })
    
    # Enabled features
    enabled_features = Column(JSON, nullable=False, default={
        "points": True,
        "achievements": True,
        "streaks": True,
        "challenges": True,
        "leaderboards": False,
        "teamChallenges": False,
        "socialSharing": False,
        "notifications": True
    })
    
    # Team settings
    team_settings = Column(JSON, nullable=False, default={
        "enableTeamLeaderboards": False,
        "teamChallengeFrequency": "monthly",
        "crossTeamCompetition": False,
        "teamSizeForChallenges": 5,
        "anonymousLeaderboards": True
    })
    
    # Policy alignment
    policy_alignment = Column(JSON, nullable=False, default={
        "expenseCategories": [],
        "receiptRequirements": "optional",
        "budgetEnforcement": {
            "enforceStrictLimits": False,
            "warningThreshold": 80,
            "penalizeOverspending": False
        },
        "invoiceTimelines": {
            "reminderFrequency": 7,
            "escalationThreshold": 30,
            "requiredFollowUpActions": []
        }
    })
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class AchievementShare(Base):
    """
    Tracks achievement shares for social features.
    Allows users to share their achievements with others.
    """
    __tablename__ = "achievement_shares"

    id = Column(Integer, primary_key=True, index=True)
    user_achievement_id = Column(Integer, ForeignKey("user_achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Share metadata
    share_message = Column(Text, nullable=True)  # Optional message with the share
    is_public = Column(Boolean, default=False, nullable=False)  # Public vs private share
    share_count = Column(Integer, default=0, nullable=False)  # How many times viewed/shared
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Leaderboard(Base):
    """
    Leaderboard entries for user rankings.
    Supports both global and organization-specific leaderboards.
    """
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_gamification_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Leaderboard scope
    leaderboard_type = Column(String, nullable=False, index=True)  # "global", "organization", "team"
    scope_id = Column(Integer, nullable=True, index=True)  # organization_id or team_id if applicable
    
    # Ranking data
    rank = Column(Integer, nullable=False, index=True)
    experience_points = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    
    # Visibility
    is_visible = Column(Boolean, default=True, nullable=False)  # User can hide from leaderboard
    is_anonymous = Column(Boolean, default=False, nullable=False)  # Anonymous entry
    
    # Metadata
    rank_change = Column(Integer, default=0, nullable=False)  # Change from last update
    last_rank_update = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    profile = relationship("UserGamificationProfile")


class GroupChallenge(Base):
    """
    Group challenges for team or organization-wide participation.
    """
    __tablename__ = "group_challenges"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Group scope
    group_type = Column(String, nullable=False, index=True)  # "organization", "team", "custom_group"
    group_id = Column(Integer, nullable=False, index=True)  # organization_id, team_id, or custom group id
    
    # Group challenge metadata
    group_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Participation
    max_participants = Column(Integer, nullable=True)  # NULL for unlimited
    current_participants = Column(Integer, default=0, nullable=False)
    
    # Rewards
    group_reward_xp = Column(Integer, default=0, nullable=False)  # Bonus XP for group completion
    individual_reward_xp = Column(Integer, default=0, nullable=False)  # Individual completion reward
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    challenge = relationship("Challenge")


class GroupChallengeParticipant(Base):
    """
    Tracks user participation in group challenges.
    """
    __tablename__ = "group_challenge_participants"

    id = Column(Integer, primary_key=True, index=True)
    group_challenge_id = Column(Integer, ForeignKey("group_challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    user_challenge_id = Column(Integer, ForeignKey("user_challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Participation status
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Contribution to group
    contribution_points = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    group_challenge = relationship("GroupChallenge")
    user_challenge = relationship("UserChallenge")
