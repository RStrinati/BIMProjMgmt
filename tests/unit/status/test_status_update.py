#!/usr/bin/env python3
"""
Test script for review status update functionality
"""

import sys
import os
from review_management_service import ReviewManagementService
from database import get_db_connection

def test_status_update():
    """Test the new status update functionality"""
    print("Testing Review Status Update Functionality")
    print("=" * 50)
    
    try:
        # Create database connection
        with get_db_connection() as db_conn:
            # Create service instance
            service = ReviewManagementService(db_conn)
            
            # Get a sample review to test with
            query = """
            SELECT TOP 1 review_id, status 
            FROM ServiceReviews 
            WHERE status IS NOT NULL
            ORDER BY review_id
            """
            service.cursor.execute(query)
            result = service.cursor.fetchone()
            
            if not result:
                print("No reviews found to test with")
                return
            
            review_id, current_status = result
            print(f"Testing with Review ID: {review_id}")
            print(f"Current Status: {current_status}")
            
            # Test status validation
            print("\n1. Testing status validation:")
            valid_statuses = ['planned', 'in_progress', 'completed', 'report_issued', 'closed', 'cancelled']
            
            for status in valid_statuses:
                is_valid = service.is_valid_status_transition(current_status, status)
                print(f"   {current_status} -> {status}: {'✓' if is_valid else '✗'}")
            
            # Test invalid status
            print(f"\n2. Testing invalid status:")
            success = service.update_review_status_to(review_id, "invalid_status")
            print(f"   Update to invalid status: {'✗ Failed as expected' if not success else '✓ Unexpectedly succeeded'}")
            
            # Test valid status update (but don't actually change)
            print(f"\n3. Testing valid status update:")
            # Update to same status (should succeed)
            success = service.update_review_status_to(review_id, current_status)
            print(f"   Update to same status ({current_status}): {'✓' if success else '✗'}")
            
            # Verify status didn't change
            new_status = service.get_review_current_status(review_id)
            print(f"   Status after update: {new_status}")
            print(f"   Status unchanged: {'✓' if new_status == current_status else '✗'}")
            
            print(f"\n4. Testing with evidence link:")
            success = service.update_review_status_to(review_id, current_status, "test_evidence_link.pdf")
            print(f"   Update with evidence link: {'✓' if success else '✗'}")
            
            print("\n" + "=" * 50)
            print("Status update functionality test completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status_update()