# ui/base_layout.py

import tkinter as tk
from tkinter import ttk
from .ui_helpers import create_scrollable_frame

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
    tab_project_container = ttk.Frame(notebook)
    tab_imports_container = ttk.Frame(notebook)
    tab_review_container = ttk.Frame(notebook)
    tab_validation_container = ttk.Frame(notebook)

    # Make each tab scrollable and return the inner frame used by builders
    tab_project = create_scrollable_frame(tab_project_container)
    tab_imports = create_scrollable_frame(tab_imports_container)
    tab_review = create_scrollable_frame(tab_review_container)
    tab_validation = create_scrollable_frame(tab_validation_container)

    notebook.add(tab_project_container, text="Project Setup")
    notebook.add(tab_imports_container, text="Data Imports")
    notebook.add(tab_review_container, text="Review Management")
    notebook.add(tab_validation_container, text="Validation & Results")

    # --- Status bar at bottom ---
    status_bar = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor="w")
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    return root, notebook, {
        "Project Setup": tab_project,
        "Data Imports": tab_imports,
        "Review Management": tab_review,
        "Validation & Results": tab_validation
    }, status_var
