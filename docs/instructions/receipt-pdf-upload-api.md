# Receipt PDF Upload API Guide

This guide explains how to upload receipt PDFs and other supported file formats as expenses using the API.

## Overview

The expense management system supports uploading receipt files (PDF, JPG, PNG) with automatic AI-powered data extraction. The system processes uploaded receipts using OCR (Optical Character Recognition) to extract expense details like amount, vendor, date, and category.

## Supported File Types

- **PDF files** (`.pdf`)
- **JPEG images** (`.jpg`, `.jpeg`)
- **PNG images** (`.png`)

## File Limitations

- **Maximum file size**: 10 MB
- **Maximum attachments per expense**: 10 files
- **Content type validation**: Files must match their declared MIME type

## API Endpoints

### Base URL
```
https://your-api-domain.com
```

### Authentication
All requests require a valid API token in the Authorization header:
```
Authorization: Bearer YOUR_API_TOKEN
```

## Complete Workflow

### Step 1: Create an Expense

**Endpoint:** `POST /expenses/`

```bash
curl -X POST "https://your-api-domain.com/expenses/" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 25.99,
    "currency": "USD",
    "expense_date": "2024-10-28",
    "category": "Meals",
    "vendor": "Restaurant ABC",
    "payment_method": "Credit Card",
    "notes": "Business lunch with client"
  }'
```

**Response:**
```json
{
  "id": 123,
  "amount": 25.99,
  "currency": "USD",
  "expense_date": "2024-10-28T00:00:00Z",
  "category": "Meals",
  "vendor": "Restaurant ABC",
  "status": "recorded",
  "analysis_status": "not_started",
  "created_at": "2024-10-28T10:30:00Z",
  "updated_at": "2024-10-28T10:30:00Z"
}
```

### Step 2: Upload Receipt File

**Endpoint:** `POST /expenses/{expense_id}/upload-receipt`

#### Upload PDF Receipt
```bash
curl -X POST "https://your-api-domain.com/expenses/123/upload-receipt" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@/path/to/receipt.pdf"
```

#### Upload JPG Receipt
```bash
curl -X POST "https://your-api-domain.com/expenses/123/upload-receipt" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@/path/to/receipt.jpg"
```

#### Upload PNG Receipt
```bash
curl -X POST "https://your-api-domain.com/expenses/123/upload-receipt" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@/path/to/receipt.png"
```

**Success Response:**
```json
{
  "message": "Attachment uploaded successfully",
  "filename": "receipt.pdf",
  "size": 245760,
  "file_path": "attachments/tenant_1/expenses/expense_123_receipt_abc123.pdf"
}
```

### Step 3: Monitor Processing Status

After upload, the system automatically queues the file for AI processing. You can check the status:

#### Get Expense Details
```bash
curl -X GET "https://your-api-domain.com/expenses/123" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**Response with AI Processing Status:**
```json
{
  "id": 123,
  "amount": 25.99,
  "analysis_status": "queued",  // or "processing", "done", "failed"
  "imported_from_attachment": true,
  "analysis_result": null,  // Will contain extracted data when complete
  "analysis_error": null,   // Will contain error message if failed
  ...
}
```

#### List Attachments
```bash
curl -X GET "https://your-api-domain.com/expenses/123/attachments" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**Response:**
```json
[
  {
    "id": 456,
    "filename": "receipt.pdf",
    "content_type": "application/pdf",
    "size_bytes": 245760,
    "uploaded_at": "2024-10-28T10:35:00Z"
  }
]
```

## AI Processing Workflow

1. **Upload**: File is uploaded and stored securely
2. **Queue**: File is queued for AI processing (analysis_status: "queued")
3. **Processing**: AI extracts data from receipt (analysis_status: "processing")
4. **Complete**: Extracted data updates expense fields (analysis_status: "done")
5. **Manual Override**: User can manually edit to override AI results

### Extracted Data Fields

The AI system can extract and populate:
- Amount
- Vendor/Merchant name
- Transaction date
- Category (based on vendor type)
- Tax amount
- Currency
- Payment method

