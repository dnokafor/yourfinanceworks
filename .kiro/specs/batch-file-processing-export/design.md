# Design Document

## Overview

The Batch File Processing and Export system enables external API clients to upload multiple documents (invoices, expenses, bank statements) in a single request, process them asynchronously using existing OCR infrastructure, and export structured results to configured cloud storage destinations. The system provides both UI and API interfaces for managing export destinations with secure credential storage.

### Key Design Principles

1. **Leverage Existing Infrastructure**: Reuse Kafka-based OCR processing, cloud storage service, and API key authentication
2. **Async-First**: All file processing is asynchronous to handle large batches without blocking
3. **Multi-Tenant Isolation**: All operations respect tenant boundaries with encrypted credential storage
4. **Fail-Safe**: Partial failures don't block entire batch; individual file errors are tracked
5. **Extensible**: New export destinations can be added without changing core logic

## Architecture

### High-Level Components

```
┌─────────────────┐
│   API Client    │
│  (External)     │
└────────┬────────┘
         │ X-API-Key
         ▼
┌─────────────────────────────────────────────────────────┐
│              Batch Upload API Endpoint                   │
│  POST /api/v1/batch-processing/upload                   │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           Batch Processing Service                       │
│  - Validates files & destination config                  │
│  - Creates BatchProcessingJob record                     │
│  - Enqueues files to Kafka topics                       │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              Kafka Topics (Existing)                     │
│  - invoice_ocr                                          │
│  - expense_ocr                                          │
│  - bank_statements_ocr                                  │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           OCR Workers (Existing)                         │
│  - Process files via Unstructured/LLM                   │
│  - Extract structured data                              │
│  - Update BatchFileProcessing records                   │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│         Batch Completion Monitor                         │
│  - Watches for job completion                           │
│  - Triggers CSV export when all files done              │
│  - Sends webhook notifications                          │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│            Export Service                                │
│  - Generates CSV from processed data                    │
│  - Uploads to configured destination                    │
│  - Updates job with export URL                          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload Phase**:
   - API client sends batch upload request with files and destination config
   - System validates API key, files, and export destination
   - Creates `BatchProcessingJob` record with status "pending"
   - Creates `BatchFileProcessing` record for each file
   - Enqueues files to appropriate Kafka topics
   - Returns job ID immediately

2. **Processing Phase**:
   - Existing OCR workers consume messages from Kafka
   - Workers process files and extract structured data
   - Workers update `BatchFileProcessing` status and results
   - System tracks progress across all files in the job

3. **Export Phase**:
   - Completion monitor detects when all files are processed
   - Export service generates CSV with all results
   - CSV is uploaded to configured destination (S3, Azure, GCS, Google Drive)
   - Job status updated to "completed" with export URL
   - Webhook notification sent if configured

## Components and Interfaces

### 1. Database Models

#### BatchProcessingJob

```python
class BatchProcessingJob(Base):
    """Tracks batch file processing jobs"""
    __tablename__ = "batch_processing_jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), unique=True, nullable=False)  # UUID
    tenant_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    api_client_id = Column(String(100), nullable=False)
    
    # Job configuration
    document_types = Column(JSON)  # ["invoice", "expense", "statement"]
    total_files = Column(Integer, nullable=False)
    export_destination_type = Column(String(50))  # s3, azure, gcs, google_drive
    export_destination_config_id = Column(Integer, ForeignKey("export_destination_configs.id"))
    custom_fields = Column(JSON)  # Optional field selection
    
    # Status tracking
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, partial_failure
    processed_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Export results
    export_file_url = Column(String(500))
    export_file_key = Column(String(500))
    export_completed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    files = relationship("BatchFileProcessing", back_populates="job")
    export_destination = relationship("ExportDestinationConfig")
```

#### BatchFileProcessing

```python
class BatchFileProcessing(Base):
    """Tracks individual file processing within a batch job"""
    __tablename__ = "batch_file_processing"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey("batch_processing_jobs.job_id"), nullable=False)
    
    # File information
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500))
    file_path = Column(String(1000))
    cloud_file_url = Column(String(1000))
    file_size = Column(Integer)
    document_type = Column(String(50))  # invoice, expense, statement
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Extracted data (stored as JSON for flexibility)
    extracted_data = Column(JSON)  # Vendor, amount, date, line items, etc.
    
    # Kafka tracking
    kafka_topic = Column(String(100))
    kafka_message_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processing_started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    job = relationship("BatchProcessingJob", back_populates="files")
