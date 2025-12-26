"""
Tests for gamification event processing and middleware integration.

These tests verify that financial events are properly intercepted and processed
through the gamification system.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

from core.schemas.gamification import ActionType, FinancialEvent, GamificationResult
from core.services.financial_event_processor import FinancialEventProcessor
from core.middleware.gamification_middleware import GamificationEventInterceptor
from core.models.gamification import UserGamificationProfile


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def event_processor(mock_db):
    """Create a financial event processor with mocked dependencies"""
    with patch('core.services.financial_event_processor.GamificationService'):
        with patch('core.services.financial_event_processor.GamificationEventInterceptor'):
            processor = FinancialEventProcessor(mock_db)
            processor.gamification_service = AsyncMock()
            processor.event_interceptor = AsyncMock()
            return processor


@pytest.fixture
def event_interceptor(mock_db):
    """Create a gamification event interceptor with mocked dependencies"""
    with patch('core.middleware.gamification_middleware.GamificationService'):
        interceptor = GamificationEventInterceptor(mock_db)
        interceptor.gamification_service = AsyncMock()
        return interceptor


class TestFinancialEventProcessor:
    """Tests for the FinancialEventProcessor"""

    @pytest.mark.asyncio
    async def test_process_expense_added(self, event_processor):
        """Test processing an expense added event"""
        # Setup
        user_id = 1
        expense_id = 100
        expense_data = {
            "vendor": "Acme Corp",
            "category": "Office Supplies",
            "amount": 150.00
        }
        
        expected_result = {
            "points_awarded": 10,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_processor.event_interceptor.process_expense_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_processor.process_expense_added(user_id, expense_id, expense_data)
        
        # Assert
        assert result == expected_result
        event_processor.event_interceptor.process_expense_event.assert_called_once()
        
        # Verify the call arguments
        call_args = event_processor.event_interceptor.process_expense_event.call_args
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["action_type"] == ActionType.EXPENSE_ADDED
        assert call_args[1]["metadata"]["expense_id"] == expense_id

    @pytest.mark.asyncio
    async def test_process_receipt_uploaded(self, event_processor):
        """Test processing a receipt upload event"""
        # Setup
        user_id = 1
        expense_id = 100
        attachment_data = {
            "id": 1,
            "file_type": "image/jpeg",
            "file_size": 2048
        }
        
        expected_result = {
            "points_awarded": 3,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_processor.event_interceptor.process_expense_event = AsyncMock(
            return_value=expected_result
        )
        
        # Mock the expense query
        mock_expense = Mock()
        mock_expense.amount = 150.00
        mock_expense.category = "Office Supplies"
        event_processor.db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        # Execute
        result = await event_processor.process_receipt_uploaded(user_id, expense_id, attachment_data)
        
        # Assert
        assert result == expected_result
        event_processor.event_interceptor.process_expense_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_invoice_created(self, event_processor):
        """Test processing an invoice creation event"""
        # Setup
        user_id = 1
        invoice_id = 50
        invoice_data = {
            "client_id": 10,
            "invoice_number": "INV-001",
            "total": 500.00
        }
        
        expected_result = {
            "points_awarded": 15,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_processor.event_interceptor.process_invoice_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_processor.process_invoice_created(user_id, invoice_id, invoice_data)
        
        # Assert
        assert result == expected_result
        event_processor.event_interceptor.process_invoice_event.assert_called_once()
        
        # Verify the call arguments
        call_args = event_processor.event_interceptor.process_invoice_event.call_args
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["action_type"] == ActionType.INVOICE_CREATED
        assert call_args[1]["metadata"]["invoice_id"] == invoice_id

    @pytest.mark.asyncio
    async def test_process_payment_recorded(self, event_processor):
        """Test processing a payment recording event"""
        # Setup
        user_id = 1
        invoice_id = 50
        payment_data = {
            "id": 1,
            "amount": 500.00,
            "payment_date": datetime.now(timezone.utc),
            "is_on_time": True
        }
        
        expected_result = {
            "points_awarded": 12,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_processor.event_interceptor.process_invoice_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_processor.process_payment_recorded(user_id, invoice_id, payment_data)
        
        # Assert
        assert result == expected_result
        event_processor.event_interceptor.process_invoice_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_budget_reviewed(self, event_processor):
        """Test processing a budget review event"""
        # Setup
        user_id = 1
        budget_data = {
            "categories": ["Office", "Travel", "Meals"],
            "total_budget": 5000.00,
            "total_spent": 3500.00
        }
        
        expected_result = {
            "points_awarded": 20,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_processor.event_interceptor.process_budget_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_processor.process_budget_reviewed(user_id, budget_data)
        
        # Assert
        assert result == expected_result
        event_processor.event_interceptor.process_budget_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_event_handles_exceptions(self, event_processor):
        """Test that event processing handles exceptions gracefully"""
        # Setup
        user_id = 1
        expense_id = 100
        expense_data = {"vendor": "Test", "category": "Test", "amount": 100}
        
        event_processor.event_interceptor.process_expense_event = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        # Execute
        result = await event_processor.process_expense_added(user_id, expense_id, expense_data)
        
        # Assert - should return None on error
        assert result is None


class TestGamificationEventInterceptor:
    """Tests for the GamificationEventInterceptor"""

    @pytest.mark.asyncio
    async def test_process_expense_event_when_enabled(self, event_interceptor):
        """Test processing an expense event when gamification is enabled"""
        # Setup
        user_id = 1
        action_type = ActionType.EXPENSE_ADDED
        expense_data = {"vendor": "Test", "category": "Office", "amount": 100}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=True)
        
        expected_result = {
            "points_awarded": 10,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_interceptor.gamification_service.process_financial_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_interceptor.process_expense_event(
            user_id, action_type, expense_data
        )
        
        # Assert
        assert result == expected_result
        event_interceptor.gamification_service.process_financial_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_expense_event_when_disabled(self, event_interceptor):
        """Test processing an expense event when gamification is disabled"""
        # Setup
        user_id = 1
        action_type = ActionType.EXPENSE_ADDED
        expense_data = {"vendor": "Test", "category": "Office", "amount": 100}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=False)
        
        # Execute
        result = await event_interceptor.process_expense_event(
            user_id, action_type, expense_data
        )
        
        # Assert
        assert result is None
        event_interceptor.gamification_service.process_financial_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_invoice_event(self, event_interceptor):
        """Test processing an invoice event"""
        # Setup
        user_id = 1
        action_type = ActionType.INVOICE_CREATED
        invoice_data = {"client_id": 10, "total": 500}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=True)
        
        expected_result = {
            "points_awarded": 15,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_interceptor.gamification_service.process_financial_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_interceptor.process_invoice_event(
            user_id, action_type, invoice_data
        )
        
        # Assert
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_process_budget_event(self, event_interceptor):
        """Test processing a budget event"""
        # Setup
        user_id = 1
        action_type = ActionType.BUDGET_REVIEWED
        budget_data = {"total_budget": 5000, "total_spent": 3500}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=True)
        
        expected_result = {
            "points_awarded": 20,
            "achievements_unlocked": [],
            "celebration_triggered": False
        }
        
        event_interceptor.gamification_service.process_financial_event = AsyncMock(
            return_value=expected_result
        )
        
        # Execute
        result = await event_interceptor.process_budget_event(
            user_id, action_type, budget_data
        )
        
        # Assert
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_event_interceptor_handles_exceptions(self, event_interceptor):
        """Test that event interceptor handles exceptions gracefully"""
        # Setup
        user_id = 1
        action_type = ActionType.EXPENSE_ADDED
        expense_data = {"vendor": "Test", "category": "Office", "amount": 100}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=True)
        event_interceptor.gamification_service.process_financial_event = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        # Execute
        result = await event_interceptor.process_expense_event(
            user_id, action_type, expense_data
        )
        
        # Assert - should return None on error
        assert result is None


class TestEventCreation:
    """Tests for financial event creation"""

    @pytest.mark.asyncio
    async def test_financial_event_creation(self, event_interceptor):
        """Test that financial events are created correctly"""
        # Setup
        user_id = 1
        action_type = ActionType.EXPENSE_ADDED
        expense_data = {"vendor": "Test", "category": "Office", "amount": 100}
        metadata = {"expense_id": 1}
        
        event_interceptor.gamification_service.is_enabled_for_user = AsyncMock(return_value=True)
        
        # Capture the event passed to process_financial_event
        captured_event = None
        
        async def capture_event(event):
            nonlocal captured_event
            captured_event = event
            return None
        
        event_interceptor.gamification_service.process_financial_event = AsyncMock(
            side_effect=capture_event
        )
        
        # Execute
        await event_interceptor.process_expense_event(
            user_id, action_type, expense_data, metadata
        )
        
        # Assert
        assert captured_event is not None
        assert captured_event.user_id == user_id
        assert captured_event.action_type == action_type
        assert captured_event.category == "Office"
        assert captured_event.amount == 100
        assert captured_event.metadata == metadata
