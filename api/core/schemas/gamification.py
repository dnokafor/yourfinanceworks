"""
Pydantic schemas for gamification API endpoints.

This module contains all request/response schemas for the gamification system,
including user profiles, achievements, streaks, challenges, and organizational settings.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums matching the database models
class DataRetentionPolicy(str, Enum):
    PRESERVE = "preserve"
    ARCHIVE = "archive"
    DELETE = "delete"


class HabitType(str, Enum):
    DAILY_EXPENSE_TRACKING = "daily_expense_tracking"
    WEEKLY_BUDGET_REVIEW = "weekly_budget_review"
    INVOICE_FOLLOW_UP = "invoice_follow_up"
    RECEIPT_DOCUMENTATION = "receipt_documentation"


class AchievementCategory(str, Enum):
    EXPENSE_TRACKING = "expense_tracking"
    INVOICE_MANAGEMENT = "invoice_management"
    HABIT_FORMATION = "habit_formation"
    FINANCIAL_HEALTH = "financial_health"
    EXPLORATION = "exploration"


class AchievementDifficulty(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class ChallengeType(str, Enum):
    PERSONAL = "personal"
    COMMUNITY = "community"
    SEASONAL = "seasonal"


class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"


class ActionType(str, Enum):
    """Types of financial actions that can earn points"""
    EXPENSE_ADDED = "expense_added"
    INVOICE_CREATED = "invoice_created"
    RECEIPT_UPLOADED = "receipt_uploaded"
    BUDGET_REVIEWED = "budget_reviewed"
    PAYMENT_RECORDED = "payment_recorded"
    CATEGORY_ASSIGNED = "category_assigned"


# Base schemas
class GamificationPreferences(BaseModel):
    """User preferences for gamification features"""
    features: Dict[str, bool] = Field(default={
        "points": True,
        "achievements": True,
        "streaks": True,
        "challenges": True,
        "social": False,
        "notifications": True
    })
    privacy: Dict[str, bool] = Field(default={
        "shareAchievements": False,
        "showOnLeaderboard": False,
        "allowFriendRequests": False
    })
    notifications: Dict[str, Union[bool, str]] = Field(default={
        "streakReminders": True,
        "achievementCelebrations": True,
        "challengeUpdates": True,
        "frequency": "daily"
    })


class UserStatistics(BaseModel):
    """User gamification statistics"""
    totalActionsCompleted: int = 0
    expensesTracked: int = 0
    invoicesCreated: int = 0
    receiptsUploaded: int = 0
    budgetReviews: int = 0
    longestStreak: int = 0
    achievementsUnlocked: int = 0
    challengesCompleted: int = 0


# User Gamification Profile schemas
class UserGamificationProfileBase(BaseModel):
    """Base schema for user gamification profile"""
    module_enabled: bool = True
    data_retention_policy: DataRetentionPolicy = DataRetentionPolicy.PRESERVE
    preferences: GamificationPreferences = Field(default_factory=GamificationPreferences)


class UserGamificationProfileCreate(UserGamificationProfileBase):
    """Schema for creating a new user gamification profile"""
    user_id: int


class UserGamificationProfileUpdate(BaseModel):
    """Schema for updating user gamification profile"""
    module_enabled: Optional[bool] = None
    data_retention_policy: Optional[DataRetentionPolicy] = None
    preferences: Optional[GamificationPreferences] = None


class UserGamificationProfileResponse(UserGamificationProfileBase):
    """Schema for user gamification profile API responses"""
    id: int
    user_id: int
    level: int
    total_experience_points: int
    current_level_progress: float
    financial_health_score: float
    statistics: UserStatistics
    enabled_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Achievement schemas
class AchievementRequirement(BaseModel):
    """Schema for achievement requirements"""
    type: str  # e.g., "expense_count", "streak_length", "invoice_total"
    target: Union[int, float]
    period: Optional[str] = None  # e.g., "daily", "weekly", "monthly"


class AchievementBase(BaseModel):
    """Base schema for achievements"""
    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    difficulty: AchievementDifficulty
    requirements: List[AchievementRequirement]
    reward_xp: int = 0
    reward_badge_url: Optional[str] = None
    is_hidden: bool = False


class AchievementCreate(AchievementBase):
    """Schema for creating new achievements"""
    pass


class AchievementResponse(AchievementBase):
    """Schema for achievement API responses"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """Schema for user achievement progress"""
    id: int
    achievement: AchievementResponse
    progress: float
    is_completed: bool
    unlocked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Streak schemas
class UserStreakBase(BaseModel):
    """Base schema for user streaks"""
    habit_type: HabitType
    current_length: int = 0
    longest_length: int = 0
    is_active: bool = True


class UserStreakResponse(UserStreakBase):
    """Schema for user streak API responses"""
    id: int
    last_activity_date: Optional[datetime] = None
    streak_start_date: Optional[datetime] = None
    times_broken: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Challenge schemas
class ChallengeRequirement(BaseModel):
    """Schema for challenge requirements"""
    type: str  # e.g., "track_expenses", "create_invoices"
    target: Union[int, float]
    period: str  # e.g., "daily", "weekly", "total"


class ChallengeBase(BaseModel):
    """Base schema for challenges"""
    challenge_id: str
    name: str
    description: str
    challenge_type: ChallengeType
    duration_days: int
    requirements: List[ChallengeRequirement]
    reward_xp: int = 0
    reward_badge_url: Optional[str] = None


class ChallengeCreate(ChallengeBase):
    """Schema for creating new challenges"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    organization_id: Optional[int] = None


