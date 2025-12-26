/**
 * TypeScript interfaces and types for the gamification system.
 * 
 * This module contains all type definitions for the gamification features,
 * including user profiles, achievements, streaks, challenges, and API responses.
 */

// Enums
export enum DataRetentionPolicy {
  PRESERVE = 'preserve',
  ARCHIVE = 'archive',
  DELETE = 'delete'
}

export enum HabitType {
  DAILY_EXPENSE_TRACKING = 'daily_expense_tracking',
  WEEKLY_BUDGET_REVIEW = 'weekly_budget_review',
  INVOICE_FOLLOW_UP = 'invoice_follow_up',
  RECEIPT_DOCUMENTATION = 'receipt_documentation'
}

export enum AchievementCategory {
  EXPENSE_TRACKING = 'expense_tracking',
  INVOICE_MANAGEMENT = 'invoice_management',
  HABIT_FORMATION = 'habit_formation',
  FINANCIAL_HEALTH = 'financial_health',
  EXPLORATION = 'exploration'
}

export enum AchievementDifficulty {
  BRONZE = 'bronze',
  SILVER = 'silver',
  GOLD = 'gold',
  PLATINUM = 'platinum'
}

export enum ChallengeType {
  PERSONAL = 'personal',
  COMMUNITY = 'community',
  SEASONAL = 'seasonal'
}

export enum NotificationFrequency {
  IMMEDIATE = 'immediate',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  DISABLED = 'disabled'
}

export enum ActionType {
  EXPENSE_ADDED = 'expense_added',
  INVOICE_CREATED = 'invoice_created',
  RECEIPT_UPLOADED = 'receipt_uploaded',
  BUDGET_REVIEWED = 'budget_reviewed',
  PAYMENT_RECORDED = 'payment_recorded',
  CATEGORY_ASSIGNED = 'category_assigned'
}

// Base interfaces
export interface GamificationPreferences {
  features: {
    points: boolean;
    achievements: boolean;
    streaks: boolean;
    challenges: boolean;
    social: boolean;
    notifications: boolean;
  };
  privacy: {
    shareAchievements: boolean;
    showOnLeaderboard: boolean;
    allowFriendRequests: boolean;
  };
  notifications: {
    streakReminders: boolean;
    achievementCelebrations: boolean;
    challengeUpdates: boolean;
    frequency: NotificationFrequency;
  };
}

export interface UserStatistics {
  totalActionsCompleted: number;
  expensesTracked: number;
  invoicesCreated: number;
  receiptsUploaded: number;
  budgetReviews: number;
  longestStreak: number;
  achievementsUnlocked: number;
  challengesCompleted: number;
}

// User Gamification Profile
export interface UserGamificationProfile {
  id: number;
  user_id: number;
  module_enabled: boolean;
  level: number;
  total_experience_points: number;
  current_level_progress: number;
  financial_health_score: number;
  preferences: GamificationPreferences;
  statistics: UserStatistics;
  data_retention_policy: DataRetentionPolicy;
  enabled_at?: string;
  disabled_at?: string;
  created_at: string;
  updated_at: string;
}

// Achievement interfaces
export interface AchievementRequirement {
  type: string;
  target: number;
  period?: string;
}

