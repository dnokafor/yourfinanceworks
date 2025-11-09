# Implementation Plan

- [x] 1. Database schema and models
  - [x] 1.1 Create BatchProcessingJob model
    - Create SQLAlchemy model with all fields: job_id (UUID), tenant_id, user_id, api_client_id, document_types (JSON), total_files, export_destination_type, export_destination_config_id, custom_fields (JSON), status, processed_files, successful_files, failed_files, progress_percentage, export_file_url, export_file_key, export_completed_at, timestamps
    - Add relationship to BatchFileProcessing and ExportDestinationConfig
    - Add indexes on job_id, tenant_id, status, created_at
    - _Requirements: 1.1, 2.1, 5.1_
  
  - [x] 1.2 Create BatchFileProcessing model
    - Create SQLAlchemy model with fields: job_id (FK), original_filename, stored_filename, file_path, cloud_file_url, file_size, document_type, status, retry_count, error_message, extracted_data (JSON), kafka_topic, kafka_message_id, timestamps
    - Add relationship to BatchProcessingJob
    - Add indexes on job_id, status, document_type
    - _Requirements: 1.1, 2.1, 2.3_
  
  - [x] 1.3 Create ExportDestinationConfig model
    - Create SQLAlchemy model with fields: tenant_id, name, destination_type, is_active, is_default, encrypted_credentials (LargeBinary), config (JSON), last_test_at, last_test_success, last_test_error, timestamps, created_by
    - Add indexes on tenant_id, is_active
    - Add unique constraint on (tenant_id, name)
    - _Requirements: 3.1, 3A.8, 9.2_
  
  - [x] 1.4 Create Alembic migration script
    - Write migration to create all three tables with proper constraints
    - Add foreign key relationships
    - Add all indexes for query performance
    - Test migration up and down
    - _Requirements: 1.1, 2.1, 3A.8_

- [x] 2. Export destination management service
  - [x] 2.1 Implement ExportDestinationService class
    - Create service class with database session injection
    - Implement credential encryption using tenant-specific keys
    - Implement credential decryption with proper error handling
    - Add methods: create_destination, update_destination, get_destination, list_destinations, delete_destination, get_decrypted_credentials
    - _Requirements: 3A.8, 3B.1, 9.1_
  
  - [x] 2.2 Implement destination-specific credential schemas
    - Create Pydantic schemas for S3 credentials (access_key_id, secret_access_key, region, bucket_name, path_prefix)
    - Create Pydantic schemas for Azure credentials (connection_string OR account_name+account_key, container_name, path_prefix)
    - Create Pydantic schemas for GCS credentials (service_account_json OR project_id+credentials, bucket_name, path_prefix)
    - Create Pydantic schemas for Google Drive credentials (oauth_token, refresh_token, folder_id)
    - Add validation for required fields per destination type
    - _Requirements: 3A.4, 3A.5, 3A.6, 3A.7_
  
  - [x] 2.3 Implement connection testing for each destination type
    - Create test_s3_connection method that attempts to list bucket contents
    - Create test_azure_connection method that attempts to list container
    - Create test_gcs_connection method that attempts to list bucket
    - Create test_google_drive_connection method that attempts to access folder
    - Update last_test_at, last_test_success, last_test_error fields after each test
    - _Requirements: 3A.10, 3.6_
  
  - [x] 2.4 Implement environment variable fallback
    - Check for destination-specific env vars when credentials are not configured
    - For S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET
    - For Azure: AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER
    - For GCS: GOOGLE_APPLICATION_CREDENTIALS, GCS_BUCKET_NAME
    - Log when fallback credentials are used
    - _Requirements: 3.7, 3A.9_

- [x] 3. Export destination API endpoints
  - [x] 3.1 Create export destinations router
    - Create new FastAPI router at /api/v1/export-destinations
    - Add API key authentication dependency
    - Add tenant context middleware
    - _Requirements: 3B.1, 3B.2, 9.1_
  
  - [x] 3.2 Implement POST /api/v1/export-destinations endpoint
    - Accept destination name, type, credentials, and config
    - Validate API client has admin or write permissions
    - Encrypt credentials before storing
    - Return created destination with masked credentials
    - Log audit event for destination creation
    - _Requirements: 3A.1, 3B.1, 3B.2, 3B.3, 9.5_
  
  - [x] 3.3 Implement GET /api/v1/export-destinations endpoint
    - List all destinations for authenticated tenant
    - Return masked credentials (show only last 4 characters)
    - Include connection test status
    - Support pagination
    - _Requirements: 3B.1, 3B.4_
  
  - [x] 3.4 Implement PUT /api/v1/export-destinations/{id} endpoint
    - Allow updating individual credential fields without requiring all fields
    - Re-encrypt credentials after update
    - Validate API client has admin or write permissions
    - Return updated destination with masked credentials
    - _Requirements: 3B.1, 3B.5_
  
  - [x] 3.5 Implement POST /api/v1/export-destinations/{id}/test endpoint
    - Test connection to destination using stored credentials
    - Update last_test_at and last_test_success fields
    - Return test result with error details if failed
    - _Requirements: 3A.10, 3.6_
  
  - [x] 3.6 Implement DELETE /api/v1/export-destinations/{id} endpoint
    - Soft delete destination (set is_active=false)
    - Validate no active batch jobs are using this destination
    - Require admin permissions
    - Log audit event for deletion
    - _Requirements: 3B.1, 9.5_

