# Design Document: User Attribution Tracking

## Overview

This feature adds comprehensive user attribution tracking to invoices, expenses, bank statements, and reminders. The system will automatically capture and store information about who created each record and who performed approval/rejection actions. This provides accountability, audit trails, and better collaboration visibility in multi-user organizations.

The design leverages existing authentication mechanisms to automatically capture user information from the session context, ensuring data accuracy and preventing manipulation. The implementation will be backward-compatible with existing records that lack attribution data.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Invoices   │  │   Expenses   │  │  Statements  │      │
│  │   Router     │  │   Router     │  │   Router     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                  ┌──────────────────┐                        │
│                  │  Authentication  │                        │
│                  │    Middleware    │                        │
│                  └────────┬─────────┘                        │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Invoice    │  │   Expense    │  │  Statement   │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                  ┌──────────────────┐                        │
│                  │   Attribution    │                        │
│                  │     Service      │                        │
│                  └────────┬─────────┘                        │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Invoices   │  │   Expenses   │  │  Statements  │      │
│  │    Table     │  │    Table     │  │    Table     │      │
│  │              │  │              │  │              │        │
│  │ +created_by  │  │ +created_by  │  │ +created_by  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Expense    │  │   Invoice    │                        │
│  │  Approvals   │  │  Approvals   │                        │
│  │              │  │              │                        │
│  │ +approved_by │  │ +approved_by │                        │
│  │ +rejected_by │  │ +rejected_by │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Reminders  │                                           │
│  │    Table     │                                           │
│  │              │                                           │
│  │ (already has │                                           │
│  │  created_by) │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Creation Flow**:
   - User makes authenticated request to create a record
   - Authentication middleware extracts user_id from JWT token
   - Service layer receives user_id from request context
   - Service automatically sets created_by_user_id field
   - Record is saved to database with attribution

2. **Approval/Rejection Flow**:
   - User makes authenticated request to approve/reject
   - Authentication middleware extracts user_id from JWT token
   - Approval service receives user_id from request context
   - Service sets approved_by_user_id or rejected_by_user_id
   - Approval record is updated with attribution

3. **Display Flow**:
   - API fetches record with user relationships
   - SQLAlchemy joins with users table
   - Response includes creator/approver name and ID
   - Frontend displays attribution information

## Components and Interfaces

### 1. Database Schema Changes

#### Invoices Table (models.py)
```python
class Invoice(Base):
    # ... existing fields ...
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
```

#### Expenses Table (models_per_tenant.py)
```python
class Expense(Base):
    # ... existing fields ...
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
```

#### Bank Statements Table (models_per_tenant.py)
```python
class BankStatement(Base):
    # ... existing fields ...
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
```

#### Reminders Table (models_per_tenant.py)
```python
# Already has created_by_id field - no changes needed
class Reminder(Base):
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
```

#### Expense Approvals Table (models_per_tenant.py)
```python
class ExpenseApproval(Base):
    # ... existing fields ...
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_user_id])
```

#### Invoice Approvals (if exists - to be determined during implementation)
```python
# Similar structure to ExpenseApproval
class InvoiceApproval(Base):
    # ... existing fields ...
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_user_id])
```

### 2. Pydantic Schema Updates

#### Invoice Schemas
```python
class InvoiceWithClient(Invoice):
    # ... existing fields ...
    created_by_user_id: Optional[int] = None
    created_by_username: Optional[str] = None
    created_by_email: Optional[str] = None
```

#### Expense Schemas
```python
class Expense(ExpenseBase):
    # ... existing fields ...
    created_by_user_id: Optional[int] = None
    created_by_username: Optional[str] = None
    created_by_email: Optional[str] = None
```

#### Bank Statement Schemas
```python
class BankStatementResponse(BaseModel):
    # ... existing fields ...
    created_by_user_id: Optional[int] = None
    created_by_username: Optional[str] = None
    created_by_email: Optional[str] = None
```

