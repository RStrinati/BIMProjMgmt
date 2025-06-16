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
    get_review_summary,
    get_project_review_progress,
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

    # ------------------------------------------------------------------
    # Scrollable container with horizontal scrollbar
    # ------------------------------------------------------------------
    canvas = tk.Canvas(tab, highlightthickness=0)
    h_scroll = ttk.Scrollbar(tab, orient="horizontal", command=canvas.xview)
    inner = ttk.Frame(canvas)
    inner.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(xscrollcommand=h_scroll.set)
    canvas.pack(fill="both", expand=True)
    h_scroll.pack(fill="x", side=tk.BOTTOM)

    # Container to hold three primary columns
    column_container = ttk.Frame(inner)
    column_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    for i in range(3):
        column_container.columnconfigure(i, weight=1, uniform="col")

    # --- Column 1 Frames ---
    frame_project = ttk.LabelFrame(column_container, text="Project Details")
    frame_project.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    frame_params = ttk.LabelFrame(column_container, text="Review Parameters")
    frame_params.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # --- Column 2 Frames ---
    frame_schedule = ttk.LabelFrame(column_container, text="Schedule Dates")
    frame_schedule.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    frame_other = ttk.LabelFrame(column_container, text="Other Inputs")
    frame_other.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    # --- Column 3 Summary Panel ---
    frame_summary = ttk.LabelFrame(column_container, text="Current Project Summary")
    frame_summary.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)

    summary_vars = {
        "Project Name": tk.StringVar(),
        "Cycle": tk.StringVar(),
        "Construction Stage": tk.StringVar(),
        "License Start": tk.StringVar(),
        "License Duration": tk.StringVar(),
        "Scoped Reviews": tk.StringVar(),
        "Completed Reviews": tk.StringVar(),
        "Last Updated": tk.StringVar(),
    }

    for idx, (lbl, var) in enumerate(summary_vars.items()):
        ttk.Label(frame_summary, text=f"{lbl}:").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame_summary, textvariable=var).grid(row=idx, column=1, sticky="w", padx=5, pady=2)

    def update_summary(event=None):
        if " - " not in cmb_projects.get() or not cmb_cycles.get():
            for v in summary_vars.values():
                v.set("")
            return
        pid = cmb_projects.get().split(" - ")[0]
        cid = cmb_cycles.get()
        data = get_review_summary(pid, cid)
        progress = get_project_review_progress(pid, cid) or {}
        if data:
            summary_vars["Project Name"].set(data.get("project_name", ""))
            summary_vars["Cycle"].set(data.get("cycle_id", ""))
            summary_vars["Construction Stage"].set(data.get("construction_stage", ""))
            summary_vars["License Start"].set(data.get("license_start", ""))
            summary_vars["License Duration"].set(f"{data.get('license_duration', '')} months")
            summary_vars["Scoped Reviews"].set(progress.get("scoped_reviews", data.get("scoped_reviews", 0)))
            summary_vars["Completed Reviews"].set(progress.get("completed_reviews", data.get("completed_reviews", 0)))
            summary_vars["Last Updated"].set(progress.get("last_updated", data.get("last_updated", "")))
        else:
            for v in summary_vars.values():
                v.set("")

    # --- Project & Cycle Selection ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(frame_project, "Project:", projects)
    cmb_projects_ref = cmb_projects
    _, cmb_cycles = create_labeled_combobox(frame_project, "Cycle:", [])

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

        update_summary()

    cmb_projects.bind("<<ComboboxSelected>>", load_cycles)
    if projects:
        load_cycles()

    create_horizontal_button_group(
        frame_project,
        [("Manage Tasks & Users", lambda: subprocess.Popen(["python", "tasks_users_ui.py"]))],
    )

    # --- Review Parameters ---
    ttk.Label(frame_params, text="Review Start Date:").pack(padx=10, anchor="w")
    start_date = DateEntry(frame_params, width=12)
    start_date.pack(padx=10, pady=2, anchor="w")
    ttk.Label(frame_params, text="Number of Reviews:").pack(padx=10, anchor="w")
    num_reviews_entry = ttk.Entry(frame_params, width=10)
    num_reviews_entry.pack(padx=10, pady=2, anchor="w")
    ttk.Label(frame_params, text="Review Frequency (days):").pack(padx=10, anchor="w")
    freq_entry = ttk.Entry(frame_params, width=10)
    freq_entry.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_params, text="License Start Date:").pack(padx=10, anchor="w")
    license_start_date = DateEntry(frame_params, width=12)
    license_start_date.pack(padx=10, pady=2, anchor="w")
    ttk.Label(frame_params, text="License Duration (months):").pack(padx=10, anchor="w")
    license_duration_entry = ttk.Entry(frame_params, width=10)
    license_duration_entry.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_params, text="Construction Stage:").pack(padx=10, anchor="w")
    stage_entry = ttk.Entry(frame_params, width=20)
    stage_entry.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_params, text="Reviews Per Phase:").pack(padx=10, anchor="w")
    reviews_per_phase_entry = ttk.Entry(frame_params, width=10)
    reviews_per_phase_entry.pack(padx=10, pady=2, anchor="w")
    # --- Other Inputs (right column) ---
    ttk.Label(frame_other, text="Proposed Fee:").pack(padx=10, anchor="w")
    fee_entry = ttk.Entry(frame_other, width=12)
    fee_entry.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_other, text="Assigned Users:").pack(padx=10, anchor="w")
    assigned_users_entry = ttk.Entry(frame_other, width=30)
    assigned_users_entry.pack(padx=10, pady=2, anchor="w")

    new_contract_var = tk.BooleanVar()
    ttk.Checkbutton(frame_other, text="New Contract", variable=new_contract_var).pack(padx=10, anchor="w")

    # --- Schedule Dates (right column) ---
    ttk.Label(frame_schedule, text="Planned Start Date:").pack(padx=10, anchor="w")
    planned_start = DateEntry(frame_schedule, width=12)
    planned_start.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_schedule, text="Planned Completion Date:").pack(padx=10, anchor="w")
    planned_completion = DateEntry(frame_schedule, width=12)
    planned_completion.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_schedule, text="Actual Start Date:").pack(padx=10, anchor="w")
    actual_start = DateEntry(frame_schedule, width=12)
    actual_start.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_schedule, text="Actual Completion Date:").pack(padx=10, anchor="w")
    actual_completion = DateEntry(frame_schedule, width=12)
    actual_completion.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_schedule, text="Hold Date:").pack(padx=10, anchor="w")
    hold_date = DateEntry(frame_schedule, width=12)
    hold_date.pack(padx=10, pady=2, anchor="w")

    ttk.Label(frame_schedule, text="Resume Date:").pack(padx=10, anchor="w")
    resume_date = DateEntry(frame_schedule, width=12)
    resume_date.pack(padx=10, pady=2, anchor="w")

    def submit_schedule():
        submit_review_schedule(
            cmb_projects,
            cmb_cycles,
            start_date,
            num_reviews_entry,
            freq_entry,
            license_start_date,
            license_duration_entry,
            stage_entry,
            fee_entry,
            assigned_users_entry,
            reviews_per_phase_entry,
            planned_start,
            planned_completion,
            actual_start,
            actual_completion,
            hold_date,
            resume_date,
            new_contract_var,
        )
        update_status(status_var, "Review schedule submitted")


    btn_frame = create_horizontal_button_group(
        inner,
        [
            ("Submit Schedule", submit_schedule),
            ("Launch Gantt Chart", lambda: launch_gantt_chart(None, None)),
        ],
        pack=False,
    )
    btn_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=10)

    # --- Reviewer Assignment Section ---
    frame_assignment = ttk.LabelFrame(inner, text="Reviewer Assignment")
    frame_assignment.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)


    summary_label = ttk.Label(frame_assignment, text="")
    summary_label.pack(anchor="w", padx=5, pady=5)
    style = ttk.Style()
    style.configure("Review.Treeview.Heading", font=("Arial", 10, "bold"))
    style.configure("Review.Treeview", rowheight=20)

    tree_reviews = ttk.Treeview(frame_assignment, columns=("id", "date", "user", "status"), show="headings", height=5, style="Review.Treeview")
    tree_reviews.heading("id", text="ID")
    tree_reviews.heading("date", text="Review Date")
    tree_reviews.heading("user", text="Reviewer")
    tree_reviews.heading("status", text="Status")
    tree_reviews.pack(side="left", fill="both", expand=True)
    scroll = ttk.Scrollbar(frame_assignment, orient="vertical", command=tree_reviews.yview)
    tree_reviews.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

    reviewer_var = tk.StringVar()
    reviewer_dropdown = ttk.Combobox(frame_assignment, textvariable=reviewer_var)
    reviewer_dropdown.pack(padx=5, pady=5, anchor="w")

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
        for idx, (sched_id, date, user, status) in enumerate(rows):
            tag = "odd" if idx % 2 else "even"
            tree_reviews.insert("", tk.END, iid=sched_id, values=(sched_id, date, user or "", status or ""), tags=(tag,))
        tree_reviews.tag_configure("odd", background="#f0f0ff")

        progress = get_project_review_progress(pid, cid) or {"scoped_reviews": len(rows), "completed_reviews": 0}
        assigned = sum(1 for _, _, u, _ in rows if u)
        summary_label.config(
            text=f"Reviews Scoped: {progress.get('scoped_reviews', len(rows))} | Assigned: {assigned} | Completed: {progress.get('completed_reviews', 0)}"
        )

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

    ttk.Button(frame_assignment, text="Assign To Selected", command=assign_reviewer).pack(padx=5, pady=5, anchor="w")

    cmb_projects.bind("<<ComboboxSelected>>", lambda e: [load_cycles(), refresh_tasks()])
    cmb_cycles.bind("<<ComboboxSelected>>", lambda e: [refresh_tasks(), update_summary()])
    refresh_tasks()
    update_summary()

    # --- Issue Tracking Section ---

    lbl_sync = ttk.Label(inner, text="Revizto Issue Synchronisation", font=("Arial", 12, "bold"))
    lbl_sync.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 0))
    frame_revizto, entry_revizto_path = create_labeled_entry(inner, "Revizto Export Folder:", pack=False)
    frame_revizto.grid(row=4, column=0, columnspan=3, sticky="w")

    CreateToolTip(entry_revizto_path, "Folder containing Revizto issue data")

    def sync_issues():
        update_status(status_var, "Synchronising Revizto issues...")

    sync_frame = create_horizontal_button_group(
        inner,
        [
            ("Sync Revizto Issues", sync_issues),
            ("Launch Revizto Exporter", open_revizto_csharp_app),
        ],
        pack=False,
    )
    sync_frame.grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=10)

    # --- Review Comment Export ---

    lbl_export = ttk.Label(inner, text="Export Review Comments", font=("Arial", 12, "bold"))
    lbl_export.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 0))


    def export_review_comments():
        update_status(status_var, "Exporting review comments...")


    export_frame = create_horizontal_button_group(
        inner,
        [("Export Comments to Excel", export_review_comments)],
        pack=False,
    )
    export_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=10)


