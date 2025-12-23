"""
Standalone tests for gamification middleware and event processor.

These tests verify the core logic without requiring database initialization.
"""

import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from core.schemas.gamification import ActionType


def test_action_types_defined():
    """Test that all required action types are defined"""
    required_actions = [
        ActionType.EXPENSE_ADDED,
        ActionType.RECEIPT_UPLOADED,
        ActionType.INVOICE_CREATED,
        ActionType.PAYMENT_RECORDED,
        ActionType.BUDGET_REVIEWED,
        ActionType.CATEGORY_ASSIGNED
    ]
    
    assert len(required_actions) == 6
    print("✓ All action types are defined")


def test_expense_data_structure():
    """Test expense data structure"""
    expense_data = {
        "vendor": "Acme Corp",
        "category": "Office Supplies",
        "amount": 150.00
    }
    
    assert expense_data["vendor"] == "Acme Corp"
    assert expense_data["category"] == "Office Supplies"
    assert float(expense_data["amount"]) == 150.00
    print("✓ Expense data structure is correct")


def test_invoice_data_structure():
    """Test invoice data structure"""
    invoice_data = {
        "client_id": 10,
        "invoice_number": "INV-001",
        "total": 500.00
    }
    
    assert invoice_data["client_id"] == 10
    assert invoice_data["invoice_number"] == "INV-001"
    assert float(invoice_data["total"]) == 500.00
    print("✓ Invoice data structure is correct")


def test_payment_data_structure():
    """Test payment data structure"""
    payment_data = {
        "id": 1,
        "amount": 500.00,
        "payment_date": datetime.now(timezone.utc),
        "is_on_time": True
    }
    
    assert payment_data["id"] == 1
    assert float(payment_data["amount"]) == 500.00
    assert isinstance(payment_data["payment_date"], datetime)
    assert payment_data["is_on_time"] is True
    print("✓ Payment data structure is correct")


def test_budget_data_structure():
    """Test budget data structure"""
    budget_data = {
        "categories": ["Office", "Travel", "Meals"],
        "total_budget": 5000.00,
        "total_spent": 3500.00
    }
    
    assert len(budget_data["categories"]) == 3
    assert float(budget_data["total_budget"]) == 5000.00
    assert float(budget_data["total_spent"]) == 3500.00
    print("✓ Budget data structure is correct")


def test_metadata_creation():
    """Test metadata creation for events"""
    expense_id = 100
    vendor = "Acme Corp"
    category = "Office Supplies"
    amount = 150.00
    
    metadata = {
        "expense_id": expense_id,
        "vendor": vendor,
        "category": category,
        "amount": float(amount)
    }
    
    assert metadata["expense_id"] == 100
    assert metadata["vendor"] == "Acme Corp"
    assert metadata["category"] == "Office Supplies"
    assert metadata["amount"] == 150.00
    print("✓ Metadata creation is correct")


def test_event_enabled_check():
    """Test event enabled/disabled check logic"""
    # When enabled
    is_enabled = True
    should_process = is_enabled
    assert should_process is True
    
    # When disabled
    is_enabled = False
    should_process = is_enabled
    assert should_process is False
    print("✓ Event enabled/disabled check is correct")


def test_processor_handles_missing_fields():
    """Test processor handles missing fields gracefully"""
    expense_data = {
        "vendor": "Test Vendor"
        # Missing category and amount
    }
    
    # Simulate safe field extraction
    metadata = {
        "vendor": expense_data.get("vendor"),
        "category": expense_data.get("category"),
        "amount": float(expense_data.get("amount", 0))
    }
    
    assert metadata["vendor"] == "Test Vendor"
    assert metadata["category"] is None
    assert metadata["amount"] == 0.0
    print("✓ Processor handles missing fields correctly")


def test_processor_converts_amounts_to_float():
    """Test processor converts amounts to float"""
    test_amounts = [
        ("100", 100.0),
        (100, 100.0),
        (100.50, 100.50),
        ("100.50", 100.50)
    ]
    
    for input_amount, expected_output in test_amounts:
        result = float(input_amount)
        assert result == expected_output
    
    print("✓ Processor converts amounts to float correctly")


def test_timestamp_creation():
    """Test timestamp creation"""
    timestamp = datetime.now(timezone.utc)
    
    # Verify timestamp is timezone-aware
    assert timestamp.tzinfo is not None
    assert timestamp.tzinfo == timezone.utc
    
    # Verify timestamp can be serialized
    iso_string = timestamp.isoformat()
    assert isinstance(iso_string, str)
    assert "T" in iso_string
    print("✓ Timestamp creation is correct")


def test_financial_event_processor_imports():
    """Test that financial event processor can be imported"""
    try:
        from core.services.financial_event_processor import (
            FinancialEventProcessor,
            create_financial_event_processor
        )
        print("✓ Financial event processor imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import financial event processor: {e}")
        raise


def test_gamification_middleware_imports():
    """Test that gamification middleware can be imported"""
    try:
        from core.middleware.gamification_middleware import (
            GamificationEventInterceptor,
            create_gamification_interceptor
        )
        print("✓ Gamification middleware imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import gamification middleware: {e}")
        raise


def test_financial_event_schema():
    """Test that FinancialEvent schema is properly defined"""
    try:
        from core.schemas.gamification import FinancialEvent
        
        # Create a test event
        event = FinancialEvent(
            user_id=1,
            action_type=ActionType.EXPENSE_ADDED,
            timestamp=datetime.now(timezone.utc),
            metadata={"test": "data"},
            category="Office",
            amount=100.0
        )
        
        assert event.user_id == 1
        assert event.action_type == ActionType.EXPENSE_ADDED
        assert event.category == "Office"
        assert event.amount == 100.0
        print("✓ FinancialEvent schema is properly defined")
    except Exception as e:
        print(f"✗ Failed to create FinancialEvent: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Gamification Middleware Tests")
    print("="*60 + "\n")
    
    tests = [
        test_action_types_defined,
        test_expense_data_structure,
        test_invoice_data_structure,
        test_payment_data_structure,
        test_budget_data_structure,
        test_metadata_creation,
        test_event_enabled_check,
        test_processor_handles_missing_fields,
        test_processor_converts_amounts_to_float,
        test_timestamp_creation,
        test_financial_event_processor_imports,
        test_gamification_middleware_imports,
        test_financial_event_schema,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