export interface Achievement {
  id: number;
  achievement_id: string;
  name: string;
  description: string;
  category: AchievementCategory;
  difficulty: AchievementDifficulty;
  requirements: AchievementRequirement[];
  reward_xp: number;
  reward_badge_url?: string;
  is_hidden: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserAchievement {
  id: number;
  achievement: Achievement;
  progress: number;
  is_completed: boolean;
  unlocked_at?: string;
  created_at: string;
  updated_at: string;
}

// Streak interfaces
export interface UserStreak {
  id: number;
  habit_type: HabitType;
  current_length: number;
  longest_length: number;
  is_active: boolean;
  last_activity_date?: string;
  streak_start_date?: string;
  times_broken: number;
  created_at: string;
  updated_at: string;
}

// Challenge interfaces
export interface ChallengeRequirement {
  type: string;
  target: number;
  period: string;
}

export interface Challenge {
  id: number;
  challenge_id: string;
  name: string;
  description: string;
  challenge_type: ChallengeType;
  duration_days: number;
  requirements: ChallengeRequirement[];
  reward_xp: number;
  reward_badge_url?: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  organization_id?: number;
  created_at: string;
  updated_at: string;
}

export interface UserChallenge {
  id: number;
  challenge: Challenge;
  progress: number;
  is_completed: boolean;
  opted_in: boolean;
  started_at: string;
  completed_at?: string;
  milestones: Record<string, any>[];
  created_at: string;
  updated_at: string;
}

// Point History
export interface PointHistory {
  id: number;
  action_type: string;
  points_awarded: number;
  base_points: number;
  streak_multiplier: number;
  accuracy_bonus: number;
  completeness_bonus: number;
  action_metadata?: Record<string, any>;
  created_at: string;
}

// Financial Event
export interface FinancialEvent {
  user_id: number;
  action_type: ActionType;
  timestamp: string;
  metadata: Record<string, any>;
  category?: string;
  amount?: number;
}

// Gamification Result
export interface GamificationResult {
  points_awarded: number;
  achievements_unlocked: Achievement[];
  streaks_updated: UserStreak[];
  celebration_triggered: boolean;
  level_up?: {
    old_level: number;
    new_level: number;
    xp_to_next: number;
  };
  financial_health_score_change?: number;
}

// Organization Configuration
export interface CustomPointValues {
  expenseTracking: number;
  invoiceCreation: number;
  budgetReview: number;
  receiptUpload: number;
  categoryAccuracy: number;
  timelyReminders: number;
  promptPaymentMarking: number;
}

export interface AchievementThresholds {
  expenseMilestones: number[];
  invoiceMilestones: number[];
  streakMilestones: number[];
  budgetAdherenceThreshold: number;
}

export interface OrganizationFeatures {
  points: boolean;
  achievements: boolean;
  streaks: boolean;
  challenges: boolean;
  leaderboards: boolean;
  teamChallenges: boolean;
  socialSharing: boolean;
  notifications: boolean;
}

export interface TeamSettings {
  enableTeamLeaderboards: boolean;
  teamChallengeFrequency: 'weekly' | 'monthly' | 'quarterly';
  crossTeamCompetition: boolean;
  teamSizeForChallenges: number;
  anonymousLeaderboards: boolean;
}

export interface PolicyAlignment {
  expenseCategories: string[];
  receiptRequirements: 'optional' | 'required_over_amount' | 'always_required';
  budgetEnforcement: {
    enforceStrictLimits: boolean;
    warningThreshold: number;
    penalizeOverspending: boolean;
  };
  invoiceTimelines: {
    reminderFrequency: number;
    escalationThreshold: number;
    requiredFollowUpActions: string[];
  };
}

export interface OrganizationGamificationConfig {
  id: number;
  organization_id: number;
  enabled: boolean;
  custom_point_values: CustomPointValues;
  achievement_thresholds: AchievementThresholds;
  enabled_features: OrganizationFeatures;
  team_settings: TeamSettings;
  policy_alignment: PolicyAlignment;
  created_by?: number;
  updated_by?: number;
  created_at: string;
  updated_at: string;
}

// Dashboard and Analytics
export interface LevelProgress {
  current_level: number;
  total_xp: number;
  xp_progress: number;
  xp_needed: number;
  progress_percentage: number;
}

export interface FinancialHealthTrend {
  date: string;
  score: number;
}

export interface GamificationDashboard {
  profile: UserGamificationProfile;
  recent_achievements: UserAchievement[];
  active_streaks: UserStreak[];
  active_challenges: UserChallenge[];
  recent_points: PointHistory[];
  level_progress: LevelProgress;
  financial_health_trend: FinancialHealthTrend[];
}

// Module Status
export interface ModuleStatus {
  enabled: boolean;
  enabled_at?: string;
  disabled_at?: string;
  data_retention_policy: DataRetentionPolicy;
  features: Record<string, boolean>;
}

// API Request/Response types
export interface EnableGamificationRequest {
  data_retention_policy?: DataRetentionPolicy;
  preferences?: GamificationPreferences;
}

export interface DisableGamificationRequest {
  data_retention_policy: DataRetentionPolicy;
}

export interface ProcessFinancialEventRequest {
  event: FinancialEvent;
}

export interface ProcessFinancialEventResponse {
  success: boolean;
  result?: GamificationResult;
  message: string;
}

export interface ValidationResult {
  user_id: number;
  profile_exists: boolean;
  module_enabled: boolean;
  data_consistent: boolean;
  issues: string[];
}

// UI Component Props
export interface GamificationToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean, policy?: DataRetentionPolicy) => void;
  loading?: boolean;
}

export interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

export interface AchievementBadgeProps {
  achievement: Achievement;
  unlocked: boolean;
  progress?: number;
  size?: 'small' | 'medium' | 'large';
}

export interface StreakIndicatorProps {
  streak: UserStreak;
  showDetails?: boolean;
}

export interface ChallengeCardProps {
  challenge: UserChallenge;
  onOptIn?: (challengeId: number) => void;
  onOptOut?: (challengeId: number) => void;
}

export interface FinancialHealthScoreProps {
  score: number;
  trend: FinancialHealthTrend[];
  showTrend?: boolean;
}

export interface CelebrationProps {
  type: 'achievement' | 'level_up' | 'streak_milestone';
  data: Achievement | { old_level: number; new_level: number } | UserStreak;
  onClose: () => void;
}

// Utility types
export type GamificationFeature = keyof GamificationPreferences['features'];
export type PrivacySetting = keyof GamificationPreferences['privacy'];
export type NotificationSetting = keyof GamificationPreferences['notifications'];

// API Client interface
export interface GamificationApiClient {
  getStatus(): Promise<ModuleStatus>;
  enable(request: EnableGamificationRequest): Promise<UserGamificationProfile>;
  disable(request: DisableGamificationRequest): Promise<void>;
  getProfile(): Promise<UserGamificationProfile | null>;
  updatePreferences(preferences: GamificationPreferences): Promise<UserGamificationProfile>;
  getDashboard(): Promise<GamificationDashboard | null>;
  processEvent(request: ProcessFinancialEventRequest): Promise<ProcessFinancialEventResponse>;
  validate(): Promise<ValidationResult>;
}

// Hook return types
export interface UseGamificationReturn {
  profile: UserGamificationProfile | null;
  status: ModuleStatus;
  dashboard: GamificationDashboard | null;
  loading: boolean;
  error: string | null;
  enable: (request: EnableGamificationRequest) => Promise<void>;
  disable: (request: DisableGamificationRequest) => Promise<void>;
  updatePreferences: (preferences: GamificationPreferences) => Promise<void>;
  processEvent: (event: FinancialEvent) => Promise<GamificationResult | null>;
  refresh: () => Promise<void>;
}

// Context types
export interface GamificationContextValue extends UseGamificationReturn {
  isEnabled: boolean;
  canShowGamification: boolean;
}

// Default values
export const DEFAULT_GAMIFICATION_PREFERENCES: GamificationPreferences = {
  features: {
    points: true,
    achievements: true,
    streaks: true,
    challenges: true,
    social: false,
    notifications: true
  },
  privacy: {
    shareAchievements: false,
    showOnLeaderboard: false,
    allowFriendRequests: false
  },
  notifications: {
    streakReminders: true,
    achievementCelebrations: true,
    challengeUpdates: true,
    frequency: NotificationFrequency.DAILY
  }
};

export const DEFAULT_USER_STATISTICS: UserStatistics = {
  totalActionsCompleted: 0,
  expensesTracked: 0,
  invoicesCreated: 0,
  receiptsUploaded: 0,
  budgetReviews: 0,
  longestStreak: 0,
  achievementsUnlocked: 0,
  challengesCompleted: 0
};