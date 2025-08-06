# TODO List

## High Priority

### Invoice Attachments System
- [ ] **URGENT**: Implement invoice attachment upload/download functionality
  - [ ] Add attachment field to Invoice model
  - [ ] Create upload endpoint for invoice attachments
  - [ ] Create download endpoint for invoice attachments
  - [ ] Add attachment UI to invoice create/edit forms
  - [ ] Support multiple file types (PDF, DOC, DOCX, JPG, JPEG, PNG)
  - [ ] File size validation and security checks

### AI Configuration Issues
- [ ] **BUG**: PDF import shows "LLM not configured" even when AI config is tested
  - [ ] Current fix: Updated AI status check to require both active AND tested configs
  - [ ] Need to verify this resolves the issue completely
  - [ ] Consider adding more detailed AI status information

## Medium Priority

### Database & Migration Issues
- [x] **FIXED**: Multiple head revisions in alembic migrations
- [x] **FIXED**: Master database table creation issues
- [x] **FIXED**: Tenant database migration errors with master_users table

### API Improvements
- [x] **FIXED**: Missing /invoices/ai-status endpoint (422 error)
- [x] **FIXED**: 502 Bad Gateway errors due to nginx proxy configuration

## Low Priority

### General Improvements
- [ ] Add comprehensive error logging for AI configuration tests
- [ ] Improve user feedback for AI configuration status
- [ ] Add retry mechanism for failed AI operations
- [ ] Optimize database queries for better performance

## Completed
- [x] Fixed AI configuration test error handling
- [x] Added missing database session dependencies in AI config endpoints
- [x] Fixed import path issues in PDF processor router
- [x] Added translation updates for settings
- [x] Resolved database migration conflicts