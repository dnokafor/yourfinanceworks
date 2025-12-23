"""
Habit Formation Support Service for the gamification system.

This service implements progressive difficulty and habit strength tracking
to help users build lasting financial habits through behavioral psychology principles.

Features:
- Progressive difficulty adaptation based on user performance
- Habit strength tracking and feedback
- Educational content and tips for habit formation
- Adaptive suggestions for struggling users
- Milestone celebrations and recognition
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from core.models.gamification import (
    UserGamificationProfile,
    UserStreak,
    HabitType,
    PointHistory
)

logger = logging.getLogger(__name__)


class HabitDifficulty(str, Enum):
    """Progressive difficulty levels for habits"""
    BEGINNER = "beginner"           # Just starting out
    NOVICE = "novice"               # Building consistency
    INTERMEDIATE = "intermediate"   # Regular performer
    ADVANCED = "advanced"           # Highly consistent
    EXPERT = "expert"               # Exceptional performance


class HabitStrengthLevel(str, Enum):
    """Levels of habit strength"""
    FRAGILE = "fragile"             # 0-20: Very weak, easily broken
    WEAK = "weak"                   # 20-40: Needs reinforcement
    MODERATE = "moderate"           # 40-60: Reasonably consistent
    STRONG = "strong"               # 60-80: Very consistent
    UNBREAKABLE = "unbreakable"     # 80-100: Deeply ingrained


class HabitStrengthScore:
    """Detailed habit strength assessment"""
    def __init__(
        self,
        habit_type: HabitType,
        overall_score: float,  # 0-100
        strength_level: HabitStrengthLevel,
        current_streak: int,
        longest_streak: int,
        consistency_percentage: float,
        days_active: int,
        times_broken: int,
        trend: str,  # "improving", "stable", "declining"
        next_milestone: Optional[int] = None,
        days_to_milestone: Optional[int] = None
    ):
        self.habit_type = habit_type
        self.overall_score = overall_score
        self.strength_level = strength_level
        self.current_streak = current_streak
        self.longest_streak = longest_streak
        self.consistency_percentage = consistency_percentage
        self.days_active = days_active
        self.times_broken = times_broken
        self.trend = trend
        self.next_milestone = next_milestone
        self.days_to_milestone = days_to_milestone


class ProgressiveDifficultyLevel:
    """Configuration for a progressive difficulty level"""
    def __init__(
        self,
        difficulty: HabitDifficulty,
        target_frequency: str,  # e.g., "daily", "weekly"
        expected_streak_length: int,
        point_multiplier: float,
        educational_tips: List[str],
        success_criteria: Dict[str, Any]
    ):
        self.difficulty = difficulty
        self.target_frequency = target_frequency
        self.expected_streak_length = expected_streak_length
        self.point_multiplier = point_multiplier
        self.educational_tips = educational_tips
        self.success_criteria = success_criteria


class AdaptiveHabitSuggestion:
    """Adaptive suggestion for struggling users"""
    def __init__(
        self,
        suggestion_type: str,  # "reduce_frequency", "simplify_task", "add_reminder", "break_into_steps"
        description: str,
        action_items: List[str],
        expected_success_rate: float,  # 0-1
        encouragement_message: str
    ):
        self.suggestion_type = suggestion_type
        self.description = description
        self.action_items = action_items
        self.expected_success_rate = expected_success_rate
        self.encouragement_message = encouragement_message


class HabitFormationSupport:
    """
    Service for supporting habit formation through progressive difficulty
    and adaptive learning strategies.
    """

    # Progressive difficulty configurations
    DIFFICULTY_CONFIGS = {
        HabitType.DAILY_EXPENSE_TRACKING: {
            HabitDifficulty.BEGINNER: {
                "target_frequency": "3-4 times per week",
                "expected_streak_length": 3,
                "point_multiplier": 1.0,
                "educational_tips": [
                    "Start by tracking just your largest expenses",
                    "Use the mobile app for quick entry - it takes less than 30 seconds",
                    "Set a daily reminder at a consistent time",
                    "Keep receipts in one place for easy reference"
                ],
                "success_criteria": {
                    "min_entries_per_week": 3,
                    "min_streak_days": 3,
                    "accuracy_threshold": 0.7
                }
            },
            HabitDifficulty.NOVICE: {
                "target_frequency": "5-6 times per week",
                "expected_streak_length": 7,
                "point_multiplier": 1.2,
                "educational_tips": [
                    "Track all expenses, even small ones",
                    "Categorize expenses as you enter them",
                    "Review your daily spending before bed",
                    "Look for patterns in your spending"
                ],
                "success_criteria": {
                    "min_entries_per_week": 5,
                    "min_streak_days": 7,
                    "accuracy_threshold": 0.85
                }
            },
            HabitDifficulty.INTERMEDIATE: {
                "target_frequency": "daily",
                "expected_streak_length": 30,
                "point_multiplier": 1.5,
                "educational_tips": [
                    "Track expenses immediately after purchase",
                    "Add notes to categorize spending patterns",
                    "Review weekly spending trends",
                    "Set spending goals for each category"
                ],
                "success_criteria": {
                    "min_entries_per_week": 7,
                    "min_streak_days": 30,
                    "accuracy_threshold": 0.95
                }
            },
            HabitDifficulty.ADVANCED: {
                "target_frequency": "daily with analysis",
                "expected_streak_length": 90,
                "point_multiplier": 2.0,
                "educational_tips": [
                    "Analyze spending patterns weekly",
                    "Identify and reduce unnecessary expenses",
                    "Compare spending across months",
                    "Create and stick to monthly budgets"
                ],
                "success_criteria": {
                    "min_entries_per_week": 7,
                    "min_streak_days": 90,
                    "accuracy_threshold": 0.98,
                    "analysis_frequency": "weekly"
                }
            },
            HabitDifficulty.EXPERT: {
                "target_frequency": "daily with advanced analysis",
                "expected_streak_length": 365,
                "point_multiplier": 2.5,
                "educational_tips": [
                    "Use advanced analytics to predict spending",
                    "Optimize spending based on data insights",
                    "Help others develop tracking habits",
                    "Maintain perfect financial records"
                ],
                "success_criteria": {
                    "min_entries_per_week": 7,
                    "min_streak_days": 365,
                    "accuracy_threshold": 0.99,
                    "analysis_frequency": "daily"
                }
            }
        },
        HabitType.WEEKLY_BUDGET_REVIEW: {
            HabitDifficulty.BEGINNER: {
                "target_frequency": "once per week",
                "expected_streak_length": 2,
                "point_multiplier": 1.0,
                "educational_tips": [
                    "Pick a specific day each week for budget review",
                    "Start with a 10-minute quick review",
                    "Focus on just one budget category",
                    "Set a calendar reminder"
                ],
                "success_criteria": {
                    "min_reviews_per_month": 3,
                    "min_streak_weeks": 2,
                    "review_depth": "basic"
                }
            },
            HabitDifficulty.NOVICE: {
                "target_frequency": "weekly",
                "expected_streak_length": 4,
                "point_multiplier": 1.3,
                "educational_tips": [
                    "Review all budget categories weekly",
                    "Compare actual vs. planned spending",
                    "Identify overspending areas",
                    "Adjust budget for next week"
                ],
                "success_criteria": {
                    "min_reviews_per_month": 4,
                    "min_streak_weeks": 4,
                    "review_depth": "comprehensive"
                }
            },
            HabitDifficulty.INTERMEDIATE: {
                "target_frequency": "weekly with analysis",
                "expected_streak_length": 12,
                "point_multiplier": 1.6,
                "educational_tips": [
                    "Analyze spending trends over weeks",
                    "Identify seasonal spending patterns",
                    "Create realistic budget adjustments",
                    "Track progress toward financial goals"
                ],
                "success_criteria": {
                    "min_reviews_per_month": 4,
                    "min_streak_weeks": 12,
                    "review_depth": "analytical"
                }
            },
            HabitDifficulty.ADVANCED: {
                "target_frequency": "weekly with forecasting",
                "expected_streak_length": 26,
                "point_multiplier": 2.0,
                "educational_tips": [
                    "Forecast spending for upcoming weeks",
                    "Adjust budgets based on predictions",
                    "Optimize spending across categories",
                    "Plan for irregular expenses"
                ],
                "success_criteria": {
                    "min_reviews_per_month": 4,
                    "min_streak_weeks": 26,
                    "review_depth": "predictive"
                }
            },
            HabitDifficulty.EXPERT: {
                "target_frequency": "weekly with optimization",
                "expected_streak_length": 52,
                "point_multiplier": 2.5,
                "educational_tips": [
                    "Optimize budget allocation for maximum savings",
                    "Implement advanced financial strategies",
                    "Mentor others on budget management",
                    "Maintain perfect budget adherence"
                ],
                "success_criteria": {
                    "min_reviews_per_month": 4,
                    "min_streak_weeks": 52,
                    "review_depth": "expert",
                    "budget_adherence": 0.95
                }
            }
        },
        HabitType.INVOICE_FOLLOW_UP: {
            HabitDifficulty.BEGINNER: {
                "target_frequency": "2-3 times per week",
                "expected_streak_length": 5,
                "point_multiplier": 1.0,
                "educational_tips": [
                    "Set a reminder to check invoices twice a week",
                    "Start with just overdue invoices",
                    "Use templates for follow-up messages",
                    "Track which invoices need attention"
                ],
                "success_criteria": {
                    "min_follow_ups_per_week": 2,
                    "min_streak_days": 5,
                    "response_rate": 0.5
                }
            },
            HabitDifficulty.NOVICE: {
                "target_frequency": "3-4 times per week",
                "expected_streak_length": 10,
                "point_multiplier": 1.2,
                "educational_tips": [
                    "Follow up on invoices within 3 days of due date",
                    "Personalize follow-up messages",
                    "Track payment status for each invoice",
                    "Document follow-up attempts"
                ],
                "success_criteria": {
                    "min_follow_ups_per_week": 3,
                    "min_streak_days": 10,
                    "response_rate": 0.7
                }
            },
            HabitDifficulty.INTERMEDIATE: {
                "target_frequency": "daily",
                "expected_streak_length": 25,
                "point_multiplier": 1.5,
                "educational_tips": [
                    "Check invoices daily for payment status",
                    "Send proactive reminders before due dates",
                    "Analyze payment patterns by client",
                    "Implement escalation procedures"
                ],
                "success_criteria": {
                    "min_follow_ups_per_week": 5,
                    "min_streak_days": 25,
                    "response_rate": 0.85
                }
            },
            HabitDifficulty.ADVANCED: {
                "target_frequency": "daily with analysis",
                "expected_streak_length": 50,
                "point_multiplier": 2.0,
                "educational_tips": [
                    "Predict payment delays based on client history",
                    "Optimize follow-up timing for each client",
                    "Implement automated reminders",
                    "Reduce days sales outstanding (DSO)"
                ],
                "success_criteria": {
                    "min_follow_ups_per_week": 5,
                    "min_streak_days": 50,
                    "response_rate": 0.95,
                    "avg_dso": 30
                }
            },
            HabitDifficulty.EXPERT: {
                "target_frequency": "daily with optimization",
                "expected_streak_length": 100,
                "point_multiplier": 2.5,
                "educational_tips": [
                    "Maintain near-perfect payment collection rates",
                    "Mentor others on invoice management",
                    "Implement advanced collection strategies",
                    "Minimize bad debt write-offs"
                ],
                "success_criteria": {
                    "min_follow_ups_per_week": 5,
                    "min_streak_days": 100,
                    "response_rate": 0.98,
                    "avg_dso": 15
                }
            }
        },
        HabitType.RECEIPT_DOCUMENTATION: {
            HabitDifficulty.BEGINNER: {
                "target_frequency": "3-4 times per week",
                "expected_streak_length": 3,
                "point_multiplier": 1.0,
                "educational_tips": [
                    "Save receipts immediately after purchase",
                    "Use the mobile app to photograph receipts",
                    "Store receipts in a designated folder",
                    "Set a weekly reminder to organize receipts"
                ],
                "success_criteria": {
                    "min_receipts_per_week": 3,
                    "min_streak_days": 3,
                    "documentation_rate": 0.6
                }
            },
            HabitDifficulty.NOVICE: {
                "target_frequency": "5-6 times per week",
                "expected_streak_length": 7,
                "point_multiplier": 1.2,
                "educational_tips": [
                    "Document all business expenses with receipts",
                    "Add notes about the business purpose",
                    "Categorize receipts by expense type",
                    "Keep digital and physical copies"
                ],
                "success_criteria": {
                    "min_receipts_per_week": 5,
                    "min_streak_days": 7,
                    "documentation_rate": 0.8
                }
            },
            HabitDifficulty.INTERMEDIATE: {
                "target_frequency": "daily",
                "expected_streak_length": 30,
                "point_multiplier": 1.5,
                "educational_tips": [
                    "Document receipts within 24 hours of purchase",
                    "Extract key information (date, amount, vendor)",
                    "Link receipts to corresponding expenses",
                    "Maintain organized filing system"
                ],
                "success_criteria": {
                    "min_receipts_per_week": 7,
                    "min_streak_days": 30,
                    "documentation_rate": 0.95
                }
            },
            HabitDifficulty.ADVANCED: {
                "target_frequency": "daily with analysis",
                "expected_streak_length": 90,
                "point_multiplier": 2.0,
                "educational_tips": [
                    "Analyze receipt data for spending insights",
                    "Identify duplicate or fraudulent charges",
                    "Track vendor relationships and pricing",
                    "Optimize expense reimbursement process"
                ],
                "success_criteria": {
                    "min_receipts_per_week": 7,
                    "min_streak_days": 90,
                    "documentation_rate": 0.98,
                    "audit_readiness": "high"
                }
            },
            HabitDifficulty.EXPERT: {
                "target_frequency": "daily with advanced analysis",
                "expected_streak_length": 365,
                "point_multiplier": 2.5,
                "educational_tips": [
                    "Maintain perfect receipt documentation",
                    "Implement advanced compliance procedures",
                    "Mentor others on expense management",
                    "Achieve audit-ready status consistently"
                ],
                "success_criteria": {
                    "min_receipts_per_week": 7,
                    "min_streak_days": 365,
                    "documentation_rate": 0.99,
                    "audit_readiness": "perfect"
                }
            }
        }
    }

    def __init__(self, db: Session):
        self.db = db

    async def get_habit_difficulty(
        self,
        user_id: int,
        habit_type: HabitType
    ) -> HabitDifficulty:
        """
        Determine the appropriate difficulty level for a user's habit.
        
        Args:
            user_id: User ID
            habit_type: Type of habit
            
        Returns:
            Current difficulty level
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return HabitDifficulty.BEGINNER

            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type
                )
            ).first()

            if not streak:
                return HabitDifficulty.BEGINNER

            # Determine difficulty based on streak and performance
            if streak.longest_length >= 365:
                return HabitDifficulty.EXPERT
            elif streak.longest_length >= 90:
                return HabitDifficulty.ADVANCED
            elif streak.longest_length >= 30:
                return HabitDifficulty.INTERMEDIATE
            elif streak.longest_length >= 7:
                return HabitDifficulty.NOVICE
            else:
                return HabitDifficulty.BEGINNER

        except Exception as e:
            logger.error(f"Error determining habit difficulty: {str(e)}")
            return HabitDifficulty.BEGINNER

    async def calculate_habit_strength(
        self,
        user_id: int,
        habit_type: HabitType
    ) -> HabitStrengthScore:
        """
        Calculate comprehensive habit strength score.
        
        Args:
            user_id: User ID
            habit_type: Type of habit
            
        Returns:
            Detailed habit strength assessment
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return self._create_empty_strength_score(habit_type)

            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type
                )
            ).first()

            if not streak:
                return self._create_empty_strength_score(habit_type)

            # Calculate consistency percentage
            consistency_pct = await self._calculate_consistency_percentage(streak)
            
            # Calculate days active
            days_active = await self._calculate_days_active(streak)
            
            # Calculate overall score (0-100)
            overall_score = await self._calculate_overall_strength_score(
                streak, consistency_pct, days_active
            )
            
            # Determine strength level
            strength_level = self._get_strength_level(overall_score)
            
            # Calculate trend
            trend = await self._calculate_trend(profile.id, habit_type)
            
            # Calculate next milestone
            next_milestone, days_to_milestone = await self._calculate_next_milestone(
                streak, habit_type
            )

            return HabitStrengthScore(
                habit_type=habit_type,
                overall_score=overall_score,
                strength_level=strength_level,
                current_streak=streak.current_length,
                longest_streak=streak.longest_length,
                consistency_percentage=consistency_pct,
                days_active=days_active,
                times_broken=streak.times_broken,
                trend=trend,
                next_milestone=next_milestone,
                days_to_milestone=days_to_milestone
            )

        except Exception as e:
            logger.error(f"Error calculating habit strength: {str(e)}")
            return self._create_empty_strength_score(habit_type)

    async def get_educational_content(
        self,
        habit_type: HabitType,
        difficulty: HabitDifficulty
    ) -> Dict[str, Any]:
        """
        Get educational content and tips for a habit at a specific difficulty level.
        
        Args:
            habit_type: Type of habit
            difficulty: Current difficulty level
            
        Returns:
            Educational content and tips
        """
        try:
            config = self.DIFFICULTY_CONFIGS.get(habit_type, {}).get(difficulty)
            
            if not config:
                return {
                    "tips": [],
                    "target_frequency": "regular",
                    "success_criteria": {}
                }

            return {
                "tips": config.get("educational_tips", []),
                "target_frequency": config.get("target_frequency", ""),
                "expected_streak_length": config.get("expected_streak_length", 0),
                "success_criteria": config.get("success_criteria", {}),
                "point_multiplier": config.get("point_multiplier", 1.0)
            }

        except Exception as e:
            logger.error(f"Error getting educational content: {str(e)}")
            return {"tips": [], "target_frequency": "", "success_criteria": {}}

    async def get_adaptive_suggestions(
        self,
        user_id: int,
        habit_type: HabitType
    ) -> List[AdaptiveHabitSuggestion]:
        """
        Get adaptive suggestions for users struggling with habit formation.
        
        Args:
            user_id: User ID
            habit_type: Type of habit
            
        Returns:
            List of adaptive suggestions
        """
        try:
            strength_score = await self.calculate_habit_strength(user_id, habit_type)
            suggestions = []

            # If habit strength is low, provide adaptive suggestions
            if strength_score.overall_score < 40:
                # Suggest reducing frequency
                if strength_score.times_broken > 2:
                    suggestions.append(AdaptiveHabitSuggestion(
                        suggestion_type="reduce_frequency",
                        description="Your habit has been broken multiple times. Let's reduce the frequency to build momentum.",
                        action_items=[
                            "Focus on 3-4 times per week instead of daily",
                            "Pick your strongest days of the week",
                            "Build up gradually as you gain confidence"
                        ],
                        expected_success_rate=0.75,
                        encouragement_message="Starting smaller often leads to bigger success!"
                    ))

                # Suggest simplifying the task
                if strength_score.consistency_percentage < 50:
                    suggestions.append(AdaptiveHabitSuggestion(
                        suggestion_type="simplify_task",
                        description="Let's simplify the task to make it easier to complete.",
                        action_items=[
                            "Focus on just the essentials",
                            "Use templates or shortcuts",
                            "Break the task into smaller steps"
                        ],
                        expected_success_rate=0.80,
                        encouragement_message="Simplicity is the key to consistency!"
                    ))

                # Suggest adding reminders
                suggestions.append(AdaptiveHabitSuggestion(
                    suggestion_type="add_reminder",
                    description="Set up reminders to help you remember.",
                    action_items=[
                        "Enable push notifications",
                        "Set a specific time each day",
                        "Use your phone's calendar app"
                    ],
                    expected_success_rate=0.70,
                    encouragement_message="A little nudge can make all the difference!"
                ))

            return suggestions

        except Exception as e:
            logger.error(f"Error getting adaptive suggestions: {str(e)}")
            return []

    async def get_milestone_celebration(
        self,
        user_id: int,
        habit_type: HabitType,
        current_streak: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get milestone celebration content when user reaches a milestone.
        
        Args:
            user_id: User ID
            habit_type: Type of habit
            current_streak: Current streak length
            
        Returns:
            Celebration content or None if no milestone reached
        """
        try:
            milestones = {
                HabitType.DAILY_EXPENSE_TRACKING: [7, 14, 30, 60, 90, 180, 365],
                HabitType.WEEKLY_BUDGET_REVIEW: [4, 8, 12, 26, 52],
                HabitType.INVOICE_FOLLOW_UP: [10, 25, 50, 100],
                HabitType.RECEIPT_DOCUMENTATION: [7, 30, 90, 365]
            }

            habit_milestones = milestones.get(habit_type, [])
            
            if current_streak not in habit_milestones:
                return None

            # Generate celebration content
            celebration_messages = {
                7: "🎉 Week Warrior! You've maintained this habit for a full week!",
                14: "🚀 Two weeks strong! Your consistency is impressive!",
                30: "🏆 Month Master! You've built a solid habit!",
                60: "💪 Two months! You're unstoppable!",
                90: "👑 Quarter Champion! This is becoming second nature!",
                180: "🌟 Half-year hero! Your dedication is inspiring!",
                365: "🎊 Year Legend! You've achieved the ultimate milestone!"
            }

            message = celebration_messages.get(current_streak, f"🎉 {current_streak}-day milestone!")

            return {
                "milestone_reached": current_streak,
                "celebration_message": message,
                "bonus_points": self._calculate_milestone_bonus(current_streak),
                "achievement_unlocked": True,
                "special_effects": "confetti"
            }

        except Exception as e:
            logger.error(f"Error getting milestone celebration: {str(e)}")
            return None

    # Private helper methods

    def _create_empty_strength_score(self, habit_type: HabitType) -> HabitStrengthScore:
        """Create an empty strength score for new habits"""
        return HabitStrengthScore(
            habit_type=habit_type,
            overall_score=0.0,
            strength_level=HabitStrengthLevel.FRAGILE,
            current_streak=0,
            longest_streak=0,
            consistency_percentage=0.0,
            days_active=0,
            times_broken=0,
            trend="stable",
            next_milestone=7,
            days_to_milestone=7
        )

    async def _calculate_consistency_percentage(self, streak: UserStreak) -> float:
        """Calculate consistency percentage for a streak"""
        try:
            if not streak.streak_start_date or streak.current_length == 0:
                return 0.0

            now = datetime.now(timezone.utc)
            start_date = streak.streak_start_date
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            days_elapsed = (now - start_date).days + 1
            
            if days_elapsed == 0:
                return 0.0

            consistency = (streak.current_length / days_elapsed) * 100
            return min(100.0, consistency)

        except Exception as e:
            logger.error(f"Error calculating consistency: {str(e)}")
            return 0.0

    async def _calculate_days_active(self, streak: UserStreak) -> int:
        """Calculate total days the habit has been active"""
        try:
            if not streak.streak_start_date:
                return 0

            now = datetime.now(timezone.utc)
            start_date = streak.streak_start_date
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            return (now - start_date).days + 1

        except Exception as e:
            logger.error(f"Error calculating days active: {str(e)}")
            return 0

    async def _calculate_overall_strength_score(
        self,
        streak: UserStreak,
        consistency_pct: float,
        days_active: int
    ) -> float:
        """Calculate overall habit strength score (0-100)"""
        try:
            # Current streak contribution (max 40 points)
            streak_score = min(40, (streak.current_length / 30) * 40)
            
            # Consistency contribution (max 35 points)
            consistency_score = consistency_pct * 0.35
            
            # Longevity contribution (max 15 points)
            longevity_score = min(15, (days_active / 365) * 15)
            
            # Break penalty (max -10 points)
            break_penalty = min(10, streak.times_broken * 2)
            
            total_score = streak_score + consistency_score + longevity_score - break_penalty
            return max(0.0, min(100.0, total_score))

        except Exception as e:
            logger.error(f"Error calculating overall strength score: {str(e)}")
            return 0.0

    def _get_strength_level(self, score: float) -> HabitStrengthLevel:
        """Determine strength level from score"""
        if score < 20:
            return HabitStrengthLevel.FRAGILE
        elif score < 40:
            return HabitStrengthLevel.WEAK
        elif score < 60:
            return HabitStrengthLevel.MODERATE
        elif score < 80:
            return HabitStrengthLevel.STRONG
        else:
            return HabitStrengthLevel.UNBREAKABLE

    async def _calculate_trend(self, profile_id: int, habit_type: HabitType) -> str:
        """Calculate trend in habit performance"""
        try:
            # Get point history for the last 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            recent_points = self.db.query(func.sum(PointHistory.points_awarded)).filter(
                and_(
                    PointHistory.profile_id == profile_id,
                    PointHistory.created_at >= thirty_days_ago
                )
            ).scalar() or 0

            # Get point history for 30-60 days ago
            sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
            previous_points = self.db.query(func.sum(PointHistory.points_awarded)).filter(
                and_(
                    PointHistory.profile_id == profile_id,
                    PointHistory.created_at >= sixty_days_ago,
                    PointHistory.created_at < thirty_days_ago
                )
            ).scalar() or 0

            if previous_points == 0:
                return "stable"
            
            change_pct = ((recent_points - previous_points) / previous_points) * 100
            
            if change_pct > 10:
                return "improving"
            elif change_pct < -10:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return "stable"

    async def _calculate_next_milestone(
        self,
        streak: UserStreak,
        habit_type: HabitType
    ) -> Tuple[Optional[int], Optional[int]]:
        """Calculate next milestone and days to reach it"""
        try:
            milestones = {
                HabitType.DAILY_EXPENSE_TRACKING: [7, 14, 30, 60, 90, 180, 365],
                HabitType.WEEKLY_BUDGET_REVIEW: [4, 8, 12, 26, 52],
                HabitType.INVOICE_FOLLOW_UP: [10, 25, 50, 100],
                HabitType.RECEIPT_DOCUMENTATION: [7, 30, 90, 365]
            }

            habit_milestones = milestones.get(habit_type, [])
            
            for milestone in habit_milestones:
                if streak.current_length < milestone:
                    days_to_milestone = milestone - streak.current_length
                    return milestone, days_to_milestone

            # All milestones reached
            return None, None

        except Exception as e:
            logger.error(f"Error calculating next milestone: {str(e)}")
            return None, None

    def _calculate_milestone_bonus(self, milestone: int) -> int:
        """Calculate bonus points for reaching a milestone"""
        bonus_map = {
            7: 50,
            14: 75,
            30: 150,
            60: 200,
            90: 300,
            180: 500,
            365: 1000,
            4: 100,
            8: 150,
            12: 250,
            26: 400,
            52: 750,
            10: 100,
            25: 200,
            50: 400,
            100: 750
        }
        return bonus_map.get(milestone, 50)
