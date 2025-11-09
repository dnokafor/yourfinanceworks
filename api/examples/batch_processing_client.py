#!/usr/bin/env python3
"""
Batch File Processing API Client Example

This example demonstrates how to use the Batch File Processing API to:
1. Configure export destinations
2. Upload batches of files for processing
3. Monitor job progress
4. Handle errors and retries

Requirements:
    pip install requests

Usage:
    python batch_processing_client.py
"""

import os
import time
import json
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not installed")
    print("Install with: pip install requests")
    exit(1)


class BatchProcessingClient:
    """Client for interacting with the Batch File Processing API"""
    
    def __init__(self, base_url: str, auth_token: str):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (e.g., https://your-domain.com)
            auth_token: JWT token or API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}'
        })
    
    def create_export_destination(
        self,
        name: str,
        destination_type: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        is_default: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new export destination configuration
        
        Args:
            name: Friendly name for the destination
            destination_type: Type of destination (s3, azure, gcs, google_drive)
            credentials: Destination-specific credentials
            config: Optional configuration parameters
            is_default: Whether this is the default destination
            
        Returns:
            Created destination configuration
            
        Example:
            destination = client.create_export_destination(
                name="Production S3",
                destination_type="s3",
                credentials={
                    "access_key_id": "AKIA...",
                    "secret_access_key": "...",
                    "region": "us-east-1",
                    "bucket_name": "my-exports"
                },
                is_default=True
            )
        """
        url = f"{self.base_url}/api/v1/export-destinations"
        payload = {
            "name": name,
            "destination_type": destination_type,
            "credentials": credentials,
            "config": config or {},
            "is_default": is_default
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_export_destinations(
        self,
        active_only: bool = True,
        destination_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all export destinations
        
        Args:
            active_only: Only return active destinations
            destination_type: Filter by destination type
            
        Returns:
            List of export destinations
        """
        url = f"{self.base_url}/api/v1/export-destinations"
        params = {}
        if active_only:
            params['active_only'] = 'true'
        if destination_type:
            params['destination_type'] = destination_type
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()['destinations']
    
    def test_export_destination(self, destination_id: int) -> Dict[str, Any]:
        """
        Test connection to an export destination
        
        Args:
            destination_id: ID of the destination to test
            
        Returns:
            Test result with success status and error details
        """
        url = f"{self.base_url}/api/v1/export-destinations/{destination_id}/test"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    
    def upload_batch(
        self,
        files: List[str],
        export_destination_id: int,
        document_types: Optional[List[str]] = None,
        custom_fields: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a batch of files for processing
        
        Args:
            files: List of file paths to upload
            export_destination_id: ID of export destination
            document_types: Optional list of document types (invoice, expense, statement)
            custom_fields: Optional list of fields to include in export
            webhook_url: Optional webhook URL for completion notification
            
        Returns:
            Batch job information including job_id
            
        Example:
            job = client.upload_batch(
                files=['invoice1.pdf', 'invoice2.pdf', 'receipt.jpg'],
                export_destination_id=1,
                document_types=['invoice', 'expense'],
                webhook_url='https://example.com/webhook'
            )
            print(f"Job ID: {job['job_id']}")
        """
        url = f"{self.base_url}/api/v1/batch-processing/upload"
        
        # Prepare files for upload
        files_data = []
        for file_path in files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_name = os.path.basename(file_path)
            files_data.append(
                ('files', (file_name, open(file_path, 'rb'), 'application/octet-stream'))
            )
        
        # Prepare form data
        data = {
            'export_destination_id': export_destination_id
        }
        
        if document_types:
            data['document_types'] = ','.join(document_types)
        
        if custom_fields:
            data['custom_fields'] = ','.join(custom_fields)
        
        if webhook_url:
            data['webhook_url'] = webhook_url
        
        try:
            response = self.session.post(url, files=files_data, data=data)
            response.raise_for_status()
            return response.json()
        finally:
            # Close all file handles
            for _, file_tuple in files_data:
                file_tuple[1].close()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a batch job
        
        Args:
            job_id: UUID of the batch job
            
        Returns:
            Job status including progress and file details
        """
        url = f"{self.base_url}/api/v1/batch-processing/jobs/{job_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def list_jobs(
        self,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all batch jobs
        
        Args:
            status_filter: Filter by status (pending, processing, completed, failed, partial_failure)
            limit: Maximum number of jobs to return
            offset: Pagination offset
            
        Returns:
            List of jobs with pagination info
        """
        url = f"{self.base_url}/api/v1/batch-processing/jobs"
        params = {
            'limit': limit,
            'offset': offset
        }
        if status_filter:
            params['status_filter'] = status_filter
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 5,
        timeout: int = 600,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Wait for a batch job to complete
        
        Args:
            job_id: UUID of the batch job
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            callback: Optional callback function called on each status update
            
        Returns:
            Final job status
            
        Raises:
            TimeoutError: If job doesn't complete within timeout
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            status = self.get_job_status(job_id)
            
            if callback:
                callback(status)
            
            job_status = status['status']
            if job_status in ['completed', 'failed', 'partial_failure']:
                return status
            
            time.sleep(poll_interval)
    
    def download_export_file(self, export_url: str, output_path: str) -> None:
        """
        Download the exported CSV file
        
        Args:
            export_url: URL of the exported file
            output_path: Local path to save the file
        """
        response = requests.get(export_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


def print_progress(status: Dict[str, Any]) -> None:
    """Callback function to print job progress"""
    progress = status['progress']
    print(f"Progress: {progress['progress_percentage']:.1f}% "
          f"({progress['processed_files']}/{progress['total_files']} files) - "
          f"Status: {status['status']}")


def example_basic_usage():
    """Example: Basic batch upload and monitoring"""
    print("=" * 60)
    print("Example 1: Basic Batch Upload")
    print("=" * 60)
    
    # Initialize client
    client = BatchProcessingClient(
        base_url="http://localhost:8000",
        auth_token="your_jwt_token_here"
    )
    
    # Upload batch of files
    print("\n1. Uploading batch of files...")
    try:
        job = client.upload_batch(
            files=[
                'test_invoice1.pdf',
                'test_invoice2.pdf',
                'test_receipt.jpg'
            ],
            export_destination_id=1,
            document_types=['invoice', 'expense']
        )
        
        print(f"✓ Batch job created successfully!")
        print(f"  Job ID: {job['job_id']}")
        print(f"  Total files: {job['total_files']}")
        print(f"  Estimated completion: {job['estimated_completion_minutes']} minutes")
        
        # Monitor progress
        print("\n2. Monitoring job progress...")
        final_status = client.wait_for_completion(
            job_id=job['job_id'],
            poll_interval=5,
            callback=print_progress
        )
        
        # Print results
        print(f"\n3. Job completed with status: {final_status['status']}")
        print(f"  Successful files: {final_status['progress']['successful_files']}")
        print(f"  Failed files: {final_status['progress']['failed_files']}")
        
        if final_status['export']['export_file_url']:
            print(f"  Export URL: {final_status['export']['export_file_url']}")
            
            # Download export file
            print("\n4. Downloading export file...")
            client.download_export_file(
                export_url=final_status['export']['export_file_url'],
                output_path='batch_results.csv'
            )
            print("✓ Export file downloaded to batch_results.csv")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("  Please ensure test files exist in the current directory")
    except requests.exceptions.HTTPError as e:
        print(f"✗ API Error: {e}")
        print(f"  Response: {e.response.text}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def example_export_destination_setup():
    """Example: Setting up export destinations"""
    print("\n" + "=" * 60)
    print("Example 2: Export Destination Setup")
    print("=" * 60)
    
    client = BatchProcessingClient(
        base_url="http://localhost:8000",
        auth_token="your_jwt_token_here"
    )
    
    # Create S3 destination
    print("\n1. Creating S3 export destination...")
    try:
        destination = client.create_export_destination(
            name="Production S3 Bucket",
            destination_type="s3",
            credentials={
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "AKIA..."),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "..."),
                "region": "us-east-1",
                "bucket_name": "my-exports",
                "path_prefix": "batch-results/"
            },
            is_default=True
        )
        
        print(f"✓ Export destination created successfully!")
        print(f"  ID: {destination['id']}")
        print(f"  Name: {destination['name']}")
        print(f"  Type: {destination['destination_type']}")
        
        # Test connection
        print("\n2. Testing connection...")
        test_result = client.test_export_destination(destination['id'])
        
        if test_result['success']:
            print("✓ Connection test successful!")
        else:
            print(f"✗ Connection test failed: {test_result['error_details']}")
        
        # List all destinations
        print("\n3. Listing all export destinations...")
        destinations = client.list_export_destinations(active_only=True)
        
        print(f"Found {len(destinations)} active destination(s):")
        for dest in destinations:
            status_icon = "✓" if dest['last_test_success'] else "✗"
            print(f"  {status_icon} {dest['name']} ({dest['destination_type']}) - ID: {dest['id']}")
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ API Error: {e}")
        print(f"  Response: {e.response.text}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def example_error_handling():
    """Example: Error handling and retries"""
    print("\n" + "=" * 60)
    print("Example 3: Error Handling")
    print("=" * 60)
    
    client = BatchProcessingClient(
        base_url="http://localhost:8000",
        auth_token="your_jwt_token_here"
    )
    
    print("\n1. Attempting to upload with invalid parameters...")
    
    # Example: Too many files
    try:
        many_files = [f'file_{i}.pdf' for i in range(60)]  # More than 50
        job = client.upload_batch(
            files=many_files,
            export_destination_id=1
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"✓ Caught expected error: {e.response.json()['detail']}")
        else:
            print(f"✗ Unexpected error: {e}")
    
    # Example: Invalid destination
    print("\n2. Attempting to use non-existent destination...")
    try:
        job = client.upload_batch(
            files=['test.pdf'],
            export_destination_id=99999
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"✓ Caught expected error: {e.response.json()['detail']}")
        else:
            print(f"✗ Unexpected error: {e}")
    
    # Example: Rate limiting
    print("\n3. Handling rate limits...")
    try:
        for i in range(100):  # Attempt many requests
            client.list_jobs(limit=1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            retry_after = e.response.headers.get('Retry-After', 60)
            print(f"✓ Rate limit hit. Retry after {retry_after} seconds")
        else:
            print(f"✗ Unexpected error: {e}")


def example_list_and_filter_jobs():
    """Example: Listing and filtering jobs"""
    print("\n" + "=" * 60)
    print("Example 4: Listing and Filtering Jobs")
    print("=" * 60)
    
    client = BatchProcessingClient(
        base_url="http://localhost:8000",
        auth_token="your_jwt_token_here"
    )
    
    try:
        # List all jobs
        print("\n1. Listing all jobs...")
        result = client.list_jobs(limit=10)
        
        print(f"Total jobs: {result['total']}")
        print(f"Showing: {len(result['jobs'])} jobs")
        
        for job in result['jobs']:
            print(f"\n  Job ID: {job['job_id']}")
            print(f"  Status: {job['status']}")
            print(f"  Files: {job['total_files']} total, "
                  f"{job['successful_files']} successful, "
                  f"{job['failed_files']} failed")
            print(f"  Created: {job['created_at']}")
            if job['export_file_url']:
                print(f"  Export: {job['export_file_url']}")
        
        # Filter by status
        print("\n2. Filtering completed jobs...")
        completed = client.list_jobs(status_filter='completed', limit=5)
        print(f"Found {len(completed['jobs'])} completed job(s)")
        
        # Filter by status
        print("\n3. Filtering failed jobs...")
        failed = client.list_jobs(status_filter='failed', limit=5)
        print(f"Found {len(failed['jobs'])} failed job(s)")
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ API Error: {e}")
        print(f"  Response: {e.response.text}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Batch File Processing API - Python Client Examples")
    print("=" * 60)
    
    print("\nNote: Update the auth_token and file paths before running")
    print("      Set AWS credentials in environment variables for Example 2")
    
    # Uncomment the examples you want to run:
    
    # example_basic_usage()
    # example_export_destination_setup()
    # example_error_handling()
    # example_list_and_filter_jobs()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
