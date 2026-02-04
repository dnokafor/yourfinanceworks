# Implementation Plan: Investment Management

## Overview

This implementation plan breaks down the investment management plugin into discrete, incremental coding tasks. The plugin is designed as a self-contained module that integrates with YourFinanceWORKS without modifying existing code. It's a commercial-tier feature requiring license validation.

The implementation follows a bottom-up approach: database models → repositories → services → API endpoints → MCP integration → UI components. Each task builds on previous work and includes testing sub-tasks to validate functionality early.

## Tasks

- [x] 1. Set up plugin module structure and database models
  - Create `api/plugins/` directory if it doesn't exist
  - Create `api/plugins/investments/` directory structure with all subdirectories
  - Define database models (Portfolio, Holding, Transaction) with SQLAlchemy
  - Define enumerations (PortfolioType, SecurityType, AssetClass, TransactionType, DividendType)
  - Create Pydantic schemas for request/response validation
  - Set up Alembic migration for investment tables with `investment_` prefix
  - _Requirements: 1.1, 1.3, 2.1, 2.2, 3.1, 3.5_

- [ ]* 1.1 Write property test for portfolio model creation
  - **Property 1: Portfolio creation and tenant association**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 1.2 Write property test for enumeration support
  - **Property 2: Portfolio type support**
  - **Property 7: Security type support**
  - **Property 13: Transaction type support**
  - **Validates: Requirements 1.3, 2.2, 3.1**

- [ ] 2. Implement repository layer
  - [x] 2.1 Create PortfolioRepository with CRUD operations
    - Implement create, get_by_id, get_by_tenant, update, delete methods
    - Ensure all queries filter by tenant_id for isolation
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6_

  - [x] 2.2 Create HoldingsRepository with CRUD operations
    - Implement create, get_by_id, get_by_portfolio, update, close methods
    - Include tenant isolation through portfolio relationship
    - _Requirements: 2.1, 2.3, 2.4, 2.6_

  - [x] 2.3 Create TransactionRepository with CRUD operations
    - Implement create, get_by_id, get_by_portfolio, get_by_date_range methods
    - Include ordering by transaction_date
    - _Requirements: 3.5, 3.7_

- [ ]* 2.4 Write property tests for tenant isolation
  - **Property 3: Tenant isolation for portfolios**
  - **Property 12: Tenant isolation for holdings**
  - **Property 20: Tenant isolation for transactions**
  - **Validates: Requirements 1.4, 8.1, 8.2, 8.3, 8.4**

- [ ] 3. Implement portfolio service layer
  - [x] 3.1 Create PortfolioService with business logic
    - Implement create_portfolio, get_portfolios, get_portfolio, update_portfolio methods
    - Implement delete_portfolio with holdings count validation
    - Add validate_tenant_access helper method
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6_

  - [ ]* 3.2 Write property tests for portfolio operations
    - **Property 4: Portfolio update persistence**
    - **Property 5: Portfolio deletion with holdings constraint**
    - **Validates: Requirements 1.5, 1.6**

  - [ ]* 3.3 Write unit tests for portfolio service
    - Test portfolio creation with various types
    - Test deletion rejection when holdings exist
    - Test tenant access validation
    - _Requirements: 1.1, 1.3, 1.6_

- [ ] 4. Implement holdings service layer
  - [x] 4.1 Create HoldingsService with business logic
    - Implement create_holding, get_holdings, get_holding, update_holding methods
    - Implement update_price, adjust_quantity, close_holding methods
    - Add validation for negative quantities
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.2 Write property tests for holdings operations
    - **Property 6: Holding creation completeness**
    - **Property 8: Holdings retrieval completeness**
    - **Property 9: Holding update persistence**
    - **Property 10: Negative quantity rejection**
    - **Property 11: Holding closure on zero quantity**
    - **Validates: Requirements 2.1, 2.3, 2.4, 2.5, 2.6**

  - [ ]* 4.3 Write unit tests for holdings service
    - Test holding creation with all security types
    - Test negative quantity rejection
    - Test holding closure when quantity reaches zero
    - _Requirements: 2.2, 2.5, 2.6_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Run all tests for models, repositories, and services
  - Verify database migrations work correctly
  - Ensure tenant isolation is working
  - Ask the user if questions arise

