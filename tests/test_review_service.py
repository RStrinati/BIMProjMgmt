#!/usr/bin/env python3
"""Test script to check ReviewManagementService functionality"""

try:
    from database import get_db_connection, get_projects
    from review_management_service import ReviewManagementService
    
    print("Testing ReviewManagementService...")
    
    # Test database connection
    print("1. Testing database connection...")
    with get_db_connection() as db_conn:
        print("✅ Database connection successful")
        
        # Test ReviewManagementService initialization
        print("2. Testing ReviewManagementService initialization...")
        review_service = ReviewManagementService(db_conn)
        print("✅ ReviewManagementService initialized")
        
        # Test getting projects
        print("3. Testing get_projects...")
        projects = get_projects()
        if projects:
            project_id = projects[0][0]
            print(f"✅ Found {len(projects)} projects, testing with project {project_id}")
            
            # Test get_project_services
            print("4. Testing get_project_services...")
            try:
                services = review_service.get_project_services(project_id)
                print(f"✅ Found {len(services)} services for project {project_id}")
            except Exception as e:
                print(f"❌ Error getting project services: {e}")
            
            # Test get_available_templates
            print("5. Testing get_available_templates...")
            try:
                templates = review_service.get_available_templates()
                print(f"✅ Found {len(templates)} available templates")
                for template in templates:
                    print(f"  - {template['name']} ({template['sector']})")
            except Exception as e:
                print(f"❌ Error getting templates: {e}")
                
            # Test missing methods
            print("6. Testing missing methods...")
            missing_methods = [
                'get_project_review_stats',
                'generate_service_reviews'
            ]
            
            for method in missing_methods:
                if hasattr(review_service, method):
                    print(f"✅ Method {method} exists")
                else:
                    print(f"❌ Method {method} is missing")
        else:
            print("❌ No projects found")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
