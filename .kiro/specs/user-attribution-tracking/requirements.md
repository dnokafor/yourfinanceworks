# Requirements Document

## Introduction

This feature adds user attribution tracking to invoices, expenses, bank statements, and reminders. In multi-user organizations, it's essential to know who created each record and who performed approval/rejection actions. This provides accountability, audit trails, and better collaboration visibility.

## Glossary

- **System**: The expense and invoice management application
- **User**: An authenticated person with access to the organization
- **Creator**: The user who originally created a record
- **Approver**: The user who approved a record requiring approval
- **Rejector**: The user who rejected a record requiring approval
- **Record**: An invoice, expense, bank statement, or reminder entity
- **Attribution**: Information about which user performed an action

## Requirements

### Requirement 1

**User Story:** As an organization member, I want to see who created each invoice, expense, statement, and reminder, so that I can identify the source and contact them if needed.

#### Acceptance Criteria

1. WHEN a user creates an invoice THEN the system SHALL store the creator's user ID with the invoice record
2. WHEN a user creates an expense THEN the system SHALL store the creator's user ID with the expense record
3. WHEN a user creates a bank statement THEN the system SHALL store the creator's user ID with the statement record
4. WHEN a user creates a reminder THEN the system SHALL store the creator's user ID with the reminder record
5. WHEN displaying a record THEN the system SHALL show the creator's name alongside the record details

### Requirement 2

**User Story:** As an organization member, I want to see who approved or rejected expenses and invoices, so that I understand the approval history and decision-making process.

#### Acceptance Criteria

1. WHEN a user approves an expense THEN the system SHALL store the approver's user ID with the approval record
2. WHEN a user rejects an expense THEN the system SHALL store the rejector's user ID with the rejection record
3. WHEN a user approves an invoice THEN the system SHALL store the approver's user ID with the approval record
4. WHEN a user rejects an invoice THEN the system SHALL store the rejector's user ID with the rejection record
5. WHEN displaying an approved record THEN the system SHALL show the approver's name
6. WHEN displaying a rejected record THEN the system SHALL show the rejector's name

### Requirement 3

**User Story:** As a system administrator, I want user attribution to be automatically captured from the authenticated session, so that the data is accurate and cannot be manipulated.

#### Acceptance Criteria

1. WHEN a user creates a record THEN the system SHALL extract the user ID from the authenticated session token
2. WHEN a user performs an approval action THEN the system SHALL extract the user ID from the authenticated session token
3. WHEN the system stores attribution data THEN the system SHALL prevent manual override of user IDs
4. WHEN a user is not authenticated THEN the system SHALL reject the creation or approval request

### Requirement 4

**User Story:** As a developer, I want the database schema to support user attribution, so that the data can be stored and queried efficiently.

#### Acceptance Criteria

1. WHEN the migration runs THEN the system SHALL add a created_by_user_id column to the invoices table
2. WHEN the migration runs THEN the system SHALL add a created_by_user_id column to the expenses table
3. WHEN the migration runs THEN the system SHALL add a created_by_user_id column to the bank_statements table
4. WHEN the migration runs THEN the system SHALL add a created_by_user_id column to the reminders table
5. WHEN the migration runs THEN the system SHALL add approved_by_user_id and rejected_by_user_id columns to approval-enabled tables
6. WHEN querying records THEN the system SHALL support filtering by creator user ID
7. WHEN querying records THEN the system SHALL support filtering by approver or rejector user ID

### Requirement 5

**User Story:** As a frontend developer, I want the API to return creator and approver information, so that I can display it in the user interface.

#### Acceptance Criteria

1. WHEN the API returns an invoice THEN the response SHALL include the creator's user ID and name
2. WHEN the API returns an expense THEN the response SHALL include the creator's user ID and name
3. WHEN the API returns a bank statement THEN the response SHALL include the creator's user ID and name
4. WHEN the API returns a reminder THEN the response SHALL include the creator's user ID and name
5. WHEN the API returns an approved record THEN the response SHALL include the approver's user ID and name
6. WHEN the API returns a rejected record THEN the response SHALL include the rejector's user ID and name

### Requirement 6

**User Story:** As an organization member, I want to see user attribution in list views and detail views, so that I can quickly identify who is responsible for each record.

#### Acceptance Criteria

1. WHEN viewing the invoices list THEN the system SHALL display the creator's name for each invoice
2. WHEN viewing the expenses list THEN the system SHALL display the creator's name for each expense
3. WHEN viewing the statements list THEN the system SHALL display the creator's name for each statement
4. WHEN viewing the reminders list THEN the system SHALL display the creator's name for each reminder
5. WHEN viewing an invoice detail page THEN the system SHALL display the creator's name and approval/rejection information
6. WHEN viewing an expense detail page THEN the system SHALL display the creator's name and approval/rejection information

### Requirement 7

**User Story:** As a system administrator, I want existing records to handle missing attribution gracefully, so that the system remains stable during the migration period.

#### Acceptance Criteria

1. WHEN a record has no creator information THEN the system SHALL display "Unknown" or "System" as the creator
2. WHEN a record has no approver information THEN the system SHALL display "Unknown" as the approver
3. WHEN querying records with missing attribution THEN the system SHALL return the records without errors
4. WHEN displaying records with missing attribution THEN the system SHALL not break the user interface
