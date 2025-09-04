#!/usr/bin/env python3
"""
Test script to debug the UI cycle display issue
"""

import sqlite3
import os
import sys
from datetime import datetime

def test_ui_cycle_loading():
    """Test loading cycles in the UI context"""
    print("🔧 Testing UI cycle loading...")
    
    try:
        # Use the test database we created
        conn = sqlite3.connect("test_project_data.db")
        
        from review_management_service import ReviewManagementService
        
        # Initialize the service
        service = ReviewManagementService(conn)
        
        # Test getting project services (what the UI does)
        project_id = 1
        services = service.get_project_services(project_id)
        print(f"✅ Found {len(services)} services for project {project_id}")
        
        # Test loading cycles for each service (what load_project_schedule does)
        for service_data in services:
            if service_data['unit_type'] == 'review':
                print(f"\n📋 Service: {service_data['service_name']}")
                print(f"   Service ID: {service_data['service_id']}")
                print(f"   Unit Type: {service_data['unit_type']}")
                
                reviews = service.get_service_reviews(service_data['service_id'])
                print(f"   Found {len(reviews)} review cycles:")
                
                for review in reviews:
                    print(f"      🔄 Cycle {review['cycle_no']}: {review['planned_date']} → {review['due_date']} ({review['status']})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ UI cycle loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_initialization():
    """Test the actual UI component that shows cycles"""
    print("\n🖥️ Testing UI initialization...")
    
    try:
        # First test if we can import the UI components
        from phase1_enhanced_ui import ProjectManagementUI
        
        print("✅ Successfully imported ProjectManagementUI")
        
        # Try to create a minimal UI instance for testing (without showing it)
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Use the test database
        conn = sqlite3.connect("test_project_data.db")
        
        # Create the UI instance
        ui = ProjectManagementUI(root)
        
        # Test if we can set the database connection manually
        if hasattr(ui, 'review_service'):
            ui.review_service.db = conn
            ui.review_service.cursor = conn.cursor()
            print("✅ Database connection set")
        
        # Test project loading
        ui.current_project_id = 1
        print("✅ Project ID set")
        
        # Test schedule loading
        if hasattr(ui, 'load_project_schedule'):
            ui.load_project_schedule()
            print("✅ Schedule loading method called")
            
            # Check if any items were added to the schedule tree
            if hasattr(ui, 'schedule_tree'):
                items = ui.schedule_tree.get_children()
                print(f"✅ Schedule tree has {len(items)} items")
                
                # Print the items
                for item in items:
                    values = ui.schedule_tree.item(item)['values']
                    print(f"   📅 {values}")
        
        root.destroy()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ UI initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the debugging tests"""
    print("🔍 Debugging Cycle Display Issue")
    print("=" * 40)
    
    # First test the data loading
    success1 = test_ui_cycle_loading()
    
    # Then test the UI initialization
    success2 = test_ui_initialization()
    
    if success1 and success2:
        print("\n🎉 Both tests passed! The issue might be elsewhere.")
    else:
        print("\n❌ One or more tests failed. Found the issue!")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)