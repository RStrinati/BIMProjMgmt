# ui/tab_validation.py

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tools.naming_validator import validate_files



from ui.ui_helpers import (
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

from database import (
    get_projects,
    get_project_details,
    get_project_folders,
    get_last_export_date,
    get_project_health_files,
    get_control_file,
    set_control_file,
)
from process_ifc import process_folder

def build_validation_tab(tab, status_var):
    # --- Project Selection & Control File ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(tab, "Project:", projects)
    _, cmb_control = create_labeled_combobox(tab, "Control File:", [])

    def load_project_data(event=None):
        if " - " not in cmb_projects.get():
            return
        pid, name = cmb_projects.get().split(" - ", 1)
        files = get_project_health_files(int(pid))
        cmb_control['values'] = files if files else ["No files"]
        current = get_control_file(pid)
        if files:
            cmb_control.current(0)
            if current and current in files:
                cmb_control.set(current)
        else:
            cmb_control.set("No files")
        _, ifc_path = get_project_folders(pid)
        entry_ifc_folder.delete(0, tk.END)
        entry_ifc_folder.insert(0, ifc_path or "")

    cmb_projects.bind("<<ComboboxSelected>>", load_project_data)

    def save_control_file():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        fname = cmb_control.get()
        if not fname or fname == "No files":
            messagebox.showerror("Error", "Select a valid control file")
            return
        if set_control_file(pid, fname):
            update_status(status_var, f"Control file saved: {fname}")
        else:
            messagebox.showerror("Error", "Failed to save control file")

    create_horizontal_button_group(tab, [("Save Control File", save_control_file)])
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

    # Entry for Regex JSON file
    _, entry_naming_json = create_labeled_entry(tab, "Regex JSON File:")
    CreateToolTip(entry_naming_json, "Select the JSON file containing regex naming rules")

    def browse_naming_json():
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            entry_naming_json.delete(0, tk.END)
            entry_naming_json.insert(0, path)

    def check_naming_conventions():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return

        project_id_str, project_name = cmb_projects.get().split(" - ", 1)
        project_id = int(project_id_str)

        json_path = entry_naming_json.get().strip()

        if not os.path.isfile(json_path):
            messagebox.showerror("Error", "Select a valid naming_conventions.json file")
            return

        project_files = get_project_health_files(project_id)
        if not project_files:
            messagebox.showinfo("No Files", "No project files found")
            return

        # Corrected location and use of project_name
        results = validate_files(project_id, project_files, json_path, project_name)


        if results:
            result_msg = "\n".join([f"{file}: {reason}" for file, reason in results])
            messagebox.showwarning("Naming Issues Found", result_msg)
        else:
            messagebox.showinfo("Success", "All files follow the naming convention!")

        update_status(status_var, "Naming convention check complete.")


    create_horizontal_button_group(tab, [
        ("Browse JSON", browse_naming_json),
        ("Check Naming", check_naming_conventions),
    ])

    # --- Asset Data Validation Section ---
    ttk.Label(tab, text="Asset Data Validation", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_asset_data_path = create_labeled_entry(tab, "Asset Data File:")
    CreateToolTip(entry_asset_data_path, "Path to asset data file for validation against model")

    def validate_asset_data():
        update_status(status_var, "Validating asset data...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Validate Asset Data", validate_asset_data)])

    # --- IFC Processing Section ---
    ttk.Label(tab, text="IFC Processing", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_ifc_folder = create_labeled_entry(tab, "IFC Folder:")

    def browse_ifc_folder():
        path = filedialog.askdirectory()
        if path:
            entry_ifc_folder.delete(0, tk.END)
            entry_ifc_folder.insert(0, path)

    def process_ifc():
        folder = entry_ifc_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Select a valid IFC folder")
            return
        process_folder(folder)
        last = get_last_export_date()
        export_label.config(text=f"Last Export Date: {last}")
        update_status(status_var, f"Last Export: {last}")

    create_horizontal_button_group(
        tab,
        [
            ("Browse IFC", browse_ifc_folder),
            ("Process IFC", process_ifc),
        ],
    )

    export_label = ttk.Label(tab, text="Last Export Date: Not available")
    export_label.pack(padx=10, pady=5, anchor="w")

    if projects:
        load_project_data()

