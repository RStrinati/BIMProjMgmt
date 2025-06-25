# ui/tab_project.py

"""UI elements for project setup and folder management."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime

from ui.ui_helpers import (
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip
from ui import tab_review

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
    """Build the project setup tab using a 3 column grid layout."""

    # ------------------------------------------------------------------
    # Container with three columns
    # ------------------------------------------------------------------
    container = ttk.Frame(tab)
    container.pack(fill="both", expand=True, padx=10, pady=10)
    for i in range(3):
        container.columnconfigure(i, weight=1, uniform="col")

    left_col = ttk.Frame(container)
    left_col.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    middle_col = ttk.Frame(container)
    middle_col.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    right_col = ttk.Frame(container)
    right_col.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

    # Column 3 summary frame
    frame_summary = ttk.LabelFrame(right_col, text="Current Project Summary")
    frame_summary.pack(fill="both", expand=True, pady=5)

    summary_vars = {
        "Name": tk.StringVar(),
        "Status": tk.StringVar(),
        "Priority": tk.StringVar(),
        "Start Date": tk.StringVar(),
        "End Date": tk.StringVar(),
        "Model Path": tk.StringVar(),
        "IFC Path": tk.StringVar(),
    }

    for idx, (label, var) in enumerate(summary_vars.items()):
        ttk.Label(frame_summary, text=f"{label}:").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame_summary, textvariable=var, wraplength=300).grid(row=idx, column=1, sticky="w", padx=5, pady=2)

    # ------------------------------------------------------------------
    # Column 1 - Selection & details
    # ------------------------------------------------------------------
    frame_select = ttk.LabelFrame(left_col, text="Project Selection")
    frame_select.pack(fill="x", pady=5)

    ttk.Label(frame_select, text="Select Active Project", font=("Arial", 12, "bold")).pack(pady=5, anchor="w")
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(frame_select, "Project:", projects)
    CreateToolTip(cmb_projects, "Select from existing projects")

    def refresh_projects():
        """Reload the project list from the database."""
        projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
        cmb_projects['values'] = projects
        if projects:
            cmb_projects.current(0)
        update_status(status_var, "Project list refreshed")

    create_horizontal_button_group(frame_select, [("Refresh", refresh_projects)])

    frame_details = ttk.LabelFrame(left_col, text="Project Details")
    frame_details.pack(fill="x", pady=5)

    _, entry_proj_number = create_labeled_entry(frame_details, "Project Name:")
    _, entry_status = create_labeled_entry(frame_details, "Status:")
    _, entry_priority = create_labeled_entry(frame_details, "Priority:")
    ttk.Label(frame_details, text="Start Date:").pack(padx=10, anchor="w")
    start_entry = DateEntry(frame_details, width=12)
    start_entry.pack(padx=10, pady=2, anchor="w")
    ttk.Label(frame_details, text="End Date:").pack(padx=10, anchor="w")
    end_entry = DateEntry(frame_details, width=12)
    end_entry.pack(padx=10, pady=2, anchor="w")

    frame_paths = ttk.LabelFrame(middle_col, text="Linked Folder Paths")
    frame_paths.pack(fill="x", pady=5)

    _, entry_model_path = create_labeled_entry(frame_paths, "Model Folder Path:")
    _, entry_ifc_path = create_labeled_entry(frame_paths, "IFC Folder Path:")

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
        summary_vars["Model Path"].set(entry_model_path.get().strip())
        summary_vars["IFC Path"].set(entry_ifc_path.get().strip())

    create_horizontal_button_group(
        frame_paths,
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
        summary_vars["Name"].set(entry_proj_number.get().strip())
        summary_vars["Status"].set(entry_status.get())
        summary_vars["Priority"].set(entry_priority.get())
        summary_vars["Start Date"].set(start_entry.get_date().strftime("%Y-%m-%d"))
        summary_vars["End Date"].set(end_entry.get_date().strftime("%Y-%m-%d"))

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
            tab_review.refresh_review_projects()
            update_status(status_var, f"Created new project: {name}")

    create_horizontal_button_group(
        frame_details,
        [
            ("Save Details", save_details),
            ("Extract Files", extract_files),
            ("Create Project", create_project),
        ],
    )

    # --- Cycle Dropdown & Tasks ---
    frame_cycle = ttk.LabelFrame(left_col, text="Review Cycle")
    frame_cycle.pack(fill="x", pady=5)

    _, cmb_cycles = create_labeled_combobox(frame_cycle, "Cycle:", [])

    def load_cycles(pid):
        cycles = get_cycle_ids(pid)
        cmb_cycles['values'] = cycles if cycles else ["No Cycles Available"]
        if cycles:
            cmb_cycles.current(0)
        else:
            cmb_cycles.set("No Cycles Available")

    def open_tasks_window():
        subprocess.Popen(["python", "tasks_users_ui.py"])

    create_horizontal_button_group(frame_cycle, [("Manage Tasks & Users", open_tasks_window)])

    # --- Recent File List ---
    frame_recent = ttk.LabelFrame(middle_col, text="Recent ACC Files")
    frame_recent.pack(fill="both", expand=True, pady=5)
    frame_recent.pack_propagate(False)
    lst_recent = tk.Listbox(frame_recent, width=80, height=10)
    lst_recent.pack(padx=10, pady=5, anchor="w", fill="both", expand=True)
    lst_scroll = ttk.Scrollbar(frame_recent, orient="horizontal", command=lst_recent.xview)
    lst_recent.configure(xscrollcommand=lst_scroll.set)
    lst_scroll.pack(side="bottom", fill="x")

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
            start_entry.set_date(datetime.strptime(details["start_date"], "%Y-%m-%d").date())
            end_entry.set_date(datetime.strptime(details["end_date"], "%Y-%m-%d").date())
            summary_vars["Name"].set(details["project_name"])
            summary_vars["Status"].set(details["status"] or "")
            summary_vars["Priority"].set(details["priority"] or "")
            summary_vars["Start Date"].set(details["start_date"])
            summary_vars["End Date"].set(details["end_date"])
        folder, ifc = get_project_folders(pid)
        entry_model_path.delete(0, tk.END); entry_model_path.insert(0, folder or "")
        entry_ifc_path.delete(0, tk.END); entry_ifc_path.insert(0, ifc or "")
        summary_vars["Model Path"].set(folder or "")
        summary_vars["IFC Path"].set(ifc or "")
        load_cycles(pid)
        update_results()

    cmb_projects.bind("<<ComboboxSelected>>", load_selected_project)

    if projects:
        load_selected_project()
