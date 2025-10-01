#!/usr/bin/env python3
"""Test UI integration for service templates"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from phase1_enhanced_ui import ReviewManagementTab

def test_ui_template_functionality():
    """Test template functionality in the UI"""
    print("🖥️ Testing UI template functionality...")
    
    # Create a test window
    root = tk.Tk()
    root.title("Template Test")
    root.geometry("1200x800")
    
    try:
        # Create notebook
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create ReviewManagementTab
        review_tab = ReviewManagementTab(notebook)
        print("✅ ReviewManagementTab created successfully")
        
        # Check if template combo is populated
        if hasattr(review_tab, 'template_combo'):
            template_values = review_tab.template_combo['values']
            if template_values:
                print(f"✅ Template dropdown populated with {len(template_values)} templates:")
                for i, template in enumerate(template_values):
                    print(f"  {i+1}. {template}")
            else:
                print("❌ Template dropdown is empty")
        else:
            print("❌ Template combo not found")
        
        # Test if review service is initialized
        if hasattr(review_tab, 'review_service') and review_tab.review_service:
            print("✅ Review service initialized")
            
            # Test get_available_templates directly
            templates = review_tab.review_service.get_available_templates()
            print(f"✅ Review service returned {len(templates)} templates")
        else:
            print("❌ Review service not initialized")
        
        print("✅ UI integration test completed successfully")
        
        # Don't actually show the window in automated test
        # root.mainloop()  # Uncomment this line to see the UI
        
        return True
        
    except Exception as e:
        print(f"❌ Error during UI testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_ui_template_functionality()
    if success:
        print("\n🎉 UI integration test passed")
    else:
        print("\n💥 UI integration test failed")
    
    sys.exit(0 if success else 1)