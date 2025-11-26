#!/usr/bin/env python3
"""
Test ACC connector API endpoints to debug the React frontend issue
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from database import get_acc_folder_path, save_acc_folder_path

def test_api_endpoints():
    """Test the ACC connector API endpoints"""
    base_url = "http://localhost:5000/api"
    project_id = 1  # Test with project 1
    
    print("=== Testing ACC Connector API Endpoints ===\n")
    
    # Test 1: Get current folder configuration
    print("1. Testing GET /api/projects/{project_id}/acc-connector-folder")
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/acc-connector-folder")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Test 2: Set a valid folder path
    test_folder = r"C:\Users\RicoStrinati\DC\ACCDocs\School Infrastructure NSW"
    if os.path.exists(test_folder):
        print(f"2. Testing POST /api/projects/{project_id}/acc-connector-folder")
        print(f"   Setting folder to: {test_folder}")
        try:
            response = requests.post(
                f"{base_url}/projects/{project_id}/acc-connector-folder",
                json={"folder_path": test_folder}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 3: Try extracting files
        print(f"3. Testing POST /api/projects/{project_id}/acc-connector-extract")
        try:
            response = requests.post(f"{base_url}/projects/{project_id}/acc-connector-extract")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    else:
        print(f"2. Skipping extraction test - folder doesn't exist: {test_folder}")
        print()
    
    # Test 4: Get extracted files
    print(f"4. Testing GET /api/projects/{project_id}/acc-connector-files")
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/acc-connector-files?limit=5")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()

def check_existing_folders():
    """Check for existing ACC connector folders"""
    print("=== Checking for Existing ACC Folders ===\n")
    
    possible_folders = [
        r"C:\Users\RicoStrinati\DC\ACCDocs",
        r"C:\Users\RicoStrinati\Autodesk\ACC",
        r"C:\Users\RicoStrinati\Documents\Autodesk\ACC",
        r"C:\Users\RicoStrinati\DC\ACCDocs\School Infrastructure NSW",
        r"C:\Users\RicoStrinati\DC\ACCDocs\School Infrastructure NSW\Nowra East PS Upgrade [P240601]"
    ]
    
    for folder in possible_folders:
        if os.path.exists(folder):
            try:
                files = os.listdir(folder)
                print(f"✅ FOUND: {folder}")
                print(f"   - Contains {len(files)} items")
                if files:
                    print(f"   - Sample items: {files[:3]}")
                print()
            except Exception as e:
                print(f"⚠️  FOUND but can't read: {folder} ({e})")
                print()
        else:
            print(f"❌ Not found: {folder}")

if __name__ == "__main__":
    check_existing_folders()
    test_api_endpoints()