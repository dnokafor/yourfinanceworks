#!/usr/bin/env python3
"""
Simple Batch Upload Example

A minimal example showing how to upload files to the batch processing API.

Usage:
    python simple_batch_upload.py
"""

import requests
import os


def upload_files_simple():
    """Simple example of uploading files to batch processing API"""
    
    # API configuration
    API_URL = "http://localhost:8000"
    API_KEY = "your_api_key_here"  # Replace with your API key
    
    # Files to upload (replace with your file paths)
    file_paths = [
        "invoice_001.pdf",
        "receipt_002.jpg",
        "statement_003.pdf"
    ]
    
    # Document types for each file (optional - system will auto-detect if not specified)
    # Options: 'invoice', 'expense', 'statement'
    document_types = [
        "invoice",
        "expense",
        "statement"
    ]
    
    # Export destination ID (must exist in your system)
    export_destination_id = 1
    
    print("📤 Uploading files to batch processing API...")
    
    # Prepare files for upload
    files = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            files.append(
                ('files', (filename, open(file_path, 'rb'), 'application/octet-stream'))
            )
            print(f"  ✓ Added: {filename}")
        else:
            print(f"  ✗ File not found: {file_path}")
    
    if not files:
        print("❌ No valid files to upload")
        return
    
    # Prepare request data
    data = {
        'export_destination_id': export_destination_id,
        'document_types': ','.join(document_types)  # Optional: specify document types
    }
    
    # Make API request
    try:
        response = requests.post(
            f"{API_URL}/api/batch-processing/jobs",
            files=files,
            data=data,
            headers={'X-API-Key': API_KEY}
        )
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ Success!")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Total files: {result['total_files']}")
        print(f"\n💡 Check job status at: {API_URL}/api/batch-processing/jobs/{result['job_id']}")
        
    except requests.HTTPError as e:
        print(f"\n❌ Upload failed: {e}")
        if e.response is not None:
            try:
                error = e.response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Ensure all files are closed
        for _, file_tuple in files:
            try:
                file_tuple[1].close()
            except:
                pass


def check_job_status(job_id: str):
    """Check the status of a batch processing job"""
    
    API_URL = "http://localhost:8000"
    API_KEY = "your_api_key_here"
    
    print(f"🔍 Checking status of job: {job_id}")
    
    try:
        response = requests.get(
            f"{API_URL}/api/batch-processing/jobs/{job_id}",
            headers={'X-API-Key': API_KEY}
        )
        response.raise_for_status()
        
        status = response.json()
        progress = status.get('progress', {})
        
        print(f"\n📊 Job Status:")
        print(f"   Status: {status.get('status')}")
        print(f"   Progress: {progress.get('processed_files')}/{progress.get('total_files')} ({progress.get('progress_percentage'):.1f}%)")
        print(f"   Successful: {progress.get('successful_files')}")
        print(f"   Failed: {progress.get('failed_files')}")
        
        export_url = status.get('export', {}).get('export_file_url')
        if export_url:
            print(f"\n📥 Export URL: {export_url}")
        
    except requests.HTTPError as e:
        print(f"❌ Failed to get status: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    # Example 1: Upload files
    upload_files_simple()
    
    # Example 2: Check job status (uncomment and replace with actual job ID)
    # check_job_status("your-job-id-here")
