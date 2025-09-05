#!/usr/bin/env python3
"""
Demo script to run the Phase 1 Enhanced UI
This shows how to properly use the classes from phase1_enhanced_ui.py
"""

import tkinter as tk
from tkinter import ttk

def main():
    """Main function to launch the enhanced UI"""
    try:
        print("🚀 Starting Phase 1 Enhanced UI...")
        
        # Import the UI classes
        from phase1_enhanced_ui import (
            EnhancedTaskManagementTab,
            ResourceManagementTab,
            ACCFolderManagementTab,
            ReviewManagementTab,
            DocumentManagementTab,
            ProjectSetupTab,
            BEPDocumentTab,
            EIRDocumentTab,
            PIRDocumentTab,
        )
        
        # Create main window
        root = tk.Tk()
        root.title("BIM Project Management - Phase 1 Enhanced UI")
        root.geometry("1200x800")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create and add tabs
        print("📋 Creating Enhanced Task Management tab...")
        task_tab = EnhancedTaskManagementTab(notebook)
        
        print("👥 Creating Resource Management tab...")
        resource_tab = ResourceManagementTab(notebook)
        
        print("📁 Creating ACC Folder Management tab...")
        acc_tab = ACCFolderManagementTab(notebook)
        
        print("📋 Creating Review Management tab...")
        review_tab = ReviewManagementTab(notebook)

        # Add BEP / EIR / PIR top-level tabs per outline
        print("Adding BEP / EIR / PIR tabs...")
        bep_tab = BEPDocumentTab(notebook)
        eir_tab = EIRDocumentTab(notebook)
        pir_tab = PIRDocumentTab(notebook)
        
        print("📄 Creating Document Management tab...")
        doc_tab = DocumentManagementTab(notebook)
        
        print("🏗️ Creating Project Setup tab...")
        project_tab = ProjectSetupTab(notebook)
        
        # Start the UI
        print("✅ UI initialized successfully!")
        print("🖥️ Starting main loop...")
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install tkcalendar pandas pyodbc")
        
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

