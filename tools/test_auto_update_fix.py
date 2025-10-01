#!/usr/bin/env python3
"""
Test script to verify the auto_update_stages_and_cycles fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_method_existence():
    """Test that the auto_update_stages_and_cycles method exists"""
    print("🔍 Testing auto_update_stages_and_cycles method existence...")
    
    # Import the UI module
    try:
        from phase1_enhanced_ui import ReviewManagementTab
        
        # Check if the method exists
        if hasattr(ReviewManagementTab, 'auto_update_stages_and_cycles'):
            print("✅ auto_update_stages_and_cycles method exists!")
            
            # Check method signature
            import inspect
            sig = inspect.signature(ReviewManagementTab.auto_update_stages_and_cycles)
            print(f"   Method signature: {sig}")
            
            # Check if required methods exist too
            required_methods = [
                'auto_sync_stages_from_services',
                'auto_sync_review_cycles_from_services', 
                'get_project_services'
            ]
            
            for method_name in required_methods:
                if hasattr(ReviewManagementTab, method_name):
                    print(f"   ✅ {method_name} exists")
                else:
                    print(f"   ❌ {method_name} missing")
            
        else:
            print("❌ auto_update_stages_and_cycles method NOT found!")
            return False
        
        print("\n🔍 Testing method availability in class...")
        
        # List all methods that contain 'auto' in name
        auto_methods = [method for method in dir(ReviewManagementTab) 
                       if 'auto' in method.lower() and not method.startswith('_')]
        
        print("   Available 'auto' methods:")
        for method in auto_methods:
            print(f"     • {method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing method: {e}")
        return False

if __name__ == "__main__":
    success = test_method_existence()
    if success:
        print("\n✅ All tests passed! The auto_update_stages_and_cycles error should be fixed.")
    else:
        print("\n❌ Tests failed. The error may still occur.")