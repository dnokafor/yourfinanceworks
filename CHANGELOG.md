# Changelog

## [Latest] - November 2025

### Comprehensive Licensing System with Feature Gating

**Summary**: Complete licensing and monetization system with JWT-based license keys, 30-day trials, and granular feature control supporting personal (free) and business (trial/paid) usage models.

#### 🔐 Core Licensing Infrastructure

**Backend Services:**
- **LicenseService**: JWT-based license validation with RSA signatures, 30-day trial + 7-day grace period
- **FeatureConfigService**: Centralized feature configuration with 13 licensable features
- **Feature Gate Decorators**: `@require_feature` and `@require_business_license` for API protection
- **InstallationInfo Model**: Track installation ID, trial dates, license status, and feature entitlements
- **License API Endpoints**: `/api/v1/license` router with status, activation, validation, and deactivation

**Frontend Integration:**
- **FeatureContext**: Global license state management with real-time updates
- **FeatureGate Component**: Conditional rendering with upgrade prompts and loading states
- **LicenseManagement UI**: Trial countdown, feature indicators, and license activation interface
- **Settings Integration**: License tab with AI Assistant toggle and feature status

#### 🎯 Feature Gating Implementation

**13 Licensable Features:**
- **AI Features**: `ai_invoice`, `ai_expense`, `ai_bank_statement`, `ai_chat`
- **Integrations**: `cloud_storage`, `tax_integration`, `slack_integration`, `sso`
- **Advanced**: `batch_processing`, `api_keys`, `approvals`, `advanced_search`
- **Core**: `reporting` (default: true), inventory (always available)

**Backend Protection:**
- Invoice PDF processing (`pdf_processor.py`) - requires `ai_invoice`
- Bank statement upload (`statements.py`) - requires `ai_bank_statement`
- Expense AI analysis - requires `ai_expense` (uploads still work)
- API key management (`external_api_auth.py`) - requires business license
- All premium endpoints return HTTP 402 without valid license

**Frontend UX:**
- **Invoice PDF Import**: Hidden menu items and cards when `ai_invoice` disabled
- **Bank Statements**: Disabled button with tooltip when `ai_bank_statement` disabled
- **Expense Attachments**: Informational alerts (uploads work, AI skipped without license)
- **Progressive Disclosure**: Users see features with upgrade prompts, not hard blocks

#### 🐛 Bug Fixes

**OCR Worker:**
- Fixed async/await issue in `notify_invoice_ocr_complete()` 
- Fixed invoice processing status mismatch (done → completed)
- Resolved infinite polling when frontend never recognized completion

**Inventory:**
- Removed from licensable features (now core feature)
- Cleaned up `@require_feature("inventory")` gates
- Fixed JSON query compatibility issues

#### ⚠️ Breaking Changes

- Premium API endpoints return HTTP 402 without license
- Fresh installations require usage type selection
- Invoice PDF, bank statement upload, and expense AI require respective features
- API key management requires business license (not available for personal use)

---

## [Previous] - January 2025

### Expense Approval Workflow & Reminders System

**Summary**: Comprehensive expense approval workflow with multi-language support, reminders, and in-app notifications.

#### 🔄 Approval Workflow Features

- **Complete Approval System**: Full expense approval workflow with status transitions (draft → submitted → approved/rejected)
- **Pending Approvals Dashboard**: Dedicated interface for reviewing and processing expense approvals
- **Processed Expenses View**: Track completed approvals with detailed history
- **Expense Detail View**: New ExpensesView page for comprehensive expense viewing
- **Approval Permissions**: Enhanced RBAC with approval-specific permissions
- **Audit Trail**: Complete approval history tracking with timestamps and user attribution

#### 🔔 Reminders & Notifications

- **Reminder System**: In-app reminder functionality with navigation support
- **Email Notifications**: Configurable email settings for approval reminders
- **Real-time Updates**: Instant UI updates for approval status changes
- **User Filtering**: Show only activated tenant users in approval workflows

#### 🌍 Internationalization

- **Multi-language Support**: Complete translations for approval workflow in English, Spanish, French, and German
- **Inventory Integration**: Translated inventory consumption features across all languages
- **Consistent UX**: Proper localization for all approval-related UI elements

#### 🔧 Technical Improvements

- **Enhanced API Endpoints**: New approval-specific endpoints for workflow management
- **Simplified Architecture**: Removed complex rule-based system in favor of streamlined approval process
- **Node.js 20**: Updated UI Dockerfile to use Node.js 20
- **Test Coverage**: Comprehensive test suite for approval integration

