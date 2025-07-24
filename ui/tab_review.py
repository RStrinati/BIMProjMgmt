# ui/tab_review.py

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import datetime

from ui.ui_helpers import (
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.status_bar import update_status

from review_handler import submit_review_schedule, generate_stage_review_schedule
from gantt_chart import launch_gantt_chart
from database import (
    get_projects,
    get_cycle_ids,
    get_users_list,
    get_review_tasks,
    update_review_task_assignee,
    get_review_summary,
    get_project_review_progress,
    get_contractual_links,
    get_project_details,
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

    # tab is already a scrollable frame with x-scroll enabled
    # Container to hold three primary columns
    column_container = ttk.Frame(tab)
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

    def show_contract_links():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        cid = cmb_cycles.get() or None
        links = get_contractual_links(pid, cid if cid else None)
        win = tk.Toplevel(tab)
        win.title("Contractual Links")
        cols = ("BEP Clause", "Billing Event", "Amount Due", "Status")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="w")
        for row in links:
            tree.insert("", tk.END, values=row)
        tree.pack(fill="both", expand=True)

    ttk.Button(frame_summary, text="View Contract Links", command=show_contract_links).grid(
        row=len(summary_vars), column=0, columnspan=2, pady=(10, 0)
    )

    # --- Project & Cycle Selection ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(frame_project, "Project:", projects)
    cmb_projects_ref = cmb_projects
    _, cmb_cycles = create_labeled_combobox(frame_project, "Cycle:", [])

    project_dates = {"start": "", "end": ""}

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

        details = get_project_details(pid)
        if details:
            project_dates["start"] = details.get("start_date", "")
            project_dates["end"] = details.get("end_date", "")

        update_summary()

    # initial binding moved later after all widgets are created

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

    # --- Schedule Dates ---
    # Date fields are now edited directly in the cycle table so
    # the standalone inputs are removed.

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
            cycle_data,
            new_contract_var,
        )
        update_status(status_var, "Review schedule submitted")


    # Place action buttons at the bottom of the Review Parameters section
    create_horizontal_button_group(
        frame_params,
        [
            ("Submit Schedule", submit_schedule),
            ("Launch Gantt Chart", lambda: launch_gantt_chart(None, None)),
        ],
    )

    # --- Stage Review Plan ---
    frame_stage_plan = ttk.LabelFrame(column_container, text="Stage Review Plan")
    frame_stage_plan.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    stage_columns = ("Stage", "Start", "End", "Reviews", "Frequency")
    tree_stages = ttk.Treeview(frame_stage_plan, columns=stage_columns, show="headings", height=4)
    for col in stage_columns:
        tree_stages.heading(col, text=col)
        tree_stages.column(col, width=100, anchor="w")
    tree_stages.pack(side="left", fill="both", expand=True)
    stage_scroll = ttk.Scrollbar(frame_stage_plan, orient="vertical", command=tree_stages.yview)
    tree_stages.configure(yscrollcommand=stage_scroll.set)
    stage_scroll.pack(side="right", fill="y")

    stage_data = []

    def add_stage_row():
        vals = ["" for _ in stage_columns]
        if project_dates["start"]:
            vals[1] = project_dates["start"]
        if project_dates["end"]:
            vals[2] = project_dates["end"]
        iid = tree_stages.insert("", tk.END, values=vals)
        stage_data.append((iid, vals.copy()))

    def delete_stage_row():
        selected = tree_stages.selection()
        for item in selected:
            tree_stages.delete(item)
        stage_data[:] = [d for d in stage_data if d[0] not in selected]

    edit_stage_var = tk.StringVar()

    def begin_stage_edit(event):
        region = tree_stages.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = tree_stages.identify_row(event.y)
        col = tree_stages.identify_column(event.x)
        if not row_id or not col:
            return
        x, y, width, height = tree_stages.bbox(row_id, col)
        col_idx = int(col[1:]) - 1
        edit_stage_var.set(tree_stages.set(row_id, column=stage_columns[col_idx]))
        entry = ttk.Entry(tree_stages, textvariable=edit_stage_var)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def save_stage(event=None):
            tree_stages.set(row_id, column=stage_columns[col_idx], value=edit_stage_var.get())
            for idx, (iid, vals) in enumerate(stage_data):
                if iid == row_id:
                    vals[col_idx] = edit_stage_var.get()
                    stage_data[idx] = (iid, vals)
                    break
            entry.destroy()

        entry.bind("<FocusOut>", save_stage)
        entry.bind("<Return>", save_stage)

    tree_stages.bind("<Double-1>", begin_stage_edit)

    stage_btn_frame = ttk.Frame(frame_stage_plan)
    stage_btn_frame.pack(fill="x", pady=5)

    ttk.Button(stage_btn_frame, text="Add Stage", command=add_stage_row).pack(side="left")
    ttk.Button(stage_btn_frame, text="Delete Stage", command=delete_stage_row).pack(side="left", padx=5)

    tree_stages.bind("<Insert>", lambda e: add_stage_row())
    tree_stages.bind("<Delete>", lambda e: delete_stage_row())

    def generate_schedule():
        if " - " not in cmb_projects.get():
            messagebox.showerror("Error", "Select a project first")
            return
        pid = cmb_projects.get().split(" - ")[0]
        stages = []
        for iid, vals in stage_data:
            stage, start, end, reviews, freq = vals
            if not stage or not start or not end or not reviews:
                continue
            try:
                s_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                e_date = datetime.datetime.strptime(end, "%Y-%m-%d").date()
                stages.append({"stage_name": stage, "start_date": s_date, "end_date": e_date, "num_reviews": int(reviews), "frequency": freq})
            except Exception:
                continue
        if not stages:
            messagebox.showerror("Error", "No valid stages defined")
            return
        if generate_stage_review_schedule(pid, stages):
            messagebox.showinfo("Success", "Review schedule generated")
            refresh_tasks()
            update_summary()

    ttk.Button(stage_btn_frame, text="Generate Schedule", command=generate_schedule).pack(side="right")

    # --- Review Cycle Table (Central Panel) ---
    frame_cycle_table = ttk.LabelFrame(column_container, text="Review Cycle Table")
    frame_cycle_table.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    filter_frame = ttk.Frame(frame_cycle_table)
    filter_frame.pack(fill="x", pady=(0, 5))
    ttk.Label(filter_frame, text="Status:").pack(side="left")
    status_filter = ttk.Entry(filter_frame, width=10)
    status_filter.pack(side="left", padx=5)
    ttk.Label(filter_frame, text="Stage:").pack(side="left")
    stage_filter = ttk.Entry(filter_frame, width=10)
    stage_filter.pack(side="left", padx=5)
    ttk.Label(filter_frame, text="Reviewer:").pack(side="left")
    reviewer_filter = ttk.Entry(filter_frame, width=10)
    reviewer_filter.pack(side="left", padx=5)

    cycle_columns = (
        "Cycle Name",
        "Planned Start",
        "Planned Completion",
        "Actual Start",
        "Actual Completion",
        "Hold",
        "Resume",
        "Status",
        "Stage",
        "Frequency",
        "Reviewer",
        "Notes",
    )

    tree_cycles = ttk.Treeview(frame_cycle_table, columns=cycle_columns, show="headings", height=5)
    for col in cycle_columns:
        tree_cycles.heading(col, text=col)
        tree_cycles.column(col, width=100, anchor="w")
    tree_cycles.pack(side="left", fill="both", expand=True)
    cycle_scroll = ttk.Scrollbar(frame_cycle_table, orient="vertical", command=tree_cycles.yview)
    tree_cycles.configure(yscrollcommand=cycle_scroll.set)
    cycle_scroll.pack(side="right", fill="y")

    date_columns = {
        "Planned Start",
        "Planned Completion",
        "Actual Start",
        "Actual Completion",
        "Hold",
        "Resume",
    }

    cycle_data = []

    def add_cycle_row():
        item_id = tree_cycles.insert("", tk.END, values=["" for _ in cycle_columns])
        cycle_data.append((item_id, ["" for _ in cycle_columns]))

    edit_var = tk.StringVar()

    def begin_edit(event):
        region = tree_cycles.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = tree_cycles.identify_row(event.y)
        col = tree_cycles.identify_column(event.x)
        if not row_id or not col:
            return
        x, y, width, height = tree_cycles.bbox(row_id, col)
        column_index = int(col[1:]) - 1
        
        column_name = cycle_columns[column_index]
        edit_var.set(tree_cycles.set(row_id, column=column_name))

        if column_name in date_columns:
            entry = DateEntry(
                tree_cycles,
                textvariable=edit_var,
                date_pattern="yyyy-mm-dd",
            )
            try:
                entry.set_date(datetime.datetime.strptime(edit_var.get(), "%Y-%m-%d").date())
            except Exception:
                pass
        else:
            entry = ttk.Entry(tree_cycles, textvariable=edit_var)

        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def save_edit(event=None):
            tree_cycles.set(row_id, column=cycle_columns[column_index], value=edit_var.get())
            for idx, (iid, vals) in enumerate(cycle_data):
                if iid == row_id:
                    vals[column_index] = edit_var.get()
                    cycle_data[idx] = (iid, vals)
                    break
            entry.destroy()

        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Return>", save_edit)

    tree_cycles.bind("<Double-1>", begin_edit)

    def apply_filters(event=None):
        for item, values in cycle_data:
            show = True
            if status_filter.get() and status_filter.get().lower() not in values[7].lower():
                show = False
            if stage_filter.get() and stage_filter.get().lower() not in values[8].lower():
                show = False
            if reviewer_filter.get() and reviewer_filter.get().lower() not in values[10].lower():
                show = False
            if show:
                tree_cycles.reattach(item, "", tk.END)
            else:
                tree_cycles.detach(item)

    status_filter.bind("<KeyRelease>", apply_filters)
    stage_filter.bind("<KeyRelease>", apply_filters)
    reviewer_filter.bind("<KeyRelease>", apply_filters)

    action_frame = ttk.Frame(frame_cycle_table)
    action_frame.pack(fill="x", pady=5)

    def delete_selected():
        selected = tree_cycles.selection()
        for item in selected:
            tree_cycles.delete(item)
        cycle_data[:] = [d for d in cycle_data if d[0] not in selected]

    cycle_menu = tk.Menu(tree_cycles, tearoff=0)
    cycle_menu.add_command(label="Add Row", command=add_cycle_row)
    cycle_menu.add_command(label="Delete Row", command=delete_selected)

    def show_cycle_menu(event):
        cycle_menu.tk_popup(event.x_root, event.y_root)

    tree_cycles.bind("<Button-3>", show_cycle_menu)
    tree_cycles.bind("<Insert>", lambda e: add_cycle_row())
    tree_cycles.bind("<Delete>", lambda e: delete_selected())

    ttk.Button(action_frame, text="Apply Changes", command=lambda: update_status(status_var, "Cycle changes applied")).pack(side="right")

    # --- Reviewer Assignment Section ---
    frame_assignment = ttk.LabelFrame(column_container, text="Reviewer Assignment")
    frame_assignment.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
    frame_assignment.grid_propagate(False)


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
    tree_reviews.column("id", width=60, stretch=False)
    tree_reviews.column("date", width=120, stretch=False)
    tree_reviews.column("user", width=150, stretch=False)
    tree_reviews.column("status", width=100, stretch=False)
    tree_reviews.pack(side="left", fill="y")
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
    if projects:
        load_cycles()
    refresh_tasks()
    update_summary()

    # --- Review Comment Export ---

    lbl_export = ttk.Label(column_container, text="Export Review Comments", font=("Arial", 12, "bold"))
    lbl_export.grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 0))


    def export_review_comments():
        update_status(status_var, "Exporting review comments...")


    export_frame = create_horizontal_button_group(
        column_container,
        [("Export Comments to Excel", export_review_comments)],
        pack=False,
    )
    export_frame.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=10)


