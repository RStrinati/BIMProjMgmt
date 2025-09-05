#!/usr/bin/env python3
"""
Simple project selector test to verify projects are loading correctly
"""

import tkinter as tk
from tkinter import ttk
from database import get_projects

def main():
    root = tk.Tk()
    root.title("Project Selector Test")
    root.geometry("600x400")
    
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    ttk.Label(frame, text="Project Loading Test", font=('Arial', 16, 'bold')).pack(pady=10)
    
    # Load projects
    try:
        projects = get_projects()
        ttk.Label(frame, text=f"Found {len(projects)} projects in database:").pack(pady=5)
        
        # Show all projects
        text_widget = tk.Text(frame, height=10, width=60)
        text_widget.pack(pady=10, fill=tk.BOTH, expand=True)
        
        for i, (proj_id, proj_name) in enumerate(projects, 1):
            text_widget.insert(tk.END, f"{i}. ID: {proj_id} - Name: {proj_name}\n")
        
        text_widget.config(state=tk.DISABLED)
        
        # Dropdown test
        ttk.Label(frame, text="Select a project:").pack(pady=(10, 5))
        
        project_var = tk.StringVar()
        project_values = [f"{p[0]} - {p[1]}" for p in projects]
        
        project_combo = ttk.Combobox(frame, textvariable=project_var, values=project_values, width=50)
        project_combo.pack(pady=5)
        
        def on_select(event):
            selected = project_var.get()
            status_label.config(text=f"Selected: {selected}")
        
        project_combo.bind("<<ComboboxSelected>>", on_select)
        
        # Status
        status_label = ttk.Label(frame, text="No project selected", foreground="blue")
        status_label.pack(pady=10)
        
        if project_values:
            project_combo.set(project_values[0])
            status_label.config(text=f"Default: {project_values[0]}")
        
    except Exception as e:
        ttk.Label(frame, text=f"Error loading projects: {e}", foreground="red").pack(pady=10)
    
    # Close button
    ttk.Button(frame, text="Close", command=root.destroy).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