#### Approval Schemas
```python
class ExpenseApprovalResponse(BaseModel):
    # ... existing fields ...
    approved_by_user_id: Optional[int] = None
    approved_by_username: Optional[str] = None
    rejected_by_user_id: Optional[int] = None
    rejected_by_username: Optional[str] = None
```

### 3. Service Layer Changes

#### Attribution Service (New)
```python
class AttributionService:
    """Service for handling user attribution logic"""
    
    @staticmethod
    def get_user_from_context(current_user: User) -> int:
        """Extract user ID from authenticated context"""
        return current_user.id
    
    @staticmethod
    def format_user_info(user: User) -> Dict[str, Any]:
        """Format user information for API responses"""
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    
    @staticmethod
    def get_display_name(user: Optional[User]) -> str:
        """Get display name for user, handling None gracefully"""
        if not user:
            return "Unknown"
        return user.username or user.email or "Unknown"
```

#### Router Updates
All routers for invoices, expenses, statements, and reminders will be updated to:
1. Accept `current_user: User = Depends(get_current_user)` parameter
2. Pass `current_user.id` to service layer methods
3. Include user information in response serialization

### 4. API Response Format

#### Example Invoice Response
```json
{
  "id": 123,
  "number": "INV-001",
  "amount": 1000.00,
  "created_at": "2025-01-01T10:00:00Z",
  "created_by_user_id": 5,
  "created_by_username": "john.doe",
  "created_by_email": "john@example.com",
  "client_name": "Acme Corp"
}
```

#### Example Expense with Approval Response
```json
{
  "id": 456,
  "amount": 250.00,
  "category": "Travel",
  "created_at": "2025-01-01T10:00:00Z",
  "created_by_user_id": 5,
  "created_by_username": "john.doe",
  "approval": {
    "status": "approved",
    "approved_by_user_id": 3,
    "approved_by_username": "manager.smith",
    "approved_at": "2025-01-02T14:30:00Z"
  }
}
```

## Data Models

### User Attribution Fields

All entities will include these common attribution fields:

```python
# Creator attribution
created_by_user_id: Optional[int]  # Foreign key to users table
created_by: User  # SQLAlchemy relationship

# For API responses
created_by_username: Optional[str]  # Computed field
created_by_email: Optional[str]  # Computed field
```

### Approval Attribution Fields

Approval entities will include:

```python
# Approver attribution
approved_by_user_id: Optional[int]  # Foreign key to users table
approved_by: User  # SQLAlchemy relationship
approved_at: Optional[datetime]  # Timestamp of approval

# Rejector attribution
rejected_by_user_id: Optional[int]  # Foreign key to users table
rejected_by: User  # SQLAlchemy relationship
rejected_at: Optional[datetime]  # Timestamp of rejection

# For API responses
approved_by_username: Optional[str]  # Computed field
rejected_by_username: Optional[str]  # Computed field
```

### Database Constraints

- All `*_by_user_id` fields will be nullable to support existing records
- Foreign key constraints will use `ON DELETE SET NULL` to preserve attribution even if user is deleted
- Indexes will be added on `created_by_user_id` for efficient filtering

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Creator attribution is immutable
*For any* record (invoice, expense, statement, reminder), once the created_by_user_id is set, it should never change throughout the record's lifecycle
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 3.3**

### Property 2: Authenticated user attribution
*For any* create operation, the created_by_user_id should match the authenticated user's ID from the session token
**Validates: Requirements 3.1, 3.4**

### Property 3: Approval attribution consistency
*For any* approved record, if approved_by_user_id is set, then approved_at timestamp must also be set, and the status must be "approved"
**Validates: Requirements 2.1, 2.3**

### Property 4: Rejection attribution consistency
*For any* rejected record, if rejected_by_user_id is set, then rejected_at timestamp must also be set, and the status must be "rejected"
**Validates: Requirements 2.2, 2.4**

