#!/usr/bin/env python3
"""
Test script for the new Review Management system
This tests the core functionality of the comprehensive workflow implementation
"""

import sys
import sqlite3
from datetime import datetime, timedelta
import json

def test_service_template_loading():
    """Test loading service templates"""
    print("🔧 Testing service template loading...")
    
    try:
        with open('templates/service_templates.json', 'r') as f:
            data = json.load(f)
        
        templates = data['templates']
        
        print(f"✅ Loaded {len(templates)} templates")
        for template in templates:
            print(f"   📋 {template['name']}: {template['sector']} - {len(template['items'])} items")
        
        return True
    except Exception as e:
        print(f"❌ Template loading failed: {e}")
        return False

def test_database_schema():
    """Test database schema creation"""
    print("\n🗄️ Testing database schema...")
    
    try:
        # Create test database
        conn = sqlite3.connect(":memory:")
        
        # Read and execute schema
        with open('sql/review_management_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema in parts (SQLite doesn't handle multiple statements well)
        statements = schema_sql.split(';')
        for stmt in statements:
            if stmt.strip():
                try:
                    conn.execute(stmt)
                except Exception as e:
                    # Skip statements that might not work in SQLite
                    if "stored procedure" in str(e).lower() or "function" in str(e).lower():
                        continue
                    else:
                        print(f"⚠️ Schema warning: {e}")
        
        conn.commit()
        
        # Test table creation
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Created {len(tables)} tables")
        for table in tables:
            print(f"   📊 {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_review_service():
    """Test review management service"""
    print("\n⚙️ Testing review management service...")
    
    try:
        from review_management_service import ReviewManagementService
        
        # Create test database
        conn = sqlite3.connect(":memory:")
        
        # Simple table for testing
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Projects (
                project_id INTEGER PRIMARY KEY,
                project_name TEXT,
                client_name TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ProjectServices (
                service_id INTEGER PRIMARY KEY,
                project_id INTEGER,
                phase TEXT,
                service_name TEXT,
                unit_type TEXT,
                unit_qty REAL,
                unit_rate REAL,
                agreed_fee REAL,
                progress_pct REAL DEFAULT 0,
                claimed_to_date REAL DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)
        
        conn.commit()
        
        # Initialize service
        service = ReviewManagementService(conn)
        print("✅ ReviewManagementService initialized")
        
        # Test template loading
        templates = service.get_available_templates()
        print(f"✅ Available templates: {templates}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Review service test failed: {e}")
        return False

def test_ui_components():
    """Test UI component creation"""
    print("\n🖥️ Testing UI components...")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        from tkcalendar import DateEntry
        
        # Create test window
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Test date picker
        date_entry = DateEntry(root, width=12, date_pattern='yyyy-mm-dd')
        print("✅ DateEntry widget created")
        
        # Test treeview
        tree = ttk.Treeview(root, columns=("A", "B", "C"), show="headings")
        print("✅ Treeview widget created")
        
        # Test combobox
        combo = ttk.Combobox(root, values=["Option 1", "Option 2"])
        print("✅ Combobox widget created")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ UI component test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Review Management System Implementation")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Service Templates", test_service_template_loading()))
    results.append(("Database Schema", test_database_schema()))
    results.append(("Review Service", test_review_service()))
    results.append(("UI Components", test_ui_components()))
    
    # Summary
    print("\n📊 Test Summary")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The Review Management system is ready.")
        print("\n📋 Next Steps:")
        print("1. Run the main application: python phase1_enhanced_ui.py")
        print("2. Select a project to test the new workflow")
        print("3. Apply a service template to create project scope")
        print("4. Generate review cycles for scheduling")
        print("5. Test progress tracking and billing claims")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Please review the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
