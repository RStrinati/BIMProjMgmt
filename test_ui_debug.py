#!/usr/bin/env python3
"""
Debug script to test UI project loading
"""

import tkinter as tk
from tkinter import ttk
from database import get_projects

def test_projects():
    """Test project loading in a simple UI"""
    try:
        print("🔍 Testing project loading...")
        
        # Test database connection
        projects = get_projects()
        print(f"✅ Found {len(projects)} projects:")
        for p in projects:
            print(f"  - {p[0]} - {p[1]}")
        
        # Test UI creation
        print("🖼️ Creating test UI...")
        root = tk.Tk()
        root.title("Project Test")
        root.geometry("400x300")
        
        # Create project dropdown
        frame = ttk.Frame(root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Projects:").pack(pady=5)
        
        project_var = tk.StringVar()
        project_combo = ttk.Combobox(frame, textvariable=project_var, width=50)
        project_combo.pack(pady=5)
        
        # Populate with projects
        project_values = [f"{p[0]} - {p[1]}" for p in projects]
        project_combo['values'] = project_values
        
        if project_values:
            project_combo.set(project_values[0])
        
        # Status label
        status_label = ttk.Label(frame, text=f"Loaded {len(projects)} projects successfully")
        status_label.pack(pady=10)
        
        # Close button
        ttk.Button(frame, text="Close", command=root.destroy).pack(pady=10)
        
        print("✅ UI created successfully!")
        print("🖥️ Starting UI...")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_projects()