## Advanced Operations

### Reprocess Failed OCR

If AI processing fails, you can trigger reprocessing:

```bash
curl -X POST "https://your-api-domain.com/expenses/123/reprocess" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**Response:**
```json
{
  "message": "Expense reprocessing started",
  "status": "queued"
}
```

### Download Attachment

```bash
curl -X GET "https://your-api-domain.com/expenses/123/attachments/456/download" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -o "downloaded_receipt.pdf"
```

### Delete Attachment

```bash
curl -X DELETE "https://your-api-domain.com/expenses/123/attachments/456" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## Error Handling

### Common Error Responses

#### File Too Large (>10MB)
```json
{
  "detail": "File too large. Maximum size is 10 MB"
}
```

#### Unsupported File Type
```json
{
  "detail": "File type not allowed. Supported: PDF, JPG, PNG"
}
```

#### Missing Filename
```json
{
  "detail": "Filename is required"
}
```

#### Too Many Attachments
```json
{
  "detail": "Maximum of 10 attachments per expense"
}
```

#### Expense Not Found
```json
{
  "detail": "Expense not found"
}
```

#### Invalid Content Type
```json
{
  "detail": "File type not allowed. Supported: PDF, JPG, PNG"
}
```

### HTTP Status Codes

- `200 OK`: Successful upload
- `400 Bad Request`: Invalid file or request
- `401 Unauthorized`: Invalid or missing API token
- `404 Not Found`: Expense not found
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Server processing error

## Security Features

- **Tenant Isolation**: Files are stored in tenant-specific directories
- **File Validation**: Content type and extension validation
- **Path Validation**: Prevents directory traversal attacks
- **UUID Filenames**: Prevents filename collisions and guessing
- **Access Control**: Role-based permissions (non-viewer required)

## Best Practices

1. **File Naming**: Use descriptive filenames for easier identification
2. **File Quality**: Higher quality images/PDFs improve AI extraction accuracy
3. **File Size**: Optimize file size while maintaining readability
4. **Error Handling**: Always check response status and handle errors gracefully
5. **Status Monitoring**: Poll expense status to track AI processing completion
6. **Batch Processing**: For multiple receipts, create expenses first, then upload files

## Example Integration Script

```bash
#!/bin/bash

API_BASE="https://your-api-domain.com"
API_TOKEN="YOUR_API_TOKEN"
RECEIPT_FILE="/path/to/receipt.pdf"

# Step 1: Create expense
EXPENSE_RESPONSE=$(curl -s -X POST "$API_BASE/expenses/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "currency": "USD",
    "expense_date": "2024-10-28",
    "category": "Office Supplies",
    "vendor": "Office Store",
    "payment_method": "Credit Card"
  }')

# Extract expense ID
EXPENSE_ID=$(echo $EXPENSE_RESPONSE | jq -r '.id')

if [ "$EXPENSE_ID" != "null" ]; then
  echo "Created expense with ID: $EXPENSE_ID"
  
  # Step 2: Upload receipt
  UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/expenses/$EXPENSE_ID/upload-receipt" \
    -H "Authorization: Bearer $API_TOKEN" \
    -F "file=@$RECEIPT_FILE")
  
  echo "Upload response: $UPLOAD_RESPONSE"
  
  # Step 3: Check processing status
  sleep 5  # Wait for processing to start
  STATUS_RESPONSE=$(curl -s -X GET "$API_BASE/expenses/$EXPENSE_ID" \
    -H "Authorization: Bearer $API_TOKEN")
  
  ANALYSIS_STATUS=$(echo $STATUS_RESPONSE | jq -r '.analysis_status')
  echo "Analysis status: $ANALYSIS_STATUS"
else
  echo "Failed to create expense"
fi
```

## Support

For technical support or questions about the Receipt PDF Upload API:
- Check the API response for detailed error messages
- Ensure file meets size and type requirements
- Verify API token has proper permissions
- Monitor analysis_status for processing updates

---

*Last updated: October 28, 2024*