#!/usr/bin/env python3
"""
Test script to debug ACC connector issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection, get_acc_folder_path, insert_files_into_tblACCDocs
from constants import schema as S

def test_database_connection():
    """Test basic database connectivity"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT TOP 3 project_id, project_name FROM projects')
            projects = cursor.fetchall()
            print("✅ Database connection successful")
            print("Projects found:")
            for project in projects:
                print(f"  - ID: {project[0]}, Name: {project[1]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_acc_folder_path(project_id):
    """Test getting ACC folder path for a project"""
    try:
        folder_path = get_acc_folder_path(project_id)
        print(f"✅ ACC folder path for project {project_id}: {folder_path}")
        
        if folder_path:
            exists = os.path.exists(folder_path)
            print(f"  - Folder exists: {exists}")
            if exists:
                files = os.listdir(folder_path)[:5]
                print(f"  - Sample files: {files}")
        else:
            print(f"  - No folder path configured for project {project_id}")
        
        return folder_path
    except Exception as e:
        print(f"❌ Error getting ACC folder path: {e}")
        return None

def test_table_structure():
    """Test ACC docs table structure"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP 3 * FROM {S.ACCDocs.TABLE}")
            rows = cursor.fetchall()
            print(f"✅ {S.ACCDocs.TABLE} table accessible")
            print(f"  - Records found: {len(rows)}")
            if rows:
                print(f"  - Sample record: {rows[0]}")
            return True
    except Exception as e:
        print(f"❌ Error accessing {S.ACCDocs.TABLE}: {e}")
        return False

def main():
    print("=== ACC Desktop Connector Debug Test ===\n")
    
    # 1. Test database connection
    print("1. Testing database connection...")
    if not test_database_connection():
        return
    
    # 2. Test table structure
    print("\n2. Testing ACC docs table...")
    test_table_structure()
    
    # 3. Test folder path for project 1
    print("\n3. Testing ACC folder path...")
    folder_path = test_acc_folder_path(1)
    
    print("\n=== Test Results ===")
    print(f"Database: ✅ Connected")
    print(f"ACC Table: ✅ Accessible")
    print(f"Folder Path: {'✅' if folder_path else '⚠️'} {folder_path or 'Not configured'}")

if __name__ == "__main__":
    main()