# ui/tab_validation.py

from tkinter import ttk
from ui.ui_helpers import create_labeled_entry, create_horizontal_button_group
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

def build_validation_tab(tab, status_var):
    # --- Model Audit Section ---
    ttk.Label(tab, text="Model Validation", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_model_validation_path = create_labeled_entry(tab, "Model Folder Path:")
    CreateToolTip(entry_model_validation_path, "Path to the folder containing models to validate")

    def run_model_validation():
        update_status(status_var, "Running model validation...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Run Model Validation", run_model_validation)])

    # --- Naming Convention Check Section ---
    ttk.Label(tab, text="Check Naming Conventions", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_naming_standards_path = create_labeled_entry(tab, "Standards Reference Folder:")
    CreateToolTip(entry_naming_standards_path, "Folder containing naming convention rules")

    def check_naming_conventions():
        update_status(status_var, "Checking naming conventions...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Check Naming", check_naming_conventions)])

    # --- Asset Data Validation Section ---
    ttk.Label(tab, text="Asset Data Validation", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_asset_data_path = create_labeled_entry(tab, "Asset Data File:")
    CreateToolTip(entry_asset_data_path, "Path to asset data file for validation against model")

    def validate_asset_data():
        update_status(status_var, "Validating asset data...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Validate Asset Data", validate_asset_data)])
