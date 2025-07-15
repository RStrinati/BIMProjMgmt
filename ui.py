import tkinter as tk  
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import threading
import webview
import pyodbc
import os
import subprocess
from datetime import datetime
from database import connect_to_db, get_projects, get_cycle_ids, store_file_details_in_db, get_recent_files, get_project_folders, insert_files_into_tblACCDocs, update_project_folders, get_last_export_date, get_project_details, update_project_details
from review_handler import submit_review_schedule, fetch_review_summary
from acc_handler import run_acc_import
from database import save_acc_folder_path, get_acc_folder_path 
from rvt_health_importer import import_health_data


global acc_model_folder_entry, acc_data_folder_entry, ifc_folder_entry, acc_folder_entry
# ui.py (top)
# after your imports
acc_model_folder_entry = None
acc_data_folder_entry  = None
ifc_folder_entry       = None
acc_folder_entry       = None
project_dropdown       = None
cycle_dropdown         = None
result_listbox         = None

def update_cycle_dropdown(project_id, cycle_dropdown):
    """Fetch latest cycle IDs and update the UI dropdown."""
    cycles = get_cycle_ids(project_id)
    if cycles:
        
        cycles = get_cycle_ids(project_id)
        cycle_dropdown['values'] = cycles if cycles else ["No Cycles Available"]
        if cycles and cycles[0] != "No Cycles Available":
            cycle_dropdown.current(0)
        else:
            cycle_dropdown.set("No Cycles Available")
    else:
        cycle_dropdown['values'] = ["No Cycles Available"]
        cycle_dropdown.set("No Cycles Available")

def open_tasks_users_ui():
    subprocess.Popen(["python", "tasks_users_ui.py"])

def open_gantt_chart():
    selected_project = project_dropdown.get()
    selected_cycle = cycle_dropdown.get()

    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
    else:
        messagebox.showerror("Error", "No project selected for the Gantt chart.")
        return

    if not selected_cycle:
        messagebox.showerror("Error", "No review cycle selected.")
        return
    
    cycle_id = selected_cycle  # Extract cycle ID

    # ✅ Call `launch_gantt_chart()` from `gantt_chart.py` instead of re-running Dash
    from gantt_chart import launch_gantt_chart
    launch_gantt_chart(project_id, cycle_id)

def open_revizto_csharp_app():
    exe_path = os.path.abspath("tools/ReviztoDataExporter.exe")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
    else:
        messagebox.showerror("Error", f"EXE not found at: {exe_path}")
        
def start_dash(project_id, cycle_id):
    from gantt_chart import launch_gantt_chart
    launch_gantt_chart(project_id, cycle_id)  # Pass both arguments
    from gantt_chart import app
    app.run_server(debug=False, use_reloader=False, port=8050)

    
    # ✅ Modify the threading call to pass project_id explicitly
    threading.Thread(target=start_dash, args=(project_id,), daemon=True).start()
    webview.create_window("Gantt Chart", "http://127.0.0.1:8050")
    webview.start()

