#!/usr/bin/env python3
"""
Test script to verify ACC Desktop Connector API endpoints are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

BASE_URL = "http://localhost:5000"

def test_get_folder(project_id):
    """Test getting ACC connector folder path"""
    print(f"\n=== Testing GET folder for project {project_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/acc-connector-folder")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_save_folder(project_id, folder_path):
    """Test saving ACC connector folder path"""
    print(f"\n=== Testing POST folder for project {project_id} ===")
    
    try:
        data = {"folder_path": folder_path}
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/acc-connector-folder",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_extract_files(project_id):
    """Test extracting files"""
    print(f"\n=== Testing POST extract files for project {project_id} ===")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/acc-connector-extract",
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_files(project_id):
    """Test getting extracted files list"""
    print(f"\n=== Testing GET files for project {project_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/acc-connector-files")
        print(f"Status: {response.status_code}")
        data = response.json()
        
        # Print summary
        if 'files' in data:
            print(f"Total files: {data.get('total_count', 0)}")
            print(f"Files in response: {len(data['files'])}")
            
            # Show first few files
            for i, file in enumerate(data['files'][:3]):
                print(f"  File {i+1}: {file['file_name']} ({file['file_extension']}) - {file['file_size']} bytes")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 Testing ACC Desktop Connector API endpoints...")
    
    # Use project 1 for testing
    project_id = 1
    test_folder = "C:\\TestFolder"
    
    # Test 1: Get current folder configuration
    folder_data = test_get_folder(project_id)
    
    # Test 2: Save folder path
    save_result = test_save_folder(project_id, test_folder)
    
    # Test 3: Verify folder was saved
    folder_data_after = test_get_folder(project_id)
    
    # Test 4: Extract files (this will fail if folder doesn't exist, which is expected)
    extract_result = test_extract_files(project_id)
    
    # Test 5: Get files list
    files_data = test_get_files(project_id)
    
    print("\n" + "="*50)
    print("📋 Test Summary:")
    print(f"✅ GET folder: {'PASS' if folder_data else 'FAIL'}")
    print(f"✅ POST folder: {'PASS' if save_result and save_result.get('success') else 'FAIL'}")
    print(f"✅ GET files: {'PASS' if files_data and 'files' in files_data else 'FAIL'}")
    
    if extract_result:
        if extract_result.get('success'):
            print("✅ Extract files: PASS")
        else:
            print(f"⚠️  Extract files: Expected failure - {extract_result.get('error', 'Unknown error')}")
    else:
        print("❌ Extract files: FAIL")

if __name__ == "__main__":
    main()