"""
Points calculation engine for the gamification system.

This module handles all point calculations including base points, bonus multipliers,
streak bonuses, accuracy bonuses, and completeness bonuses.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.models.gamification import (
    UserGamificationProfile,
    UserStreak,
    HabitType,
    OrganizationGamificationConfig
)
from core.schemas.gamification import ActionType, FinancialEvent

logger = logging.getLogger(__name__)


class PointsCalculator:
    """
    Core points calculation engine for the gamification system.
    
    Handles:
    - Base point values for different financial actions
    - Streak multipliers for habit formation
    - Accuracy bonuses for data quality
    - Completeness bonuses for thorough record keeping
    - Organization-specific point customizations
    """

    # Default base point values (can be overridden by organization settings)
    DEFAULT_BASE_POINTS = {
        ActionType.EXPENSE_ADDED: 10,
        ActionType.INVOICE_CREATED: 15,
        ActionType.RECEIPT_UPLOADED: 3,
        ActionType.BUDGET_REVIEWED: 20,
        ActionType.PAYMENT_RECORDED: 12,
        ActionType.CATEGORY_ASSIGNED: 5
    }

    # Bonus multiplier configurations
    STREAK_MULTIPLIER_RATE = 0.1  # 10% increase per streak day
    MAX_STREAK_MULTIPLIER = 3.0   # Cap at 300% of base points
    
    # Accuracy bonus values
    ACCURACY_BONUSES = {
        "has_receipt": 2,
        "categorized_correctly": 3,
        "complete_description": 1,
        "proper_vendor_name": 2,
        "valid_amount": 1
    }
    
    # Completeness bonus values
    COMPLETENESS_BONUSES = {
        "has_all_required_fields": 2,
        "has_notes": 1,
        "has_tags": 1,
        "has_project_assignment": 2,
        "has_client_assignment": 2
    }

    def __init__(self, db: Session):
        self.db = db

    async def calculate_points(
        self, 
        event: FinancialEvent, 
        profile: UserGamificationProfile,
        organization_id: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate total points for a financial event.
        
        Args:
            event: The financial event that occurred
            profile: User's gamification profile
            organization_id: Optional organization ID for custom point values
            
        Returns:
            Tuple of (total_points, breakdown_dict)
        """
        try:
            # Get base points (with organization customization if applicable)
            base_points = await self._get_base_points(event.action_type, organization_id)
            
            # Calculate streak multiplier
            streak_multiplier = await self._calculate_streak_multiplier(
                profile, event.action_type
            )
            
            # Calculate accuracy bonus
            accuracy_bonus = await self._calculate_accuracy_bonus(event)
            
            # Calculate completeness bonus
            completeness_bonus = await self._calculate_completeness_bonus(event)
            
            # Calculate timeliness bonus
            timeliness_bonus = await self._calculate_timeliness_bonus(event)
            
            # Apply streak multiplier to base points
            multiplied_base = int(base_points * streak_multiplier)
            
            # Calculate total points
            total_points = multiplied_base + accuracy_bonus + completeness_bonus + timeliness_bonus
            
            # Ensure minimum 1 point
            total_points = max(total_points, 1)
            
            # Create breakdown for transparency
            breakdown = {
                "base_points": base_points,
                "streak_multiplier": streak_multiplier,
                "multiplied_base": multiplied_base,
                "accuracy_bonus": accuracy_bonus,
                "completeness_bonus": completeness_bonus,
                "timeliness_bonus": timeliness_bonus,
                "total_points": total_points,
                "action_type": event.action_type.value,
                "timestamp": event.timestamp
            }
            
            logger.info(f"Points calculated for user {event.user_id}: {total_points} points for {event.action_type.value}")
            
            return total_points, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating points for user {event.user_id}: {str(e)}")
            # Return minimum points on error
            return 1, {
                "base_points": 1,
                "streak_multiplier": 1.0,
                "multiplied_base": 1,
                "accuracy_bonus": 0,
                "completeness_bonus": 0,
                "timeliness_bonus": 0,
                "total_points": 1,
                "action_type": event.action_type.value,
                "error": str(e)
            }

    async def _get_base_points(self, action_type: ActionType, organization_id: Optional[int] = None) -> int:
        """Get base points for an action type, considering organization customizations"""
        try:
            # Check for organization-specific point values
            if organization_id:
                org_config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()
                
                if org_config and org_config.enabled:
                    custom_points = org_config.custom_point_values or {}
                    
                    # Map action types to organization config keys
                    action_mapping = {
                        ActionType.EXPENSE_ADDED: "expenseTracking",
                        ActionType.INVOICE_CREATED: "invoiceCreation",
                        ActionType.BUDGET_REVIEWED: "budgetReview",
                        ActionType.RECEIPT_UPLOADED: "receiptUpload",
                        ActionType.CATEGORY_ASSIGNED: "categoryAccuracy",
                        ActionType.PAYMENT_RECORDED: "promptPaymentMarking"
                    }
                    
                    config_key = action_mapping.get(action_type)
                    if config_key and config_key in custom_points:
                        return custom_points[config_key]
            
            # Fall back to default points
            return self.DEFAULT_BASE_POINTS.get(action_type, 0)
            
        except Exception as e:
            logger.error(f"Error getting base points for {action_type}: {str(e)}")
            return self.DEFAULT_BASE_POINTS.get(action_type, 0)

    async def _calculate_streak_multiplier(
        self, 
        profile: UserGamificationProfile, 
        action_type: ActionType
    ) -> float:
        """Calculate streak multiplier for an action type"""
        try:
            # Map action types to habit types
            habit_mapping = {
                ActionType.EXPENSE_ADDED: HabitType.DAILY_EXPENSE_TRACKING,
                ActionType.RECEIPT_UPLOADED: HabitType.RECEIPT_DOCUMENTATION,
                ActionType.INVOICE_CREATED: HabitType.INVOICE_FOLLOW_UP,
                ActionType.BUDGET_REVIEWED: HabitType.WEEKLY_BUDGET_REVIEW,
                ActionType.PAYMENT_RECORDED: HabitType.INVOICE_FOLLOW_UP,
                ActionType.CATEGORY_ASSIGNED: HabitType.DAILY_EXPENSE_TRACKING
            }
            
            habit_type = habit_mapping.get(action_type)
            if not habit_type:
                return 1.0
            
            # Get current streak for this habit
            streak = self.db.query(UserStreak).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.habit_type == habit_type,
                    UserStreak.is_active == True
                )
            ).first()
            
            if not streak or streak.current_length == 0:
                return 1.0
            
            # Calculate multiplier: 1.0 + (streak_length * rate), capped at max
            multiplier = 1.0 + (streak.current_length * self.STREAK_MULTIPLIER_RATE)
            return min(multiplier, self.MAX_STREAK_MULTIPLIER)
            
        except Exception as e:
            logger.error(f"Error calculating streak multiplier: {str(e)}")
            return 1.0

    async def _calculate_accuracy_bonus(self, event: FinancialEvent) -> int:
        """Calculate accuracy bonus based on event metadata"""
        try:
            metadata = event.metadata or {}
            bonus = 0
            
            # Check each accuracy criterion
            for criterion, points in self.ACCURACY_BONUSES.items():
                if metadata.get(criterion, False):
                    bonus += points
                    logger.debug(f"Accuracy bonus: +{points} for {criterion}")
            
            return bonus
            
        except Exception as e:
            logger.error(f"Error calculating accuracy bonus: {str(e)}")
            return 0

    async def _calculate_completeness_bonus(self, event: FinancialEvent) -> int:
        """Calculate completeness bonus based on event metadata"""
        try:
            metadata = event.metadata or {}
            bonus = 0
            
            # Check each completeness criterion
            for criterion, points in self.COMPLETENESS_BONUSES.items():
                if metadata.get(criterion, False):
                    bonus += points
                    logger.debug(f"Completeness bonus: +{points} for {criterion}")
            
            return bonus
            
        except Exception as e:
            logger.error(f"Error calculating completeness bonus: {str(e)}")
            return 0

    async def _calculate_timeliness_bonus(self, event: FinancialEvent) -> int:
        """Calculate timeliness bonus for prompt actions"""
        try:
            metadata = event.metadata or {}
            bonus = 0
            
            # Timeliness bonuses for different action types
            if event.action_type == ActionType.EXPENSE_ADDED:
                # Bonus for adding expense on same day as transaction
                transaction_date = metadata.get("transaction_date")
                if transaction_date:
                    try:
                        if isinstance(transaction_date, str):
                            transaction_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
                        
                        # Check if expense was added within 24 hours of transaction
                        time_diff = event.timestamp - transaction_date
                        if time_diff <= timedelta(hours=24):
                            bonus += 3
                            logger.debug("Timeliness bonus: +3 for same-day expense entry")
                    except (ValueError, TypeError):
                        pass
            
            elif event.action_type == ActionType.INVOICE_CREATED:
                # Bonus for creating invoice promptly after work completion
                work_completion_date = metadata.get("work_completion_date")
                if work_completion_date:
                    try:
                        if isinstance(work_completion_date, str):
                            work_completion_date = datetime.fromisoformat(work_completion_date.replace('Z', '+00:00'))
                        
                        # Check if invoice was created within 3 days of work completion
                        time_diff = event.timestamp - work_completion_date
                        if time_diff <= timedelta(days=3):
                            bonus += 5
                            logger.debug("Timeliness bonus: +5 for prompt invoice creation")
                    except (ValueError, TypeError):
                        pass
            
            elif event.action_type == ActionType.PAYMENT_RECORDED:
                # Bonus for recording payment promptly after receipt
                payment_received_date = metadata.get("payment_received_date")
                if payment_received_date:
                    try:
                        if isinstance(payment_received_date, str):
                            payment_received_date = datetime.fromisoformat(payment_received_date.replace('Z', '+00:00'))
                        
                        # Check if payment was recorded within 2 days of receipt
                        time_diff = event.timestamp - payment_received_date
                        if time_diff <= timedelta(days=2):
                            bonus += 4
                            logger.debug("Timeliness bonus: +4 for prompt payment recording")
                    except (ValueError, TypeError):
                        pass
            
            return bonus
            
        except Exception as e:
            logger.error(f"Error calculating timeliness bonus: {str(e)}")
            return 0

    async def validate_point_award(
        self, 
        user_id: int, 
        action_type: ActionType, 
        event_metadata: Dict[str, Any]
    ) -> bool:
        """
        Validate that a point award is legitimate and not a duplicate.
        
        This helps prevent gaming the system or accidental double-awards.
        """
        try:
            # Check for potential duplicate events within a short time window
            recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            # For some action types, we need to be more strict about duplicates
            if action_type in [ActionType.EXPENSE_ADDED, ActionType.INVOICE_CREATED]:
                # Check if there's a very similar event recently
                # This would require checking against recent point history
                # For now, we'll implement basic validation
                pass
            
            # Validate metadata makes sense for the action type
            if action_type == ActionType.EXPENSE_ADDED:
                # Expense should have an amount
                if not event_metadata.get("amount"):
                    logger.warning(f"Expense added without amount for user {user_id}")
                    return False
            
            elif action_type == ActionType.INVOICE_CREATED:
                # Invoice should have a total
                if not event_metadata.get("total"):
                    logger.warning(f"Invoice created without total for user {user_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating point award: {str(e)}")
            return True  # Default to allowing the award on validation errors

    async def get_point_breakdown_explanation(self, breakdown: Dict[str, Any]) -> str:
        """Generate human-readable explanation of point calculation"""
        try:
            explanation_parts = []
            
            # Base points
            base = breakdown.get("base_points", 0)
            action = breakdown.get("action_type", "action")
            explanation_parts.append(f"{base} base points for {action.replace('_', ' ')}")
            
            # Streak multiplier
            multiplier = breakdown.get("streak_multiplier", 1.0)
            if multiplier > 1.0:
                streak_bonus = breakdown.get("multiplied_base", base) - base
                explanation_parts.append(f"+{streak_bonus} streak bonus ({multiplier:.1f}x multiplier)")
            
            # Accuracy bonus
            accuracy = breakdown.get("accuracy_bonus", 0)
            if accuracy > 0:
                explanation_parts.append(f"+{accuracy} accuracy bonus")
            
            # Completeness bonus
            completeness = breakdown.get("completeness_bonus", 0)
            if completeness > 0:
                explanation_parts.append(f"+{completeness} completeness bonus")
            
            # Timeliness bonus
            timeliness = breakdown.get("timeliness_bonus", 0)
            if timeliness > 0:
                explanation_parts.append(f"+{timeliness} timeliness bonus")
            
            total = breakdown.get("total_points", 0)
            explanation = " + ".join(explanation_parts) + f" = {total} total points"
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating point explanation: {str(e)}")
            return f"Earned {breakdown.get('total_points', 0)} points"