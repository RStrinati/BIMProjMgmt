# ui/base_layout.py

import tkinter as tk
from tkinter import ttk

def build_main_ui():
    root = tk.Tk()
    root.title("Project & Review Management System")
    root.geometry("1280x720")

    # --- Status bar variable ---
    status_var = tk.StringVar()
    status_var.set("Ready")

    # --- Tab notebook ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Placeholder tabs (content will come from submodules)
    tab_project = ttk.Frame(notebook)
    tab_imports = ttk.Frame(notebook)
    tab_review = ttk.Frame(notebook)
    tab_validation = ttk.Frame(notebook)

    notebook.add(tab_project, text="Project Setup")
    notebook.add(tab_imports, text="Data Imports")
    notebook.add(tab_review, text="Review Management")
    notebook.add(tab_validation, text="Validation & Results")

    # --- Status bar at bottom ---
    status_bar = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor="w")
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    return root, notebook, {
        "Project Setup": tab_project,
        "Data Imports": tab_imports,
        "Review Management": tab_review,
        "Validation & Results": tab_validation
    }, status_var