### Property 5: Mutual exclusivity of approval states
*For any* approval record, it cannot have both approved_by_user_id and rejected_by_user_id set simultaneously
**Validates: Requirements 2.1, 2.2**

### Property 6: API response completeness
*For any* API response containing a record with created_by_user_id, the response should also include created_by_username or display "Unknown" if user not found
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 7.1**

### Property 7: Graceful handling of missing attribution
*For any* record where created_by_user_id is NULL, the system should return "Unknown" or "System" as the creator name without errors
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Foreign key integrity
*For any* record with a non-NULL created_by_user_id, the referenced user must exist in the users table or the field must be NULL
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

## Error Handling

### Error Scenarios

1. **Missing Authentication**
   - Error: `401 Unauthorized`
   - Message: "Authentication required to create records"
   - Handling: Reject request before reaching service layer

2. **User Not Found**
   - Error: `404 Not Found`
   - Message: "User not found"
   - Handling: Should not occur if authentication is working correctly

3. **Database Constraint Violation**
   - Error: `500 Internal Server Error`
   - Message: "Failed to save attribution data"
   - Handling: Log error, rollback transaction, return generic error

4. **Missing Attribution Data (Legacy Records)**
   - Error: None (graceful handling)
   - Handling: Display "Unknown" or "System" as creator

### Error Response Format

```json
{
  "detail": "Authentication required to create records",
  "error_code": "AUTHENTICATION_REQUIRED",
  "timestamp": "2025-01-01T10:00:00Z"
}
```

## Testing Strategy

### Unit Tests

1. **Model Tests**
   - Test that created_by_user_id can be set and retrieved
   - Test that relationships load correctly
   - Test that NULL values are handled gracefully

2. **Service Tests**
   - Test AttributionService.get_user_from_context()
   - Test AttributionService.format_user_info()
   - Test AttributionService.get_display_name() with NULL user

3. **Router Tests**
   - Test that current_user is passed to services
   - Test that responses include attribution data
   - Test that unauthenticated requests are rejected

### Property-Based Tests

Property-based tests will use the `hypothesis` library for Python to generate random test data and verify the correctness properties defined above.

Configuration:
- Minimum 100 iterations per property test
- Use `@given` decorator with appropriate strategies
- Tag each test with the property number it validates

Example test structure:
```python
from hypothesis import given, strategies as st
import pytest

@given(
    user_id=st.integers(min_value=1, max_value=1000),
    record_data=st.fixed_dictionaries({
        'amount': st.floats(min_value=0.01, max_value=10000),
        'category': st.text(min_size=1, max_size=50)
    })
)
@pytest.mark.property_test
def test_property_1_creator_immutable(user_id, record_data):
    """
    Feature: user-attribution-tracking, Property 1: Creator attribution is immutable
    
    For any record, once created_by_user_id is set, it should never change
    """
    # Test implementation
    pass
```

### Integration Tests

1. **End-to-End Creation Flow**
   - Create invoice/expense/statement with authenticated user
   - Verify created_by_user_id is set correctly
   - Verify API response includes creator information

2. **Approval Flow**
   - Submit expense for approval
   - Approve with different user
   - Verify approved_by_user_id is set correctly
   - Verify API response includes approver information

3. **Legacy Data Handling**
   - Query records with NULL created_by_user_id
   - Verify "Unknown" is displayed
   - Verify no errors occur

### Edge Cases

1. **User Deletion**
   - Delete user who created records
   - Verify created_by_user_id becomes NULL (ON DELETE SET NULL)
   - Verify "Unknown" is displayed

2. **Concurrent Approvals**
   - Two users attempt to approve same expense simultaneously
   - Verify only one approval succeeds
   - Verify correct approver is recorded

3. **Migration of Existing Data**
   - Existing records have NULL created_by_user_id
   - Verify system handles gracefully
   - Verify filtering works with NULL values

