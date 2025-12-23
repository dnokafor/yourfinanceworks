"""
Gamification middleware for intercepting financial events.

This middleware intercepts financial actions (expense creation, invoice creation, etc.)
and processes them through the gamification system when enabled for the user.
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.schemas.gamification import FinancialEvent, ActionType
from core.services.gamification_service import GamificationService

logger = logging.getLogger(__name__)


class GamificationEventInterceptor:
    """
    Intercepts financial events and processes them through the gamification system.
    
    This class provides methods to capture financial actions and route them to the
    gamification service for processing when gamification is enabled for the user.
    """

    def __init__(self, db: Session):
        self.db = db
        self.gamification_service = GamificationService(db)

    async def process_expense_event(
        self,
        user_id: int,
        action_type: ActionType,
        expense_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process an expense-related event through the gamification system.
        
        Args:
            user_id: The ID of the user performing the action
            action_type: The type of action (EXPENSE_ADDED, RECEIPT_UPLOADED, etc.)
            expense_data: The expense data
            metadata: Additional metadata about the event
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            # Check if gamification is enabled for this user
            if not await self.gamification_service.is_enabled_for_user(user_id):
                return None

            # Create the financial event
            event = FinancialEvent(
                user_id=user_id,
                action_type=action_type,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                category=expense_data.get("category"),
                amount=float(expense_data.get("amount", 0))
            )

            # Process the event through the gamification service
            result = await self.gamification_service.process_financial_event(event)

            if result:
                logger.info(
                    f"Gamification event processed for user {user_id}: "
                    f"action={action_type.value}, points={result.points_awarded}"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error processing gamification event for user {user_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - gamification failures shouldn't break the main flow
            return None

    async def process_invoice_event(
        self,
        user_id: int,
        action_type: ActionType,
        invoice_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process an invoice-related event through the gamification system.
        
        Args:
            user_id: The ID of the user performing the action
            action_type: The type of action (INVOICE_CREATED, PAYMENT_RECORDED, etc.)
            invoice_data: The invoice data
            metadata: Additional metadata about the event
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            # Check if gamification is enabled for this user
            if not await self.gamification_service.is_enabled_for_user(user_id):
                return None

            # Create the financial event
            event = FinancialEvent(
                user_id=user_id,
                action_type=action_type,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                amount=float(invoice_data.get("total", 0))
            )

            # Process the event through the gamification service
            result = await self.gamification_service.process_financial_event(event)

            if result:
                logger.info(
                    f"Gamification event processed for user {user_id}: "
                    f"action={action_type.value}, points={result.points_awarded}"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error processing gamification event for user {user_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - gamification failures shouldn't break the main flow
            return None

    async def process_budget_event(
        self,
        user_id: int,
        action_type: ActionType,
        budget_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a budget-related event through the gamification system.
        
        Args:
            user_id: The ID of the user performing the action
            action_type: The type of action (BUDGET_REVIEWED, etc.)
            budget_data: The budget data
            metadata: Additional metadata about the event
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            # Check if gamification is enabled for this user
            if not await self.gamification_service.is_enabled_for_user(user_id):
                return None

            # Create the financial event
            event = FinancialEvent(
                user_id=user_id,
                action_type=action_type,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )

            # Process the event through the gamification service
            result = await self.gamification_service.process_financial_event(event)

            if result:
                logger.info(
                    f"Gamification event processed for user {user_id}: "
                    f"action={action_type.value}, points={result.points_awarded}"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error processing gamification event for user {user_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - gamification failures shouldn't break the main flow
            return None

    async def process_generic_event(
        self,
        user_id: int,
        action_type: ActionType,
        event_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a generic financial event through the gamification system.
        
        Args:
            user_id: The ID of the user performing the action
            action_type: The type of action
            event_data: The event data
            metadata: Additional metadata about the event
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            # Check if gamification is enabled for this user
            if not await self.gamification_service.is_enabled_for_user(user_id):
                return None

            # Create the financial event
            event = FinancialEvent(
                user_id=user_id,
                action_type=action_type,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                category=event_data.get("category"),
                amount=float(event_data.get("amount", 0)) if event_data.get("amount") else None
            )

            # Process the event through the gamification service
            result = await self.gamification_service.process_financial_event(event)

            if result:
                logger.info(
                    f"Gamification event processed for user {user_id}: "
                    f"action={action_type.value}, points={result.points_awarded}"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error processing gamification event for user {user_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - gamification failures shouldn't break the main flow
            return None


def create_gamification_interceptor(db: Session) -> GamificationEventInterceptor:
    """Factory function to create a gamification event interceptor"""
    return GamificationEventInterceptor(db)
