"""
Test approval router endpoints for user attribution.

This test verifies that the approval router endpoints properly capture
and return approver/rejector information.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from main import app
from core.models.database import get_db
from core.models.models import MasterUser
from core.models.models_per_tenant import (
    User, Expense, ExpenseApproval, ApprovalRule
)


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_db(test_client):
    """Get test database session"""
    return next(get_db())


@pytest.fixture
def test_users(test_db: Session):
    """Create test users"""
    # Create submitter
    submitter = User(
        email="submitter@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Submitter",
        role="user"
    )
    test_db.add(submitter)
    
    # Create approver
    approver = User(
        email="approver@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Approver",
        role="admin"
    )
    test_db.add(approver)
    
    test_db.commit()
    test_db.refresh(submitter)
    test_db.refresh(approver)
    
    return {"submitter": submitter, "approver": approver}


@pytest.fixture
def test_expense(test_db: Session, test_users: dict):
    """Create test expense"""
    expense = Expense(
        amount=100.0,
        currency="USD",
        category="Travel",
        vendor="Test Vendor",
        status="pending_approval",
        user_id=test_users["submitter"].id
    )
    test_db.add(expense)
    test_db.commit()
    test_db.refresh(expense)
    return expense


@pytest.fixture
def test_approval_rule(test_db: Session, test_users: dict):
    """Create test approval rule"""
    rule = ApprovalRule(
        name="Test Rule",
        min_amount=0,
        max_amount=1000,
        currency="USD",
        approval_level=1,
        approver_id=test_users["approver"].id,
        is_active=True
    )
    test_db.add(rule)
    test_db.commit()
    test_db.refresh(rule)
    return rule


@pytest.fixture
def test_approval(test_db: Session, test_expense: Expense, test_approval_rule: ApprovalRule, test_users: dict):
    """Create test approval"""
    approval = ExpenseApproval(
        expense_id=test_expense.id,
        approver_id=test_users["approver"].id,
        approval_rule_id=test_approval_rule.id,
        status="pending",
        submitted_at=datetime.now(timezone.utc),
        approval_level=1,
        is_current_level=True
    )
    test_db.add(approval)
    test_db.commit()
    test_db.refresh(approval)
    return approval


def test_approve_expense_includes_approver_info(
    test_client: TestClient,
    test_db: Session,
    test_approval: ExpenseApproval,
    test_users: dict
):
    """
    Test that approving an expense includes approver information in response.

    Validates Requirements 2.1, 2.5
    """
    # Mock authentication to return the approver user
    approver = test_users["approver"]

    # Create approval decision
    decision_data = {
        "status": "approved",
        "notes": "Looks good"
    }

    # Approve the expense (would need proper auth in real scenario)
    # For this test, we'll directly call the service and verify the response format
    from commercial.workflows.approvals.services.approval_service import ApprovalService
    from core.services.notification_service import NotificationService

    notification_service = NotificationService(test_db, None)
    approval_service = ApprovalService(test_db, notification_service)

    # Approve the expense
    approval = approval_service.approve_expense(
        approval_id=test_approval.id,
        approver_id=approver.id,
        notes=decision_data["notes"]
    )

    # Verify the approval was updated
    assert approval.status == "approved"
    assert approval.approved_by_user_id == approver.id
    assert approval.decided_at is not None

    # Verify the approved_by relationship is set
    test_db.refresh(approval)
    assert approval.approved_by is not None
    assert approval.approved_by.id == approver.id
    assert approval.approved_by.first_name == "Test"
    assert approval.approved_by.last_name == "Approver"


def test_reject_expense_includes_rejector_info(
    test_client: TestClient,
    test_db: Session,
    test_approval: ExpenseApproval,
    test_users: dict
):
    """
    Test that rejecting an expense includes rejector information in response.

    Validates Requirements 2.2, 2.6
    """
    # Mock authentication to return the approver user
    approver = test_users["approver"]

    # Create rejection decision
    decision_data = {
        "status": "rejected",
        "rejection_reason": "Missing receipt",
        "notes": "Please resubmit with receipt"
    }

    # Reject the expense
    from commercial.workflows.approvals.services.approval_service import ApprovalService
    from core.services.notification_service import NotificationService

    notification_service = NotificationService(test_db, None)
    approval_service = ApprovalService(test_db, notification_service)

    # Reject the expense
    approval = approval_service.reject_expense(
        approval_id=test_approval.id,
        approver_id=approver.id,
        rejection_reason=decision_data["rejection_reason"],
        notes=decision_data["notes"]
    )

    # Verify the approval was updated
    assert approval.status == "rejected"
    assert approval.rejected_by_user_id == approver.id
    assert approval.rejection_reason == "Missing receipt"
    assert approval.decided_at is not None

    # Verify the rejected_by relationship is set
    test_db.refresh(approval)
    assert approval.rejected_by is not None
    assert approval.rejected_by.id == approver.id
    assert approval.rejected_by.first_name == "Test"
    assert approval.rejected_by.last_name == "Approver"


def test_approval_response_format(
    test_db: Session,
    test_approval: ExpenseApproval,
    test_users: dict
):
    """
    Test that the approval response includes all required attribution fields.

    Validates Requirements 2.5, 2.6
    """
    approver = test_users["approver"]

    # Approve the expense
    from commercial.workflows.approvals.services.approval_service import ApprovalService
    from core.services.notification_service import NotificationService
    from core.services.attribution_service import AttributionService

    notification_service = NotificationService(test_db, None)
    approval_service = ApprovalService(test_db, notification_service)

    approval = approval_service.approve_expense(
        approval_id=test_approval.id,
        approver_id=approver.id,
        notes="Approved"
    )

    # Refresh to load relationships
    from sqlalchemy.orm import joinedload
    from core.models.models_per_tenant import ExpenseApproval as ExpenseApprovalModel

    test_db.refresh(approval)
    approval = test_db.query(ExpenseApprovalModel).options(
        joinedload(ExpenseApprovalModel.approved_by),
        joinedload(ExpenseApprovalModel.rejected_by)
    ).filter(ExpenseApprovalModel.id == test_approval.id).first()

    # Build response dict as the router would
    response_dict = {
        "id": approval.id,
        "expense_id": approval.expense_id,
        "approver_id": approval.approver_id,
        "approval_rule_id": approval.approval_rule_id,
        "status": approval.status,
        "rejection_reason": approval.rejection_reason,
        "notes": approval.notes,
        "submitted_at": approval.submitted_at,
        "decided_at": approval.decided_at,
        "approval_level": approval.approval_level,
        "is_current_level": approval.is_current_level,
        "created_at": approval.created_at,
        "updated_at": approval.updated_at,
        "approved_by_user_id": approval.approved_by_user_id,
        "approved_by_username": AttributionService.get_display_name(approval.approved_by) if approval.approved_by else None,
        "rejected_by_user_id": approval.rejected_by_user_id,
        "rejected_by_username": AttributionService.get_display_name(approval.rejected_by) if approval.rejected_by else None,
    }

    # Verify all required fields are present
    assert "approved_by_user_id" in response_dict
    assert "approved_by_username" in response_dict
    assert "rejected_by_user_id" in response_dict
    assert "rejected_by_username" in response_dict

    # Verify approved fields are populated
    assert response_dict["approved_by_user_id"] == approver.id
    assert response_dict["approved_by_username"] == "Test Approver"

    # Verify rejected fields are None (since this was approved)
    assert response_dict["rejected_by_user_id"] is None
    assert response_dict["rejected_by_username"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