#### 📁 Files Modified

- `api/routers/approvals.py` - Enhanced approval endpoints
- `ui/src/pages/ExpensesView.tsx` - New expense detail view
- `ui/src/pages/Expenses.tsx` - Approval workflow integration
- `ui/src/components/ProcessedExpensesList.tsx` - Completed approvals view
- `ui/src/i18n/locales/*.json` - Approval translations for all languages
- `ui/Dockerfile` - Updated to Node.js 20

---

## [1.0.0] - December 2024

### Invoice Management Enhancements

**Summary**: Major improvements to invoice system with zero-price items, cancelled status, and business logic enhancements.

#### 💰 Invoice Features

- **Zero-Price Items**: Allow invoice items with $0.00 price (previously minimum $0.01)
- **Cancelled Status**: New 'cancelled' status option for invoice lifecycle management
- **Deletion Protection**: Prevent permanent deletion of invoices with linked expenses
- **Internationalization**: Complete i18n support for InvoiceCard component
- **Status Translations**: Translated status labels across all supported languages

#### 🏢 Organization Join Request System

- **Join Workflow**: Users can search and request to join existing organizations
- **Organization Lookup**: Search functionality during signup process
- **Request Management**: Comprehensive join request handling in Users page
- **Approval Workflow**: Admin approval/rejection with role assignment
- **Email Notifications**: Automated notifications for join request events
- **Request Tracking**: Complete audit trail for join requests
- **Expiration Handling**: Automatic request cleanup and expiration

#### 📦 Inventory Management System

- **Inventory Consumption**: Link expenses to inventory item consumption
- **Inventory Attachments**: Support for file attachments on inventory items
- **MCP Tools Integration**: Comprehensive inventory tools for AI assistant
- **Inventory Reporting**: Detailed reporting functionality for inventory tracking
- **Invoice Integration**: Seamless integration between inventory and invoicing
- **Consumption Tracking**: Track which expenses consumed which inventory items

#### 🔧 Technical Improvements

- **Database Models**: Added OrganizationJoinRequest model with lifecycle management
- **API Endpoints**: New organization join router with lookup and approval endpoints
- **Middleware Updates**: Allow public access to join endpoints
- **Enhanced Schemas**: Updated client and invoice data structures
- **Performance Optimization**: Improved InvoiceForm component performance
- **Mobile Enhancements**: Updated mobile invoice screens (EditInvoiceScreen, NewInvoiceScreen)

#### 🔒 Security Updates

- **Dependency Updates**: Multiple Snyk security fixes for vulnerabilities
- **React Upgrade**: Upgraded React from 19.0.0 to 19.1.1
- **esbuild Update**: Bumped esbuild from 0.21.5 to 0.25.10
- **API Requirements**: Fixed vulnerabilities in requests, urllib3, and transformers packages

#### 📁 Files Modified

- `api/models/models.py` - Added OrganizationJoinRequest model
- `api/routers/organization_join.py` - New join request router
- `api/routers/clients.py` - Enhanced client endpoints
- `api/routers/invoices.py` - Updated invoice endpoints
- `ui/src/components/InvoiceCard.tsx` - Added i18n support
- `ui/src/pages/Signup.tsx` - Enhanced with join organization flow
- `ui/src/pages/Users.tsx` - Added join request management
- `mobile/src/screens/EditInvoiceScreen.tsx` - Mobile invoice improvements
- `mobile/src/screens/NewInvoiceScreen.tsx` - Mobile invoice improvements

---

## [Previous] - September 2025

### Microsoft Azure AD SSO Implementation

**Summary**: Added enterprise-grade Single Sign-On support with Microsoft Azure AD/Entra ID, enabling seamless authentication for organizations using Microsoft identity services.

#### 🔐 Authentication & Security Enhancements

- **Azure AD OAuth 2.0 Integration**: Full implementation using Microsoft Authentication Library (MSAL)
- **Multi-tenant Support**: Supports both single-tenant and multi-tenant Azure AD configurations
- **Database Schema Extensions**: Added `azure_ad_id` and `azure_tenant_id` fields to user models
- **Automatic User Provisioning**: Creates users and tenants automatically for new Azure AD users
- **Account Linking**: Links existing users with Azure AD accounts seamlessly
- **CSRF Protection**: Secure state management with token expiration

#### 🎨 User Interface Updates

- **Microsoft Login Button**: Added official Microsoft branding to login page
- **Multi-language Support**: Translations for "Sign in with Microsoft" in English, French, Spanish, and German
- **Consistent UX**: Matches existing Google OAuth button styling and behavior
- **OAuth Flow Handling**: Seamless redirect-based authentication flow

