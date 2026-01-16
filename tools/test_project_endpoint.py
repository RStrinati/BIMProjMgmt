#!/usr/bin/env python3
"""
Quick test script to verify the new GET /api/projects/<id> endpoint works.
Usage: python test_project_endpoint.py [project_id] [base_url]
"""
import sys
import os
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Defaults
PROJECT_ID = 1
BASE_URL = "http://localhost:5000"


def test_project_endpoint():
    """Test the GET /api/projects/<id> endpoint"""
    project_id = int(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ID
    base_url = sys.argv[2] if len(sys.argv) > 2 else BASE_URL
    
    url = f"{base_url}/api/projects/{project_id}"
    
    print(f"Testing: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Project loaded")
            print(f"Project Name: {data.get('project_name', 'N/A')}")
            print(f"Status: {data.get('status', 'N/A')}")
            print(f"Priority: {data.get('priority_label', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"❌ NOT FOUND - Project {project_id} does not exist")
            return False
        else:
            print(f"❌ ERROR - Status {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False


if __name__ == "__main__":
    success = test_project_endpoint()
    sys.exit(0 if success else 1)
