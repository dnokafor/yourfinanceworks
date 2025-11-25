import sys
import os
import requests
import json

# Add parent directory to path to import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"

def login(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def get_settings(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/settings/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get settings failed: {response.text}")
        return None

def update_settings(token, settings):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{BASE_URL}/settings/", headers=headers, json=settings)
    return response

def main():
    # Assuming we have a user 'admin@example.com' with password 'password'
    # You might need to adjust this based on your local DB
    email = "admin@example.com"
    password = "password"
    
    print(f"Logging in as {email}...")
    token = login(email, password)
    if not token:
        return

    print("Getting current settings...")
    current_settings = get_settings(token)
    if not current_settings:
        return
    
    ai_enabled = current_settings.get("enable_ai_assistant", False)
    print(f"Current AI Assistant status: {ai_enabled}")

    # Try to enable AI Assistant (should fail if no license)
    print("\nAttempting to ENABLE AI Assistant...")
    response = update_settings(token, {"enable_ai_assistant": True})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 402:
        print("SUCCESS: License check blocked enabling.")
    elif response.status_code == 200:
        print("WARNING: AI Assistant enabled (maybe license is valid or check failed).")
    else:
        print("Unexpected response.")

    # Try to disable AI Assistant (should always succeed)
    print("\nAttempting to DISABLE AI Assistant...")
    response = update_settings(token, {"enable_ai_assistant": False})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("SUCCESS: AI Assistant disabled.")
    else:
        print("FAILURE: Could not disable AI Assistant.")

if __name__ == "__main__":
    main()
