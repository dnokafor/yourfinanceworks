# Requirements Document

## Introduction

This feature enables external systems and users to batch upload files (invoices, expenses, bank statements) via API key authentication, process them asynchronously, and export the extracted results to various destinations including CSV files on local storage, Google Drive, AWS S3, Azure Blob Storage, and Google Cloud Storage. The system supports comma-separated attachment paths for multi-file scenarios.

## Glossary

- **Batch Processing System**: The system component that handles multiple file uploads and processes them asynchronously
- **Export Destination**: The target location where processed results are written (local folder, cloud storage)
- **API Client**: An external system or user authenticated via API key
- **Processing Job**: A unit of work representing one batch upload request with multiple files
- **Result Manifest**: A CSV file containing extracted data from processed documents
- **Attachment Path**: File system or cloud storage URL pointing to uploaded files
- **Export Destination Configuration**: Tenant-specific settings defining cloud storage credentials and paths for result exports
- **Settings Page**: Web UI interface for tenant administrators to manage system configuration

## Requirements

### Requirement 1: API Key Authenticated Batch Upload

**User Story:** As an external system integrator, I want to upload multiple files in a single API request using my API key, so that I can efficiently process documents without manual intervention.

#### Acceptance Criteria

1. WHEN THE API Client submits a POST request to the batch upload endpoint with valid X-API-Key header, THE Batch Processing System SHALL accept up to 50 files per request
2. WHEN THE API Client includes files for invoices, expenses, or statements, THE Batch Processing System SHALL validate each file type and size (maximum 20MB per file)
3. IF THE API Client provides invalid authentication credentials, THEN THE Batch Processing System SHALL return HTTP 401 with error details
4. WHEN THE Batch Processing System receives valid files, THE Batch Processing System SHALL create a Processing Job with unique job ID and return it immediately
5. THE Batch Processing System SHALL support PDF, PNG, JPG, and CSV file formats for document uploads

### Requirement 2: Asynchronous Document Processing

**User Story:** As an API client, I want my uploaded files to be processed asynchronously, so that I don't have to wait for long-running OCR operations to complete.

#### Acceptance Criteria

1. WHEN THE Batch Processing System creates a Processing Job, THE Batch Processing System SHALL enqueue each file for OCR processing via the existing Kafka infrastructure
2. WHILE THE Processing Job is active, THE Batch Processing System SHALL update job status to reflect progress (pending, processing, completed, failed)
3. WHEN A file completes OCR processing, THE Batch Processing System SHALL extract structured data (vendor, amount, date, line items, etc.)
4. IF A file processing fails, THEN THE Batch Processing System SHALL record the error message and continue processing remaining files
5. WHEN ALL files in a Processing Job complete, THE Batch Processing System SHALL transition job status to "completed" or "partial_failure"

### Requirement 3: Multi-Destination Export Configuration

**User Story:** As an API client, I want to specify where my processed results should be exported, so that I can integrate with my existing data pipelines.

#### Acceptance Criteria

1. WHEN THE API Client creates a batch upload request, THE API Client SHALL specify export destination type (s3, azure, gcs, google_drive)
2. WHERE THE export destination is AWS S3, THE Batch Processing System SHALL upload CSV results using configured S3 credentials and bucket
3. WHERE THE export destination is Azure Blob Storage, THE Batch Processing System SHALL upload CSV results using configured Azure credentials and container
4. WHERE THE export destination is Google Cloud Storage, THE Batch Processing System SHALL upload CSV results using configured GCS credentials and bucket
5. WHERE THE export destination is Google Drive, THE Batch Processing System SHALL upload CSV results using OAuth2 credentials and folder ID
6. THE Batch Processing System SHALL validate export destination configuration before accepting the batch upload request
7. IF NO destination-specific credentials are configured, THEN THE Batch Processing System SHALL use environment variables as fallback credentials

### Requirement 3A: Export Destination Management UI

**User Story:** As a tenant administrator, I want to configure export destinations through a settings interface, so that I can manage credentials securely without code changes.

#### Acceptance Criteria

1. THE Batch Processing System SHALL provide a "Export Destinations" tab in the Settings page
2. THE Export Destinations tab SHALL display a dropdown selector with options: AWS S3, Azure Blob Storage, Google Cloud Storage, Google Drive
3. WHEN A user selects a destination type, THE Batch Processing System SHALL display credential input fields specific to that provider
4. WHERE AWS S3 is selected, THE Batch Processing System SHALL request: Access Key ID, Secret Access Key, Region, Bucket Name, and optional Path Prefix
5. WHERE Azure Blob Storage is selected, THE Batch Processing System SHALL request: Connection String or (Account Name + Account Key), Container Name, and optional Path Prefix
6. WHERE Google Cloud Storage is selected, THE Batch Processing System SHALL request: Service Account JSON or Project ID + Credentials, Bucket Name, and optional Path Prefix
7. WHERE Google Drive is selected, THE Batch Processing System SHALL provide OAuth2 authorization flow and request Folder ID
8. THE Batch Processing System SHALL encrypt stored credentials using tenant-specific encryption keys
9. WHEN NO credentials are configured for a destination, THE Batch Processing System SHALL display a notice that environment variables will be used as fallback
10. THE Batch Processing System SHALL allow testing the destination connection before saving configuration

### Requirement 3B: API-Based Destination Management

**User Story:** As an API client, I want to configure export destinations programmatically via API, so that I can automate deployment and configuration.

#### Acceptance Criteria

