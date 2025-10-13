#!/usr/bin/env python3
"""Test script to reproduce service template loading issues"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection, get_projects
from review_management_service import ReviewManagementService
import json

def test_template_loading():
    """Test template loading functionality"""
    print("🔍 Testing service template loading...")
    
    try:
        # Test 1: Check if templates directory exists
        template_file = os.path.join(os.path.dirname(__file__), '..', 'templates', 'service_templates.json')
        template_file = os.path.abspath(template_file)
        print(f"📁 Template file path: {template_file}")
        
        if not os.path.exists(template_file):
            print("❌ Template file does not exist!")
            return False
        else:
            print("✅ Template file exists")
        
        # Test 2: Check if template file can be loaded
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Template file loaded successfully - {len(data.get('templates', []))} templates found")
        except json.JSONDecodeError as e:
            print(f"❌ Template file JSON decode error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading template file: {e}")
            return False
        
        # Test 3: Connect to database
        with get_db_connection() as conn:
        if not conn:
            print("❌ Database connection failed")
            return False
        print("✅ Database connected successfully")
        
        # Test 4: Initialize ReviewManagementService
        try:
            review_service = ReviewManagementService(conn)
            print("✅ ReviewManagementService initialized")
        except Exception as e:
            print(f"❌ Error initializing ReviewManagementService: {e}")
            return False
        
        # Test 5: Get available templates
        try:
            templates = review_service.get_available_templates()
            print(f"✅ get_available_templates() returned {len(templates)} templates:")
            for i, template in enumerate(templates):
                print(f"  {i+1}. {template.get('name', 'Unknown')} ({template.get('sector', 'Unknown')})")
        except Exception as e:
            print(f"❌ Error getting available templates: {e}")
            return False
        
        # Test 6: Try to load each template
        if templates:
            for template in templates:
                template_name = template.get('name', '')
                if template_name:
                    try:
                        loaded_template = review_service.load_template(template_name)
                        if loaded_template:
                            print(f"✅ Template '{template_name}' loaded successfully - {len(loaded_template.get('items', []))} items")
                        else:
                            print(f"❌ Template '{template_name}' returned None")
                    except Exception as e:
                        print(f"❌ Error loading template '{template_name}': {e}")
        else:
            print("❌ No templates available to test loading")
        
        # Test 7: Try applying a template to a project
        projects = get_projects()
        if projects and templates:
            project_id = projects[0][0]
            template_name = templates[0].get('name', '')
            
            if template_name:
                try:
                    print(f"\n🔧 Testing template application: '{template_name}' to project {project_id}")
                    services = review_service.apply_template(project_id, template_name)
                    if services:
                        print(f"✅ Template applied successfully - {len(services)} services created")
                        for service in services:
                            print(f"  - {service.get('service_name', 'Unknown Service')}")
                    else:
                        print("❌ Template application returned no services")
                except Exception as e:
                    print(f"❌ Error applying template: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals() and conn:

if __name__ == "__main__":
    success = test_template_loading()
    if success:
        print("\n🎉 Template testing completed")
    else:
        print("\n💥 Template testing failed")
    
    sys.exit(0 if success else 1)