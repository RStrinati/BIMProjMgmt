# app.py

import tkinter as tk
from tkinter import ttk
from ui-ss.tab_project import build_project_tab
from ui-ss.tab_data_imports import build_data_imports_tab
from ui-ss.tab_review import build_review_tab
from ui-ss.tab_validation import build_validation_tab
from ui-ss.status_bar import update_status

# --- Main App Window ---
def main():
    root = tk.Tk()
    root.title("BIM Project Management")
    root.geometry("1200x800")

    # --- Status Bar Variable ---
    status_var = tk.StringVar()
    update_status(status_var, "Ready")

    # --- Notebook Setup ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Tabs ---
    tab_project = ttk.Frame(notebook)
    tab_data = ttk.Frame(notebook)
    tab_review = ttk.Frame(notebook)
    tab_validation = ttk.Frame(notebook)

    notebook.add(tab_project, text="Project Setup")
    notebook.add(tab_data, text="Data Imports")
    notebook.add(tab_review, text="Review Management")
    notebook.add(tab_validation, text="Validation & Results")

    # --- Build UI Sections ---
    build_project_tab(tab_project, status_var)
    build_data_imports_tab(tab_data, status_var)
    build_review_tab(tab_review, status_var)
    build_validation_tab(tab_validation, status_var)

    # --- Status Bar ---
    status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w")
    status_bar.pack(fill="x", side="bottom")

    root.mainloop()

if __name__ == "__main__":
    main()
