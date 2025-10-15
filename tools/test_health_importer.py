#!/usr/bin/env python3
"""
Test suite for the Revit Health Importer functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def test_database_connection():
    """Test that we can connect to the RevitHealthCheckDB."""
    print("Testing database connection...")
    try:
        from database_pool import get_db_connection
        
        with get_db_connection('RevitHealthCheckDB') as conn:
            cursor = conn.cursor()
            result = cursor.execute("SELECT DB_NAME()").fetchone()
            print(f"✅ Connected to: {result[0]}")
            
            # Test table existence
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'tblRvtProjHealth'
            """)
            table_exists = cursor.fetchone()[0] > 0
            print(f"✅ tblRvtProjHealth table exists: {table_exists}")
            
            # Test record count
            cursor.execute("SELECT COUNT(*) FROM tblRvtProjHealth")
            record_count = cursor.fetchone()[0]
            print(f"📊 Current records in tblRvtProjHealth: {record_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_import_function():
    """Test that the import function can be called."""
    print("\nTesting import function...")
    try:
        from handlers.rvt_health_importer import import_health_data
        
        # Test with non-existent folder
        test_folder = r"C:\NonExistent\TestFolder"
        print(f"Testing with non-existent folder: {test_folder}")
        import_health_data(test_folder, project_id=123)
        print("✅ Function handles non-existent folder gracefully")
        return True
        
    except Exception as e:
        print(f"❌ Import function test failed: {e}")
        return False

def check_recent_logs():
    """Check recent log entries from the health importer."""
    print("\nChecking recent imports...")
    try:
        from database_pool import get_db_connection
        
        with get_db_connection('RevitHealthCheckDB') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    SELECT TOP 5 strRvtFileName, strProjectName, strRvtVersion
                FROM tblRvtProjHealth 
                    ORDER BY nId DESC
            """)
            rows = cursor.fetchall()
            
            if rows:
                print("📋 Last 5 imported files:")
                for row in rows:
                        print(f"   {row[0]} - {row[1]} (Revit: {row[2]})")
            else:
                print("📋 No records found in tblRvtProjHealth")
                
            return True
            
    except Exception as e:
        print(f"❌ Log check failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Revit Health Importer Test Suite ===\n")
    
    results = []
    results.append(("Database Connection", test_database_connection()))
    results.append(("Import Function", test_import_function()))
    results.append(("Recent Logs Check", check_recent_logs()))
    
    print("\n=== Test Summary ===")
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())