- [x] 4. Export destinations UI in Settings
  - [x] 4.1 Create ExportDestinationsTab component
    - Add new tab to Settings page
    - Display list of configured destinations with status indicators
    - Show "Add Destination" button
    - Show edit/delete/test buttons for each destination
    - _Requirements: 3A.1, 3A.2_
  
  - [x] 4.2 Create destination type selector dropdown
    - Add dropdown with options: AWS S3, Azure Blob Storage, Google Cloud Storage, Google Drive
    - Update credential form fields when selection changes
    - _Requirements: 3A.2, 3A.3_
  
  - [x] 4.3 Create S3 credential input form
    - Add input fields: Access Key ID, Secret Access Key, Region, Bucket Name, Path Prefix
    - Add field validation
    - Show/hide password toggle for secret key
    - _Requirements: 3A.4_
  
  - [x] 4.4 Create Azure credential input form
    - Add radio button to choose between Connection String or Account Name+Key
    - Add input fields based on selection
    - Add Container Name and Path Prefix fields
    - Add field validation
    - _Requirements: 3A.5_
  
  - [x] 4.5 Create GCS credential input form
    - Add radio button to choose between Service Account JSON or Project ID+Credentials
    - Add file upload for service account JSON
    - Add Bucket Name and Path Prefix fields
    - Add field validation
    - _Requirements: 3A.6_
  
  - [x] 4.6 Create Google Drive credential input form
    - Add OAuth2 authorization button
    - Display authorization status
    - Add Folder ID input field
    - Show folder path after successful authorization
    - _Requirements: 3A.7_
  
  - [x] 4.7 Implement test connection functionality
    - Add "Test Connection" button for each destination
    - Show loading spinner during test
    - Display success/error message with details
    - Update UI to show last test timestamp and status
    - _Requirements: 3A.10_
  
  - [x] 4.8 Implement environment variable fallback notice
    - Display notice when no credentials are configured
    - Show which environment variables will be used
    - Add link to documentation
    - _Requirements: 3A.9_

- [x] 5. Batch processing service core
  - [x] 5.1 Create BatchProcessingService class
    - Initialize with database session, OCR service, and export service
    - Add method to generate unique job IDs (UUID)
    - Add method to determine document type from file extension/content
    - _Requirements: 1.1, 1.4, 2.1_
  
  - [x] 5.2 Implement create_batch_job method
    - Validate file count (max 50 files)
    - Validate file sizes (max 20MB per file)
    - Validate file types (PDF, PNG, JPG, CSV)
    - Validate export destination exists and is active
    - Create BatchProcessingJob record with status "pending"
    - Create BatchFileProcessing record for each file
    - Store files to tenant-specific storage
    - _Requirements: 1.1, 1.2, 1.3, 3.6_
  
  - [x] 5.3 Implement file enqueueing to Kafka
    - Determine appropriate Kafka topic based on document type (invoice_ocr, expense_ocr, bank_statements_ocr)
    - Publish message for each file with job_id, file_id, file_path, tenant_id
    - Update BatchFileProcessing with kafka_topic and kafka_message_id
    - Handle Kafka publish failures with retry logic
    - _Requirements: 2.1, 2.2_
  
  - [x] 5.4 Implement process_file_completion method
    - Accept file_id, extracted_data, status, error_message
    - Update BatchFileProcessing record with results
    - Update BatchProcessingJob progress counters (processed_files, successful_files, failed_files)
    - Calculate and update progress_percentage
    - Check if all files are processed and trigger export if complete
    - _Requirements: 2.3, 2.4, 5.3_
  
  - [x] 5.5 Implement retry logic for failed files
    - Check retry_count before retrying
    - Increment retry_count on each retry
    - Use exponential backoff (1s, 2s, 4s)
    - Mark as permanently failed after 3 retries
    - Record error message for each retry attempt
    - _Requirements: 7.1, 7.2_

