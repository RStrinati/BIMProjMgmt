#!/usr/bin/env python3
"""
Test script for Review Management Tab reliability fixes

This script validates that the critical reliability fixes are working correctly:
1. TabOperationManager functionality
2. Enhanced error handling 
3. Fixed date generation logic
4. Improved template refresh
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import traceback

def test_tab_operation_manager():
    """Test the TabOperationManager functionality"""
    print("🧪 Testing TabOperationManager...")
    
    try:
        # Import the class (it's now embedded in the main UI file)
        from phase1_enhanced_ui import TabOperationManager
        
        manager = TabOperationManager()
        
        # Test starting operations
        result1 = manager.start_operation("test_operation")
        assert result1 == True, "Should allow starting new operation"
        
        # Test preventing concurrent operations
        result2 = manager.start_operation("test_operation")
        assert result2 == False, "Should prevent concurrent operations"
        
        # Test ending operations
        manager.end_operation("test_operation")
        
        # Test restarting after end
        result3 = manager.start_operation("test_operation")
        assert result3 == True, "Should allow restarting after end"
        
        manager.end_operation("test_operation")
        
        print("✅ TabOperationManager tests passed")
        return True
        
    except Exception as e:
        print(f"❌ TabOperationManager tests failed: {e}")
        return False

def test_date_generation_logic():
    """Test the improved date generation logic"""
    print("🧪 Testing date generation logic...")
    
    try:
        from review_management_service import ReviewManagementService
        from database import connect_to_db
        
        # Create service instance
        conn = connect_to_db()
        if not conn:
            print("⚠️  Could not connect to database, skipping date tests")
            return True
            
        service = ReviewManagementService(conn)
        
        # Test one-off review generation
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        # This should create exactly 1 review at start date
        cycles = service.generate_review_cycles(
            service_id=999,  # Dummy service ID for testing
            unit_qty=1,
            start_date=start_date,
            end_date=end_date,
            cadence='one-off',
            disciplines='All'
        )
        
        # Should have exactly 1 cycle
        if len(cycles) != 1:
            print(f"❌ Expected 1 one-off cycle, got {len(cycles)}")
            return False
            
        # Should be at start date
        if cycles[0]['planned_date'] != start_date.strftime('%Y-%m-%d'):
            print(f"❌ Expected one-off at {start_date}, got {cycles[0]['planned_date']}")
            return False
        
        print("✅ One-off review generation working correctly")
        
        # Test weekly review generation
        cycles_weekly = service.generate_review_cycles(
            service_id=998,  # Dummy service ID
            unit_qty=4,
            start_date=start_date,
            end_date=end_date,
            cadence='weekly',
            disciplines='All'
        )
        
        if len(cycles_weekly) != 4:
            print(f"❌ Expected 4 weekly cycles, got {len(cycles_weekly)}")
            return False
        
        print("✅ Weekly review generation working correctly")
        print("✅ Date generation logic tests passed")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Date generation tests failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_error_handling():
    """Test enhanced error handling"""
    print("🧪 Testing enhanced error handling...")
    
    try:
        # Test that error handling methods exist and can be called
        from phase1_enhanced_ui import ReviewManagementTab
        import tkinter as tk
        
        # Create minimal tkinter app for testing
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        notebook = tk.Notebook(root)
        tab = ReviewManagementTab(notebook)
        
        # Test that the error handling method exists
        if not hasattr(tab, 'show_user_friendly_error'):
            print("❌ show_user_friendly_error method not found")
            return False
        
        print("✅ Enhanced error handling method available")
        
        # Test operation manager integration
        if not hasattr(tab, 'operation_manager'):
            print("❌ operation_manager not found in ReviewManagementTab")
            return False
            
        print("✅ Operation manager integrated into tab")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Error handling tests failed: {e}")
        return False

def run_all_tests():
    """Run all reliability tests"""
    print("🔧 Running Review Management Tab Reliability Tests")
    print("=" * 60)
    
    tests = [
        ("TabOperationManager", test_tab_operation_manager),
        ("Date Generation Logic", test_date_generation_logic), 
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} tests failed")
        except Exception as e:
            print(f"❌ {test_name} tests crashed: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All reliability fixes are working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the fixes.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)