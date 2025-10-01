#!/usr/bin/env python3
"""Test review generation after fixing database schema issues"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_management_service import ReviewManagementService
from database import connect_to_db

def test_review_generation_fixed():
    """Test if review generation works after schema fixes"""
    
    print("🧪 Testing Review Generation After Schema Fix...")
    print("=" * 50)
    
    # Connect to the database
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return False
    
    service = ReviewManagementService(db)
    
    # Find a project with review services
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT ps.project_id, p.project_name, COUNT(ps.service_id) as service_count
        FROM ProjectServices ps
        JOIN Projects p ON ps.project_id = p.project_id
        WHERE ps.unit_type = 'review' AND ps.unit_qty > 0
        GROUP BY ps.project_id, p.project_name
        ORDER BY service_count DESC
    """)
    
    projects_with_services = cursor.fetchall()
    
    if not projects_with_services:
        print("❌ No projects found with review services configured")
        return False
    
    # Use the first project
    project_id = projects_with_services[0][0]
    project_name = projects_with_services[0][1]
    service_count = projects_with_services[0][2]
    
    print(f"🎯 Testing with Project {project_id}: {project_name} ({service_count} review services)")
    
    # Test get_project_services (should work now)
    print(f"\n🔍 Testing get_project_services()...")
    services = service.get_project_services(project_id)
    
    if services:
        print(f"✅ Successfully retrieved {len(services)} services")
        
        review_services = [s for s in services if s.get('unit_type') == 'review' and (s.get('unit_qty') or 0) > 0]
        print(f"📊 Found {len(review_services)} services configured for review generation:")
        
        for svc in review_services:
            print(f"  📄 Service {svc['service_id']}: {svc.get('service_name', 'Unknown')}")
            print(f"    - Quantity: {svc.get('unit_qty')}")
            print(f"    - Schedule: {svc.get('schedule_start')} to {svc.get('schedule_end')}")
            print(f"    - Frequency: {svc.get('schedule_frequency')}")
    else:
        print("❌ Failed to retrieve services")
        return False
    
    # Test get_service_reviews (should work now) 
    print(f"\n🔍 Testing get_service_reviews()...")
    existing_reviews = service.get_service_reviews(project_id)
    print(f"📊 Found {len(existing_reviews)} existing reviews")
    
    if existing_reviews:
        print("📋 Sample existing reviews:")
        for i, review in enumerate(existing_reviews[:3]):
            print(f"  {i+1}. Review {review.get('review_id')}: Cycle {review.get('cycle_no')}")
            print(f"     Service: {review.get('service_name')} (ID: {review.get('service_id')})")
            print(f"     Date: {review.get('planned_date')}, Status: {review.get('status')}")
    
    # Test generate_service_reviews
    print(f"\n🏗️ Testing generate_service_reviews()...")
    try:
        reviews_created = service.generate_service_reviews(project_id)
        
        if reviews_created:
            print(f"✅ Successfully generated {len(reviews_created)} review cycles!")
            print("📋 Generated reviews summary:")
            for i, review in enumerate(reviews_created[:5]):  # Show first 5
                print(f"  {i+1}. Review ID: {review.get('review_id')}")
                print(f"     Service ID: {review.get('service_id')}")
                print(f"     Cycle: {review.get('cycle_no')}")
                print(f"     Planned Date: {review.get('planned_date')}")
                print(f"     Discipline: {review.get('disciplines', 'N/A')}")
            
            if len(reviews_created) > 5:
                print(f"  ... and {len(reviews_created) - 5} more")
        else:
            print("⚠️ No reviews were generated")
            print("🔍 This could be because:")
            print("  - Services already have reviews generated")
            print("  - Date/schedule configuration issues")
            print("  - Database constraints")
            
        # Check the result again
        print(f"\n🔄 Checking reviews after generation...")
        updated_reviews = service.get_service_reviews(project_id)
        print(f"📊 Now have {len(updated_reviews)} total reviews")
        
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

if __name__ == "__main__":
    success = test_review_generation_fixed()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Review generation test PASSED!")
        print("✅ The review generation functionality now works correctly.")
        print("✅ Both Services Setup and Review Planning tabs should work.")
    else:
        print("❌ Review generation test FAILED!")
        print("❌ There are still issues with the review generation process.")