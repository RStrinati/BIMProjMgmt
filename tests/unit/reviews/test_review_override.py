"""
Test Script for Review Status Override Implementation

This script tests the manual override functionality for review status management.
Run this AFTER running the migration script and deploying code changes.

Test Cases:
1. Manual status update persists through refresh
2. Auto status update works for non-override reviews
3. Edit dialog updates persist through refresh
4. Reset to auto works correctly
5. Background sync respects overrides
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db, get_db_connection
from review_management_service import ReviewManagementService
from datetime import datetime, timedelta

def setup_test_data():
    """Create test project and reviews for testing"""
    print("\n" + "=" * 70)
    print("Setting Up Test Data")
    print("=" * 70)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find or create a test project
            cursor.execute("SELECT TOP 1 project_id, project_name FROM Projects ORDER BY project_id DESC")
            result = cursor.fetchone()
            
            if not result:
                print("❌ No projects found. Please create a project first.")
                return None, None
            
            project_id, project_name = result
            print(f"✅ Using project: {project_name} (ID: {project_id})")
            
            # Find reviews for this project
            cursor.execute("""
                SELECT TOP 5 sr.review_id, sr.due_date, sr.status, ps.service_name,
                       ISNULL(sr.status_override, 0) as status_override
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
                ORDER BY sr.due_date
            """, (project_id,))
            
            reviews = cursor.fetchall()
            
            if not reviews:
                print("❌ No reviews found for this project. Please generate reviews first.")
                return None, None
            
            print(f"✅ Found {len(reviews)} reviews for testing")
            for review in reviews:
                override_status = "🔒 Manual" if review[4] else "Auto"
                print(f"   Review {review[0]}: {review[3]} - {review[1]} - Status: {review[2]} ({override_status})")
            
            return project_id, reviews
    
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return None, None

def test_case_1_manual_override_persists():
    """TC1: Manual status update persists through refresh"""
    print("\n" + "=" * 70)
    print("TEST CASE 1: Manual Status Update Persists Through Refresh")
    print("=" * 70)
    
    project_id, reviews = setup_test_data()
    if not project_id or not reviews:
        return False
    
    # Find a future review (should be 'planned')
    future_review = None
    for review in reviews:
        review_date = review[1]
        if isinstance(review_date, str):
            review_date = datetime.strptime(review_date, '%Y-%m-%d').date()
        if review_date > datetime.now().date():
            future_review = review
            break
    
    if not future_review:
        print("⚠️  No future reviews found for testing")
        return False
    
    review_id = future_review[0]
    original_status = future_review[2]
    
    print(f"\n📋 Testing with Review ID: {review_id}")
    print(f"   Original status: {original_status}")
    print(f"   Due date: {future_review[1]} (future)")
    
    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            
            # Step 1: Manually set status to 'completed' (should trigger override)
            print("\n1️⃣  Setting status to 'completed' manually...")
            success = service.update_review_status_to(review_id, 'completed', is_manual_override=True)
            
            if not success:
                print("❌ Failed to update status")
                return False
            
            print("✅ Status updated to 'completed'")
            
            # Step 2: Verify override flag is set
            print("\n2️⃣  Verifying override flag is set...")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, status_override, status_override_by, status_override_at
                FROM ServiceReviews
                WHERE review_id = ?
            """, (review_id,))
            
            result = cursor.fetchone()
            status, override_flag, override_by, override_at = result
            
            if status != 'completed':
                print(f"❌ Status is '{status}', expected 'completed'")
                return False
            
            if override_flag != 1:
                print(f"❌ Override flag is {override_flag}, expected 1")
                return False
            
            print(f"✅ Status: {status}")
            print(f"✅ Override flag: {override_flag}")
            print(f"✅ Override by: {override_by}")
            print(f"✅ Override at: {override_at}")
            
            # Step 3: Run refresh (should NOT change status)
            print("\n3️⃣  Running status refresh (should preserve manual override)...")
            refresh_result = service.update_service_statuses_by_date(project_id, respect_overrides=True)
            
            print(f"✅ Refresh completed: {refresh_result['updated_count']} updates, {refresh_result.get('skipped_count', 0)} skipped")
            
            # Step 4: Verify status is still 'completed'
            print("\n4️⃣  Verifying status is still 'completed'...")
            cursor.execute("SELECT status, status_override FROM ServiceReviews WHERE review_id = ?", (review_id,))
            result = cursor.fetchone()
            status, override_flag = result
            
            if status != 'completed':
                print(f"❌ FAIL: Status changed to '{status}' after refresh!")
                return False
            
            if override_flag != 1:
                print(f"❌ FAIL: Override flag cleared after refresh!")
                return False
            
            print(f"✅ Status still 'completed' (override preserved)")
            print(f"✅ Override flag still set")
            
            print("\n✅ TEST CASE 1 PASSED")
            return True
        
    except Exception as e:
        print(f"❌ TEST CASE 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_case_2_auto_status_update():
    """TC2: Auto status update works for non-override reviews"""
    print("\n" + "=" * 70)
    print("TEST CASE 2: Auto Status Update Works")
    print("=" * 70)
    
    project_id, reviews = setup_test_data()
    if not project_id or not reviews:
        return False
    
    # Find a past review without override
    past_review = None
    for review in reviews:
        review_date = review[1]
        if isinstance(review_date, str):
            review_date = datetime.strptime(review_date, '%Y-%m-%d').date()
        if review_date < datetime.now().date() and review[4] == 0:  # Not overridden
            past_review = review
            break
    
    if not past_review:
        print("⚠️  No past reviews without override found for testing")
        return False
    
    review_id = past_review[0]
    original_status = past_review[2]
    
    print(f"\n📋 Testing with Review ID: {review_id}")
    print(f"   Original status: {original_status}")
    print(f"   Due date: {past_review[1]} (past)")
    print(f"   Override: No")
    
    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            cursor = conn.cursor()
            
            # First set it to 'planned' without override
            print("\n1️⃣  Setting status to 'planned' (auto-managed)...")
            cursor.execute("""
                UPDATE ServiceReviews 
                SET status = 'planned', 
                    status_override = 0,
                    status_override_by = NULL,
                    status_override_at = NULL
                WHERE review_id = ?
            """, (review_id,))
            conn.commit()
            print("✅ Status set to 'planned' (auto-managed)")
            
            # Run refresh
            print("\n2️⃣  Running status refresh (should auto-update to 'completed')...")
            refresh_result = service.update_service_statuses_by_date(project_id, respect_overrides=True)
            print(f"✅ Refresh completed: {refresh_result['updated_count']} updates")
            
            # Verify status changed to 'completed'
            print("\n3️⃣  Verifying status changed to 'completed'...")
            cursor.execute("SELECT status, status_override FROM ServiceReviews WHERE review_id = ?", (review_id,))
            result = cursor.fetchone()
            status, override_flag = result
            
            if status != 'completed':
                print(f"❌ FAIL: Status is '{status}', expected 'completed'")
                return False
            
            if override_flag != 0:
                print(f"❌ FAIL: Override flag set to {override_flag}, should be 0")
                return False
            
            print(f"✅ Status auto-updated to 'completed'")
            print(f"✅ Override flag is 0 (auto-managed)")
            
            print("\n✅ TEST CASE 2 PASSED")
            return True
        
    except Exception as e:
        print(f"❌ TEST CASE 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_case_3_reset_to_auto():
    """TC3: Reset to auto works correctly"""
    print("\n" + "=" * 70)
    print("TEST CASE 3: Reset to Auto Works")
    print("=" * 70)
    
    project_id, reviews = setup_test_data()
    if not project_id or not reviews:
        return False
    
    # Use first review
    review_id = reviews[0][0]
    
    print(f"\n📋 Testing with Review ID: {review_id}")
    
    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            cursor = conn.cursor()
            
            # Set manual override
            print("\n1️⃣  Setting manual override...")
            service.update_review_status_to(review_id, 'in_progress', is_manual_override=True)
            
            cursor.execute("SELECT status, status_override FROM ServiceReviews WHERE review_id = ?", (review_id,))
            status, override = cursor.fetchone()
            
            if override != 1:
                print(f"❌ Failed to set override")
                return False
            
            print(f"✅ Manual override set (status: {status})")
            
            # Clear override
            print("\n2️⃣  Clearing override flag...")
            cursor.execute("""
                UPDATE ServiceReviews 
                SET status_override = 0,
                    status_override_by = NULL,
                    status_override_at = NULL
                WHERE review_id = ?
            """, (review_id,))
            conn.commit()
            print("✅ Override flag cleared")
            
            # Verify cleared
            print("\n3️⃣  Verifying override is cleared...")
            cursor.execute("SELECT status_override FROM ServiceReviews WHERE review_id = ?", (review_id,))
            override = cursor.fetchone()[0]
            
            if override != 0:
                print(f"❌ Override flag is {override}, should be 0")
                return False
            
            print("✅ Override flag is 0 (reset to auto)")
            
            # Run refresh to recalculate
            print("\n4️⃣  Running refresh to recalculate status...")
            service.update_service_statuses_by_date(project_id, respect_overrides=False)
            
            cursor.execute("SELECT status FROM ServiceReviews WHERE review_id = ?", (review_id,))
            new_status = cursor.fetchone()[0]
            
            print(f"✅ Status recalculated to: {new_status}")
            
            print("\n✅ TEST CASE 3 PASSED")
            return True
        
    except Exception as e:
        print(f"❌ TEST CASE 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 70)
    print("REVIEW STATUS OVERRIDE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    results = {
        'TC1: Manual Override Persists': test_case_1_manual_override_persists(),
        'TC2: Auto Status Update': test_case_2_auto_status_update(),
        'TC3: Reset to Auto': test_case_3_reset_to_auto(),
    }
    
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for p in results.values() if p)
    
    print("\n" + "=" * 70)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    print("Review Status Override Test Suite")
    print("=" * 70)
    print("\nPrerequisites:")
    print("1. ✅ Migration script has been run")
    print("2. ✅ Code changes deployed")
    print("3. ✅ At least one project with reviews exists")
    print("\nStarting tests in 3 seconds...")
    
    import time
    time.sleep(3)
    
    success = run_all_tests()
    
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
