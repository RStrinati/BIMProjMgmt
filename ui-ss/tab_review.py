# ui/tab_review.py

from tkinter import ttk
from ui.ui_helpers import create_labeled_entry, create_horizontal_button_group
from ui.status_bar import update_status
from ui.tooltips import CreateToolTip

def build_review_tab(tab, status_var):
    # --- Review Upload Section ---
    ttk.Label(tab, text="Review Model Uploads", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
    _, entry_review_path = create_labeled_entry(tab, "Review Folder Path:")
    CreateToolTip(entry_review_path, "Folder for model review uploads")

    def upload_review_models():
        update_status(status_var, "Uploading review models...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Upload Review Models", upload_review_models)])

    # --- Issue Tracking Section ---
    ttk.Label(tab, text="Revizto Issue Synchronisation", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)
    _, entry_revizto_path = create_labeled_entry(tab, "Revizto Export Folder:")
    CreateToolTip(entry_revizto_path, "Folder containing Revizto issue data")

    def sync_issues():
        update_status(status_var, "Synchronising Revizto issues...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Sync Revizto Issues", sync_issues)])

    # --- Review Comment Export ---
    ttk.Label(tab, text="Export Review Comments", font=("Arial", 12, "bold")).pack(pady=20, anchor="w", padx=10)

    def export_review_comments():
        update_status(status_var, "Exporting review comments...")
        # Placeholder for logic

    create_horizontal_button_group(tab, [("Export Comments to Excel", export_review_comments)])