# Invoice Attachment Migration Guide

This guide helps you migrate from the legacy `upload-attachment` endpoint to the new `attachments` endpoint system.

## Overview

The invoice attachment system has been upgraded to provide better functionality, metadata support, and multiple attachment capabilities per invoice.

### Key Changes

| Aspect | Legacy System | New System |
|--------|---------------|------------|
| **Endpoint** | `POST /invoices/{id}/upload-attachment` | `POST /invoices/{id}/attachments` |
| **Storage** | Single attachment per invoice | Multiple attachments per invoice |
| **Database** | `attachment_path`, `attachment_filename` fields | Dedicated `InvoiceAttachment` table |
| **Metadata** | Basic filename only | Type, description, document classification |
| **File Types** | PDF, DOC, DOCX, JPG, PNG | PDF, DOC, DOCX, JPG, PNG, GIF, XLS, XLSX, TXT, CSV |
| **Response** | Basic success message | Full attachment metadata with ID |

## Migration Steps

### 1. Update API Calls

#### Frontend (TypeScript/JavaScript)

**Before (Legacy):**
```typescript
// Old way
const response = await fetch(`/invoices/${invoiceId}/upload-attachment`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

**After (New):**
```typescript
// New way with enhanced options
const formData = new FormData();
formData.append('file', file);
formData.append('attachment_type', 'document'); // 'image' or 'document'
formData.append('document_type', 'contract');   // Optional classification
formData.append('description', 'Signed service agreement'); // Optional

const response = await fetch(`/invoices/${invoiceId}/attachments`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

#### Mobile (React Native)

**Before:**
```typescript
const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/upload-attachment`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data',
  },
  body: formData,
});
```

**After:**
```typescript
const formData = new FormData();
formData.append('file', {
  uri: fileUri,
  type: 'application/pdf',
  name: 'contract.pdf',
} as any);
formData.append('attachment_type', 'document');
formData.append('description', 'Contract document');

const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/attachments`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data',
  },
  body: formData,
});
```

#### cURL Examples

**Before:**
```bash
curl -X POST "https://api.example.com/invoices/123/upload-attachment" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@contract.pdf"
```

**After:**
```bash
curl -X POST "https://api.example.com/invoices/123/attachments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@contract.pdf" \
  -F "attachment_type=document" \
  -F "document_type=contract" \
  -F "description=Signed service agreement"
```

### 2. Update Response Handling

#### Legacy Response Format
```json
{
  "message": "Attachment uploaded successfully",
  "filename": "contract.pdf",
  "size": 245760,
  "attachment_path": "/path/to/file",
  "attachment_filename": "contract.pdf",
  "has_attachment": true
}
```

#### New Response Format
```json
{
  "id": 789,
  "invoice_id": 123,
  "filename": "contract.pdf",
  "file_size": 245760,
  "attachment_type": "document",
  "document_type": "contract",
  "description": "Signed service agreement",
  "created_at": "2024-10-28T10:30:00Z",
  "status": "success",
  "message": "Attachment uploaded successfully"
}
```

### 3. Database Migration

Two migration scripts are provided depending on your setup:

#### Option A: Full FastAPI Environment (Recommended for Production)

```bash
# Requires DATABASE_URL environment variable and full FastAPI setup
export DATABASE_URL="your_database_url"

# Dry run to see what would be migrated
python api/scripts/migrate_invoice_attachments.py --tenant-id 1 --dry-run

# Run actual migration
python api/scripts/migrate_invoice_attachments.py --tenant-id 1

# Clean up legacy fields after verifying migration
python api/scripts/migrate_invoice_attachments.py --tenant-id 1 --cleanup --dry-run
python api/scripts/migrate_invoice_attachments.py --tenant-id 1 --cleanup
```

#### Option B: Simple SQLite Migration (For Development/Testing)

```bash
# Works directly with SQLite database files
# Dry run to see what would be migrated
python api/scripts/migrate_invoice_attachments_simple.py --database-url "sqlite:///./tenant_1.db" --dry-run

# Run actual migration
python api/scripts/migrate_invoice_attachments_simple.py --database-url "sqlite:///./tenant_1.db"

# Clean up legacy fields after verifying migration
python api/scripts/migrate_invoice_attachments_simple.py --database-url "sqlite:///./tenant_1.db" --cleanup --dry-run
python api/scripts/migrate_invoice_attachments_simple.py --database-url "sqlite:///./tenant_1.db" --cleanup
```