## Migration Strategy

### Database Migration

1. **Add Columns**
   ```sql
   -- Invoices (master database)
   ALTER TABLE invoices ADD COLUMN created_by_user_id INTEGER;
   ALTER TABLE invoices ADD CONSTRAINT fk_invoices_created_by 
       FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
   CREATE INDEX idx_invoices_created_by ON invoices(created_by_user_id);
   
   -- Expenses (per-tenant database)
   ALTER TABLE expenses ADD COLUMN created_by_user_id INTEGER;
   ALTER TABLE expenses ADD CONSTRAINT fk_expenses_created_by 
       FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
   CREATE INDEX idx_expenses_created_by ON expenses(created_by_user_id);
   
   -- Bank Statements (per-tenant database)
   ALTER TABLE bank_statements ADD COLUMN created_by_user_id INTEGER;
   ALTER TABLE bank_statements ADD CONSTRAINT fk_bank_statements_created_by 
       FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
   CREATE INDEX idx_bank_statements_created_by ON bank_statements(created_by_user_id);
   
   -- Expense Approvals (per-tenant database)
   ALTER TABLE expense_approvals ADD COLUMN approved_by_user_id INTEGER;
   ALTER TABLE expense_approvals ADD COLUMN rejected_by_user_id INTEGER;
   ALTER TABLE expense_approvals ADD CONSTRAINT fk_expense_approvals_approved_by 
       FOREIGN KEY (approved_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
   ALTER TABLE expense_approvals ADD CONSTRAINT fk_expense_approvals_rejected_by 
       FOREIGN KEY (rejected_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
   CREATE INDEX idx_expense_approvals_approved_by ON expense_approvals(approved_by_user_id);
   CREATE INDEX idx_expense_approvals_rejected_by ON expense_approvals(rejected_by_user_id);
   ```

2. **Backward Compatibility**
   - All new columns are nullable
   - Existing records will have NULL values
   - Application handles NULL gracefully

3. **Data Backfill (Optional)**
   - Can attempt to infer creator from audit logs
   - Can set to system user for old records
   - Not required for functionality

### Deployment Steps

1. Run database migrations
2. Deploy updated API code
3. Deploy updated frontend code
4. Monitor for errors
5. Optionally backfill historical data

## Performance Considerations

### Database Performance

1. **Indexes**
   - Add indexes on all `*_by_user_id` columns
   - Improves filtering and joining performance

2. **Query Optimization**
   - Use `joinedload` for eager loading user relationships
   - Avoid N+1 queries when fetching lists

3. **Caching**
   - Consider caching user information for frequently accessed records
   - Cache TTL: 5 minutes

### API Performance

1. **Response Size**
   - Additional fields add minimal overhead (~50 bytes per record)
   - Acceptable for typical use cases

2. **Query Complexity**
   - Additional JOIN adds minimal overhead
   - Properly indexed foreign keys ensure fast lookups

## Security Considerations

### Authentication

- All create/approve/reject operations require authentication
- User ID extracted from JWT token (cannot be spoofed)
- Middleware validates token before reaching service layer

### Authorization

- Users can only create records in their own organization
- Approval permissions checked by existing approval service
- Attribution data is read-only (cannot be modified by users)

### Data Privacy

- User email may be sensitive - consider encryption
- Attribution data included in audit logs
- Follow existing encryption patterns for sensitive fields

## Future Enhancements

1. **Bulk Operations**
   - Track who performed bulk imports
   - Store batch ID for grouping

2. **Modification History**
   - Track who modified records (beyond creation)
   - Store modification history with user attribution

3. **Advanced Filtering**
   - Filter by creator
   - Filter by approver
   - Date range filtering

4. **Analytics**
   - Reports on user activity
   - Approval turnaround times by approver
   - Creation patterns by user

5. **Audit Trail Enhancement**
   - Link attribution to existing audit log system
   - Comprehensive change tracking
