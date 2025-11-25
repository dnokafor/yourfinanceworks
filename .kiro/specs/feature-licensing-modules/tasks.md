# Implementation Plan: Feature Licensing & Modularization System

## Overview

This implementation plan covers building a complete feature licensing system for self-hosted installations, including license generation, verification, feature gating, and payment integration.

## Task List

- [x] 1. Setup and Infrastructure
- [x] 1.1 Generate RSA key pair for license signing
  - Run key generation script to create private_key.pem and public_key.pem
  - Secure private key (chmod 600, add to .gitignore)
  - Store public key for embedding in application
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Install required dependencies
  - Add PyJWT library to api/requirements.txt
  - Add cryptography library for RSA operations
  - Install dependencies: pip install PyJWT cryptography
  - _Requirements: 1.1_

- [x] 2. Database Schema and Models
- [x] 2.1 Create database models for license management
  - Create InstallationInfo model in api/models/models_per_tenant.py
  - Create LicenseValidationLog model for audit trail
  - Add fields: installation_id, trial dates, license key, features, etc.
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2.2 Create Alembic migration for license tables
  - Generate migration: alembic revision -m "add_license_tables"
  - Add InstallationInfo and LicenseValidationLog tables
  - Test migration: alembic upgrade head
  - _Requirements: 1.1_

- [x] 3. Customer-Side License Verification (Core)
- [x] 3.1 Create LicenseService for verification
  - Create api/services/license_service.py
  - Implement verify_license() method with JWT signature verification
  - Embed public key in the service
  - Add caching for validation results (1 hour TTL)
  - _Requirements: 1.3, 1.4, 1.5_

- [x] 3.2 Implement trial management
  - Add is_trial_active() method to check 30-day trial
  - Add get_trial_status() method for detailed trial info
  - Implement grace period (7 days after trial expiration)
  - Auto-create installation record on first startup
  - _Requirements: 1.1, 1.2_

- [x] 3.3 Implement license activation
  - Add activate_license() method to save license to database
  - Add deactivate_license() method to remove license
  - Add get_enabled_features() to return list of licensed features
  - Add has_feature() helper for feature checks
  - _Requirements: 1.2, 1.3, 1.4_

- [ ] 4. Feature Gating System
- [x] 4.1 Create feature gate decorator
  - Create api/utils/feature_gate.py
  - Implement @require_feature(feature_id) decorator
  - Return HTTP 402 (Payment Required) when feature not licensed
  - Include upgrade message in error response
  - _Requirements: 1.3, 1.4_

- [x] 4.2 Create feature configuration service
  - Create api/services/feature_config_service.py
  - Define FEATURES dictionary with all licensable features
  - Implement is_enabled() method with environment variable fallback
  - Add get_enabled_features() for listing all features
  - _Requirements: 1.1, 1.11_

- [x] 4.3 Add feature gates to AI endpoints
  - Add @require_feature("ai_invoice") to AI invoice endpoints
  - Add @require_feature("ai_expense") to AI expense endpoints
  - Add @require_feature("ai_bank_statement") to bank statement endpoints
  - Add @require_feature("ai_chat") to AI chat endpoints
  - _Requirements: 1.4_

- [x] 4.4 Add feature gates to integration endpoints
  - Add @require_feature("tax_integration") to tax service endpoints
  - Add @require_feature("slack_integration") to Slack endpoints
  - Add @require_feature("batch_processing") to batch processing endpoints
  - _Requirements: 1.5_

- [x] 4.5 Add feature gates to advanced endpoints
  - Add @require_feature("inventory") to inventory endpoints
  - Add @require_feature("approvals") to approval workflow endpoints
  - Add @require_feature("reporting") to advanced reporting endpoints
  - _Requirements: 1.6_

- [x] 5. License Management API (Customer-Side)
- [x] 5.1 Create license router
  - Create api/routers/license.py
  - Add GET /license/status endpoint for trial/license status
  - Add POST /license/activate endpoint for license activation
  - Add POST /license/validate endpoint for manual validation
  - _Requirements: 1.7_

- [x] 5.2 Add feature availability endpoint
  - Add GET /license/features endpoint to list all features
  - Return feature ID, name, description, and enabled status
  - Include trial status and expiration info
  - _Requirements: 1.7, 1.8_

- [x] 5.3 Register license router in main.py
  - Import license router in api/main.py
  - Add app.include_router(license.router, prefix="/api/v1")
  - Test endpoints with curl or Postman
  - _Requirements: 1.7_

- [x] 6. Frontend License Management UI
- [x] 6.1 Create FeatureContext for React
  - Create ui/src/contexts/FeatureContext.tsx
  - Implement FeatureProvider component
  - Add useFeatures() hook for accessing feature flags
  - Fetch enabled features from /license/features endpoint
  - _Requirements: 1.8_

- [x] 6.2 Create FeatureGate component
  - Create ui/src/components/FeatureGate.tsx
  - Implement conditional rendering based on feature availability
  - Add showUpgradePrompt prop for locked features
  - Add fallback prop for alternative content
  - _Requirements: 1.8_

- [x] 6.3 Create License Management page
  - Create ui/src/pages/LicenseManagement.tsx
  - Show current license status (trial/licensed/expired)
  - Add license key input field and activate button
  - Display enabled features and expiration date
  - Add "Purchase License" button linking to pricing page
  - _Requirements: 1.7, 1.8_

- [x] 6.4 Add license management to navigation
  - Add "License" menu item in Settings dropdown
  - Add route in ui/src/App.tsx
  - Show trial banner when in trial mode
  - Show expiration warning 30 days before expiration
  - _Requirements: 1.8_

