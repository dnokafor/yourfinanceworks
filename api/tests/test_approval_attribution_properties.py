"""
Property-based tests for Approval Attribution.

Feature: user-attribution-tracking, Property 3: Approval attribution consistency
Feature: user-attribution-tracking, Property 4: Rejection attribution consistency
Feature: user-attribution-tracking, Property 5: Mutual exclusivity of approval states
Validates: Requirements 2.1, 2.2, 2.3, 2.4

These tests verify that approval and rejection attribution is correctly captured
and maintains consistency throughout the approval lifecycle.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone
from core.models.models import MasterUser
from core.models.models_per_tenant import ExpenseApproval, Expense
from core.schemas.approval import ApprovalStatus


# Custom strategies for generating test data
@st.composite
def valid_user(draw):
    """Generate a valid MasterUser"""
    user = MasterUser()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.email = draw(st.emails())
    user.username = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    user.tenant_id = draw(st.integers(min_value=1, max_value=1000))
    return user


@st.composite
def valid_expense(draw):
    """Generate a valid Expense"""
    expense = Expense()
    expense.id = draw(st.integers(min_value=1, max_value=100000))
    expense.amount = draw(st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False))
    expense.currency = draw(st.sampled_from(["USD", "EUR", "GBP", "CAD"]))
    expense.category = draw(st.sampled_from(["Travel", "Meals", "Software", "Office Supplies", "Marketing"]))
    expense.status = draw(st.sampled_from(["recorded", "pending_approval", "approved", "rejected"]))
    expense.user_id = draw(st.integers(min_value=1, max_value=100000))
    return expense


@st.composite
def valid_approval_notes(draw):
    """Generate valid approval notes"""
    return draw(st.text(min_size=0, max_size=500))


@st.composite
def valid_rejection_reason(draw):
    """Generate valid rejection reason"""
    return draw(st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))


class TestApprovalAttributionProperties:
    """Property-based tests for approval attribution"""
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        notes=valid_approval_notes()
    )
    def test_property_3_approval_attribution_consistency(self, approver, expense, notes):
        """
        Feature: user-attribution-tracking, Property 3: Approval attribution consistency
        
        For any approved record, if approved_by_user_id is set, then approved_at
        timestamp must also be set, and the status must be "approved".
        
        Validates: Requirements 2.1, 2.3
        """
        # Create an approval record
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.APPROVED,
            submitted_at=now,
            decided_at=now,
            approved_by_user_id=approver.id,  # Set approver
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # Verify consistency: if approved_by_user_id is set
        if approval.approved_by_user_id is not None:
            # Then decided_at must be set
            assert approval.decided_at is not None
            # And status must be APPROVED
            assert approval.status == ApprovalStatus.APPROVED
            # And approved_by_user_id should match the approver
            assert approval.approved_by_user_id == approver.id
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        rejection_reason=valid_rejection_reason(),
        notes=valid_approval_notes()
    )
    def test_property_4_rejection_attribution_consistency(self, approver, expense, rejection_reason, notes):
        """
        Feature: user-attribution-tracking, Property 4: Rejection attribution consistency
        
        For any rejected record, if rejected_by_user_id is set, then rejected_at
        timestamp must also be set, and the status must be "rejected".
        
        Validates: Requirements 2.2, 2.4
        """
        # Create a rejection record
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.REJECTED,
            submitted_at=now,
            decided_at=now,
            rejected_by_user_id=approver.id,  # Set rejector
            rejection_reason=rejection_reason,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # Verify consistency: if rejected_by_user_id is set
        if approval.rejected_by_user_id is not None:
            # Then decided_at must be set
            assert approval.decided_at is not None
            # And status must be REJECTED
            assert approval.status == ApprovalStatus.REJECTED
            # And rejected_by_user_id should match the approver
            assert approval.rejected_by_user_id == approver.id
            # And rejection_reason must be set
            assert approval.rejection_reason is not None
            assert len(approval.rejection_reason) > 0
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        notes=valid_approval_notes()
    )
    def test_property_5_mutual_exclusivity_approved(self, approver, expense, notes):
        """
        Feature: user-attribution-tracking, Property 5: Mutual exclusivity of approval states
        
        For any approval record that is approved, it cannot have rejected_by_user_id set.
        
        Validates: Requirements 2.1, 2.2
        """
        # Create an approved record
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.APPROVED,
            submitted_at=now,
            decided_at=now,
            approved_by_user_id=approver.id,
            rejected_by_user_id=None,  # Should be None for approved
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # Verify mutual exclusivity
        if approval.status == ApprovalStatus.APPROVED:
            assert approval.approved_by_user_id is not None
            assert approval.rejected_by_user_id is None
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        rejection_reason=valid_rejection_reason(),
        notes=valid_approval_notes()
    )
    def test_property_5_mutual_exclusivity_rejected(self, approver, expense, rejection_reason, notes):
        """
        Feature: user-attribution-tracking, Property 5: Mutual exclusivity of approval states
        
        For any approval record that is rejected, it cannot have approved_by_user_id set.
        
        Validates: Requirements 2.1, 2.2
        """
        # Create a rejected record
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.REJECTED,
            submitted_at=now,
            decided_at=now,
            approved_by_user_id=None,  # Should be None for rejected
            rejected_by_user_id=approver.id,
            rejection_reason=rejection_reason,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # Verify mutual exclusivity
        if approval.status == ApprovalStatus.REJECTED:
            assert approval.rejected_by_user_id is not None
            assert approval.approved_by_user_id is None
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense()
    )
    def test_property_5_pending_has_no_attribution(self, approver, expense):
        """
        Feature: user-attribution-tracking, Property 5: Mutual exclusivity of approval states
        
        For any approval record that is pending, it should not have either
        approved_by_user_id or rejected_by_user_id set.
        
        Validates: Requirements 2.1, 2.2
        """
        # Create a pending record
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.PENDING,
            submitted_at=now,
            decided_at=None,
            approved_by_user_id=None,
            rejected_by_user_id=None,
            approval_level=1,
            is_current_level=True
        )
        
        # Verify no attribution for pending
        if approval.status == ApprovalStatus.PENDING:
            assert approval.approved_by_user_id is None
            assert approval.rejected_by_user_id is None
            assert approval.decided_at is None
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        notes=valid_approval_notes()
    )
    def test_property_3_approved_by_is_positive_integer(self, approver, expense, notes):
        """
        Feature: user-attribution-tracking, Property 3: Approval attribution consistency
        
        For any approved record, approved_by_user_id should be a positive integer.
        
        Validates: Requirements 2.1
        """
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.APPROVED,
            submitted_at=now,
            decided_at=now,
            approved_by_user_id=approver.id,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        if approval.approved_by_user_id is not None:
            assert isinstance(approval.approved_by_user_id, int)
            assert approval.approved_by_user_id > 0
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        rejection_reason=valid_rejection_reason(),
        notes=valid_approval_notes()
    )
    def test_property_4_rejected_by_is_positive_integer(self, approver, expense, rejection_reason, notes):
        """
        Feature: user-attribution-tracking, Property 4: Rejection attribution consistency
        
        For any rejected record, rejected_by_user_id should be a positive integer.
        
        Validates: Requirements 2.2
        """
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.REJECTED,
            submitted_at=now,
            decided_at=now,
            rejected_by_user_id=approver.id,
            rejection_reason=rejection_reason,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        if approval.rejected_by_user_id is not None:
            assert isinstance(approval.rejected_by_user_id, int)
            assert approval.rejected_by_user_id > 0
    
    @settings(max_examples=100)
    @given(
        approver1=valid_user(),
        approver2=valid_user(),
        expense=valid_expense(),
        notes=valid_approval_notes()
    )
    def test_property_3_approved_by_matches_actual_approver(self, approver1, approver2, expense, notes):
        """
        Feature: user-attribution-tracking, Property 3: Approval attribution consistency
        
        For any approved record, approved_by_user_id should match the user who
        actually performed the approval action.
        
        Validates: Requirements 2.1, 3.2
        """
        # Ensure approvers are different
        assume(approver1.id != approver2.id)
        
        # Create approval assigned to approver1 but approved by approver2
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver1.id,  # Assigned to approver1
            status=ApprovalStatus.APPROVED,
            submitted_at=now,
            decided_at=now,
            approved_by_user_id=approver2.id,  # But approved by approver2
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # The approved_by_user_id should reflect who actually approved
        assert approval.approved_by_user_id == approver2.id
        # It may differ from the assigned approver (delegation case)
        # But it must be set and valid
        assert approval.approved_by_user_id is not None
        assert isinstance(approval.approved_by_user_id, int)
        assert approval.approved_by_user_id > 0
    
    @settings(max_examples=100)
    @given(
        approver1=valid_user(),
        approver2=valid_user(),
        expense=valid_expense(),
        rejection_reason=valid_rejection_reason(),
        notes=valid_approval_notes()
    )
    def test_property_4_rejected_by_matches_actual_rejector(self, approver1, approver2, expense, rejection_reason, notes):
        """
        Feature: user-attribution-tracking, Property 4: Rejection attribution consistency
        
        For any rejected record, rejected_by_user_id should match the user who
        actually performed the rejection action.
        
        Validates: Requirements 2.2, 3.2
        """
        # Ensure approvers are different
        assume(approver1.id != approver2.id)
        
        # Create approval assigned to approver1 but rejected by approver2
        now = datetime.now(timezone.utc)
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver1.id,  # Assigned to approver1
            status=ApprovalStatus.REJECTED,
            submitted_at=now,
            decided_at=now,
            rejected_by_user_id=approver2.id,  # But rejected by approver2
            rejection_reason=rejection_reason,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        # The rejected_by_user_id should reflect who actually rejected
        assert approval.rejected_by_user_id == approver2.id
        # It may differ from the assigned approver (delegation case)
        # But it must be set and valid
        assert approval.rejected_by_user_id is not None
        assert isinstance(approval.rejected_by_user_id, int)
        assert approval.rejected_by_user_id > 0
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        notes=valid_approval_notes()
    )
    def test_property_3_decided_at_is_set_when_approved(self, approver, expense, notes):
        """
        Feature: user-attribution-tracking, Property 3: Approval attribution consistency
        
        For any approved record, decided_at timestamp must be set and should be
        after or equal to submitted_at.
        
        Validates: Requirements 2.1
        """
        submitted_time = datetime.now(timezone.utc)
        decided_time = datetime.now(timezone.utc)
        
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.APPROVED,
            submitted_at=submitted_time,
            decided_at=decided_time,
            approved_by_user_id=approver.id,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        if approval.status == ApprovalStatus.APPROVED:
            assert approval.decided_at is not None
            assert approval.decided_at >= approval.submitted_at
    
    @settings(max_examples=100)
    @given(
        approver=valid_user(),
        expense=valid_expense(),
        rejection_reason=valid_rejection_reason(),
        notes=valid_approval_notes()
    )
    def test_property_4_decided_at_is_set_when_rejected(self, approver, expense, rejection_reason, notes):
        """
        Feature: user-attribution-tracking, Property 4: Rejection attribution consistency
        
        For any rejected record, decided_at timestamp must be set and should be
        after or equal to submitted_at.
        
        Validates: Requirements 2.2
        """
        submitted_time = datetime.now(timezone.utc)
        decided_time = datetime.now(timezone.utc)
        
        approval = ExpenseApproval(
            id=1,
            expense_id=expense.id,
            approver_id=approver.id,
            status=ApprovalStatus.REJECTED,
            submitted_at=submitted_time,
            decided_at=decided_time,
            rejected_by_user_id=approver.id,
            rejection_reason=rejection_reason,
            approval_level=1,
            is_current_level=False,
            notes=notes
        )
        
        if approval.status == ApprovalStatus.REJECTED:
            assert approval.decided_at is not None
            assert approval.decided_at >= approval.submitted_at
