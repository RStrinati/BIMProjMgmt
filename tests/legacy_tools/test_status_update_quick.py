#!/usr/bin/env python3
"""
Quick test for status update functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from review_management_service import ReviewManagementService

def test_status_update():
    """Test the status update functionality"""
    print("\n" + "="*70)
    print("Testing Non-Review Service Status Update")
    print("="*70)
    
    with get_db_connection() as conn:
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        service = ReviewManagementService(conn)
        project_id = 1
        
        # Get services
        services = service.get_project_services(project_id)
        non_review = [s for s in services if s.get('unit_type', '').lower() != 'review']
        
        if not non_review:
            print("⚠️ No non-review services found in project 1")
            return False
        
        test_service = non_review[0]
        service_id = test_service.get('service_id')
        service_name = test_service.get('service_name')
        
        print(f"\n✅ Testing with service: {service_name} (ID: {service_id})")
        print(f"   Type: {test_service.get('unit_type')}")
        print(f"   Current Status: {test_service.get('status')}")
        print(f"   Current Progress: {test_service.get('progress_pct')}%")
        
        # Test status progression
        test_statuses = [
            ('planned', 0),
            ('in_progress', 50),
            ('completed', 100)
        ]
        
        all_passed = True
        
        for status, expected_progress in test_statuses:
            print(f"\n🔄 Setting status to: {status} (expected progress: {expected_progress}%)")
            
            result = service.set_non_review_service_status(service_id, status)
            
            if result:
                # Verify
                updated_services = service.get_project_services(project_id)
                updated = next((s for s in updated_services if s.get('service_id') == service_id), None)
                
                if updated:
                    actual_status = updated.get('status')
                    actual_progress = float(updated.get('progress_pct', 0))
                    
                    if actual_status == status and actual_progress == expected_progress:
                        print(f"   ✅ SUCCESS - Status: {actual_status}, Progress: {actual_progress}%")
                    else:
                        print(f"   ❌ FAILED - Expected: {status}/{expected_progress}%, Got: {actual_status}/{actual_progress}%")
                        all_passed = False
                else:
                    print(f"   ❌ FAILED - Could not retrieve updated service")
                    all_passed = False
            else:
                print(f"   ❌ FAILED - Update returned False")
                all_passed = False
        
        print("\n" + "="*70)
        if all_passed:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:

if __name__ == "__main__":
    success = test_status_update()
    sys.exit(0 if success else 1)
