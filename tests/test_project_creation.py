#!/usr/bin/env python3
"""
Test script to verify project creation functionality works end-to-end
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import insert_project, update_project_record, get_projects, get_db_connection
from config import Config

def test_project_creation():
    """Test creating a project and verify it appears in the project list"""
    print("🧪 Testing project creation functionality...")

    # Test data - using the same format as the UI
    test_project_data = {
        'name': 'Test Project - Automated Test',
        'client_id': 1,  # Assuming client ID 1 exists
        'status': 'Planning',
        'priority': 'Medium',
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'folder_path': 'C:\\Test\\Models',
        'ifc_folder_path': 'C:\\Test\\IFC'
    }

    try:
        # Create basic project first
        print("📝 Creating basic test project...")
        basic_success = insert_project(
            test_project_data['name'], 
            test_project_data.get('folder_path', ''), 
            test_project_data.get('ifc_folder_path', '')
        )
        
        if not basic_success:
            print("❌ Basic project creation failed")
            return False

        # Get the newly created project ID
        projects = get_projects()
        new_project_id = None
        for project_id, project_name in projects:
            if project_name == test_project_data['name']:
                new_project_id = project_id
                break
        
        if not new_project_id:
            print(f"❌ Could not find newly created project: {test_project_data['name']}")
            return False

        # Update with additional details
        additional_data = {}
        if test_project_data.get('client_id'):
            additional_data['client_id'] = test_project_data['client_id']
        if test_project_data.get('status'):
            additional_data['status'] = test_project_data['status']
        if test_project_data.get('priority'):
            additional_data['priority'] = test_project_data['priority']
        if test_project_data.get('start_date'):
            additional_data['start_date'] = test_project_data['start_date']
        if test_project_data.get('end_date'):
            additional_data['end_date'] = test_project_data['end_date']
            
        if additional_data:
            print("📝 Updating project with additional details...")
            update_success = update_project_record(new_project_id, additional_data)
            if not update_success:
                print("❌ Failed to update project with additional details")
                return False

        print("✅ Project created successfully")

        # Verify project appears in list
        print("🔍 Verifying project appears in project list...")
        projects = get_projects()
        project_names = [name for id, name in projects]

        if test_project_data['name'] in project_names:
            print("✅ Project found in project list")
            return True
        else:
            print("❌ Project not found in project list")
            print(f"Available projects: {project_names}")
            return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting project creation tests...\n")

    # Test database connection first
    if not test_database_connection():
        sys.exit(1)

    print()

    # Test project creation
    if test_project_creation():
        print("\n🎉 All tests passed! Project creation functionality is working.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed! Check the implementation.")
        sys.exit(1)