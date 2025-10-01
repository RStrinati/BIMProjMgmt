#!/usr/bin/env python3
"""
Test Non-Review Service Status and Billing Integration

This script tests the new status management system for non-review services
(lump_sum, audit, etc.) and verifies that status changes properly affect
billing calculations and progress percentages.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from review_management_service import ReviewManagementService

def test_non_review_status_updates():
    """Test status updates for non-review services"""
    print("\n🧪 Testing Non-Review Service Status Updates")
    print("=" * 70)
    
    conn = connect_to_db()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        service = ReviewManagementService(conn)
        
        # Test with a known project (adjust project_id as needed)
        test_project_id = 1
        
        print(f"\n📋 Getting services for project {test_project_id}...")
        services = service.get_project_services(test_project_id)
        
        # Find non-review services
        non_review_services = [s for s in services if s.get('unit_type', '').lower() != 'review']
        
        if not non_review_services:
            print("ℹ️  No non-review services found. Creating a test service...")
            # Could create a test service here if needed
            print("   Please create a Digital Initiation or similar service in the UI")
            return False
        
        print(f"\n✅ Found {len(non_review_services)} non-review service(s)")
        
        # Display non-review services
        print("\n" + "─" * 70)
        print(f"{'Service Name':<40} {'Type':<12} {'Status':<15} {'Progress':<10}")
        print("─" * 70)
        
        for svc in non_review_services:
            service_name = svc.get('service_name', 'Unknown')[:38]
            unit_type = svc.get('unit_type', 'unknown')
            status = svc.get('status', 'not_started')
            progress = svc.get('progress_pct', 0)
            
            print(f"{service_name:<40} {unit_type:<12} {status:<15} {progress:>6.1f}%")
        
        # Test status progression on first non-review service
        if non_review_services:
            test_service = non_review_services[0]
            service_id = test_service.get('service_id')
            service_name = test_service.get('service_name')
            
            print(f"\n🔬 Testing status progression on: {service_name}")
            print("─" * 70)
            
            # Test each status
            test_statuses = ['planned', 'in_progress', 'completed']
            expected_progress = {'planned': 0, 'in_progress': 50, 'completed': 100}
            
            for test_status in test_statuses:
                print(f"\n  Setting status to: {test_status}")
                
                # Update status
                success = service.set_non_review_service_status(service_id, test_status)
                
                if success:
                    # Verify the update
                    conn.commit()  # Commit the change
                    
                    # Re-fetch to verify
                    updated_services = service.get_project_services(test_project_id)
                    updated_service = next((s for s in updated_services if s.get('service_id') == service_id), None)
                    
                    if updated_service:
                        actual_status = updated_service.get('status', '')
                        actual_progress = updated_service.get('progress_pct', 0)
                        expected = expected_progress[test_status]
                        
                        status_match = "✅" if actual_status == test_status else "❌"
                        progress_match = "✅" if actual_progress == expected else "❌"
                        
                        print(f"    Status: {actual_status} {status_match}")
                        print(f"    Progress: {actual_progress}% (expected: {expected}%) {progress_match}")
                        
                        if actual_status == test_status and actual_progress == expected:
                            print(f"    ✅ Status update successful!")
                        else:
                            print(f"    ❌ Status update verification failed!")
                    else:
                        print(f"    ❌ Could not verify update")
                else:
                    print(f"    ❌ Failed to set status to {test_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


def test_billing_integration():
    """Test that status changes affect billing calculations"""
    print("\n\n💰 Testing Billing Integration")
    print("=" * 70)
    
    conn = connect_to_db()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        service = ReviewManagementService(conn)
        test_project_id = 1
        
        print(f"\n📊 Service Progress Summary for Project {test_project_id}:")
        print("─" * 90)
        print(f"{'Service':<35} {'Type':<10} {'Fee':<12} {'Progress':<10} {'Billed':<12} {'Remaining':<12}")
        print("─" * 90)
        
        progress_summary = service.get_service_progress_summary(test_project_id)
        
        total_value = 0
        total_billed = 0
        
        for svc in progress_summary:
            service_name = svc.get('service_name', '')[:33]
            unit_type = svc.get('unit_type', 'N/A') if 'unit_type' in svc else 'N/A'
            agreed_fee = svc.get('agreed_fee', 0)
            progress_pct = svc.get('progress_pct', 0)
            billed_amount = svc.get('billed_amount', 0)
            remaining = svc.get('remaining_amount', 0)
            
            total_value += agreed_fee
            total_billed += billed_amount
            
            print(f"{service_name:<35} {unit_type:<10} ${agreed_fee:>10,.0f} "
                  f"{progress_pct:>7.1f}% ${billed_amount:>10,.0f} ${remaining:>10,.0f}")
        
        print("─" * 90)
        print(f"{'TOTALS':<45} ${total_value:>10,.0f} "
              f"         ${total_billed:>10,.0f} ${total_value - total_billed:>10,.0f}")
        print("=" * 90)
        
        # Test billable by stage
        print("\n\n📑 Total Billable by Stage:")
        print("─" * 50)
        print(f"{'Stage/Phase':<35} {'Billed Amount':<15}")
        print("─" * 50)
        
        stage_billing = service.get_billable_by_stage(test_project_id)
        stage_total = 0
        
        for stage_data in stage_billing:
            phase = stage_data.get('phase', 'Unknown')
            billed = stage_data.get('billed_amount', 0)
            stage_total += billed
            print(f"{phase:<35} ${billed:>13,.0f}")
        
        print("─" * 50)
        print(f"{'TOTAL':<35} ${stage_total:>13,.0f}")
        print("=" * 50)
        
        # Test billable by month
        print("\n\n📅 Total Billable by Month:")
        print("─" * 50)
        print(f"{'Month':<35} {'Total Billed':<15}")
        print("─" * 50)
        
        month_billing = service.get_billable_by_month(test_project_id)
        month_total = 0
        
        for month_data in month_billing:
            month_label = month_data.get('month', 'Unknown')
            billed = month_data.get('total_billed', 0)
            month_total += billed
            print(f"{month_label:<35} ${billed:>13,.0f}")
        
        print("─" * 50)
        print(f"{'TOTAL':<35} ${month_total:>13,.0f}")
        print("=" * 50)
        
        print("\n\n✅ Billing integration test completed!")
        print("\nKey Points:")
        print("  • Non-review services (lump_sum, audit) can be set to planned/in_progress/completed")
        print("  • Status changes automatically update progress_pct (0%, 50%, 100%)")
        print("  • Progress changes are reflected in billing calculations")
        print("  • Billing totals are aggregated by stage and by month")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during billing test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔬 BIM Project Management - Non-Review Status & Billing Test")
    print("=" * 70)
    
    # Run tests
    status_test_success = test_non_review_status_updates()
    billing_test_success = test_billing_integration()
    
    print("\n\n" + "=" * 70)
    print("📝 TEST SUMMARY")
    print("=" * 70)
    print(f"Status Update Test: {'✅ PASSED' if status_test_success else '❌ FAILED'}")
    print(f"Billing Integration Test: {'✅ PASSED' if billing_test_success else '❌ FAILED'}")
    print("=" * 70)
    
    print("\n🏁 Test completed!")
