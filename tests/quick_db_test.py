#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

def test_database_connection():
    """Quick test of database connection and view access"""
    print("=== Testing Database Connection ===")
    
    try:
        conn = connect_to_db()
        if conn is None:
            print("❌ Failed to connect to database")
            return False
            
        print("✅ Connected to database successfully")
        
        cursor = conn.cursor()
        
        # Test basic projects table
        print("\n=== Testing Projects Table ===")
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"Found {project_count} projects")
        
        # Test if the view exists
        print("\n=== Testing AllIssues View ===")
        try:
            cursor.execute("SELECT COUNT(*) FROM vw_ProjectManagement_AllIssues")
            issue_count = cursor.fetchone()[0]
            print(f"✅ Found {issue_count} issues in view")
        except Exception as e:
            print(f"❌ Error accessing vw_ProjectManagement_AllIssues: {e}")
            # Try to see what views do exist
            try:
                cursor.execute("""
                SELECT name 
                FROM sys.views 
                WHERE name LIKE '%issue%' OR name LIKE '%project%'
                ORDER BY name
                """)
                views = cursor.fetchall()
                print(f"Available views: {[v[0] for v in views]}")
            except Exception as view_err:
                print(f"Could not list views: {view_err}")
        
        # Test project_aliases table
        print("\n=== Testing Project Aliases Table ===")
        try:
            cursor.execute("SELECT COUNT(*) FROM project_aliases")
            alias_count = cursor.fetchone()[0]
            print(f"✅ Found {alias_count} project aliases")
        except Exception as e:
            print(f"❌ Error accessing project_aliases: {e}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()