#!/usr/bin/env python3
"""
Test the improved delete_all_project_reviews method
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from review_management_service import ReviewManagementService

def test_delete_all_reviews_detailed():
    """Test the delete_all_project_reviews method with detailed logging"""
    print("🔍 Testing improved delete_all_project_reviews method...")
    
    # Connect to database
    with get_db_connection() as conn:
    if conn is None:
        print("❌ Failed to connect to database")
        return False
    
    try:
        service = ReviewManagementService(conn)
        
        # First, let's see what projects have services
        print("\n1. Checking available projects with services:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 5 p.project_id, p.project_name, COUNT(s.service_id) as service_count
            FROM Projects p
            LEFT JOIN ProjectServices s ON p.project_id = s.project_id
            GROUP BY p.project_id, p.project_name
            HAVING COUNT(s.service_id) > 0
            ORDER BY service_count DESC
        """)
        projects = cursor.fetchall()
        
        if not projects:
            print("   No projects with services found")
            return True
        
        for project in projects:
            project_id, project_name, service_count = project
            print(f"   Project {project_id}: '{project_name}' - {service_count} services")
        
        # Test with the first project
        test_project_id = projects[0][0]
        print(f"\n2. Testing with project {test_project_id}:")
        
        # Get current services and reviews
        services = service.get_project_services(test_project_id)
        print(f"   Services found: {len(services)}")
        
        # Count reviews
        cursor.execute("""
            SELECT COUNT(*) FROM ServiceReviews sr
            JOIN ProjectServices ps ON sr.service_id = ps.service_id  
            WHERE ps.project_id = ?
        """, (test_project_id,))
        review_count = cursor.fetchone()[0]
        print(f"   Reviews found: {review_count}")
        
        if review_count == 0:
            print("   No reviews to delete - testing with empty case")
        
        # Test the delete method
        print(f"\n3. Running delete_all_project_reviews({test_project_id}):")
        result = service.delete_all_project_reviews(test_project_id)
        
        print(f"   Result: {result}")
        
        # Verify the result structure
        expected_keys = ['reviews_deleted', 'services_deleted', 'success']
        if all(key in result for key in expected_keys):
            print("✅ Method returns correct structure")
            if result['success']:
                print("✅ Operation reported success")
                return True
            else:
                print("❌ Operation reported failure")
                return False
        else:
            print("❌ Method return structure incorrect")
            return False
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:

if __name__ == "__main__":
    success = test_delete_all_reviews_detailed()
    
    if success:
        print("\n✅ Delete method test completed successfully!")
    else:
        print("\n❌ Delete method test failed!")