# Implementation Plan

**Note:** All tests should be run in the API Docker container using:
```bash
docker exec invoice_app_api python -m pytest <test_file> -v
```

- [x] 1. Database models already have attribution fields
  - Invoice model has created_by_user_id and created_by relationship (api/core/models/models.py)
  - Expense model has created_by_user_id and created_by relationship (api/core/models/models_per_tenant.py)
  - BankStatement model has created_by_user_id and created_by relationship (api/core/models/models_per_tenant.py)
  - ExpenseApproval model has approved_by_user_id, rejected_by_user_id and relationships (api/core/models/models_per_tenant.py)
  - Reminder model has created_by_id field (api/core/models/models_per_tenant.py)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Update Pydantic schemas to include attribution fields
  - Update InvoiceWithClient schema to include created_by_user_id, created_by_username, created_by_email
  - Update Expense schema to include created_by_user_id, created_by_username, created_by_email
  - Create/update BankStatementResponse schema to include created_by_user_id, created_by_username, created_by_email
  - Update ExpenseApprovalResponse schema to include approved_by_user_id, approved_by_username, rejected_by_user_id, rejected_by_username
  - Update ReminderResponse schema to include created_by information
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 3. Create AttributionService for common attribution logic
  - Create api/core/services/attribution_service.py
  - Implement get_user_from_context() method
  - Implement format_user_info() method
  - Implement get_display_name() method with graceful NULL handling
  - _Requirements: 3.1, 3.2, 7.1, 7.2_

- [x] 3.1 Write property test for AttributionService
  - **Property 7: Graceful handling of missing attribution**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 4. Update invoice router and service to capture creator
  - Modify create_invoice endpoint to pass current_user.id to invoice creation logic
  - Set created_by_user_id when creating new invoices
  - Update invoice query to joinedload created_by relationship
  - Update response serialization to include creator information
  - _Requirements: 1.1, 3.1, 5.1, 6.1, 6.5_

- [x] 4.1 Write property test for invoice creator attribution
  - **Property 1: Creator attribution is immutable**
  - **Property 2: Authenticated user attribution**
  - **Validates: Requirements 1.1, 3.1, 3.4**

- [x] 5. Update expense router and service to capture creator
  - Modify create_expense endpoint to pass current_user.id to expense creation logic
  - Set created_by_user_id when creating new expenses
  - Update expense query to joinedload created_by relationship
  - Update response serialization to include creator information
  - _Requirements: 1.2, 3.1, 5.2, 6.2, 6.6_

- [x] 5.1 Write property test for expense creator attribution
  - **Property 1: Creator attribution is immutable**
  - **Property 2: Authenticated user attribution**
  - **Validates: Requirements 1.2, 3.1, 3.4**

- [x] 6. Update bank statement router and service to capture creator
  - Modify create_statement endpoint to pass current_user.id to statement creation logic
  - Set created_by_user_id when creating new statements
  - Update statement query to joinedload created_by relationship
  - Update response serialization to include creator information
  - _Requirements: 1.3, 3.1, 5.3, 6.3_

- [x] 6.1 Write property test for statement creator attribution
  - **Property 1: Creator attribution is immutable**
  - **Property 2: Authenticated user attribution**
  - **Validates: Requirements 1.3, 3.1, 3.4**

- [x] 7. Update reminder router to ensure creator attribution (verify existing implementation)
  - Verify reminder creation already captures created_by_id
  - Verify reminder query includes created_by relationship
  - Verify response includes creator information
  - Update if needed to match other entities
  - _Requirements: 1.4, 5.4, 6.4_

- [x] 8. Update approval service to capture approver/rejector
  - Modify approve_expense method to set approved_by_user_id and approved_at when approving
  - Modify reject_expense method to set rejected_by_user_id and rejected_at when rejecting
  - Update approval queries to joinedload approver/rejector relationships
  - _Requirements: 2.1, 2.2, 3.2_

- [x] 8.1 Write property test for approval attribution
  - **Property 3: Approval attribution consistency**
  - **Property 4: Rejection attribution consistency**
  - **Property 5: Mutual exclusivity of approval states**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 9. Update approval router endpoints
  - Update approve endpoint to pass current_user to service
  - Update reject endpoint to pass current_user to service
  - Update response serialization to include approver/rejector information
  - _Requirements: 2.1, 2.2, 2.5, 2.6_

- [x] 10. Add filtering support for creator attribution
  - Add created_by_user_id query parameter to invoice list endpoint
  - Add created_by_user_id query parameter to expense list endpoint
  - Add created_by_user_id query parameter to statement list endpoint
  - Add created_by_user_id query parameter to reminder list endpoint
  - Implement filtering logic in service layer
  - _Requirements: 4.6, 4.7_

- [x] 11. Update frontend to display creator information
  - Update invoice list component to show creator name
  - Update expense list component to show creator name
  - Update statement list component to show creator name
  - Update reminder list component to show creator name
  - Add "Created by" field to detail views
  - Handle "Unknown" creator gracefully in UI
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.4_

- [x] 12. Update frontend to display approver/rejector information
  - Update expense detail view to show approver name when approved
  - Update expense detail view to show rejector name when rejected
  - Update invoice detail view to show approver name when approved (if applicable)
  - Update invoice detail view to show rejector name when rejected (if applicable)
  - Add approval/rejection timestamp display
  - _Requirements: 2.5, 2.6, 6.5, 6.6_

- [x] 13. Add mobile app support for attribution display
  - Update mobile invoice list to show creator
  - Update mobile expense list to show creator
  - Update mobile detail views to show creator
  - Update mobile approval screens to show approver/rejector
  - _Requirements: 6.1, 6.2, 6.5, 6.6_

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Write property test for API response completeness
  - **Property 6: API response completeness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 7.1**

- [ ] 16. Write property test for foreign key integrity
  - **Property 8: Foreign key integrity**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 17. Update API documentation
  - Document new attribution fields in API responses
  - Document filtering by creator parameters
  - Add examples showing attribution data
  - Document "Unknown" handling for legacy data
  - _Requirements: All requirements_

- [ ] 18. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
