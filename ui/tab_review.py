# ui/tab_review.py

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from ui.ui_helpers import create_labeled_entry, create_horizontal_button_group
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

from review_handler import submit_review_schedule
from gantt_chart import launch_gantt_chart
from database import get_projects, get_cycle_ids


def open_revizto_csharp_app():
    exe_path = os.path.abspath("tools/ReviztoDataExporter.exe")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
    else:
        messagebox.showerror("Error", f"EXE not found at: {exe_path}")

def build_review_tab(tab, status_var):
    # --- Project & Cycle Selection ---
    projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
    _, cmb_projects = create_labeled_combobox(tab, "Project:", projects)
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

    def submit_schedule():
        submit_review_schedule(start_date.get_date(), num_reviews_entry.get(), freq_entry.get())
        update_status(status_var, "Review schedule submitted")

    create_horizontal_button_group(
        tab,
        [("Submit Schedule", submit_schedule), ("Launch Gantt Chart", lambda: launch_gantt_chart(None, None))],
    )

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

