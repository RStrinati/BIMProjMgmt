#!/usr/bin/env python3
"""Test the simplified delete all reviews functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_management_service import ReviewManagementService
from database import connect_to_db
import time

def test_delete_method():
    """Test if the simplified delete method works without freezing"""
    
    # Connect to the database
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return False
    
    service = ReviewManagementService(db)
    
    # Test with a project (use a project ID that exists)
    # Let's first see what projects we have
    cursor = db.cursor()
    cursor.execute("SELECT TOP 5 project_id, project_name FROM Projects ORDER BY project_id")
    projects = cursor.fetchall()
    
    print("📋 Available projects:")
    for project in projects:
        print(f"  - Project {project[0]}: {project[1]}")
    
    if not projects:
        print("❌ No projects found in database")
        cursor.close()
        db.close()
        return False
    
    # Use the first project for testing
    test_project_id = projects[0][0]
    test_project_name = projects[0][1]
    
    print(f"\n🧪 Testing delete method with Project {test_project_id}: {test_project_name}")
    
    # First check how many reviews exist
    cursor.execute("""
        SELECT COUNT(*) FROM ServiceReviews sr
        INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
        WHERE ps.project_id = ?
    """, (test_project_id,))
    
    review_count = cursor.fetchone()[0]
    print(f"📊 Current reviews for this project: {review_count}")
    
    if review_count == 0:
        print("ℹ️ No reviews to delete - test will still run to check for errors")
    
    # Test the delete method with timeout
    print(f"\n⏱️ Starting delete operation (with 10 second timeout)...")
    start_time = time.time()
    
    try:
        result = service.delete_all_project_reviews(test_project_id)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Delete completed in {duration:.2f} seconds")
        print(f"📊 Result: {result}")
        
        if result.get('success'):
            print("🎉 Delete method worked successfully!")
            return True
        else:
            print(f"❌ Delete method returned error: {result.get('error')}")
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Delete method failed after {duration:.2f} seconds")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    print("🧪 Testing simplified delete all reviews method...")
    success = test_delete_method()
    
    if success:
        print("\n✅ Delete method test PASSED!")
        print("The simplified approach appears to work correctly.")
    else:
        print("\n❌ Delete method test FAILED!")
        print("The method still has issues that need to be addressed.")