class ChallengeResponse(ChallengeBase):
    """Schema for challenge API responses"""
    id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserChallengeResponse(BaseModel):
    """Schema for user challenge participation"""
    id: int
    challenge: ChallengeResponse
    progress: float
    is_completed: bool
    opted_in: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    milestones: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Point History schemas
class PointHistoryResponse(BaseModel):
    """Schema for point history API responses"""
    id: int
    action_type: str
    points_awarded: int
    base_points: int
    streak_multiplier: float
    accuracy_bonus: int
    completeness_bonus: int
    timeliness_bonus: int
    action_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Financial Event schemas
class FinancialEvent(BaseModel):
    """Schema for financial events that trigger gamification"""
    user_id: int
    action_type: ActionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    amount: Optional[float] = None


class GamificationResult(BaseModel):
    """Schema for gamification processing results"""
    points_awarded: int
    achievements_unlocked: List[AchievementResponse] = []
    streaks_updated: List[UserStreakResponse] = []
    celebration_triggered: bool = False
    level_up: Optional[Dict[str, Any]] = None
    financial_health_score_change: Optional[float] = None
    challenges_updated: List[Dict[str, Any]] = []


# Organization Configuration schemas
class CustomPointValues(BaseModel):
    """Schema for organization custom point values"""
    expenseTracking: int = Field(ge=1, le=100, default=10)
    invoiceCreation: int = Field(ge=1, le=100, default=15)
    budgetReview: int = Field(ge=1, le=100, default=20)
    receiptUpload: int = Field(ge=1, le=20, default=3)
    categoryAccuracy: int = Field(ge=1, le=20, default=5)
    timelyReminders: int = Field(ge=1, le=50, default=8)
    promptPaymentMarking: int = Field(ge=1, le=50, default=12)


class AchievementThresholds(BaseModel):
    """Schema for organization achievement thresholds"""
    expenseMilestones: List[int] = [10, 50, 100, 500]
    invoiceMilestones: List[int] = [1, 10, 100]
    streakMilestones: List[int] = [7, 30, 90, 365]
    budgetAdherenceThreshold: int = Field(ge=50, le=100, default=90)


class OrganizationFeatures(BaseModel):
    """Schema for organization-enabled features"""
    points: bool = True
    achievements: bool = True
    streaks: bool = True
    challenges: bool = True
    leaderboards: bool = False
    teamChallenges: bool = False
    socialSharing: bool = False
    notifications: bool = True


class TeamSettings(BaseModel):
    """Schema for organization team settings"""
    enableTeamLeaderboards: bool = False
    teamChallengeFrequency: str = Field(pattern="^(weekly|monthly|quarterly)$", default="monthly")
    crossTeamCompetition: bool = False
    teamSizeForChallenges: int = Field(ge=2, le=50, default=5)
    anonymousLeaderboards: bool = True


class PolicyAlignment(BaseModel):
    """Schema for organization policy alignment"""
    expenseCategories: List[str] = []
    receiptRequirements: str = Field(pattern="^(optional|required_over_amount|always_required)$", default="optional")
    budgetEnforcement: Dict[str, Union[bool, int]] = Field(default={
        "enforceStrictLimits": False,
        "warningThreshold": 80,
        "penalizeOverspending": False
    })
    invoiceTimelines: Dict[str, Union[int, List[str]]] = Field(default={
        "reminderFrequency": 7,
        "escalationThreshold": 30,
        "requiredFollowUpActions": []
    })


