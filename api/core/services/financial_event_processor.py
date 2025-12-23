"""
Financial event processor for gamification integration.

This service processes financial events from the core finance app and routes them
to the gamification system for points, achievements, and habit tracking.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.schemas.gamification import ActionType, FinancialEvent
from core.services.gamification_service import GamificationService
from core.middleware.gamification_middleware import GamificationEventInterceptor

logger = logging.getLogger(__name__)


class FinancialEventProcessor:
    """
    Processes financial events and routes them to the gamification system.
    
    This service acts as a bridge between the core finance app and the gamification
    system, handling event creation, validation, and processing.
    """

    def __init__(self, db: Session):
        self.db = db
        self.gamification_service = GamificationService(db)
        self.event_interceptor = GamificationEventInterceptor(db)

    async def process_expense_added(
        self,
        user_id: int,
        expense_id: int,
        expense_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process an expense addition event.
        
        Args:
            user_id: The ID of the user who added the expense
            expense_id: The ID of the created expense
            expense_data: The expense data including amount, category, etc.
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "expense_id": expense_id,
                "vendor": expense_data.get("vendor"),
                "category": expense_data.get("category"),
                "amount": float(expense_data.get("amount", 0))
            }

            result = await self.event_interceptor.process_expense_event(
                user_id=user_id,
                action_type=ActionType.EXPENSE_ADDED,
                expense_data=expense_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing expense added event: {str(e)}", exc_info=True)
            return None

    async def process_receipt_uploaded(
        self,
        user_id: int,
        expense_id: int,
        attachment_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a receipt upload event.
        
        Args:
            user_id: The ID of the user who uploaded the receipt
            expense_id: The ID of the expense the receipt is attached to
            attachment_data: The attachment data
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "expense_id": expense_id,
                "attachment_id": attachment_data.get("id"),
                "file_type": attachment_data.get("file_type"),
                "file_size": attachment_data.get("file_size")
            }

            # Get the expense to pass its data
            from core.models.models_per_tenant import Expense
            expense = self.db.query(Expense).filter(Expense.id == expense_id).first()
            
            expense_data = {
                "amount": float(expense.amount) if expense else 0,
                "category": expense.category if expense else None
            }

            result = await self.event_interceptor.process_expense_event(
                user_id=user_id,
                action_type=ActionType.RECEIPT_UPLOADED,
                expense_data=expense_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing receipt uploaded event: {str(e)}", exc_info=True)
            return None

    async def process_expense_categorized(
        self,
        user_id: int,
        expense_id: int,
        category: str,
        expense_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process an expense categorization event.
        
        Args:
            user_id: The ID of the user who categorized the expense
            expense_id: The ID of the expense
            category: The category assigned
            expense_data: The expense data
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "expense_id": expense_id,
                "category": category,
                "amount": float(expense_data.get("amount", 0))
            }

            result = await self.event_interceptor.process_expense_event(
                user_id=user_id,
                action_type=ActionType.CATEGORY_ASSIGNED,
                expense_data=expense_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing expense categorized event: {str(e)}", exc_info=True)
            return None

    async def process_invoice_created(
        self,
        user_id: int,
        invoice_id: int,
        invoice_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process an invoice creation event.
        
        Args:
            user_id: The ID of the user who created the invoice
            invoice_id: The ID of the created invoice
            invoice_data: The invoice data including total, client, etc.
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "invoice_id": invoice_id,
                "client_id": invoice_data.get("client_id"),
                "invoice_number": invoice_data.get("invoice_number"),
                "total": float(invoice_data.get("total", 0))
            }

            result = await self.event_interceptor.process_invoice_event(
                user_id=user_id,
                action_type=ActionType.INVOICE_CREATED,
                invoice_data=invoice_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing invoice created event: {str(e)}", exc_info=True)
            return None

    async def process_invoice_reminder_sent(
        self,
        user_id: int,
        invoice_id: int,
        invoice_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process an invoice reminder sent event.
        
        Args:
            user_id: The ID of the user who sent the reminder
            invoice_id: The ID of the invoice
            invoice_data: The invoice data
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "invoice_id": invoice_id,
                "reminder_count": invoice_data.get("reminder_count", 1),
                "days_overdue": invoice_data.get("days_overdue", 0)
            }

            result = await self.event_interceptor.process_invoice_event(
                user_id=user_id,
                action_type=ActionType.INVOICE_CREATED,  # Using INVOICE_CREATED as proxy for reminder
                invoice_data=invoice_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing invoice reminder sent event: {str(e)}", exc_info=True)
            return None

    async def process_payment_recorded(
        self,
        user_id: int,
        invoice_id: int,
        payment_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a payment recording event.
        
        Args:
            user_id: The ID of the user who recorded the payment
            invoice_id: The ID of the invoice
            payment_data: The payment data including amount, date, etc.
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "invoice_id": invoice_id,
                "payment_id": payment_data.get("id"),
                "amount": float(payment_data.get("amount", 0)),
                "payment_date": payment_data.get("payment_date"),
                "is_on_time": payment_data.get("is_on_time", False)
            }

            result = await self.event_interceptor.process_invoice_event(
                user_id=user_id,
                action_type=ActionType.PAYMENT_RECORDED,
                invoice_data={"total": float(payment_data.get("amount", 0))},
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing payment recorded event: {str(e)}", exc_info=True)
            return None

    async def process_budget_reviewed(
        self,
        user_id: int,
        budget_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a budget review event.
        
        Args:
            user_id: The ID of the user who reviewed the budget
            budget_data: The budget data including categories, totals, etc.
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            metadata = {
                "review_date": datetime.now(timezone.utc).isoformat(),
                "categories_reviewed": len(budget_data.get("categories", [])),
                "total_budget": float(budget_data.get("total_budget", 0)),
                "total_spent": float(budget_data.get("total_spent", 0))
            }

            result = await self.event_interceptor.process_budget_event(
                user_id=user_id,
                action_type=ActionType.BUDGET_REVIEWED,
                budget_data=budget_data,
                metadata=metadata
            )

            return result

        except Exception as e:
            logger.error(f"Error processing budget reviewed event: {str(e)}", exc_info=True)
            return None

    async def process_generic_financial_event(
        self,
        user_id: int,
        action_type: ActionType,
        event_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a generic financial event.
        
        Args:
            user_id: The ID of the user performing the action
            action_type: The type of action
            event_data: The event data
            metadata: Additional metadata
            
        Returns:
            Gamification result if gamification is enabled, None otherwise
        """
        try:
            result = await self.event_interceptor.process_generic_event(
                user_id=user_id,
                action_type=action_type,
                event_data=event_data,
                metadata=metadata or {}
            )

            return result

        except Exception as e:
            logger.error(f"Error processing generic financial event: {str(e)}", exc_info=True)
            return None


def create_financial_event_processor(db: Session) -> FinancialEventProcessor:
    """Factory function to create a financial event processor"""
    return FinancialEventProcessor(db)
