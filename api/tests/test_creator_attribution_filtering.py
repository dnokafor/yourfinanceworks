"""
Test creator attribution filtering across all endpoints.

This test verifies that the created_by_user_id filter parameter is accepted
by all relevant endpoints.
"""

import pytest


def test_invoice_endpoint_accepts_creator_filter():
    """Test that invoice endpoint accepts created_by_user_id parameter"""
    # This is a simple smoke test to verify the parameter is accepted
    # Full integration tests would require extensive setup
    from fastapi import Query
    from typing import Optional
    from core.routers.invoices import read_invoices
    import inspect
    
    # Get the function signature
    sig = inspect.signature(read_invoices)
    params = sig.parameters
    
    # Verify created_by_user_id parameter exists
    assert 'created_by_user_id' in params
    
    # Verify it's Optional[int]
    param = params['created_by_user_id']
    assert param.default is None


def test_expense_endpoint_accepts_creator_filter():
    """Test that expense endpoint accepts created_by_user_id parameter"""
    from core.routers.expenses import list_expenses
    import inspect
    
    # Get the function signature
    sig = inspect.signature(list_expenses)
    params = sig.parameters
    
    # Verify created_by_user_id parameter exists
    assert 'created_by_user_id' in params
    
    # Verify it's Optional[int]
    param = params['created_by_user_id']
    assert param.default is None


def test_statement_endpoint_accepts_creator_filter():
    """Test that statement endpoint accepts created_by_user_id parameter"""
    from core.routers.statements import list_statements
    import inspect
    
    # Get the function signature
    sig = inspect.signature(list_statements)
    params = sig.parameters
    
    # Verify created_by_user_id parameter exists
    assert 'created_by_user_id' in params
    
    # Verify it's Optional[int]
    param = params['created_by_user_id']
    assert param.default is None


def test_reminder_endpoint_accepts_creator_filter():
    """Test that reminder endpoint accepts created_by_id parameter"""
    from core.routers.reminders import get_reminders
    import inspect
    
    # Get the function signature
    sig = inspect.signature(get_reminders)
    params = sig.parameters
    
    # Verify created_by_id parameter exists (note: reminders use created_by_id not created_by_user_id)
    assert 'created_by_id' in params
    
    # Verify it's Optional[int]
    param = params['created_by_id']
    # For Query parameters, check the annotation
    assert 'Optional' in str(param.annotation) or param.default is None
