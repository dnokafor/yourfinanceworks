"""
Streak tracking service for the gamification system.

This service handles all streak-related functionality including:
- Tracking daily/weekly habit streaks
- Calculating streak bonuses and multipliers
- Detecting streak risks and sending notifications
- Managing streak recovery after breaks
- Analyzing habit formation patterns
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta, date
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.models.gamification import (
    UserGamificationProfile,
    UserStreak,
    HabitType,
    PointHistory
)
from core.schemas.gamification import ActionType, FinancialEvent

logger = logging.getLogger(__name__)


class StreakRiskLevel(str, Enum):
    """Risk levels for streak maintenance"""
    SAFE = "safe"           # Recent activity, no risk
    LOW_RISK = "low_risk"   # 1 day since last activity
    MEDIUM_RISK = "medium_risk"  # 2 days since last activity
    HIGH_RISK = "high_risk"      # 3+ days since last activity
    BROKEN = "broken"       # Streak has been broken


class StreakStatus:
    """Status information for a user's streak"""
    def __init__(
        self,
        current: int,
        longest: int,
        last_activity: Optional[datetime],
        is_active: bool,
        risk_level: StreakRiskLevel,
        days_since_activity: int = 0,
        streak_start_date: Optional[datetime] = None,
        times_broken: int = 0
    ):
        self.current = current
        self.longest = longest
        self.last_activity = last_activity
        self.is_active = is_active
        self.risk_level = risk_level
        self.days_since_activity = days_since_activity
        self.streak_start_date = streak_start_date
        self.times_broken = times_broken


class StreakUpdate:
    """Information about a streak update"""
    def __init__(
        self,
        habit_type: HabitType,
        previous_length: int,
        new_length: int,
        is_new_record: bool,
        multiplier_change: float,
        risk_level_change: Optional[Tuple[StreakRiskLevel, StreakRiskLevel]] = None
    ):
        self.habit_type = habit_type
        self.previous_length = previous_length
        self.new_length = new_length
        self.is_new_record = is_new_record
        self.multiplier_change = multiplier_change
        self.risk_level_change = risk_level_change


class StreakRecovery:
    """Information about streak recovery options"""
    def __init__(
        self,
        habit_type: HabitType,
        broken_streak_length: int,
        recovery_suggestions: List[str],
        encouragement_message: str,
        recovery_challenge_available: bool = False
    ):
        self.habit_type = habit_type
        self.broken_streak_length = broken_streak_length
        self.recovery_suggestions = recovery_suggestions
        self.encouragement_message = encouragement_message
        self.recovery_challenge_available = recovery_challenge_available


class StreakAnalytics:
    """Analytics data for user streaks"""
    def __init__(
        self,
        total_active_streaks: int,
        longest_overall_streak: int,
        most_consistent_habit: Optional[HabitType],
        habit_strength_scores: Dict[HabitType, float],
        weekly_consistency: Dict[str, float],  # Day of week -> consistency percentage
        monthly_trends: List[Dict[str, Any]]
    ):
        self.total_active_streaks = total_active_streaks
        self.longest_overall_streak = longest_overall_streak
        self.most_consistent_habit = most_consistent_habit
        self.habit_strength_scores = habit_strength_scores
        self.weekly_consistency = weekly_consistency
        self.monthly_trends = monthly_trends


