# ui/tab_project.py

"""UI elements for project setup and folder management."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry

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
    update_project_details,
    update_project_folders,
    get_project_folders,
    insert_files_into_tblACCDocs,
    insert_project,
    get_recent_files,
    get_cycle_ids,
)
import subprocess

def build_project_tab(tab, status_var):
    # --- Project Selection Section ---
    ttk.Label(tab, text="Select Active Project", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(tab, "Project:", projects)
    CreateToolTip(cmb_projects, "Select from existing projects")

    def refresh_projects():
        """Reload the project list from the database."""
        projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
        cmb_projects['values'] = projects
        if projects:
            cmb_projects.current(0)
        update_status(status_var, "Project list refreshed")

    create_horizontal_button_group(tab, [("Refresh", refresh_projects)])

    # --- Project Details Section ---
    ttk.Label(tab, text="Project Details", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_proj_number = create_labeled_entry(tab, "Project Name:")
    _, entry_status = create_labeled_entry(tab, "Status:")
    _, entry_priority = create_labeled_entry(tab, "Priority:")
    start_entry = DateEntry(tab, width=12)
    start_entry.pack(padx=10, pady=2, anchor="w")
    end_entry = DateEntry(tab, width=12)
    end_entry.pack(padx=10, pady=2, anchor="w")

    # --- Folder Path Section ---
    ttk.Label(tab, text="Linked Folder Paths", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_model_path = create_labeled_entry(tab, "Model Folder Path:")
    _, entry_ifc_path = create_labeled_entry(tab, "IFC Folder Path:")

    def browse_models():
        path = filedialog.askdirectory()
        if path:
            entry_model_path.delete(0, tk.END)
            entry_model_path.insert(0, path)

    def browse_ifc():
        path = filedialog.askdirectory()
        if path:
            entry_ifc_path.delete(0, tk.END)
            entry_ifc_path.insert(0, path)

    def save_paths():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        update_project_folders(
            pid,
            models_path=entry_model_path.get().strip() or None,
            data_path=None,
            ifc_path=entry_ifc_path.get().strip() or None,
        )
        update_status(status_var, "Folder paths saved")

    create_horizontal_button_group(
        tab,
        [
            ("Browse Models", browse_models),
            ("Browse IFC", browse_ifc),
            ("Save Paths", save_paths),
        ],
    )


    def save_details():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        update_project_details(
            pid,
            start_entry.get_date().strftime("%Y-%m-%d"),
            end_entry.get_date().strftime("%Y-%m-%d"),
            entry_status.get(),
            entry_priority.get(),
        )
        update_status(status_var, "Project details updated")

    def extract_files():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        folder, _ = get_project_folders(pid)
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid model folder")
            return
        if insert_files_into_tblACCDocs(pid, folder):
            update_status(status_var, "Files extracted")
        else:
            messagebox.showerror("Error", "Failed to extract files")

    def create_project():
        name = entry_proj_number.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter a project name")
            return
        if insert_project(name, "", None):
            refresh_projects()
            update_status(status_var, f"Created new project: {name}")

    create_horizontal_button_group(
        tab,
        [
            ("Save Details", save_details),
            ("Extract Files", extract_files),
            ("Create Project", create_project),
        ],
    )

    # --- Cycle Dropdown & Tasks ---
    ttk.Label(tab, text="Select Review Cycle", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, cmb_cycles = create_labeled_combobox(tab, "Cycle:", [])

    def load_cycles(pid):
        cycles = get_cycle_ids(pid)
        cmb_cycles['values'] = cycles if cycles else ["No Cycles Available"]
        if cycles:
            cmb_cycles.current(0)
        else:
            cmb_cycles.set("No Cycles Available")

    def open_tasks_window():
        subprocess.Popen(["python", "tasks_users_ui.py"])

    create_horizontal_button_group(tab, [("Manage Tasks & Users", open_tasks_window)])

    # --- Recent File List ---
    ttk.Label(tab, text="Recent ACC Files", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    lst_recent = tk.Listbox(tab, width=80, height=10)
    lst_recent.pack(padx=10, pady=5, anchor="w")

    def update_results():
        lst_recent.delete(0, tk.END)
        for row in get_recent_files():
            level, fname, dmod, recent = row
            lst_recent.insert(tk.END, f"{level} | {fname} | {dmod} | {recent}")

    def load_selected_project(event=None):
        if " - " not in cmb_projects.get():
            return
        pid = cmb_projects.get().split(" - ")[0]
        details = get_project_details(pid)
        if details:
            entry_proj_number.delete(0, tk.END)
            entry_proj_number.insert(0, details["project_name"])
            entry_status.delete(0, tk.END)
            entry_status.insert(0, details["status"]) if details["status"] else None
            entry_priority.delete(0, tk.END)
            entry_priority.insert(0, details["priority"]) if details["priority"] else None
            start_entry.set_date(details["start_date"])
            end_entry.set_date(details["end_date"])
        folder, ifc = get_project_folders(pid)
        entry_model_path.delete(0, tk.END); entry_model_path.insert(0, folder or "")
        entry_ifc_path.delete(0, tk.END); entry_ifc_path.insert(0, ifc or "")
        load_cycles(pid)
        update_results()

    cmb_projects.bind("<<ComboboxSelected>>", load_selected_project)

    if projects:
        load_selected_project()
