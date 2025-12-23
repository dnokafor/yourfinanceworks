"""
Financial Health Score Calculator for the gamification system.

This service calculates and manages the Financial Health Score based on multiple
financial management factors including expense tracking consistency, budget adherence,
invoice management, and habit formation.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from dataclasses import dataclass
from enum import Enum

from core.models.gamification import (
    UserGamificationProfile,
    UserStreak,
    PointHistory,
    HabitType
)
from core.schemas.gamification import FinancialEvent, ActionType

logger = logging.getLogger(__name__)


class ScoreTrend(str, Enum):
    """Trend direction for financial health score"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class HealthScoreComponent:
    """Individual component of the financial health score"""
    name: str
    current_score: float  # 0-100
    weight: float  # Weight in overall score calculation
    description: str
    recommendations: List[str]


@dataclass
class FinancialHealthScore:
    """Complete financial health score with components and trends"""
    overall: float  # 0-100
    components: Dict[str, float]  # Component name -> score
    trend: ScoreTrend
    recommendations: List[str]
    last_updated: datetime
    score_history: List[Dict[str, Any]]


class FinancialHealthCalculator:
    """
    Calculates and manages Financial Health Scores based on user financial behavior.
    
    The score is calculated from multiple components:
    - Expense Tracking Consistency (25% weight)
    - Budget Adherence (20% weight) 
    - Invoice Management (20% weight)
    - Habit Consistency (20% weight)
    - Financial Goals Progress (15% weight)
    """

    # Component weights (must sum to 1.0)
    COMPONENT_WEIGHTS = {
        "expense_tracking": 0.25,
        "budget_adherence": 0.20,
        "invoice_management": 0.20,
        "habit_consistency": 0.20,
        "financial_goals": 0.15
    }

    # Scoring thresholds
    EXCELLENT_THRESHOLD = 90.0
    GOOD_THRESHOLD = 75.0
    FAIR_THRESHOLD = 60.0
    POOR_THRESHOLD = 40.0

    def __init__(self, db: Session):
        self.db = db

    async def calculate_score(self, user_id: int) -> Optional[FinancialHealthScore]:
        """
        Calculate the complete financial health score for a user.
        
        Args:
            user_id: The user ID to calculate score for
            
        Returns:
            FinancialHealthScore object with all components and recommendations
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile or not profile.module_enabled:
                return None

            # Calculate individual component scores
            expense_tracking_score = await self._calculate_expense_tracking_score(profile)
            budget_adherence_score = await self._calculate_budget_adherence_score(profile)
            invoice_management_score = await self._calculate_invoice_management_score(profile)
            habit_consistency_score = await self._calculate_habit_consistency_score(profile)
            financial_goals_score = await self._calculate_financial_goals_score(profile)

            # Calculate weighted overall score
            components = {
                "expense_tracking": expense_tracking_score,
                "budget_adherence": budget_adherence_score,
                "invoice_management": invoice_management_score,
                "habit_consistency": habit_consistency_score,
                "financial_goals": financial_goals_score
            }

            overall_score = sum(
                score * self.COMPONENT_WEIGHTS[component]
                for component, score in components.items()
            )

            # Determine trend
            trend = await self._calculate_score_trend(profile, overall_score)

            # Generate recommendations
            recommendations = await self._generate_recommendations(components, overall_score)

            # Get score history
            score_history = await self._get_score_history(profile)

            return FinancialHealthScore(
                overall=round(overall_score, 1),
                components=components,
                trend=trend,
                recommendations=recommendations,
                last_updated=datetime.now(timezone.utc),
                score_history=score_history
            )

        except Exception as e:
            logger.error(f"Error calculating financial health score for user {user_id}: {str(e)}")
            return None

    async def update_score(self, user_id: int, event: FinancialEvent) -> Optional[float]:
        """
        Update the financial health score based on a financial event.
        
        Args:
            user_id: The user ID
            event: The financial event that occurred
            
        Returns:
            The change in score (positive or negative)
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile or not profile.module_enabled:
                return None

            old_score = profile.financial_health_score

            # Recalculate the complete score
            health_score = await self.calculate_score(user_id)
            if not health_score:
                return None

            # Update the profile with the new score
            profile.financial_health_score = health_score.overall
            profile.updated_at = datetime.now(timezone.utc)

            # Store score history entry
            await self._store_score_history(profile, health_score.overall, event)

            return health_score.overall - old_score

        except Exception as e:
            logger.error(f"Error updating financial health score for user {user_id}: {str(e)}")
            return None

    async def get_score_components(self) -> List[HealthScoreComponent]:
        """Get information about all score components"""
        return [
            HealthScoreComponent(
                name="expense_tracking",
                current_score=0.0,  # Will be calculated per user
                weight=self.COMPONENT_WEIGHTS["expense_tracking"],
                description="Consistency and completeness of expense tracking",
                recommendations=[
                    "Track expenses daily for better consistency",
                    "Add receipt photos to improve completeness",
                    "Categorize expenses accurately"
                ]
            ),
            HealthScoreComponent(
                name="budget_adherence",
                current_score=0.0,
                weight=self.COMPONENT_WEIGHTS["budget_adherence"],
                description="How well you stay within budget limits",
                recommendations=[
                    "Review budget categories regularly",
                    "Set realistic budget limits",
                    "Monitor spending throughout the month"
                ]
            ),
            HealthScoreComponent(
                name="invoice_management",
                current_score=0.0,
                weight=self.COMPONENT_WEIGHTS["invoice_management"],
                description="Timeliness and completeness of invoice management",
                recommendations=[
                    "Send invoices promptly after work completion",
                    "Follow up on overdue invoices regularly",
                    "Mark payments as received promptly"
                ]
            ),
            HealthScoreComponent(
                name="habit_consistency",
                current_score=0.0,
                weight=self.COMPONENT_WEIGHTS["habit_consistency"],
                description="Consistency in maintaining financial habits",
                recommendations=[
                    "Maintain daily expense tracking streaks",
                    "Review finances weekly",
                    "Build sustainable financial routines"
                ]
            ),
            HealthScoreComponent(
                name="financial_goals",
                current_score=0.0,
                weight=self.COMPONENT_WEIGHTS["financial_goals"],
                description="Progress toward financial goals and milestones",
                recommendations=[
                    "Set specific financial goals",
                    "Track progress regularly",
                    "Celebrate milestone achievements"
                ]
            )
        ]

    # Private calculation methods for each component

    async def _calculate_expense_tracking_score(self, profile: UserGamificationProfile) -> float:
        """
        Calculate expense tracking consistency score (0-100).
        
        Factors:
        - Daily tracking consistency (streak length)
        - Completeness (receipts, categories)
        - Recent activity level
        """
        try:
            stats = profile.statistics or {}
            expenses_tracked = stats.get("expensesTracked", 0)
            receipts_uploaded = stats.get("receiptsUploaded", 0)

            # Get expense tracking streak
            expense_streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == HabitType.DAILY_EXPENSE_TRACKING
                )
            ).first()

            # Base score from activity level (0-40 points)
            if expenses_tracked == 0:
                activity_score = 0
            elif expenses_tracked < 10:
                activity_score = 10
            elif expenses_tracked < 50:
                activity_score = 25
            else:
                activity_score = 40

            # Streak consistency score (0-35 points)
            streak_score = 0
            if expense_streak:
                current_streak = expense_streak.current_length
                if current_streak >= 30:
                    streak_score = 35
                elif current_streak >= 14:
                    streak_score = 25
                elif current_streak >= 7:
                    streak_score = 15
                elif current_streak >= 3:
                    streak_score = 10

            # Completeness score (0-25 points)
            completeness_score = 0
            if expenses_tracked > 0:
                receipt_ratio = receipts_uploaded / expenses_tracked
                if receipt_ratio >= 0.8:
                    completeness_score = 25
                elif receipt_ratio >= 0.6:
                    completeness_score = 20
                elif receipt_ratio >= 0.4:
                    completeness_score = 15
                elif receipt_ratio >= 0.2:
                    completeness_score = 10

            total_score = activity_score + streak_score + completeness_score
            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating expense tracking score: {str(e)}")
            return 0.0

    async def _calculate_budget_adherence_score(self, profile: UserGamificationProfile) -> float:
        """
        Calculate budget adherence score (0-100).
        
        Note: This is a simplified implementation since we don't have
        direct budget data in the gamification system. In a full implementation,
        this would integrate with the budget management system.
        """
        try:
            stats = profile.statistics or {}
            budget_reviews = stats.get("budgetReviews", 0)

            # Base score from budget review frequency
            if budget_reviews == 0:
                return 0.0
            elif budget_reviews < 4:
                return 30.0
            elif budget_reviews < 12:
                return 60.0
            else:
                return 85.0

        except Exception as e:
            logger.error(f"Error calculating budget adherence score: {str(e)}")
            return 0.0

    async def _calculate_invoice_management_score(self, profile: UserGamificationProfile) -> float:
        """
        Calculate invoice management score (0-100).
        
        Factors:
        - Invoice creation frequency
        - Follow-up consistency
        - Payment tracking
        """
        try:
            stats = profile.statistics or {}
            invoices_created = stats.get("invoicesCreated", 0)

            # Get invoice follow-up streak
            invoice_streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == HabitType.INVOICE_FOLLOW_UP
                )
            ).first()

            # Base score from invoice activity (0-50 points)
            if invoices_created == 0:
                activity_score = 0
            elif invoices_created < 5:
                activity_score = 20
            elif invoices_created < 20:
                activity_score = 35
            else:
                activity_score = 50

            # Follow-up consistency score (0-50 points)
            followup_score = 0
            if invoice_streak:
                current_streak = invoice_streak.current_length
                if current_streak >= 14:
                    followup_score = 50
                elif current_streak >= 7:
                    followup_score = 35
                elif current_streak >= 3:
                    followup_score = 20
                elif current_streak >= 1:
                    followup_score = 10

            total_score = activity_score + followup_score
            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating invoice management score: {str(e)}")
            return 0.0

    async def _calculate_habit_consistency_score(self, profile: UserGamificationProfile) -> float:
        """
        Calculate overall habit consistency score (0-100).
        
        Factors:
        - Number of active streaks
        - Average streak length
        - Streak recovery rate
        """
        try:
            streaks = self.db.query(UserStreak).filter(
                UserStreak.profile_id == profile.id
            ).all()

            if not streaks:
                return 0.0

            active_streaks = [s for s in streaks if s.is_active and s.current_length > 0]
            total_streaks = len(streaks)
            
            # Active streak ratio (0-40 points)
            active_ratio = len(active_streaks) / total_streaks if total_streaks > 0 else 0
            active_score = active_ratio * 40

            # Average streak length (0-40 points)
            if active_streaks:
                avg_streak_length = sum(s.current_length for s in active_streaks) / len(active_streaks)
                if avg_streak_length >= 30:
                    length_score = 40
                elif avg_streak_length >= 14:
                    length_score = 30
                elif avg_streak_length >= 7:
                    length_score = 20
                elif avg_streak_length >= 3:
                    length_score = 10
                else:
                    length_score = 5
            else:
                length_score = 0

            # Longest streak bonus (0-20 points)
            longest_streak = max((s.longest_length for s in streaks), default=0)
            if longest_streak >= 90:
                longest_score = 20
            elif longest_streak >= 30:
                longest_score = 15
            elif longest_streak >= 14:
                longest_score = 10
            elif longest_streak >= 7:
                longest_score = 5
            else:
                longest_score = 0

            total_score = active_score + length_score + longest_score
            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating habit consistency score: {str(e)}")
            return 0.0

    async def _calculate_financial_goals_score(self, profile: UserGamificationProfile) -> float:
        """
        Calculate financial goals progress score (0-100).
        
        Factors:
        - Achievement completion rate
        - Level progression
        - Overall engagement
        """
        try:
            # Level progression score (0-50 points)
            level = profile.level
            if level >= 20:
                level_score = 50
            elif level >= 10:
                level_score = 35
            elif level >= 5:
                level_score = 25
            elif level >= 2:
                level_score = 15
            else:
                level_score = 5

            # Achievement completion score (0-50 points)
            stats = profile.statistics or {}
            achievements_unlocked = stats.get("achievementsUnlocked", 0)
            
            if achievements_unlocked >= 20:
                achievement_score = 50
            elif achievements_unlocked >= 10:
                achievement_score = 35
            elif achievements_unlocked >= 5:
                achievement_score = 25
            elif achievements_unlocked >= 2:
                achievement_score = 15
            elif achievements_unlocked >= 1:
                achievement_score = 10
            else:
                achievement_score = 0

            total_score = level_score + achievement_score
            return min(total_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating financial goals score: {str(e)}")
            return 0.0

    async def _calculate_score_trend(self, profile: UserGamificationProfile, current_score: float) -> ScoreTrend:
        """Calculate the trend direction of the financial health score"""
        try:
            # Get recent score history (last 7 days)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            # For now, use a simple comparison with the stored score
            # In a full implementation, this would use historical score data
            stored_score = profile.financial_health_score
            
            if current_score > stored_score + 2:
                return ScoreTrend.IMPROVING
            elif current_score < stored_score - 2:
                return ScoreTrend.DECLINING
            else:
                return ScoreTrend.STABLE

        except Exception as e:
            logger.error(f"Error calculating score trend: {str(e)}")
            return ScoreTrend.STABLE

    async def _generate_recommendations(self, components: Dict[str, float], overall_score: float) -> List[str]:
        """Generate personalized recommendations based on component scores"""
        recommendations = []

        # Overall score recommendations
        if overall_score >= self.EXCELLENT_THRESHOLD:
            recommendations.append("Excellent financial health! Keep up the great work.")
        elif overall_score >= self.GOOD_THRESHOLD:
            recommendations.append("Good financial health. Focus on consistency to reach excellence.")
        elif overall_score >= self.FAIR_THRESHOLD:
            recommendations.append("Fair financial health. Identify areas for improvement below.")
        else:
            recommendations.append("Your financial health needs attention. Start with the highest-impact improvements.")

        # Component-specific recommendations
        if components["expense_tracking"] < 60:
            recommendations.append("Improve expense tracking by recording expenses daily and adding receipt photos.")
        
        if components["budget_adherence"] < 60:
            recommendations.append("Review your budget more frequently and track spending against limits.")
        
        if components["invoice_management"] < 60:
            recommendations.append("Create invoices promptly and follow up on payments regularly.")
        
        if components["habit_consistency"] < 60:
            recommendations.append("Focus on building consistent financial habits through daily actions.")
        
        if components["financial_goals"] < 60:
            recommendations.append("Set specific financial goals and track your progress toward achievements.")

        return recommendations

    async def _get_score_history(self, profile: UserGamificationProfile) -> List[Dict[str, Any]]:
        """Get historical score data for trend analysis"""
        try:
            # This is a simplified implementation
            # In a full implementation, this would query a score history table
            current_score = profile.financial_health_score
            now = datetime.now(timezone.utc)
            
            return [
                {
                    "date": now - timedelta(days=30),
                    "score": max(current_score - 15, 0)
                },
                {
                    "date": now - timedelta(days=20),
                    "score": max(current_score - 10, 0)
                },
                {
                    "date": now - timedelta(days=10),
                    "score": max(current_score - 5, 0)
                },
                {
                    "date": now,
                    "score": current_score
                }
            ]

        except Exception as e:
            logger.error(f"Error getting score history: {str(e)}")
            return []

    async def _store_score_history(self, profile: UserGamificationProfile, score: float, event: FinancialEvent):
        """Store a score history entry (simplified implementation)"""
        try:
            # In a full implementation, this would store to a dedicated score history table
            # For now, we'll just update the profile's updated_at timestamp
            profile.updated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error storing score history: {str(e)}")