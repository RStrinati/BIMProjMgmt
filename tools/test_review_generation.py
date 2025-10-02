#!/usr/bin/env python3
"""Test review generation functionality from both tabs"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_management_service import ReviewManagementService
from database import connect_to_db
from datetime import datetime, timedelta

def test_review_generation():
    """Test if review generation works correctly"""
    
    # Connect to the database
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return False
    
    service = ReviewManagementService(db)
    
    # Get a test project with services
    cursor = db.cursor()
    
    # Find a project with services configured for reviews
    cursor.execute("""
        SELECT p.project_id, p.project_name, COUNT(ps.service_id) as service_count
        FROM Projects p
        LEFT JOIN ProjectServices ps ON p.project_id = ps.project_id
        WHERE ps.unit_type = 'review' AND ps.unit_qty > 0
        GROUP BY p.project_id, p.project_name
        HAVING COUNT(ps.service_id) > 0
        ORDER BY service_count DESC
    """)
    
    projects_with_services = cursor.fetchall()
    
    if not projects_with_services:
        print("❌ No projects found with review services configured")
        print("📋 Let me check all projects and their services:")
        
        cursor.execute("""
            SELECT p.project_id, p.project_name, 
                   ps.service_id, ps.unit_type, ps.unit_qty, ps.schedule_frequency
            FROM Projects p
            LEFT JOIN ProjectServices ps ON p.project_id = ps.project_id
            ORDER BY p.project_id, ps.service_id
        """)
        
        all_projects = cursor.fetchall()
        current_project = None
        
        for row in all_projects:
            project_id, project_name, service_id, unit_type, unit_qty, frequency = row
            
            if current_project != project_id:
                print(f"\n📁 Project {project_id}: {project_name}")
                current_project = project_id
            
            if service_id:
                print(f"  📄 Service {service_id}: {unit_type or 'None'} (qty: {unit_qty or 0}, freq: {frequency or 'None'})")
            else:
                print(f"  ⚠️ No services configured")
        
        cursor.close()
        db.close()
        return False
    
    # Use the first project with review services
    test_project = projects_with_services[0]
    project_id = test_project[0]
    project_name = test_project[1]
    service_count = test_project[2]
    
    print(f"🧪 Testing with Project {project_id}: {project_name} ({service_count} review services)")
    
    # Get the actual services to see their configuration
    services = service.get_project_services(project_id)
    print(f"\n📋 Services for this project:")
    
    for svc in services:
        print(f"  📄 Service {svc['service_id']}: {svc.get('service_name', 'Unknown')}")
        print(f"    - Unit Type: {svc.get('unit_type')}")
        print(f"    - Unit Quantity: {svc.get('unit_qty')}")
        print(f"    - Schedule Start: {svc.get('schedule_start')}")
        print(f"    - Schedule End: {svc.get('schedule_end')}")
        print(f"    - Frequency: {svc.get('schedule_frequency')}")
    
    # Check existing reviews before generation
    existing_reviews = service.get_service_reviews(project_id)
    print(f"\n📊 Existing reviews: {len(existing_reviews)}")
    
    # Test the generation method
    print(f"\n🏗️ Testing generate_service_reviews()...")
    try:
        reviews_created = service.generate_service_reviews(project_id)
        
        if reviews_created:
            print(f"✅ Successfully generated {len(reviews_created)} review cycles")
            print("📋 Generated reviews:")
            for i, review in enumerate(reviews_created[:5]):  # Show first 5
                print(f"  {i+1}. Review ID: {review.get('review_id', 'N/A')}")
                print(f"     Service ID: {review.get('service_id', 'N/A')}")
                print(f"     Planned Date: {review.get('planned_date', 'N/A')}")
                print(f"     Discipline: {review.get('discipline', 'N/A')}")
            
            if len(reviews_created) > 5:
                print(f"  ... and {len(reviews_created) - 5} more")
        else:
            print("⚠️ No reviews were generated")
            print("🔍 This could be because:")
            print("  - No services have unit_type = 'review'")
            print("  - Services have unit_qty = 0")
            print("  - Date calculation issues")
            print("  - Database constraints")
        
        cursor.close()
        db.close()
        return len(reviews_created) > 0
        
    except Exception as e:
        print(f"❌ Error during review generation: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        db.close()
        return False

def test_service_configuration():
    """Check if services are properly configured for review generation"""
    
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return
    
    cursor = db.cursor()
    
    print("🔍 Checking service configuration for review generation...")
    
    # Check all services that should generate reviews
    cursor.execute("""
        SELECT ps.project_id, p.project_name, ps.service_id, ps.service_name,
               ps.unit_type, ps.unit_qty, ps.schedule_start, ps.schedule_end,
               ps.schedule_frequency
        FROM ProjectServices ps
        JOIN Projects p ON ps.project_id = p.project_id
        ORDER BY ps.project_id, ps.service_id
    """)
    
    all_services = cursor.fetchall()
    
    review_services = []
    other_services = []
    
    for service in all_services:
        project_id, project_name, service_id, service_name, unit_type, unit_qty, start, end, freq = service
        
        if unit_type == 'review' and unit_qty and unit_qty > 0:
            review_services.append(service)
        else:
            other_services.append(service)
    
    print(f"\n📊 Service Summary:")
    print(f"  🔄 Review services (should generate cycles): {len(review_services)}")
    print(f"  📄 Other services: {len(other_services)}")
    
    if review_services:
        print(f"\n✅ Review services that should work:")
        for service in review_services:
            project_id, project_name, service_id, service_name, unit_type, unit_qty, start, end, freq = service
            print(f"  📁 Project {project_id} ({project_name})")
            print(f"    📄 Service {service_id}: {service_name}")
            print(f"    ⚙️ Config: {unit_qty} {unit_type} cycles, {freq or 'weekly'}")
            print(f"    📅 Schedule: {start or 'No start'} to {end or 'No end'}")
    
    if len(review_services) == 0:
        print(f"\n⚠️ No properly configured review services found!")
        print(f"📋 To fix this, you need services with:")
        print(f"  - unit_type = 'review'")
        print(f"  - unit_qty > 0")
        print(f"  - Optionally: schedule dates and frequency")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    print("🧪 Testing Review Generation Functionality...")
    print("=" * 50)
    
    # First check service configuration
    test_service_configuration()
    
    print("\n" + "=" * 50)
    
    # Then test actual generation
    success = test_review_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Review generation test PASSED!")
        print("The generation functionality appears to work correctly.")
    else:
        print("❌ Review generation test FAILED!")
        print("There are issues with the review generation process.")