class StreakTracker:
    """
    Core streak tracking service for the gamification system.
    
    Handles:
    - Daily and weekly habit streak tracking
    - Streak risk detection and notifications
    - Streak bonus calculations
    - Habit formation analytics
    - Streak recovery mechanisms
    """

    # Streak configuration
    DAILY_HABIT_GRACE_HOURS = 6  # Allow 6 hours past midnight for daily habits
    WEEKLY_HABIT_GRACE_DAYS = 1  # Allow 1 day past week end for weekly habits
    
    # Risk level thresholds (in hours for daily habits, days for weekly habits)
    RISK_THRESHOLDS = {
        HabitType.DAILY_EXPENSE_TRACKING: {
            StreakRiskLevel.LOW_RISK: 30,    # 30 hours
            StreakRiskLevel.MEDIUM_RISK: 48, # 48 hours
            StreakRiskLevel.HIGH_RISK: 72,   # 72 hours
        },
        HabitType.RECEIPT_DOCUMENTATION: {
            StreakRiskLevel.LOW_RISK: 30,
            StreakRiskLevel.MEDIUM_RISK: 48,
            StreakRiskLevel.HIGH_RISK: 72,
        },
        HabitType.WEEKLY_BUDGET_REVIEW: {
            StreakRiskLevel.LOW_RISK: 8,     # 8 days
            StreakRiskLevel.MEDIUM_RISK: 10, # 10 days
            StreakRiskLevel.HIGH_RISK: 14,   # 14 days
        },
        HabitType.INVOICE_FOLLOW_UP: {
            StreakRiskLevel.LOW_RISK: 48,    # 48 hours
            StreakRiskLevel.MEDIUM_RISK: 96, # 96 hours
            StreakRiskLevel.HIGH_RISK: 168,  # 1 week
        }
    }

    # Action type to habit type mapping
    ACTION_TO_HABIT_MAPPING = {
        ActionType.EXPENSE_ADDED: HabitType.DAILY_EXPENSE_TRACKING,
        ActionType.RECEIPT_UPLOADED: HabitType.RECEIPT_DOCUMENTATION,
        ActionType.INVOICE_CREATED: HabitType.INVOICE_FOLLOW_UP,
        ActionType.PAYMENT_RECORDED: HabitType.INVOICE_FOLLOW_UP,
        ActionType.BUDGET_REVIEWED: HabitType.WEEKLY_BUDGET_REVIEW,
        ActionType.CATEGORY_ASSIGNED: HabitType.DAILY_EXPENSE_TRACKING
    }

    def __init__(self, db: Session):
        self.db = db

    async def track_streak(self, user_id: int, habit_type: HabitType, event_timestamp: Optional[datetime] = None) -> StreakStatus:
        """
        Track and update a user's streak for a specific habit type.
        
        Args:
            user_id: User ID
            habit_type: Type of habit being tracked
            event_timestamp: When the activity occurred (defaults to now)
            
        Returns:
            Updated streak status
        """
        try:
            if event_timestamp is None:
                event_timestamp = datetime.now(timezone.utc)

            # Get user's gamification profile
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile or not profile.module_enabled:
                logger.warning(f"Gamification not enabled for user {user_id}")
                return StreakStatus(0, 0, None, False, StreakRiskLevel.BROKEN)

            # Get or create streak record
            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type
                )
            ).first()

            if not streak:
                streak = UserStreak(
                    profile_id=profile.id,
                    habit_type=habit_type,
                    current_length=0,
                    longest_length=0,
                    is_active=True,
                    times_broken=0
                )
                self.db.add(streak)

            # Calculate streak update
            previous_length = streak.current_length
            updated_streak = await self._update_streak_logic(streak, event_timestamp)
            
            # Update database
            self.db.commit()
            self.db.refresh(streak)

            # Calculate risk level
            risk_level = await self._calculate_risk_level(streak, habit_type)

            # Update profile statistics if this is a new record
            if streak.current_length > streak.longest_length:
                await self._update_profile_longest_streak(profile, streak.current_length)

            return StreakStatus(
                current=streak.current_length,
                longest=streak.longest_length,
                last_activity=streak.last_activity_date,
                is_active=streak.is_active,
                risk_level=risk_level,
                days_since_activity=await self._calculate_days_since_activity(streak, habit_type),
                streak_start_date=streak.streak_start_date,
                times_broken=streak.times_broken
            )

        except Exception as e:
            logger.error(f"Error tracking streak for user {user_id}, habit {habit_type}: {str(e)}")
            self.db.rollback()
            return StreakStatus(0, 0, None, False, StreakRiskLevel.BROKEN)

    async def calculate_streak_bonus(self, streak_length: int, habit_type: HabitType) -> float:
        """
        Calculate the streak bonus multiplier for a given streak length.
        
        Args:
            streak_length: Current streak length
            habit_type: Type of habit (affects bonus calculation)
            
        Returns:
            Multiplier value (1.0 = no bonus, 2.0 = double points, etc.)
        """
        try:
            if streak_length <= 0:
                return 1.0

            # Base multiplier rate varies by habit type
            base_rates = {
                HabitType.DAILY_EXPENSE_TRACKING: 0.05,    # 5% per day
                HabitType.RECEIPT_DOCUMENTATION: 0.03,     # 3% per day
                HabitType.WEEKLY_BUDGET_REVIEW: 0.15,      # 15% per week
                HabitType.INVOICE_FOLLOW_UP: 0.08          # 8% per occurrence
            }

            # Maximum multipliers by habit type
            max_multipliers = {
                HabitType.DAILY_EXPENSE_TRACKING: 3.0,     # 300% max
                HabitType.RECEIPT_DOCUMENTATION: 2.5,      # 250% max
                HabitType.WEEKLY_BUDGET_REVIEW: 4.0,       # 400% max
                HabitType.INVOICE_FOLLOW_UP: 2.0           # 200% max
            }

            rate = base_rates.get(habit_type, 0.05)
            max_multiplier = max_multipliers.get(habit_type, 3.0)

            # Calculate multiplier with diminishing returns
            if streak_length <= 7:
                # Linear growth for first week
                multiplier = 1.0 + (streak_length * rate)
            elif streak_length <= 30:
                # Slower growth for first month
                base_week_bonus = 1.0 + (7 * rate)
                additional_days = streak_length - 7
                multiplier = base_week_bonus + (additional_days * rate * 0.7)
            else:
                # Even slower growth after first month
                base_month_bonus = 1.0 + (7 * rate) + (23 * rate * 0.7)
                additional_days = streak_length - 30
                multiplier = base_month_bonus + (additional_days * rate * 0.5)

            return min(multiplier, max_multiplier)

        except Exception as e:
            logger.error(f"Error calculating streak bonus: {str(e)}")
            return 1.0

    async def handle_streak_break(self, user_id: int, habit_type: HabitType) -> StreakRecovery:
        """
        Handle a broken streak and provide recovery options.
        
        Args:
            user_id: User ID
            habit_type: Type of habit that was broken
            
        Returns:
            Recovery information and suggestions
        """
        try:
            # Get user's gamification profile
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return StreakRecovery(habit_type, 0, [], "Profile not found", False)

            # Get streak record
            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type
                )
            ).first()

            if not streak:
                return StreakRecovery(habit_type, 0, [], "Streak not found", False)

            # Record the broken streak
            broken_length = streak.current_length
            streak.current_length = 0
            streak.is_active = False
            streak.times_broken += 1
            streak.streak_start_date = None

            self.db.commit()

            # Generate recovery suggestions
            suggestions = await self._generate_recovery_suggestions(habit_type, broken_length)
            
            # Generate encouragement message
            encouragement = await self._generate_encouragement_message(habit_type, broken_length, streak.times_broken)

            # Check if recovery challenge is available
            recovery_challenge_available = await self._check_recovery_challenge_availability(
                profile, habit_type, broken_length
            )

            return StreakRecovery(
                habit_type=habit_type,
                broken_streak_length=broken_length,
                recovery_suggestions=suggestions,
                encouragement_message=encouragement,
                recovery_challenge_available=recovery_challenge_available
            )

        except Exception as e:
            logger.error(f"Error handling streak break for user {user_id}: {str(e)}")
            self.db.rollback()
            return StreakRecovery(habit_type, 0, [], "Error occurred", False)

    async def get_streak_insights(self, user_id: int) -> StreakAnalytics:
        """
        Get comprehensive streak analytics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Detailed streak analytics
        """
        try:
            # Get user's gamification profile
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return StreakAnalytics(0, 0, None, {}, {}, [])

            # Get all user streaks
            streaks = self.db.query(UserStreak).filter(
                UserStreak.profile_id == profile.id
            ).all()

            # Calculate analytics
            total_active = sum(1 for s in streaks if s.is_active and s.current_length > 0)
            longest_overall = max((s.longest_length for s in streaks), default=0)
            
            # Find most consistent habit
            most_consistent = None
            best_consistency_score = 0
            habit_strength_scores = {}

            for streak in streaks:
                consistency_score = await self._calculate_habit_strength(streak)
                habit_strength_scores[streak.habit_type] = consistency_score
                
                if consistency_score > best_consistency_score:
                    best_consistency_score = consistency_score
                    most_consistent = streak.habit_type

            # Calculate weekly consistency patterns
            weekly_consistency = await self._calculate_weekly_consistency(profile.id)

            # Calculate monthly trends
            monthly_trends = await self._calculate_monthly_trends(profile.id)

            return StreakAnalytics(
                total_active_streaks=total_active,
                longest_overall_streak=longest_overall,
                most_consistent_habit=most_consistent,
                habit_strength_scores=habit_strength_scores,
                weekly_consistency=weekly_consistency,
                monthly_trends=monthly_trends
            )

        except Exception as e:
            logger.error(f"Error getting streak insights for user {user_id}: {str(e)}")
            return StreakAnalytics(0, 0, None, {}, {}, [])

    async def update_streaks_from_event(self, event: FinancialEvent) -> List[StreakUpdate]:
        """
        Update relevant streaks based on a financial event.
        
        Args:
            event: Financial event that occurred
            
        Returns:
            List of streak updates that occurred
        """
        try:
            updates = []
            
            # Map action type to habit types
            habit_types = []
            primary_habit = self.ACTION_TO_HABIT_MAPPING.get(event.action_type)
            if primary_habit:
                habit_types.append(primary_habit)

            # Some actions can contribute to multiple habits
            if event.action_type == ActionType.EXPENSE_ADDED and event.metadata.get("has_receipt"):
                habit_types.append(HabitType.RECEIPT_DOCUMENTATION)

            # Update each relevant streak
            for habit_type in habit_types:
                old_status = await self._get_current_streak_status(event.user_id, habit_type)
                new_status = await self.track_streak(event.user_id, habit_type, event.timestamp)
                
                if old_status and new_status:
                    # Calculate multiplier change
                    old_multiplier = await self.calculate_streak_bonus(old_status.current, habit_type)
                    new_multiplier = await self.calculate_streak_bonus(new_status.current, habit_type)
                    
                    # Check for risk level changes
                    risk_change = None
                    if old_status.risk_level != new_status.risk_level:
                        risk_change = (old_status.risk_level, new_status.risk_level)

                    update = StreakUpdate(
                        habit_type=habit_type,
                        previous_length=old_status.current,
                        new_length=new_status.current,
                        is_new_record=(new_status.current > old_status.longest),
                        multiplier_change=new_multiplier - old_multiplier,
                        risk_level_change=risk_change
                    )
                    updates.append(update)

            return updates

        except Exception as e:
            logger.error(f"Error updating streaks from event: {str(e)}")
            return []

    async def get_users_at_risk(self, risk_level: StreakRiskLevel = StreakRiskLevel.MEDIUM_RISK) -> List[Dict[str, Any]]:
        """
        Get users whose streaks are at risk of breaking.
        
        Args:
            risk_level: Minimum risk level to include
            
        Returns:
            List of users with at-risk streaks
        """
        try:
            at_risk_users = []
            
            # Get all active streaks
            active_streaks = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.is_active == True,
                    UserStreak.current_length > 0
                )
            ).all()

            for streak in active_streaks:
                current_risk = await self._calculate_risk_level(streak, streak.habit_type)
                
                # Check if risk level meets threshold
                risk_levels = [StreakRiskLevel.SAFE, StreakRiskLevel.LOW_RISK, 
                              StreakRiskLevel.MEDIUM_RISK, StreakRiskLevel.HIGH_RISK]
                
                if risk_levels.index(current_risk) >= risk_levels.index(risk_level):
                    # Get user profile
                    profile = self.db.query(UserGamificationProfile).filter(
                        UserGamificationProfile.id == streak.profile_id
                    ).first()
                    
                    if profile and profile.module_enabled:
                        at_risk_users.append({
                            "user_id": profile.user_id,
                            "habit_type": streak.habit_type,
                            "current_streak": streak.current_length,
                            "risk_level": current_risk,
                            "days_since_activity": await self._calculate_days_since_activity(streak, streak.habit_type),
                            "last_activity": streak.last_activity_date
                        })

            return at_risk_users

        except Exception as e:
            logger.error(f"Error getting users at risk: {str(e)}")
            return []

    # Private helper methods

    async def _update_streak_logic(self, streak: UserStreak, event_timestamp: datetime) -> UserStreak:
        """Update streak logic based on habit type and timing"""
        try:
            now = event_timestamp
            today = now.date()
            
            # Handle different habit types
            if streak.habit_type in [HabitType.DAILY_EXPENSE_TRACKING, HabitType.RECEIPT_DOCUMENTATION]:
                # Daily habits
                if streak.last_activity_date:
                    last_date = streak.last_activity_date.date()
                    days_diff = (today - last_date).days
                    
                    if days_diff == 0:
                        # Same day - no streak change, just update timestamp
                        streak.last_activity_date = now
                    elif days_diff == 1:
                        # Next day - extend streak
                        streak.current_length += 1
                        streak.last_activity_date = now
                        streak.is_active = True
                        if not streak.streak_start_date:
                            streak.streak_start_date = now
                    else:
                        # Gap in days - break streak
                        streak.current_length = 1  # Start new streak
                        streak.last_activity_date = now
                        streak.is_active = True
                        streak.times_broken += 1
                        streak.streak_start_date = now
                else:
                    # First activity
                    streak.current_length = 1
                    streak.last_activity_date = now
                    streak.is_active = True
                    streak.streak_start_date = now

            elif streak.habit_type == HabitType.WEEKLY_BUDGET_REVIEW:
                # Weekly habits
                if streak.last_activity_date:
                    last_week = streak.last_activity_date.isocalendar()[1]
                    current_week = now.isocalendar()[1]
                    last_year = streak.last_activity_date.year
                    current_year = now.year
                    
                    # Calculate week difference accounting for year changes
                    if current_year == last_year:
                        week_diff = current_week - last_week
                    else:
                        # Simplified year transition handling
                        week_diff = (current_year - last_year) * 52 + (current_week - last_week)
                    
                    if week_diff == 0:
                        # Same week - no streak change
                        streak.last_activity_date = now
                    elif week_diff == 1:
                        # Next week - extend streak
                        streak.current_length += 1
                        streak.last_activity_date = now
                        streak.is_active = True
                        if not streak.streak_start_date:
                            streak.streak_start_date = now
                    else:
                        # Gap in weeks - break streak
                        streak.current_length = 1
                        streak.last_activity_date = now
                        streak.is_active = True
                        streak.times_broken += 1
                        streak.streak_start_date = now
                else:
                    # First activity
                    streak.current_length = 1
                    streak.last_activity_date = now
                    streak.is_active = True
                    streak.streak_start_date = now

            elif streak.habit_type == HabitType.INVOICE_FOLLOW_UP:
                # Invoice follow-up is more flexible - any activity extends
                if streak.last_activity_date:
                    # Ensure timezone-aware comparison
                    last_activity = streak.last_activity_date
                    if last_activity.tzinfo is None:
                        last_activity = last_activity.replace(tzinfo=timezone.utc)
                    
                    hours_diff = (now - last_activity).total_seconds() / 3600
                    
                    if hours_diff <= 168:  # Within a week
                        streak.current_length += 1
                        streak.last_activity_date = now
                        streak.is_active = True
                        if not streak.streak_start_date:
                            streak.streak_start_date = now
                    else:
                        # Too long gap - break streak
                        streak.current_length = 1
                        streak.last_activity_date = now
                        streak.is_active = True
                        streak.times_broken += 1
                        streak.streak_start_date = now
                else:
                    # First activity
                    streak.current_length = 1
                    streak.last_activity_date = now
                    streak.is_active = True
                    streak.streak_start_date = now

            # Update longest streak if current is longer
            if streak.current_length > streak.longest_length:
                streak.longest_length = streak.current_length

            return streak

        except Exception as e:
            logger.error(f"Error updating streak logic: {str(e)}")
            return streak

    async def _calculate_risk_level(self, streak: UserStreak, habit_type: HabitType) -> StreakRiskLevel:
        """Calculate the risk level for a streak"""
        try:
            if not streak.is_active or streak.current_length == 0:
                return StreakRiskLevel.BROKEN

            if not streak.last_activity_date:
                return StreakRiskLevel.HIGH_RISK

            now = datetime.now(timezone.utc)
            
            # Ensure both datetimes are timezone-aware
            last_activity = streak.last_activity_date
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            
            time_diff = now - last_activity

            # Get thresholds for this habit type
            thresholds = self.RISK_THRESHOLDS.get(habit_type, {})
            
            if habit_type == HabitType.WEEKLY_BUDGET_REVIEW:
                # Weekly habits use days
                days_diff = time_diff.days
                
                if days_diff <= thresholds.get(StreakRiskLevel.LOW_RISK, 8):
                    return StreakRiskLevel.SAFE
                elif days_diff <= thresholds.get(StreakRiskLevel.MEDIUM_RISK, 10):
                    return StreakRiskLevel.LOW_RISK
                elif days_diff <= thresholds.get(StreakRiskLevel.HIGH_RISK, 14):
                    return StreakRiskLevel.MEDIUM_RISK
                else:
                    return StreakRiskLevel.HIGH_RISK
            else:
                # Daily habits use hours
                hours_diff = time_diff.total_seconds() / 3600
                
                if hours_diff <= thresholds.get(StreakRiskLevel.LOW_RISK, 30):
                    return StreakRiskLevel.SAFE
                elif hours_diff <= thresholds.get(StreakRiskLevel.MEDIUM_RISK, 48):
                    return StreakRiskLevel.LOW_RISK
                elif hours_diff <= thresholds.get(StreakRiskLevel.HIGH_RISK, 72):
                    return StreakRiskLevel.MEDIUM_RISK
                else:
                    return StreakRiskLevel.HIGH_RISK

        except Exception as e:
            logger.error(f"Error calculating risk level: {str(e)}")
            return StreakRiskLevel.HIGH_RISK

    async def _calculate_days_since_activity(self, streak: UserStreak, habit_type: HabitType) -> int:
        """Calculate days since last activity"""
        try:
            if not streak.last_activity_date:
                return 999  # Large number to indicate no activity

            now = datetime.now(timezone.utc)
            
            # Ensure both datetimes are timezone-aware
            last_activity = streak.last_activity_date
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            
            time_diff = now - last_activity

            if habit_type == HabitType.WEEKLY_BUDGET_REVIEW:
                return time_diff.days
            else:
                # For daily habits, return fractional days as whole days
                return max(0, int(time_diff.total_seconds() / 86400))

        except Exception as e:
            logger.error(f"Error calculating days since activity: {str(e)}")
            return 999

    async def _generate_recovery_suggestions(self, habit_type: HabitType, broken_length: int) -> List[str]:
        """Generate recovery suggestions for a broken streak"""
        suggestions = []
        
        habit_suggestions = {
            HabitType.DAILY_EXPENSE_TRACKING: [
                "Start small - track just one expense today",
                "Set a daily reminder on your phone",
                "Keep receipts in a designated pocket or wallet section",
                "Use the mobile app for quick expense entry"
            ],
            HabitType.RECEIPT_DOCUMENTATION: [
                "Take photos of receipts immediately after purchases",
                "Set up a 'receipt folder' on your phone",
                "Review and upload receipts during your commute",
                "Ask for digital receipts when possible"
            ],
            HabitType.WEEKLY_BUDGET_REVIEW: [
                "Schedule a specific day and time for budget reviews",
                "Start with a 10-minute quick review",
                "Focus on just one budget category this week",
                "Set up calendar reminders for budget check-ins"
            ],
            HabitType.INVOICE_FOLLOW_UP: [
                "Create a simple invoice tracking spreadsheet",
                "Set reminders for follow-up dates",
                "Draft template follow-up emails",
                "Check invoice status during your morning routine"
            ]
        }
        
        base_suggestions = habit_suggestions.get(habit_type, ["Start fresh with a small, achievable goal"])
        
        # Add encouragement based on broken streak length
        if broken_length >= 30:
            suggestions.append("You had an amazing 30+ day streak! You can build it back up.")
        elif broken_length >= 7:
            suggestions.append("A week-long streak shows you can do this - let's rebuild!")
        
        return base_suggestions + suggestions

    async def _generate_encouragement_message(self, habit_type: HabitType, broken_length: int, times_broken: int) -> str:
        """Generate an encouraging message for streak recovery"""
        habit_names = {
            HabitType.DAILY_EXPENSE_TRACKING: "expense tracking",
            HabitType.RECEIPT_DOCUMENTATION: "receipt documentation",
            HabitType.WEEKLY_BUDGET_REVIEW: "budget reviews",
            HabitType.INVOICE_FOLLOW_UP: "invoice follow-ups"
        }
        
        habit_name = habit_names.get(habit_type, "financial habit")
        
        if broken_length == 0:
            return f"Every expert was once a beginner. Start your {habit_name} journey today!"
        elif broken_length >= 30:
            return f"Your {broken_length}-day {habit_name} streak was incredible! That shows real dedication. One setback doesn't erase your progress - you've got this!"
        elif broken_length >= 7:
            return f"A {broken_length}-day streak proves you can build lasting habits. Take a deep breath and start again - you're closer to success than you think!"
        else:
            return f"Building habits takes practice. Your {broken_length}-day effort wasn't wasted - it was training. Let's build on that foundation!"

    async def _check_recovery_challenge_availability(self, profile: UserGamificationProfile, habit_type: HabitType, broken_length: int) -> bool:
        """Check if a recovery challenge is available for this user"""
        # Recovery challenges are available for streaks that were at least 7 days long
        return broken_length >= 7

    async def _update_profile_longest_streak(self, profile: UserGamificationProfile, new_longest: int):
        """Update the profile's longest streak statistic"""
        try:
            stats = profile.statistics or {}
            current_longest = stats.get("longestStreak", 0)
            
            if new_longest > current_longest:
                stats["longestStreak"] = new_longest
                profile.statistics = stats

        except Exception as e:
            logger.error(f"Error updating profile longest streak: {str(e)}")

    async def _get_current_streak_status(self, user_id: int, habit_type: HabitType) -> Optional[StreakStatus]:
        """Get current streak status for a user and habit type"""
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return None

            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type
                )
            ).first()

            if not streak:
                return None

            risk_level = await self._calculate_risk_level(streak, habit_type)
            days_since = await self._calculate_days_since_activity(streak, habit_type)

            return StreakStatus(
                current=streak.current_length,
                longest=streak.longest_length,
                last_activity=streak.last_activity_date,
                is_active=streak.is_active,
                risk_level=risk_level,
                days_since_activity=days_since,
                streak_start_date=streak.streak_start_date,
                times_broken=streak.times_broken
            )

        except Exception as e:
            logger.error(f"Error getting current streak status: {str(e)}")
            return None

    async def _calculate_habit_strength(self, streak: UserStreak) -> float:
        """Calculate habit strength score (0-100) based on streak history"""
        try:
            # Base score from current streak
            current_score = min(streak.current_length * 2, 50)  # Max 50 from current streak
            
            # Bonus from longest streak
            longest_bonus = min(streak.longest_length * 1, 30)  # Max 30 from longest streak
            
            # Penalty for breaks (but not too harsh)
            break_penalty = min(streak.times_broken * 5, 20)  # Max 20 penalty
            
            # Consistency bonus if active
            consistency_bonus = 20 if streak.is_active and streak.current_length > 0 else 0
            
            total_score = current_score + longest_bonus + consistency_bonus - break_penalty
            return max(0, min(100, total_score))

        except Exception as e:
            logger.error(f"Error calculating habit strength: {str(e)}")
            return 0.0

    async def _calculate_weekly_consistency(self, profile_id: int) -> Dict[str, float]:
        """Calculate consistency patterns by day of week"""
        try:
            # This would require analyzing point history by day of week
            # For now, return a placeholder implementation
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            return {day: 50.0 for day in days}  # Placeholder 50% consistency

        except Exception as e:
            logger.error(f"Error calculating weekly consistency: {str(e)}")
            return {}

    async def _calculate_monthly_trends(self, profile_id: int) -> List[Dict[str, Any]]:
        """Calculate monthly streak trends"""
        try:
            # This would require analyzing streak data over time
            # For now, return a placeholder implementation
            now = datetime.now(timezone.utc)
            trends = []
            
            for i in range(3):  # Last 3 months
                month_date = now - timedelta(days=30 * i)
                trends.append({
                    "month": month_date.strftime("%Y-%m"),
                    "average_streak_length": 5.0,  # Placeholder
                    "total_activities": 20,        # Placeholder
                    "consistency_score": 75.0      # Placeholder
                })
            
            return trends

        except Exception as e:
            logger.error(f"Error calculating monthly trends: {str(e)}")
            return []