- [x] 6. OCR worker integration
  - [x] 6.1 Update invoice OCR worker to handle batch jobs
    - Check if message contains batch job_id and file_id
    - Process file using existing OCR logic
    - Call BatchProcessingService.process_file_completion on success/failure
    - Include extracted data in completion callback
    - _Requirements: 2.1, 2.3_
  
  - [x] 6.2 Update expense OCR worker to handle batch jobs
    - Check if message contains batch job_id and file_id
    - Process file using existing OCR logic
    - Call BatchProcessingService.process_file_completion on success/failure
    - Include extracted data in completion callback
    - _Requirements: 2.1, 2.3_
  
  - [x] 6.3 Update bank statement OCR worker to handle batch jobs
    - Check if message contains batch job_id and file_id
    - Process file using existing OCR logic
    - Call BatchProcessingService.process_file_completion on success/failure
    - Include extracted transactions in completion callback
    - _Requirements: 2.1, 2.3_

- [x] 7. Export service implementation
  - [x] 7.1 Create ExportService class
    - Initialize with database session and cloud storage service
    - Add method to generate CSV filename with timestamp
    - _Requirements: 4.1, 4.2_
  
  - [x] 7.2 Implement generate_csv method
    - Query all BatchFileProcessing records for the job
    - Extract data from extracted_data JSON field
    - Build CSV rows with columns: file_name, document_type, status, vendor, amount, currency, date, tax_amount, category, line_items, attachment_paths, error_message
    - Handle comma-separated attachment paths
    - Serialize line_items as JSON string
    - Escape special characters per RFC 4180
    - Support custom field selection if specified in job
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 10.1, 10.2_
  
  - [x] 7.3 Implement upload_to_s3 method
    - Get decrypted S3 credentials from ExportDestinationConfig
    - Use boto3 to upload CSV to specified bucket and path
    - Generate presigned URL for download (24 hour expiry)
    - Return S3 URL
    - _Requirements: 3.2, 3.7_
  
  - [x] 7.4 Implement upload_to_azure method
    - Get decrypted Azure credentials from ExportDestinationConfig
    - Use azure-storage-blob to upload CSV to container
    - Generate SAS URL for download (24 hour expiry)
    - Return Azure Blob URL
    - _Requirements: 3.3, 3.7_
  
  - [x] 7.5 Implement upload_to_gcs method
    - Get decrypted GCS credentials from ExportDestinationConfig
    - Use google-cloud-storage to upload CSV to bucket
    - Generate signed URL for download (24 hour expiry)
    - Return GCS URL
    - _Requirements: 3.4, 3.7_
  
  - [x] 7.6 Implement upload_to_google_drive method
    - Get decrypted Google Drive OAuth tokens from ExportDestinationConfig
    - Use Google Drive API to upload CSV to specified folder
    - Set file permissions for sharing
    - Return Google Drive file URL
    - _Requirements: 3.5, 3.7_
  
  - [x] 7.7 Implement export retry logic
    - Retry upload up to 5 times on failure
    - Use exponential backoff (2s, 4s, 8s, 16s, 32s)
    - Log each retry attempt
    - Mark job as failed if all retries exhausted
    - _Requirements: 7.3, 7.4_
  
  - [x] 7.8 Implement generate_and_export_results method
    - Generate CSV from job files
    - Determine destination type from job configuration
    - Call appropriate upload method
    - Update BatchProcessingJob with export_file_url and export_completed_at
    - Update job status to "completed" or "partial_failure"
    - _Requirements: 2.5, 4.1_

- [x] 8. Batch completion monitoring
  - [x] 8.1 Create BatchCompletionMonitor service
    - Create background service that polls for completed jobs
    - Query BatchProcessingJob records where processed_files == total_files and status == "processing"
    - Trigger export for each completed job
    - Run every 30 seconds
    - _Requirements: 2.5, 5.3_
  
  - [x] 8.2 Implement webhook notification
    - Check if job has webhook_url configured
    - Send POST request to webhook_url with job status and export URL
    - Include job_id, status, total_files, successful_files, failed_files, export_file_url
    - Retry up to 3 times on failure
    - Use 30-second timeout
    - Log webhook delivery status
    - _Requirements: 5.5, 7.1, 7.2, 7.3_

