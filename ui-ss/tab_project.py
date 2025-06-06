# ui/tab_project.py

from tkinter import ttk
from ui.ui_helpers import create_labeled_entry, create_labeled_combobox, create_horizontal_button_group
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

# Sample project data
project_names = ["Project A", "Project B", "Project C"]

def build_project_tab(tab, status_var):
    # --- Project Selection Section ---
    ttk.Label(tab, text="Select Active Project", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, cmb_projects = create_labeled_combobox(tab, "Project:", project_names)
    CreateToolTip(cmb_projects, "Select from existing projects")

    def refresh_projects():
        update_status(status_var, "Project list refreshed")
        # Placeholder logic for refreshing list

    create_horizontal_button_group(tab, [("Refresh", refresh_projects)])

    # --- Project Details Section ---
    ttk.Label(tab, text="Project Details", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_proj_number = create_labeled_entry(tab, "Project Number:")
    _, entry_client = create_labeled_entry(tab, "Client Name:")
    _, entry_architect = create_labeled_entry(tab, "Architect:")
    CreateToolTip(entry_proj_number, "Enter the official project number")
    CreateToolTip(entry_client, "Enter the client name")
    CreateToolTip(entry_architect, "Enter the architect's name")

    # --- Folder Path Section ---
    ttk.Label(tab, text="Linked Folder Paths", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_model_path = create_labeled_entry(tab, "Model Folder Path:")
    _, entry_acc_path = create_labeled_entry(tab, "ACC Export Folder:")
    _, entry_review_path = create_labeled_entry(tab, "Review Folder:")
    CreateToolTip(entry_model_path, "Directory for Revit models")
    CreateToolTip(entry_acc_path, "Folder containing ACC exports")
    CreateToolTip(entry_review_path, "Folder for review documentation")

    # --- Create Project Section ---
    def create_project():
        update_status(status_var, f"Created new project: {entry_proj_number.get()}")
        # Placeholder logic for creating a project

    create_horizontal_button_group(tab, [("Create Project", create_project)])