- [x] 6.5 Update UI components with feature gates
  - Wrap AI processing buttons with <FeatureGate feature="ai_invoice">
  - Hide integration settings when features not licensed
  - Show upgrade prompts for locked features
  - Update navigation to hide unlicensed feature pages
  - _Requirements: 1.8_

- [x] 7. License Generation System (Your Side)
- [x] 7.1 Create license generator script
  - Create separate repo/folder for license server code
  - Create license_generator.py with LicenseGenerator class
  - Implement generate_license() method using PyJWT
  - Sign licenses with private key (RSA256)
  - _Requirements: 1.2_

- [x] 7.2 Create CLI tool for license generation
  - Create generate_license_cli.py
  - Add command-line arguments (email, name, features, duration)
  - Support trial license generation
  - Output license key and save to file option
  - _Requirements: 1.2, 1.10_

- [ ]* 7.3 Create web-based license generator (optional)
  - Create Flask app for license generation UI
  - Add form for customer info and feature selection
  - Generate and display license key
  - Add copy-to-clipboard functionality
  - _Requirements: 1.10_

- [x] 8. Payment Integration (Stripe)
- [x] 8.1 Create Stripe checkout integration
  - Set up Stripe account and get API keys
  - Create pricing page on your website
  - Implement Stripe Checkout session creation
  - Add feature selection and pricing logic
  - _Requirements: 1.2_

- [x] 8.2 Implement Stripe webhook handler
  - Create webhook endpoint for checkout.session.completed
  - Verify webhook signature for security
  - Extract customer info and purchased features
  - Generate license key automatically
  - _Requirements: 1.2_

- [x] 8.3 Implement license email delivery
  - Create email template for license delivery
  - Include license key, features, and activation instructions
  - Send email via SMTP/SendGrid/AWS SES
  - Log email delivery for tracking
  - _Requirements: 1.2, 1.7_

- [x] 8.4 Create license database for tracking
  - Create database to store issued licenses
  - Track customer email, features, expiration, payment info
  - Add license lookup and management endpoints
  - _Requirements: 1.10_

- [x] 9. Testing and Validation
- [x] 9.1 Test license generation and verification
  - Generate test license with CLI tool
  - Verify signature validation works correctly
  - Test expiration date enforcement
  - Test invalid license rejection
  - _Requirements: 1.3, 1.9_

- [x] 9.2 Test trial functionality
  - Test 30-day trial auto-activation on first install
  - Test grace period after trial expiration
  - Test feature access during trial
  - Test feature blocking after trial expires
  - _Requirements: 1.2_

- [x] 9.3 Test feature gating
  - Test API endpoints with and without licenses
  - Verify HTTP 402 responses for unlicensed features
  - Test feature gates with expired licenses
  - Test UI feature visibility based on license
  - _Requirements: 1.3, 1.4, 1.8, 1.9_

- [x] 9.4 Test payment flow end-to-end
  - Test Stripe checkout with test card
  - Verify webhook receives payment notification
  - Verify license generation and email delivery
  - Test license activation in customer app
  - _Requirements: 1.2_

- [x] 10. Documentation and Deployment
- [x] 10.1 Create customer documentation
  - Document how to activate a license
  - Explain trial period and grace period
  - Create FAQ for common license issues
  - Document how to purchase additional features
  - _Requirements: 1.12_

- [x] 10.2 Create admin documentation
  - Document license generation process
  - Explain how to handle customer support requests
  - Document license revocation process (if implemented)
  - Create troubleshooting guide
  - _Requirements: 1.10_

- [x] 10.3 Update deployment scripts
  - Add database migration to deployment process
  - Ensure public key is embedded in production builds
  - Add environment variables for feature flags
  - Test deployment on staging environment
  - _Requirements: 1.12_

- [x] 10.4 Create migration script for existing customers
  - Create script to generate licenses for existing tenants
  - Auto-activate all features for existing customers
  - Send notification emails about new licensing system
  - Provide grace period before enforcement
  - _Requirements: 1.12_

## Optional Enhancements (Future)

- [ ]* 11. Advanced Features
- [ ]* 11.1 Add online license validation
  - Implement optional online check to license server
  - Check for license revocation
  - Rate limit to once per day
  - Gracefully handle offline mode
  - _Requirements: 1.9_

- [ ]* 11.2 Add usage analytics
  - Track feature usage per tenant
  - Send anonymous usage stats to license server
  - Generate usage reports for customers
  - _Requirements: 1.10_

- [ ]* 11.3 Create license management dashboard
  - Build admin dashboard for license management
  - View all issued licenses
  - Search and filter licenses
  - Manually revoke or extend licenses
  - _Requirements: 1.10_

- [ ]* 11.4 Add automatic renewal reminders
  - Send email 30 days before expiration
  - Send email 7 days before expiration
  - Send email on expiration day
  - Include renewal link in emails
  - _Requirements: 1.7_

## Notes

- Tasks marked with * are optional and can be skipped for MVP
- Focus on core functionality first (tasks 1-6)
- Payment integration (tasks 7-8) can be added after core is working
- Test thoroughly before deploying to production
- Keep private key secure at all times
- Consider starting with environment variable feature flags before full licensing

## Success Criteria

- ✅ Customers can install and use app with 30-day trial
- ✅ Customers can purchase licenses via Stripe
- ✅ Customers receive license key via email within 1 minute
- ✅ Customers can activate license in app
- ✅ Features are gated based on license
- ✅ License verification works offline
- ✅ Expired licenses disable features automatically
- ✅ UI shows only licensed features
- ✅ System is secure (can't forge licenses)
- ✅ Existing customers retain access (backward compatible)
