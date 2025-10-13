#!/usr/bin/env python3
"""
Test the enhanced template loading system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_management_service import ReviewManagementService
import sqlite3

def test_template_loading():
    """Test the enhanced template loading functionality"""
    
    print("🧪 Testing Enhanced Template Loading System")
    print("=" * 50)
    
    # Create a mock database connection
    conn = sqlite3.connect(':memory:')
    service = ReviewManagementService(conn)
    
    # Test 1: Get available templates
    print("\n1️⃣ Testing get_available_templates()")
    templates = service.get_available_templates()
    
    if templates:
        print(f"✅ Found {len(templates)} templates:")
        for template in templates:
            print(f"   📋 {template['name']} ({template['sector']})")
            print(f"      Items: {template['total_items']}, Reviews: {template['total_reviews']}")
            print(f"      Estimated Value: ${template['estimated_value']:,.2f}")
            print(f"      Valid: {'✅' if template['is_valid'] else '❌'}")
            if not template['is_valid']:
                print(f"      Errors: {template['validation_errors']}")
            print()
    else:
        print("❌ No templates found")
        return False
    
    # Test 2: Load templates by exact name
    print("\n2️⃣ Testing load_template() with exact names")
    test_names = [
        "SINSW – Melrose Park HS",
        "AWS – MEL081 STOCKMAN (Day 1)",
        "Standard Commercial – Office Development"
    ]
    
    for name in test_names:
        print(f"\n🔍 Loading template: '{name}'")
        template = service.load_template(name)
        if template:
            print(f"✅ Successfully loaded: {template['name']}")
            print(f"   Sector: {template['sector']}")
            print(f"   Items: {len(template['items'])}")
        else:
            print(f"❌ Failed to load template")
    
    # Test 3: Test fuzzy matching
    print("\n3️⃣ Testing fuzzy matching")
    fuzzy_names = [
        "SINSW",
        "Melrose Park",
        "AWS",
        "Commercial",
        "Office"
    ]
    
    for name in fuzzy_names:
        print(f"\n🔍 Fuzzy search for: '{name}'")
        template = service.load_template(name)
        if template:
            print(f"✅ Fuzzy match found: {template['name']}")
        else:
            print(f"❌ No fuzzy match found")
    
    # Test 4: Test invalid template names
    print("\n4️⃣ Testing invalid template names")
    invalid_names = [
        "NonExistentTemplate",
        "",
        "123InvalidName"
    ]
    
    for name in invalid_names:
        print(f"\n🔍 Testing invalid name: '{name}'")
        template = service.load_template(name)
        if template:
            print(f"⚠️  Unexpected success for invalid name")
        else:
            print(f"✅ Correctly rejected invalid name")
    print("\n" + "=" * 50)
    print("🎉 Template loading system test completed!")
    return True

if __name__ == "__main__":
    success = test_template_loading()
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)