- [x] 6. Implement transaction service layer with simple average cost basis
  - [x] 6.1 Create TransactionService with transaction processing
    - Implement record_transaction dispatcher method
    - Implement process_buy method (increase quantity and cost basis)
    - Implement process_sell method (decrease quantity, calculate realized gains using simple average cost)
    - Implement process_dividend method (record income, no quantity change)
    - Implement process_interest method (record only, no holding change)
    - Implement process_fee method (record only, no holding change)
    - Implement process_transfer method (record only, no holding change)
    - Implement process_contribution method (record only, no holding change)
    - Implement calculate_realized_gain with simple average cost algorithm
    - Add validation for required fields, positive amounts, non-future dates
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.5, 10.1, 10.2, 10.3_

  - [ ]* 6.2 Write property tests for transaction operations
    - **Property 14: Buy transaction effects**
    - **Property 15: Sell transaction effects**
    - **Property 16: Dividend transaction invariant**
    - **Property 17: Transaction data completeness**
    - **Property 18: Sell quantity validation**
    - **Property 19: Transaction ordering**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

  - [ ]* 6.3 Write property test for average cost basis
    - **Property 35: Average cost basis calculation**
    - **Property 36: Cost basis consistency**
    - **Validates: Requirements 7.5, 10.4**

  - [ ]* 6.4 Write unit tests for transaction service
    - Test buy transaction updates holding correctly
    - Test sell transaction with insufficient quantity fails
    - Test dividend doesn't change quantity
    - Test simple average cost with multiple buy lots
    - Test validation errors (negative amounts, future dates, missing fields)
    - _Requirements: 3.2, 3.3, 3.4, 3.6, 10.1, 10.2, 10.3_

- [x] 7. Implement analytics service layer
  - [x] 7.1 Create PerformanceCalculator
    - Implement calculate_total_return method (inception-to-date only)
    - Implement calculate_unrealized_gains method
    - Implement calculate_realized_gains method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 7.2 Create AssetAllocationAnalyzer
    - Implement calculate_asset_allocation method
    - Group holdings by asset class
    - Calculate percentages ensuring they sum to 100%
    - Handle empty portfolios
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 7.3 Create TaxDataExporter
    - Implement export_transaction_data method (CSV and JSON formats)
    - Implement calculate_realized_gains method (raw amounts, no classification)
    - Implement calculate_dividend_income method (raw amounts, no classification)
    - Include all transaction details for accountant/tax software
    - Note: This is specifically for tax-related data export
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 7.4 Create AnalyticsService orchestrator
    - Implement calculate_portfolio_performance method (inception-to-date only)
    - Implement calculate_asset_allocation method
    - Implement calculate_dividend_income method
    - Implement export_tax_data method
    - _Requirements: 4.1, 5.1, 6.3, 6.4, 7.1_

  - [ ]* 7.5 Write property tests for analytics calculations
    - **Property 21: Total return calculation**
    - **Property 22: Performance calculation completeness**
    - **Property 23: Unrealized gain calculation**
    - **Property 24: Realized gain aggregation**
    - **Property 27: Allocation percentage calculation**
    - **Property 32: Dividend income aggregation**
    - **Property 34: Tax export completeness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.3, 6.4, 7.1, 7.2, 7.3**

  - [ ]* 7.6 Write unit tests for analytics service
    - Test performance calculation with dividends and realized gains
    - Test asset allocation with multiple asset classes
    - Test allocation percentages sum to 100%
    - Test empty portfolio returns zero/empty allocation
    - Test tax data export includes all required fields
    - _Requirements: 4.1, 4.3, 5.3, 5.5, 7.1, 7.2, 7.3_

- [x] 8. Checkpoint - Ensure all business logic tests pass
  - Run all service layer tests
  - Verify average cost basis calculations are correct
  - Verify performance and allocation calculations are accurate
  - Ask the user if questions arise

