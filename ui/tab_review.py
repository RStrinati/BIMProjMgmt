# ui/tab_review.py

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from ui.ui_helpers import (
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

from review_handler import submit_review_schedule
from gantt_chart import launch_gantt_chart
from database import (
    get_projects,
    get_cycle_ids,
    get_users_list,
    get_review_tasks,
    update_review_task_assignee,
)

# Global reference to the project dropdown so other tabs can refresh it
cmb_projects_ref = None

def refresh_review_projects():
    """Reload the project list for the review tab combobox."""
    if cmb_projects_ref is None:
        return
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    cmb_projects_ref['values'] = projects
    if projects:
        cmb_projects_ref.current(0)
        cmb_projects_ref.event_generate('<<ComboboxSelected>>')
        
def open_revizto_csharp_app():
    exe_path = os.path.abspath("tools/ReviztoDataExporter.exe")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
    else:
        messagebox.showerror("Error", f"EXE not found at: {exe_path}")

def build_review_tab(tab, status_var):
    global cmb_projects_ref
    # --- Project & Cycle Selection ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(tab, "Project:", projects)
    cmb_projects_ref = cmb_projects
    _, cmb_cycles = create_labeled_combobox(tab, "Cycle:", [])

    def load_cycles(event=None):
        if " - " not in cmb_projects.get():
            return
        pid = cmb_projects.get().split(" - ")[0]
        cycles = get_cycle_ids(pid)
        cmb_cycles['values'] = cycles if cycles else ["No Cycles Available"]
        if cycles:
            cmb_cycles.current(0)
        else:
            cmb_cycles.set("No Cycles Available")

    cmb_projects.bind("<<ComboboxSelected>>", load_cycles)
    if projects:
        load_cycles()

    create_horizontal_button_group(tab, [("Manage Tasks & Users", lambda: subprocess.Popen(["python", "tasks_users_ui.py"]))])

    # --- Review Upload Section ---
    ttk.Label(tab, text="Review Scheduling", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)

    start_date = DateEntry(tab, width=12)
    start_date.pack(padx=10, anchor="w")
    num_reviews_entry = ttk.Entry(tab, width=10)
    num_reviews_entry.pack(padx=10, pady=2, anchor="w")
    freq_entry = ttk.Entry(tab, width=10)
    freq_entry.pack(padx=10, pady=2, anchor="w")

    ttk.Label(tab, text="License Start Date:").pack(padx=10, anchor="w")
    license_start_date = DateEntry(tab, width=12)
    license_start_date.pack(padx=10, pady=2, anchor="w")
    ttk.Label(tab, text="License Duration (months):").pack(padx=10, anchor="w")
    license_duration_entry = ttk.Entry(tab, width=10)
    license_duration_entry.pack(padx=10, pady=2, anchor="w")

    def submit_schedule():
        submit_review_schedule(
            cmb_projects,
            cmb_cycles,
            start_date,
            num_reviews_entry,
            freq_entry,
            license_start_date,
            license_duration_entry,
        )
        update_status(status_var, "Review schedule submitted")

    create_horizontal_button_group(
        tab,
        [("Submit Schedule", submit_schedule), ("Launch Gantt Chart", lambda: launch_gantt_chart(None, None))],
    )

    # --- Reviewer Assignment Section ---
    ttk.Label(tab, text="Reviewer Assignment", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)

    assignment_frame = ttk.Frame(tab)
    assignment_frame.pack(fill="both", padx=10, pady=5)

    tree_reviews = ttk.Treeview(assignment_frame, columns=("id", "date", "user"), show="headings", height=5)
    tree_reviews.heading("id", text="ID")
    tree_reviews.heading("date", text="Review Date")
    tree_reviews.heading("user", text="Reviewer")
    tree_reviews.pack(side="left", fill="both", expand=True)

    scroll = ttk.Scrollbar(assignment_frame, orient="vertical", command=tree_reviews.yview)
    tree_reviews.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

    reviewer_var = tk.StringVar()
    reviewer_dropdown = ttk.Combobox(tab, textvariable=reviewer_var)
    reviewer_dropdown.pack(padx=10, anchor="w")

    def load_users():
        users = get_users_list()
        reviewer_dropdown['values'] = [u[1] for u in users]
        return {u[1]: u[0] for u in users}

    users_map = load_users()

    def refresh_tasks(event=None):
        nonlocal users_map
        users_map = load_users()
        for item in tree_reviews.get_children():
            tree_reviews.delete(item)
        if " - " not in cmb_projects.get() or not cmb_cycles.get():
            return
        pid = cmb_projects.get().split(" - ")[0]
        cid = cmb_cycles.get()
        rows = get_review_tasks(pid, cid)
        for sched_id, date, user in rows:
            tree_reviews.insert("", tk.END, iid=sched_id, values=(sched_id, date, user or ""))

    def assign_reviewer():
        sel = tree_reviews.focus()
        if not sel:
            messagebox.showerror("Error", "Select a review task")
            return
        name = reviewer_var.get()
        if not name or name not in users_map:
            messagebox.showerror("Error", "Select a reviewer")
            return
        if update_review_task_assignee(sel, users_map[name]):
            refresh_tasks()

    ttk.Button(tab, text="Assign To Selected", command=assign_reviewer).pack(padx=10, pady=2, anchor="w")

    cmb_projects.bind("<<ComboboxSelected>>", lambda e: [load_cycles(), refresh_tasks()])
    cmb_cycles.bind("<<ComboboxSelected>>", refresh_tasks)
    refresh_tasks()

    # --- Issue Tracking Section ---
    ttk.Label(tab, text="Revizto Issue Synchronisation", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_revizto_path = create_labeled_entry(tab, "Revizto Export Folder:")
    CreateToolTip(entry_revizto_path, "Folder containing Revizto issue data")

    def sync_issues():
        update_status(status_var, "Synchronising Revizto issues...")

    create_horizontal_button_group(
        tab,
        [
            ("Sync Revizto Issues", sync_issues),
            ("Launch Revizto Exporter", open_revizto_csharp_app),
        ],
    )

    # --- Review Comment Export ---
    ttk.Label(tab, text="Export Review Comments", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)

    def export_review_comments():
        update_status(status_var, "Exporting review comments...")

    create_horizontal_button_group(tab, [("Export Comments to Excel", export_review_comments)])

