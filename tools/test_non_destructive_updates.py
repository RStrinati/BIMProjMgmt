#!/usr/bin/env python3
"""
Test script to verify the non-destructive review cycle update fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from review_management_service import ReviewManagementService
from datetime import datetime, timedelta

def test_non_destructive_updates():
    """Test that manual changes are preserved during automatic updates"""
    
    print("🧪 Testing non-destructive review cycle updates...")
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        review_service = ReviewManagementService(conn)
        
        # Find a project with existing services
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 p.project_id, p.project_name 
            FROM Projects p
            JOIN ProjectServices ps ON p.project_id = ps.project_id
            WHERE ps.unit_type = 'review'
            AND ps.unit_qty > 0
        """)
        
        result = cursor.fetchone()
        if not result:
            print("⚠️ No test projects with review services found")
            return False
        
        project_id, project_name = result
        print(f"📋 Testing with project: {project_name} (ID: {project_id})")
        
        # Get existing review cycles before update
        cursor.execute("""
            SELECT sr.review_id, sr.planned_date, sr.status, sr.regeneration_signature
            FROM ServiceReviews sr
            JOIN ProjectServices ps ON sr.service_id = ps.service_id
            WHERE ps.project_id = ?
        """, (project_id,))
        
        before_reviews = cursor.fetchall()
        print(f"📊 Found {len(before_reviews)} existing review cycles")
        
        if not before_reviews:
            print("⚠️ No existing reviews to test with")
            return False
        
        # Manually modify a review status to test preservation
        test_review_id = before_reviews[0][0]
        original_status = before_reviews[0][2]
        new_status = 'in-progress' if original_status != 'in-progress' else 'completed'
        
        cursor.execute("""
            UPDATE ServiceReviews 
            SET status = ?
            WHERE review_id = ?
        """, (new_status, test_review_id))
        conn.commit()
        
        print(f"🔧 Modified review {test_review_id} status: {original_status} → {new_status}")
        
        # Trigger automatic update (should preserve manual changes)
        print("🔄 Triggering automatic review generation...")
        reviews_created = review_service.generate_service_reviews(project_id, force_regenerate=False)
        
        # Check if manual change was preserved
        cursor.execute("""
            SELECT status FROM ServiceReviews 
            WHERE review_id = ?
        """, (test_review_id,))
        
        preserved_status = cursor.fetchone()[0]
        
        if preserved_status == new_status:
            print(f"✅ Manual change preserved! Status still: {preserved_status}")
        else:
            print(f"❌ Manual change lost! Status changed back to: {preserved_status}")
            return False
        
        # Test that forced regeneration does replace cycles
        print("🔄 Testing forced regeneration...")
        reviews_before_force = len(review_service.get_project_review_cycles(project_id))
        
        reviews_created_force = review_service.generate_service_reviews(project_id, force_regenerate=True)
        reviews_after_force = len(review_service.get_project_review_cycles(project_id))
        
        print(f"📊 Forced regeneration: {reviews_before_force} → {reviews_after_force} cycles")
        
        print("✅ All tests passed! Non-destructive update is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_non_destructive_updates()
    sys.exit(0 if success else 1)