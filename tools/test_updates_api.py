"""Test the project updates API endpoint."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

def test_create_update():
    # Test creating a project update
    url = 'http://localhost:5000/api/projects/10/updates'
    
    payload = {
        'body': 'Test update from API test script'
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✓ SUCCESS: Update created!")
        else:
            print(f"\n✗ FAILED: Got status {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

if __name__ == '__main__':
    test_create_update()