def update_project_details(project_id, start_date, end_date, status, priority):
    """Update project details if they exist, otherwise insert."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()
        
        # Check if the record exists
        cursor.execute("""
            SELECT COUNT(*) FROM dbo.projects WHERE project_id = ?
        """, (project_id,))
        record_exists = cursor.fetchone()[0] > 0

        if record_exists:
            # Update the record if it exists
            cursor.execute("""
                UPDATE dbo.projects 
                SET start_date = ?, end_date = ?, status = ?, priority = ?, updated_at = GETDATE()
                WHERE project_id = ?;
            """, (start_date, end_date, status, priority, project_id))
        else:
            # Insert if no record exists (Should not normally happen)
            cursor.execute("""
                INSERT INTO dbo.projects (project_id, start_date, end_date, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE());
            """, (project_id, start_date, end_date, status, priority))

        conn.commit()
        print(f"✅ Project {project_id} details updated.")
        return True
    except Exception as e:
        print(f"❌ Database Error updating project details: {e}")
        return False
    finally:
        conn.close()


def save_project_info():
    """Save updated project details to the database."""
    selected_project = project_dropdown.get()

    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
        
        start_date = start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = end_date_entry.get_date().strftime('%Y-%m-%d')
        status = status_entry.get().strip()
        priority = priority_entry.get().strip()

        success = update_project_details(project_id, start_date, end_date, status, priority)

        if success:
            messagebox.showinfo("Success", "Project details updated successfully!")
            update_project_info()
        else:
            messagebox.showerror("Error", "Failed to update project details.")

def browse_acc_model_folder():
    global acc_model_folder_entry
    path = filedialog.askdirectory(title="Select ACC Models Folder")
    if path:
        acc_model_folder_entry.delete(0, tk.END)
        acc_model_folder_entry.insert(0, path)

def save_models_folder_path():
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    pid = sel.split(" - ")[0]

    path = acc_model_folder_entry.get().strip()
    if not path or not os.path.isdir(path):
        return messagebox.showerror("Error", "Invalid ACC Models folder path.")

    # pass it in as the “standard” folder_path, leave IFC untouched:
    success = update_project_folders(pid, path, None)
    if success:
        messagebox.showinfo("Success", "ACC Models folder saved.")
        update_folder_path()
    else:
        messagebox.showerror("Error", "Failed to save ACC Models folder.")




def update_folder_path():
    """Update folder path and IFC folder path based on the selected project."""
    selected_project = project_dropdown.get()
    
    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]

        # ✅ Fetch both folder paths from the database
        folder_path, ifc_folder_path = get_project_folders(project_id)

        # ✅ Debugging print statements
        print(f"🔍 Fetching Project {project_id}")
        print(f"📂 Folder Path: {folder_path}")
        print(f"📂 IFC Folder Path: {ifc_folder_path}")

        # ✅ Display folder path
        acc_model_folder_entry.delete(0, tk.END)
        acc_model_folder_entry.insert(0, folder_path or "")

        # ✅ Display IFC folder path
        ifc_folder_entry.delete(0, tk.END)
        ifc_folder_entry.insert(0, ifc_folder_path if ifc_folder_path else "No IFC folder assigned")

        # ✅ Show last import logs
        if acc_summary_listbox:
            from database import get_acc_import_logs
            acc_summary_listbox.delete(0, "end")
            logs = get_acc_import_logs(project_id)
            if logs:
                for folder, date, summary in logs:
                    acc_summary_listbox.insert("end", f"✅ {folder} @ {date.strftime('%Y-%m-%d %H:%M')}")
            else:
                acc_summary_listbox.insert("end", "No previous ACC imports found.")


def extract_files():
    """Extract files from the selected project's folder and store them in tblACCDocs."""
    selected_project = project_dropdown.get()

    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
    else:
        messagebox.showerror("Error", "No project selected.")
        return

    # ✅ Properly retrieve only the folder path
    folder_path, _ = get_project_folders(project_id)  

    if not folder_path or not os.path.exists(folder_path):
        messagebox.showerror("Error", "Invalid or missing folder path.")
        return

    # 🔍 Check if the function is properly called and connected
    print(f"📂 Attempting to extract files for Project ID: {project_id}")
    print(f"📂 Folder Path: {folder_path}")

    try:
        # ✅ Call the improved function and include common ACC directories
        success = insert_files_into_tblACCDocs(
            project_id,
            folder_path,
            include_dirs=[
                "WIP",
                "Work in Progress",
                "Shared",
                "Published",
                "Admin",
                "Documentation",

            ],
        )
        
        if success:
            print(f"✅ Files successfully inserted for Project ID {project_id}.")
            messagebox.showinfo("Success", f"Files extracted and stored for Project ID {project_id}.")
        else:
            print(f"❌ No files found or insertion failed for Project ID {project_id}.")
            messagebox.showerror("Error", "No files found or failed to insert.")
    
    except Exception as e:
        print(f"❌ Error during extraction process: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

def process_folder_data():
    folder_path = acc_model_folder_entry.get().strip()
    
    if not folder_path or not os.path.exists(folder_path):
        messagebox.showerror("Error", "Invalid folder path.")
        return
    
    file_details = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                date_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_type = os.path.splitext(file_name)[1][1:] if os.path.splitext(file_name)[1] else "Unknown"
                file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
                file_details.append((file_name, file_path, date_modified, file_type, file_size_kb))
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    if file_details:
        store_file_details_in_db(file_details)
        update_results()
        messagebox.showinfo("Success", "Folder data stored and list updated.")
    else:
        messagebox.showwarning("No Files", "No valid files found in the selected folder.")

def update_results():
    result_listbox.delete(0, tk.END)
    recent_files = get_recent_files()
    for row in recent_files:
        level_10_folder, file_name, date_modified, is_recent_status = row
        display_text = f"{level_10_folder} | {file_name} | {date_modified} | {is_recent_status}"
        result_listbox.insert(tk.END, display_text)

def browse_acc_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        acc_folder_entry.delete(0, tk.END)
        acc_folder_entry.insert(0, folder_selected)
        
        
def handle_import():
    success, msg = run_acc_import(project_dropdown, acc_folder_entry, acc_summary_listbox)
    if success:
        messagebox.showinfo("Success", msg)
    else:
        messagebox.showerror("Error", msg)

def process_ifc_files():
    """Processes IFC files from the selected project's IFC folder and updates the last export date."""
    selected_project = project_dropdown.get()
    
    if not selected_project or " - " not in selected_project:
        messagebox.showerror("Error", "Please select a valid project first.")
        return

    project_id = selected_project.split(" - ")[0]

    # ✅ Retrieve correct folder path
    _, ifc_folder_path = get_project_folders(project_id)  # Ignore standard folder path, use IFC path

    if not ifc_folder_path or not os.path.exists(ifc_folder_path):
        messagebox.showerror("Error", "Invalid IFC folder path.")
        return

    # ✅ Run IFC processing in a separate thread
    def run_processing():
        from process_ifc import process_folder  # Import IFC processing function
        process_folder(ifc_folder_path)

        # ✅ Fetch and update last export date
        last_export = get_last_export_date()
        export_date_label.config(text=f"Last Export Date: {last_export}")

        messagebox.showinfo("Success", f"IFC files processed. Last Export: {last_export}")

    threading.Thread(target=run_processing, daemon=True).start()

def update_project_info():
    """Fetch and display selected project's details (excluding folder paths)."""
    selected_project = project_dropdown.get()

    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
        project_details = get_project_details(project_id)

        if project_details:
            project_name_entry.config(state=tk.NORMAL)
            project_name_entry.delete(0, tk.END)
            project_name_entry.insert(0, project_details["project_name"])
            project_name_entry.config(state="readonly")

            start_date_entry.set_date(project_details["start_date"])
            end_date_entry.set_date(project_details["end_date"])

            status_entry.delete(0, tk.END)
            status_entry.insert(0, project_details["status"])

            priority_entry.delete(0, tk.END)
            priority_entry.insert(0, project_details["priority"])

            print(f"📋 Loaded project details for {selected_project}")

def save_new_project(project_name):
    """Save a new project to the database, with today as start/end and blank status/priority."""
    if not project_name.strip():
        return messagebox.showerror("Error", "Project name cannot be empty.")

    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return messagebox.showerror("Error", "Database connection failed.")

    try:
        cursor = conn.cursor()

        # use today for start_date and end_date, empty strings for status/priority
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO dbo.projects
                (project_name, start_date, end_date, status, priority, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (project_name, today, today, '', ''))
        conn.commit()

        # now repopulate the project dropdown and select the new one
        projects = get_projects()
        project_dropdown['values'] = [f"{p[0]} - {p[1]}" for p in projects]
        project_dropdown.current(len(projects) - 1)

        messagebox.showinfo("Success", f"Project '{project_name}' created.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create project: {e}")
    finally:
        conn.close()
        
def save_acc_folder_path_ui():
    path = acc_folder_entry.get().strip()
    if not path or not os.path.exists(path):
        return messagebox.showerror("Error", "Invalid ACC folder path.")
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    project_id = sel.split(" - ")[0]

    # call your database helper
    if save_acc_folder_path(project_id, path):
        messagebox.showinfo("Success", "ACC folder path saved.")
    else:
        messagebox.showerror("Error", "Failed to save ACC folder path.")


def browse_acc_model_folder():
    global acc_model_folder_entry
    path = filedialog.askdirectory(title="Select ACC Models Folder")
    if path:
        acc_model_folder_entry.delete(0, tk.END)
        acc_model_folder_entry.insert(0, path)

def save_acc_model_folder_path():
    proj = project_dropdown.get()
    if " - " not in proj or not os.path.exists(acc_model_folder_entry.get()):
        return messagebox.showerror("Error", "Invalid project or models folder.")
    pid = proj.split(" - ")[0]
    if update_project_folders(pid, acc_model_folder_entry.get(), None):  # assume your DB helper can take three args
        messagebox.showinfo("Success", "Models folder saved.")
    else:
        messagebox.showerror("Error","Failed to save models folder.")

def browse_acc_data_folder():
    path = filedialog.askdirectory(title="Select ACC Data Export Folder")
    if path:
        acc_data_folder_entry.delete(0, tk.END)
        acc_data_folder_entry.insert(0, path)

def save_acc_data_folder_path_ui():
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    pid = sel.split(" - ")[0]

    path = acc_data_folder_entry.get().strip()
    if not path or not os.path.isdir(path):
        return messagebox.showerror("Error", "Invalid ACC Data Export folder path.")

    if save_acc_folder_path(pid, path):
        messagebox.showinfo("Success", "ACC Data Export folder saved.")
    else:
        messagebox.showerror("Error", "Failed to save ACC Data Export folder.")
        
def update_folder_path():
    pid = project_dropdown.get().split(" - ")[0]
    std_folder, ifc_folder = get_project_folders(pid)
    data_folder = get_acc_folder_path(pid)

    acc_model_folder_entry.delete(0, tk.END)
    acc_model_folder_entry.insert(0, std_folder or "")

    ifc_folder_entry.delete(0, tk.END)
    ifc_folder_entry.insert(0, ifc_folder or "")

    acc_data_folder_entry.delete(0, tk.END)
    acc_data_folder_entry.insert(0, data_folder or "")

def browse_ifc_folder():
    path = filedialog.askdirectory(title="Select IFC Folder")
    if path:
        ifc_folder_entry.delete(0, tk.END)
        ifc_folder_entry.insert(0, path)

def save_ifc_folder_path_ui():
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    pid = sel.split(" - ")[0]

    path = ifc_folder_entry.get().strip()
    if not path or not os.path.isdir(path):
        return messagebox.showerror("Error", "Invalid IFC folder path.")

    # pass it in as the ifc_folder_path, leave standard folder_path untouched:
    success = update_project_folders(pid, None, path)
    if success:
        messagebox.showinfo("Success", "IFC folder saved.")
        update_folder_path()
    else:
        messagebox.showerror("Error", "Failed to save IFC folder.")

        
def save_data_export_folder_path():
    path = acc_data_folder_entry.get().strip()
    if not path or not os.path.isdir(path):
        return messagebox.showerror("Error", "Invalid ACC Data Export folder path.")
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    pid = sel.split(" - ")[0]

    success = update_project_folders(
        pid,
        models_path=None,
        data_path=path,
        ifc_path=None
    )
    if success:
        messagebox.showinfo("Success", "ACC Data Export folder saved.")
    else:
        messagebox.showerror("Error", "Failed to save ACC Data Export folder.")

def save_ifc_folder_path_ui():
    path = ifc_folder_entry.get().strip()
    if not path or not os.path.isdir(path):
        return messagebox.showerror("Error", "Invalid IFC folder path.")
    sel = project_dropdown.get()
    if " - " not in sel:
        return messagebox.showerror("Error", "No project selected.")
    pid = sel.split(" - ")[0]

    success = update_project_folders(
        pid,
        models_path=None,
        data_path=None,
        ifc_path=path
    )
    if success:
        messagebox.showinfo("Success", "IFC folder saved.")
    else:
        messagebox.showerror("Error", "Failed to save IFC folder.")
      
def save_project_info():
    """Save updated project details to the database."""
    selected_project = project_dropdown.get()

    if " - " in selected_project:
        project_id = selected_project.split(" - ")[0]
        
        start_date = start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = end_date_entry.get_date().strftime('%Y-%m-%d')
        status = status_entry.get().strip()
        priority = priority_entry.get().strip()

        success = update_project_details(project_id, start_date, end_date, status, priority)

        if success:
            messagebox.showinfo("Success", "Project details updated successfully!")
            update_project_info()  # ✅ Refresh UI
        else:
            messagebox.showerror("Error", "Failed to update project details.")
def create_ui(root):
    """Create the UI layout with a scrollbar for the whole window."""
    global acc_model_folder_entry, acc_data_folder_entry, ifc_folder_entry, acc_folder_entry
    global project_dropdown, result_listbox, cycle_dropdown, export_date_label
    global start_date_entry, end_date_entry, status_entry, priority_entry
    global project_name_entry, acc_summary_listbox
    root.title("Project & Review Management System")
    root.geometry("1200x700")
    root.geometry("1200x700")

    # ✅ Create a main frame with scrolling capabilities
    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )


    window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ✅ Pack a frame inside the scrollable area
    main_frame = tk.Frame(scrollable_frame)
    main_frame.pack(fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, padx=10, pady=10)

    # ✅ Define section_project BEFORE using it
    section_project = tk.LabelFrame(left_frame, text="Project Management")
    section_project.pack(fill="x", padx=5, pady=5)

    tk.Label(section_project, text="New Project Name:").pack()
    new_project_name_entry = tk.Entry(section_project, width=50)
    new_project_name_entry.pack()

    # (optionally) a button to actually save/create your new project:
    tk.Button(section_project,
              text="Create Project",
              command=lambda: save_new_project(new_project_name_entry.get())
                )  .pack(pady=4)


    # ✅ Create a frame for buttons
    # ── ACC Models (Desktop Connector) ────────────────────────────────────
    tk.Label(section_project, text="ACC Models Folder:").pack()
    acc_model_folder_entry = tk.Entry(section_project, width=50)
    acc_model_folder_entry.pack()

    btn_frame1 = tk.Frame(section_project); btn_frame1.pack(pady=5)
    tk.Button(btn_frame1, text="Browse Models",    command=browse_acc_model_folder).pack(side="left", padx=4)
    tk.Button(btn_frame1, text="Save Models Path", command=save_models_folder_path).pack(side="left", padx=4)
    tk.Button(btn_frame1, text="Extract Files",     command=extract_files).pack(side="left", padx=4)


    # ✅ Project Dropdown
    tk.Label(section_project, text="Select Project:").pack()
    project_dropdown = ttk.Combobox(section_project, width=50, state="readonly")
    project_dropdown['values'] = [f"{proj[0]} - {proj[1]}" for proj in get_projects()]
    project_dropdown.current(len(project_dropdown['values'])-1) 
    project_dropdown.pack()

    # ✅ Start Date
    tk.Label(section_project, text="Start Date:").pack()
    start_date_entry = DateEntry(section_project, width=12, background='darkblue', foreground='white', borderwidth=2)
    start_date_entry.pack()

    # ✅ End Date
    tk.Label(section_project, text="End Date:").pack()
    end_date_entry = DateEntry(section_project, width=12, background='darkblue', foreground='white', borderwidth=2)
    end_date_entry.pack()

    # ✅ Status
    tk.Label(section_project, text="Status:").pack()
    status_entry = tk.Entry(section_project, width=50)
    status_entry.pack()

    # ✅ Priority
    tk.Label(section_project, text="Priority:").pack()
    priority_entry = tk.Entry(section_project, width=50)
    priority_entry.pack()

    # ✅ Save Button
    save_button = tk.Button(section_project, text="Save Project Info", command=save_project_info)
    save_button.pack(pady=5)
    
    # ✅ ACC Data Logging
    acc_section = tk.LabelFrame(left_frame, text="ACC Data Export")
    acc_section.pack(fill="x", padx=5, pady=5)
    # 2) ACC Data Export folder
    tk.Label(acc_section, text="ACC Data Export Folder:").pack()
    acc_data_folder_entry = tk.Entry(acc_section, width=50)
    acc_data_folder_entry.pack()

    # ACC Folder Entry for import (used by browse_acc_folder and related functions)
    tk.Label(acc_section, text="ACC Folder:").pack()
    acc_folder_entry = tk.Entry(acc_section, width=50)
    acc_folder_entry.pack()
    acc_data_folder_entry.pack()

    tk.Button(acc_section, text="Browse Data Export",    command=browse_acc_data_folder).pack(pady=2)
    tk.Button(acc_section, text="Save Data Export Path", command=save_acc_data_folder_path_ui).pack(pady=2)
    tk.Button(acc_section, text="Import ACC Data",       command=handle_import).pack(pady=2)

    acc_summary_listbox = tk.Listbox(acc_section, width=80, height=5)
    acc_summary_listbox.pack()
    
    tk.Button(section_project, text="Launch Revizto Exporter", command=open_revizto_csharp_app).pack(pady=5)


    # Inside your UI layout
    health_frame = tk.LabelFrame(left_frame, text="Revit Health Check")
    health_frame.pack(fill="x", padx=5, pady=5)

    rvt_json_path_entry = tk.Entry(health_frame, width=50)
    rvt_json_path_entry.pack()

    def browse_health_folder():
        path = filedialog.askdirectory(title="Select JSON Export Folder")
        if path:
            rvt_json_path_entry.delete(0, tk.END)
            rvt_json_path_entry.insert(0, path)

    def run_health_import():
        folder = rvt_json_path_entry.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Invalid folder path.")
            return
        try:
            import_health_data(folder, "localhost\\SQLEXPRESS", "RevitHealthCheckDB", "admin02", "1234")
            messagebox.showinfo("Success", "Revit Health data imported.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(health_frame, text="Browse Folder", command=browse_health_folder).pack(side="left", padx=5)
    tk.Button(health_frame, text="Import JSON", command=run_health_import).pack(side="left", padx=5)


    # ✅ Bind dropdown selection to update_folder_path()
    project_dropdown.bind("<<ComboboxSelected>>", lambda event: update_folder_path())
 
    # ✅ Cycle Dropdown
    tk.Label(section_project, text="Select Review Option:").pack()
    cycle_dropdown = ttk.Combobox(section_project, width=50, state="readonly")
    cycle_dropdown.pack()

    task_user_btn = tk.Button(root, text="Manage Tasks & Users", command=lambda: messagebox.showinfo("Task", "Manage tasks!"))
    task_user_btn.pack()

    # ✅ Review Section
    section_review = tk.LabelFrame(left_frame, text="Review Scheduling")
    section_review.pack(fill="x", padx=5, pady=5)

    tk.Label(section_review, text="Review Start Date:").pack()
    review_start_date_entry = DateEntry(section_review, width=12)
    review_start_date_entry.pack()

    tk.Label(section_review, text="Number of Reviews:").pack()
    number_of_reviews_entry = tk.Entry(section_review, width=10)
    number_of_reviews_entry.pack()

    tk.Label(section_review, text="Review Frequency (days):").pack()
    review_frequency_entry = tk.Entry(section_review, width=10)
    review_frequency_entry.pack()

    tk.Label(section_review, text="License Start Date:").pack()
    license_start_date_entry = DateEntry(section_review, width=12)
    license_start_date_entry.pack()

    tk.Label(section_review, text="License Duration (months):").pack()
    license_duration_entry = tk.Entry(section_review, width=10)
    license_duration_entry.pack()

    # ✅ IFC Folder Section
    # 3) IFC folder
    ifc_section = tk.LabelFrame(left_frame, text="IFC File Management")
    ifc_section.pack(fill="x", padx=5, pady=5)

    tk.Label(ifc_section, text="IFC Folder:").pack()
    ifc_folder_entry = tk.Entry(ifc_section, width=50)
    ifc_folder_entry.pack()

    # ✅ Buttons for IFC management
    ifc_button_frame = tk.Frame(ifc_section)
    ifc_button_frame.pack(fill=tk.X, pady=5)

    tk.Button(ifc_button_frame,
          text="Browse IFC Folder",
          command=browse_ifc_folder
    ).pack(side="left", padx=5)

    tk.Button(ifc_button_frame,
            text="Save IFC Folder Path",
            command=save_ifc_folder_path_ui
    ).pack(side="left", padx=5)

    tk.Button(ifc_button_frame,
            text="Process IFC Files",
            command=process_ifc_files
    ).pack(side="left", padx=5)


    # ✅ Review Summary Section
    section_summary = tk.LabelFrame(left_frame, text="Project Review Summary")
    section_summary.pack(fill="x", padx=5, pady=5)

    summary_label = tk.Label(section_summary, text="No review summary available yet.")
    summary_label.pack()

    summary_buttons = tk.Frame(section_summary)
    summary_buttons.pack(fill=tk.X, pady=5)

    submit_review_btn = tk.Button(summary_buttons, text="Submit Review Schedule", command=lambda: messagebox.showinfo("Submit", "Review schedule submitted!"))
    submit_review_btn.pack(side=tk.LEFT, padx=5)

    check_review_btn = tk.Button(summary_buttons, text="Check Review Summary", command=lambda: messagebox.showinfo("Check", "Review summary checked!"))
    check_review_btn.pack(side=tk.LEFT, padx=5)

    gantt_chart_btn = tk.Button(summary_buttons, text="Launch Gantt Chart", command=lambda: messagebox.showinfo("Gantt", "Gantt chart launched!"))
    gantt_chart_btn.pack(side=tk.LEFT, padx=5)

    # ✅ Add a Label to Display Last Export Date
    export_date_label = tk.Label(root, text="Last Export Date: Not available", font=("Arial", 10))
    export_date_label.pack(pady=5)


    # ✅ File List
    result_listbox = tk.Listbox(left_frame, width=80, height=10)
    result_listbox.pack()

    return acc_model_folder_entry, result_listbox, project_dropdown, cycle_dropdown
