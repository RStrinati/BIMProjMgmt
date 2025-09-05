#!/usr/bin/env python3
"""Test script to check which projects have services"""

try:
    from database import connect_to_db, get_projects
    from review_management_service import ReviewManagementService
    
    print("Checking which projects have services...")
    
    # Test database connection
    db_conn = connect_to_db()
    if db_conn:
        review_service = ReviewManagementService(db_conn)
        
        # Test all projects
        projects = get_projects()
        print(f"Found {len(projects)} projects:")
        
        for project in projects:
            project_id = project[0]
            project_name = project[1] if len(project) > 1 else f"Project {project_id}"
            
            try:
                services = review_service.get_project_services(project_id)
                print(f"  Project {project_id} ({project_name}): {len(services)} services")
                
                if services:
                    print("    Services found:")
                    for service in services:
                        print(f"      - {service.get('service_name', 'Unknown')} ({service.get('unit_type', 'Unknown')})")
                        
            except Exception as e:
                print(f"  Project {project_id}: Error getting services - {e}")
        
        # Test review generation on project with services
        for project in projects:
            project_id = project[0]
            services = review_service.get_project_services(project_id)
            if services:
                print(f"\nTesting review generation on project {project_id}...")
                reviews = review_service.generate_service_reviews(project_id)
                print(f"Generated {len(reviews)} reviews")
                break
        else:
            print("\nNo projects have services - cannot test review generation")
        
    else:
        print("❌ Database connection failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