```

#### ExportDestinationConfig

```python
class ExportDestinationConfig(Base):
    """Stores export destination configurations per tenant"""
    __tablename__ = "export_destination_configs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False)
    
    # Destination details
    name = Column(String(200), nullable=False)  # User-friendly name
    destination_type = Column(String(50), nullable=False)  # s3, azure, gcs, google_drive
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Encrypted credentials (using tenant encryption key)
    encrypted_credentials = Column(LargeBinary)  # Encrypted JSON blob
    
    # Destination-specific configuration
    config = Column(JSON)  # Bucket name, container, folder ID, path prefix, etc.
    
    # Connection testing
    last_test_at = Column(DateTime(timezone=True))
    last_test_success = Column(Boolean)
    last_test_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Indexes
    __table_args__ = (
        Index('idx_export_dest_tenant', 'tenant_id'),
        Index('idx_export_dest_active', 'tenant_id', 'is_active'),
    )
```

### 2. API Endpoints

#### Batch Upload Endpoint

```python
POST /api/v1/batch-processing/upload
Headers:
  X-API-Key: <api_key>
  Content-Type: multipart/form-data

Request Body:
  files: [file1, file2, ...file50]  # Up to 50 files
  document_types: ["invoice", "expense", "statement"]  # Optional, auto-detect if not provided
  export_destination_id: <int>  # ID of configured export destination
  custom_fields: ["vendor", "amount", "date", "line_items"]  # Optional field selection
  webhook_url: <url>  # Optional webhook for completion notification

Response (201 Created):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "total_files": 25,
  "estimated_completion_minutes": 15,
  "status_url": "/api/v1/batch-processing/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

#### Job Status Endpoint

```python
GET /api/v1/batch-processing/jobs/{job_id}
Headers:
  X-API-Key: <api_key>

Response (200 OK):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percentage": 68.0,
  "total_files": 25,
  "processed_files": 17,
  "successful_files": 16,
  "failed_files": 1,
  "export_file_url": null,
  "created_at": "2025-11-08T10:30:00Z",
  "estimated_completion_at": "2025-11-08T10:45:00Z",
  "files": [
    {
      "filename": "invoice_001.pdf",
      "status": "completed",
      "document_type": "invoice",
      "extracted_data": {
        "vendor": "Acme Corp",
        "amount": 1250.00,
        "currency": "USD",
        "date": "2025-11-01",
        "attachment_paths": "s3://bucket/tenant_1/invoices/001.pdf"
      }
    },
    {
      "filename": "receipt_002.jpg",
      "status": "failed",
      "error_message": "OCR extraction failed: Image quality too low"
    }
  ]
}
```

#### List Jobs Endpoint

```python
GET /api/v1/batch-processing/jobs
Headers:
  X-API-Key: <api_key>
Query Parameters:
  status: <pending|processing|completed|failed>
  limit: <int>
  offset: <int>

Response (200 OK):
{
  "jobs": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### Export Destination Management Endpoints

```python
# Create destination
POST /api/v1/export-destinations
Headers:
  X-API-Key: <api_key>
Body:
{
  "name": "Production S3 Bucket",
  "destination_type": "s3",
  "credentials": {
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "region": "us-east-1"
  },
  "config": {
    "bucket_name": "my-exports",
    "path_prefix": "batch-results/"
  }
}

# List destinations
GET /api/v1/export-destinations
Headers:
  X-API-Key: <api_key>

# Update destination
PUT /api/v1/export-destinations/{id}
Headers:
  X-API-Key: <api_key>

# Test destination connection
POST /api/v1/export-destinations/{id}/test
Headers:
  X-API-Key: <api_key>

# Delete destination
DELETE /api/v1/export-destinations/{id}
Headers:
  X-API-Key: <api_key>