#### 🔧 Technical Implementation

- **New Dependencies**: Added MSAL 1.31.0 for Microsoft authentication
- **API Endpoints**:
  - `/api/v1/auth/azure/login` - Initiates Azure AD authentication
  - `/api/v1/auth/azure/callback` - Handles OAuth callback and user creation
- **Environment Configuration**: Docker Compose support for Azure AD variables
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Error Handling**: Graceful handling of authentication failures and edge cases

#### 📚 Documentation

- **Implementation Guide**: Complete Azure AD SSO setup documentation
- **Testing Guide**: Comprehensive testing scenarios and troubleshooting
- **Security Documentation**: Enterprise compliance and security considerations

#### 🗄️ Database Changes

```sql
-- Added to both MasterUser and TenantUser models
azure_ad_id VARCHAR UNIQUE NULL     -- Azure AD Object ID
azure_tenant_id VARCHAR NULL        -- Azure AD Tenant ID
```

#### 📁 Files Modified

- `api/requirements.txt` - Added MSAL dependency
- `api/models/models.py` - Extended MasterUser and User models
- `api/models/models_per_tenant.py` - Extended TenantUser model
- `api/routers/auth.py` - Added Azure AD OAuth endpoints and client
- `docker-compose.yml` - Added Azure AD environment variables
- `ui/src/pages/Login.tsx` - Added Microsoft login button and handler
- `ui/src/i18n/locales/*.json` - Added Microsoft login translations
- `mobile/src/i18n/locales/*.json` - Added mobile translations

#### 🧪 Testing

- Manual testing scenarios documented
- Error handling verification
- Multi-language UI testing
- Database integration testing
- OAuth flow validation

---

## [Previous] - Bank Statement Processing Improvements

### Summary

Enhanced bank statement extraction service and added CSV export + expense creation features to the transactions interface.

## Changes Made

### 1. Bank Statement Service Refactor

- **File**: `api/services/statement_service.py`
- **Issue**: Bank statement extraction was not finding all 14 transactions from test PDF
- **Solution**: Refactored service using proven patterns from `test-main.py`
- **Key Changes**:
  - Updated date normalization to use exact formats from test-main.py Pydantic validator
  - Simplified regex patterns to match test-main.py `_extract_with_regex` method
  - Streamlined text preprocessing to match test-main.py approach
  - Removed bank-specific (RBC) optimizations for generic compatibility
  - Enhanced LLM response parsing with proper fallback to regex extraction

### 2. CSV Export Feature

- **File**: `ui/src/pages/Statements.tsx`
- **Feature**: Added CSV export functionality for transaction data
- **Implementation**:
  - Export button with FileText icon
  - Proper CSV formatting with quoted descriptions
  - Filename includes original PDF name
  - Handles all transaction fields (Date, Description, Amount, Type, Balance, Category)

### 3. Financial Summary Display

- **File**: `ui/src/pages/Statements.tsx`
- **Feature**: Added income/expense totals above transaction table
- **Implementation**:
  - Three-column grid showing Total Income, Total Expenses, Net Amount
  - Color-coded values (green for positive, red for negative)
  - Real-time calculation as transactions change
  - Only displays when transactions exist

### 4. Expense Creation from Transactions

- **File**: `ui/src/pages/Statements.tsx`
- **Feature**: Create expense records from debit transactions
- **Implementation**:
  - "Expense" button in Actions column for debit transactions only
  - Maps bank transaction categories to valid expense categories
  - Auto-populates expense with transaction data
  - Links back to bank statement via notes field
  - Sets appropriate defaults (Bank Transfer, completed status)

## Technical Details

### Bank Statement Extraction Patterns

```javascript
// Simplified regex patterns from test-main.py
patterns = [
  r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([^$\d-]+?)\s+([-$]?\d+\.?\d*)',
  r'(\d{4}-\d{2}-\d{2})\s+([^$\d-]+?)\s+([-$]?\d+\.?\d*)',
]
```

### Category Mapping

```javascript
const categoryMap = {
  'Transportation': 'Transportation',
  'Food': 'Meals',
  'Travel': 'Travel',
  'Other': 'General'
};
```

## Files Modified

- `api/services/statement_service.py` - Complete refactor
- `ui/src/pages/Statements.tsx` - Added CSV export, totals, expense creation

## Testing

- Verified with test PDF that all 14 transactions are now extracted
- CSV export generates proper format with all fields
- Expense creation works for debit transactions with proper category mapping
- Financial totals calculate correctly and update in real-time
