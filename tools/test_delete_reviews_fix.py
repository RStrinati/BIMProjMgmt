#!/usr/bin/env python3
"""
Test script to verify the delete_all_project_reviews method
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from review_management_service import ReviewManagementService

def test_delete_all_reviews_method():
    """Test that the delete_all_project_reviews method exists and has correct signature"""
    print("🔍 Testing delete_all_project_reviews method...")
    
    # Test method existence
    if hasattr(ReviewManagementService, 'delete_all_project_reviews'):
        print("✅ delete_all_project_reviews method exists!")
        
        # Check method signature
        import inspect
        sig = inspect.signature(ReviewManagementService.delete_all_project_reviews)
        print(f"   Method signature: {sig}")
        
        # Test with database connection
        with get_db_connection() as conn:
        if conn is None:
            print("❌ Failed to connect to database")
            return False
        
        try:
            service = ReviewManagementService(conn)
            
            # Test method with a non-existent project (should not fail)
            result = service.delete_all_project_reviews(999999)  # Very high ID unlikely to exist
            
            print(f"   Test result: {result}")
            
            # Check expected return structure
            expected_keys = ['reviews_deleted', 'services_deleted', 'success']
            if all(key in result for key in expected_keys):
                print("✅ Method returns correct structure")
                return True
            else:
                print("❌ Method return structure incorrect")
                return False
                
        except Exception as e:
            print(f"❌ Error testing method: {e}")
            return False
        finally:
    else:
        print("❌ delete_all_project_reviews method NOT found!")
        return False

def list_available_delete_methods():
    """List all delete-related methods in ReviewManagementService"""
    print("\n🔍 Available delete methods in ReviewManagementService:")
    
    delete_methods = [method for method in dir(ReviewManagementService) 
                     if 'delete' in method.lower() and not method.startswith('_')]
    
    for method in delete_methods:
        print(f"   • {method}")
    
    if not delete_methods:
        print("   No delete methods found")

if __name__ == "__main__":
    success = test_delete_all_reviews_method()
    list_available_delete_methods()
    
    if success:
        print("\n✅ All tests passed! The delete_all_project_reviews error should be fixed.")
    else:
        print("\n❌ Tests failed. The error may still occur.")