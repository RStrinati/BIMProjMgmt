#!/usr/bin/env python3
"""Test service addition process"""

from database import connect_to_db, get_projects
from review_management_service import ReviewManagementService

try:
    print("🔍 Testing service addition process...")
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        print("❌ Database connection failed")
        exit(1)
    
    review_service = ReviewManagementService(conn)
    print("✅ ReviewManagementService initialized")
    
    # Get first project
    projects = get_projects()
    if not projects:
        print("❌ No projects found")
        exit(1)
    
    project_id = projects[0][0]
    print(f"📁 Using project ID: {project_id}")
    
    # Test getting available templates
    print("\n📋 Testing get_available_templates...")
    templates = review_service.get_available_templates()
    print(f"✅ Found {len(templates)} templates:")
    for template in templates:
        print(f"  - {template['name']} ({template['sector']})")
    
    # Test loading a template
    if templates:
        template_name = templates[0]['name']
        print(f"\n📄 Testing load_template: {template_name}")
        template = review_service.load_template(template_name)
        if template:
            print(f"✅ Template loaded with {len(template['items'])} items")
        else:
            print("❌ Failed to load template")
    
    # Test getting current project services
    print(f"\n🔧 Testing get_project_services for project {project_id}...")
    services = review_service.get_project_services(project_id)
    print(f"✅ Found {len(services)} existing services")
    
    # Test creating a simple service manually
    print(f"\n➕ Testing manual service creation...")
    service_data = {
        'project_id': project_id,
        'phase': 'Test Phase',
        'service_code': 'TEST',
        'service_name': 'Test Service',
        'unit_type': 'lump_sum',
        'unit_qty': 1,
        'unit_rate': 0,
        'lump_sum_fee': 1000,
        'agreed_fee': 1000,
        'bill_rule': 'on_completion',
        'notes': 'Test service created by script'
    }
    
    try:
        service_id = review_service.create_project_service(service_data)
        print(f"✅ Service created with ID: {service_id}")
        
        # Clean up - delete the test service
        print("🗑️ Cleaning up test service...")
        review_service.delete_project_service(service_id)
        print("✅ Test service deleted")
        
    except Exception as e:
        print(f"❌ Error creating service: {e}")
        import traceback
        traceback.print_exc()
    
    conn.close()
    print("\n✅ All tests completed")
    
except Exception as e:
    print(f"❌ Error in test: {e}")
    import traceback
    traceback.print_exc()