### 4. Update Tests

**Before:**
```python
response = client.post(
    f"/api/v1/invoices/{invoice_id}/upload-attachment",
    files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    headers=auth_headers,
)
```

**After:**
```python
response = client.post(
    f"/api/v1/invoices/{invoice_id}/attachments",
    files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    data={
        "attachment_type": "document",
        "document_type": "invoice",
        "description": "Test invoice attachment"
    },
    headers=auth_headers,
)
```

## Enhanced Features

### 1. Multiple Attachments

The new system supports multiple attachments per invoice:

```typescript
// Upload multiple files
const files = [contractFile, invoiceFile, receiptFile];

for (const file of files) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('attachment_type', getAttachmentType(file));
  formData.append('description', getFileDescription(file));
  
  await fetch(`/invoices/${invoiceId}/attachments`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
}
```

### 2. List All Attachments

```typescript
// Get all attachments for an invoice
const response = await fetch(`/invoices/${invoiceId}/attachments`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();
console.log(`Invoice has ${data.total_count} attachments`);
```

### 3. Attachment Metadata

```typescript
// Upload with rich metadata
const formData = new FormData();
formData.append('file', file);
formData.append('attachment_type', 'document');
formData.append('document_type', 'contract');
formData.append('description', 'Master service agreement - signed version');
```

## Backward Compatibility

The legacy endpoint remains active during the transition period, but:

1. **New features** (multiple attachments, metadata) are only available in the new system
2. **File type support** is limited in the legacy endpoint
3. **Future development** will focus on the new system

## Migration Checklist

### Code Updates
- [x] Update all frontend API calls to use `/attachments` endpoint
- [x] Update mobile app API calls  
- [x] Add support for new optional parameters (`attachment_type`, `document_type`, `description`)
- [x] Update response handling to use new format
- [x] Update tests to use new endpoint
- [x] Update documentation and API guides
- [x] Mark legacy endpoint as deprecated

### Database Migration
- [ ] Choose appropriate migration script (full FastAPI vs simple SQLite)
- [ ] Run migration script in dry-run mode first
- [ ] Verify migration results
- [ ] Run actual migration
- [ ] Test that all existing attachments are accessible
- [ ] Test multiple attachment functionality
- [ ] Clean up legacy database fields (after verification)

### Testing & Deployment
- [ ] Test new endpoint functionality
- [ ] Verify backward compatibility with legacy endpoint
- [ ] Test file upload with new metadata parameters
- [ ] Test multiple attachments per invoice
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Monitor for any issues

## Rollback Plan

If issues arise during migration:

1. **API Level**: The legacy endpoint remains active, so you can revert API calls
2. **Database Level**: Legacy fields are preserved until manual cleanup
3. **Files**: Original files remain in their locations

To rollback:
1. Revert frontend code changes
2. Legacy attachments continue to work as before
3. New attachment records can be safely removed if needed

## Testing the Migration

### 1. Test Legacy Compatibility
```bash
# Verify legacy endpoint still works
curl -X POST "https://api.example.com/invoices/123/upload-attachment" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"
```

### 2. Test New Functionality
```bash
# Test new endpoint with metadata
curl -X POST "https://api.example.com/invoices/123/attachments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "attachment_type=document" \
  -F "description=Test attachment"
```

### 3. Test Multiple Attachments
```bash
# Upload multiple files to same invoice
curl -X POST "https://api.example.com/invoices/123/attachments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@contract.pdf" \
  -F "attachment_type=document"

curl -X POST "https://api.example.com/invoices/123/attachments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@receipt.jpg" \
  -F "attachment_type=image"
```

### 4. Verify Migration Results
```bash
# List all attachments
curl -X GET "https://api.example.com/invoices/123/attachments" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Support and Troubleshooting

### Common Issues

1. **File type not supported**: Check the expanded file type list in the new system
2. **Missing metadata**: The new system accepts optional metadata parameters
3. **Multiple attachments not showing**: Ensure you're using the new `/attachments` list endpoint
4. **Legacy attachments missing**: Run the migration script to convert them

### Getting Help

- Check the migration script logs for detailed error messages
- Verify file permissions and paths during migration
- Test with small files first before migrating large attachments
- Keep backups of the database before running cleanup operations

---

*Migration guide last updated: October 28, 2024*