```

### 3. Services

#### BatchProcessingService

```python
class BatchProcessingService:
    """Orchestrates batch file processing operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ocr_service = OCRService()
        self.export_service = ExportService(db)
        
    async def create_batch_job(
        self,
        files: List[UploadFile],
        tenant_id: int,
        user_id: int,
        api_client_id: str,
        export_destination_id: int,
        document_types: Optional[List[str]] = None,
        custom_fields: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> BatchProcessingJob:
        """Create a new batch processing job and enqueue files"""
        
    async def process_file_completion(
        self,
        file_id: int,
        extracted_data: Dict[str, Any],
        status: str,
        error_message: Optional[str] = None
    ):
        """Handle individual file completion and check if job is done"""
        
    async def check_job_completion(self, job_id: str):
        """Check if all files in a job are processed and trigger export"""
        
    async def get_job_status(
        self,
        job_id: str,
        tenant_id: int
    ) -> Dict[str, Any]:
        """Get detailed status of a batch job"""
```

#### ExportService

```python
class ExportService:
    """Handles CSV generation and export to destinations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cloud_storage_service = CloudStorageService(db)
        
    async def generate_and_export_results(
        self,
        job: BatchProcessingJob
    ) -> str:
        """Generate CSV from job results and export to destination"""
        
    def generate_csv(
        self,
        files: List[BatchFileProcessing],
        custom_fields: Optional[List[str]] = None
    ) -> bytes:
        """Generate CSV content from processed files"""
        
    async def upload_to_destination(
        self,
        csv_content: bytes,
        destination_config: ExportDestinationConfig,
        job_id: str
    ) -> str:
        """Upload CSV to configured destination and return URL"""
```

#### ExportDestinationService

```python
class ExportDestinationService:
    """Manages export destination configurations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService()
        
    def create_destination(
        self,
        tenant_id: int,
        name: str,
        destination_type: str,
        credentials: Dict[str, Any],
        config: Dict[str, Any],
        user_id: int
    ) -> ExportDestinationConfig:
        """Create new export destination with encrypted credentials"""
        
    def update_destination(
        self,
        destination_id: int,
        tenant_id: int,
        updates: Dict[str, Any]
    ) -> ExportDestinationConfig:
        """Update destination configuration"""
        
    def get_decrypted_credentials(
        self,
        destination_id: int,
        tenant_id: int
    ) -> Dict[str, Any]:
        """Retrieve and decrypt destination credentials"""
        
    async def test_connection(
        self,
        destination_id: int,
        tenant_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Test connection to export destination"""
```

### 4. UI Components

#### Settings Page - Export Destinations Tab

```typescript
// New tab in Settings.tsx
interface ExportDestination {
  id: number;
  name: string;
  destination_type: 's3' | 'azure' | 'gcs' | 'google_drive';
  is_active: boolean;
  is_default: boolean;
  last_test_success: boolean;
  last_test_at: string;
}

