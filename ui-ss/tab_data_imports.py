# ui/tab_data_imports.py

from tkinter import ttk
from ui.ui_helpers import create_labeled_entry, create_horizontal_button_group
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

def build_data_imports_tab(tab, status_var):
    # --- Revit Audit Import Section ---
    ttk.Label(tab, text="Revit Health Check JSON Import", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_json_path = create_labeled_entry(tab, "Audit JSON Folder:")
    CreateToolTip(entry_json_path, "Folder where exported Revit audit JSONs are saved")

    def import_revit_audit():
        update_status(status_var, "Revit audit import started")
        # Placeholder for actual logic

    create_horizontal_button_group(tab, [("Import Audit JSONs", import_revit_audit)])

    # --- ACC CSV Import Section ---
    ttk.Label(tab, text="ACC Export CSV Import", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_acc_folder = create_labeled_entry(tab, "ACC CSV Folder:")
    CreateToolTip(entry_acc_folder, "Select the folder containing weekly ACC CSV exports")

    def import_acc_csv():
        update_status(status_var, "ACC CSV import started")
        # Placeholder for actual logic

    create_horizontal_button_group(tab, [("Import ACC CSVs", import_acc_csv)])

    # --- Clash CSV Import Section ---
    ttk.Label(tab, text="Clash CSV Import", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_clash_folder = create_labeled_entry(tab, "Clash CSV Folder:")
    CreateToolTip(entry_clash_folder, "Folder path containing Navisworks clash detection results")

    def import_clash_csv():
        update_status(status_var, "Clash CSV import started")
        # Placeholder for actual logic

    create_horizontal_button_group(tab, [("Import Clash CSVs", import_clash_csv)])
