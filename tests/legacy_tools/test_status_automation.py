#!/usr/bin/env python3
"""
Test Status Automation System

This script tests the new automatic status update functionality for services and reviews.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from database_pool import get_db_connection, get_db_connection
from review_management_service import ReviewManagementService

def test_status_automation():
    """Test the automatic status updates"""
    print("🧪 Testing Automatic Status Update System")
    print("=" * 50)
    
    try:
        # Connect to database
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            
            # Test with a sample project (assumes project ID 1 exists)
            project_id = 1
            
            print(f"📊 Testing status automation for project {project_id}")
            
            # 1. Test date-based status updates
            print("\n1. Testing date-based status updates...")
            update_results = service.update_service_statuses_by_date(project_id)
            print(f"   Reviews updated: {update_results.get('updated_count', 0)}")
            if update_results.get('error'):
                print(f"   ❌ Error: {update_results['error']}")
            
            # 2. Test overall status calculation
            print("\n2. Testing overall status calculation...")
            overall_status = service.calculate_overall_review_status(project_id)
            print(f"   Overall Status: {overall_status.get('overall_status', 'Unknown')}")
            print(f"   Summary: {overall_status.get('status_summary', 'No summary')}")
            print(f"   Progress: {overall_status.get('progress_percentage', 0):.1f}%")
            print(f"   Total Reviews: {overall_status.get('total_reviews', 0)}")
            print(f"   Completed: {overall_status.get('completed_reviews', 0)}")
            print(f"   In Progress: {overall_status.get('in_progress_reviews', 0)}")
            print(f"   Planned: {overall_status.get('planned_reviews', 0)}")
            
            # 3. Test service progress updates
            print("\n3. Testing service progress updates...")
            services = service.get_project_services(project_id)
            services_updated = 0
            for svc in services[:3]:  # Test first 3 services
                service_id = svc['service_id']
                if service.update_service_progress_from_reviews(service_id):
                    services_updated += 1
                    print(f"   ✅ Updated service {service_id} progress")
            print(f"   Services updated: {services_updated}")
            
            # 4. Test comprehensive refresh
            print("\n4. Testing comprehensive status refresh...")
            refresh_results = service.refresh_all_project_statuses(project_id)
            print(f"   📋 Reviews updated: {refresh_results.get('reviews_updated', 0)}")
            print(f"   🔧 Services updated: {refresh_results.get('services_updated', 0)}")
            print(f"   📊 Final status: {refresh_results.get('overall_status', {}).get('status_summary', 'Unknown')}")
            
            if refresh_results.get('errors'):
                print(f"   ❌ Errors encountered:")
                for error in refresh_results['errors']:
                    print(f"      - {error}")
            
            print("\n✅ Status automation tests completed successfully!")
            return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_billing_integration():
    """Test how status updates affect billing calculations"""
    print("\n💰 Testing Billing Integration")
    print("=" * 30)
    
    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            project_id = 1  # Test project
            
            # Get service progress summary
            progress_summary = service.get_service_progress_summary(project_id)
            
            print(f"Service billing status for project {project_id}:")
            print(f"{'Service':<30} {'Progress':<10} {'Billed':<12} {'Remaining':<12}")
            print("-" * 70)
            
            for svc in progress_summary[:5]:  # Show first 5 services
                print(f"{svc['service_name'][:28]:<30} "
                      f"{svc['progress_pct']:>7.1f}% "
                      f"${svc['billed_amount']:>10,.0f} "
                      f"${svc['remaining_amount']:>10,.0f}")
            
            total_billed = sum(s['billed_amount'] for s in progress_summary)
            total_remaining = sum(s['remaining_amount'] for s in progress_summary)
            
            print("-" * 70)
            print(f"{'TOTALS':<30} {'':>10} ${total_billed:>10,.0f} ${total_remaining:>10,.0f}")
            
            print("\n✅ Billing integration test completed!")
            return True
        
    except Exception as e:
        print(f"❌ Error during billing test: {e}")
        return False

if __name__ == "__main__":
    print("🔄 BIM Project Management - Status Automation Test")
    print("=" * 60)
    
    success = test_status_automation()
    if success:
        test_billing_integration()
    
    print("\n🏁 Test completed!")