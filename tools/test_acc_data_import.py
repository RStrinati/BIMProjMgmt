#!/usr/bin/env python3
"""
Test script to verify ACC Data Import tab functionality.
Tests backend endpoints and identifies missing API functions.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_acc_data_import_endpoints():
    """Test all ACC Data Import backend endpoints"""
    print("🧪 Testing ACC Data Import Backend Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api"
    test_project_id = 1  # Use a known project ID
    
    # Test 1: Get ACC Import Logs (exists)
    print("\n1️⃣ Testing GET /api/projects/{project_id}/acc-data-import-logs")
    try:
        response = requests.get(f"{base_url}/projects/{test_project_id}/acc-data-import-logs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logs = result.get('logs', [])
            print(f"   ✅ SUCCESS: Found {len(logs)} import logs")
            if logs:
                print(f"   📊 Latest: {logs[0].get('folder_name', 'N/A')} ({logs[0].get('import_date', 'N/A')})")
        else:
            result = response.json()
            print(f"   ❌ ERROR: {result.get('error', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend not running! Start with: python run_enhanced_ui.py")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 2: Import ACC Data (exists)
    print("\n2️⃣ Testing POST /api/projects/{project_id}/acc-data-import")
    try:
        test_data = {"folder_path": "C:/temp/test_acc"}
        response = requests.post(f"{base_url}/projects/{test_project_id}/acc-data-import", json=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS: {result.get('message', 'Import completed')}")
        elif response.status_code == 400:
            result = response.json()
            print(f"   ℹ️  INFO: {result.get('error', 'Bad request')} (expected for test path)")
        else:
            result = response.json()
            print(f"   ❌ ERROR: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: Get ACC Bookmarks (does NOT exist - causing React crash)
    print("\n3️⃣ Testing GET /api/projects/{project_id}/acc-bookmarks")
    try:
        response = requests.get(f"{base_url}/projects/{test_project_id}/acc-bookmarks")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS: Found bookmarks")
        elif response.status_code == 404:
            print(f"   🚫 NOT FOUND: Bookmarks API doesn't exist (causing React crash)")
        else:
            print(f"   ❌ ERROR: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 4: Add ACC Bookmark (does NOT exist - causing React crash)
    print("\n4️⃣ Testing POST /api/projects/{project_id}/acc-bookmarks")
    try:
        test_data = {"bookmark_name": "Test", "file_path": "C:/test", "import_type": "zip"}
        response = requests.post(f"{base_url}/projects/{test_project_id}/acc-bookmarks", json=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Bookmark added")
        elif response.status_code == 404:
            print(f"   🚫 NOT FOUND: Bookmarks API doesn't exist (causing React crash)")
        else:
            print(f"   ❌ ERROR: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    return True

def analyze_tkinter_vs_react():
    """Analyze differences between Tkinter and React implementations"""
    print("\n🔄 Workflow Analysis: Tkinter vs React ACC Import")
    print("=" * 60)
    
    print("\n🖥️  TKINTER IMPLEMENTATION (WORKING):")
    print("   File: ui/tab_data_imports.py")
    print("   1. Project dropdown selection")
    print("   2. ACC CSV Folder/ZIP input field")
    print("   3. Browse button → browse_acc_folder() → filedialog")
    print("   4. Import ACC CSVs button → import_acc_csv() → run_acc_import()")
    print("   5. Import logs display in Listbox widget")
    print("   6. No bookmarks functionality")
    
    print("\n🌐 REACT IMPLEMENTATION (BROKEN):")
    print("   File: frontend/src/components/dataImports/ACCDataImportPanel.tsx")
    print("   1. ✅ Project selection (from URL/props)")
    print("   2. ✅ File path input field")
    print("   3. ✅ Browse button → fileBrowserApi.selectFile()")
    print("   4. ✅ Import Data button → accDataImportApi.importData()")
    print("   5. ✅ Import logs display in Table")
    print("   6. ❌ BROKEN: Bookmarks functionality calls non-existent APIs")
    
    print("\n🚫 ROOT CAUSE OF BLANK PAGE:")
    print("   • React component calls accDataImportApi.getBookmarks()")
    print("   • Backend doesn't have /api/projects/{id}/acc-bookmarks endpoint")
    print("   • API call fails → useQuery fails → component crashes → blank page")
    
    print("\n✅ SOLUTION:")
    print("   • Remove bookmarks functionality from React component")
    print("   • Use simplified component that matches Tkinter workflow")
    print("   • Keep: Browse → Import → Show Logs")
    print("   • Remove: Bookmarks APIs and UI")

def main():
    """Main test function"""
    print("🚀 ACC Data Import Integration Test")
    print("=" * 50)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test backend endpoints
    if test_acc_data_import_endpoints():
        print("\n✅ Backend endpoints tested")
    
    # Analyze workflow differences
    analyze_tkinter_vs_react()
    
    print("\n🎯 NEXT STEPS:")
    print("=" * 50)
    print("1. ✅ COMPLETED: Created simplified React component without bookmarks")
    print("2. ✅ COMPLETED: Fixed TypeScript types to match backend response")
    print("3. ✅ COMPLETED: Removed bookmarks API calls from frontend")
    print("4. 🔄 IN PROGRESS: Replace broken component with fixed version")
    print("5. 🧪 TO TEST: Start frontend and navigate to ACC Data Import tab")
    
    print("\n🧪 MANUAL TEST INSTRUCTIONS:")
    print("   1. Start backend: python run_enhanced_ui.py")
    print("   2. Start React: npm run dev (in frontend folder)")
    print("   3. Navigate to: http://localhost:5174/projects/1/data-imports")
    print("   4. Click 'ACC Data Import' tab (should not be blank)")
    print("   5. Test Browse → Import workflow")

if __name__ == "__main__":
    main()