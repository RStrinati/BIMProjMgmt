#!/usr/bin/env python3
"""
Quick UI test to check if tabs load without errors
"""

import tkinter as tk
from tkinter import ttk
from phase1_enhanced_ui import ProjectSetupTab, EnhancedTaskManagementTab, ResourceManagementTab, ReviewManagementTab, ReviewManagementTab, ACCFolderManagementTab, DocumentManagementTab, ProjectBookmarksTab

def test_ui():
    root = tk.Tk()
    root.title("UI Test")
    root.geometry("800x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    try:
        print("Creating Project Setup tab...")
        ProjectSetupTab(notebook)
        print("✅ Project Setup tab created successfully")

        print("Creating Enhanced Task Management tab...")
        EnhancedTaskManagementTab(notebook)
        print("✅ Enhanced Task Management tab created successfully")

        print("Creating Resource Management tab...")
        ResourceManagementTab(notebook)
        print("✅ Resource Management tab created successfully")

        print("Creating Review Management tab...")
        ReviewManagementTab(notebook)
        print("✅ Review Management tab created successfully")

        print("Creating Project Bookmarks tab...")
        ProjectBookmarksTab(notebook)
        print("✅ Project Bookmarks tab created successfully")

        # Test that we can access the frames
        tabs = notebook.tabs()
        if tabs:
            print(f"✅ Notebook has {len(tabs)} tab(s)")
        else:
            print("❌ No tabs found")

    except Exception as e:
        print(f"❌ Error creating UI: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Don't show the window, just test creation
    root.destroy()
    return True

if __name__ == "__main__":
    success = test_ui()
    print("UI test result:", "PASSED" if success else "FAILED")