const ExportDestinationsTab = () => {
  const [destinations, setDestinations] = useState<ExportDestination[]>([]);
  const [selectedType, setSelectedType] = useState<string>('s3');
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Render destination type selector
  // Render credential input fields based on selected type
  // Handle create/update/delete operations
  // Test connection functionality
}
```

#### Credential Input Forms

Each destination type has specific credential fields:

**AWS S3**:
- Access Key ID
- Secret Access Key
- Region
- Bucket Name
- Path Prefix (optional)

**Azure Blob Storage**:
- Connection String OR (Account Name + Account Key)
- Container Name
- Path Prefix (optional)

**Google Cloud Storage**:
- Service Account JSON OR (Project ID + Credentials)
- Bucket Name
- Path Prefix (optional)

**Google Drive**:
- OAuth2 Authorization Button
- Folder ID
- Folder Path (display only)

## Data Models

### CSV Export Format

The generated CSV will have the following structure:

```csv
file_name,document_type,status,vendor,amount,currency,date,tax_amount,category,line_items,attachment_paths,error_message
invoice_001.pdf,invoice,completed,Acme Corp,1250.00,USD,2025-11-01,125.00,Services,"[{""description"":""Consulting"",""quantity"":10,""price"":125.00}]","s3://bucket/tenant_1/invoices/001.pdf",
receipt_002.jpg,expense,completed,Office Depot,45.99,USD,2025-11-02,3.68,Office Supplies,[],"s3://bucket/tenant_1/expenses/002.jpg",
statement_003.pdf,statement,failed,,,,,,,,"s3://bucket/tenant_1/statements/003.pdf","OCR extraction failed: Image quality too low"
```

### Extracted Data Schema

```json
{
  "vendor": "string",
  "amount": "number",
  "currency": "string",
  "date": "string (ISO 8601)",
  "tax_amount": "number",
  "tax_rate": "number",
  "category": "string",
  "payment_method": "string",
  "reference_number": "string",
  "line_items": [
    {
      "description": "string",
      "quantity": "number",
      "price": "number",
      "amount": "number"
    }
  ],
  "attachment_paths": "string (comma-separated)",
  "custom_fields": {}
}
```

## Error Handling

### File Processing Errors

1. **Invalid File Format**: Return 400 with specific error message
2. **File Too Large**: Return 413 with size limit information
3. **OCR Failure**: Retry up to 3 times, then mark as failed with error details
4. **Extraction Failure**: Mark file as failed but continue processing other files

### Export Errors

1. **Destination Unreachable**: Retry up to 5 times with exponential backoff
2. **Authentication Failure**: Mark job as failed, notify via webhook
3. **Quota Exceeded**: Mark job as failed with specific error
4. **Network Timeout**: Retry with increased timeout

### Webhook Notification Errors

1. **Webhook Unreachable**: Retry up to 3 times
2. **Invalid Response**: Log error but don't fail job
3. **Timeout**: Use 30-second timeout, log if exceeded

## Testing Strategy

### Unit Tests

1. **BatchProcessingService**:
   - Test job creation with various file combinations
   - Test progress tracking and completion detection
   - Test error handling for individual file failures

2. **ExportService**:
   - Test CSV generation with different field selections
   - Test upload to each destination type
   - Test error handling for upload failures

3. **ExportDestinationService**:
   - Test credential encryption/decryption
   - Test connection testing for each provider
   - Test fallback to environment variables

### Integration Tests

1. **End-to-End Batch Processing**:
   - Upload batch of mixed document types
   - Verify all files are processed
   - Verify CSV is generated and exported
   - Verify webhook notification is sent

2. **Multi-Tenant Isolation**:
   - Verify tenant A cannot access tenant B's jobs
   - Verify tenant-specific encryption keys are used
   - Verify export destinations are tenant-scoped

3. **Error Recovery**:
   - Test partial failure scenarios
   - Test retry logic for failed files
   - Test export retry on destination failure

### Performance Tests

1. **Large Batch Processing**:
   - Test with 50 files (maximum)
   - Measure end-to-end processing time
   - Verify no memory leaks

2. **Concurrent Jobs**:
   - Test multiple API clients with concurrent jobs
   - Verify rate limiting works correctly
   - Verify no resource contention

## Security Considerations

1. **Credential Storage**:
   - All export destination credentials encrypted using tenant-specific keys
   - Credentials never returned in API responses (masked)
   - Credentials stored in `encrypted_credentials` BLOB column

2. **API Key Validation**:
   - All endpoints require valid X-API-Key header
   - API keys validated against `APIClient` table
   - Rate limits enforced per API client

3. **Tenant Isolation**:
   - All database queries filtered by tenant_id
   - Export destinations scoped to tenant
   - Files stored in tenant-specific paths

4. **Audit Logging**:
   - All batch operations logged with user_id and timestamp
   - Export operations logged with destination details
   - Failed operations logged with error details

## Deployment Considerations

1. **Database Migrations**:
   - Add `batch_processing_jobs` table
   - Add `batch_file_processing` table
   - Add `export_destination_configs` table
   - Add indexes for performance

2. **Environment Variables**:
   - Fallback credentials for each destination type
   - Kafka configuration (reuse existing)
   - Webhook timeout configuration

3. **Monitoring**:
   - Track batch job completion rates
   - Monitor export success/failure rates
   - Alert on high failure rates
   - Track processing time metrics

4. **Scaling**:
   - OCR workers can be scaled independently
   - Batch completion monitor can run as separate service
   - Export service can be scaled horizontally
