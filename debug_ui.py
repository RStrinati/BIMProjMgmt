#!/usr/bin/env python3
"""
Debug version of run_enhanced_ui.py with more detailed error tracking
"""

import tkinter as tk
from tkinter import ttk
import traceback

def main():
    """Main function to launch the enhanced UI with debug info"""
    try:
        print("🚀 Starting Phase 1 Enhanced UI (Debug Mode)...")
        
        # Test database connection first
        print("🔍 Testing database connection...")
        from database import get_projects
        projects = get_projects()
        print(f"✅ Database connected successfully. Found {len(projects)} projects.")
        
        # Import the UI classes
        print("📥 Importing UI classes...")
        from phase1_enhanced_ui import (
            EnhancedTaskManagementTab,
            ResourceManagementTab, 
            ACCFolderManagementTab,
            ReviewManagementTab,
            DocumentManagementTab,
            ProjectSetupTab
        )
        print("✅ UI classes imported successfully.")
        
        # Create main window
        print("🪟 Creating main window...")
        root = tk.Tk()
        root.title("BIM Project Management - Phase 1 Enhanced")
        root.geometry("1400x900")
        root.state('zoomed')  # Maximize window
        
        # Create notebook for tabs
        print("📒 Creating notebook...")
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs with individual error handling
        try:
            print("📋 Creating Enhanced Task Management tab...")
            task_tab = EnhancedTaskManagementTab(notebook)
            print("✅ Task Management tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating Task Management tab: {e}")
            traceback.print_exc()
        
        try:
            print("👥 Creating Resource Management tab...")
            resource_tab = ResourceManagementTab(notebook)
            print("✅ Resource Management tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating Resource Management tab: {e}")
            traceback.print_exc()
        
        try:
            print("📁 Creating ACC Folder Management tab...")
            acc_tab = ACCFolderManagementTab(notebook)
            print("✅ ACC Folder Management tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating ACC Folder Management tab: {e}")
            traceback.print_exc()
        
        try:
            print("📋 Creating Review Management tab...")
            review_tab = ReviewManagementTab(notebook)
            print("✅ Review Management tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating Review Management tab: {e}")
            traceback.print_exc()
        
        try:
            print("📄 Creating Document Management tab...")
            doc_tab = DocumentManagementTab(notebook)
            print("✅ Document Management tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating Document Management tab: {e}")
            traceback.print_exc()
        
        try:
            print("🏗️ Creating Project Setup tab...")
            project_tab = ProjectSetupTab(notebook)
            print("✅ Project Setup tab created successfully.")
        except Exception as e:
            print(f"❌ Error creating Project Setup tab: {e}")
            traceback.print_exc()
        
        # Start the UI
        print("✅ UI initialized successfully!")
        print("🖥️ Starting main loop...")
        root.mainloop()
        print("🔚 Application closed.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install tkcalendar pandas pyodbc")
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
