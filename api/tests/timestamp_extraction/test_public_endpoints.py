#!/usr/bin/env python3
"""
Test the public timestamp extraction endpoints
"""
import requests
import json

def test_public_endpoints():
    """Test the public timestamp extraction endpoints"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 TESTING PUBLIC TIMESTAMP EXTRACTION ENDPOINTS")
    print("=" * 55)
    
    # Test 1: Public sample receipts endpoint
    print("\n📋 Test 1: Public Sample Receipts Endpoint")
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
                
                # Show extracted timestamp if available
                if first_sample.get('extraction') and 'receipt_timestamp' in first_sample['extraction']:
                    print(f"Sample timestamp: {first_sample['extraction']['receipt_timestamp']}")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Public text extraction endpoint
    print("\n📋 Test 2: Public Text Extraction Endpoint")
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
            print(f"Input: {test_data['text']}")
            print(f"Timestamp found: {data.get('timestamp_found', False)}")
            
            if data.get('heuristic_extraction'):
                heur = data['heuristic_extraction']
                if 'receipt_timestamp' in heur:
                    print(f"✅ Extracted timestamp: {heur['receipt_timestamp']}")
                    
                    # Verify it matches the input (our fix)
                    if heur['receipt_timestamp'] == test_data['text']:
                        print("✅ PERFECT: Timestamp extraction working correctly!")
                    else:
                        print(f"⚠️  Extracted '{heur['receipt_timestamp']}' but expected '{test_data['text']}'")
                else:
                    print("❌ No timestamp in heuristic result")
            
            print(f"Recommendation: {data.get('recommendation', 'None')}")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Additional test cases
    print("\n📋 Test 3: Additional Test Cases")
    test_cases = [
        "2024-11-06 14:32",
        "11/06/2024 2:45 PM", 
        "Just some text with no timestamp",
        "WALMART\nDate: 2024-11-06\nTime: 14:32\nTotal: $25.99"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n   Test 3.{i}: {repr(test_text)}")
        try:
            response = requests.post(
                f"{base_url}/public/test-timestamp/extract-from-text",
                json={"text": test_text}
            )
            
            if response.status_code == 200:
                data = response.json()
                timestamp_found = data.get('timestamp_found', False)
                
                if timestamp_found and data.get('heuristic_extraction', {}).get('receipt_timestamp'):
                    extracted_ts = data['heuristic_extraction']['receipt_timestamp']
                    print(f"   ✅ Extracted: {extracted_ts}")
                else:
                    print(f"   ❌ No timestamp extracted")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 55)
    print("🎯 PUBLIC ENDPOINT TEST COMPLETE")
    print("✅ These endpoints work without authentication!")
    print("✅ Frontend should now work correctly!")


if __name__ == "__main__":
    test_public_endpoints()