1. THE Batch Processing System SHALL provide REST endpoints for creating, updating, listing, and deleting export destination configurations
2. WHEN THE API Client calls the destination configuration endpoint with valid X-API-Key header, THE Batch Processing System SHALL authenticate and authorize the request
3. THE Batch Processing System SHALL validate that the API Client has admin or write permissions before allowing destination configuration changes
4. THE Batch Processing System SHALL return masked credentials (showing only last 4 characters) when listing destinations
5. THE Batch Processing System SHALL support updating individual credential fields without requiring all fields to be resent

### Requirement 4: CSV Result Generation

**User Story:** As an API client, I want processed document data exported as CSV files, so that I can easily import results into spreadsheets and databases.

#### Acceptance Criteria

1. WHEN THE Processing Job completes, THE Batch Processing System SHALL generate a Result Manifest in CSV format
2. THE Result Manifest SHALL include columns for: file_name, document_type, status, vendor, amount, currency, date, tax_amount, category, line_items, attachment_paths, error_message
3. WHERE A document has multiple attachments, THE Batch Processing System SHALL list attachment paths separated by commas in the attachment_paths column
4. THE Batch Processing System SHALL escape special characters in CSV fields according to RFC 4180 standard
5. WHEN LINE items exist, THE Batch Processing System SHALL serialize them as JSON string within the line_items CSV column

### Requirement 5: Job Status Monitoring

**User Story:** As an API client, I want to check the status of my batch processing jobs, so that I know when results are ready for download.

#### Acceptance Criteria

1. WHEN THE API Client requests job status with valid job ID, THE Batch Processing System SHALL return current status, progress percentage, and file-level details
2. THE Batch Processing System SHALL provide endpoints to list all jobs for the authenticated API Client
3. WHEN THE Processing Job completes, THE Batch Processing System SHALL include export destination URL in the status response
4. THE Batch Processing System SHALL retain job records for 30 days before automatic cleanup
5. WHERE THE API Client has webhook URL configured, THE Batch Processing System SHALL send webhook notification when job status changes to completed or failed

### Requirement 6: Attachment Path Management

**User Story:** As an API client, I want to reference multiple attachment files for a single document, so that I can link related files together.

#### Acceptance Criteria

1. WHEN THE API Client uploads files, THE Batch Processing System SHALL store each file with a unique identifier
2. THE Batch Processing System SHALL support both local file paths and cloud storage URLs as attachment paths
3. WHEN GENERATING the Result Manifest, THE Batch Processing System SHALL include comma-separated attachment paths for each processed document
4. THE Batch Processing System SHALL validate that attachment paths are accessible before including them in results
5. WHERE CLOUD storage is enabled, THE Batch Processing System SHALL prefer cloud URLs over local paths in the Result Manifest

### Requirement 7: Error Handling and Retry Logic

**User Story:** As an API client, I want robust error handling for failed file processing, so that transient failures don't cause data loss.

#### Acceptance Criteria

1. IF A file fails OCR processing, THEN THE Batch Processing System SHALL retry up to 3 times with exponential backoff
2. WHEN A file exceeds retry limit, THE Batch Processing System SHALL mark it as failed and record the error message
3. IF EXPORT destination is unreachable, THEN THE Batch Processing System SHALL retry export operation up to 5 times
4. THE Batch Processing System SHALL log all errors with sufficient context for debugging
5. WHEN PARTIAL failures occur, THE Batch Processing System SHALL still generate Result Manifest with error details for failed files

### Requirement 8: Rate Limiting and Quotas

**User Story:** As a system administrator, I want to enforce rate limits on batch processing, so that no single API client can overwhelm the system.

#### Acceptance Criteria

1. THE Batch Processing System SHALL enforce per-API-client rate limits configured in the API Client record
2. WHEN AN API Client exceeds rate limits, THE Batch Processing System SHALL return HTTP 429 with Retry-After header
3. THE Batch Processing System SHALL track daily, hourly, and per-minute request counts per API Client
4. THE Batch Processing System SHALL enforce maximum concurrent processing jobs per API Client (default 5)
5. WHERE AN API Client has custom quotas configured, THE Batch Processing System SHALL apply those limits instead of defaults

### Requirement 9: Security and Access Control

**User Story:** As a security administrator, I want batch processing to respect tenant isolation and permissions, so that data remains secure.

#### Acceptance Criteria

1. THE Batch Processing System SHALL process all files within the authenticated API Client's tenant context
2. THE Batch Processing System SHALL validate that export destinations are accessible only to the owning tenant
3. WHEN WRITING to cloud storage, THE Batch Processing System SHALL use tenant-specific credentials or paths
4. THE Batch Processing System SHALL encrypt sensitive data in Result Manifests when tenant encryption is enabled
5. THE Batch Processing System SHALL audit all batch upload and export operations with user ID, timestamp, and file count

### Requirement 10: Export Format Customization

**User Story:** As an API client, I want to customize which fields are included in my CSV exports, so that I only receive relevant data.

#### Acceptance Criteria

1. WHEN THE API Client creates a batch upload request, THE API Client SHALL optionally specify a list of fields to include in the Result Manifest
2. WHERE NO field list is provided, THE Batch Processing System SHALL include all available fields in the Result Manifest
3. THE Batch Processing System SHALL support field aliases to rename columns in the Result Manifest
4. THE Batch Processing System SHALL validate that requested fields exist for the document type
5. WHERE CUSTOM fields are defined on documents, THE Batch Processing System SHALL include them in the Result Manifest when requested