class OrganizationGamificationConfigBase(BaseModel):
    """Base schema for organization gamification configuration"""
    enabled: bool = True
    custom_point_values: CustomPointValues = Field(default_factory=CustomPointValues)
    achievement_thresholds: AchievementThresholds = Field(default_factory=AchievementThresholds)
    enabled_features: OrganizationFeatures = Field(default_factory=OrganizationFeatures)
    team_settings: TeamSettings = Field(default_factory=TeamSettings)
    policy_alignment: PolicyAlignment = Field(default_factory=PolicyAlignment)


class OrganizationGamificationConfigCreate(OrganizationGamificationConfigBase):
    """Schema for creating organization gamification configuration"""
    organization_id: int


class OrganizationGamificationConfigUpdate(BaseModel):
    """Schema for updating organization gamification configuration"""
    enabled: Optional[bool] = None
    custom_point_values: Optional[CustomPointValues] = None
    achievement_thresholds: Optional[AchievementThresholds] = None
    enabled_features: Optional[OrganizationFeatures] = None
    team_settings: Optional[TeamSettings] = None
    policy_alignment: Optional[PolicyAlignment] = None


class OrganizationGamificationConfigResponse(OrganizationGamificationConfigBase):
    """Schema for organization gamification configuration API responses"""
    id: int
    organization_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dashboard and Analytics schemas
class GamificationDashboard(BaseModel):
    """Schema for gamification dashboard data"""
    profile: UserGamificationProfileResponse
    recent_achievements: List[UserAchievementResponse] = []
    active_streaks: List[UserStreakResponse] = []
    active_challenges: List[UserChallengeResponse] = []
    recent_points: List[PointHistoryResponse] = []
    level_progress: Dict[str, Union[int, float]] = {}
    financial_health_trend: List[Dict[str, Union[datetime, float]]] = []


# Financial Health Score schemas
class FinancialHealthScoreResponse(BaseModel):
    """Schema for financial health score API responses"""
    overall: float
    components: Dict[str, float]
    trend: str  # "improving", "stable", "declining"
    recommendations: List[str]
    last_updated: str  # ISO format datetime
    score_history: List[Dict[str, Union[str, float]]]


class HealthScoreComponentResponse(BaseModel):
    """Schema for health score component information"""
    name: str
    weight: float
    description: str
    recommendations: List[str]


class ModuleStatus(BaseModel):
    """Schema for gamification module status"""
    enabled: bool
    enabled_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None
    data_retention_policy: DataRetentionPolicy
    features: Dict[str, bool]


# API Request/Response schemas
class EnableGamificationRequest(BaseModel):
    """Schema for enabling gamification"""
    data_retention_policy: DataRetentionPolicy = DataRetentionPolicy.PRESERVE
    preferences: Optional[GamificationPreferences] = None


class DisableGamificationRequest(BaseModel):
    """Schema for disabling gamification"""
    data_retention_policy: DataRetentionPolicy = DataRetentionPolicy.PRESERVE


class ProcessFinancialEventRequest(BaseModel):
    """Schema for processing financial events"""
    event: FinancialEvent


class ProcessFinancialEventResponse(BaseModel):
    """Schema for financial event processing response"""
    success: bool
    result: Optional[GamificationResult] = None
    message: str = ""


# Streak-related response schemas
class StreakStatusResponse(BaseModel):
    """Schema for streak status information"""
    habit_type: str
    current_length: int
    longest_length: int
    last_activity: Optional[datetime] = None
    is_active: bool
    risk_level: str
    days_since_activity: int
    times_broken: int
    streak_multiplier: float


class StreakRecoveryResponse(BaseModel):
    """Schema for streak recovery information"""
    habit_type: str
    broken_streak_length: int
    recovery_suggestions: List[str]
    encouragement_message: str
    recovery_challenge_available: bool


class StreakAnalyticsResponse(BaseModel):
    """Schema for streak analytics"""
    total_active_streaks: int
    longest_overall_streak: int
    most_consistent_habit: Optional[str] = None
    habit_strength_scores: Dict[str, float]
    weekly_consistency: Dict[str, float]
    monthly_trends: List[Dict[str, Any]]


