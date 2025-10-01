"""
Quick Test for Date-Based Refresh Issues

This script will help diagnose why the manual refresh might be failing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_manual_refresh():
    """Test the manual refresh functionality"""
    
    print("🔧 Testing Manual Date-Based Refresh")
    print("=" * 40)
    
    try:
        # Import required modules
        from database import connect_to_db
        from review_management_service import ReviewManagementService
        
        # Connect to database
        print("📊 Connecting to database...")
        db_connection = connect_to_db()
        
        if not db_connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connected successfully")
        
        # Create review service
        print("🔄 Creating review service...")
        review_service = ReviewManagementService(db_connection)
        print("✅ Review service created successfully")
        
        # Test the refresh method directly
        project_id = 1  # Use project 1 as test
        print(f"📋 Testing refresh for project {project_id}...")
        
        # Call the comprehensive refresh method
        results = review_service.refresh_review_cycles_by_date(project_id)
        
        print(f"📝 Results received:")
        print(f"   Success: {results.get('success', 'NOT SET')}")
        print(f"   Reviews Updated: {results.get('reviews_updated', 'NOT SET')}")
        print(f"   Error: {results.get('error', 'NONE')}")
        print(f"   Message: {results.get('message', 'NO MESSAGE')}")
        
        # Check each component
        if 'project_kpis' in results:
            print(f"   Project KPIs: {len(results['project_kpis'])} items")
        else:
            print("   Project KPIs: NOT INCLUDED")
            
        if 'service_percentages' in results:
            print(f"   Service Percentages: {len(results['service_percentages'])} items")
        else:
            print("   Service Percentages: NOT INCLUDED")
        
        # Close database connection
        db_connection.close()
        
        return results.get('success', False)
        
    except Exception as e:
        print(f"❌ Error during manual refresh test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test each component individually"""
    
    print("\n🔍 Testing Individual Components")
    print("=" * 35)
    
    try:
        from database import connect_to_db
        from review_management_service import ReviewManagementService
        
        # Connect to database
        db_connection = connect_to_db()
        if not db_connection:
            print("❌ Failed to connect to database")
            return False
            
        review_service = ReviewManagementService(db_connection)
        project_id = 1
        
        # Test 1: Status update method
        print("1️⃣ Testing update_service_statuses_by_date...")
        status_result = review_service.update_service_statuses_by_date(project_id)
        print(f"   Result: {status_result}")
        
        # Test 2: Project KPIs method
        print("2️⃣ Testing get_project_review_kpis...")
        kpi_result = review_service.get_project_review_kpis(project_id)
        print(f"   Result: {type(kpi_result)} with {len(kpi_result) if kpi_result else 0} items")
        
        # Test 3: Service percentages
        print("3️⃣ Testing service percentage calculation...")
        services = review_service.get_project_services(project_id)
        print(f"   Found {len(services)} services")
        
        for i, service in enumerate(services[:2]):  # Test first 2 services
            service_id = service[0]
            percentage = review_service.calculate_service_review_completion_percentage(service_id)
            print(f"   Service {service_id}: {percentage}%")
        
        db_connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing individual components: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Diagnosing Date-Based Refresh Issues")
    print("=" * 50)
    
    # Test 1: Manual refresh
    test1_success = test_manual_refresh()
    
    # Test 2: Individual components
    test2_success = test_individual_components()
    
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 20)
    
    if test1_success:
        print("✅ Manual refresh working correctly")
    else:
        print("❌ Manual refresh has issues")
        
    if test2_success:
        print("✅ Individual components working correctly")
    else:
        print("❌ Individual components have issues")
        
    if test1_success and test2_success:
        print("\n🎯 CONCLUSION: System should be working")
        print("   The issue might be in the UI interaction or timing")
    else:
        print("\n⚠️ CONCLUSION: There are underlying issues to fix")