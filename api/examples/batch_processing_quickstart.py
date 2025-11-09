#!/usr/bin/env python3
"""
Batch File Processing - Quick Start Example

A simple example showing the most common use case:
1. Upload files
2. Wait for processing
3. Download results

Requirements:
    pip install requests

Usage:
    python batch_processing_quickstart.py
"""

import requests
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with your JWT token
EXPORT_DESTINATION_ID = 1  # Replace with your destination ID

# Files to process
FILES_TO_PROCESS = [
    "invoice1.pdf",
    "invoice2.pdf",
    "receipt.jpg"
]


def upload_batch(files, destination_id):
    """Upload files for batch processing"""
    url = f"{BASE_URL}/api/v1/batch-processing/upload"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    # Prepare files
    files_data = []
    for file_path in files:
        try:
            files_data.append(
                ('files', (file_path, open(file_path, 'rb')))
            )
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return None
    
    # Upload
    data = {"export_destination_id": destination_id}
    
    try:
        response = requests.post(url, headers=headers, files=files_data, data=data)
        response.raise_for_status()
        return response.json()
    finally:
        # Close file handles
        for _, file_tuple in files_data:
            file_tuple[1].close()


def get_job_status(job_id):
    """Get job status"""
    url = f"{BASE_URL}/api/v1/batch-processing/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def wait_for_completion(job_id, timeout=600):
    """Wait for job to complete"""
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            print(f"Timeout: Job did not complete in {timeout} seconds")
            return None
        
        status = get_job_status(job_id)
        progress = status['progress']['progress_percentage']
        
        print(f"Progress: {progress:.1f}% - Status: {status['status']}")
        
        if status['status'] in ['completed', 'failed', 'partial_failure']:
            return status
        
        time.sleep(5)


def download_results(export_url, output_file):
    """Download export file"""
    response = requests.get(export_url, stream=True)
    response.raise_for_status()
    
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    """Main execution"""
    print("Batch File Processing - Quick Start")
    print("=" * 50)
    
    # Step 1: Upload files
    print("\n1. Uploading files...")
    job = upload_batch(FILES_TO_PROCESS, EXPORT_DESTINATION_ID)
    
    if not job:
        print("Failed to upload files")
        sys.exit(1)
    
    print(f"✓ Job created: {job['job_id']}")
    print(f"  Total files: {job['total_files']}")
    print(f"  Estimated time: {job['estimated_completion_minutes']} minutes")
    
    # Step 2: Wait for completion
    print("\n2. Waiting for processing to complete...")
    final_status = wait_for_completion(job['job_id'])
    
    if not final_status:
        print("Job did not complete")
        sys.exit(1)
    
    # Step 3: Check results
    print(f"\n3. Processing complete!")
    print(f"  Status: {final_status['status']}")
    print(f"  Successful: {final_status['progress']['successful_files']}")
    print(f"  Failed: {final_status['progress']['failed_files']}")
    
    # Step 4: Download results
    if final_status['export']['export_file_url']:
        print("\n4. Downloading results...")
        download_results(
            final_status['export']['export_file_url'],
            'batch_results.csv'
        )
        print("✓ Results saved to: batch_results.csv")
    else:
        print("\n4. No export file available")
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\nAPI Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