class UsersAtRiskResponse(BaseModel):
    """Schema for users at streak risk"""
    risk_level: str
    users_at_risk: List[Dict[str, Any]]
    total_count: int


# Social Features schemas
class AchievementShareBase(BaseModel):
    """Base schema for achievement shares"""
    share_message: Optional[str] = None
    is_public: bool = False


class AchievementShareCreate(AchievementShareBase):
    """Schema for creating achievement shares"""
    user_achievement_id: int


class AchievementShareResponse(AchievementShareBase):
    """Schema for achievement share API responses"""
    id: int
    user_achievement_id: int
    shared_by_user_id: int
    share_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntryBase(BaseModel):
    """Base schema for leaderboard entries"""
    leaderboard_type: str  # "global", "organization", "team"
    scope_id: Optional[int] = None
    is_visible: bool = True
    is_anonymous: bool = False


class LeaderboardEntryResponse(LeaderboardEntryBase):
    """Schema for leaderboard entry API responses"""
    id: int
    profile_id: int
    rank: int
    experience_points: int
    level: int
    rank_change: int
    last_rank_update: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard API responses"""
    leaderboard_type: str
    scope_id: Optional[int] = None
    entries: List[LeaderboardEntryResponse]
    total_entries: int
    user_rank: Optional[int] = None
    user_entry: Optional[LeaderboardEntryResponse] = None
    last_updated: datetime


class UserLeaderboardPosition(BaseModel):
    """Schema for user's position on leaderboard"""
    rank: int
    experience_points: int
    level: int
    rank_change: int
    percentile: float  # User's percentile ranking (0-100)
    entries_ahead: int
    entries_behind: int


class GroupChallengeBase(BaseModel):
    """Base schema for group challenges"""
    challenge_id: int
    group_type: str  # "organization", "team", "custom_group"
    group_id: int
    group_name: str
    description: Optional[str] = None
    max_participants: Optional[int] = None
    group_reward_xp: int = 0
    individual_reward_xp: int = 0


class GroupChallengeCreate(GroupChallengeBase):
    """Schema for creating group challenges"""
    start_date: datetime
    end_date: datetime


class GroupChallengeResponse(GroupChallengeBase):
    """Schema for group challenge API responses"""
    id: int
    current_participants: int
    is_active: bool
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupChallengeParticipantResponse(BaseModel):
    """Schema for group challenge participant"""
    id: int
    group_challenge_id: int
    user_challenge_id: int
    joined_at: datetime
    left_at: Optional[datetime] = None
    is_active: bool
    contribution_points: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupChallengeDetailResponse(GroupChallengeResponse):
    """Schema for detailed group challenge with participants"""
    participants: List[GroupChallengeParticipantResponse] = []
    group_progress: float  # Percentage of group completion
    top_contributors: List[Dict[str, Any]] = []


class SocialFeaturesStatusResponse(BaseModel):
    """Schema for social features status"""
    social_features_enabled: bool
    leaderboards_enabled: bool
    achievement_sharing_enabled: bool
    group_challenges_enabled: bool
    user_social_preferences: Dict[str, bool]


class ShareAchievementRequest(BaseModel):
    """Schema for sharing an achievement"""
    user_achievement_id: int
    share_message: Optional[str] = None
    is_public: bool = False


class ShareAchievementResponse(BaseModel):
    """Schema for achievement share response"""
    success: bool
    share_id: int
    message: str
    share_url: Optional[str] = None


class JoinGroupChallengeRequest(BaseModel):
    """Schema for joining a group challenge"""
    group_challenge_id: int


class JoinGroupChallengeResponse(BaseModel):
    """Schema for joining group challenge response"""
    success: bool
    participant_id: int
    message: str
    group_challenge: GroupChallengeResponse


class LeaveGroupChallengeRequest(BaseModel):
    """Schema for leaving a group challenge"""
    group_challenge_id: int


class LeaveGroupChallengeResponse(BaseModel):
    """Schema for leaving group challenge response"""
    success: bool
    message: str


class UpdateLeaderboardVisibilityRequest(BaseModel):
    """Schema for updating leaderboard visibility"""
    is_visible: bool
    is_anonymous: bool = False


class UpdateLeaderboardVisibilityResponse(BaseModel):
    """Schema for leaderboard visibility update response"""
    success: bool
    message: str
    new_visibility: Dict[str, bool]