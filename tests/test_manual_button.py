"""
Manual Button Test for Date-Based Refresh

This will simulate clicking the manual button to see if there are issues
with the comprehensive refresh when called manually vs. automatically.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_manual_button_scenario():
    """Simulate what happens when the manual button is clicked"""
    
    print("🔘 Testing Manual Button Scenario")
    print("=" * 40)
    
    try:
        from database import get_db_connection
        from review_management_service import ReviewManagementService
        
        # Connect to database
        with get_db_connection() as db_connection:
            # Create review service
            review_service = ReviewManagementService(db_connection)
            project_id = 1  # Test with project 1
            
            print(f"🔄 Testing manual refresh for project {project_id}...")
            
            # This is exactly what the UI button calls
            results = review_service.refresh_review_cycles_by_date(project_id)
            
            print(f"📋 Manual refresh results:")
            print(f"   Type: {type(results)}")
            
            for key, value in results.items():
                print(f"   {key}: {value}")
            
            # Check success specifically
            success = results.get('success', 'NOT SET')
            reviews_updated = results.get('reviews_updated', 'NOT SET')
            error = results.get('error', 'NONE')
            
            print(f"\n🎯 Key Results:")
            print(f"   Success: {success}")
            print(f"   Reviews Updated: {reviews_updated}")
            print(f"   Error: {error}")
            
            # Simulate UI logic
            if results.get('success', False):
                print("✅ UI would show success message")
            else:
                print(f"❌ UI would show error: {results.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in manual button test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Manual Button Test")
    print("=" * 25)
    
    success = test_manual_button_scenario()
    
    if success:
        print("\n✅ Manual button test completed")
    else:
        print("\n❌ Manual button test failed")