- [x] 9. Batch upload API endpoint
  - [x] 9.1 Create batch processing router
    - Create new FastAPI router at /api/v1/batch-processing
    - Add API key authentication dependency
    - Add tenant context middleware
    - _Requirements: 1.1, 9.1, 9.2_
  
  - [x] 9.2 Implement POST /api/v1/batch-processing/upload endpoint
    - Accept multipart/form-data with up to 50 files
    - Accept document_types, export_destination_id, custom_fields, webhook_url parameters
    - Validate API key and extract tenant_id, user_id, api_client_id
    - Validate file count, sizes, and types
    - Validate export destination exists and belongs to tenant
    - Call BatchProcessingService.create_batch_job
    - Return job_id, status, total_files, estimated_completion_minutes, status_url
    - Log audit event
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.6, 9.5_
  
  - [x] 9.3 Implement GET /api/v1/batch-processing/jobs/{job_id} endpoint
    - Validate API key and tenant ownership of job
    - Query BatchProcessingJob and related BatchFileProcessing records
    - Return job status, progress, file details, export URL
    - Include estimated completion time based on average processing time
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 9.4 Implement GET /api/v1/batch-processing/jobs endpoint
    - List all jobs for authenticated API client
    - Support filtering by status
    - Support pagination (limit, offset)
    - Return job summaries without file details
    - _Requirements: 5.2, 5.4_

- [x] 10. Rate limiting and quotas
  - [x] 10.1 Implement per-API-client rate limiting
    - Check APIClient rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day
    - Track request counts in Redis or in-memory cache
    - Return HTTP 429 with Retry-After header when limit exceeded
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 10.2 Implement concurrent job limits
    - Check number of active jobs (status = "pending" or "processing") for API client
    - Enforce maximum of 5 concurrent jobs per client (configurable)
    - Return HTTP 429 if limit exceeded
    - _Requirements: 8.4_
  
  - [x] 10.3 Implement custom quota support
    - Check if APIClient has custom quotas configured
    - Apply custom limits instead of defaults
    - Log when custom quotas are applied
    - _Requirements: 8.5_

- [x] 11. Security and access control
  - [x] 11.1 Implement tenant isolation in all queries
    - Add tenant_id filter to all BatchProcessingJob queries
    - Add tenant_id filter to all ExportDestinationConfig queries
    - Validate job ownership before returning status
    - _Requirements: 9.1, 9.2_
  
  - [x] 11.2 Implement credential encryption
    - Use tenant-specific encryption keys from existing encryption service
    - Encrypt credentials before storing in encrypted_credentials column
    - Decrypt credentials only when needed for operations
    - Never return decrypted credentials in API responses
    - _Requirements: 3A.8, 9.3, 9.4_
  
  - [x] 11.3 Implement audit logging
    - Log all batch upload operations with user_id, timestamp, file_count
    - Log all export operations with destination type and success/failure
    - Log all destination configuration changes
    - Log all failed operations with error details
    - _Requirements: 9.5_

- [x] 12. Documentation and examples
  - [x] 12.1 Create API documentation
    - Document all batch processing endpoints with request/response examples
    - Document all export destination endpoints
    - Include authentication requirements
    - Include rate limit information
    - _Requirements: 1.1, 3.1, 5.1_
  
  - [x] 12.2 Create Python client example
    - Write example script showing batch upload
    - Write example script showing job status polling
    - Write example script showing destination configuration
    - Include error handling examples
    - _Requirements: 1.1, 5.1_
  
  - [x] 12.3 Create UI user guide
    - Document how to configure export destinations in Settings
    - Document how to test connections
    - Document environment variable fallback
    - Include screenshots
    - _Requirements: 3A.1, 3A.10, 3A.9_

- [x] 13. Testing and validation
  - [x] 13.1 Write unit tests for BatchProcessingService
    - Test job creation with various file combinations
    - Test progress tracking and completion detection
    - Test error handling for individual file failures
    - Test retry logic
    - _Requirements: 2.1, 2.3, 2.4, 7.1_
  
  - [x] 13.2 Write unit tests for ExportService
    - Test CSV generation with different field selections
    - Test upload to each destination type
    - Test error handling for upload failures
    - Test retry logic
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 7.3_
  
  - [x] 13.3 Write unit tests for ExportDestinationService
    - Test credential encryption/decryption
    - Test connection testing for each provider
    - Test fallback to environment variables
    - _Requirements: 3.7, 3A.8, 3A.10_
  
  - [ ]* 13.4 Write integration tests for end-to-end batch processing
    - Upload batch of mixed document types
    - Verify all files are processed
    - Verify CSV is generated and exported
    - Verify webhook notification is sent
    - _Requirements: 1.1, 2.1, 2.5, 4.1, 5.5_
  
  - [ ]* 13.5 Write integration tests for multi-tenant isolation
    - Verify tenant A cannot access tenant B's jobs
    - Verify tenant-specific encryption keys are used
    - Verify export destinations are tenant-scoped
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ]* 13.6 Write performance tests
    - Test with 50 files (maximum batch size)
    - Measure end-to-end processing time
    - Test multiple concurrent jobs
    - Verify rate limiting works correctly
    - _Requirements: 1.1, 8.1, 8.4_