- [x] 9. Implement API endpoints
  - [x] 9.1 Create investment router with portfolio endpoints
    - POST /api/v1/investments/portfolios (create portfolio)
    - GET /api/v1/investments/portfolios (list portfolios)
    - GET /api/v1/investments/portfolios/{id} (get portfolio)
    - PUT /api/v1/investments/portfolios/{id} (update portfolio)
    - DELETE /api/v1/investments/portfolios/{id} (delete portfolio)
    - Add feature gate dependency requiring commercial license
    - Add tenant authentication dependency
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 8.1, 8.4_

  - [x] 9.2 Add holdings endpoints to router
    - POST /api/v1/investments/portfolios/{id}/holdings (create holding)
    - GET /api/v1/investments/portfolios/{id}/holdings (list holdings)
    - GET /api/v1/investments/holdings/{id} (get holding)
    - PUT /api/v1/investments/holdings/{id} (update holding)
    - PATCH /api/v1/investments/holdings/{id}/price (update price)
    - _Requirements: 2.1, 2.3, 2.4, 8.2, 11.1, 11.2_

  - [x] 9.3 Add transaction endpoints to router
    - POST /api/v1/investments/portfolios/{id}/transactions (create transaction)
    - GET /api/v1/investments/portfolios/{id}/transactions (list transactions)
    - GET /api/v1/investments/transactions/{id} (get transaction)
    - _Requirements: 3.1, 3.7, 8.3_

  - [x] 9.4 Add analytics endpoints to router
    - GET /api/v1/investments/portfolios/{id}/performance (get performance - inception-to-date)
    - GET /api/v1/investments/portfolios/{id}/allocation (get asset allocation)
    - GET /api/v1/investments/portfolios/{id}/dividends (get dividend history)
    - GET /api/v1/investments/portfolios/{id}/tax-export (export tax data)
    - _Requirements: 4.1, 4.6, 5.1, 6.3, 7.1_

  - [ ]* 9.5 Write integration tests for API endpoints
    - Test complete flow: create portfolio → add holding → record transactions → get performance
    - Test tenant isolation at API level
    - Test feature gate blocks access without commercial license
    - Test error responses (404, 400, 403)
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 8.4_

- [x] 10. Implement error handling and validation
  - [x] 10.1 Add comprehensive error handling to all endpoints
    - Return 400 for validation errors with descriptive messages
    - Return 403 for tenant access violations
    - Return 404 for non-existent resources
    - Return 409 for conflicts (e.g., deleting portfolio with holdings)
    - Return 500 for server errors with logging
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 10.2 Add input validation middleware
    - Validate required fields
    - Validate positive amounts and quantities
    - Validate non-future dates
    - Validate portfolio types, security types, transaction types
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 10.3 Add duplicate transaction detection
    - Check for identical transactions within 60-second window
    - Return 409 Conflict if duplicate detected
    - _Requirements: 10.5_

  - [ ]* 10.4 Write property tests for validation
    - **Property 37: Required field validation**
    - **Property 38: Positive amount validation**
    - **Property 39: Future date validation**
    - **Property 40: Duplicate transaction prevention**
    - **Property 53: Non-existent resource error**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.5, 15.2**

- [x] 11. Implement MCP assistant integration
  - [x] 11.1 Create InvestmentMCPProvider
    - Implement get_portfolio_summary method
    - Implement get_holding_details method
    - Implement get_performance_summary method
    - Implement get_dividend_forecast method
    - Implement get_tax_summary method
    - Enforce tenant isolation in all methods
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [ ]* 11.2 Write unit tests for MCP provider
    - Test portfolio summary returns correct data
    - Test tenant isolation in MCP queries
    - Test data formatting for AI assistant
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 12. Implement plugin registration
  - [x] 12.1 Create plugin registration module
    - Implement register_investment_plugin function
    - Register API router with commercial license dependency
    - Register MCP provider with MCP registry
    - Return plugin metadata (name, version, license_tier, routes)
    - _Requirements: 8.1, 8.4_

  - [x] 12.2 Create plugin manifest (plugin.json)
    - Define plugin metadata (name, version, author, license)
    - Specify license tier requirement (commercial)
    - List API routes and MCP providers
    - Define required permissions
    - _Requirements: 8.1_

  - [ ]* 12.3 Write integration test for plugin registration
    - Test plugin registers routes correctly
    - Test feature gate blocks access without license
    - Test MCP provider is accessible
    - _Requirements: 8.1, 8.4_

