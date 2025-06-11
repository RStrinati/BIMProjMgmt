# ui/tab_data_imports.py

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ideate_health_exporter import export_health_checks_to_sql
from database import log_acc_import, get_project_health_files, set_control_file



from ui.ui_helpers import (
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip
from database import (
    get_projects,
    save_acc_folder_path,
    get_acc_folder_path,
    get_acc_import_logs,
)

from acc_handler import run_acc_import
from rvt_health_importer import import_health_data

def build_data_imports_tab(tab, status_var):
    # --- Project Selection ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(tab, "Project:", projects)
    CreateToolTip(cmb_projects, "Project for ACC data import")

    def load_project_details(event=None):
        if " - " not in cmb_projects.get():
            return
        pid = cmb_projects.get().split(" - ")[0]
        folder = get_acc_folder_path(pid)
        entry_data_export.delete(0, tk.END); entry_data_export.insert(0, folder or "")
        log_list.delete(0, tk.END)
        logs = get_acc_import_logs(pid)
        if logs:
            for folder_name, date, _ in logs:
                log_list.insert(tk.END, f"✅ {folder_name} @ {date.strftime('%Y-%m-%d %H:%M')}")
        else:
            log_list.insert(tk.END, "No previous ACC imports found.")

    cmb_projects.bind("<<ComboboxSelected>>", load_project_details)
    if projects:
        load_project_details()
    # --- Revit Audit Import Section ---
    ttk.Label(tab, text="Revit Health Check JSON Import", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_json_path = create_labeled_entry(tab, "Audit JSON Folder:")
    CreateToolTip(entry_json_path, "Folder where exported Revit audit JSONs are saved")

    # --- Control Model Selection ---
    ttk.Label(tab, text="Set Control Model File", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    control_file_var = tk.StringVar()
    cmb_control_file = ttk.Combobox(tab, textvariable=control_file_var, width=60)
    cmb_control_file.pack(padx=10, pady=5, anchor="w")
    CreateToolTip(cmb_control_file, "Select the .rvt file to be used as the control model")

    def load_control_files(event=None):
        if " - " not in cmb_projects.get():
            return
        project_id = int(cmb_projects.get().split(" - ")[0])
        files = get_project_health_files(project_id)
        cmb_control_file["values"] = files
        if files:
            cmb_control_file.current(0)

    def save_control_file():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        project_id = int(cmb_projects.get().split(" - ")[0])
        selected_file = control_file_var.get()
        if not selected_file:
            messagebox.showerror("Error", "Select a control model file")
            return
        success = set_control_file(project_id, selected_file)
        if success:
            update_status(status_var, f"✅ Control model saved: {selected_file}")
        else:
            messagebox.showerror("Error", "Failed to save control model")

    # Link dropdown refresh to project change
    cmb_projects.bind("<<ComboboxSelected>>", lambda e: [load_project_details(), load_control_files()])

    create_horizontal_button_group(tab, [
        ("Save Control Model", save_control_file),
    ])

    def browse_audit_folder():
        path = filedialog.askdirectory()
        if path:
            entry_json_path.delete(0, tk.END)
            entry_json_path.insert(0, path)

    def import_revit_audit():
        folder = entry_json_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Select a valid folder")
            return
        try:
            import_health_data(folder, "localhost\\SQLEXPRESS", "RevitHealthCheckDB", "admin02", "1234")
            update_status(status_var, "Revit audit import finished")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    create_horizontal_button_group(tab, [
        ("Browse", browse_audit_folder),
        ("Import Audit JSONs", import_revit_audit),
    ])

    # --- ACC Data Export Folder Management ---
    ttk.Label(tab, text="ACC Data Export Folder", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_data_export = create_labeled_entry(tab, "Export Folder:")

    def browse_data_export():
        path = filedialog.askdirectory()
        if path:
            entry_data_export.delete(0, tk.END)
            entry_data_export.insert(0, path)

    def save_data_export():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        path = entry_data_export.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Error", "Select a valid folder")
            return
        save_acc_folder_path(pid, path)
        update_status(status_var, "ACC data export path saved")

    create_horizontal_button_group(tab, [
        ("Browse", browse_data_export),
        ("Save Path", save_data_export),
    ])

    log_list = tk.Listbox(tab, width=80, height=5)
    log_list.pack(padx=10, pady=5, anchor="w")

    # --- ACC CSV Import Section ---
    ttk.Label(tab, text="ACC Export CSV Import", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_acc_folder = create_labeled_entry(tab, "ACC CSV Folder/ZIP:")
    CreateToolTip(entry_acc_folder, "Select the folder containing weekly ACC CSV exports or a ZIP archive")

    def browse_acc_folder():
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if path:
            entry_acc_folder.delete(0, tk.END)
            entry_acc_folder.insert(0, path)
        else:
            path = filedialog.askdirectory()
            if path:
                entry_acc_folder.delete(0, tk.END)
                entry_acc_folder.insert(0, path)

    def import_acc_csv():
        folder = entry_acc_folder.get().strip()
        if not folder or not (
            os.path.isdir(folder)
            or (os.path.isfile(folder) and folder.lower().endswith(".zip"))
        ):
            messagebox.showerror("Error", "Select a valid folder or ZIP file")
            return
        success, msg = run_acc_import(cmb_projects, entry_acc_folder, log_list)
        if success:
            update_status(status_var, msg)
        else:
            messagebox.showerror("Error", msg)

    create_horizontal_button_group(tab, [
        ("Browse", browse_acc_folder),
        ("Import ACC CSVs", import_acc_csv),
    ])

    # --- Clash CSV Import Section ---
    ttk.Label(tab, text="Clash CSV Import", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_clash_folder = create_labeled_entry(tab, "Clash CSV Folder:")
    CreateToolTip(entry_clash_folder, "Folder path containing Navisworks clash detection results")

    def import_clash_csv():
        update_status(status_var, "Clash CSV import started")

    create_horizontal_button_group(tab, [("Import Clash CSVs", import_clash_csv)])


    # --- Ideate Health Check Excel Import Section ---
    ttk.Label(tab, text="Ideate Health Check Import", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_ideate_folder = create_labeled_entry(tab, "Ideate Excel Folder:")
    CreateToolTip(entry_ideate_folder, "Select the folder containing Ideate Health Check Excel files")

    def browse_ideate_folder():
        path = filedialog.askdirectory()
        if path:
            entry_ideate_folder.delete(0, tk.END)
            entry_ideate_folder.insert(0, path)

    def import_ideate_health_checks():
        folder = entry_ideate_folder.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Select a valid folder")
            return

        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return

        try:
            project_id = int(cmb_projects.get().split(" - ")[0])
            df_result = export_health_checks_to_sql(
                folder_path=folder,
                project_id=project_id,
                table_name="dbo.IdeateHealthCheckSummary"
            )

            log_acc_import(project_id, os.path.basename(folder), "Ideate Health Check import complete")
            update_status(status_var, f"Ideate Health Check import complete ({len(df_result)} files processed)")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    create_horizontal_button_group(tab, [
        ("Browse", browse_ideate_folder),
        ("Import Ideate Excel", import_ideate_health_checks),
    ])
