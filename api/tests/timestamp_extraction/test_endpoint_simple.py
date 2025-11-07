#!/usr/bin/env python3
"""
Simple test to verify the test-timestamp endpoints are working
"""
import requests
import json

def test_endpoints():
    """Test the timestamp extraction endpoints"""
    
    base_url = "http://localhost:8000/api/v1"  # Adjust if different
    
    print("🧪 TESTING TIMESTAMP EXTRACTION ENDPOINTS")
    print("=" * 50)
    
    # Test 1: Sample receipts endpoint
    print("\n📋 Test 1: Sample Receipts Endpoint")
    try:
        response = requests.get(f"{base_url}/public/test-timestamp/sample-receipts")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('samples', []))} samples")
            print(f"Response keys: {list(data.keys())}")
            
            if 'samples' in data and len(data['samples']) > 0:
                first_sample = data['samples'][0]
                print(f"First sample: {first_sample.get('name', 'Unknown')}")
                print(f"Timestamp extracted: {first_sample.get('timestamp_extracted', False)}")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Text extraction endpoint
    print("\n📋 Test 2: Text Extraction Endpoint")
    try:
        test_data = {"text": "09/13/25 18:36:08"}
        response = requests.post(
            f"{base_url}/public/test-timestamp/extract-from-text",
            json=test_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Timestamp found: {data.get('timestamp_found', False)}")
            
            if data.get('heuristic_extraction'):
                heur = data['heuristic_extraction']
                if 'receipt_timestamp' in heur:
                    print(f"Extracted timestamp: {heur['receipt_timestamp']}")
                else:
                    print("No timestamp in heuristic result")
            
            print(f"Recommendation: {data.get('recommendation', 'None')}")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Analytics preview endpoint
    print("\n📋 Test 3: Analytics Preview Endpoint")
    try:
        response = requests.get(f"{base_url}/test-timestamp/analytics-preview")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Response keys: {list(data.keys())}")
            
            if 'preview' in data:
                preview = data['preview']
                if 'extraction_stats' in preview:
                    stats = preview['extraction_stats']
                    print(f"Sample extraction rate: {stats.get('extraction_success_rate', 0)}%")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ENDPOINT TEST COMPLETE")
    print("If all tests passed, the frontend should work correctly!")


if __name__ == "__main__":
    test_endpoints()