- [x] 13. Implement retirement account features
  - [x] 13.1 Add retirement account support to services
    - Support generic RETIREMENT portfolio type
    - Support CONTRIBUTION transaction type
    - _Requirements: 12.1, 12.2, 12.3_

  - [ ]* 13.2 Write property tests for retirement accounts
    - **Property 45: Retirement portfolio type tracking**
    - **Property 46: Retirement contribution tracking**
    - **Validates: Requirements 12.2, 12.3**

- [-] 14. Implement business investment features
  - [x] 14.1 Add business portfolio support
    - Support BUSINESS portfolio type
    - Associate business portfolios with business tenants
    - Support all security types for business portfolios
    - Add portfolio_type filter to reports
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ]* 14.2 Write property tests for business portfolios
    - **Property 47: Business portfolio creation**
    - **Property 48: Business security tracking**
    - **Property 49: Business data separation**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4**

- [x] 15. Implement data retention and archival
  - [x] 15.1 Add soft delete for portfolios
    - Mark portfolios as archived instead of deleting
    - Preserve all transaction history
    - Preserve closed holdings
    - _Requirements: 14.1, 14.2, 14.4_

  - [x] 15.2 Add full portfolio data export functionality
    - Implement CSV export for transactions
    - Implement JSON export for complete portfolio data (holdings, transactions, performance)
    - Note: This is for full portfolio backup/export, separate from tax-specific export in Task 7.3
    - _Requirements: 14.5_

  - [ ]* 15.3 Write property tests for data retention
    - **Property 50: Transaction immutability**
    - **Property 51: Closed holding transaction preservation**
    - **Property 52: Portfolio archival on deletion**
    - **Validates: Requirements 14.1, 14.2, 14.4**

- [x] 16. Implement price management features
  - [x] 16.1 Add manual price update functionality
    - Implement update_price endpoint
    - Record price and timestamp
    - Use latest price for valuations
    - Fallback to cost basis when price unavailable
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 16.2 Write property tests for price management
    - **Property 41: Manual price update**
    - **Property 42: Latest price usage**
    - **Property 43: Price fallback to cost basis**
    - **Property 44: Price timestamp presence**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [-] 17. Implement dividend tracking features
  - [x] 17.1 Add dividend-specific functionality
    - Support ORDINARY dividend type
    - Implement dividend history filtering by date range
    - Implement dividend income aggregation
    - Associate dividends with holdings
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 17.2 Write property tests for dividend tracking
    - **Property 29: Dividend holding association**
    - **Property 30: Dividend data completeness**
    - **Property 31: Dividend history filtering**
    - **Property 33: Dividend type support**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**

- [x] 18. Final checkpoint - Comprehensive testing
  - Run full test suite (unit tests and property tests)
  - Verify all 53 correctness properties pass
  - Test complete user flows end-to-end
  - Verify tenant isolation across all operations
  - Verify feature gate blocks access without commercial license
  - Test error handling and validation
  - Ask the user if questions arise

- [ ] 19. Create database migration scripts
  - [ ] 19.1 Create Alembic migration for investment tables
    - Create investment_portfolios table
    - Create investment_holdings table
    - Create investment_transactions table
    - Add indexes for tenant_id, portfolio_id, transaction_date
    - Add check constraints for positive quantities and amounts
    - _Requirements: 1.1, 2.1, 3.1_

  - [ ] 19.2 Create migration rollback script
    - Drop all investment tables
    - Clean up any orphaned data
    - _Requirements: 14.4_

- [x] 20. Integration with main application
  - [x] 20.1 Register plugin in main application startup
    - Import register_investment_plugin in main.py
    - Call registration function with app, mcp_registry, feature_gate
    - Verify routes are registered under /api/v1/investments
    - Verify MCP provider is registered
    - _Requirements: 8.1, 9.1_

  - [ ]* 20.2 Write integration test for full application
    - Test investment endpoints are accessible with commercial license
    - Test investment endpoints are blocked without license
    - Test MCP assistant can query investment data
    - Test tenant isolation at application level
    - _Requirements: 8.1, 8.4, 9.1, 9.3_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- The plugin is designed to be self-contained and not modify existing code
- All endpoints require commercial license via feature gate
- Tenant isolation is enforced at every layer (repository, service, API)
- MVP uses simple average cost basis (FIFO deferred to Phase 2)
- MVP supports inception-to-date performance only (multi-period deferred to Phase 2)
- Tax classification and jurisdiction-specific rules deferred to future plugin
