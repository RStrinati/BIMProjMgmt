#!/usr/bin/env python3
"""
Test the improved template loading functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from review_management_service import ReviewManagementService

def test_template_loading():
    """Test template loading with the improved matching"""
    print("🔍 Testing improved template loading...")
    
    # Connect to database
    conn = connect_to_db()
    if conn is None:
        print("❌ Failed to connect to database")
        return
    
    try:
        service = ReviewManagementService(conn)
        
        # Test the exact template name that was failing
        problem_template = "AWS – MEL081 STOCKMAN"
        print(f"\n1. Testing problematic template: '{problem_template}'")
        
        result = service.load_template(problem_template)
        if result:
            print("✅ Template loaded successfully!")
            print(f"   Template name: '{result.get('name')}'")
            print(f"   Sector: '{result.get('sector')}'")
            print(f"   Items count: {len(result.get('items', []))}")
        else:
            print("❌ Template still failed to load")
        
        # Test all available templates to make sure we didn't break anything
        print(f"\n2. Testing all available templates:")
        templates = service.get_available_templates()
        
        for template in templates:
            name = template.get('name')
            print(f"   Testing: '{name}'")
            result = service.load_template(name)
            if result:
                print(f"   ✅ OK")
            else:
                print(f"   ❌ Failed")
        
        # Test normalized names
        print(f"\n3. Testing normalized names:")
        test_names = [
            "AWS - MEL081 STOCKMAN",  # Regular hyphen
            "AWS – MEL081 STOCKMAN",  # En-dash
            "AWS — MEL081 STOCKMAN",  # Em-dash
        ]
        
        for test_name in test_names:
            print(f"   Testing: '{test_name}' (ord of dash: {ord(test_name[4])})")
            result = service.load_template(test_name)
            if result:
                print(f"   ✅ Matched: '{result.get('name')}'")
            else:
                print(f"   ❌ No match")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_template_loading()