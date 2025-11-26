#!/usr/bin/env python3
"""
Test the backend API endpoints for health data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

def test_health_endpoints():
    """Test the health-related API endpoints."""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Testing Backend Health API Endpoints ===\n")
    
    # Test 1: Health files endpoint
    print("1. Testing GET /api/projects/<id>/health-files endpoint...")
    try:
        response = requests.get(f"{base_url}/api/projects/1/health-files")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running. Start with: python backend/app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Health summary endpoint
    print("\n2. Testing GET /api/projects/<id>/health-summary endpoint...")
    try:
        response = requests.get(f"{base_url}/api/projects/1/health-summary")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Summary keys: {list(data.keys())}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Health import endpoint (POST)
    print("\n3. Testing POST /api/projects/<id>/health-import endpoint...")
    try:
        response = requests.post(f"{base_url}/api/projects/1/health-import", 
                                 json={"folder_path": "C:\\TestFolder"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✅ All endpoint tests completed!")
    return True

if __name__ == "__main__":
    test_health_endpoints()