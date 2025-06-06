import tkinter as tk
import threading
from database import get_projects, get_cycle_ids
from review_handler import submit_review_schedule
from ui import create_ui, update_cycle_dropdown  
from gantt_chart import launch_gantt_chart



# ---------------------------------------------------
# Initialize Tkinter Root Window
# ---------------------------------------------------
root = tk.Tk()
root.geometry("1200x700")

# ✅ Call `create_ui()` to create the UI inside the `root` window
models_entry, result_listbox, project_dropdown, cycle_dropdown = create_ui(root) # ✅ Unpack all four values


# ✅ Refresh cycle dropdown when submitting a review
def refresh_cycle_dropdown():
    selected_project = project_dropdown.get()
    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
        update_cycle_dropdown(project_id, cycle_dropdown)

# Run Tkinter
root.mainloop()
