from ui.tooltips import CreateToolTip
from ui.tab_issue_analytics import IssueAnalyticsDashboard
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import time
import csv
from datetime import datetime, timedelta
import logging
import webbrowser
import threading

class TabOperationManager:
    """Manages concurrent operations across the Review Management tab"""
    
    def __init__(self):
        self._operations = {}
    
    def start_operation(self, operation_name: str) -> bool:
        """Start an operation if not already running"""
        if operation_name in self._operations:
            print(f"⚠️  Operation '{operation_name}' already in progress")
            return False
        
        self._operations[operation_name] = True
        print(f"🔄 Starting operation: {operation_name}")
        return True
    
    def end_operation(self, operation_name: str):
        """Mark operation as complete"""
        if operation_name in self._operations:
            del self._operations[operation_name]
            print(f"✅ Completed operation: {operation_name}")
    
    def is_operation_running(self, operation_name: str) -> bool:
        """Check if operation is currently running"""
        return operation_name in self._operations
    
    def get_active_operations(self) -> list:
        """Get list of currently active operations"""
        return list(self._operations.keys())

from database import (
    get_projects, save_acc_folder_path, get_acc_folder_path,
    connect_to_db, get_db_connection, get_acc_import_logs, get_project_details,
    get_project_folders, delete_project, get_available_clients,
    get_review_cycles, get_cycle_ids, get_users_list,
    get_bookmark_categories, get_project_bookmarks, add_bookmark,
    update_bookmark, delete_bookmark, get_contractual_links,
    update_project_folders, insert_files_into_tblACCDocs,
    start_revizto_extraction_run, complete_revizto_extraction_run,
    get_revizto_extraction_runs, get_last_revizto_extraction_run,
    get_project_combined_issues_overview, get_project_issues_by_status
)
from shared import project_service
from shared.project_service import ProjectServiceError, ProjectValidationError
from review_management_service import ReviewManagementService
from handlers.acc_handler import run_acc_import
from handlers.review_handler import submit_review_schedule
from ui.ui_helpers import (
    set_combo_from_pairs, parse_id_from_display, clear_treeview,
    format_id_name_list
)
from phase1_enhanced_database import ResourceManager
from tkcalendar import DateEntry
from constants import schema as S
logger = logging.getLogger(__name__)

# Set up logger

# Import required modules
from ui.ui_helpers import (
    set_combo_from_pairs, parse_id_from_display, clear_treeview,
    format_id_name_list
)
from phase1_enhanced_database import ResourceManager
from tkcalendar import DateEntry
from constants import schema as S

# Simple notification system stub
class ProjectNotificationSystem:
    """
    Enhanced notification system for cross-tab communication.
    
    This system uses the observer pattern to notify registered components
    (tabs, widgets, etc.) of various project-related events. This ensures
    all UI components stay synchronized with database changes.
    
    Event Types:
    - project_changed: Selected project changed
    - project_list_changed: Project list modified (add/delete/update)
    - project_dates_changed: Project start/end dates modified
    - client_changed: Project client assignment changed
    - review_status_changed: Review status updated
    - service_progress_changed: Service progress % updated
    - task_status_changed: Task status or completion changed
    - billing_claim_generated: New billing claim created
    - project_hold_changed: Project hold status changed
    - acc_data_imported: ACC data import completed
    """
    
    # Event type constants
    EVENT_TYPES = {
        'PROJECT_CHANGED': 'project_changed',
        'PROJECT_LIST_CHANGED': 'project_list_changed',
        'PROJECT_DATES_CHANGED': 'project_dates_changed',
        'CLIENT_CHANGED': 'client_changed',
        'REVIEW_STATUS_CHANGED': 'review_status_changed',
        'SERVICE_PROGRESS_CHANGED': 'service_progress_changed',
        'TASK_STATUS_CHANGED': 'task_status_changed',
        'BILLING_CLAIM_GENERATED': 'billing_claim_generated',
        'PROJECT_HOLD_CHANGED': 'project_hold_changed',
        'ACC_DATA_IMPORTED': 'acc_data_imported',
    }
    
    def __init__(self):
        self.observers = []
    
    def register_observer(self, observer):
        """Register an observer to receive notifications."""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def unregister_observer(self, observer):
        """Unregister an observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify(self, event_type, **kwargs):
        """
        Generic notification dispatcher.
        
        Args:
            event_type: Event type from EVENT_TYPES
            **kwargs: Event-specific data
        """
        handler_name = f"on_{event_type}"
        for observer in self.observers:
            if hasattr(observer, handler_name):
                try:
                    # Call with kwargs - handlers must accept **kwargs or specific named params
                    getattr(observer, handler_name)(**kwargs)
                except TypeError as e:
                    # Try calling with just the first positional argument for backwards compatibility
                    if 'project_selection' in kwargs:
                        try:
                            getattr(observer, handler_name)(kwargs['project_selection'])
                        except Exception as fallback_error:
                            print(f"⚠️  Error notifying {observer.__class__.__name__}.{handler_name}: {fallback_error}")
                    else:
                        print(f"⚠️  Error notifying {observer.__class__.__name__}.{handler_name}: {e}")
                except Exception as e:
                    print(f"⚠️  Error notifying {observer.__class__.__name__}.{handler_name}: {e}")
    
    # Convenience methods for specific event types
    
    def notify_project_changed(self, project_selection):
        """Notify that the selected project changed."""
        # Send both parameter names for backwards compatibility
        self.notify(self.EVENT_TYPES['PROJECT_CHANGED'], project_selection=project_selection, new_project=project_selection)
    
    def notify_project_list_changed(self):
        """Notify that the project list was modified."""
        self.notify(self.EVENT_TYPES['PROJECT_LIST_CHANGED'])
    
    def notify_project_dates_changed(self, project_id, start_date, end_date):
        """
        Notify that project dates changed.
        
        This triggers updates to:
        - ServiceScheduleSettings
        - ServiceReviews
        - Tasks
        - Gantt charts
        """
        self.notify(
            self.EVENT_TYPES['PROJECT_DATES_CHANGED'],
            project_id=project_id,
            start_date=start_date,
            end_date=end_date
        )
    
    def notify_client_changed(self, project_id, old_client_id, new_client_id, new_client_name):
        """
        Notify that project client assignment changed.
        
        Note: Existing billing claims preserve old client via snapshot columns.
        """
        self.notify(
            self.EVENT_TYPES['CLIENT_CHANGED'],
            project_id=project_id,
            old_client_id=old_client_id,
            new_client_id=new_client_id,
            new_client_name=new_client_name
        )
    
    def notify_review_status_changed(self, review_id, service_id, old_status, new_status):
        """
        Notify that a review status changed.
        
        May trigger:
        - Task completion
        - Service progress update
        - Billing eligibility check
        """
        self.notify(
            self.EVENT_TYPES['REVIEW_STATUS_CHANGED'],
            review_id=review_id,
            service_id=service_id,
            old_status=old_status,
            new_status=new_status
        )
    
    def notify_service_progress_changed(self, service_id, project_id, old_progress, new_progress):
        """
        Notify that service progress % changed.
        
        May trigger:
        - Billing claim generation
        - Project overall progress update
        """
        self.notify(
            self.EVENT_TYPES['SERVICE_PROGRESS_CHANGED'],
            service_id=service_id,
            project_id=project_id,
            old_progress=old_progress,
            new_progress=new_progress
        )
    
    def notify_task_status_changed(self, task_id, project_id, old_status, new_status):
        """Notify that a task status changed."""
        self.notify(
            self.EVENT_TYPES['TASK_STATUS_CHANGED'],
            task_id=task_id,
            project_id=project_id,
            old_status=old_status,
            new_status=new_status
        )
    
    def notify_billing_claim_generated(self, claim_id, project_id, total_amount):
        """
        Notify that a billing claim was generated.
        
        Includes client snapshot for historical accuracy.
        """
        self.notify(
            self.EVENT_TYPES['BILLING_CLAIM_GENERATED'],
            claim_id=claim_id,
            project_id=project_id,
            total_amount=total_amount
        )
    
    def notify_project_hold_changed(self, project_id, is_on_hold, hold_reason=None):
        """Notify that project hold status changed."""
        self.notify(
            self.EVENT_TYPES['PROJECT_HOLD_CHANGED'],
            project_id=project_id,
            is_on_hold=is_on_hold,
            hold_reason=hold_reason
        )
    
    def notify_acc_data_imported(self, project_id, folder_name, import_id, record_count):
        """Notify that ACC data import completed."""
        self.notify(
            self.EVENT_TYPES['ACC_DATA_IMPORTED'],
            project_id=project_id,
            folder_name=folder_name,
            import_id=import_id,
            record_count=record_count
        )

project_notification_system = ProjectNotificationSystem()

class ProjectSetupTab:
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Project Setup")
        self.setup_ui()

    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # ===== TOP SECTION: PROJECT SELECTION =====
        project_frame = ttk.LabelFrame(main_frame, text="Project Selection & Status", padding=15)
        project_frame.pack(fill="x", pady=(0, 15))
        # Current project selection
        selection_frame = ttk.Frame(project_frame)
        selection_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(selection_frame, text="Current Project:", font=("Arial", 10, "bold")).pack(side="left")
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(selection_frame, textvariable=self.project_var, width=50)
        self.project_combo.pack(side="left", padx=(10, 0))
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
        # Folder path display
        ttk.Label(selection_frame, text="Desktop Connector Folder:", font=("Arial", 10)).pack(side="left", padx=(20, 0))
        self.folder_path_var = tk.StringVar()
        self.folder_path_entry = ttk.Entry(selection_frame, textvariable=self.folder_path_var, width=40, state="readonly")
        self.folder_path_entry.pack(side="left", padx=(10, 0))
        # Project status display
        status_frame = ttk.Frame(project_frame)
        status_frame.pack(fill="x")
        # Left column - basic info

    def show_project_dialog(self, mode="create", project_id=None):
        import tkinter as tk
        from tkinter import ttk, messagebox
        from tkcalendar import DateEntry
        from database import get_project_details, get_project_folders, get_available_clients
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Project" if mode == "create" else "Edit Project Details")
        dialog.geometry("700x600")
        dialog.resizable(True, True)
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")
        main_canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        title_label = ttk.Label(content_frame, text="Create New Project" if mode == "create" else "Edit Project Details", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        existing_data = {}
        if mode == "edit" and project_id:
            try:
                project_details = get_project_details(project_id)
                folder_path, ifc_folder_path = get_project_folders(project_id)
                existing_data = {
                    'name': project_details.get('project_name', ''),
                    'client_name': project_details.get('client_name', ''),
                    'status': project_details.get('status', ''),
                    'priority': project_details.get('priority', ''),
                    'start_date': project_details.get('start_date', ''),
                    'end_date': project_details.get('end_date', ''),
                    'folder_path': folder_path or '',
                    'ifc_folder_path': ifc_folder_path or ''
                }
            except Exception as e:
                print(f"Error loading project data: {e}")
        basic_frame = ttk.LabelFrame(content_frame, text="?? Basic Project Information", padding=15)
        basic_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(basic_frame, text="Project Name*:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        project_name_var = tk.StringVar(value=existing_data.get('name', ''))
        project_name_entry = ttk.Entry(basic_frame, textvariable=project_name_var, width=50)
        project_name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(basic_frame, text="Client*:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        client_var = tk.StringVar()
        client_combo = ttk.Combobox(basic_frame, textvariable=client_var, width=30, state="readonly")
        client_combo.grid(row=1, column=1, sticky="ew", pady=5)
        try:
            clients = get_available_clients()
            client_names = [f"{client[0]} - {client[1]}" for client in clients]
            client_combo['values'] = client_names
            if existing_data.get('client_name'):
                for client_option in client_names:
                    if existing_data['client_name'] in client_option:
                        client_var.set(client_option)
                        break
        except Exception as e:
            print(f"Error loading clients: {e}")
        ttk.Button(basic_frame, text="+ New Client", command=lambda: self.show_new_client_dialog(client_combo)).grid(row=1, column=2, padx=(10, 0), pady=5)
        ttk.Label(basic_frame, text="Project Type:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=5)
        project_type_var = tk.StringVar()
        project_type_combo = ttk.Combobox(basic_frame, textvariable=project_type_var, width=30)
        project_type_combo.grid(row=2, column=1, sticky="ew", pady=5)
        project_type_combo['values'] = ["Solar PV", "Wind Farm", "Battery Storage", "Hybrid Project", "Transmission", "Other"]
        ttk.Label(basic_frame, text="Area (hectares):").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=5)
        area_var = tk.StringVar()
        area_entry = ttk.Entry(basic_frame, textvariable=area_var, width=20)
        area_entry.grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(basic_frame, text="MW Capacity:").grid(row=3, column=2, sticky="w", padx=(20, 10), pady=5)
        mw_var = tk.StringVar()
        mw_entry = ttk.Entry(basic_frame, textvariable=mw_var, width=20)
        mw_entry.grid(row=3, column=3, sticky="w", pady=5)
        basic_frame.columnconfigure(1, weight=1)
        status_frame = ttk.LabelFrame(content_frame, text="?? Project Status & Timeline", padding=15)
        status_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        status_var = tk.StringVar(value=existing_data.get('status', 'Planning'))
        status_combo = ttk.Combobox(status_frame, textvariable=status_var, width=20)
        status_combo.grid(row=0, column=1, sticky="w", pady=5)
        status_combo['values'] = ["Planning", "Design", "Construction", "Commissioning", "Operational", "Completed", "On Hold", "Cancelled"]
        ttk.Label(status_frame, text="Priority:").grid(row=0, column=2, sticky="w", padx=(20, 10), pady=5)
        priority_var = tk.StringVar(value=existing_data.get('priority', 'Medium'))
        priority_combo = ttk.Combobox(status_frame, textvariable=priority_var, width=15)
        priority_combo.grid(row=0, column=3, sticky="w", pady=5)
        priority_combo['values'] = ["Low", "Medium", "High", "Critical"]
        ttk.Label(status_frame, text="Start Date:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        start_date_var = tk.StringVar(value=existing_data.get('start_date', ''))
        start_date_entry = DateEntry(status_frame, textvariable=start_date_var, width=15, date_pattern='yyyy-mm-dd')
        start_date_entry.grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(status_frame, text="End Date:").grid(row=1, column=2, sticky="w", padx=(20, 10), pady=5)
        end_date_var = tk.StringVar(value=existing_data.get('end_date', ''))
        end_date_entry = DateEntry(status_frame, textvariable=end_date_var, width=15, date_pattern='yyyy-mm-dd')
        end_date_entry.grid(row=1, column=3, sticky="w", pady=5)
        location_frame = ttk.LabelFrame(content_frame, text="?? Location Information", padding=15)
        location_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(location_frame, text="Address:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        address_var = tk.StringVar()
        address_entry = ttk.Entry(location_frame, textvariable=address_var, width=50)
        address_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)
        ttk.Label(location_frame, text="City:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        city_var = tk.StringVar()
        city_entry = ttk.Entry(location_frame, textvariable=city_var, width=20)
        city_entry.grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(location_frame, text="State:").grid(row=1, column=2, sticky="w", padx=(20, 10), pady=5)
        state_var = tk.StringVar()
        state_entry = ttk.Entry(location_frame, textvariable=state_var, width=10)
        state_entry.grid(row=1, column=3, sticky="w", pady=5)
        ttk.Label(location_frame, text="Postcode:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=5)
        postcode_var = tk.StringVar()
        postcode_entry = ttk.Entry(location_frame, textvariable=postcode_var, width=15)
        postcode_entry.grid(row=2, column=1, sticky="w", pady=5)
        location_frame.columnconfigure(1, weight=1)
        paths_frame = ttk.LabelFrame(content_frame, text="?? File Paths", padding=15)
        paths_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(paths_frame, text="Model Folder:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        folder_path_var = tk.StringVar(value=existing_data.get('folder_path', ''))
        folder_path_entry = ttk.Entry(paths_frame, textvariable=folder_path_var, width=50)
        folder_path_entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(paths_frame, text="Browse", command=lambda: self.browse_folder(folder_path_var)).grid(row=0, column=2, padx=(5, 0), pady=5)
        ttk.Label(paths_frame, text="IFC Folder:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        ifc_path_var = tk.StringVar(value=existing_data.get('ifc_folder_path', ''))
        ifc_path_entry = ttk.Entry(paths_frame, textvariable=ifc_path_var, width=50)
        ifc_path_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(paths_frame, text="Browse", command=lambda: self.browse_folder(ifc_path_var)).grid(row=1, column=2, padx=(5, 0), pady=5)
        paths_frame.columnconfigure(1, weight=1)
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        def save_project():
            try:
                if not project_name_var.get().strip():
                    messagebox.showerror("Error", "Project name is required")
                    return
                if not client_var.get():
                    messagebox.showerror("Error", "Please select a client")
                    return
                client_id = client_var.get().split(" - ")[0] if client_var.get() else None
                project_data = {
                    'name': project_name_var.get().strip(),
                    'client_id': client_id,
                    'project_type': project_type_var.get(),
                    'area': area_var.get(),
                    'mw_capacity': mw_var.get(),
                    'status': status_var.get(),
                    'priority': priority_var.get(),
                    'start_date': start_date_var.get(),
                    'end_date': end_date_var.get(),
                    'address': address_var.get(),
                    'city': city_var.get(),
                    'state': state_var.get(),
                    'postcode': postcode_var.get(),
                    'folder_path': folder_path_var.get(),
                    'ifc_folder_path': ifc_path_var.get()
                }
                if mode == "create":
                    success = self.create_project_in_db(project_data)
                    if success:
                        messagebox.showinfo("Success", "Project created successfully!")
                        dialog.destroy()
                        self.refresh_data()
                        project_notification_system.notify_project_list_changed()
                else:
                    success = self.update_project_in_db(project_id, project_data)
                    if success:
                        messagebox.showinfo("Success", "Project updated successfully!")
                        dialog.destroy()
                        self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")
        ttk.Button(button_frame, text="Save", command=save_project).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
        project_name_entry.focus()

    def show_new_client_dialog(self, client_combo=None):
        import tkinter as tk
        from tkinter import ttk, messagebox
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Client")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        title_label = ttk.Label(content_frame, text="Create New Client", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        fields_frame = ttk.Frame(content_frame)
        fields_frame.pack(fill="both", expand=True)
        fields_frame.columnconfigure(1, weight=1)
        client_vars = {}
        ttk.Label(fields_frame, text="Client Name*:").grid(row=0, column=0, sticky="w", pady=5)
        client_vars['name'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['name'], width=40).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(fields_frame, text="Contact Name:").grid(row=1, column=0, sticky="w", pady=5)
        client_vars['contact'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['contact'], width=40).grid(row=1, column=1, sticky="ew", pady=5)

    def show_new_client_dialog(self, client_combo=None):
        """Show dialog to create a new client"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Client")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(content_frame, text="Create New Client", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Form fields
        fields_frame = ttk.Frame(content_frame)
        fields_frame.pack(fill="both", expand=True)
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Client variables
        client_vars = {}
        
        # Client Name
        ttk.Label(fields_frame, text="Client Name*:").grid(row=0, column=0, sticky="w", pady=5)
        client_vars['name'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['name'], width=40).grid(row=0, column=1, sticky="ew", pady=5)
        
        # Contact Name
        ttk.Label(fields_frame, text="Contact Name:").grid(row=1, column=0, sticky="w", pady=5)
        client_vars['contact'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['contact'], width=40).grid(row=1, column=1, sticky="ew", pady=5)
        
        # Contact Email
        ttk.Label(fields_frame, text="Contact Email:").grid(row=2, column=0, sticky="w", pady=5)
        client_vars['email'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['email'], width=40).grid(row=2, column=1, sticky="ew", pady=5)
        
        # Contact Phone
        ttk.Label(fields_frame, text="Contact Phone:").grid(row=3, column=0, sticky="w", pady=5)
        client_vars['phone'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['phone'], width=40).grid(row=3, column=1, sticky="ew", pady=5)
        
        # Address
        ttk.Label(fields_frame, text="Address:").grid(row=4, column=0, sticky="w", pady=5)
        client_vars['address'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['address'], width=40).grid(row=4, column=1, sticky="ew", pady=5)
        
        # City
        ttk.Label(fields_frame, text="City:").grid(row=5, column=0, sticky="w", pady=5)
        client_vars['city'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['city'], width=40).grid(row=5, column=1, sticky="ew", pady=5)
        
        # State
        ttk.Label(fields_frame, text="State:").grid(row=6, column=0, sticky="w", pady=5)
        client_vars['state'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['state'], width=40).grid(row=6, column=1, sticky="ew", pady=5)
        
        # Postcode
        ttk.Label(fields_frame, text="Postcode:").grid(row=7, column=0, sticky="w", pady=5)
        client_vars['postcode'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['postcode'], width=40).grid(row=7, column=1, sticky="ew", pady=5)
        
        def save_client():
            """Save the new client to database"""
            try:
                from database import create_new_client
                
                client_data = {
                    'client_name': client_vars['name'].get().strip(),
                    'contact_name': client_vars['contact'].get().strip(),
                    'contact_email': client_vars['email'].get().strip(),
                    'contact_phone': client_vars['phone'].get().strip(),
                    'address': client_vars['address'].get().strip(),
                    'city': client_vars['city'].get().strip(),
                    'state': client_vars['state'].get().strip(),
                    'postcode': client_vars['postcode'].get().strip(),
                    'country': 'Australia',  # Default country
                }
                
                if not client_data['client_name']:
                    messagebox.showerror("Error", "Client name is required")
                    return
                
                client_id = create_new_client(client_data)
                
                if client_id:
                    messagebox.showinfo("Success", f"Client created successfully! (ID: {client_id})")
                    # Refresh client combo box
                    clients = get_available_clients()
                    client_names = [f"{client[0]} - {client[1]}" for client in clients]
                    client_combo['values'] = client_names
                    # Select the new client
                    new_client_name = client_vars['name'].get().strip()
                    for client_option in client_names:
                        if new_client_name in client_option:
                            client_combo.set(client_option)
                            break
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to create client - check database connection")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create client: {str(e)}")
                print(f"Client creation error: {e}")  # For debugging
        
        # Buttons frame with better spacing
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Create buttons with better styling
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=5)
        
        save_btn = ttk.Button(button_frame, text="Save Client", command=save_client)
        save_btn.pack(side="right", padx=5)
        
        # Focus on client name field
        client_vars['name'].set("")
        dialog.after(100, lambda: dialog.focus_set())

    def create_project_in_db(self, project_data):
        """Create a new project using the shared service layer."""
        try:
            project_service.create_project(project_data)
            return True
        except ProjectValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except ProjectServiceError as exc:
            messagebox.showerror("Error", f"Failed to create project: {exc}")
            logger.exception("Project creation error via service layer")
        except Exception as exc:  # Fallback to catch unexpected issues
            messagebox.showerror("Error", f"Failed to create project: {exc}")
            logger.exception("Unexpected project creation error")
        return False

    def update_project_in_db(self, project_id, project_data):
        """Update an existing project in the database"""
        try:
            project_service.update_project(project_id, project_data)
            print(f"✅ Successfully updated project {project_id}")
            return True
        except ProjectValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except ProjectServiceError as exc:
            print(f"❌ Error updating project {project_id}: {exc}")
            messagebox.showerror("Database Error", f"Failed to update project: {exc}")
        except Exception as exc:
            print(f"❌ Unexpected error updating project {project_id}: {exc}")
            messagebox.showerror("Database Error", f"Failed to update project: {exc}")
        return False

    def browse_folder(self, path_var):
        """Open folder browser dialog and update the path variable"""
        from tkinter import filedialog
        import os
        
        # Get current path as initial directory
        current_path = path_var.get()
        initial_dir = current_path if current_path and os.path.isdir(current_path) else os.path.expanduser("~")
        
        # Open folder dialog
        folder_path = filedialog.askdirectory(
            title="Select Folder",
            initialdir=initial_dir
        )
        
        # Update the variable if a folder was selected
        if folder_path:
            path_var.set(folder_path)
            print(f"📁 Selected folder: {folder_path}")
    
    def setup_ui(self):
        """Set up the project setup interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== TOP SECTION: PROJECT SELECTION =====
        project_frame = ttk.LabelFrame(main_frame, text="Project Selection & Status", padding=15)
        project_frame.pack(fill="x", pady=(0, 15))

        # Current project selection
        selection_frame = ttk.Frame(project_frame)
        selection_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(selection_frame, text="Current Project:", font=("Arial", 10, "bold")).pack(side="left")
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(selection_frame, textvariable=self.project_var, width=50)
        self.project_combo.pack(side="left", padx=(10, 0))
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)

        # Folder path display
        ttk.Label(selection_frame, text="Desktop Connector Folder:", font=("Arial", 10)).pack(side="left", padx=(20, 0))
        self.folder_path_var = tk.StringVar()
        self.folder_path_entry = ttk.Entry(selection_frame, textvariable=self.folder_path_var, width=40, state="readonly")
        self.folder_path_entry.pack(side="left", padx=(10, 0))

        # Project status display
        status_frame = ttk.Frame(project_frame)
        status_frame.pack(fill="x")

        # Left column - basic info
        left_status = ttk.Frame(status_frame)
        left_status.pack(side="left", fill="both", expand=True)

        self.status_labels = {}
        basic_fields = ["Client", "Status", "Priority", "Start Date", "End Date"]
        for i, field in enumerate(basic_fields):
            row_frame = ttk.Frame(left_status)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=f"{field}:", width=12, anchor="w").pack(side="left")
            self.status_labels[field] = ttk.Label(row_frame, text="Not Selected", foreground="gray")
            self.status_labels[field].pack(side="left", padx=(5, 0))

        # Right column - file paths
        right_status = ttk.Frame(status_frame)
        right_status.pack(side="right", fill="both", expand=True)

        path_fields = ["Model Path", "IFC Path"]
        for i, field in enumerate(path_fields):
            row_frame = ttk.Frame(right_status)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=f"{field}:", width=12, anchor="w").pack(side="left")
            self.status_labels[field] = ttk.Label(row_frame, text="Not Configured", foreground="gray", wraplength=300)
            self.status_labels[field].pack(side="left", padx=(5, 0))

        # ===== REVIEW STATUS KPI DASHBOARD =====
        kpi_frame = ttk.LabelFrame(main_frame, text="📊 Review Status Dashboard", padding=15)
        kpi_frame.pack(fill="x", pady=(0, 15))

        # KPI metrics in a grid layout
        kpi_grid = ttk.Frame(kpi_frame)
        kpi_grid.pack(fill="x")

        # Initialize KPI labels
        self.kpi_labels = {}
        
        # Top row - main metrics
        top_row = ttk.Frame(kpi_grid)
        top_row.pack(fill="x", pady=(0, 10))
        
        kpi_metrics = [
            ("Total Services", "0", "blue"),
            ("Total Reviews", "0", "black"),
            ("Completed", "0", "green"),
            ("In Progress", "0", "orange"),
            ("Overdue", "0", "red")
        ]
        
        for i, (label, value, color) in enumerate(kpi_metrics):
            metric_frame = ttk.Frame(top_row)
            metric_frame.pack(side="left", padx=(0, 20))
            
            ttk.Label(metric_frame, text=label + ":", font=("Arial", 9)).pack()
            self.kpi_labels[label] = ttk.Label(metric_frame, text=value, font=("Arial", 12, "bold"), foreground=color)
            self.kpi_labels[label].pack()
        
        # Progress bar section
        progress_frame = ttk.Frame(kpi_frame)
        progress_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(progress_frame, text="Overall Progress:", font=("Arial", 10)).pack(side="left")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=200, mode='determinate')
        self.progress_bar.pack(side="left", padx=(10, 10))
        
        self.kpi_labels["Progress"] = ttk.Label(progress_frame, text="0.0%", font=("Arial", 10, "bold"))
        self.kpi_labels["Progress"].pack(side="left")
        
        # Upcoming reviews section
        upcoming_frame = ttk.Frame(kpi_frame)
        upcoming_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(upcoming_frame, text="Upcoming Reviews (Next 7 Days):", font=("Arial", 9, "bold")).pack(anchor="w")
        self.upcoming_text = tk.Text(upcoming_frame, height=3, wrap="word", state="disabled", font=("Arial", 8))
        self.upcoming_text.pack(fill="x", pady=(5, 0))

        # ===== PROJECT ISSUES OVERVIEW SECTION =====
        issues_frame = ttk.LabelFrame(main_frame, text="Project Issues Overview", padding=15)
        issues_frame.pack(fill="x", pady=(0, 15))

        # Issues summary section
        summary_frame = ttk.Frame(issues_frame)
        summary_frame.pack(fill="x", pady=(0, 10))

        # Left side - Issue statistics
        stats_frame = ttk.Frame(summary_frame)
        stats_frame.pack(side="left", fill="both", expand=True)

        self.issues_stats_labels = {}
        
        # Total issues display
        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(fill="x", pady=2)
        ttk.Label(total_frame, text="Total Issues:", font=("Arial", 10, "bold"), width=15).pack(side="left")
        self.issues_stats_labels["total"] = ttk.Label(total_frame, text="0", foreground="blue", font=("Arial", 10, "bold"))
        self.issues_stats_labels["total"].pack(side="left", padx=(5, 0))

        # ACC Issues
        acc_frame = ttk.Frame(stats_frame)
        acc_frame.pack(fill="x", pady=2)
        ttk.Label(acc_frame, text="ACC Issues:", width=15).pack(side="left")
        self.issues_stats_labels["acc_total"] = ttk.Label(acc_frame, text="0", foreground="gray")
        self.issues_stats_labels["acc_total"].pack(side="left", padx=(5, 0))
        ttk.Label(acc_frame, text="(Open:").pack(side="left", padx=(5, 0))
        self.issues_stats_labels["acc_open"] = ttk.Label(acc_frame, text="0", foreground="red")
        self.issues_stats_labels["acc_open"].pack(side="left")
        ttk.Label(acc_frame, text="Closed:").pack(side="left", padx=(5, 0))
        self.issues_stats_labels["acc_closed"] = ttk.Label(acc_frame, text="0", foreground="green")
        self.issues_stats_labels["acc_closed"].pack(side="left")
        ttk.Label(acc_frame, text=")").pack(side="left")

        # Revizto Issues
        revizto_frame = ttk.Frame(stats_frame)
        revizto_frame.pack(fill="x", pady=2)
        ttk.Label(revizto_frame, text="Revizto Issues:", width=15).pack(side="left")
        self.issues_stats_labels["revizto_total"] = ttk.Label(revizto_frame, text="0", foreground="gray")
        self.issues_stats_labels["revizto_total"].pack(side="left", padx=(5, 0))
        ttk.Label(revizto_frame, text="(Open:").pack(side="left", padx=(5, 0))
        self.issues_stats_labels["revizto_open"] = ttk.Label(revizto_frame, text="0", foreground="red")
        self.issues_stats_labels["revizto_open"].pack(side="left")
        ttk.Label(revizto_frame, text="Closed:").pack(side="left", padx=(5, 0))
        self.issues_stats_labels["revizto_closed"] = ttk.Label(revizto_frame, text="0", foreground="green")
        self.issues_stats_labels["revizto_closed"].pack(side="left")
        ttk.Label(revizto_frame, text=")").pack(side="left")

        # Right side - Recent Issues
        recent_frame = ttk.Frame(summary_frame)
        recent_frame.pack(side="right", fill="both", expand=True)

        ttk.Label(recent_frame, text="Recent Issues:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        # Recent issues listbox with scrollbar
        recent_container = ttk.Frame(recent_frame)
        recent_container.pack(fill="both", expand=True, pady=(5, 0))
        
        self.recent_issues_listbox = tk.Listbox(recent_container, height=6, font=("Arial", 9))
        recent_scrollbar = ttk.Scrollbar(recent_container, orient="vertical", command=self.recent_issues_listbox.yview)
        self.recent_issues_listbox.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_issues_listbox.pack(side="left", fill="both", expand=True)
        recent_scrollbar.pack(side="right", fill="y")

        # Issues action buttons
        issues_actions_frame = ttk.Frame(issues_frame)
        issues_actions_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(issues_actions_frame, text="View All Open Issues", command=self.view_open_issues).pack(side="left", padx=(0, 5))
        ttk.Button(issues_actions_frame, text="View All Closed Issues", command=self.view_closed_issues).pack(side="left", padx=5)
        ttk.Button(issues_actions_frame, text="Refresh Issues", command=self.refresh_issues_overview).pack(side="left", padx=5)

        # ===== MIDDLE SECTION: PROJECT ACTIONS =====
        actions_frame = ttk.LabelFrame(main_frame, text="Project Actions", padding=15)
        actions_frame.pack(fill="x", pady=(0, 15))

        # Action buttons in a grid
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(fill="x")

        action_buttons = [
            ("Create New Project", self.create_new_project, "Create a new project"),
            ("Edit Project Details", self.edit_project_details, "Modify current project information"),
            ("Delete Project", self.delete_project, "Permanently delete the selected project and all related data"),
            ("Configure File Paths", self.configure_paths, "Set model and IFC file locations"),
            ("Extract Files from Model Folder", self.extract_model_files, "Extract files from configured model folder"),
            ("Extract Files from Desktop Connector", self.extract_acc_files, "Extract files from ACC Desktop Connector"),
            ("Refresh Project Data", self.refresh_data, "Reload project information from handlers.database"),
            ("Debug Dropdown", self.debug_dropdown, "Debug project dropdown issues"),
            ("View Project Dashboard", self.view_dashboard, "Open comprehensive project overview"),
            ("Archive Project", self.archive_project, "Archive completed or cancelled project")
        ]

        for i, (text, command, tooltip) in enumerate(action_buttons):
            row = i // 3
            col = i % 3
            btn = ttk.Button(buttons_frame, text=text, command=command, width=25)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        # Configure grid weights
        for i in range(3):
            buttons_frame.columnconfigure(i, weight=1)

        # ===== BOTTOM SECTION: PROJECT DETAILS =====
        details_frame = ttk.LabelFrame(main_frame, text="Project Details", padding=15)
        details_frame.pack(fill="both", expand=True)

        # Create project details display
        self.create_project_details_display(details_frame)

        # Initialize and load projects
        self.refresh_projects()

    def on_project_selected(self, event=None):
        """Handle project selection from dropdown"""
        project_selection = self.project_var.get()
        if project_selection and ' - ' in project_selection:
            project_id = project_selection.split(' - ')[0].strip()
            project_name = project_selection.split(' - ')[1].strip()
            
            # Update folder path
            try:
                folder_path = get_acc_folder_path(project_id)
                self.folder_path_var.set(folder_path if folder_path else "Not configured")
            except Exception as e:
                print(f"Error getting folder path: {e}")
                self.folder_path_var.set("Error loading path")
            
            # Update project status
            self.update_project_status(project_name)
            
            # Update project details
            self.update_project_details(project_id)
            
            # Update issues overview
            self.update_issues_overview(project_id)
            
            # Notify other tabs about project change
            project_notification_system.notify_project_changed(project_selection)

    def update_project_status(self, project_name):
        """Update the status display for selected project"""
        try:
            # Get project details from database
            project_selection = self.project_var.get()
            if project_selection and ' - ' in project_selection:
                project_id = project_selection.split(' - ')[0].strip()
                
                # Try to get project details
                try:
                    project_details = get_project_details(project_id)
                    if project_details:
                        # Update status labels with real data
                        self.status_labels["Client"].config(text=project_details.get('client_name', 'Unknown'), foreground="black")
                        self.status_labels["Status"].config(text=project_details.get('status', 'Unknown'), foreground="black")
                        self.status_labels["Priority"].config(text=project_details.get('priority', 'Normal'), foreground="black")
                        self.status_labels["Start Date"].config(text=str(project_details.get('start_date', 'Not set')), foreground="black")
                        self.status_labels["End Date"].config(text=str(project_details.get('end_date', 'Not set')), foreground="black")
                        
                        # Update KPI dashboard
                        self.update_kpi_dashboard(project_id)
                        
                        # Try to get project folders
                        try:
                            folders = get_project_folders(project_id)
                            if folders and folders[0]:  # Check if folder_path exists
                                self.status_labels["Model Path"].config(text=folders[0], foreground="black")
                            else:
                                self.status_labels["Model Path"].config(text="Not configured", foreground="gray")

                            if folders and folders[1]:  # Check if ifc_folder_path exists
                                self.status_labels["IFC Path"].config(text=folders[1], foreground="black")
                            else:
                                self.status_labels["IFC Path"].config(text="Not configured", foreground="gray")
                        except Exception as e:
                            print(f"Error getting project folders: {e}")
                            self.status_labels["Model Path"].config(text="Error loading", foreground="red")
                            self.status_labels["IFC Path"].config(text="Error loading", foreground="red")
                    else:
                        # No project details found - show basic info
                        self.status_labels["Client"].config(text="Data unavailable", foreground="gray")
                        self.status_labels["Status"].config(text="Active", foreground="black")
                        self.status_labels["Priority"].config(text="Normal", foreground="black")
                        self.status_labels["Start Date"].config(text="Not set", foreground="gray")
                        self.status_labels["End Date"].config(text="Not set", foreground="gray")
                        self.status_labels["Model Path"].config(text="Not configured", foreground="gray")
                        self.status_labels["IFC Path"].config(text="Not configured", foreground="gray")
                except Exception as e:
                    print(f"Error getting project details: {e}")
                    # Show basic info on error
                    self.status_labels["Client"].config(text="Data unavailable", foreground="gray")
                    self.status_labels["Status"].config(text="Active", foreground="black")
                    self.status_labels["Priority"].config(text="Normal", foreground="black")
                    self.status_labels["Start Date"].config(text="Not set", foreground="gray")
                    self.status_labels["End Date"].config(text="Not set", foreground="gray")
                    self.status_labels["Model Path"].config(text="Not configured", foreground="gray")
                    self.status_labels["IFC Path"].config(text="Not configured", foreground="gray")
            else:
                # Clear all status labels
                for field in ["Client", "Status", "Priority", "Start Date", "End Date", "Model Path", "IFC Path"]:
                    self.status_labels[field].config(text="Not selected", foreground="gray")
                    
        except Exception as e:
            print(f"Error updating project status: {e}")
            # Clear status labels on error
            for label in self.status_labels.values():
                label.config(text="Error", foreground="red")

    def update_kpi_dashboard(self, project_id):
        """Update the KPI dashboard with review statistics"""
        try:
            # Initialize review management service if not available
            if not hasattr(self, 'review_service') or not self.review_service:
                from review_management_service import ReviewManagementService
                try:
                    with get_db_connection() as conn:
                        self.review_service = ReviewManagementService(conn)
                except Exception as e:
                    print(f"Could not connect to database for KPI dashboard: {e}")
                    return
            
            # Get project review KPIs
            kpis = self.review_service.get_project_review_kpis(project_id)
            
            # Update KPI labels
            self.kpi_labels["Total Services"].config(text=str(kpis['total_services']))
            self.kpi_labels["Total Reviews"].config(text=str(kpis['total_reviews']))
            self.kpi_labels["Completed"].config(text=str(kpis['completed_reviews']))
            self.kpi_labels["In Progress"].config(text=str(kpis['in_progress_reviews']))
            self.kpi_labels["Overdue"].config(text=str(kpis['overdue_reviews']))
            
            # Update progress bar and percentage
            progress_pct = kpis['overall_completion_percentage']
            self.progress_var.set(progress_pct)
            self.kpi_labels["Progress"].config(text=f"{progress_pct:.1f}%")
            
            # Update upcoming reviews text
            self.upcoming_text.config(state="normal")
            self.upcoming_text.delete(1.0, tk.END)
            
            if kpis['upcoming_reviews']:
                upcoming_text = ""
                for review in kpis['upcoming_reviews'][:5]:  # Show max 5 upcoming reviews
                    upcoming_text += f"• {review['service_name']} - {review['planned_date']} ({review['status']})\n"
                self.upcoming_text.insert(tk.END, upcoming_text.strip())
            else:
                self.upcoming_text.insert(tk.END, "No upcoming reviews in the next 7 days")
            
            self.upcoming_text.config(state="disabled")
            
            # Update colors based on status
            if kpis['overdue_reviews'] > 0:
                self.kpi_labels["Overdue"].config(foreground="red")
            else:
                self.kpi_labels["Overdue"].config(foreground="green")
                
            if progress_pct >= 90:
                self.kpi_labels["Progress"].config(foreground="green")
            elif progress_pct >= 70:
                self.kpi_labels["Progress"].config(foreground="orange")
            else:
                self.kpi_labels["Progress"].config(foreground="black")
                
        except Exception as e:
            print(f"Error updating KPI dashboard: {e}")
            # Show error state
            for label_name in ["Total Services", "Total Reviews", "Completed", "In Progress", "Overdue"]:
                if label_name in self.kpi_labels:
                    self.kpi_labels[label_name].config(text="Error", foreground="red")

    def create_project_details_display(self, parent_frame):
        """Create the project details display with current activities, billing, scope, and completion"""
        # Create scrollable frame for project details
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Initialize detail labels
        self.detail_labels = {}

        # Current activities section
        activities_frame = ttk.LabelFrame(scrollable_frame, text="Current Activities for Month", padding=10)
        activities_frame.pack(fill="x", pady=(0, 10))

        self.detail_labels['activities'] = ttk.Label(activities_frame, text="No project selected",
                                                   font=("Arial", 10), justify="left")
        self.detail_labels['activities'].pack(anchor="w")

        # Billing section - Enhanced with KPIs
        billing_frame = ttk.LabelFrame(scrollable_frame, text="Billing & Progress KPIs", padding=10)
        billing_frame.pack(fill="x", pady=(0, 10))

        # Overall billing summary
        self.detail_labels['billing_summary'] = ttk.Label(billing_frame, text="No project selected",
                                                font=("Arial", 10, "bold"), justify="left")
        self.detail_labels['billing_summary'].pack(anchor="w", pady=(0, 5))
        
        # Current month billing
        self.detail_labels['billing'] = ttk.Label(billing_frame, text="No project selected",
                                                font=("Arial", 10), justify="left")
        self.detail_labels['billing'].pack(anchor="w", pady=(0, 5))

        # Billable by Stage table
        stage_billing_subframe = ttk.Frame(billing_frame)
        stage_billing_subframe.pack(fill="x", pady=(5, 0))
        
        ttk.Label(stage_billing_subframe, text="Billable by Stage:", 
                  font=("Arial", 9, "bold")).pack(anchor="w")
        
        # Create treeview for stage billing
        stage_columns = ("Stage", "Billed Amount")
        self.stage_billing_tree = ttk.Treeview(stage_billing_subframe, columns=stage_columns, 
                                               show="headings", height=4)
        self.stage_billing_tree.heading("Stage", text="Stage/Phase")
        self.stage_billing_tree.heading("Billed Amount", text="Billed Amount")
        self.stage_billing_tree.column("Stage", width=200, anchor="w")
        self.stage_billing_tree.column("Billed Amount", width=150, anchor="e")
        self.stage_billing_tree.pack(fill="x", pady=(2, 0))

        # Scope remaining section
        scope_frame = ttk.LabelFrame(scrollable_frame, text="Scope Remaining", padding=10)
        scope_frame.pack(fill="x", pady=(0, 10))

        self.detail_labels['scope'] = ttk.Label(scope_frame, text="No project selected",
                                              font=("Arial", 10), justify="left")
        self.detail_labels['scope'].pack(anchor="w")

        # Estimated completion section
        completion_frame = ttk.LabelFrame(scrollable_frame, text="Estimated Project Completion", padding=10)
        completion_frame.pack(fill="x", pady=(0, 10))

        self.detail_labels['completion'] = ttk.Label(completion_frame, text="No project selected",
                                                   font=("Arial", 10), justify="left")
        self.detail_labels['completion'].pack(anchor="w")

        # Start automatic refresh timer (every hour)
        self.start_auto_refresh()

    def update_project_details(self, project_id):
        """Update the project details display with current data"""
        try:
            from database import get_project_details_summary, connect_to_db
            from review_management_service import ReviewManagementService
            
            details = get_project_details_summary(project_id)

            # Update current activities
            if details['current_activities']:
                activities_text = "\n".join(f"• {activity}" for activity in details['current_activities'])
            else:
                activities_text = "No activities scheduled for this month"
            self.detail_labels['activities'].config(text=activities_text)

            # Get comprehensive billing KPIs
            try:
                with get_db_connection() as conn:
                    review_service = ReviewManagementService(conn)
                    
                    # Get service progress summary for overall KPIs
                    progress_summary = review_service.get_service_progress_summary(int(project_id))
                    
                    # Calculate totals
                    total_value = sum(s.get('agreed_fee', 0) for s in progress_summary)
                    total_billed = sum(s.get('billed_amount', 0) for s in progress_summary)
                    total_remaining = total_value - total_billed
                    
                    # Overall progress percentage
                    if total_value > 0:
                        overall_progress = (total_billed / total_value) * 100
                    else:
                        overall_progress = 0
                    
                    # Update billing summary
                    billing_summary = (f"Total Project Value: ${total_value:,.0f} | "
                                     f"Billed to Date: ${total_billed:,.0f} ({overall_progress:.1f}%) | "
                                     f"Remaining: ${total_remaining:,.0f}")
                    self.detail_labels['billing_summary'].config(text=billing_summary, foreground="darkblue")
                    
                    # Update current month billing
                    current_month = datetime.now().strftime('%B')
                    if details['billing_amount'] > 0:
                        billing_text = f"This Month ({current_month}): ${details['billing_amount']:,.0f} ({len(details['current_activities'])} reviews)"
                    else:
                        billing_text = f"This Month ({current_month}): No billing due"
                    self.detail_labels['billing'].config(text=billing_text, foreground="black")
                    
                    # Update billable by stage table
                    for item in self.stage_billing_tree.get_children():
                        self.stage_billing_tree.delete(item)
                    
                    stage_billing = review_service.get_billable_by_stage(int(project_id))
                    for stage_data in stage_billing:
                        phase = stage_data.get('phase', 'Unknown')
                        billed = stage_data.get('billed_amount', 0)
                        self.stage_billing_tree.insert('', 'end', values=(phase, f"${billed:,.0f}"))
            except Exception as e:
                print(f"Error getting billing KPIs: {e}")
                # Fallback to basic billing if error occurs
                current_month = datetime.now().strftime('%B')
                if details['billing_amount'] > 0:
                    billing_text = f"${details['billing_amount']:,.0f} to bill for {current_month} ({len(details['current_activities'])}x reviews in {current_month})"
                else:
                    billing_text = f"No billing due for {current_month}"
                self.detail_labels['billing'].config(text=billing_text)
                self.detail_labels['billing_summary'].config(text="Billing KPIs unavailable", foreground="orange")

            # Update scope remaining
            if details['scope_remaining']:
                scope_text = "\n".join(f"• {item}" for item in details['scope_remaining'])
            else:
                scope_text = "No remaining scope identified"
            self.detail_labels['scope'].config(text=scope_text)

            # Update completion estimates
            completion_lines = []
            if details['phase_completion']:
                completion_lines.append(f"Phase 7 completion: {details['phase_completion']}")
            if details['project_completion']:
                completion_lines.append(f"Project completion: {details['project_completion']}")

            if completion_lines:
                completion_text = "\n".join(completion_lines)
            else:
                completion_text = "No completion estimates available"
            self.detail_labels['completion'].config(text=completion_text)

        except Exception as e:
            print(f"Error updating project details: {e}")
            for label in self.detail_labels.values():
                label.config(text="Error loading project details", foreground="red")

    def start_auto_refresh(self):
        """Start automatic refresh timer for project details"""
        # Refresh every hour (3600000 milliseconds)
        self.frame.after(3600000, self.auto_refresh_project_details)

    def auto_refresh_project_details(self):
        """Automatically refresh project details and schedule next refresh"""
        try:
            project_selection = self.project_var.get()
            if project_selection and ' - ' in project_selection:
                project_id = project_selection.split(' - ')[0].strip()
                self.update_project_details(project_id)
        except Exception as e:
            print(f"Error in auto refresh: {e}")

        # Schedule next refresh
        self.frame.after(3600000, self.auto_refresh_project_details)

    def refresh_projects(self):
        """Load available projects into the dropdown"""
        try:
            print("Loading projects from database...")
            projects = get_projects()
            project_list = []
            
            if projects:
                for project in projects:
                    if isinstance(project, dict):
                        project_id = project.get('id', '')
                        project_name = project.get('name', '')
                        if project_id and project_name:
                            project_list.append(f"{project_id} - {project_name}")
                    elif isinstance(project, tuple) and len(project) >= 2:
                        project_list.append(f"{project[0]} - {project[1]}")
                
                print(f"Found {len(project_list)} projects")
                self.project_combo['values'] = project_list
                
                if project_list:
                    self.project_combo.set(project_list[0])
                    self.on_project_selected()
                else:
                    self.project_combo.set("No projects found")
            else:
                print("No projects returned from database")
                self.project_combo['values'] = ["No projects available"]
                self.project_combo.set("No projects available")
                
        except Exception as e:
            print(f"Error loading projects: {e}")
            self.project_combo['values'] = ["Error loading projects"]
            self.project_combo.set("Error loading projects")
            messagebox.showerror("Error", f"Failed to load projects: {e}")

    def configure_paths(self):
        """Configure Desktop Connector folder path for selected project"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        project_id = project_selection.split(' - ')[0].strip()
        project_name = project_selection.split(' - ')[1].strip()
        
        print(f"Configuring path for Project ID: {project_id}, Name: {project_name}")
        
        # Ask user to select Desktop Connector folder
        folder_path = filedialog.askdirectory(
            title=f"Select Desktop Connector Folder for {project_name}",
            initialdir=os.path.expanduser("~")
        )
        
        if folder_path:
            print(f"Selected folder path: {folder_path}")
            try:
                # Save the folder path to database
                success = save_acc_folder_path(project_id, folder_path)
                print(f"Save result: {success}")
                
                if success:
                    self.folder_path_var.set(folder_path)
                    messagebox.showinfo("Success", f"Desktop Connector folder configured:\n{folder_path}")
                    
                    # Test retrieval immediately
                    retrieved_path = get_acc_folder_path(project_id)
                    print(f"Retrieved path verification: {retrieved_path}")
                    
                    if retrieved_path != folder_path:
                        print(f"WARNING: Retrieved path doesn't match saved path!")
                        print(f"Saved: {folder_path}")
                        print(f"Retrieved: {retrieved_path}")
                else:
                    messagebox.showerror("Error", "Failed to save folder path to database")
            except Exception as e:
                print(f"Error saving folder path: {e}")
                messagebox.showerror("Error", f"Failed to save folder path: {e}")
        else:
            print("No folder selected")

    def extract_acc_files(self):
        """Extract Desktop Connector folder contents and override SQL data"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        project_id = project_selection.split(' - ')[0].strip()
        project_name = project_selection.split(' - ')[1].strip()
        
        # Get the configured folder path
        try:
            print(f"Getting folder path for project ID: {project_id}")
            folder_path = get_acc_folder_path(project_id)
            print(f"Retrieved folder path: {folder_path}")
            
            if not folder_path:
                print("No folder path found in database")
                result = messagebox.askyesno("Configure Path", 
                    "No Desktop Connector folder configured for this project.\n\n"
                    "Would you like to configure it now?")
                if result:
                    self.configure_paths()
                return
                
            if not os.path.exists(folder_path):
                print(f"Folder path does not exist: {folder_path}")
                messagebox.showerror("Error", f"Desktop Connector folder does not exist:\n{folder_path}\n\nPlease configure a valid path.")
                return
            
            # Confirm extraction - this will override existing data
            confirm = messagebox.askyesno(
                "Confirm Extraction", 
                f"This will extract all files from the Desktop Connector folder and override existing data in the database for project '{project_name}'.\n\nDo you want to continue?"
            )
            
            if not confirm:
                return
            
            # Show progress dialog and perform extraction
            self._perform_desktop_connector_extraction(project_id, project_name, folder_path)
            
        except Exception as e:
            print(f"Error extracting Desktop Connector files: {e}")
            messagebox.showerror("Error", f"Failed to extract Desktop Connector files: {e}")

    def _perform_desktop_connector_extraction(self, project_id, project_name, folder_path):
        """Perform the Desktop Connector folder extraction with progress tracking"""
        # Create progress window
        progress_window = tk.Toplevel(self.frame)
        progress_window.title("Extracting Desktop Connector Data")
        progress_window.geometry("500x200")
        progress_window.transient(self.frame)
        progress_window.grab_set()
        
        # Center the window
        progress_window.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + 100,
            self.frame.winfo_rooty() + 100
        ))
        
        # Progress frame
        progress_frame = ttk.Frame(progress_window, padding="20")
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(progress_frame, text=f"Extracting data for: {project_name}", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Status label
        status_label = ttk.Label(progress_frame, text="Scanning Desktop Connector folder...")
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Progress text
        progress_text = ttk.Label(progress_frame, text="Initializing...")
        progress_text.pack()
        
        def extraction_thread():
            """Run extraction in separate thread"""
            try:
                # Step 1: Scan for files and collect metadata
                status_label.config(text="Scanning folder structure...")
                progress_window.update()
                
                files_found = []
                total_files_scanned = 0
                
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Get file stats
                            stat = os.stat(file_path)
                            file_size_bytes = stat.st_size
                            file_size_kb = file_size_bytes / 1024
                            date_modified = datetime.fromtimestamp(stat.st_mtime)
                            
                            # Normalize file path for database storage (use forward slashes)
                            normalized_path = file_path.replace('\\', '/')
                            
                            # Ensure the path isn't too long for database field
                            if len(normalized_path) > 500:  # Assuming max field length
                                print(f"Warning: File path too long, truncating: {normalized_path}")
                                normalized_path = normalized_path[:500]
                            
                            # Ensure file name isn't too long
                            file_name_clean = file
                            if len(file_name_clean) > 255:  # Assuming max field length
                                print(f"Warning: File name too long, truncating: {file_name_clean}")
                                file_name_clean = file_name_clean[:255]
                            
                            # Determine file type
                            file_ext = os.path.splitext(file)[1].lower()
                            if file_ext in ['.dwg', '.dxf']:
                                file_type = 'CAD'
                            elif file_ext in ['.rvt', '.rfa', '.rte']:
                                file_type = 'Revit'
                            elif file_ext in ['.ifc', '.ifczip']:
                                file_type = 'IFC'
                            elif file_ext in ['.pdf']:
                                file_type = 'PDF'
                            elif file_ext in ['.doc', '.docx', '.txt']:
                                file_type = 'Document'
                            elif file_ext in ['.xls', '.xlsx', '.csv']:
                                file_type = 'Spreadsheet'
                            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                                file_type = 'Image'
                            elif file_ext in ['.zip', '.rar', '.7z']:
                                file_type = 'Archive'
                            else:
                                file_type = 'Other'
                            
                            # Store file metadata
                            files_found.append({
                                'file_name': file_name_clean,
                                'file_path': normalized_path,
                                'date_modified': date_modified,
                                'file_type': file_type,
                                'file_size_kb': file_size_kb
                            })
                            
                            total_files_scanned += 1
                            
                        except Exception as e:
                            print(f"Warning: Could not process file {file_path}: {str(e)}")
                
                if not files_found:
                    status_label.config(text="No files found in Desktop Connector folder")
                    progress_text.config(text="Complete")
                    time.sleep(2)
                    progress_window.destroy()
                    messagebox.showinfo("No Files", "No files found in the Desktop Connector folder.")
                    return
                
                progress_var.set(20)
                progress_text.config(text=f"20% - Found {len(files_found)} files")
                progress_window.update()
                
                # Step 2: Connect to database
                status_label.config(text="Connecting to database...")
                progress_window.update()
                
                try:
                    with get_db_connection() as conn:
                        progress_var.set(30)
                        progress_text.config(text="30% - Database connected")
                        progress_window.update()
                        
                        # Step 3: Clear existing project files (override)
                        status_label.config(text="Clearing existing file records...")
                        progress_window.update()
                        
                        cursor = conn.cursor()
                        
                        # Import schema constants
                        from constants import schema as S
                        
                        # Clear existing records for this project
                        cursor.execute(f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?", (project_id,))
                        conn.commit()
                        
                        progress_var.set(40)
                        progress_text.config(text="40% - Existing records cleared")
                        progress_window.update()
                        
                        # Step 4: Insert file metadata into tblACCDocs
                        total_files = len(files_found)
                        
                        for i, file_info in enumerate(files_found):
                            status_label.config(text=f"Processing: {file_info['file_name']}")
                            progress_window.update()
                            
                            try:
                                # Debug: Print file info
                                print(f"Inserting file: {file_info['file_name']}")
                                print(f"File path: {file_info['file_path']}")
                                print(f"File type: {file_info['file_type']}")
                                print(f"File size: {file_info['file_size_kb']} KB")
                                print(f"Project ID: {project_id}")
                                
                                # Build the SQL statement
                                sql_statement = f"""
                                    INSERT INTO {S.ACCDocs.TABLE} 
                                    ({S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, {S.ACCDocs.DATE_MODIFIED}, 
                                     {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB}, {S.ACCDocs.CREATED_AT}, {S.ACCDocs.PROJECT_ID})
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """
                                
                                print(f"SQL Statement: {sql_statement}")
                                
                                # Insert file metadata into tblACCDocs
                                cursor.execute(sql_statement, (
                                    file_info['file_name'],
                                    file_info['file_path'],
                                    file_info['date_modified'],
                                    file_info['file_type'],
                                    round(file_info['file_size_kb'], 2),  # Round to 2 decimal places
                                    datetime.now(),
                                    int(project_id)  # Ensure project_id is integer
                                ))
                                
                                print(f"Successfully inserted: {file_info['file_name']}")
                                
                                # Update progress
                                file_progress = 40 + ((i + 1) / total_files) * 50
                                progress_var.set(file_progress)
                                progress_text.config(text=f"{file_progress:.0f}% - {i + 1}/{total_files} files")
                                progress_window.update()
                                
                            except Exception as e:
                                print(f"ERROR: Failed to insert file {file_info['file_name']}: {str(e)}")
                                print(f"File info: {file_info}")
                                # Continue with next file instead of stopping
                                continue
                        
                        # Step 5: Finalize
                        conn.commit()
                        
                        progress_var.set(100)
                        progress_text.config(text="100% - Complete")
                        status_label.config(text="File extraction completed successfully!")
                        progress_window.update()
                        
                        time.sleep(2)
                        progress_window.destroy()
                        
                        # Show success message
                        messagebox.showinfo("Success", 
                            f"Successfully extracted metadata for {total_files} files from Desktop Connector folder.\n\n"
                            f"Project: {project_name}\n"
                            f"Files processed: {total_files}\n"
                            f"Data updated in tblACCDocs table")
                        
                        # Refresh the project data in UI
                        self.refresh_projects()
                except Exception as e:
                    raise Exception(f"Failed to connect to database: {e}")
                
            except Exception as e:
                progress_window.destroy()
                print(f"Desktop Connector extraction failed: {str(e)}")
                messagebox.showerror("Extraction Failed", f"Failed to extract Desktop Connector data:\n{str(e)}")
        
        # Start extraction in thread
        thread = threading.Thread(target=extraction_thread)
        thread.daemon = True
        thread.start()
    
    def refresh_data(self):
        """Refresh all project data"""
        try:
            self.refresh_projects()
            messagebox.showinfo("Success", "Project data refreshed successfully")
        except Exception as e:
            print(f"Error refreshing data: {e}")
            messagebox.showerror("Error", f"Failed to refresh data: {e}")

    def debug_dropdown(self):
        """Debug project dropdown issues"""
        try:
            print("=== Project Dropdown Debug ===")
            projects = get_projects()
            print(f"Raw projects data: {projects}")
            print(f"Projects type: {type(projects)}")
            
            if projects:
                print(f"Number of projects: {len(projects)}")
                for i, project in enumerate(projects):
                    print(f"Project {i}: {project} (type: {type(project)})")
            else:
                print("No projects found")
                
            current_values = self.project_combo['values']
            print(f"Current combo values: {current_values}")
            print(f"Current selection: {self.project_var.get()}")
            print("=== End Debug ===")
            
            messagebox.showinfo("Debug", f"Debug info printed to console.\nCurrent projects: {len(projects) if projects else 0}")
            
        except Exception as e:
            print(f"Error in debug: {e}")
            messagebox.showerror("Error", f"Debug failed: {e}")

    # Additional methods for other functionality
    def create_new_project(self):
        """Open create new project dialog"""
        self.show_project_dialog(mode="create")

    def edit_project_details(self):
        """Open edit project details dialog"""
        project_selection = self.project_var.get()
        if not project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        # Parse project ID from "ID - Name" format
        if " - " in project_selection:
            project_id_str, project_name = project_selection.split(" - ", 1)
            try:
                project_id = int(project_id_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid project selection format")
                return
        else:
            messagebox.showerror("Error", "Invalid project selection format")
            return
        self.show_project_dialog(mode="edit", project_id=project_id)

    def delete_project(self):
        """Delete selected project"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Info", "Delete Project functionality will be implemented in future version")

    def extract_model_files(self):
        """Extract files from model folder"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Info", "Extract Model Files functionality will be implemented in future version")

    def view_dashboard(self):
        """Open project dashboard"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Info", "Project Dashboard functionality will be implemented in future version")

    def archive_project(self):
        """Archive selected project"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Info", "Archive Project functionality will be implemented in future version")

    def update_issues_overview(self, project_id):
        """Update the issues overview section with current project data"""
        try:
            # Get combined issues overview for the project
            issues_data = get_project_combined_issues_overview(project_id)
            
            if not issues_data or 'summary' not in issues_data:
                # Clear display if no data
                self.clear_issues_display()
                return
            
            summary = issues_data['summary']
            recent_issues = issues_data['recent_issues']
            
            # Update statistics labels
            self.issues_stats_labels["total"].config(text=str(summary.get('total_issues', 0)))
            
            # ACC Issues
            acc_stats = summary.get('acc_issues', {})
            self.issues_stats_labels["acc_total"].config(text=str(acc_stats.get('total', 0)))
            self.issues_stats_labels["acc_open"].config(text=str(acc_stats.get('open', 0)))
            self.issues_stats_labels["acc_closed"].config(text=str(acc_stats.get('closed', 0)))
            
            # Revizto Issues
            revizto_stats = summary.get('revizto_issues', {})
            self.issues_stats_labels["revizto_total"].config(text=str(revizto_stats.get('total', 0)))
            self.issues_stats_labels["revizto_open"].config(text=str(revizto_stats.get('open', 0)))
            self.issues_stats_labels["revizto_closed"].config(text=str(revizto_stats.get('closed', 0)))
            
            # Update recent issues list
            self.recent_issues_listbox.delete(0, tk.END)
            for issue in recent_issues[:10]:  # Show only top 10
                # Format the issue for display
                created_date = issue['created_at'].strftime('%m/%d') if issue['created_at'] else 'N/A'
                status_indicator = '🔴' if issue['status'] == 'open' else '🟢'
                source_indicator = '[ACC]' if issue['source'] == 'ACC' else '[REV]'
                
                # Truncate title if too long
                title = issue['title']
                if len(title) > 50:
                    title = title[:47] + '...'
                
                display_text = f"{status_indicator} {source_indicator} {created_date} - {title}"
                self.recent_issues_listbox.insert(tk.END, display_text)
            
            if not recent_issues:
                self.recent_issues_listbox.insert(tk.END, "No recent issues found")
                
        except Exception as e:
            print(f"Error updating issues overview: {e}")
            self.clear_issues_display()
    
    def clear_issues_display(self):
        """Clear the issues overview display"""
        try:
            # Clear all statistics
            for label in self.issues_stats_labels.values():
                label.config(text="0")
            
            # Clear recent issues
            self.recent_issues_listbox.delete(0, tk.END)
            self.recent_issues_listbox.insert(tk.END, "No project selected")
        except Exception as e:
            print(f"Error clearing issues display: {e}")
    
    def refresh_issues_overview(self):
        """Refresh the issues overview for the current project"""
        project_selection = self.project_var.get()
        if project_selection and ' - ' in project_selection:
            project_id = project_selection.split(' - ')[0].strip()
            self.update_issues_overview(project_id)
        else:
            messagebox.showwarning("Warning", "Please select a project first")
    
    def view_open_issues(self):
        """Open a window showing all open issues for the current project"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_id = project_selection.split(' - ')[0].strip()
        self._show_issues_window(project_id, 'open', 'Open Issues')
    
    def view_closed_issues(self):
        """Open a window showing all closed issues for the current project"""
        project_selection = self.project_var.get()
        if not project_selection or ' - ' not in project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_id = project_selection.split(' - ')[0].strip()
        self._show_issues_window(project_id, 'closed', 'Closed Issues')
    
    def _show_issues_window(self, project_id, status, window_title):
        """Show a detailed window with issues filtered by status"""
        try:
            issues = get_project_issues_by_status(project_id, status)
            
            # Create the window
            issues_window = tk.Toplevel(self.frame)
            issues_window.title(f"{window_title} - Project {project_id}")
            issues_window.geometry("1000x600")
            issues_window.transient(self.frame)
            
            # Create treeview for issues
            frame = ttk.Frame(issues_window)
            frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            columns = ("Source", "Issue ID", "Title", "Status", "Created", "Assignee", "Author")
            tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
            
            # Configure column headings and widths
            tree.heading("Source", text="Source")
            tree.heading("Issue ID", text="Issue ID")
            tree.heading("Title", text="Title")
            tree.heading("Status", text="Status")
            tree.heading("Created", text="Created")
            tree.heading("Assignee", text="Assignee")
            tree.heading("Author", text="Author")
            
            tree.column("Source", width=80)
            tree.column("Issue ID", width=80)
            tree.column("Title", width=350)
            tree.column("Status", width=80)
            tree.column("Created", width=120)
            tree.column("Assignee", width=150)
            tree.column("Author", width=100)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack tree and scrollbar
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Populate with issues data
            for issue in issues:
                created_date = issue['created_at'].strftime('%Y-%m-%d %H:%M') if issue['created_at'] else 'N/A'
                tree.insert("", tk.END, values=(
                    issue['source'],
                    str(issue['issue_id']),
                    issue['title'],
                    issue['status'],
                    created_date,
                    issue['assignee'] or 'Unassigned',
                    issue['author'] or 'N/A'
                ))
            
            if not issues:
                tree.insert("", tk.END, values=(
                    "", "", f"No {status} issues found", "", "", "", ""
                ))
            
            # Add summary label
            summary_label = ttk.Label(frame, text=f"Total {status} issues: {len(issues)}")
            summary_label.pack(pady=(10, 0))
            
        except Exception as e:
            print(f"Error showing issues window: {e}")
            messagebox.showerror("Error", f"Failed to load {status} issues: {str(e)}")

class EnhancedTaskManagementTab:
    """Enhanced task management interface with dependencies and progress tracking"""
    
    def __init__(self, parent_notebook):
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        from database import get_projects, save_acc_folder_path, get_acc_folder_path, insert_files_into_tblACCDocs
        
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? Task Management")


        class NestedProjectSetupTab:
            def __init__(self, parent):
                self.frame = ttk.Frame(parent)
                self.project_var = tk.StringVar()
                self.acc_path_var = tk.StringVar()
                self.status_var = tk.StringVar()
                self.setup_ui()

            def setup_ui(self):
                # Project selection
                project_frame = ttk.Frame(self.frame)
                project_frame.pack(fill=tk.X, padx=10, pady=5)
                ttk.Label(project_frame, text="Select Project:").pack(side=tk.LEFT)
                self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, state="readonly")
                self.project_combo.pack(side=tk.LEFT, padx=5)
                self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
                self.refresh_projects()

                # ACC folder path configuration
                path_frame = ttk.Frame(self.frame)
                path_frame.pack(fill=tk.X, padx=10, pady=5)
                ttk.Label(path_frame, text="ACC Folder Path:").pack(side=tk.LEFT)
                self.acc_path_entry = ttk.Entry(path_frame, textvariable=self.acc_path_var, width=50)
                self.acc_path_entry.pack(side=tk.LEFT, padx=5)
                self.acc_path_button = ttk.Button(path_frame, text="Configure Path", command=self.configure_paths)
                self.acc_path_button.pack(side=tk.LEFT, padx=5)

                # Status label
                status_frame = ttk.Frame(self.frame)
                status_frame.pack(fill=tk.X, padx=10, pady=5)
                self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
                self.status_label.pack(side=tk.LEFT)

                # Extract files button
                extract_frame = ttk.Frame(self.frame)
                extract_frame.pack(fill=tk.X, padx=10, pady=5)
                self.extract_button = ttk.Button(extract_frame, text="Extract ACC Files", command=self.extract_acc_files)
                self.extract_button.pack(side=tk.LEFT)

            def refresh_projects(self):
                projects = get_projects()
                self.project_combo['values'] = [f"{p['ProjectID']} - {p['ProjectName']}" for p in projects]
                if projects:
                    self.project_combo.current(0)
                    self.on_project_selected()

            def on_project_selected(self, event=None):
                selected = self.project_var.get()
                if '-' in selected:
                    project_id = selected.split('-')[0].strip()
                    folder_path = get_acc_folder_path(project_id)
                    self.acc_path_var.set(folder_path if folder_path else "")
                    self.status_var.set(f"Selected Project: {selected}")
                else:
                    messagebox.showerror("Error", "Invalid project selection format")

            def configure_paths(self):
                selected = self.project_var.get()
                if '-' not in selected:
                    messagebox.showwarning("Warning", "Please select a project first")
                    return
                project_id = selected.split('-')[0].strip()
                folder_path = filedialog.askdirectory(title="Select Desktop Connector Folder")
                if not folder_path:
                    messagebox.showwarning("Warning", "No folder selected")
                    return
                save_acc_folder_path(project_id, folder_path)
                self.acc_path_var.set(folder_path)
                self.status_var.set(f"Configured folder for project {project_id}")
                messagebox.showinfo("Success", f"Desktop Connector folder path saved for project {project_id}")

            def extract_acc_files(self):
                selected = self.project_var.get()
                if '-' not in selected:
                    messagebox.showwarning("Warning", "Please select a project first")
                    return
                project_id = selected.split('-')[0].strip()
                folder_path = self.acc_path_var.get()
                if not folder_path:
                    messagebox.showwarning("Warning", "No folder path configured")
                    return
                try:
                    count = insert_files_into_tblACCDocs(project_id, folder_path)
                    self.status_var.set(f"Extracted {count} files for project {project_id}")
                    messagebox.showinfo("Success", f"Extracted {count} files for project {project_id}")
                except Exception as e:
                    self.status_var.set(f"Error extracting files: {e}")
                    messagebox.showerror("Error", f"Failed to extract files: {e}")
            
            # Create scrollable frame for task management
            from ui.ui_helpers import create_scrollable_frame
            scrollable_frame = create_scrollable_frame(self.frame)
            
            # Task list frame
            task_list_frame = ttk.Frame(scrollable_frame)
            task_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Task tree view
            columns = ("Task", "Priority", "Progress", "Status", "Assigned", "Start", "End", "Health")
            self.task_tree = ttk.Treeview(task_list_frame, columns=columns, show="tree headings", height=10)
            
            # Configure columns
            self.task_tree.heading("#0", text="ID")
            self.task_tree.column("#0", width=50)
            
            for col in columns:
                self.task_tree.heading(col, text=col)
                self.task_tree.column(col, width=100)
            
            # Add scrollbar to tree
            task_scrollbar = ttk.Scrollbar(task_list_frame, orient="vertical", command=self.task_tree.yview)
            self.task_tree.configure(yscrollcommand=task_scrollbar.set)
            
            self.task_tree.pack(side="left", fill="both", expand=True)
            task_scrollbar.pack(side="right", fill="y")
            
            # Task details and progress update
            task_details_frame = ttk.LabelFrame(scrollable_frame, text="Task Progress Update", padding=10)
            task_details_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(task_details_frame, text="Progress %:").grid(row=0, column=0, sticky="w", padx=5)
            self.progress_var = tk.StringVar()
            progress_entry = ttk.Entry(task_details_frame, textvariable=self.progress_var, width=10)
            progress_entry.grid(row=0, column=1, padx=5)
            
            ttk.Label(task_details_frame, text="Actual Hours:").grid(row=0, column=2, sticky="w", padx=5)
            self.actual_hours_var = tk.StringVar()
            actual_hours_entry = ttk.Entry(task_details_frame, textvariable=self.actual_hours_var, width=10)
            actual_hours_entry.grid(row=0, column=3, padx=5)
            
            ttk.Label(task_details_frame, text="Comment:").grid(row=1, column=0, sticky="nw", padx=5)
            self.comment_text = tk.Text(task_details_frame, height=2, width=50)
            self.comment_text.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
            
            update_btn = ttk.Button(task_details_frame, text="Update Progress", command=self.update_task_progress)
            update_btn.grid(row=2, column=0, columnspan=4, pady=5)
            
            task_details_frame.columnconfigure(1, weight=1)
            
            # Bind tree selection
            self.task_tree.bind("<<TreeviewSelect>>", self.on_task_selected)
    
    def refresh_data(self):
        """Refresh project and user data"""
        # Load projects
        set_combo_from_pairs(self.project_combo, get_projects())
        
        # Populate assigned users and predecessor tasks
        set_combo_from_pairs(self.assigned_to_combo, get_users_list())
        self.predecessor_combo['values'] = []

        # Load tasks for the current project if selected
        if hasattr(self, 'current_project_id'):
            self.load_project_tasks()

    def load_project_tasks(self):
            """Load tasks for the selected project and update the treeview"""
            clear_treeview(self.task_tree)
            if not hasattr(self, 'current_project_id'):
                return

            tasks = self.task_mgr.get_project_tasks(self.current_project_id)
            self.predecessor_combo['values'] = [
                f"{t['task_id']} - {t['task_name']}" for t in tasks
            ]

            health_colors = {
                'Healthy': '✅',
                'Warning': '⚠️',
                'Critical': '❌',
                'Overdue': '⏰'
            }

            for task in tasks:
                progress_display = f"{task.get('progress_percentage', 0)}%"
                if task.get('estimated_hours') and task.get('actual_hours'):
                    variance = task['actual_hours'] - task['estimated_hours']
                    if variance != 0:
                        progress_display += f" ({variance:+.1f}h)"
    
                health_icon = health_colors.get(task.get('health_status', ''), '?')
                values = (
                    task.get('task_name', ''),
                    task.get('priority', ''),
                    progress_display,
                    task.get('status', ''),
                    task.get('assigned_to_name', ''),
                    str(task.get('start_date', '')),
                    str(task.get('end_date', '')),
                    health_icon
                )
                self.task_tree.insert("", "end", text=str(task.get('task_id', '')), values=values)
    
    def on_task_selected(self, event=None):
        """Handle task selection in the tree"""
        selection = self.task_tree.selection()
        if selection:
            item = self.task_tree.item(selection[0])
            self.selected_task_id = int(item['text'])
            # Optionally populate task details for editing
    
    def create_task(self):
        """Create a new task"""
        if not hasattr(self, 'current_project_id'):
            messagebox.showerror("Error", "Please select a project first")
            return
        # Get assigned user ID
        assigned_to = parse_id_from_display(self.assigned_to_var.get())
        # Get predecessor task ID
        predecessor_id = parse_id_from_display(self.predecessor_var.get())
        
        task_data = {
            'task_name': self.task_name_entry.get().strip(),
            'project_id': self.current_project_id,
            'start_date': self.start_date_entry.get_date(),
            'end_date': self.end_date_entry.get_date(),
            'assigned_to': assigned_to,
            'priority': self.priority_var.get(),
            'estimated_hours': float(self.estimated_hours_entry.get() or 0),
            'predecessor_task_id': predecessor_id,
            'description': self.description_text.get(1.0, tk.END).strip(),
            'status': 'Not Started'
        }
        
        if not task_data['task_name']:
            messagebox.showerror("Error", "Task name is required")
            return
        
        success = self.task_mgr.create_task_with_dependencies(task_data)
        if success:
            messagebox.showinfo("Success", "Task created successfully!")
            self.clear_task_form()
            self.load_project_tasks()
        else:
            messagebox.showerror("Error", "Failed to create task")
    
    def update_task_progress(self):
        """Update task progress"""
        if not hasattr(self, 'selected_task_id'):
            messagebox.showerror("Error", "Please select a task first")
            return
        
        try:
            progress = int(self.progress_var.get() or 0)
            actual_hours = float(self.actual_hours_var.get() or 0) if self.actual_hours_var.get() else None
            comment = self.comment_text.get(1.0, tk.END).strip()
            
            success = self.task_mgr.update_task_progress(
                self.selected_task_id, progress, actual_hours, comment, user_id=1  # Default user
            )
            
            if success:
                messagebox.showinfo("Success", "Task progress updated!")
                self.load_project_tasks()
                self.comment_text.delete(1.0, tk.END)
            else:
                messagebox.showerror("Error", "Failed to update task progress")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
    
    def clear_task_form(self):
        """Clear the task creation form"""
        self.task_name_entry.delete(0, tk.END)
        self.priority_var.set("Medium")
        self.estimated_hours_entry.delete(0, tk.END)
        self.assigned_to_var.set("")
        self.predecessor_var.set("")
        self.description_text.delete(1.0, tk.END)
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection and notify other tabs"""
        project_selection = self.project_combo.get()
        if project_selection:
            project_notification_system.notify_project_changed(project_selection)
    
    def on_project_changed(self, project_selection):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != project_selection:
            self.project_var.set(project_selection)
        self.refresh_project_data()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()
    
    def refresh_project_data(self):
        """Refresh data when project changes"""
        if " - " not in self.project_combo.get():
            return

        # Sync current project id and reload tasks using DB-backed hierarchy
        try:
            project_id = int(self.project_combo.get().split(" - ")[0])
            self.current_project_id = project_id
            self.load_project_tasks()
        except Exception as e:
            logger.error("Error refreshing project data: %s", e)

class ResourceManagementTab:
    """Resource allocation and workload management interface"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? Resources")
        
        self.resource_mgr = ResourceManager()
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Setup resource management UI"""
        
        # === Filters ===
        filter_frame = ttk.LabelFrame(self.frame, text="Filters", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=0, sticky="w", padx=5)
        self.start_date_filter = DateEntry(filter_frame, width=12, date_pattern='yyyy-mm-dd')
        self.start_date_filter.grid(row=0, column=1, padx=5)
        
        ttk.Label(filter_frame, text="to").grid(row=0, column=2, padx=5)
        self.end_date_filter = DateEntry(filter_frame, width=12, date_pattern='yyyy-mm-dd',
                                       date=datetime.now() + timedelta(days=30))
        self.end_date_filter.grid(row=0, column=3, padx=5)
        
        refresh_btn = ttk.Button(filter_frame, text="Refresh", command=self.refresh_resource_data)
        refresh_btn.grid(row=0, column=4, padx=10)
        
        # === Resource Utilization View ===
        resource_frame = ttk.LabelFrame(self.frame, text="Resource Utilization", padding=10)
        resource_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("Name", "Role", "Department", "Capacity", "Allocated", "Utilization", "Status", "Available")
        self.resource_tree = ttk.Treeview(resource_frame, columns=columns, show="tree headings", height=12)
        
        self.resource_tree.heading("#0", text="ID")
        self.resource_tree.column("#0", width=40)
        
        for col in columns:
            self.resource_tree.heading(col, text=col)
            self.resource_tree.column(col, width=100)
        
        resource_scrollbar = ttk.Scrollbar(resource_frame, orient="vertical", command=self.resource_tree.yview)
        self.resource_tree.configure(yscrollcommand=resource_scrollbar.set)
        
        self.resource_tree.pack(side="left", fill="both", expand=True)
        resource_scrollbar.pack(side="right", fill="y")
        
        # === Resource Search ===
        search_frame = ttk.LabelFrame(self.frame, text="Find Available Resources", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="Required Skills:").grid(row=0, column=0, sticky="w", padx=5)
        self.skills_entry = ttk.Entry(search_frame, width=30)
        self.skills_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(search_frame, text="Role Level:").grid(row=0, column=2, sticky="w", padx=5)
        self.role_var = tk.StringVar()
        role_combo = ttk.Combobox(search_frame, textvariable=self.role_var,
                                values=["", "Junior", "Mid", "Senior", "Lead", "Manager"], width=15)
        role_combo.grid(row=0, column=3, padx=5)
        
        ttk.Label(search_frame, text="Max Utilization %:").grid(row=0, column=4, sticky="w", padx=5)
        self.max_util_var = tk.StringVar(value="80")
        util_entry = ttk.Entry(search_frame, textvariable=self.max_util_var, width=10)
        util_entry.grid(row=0, column=5, padx=5)
        
        search_btn = ttk.Button(search_frame, text="Find Available", command=self.find_available_resources)
        search_btn.grid(row=0, column=6, padx=10)
        
        # === Summary Stats ===
        stats_frame = ttk.LabelFrame(self.frame, text="Resource Summary", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="No data loaded", font=("Arial", 10))
        self.stats_label.pack(pady=5)
    
    def refresh_data(self):
        """Initial data refresh"""
        self.refresh_resource_data()
    
    def refresh_resource_data(self):
        """Refresh resource utilization data"""
        start_date = self.start_date_filter.get_date()
        end_date = self.end_date_filter.get_date()
        
        # Clear existing items
        clear_treeview(self.resource_tree)
        
        # Load resource data
        resources = self.resource_mgr.get_resource_workload(
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time())
        )
        
        # Summary statistics
        total_resources = len(resources)
        overallocated = sum(1 for r in resources if r['is_overallocated'])
        avg_utilization = sum(r['utilization_percentage'] for r in resources) / total_resources if total_resources > 0 else 0
        
        # Status colors
        status_colors = {
            'Overallocated': '??',
            'High': '??',
            'Medium': '??',
            'Low': '??'
        }
        
        # Populate tree
        for resource in resources:
            status_icon = status_colors.get(resource['workload_status'], '?')
            values = (
                resource.get('name', ''),
                resource.get('role', ''),
                resource.get('department', ''),
                f"{resource.get('capacity_hours', 0):.1f}h",
                f"{resource.get('allocated_hours', 0):.1f}h",
                f"{resource.get('utilization_percentage', 0):.1f}%",
                status_icon,
                f"{resource.get('available_hours', 0):.1f}h"
            )
            self.resource_tree.insert("", "end", text=str(resource.get('user_id', '')), values=values)
        
        # Update summary
        summary_text = f"Total Resources: {total_resources} | Overallocated: {overallocated} | Avg Utilization: {avg_utilization:.1f}%"
        self.stats_label.config(text=summary_text)
    
    def find_available_resources(self):
        """Find available resources based on search criteria"""
        required_skills = self.skills_entry.get().strip() if hasattr(self, 'skills_entry') else ''
        role_level = self.role_var.get() if hasattr(self, 'role_var') else ''
        try:
            max_utilization = float(self.max_util_var.get() or 100) if hasattr(self, 'max_util_var') else 100
        except ValueError:
            max_utilization = 100
        
        available = self.resource_mgr.find_available_resources(
            required_skills=required_skills,
            role_level=role_level,
            max_utilization=max_utilization
        )

        if available:
            result_text = f"Found {len(available)} available resources:\n\n"
            for resource in available[:5]:  # Show top 5
                result_text += f"• {resource['name']} ({resource['role_level']})\n"
                result_text += f"   Utilization: {resource['utilization_percentage']:.1f}%\n"
                result_text += f"   Available: {resource['available_hours']:.1f} hours\n"
                if resource['skills']:
                    result_text += f"   Skills: {resource['skills']}\n"
                result_text += "\n"
        else:
            result_text = "No available resources found matching the criteria."

        # Show results in a popup
        result_window = tk.Toplevel(self.frame)
        result_window.title("Available Resources")
        result_window.geometry("400x300")

        text_widget = tk.Text(result_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert(1.0, result_text)
        text_widget.config(state="disabled")
    
    def refresh_data(self):
        """Refresh resource data"""
        self.refresh_resource_data()
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection"""
        self.refresh_data()
        
        # Notify other tabs about the project change
        if hasattr(self, 'project_var'):
            project_notification_system.notify_project_changed(self.project_var.get())
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        # ResourceManagementTab may not have project selection, but implement for completeness
        self.refresh_data()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()


class ACCFolderManagementTab:
    """ACC Folder Management and Data Import Interface"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? ACC Folders")
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Setup the ACC folder management UI"""
        
        # === Project Selection ===
        project_frame = ttk.LabelFrame(self.frame, text="Project Selection", padding=10)
        project_frame.pack(fill="x", padx=10, pady=5)
        
        projects = format_id_name_list(get_projects())
        ttk.Label(project_frame, text="Select Project:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, values=projects, width=50)
        self.project_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected_local)
        
        project_frame.columnconfigure(1, weight=1)
        
        # === ACC Data Export Path ===
        export_frame = ttk.LabelFrame(self.frame, text="ACC Data Export Configuration", padding=10)
        export_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(export_frame, text="ACC Data Export Folder:").grid(row=0, column=0, sticky="w", padx=5)
        self.export_path_entry = ttk.Entry(export_frame, width=60)
        self.export_path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        def browse_export_folder():
            path = filedialog.askdirectory(title="Select ACC Data Export Folder")
            if path:
                self.export_path_entry.delete(0, tk.END)
                self.export_path_entry.insert(0, path)
        
        def save_export_path():
            if " - " not in self.project_combo.get():
                messagebox.showerror("Error", "Select a project first")
                return
            pid = self.project_combo.get().split(" - ")[0]
            path = self.export_path_entry.get().strip()
            if not path or not os.path.isdir(path):
                messagebox.showerror("Error", "Select a valid folder")
                return
            save_acc_folder_path(pid, path)
            messagebox.showinfo("Success", "ACC data export path saved")
        
        ttk.Button(export_frame, text="Browse", command=browse_export_folder).grid(row=0, column=2, padx=5)
        ttk.Button(export_frame, text="Save Path", command=save_export_path).grid(row=0, column=3, padx=5)
        
        export_frame.columnconfigure(1, weight=1)
        
        # === ACC CSV Import Section ===
        import_frame = ttk.LabelFrame(self.frame, text="ACC Issues ZIP Import", padding=10)
        import_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(import_frame, text="ACC Issues ZIP File:").grid(row=0, column=0, sticky="w", padx=5)
        self.import_path_entry = ttk.Entry(import_frame, width=60)
        self.import_path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        CreateToolTip(self.import_path_entry, "Select the ZIP file manually downloaded from ACC containing Issues data")
        
        def browse_import_zip():
            filetypes = [("ZIP files", "*.zip"), ("All files", "*.*")]
            path = filedialog.askopenfilename(
                title="Select ACC Issues ZIP File", 
                filetypes=filetypes
            )
            if path and path.lower().endswith(".zip"):
                self.import_path_entry.delete(0, tk.END)
                self.import_path_entry.insert(0, path)
        
        def import_acc_issues():
            zip_file = self.import_path_entry.get().strip()
            if not zip_file or not (os.path.isfile(zip_file) and zip_file.lower().endswith(".zip")):
                messagebox.showerror("Error", "Please select a valid ACC Issues ZIP file")
                return
            
            if " - " not in self.project_combo.get():
                messagebox.showerror("Error", "Please select a project first")
                return
            
            try:
                # Import the ZIP file focusing on issues data
                success, msg = run_acc_import(self.project_combo, self.import_path_entry, self.log_listbox)
                if success:
                    messagebox.showinfo("Success", f"ACC Issues imported successfully!\n\nData is now available in:\nacc_data_schema.dbo.vw_issues_expanded_pm")
                    self.refresh_import_logs()
                    
                    # Show import summary with focus on issues
                    self.show_issues_import_summary()
                else:
                    messagebox.showerror("Error", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import ACC Issues: {str(e)}")
        
        ttk.Button(import_frame, text="Browse ZIP", command=browse_import_zip).grid(row=0, column=2, padx=5)
        ttk.Button(import_frame, text="Import ACC Issues", command=import_acc_issues).grid(row=0, column=3, padx=5)
        
        import_frame.columnconfigure(1, weight=1)
        
        # === Issues Data Preview ===
        preview_frame = ttk.LabelFrame(self.frame, text="Issues Data Preview (from acc_data_schema.dbo.vw_issues_expanded_pm)", padding=10)
        preview_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(preview_frame, text="Preview Issues Data", command=self.preview_issues_data).pack(pady=5)
        
        # Preview text area
        self.preview_text = tk.Text(preview_frame, height=6, width=80, wrap=tk.WORD)
        self.preview_text.pack(fill="x", pady=5)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_text.xview)
        self.preview_text.configure(xscrollcommand=preview_scroll.set)
        preview_scroll.pack(fill="x")
        
        import_frame.columnconfigure(1, weight=1)
        
        # === Import History ===
        history_frame = ttk.LabelFrame(self.frame, text="Import History", padding=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_listbox = tk.Listbox(history_frame, height=10)
        self.log_listbox.pack(side="left", fill="both", expand=True)
        
        log_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        if " - " not in self.project_combo.get():
            return
        
        pid = self.project_combo.get().split(" - ")[0]
        folder = get_acc_folder_path(pid)
        
        # Load saved export path
        self.export_path_entry.delete(0, tk.END)
        self.export_path_entry.insert(0, folder or "")
        
        # Refresh import logs
        self.refresh_import_logs()
    
    def refresh_import_logs(self):
        """Refresh the import logs display"""
        if " - " not in self.project_combo.get():
            return
        
        pid = self.project_combo.get().split(" - ")[0]
        self.log_listbox.delete(0, tk.END)
        
        logs = get_acc_import_logs(pid)
        if logs:
            for folder_name, date, summary in logs:
                self.log_listbox.insert(tk.END, f"? {folder_name} @ {date.strftime('%Y-%m-%d %H:%M')}")
        else:
            self.log_listbox.insert(tk.END, "No previous ACC imports found.")
    
    def show_issues_import_summary(self):
        """Show summary of imported issues data"""
        try:
            with get_db_connection("acc_data_schema") as conn:
                cursor = conn.cursor()
                
                # Query the issues view for summary
                cursor.execute("""
                    SELECT TOP 5
                        issue_number,
                        title,
                        issue_type,
                        status,
                        created_at
                    FROM dbo.vw_issues_expanded_pm
                    ORDER BY created_at DESC
                """)
                
                results = cursor.fetchall()
                
                if results:
                    summary = "Latest 5 imported issues:\n\n"
                    for issue_num, title, issue_type, status, created_at in results:
                        summary += f"#{issue_num}: {title[:50]}... ({issue_type}, {status})\n"
                    
                    messagebox.showinfo("Import Summary", summary)
                else:
                    messagebox.showinfo("Import Summary", "No issues found in the imported data")
        except Exception as e:
            logger.error("Error showing issues summary: %s", e)
    
    def preview_issues_data(self):
        """Preview issues data from acc_data_schema database"""
        try:
            try:
                with get_db_connection("acc_data_schema") as conn:
                    cursor = conn.cursor()
                    
                    # Query the issues view
                    cursor.execute("""
                        SELECT TOP 10
                            issue_number,
                            title,
                            issue_type,
                            status,
                            assigned_to,
                            created_at
                        FROM dbo.vw_issues_expanded_pm
                        ORDER BY created_at DESC
                    """)
                    
                    results = cursor.fetchall()
                    
                    # Display results
                    self.preview_text.delete(1.0, tk.END)
                    
                    if results:
                        preview_content = f"Found {len(results)} recent issues in acc_data_schema.dbo.vw_issues_expanded_pm:\n\n"
                        
                        for issue_num, title, issue_type, status, assigned_to, created_at in results:
                            preview_content += f"#{issue_num}: {title[:40]}...\n"
                            preview_content += f"   Type: {issue_type} | Status: {status} | Assigned: {assigned_to}\n"
                            preview_content += f"   Created: {created_at}\n\n"
                        
                        self.preview_text.insert(1.0, preview_content)
                    else:
                        self.preview_text.insert(1.0, "No issues data found in acc_data_schema.dbo.vw_issues_expanded_pm\n\nPlease import ACC Issues ZIP file first.")
            except Exception as e:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, f"? Cannot connect to acc_data_schema database: {str(e)}")
                
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"? Error querying issues data: {str(e)}")
    
    def refresh_data(self):
        """Refresh all data in the tab"""
        # Update project dropdown
        projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
        self.project_combo['values'] = projects
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection"""
        self.refresh_data()
        
        # Notify other tabs about the project change
        project_notification_system.notify_project_changed(self.project_var.get())
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.refresh_data()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()

class ReviewManagementTab:
    """Enhanced Review Management Interface with Service Templates and Advanced Planning"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? Review Management")
        
        self.current_project_id = None
        self.current_cycle_id = None
        self.review_service = None
        self.auto_complete_candidates = []
        self.operation_manager = TabOperationManager()
        
        # Initialize missing UI components to prevent attribute errors
        self.summary_vars = {
            "Project Name": tk.StringVar(value=""),
            "Construction Stage": tk.StringVar(value=""),
            "Total Services": tk.StringVar(value="0"),
            "Active Reviews": tk.StringVar(value="0"),
            "Completed Reviews": tk.StringVar(value="0"),
            "Overall Progress": tk.StringVar(value="0%")
        }
        
        # Create a placeholder tasks tree (will be properly initialized if needed)
        self.tasks_tree = None
        
        # Initialize resource manager
        try:
            from phase1_enhanced_database import ResourceManager
            self.resource_mgr = ResourceManager()
        except ImportError:
            self.resource_mgr = None
        
        self.setup_ui()
        self.refresh_data()
        
        # Initialize background sync for automatic updates
        self._last_services_signature = ""
        self.frame.after(5000, self.start_background_sync)  # Start after 5 seconds
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def clear_stages(self):
        """Clear all stages from the stages tree"""
        try:
            for item in self.stages_tree.get_children():
                self.stages_tree.delete(item)
            messagebox.showinfo("Success", "Stages cleared successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error clearing stages: {e}")
    
    def setup_ui(self):
        """Set up the comprehensive review management interface"""
        # Create main notebook for sub-tabs
        self.sub_notebook = ttk.Notebook(self.frame)
        self.sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Service Setup & Templates
        self.setup_service_template_tab()
        
        # Tab 2: Review Planning & Scheduling
        self.setup_review_planning_tab()
        
        # Tab 3: Review Execution & Tracking
        self.setup_review_tracking_tab()
        
        # Tab 4: Billing & Progress
        self.setup_billing_tab()
    
    def setup_service_template_tab(self):
        """Setup the Service Templates and Project Services tab"""
        service_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(service_frame, text="Service Setup")
        
        # Project Selection Frame
        project_frame = ttk.LabelFrame(service_frame, text="Project Selection", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(project_frame, text="Project:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)
        
        # Service Template Frame
        template_frame = ttk.LabelFrame(service_frame, text="Service Templates", padding=10)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Template selection
        ttk.Label(template_frame, text="Available Templates:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, width=40, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Template action buttons
        ttk.Button(template_frame, text="Load Template", command=self.load_template).grid(row=0, column=2, padx=5)
        ttk.Button(template_frame, text="Apply to Project", command=self.apply_template).grid(row=0, column=3, padx=5)
        ttk.Button(template_frame, text="Save as Template", command=self.save_as_template).grid(row=0, column=4, padx=5)
        ttk.Button(template_frame, text="Clear All Services", command=self.clear_services).grid(row=0, column=5, padx=5)
        
        # Current Project Services Frame
        services_frame = ttk.LabelFrame(service_frame, text="Current Project Services", padding=10)
        services_frame.pack(fill=tk.BOTH, expand=True)
        
        # Services treeview
        service_columns = ("Service ID", "Phase", "Service Code", "Service Name", "Unit Type", "Qty", "Rate", "Fee", "Status", "Start", "End", "Frequency")
        self.services_tree = ttk.Treeview(services_frame, columns=service_columns, show="headings", height=8)
        
        for col in service_columns:
            self.services_tree.heading(col, text=col)
            if col in ["Service ID", "Qty"]:
                width = 80
            elif col in ["Rate", "Fee"]:
                width = 100
            elif col in ["Start", "End", "Frequency"]:
                width = 110
            else:
                width = 150
            self.services_tree.column(col, width=width, anchor="w")

        
        # Scrollbars for services
        services_v_scroll = ttk.Scrollbar(services_frame, orient=tk.VERTICAL, command=self.services_tree.yview)
        services_h_scroll = ttk.Scrollbar(services_frame, orient=tk.HORIZONTAL, command=self.services_tree.xview)
        self.services_tree.configure(yscrollcommand=services_v_scroll.set, xscrollcommand=services_h_scroll.set)
        
        self.services_tree.grid(row=0, column=0, sticky="nsew")
        services_v_scroll.grid(row=0, column=1, sticky="ns")
        services_h_scroll.grid(row=1, column=0, sticky="ew")
        
        services_frame.grid_rowconfigure(0, weight=1)
        services_frame.grid_columnconfigure(0, weight=1)
        
        # Service action buttons
        service_buttons_frame = ttk.Frame(services_frame)
        service_buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Button(service_buttons_frame, text="Add Service", command=self.add_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(service_buttons_frame, text="Edit Service", command=self.edit_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(service_buttons_frame, text="Delete Service", command=self.delete_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(service_buttons_frame, text="Update Status", command=self.update_service_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(service_buttons_frame, text="Generate Reviews", command=self.generate_reviews_from_services).pack(side=tk.LEFT, padx=5)
        ttk.Button(service_buttons_frame, text="Refresh Status", command=self.manual_refresh_statuses).pack(side=tk.LEFT, padx=5)
    

    def setup_review_planning_tab(self):
        """Setup the Review Planning & Scheduling tab with column layout."""
        planning_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(planning_frame, text="Review Planning")

        layout = ttk.Panedwindow(planning_frame, orient=tk.HORIZONTAL)
        layout.pack(fill=tk.BOTH, expand=True)

        context_column = ttk.Frame(layout, padding=10)
        layout.add(context_column, weight=1)

        workbench_column = ttk.Frame(layout, padding=10)
        layout.add(workbench_column, weight=3)

        insights_column = ttk.Frame(layout, padding=10)
        layout.add(insights_column, weight=1)

        # === Context Column ===
        context_frame = ttk.LabelFrame(context_column, text="?? Project Context", padding=10)
        context_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            context_frame,
            text="Capture key milestone notes or coordination focus areas for this review cycle.",
            wraplength=220
        ).pack(anchor="w")

        self.context_notes_text = tk.Text(context_frame, height=8, wrap="word")
        self.context_notes_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.context_notes_text.insert("1.0", "Notes for design managers, discipline leads, or client feedback...")

        # === Workbench Column ===
        service_frame = ttk.LabelFrame(workbench_column, text="?? Service Review Planning", padding=10)
        service_frame.pack(fill=tk.X, expand=False)

        # Info label explaining the purpose
        info_label = ttk.Label(service_frame, text="Services are managed in the Service Setup tab. This view shows service review planning details.", 
                              foreground="blue", font=("Arial", 9, "italic"))
        info_label.pack(anchor="w", pady=(0, 10))

        # Service review planning treeview - shows services with review details
        service_columns = ("Stage", "Start Date", "Expected End Date", "Review Count", "Frequency", "Status (%)")
        self.services_review_tree = ttk.Treeview(service_frame, columns=service_columns, show="headings", height=8)
        for col in service_columns:
            self.services_review_tree.heading(col, text=col)
            width = 100 if col in ["Review Count", "Status (%)"] else 120
            self.services_review_tree.column(col, width=width, anchor="w")
        self.services_review_tree.pack(fill=tk.BOTH, expand=True)

        # Refresh button for service review planning
        refresh_btn_frame = ttk.Frame(service_frame)
        refresh_btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(refresh_btn_frame, text="Refresh Service Planning", 
                  command=self.load_services_for_review_planning).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(refresh_btn_frame, text="Generate Reviews", 
                  command=self.generate_reviews_from_services_planning).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(refresh_btn_frame, text="📅 Update by Dates", 
                  command=self.refresh_cycles_by_meeting_dates).pack(side=tk.LEFT)

        cycles_frame = ttk.LabelFrame(workbench_column, text="?? Review Cycles", padding=10)
        cycles_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        filter_frame = ttk.Frame(cycles_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Cycle:").pack(side=tk.LEFT, padx=(0, 6))
        self.cycle_filter_var = tk.StringVar()
        self.cycle_filter_combo = ttk.Combobox(filter_frame, textvariable=self.cycle_filter_var, width=22, state="readonly")
        self.cycle_filter_combo['values'] = ["All Cycles"]
        self.cycle_filter_combo.set("All Cycles")
        self.cycle_filter_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.cycle_filter_combo.bind('<<ComboboxSelected>>', self.on_cycle_filter_changed)

        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 6))
        self.status_filter_var = tk.StringVar()
        status_filter = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, width=15, state="readonly")
        status_filter['values'] = ["All", "planned", "in_progress", "completed", "on_hold"]
        status_filter.set("All")
        status_filter.pack(side=tk.LEFT, padx=(0, 12))
        status_filter.bind('<<ComboboxSelected>>', lambda _event: self.refresh_cycles())

        ttk.Button(filter_frame, text="Refresh Cycles", command=self.refresh_cycles).pack(side=tk.LEFT)

        actions_frame = ttk.Frame(cycles_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="Edit Review", command=self.edit_review_cycle).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text="Delete Review", command=self.delete_review_cycle).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text="Mark as Issued", command=self.mark_review_issued).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text="Mark as Completed", command=self.mark_review_completed).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text="Confirm Due Reviews", command=self.confirm_due_reviews).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions_frame, text="Delete All Reviews", command=self.delete_all_reviews).pack(side=tk.LEFT, padx=4)

        tree_frame = ttk.Frame(cycles_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cycle_columns = ("Review ID", "Cycle", "Meeting Date", "Status", "Stage", "Reviewer", "Notes")
        self.cycles_tree = ttk.Treeview(tree_frame, columns=cycle_columns, show="headings", height=8)
        for col in cycle_columns:
            self.cycles_tree.heading(col, text=col)
            width = 80 if col == "Review ID" else 110
            self.cycles_tree.column(col, width=width, anchor="w")
        cycles_v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.cycles_tree.yview)
        cycles_h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.cycles_tree.xview)
        self.cycles_tree.configure(yscrollcommand=cycles_v_scroll.set, xscrollcommand=cycles_h_scroll.set)
        self.cycles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cycles_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        cycles_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # === Insights Column ===
        insights_frame = ttk.LabelFrame(insights_column, text="?? Review Insights", padding=10)
        insights_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            insights_frame,
            text="Visual summaries and KPIs will appear here in the next iteration.",
            wraplength=220
        ).pack(anchor="w")

        self.insights_placeholder = tk.Listbox(insights_frame, height=8)
        self.insights_placeholder.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.insights_placeholder.insert(tk.END, "• Upcoming deliverable focus")
        self.insights_placeholder.insert(tk.END, "• High-risk stages")
        self.insights_placeholder.insert(tk.END, "• Review volume by discipline")
    def setup_review_tracking_tab(self):
        """Setup the enhanced Review Execution & Tracking tab with visual progress indicators"""
        tracking_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(tracking_frame, text="📊 Review Tracking")

        # Create main layout with progress overview and detailed tracking
        main_layout = ttk.Panedwindow(tracking_frame, orient=tk.HORIZONTAL)
        main_layout.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Progress Overview & Milestones
        overview_panel = ttk.Frame(main_layout)
        main_layout.add(overview_panel, weight=1)

        # Right panel - Detailed Task Tracking
        details_panel = ttk.Frame(main_layout)
        main_layout.add(details_panel, weight=2)

        # === OVERVIEW PANEL ===
        self.setup_progress_overview(overview_panel)
        self.setup_milestone_timeline(overview_panel)

        # === DETAILS PANEL ===
        self.setup_detailed_tracking(details_panel)

        # Initialize progress tracking data
        self.progress_data = {}
        self.milestone_data = []
    
    def setup_progress_overview(self, parent):
        """Setup progress overview panel with key metrics and charts"""
        overview_frame = ttk.LabelFrame(parent, text="Progress Overview", padding=10)
        overview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create metrics grid
        metrics_frame = ttk.Frame(overview_frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))

        # Key metrics
        metrics = [
            ("Total Reviews", "0", "Total number of reviews"),
            ("Completed", "0", "Reviews marked as completed"),
            ("In Progress", "0", "Currently active reviews"),
            ("Overdue", "0", "Reviews past due date")
        ]

        for i, (label, value, tooltip) in enumerate(metrics):
            metric_frame = ttk.LabelFrame(metrics_frame, text=label, padding=5)
            metric_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

            value_label = ttk.Label(metric_frame, text=value, font=("Arial", 16, "bold"))
            value_label.pack()

            CreateToolTip(metric_frame, tooltip)

        # Progress chart placeholder
        chart_frame = ttk.LabelFrame(overview_frame, text="Review Progress Chart", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(chart_frame, text="Progress visualization will be implemented here\n(Chart showing review completion over time)").pack(expand=True)

    def setup_milestone_timeline(self, parent):
        """Setup milestone timeline panel"""
        timeline_frame = ttk.LabelFrame(parent, text="Milestone Timeline", padding=10)
        timeline_frame.pack(fill=tk.BOTH, expand=True)

        # Timeline controls
        controls_frame = ttk.Frame(timeline_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls_frame, text="Time Range:").pack(side=tk.LEFT, padx=(0, 5))
        time_range = ttk.Combobox(controls_frame, values=["Last 30 days", "Last 90 days", "Last 6 months", "All time"], state="readonly", width=15)
        time_range.set("Last 30 days")
        time_range.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(controls_frame, text="Refresh Timeline").pack(side=tk.LEFT)

        # Timeline visualization placeholder
        viz_frame = ttk.Frame(timeline_frame)
        viz_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(viz_frame, text="Timeline visualization will be implemented here\n(Showing key milestones and deadlines)").pack(expand=True)

    def setup_detailed_tracking(self, parent):
        """Setup detailed tracking panel with task breakdowns"""
        tracking_frame = ttk.LabelFrame(parent, text="Detailed Task Tracking", padding=10)
        tracking_frame.pack(fill=tk.BOTH, expand=True)

        # Task filter controls
        filter_frame = ttk.Frame(tracking_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=(0, 5))

        status_filter = ttk.Combobox(filter_frame, values=["All", "Not Started", "In Progress", "Completed", "Overdue"], state="readonly", width=12)
        status_filter.set("All")
        status_filter.pack(side=tk.LEFT, padx=(0, 10))

        priority_filter = ttk.Combobox(filter_frame, values=["All", "High", "Medium", "Low"], state="readonly", width=8)
        priority_filter.set("All")
        priority_filter.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(filter_frame, text="Apply Filters").pack(side=tk.LEFT)

        # Task details tree
        tree_frame = ttk.Frame(tracking_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Task", "Assigned To", "Due Date", "Status", "Progress", "Priority")
        task_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        for col in columns:
            task_tree.heading(col, text=col)
            task_tree.column(col, width=100, anchor="w")

        # Add sample data
        sample_tasks = [
            ("Review architectural drawings", "John Smith", "2025-10-01", "In Progress", "75%", "High"),
            ("Check structural calculations", "Jane Doe", "2025-09-28", "Completed", "100%", "Medium"),
            ("Verify MEP coordination", "Bob Wilson", "2025-10-05", "Not Started", "0%", "High")
        ]

        for task in sample_tasks:
            task_tree.insert("", tk.END, values=task)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=task_tree.yview)
        task_tree.configure(yscrollcommand=scrollbar.set)

        task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_billing_tab(self):
        """Setup the Billing & Progress tab"""
        billing_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(billing_frame, text="Billing")
        
        # Create main container with left and right panels
        main_container = ttk.PanedWindow(billing_frame, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Claims and Service Progress
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=2)
        
        # Billing Claims Frame
        claims_frame = ttk.LabelFrame(left_panel, text="Billing Claims", padding=10)
        claims_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Claims treeview
        claim_columns = ("Claim ID", "Period Start", "Period End", "PO Ref", "Invoice Ref", "Status", "Total Amount")
        self.claims_tree = ttk.Treeview(claims_frame, columns=claim_columns, show="headings", height=6)
        
        for col in claim_columns:
            self.claims_tree.heading(col, text=col)
            self.claims_tree.column(col, width=120, anchor="w")
        
        self.claims_tree.pack(fill=tk.BOTH, expand=True)
        
        # Service Progress Frame
        progress_frame = ttk.LabelFrame(left_panel, text="Service Progress & Billing", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress treeview
        progress_columns = ("Service", "Phase", "Total Fee", "Completed %", "Billed Amount", "Remaining", "Next Milestone")
        self.progress_tree = ttk.Treeview(progress_frame, columns=progress_columns, show="headings", height=6)
        
        for col in progress_columns:
            self.progress_tree.heading(col, text=col)
            self.progress_tree.column(col, width=120, anchor="w")
        
        self.progress_tree.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Billing Summaries
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=1)
        
        # Total Billable by Stage Frame
        stage_summary_frame = ttk.LabelFrame(right_panel, text="Total Billable by Stage", padding=10)
        stage_summary_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        stage_columns = ("Stage/Phase", "Billed Amount")
        self.stage_summary_tree = ttk.Treeview(stage_summary_frame, columns=stage_columns, 
                                               show="headings", height=6)
        self.stage_summary_tree.heading("Stage/Phase", text="Stage/Phase")
        self.stage_summary_tree.heading("Billed Amount", text="Billed Amount")
        self.stage_summary_tree.column("Stage/Phase", width=180, anchor="w")
        self.stage_summary_tree.column("Billed Amount", width=120, anchor="e")
        self.stage_summary_tree.pack(fill=tk.BOTH, expand=True)
        
        # Total Billable by Month Frame
        month_summary_frame = ttk.LabelFrame(right_panel, text="Total Billable by Month", padding=10)
        month_summary_frame.pack(fill=tk.BOTH, expand=True)
        
        month_columns = ("Month", "Total Billed")
        self.month_summary_tree = ttk.Treeview(month_summary_frame, columns=month_columns, 
                                               show="headings", height=6)
        self.month_summary_tree.heading("Month", text="Month")
        self.month_summary_tree.heading("Total Billed", text="Total Billed")
        self.month_summary_tree.column("Month", width=180, anchor="w")
        self.month_summary_tree.column("Total Billed", width=120, anchor="e")
        self.month_summary_tree.pack(fill=tk.BOTH, expand=True)
        
        self.progress_tree.pack(fill=tk.BOTH, expand=True)
    
    def safe_format_datetime(self, dt_value):
        """Safely format datetime value that might be string or datetime object"""
        if not dt_value:
            return 'N/A'
        if isinstance(dt_value, str):
            try:
                # Try to parse string as datetime
                dt_obj = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                return str(dt_value)
        elif hasattr(dt_value, 'strftime'):
            return dt_value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(dt_value)
    
    def refresh_revizto_history(self):
        """Refresh the Revizto extraction history"""
        try:
            # Clear existing data
            for item in self.revizto_history_tree.get_children():
                self.revizto_history_tree.delete(item)
            
            # Get extraction runs
            runs = get_revizto_extraction_runs()
            
            for run in runs:
                start_time = self.safe_format_datetime(run['start_time'])
                end_time = self.safe_format_datetime(run['end_time']) if run['end_time'] else 'Running'
                
                # Calculate duration
                if run['end_time'] and run['start_time']:
                    try:
                        # Convert to datetime objects if they are strings
                        start_dt = run['start_time'] if isinstance(run['start_time'], datetime) else datetime.fromisoformat(str(run['start_time']).replace('Z', '+00:00'))
                        end_dt = run['end_time'] if isinstance(run['end_time'], datetime) else datetime.fromisoformat(str(run['end_time']).replace('Z', '+00:00'))
                        duration = str(end_dt - start_dt).split('.')[0]  # Remove microseconds
                    except (ValueError, TypeError):
                        duration = 'N/A'
                else:
                    duration = 'N/A'
                
                self.revizto_history_tree.insert("", tk.END, values=(
                    run['run_id'],
                    start_time,
                    end_time,
                    run['status'],
                    run['projects_extracted'],
                    run['issues_extracted'],
                    run['licenses_extracted'],
                    duration
                ))
            
            # Update last run info
            last_run = get_last_revizto_extraction_run()
            if last_run:
                last_run_time = last_run['end_time'] or last_run['start_time']
                self.last_run_var.set(f"Last run: {last_run_time.strftime('%Y-%m-%d %H:%M:%S')} ({last_run['status']})")
            else:
                self.last_run_var.set("No extraction runs found")
            
            # Load project changes
            self.refresh_revizto_changes()
            
        except Exception as e:
            logger.error(f"Error refreshing Revizto history: {e}")
            messagebox.showerror("Error", f"Failed to refresh extraction history: {e}")
    
    def refresh_revizto_changes(self):
        """Refresh the recent project changes"""
        try:
            # Clear existing data
            for item in self.revizto_changes_tree.get_children():
                self.revizto_changes_tree.delete(item)
            
            # Get projects changed since last run
            from database import get_revizto_projects_since_last_run
            changed_projects = get_revizto_projects_since_last_run()
            
            for project in changed_projects:
                status = "Archived" if project['archived'] else ("Frozen" if project['frozen'] else "Active")
                updated_time = self.safe_format_datetime(project['updated'])
                
                self.revizto_changes_tree.insert("", tk.END, values=(
                    project['project_uuid'],
                    project['title'],
                    updated_time,
                    project['owner_email'],
                    status
                ))
            
        except Exception as e:
            logger.error(f"Error refreshing Revizto changes: {e}")
    
    def refresh_data(self):
        """Refresh all data in the tab"""
        try:
            # Initialize review service connection
            try:
                with get_db_connection() as db_conn:
                    self.review_service = ReviewManagementService(db_conn)
            except Exception as e:
                logger.error(f"Error connecting to database: {e}")
                self.review_service = None
            
            # Load projects
            projects = get_projects()
            project_list = [f"{p[0]} - {p[1]}" for p in projects]
            self.project_combo['values'] = project_list
            
            # Load available templates
            if self.review_service:
                templates = self.review_service.get_available_templates()
                template_list = [f"{t['name']} ({t['sector']})" for t in templates]
                self.template_combo['values'] = template_list
            
            if project_list:
                if not self.project_var.get():
                    self.project_combo.current(0)
                self.on_project_selected()
                
        except Exception as e:
            pass  # Handle the exception or log it as needed
            logger.error("Error refreshing review data: %s", e)
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        try:
            selected = self.project_var.get()
            if not selected or " - " not in selected:
                return
            
            self.current_project_id = int(selected.split(" - ")[0])
            self.current_cycle_id = None
            if hasattr(self, 'cycle_filter_var'):
                self.cycle_filter_var.set("All Cycles")
            
            # Initialize review service with database connection
            try:
                with get_db_connection() as db_conn:
                    self.review_service = ReviewManagementService(db_conn)
                    print(f"? Review service initialized for project {self.current_project_id}")
            except Exception as e:
                print(f"? Error initializing review service: {e}")
                self.review_service = None
            
            # Load cycles for this project
            cycles = get_cycle_ids(self.current_project_id)
            if hasattr(self, 'cycle_filter_combo'):
                self.cycle_filter_combo['values'] = cycles if cycles else ["No Cycles Available"]
            
            # Load project services
            self.load_project_services()
            
            # Load project summary
            self.load_project_summary()
            
            # Load billing overview
            self.load_billing_data()
            
            # Refresh review cycles
            self.refresh_cycles()
            
            # Load services for review planning view
            self.load_services_for_review_planning()
            
            # Check if we should auto-populate stages from services
            self.check_auto_populate_stages()
            
            # Auto-refresh project statuses based on current date
            self.refresh_project_statuses()
            
            # NOTE: Removed automatic sync of stages and cycles on project change
            # Users can manually trigger this via "Load Stages from Services" button
            # self.auto_update_stages_and_cycles()
            
            # Notify other tabs
            project_notification_system.notify_project_changed(selected)
            
        except Exception as e:
            print(f"Error loading project data: {e}")
    
    def auto_update_stages_and_cycles(self, force_update=False):
        """Automatically update stages and cycles based on current services"""
        try:
            if not self.review_service or not self.current_project_id:
                print("⚠️ Cannot auto-update: No review service or project selected")
                return
            
            # Get current services for the project
            services = self.get_project_services()
            if not services:
                print("📊 No services found - skipping auto-update")
                return
            
            print(f"🔄 Auto-updating stages and cycles from {len(services)} services...")
            
            # Update review cycles from services
            self.auto_sync_review_cycles_from_services(services)
            print("✅ Review cycles updated from services")
            
            # Refresh the UI
            if hasattr(self, 'refresh_cycles'):
                self.refresh_cycles()
                
        except Exception as e:
            print(f"❌ Error auto-updating stages and cycles: {e}")
            # Don't show error dialog as this is an automatic operation
    
    def get_project_services(self):
        """Get services for the current project"""
        try:
            if not self.current_project_id or not self.review_service:
                return []
            return self.review_service.get_project_services(self.current_project_id)
        except Exception as e:
            print(f"❌ Error getting project services: {e}")
            return []
    
    def check_auto_populate_stages(self):
        """Check if stages should be auto-populated from services"""
        try:
            if not self.review_service or not hasattr(self, 'stages_tree'):
                return
            
            # Check if stages tree is empty
            if self.stages_tree.get_children():
                return  # Already has stages
            
            # Check if project has services
            services = self.review_service.get_project_services(self.current_project_id)
            if not services:
                return  # No services to populate from
            
            # Extract phases
            phases = set()
            required_skills = self.skills_entry.get().strip() if hasattr(self, 'skills_entry') else ''
            role_level = self.role_var.get().strip() if hasattr(self, 'role_var') else ''
            try:
                max_utilization = float(self.max_util_var.get()) if hasattr(self, 'max_util_var') else 80.0
            except Exception:
                max_utilization = 80.0

            status_colors = {
                'Overallocated': '??',
                'High': '??',
                'Medium': '??',
                'Low': '??'
            }

            resources = self.resource_mgr.get_resource_workload(
                start_date=datetime.combine(datetime.now(), datetime.min.time()),
                end_date=datetime.combine(datetime.now() + timedelta(days=30), datetime.min.time())
            ) if self.resource_mgr else []
            for resource in resources:
                status_icon = status_colors.get(resource.get('workload_status', ''), '?')
                self.resource_tree.insert("", "end", values=(resource.get('user_id', ''), required_skills, role_level, max_utilization))

            available = self.resource_mgr.find_available_resources(
                required_skills=required_skills,
                role_level=role_level,
                max_utilization=max_utilization
            ) if self.resource_mgr else []

            if available:
                result_text = f"Found {len(available)} available resources:\n\n"
                for resource in available[:5]:  # Show top 5
                    result_text += f"?? {resource.get('name', '')} ({resource.get('role_level', '')})\n"
                    result_text += f"   Utilization: {resource.get('utilization_percentage', 0):.1f}%\n"
                    result_text += f"   Available: {resource.get('available_hours', 0):.1f} hours\n"
                    if resource.get('skills', ''):
                        result_text += f"   Skills: {resource['skills']}\n"
                    result_text += "\n"
            else:
                result_text = "No available resources found matching the criteria."

            # Show results in a popup
            result_window = tk.Toplevel(self.frame)
            result_window.title("Available Resources")
            result_window.geometry("400x300")

            text_widget = tk.Text(result_window, wrap=tk.WORD, padx=10, pady=10)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert(1.0, result_text)

            # Ask user about auto-populate stages
            result = messagebox.askyesno(
                "Auto-Populate Stages",
                f"Found {len(services)} services for this project, but no stages are defined.\n\n"
                "Would you like to automatically create stages based on the service phases and dates?"
            )
            should_update_stages = False
            if result:
                should_update_stages = True
                print("📋 Auto-populating empty stages from services...")
            else:
                print("📋 User declined auto-population of stages")

            # Update stages if needed
            if should_update_stages:
                self.auto_sync_stages_from_services(services, silent=True)

            # Check if review cycles need updating
            review_services = [s for s in services if s.get('unit_type') == 'review']
            if review_services:
                # Get current review cycles count
                if hasattr(self.review_service, 'get_service_reviews'):
                    current_cycles = self.review_service.get_service_reviews(self.current_project_id)
                else:
                    current_cycles = []

                # Calculate expected cycles from review services
                expected_cycles = sum(s.get('unit_qty', 0) for s in review_services)

                # Ask user before auto-generating review cycles
                if expected_cycles > len(current_cycles):
                    missing_cycles = expected_cycles - len(current_cycles)
                    result = messagebox.askyesno(
                        "Auto-Generate Review Cycles",
                        f"Found {len(review_services)} services that generate reviews.\n"
                        f"Current reviews: {len(current_cycles)}, Expected: {expected_cycles}\n"
                        f"Missing: {missing_cycles} review cycles\n\n"
                        "Would you like to automatically generate the missing review cycles?"
                    )
                    if result:
                        print("🔄 Auto-updating review cycles from services...")
                        self.auto_sync_review_cycles_from_services(services)
                    else:
                        print("🔄 User declined auto-generation of review cycles")
                else:
                    print(f"📊 Review cycles in sync: Current={len(current_cycles)}, Expected={expected_cycles}")
            else:
                print("📊 No review services found - no review cycles to generate")

        except Exception as e:
            print(f"Error in check_auto_populate_stages: {e}")
            messagebox.showerror("Error", f"Failed to check auto-populate stages: {e}")
    
    def auto_sync_stages_from_services(self, services, silent=False):
        """Automatically sync stages based on service phases with individual service dates"""
        try:
            # Clear existing stages if not silent mode
            if not silent:
                for item in self.stages_tree.get_children():
                    self.stages_tree.delete(item)
            
            # Create stage entries for each service individually
            stages_created = 0
            for service in services:
                phase = service.get('phase', '').strip()
                if not phase:
                    continue
                    
                # Get service dates and frequency
                service_start = service.get('schedule_start')
                service_end = service.get('schedule_end')
                service_frequency = service.get('schedule_frequency', '').strip()
                
                # Handle different date formats
                start_date = None
                end_date = None
                
                if service_start:
                    if isinstance(service_start, str):
                        try:
                            start_date = datetime.strptime(service_start, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    elif hasattr(service_start, 'date') and callable(getattr(service_start, 'date')):
                        start_date = service_start.date()
                    elif hasattr(service_start, 'year'):  # Already a date object
                        start_date = service_start
                
                if service_end:
                    if isinstance(service_end, str):
                        try:
                            end_date = datetime.strptime(service_end, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    elif hasattr(service_end, 'date') and callable(getattr(service_end, 'date')):
                        end_date = service_end.date()
                    elif hasattr(service_end, 'year'):  # Already a date object
                        end_date = service_end
                
                # Use service frequency or determine from phase/service name
                if service_frequency:
                    frequency = service_frequency
                else:
                    frequency = "weekly"
                    if "initiation" in phase.lower() or "setup" in phase.lower():
                        frequency = "one-off"
                    elif "handover" in phase.lower() or "completion" in phase.lower():
                        frequency = "one-off"
                    elif "construction" in phase.lower():
                        frequency = "weekly"
                    elif "design" in phase.lower() or "documentation" in phase.lower():
                        frequency = "bi-weekly"
                
                # Calculate review count from service
                reviews = service.get('unit_qty', 1) if service.get('unit_type') == 'review' else 1
                reviews = max(1, reviews)
                
                # Use actual dates if available, otherwise skip this service
                if start_date and end_date:
                    # Create stage name from phase and service details
                    service_code = service.get('service_code', '')
                    service_name = service.get('service_name', '')
                    stage_name = f"{phase}"
                    if service_code and service_name:
                        stage_name = f"{phase} - {service_code}"
                    
                    # Check if stage already exists (in silent mode)
                    stage_exists = False
                    if silent:
                        for item in self.stages_tree.get_children():
                            values = self.stages_tree.item(item)['values']
                            if values and values[0] == stage_name:
                                stage_exists = True
                                break
                    
                    if not stage_exists:
                        # Insert new stage with actual service dates and frequency
                        self.stages_tree.insert("", tk.END, values=(
                            stage_name,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d'), 
                            reviews,
                            frequency,
                            1  # Service count
                        ))
                        stages_created += 1
            
            if not silent:
                print(f"📋 Synced {stages_created} stages from individual services with actual dates and frequencies")
                
        except Exception as e:
            print(f"Error in auto_sync_stages_from_services: {e}")
    
    def auto_sync_review_cycles_from_services(self, services):
        """Generate review cycles based on services with review unit type"""
        try:
            # Find services that should generate reviews
            review_services = [s for s in services if s.get('unit_type') == 'review']

            if not review_services:
                print("📊 No review services found - no review cycles to generate")
                return

            print(f"🔄 Smart sync: checking review cycles from {len(review_services)} review services...")
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id, force_regenerate=False)

            if reviews_created:
                print(f"✅ Generated {len(reviews_created)} review cycles")
                # Refresh the UI
                self.refresh_cycles()
                self.load_billing_data()
            else:
                print("⚠️ No review cycles were generated")

        except Exception as e:
            print(f"Error in auto_sync_review_cycles_from_services: {e}")
    
    def start_background_sync(self):
        """Start background sync mechanism for automatic updates"""
        try:
            # Check for updates every 60 seconds (reduced frequency to avoid conflicts)
            if hasattr(self, 'current_project_id') and self.current_project_id:
                # Only do a light check, not full regeneration
                self.check_service_changes_and_update()
            
            # Schedule next check (increased to 60 seconds)
            self.frame.after(60000, self.start_background_sync)  # 60 seconds
            
        except Exception as e:
            print(f"Error in background sync: {e}")
            # Schedule next check even if there was an error
            self.frame.after(60000, self.start_background_sync)
    
    def check_service_changes_and_update(self):
        """Check for service changes and update if needed"""
        try:
            if not self.current_project_id or not self.review_service:
                return False
                
            # Get current services hash for change detection
            services = self.review_service.get_project_services(self.current_project_id)
            
            # Create a more comprehensive signature including dates and frequency
            services_signature = str(len(services))
            review_services = [s for s in services if s.get('unit_type') == 'review']
            for service in review_services:
                services_signature += str(service.get('unit_qty', 0))
                services_signature += str(service.get('schedule_start', ''))
                services_signature += str(service.get('schedule_end', ''))
                services_signature += str(service.get('schedule_frequency', ''))
            
            # Compare with stored signature
            if not hasattr(self, '_last_services_signature'):
                self._last_services_signature = services_signature
                return False
                
            if self._last_services_signature != services_signature:
                print(f"🔍 Service changes detected (dates/frequency/quantity), light sync...")
                # Only regenerate review cycles if needed, don't modify stages automatically
                self.auto_sync_review_cycles_from_services(services)
                self._last_services_signature = services_signature
                return True
                
            return False
            
        except Exception as e:
            print(f"Error checking service changes: {e}")
            return False

    def load_template(self):
        """Load and display selected template"""
        try:
            if not self.template_var.get():
                messagebox.showwarning("Warning", "Please select a template first")
                return
            
            # Extract template name
            template_name = self.template_var.get().split(" (")[0]
            
            if self.review_service:
                template = self.review_service.load_template(template_name)
                if template:
                    # Show template details in a popup
                    self.show_template_details(template)
                else:
                    messagebox.showerror("Error", f"Could not load template: {template_name}")
            else:
                messagebox.showerror("Error", "Review service not initialized")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading template: {e}")
    
    def show_template_details(self, template):
        """Show template details in a popup window"""
        try:
            win = tk.Toplevel(self.frame)
            win.title(f"Template: {template['name']}")
            win.geometry("900x700")
            
            # Template info
            info_frame = ttk.LabelFrame(win, text="Template Information", padding=10)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"Name: {template['name']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Sector: {template['sector']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Notes: {template.get('notes', 'N/A')}").pack(anchor=tk.W)
            
            # Create notebook for services and phases
            details_notebook = ttk.Notebook(win)
            details_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Services tab
            services_frame = ttk.Frame(details_notebook)
            details_notebook.add(services_frame, text="?? Services")
            
            columns = ("Phase", "Service Code", "Service Name", "Unit Type", "Units", "Rate/Fee")
            tree = ttk.Treeview(services_frame, columns=columns, show="headings")
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="w")
            
            for item in template['items']:
                fee = item.get('lump_sum_fee', 0) or (item.get('default_units', 1) * item.get('unit_rate', 0))
                values = (
                    item['phase'],
                    item['service_code'], 
                    item['service_name'],
                    item['unit_type'],
                    item.get('default_units', 1),
                    f"${fee:,.2f}"
                )
                tree.insert("", tk.END, values=values)
            
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Phases analysis tab
            phases_frame = ttk.Frame(details_notebook)
            details_notebook.add(phases_frame, text="??? Phases Preview")
            
            # Analyze phases
            phases_analysis = {}
            for item in template['items']:
                phase = item['phase']
                if phase not in phases_analysis:
                    phases_analysis[phase] = {
                        'services': [],
                        'total_reviews': 0,
                        'total_fee': 0
                    }
                
                phases_analysis[phase]['services'].append(item)
                if item['unit_type'] == 'review':
                    phases_analysis[phase]['total_reviews'] += item.get('default_units', 0)
                
                fee = item.get('lump_sum_fee', 0) or (item.get('default_units', 1) * item.get('unit_rate', 0))
                phases_analysis[phase]['total_fee'] += fee
            
            # Phases summary
            phase_columns = ("Phase", "Services", "Reviews", "Total Fee", "Suggested Frequency")
            phase_tree = ttk.Treeview(phases_frame, columns=phase_columns, show="headings", height=8)
            
            for col in phase_columns:
                phase_tree.heading(col, text=col)
                phase_tree.column(col, width=150, anchor="w")
            
            for phase, data in phases_analysis.items():
                # Suggest frequency based on phase characteristics
                frequency = "weekly"
                if "initiation" in phase.lower() or "setup" in phase.lower():
                    frequency = "one-off"
                elif "handover" in phase.lower() or "completion" in phase.lower():
                    frequency = "one-off"
                elif "construction" in phase.lower():
                    frequency = "weekly"
                elif "design" in phase.lower() or "documentation" in phase.lower():
                    frequency = "bi-weekly"
                
                values = (
                    phase,
                    len(data['services']),
                    data['total_reviews'],
                    f"${data['total_fee']:,.2f}",
                    frequency
                )
                phase_tree.insert("", tk.END, values=values)
            
            phase_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Info label
            info_label = ttk.Label(phases_frame, 
                text="?? These phases will become review stages when template is applied",
                font=('TkDefaultFont', 9, 'italic'))
            info_label.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing template details: {e}")
    
    def apply_template(self):
        """Apply selected template to current project"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.template_var.get():
                messagebox.showwarning("Warning", "Please select a template first")
                return
            
            # Confirm action
            result = messagebox.askyesno("Confirm", "This will add services from the template to the current project. Continue?")
            if not result:
                return
            
            template_name = self.template_var.get().split(" (")[0]
            
            if self.review_service:
                services = self.review_service.apply_template(self.current_project_id, template_name)
                if services:
                    messagebox.showinfo("Success", f"Applied template successfully. {len(services)} services created.")
                    self.load_project_services()
                    
                    # Automatically update stages and cycles after applying template
                    print("🔄 Auto-updating stages and cycles after applying template...")
                    self.auto_update_stages_and_cycles(force_update=True)
                    
                    # Ask if user wants to auto-populate stages from the new services
                    auto_stages = messagebox.askyesno("Auto-populate Stages", 
                        "Would you like to automatically create review stages from the service phases?")
                    if auto_stages:
                        # Switch to the Review Planning tab
                        self.sub_notebook.select(1)  # Index 1 is the Review Planning tab
                        # Load stages from services
                        self.load_stages_from_services()
                else:
                    messagebox.showerror("Error", "Failed to apply template")
            else:
                messagebox.showerror("Error", "Review service not initialized")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error applying template: {e}")
    
    def save_as_template(self):
        """Save current project services as a new template"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Get current project services
            services = self.review_service.get_project_services(self.current_project_id)
            if not services:
                messagebox.showwarning("Warning", "No services found in current project")
                return
            
            # Show save template dialog
            self.show_save_template_dialog(services)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving template: {e}")
    
    def show_save_template_dialog(self, services):
        """Show dialog to save services as template"""
        try:
            dialog = tk.Toplevel(self.frame)
            dialog.title("Save as Template")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            form_frame = ttk.LabelFrame(dialog, text="Template Details", padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Template name
            ttk.Label(form_frame, text="Template Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(form_frame, textvariable=name_var, width=40)
            name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Sector
            ttk.Label(form_frame, text="Sector:").grid(row=1, column=0, sticky=tk.W, pady=5)
            sector_var = tk.StringVar()
            sector_combo = ttk.Combobox(form_frame, textvariable=sector_var, width=20, state="normal")
            sector_combo['values'] = ["Education", "Data Centre", "Commercial", "Residential", "Infrastructure", "Healthcare", "Other"]
            sector_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Notes
            ttk.Label(form_frame, text="Notes:").grid(row=2, column=0, sticky=tk.NW, pady=5)
            notes_text = tk.Text(form_frame, width=40, height=4)
            notes_text.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Existing templates option
            ttk.Label(form_frame, text="Save Options:").grid(row=3, column=0, sticky=tk.W, pady=10)
            save_option_var = tk.StringVar(value="new")
            ttk.Radiobutton(form_frame, text="Create New Template", variable=save_option_var, value="new").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
            ttk.Radiobutton(form_frame, text="Overwrite Existing Template", variable=save_option_var, value="overwrite").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
            
            # Existing template selector (initially hidden)
            existing_frame = ttk.Frame(form_frame)
            existing_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
            ttk.Label(existing_frame, text="Existing Template:").pack(side=tk.LEFT)
            existing_var = tk.StringVar()
            existing_combo = ttk.Combobox(existing_frame, textvariable=existing_var, width=30, state="readonly")
            existing_combo.pack(side=tk.LEFT, padx=(10, 0))
            existing_frame.grid_remove()  # Hide initially
            
            def on_save_option_change():
                if save_option_var.get() == "overwrite":
                    existing_combo['values'] = [t['name'] for t in self.review_service.get_available_templates()]
                    existing_frame.grid()
                else:
                    existing_frame.grid_remove()
            
            save_option_var.trace("w", lambda *args: on_save_option_change())
            
            form_frame.columnconfigure(1, weight=1)
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            def save_template():
                try:
                    template_name = name_var.get().strip()
                    if not template_name:
                        messagebox.showerror("Error", "Template name is required")
                        return
                    
                    sector = sector_var.get().strip()
                    notes = notes_text.get("1.0", tk.END).strip()
                    
                    if save_option_var.get() == "overwrite":
                        existing_name = existing_var.get()
                        if not existing_name:
                            messagebox.showerror("Error", "Please select an existing template to overwrite")
                            return
                        template_name = existing_name
                    
                    # Convert services to template format
                    template_items = []
                    for service in services:
                        item = {
                            "phase": service.get('phase', ''),
                            "service_code": service.get('service_code', ''),
                            "service_name": service.get('service_name', ''),
                            "unit_type": service.get('unit_type', 'lump_sum'),
                            "default_units": service.get('unit_qty', 1),
                            "unit_rate": service.get('unit_rate', 0),
                            "lump_sum_fee": service.get('lump_sum_fee', 0),
                            "bill_rule": service.get('bill_rule', 'on_completion'),
                            "notes": service.get('notes', '')
                        }
                        template_items.append(item)
                    
                    # Save template
                    success = self.review_service.save_template(template_name, sector, notes, template_items, save_option_var.get() == "overwrite")
                    
                    if success:
                        messagebox.showinfo("Success", f"Template '{template_name}' saved successfully")
                        dialog.destroy()
                        # Refresh template list
                        self.refresh_template_list()
                    else:
                        messagebox.showerror("Error", "Failed to save template")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Error saving template: {e}")
            
            def cancel_save():
                dialog.destroy()
            
            ttk.Button(button_frame, text="Save Template", command=save_template).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=cancel_save).pack(side=tk.LEFT)
            
        except Exception as e:
            self.show_user_friendly_error("Template Save Dialog Error", e, "Failed to show template save dialog")
    
    def show_user_friendly_error(self, title: str, error: Exception, context: str = ""):
        """Show detailed but user-friendly error dialogs"""
        import traceback
        
        # Simple message for users
        user_message = f"{context}\n\nError: {str(error)}"
        
        # Detailed message for developers/logs
        detailed_message = f"""
Context: {context}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Traceback:
{traceback.format_exc()}
"""
        
        print(f"❌ ERROR: {detailed_message}")
        
        # Show simple message to user with option for details
        result = messagebox.askyesno(title, 
                                    f"{user_message}\n\nWould you like to see technical details?")
        
        if result:
            # Show detailed error in separate dialog
            detail_window = tk.Toplevel(self.frame)
            detail_window.title(f"{title} - Details")
            detail_window.geometry("600x400")
            detail_window.transient(self.frame)
            detail_window.grab_set()
            
            text_widget = tk.Text(detail_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, detailed_message)
            text_widget.config(state=tk.DISABLED)
            
            ttk.Button(detail_window, text="Close", 
                      command=detail_window.destroy).pack(pady=10)
    
    def show_user_friendly_error(self, title: str, error: Exception, context: str = ""):
        """Show detailed but user-friendly error dialogs"""
        import traceback
        
        # Simple message for users
        user_message = f"{context}\n\nError: {str(error)}"
        
        # Detailed message for developers/logs
        detailed_message = f"""
Context: {context}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Traceback:
{traceback.format_exc()}
"""
        
        print(f"❌ ERROR: {detailed_message}")
        
        # Show simple message to user with option for details
        result = messagebox.askyesno(title, 
                                    f"{user_message}\n\nWould you like to see technical details?")
        
        if result:
            # Show detailed error in separate dialog
            detail_window = tk.Toplevel(self.frame)
            detail_window.title(f"{title} - Details")
            detail_window.geometry("600x400")
            detail_window.transient(self.frame)
            detail_window.grab_set()
            
            text_widget = tk.Text(detail_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, detailed_message)
            text_widget.config(state=tk.DISABLED)
            
            ttk.Button(detail_window, text="Close", 
                      command=detail_window.destroy).pack(pady=10)
    
    def refresh_template_list(self):
        """Enhanced template refresh with user feedback"""
        try:
            if not self.review_service:
                print("⚠️  Review service not initialized")
                return False
                
            if not hasattr(self, 'template_combo'):
                print("⚠️  Template combo box not found")
                return False
            
            # Show loading indicator
            original_state = self.template_combo['state']
            self.template_combo['state'] = 'disabled'
            self.template_combo.set("Loading templates...")
            
            # Update GUI
            self.template_combo.update_idletasks()
            
            # Load templates
            templates = self.review_service.get_available_templates()
            template_list = [f"{t['name']} ({t['sector']})" for t in templates]
            
            # Update combo box
            self.template_combo['values'] = template_list
            self.template_combo['state'] = original_state
            
            if not templates:
                self.template_combo.set("No templates available")
            else:
                self.template_combo.set("Select template...")
                
            print(f"✅ Loaded {len(templates)} templates successfully")
            return True
            
        except Exception as e:
            # Restore combo box state
            if hasattr(self, 'template_combo'):
                self.template_combo['state'] = 'readonly'
                self.template_combo.set("Error loading templates")
            
            error_msg = f"Failed to load templates: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Show user-friendly error
            messagebox.showerror("Template Loading Error", 
                               f"Could not load service templates.\n\n{error_msg}")
            return False
    
    def load_project_services(self):
        """Load project services into the services tree with enhanced protection"""
        operation_name = "load_project_services"
        
        if not self.operation_manager.start_operation(operation_name):
            return
        
        try:
            # Clear existing services
            for item in self.services_tree.get_children():
                self.services_tree.delete(item)

            if not self.current_project_id or not self.review_service:
                print("⚠️  Missing project ID or review service")
                return

            # Get project services
            services = self.review_service.get_project_services(self.current_project_id)
            print(f"📋 Loading {len(services)} project services")

            for service in services:
                start_date = service.get('schedule_start')
                end_date = service.get('schedule_end')
                frequency = service.get('schedule_frequency') or ''

                if hasattr(start_date, 'strftime'):
                    start_display = start_date.strftime('%Y-%m-%d')
                elif start_date:
                    start_display = str(start_date)
                else:
                    start_display = ''

                if hasattr(end_date, 'strftime'):
                    end_display = end_date.strftime('%Y-%m-%d')
                elif end_date:
                    end_display = str(end_date)
                else:
                    end_display = ''

                values = (
                    service.get('service_id', ''),
                    service.get('phase', ''),
                    service.get('service_code', ''),
                    service.get('service_name', ''),
                    service.get('unit_type', ''),
                    service.get('unit_qty', 0),
                    f"${service.get('unit_rate', 0):,.2f}",
                    f"${service.get('agreed_fee', 0):,.2f}",
                    service.get('status', 'active'),
                    start_display,
                    end_display,
                    frequency
                )
                self.services_tree.insert("", tk.END, values=values)
            
            print(f"✅ Loaded {len(services)} services successfully")

        except Exception as e:
            self.show_user_friendly_error("Service Loading Error", e, "Failed to load project services")
        finally:
            self.operation_manager.end_operation(operation_name)
    
    def generate_reviews_from_services(self):
        """Generate review cycles from current project services"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Check if there are already review cycles to avoid conflicts
            existing_cycles = self.review_service.get_service_reviews(self.current_project_id)
            if existing_cycles:
                result = messagebox.askyesno("Confirm", 
                    f"There are {len(existing_cycles)} existing review cycles. "
                    "This will delete all existing cycles and regenerate them based on current services. "
                    "Continue?")
                if not result:
                    return
            else:
                # Confirm action for new generation
                result = messagebox.askyesno("Confirm", "Generate review cycles based on project services?")
                if not result:
                    return
            
            # Generate reviews - force regeneration since user explicitly requested it
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id, force_regenerate=True)
            
            if reviews_created:
                messagebox.showinfo("Success", f"Generated {len(reviews_created)} review cycles from services")
                self.load_billing_data()
                self.refresh_cycles()
                
                # Update stages to ensure they're in sync (but don't trigger another auto-update)
                print("🔄 Updating stages after manual review generation...")
                services = self.review_service.get_project_services(self.current_project_id)
                if services:
                    self.auto_sync_stages_from_services(services, silent=True)
            else:
                messagebox.showwarning("Info", "No reviews generated. Check if services are properly configured.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating reviews: {e}")
    
    def load_stages_from_services(self):
        """Load stages from current project services with actual dates"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Get project services
            services = self.review_service.get_project_services(self.current_project_id)
            
            if not services:
                messagebox.showwarning("Warning", "No services found for this project. Please apply a service template first.")
                return
            
            # Ask user if they want to replace existing stages
            if self.stages_tree.get_children():
                result = messagebox.askyesno("Confirm", "This will replace existing stages with services from the current project. Continue?")
                if not result:
                    return
            
            # Use the corrected auto_sync method to populate stages with actual service dates
            print(f"🔄 Loading stages from services for project {self.current_project_id}...")
            self.auto_sync_stages_from_services(services, silent=False)
            
            # Automatically trigger review cycle update
            print("🔄 Auto-updating review cycles after loading stages from services...")
            self.auto_sync_review_cycles_from_services(services)
            
            messagebox.showinfo("Success", f"Loaded {len(self.stages_tree.get_children())} stages from project services with actual dates and frequencies")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading stages from services: {e}")
            print(f"Error in load_stages_from_services: {e}")
    
    def load_services_for_review_planning(self):
        """Load services for review planning view"""
        try:
            # Clear existing services
            for item in self.services_review_tree.get_children():
                self.services_review_tree.delete(item)

            if not self.current_project_id or not self.review_service:
                return

            # Get project services
            services = self.review_service.get_project_services(self.current_project_id)

            for service in services:
                # Extract service data
                stage = service.get('phase', '')
                start_date = service.get('schedule_start')
                end_date = service.get('schedule_end')
                frequency = service.get('schedule_frequency', '')
                unit_type = service.get('unit_type', '')
                unit_qty = service.get('unit_qty', 0)

                # Format dates
                if hasattr(start_date, 'strftime'):
                    start_display = start_date.strftime('%Y-%m-%d')
                elif start_date:
                    start_display = str(start_date)
                else:
                    start_display = ''

                if hasattr(end_date, 'strftime'):
                    end_display = end_date.strftime('%Y-%m-%d')
                elif end_date:
                    end_display = str(end_date)
                else:
                    end_display = ''

                # Determine review count based on unit type
                if unit_type == 'review':
                    review_count = str(unit_qty)
                else:
                    # For other unit types, calculate based on duration and frequency
                    review_count = self._calculate_review_count(start_date, end_date, frequency)

                # Calculate actual completion percentage based on review status
                service_id = service.get('service_id')
                if service_id and self.review_service:
                    try:
                        status_summary = self.review_service.get_service_review_status_summary(service_id)
                        status_percent = status_summary['status_display']
                    except Exception as e:
                        print(f"Error getting status for service {service_id}: {e}")
                        status_percent = "0.0%"
                else:
                    status_percent = "0.0%"

                values = (stage, start_display, end_display, review_count, frequency, status_percent)
                self.services_review_tree.insert("", tk.END, values=values)

        except Exception as e:
            print(f"Error loading services for review planning: {e}")
    
    def generate_reviews_from_services_planning(self):
        """Generate review cycles from services shown in the review planning view"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Check if there are services to generate reviews from
            services = self.review_service.get_project_services(self.current_project_id)
            if not services:
                messagebox.showwarning("Warning", "No services found for this project")
                return
            
            # Check if there are already review cycles to avoid conflicts
            existing_cycles = self.review_service.get_service_reviews(self.current_project_id)
            if existing_cycles:
                result = messagebox.askyesno("Confirm", 
                    f"There are {len(existing_cycles)} existing review cycles. "
                    "This will delete all existing cycles and regenerate them based on current services. "
                    "Continue?")
                if not result:
                    return
            else:
                # Confirm action for new generation
                result = messagebox.askyesno("Confirm", 
                    f"Generate review cycles for {len(services)} services? "
                    "This will create review schedules based on each service's duration and frequency.")
                if not result:
                    return
            
            # Generate reviews - force regeneration since user explicitly requested it
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id, force_regenerate=True)
            
            if reviews_created:
                messagebox.showinfo("Success", 
                    f"Generated {len(reviews_created)} review cycles from {len(services)} services")
                
                # Refresh all relevant data
                self.load_services_for_review_planning()  # Refresh the service planning view
                self.load_billing_data()  # Refresh billing data
                self.refresh_cycles()  # Refresh review cycles
                
                # Update stages to ensure they're in sync
                print("🔄 Updating stages after review generation...")
                if services:
                    self.auto_sync_stages_from_services(services, silent=True)
            else:
                messagebox.showwarning("Info", "No reviews generated. Check if services are properly configured.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating reviews from services: {e}")
    
    def _calculate_review_count(self, start_date, end_date, frequency):
        """Calculate review count based on service duration and frequency"""
        try:
            if not start_date or not end_date or not frequency:
                return "0"

            # Convert dates if needed
            if isinstance(start_date, str):
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
            elif hasattr(start_date, 'date'):
                start = start_date.date()
            else:
                start = start_date

            if isinstance(end_date, str):
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif hasattr(end_date, 'date'):
                end = end_date.date()
            else:
                end = end_date

            # Calculate duration in days
            duration_days = (end - start).days

            # Calculate review count based on frequency
            if frequency == 'one-off':
                return "1"  # One-off reviews always have exactly one review
            elif frequency == 'weekly':
                weeks = duration_days / 7
                return str(max(1, int(weeks)))
            elif frequency == 'bi-weekly':
                biweeks = duration_days / 14
                return str(max(1, int(biweeks)))
            elif frequency == 'monthly':
                months = duration_days / 30
                return str(max(1, int(months)))
            else:
                return "1"  # Default for unknown frequency

        except Exception as e:
            print(f"Error calculating review count: {e}")
            return "1"
    
    def add_stage(self):
        """Add a new stage to the stage planning"""
        try:
            stage = self.stage_var.get().strip()
            start_date = self.stage_start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.stage_end_date.get_date().strftime('%Y-%m-%d')
            reviews = self.stage_reviews_var.get().strip()
            frequency = self.stage_freq_var.get()
            
            if not all([stage, start_date, end_date, reviews]):
                messagebox.showwarning("Warning", "Please fill in all stage fields")
                return
            
            # Add to tree
            values = (stage, start_date, end_date, reviews, frequency, "planned")
            self.stages_tree.insert("", tk.END, values=values)
            
            # Clear input fields
            self.stage_var.set("")
            self.stage_reviews_var.set("4")
            
            # Automatically update review cycles after adding stage
            print("🔄 Auto-updating review cycles after adding stage...")
            self.auto_update_stages_and_cycles()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error adding stage: {e}")
    
    def delete_stage(self):
        """Delete selected stage"""
        try:
            selection = self.stages_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a stage to delete")
                return
            
            for item in selection:
                self.stages_tree.delete(item)
            
            # Automatically update review cycles after deleting stage
            print("🔄 Auto-updating review cycles after deleting stage...")
            self.auto_update_stages_and_cycles()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting stage: {e}")
    
    def generate_stage_schedule(self):
        """Generate review schedule from stages"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            # Get stages from tree
            stages = []
            for item in self.stages_tree.get_children():
                values = self.stages_tree.item(item)['values']
                if len(values) >= 5:
                    stage_data = {
                        'stage_name': values[0],
                        'start_date': values[1],
                        'end_date': values[2],
                        'num_reviews': int(values[3]),
                        'frequency': values[4]
                    }
                    stages.append(stage_data)
            
            print(f"?? Found {len(stages)} stages to process")
            for stage in stages:
                print(f"  - Stage: {stage['stage_name']}, Reviews: {stage['num_reviews']}, Dates: {stage['start_date']} to {stage['end_date']}")
            
            if not stages:
                messagebox.showwarning("Warning", "No stages defined. Please add stages first.")
                return
            
            # Generate schedule using the modern review service
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            print(f"?? Generating schedule for project {self.current_project_id}")
            result = self.review_service.generate_stage_schedule_new(self.current_project_id, stages)
            
            if result:
                print("? Stage review schedule generated successfully")
                messagebox.showinfo("Success", "Stage review schedule generated successfully")
                self.refresh_cycles()
            else:
                print("? Failed to generate stage schedule")
                messagebox.showerror("Error", "Failed to generate stage schedule")
                
        except Exception as e:
            print(f"? Error generating stage schedule: {e}")
            messagebox.showerror("Error", f"Error generating stage schedule: {e}")
    
    def refresh_cycles(self):
        """Refresh the review cycles display"""
        try:
            for item in self.cycles_tree.get_children():
                self.cycles_tree.delete(item)

            if not self.current_project_id:
                return

            self.auto_complete_candidates = []
            cycles = get_review_cycles(self.current_project_id)
            available_cycles = []

            selected_status = "all"
            if hasattr(self, 'status_filter_var'):
                selected_status = (self.status_filter_var.get() or "All").lower()

            selected_cycle = None
            if hasattr(self, 'cycle_filter_var'):
                raw_cycle = self.cycle_filter_var.get()
                if raw_cycle not in ("All Cycles", "", None):
                    selected_cycle = raw_cycle

            today = datetime.now().date()
            completed_states = {'completed', 'closed', 'cancelled'}

            for cycle in cycles:
                if len(cycle) < 6:
                    continue

                cycle_no = str(cycle[2])
                if cycle_no not in available_cycles:
                    available_cycles.append(cycle_no)

                cycle_status = (cycle[5] or "").lower()
                if selected_status != 'all' and cycle_status != selected_status:
                    continue

                if selected_cycle and cycle_no != selected_cycle:
                    continue

                notes = ""
                
                # Check if manual override is set (index 7 is status_override from query)
                has_override = len(cycle) > 7 and cycle[7] == 1
                override_icon = "🔒 " if has_override else ""

                formatted_cycle = (
                    str(cycle[0]),
                    f"{cycle[1]} - Cycle {cycle_no}",
                    cycle[3] or "",
                    f"{override_icon}{cycle[5] or ''}",  # Add lock icon to status if override
                    cycle[6] if len(cycle) > 6 and cycle[6] else "All",
                    "",
                    notes
                )
                self.cycles_tree.insert("", tk.END, values=formatted_cycle)

            if hasattr(self, 'cycle_filter_combo'):
                if available_cycles:
                    sorted_cycles = sorted(
                        available_cycles,
                        key=lambda val: (0, int(val)) if str(val).isdigit() else (1, val)
                    )
                    values = ["All Cycles"] + sorted_cycles
                else:
                    values = ["All Cycles"]
                self.cycle_filter_combo['values'] = values

                if selected_cycle and selected_cycle in available_cycles:
                    self.cycle_filter_var.set(selected_cycle)
                else:
                    self.cycle_filter_var.set("All Cycles")
                    selected_cycle = None

            self.current_cycle_id = selected_cycle
            self.load_review_tasks()
        except Exception as e:
            print(f"Error refreshing cycles: {e}")

    def load_project_summary(self):
            """Load project summary information"""
            try:
                if not self.current_project_id:
                    return
                
                # Get project details
                project_details = get_project_details(self.current_project_id)
                if project_details:
                    self.summary_vars["Project Name"].set(project_details.get("project_name", ""))
                    self.summary_vars["Construction Stage"].set(project_details.get("construction_stage", ""))
                    
                # Get review statistics
                if self.review_service:
                    stats = self.review_service.get_project_review_stats(self.current_project_id)
                    if stats:
                        self.summary_vars["Total Services"].set(str(stats.get("total_services", 0)))
                        self.summary_vars["Active Reviews"].set(str(stats.get("active_reviews", 0)))
                        self.summary_vars["Completed Reviews"].set(str(stats.get("completed_reviews", 0)))
                        
                        # Calculate overall progress
                        total = stats.get("total_reviews", 0)
                        completed = stats.get("completed_reviews", 0)
                        if total > 0:
                            progress = round((completed / total) * 100, 1)
                            self.summary_vars["Overall Progress"].set(f"{progress}%")
                        else:
                            self.summary_vars["Overall Progress"].set("0%")
                
            except Exception as e:
                print(f"Error loading project summary: {e}")

    def load_billing_data(self):
        """Load billing claims and service progress for the current project."""
        try:
            if not hasattr(self, 'claims_tree') or not hasattr(self, 'progress_tree'):
                return

            # Clear existing data
            for item in self.claims_tree.get_children():
                self.claims_tree.delete(item)

            for item in self.progress_tree.get_children():
                self.progress_tree.delete(item)
                
            # Clear summary tables if they exist
            if hasattr(self, 'stage_summary_tree'):
                for item in self.stage_summary_tree.get_children():
                    self.stage_summary_tree.delete(item)
                    
            if hasattr(self, 'month_summary_tree'):
                for item in self.month_summary_tree.get_children():
                    self.month_summary_tree.delete(item)

            if not self.current_project_id or not self.review_service:
                return

            # Load billing claims
            claims = self.review_service.get_billing_claims(self.current_project_id)
            for claim in claims:
                values = (
                    claim.get('claim_id', ''),
                    claim.get('period_start', '') or '',
                    claim.get('period_end', '') or '',
                    claim.get('po_ref', '') or '',
                    claim.get('invoice_ref', '') or '',
                    claim.get('status', '') or '',
                    f"${float(claim.get('total_amount', 0) or 0):,.2f}"
                )
                self.claims_tree.insert('', tk.END, values=values)

            # Load service progress
            services = self.review_service.get_service_progress_summary(self.current_project_id)
            for service in services:
                values = (
                    service.get('service_name', ''),
                    service.get('phase', ''),
                    f"${float(service.get('agreed_fee', 0) or 0):,.2f}",
                    f"{float(service.get('progress_pct', 0) or 0):.1f}%",
                    f"${float(service.get('billed_amount', 0) or 0):,.2f}",
                    f"${float(service.get('remaining_amount', 0) or 0):,.2f}",
                    service.get('next_milestone', '')
                )
                self.progress_tree.insert('', tk.END, values=values)
            
            # Load billable by stage summary
            if hasattr(self, 'stage_summary_tree'):
                stage_billing = self.review_service.get_billable_by_stage(self.current_project_id)
                stage_total = 0
                for stage_data in stage_billing:
                    phase = stage_data.get('phase', 'Unknown')
                    billed = float(stage_data.get('billed_amount', 0))
                    stage_total += billed
                    self.stage_summary_tree.insert('', tk.END, values=(phase, f"${billed:,.0f}"))
                
                # Add total row
                if stage_total > 0:
                    self.stage_summary_tree.insert('', tk.END, values=("═══ TOTAL ═══", f"${stage_total:,.0f}"), 
                                                   tags=('total',))
                    self.stage_summary_tree.tag_configure('total', font=('Arial', 9, 'bold'))
            
            # Load billable by month summary
            if hasattr(self, 'month_summary_tree'):
                month_billing = self.review_service.get_billable_by_month(self.current_project_id)
                month_total = 0
                for month_data in month_billing:
                    month_label = month_data.get('month', 'Unknown')
                    billed = float(month_data.get('total_billed', 0))
                    month_total += billed
                    self.month_summary_tree.insert('', tk.END, values=(month_label, f"${billed:,.0f}"))
                
                # Add total row
                if month_total > 0:
                    self.month_summary_tree.insert('', tk.END, values=("═══ TOTAL ═══", f"${month_total:,.0f}"),
                                                   tags=('total',))
                    self.month_summary_tree.tag_configure('total', font=('Arial', 9, 'bold'))
                    
        except Exception as e:
            print(f"Error loading billing data: {e}")
            import traceback
            traceback.print_exc()

    def add_service(self):
        """Add a new service to the project"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Create service input dialog
            self.show_service_dialog()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error adding service: {e}")
    
    def show_service_dialog(self, service_data=None):
        """Show dialog for adding/editing a service"""
        try:
            dialog = tk.Toplevel(self.frame)
            dialog.title("Add Service" if not service_data else "Edit Service")
            dialog.geometry("620x560")
            dialog.transient(self.frame)
            dialog.grab_set()

            form_frame = ttk.LabelFrame(dialog, text="Service Details", padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            phase_var = tk.StringVar(value=service_data.get('phase', '') if service_data else '')
            service_code_var = tk.StringVar(value=service_data.get('service_code', '') if service_data else '')
            service_name_var = tk.StringVar(value=service_data.get('service_name', '') if service_data else '')
            unit_type_var = tk.StringVar(value=service_data.get('unit_type', 'lump_sum') if service_data else 'lump_sum')
            unit_qty_var = tk.StringVar(value=str(service_data.get('unit_qty', 1)) if service_data else '1')
            unit_rate_var = tk.StringVar(value=str(service_data.get('unit_rate', 0)) if service_data else '0')
            lump_sum_var = tk.StringVar(value=str(service_data.get('lump_sum_fee', 0)) if service_data else '0')
            bill_rule_var = tk.StringVar(value=service_data.get('bill_rule', 'on_completion') if service_data else 'on_completion')
            notes_var = tk.StringVar(value=service_data.get('notes', '') if service_data else '')

            default_start = datetime.today().date()
            default_end = default_start + timedelta(days=90)
            if service_data and service_data.get('schedule_start'):
                try:
                    default_start = datetime.strptime(str(service_data['schedule_start']), '%Y-%m-%d').date()
                except ValueError:
                    pass
            if service_data and service_data.get('schedule_end'):
                try:
                    default_end = datetime.strptime(str(service_data['schedule_end']), '%Y-%m-%d').date()
                except ValueError:
                    pass
            frequency_default = service_data.get('schedule_frequency', 'weekly') if service_data else 'weekly'
            frequency_var = tk.StringVar(value=frequency_default)

            row = 0
            ttk.Label(form_frame, text="Phase:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            phase_combo = ttk.Combobox(form_frame, textvariable=phase_var, width=40, state="normal")
            if self.review_service:
                phase_combo['values'] = self.review_service.get_available_phases()
            phase_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            row += 1

            ttk.Label(form_frame, text="Service Code:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            service_code_combo = ttk.Combobox(form_frame, textvariable=service_code_var, width=20, state="normal")
            if self.review_service:
                service_code_combo['values'] = self.review_service.get_available_service_codes()
            service_code_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Service Name:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            service_name_entry = ttk.Entry(form_frame, textvariable=service_name_var, width=40)
            service_name_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            row += 1

            ttk.Label(form_frame, text="Unit Type:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            unit_type_combo = ttk.Combobox(form_frame, textvariable=unit_type_var, width=20, state="readonly")
            unit_type_combo['values'] = ['lump_sum', 'review', 'audit', 'hourly']
            unit_type_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Unit Quantity:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=unit_qty_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Unit Rate ($):").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=unit_rate_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Lump Sum Fee ($):").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=lump_sum_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Bill Rule:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            bill_rule_combo = ttk.Combobox(form_frame, textvariable=bill_rule_var, width=20, state="readonly")
            bill_rule_combo['values'] = ['on_completion', 'per_unit_complete', 'on_setup', 'on_report_issue', 'monthly']
            bill_rule_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Schedule Start:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            start_entry = DateEntry(form_frame, width=15, date_pattern='yyyy-mm-dd')
            start_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
            start_entry.set_date(default_start)
            row += 1

            ttk.Label(form_frame, text="Schedule End:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            end_entry = DateEntry(form_frame, width=15, date_pattern='yyyy-mm-dd')
            end_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
            end_entry.set_date(default_end)
            row += 1

            ttk.Label(form_frame, text="Review Frequency:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            frequency_combo = ttk.Combobox(form_frame, textvariable=frequency_var, width=15, state="readonly")
            frequency_combo['values'] = ['one-off', 'weekly', 'bi-weekly', 'monthly']
            frequency_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1

            ttk.Label(form_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W+tk.N, padx=(0, 5), pady=2)
            notes_text = tk.Text(form_frame, width=40, height=4)
            notes_text.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            notes_text.insert(tk.END, notes_var.get())
            row += 1

            form_frame.columnconfigure(1, weight=1)

            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            def save_service():
                try:
                    start_value = start_entry.get_date()
                    end_value = end_entry.get_date()
                    if end_value < start_value:
                        messagebox.showerror("Error", "Schedule end date cannot be before start date")
                        return

                    unit_qty = float(unit_qty_var.get() or 0)
                    unit_rate = float(unit_rate_var.get() or 0)
                    lump_sum = float(lump_sum_var.get() or 0)

                    if unit_type_var.get() == 'lump_sum':
                        agreed_fee = lump_sum
                    else:
                        agreed_fee = unit_qty * unit_rate

                    new_service_data = {
                        'project_id': self.current_project_id,
                        'phase': phase_var.get().strip(),
                        'service_code': service_code_var.get().strip(),
                        'service_name': service_name_var.get().strip(),
                        'unit_type': unit_type_var.get(),
                        'unit_qty': unit_qty,
                        'unit_rate': unit_rate,
                        'lump_sum_fee': lump_sum,
                        'agreed_fee': agreed_fee,
                        'bill_rule': bill_rule_var.get(),
                        'notes': notes_text.get(1.0, tk.END).strip()
                    }

                    start_str = start_value.strftime('%Y-%m-%d')
                    end_str = end_value.strftime('%Y-%m-%d')
                    frequency = frequency_var.get() or 'weekly'

                    if service_data and service_data.get('service_id'):
                        service_id = int(service_data['service_id'])
                        new_service_data['status'] = service_data.get('status', 'active')
                        new_service_data['progress_pct'] = service_data.get('progress_pct')
                        new_service_data['claimed_to_date'] = service_data.get('claimed_to_date')

                        success = self.review_service.update_project_service(service_id, new_service_data)
                        if success:
                            self.review_service.upsert_service_schedule(service_id, start_str, end_str, frequency)
                            if unit_type_var.get() == 'review':
                                self.review_service.rebuild_service_reviews(service_id)
                            else:
                                self.review_service.delete_service_reviews(service_id)
                            messagebox.showinfo("Success", "Service updated successfully")
                            dialog.destroy()
                        else:
                            messagebox.showerror("Error", "Failed to update service")
                            return
                    else:
                        # Check for duplicate service before inserting
                        existing_services = self.review_service.get_project_services(self.current_project_id)
                        duplicate = False
                        for svc in existing_services:
                            if (svc.get('service_code', '').strip().lower() == new_service_data['service_code'].strip().lower() and
                                svc.get('phase', '').strip().lower() == new_service_data['phase'].strip().lower() and
                                svc.get('service_name', '').strip().lower() == new_service_data['service_name'].strip().lower()):
                                duplicate = True
                                break
                        if duplicate:
                            messagebox.showerror("Error", "A service with the same code, phase, and name already exists for this project.")
                            return
                        service_id = self.review_service.create_project_service(new_service_data)
                        if service_id:
                            self.review_service.upsert_service_schedule(service_id, start_str, end_str, frequency)
                            if unit_type_var.get() == 'review':
                                self.review_service.rebuild_service_reviews(service_id)
                            else:
                                self.review_service.delete_service_reviews(service_id)
                            messagebox.showinfo("Success", f"Service created successfully with ID: {service_id}")
                            dialog.destroy()
                        else:
                            messagebox.showerror("Error", "Failed to create service")
                            return

                    self.load_project_services()
                    self.load_billing_data()
                    self.refresh_cycles()
                    
                    # Automatically update stages and cycles after service modification
                    # Note: Don't call auto_update_stages_and_cycles here as it might cause refresh conflicts
                    print("🔄 Service saved successfully - UI refreshed")
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid numeric values for quantities and fees")
                except Exception as exc:
                    messagebox.showerror("Error", f"Error saving service: {exc}")

            ttk.Button(button_frame, text="Save", command=save_service).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

            phase_combo.focus()
        except Exception as e:
            messagebox.showerror("Error", f"Error showing service dialog: {e}")
    
    def edit_service(self):
        """Edit selected service"""
        try:
            selection = self.services_tree.selection()
            if not selection:
                messagebox.showerror("Error", "Please select a service to edit")
                return
            item = self.services_tree.item(selection[0])
            service_tuple = item['values'] if 'values' in item else None
            if not service_tuple or len(service_tuple) < 1 or not self.review_service:
                messagebox.showerror("Error", "Unable to load service details")
                return
            
            # Get the service_id from the treeview
            service_id = service_tuple[0]
            if not service_id:
                messagebox.showerror("Error", "Invalid service ID")
                return
            
            # Load the full service data from handlers.database
            services = self.review_service.get_project_services(self.current_project_id)
            service_data = None
            for svc in services:
                if str(svc.get('service_id', '')) == str(service_id):
                    service_data = svc
                    break
            
            if not service_data:
                messagebox.showerror("Error", "Service not found in database")
                return
            
            # Show dialog for editing, passing service_data as dictionary
            self.show_service_dialog(service_data)
        except Exception as e:
            messagebox.showerror("Error", f"Error editing service: {e}")
    
    def delete_service(self):
        """Delete selected service"""
        try:
            selection = self.services_tree.selection()
            if not selection:
                messagebox.showerror("Error", "Please select a service to delete")
                return
            item = self.services_tree.item(selection[0])
            service_data = item['values'] if 'values' in item else None
            if not service_data or not self.review_service:
                messagebox.showerror("Error", "Invalid service selected")
                return
            # Extract service_id and service_name from service_data
            # Adjust indices as per your treeview column order
            service_id = service_data[0] if len(service_data) > 0 else None
            service_name = service_data[2] if len(service_data) > 2 else ""
            result = messagebox.askyesno("Confirm Delete", 
                f"Are you sure you want to delete the service:\n\n{service_name}\n\nThis action cannot be undone.")
            if result:
                if self.review_service.delete_project_service(service_id):
                    messagebox.showinfo("Success", "Service deleted successfully")
                    self.load_project_services()  # Refresh the services list
                    print("🔄 Auto-updating stages and cycles after service deletion...")
                    self.auto_update_stages_and_cycles()
                else:
                    messagebox.showerror("Error", "Failed to delete service")
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting service: {e}")
    
    def clear_services(self):
        """Clear all services for the current project"""
        try:
            if not self.current_project_id:
                messagebox.showerror("Error", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Get count of services to confirm
            services = self.review_service.get_project_services(self.current_project_id)
            service_count = len(services)
            
            if service_count == 0:
                messagebox.showinfo("Info", "No services to clear")
                return
            
            # Confirm deletion
            result = messagebox.askyesno("Confirm Clear All Services", 
                f"Are you sure you want to clear ALL {service_count} services for this project?\n\n"
                "This will also delete any associated review cycles and schedules.\n\n"
                "This action cannot be undone.")
            
            if result:
                # Clear all services
                deleted_count = self.review_service.clear_all_project_services(self.current_project_id)
                
                if deleted_count > 0:
                    messagebox.showinfo("Success", f"Successfully cleared {deleted_count} services")
                    self.load_project_services()  # Refresh the services list
                    self.load_billing_data()  # Refresh billing data
                    self.refresh_cycles()  # Refresh review cycles
                    
                    # Automatically update stages and cycles after clearing services
                    print("🔄 Auto-updating stages and cycles after clearing services...")
                    self.auto_update_stages_and_cycles()
                else:
                    messagebox.showerror("Error", "Failed to clear services")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error clearing services: {e}")
    
    def update_service_status(self):
        """Update status for non-review services (lump_sum, audit, etc.)"""
        try:
            selection = self.services_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a service first")
                return
            
            item = self.services_tree.item(selection[0])
            service_data = item['values'] if 'values' in item else None
            if not service_data or not self.review_service:
                messagebox.showerror("Error", "Invalid service selected")
                return
            
            # Extract service details
            service_id = service_data[0] if len(service_data) > 0 else None
            service_name = service_data[3] if len(service_data) > 3 else ""
            unit_type = service_data[4] if len(service_data) > 4 else ""
            current_status = service_data[8] if len(service_data) > 8 else "not_started"
            
            # Check if this is a review-type service
            if unit_type.lower() == 'review':
                messagebox.showinfo("Info", 
                    "Review-type services are managed through review cycles.\n"
                    "Use the Review Planning tab to manage review statuses.")
                return
            
            # Create status update dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Update Status: {service_name}")
            dialog.geometry("400x200")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Status selection
            ttk.Label(dialog, text=f"Service: {service_name}", 
                     font=("Arial", 10, "bold")).pack(pady=10)
            ttk.Label(dialog, text=f"Type: {unit_type}", 
                     font=("Arial", 9)).pack(pady=5)
            ttk.Label(dialog, text=f"Current Status: {current_status}", 
                     font=("Arial", 9)).pack(pady=5)
            
            ttk.Label(dialog, text="Select New Status:", 
                     font=("Arial", 10)).pack(pady=10)
            
            status_var = tk.StringVar(value=current_status)
            status_frame = ttk.Frame(dialog)
            status_frame.pack(pady=10)
            
            ttk.Radiobutton(status_frame, text="[ ] Planned (0%)", 
                           variable=status_var, value="planned").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(status_frame, text="[~] In Progress (50%)", 
                           variable=status_var, value="in_progress").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(status_frame, text="[X] Completed (100%)", 
                           variable=status_var, value="completed").pack(anchor=tk.W, pady=2)
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=15)
            
            def save_status():
                new_status = status_var.get()
                if self.review_service.set_non_review_service_status(service_id, new_status):
                    progress_map = {'planned': 0, 'in_progress': 50, 'completed': 100}
                    messagebox.showinfo("Success", 
                        f"Status updated to '{new_status}'\n"
                        f"Progress set to: {progress_map[new_status]}%")
                    self.load_project_services()  # Refresh display
                    self.load_billing_data()  # Refresh billing since progress changed
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update status")
            
            ttk.Button(button_frame, text="Save", command=save_status).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error updating service status: {e}")
            import traceback
            traceback.print_exc()
    
    def on_cycle_filter_changed(self, event=None):
        """Handle cycle filter change"""
        selection = self.cycle_filter_var.get()
        if selection in ("All Cycles", "", None):
            self.current_cycle_id = None
        else:
            self.current_cycle_id = selection
        self.refresh_cycles()
    
    def load_review_tasks(self):
        """Load review tasks for current project/cycle"""
        try:
            # Check if tasks_tree exists and is not None
            if not hasattr(self, 'tasks_tree') or self.tasks_tree is None:
                return
                
            # Clear existing tasks
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
            
            if not self.current_project_id:
                return
            
            # Get service reviews
            if self.review_service:
                if self.current_cycle_id:
                    reviews = self.review_service.get_service_reviews(self.current_project_id, self.current_cycle_id)
                else:
                    reviews = self.review_service.get_service_reviews(self.current_project_id)

                for review in reviews:
                    values = (
                        review.get('review_id', ''),
                        review.get('service_name', ''),
                        review.get('cycle_no', ''),
                        review.get('due_date', ''),
                        review.get('status', ''),
                        review.get('assignee', 'Unassigned'),
                        f"{review.get('progress', 0)}%",
                        review.get('evidence_links', '')
                    )
                    self.tasks_tree.insert("", tk.END, values=values)
                    
        except Exception as e:
            print(f"Error loading review tasks: {e}")
    
    def edit_review_task(self, event):
        """Handle review task editing"""
        try:
            selection = self.tasks_tree.selection()
            if not selection:
                return
            
            item = self.tasks_tree.item(selection[0])
            task_data = item['values']
            
            if len(task_data) >= 1:
                review_id = task_data[0]
                messagebox.showinfo("Info", f"Edit review {review_id} - Feature coming soon!")
                
        except Exception as e:
            print(f"Error editing review task: {e}")
    
    def update_review_status(self):
        """Update status of selected review"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review to update")
                return
            
            # Get selected review data
            item = self.cycles_tree.item(selection[0])
            review_data = item['values']
            
            if not review_data:
                messagebox.showwarning("Warning", "Invalid review selection")
                return
            
            review_id = review_data[0]  # Review ID is first column
            current_status = review_data[6]  # Status is 7th column (index 6)
            
            # Create status update dialog
            self.show_status_update_dialog(review_id, current_status)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error updating review status: {e}")
    
    def show_status_update_dialog(self, review_id, current_status):
        """Show dialog for updating review status"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Update Review Status")
        dialog.geometry("400x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(main_frame, text=f"Update Status for Review ID: {review_id}", 
                font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # Current status
        tk.Label(main_frame, text=f"Current Status: {current_status}", 
                font=('Arial', 10)).pack(pady=(0, 10))
        
        # New status selection
        tk.Label(main_frame, text="New Status:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        status_options = ['planned', 'in_progress', 'completed', 'report_issued', 'closed', 'cancelled']
        status_var = tk.StringVar(value=current_status)
        
        status_combo = ttk.Combobox(main_frame, textvariable=status_var, 
                                   values=status_options, state='readonly', width=20)
        status_combo.pack(pady=(0, 15))
        
        # Evidence link (optional)
        tk.Label(main_frame, text="Evidence Link (optional):", font=('Arial', 10)).pack(anchor='w', pady=(0, 5))
        evidence_var = tk.StringVar()
        evidence_entry = tk.Entry(main_frame, textvariable=evidence_var, width=40)
        evidence_entry.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def update_status():
            new_status = status_var.get()
            evidence_link = evidence_var.get().strip() if evidence_var.get().strip() else None
            
            if new_status == current_status and not evidence_link:
                messagebox.showinfo("Info", "No changes to apply")
                return
            
            try:
                # Update status using review management service
                if hasattr(self, 'review_service') and self.review_service:
                    success = self.review_service.update_review_status_to(review_id, new_status, evidence_link)
                else:
                    # Create service instance if not available
                    from handlers.review_management_service import ReviewManagementService
                    try:
                        with get_db_connection() as db_conn:
                            service = ReviewManagementService(db_conn)
                            success = service.update_review_status_to(review_id, new_status, evidence_link)
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not connect to database: {e}")
                        return
                
                if success:
                    messagebox.showinfo("Success", f"Review status updated to '{new_status}'")
                    dialog.destroy()
                    self.refresh_cycles()  # Refresh the cycles display
                else:
                    messagebox.showerror("Error", "Failed to update review status")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error updating status: {e}")
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        tk.Button(button_frame, text="Update", command=update_status, 
                 bg='#4CAF50', fg='white', padx=20).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(button_frame, text="Cancel", command=cancel, 
                 padx=20).pack(side=tk.RIGHT)
    
    def submit_schedule(self):
        """Submit review schedule"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            # Use the review handler to submit schedule
            result = submit_review_schedule(self.current_project_id, self.current_cycle_id)
            if result:
                messagebox.showinfo("Success", "Review schedule submitted successfully")
                self.refresh_data()
            else:
                messagebox.showerror("Error", "Failed to submit review schedule")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error submitting schedule: {e}")
    
    def launch_gantt(self):
        """Launch Gantt chart for current project"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            from ui.gantt_chart import launch_gantt_chart
            launch_gantt_chart(self.current_project_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error launching Gantt chart: {e}")
    
    def show_contract_links(self):
        """Show contractual links for current project/cycle"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            links = get_contractual_links(self.current_project_id, self.current_cycle_id)
            
            # Create popup window
            win = tk.Toplevel(self.frame)
            win.title("Contractual Links")
            win.geometry("800x400")
            
            columns = ("BEP Clause", "Billing Event", "Amount Due", "Status")
            tree = ttk.Treeview(win, columns=columns, show="headings")
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=180, anchor="w")
            
            for row in links:
                tree.insert("", tk.END, values=row)
            
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing contract links: {e}")
    
    def edit_review_cycle(self):
        """Edit the selected review cycle"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review cycle to edit")
                return
            
            # Get selected review data
            item = self.cycles_tree.item(selection[0])
            values = item['values']
            review_id = values[0]
            cycle_name = values[1]
            planned_start = values[2]
            status = values[3]
            stage = values[4]
            
            # Create edit dialog
            self.show_edit_review_dialog(review_id, cycle_name, planned_start, status, stage)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error editing review cycle: {e}")
    
    def delete_review_cycle(self):
        """Delete the selected review cycle"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review cycle to delete")
                return
            
            # Get selected review data
            item = self.cycles_tree.item(selection[0])
            values = item['values']
            review_id = values[0]
            cycle_name = values[1]
            
            # Confirm deletion
            result = messagebox.askyesno(
                "Confirm Deletion", 
                f"Are you sure you want to delete the review cycle:\n\n{cycle_name}\n\nThis action cannot be undone."
            )
            
            if result:
                success = self.delete_review_from_database(review_id)
                if success:
                    messagebox.showinfo("Success", "Review cycle deleted successfully")
                    self.refresh_cycles()
                else:
                    messagebox.showerror("Error", "Failed to delete review cycle")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting review cycle: {e}")
    
    def delete_all_reviews(self):
        """Delete all review cycles for the current project"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            # Count existing reviews
            review_count = len(self.cycles_tree.get_children())
            
            if review_count == 0:
                messagebox.showinfo("Info", "No reviews to delete")
                return
            
            # Confirm deletion
            result = messagebox.askyesno(
                "Confirm Delete All", 
                f"Are you sure you want to delete ALL {review_count} review cycles for this project?\n\n"
                "This will also delete the associated services that were created for review generation.\n\n"
                "This action cannot be undone."
            )
            
            if result:
                print(f"🗑️ User confirmed deletion for project {self.current_project_id}")
                
                if self.review_service:
                    # Use the service method for better consistency
                    delete_result = self.review_service.delete_all_project_reviews(self.current_project_id)
                    
                    if delete_result.get('success'):
                        messagebox.showinfo(
                            "Success", 
                            f"Successfully deleted:\n"
                            f"• {delete_result['reviews_deleted']} review cycles\n"
                            f"• {delete_result['services_deleted']} auto-generated services"
                        )
                        # Simple refresh - just the cycles tree
                        self.refresh_cycles()
                    else:
                        error_msg = delete_result.get('error', 'Unknown error occurred')
                        messagebox.showerror("Error", f"Failed to delete reviews: {error_msg}")
                else:
                    # Fallback to direct database method
                    success = self.delete_all_reviews_from_database()
                    if success:
                        messagebox.showinfo("Success", f"All {review_count} review cycles deleted successfully")
                        self.refresh_cycles()
                    else:
                        messagebox.showerror("Error", "Failed to delete all review cycles")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting all review cycles: {e}")
    
    def mark_review_issued(self):
        """Mark the selected review as issued"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review cycle to mark as issued")
                return
            
            # Get selected review data
            item = self.cycles_tree.item(selection[0])
            values = item['values']
            review_id = values[0]
            cycle_name = values[1]
            
            # Confirm action
            result = messagebox.askyesno(
                "Mark as Issued", 
                f"Mark the following review cycle as issued:\n\n{cycle_name}\n\nThis will update the status to 'report_issued'."
            )
            
            if result:
                # Prompt for evidence link (optional)
                evidence_link = tk.simpledialog.askstring(
                    "Evidence Link", 
                    "Enter evidence link (optional):",
                    initialvalue=""
                )
                
                if self.review_service:
                    success = self.review_service.mark_review_issued(review_id, evidence_link)
                    if success:
                        messagebox.showinfo("Success", "Review marked as issued successfully")
                        self.refresh_cycles()
                    else:
                        messagebox.showerror("Error", "Failed to mark review as issued")
                else:
                    messagebox.showerror("Error", "Review service not available")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error marking review as issued: {e}")
    
    def mark_review_completed(self):
        """Mark the selected review as completed"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review cycle to mark as completed")
                return
            
            # Get selected review data
            item = self.cycles_tree.item(selection[0])
            values = item['values']
            review_id = values[0]
            cycle_name = values[1]
            
            # Confirm action
            result = messagebox.askyesno(
                "Mark as Completed", 
                f"Mark the following review cycle as completed:\n\n{cycle_name}\n\nThis will update the status to 'completed'."
            )
            
            if result:
                # Prompt for evidence link (optional)
                evidence_link = tk.simpledialog.askstring(
                    "Evidence Link", 
                    "Enter evidence link (optional):",
                    initialvalue=""
                )
                
                if self.review_service:
                    # Use the update_review_status_to method to mark as completed
                    success = self.review_service.update_review_status_to(review_id, 'completed', evidence_link)
                    if success:
                        messagebox.showinfo("Success", "Review marked as completed successfully")
                        self.refresh_cycles()
                    else:
                        messagebox.showerror("Error", "Failed to mark review as completed")
                else:
                    messagebox.showerror("Error", "Review service not available")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error marking review as completed: {e}")
    
    def show_edit_review_dialog(self, review_id, cycle_name, planned_start, status, stage):
        """Show dialog to edit review cycle details"""
        try:
            # Create edit window
            edit_win = tk.Toplevel(self.frame)
            edit_win.title(f"Edit Review Cycle: {cycle_name}")
            edit_win.geometry("500x400")
            edit_win.transient(self.frame)
            edit_win.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(edit_win, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Review ID (read-only)
            ttk.Label(main_frame, text="Review ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            ttk.Label(main_frame, text=str(review_id), background="lightgray").grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Cycle name (read-only)
            ttk.Label(main_frame, text="Cycle:").grid(row=1, column=0, sticky=tk.W, pady=5)
            ttk.Label(main_frame, text=cycle_name, background="lightgray").grid(row=1, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Planned start date
            ttk.Label(main_frame, text="Meeting Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
            start_date_var = tk.StringVar(value=planned_start)
            start_date_entry = DateEntry(main_frame, textvariable=start_date_var, width=12, 
                                       background='darkblue', foreground='white', 
                                       borderwidth=2, date_pattern='yyyy-mm-dd')
            start_date_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Status
            ttk.Label(main_frame, text="Status:").grid(row=3, column=0, sticky=tk.W, pady=5)
            status_var = tk.StringVar(value=status)
            status_combo = ttk.Combobox(main_frame, textvariable=status_var, width=15, state="readonly")
            status_combo['values'] = ["planned", "in_progress", "report_issued", "completed", "on_hold", "cancelled"]
            status_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Stage/Disciplines
            ttk.Label(main_frame, text="Stage/Disciplines:").grid(row=4, column=0, sticky=tk.W, pady=5)
            stage_var = tk.StringVar(value=stage)
            stage_entry = ttk.Entry(main_frame, textvariable=stage_var, width=30)
            stage_entry.grid(row=4, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Notes
            ttk.Label(main_frame, text="Notes:").grid(row=5, column=0, sticky=tk.NW, pady=5)
            notes_text = tk.Text(main_frame, width=40, height=4)
            notes_text.grid(row=5, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=6, column=0, columnspan=2, pady=20)
            
            def save_changes():
                try:
                    # Update review in database
                    success = self.update_review_in_database(
                        review_id,
                        start_date_var.get(),
                        status_var.get(),
                        stage_var.get(),
                        notes_text.get("1.0", tk.END).strip()
                    )
                    
                    if success:
                        messagebox.showinfo("Success", "Review cycle updated successfully")
                        edit_win.destroy()
                        self.refresh_cycles()
                    else:
                        messagebox.showerror("Error", "Failed to update review cycle")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Error saving changes: {e}")
            
            def cancel_edit():
                edit_win.destroy()
            
            ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.LEFT, padx=10)
            
            # Configure column weights
            main_frame.columnconfigure(1, weight=1)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing edit dialog: {e}")
    
    def update_review_in_database(self, review_id, planned_start, status, stage, notes):
        """Update review cycle in database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # FIX 1: Update BOTH planned_date AND due_date (due_date is used by refresh logic)
                # FIX 2: Add status_override flag to mark as manual override
                # FIX 3: Store notes in evidence_links with timestamp
                from datetime import datetime
                
                # Format notes with timestamp if provided
                note_entry = ""
                if notes:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                    note_entry = f"[{timestamp}] {notes}"
                
                update_sql = """
                UPDATE ServiceReviews 
                SET planned_date = ?, 
                    due_date = ?,  -- CRITICAL FIX: Also update due_date (used by refresh logic)
                    status = ?, 
                    disciplines = ?,
                    evidence_links = CASE 
                        WHEN evidence_links IS NULL OR evidence_links = '' THEN ?
                        ELSE evidence_links + CHAR(10) + ?
                    END,
                    status_override = 1,  -- CRITICAL FIX: Mark as manual override
                    status_override_by = SYSTEM_USER,
                    status_override_at = SYSDATETIME()
                WHERE review_id = ?
                """
                
                cursor.execute(update_sql, (
                    planned_start, 
                    planned_start,  # Use same date for due_date
                    status, 
                    stage,
                    note_entry,
                    note_entry,
                    review_id
                ))
                conn.commit()
                
                print(f"✅ Review {review_id} updated with manual override flag")
                return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating review in database: {e}")
            return False
    
    def delete_review_from_database(self, review_id):
        """Delete review cycle from handlers.database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Delete from ServiceReviews table
                delete_sql = "DELETE FROM ServiceReviews WHERE review_id = ?"
                cursor.execute(delete_sql, (review_id,))
                conn.commit()
                
                return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting review from handlers.database: {e}")
            return False
    
    def delete_all_reviews_from_database(self):
        """Delete all review cycles for the current project from handlers.database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First, get all service IDs that are auto-generated review services for this project
                get_services_sql = """
                SELECT service_id FROM ProjectServices 
                WHERE project_id = ? AND service_code = 'STAGE_REVIEW'
                """
                cursor.execute(get_services_sql, (self.current_project_id,))
                service_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete all ServiceReviews for this project (CASCADE should handle this, but be explicit)
                delete_reviews_sql = """
                DELETE sr FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
                """
                cursor.execute(delete_reviews_sql, (self.current_project_id,))
                reviews_deleted = cursor.rowcount
                
                # Delete auto-generated services (those with service_code = 'STAGE_REVIEW')
                delete_services_sql = """
                DELETE FROM ProjectServices 
                WHERE project_id = ? AND service_code = 'STAGE_REVIEW'
                """
                cursor.execute(delete_services_sql, (self.current_project_id,))
                services_deleted = cursor.rowcount
                
                conn.commit()
                
                print(f"? Deleted {reviews_deleted} reviews and {services_deleted} auto-generated services")
                return True
            
        except Exception as e:
            print(f"Error deleting all reviews from handlers.database: {e}")
            return False
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected()

    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()

    def confirm_due_reviews(self):
        """Prompt user to confirm auto-completion of due reviews"""
        try:
            if not getattr(self, 'auto_complete_candidates', []):
                messagebox.showinfo("Reviews", "No reviews are awaiting confirmation.")
                return

            dialog = tk.Toplevel(self.frame)
            dialog.title("Confirm Due Reviews")
            dialog.geometry("520x360")
            dialog.transient(self.frame.winfo_toplevel())
            dialog.grab_set()

            container = ttk.Frame(dialog, padding=10)
            container.pack(fill=tk.BOTH, expand=True)

            ttk.Label(
                container,
                text="Select the reviews to mark as completed:",
                font=("Arial", 10, "bold")
            ).pack(anchor='w', pady=(0, 10))

            vars = []
            checklist_frame = ttk.Frame(container)
            checklist_frame.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(checklist_frame, borderwidth=0, highlightthickness=0)
            scrollbar = ttk.Scrollbar(checklist_frame, orient=tk.VERTICAL, command=canvas.yview)
            inner_frame = ttk.Frame(canvas)

            inner_frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set, height=220)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for candidate in self.auto_complete_candidates:
                var = tk.BooleanVar(value=True)
                label = f"{candidate['label']} (Due {candidate['due_date'] or 'n/a'})"
                ttk.Checkbutton(inner_frame, text=label, variable=var).pack(anchor='w', pady=2)
                vars.append((var, candidate))

            button_frame = ttk.Frame(container)
            button_frame.pack(fill=tk.X, pady=(12, 0))

            def confirm():
                if not self.review_service:
                    dialog.destroy()
                    return
                selected_ids = [candidate['review_id'] for var, candidate in vars if var.get()]
                if selected_ids:
                    updated = self.review_service.mark_reviews_completed(selected_ids)
                    messagebox.showinfo("Reviews", f"Marked {updated} review(s) as completed.")
                dialog.destroy()
                self.refresh_cycles()

            ttk.Button(button_frame, text="Confirm Completed", command=confirm).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("Error", f"Error confirming reviews: {e}")
    
    def refresh_project_statuses(self):
        """Refresh all project statuses based on current date"""
        try:
            if not self.current_project_id or not self.review_service:
                return
                
            print(f"🔄 Refreshing statuses for project {self.current_project_id}...")
            
            # Call the comprehensive status refresh
            results = self.review_service.refresh_all_project_statuses(self.current_project_id)
            
            if results['reviews_updated'] > 0 or results['services_updated'] > 0:
                # Refresh UI components if changes were made
                self.load_project_services()
                self.load_billing_data()
                self.refresh_cycles()
                
                # Show notification if significant updates occurred
                if results['reviews_updated'] > 0:
                    print(f"✅ Auto-updated {results['reviews_updated']} review statuses")
                if results['services_updated'] > 0:
                    print(f"✅ Auto-updated {results['services_updated']} service progress percentages")
                    
        except Exception as e:
            print(f"❌ Error refreshing project statuses: {e}")

    def refresh_cycles_by_meeting_dates(self):
        """Refresh review cycles based on meeting dates with automatic status progression"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
                
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Show confirmation dialog
            result = messagebox.askyesno(
                "Refresh Review Cycles by Dates", 
                "This will update review statuses based on meeting dates:\n\n"
                "• Past meetings → Completed\n"
                "• Next upcoming meeting → In Progress\n"
                "• Future meetings → Planned\n\n"
                "Status percentages will be updated in Project Setup and Service Review Planning.\n\n"
                "Continue?",
                icon="question"
            )
            
            if not result:
                return
            
            print(f"🔄 Refreshing review cycles by meeting dates for project {self.current_project_id}")
            
            # Call the new comprehensive refresh method
            results = self.review_service.refresh_review_cycles_by_date(self.current_project_id)
            
            print(f"🔍 UI received results: {results}")
            
            if results.get('success', False):
                # Update UI components with new data
                self.load_services_for_review_planning()  # Refresh service percentages
                self.update_kpi_dashboard()  # Refresh Project Setup KPIs
                self.refresh_cycles()  # Refresh review cycles display
                # Update UI components with new data
                self.load_services_for_review_planning()  # Refresh service percentages
                self.update_kpi_dashboard()  # Refresh Project Setup KPIs
                self.refresh_cycles()  # Refresh review cycles display
                
                # Show success message with details
                message = f"""Review Cycles Updated Successfully!

📋 Reviews Updated: {results['reviews_updated']}
📊 Status percentages refreshed
🎯 Project KPIs updated

The system has automatically updated review statuses based on meeting dates:
• Past meetings are marked as completed
• The next upcoming meeting is set to in progress  
• Future meetings remain planned

All status percentages in Project Setup and Service Review Planning have been updated."""
                
                messagebox.showinfo("Success", message)
                
                # Log the update for debugging
                print(f"✅ Date-based refresh completed: {results['reviews_updated']} reviews updated")
                
            else:
                error_msg = results.get('error', 'Unknown error occurred')
                messagebox.showerror("Error", f"Failed to refresh review cycles:\n\n{error_msg}")
                print(f"❌ Date-based refresh failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Error refreshing cycles by dates: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"❌ {error_msg}")

    def manual_refresh_statuses(self):
        """Manual refresh button handler for status updates with override protection"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
                
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # NEW: Check for manual overrides and show confirmation
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM ServiceReviews sr
                        INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                        WHERE ps.project_id = ? AND ISNULL(sr.status_override, 0) = 1
                    """, (self.current_project_id,))
                    override_count = cursor.fetchone()[0]
                    
                    if override_count > 0:
                        result = messagebox.askyesno(
                            "Refresh Status", 
                            f"This will auto-update review statuses based on meeting dates.\n\n"
                            f"⚠️  {override_count} review(s) have manual status overrides.\n"
                            f"These will NOT be changed.\n\n"
                            f"Continue with refresh?"
                        )
                        if not result:
                            return
            except Exception as e:
                print(f"Error checking override count: {e}")
                result = True  # Continue anyway if can't check
                
            results = self.review_service.refresh_all_project_statuses(self.current_project_id)
            
            # Enhanced results dialog with override information
            skipped = results.get('skipped_count', 0)
            summary = f"""Status Refresh Results:

📋 Reviews Auto-Updated: {results['reviews_updated']}
🔒 Manual Overrides Preserved: {skipped}
🔧 Services Updated: {results['services_updated']}
📊 Overall Status: {results['overall_status'].get('status_summary', 'Unknown')}
📈 Progress: {results['overall_status'].get('progress_percentage', 0):.1f}%

Completed: {results['overall_status'].get('completed_reviews', 0)}
In Progress: {results['overall_status'].get('in_progress_reviews', 0)}
Planned: {results['overall_status'].get('planned_reviews', 0)}"""

            if results['errors']:
                summary += f"\n\n❌ Errors:\n" + "\n".join(results['errors'])
                
            messagebox.showinfo("Status Refresh Complete", summary)
            
            # Refresh UI
            self.load_project_services()
            self.load_billing_data()
            self.refresh_cycles()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing statuses: {e}")
    
    def reset_review_to_auto(self):
        """Reset selected review to automatic status management"""
        try:
            selection = self.cycles_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a review to reset")
                return
            
            item = self.cycles_tree.item(selection[0])
            review_data = item['values']
            review_id = review_data[0]
            current_status = review_data[3]  # Status with possible lock icon
            
            # Check if it has override
            if not str(current_status).startswith("🔒"):
                messagebox.showinfo("Info", "This review is already using automatic status management")
                return
            
            # Confirm action
            result = messagebox.askyesno(
                "Reset to Auto", 
                "This will reset the review to automatic status management.\\n"
                "The status will be recalculated based on the meeting date.\\n\\n"
                "Continue?"
            )
            
            if not result:
                return
            
            # Clear override flag
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE ServiceReviews 
                        SET status_override = 0,
                            status_override_by = NULL,
                            status_override_at = NULL
                        WHERE review_id = ?
                    """, (review_id,))
                    conn.commit()
                    
                    # Trigger refresh to recalculate status
                    if self.review_service:
                        # Force recalculation for this review
                        self.review_service.update_service_statuses_by_date(
                            self.current_project_id, 
                            respect_overrides=False  # Force recalculation
                        )
                    
                    messagebox.showinfo("Success", "Review reset to automatic status management")
                    self.refresh_cycles()
            except Exception as e:
                messagebox.showerror("Error", f"Error resetting to auto: {e}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error resetting to auto: {e}")


class DuplicateProjectSetupTab:
    """Project Setup and Management Interface - For creating and managing projects"""
    
    def __init__(self, parent_notebook):
        print("?? ProjectSetupTab: Starting initialization...")
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="??? Project Setup")
        print("? ProjectSetupTab: Frame created and added to notebook")
        
        print("?? ProjectSetupTab: Setting up UI...")
        self.setup_ui()
        print("? ProjectSetupTab: UI setup completed")
        
        print("?? ProjectSetupTab: Refreshing data...")
        self.refresh_data()
        print("? ProjectSetupTab: Data refresh completed")
        
        # Register for project change notifications
        print("?? ProjectSetupTab: Registering for project notifications...")
        project_notification_system.register_observer(self)
        print("? ProjectSetupTab: Initialization completed successfully")
    
    def setup_ui(self):
        """Set up the project setup interface"""

        # Main container with padding
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== TOP SECTION: PROJECT SELECTION =====
        project_frame = ttk.LabelFrame(main_frame, text="Project Selection & Status", padding=15)
        project_frame.pack(fill="x", pady=(0, 15))

        # Current project selection
        selection_frame = ttk.Frame(project_frame)
        selection_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(selection_frame, text="Current Project:", font=("Arial", 10, "bold")).pack(side="left")
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(selection_frame, textvariable=self.project_var, width=50)
        self.project_combo.pack(side="left", padx=(10, 0))
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)

class NestedProjectSetupTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.project_var = tk.StringVar()
        self.acc_path_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.setup_ui()  # Initialize UI components

        # Project selection
        project_frame = ttk.Frame(self.frame)
        project_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(project_frame, text="Select Project:").pack(side=tk.LEFT)
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, state="readonly")
        self.project_combo.pack(side=tk.LEFT, padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
        self.refresh_projects()

        # ACC folder path configuration
        path_frame = ttk.Frame(self.frame)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(path_frame, text="ACC Folder Path:").pack(side=tk.LEFT)
        self.acc_path_entry = ttk.Entry(path_frame, textvariable=self.acc_path_var, width=50)
        self.acc_path_entry.pack(side=tk.LEFT, padx=5)
        self.acc_path_button = ttk.Button(path_frame, text="Configure Path", command=self.configure_paths)
        self.acc_path_button.pack(side=tk.LEFT, padx=5)

        # Status label
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT)

        # Extract files button
        extract_frame = ttk.Frame(self.frame)
        extract_frame.pack(fill=tk.X, padx=10, pady=5)
        self.extract_button = ttk.Button(extract_frame, text="Extract ACC Files", command=self.extract_acc_files)
        self.extract_button.pack(side=tk.LEFT)

    def refresh_projects(self):
        projects = get_projects()
        self.project_combo['values'] = [f"{p[0]} - {p[1]}" for p in projects]
        if projects:
            self.project_combo.current(0)
            self.on_project_selected()

    def on_project_selected(self, event=None):
        selected = self.project_var.get()
        if '-' in selected:
            project_id = selected.split('-')[0].strip()
            folder_path = get_acc_folder_path(project_id)
            self.acc_path_var.set(folder_path if folder_path else "")
            self.status_var.set(f"Selected Project: {selected}")
        else:
            messagebox.showerror("Error", "Invalid project selection format")

    def configure_paths(self):
        selected = self.project_var.get()
        if '-' not in selected:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        project_id = selected.split('-')[0].strip()
        folder_path = filedialog.askdirectory(title="Select Desktop Connector Folder")
        if not folder_path:
            messagebox.showwarning("Warning", "No folder selected")
            return
        save_acc_folder_path(project_id, folder_path)
        self.acc_path_var.set(folder_path)
        self.status_var.set(f"Configured folder for project {project_id}")
        messagebox.showinfo("Success", f"Desktop Connector folder path saved for project {project_id}")

    def extract_acc_files(self):
        selected = self.project_var.get()
        if '-' not in selected:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        project_id = selected.split('-')[0].strip()
        folder_path = self.acc_path_var.get()
        if not folder_path:
            messagebox.showwarning("Warning", "No folder path configured")
            return
        try:
            count = insert_files_into_tblACCDocs(project_id, folder_path)
            self.status_var.set(f"Extracted {count} files for project {project_id}")
            messagebox.showinfo("Success", f"Extracted {count} files for project {project_id}")
        except Exception as e:
            self.status_var.set(f"Error extracting files: {e}")
            messagebox.showerror("Error", f"Failed to extract files: {e}")

    def on_project_selected(self, event=None):
        """Handle project selection from dropdown"""
        project_selection = self.project_var.get()
        if project_selection:
            # Parse project name from "ID - Name" format
            if " - " in project_selection:
                project_id_str, project_name = project_selection.split(" - ", 1)
                try:
                    project_id = int(project_id_str)
                except ValueError:
                    project_id = None
            else:
                project_name = project_selection
                project_id = None
            
            # Update status labels
            self.update_project_status(project_name)
            # Notify other tabs with the full selection string
            project_notification_system.notify_project_changed(project_selection)

    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected()

    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()

    def update_project_status(self, project_name):
        """Update the status display for selected project"""
        try:
            # For now, just show that a project is selected
            # TODO: Implement full project data retrieval
            self.status_labels["Client"].config(text="Data not available")
            self.status_labels["Status"].config(text="Data not available")
            self.status_labels["Priority"].config(text="Data not available")
            self.status_labels["Start Date"].config(text="Data not available")
            self.status_labels["End Date"].config(text="Data not available")
            self.status_labels["Model Path"].config(text="Data not available")
            self.status_labels["IFC Path"].config(text="Data not available")
        except Exception as e:
            print(f"Error updating project status: {e}")
            # Clear status labels on error
            for label in self.status_labels.values():
                label.config(text="Error", foreground="red")

    def create_new_project(self):
        """Open create new project dialog"""
        self.show_project_dialog(mode="create")

    def edit_project_details(self):
        """Open edit project details dialog"""
        project_selection = self.project_var.get()
        if not project_selection:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Parse project ID from "ID - Name" format
        if " - " in project_selection:
            project_id_str, project_name = project_selection.split(" - ", 1)
            try:
                project_id = int(project_id_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid project selection format")
                return
        else:
            messagebox.showerror("Error", "Invalid project selection format")
            return
            
        self.show_project_dialog(mode="edit", project_id=project_id)

    def configure_paths(self):
        """Configure Desktop Connector folder path for the current project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        # Parse project ID
        project_selection = self.project_var.get()
        if " - " in project_selection:
            project_id_str, _ = project_selection.split(" - ", 1)
            try:
                project_id = int(project_id_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid project selection format")
                return
        else:
            messagebox.showerror("Error", "Invalid project selection format")
            return

        # Ask user for folder (Desktop Connector)
        folder_path = filedialog.askdirectory(title="Select Desktop Connector Folder")
        if not folder_path:
            messagebox.showwarning("Warning", "No folder selected")
            return

        # Save to database
        from database import save_acc_folder_path
        save_acc_folder_path(project_id, folder_path)
        self.folder_path_var.set(folder_path)
        messagebox.showinfo("Success", f"Desktop Connector folder path saved for project {project_id}")

    def extract_model_files(self):
        """Extract files from configured model folder"""
        # TODO: Implement model file extraction
        messagebox.showinfo("Info", "Model file extraction not yet implemented")

    def extract_acc_files(self):
        """Extract files from Desktop Connector folder and save to SQL database"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        project_selection = self.project_var.get()
        if " - " in project_selection:
            project_id_str, _ = project_selection.split(" - ", 1)
            try:
                project_id = int(project_id_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid project selection format")
                return
        else:
            messagebox.showerror("Error", "Invalid project selection format")
            return

        from database import get_acc_folder_path, insert_files_into_tblACCDocs
        folder_path = get_acc_folder_path(project_id)
        if not folder_path:
            messagebox.showwarning("Warning", "No Desktop Connector folder path configured for this project")
            return
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", f"Folder path does not exist: {folder_path}")
            return

        # Extract files and insert into database
        try:
            result = insert_files_into_tblACCDocs(project_id, folder_path)
            if result:
                messagebox.showinfo("Success", f"Files extracted and stored for Project ID {project_id}.")
            else:
                messagebox.showerror("Error", "No files found or failed to insert.")
        except Exception as e:
            messagebox.showerror("Error", f"Error during extraction: {e}")

    def refresh_data(self):
        """Reload project information from handlers.database"""
        try:
            # Refresh project list
            self.load_projects()
            # Clear current selection
            self.project_var.set("")
            # Clear status labels
            for label in self.status_labels.values():
                label.config(text="Not Selected", foreground="gray")
            messagebox.showinfo("Success", "Project data refreshed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")

    def setup_ui(self):
        # Initialize status labels dictionary
        self.status_labels = {}
        
        # Project selection
        project_frame = ttk.Frame(self.frame)
        project_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(project_frame, text="Select Project:").pack(side=tk.LEFT)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, state="readonly")
        self.project_combo.pack(side=tk.LEFT, padx=5)
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
        
        # Status display labels
        status_fields = ["Client", "Status", "Priority", "Start Date", "End Date", "Model Path", "IFC Path"]
        for field in status_fields:
            self.status_labels[field] = ttk.Label(self.frame, text=f"{field}: Not Selected", foreground="gray")
            self.status_labels[field].pack(fill=tk.X, padx=10, pady=2)
        
        self.refresh_projects()

        # ACC folder path configuration
        path_frame = ttk.Frame(self.frame)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(path_frame, text="ACC Folder Path:").pack(side=tk.LEFT)
        self.acc_path_var = tk.StringVar()
        self.acc_path_entry = ttk.Entry(path_frame, textvariable=self.acc_path_var, width=50)
        self.acc_path_entry.pack(side=tk.LEFT, padx=5)
        self.acc_path_button = ttk.Button(path_frame, text="Configure Path", command=self.configure_paths)
        self.acc_path_button.pack(side=tk.LEFT, padx=5)

        # Status label
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT)

        # Extract files button
        extract_frame = ttk.Frame(self.frame)
        extract_frame.pack(fill=tk.X, padx=10, pady=5)
        self.extract_button = ttk.Button(extract_frame, text="Extract ACC Files", command=self.extract_acc_files)
        self.extract_button.pack(side=tk.LEFT)

    def load_projects(self):
        """Load available projects into the dropdown"""
        try:
            projects = project_service.list_projects_basic()
            project_options = [f"{p['project_id']} - {p['name']}" for p in projects]
            self.project_combo['values'] = project_options
            print(f"Loaded {len(project_options)} projects: {project_options[:3]}...")
            if not project_options:
                messagebox.showwarning("No Projects", "No projects found in database")
        except Exception as exc:
            print(f"Error loading projects: {exc}")
            messagebox.showerror("Error", f"Failed to load projects: {exc}")
            self.project_combo['values'] = []

    def show_project_dialog(self, mode="create", project_id=None):
        """Show create/edit project dialog"""

        # Create dialog window
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Project" if mode == "create" else "Edit Project Details")
        dialog.geometry("700x600")
        dialog.resizable(True, True)

        # Make dialog modal
        dialog.transient(self.frame)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")

        # Main container with scrollbar
        main_canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Content frame
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(content_frame, text="Create New Project" if mode == "create" else "Edit Project Details",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))

        # Load existing data if editing
        existing_data = {}
        if mode == "edit" and project_id:
            try:
                project_details = get_project_details(project_id)
                folder_path, ifc_folder_path = get_project_folders(project_id)
                existing_data = {
                    'name': project_details.get('project_name', ''),
                    'client_name': project_details.get('client_name', ''),
                    'status': project_details.get('status', ''),
                    'priority': project_details.get('priority', ''),
                    'start_date': project_details.get('start_date', ''),
                    'end_date': project_details.get('end_date', ''),
                    'folder_path': folder_path or '',
                    'ifc_folder_path': ifc_folder_path or ''
                }
            except Exception as e:
                print(f"Error loading project data: {e}")

        # === BASIC PROJECT INFO ===
        basic_frame = ttk.LabelFrame(content_frame, text="?? Basic Project Information", padding=15)
        basic_frame.pack(fill="x", pady=(0, 10))

        # Project Name
        ttk.Label(basic_frame, text="Project Name*:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        project_name_var = tk.StringVar(value=existing_data.get('name', ''))
        project_name_entry = ttk.Entry(basic_frame, textvariable=project_name_var, width=50)
        project_name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

        # Client Selection
        ttk.Label(basic_frame, text="Client*:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        client_var = tk.StringVar()
        client_combo = ttk.Combobox(basic_frame, textvariable=client_var, width=30, state="readonly")
        client_combo.grid(row=1, column=1, sticky="ew", pady=5)

        # Load clients
        try:
            clients = get_available_clients()
            client_names = [f"{client[0]} - {client[1]}" for client in clients]
            client_combo['values'] = client_names

            # Set existing client if editing
            if existing_data.get('client_name'):
                for client_option in client_names:
                    if existing_data['client_name'] in client_option:
                        client_var.set(client_option)
                        break
        except Exception as e:
            print(f"Error loading clients: {e}")

        # New Client Button
        ttk.Button(basic_frame, text="+ New Client",
                  command=lambda: self.show_new_client_dialog(client_combo)).grid(row=1, column=2, padx=(10, 0), pady=5)

        # Project Type
        ttk.Label(basic_frame, text="Project Type:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=5)
        project_type_var = tk.StringVar()
        project_type_combo = ttk.Combobox(basic_frame, textvariable=project_type_var, width=30)
        project_type_combo.grid(row=2, column=1, sticky="ew", pady=5)
        project_type_combo['values'] = ["Solar PV", "Wind Farm", "Battery Storage", "Hybrid Project", "Transmission", "Other"]

        # Area/Size
        ttk.Label(basic_frame, text="Area (hectares):").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=5)
        area_var = tk.StringVar()
        area_entry = ttk.Entry(basic_frame, textvariable=area_var, width=20)
        area_entry.grid(row=3, column=1, sticky="w", pady=5)

        # MW Capacity
        ttk.Label(basic_frame, text="MW Capacity:").grid(row=3, column=2, sticky="w", padx=(20, 10), pady=5)
        mw_var = tk.StringVar()
        mw_entry = ttk.Entry(basic_frame, textvariable=mw_var, width=20)
        mw_entry.grid(row=3, column=3, sticky="w", pady=5)

        basic_frame.columnconfigure(1, weight=1)

        # === PROJECT STATUS ===
        status_frame = ttk.LabelFrame(content_frame, text="?? Project Status & Timeline", padding=15)
        status_frame.pack(fill="x", pady=(0, 10))

        # Status
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        status_var = tk.StringVar(value=existing_data.get('status', 'Planning'))
        status_combo = ttk.Combobox(status_frame, textvariable=status_var, width=20)
        status_combo.grid(row=0, column=1, sticky="w", pady=5)
        status_combo['values'] = ["Planning", "Design", "Construction", "Commissioning", "Operational", "Completed", "On Hold", "Cancelled"]

        # Priority
        ttk.Label(status_frame, text="Priority:").grid(row=0, column=2, sticky="w", padx=(20, 10), pady=5)
        priority_var = tk.StringVar(value=existing_data.get('priority', 'Medium'))
        priority_combo = ttk.Combobox(status_frame, textvariable=priority_var, width=15)
        priority_combo.grid(row=0, column=3, sticky="w", pady=5)
        priority_combo['values'] = ["Low", "Medium", "High", "Critical"]

        # Start Date
        ttk.Label(status_frame, text="Start Date:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        start_date_var = tk.StringVar(value=existing_data.get('start_date', ''))
        start_date_entry = DateEntry(status_frame, textvariable=start_date_var, width=15, date_pattern='yyyy-mm-dd')
        start_date_entry.grid(row=1, column=1, sticky="w", pady=5)

        # End Date
        ttk.Label(status_frame, text="End Date:").grid(row=1, column=2, sticky="w", padx=(20, 10), pady=5)
        end_date_var = tk.StringVar(value=existing_data.get('end_date', ''))
        end_date_entry = DateEntry(status_frame, textvariable=end_date_var, width=15, date_pattern='yyyy-mm-dd')
        end_date_entry.grid(row=1, column=3, sticky="w", pady=5)

        # === LOCATION INFORMATION ===
        location_frame = ttk.LabelFrame(content_frame, text="?? Location Information", padding=15)
        location_frame.pack(fill="x", pady=(0, 10))

        # Address
        ttk.Label(location_frame, text="Address:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        address_var = tk.StringVar()
        address_entry = ttk.Entry(location_frame, textvariable=address_var, width=50)
        address_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)

        # City, State, Postcode
        ttk.Label(location_frame, text="City:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        city_var = tk.StringVar()
        city_entry = ttk.Entry(location_frame, textvariable=city_var, width=20)
        city_entry.grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(location_frame, text="State:").grid(row=1, column=2, sticky="w", padx=(20, 10), pady=5)
        state_var = tk.StringVar()
        state_entry = ttk.Entry(location_frame, textvariable=state_var, width=10)
        state_entry.grid(row=1, column=3, sticky="w", pady=5)

        ttk.Label(location_frame, text="Postcode:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=5)
        postcode_var = tk.StringVar()
        postcode_entry = ttk.Entry(location_frame, textvariable=postcode_var, width=15)
        postcode_entry.grid(row=2, column=1, sticky="w", pady=5)

        location_frame.columnconfigure(1, weight=1)

        # === FILE PATHS ===
        paths_frame = ttk.LabelFrame(content_frame, text="?? File Paths", padding=15)
        paths_frame.pack(fill="x", pady=(0, 10))

        # Model Folder Path
        ttk.Label(paths_frame, text="Model Folder:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        folder_path_var = tk.StringVar(value=existing_data.get('folder_path', ''))
        folder_path_entry = ttk.Entry(paths_frame, textvariable=folder_path_var, width=50)
        folder_path_entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(paths_frame, text="Browse",
                  command=lambda: self.browse_folder(folder_path_var)).grid(row=0, column=2, padx=(5, 0), pady=5)

        # IFC Folder Path
        ttk.Label(paths_frame, text="IFC Folder:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        ifc_path_var = tk.StringVar(value=existing_data.get('ifc_folder_path', ''))
        ifc_path_entry = ttk.Entry(paths_frame, textvariable=ifc_path_var, width=50)
        ifc_path_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(paths_frame, text="Browse",
                  command=lambda: self.browse_folder(ifc_path_var)).grid(row=1, column=2, padx=(5, 0), pady=5)

        paths_frame.columnconfigure(1, weight=1)

        # === BUTTONS ===
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        def save_project():
            """Save the project data"""
            try:
                # Validate required fields
                if not project_name_var.get().strip():
                    messagebox.showerror("Error", "Project name is required")
                    return

                if not client_var.get():
                    messagebox.showerror("Error", "Please select a client")
                    return

                # Prepare project data
                client_id = client_var.get().split(" - ")[0] if client_var.get() else None

                project_data = {
                    'name': project_name_var.get().strip(),
                    'client_id': client_id,
                    'project_type': project_type_var.get(),
                    'area': area_var.get(),
                    'mw_capacity': mw_var.get(),
                    'status': status_var.get(),
                    'priority': priority_var.get(),
                    'start_date': start_date_var.get(),
                    'end_date': end_date_var.get(),
                    'address': address_var.get(),
                    'city': city_var.get(),
                    'state': state_var.get(),
                    'postcode': postcode_var.get(),
                    'folder_path': folder_path_var.get(),
                    'ifc_folder_path': ifc_path_var.get()
                }

                if mode == "create":
                    success = self.create_project_in_db(project_data)
                    if success:
                        messagebox.showinfo("Success", "Project created successfully!")
                        dialog.destroy()
                        self.refresh_data()
                        # Notify all tabs that the project list has changed
                        project_notification_system.notify_project_list_changed()
                else:
                    success = self.update_project_in_db(project_id, project_data)
                    if success:
                        messagebox.showinfo("Success", "Project updated successfully!")
                        dialog.destroy()
                        self.refresh_data()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")

        # Buttons
        ttk.Button(button_frame, text="Save", command=save_project).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

        # Focus on project name field
        project_name_entry.focus()
        
    def show_new_client_dialog(self, client_combo=None):
        """Show dialog to create a new client"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Client")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(content_frame, text="Create New Client", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Form fields
        fields_frame = ttk.Frame(content_frame)
        fields_frame.pack(fill="both", expand=True)
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Client variables
        client_vars = {}
        
        # Client Name
        ttk.Label(fields_frame, text="Client Name*:").grid(row=0, column=0, sticky="w", pady=5)
        client_vars['name'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['name'], width=40).grid(row=0, column=1, sticky="ew", pady=5)
        
        # Contact Name
        ttk.Label(fields_frame, text="Contact Name:").grid(row=1, column=0, sticky="w", pady=5)
        client_vars['contact'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['contact'], width=40).grid(row=1, column=1, sticky="ew", pady=5)
        
        # Contact Email
        ttk.Label(fields_frame, text="Contact Email:").grid(row=2, column=0, sticky="w", pady=5)
        client_vars['email'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['email'], width=40).grid(row=2, column=1, sticky="ew", pady=5)
        
        # Contact Phone
        ttk.Label(fields_frame, text="Contact Phone:").grid(row=3, column=0, sticky="w", pady=5)
        client_vars['phone'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['phone'], width=40).grid(row=3, column=1, sticky="ew", pady=5)
        
        # Address
        ttk.Label(fields_frame, text="Address:").grid(row=4, column=0, sticky="w", pady=5)
        client_vars['address'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['address'], width=40).grid(row=4, column=1, sticky="ew", pady=5)
        
        # City
        ttk.Label(fields_frame, text="City:").grid(row=5, column=0, sticky="w", pady=5)
        client_vars['city'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['city'], width=40).grid(row=5, column=1, sticky="ew", pady=5)
        
        # State
        ttk.Label(fields_frame, text="State:").grid(row=6, column=0, sticky="w", pady=5)
        client_vars['state'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['state'], width=40).grid(row=6, column=1, sticky="ew", pady=5)
        
        # Postcode
        ttk.Label(fields_frame, text="Postcode:").grid(row=7, column=0, sticky="w", pady=5)
        client_vars['postcode'] = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=client_vars['postcode'], width=40).grid(row=7, column=1, sticky="ew", pady=5)
        
        def save_client():
            """Save the new client to database"""
            try:
                from database import create_new_client
                
                client_data = {
                    'client_name': client_vars['name'].get().strip(),
                    'contact_name': client_vars['contact'].get().strip(),
                    'contact_email': client_vars['email'].get().strip(),
                    'contact_phone': client_vars['phone'].get().strip(),
                    'address': client_vars['address'].get().strip(),
                    'city': client_vars['city'].get().strip(),
                    'state': client_vars['state'].get().strip(),
                    'postcode': client_vars['postcode'].get().strip(),
                    'country': 'Australia',  # Default country
                }
                
                if not client_data['client_name']:
                    messagebox.showerror("Error", "Client name is required")
                    return
                
                client_id = create_new_client(client_data)
                
                if client_id:
                    messagebox.showinfo("Success", f"Client created successfully! (ID: {client_id})")
                    # Refresh client combo box
                    clients = get_available_clients()
                    client_names = [f"{client[0]} - {client[1]}" for client in clients]
                    client_combo['values'] = client_names
                    # Select the new client
                    new_client_name = client_vars['name'].get().strip()
                    for client_option in client_names:
                        if new_client_name in client_option:
                            client_combo.set(client_option)
                            break
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to create client - check database connection")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create client: {str(e)}")
                print(f"Client creation error: {e}")  # For debugging
        
        # Buttons frame with better spacing
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Create buttons with better styling
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=5)
        
        save_btn = ttk.Button(button_frame, text="Save Client", command=save_client)
        save_btn.pack(side="right", padx=5)
        
        # Focus on client name field
        client_vars['name'].set("")
        dialog.after(100, lambda: dialog.focus_set())
    
    def create_project_in_db(self, project_data):
        """Create a new project in the database with all collected fields"""
        try:
            project_service.create_project(project_data)
            return True
        except ProjectValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except ProjectServiceError as exc:
            messagebox.showerror("Error", f"Failed to create project: {exc}")
            logger.exception("Project creation error via service layer")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to create project: {exc}")
            logger.exception("Unexpected project creation error")
        return False

    def refresh_data(self):
        """Refresh project data by reloading the project list"""
        self.load_projects()

class _DocumentTypeTab:
    """Standalone tab that presents the four-pillar UI for a single document type (BEP/EIR/PIR)."""
    def __init__(self, parent_notebook, doc_type: str, tab_label: str = None):
        self.doc_type = doc_type
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text=tab_label or doc_type)
        self.current_project = None
        self.current_project_id = None
        self.current_project_document_id = None

        # Build four-pillar UI
        self._build_ui(self.frame)

        # Register for project change notifications
        project_notification_system.register_observer(self)

    def _build_ui(self, parent):
        # This is a placeholder - the actual implementation would be complex
        # For now, just create a simple frame with a label
        ttk.Label(parent, text=f"{self.doc_type} Document Management").pack(pady=20)


class BEPDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="BEP", tab_label="BEP")


class EIRDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="EIR", tab_label="EIR")


class PIRDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="PIR", tab_label="PIR")


class DocumentManagementTab:
    """Document Management Interface - For managing BEP, PIR, and EIR documents"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📁 Documents")
        
        # Initialize project tracking
        self.current_project = None
        
        # Main container with scrollable content
        
    def create_project_in_db(self, project_data):
        """Create a new project in the database with all collected fields"""
        try:
            project_service.create_project(project_data)
            print(f"✅ Successfully created project: {project_data['name']}")
            return True
        except ProjectValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except ProjectServiceError as exc:
            print(f"❌ Failed to create project: {project_data['name']}: {exc}")
            messagebox.showerror("Database Error", f"Failed to create project: {exc}")
        except Exception as exc:
            print(f"❌ Error creating project: {exc}")
            messagebox.showerror("Database Error", f"Failed to create project: {exc}")
        return False
    
    def update_project_in_db(self, project_id, project_data):
        """Update an existing project in the database"""
        try:
            project_service.update_project(project_id, project_data)
            print(f"✅ Successfully updated project {project_id}")
            return True
        except ProjectValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except ProjectServiceError as exc:
            print(f"❌ Error updating project {project_id}: {exc}")
            messagebox.showerror("Database Error", f"Failed to update project: {exc}")
        except Exception as exc:
            print(f"❌ Unexpected error updating project {project_id}: {exc}")
            messagebox.showerror("Database Error", f"Failed to update project: {exc}")
        return False
    
    def configure_paths(self):
        """Configure model and IFC file paths for the selected project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        try:
            # Get current project ID and data
            project_text = self.project_var.get()
            project_id = int(project_text.split(" - ")[0])
            
            # Get current project details
            project_data = get_project_details(project_id)
            if not project_data:
                messagebox.showerror("Error", "Could not load project details")
                return
            
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Configure File Paths")
            dialog.geometry("700x500")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Make dialog resizable
            dialog.rowconfigure(0, weight=1)
            dialog.columnconfigure(0, weight=1)
            
            # Main content frame
            content_frame = ttk.Frame(dialog, padding=20)
            content_frame.pack(fill="both", expand=True)
            content_frame.rowconfigure(6, weight=1)  # Make the preview area expandable
            content_frame.columnconfigure(1, weight=1)
            
            # Title
            title_label = ttk.Label(content_frame, text="?? Configure File Paths", 
                                   font=("Arial", 14, "bold"))
            title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
            
            # Project info
            project_info = ttk.Label(content_frame, 
                                   text=f"Project: {project_data.get('project_name', 'Unknown')} (ID: {project_id})",
                                   font=("Arial", 10))
            project_info.grid(row=1, column=0, columnspan=3, pady=(0, 15), sticky="w")
            
            # Model Folder Path
            ttk.Label(content_frame, text="Model Folder Path:", 
                     font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
            
            model_path_var = tk.StringVar(value=project_data.get('folder_path', ''))
            model_path_entry = ttk.Entry(content_frame, textvariable=model_path_var, width=60)
            model_path_entry.grid(row=2, column=1, sticky="ew", padx=(10, 5), pady=5)
            
            def browse_model_path():
                folder_path = filedialog.askdirectory(
                    title="Select Model Folder Path",
                    initialdir=model_path_var.get() if model_path_var.get() else "/"
                )
                if folder_path:
                    model_path_var.set(folder_path)
            
            ttk.Button(content_frame, text="?? Browse", 
                      command=browse_model_path).grid(row=2, column=2, padx=(0, 0), pady=5)
            
            # IFC Folder Path
            ttk.Label(content_frame, text="IFC Folder Path:", 
                     font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
            
            ifc_path_var = tk.StringVar(value=project_data.get('ifc_folder_path', ''))
            ifc_path_entry = ttk.Entry(content_frame, textvariable=ifc_path_var, width=60)
            ifc_path_entry.grid(row=3, column=1, sticky="ew", padx=(10, 5), pady=5)
            
            def browse_ifc_path():
                folder_path = filedialog.askdirectory(
                    title="Select IFC Folder Path",
                    initialdir=ifc_path_var.get() if ifc_path_var.get() else "/"
                )
                if folder_path:
                    ifc_path_var.set(folder_path)
            
            ttk.Button(content_frame, text="?? Browse", 
                      command=browse_ifc_path).grid(row=3, column=2, padx=(0, 0), pady=5)
            
            # Path validation info
            validation_frame = ttk.LabelFrame(content_frame, text="Path Validation", padding=10)
            validation_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=15)
            
            model_status_var = tk.StringVar()
            ifc_status_var = tk.StringVar()
            
            ttk.Label(validation_frame, text="Model Path:").grid(row=0, column=0, sticky="w")
            model_status_label = ttk.Label(validation_frame, textvariable=model_status_var)
            model_status_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
            
            ttk.Label(validation_frame, text="IFC Path:").grid(row=1, column=0, sticky="w")
            ifc_status_label = ttk.Label(validation_frame, textvariable=ifc_status_var)
            ifc_status_label.grid(row=1, column=1, sticky="w", padx=(10, 0))
            
            def validate_paths():
                """Validate the entered paths"""
                # Validate model path
                model_path = model_path_var.get().strip()
                if not model_path:
                    model_status_var.set("? Path not set")
                elif not os.path.exists(model_path):
                    model_status_var.set("? Path does not exist")
                elif not os.path.isdir(model_path):
                    model_status_var.set("? Not a directory")
                else:
                    model_status_var.set("? Valid path")
                
                # Validate IFC path
                ifc_path = ifc_path_var.get().strip()
                if not ifc_path:
                    ifc_status_var.set("?? Path not set (optional)")
                elif not os.path.exists(ifc_path):
                    ifc_status_var.set("? Path does not exist")
                elif not os.path.isdir(ifc_path):
                    ifc_status_var.set("? Not a directory")
                else:
                    ifc_status_var.set("? Valid path")
            
            # Validate paths initially and on changes
            def on_path_change(*args):
                dialog.after_idle(validate_paths)
            
            model_path_var.trace_add('write', on_path_change)
            ifc_path_var.trace_add('write', on_path_change)
            validate_paths()  # Initial validation
            
            # Validate button
            ttk.Button(validation_frame, text="?? Validate Paths", 
                      command=validate_paths).grid(row=0, column=2, rowspan=2, padx=(20, 0))
            
            # Notes section
            notes_frame = ttk.LabelFrame(content_frame, text="Notes & Guidelines", padding=10)
            notes_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 15))
            
            notes_text = (
                "• Model Folder Path: Main project folder containing ACC documents and models\n"
                "• IFC Folder Path: Specific folder for IFC files (optional, can be within model folder)\n"
                "• Paths should be accessible and contain the relevant project files\n"
                "• Use network paths (UNC) for shared project folders\n"
                "• Ensure proper permissions for read/write access"
            )
            
            notes_label = ttk.Label(notes_frame, text=notes_text, justify="left", 
                                   font=("Arial", 9), foreground="gray")
            notes_label.pack(anchor="w")
            
            # Preview section
            preview_frame = ttk.LabelFrame(content_frame, text="Folder Contents Preview", padding=10)
            preview_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(0, 15))
            
            preview_text = tk.Text(preview_frame, height=8, wrap="none", font=("Consolas", 9))
            preview_scrollbar_y = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
            preview_scrollbar_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=preview_text.xview)
            preview_text.configure(yscrollcommand=preview_scrollbar_y.set, xscrollcommand=preview_scrollbar_x.set)
            
            preview_text.grid(row=0, column=0, sticky="nsew")
            preview_scrollbar_y.grid(row=0, column=1, sticky="ns")
            preview_scrollbar_x.grid(row=1, column=0, sticky="ew")
            
            preview_frame.rowconfigure(0, weight=1)
            preview_frame.columnconfigure(0, weight=1)
            
            def update_preview():
                """Update the folder contents preview"""
                preview_text.delete(1.0, tk.END)
                
                model_path = model_path_var.get().strip()
                if model_path and os.path.exists(model_path) and os.path.isdir(model_path):
                    try:
                        preview_text.insert(tk.END, f"?? Model Folder Contents: {model_path}\n")
                        preview_text.insert(tk.END, "="*60 + "\n\n")
                        
                        items = os.listdir(model_path)
                        if items:
                            folders = [item for item in items if os.path.isdir(os.path.join(model_path, item))]
                            files = [item for item in items if os.path.isfile(os.path.join(model_path, item))]
                            
                            if folders:
                                preview_text.insert(tk.END, "?? Folders:\n")
                                for folder in sorted(folders):
                                    preview_text.insert(tk.END, f"  ?? {folder}\n")
                                preview_text.insert(tk.END, "\n")
                            
                            if files:
                                preview_text.insert(tk.END, "?? Files:\n")
                                for file in sorted(files):
                                    preview_text.insert(tk.END, f"  ?? {file}\n")
                        else:
                            preview_text.insert(tk.END, "Empty folder")
                            
                    except Exception as e:
                        preview_text.insert(tk.END, f"Error reading folder: {str(e)}")
                else:
                    preview_text.insert(tk.END, "No valid model path selected for preview")
            
            ttk.Button(preview_frame, text="?? Refresh Preview", 
                      command=update_preview).grid(row=2, column=0, pady=(5, 0), sticky="w")
            
            # Initial preview
            update_preview()
            
            # Result variable
            result = {"saved": False}
            
            # Buttons frame
            buttons_frame = ttk.Frame(content_frame)
            buttons_frame.grid(row=7, column=0, columnspan=3, pady=(15, 0), sticky="ew")
            
            def save_paths():
                """Save the configured paths"""
                model_path = model_path_var.get().strip()
                ifc_path = ifc_path_var.get().strip()
                
                # Validate model path is set
                if not model_path:
                    messagebox.showerror("Validation Error", "Model Folder Path is required")
                    return
                
                # Validate model path exists
                if not os.path.exists(model_path):
                    if not messagebox.askyesno("Path Warning", 
                        f"Model folder path does not exist:\n{model_path}\n\nDo you want to save anyway?"):
                        return
                
                # Validate IFC path if provided
                if ifc_path and not os.path.exists(ifc_path):
                    if not messagebox.askyesno("Path Warning", 
                        f"IFC folder path does not exist:\n{ifc_path}\n\nDo you want to save anyway?"):
                        return
                
                try:
                    # Save to database using update_project_folders function
                    success = update_project_folders(
                        project_id=project_id,
                        models_path=model_path,
                        ifc_path=ifc_path if ifc_path else None
                    )
                    
                    if success:
                        messagebox.showinfo("Success", "File paths saved successfully!")
                        result["saved"] = True
                        dialog.destroy()
                        
                        # Refresh the project data in the main UI
                        self.refresh_data()
                    else:
                        messagebox.showerror("Error", "Failed to save file paths")
                        
                except Exception as e:
                    print(f"? Error saving paths: {e}")
                    messagebox.showerror("Error", f"Failed to save paths: {str(e)}")
            
            def cancel():
                dialog.destroy()
            
            # Save and Cancel buttons
            ttk.Button(buttons_frame, text="?? Save Paths", command=save_paths, 
                      style="Accent.TButton").pack(side="left", padx=(0, 10))
            ttk.Button(buttons_frame, text="? Cancel", command=cancel).pack(side="left")
            
            # Focus on model path entry
            model_path_entry.focus()
            
        except Exception as e:
            print(f"? Error opening configure paths dialog: {e}")
            messagebox.showerror("Error", f"Failed to open configure paths dialog: {str(e)}")
    
    def extract_acc_files(self):
        """Extract files from ACC Desktop Connector"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        try:
            # Get current project ID
            project_text = self.project_var.get()
            project_id = int(project_text.split(" - ")[0])
            
            # Get project folder path using the same method as app.py
            folder_path, ifc_path = get_project_folders(project_id)
            if not folder_path:
                messagebox.showerror("Error", 
                    "No folder path configured for this project.\n"
                    "Please use 'Configure File Paths' to set the ACC folder location.")
                return
                
            if not os.path.exists(folder_path):
                messagebox.showerror("Error", 
                    f"ACC folder path does not exist:\n{folder_path}\n\n"
                    "Please verify the path or use 'Configure File Paths' to update it.")
                return
            
            # Get project details for display purposes
            project_data = get_project_details(project_id)
            project_name = project_data.get('project_name', 'Unknown') if project_data else 'Unknown'
            
            # Confirm extraction
            if not messagebox.askyesno("Extract Files", 
                f"Extract files from ACC Desktop Connector?\n\n"
                f"Project: {project_name}\n"
                f"Folder: {folder_path}\n\n"
                f"This will scan the folder and update the project database."):
                return
            
            # Import the database function
            from handlers.database import insert_files_into_tblACCDocs
            
            # Show progress dialog
            progress_dialog = tk.Toplevel(self.frame)
            progress_dialog.title("Extracting Files")
            progress_dialog.geometry("400x150")
            progress_dialog.transient(self.frame.winfo_toplevel())
            progress_dialog.grab_set()
            
            progress_frame = ttk.Frame(progress_dialog, padding=20)
            progress_frame.pack(fill="both", expand=True)
            
            ttk.Label(progress_frame, text="Extracting files from ACC Desktop Connector...", 
                     font=("Arial", 10, "bold")).pack(pady=(0, 10))
            
            progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=300)
            progress_bar.pack(pady=(0, 10))
            progress_bar.start()
            
            status_label = ttk.Label(progress_frame, text="Processing...")
            status_label.pack()
            
            # Update the UI
            progress_dialog.update()
            
            try:
                # Perform the extraction
                result = insert_files_into_tblACCDocs(project_id, folder_path)
                
                progress_bar.stop()
                progress_dialog.destroy()
                
                if result:
                    messagebox.showinfo("Success", 
                        f"Files extracted successfully from ACC Desktop Connector!\n\n"
                        f"Project: {project_name}\n"
                        f"Database updated with file information.")
                    
                    # Refresh the project data
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", 
                        "File extraction failed. Please check the folder path and try again.")
                        
            except Exception as e:
                progress_bar.stop()
                progress_dialog.destroy()
                raise e
                
        except Exception as e:
            print(f"? Error during file extraction: {e}")
            messagebox.showerror("Error", f"File extraction failed: {str(e)}")
    
    def view_dashboard(self):
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Feature", "Project Dashboard will be implemented")
    
    def archive_project(self):
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        result = messagebox.askyesno("Confirm", "Are you sure you want to archive this project?")
        if result:
            messagebox.showinfo("Feature", "Project archiving will be implemented")
    
    def on_project_selected(self, event=None):
        """Handle project selection from dropdown"""
        project_selection = self.project_var.get()
        if project_selection:
            # Parse project name from "ID - Name" format
            if " - " in project_selection:
                project_id_str, project_name = project_selection.split(" - ", 1)
                try:
                    project_id = int(project_id_str)
                except ValueError:
                    project_id = None
            else:
                project_name = project_selection
                project_id = None

            # Update status labels
            self.update_project_status(project_name)
            # Update folder path display
            if project_id is not None:
                from database import get_acc_folder_path
                folder_path = get_acc_folder_path(project_id)
                self.folder_path_var.set(folder_path if folder_path else "")
            # Notify other tabs with the full selection string
            project_notification_system.notify_project_changed(project_selection)
    
    def load_scope(self):
        """Load scope data for the current project"""
        try:
            # Clear existing scope data
            for item in self.scope_tree.get_children():
                self.scope_tree.delete(item)
            
            if not self.current_project_id:
                return
            
            # For now, add placeholder data
            # TODO: Implement actual scope loading from database
            print("Loading scope data...")
            
        except Exception as e:
            print(f"Error loading scope: {e}")
    
    def load_schedule(self):
        """Load schedule data for the current project"""
        try:
            # Clear existing schedule data
            for item in self.schedule_tree.get_children():
                self.schedule_tree.delete(item)
            
            if not self.current_project_id:
                return
            
            # For now, add placeholder data
            # TODO: Implement actual schedule loading from database
            print("Loading schedule data...")
            
        except Exception as e:
            print(f"Error loading schedule: {e}")
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected_local()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()


class DocumentManagementTab:
    """Document Management Interface - For managing BEP, PIR, and EIR documents"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📁 Documents")
        
        # Initialize project tracking
        self.current_project = None
        
        # Main container with scrollable content
        self.setup_ui()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Create main container
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Project status frame
        project_frame = ttk.LabelFrame(main_container, text="📊 Current Project", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.project_label = ttk.Label(project_frame, text="No project selected", 
                                     font=('Arial', 10, 'bold'))
        self.project_label.pack()
        
        # Create notebook for document types
        self.doc_notebook = ttk.Notebook(main_container)
        self.doc_notebook.pack(fill=tk.BOTH, expand=True)
        
        # BEP Tab
        self.bep_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.bep_frame, text="🏗 BEP (BIM Execution Plan)")
        self.setup_bep_tab()
        
        # PIR Tab
        self.pir_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.pir_frame, text="📋 PIR (Project Information Requirements)")
        self.setup_pir_tab()
        
        # EIR Tab
        self.eir_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.eir_frame, text="📄 EIR (Employer Information Requirements)")
        self.setup_eir_tab()
    
    def setup_bep_tab(self):
        """Setup the BEP tab"""
        # Content for BEP tab
        content_frame = ttk.LabelFrame(self.bep_frame, text="BEP Document Management", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder content
        ttk.Label(content_frame, text="BEP document management will be implemented here").pack(pady=20)
    
    def setup_pir_tab(self):
        """Setup the PIR tab"""
        # Content for PIR tab
        content_frame = ttk.LabelFrame(self.pir_frame, text="PIR Document Management", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder content
        ttk.Label(content_frame, text="PIR document management will be implemented here").pack(pady=20)
    
    def setup_eir_tab(self):
        """Setup the EIR tab"""
        # Content for EIR tab
        content_frame = ttk.LabelFrame(self.eir_frame, text="EIR Document Management", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder content
        ttk.Label(content_frame, text="EIR document management will be implemented here").pack(pady=20)
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        self.current_project = new_project
        if new_project:
            self.project_label.config(text=f"Project: {new_project}")
        else:
            self.project_label.config(text="No project selected")
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        # DocumentManagementTab doesn't have project selection, but implement for completeness
        pass


class ProjectBookmarksTab:
    """Project Bookmarks Management Interface"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="🔗 Project Bookmarks")
        
        self.current_project_id = None
        self.bookmarks_tree = None
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Setup the bookmarks management interface"""
        # Main container
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Project Selection
        project_frame = ttk.LabelFrame(main_frame, text="Project Selection", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(project_frame, text="Select Project:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50, state="readonly")
        self.project_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
        
        project_frame.columnconfigure(1, weight=1)
        
        # Bookmarks Management
        bookmarks_frame = ttk.LabelFrame(main_frame, text="Project Bookmarks", padding=10)
        bookmarks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Search and Filter Frame
        search_frame = ttk.LabelFrame(bookmarks_frame, text="Search & Filter", padding=5)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search row
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(search_row, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Label(search_row, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter_var = tk.StringVar(value="All")
        self.category_filter_combo = ttk.Combobox(search_row, textvariable=self.category_filter_var, 
                                                 width=15, state="readonly")
        self.category_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.category_filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        ttk.Label(search_row, text="Tags:").pack(side=tk.LEFT, padx=(0, 5))
        self.tags_filter_var = tk.StringVar(value="All")
        self.tags_filter_combo = ttk.Combobox(search_row, textvariable=self.tags_filter_var, 
                                             width=15, state="readonly")
        self.tags_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.tags_filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        ttk.Label(search_row, text="Sort by:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="Name")
        self.sort_combo = ttk.Combobox(search_row, textvariable=self.sort_var, 
                                      values=["Name", "Category", "Created", "URL"], 
                                      width=10, state="readonly")
        self.sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.sort_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Clear filters button
        ttk.Button(search_row, text="Clear Filters", command=self.clear_filters).pack(side=tk.RIGHT)
        
        # Toolbar
        toolbar_frame = ttk.Frame(bookmarks_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="Add Bookmark", command=self.add_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Templates", command=self.show_templates).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Edit Bookmark", command=self.edit_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Delete Bookmark", command=self.delete_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Open in Browser", command=self.open_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Duplicate", command=self.duplicate_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Import", command=self.import_bookmarks).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Export", command=self.export_bookmarks).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Check Links", command=self.check_links).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="View Notes", command=self.view_notes).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Refresh", command=self.refresh_bookmarks).pack(side=tk.RIGHT, padx=5)
        
        # Bookmarks Treeview
        columns = ("Name", "URL", "Description", "Category", "Tags", "Created")
        self.bookmarks_tree = ttk.Treeview(bookmarks_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.bookmarks_tree.heading("Name", text="Name")
        self.bookmarks_tree.column("Name", width=150)
        
        self.bookmarks_tree.heading("URL", text="URL")
        self.bookmarks_tree.column("URL", width=250)
        
        self.bookmarks_tree.heading("Description", text="Description")
        self.bookmarks_tree.column("Description", width=200)
        
        self.bookmarks_tree.heading("Category", text="Category")
        self.bookmarks_tree.column("Category", width=100)
        
        self.bookmarks_tree.heading("Tags", text="Tags")
        self.bookmarks_tree.column("Tags", width=120)
        
        self.bookmarks_tree.heading("Created", text="Created")
        self.bookmarks_tree.column("Created", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(bookmarks_frame, orient=tk.VERTICAL, command=self.bookmarks_tree.yview)
        h_scrollbar = ttk.Scrollbar(bookmarks_frame, orient=tk.HORIZONTAL, command=self.bookmarks_tree.xview)
        self.bookmarks_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.bookmarks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to open bookmark
        self.bookmarks_tree.bind("<Double-1>", lambda e: self.open_bookmark())
        
        # Quick Access Panel
        self.quick_access_expanded = False
        quick_access_frame = ttk.LabelFrame(main_frame, text="Quick Access (Click to Expand)", padding=5)
        quick_access_frame.pack(fill=tk.X, pady=(10, 0))
        quick_access_frame.bind("<Button-1>", self.toggle_quick_access)
        
        self.quick_access_content = ttk.Frame(quick_access_frame)
        # Don't pack initially - will be packed when expanded
        
        # Quick access buttons will be added here when expanded
        self.quick_access_buttons_frame = ttk.Frame(self.quick_access_content)
        self.quick_access_label = ttk.Label(self.quick_access_content, text="No frequently used bookmarks yet.\nAdd bookmarks and use them to populate this panel.")
        self.quick_access_label.pack(pady=20)
    
    def refresh_data(self):
        """Refresh project list"""
        projects = get_projects()
        project_options = [f"{p[0]} - {p[1]}" for p in projects]
        self.project_combo['values'] = project_options
        
        # Auto-select if only one project
        if len(project_options) == 1:
            self.project_var.set(project_options[0])
            self.on_project_selected()
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        selection = self.project_var.get()
        if selection:
            try:
                self.current_project_id = int(selection.split(' - ')[0])
                self.refresh_bookmarks()
            except (ValueError, IndexError):
                self.current_project_id = None
        else:
            self.current_project_id = None
        
        # Notify other tabs
        project_notification_system.notify_project_changed(selection)
    
    def refresh_bookmarks(self):
        """Refresh the bookmarks list with search and filter applied"""
        if not self.current_project_id or not self.bookmarks_tree:
            return
        
        # Clear existing items
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)
        
        # Get all bookmarks
        all_bookmarks = get_project_bookmarks(self.current_project_id)
        
        # Apply search filter
        search_term = self.search_var.get().strip().lower()
        if search_term:
            all_bookmarks = [
                b for b in all_bookmarks 
                if search_term in b['name'].lower() or 
                   search_term in (b['url'] or '').lower() or 
                   search_term in (b['description'] or '').lower() or
                   search_term in (b['tags'] or '').lower()
            ]
        
        # Apply category filter
        category_filter = self.category_filter_var.get()
        if category_filter != "All":
            all_bookmarks = [b for b in all_bookmarks if b['category'] == category_filter]
        
        # Apply tags filter
        tags_filter = self.tags_filter_var.get()
        if tags_filter != "All":
            all_bookmarks = [
                b for b in all_bookmarks 
                if b['tags'] and tags_filter in b['tags']
            ]
        
        # Apply sorting
        sort_by = self.sort_var.get()
        if sort_by == "Name":
            all_bookmarks.sort(key=lambda x: x['name'].lower())
        elif sort_by == "Category":
            all_bookmarks.sort(key=lambda x: (x['category'] or '', x['name'].lower()))
        elif sort_by == "Created":
            all_bookmarks.sort(key=lambda x: x['created_at'] or '', reverse=True)
        elif sort_by == "URL":
            all_bookmarks.sort(key=lambda x: x['url'].lower())
        
        # Update category filter dropdown with available categories
        categories = list(set(b['category'] for b in all_bookmarks if b['category']))
        categories.sort()
        self.category_filter_combo['values'] = ["All"] + categories
        
        # Update tags filter dropdown with available tags
        all_tags = []
        for b in all_bookmarks:
            if b['tags']:
                all_tags.extend([tag.strip() for tag in b['tags'].split(',') if tag.strip()])
        unique_tags = list(set(all_tags))
        unique_tags.sort()
        self.tags_filter_combo['values'] = ["All"] + unique_tags
        
        # Group by category and display
        categories_dict = {}
        for bookmark in all_bookmarks:
            category = bookmark['category'] or 'Uncategorized'
            if category not in categories_dict:
                categories_dict[category] = []
            categories_dict[category].append(bookmark)
        
        # Add to treeview
        for category, category_bookmarks in categories_dict.items():
            # Add category as parent
            category_item = self.bookmarks_tree.insert("", tk.END, text=category, values=("", "", "", category, ""))
            
            # Add bookmarks under category
            for bookmark in category_bookmarks:
                # Format created_at date
                created_at_str = ''
                if bookmark['created_at']:
                    if isinstance(bookmark['created_at'], str):
                        created_at_str = bookmark['created_at'][:10]
                    else:
                        # Handle datetime object
                        created_at_str = bookmark['created_at'].strftime('%Y-%m-%d')
                
                self.bookmarks_tree.insert(
                    category_item, tk.END,
                    values=(
                        bookmark['name'],
                        bookmark['url'],
                        bookmark['description'] or '',
                        bookmark['category'],
                        bookmark['tags'] or '',
                        created_at_str
                ),
                tags=(str(bookmark['id']),)
                )
        
        # Refresh quick access panel if expanded
        if self.quick_access_expanded:
            self.refresh_quick_access()
    
    def add_bookmark(self):
        """Add a new bookmark"""
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Please select a project first.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Bookmark")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=50)
        name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="URL:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Category:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        category_var = tk.StringVar(value="General")
        category_combo = ttk.Combobox(dialog, textvariable=category_var, width=47)
        category_combo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Get existing categories
        categories = get_bookmark_categories(self.current_project_id)
        if categories:
            category_combo['values'] = categories
        
        ttk.Label(dialog, text="Tags:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        tags_entry = ttk.Entry(dialog, width=50)
        tags_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        tags_entry.insert(0, "BIM, Documentation")  # Default suggestion
        
        ttk.Label(dialog, text="Description:").grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, height=5, width=40)
        desc_text.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        dialog.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        def save_bookmark():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get().strip() or "General"
            tags = tags_entry.get().strip()
            description = desc_text.get(1.0, tk.END).strip()
            
            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required.")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            success = add_bookmark(self.current_project_id, name, url, description, category, tags)
            if success:
                messagebox.showinfo("Success", "Bookmark added successfully.")
                dialog.destroy()
                self.refresh_bookmarks()
            else:
                messagebox.showerror("Error", "Failed to add bookmark.")
        
        ttk.Button(button_frame, text="Save", command=save_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def edit_bookmark(self):
        """Edit selected bookmark"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bookmark to edit.")
            return
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, 'tags')
        if not tags:
            messagebox.showwarning("Invalid Selection", "Please select a bookmark (not a category).")
            return
        
        bookmark_id = int(tags[0])
        values = self.bookmarks_tree.item(item, 'values')
        
        # Create edit dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Edit Bookmark")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Form fields with existing values
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=50)
        name_entry.insert(0, values[0])
        name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="URL:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.insert(0, values[1])
        url_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Category:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        category_var = tk.StringVar(value=values[3])
        category_combo = ttk.Combobox(dialog, textvariable=category_var, width=47)
        category_combo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Get existing categories
        categories = get_bookmark_categories(self.current_project_id)
        if categories:
            category_combo['values'] = categories
        
        ttk.Label(dialog, text="Tags:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        tags_entry = ttk.Entry(dialog, width=50)
        tags_entry.insert(0, values[4])  # Tags are in index 4 now
        tags_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Description:").grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, height=5, width=40)
        desc_text.insert(1.0, values[2])
        desc_text.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        dialog.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        def update_bookmark_data():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get().strip() or "General"
            tags = tags_entry.get().strip()
            description = desc_text.get(1.0, tk.END).strip()
            
            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required.")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            success = update_bookmark(bookmark_id, name=name, url=url, description=description, category=category, tags=tags)
            if success:
                messagebox.showinfo("Success", "Bookmark updated successfully.")
                dialog.destroy()
                self.refresh_bookmarks()
            else:
                messagebox.showerror("Error", "Failed to update bookmark.")
        
        ttk.Button(button_frame, text="Update", command=update_bookmark_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_bookmark(self):
        """Delete selected bookmark"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bookmark to delete.")
            return
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, 'tags')
        if not tags:
            messagebox.showwarning("Invalid Selection", "Please select a bookmark (not a category).")
            return
        
        bookmark_id = int(tags[0])
        values = self.bookmarks_tree.item(item, 'values')
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Delete bookmark '{values[0]}'?"):
            return
        
        success = delete_bookmark(bookmark_id)
        if success:
            messagebox.showinfo("Success", "Bookmark deleted successfully.")
            self.refresh_bookmarks()
        else:
            messagebox.showerror("Error", "Failed to delete bookmark.")
    
    def on_search_change(self, event=None):
        """Handle search input changes"""
        self.refresh_bookmarks()
    
    def on_filter_change(self, event=None):
        """Handle filter changes"""
        self.refresh_bookmarks()
    
    def clear_filters(self):
        """Clear all search and filter criteria"""
        self.search_var.set("")
        self.category_filter_var.set("All")
        self.tags_filter_var.set("All")
        self.sort_var.set("Name")
        self.refresh_bookmarks()
    
    def duplicate_bookmark(self):
        """Duplicate selected bookmark"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bookmark to duplicate.")
            return
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, 'tags')
        if not tags:
            messagebox.showwarning("Invalid Selection", "Please select a bookmark (not a category).")
            return
        
        bookmark_id = int(tags[0])
        values = self.bookmarks_tree.item(item, 'values')
        
        # Create duplicate with "Copy" suffix
        new_name = f"{values[0]} (Copy)"
        
        success = add_bookmark(
            self.current_project_id, 
            new_name, 
            values[1],  # URL
            values[2],  # Description
            values[3],  # Category
            values[4]   # Tags
        )
        
        if success:
            messagebox.showinfo("Success", "Bookmark duplicated successfully.")
            self.refresh_bookmarks()
        else:
            messagebox.showerror("Error", "Failed to duplicate bookmark.")
    
    def import_bookmarks(self):
        """Import bookmarks from CSV file"""
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Please select a project first.")
            return
        
        # Ask for file location
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import Bookmarks"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            imported_count = 0
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                    try:
                        name = row.get('name', '').strip()
                        url = row.get('url', '').strip()
                        description = row.get('description', '').strip()
                        category = row.get('category', 'General').strip()
                        tags = row.get('tags', '').strip()
                        
                        if not name or not url:
                            errors.append(f"Row {row_num}: Missing name or URL")
                            continue
                        
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        
                        success = add_bookmark(
                            self.current_project_id,
                            name,
                            url,
                            description,
                            category,
                            tags
                        )
                        
                        if success:
                            imported_count += 1
                        else:
                            errors.append(f"Row {row_num}: Failed to save bookmark '{name}'")
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            # Show results
            if imported_count > 0:
                self.refresh_bookmarks()
                
            message = f"Import completed: {imported_count} bookmarks imported successfully."
            if errors:
                message += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    message += f"\n... and {len(errors) - 5} more errors"
            
            if errors:
                # Show in a scrollable text dialog for errors
                error_dialog = tk.Toplevel(self.frame)
                error_dialog.title("Import Results")
                error_dialog.geometry("500x400")
                error_dialog.transient(self.frame)
                
                text_widget = tk.Text(error_dialog, wrap=tk.WORD, padx=10, pady=10)
                text_widget.insert(tk.END, message)
                text_widget.config(state=tk.DISABLED)
                
                scrollbar = ttk.Scrollbar(error_dialog, command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                ttk.Button(error_dialog, text="Close", command=error_dialog.destroy).pack(pady=10)
            else:
                messagebox.showinfo("Import Successful", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import bookmarks: {e}")
    
    def export_bookmarks(self):
        """Export bookmarks to CSV file"""
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Please select a project first.")
            return
        
        # Get all bookmarks (unfiltered)
        all_bookmarks = get_project_bookmarks(self.current_project_id)
        
        if not all_bookmarks:
            messagebox.showinfo("No Bookmarks", "No bookmarks to export.")
            return
        
        # Ask for file location
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Bookmarks"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'url', 'description', 'category', 'created_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for bookmark in all_bookmarks:
                    writer.writerow({
                        'name': bookmark['name'],
                        'url': bookmark['url'],
                        'description': bookmark['description'] or '',
                        'category': bookmark['category'] or '',
                        'created_at': bookmark['created_at']
                    })
            
            messagebox.showinfo("Success", f"Exported {len(all_bookmarks)} bookmarks to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export bookmarks: {e}")
    
    def check_links(self):
        """Check the health of bookmark URLs"""
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Please select a project first.")
            return
        
        # Get all bookmarks
        bookmarks = get_project_bookmarks(self.current_project_id)
        if not bookmarks:
            messagebox.showinfo("No Bookmarks", "No bookmarks to check.")
            return
        
        # Create progress dialog
        progress_dialog = tk.Toplevel(self.frame)
        progress_dialog.title("Checking Links")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.frame)
        progress_dialog.grab_set()
        
        ttk.Label(progress_dialog, text="Checking bookmark URLs...").pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=len(bookmarks))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_dialog, text="Starting...")
        status_label.pack(pady=5)
        
        results = []
        
        def check_url(url, name):
            """Check if URL is accessible"""
            try:
                import urllib.request
                import urllib.error
                import socket
                
                # Set timeout
                socket.setdefaulttimeout(10)
                
                # Try to open URL
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req)
                return "OK", response.getcode()
                
            except urllib.error.HTTPError as e:
                return "ERROR", e.code
            except urllib.error.URLError as e:
                return "ERROR", str(e.reason)
            except Exception as e:
                return "ERROR", str(e)
        
        def run_checks():
            """Run link checks in background"""
            for i, bookmark in enumerate(bookmarks):
                status_label.config(text=f"Checking: {bookmark['name'][:30]}...")
                progress_var.set(i + 1)
                progress_dialog.update()
                
                status, detail = check_url(bookmark['url'], bookmark['name'])
                results.append({
                    'bookmark': bookmark,
                    'status': status,
                    'detail': detail
                })
            
            # Close progress dialog
            progress_dialog.destroy()
            
            # Show results
            self.show_link_check_results(results)
        
        # Run checks in separate thread
        import threading
        check_thread = threading.Thread(target=run_checks)
        check_thread.daemon = True
        check_thread.start()
    
    def show_link_check_results(self, results):
        """Show the results of link checking"""
        # Create results dialog
        results_dialog = tk.Toplevel(self.frame)
        results_dialog.title("Link Check Results")
        results_dialog.geometry("700x500")
        results_dialog.transient(self.frame)
        
        # Summary
        ok_count = sum(1 for r in results if r['status'] == 'OK')
        error_count = len(results) - ok_count
        
        summary_frame = ttk.Frame(results_dialog)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(summary_frame, text=f"Total: {len(results)}", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(summary_frame, text=f"OK: {ok_count}", foreground="green").pack(side=tk.LEFT, padx=10)
        ttk.Label(summary_frame, text=f"Errors: {error_count}", foreground="red").pack(side=tk.LEFT, padx=10)
        
        # Results treeview
        columns = ("Name", "URL", "Status", "Details")
        results_tree = ttk.Treeview(results_dialog, columns=columns, show="headings", height=15)
        
        results_tree.heading("Name", text="Bookmark Name")
        results_tree.column("Name", width=150)
        
        results_tree.heading("URL", text="URL")
        results_tree.column("URL", width=200)
        
        results_tree.heading("Status", text="Status")
        results_tree.column("Status", width=80)
        
        results_tree.heading("Details", text="Details")
        results_tree.column("Details", width=150)
        
        # Add results
        for result in results:
            results_tree.insert("", tk.END, values=(
                result['bookmark']['name'],
                result['bookmark']['url'],
                result['status'],
                str(result['detail'])
            ), tags=(result['status'],))
        
        # Color rows based on status
        results_tree.tag_configure("OK", foreground="green")
        results_tree.tag_configure("ERROR", foreground="red")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_dialog, orient=tk.VERTICAL, command=results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_dialog, orient=tk.HORIZONTAL, command=results_tree.xview)
        results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(results_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=results_dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def view_notes(self):
        """View and edit notes for selected bookmark"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bookmark to view notes.")
            return
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, 'tags')
        if not tags:
            messagebox.showwarning("Invalid Selection", "Please select a bookmark (not a category).")
            return
        
        bookmark_id = int(tags[0])
        values = self.bookmarks_tree.item(item, 'values')
        
        # Get full bookmark data including notes
        bookmarks = get_project_bookmarks(self.current_project_id)
        bookmark = next((b for b in bookmarks if b['id'] == bookmark_id), None)
        
        if not bookmark:
            messagebox.showerror("Error", "Bookmark not found.")
            return
        
        # Create notes dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Notes: {bookmark['name']}")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Notes text area
        ttk.Label(dialog, text="Notes:").pack(anchor="w", padx=10, pady=(10, 5))
        
        notes_frame = ttk.Frame(dialog)
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=15)
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(notes_frame, command=notes_text.yview)
        notes_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert existing notes
        if bookmark['notes']:
            notes_text.insert(1.0, bookmark['notes'])
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def save_notes():
            new_notes = notes_text.get(1.0, tk.END).strip()
            success = update_bookmark(bookmark_id, notes=new_notes)
            if success:
                messagebox.showinfo("Success", "Notes saved successfully.")
                dialog.destroy()
                self.refresh_bookmarks()
            else:
                messagebox.showerror("Error", "Failed to save notes.")
        
        ttk.Button(button_frame, text="Save", command=save_notes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def toggle_quick_access(self, event=None):
        """Toggle the quick access panel"""
        if self.quick_access_expanded:
            # Collapse
            self.quick_access_content.pack_forget()
            self.quick_access_expanded = False
            # Find the label frame and update text
            for child in self.frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and "Quick Access" in str(child.cget("text")):
                    child.config(text="Quick Access (Click to Expand)")
                    break
        else:
            # Expand
            self.quick_access_content.pack(fill=tk.X, pady=5)
            self.quick_access_expanded = True
            # Find the label frame and update text
            for child in self.frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and "Quick Access" in str(child.cget("text")):
                    child.config(text="Quick Access (Click to Collapse)")
                    break
            # Refresh quick access content
            self.refresh_quick_access()
    
    def refresh_quick_access(self):
        """Refresh the quick access panel with recent bookmarks"""
        if not self.quick_access_expanded:
            return
        
        # Clear existing buttons
        for widget in self.quick_access_buttons_frame.winfo_children():
            widget.destroy()
        
        # Get recent bookmarks (last 10 by creation date)
        bookmarks = get_project_bookmarks(self.current_project_id)
        if not bookmarks:
            self.quick_access_label.pack(pady=20)
            return
        
        # Sort by creation date (most recent first) and take top 10
        recent_bookmarks = sorted(
            bookmarks, 
            key=lambda x: x['created_at'] or '', 
            reverse=True
        )[:10]
        
        if not recent_bookmarks:
            self.quick_access_label.pack(pady=20)
            return
        
        # Hide the "no bookmarks" label
        self.quick_access_label.pack_forget()
        
        # Pack the buttons frame
        self.quick_access_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Create buttons for recent bookmarks
        for bookmark in recent_bookmarks:
            btn = ttk.Button(
                self.quick_access_buttons_frame,
                text=bookmark['name'][:20] + ("..." if len(bookmark['name']) > 20 else ""),
                command=lambda b=bookmark: self.open_bookmark_by_id(b['id'])
            )
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            # Add tooltip
            CreateToolTip(btn, f"{bookmark['name']}\n{bookmark['url']}\nCategory: {bookmark['category'] or 'None'}")
    
    def open_bookmark_by_id(self, bookmark_id):
        """Open a bookmark by its ID"""
        # Get bookmark details
        bookmarks = get_project_bookmarks(self.current_project_id)
        bookmark = next((b for b in bookmarks if b['id'] == bookmark_id), None)
        
        if bookmark:
            try:
                webbrowser.open(bookmark['url'])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open URL: {e}")
    
    def show_templates(self):
        """Show bookmark templates dialog"""
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Please select a project first.")
            return
        
        # Create templates dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Bookmark Templates")
        dialog.geometry("600x500")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Templates data
        templates = [
            {
                "name": "Autodesk Construction Cloud",
                "url": "https://acc.autodesk.com",
                "category": "BIM Tools",
                "tags": "Autodesk, ACC, Construction Cloud, BIM",
                "description": "Autodesk Construction Cloud - Project management and BIM collaboration platform"
            },
            {
                "name": "Revit Health Check",
                "url": "https://healthcheck.autodesk.com",
                "category": "BIM Tools",
                "tags": "Autodesk, Revit, Health Check, BIM",
                "description": "Autodesk Revit Health Check - Analyze model performance and issues"
            },
            {
                "name": "BIM 360 Docs",
                "url": "https://docs.b360.autodesk.com",
                "category": "Document Management",
                "tags": "Autodesk, BIM 360, Documents, Collaboration",
                "description": "BIM 360 Docs - Document management and collaboration platform"
            },
            {
                "name": "Navisworks",
                "url": "https://www.autodesk.com/products/navisworks/overview",
                "category": "BIM Tools",
                "tags": "Autodesk, Navisworks, Coordination, BIM",
                "description": "Autodesk Navisworks - Project review and coordination software"
            },
            {
                "name": "IFC Model Viewer",
                "url": "https://ifcjs.github.io/web-ifc-viewer/example/index",
                "category": "BIM Tools",
                "tags": "IFC, Viewer, Open Source, BIM",
                "description": "Web IFC Viewer - Open source IFC model viewer"
            },
            {
                "name": "Construction Specifications Institute",
                "url": "https://www.csiresources.org",
                "category": "Standards",
                "tags": "CSI, Specifications, Standards, Construction",
                "description": "CSI - Construction Specifications Institute resources"
            },
            {
                "name": "Building Information Modeling Forum",
                "url": "https://www.bimforum.org",
                "category": "Industry",
                "tags": "BIM, Forum, Industry, Standards",
                "description": "BIMForum - Building Information Modeling industry organization"
            },
            {
                "name": "ISO 19650 Standards",
                "url": "https://www.iso.org/standard/68078.html",
                "category": "Standards",
                "tags": "ISO, 19650, BIM, Standards",
                "description": "ISO 19650 - Information management using building information modelling"
            }
        ]
        
        # Create treeview for templates
        columns = ("Name", "Category", "Tags")
        template_tree = ttk.Treeview(dialog, columns=columns, show="headings", height=12)
        
        template_tree.heading("Name", text="Template Name")
        template_tree.column("Name", width=200)
        
        template_tree.heading("Category", text="Category")
        template_tree.column("Category", width=120)
        
        template_tree.heading("Tags", text="Tags")
        template_tree.column("Tags", width=150)
        
        # Add templates to treeview
        for template in templates:
            template_tree.insert("", tk.END, values=(
                template["name"],
                template["category"],
                template["tags"]
            ), tags=(str(templates.index(template)),))
        
        template_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def add_selected_template():
            selection = template_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a template to add.")
                return
            
            item = selection[0]
            item_tags = template_tree.item(item, 'tags')
            if not item_tags:
                return
            
            template_index = int(item_tags[0])
            template = templates[template_index]
            
            success = add_bookmark(
                self.current_project_id,
                template["name"],
                template["url"],
                template["description"],
                template["category"],
                template["tags"]
            )
            
            if success:
                messagebox.showinfo("Success", f"Template '{template['name']}' added successfully.")
                dialog.destroy()
                self.refresh_bookmarks()
            else:
                messagebox.showerror("Error", "Failed to add template bookmark.")
        
        def preview_template():
            selection = template_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a template to preview.")
                return
            
            item = selection[0]
            item_tags = template_tree.item(item, 'tags')
            if not item_tags:
                return
            
            template_index = int(item_tags[0])
            template = templates[template_index]
            
            # Show preview dialog
            preview_dialog = tk.Toplevel(dialog)
            preview_dialog.title(f"Preview: {template['name']}")
            preview_dialog.geometry("500x300")
            preview_dialog.transient(dialog)
            
            ttk.Label(preview_dialog, text="Name:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(preview_dialog, text=template["name"]).grid(row=0, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Label(preview_dialog, text="URL:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(preview_dialog, text=template["url"]).grid(row=1, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Label(preview_dialog, text="Category:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(preview_dialog, text=template["category"]).grid(row=2, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Label(preview_dialog, text="Tags:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(preview_dialog, text=template["tags"]).grid(row=3, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Label(preview_dialog, text="Description:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="nw", padx=10, pady=5)
            desc_label = ttk.Label(preview_dialog, text=template["description"], wraplength=300)
            desc_label.grid(row=4, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Button(preview_dialog, text="Close", command=preview_dialog.destroy).grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Preview", command=preview_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Template", command=add_selected_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def open_bookmark(self):
        """Open selected bookmark in browser"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a bookmark to open.")
            return
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, 'tags')
        if not tags:
            messagebox.showwarning("Invalid Selection", "Please select a bookmark (not a category).")
            return
        
        values = self.bookmarks_tree.item(item, 'values')
        url = values[1]
        
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open URL: {e}")
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()


class IssueManagementTab:
    """Issue Management Interface - ACC Folders and Revizto Data"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? Issue Management")
        
        # Initialize variables that will be used across sub-tabs
        self.current_project_id = None
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Set up the issue management interface with sub-tabs"""
        # Create main notebook for sub-tabs
        self.sub_notebook = ttk.Notebook(self.frame)
        self.sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: ACC Folder Management
        self.setup_acc_folder_tab()
        
        # Tab 2: Revizto Data Management
        self.setup_revizto_tab()
        
        # Tab 3: Analytics Dashboard (NEW)
        self.setup_analytics_dashboard_tab()
    
    def setup_revizto_tab(self):
        """Setup the Revizto Data Management sub-tab"""
        revizto_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(revizto_frame, text="?? Revizto Data")
        
        # Extraction Control Frame
        control_frame = ttk.LabelFrame(revizto_frame, text="?? Extraction Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Extraction buttons
        ttk.Button(control_frame, text="Start Revizto Extract", 
                  command=self.open_revizto_exporter).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh History", 
                  command=self.refresh_revizto_history).pack(side=tk.LEFT, padx=5)
        
        # Last run info
        self.last_run_var = tk.StringVar(value="No extraction runs found")
        ttk.Label(control_frame, textvariable=self.last_run_var, 
                 font=("Arial", 10)).pack(side=tk.RIGHT, padx=20)
        
        # Extraction History Frame
        history_frame = ttk.LabelFrame(revizto_frame, text="?? Extraction History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # History treeview
        history_columns = ("Run ID", "Start Time", "End Time", "Status", "Projects", "Issues", "Licenses", "Duration")
        self.revizto_history_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=8)
        
        for col in history_columns:
            self.revizto_history_tree.heading(col, text=col)
            if col in ["Run ID", "Projects", "Issues", "Licenses"]:
                width = 80
            elif col == "Status":
                width = 100
            elif col == "Duration":
                width = 120
            else:
                width = 150
            self.revizto_history_tree.column(col, width=width, anchor="w")
        
        # Scrollbars
        history_v_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.revizto_history_tree.yview)
        history_h_scroll = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.revizto_history_tree.xview)
        self.revizto_history_tree.configure(yscrollcommand=history_v_scroll.set, xscrollcommand=history_h_scroll.set)
        
        self.revizto_history_tree.grid(row=0, column=0, sticky="nsew")
        history_v_scroll.grid(row=0, column=1, sticky="ns")
        history_h_scroll.grid(row=1, column=0, sticky="ew")
        
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)
        
        # Project Changes Frame
        changes_frame = ttk.LabelFrame(revizto_frame, text="?? Recent Project Changes", padding=10)
        changes_frame.pack(fill=tk.BOTH, expand=True)
        
        # Changes treeview
        changes_columns = ("Project UUID", "Title", "Updated", "Owner", "Status")
        self.revizto_changes_tree = ttk.Treeview(changes_frame, columns=changes_columns, show="headings", height=6)
        
        for col in changes_columns:
            self.revizto_changes_tree.heading(col, text=col)
            if col == "Project UUID":
                width = 200
            elif col == "Updated":
                width = 150
            elif col == "Status":
                width = 100
            else:
                width = 120
            self.revizto_changes_tree.column(col, width=width, anchor="w")
        
        self.revizto_changes_tree.pack(fill=tk.BOTH, expand=True)
    
    def safe_format_datetime(self, dt_value):
        """Safely format datetime value that might be string or datetime object"""
        if not dt_value:
            return 'N/A'
        if isinstance(dt_value, str):
            try:
                # Try to parse string as datetime
                dt_obj = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                return str(dt_value)
        elif hasattr(dt_value, 'strftime'):
            return dt_value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(dt_value)
    
    def open_revizto_exporter(self):
        """Open Revizto data exporter and track the extraction run"""
        try:
            exe_path = os.path.abspath("tools/ReviztoDataExporter.exe")
            if os.path.exists(exe_path):
                # Start recording the extraction run
                export_folder = os.path.join(os.path.dirname(exe_path), "Exports")
                run_id = start_revizto_extraction_run(
                    export_folder=export_folder,
                    notes="Started via BIM Project Management UI"
                )

                if run_id:
                    logger.info(f"Started Revizto extraction run {run_id}")
                    messagebox.showinfo("Revizto Extract", f"Started extraction run #{run_id}. Check the extraction history tab to monitor progress.")
                else:
                    logger.warning("Failed to record extraction run start")

                # Launch the exporter
                import subprocess
                subprocess.Popen([exe_path])

                # Note: In a future enhancement, we could monitor the export folder
                # for new files to automatically detect completion and update the run record

            else:
                messagebox.showerror("Error", f"Revizto Exporter not found at: {exe_path}")
        except Exception as e:
            logger.error(f"Error opening Revizto exporter: {e}")
            messagebox.showerror("Error", f"Error opening Revizto exporter: {e}")
    
    def refresh_revizto_history(self):
        """Refresh the Revizto extraction history"""
        try:
            # Clear existing data
            for item in self.revizto_history_tree.get_children():
                self.revizto_history_tree.delete(item)
            
            # Get extraction runs
            runs = get_revizto_extraction_runs()
            
            for run in runs:
                start_time = self.safe_format_datetime(run['start_time'])
                end_time = self.safe_format_datetime(run['end_time']) if run['end_time'] else 'Running'
                
                # Calculate duration
                if run['end_time'] and run['start_time']:
                    try:
                        # Convert to datetime objects if they are strings
                        start_dt = run['start_time'] if isinstance(run['start_time'], datetime) else datetime.fromisoformat(str(run['start_time']).replace('Z', '+00:00'))
                        end_dt = run['end_time'] if isinstance(run['end_time'], datetime) else datetime.fromisoformat(str(run['end_time']).replace('Z', '+00:00'))
                        duration = str(end_dt - start_dt).split('.')[0]  # Remove microseconds
                    except (ValueError, TypeError):
                        duration = 'N/A'
                else:
                    duration = 'N/A'
                
                self.revizto_history_tree.insert("", tk.END, values=(
                    run['run_id'],
                    start_time,
                    end_time,
                    run['status'],
                    run['projects_extracted'],
                    run['issues_extracted'],
                    run['licenses_extracted'],
                    duration
                ))
            
            # Update last run info
            last_run = get_last_revizto_extraction_run()
            if last_run:
                last_run_time = last_run['end_time'] or last_run['start_time']
                self.last_run_var.set(f"Last run: {self.safe_format_datetime(last_run_time)} ({last_run['status']})")
            else:
                self.last_run_var.set("No extraction runs found")
            
            # Load project changes
            self.refresh_revizto_changes()
            
        except Exception as e:
            logger.error(f"Error refreshing Revizto history: {e}")
            messagebox.showerror("Error", f"Failed to refresh extraction history: {e}")
    
    def refresh_revizto_changes(self):
        """Refresh the recent project changes"""
        try:
            # Clear existing data
            for item in self.revizto_changes_tree.get_children():
                self.revizto_changes_tree.delete(item)
            
            # Get projects changed since last run
            from database import get_revizto_projects_since_last_run
            changed_projects = get_revizto_projects_since_last_run()
            
            for project in changed_projects:
                status = "Archived" if project['archived'] else ("Frozen" if project['frozen'] else "Active")
                updated_time = self.safe_format_datetime(project['updated'])
                
                self.revizto_changes_tree.insert("", tk.END, values=(
                    project['project_uuid'],
                    project['title'],
                    updated_time,
                    project['owner_email'],
                    status
                ))
            
        except Exception as e:
            logger.error(f"Error refreshing Revizto changes: {e}")
    
    def setup_analytics_dashboard_tab(self):
        """Setup the Issue Analytics Dashboard sub-tab"""
        try:
            # Create the dashboard using the dedicated class
            self.analytics_dashboard = IssueAnalyticsDashboard(self.sub_notebook)
            logger.info("Issue Analytics Dashboard tab initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Analytics Dashboard: {e}")
            messagebox.showerror("Error", f"Failed to initialize Analytics Dashboard:\n{str(e)}")
    
    def setup_acc_folder_tab(self):
        """Setup the ACC folder management sub-tab"""
        # Initialize current project ID
        self.current_project_id = None
        
        acc_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(acc_frame, text="?? ACC Folders")
        
        # === Project Selection ===
        project_frame = ttk.LabelFrame(acc_frame, text="Project Selection", padding=10)
        project_frame.pack(fill="x", padx=10, pady=5)
        
        projects = format_id_name_list(get_projects())
        ttk.Label(project_frame, text="Select Project:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, values=projects, width=50)
        self.project_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected_local)
        
        project_frame.columnconfigure(1, weight=1)
        
        # === ACC Data Export Path ===
        export_frame = ttk.LabelFrame(acc_frame, text="ACC Data Export Configuration", padding=10)
        export_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(export_frame, text="ACC Data Export Folder:").grid(row=0, column=0, sticky="w", padx=5)
        self.export_path_entry = ttk.Entry(export_frame, width=60)
        self.export_path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        def browse_export_folder():
            path = filedialog.askdirectory(title="Select ACC Data Export Folder")
            if path:
                self.export_path_entry.delete(0, tk.END)
                self.export_path_entry.insert(0, path)
        
        def save_export_path():
            if " - " not in self.project_combo.get():
                messagebox.showerror("Error", "Select a project first")
                return
            pid = self.project_combo.get().split(" - ")[0]
            path = self.export_path_entry.get().strip()
            if not path or not os.path.isdir(path):
                messagebox.showerror("Error", "Select a valid folder")
                return
            save_acc_folder_path(pid, path)
            messagebox.showinfo("Success", "ACC data export path saved")
        
        ttk.Button(export_frame, text="Browse", command=browse_export_folder).grid(row=0, column=2, padx=5)
        ttk.Button(export_frame, text="Save Path", command=save_export_path).grid(row=0, column=3, padx=5)
        
        export_frame.columnconfigure(1, weight=1)
        
        # === ACC CSV Import Section ===
        import_frame = ttk.LabelFrame(acc_frame, text="ACC Issues ZIP Import", padding=10)
        import_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(import_frame, text="ACC Issues ZIP File:").grid(row=0, column=0, sticky="w", padx=5)
        self.import_path_entry = ttk.Entry(import_frame, width=60)
        self.import_path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        def browse_import_file():
            path = filedialog.askopenfilename(
                title="Select ACC Issues ZIP File",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
            )
            if path:
                self.import_path_entry.delete(0, tk.END)
                self.import_path_entry.insert(0, path)
        
        def run_import():
            zip_path = self.import_path_entry.get().strip()
            if not zip_path or not os.path.isfile(zip_path):
                messagebox.showerror("Error", "Select a valid ZIP file")
                return
            
            # Check if project is selected
            if " - " not in self.project_combo.get():
                messagebox.showerror("Error", "Please select a project first")
                return
            
            try:
                # Run the ACC import with proper parameters
                # Since we don't have a dedicated listbox here, we'll create a temporary one for logging
                temp_log_listbox = tk.Listbox(acc_frame, height=1)  # Temporary listbox for compatibility
                success, msg = run_acc_import(self.project_combo, self.import_path_entry, temp_log_listbox)
                temp_log_listbox.destroy()  # Clean up temporary widget
                
                if success:
                    messagebox.showinfo("Success", "ACC import completed successfully")
                    # Refresh the logs tree view
                    self.refresh_acc_logs()
                else:
                    messagebox.showerror("Error", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
        
        ttk.Button(import_frame, text="Browse", command=browse_import_file).grid(row=0, column=2, padx=5)
        ttk.Button(import_frame, text="Import ACC Issues", command=run_import).grid(row=0, column=3, padx=5)
        
        import_frame.columnconfigure(1, weight=1)
        
        # === ACC Import Logs ===
        logs_frame = ttk.LabelFrame(acc_frame, text="ACC Import Logs", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Logs treeview
        logs_columns = ("Log ID", "Project", "Folder", "Import Date", "Status", "Summary")
        self.logs_tree = ttk.Treeview(logs_frame, columns=logs_columns, show="headings", height=8)
        
        for col in logs_columns:
            self.logs_tree.heading(col, text=col)
            width = 100 if col in ["Log ID", "Status"] else 120 if col == "Import Date" else 150
            self.logs_tree.column(col, width=width, anchor="w")
        
        logs_scroll = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=logs_scroll.set)
        
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh logs button
        ttk.Button(logs_frame, text="Refresh Logs", command=self.refresh_acc_logs).pack(pady=5)
    
    def on_project_selected_local(self, event=None):
        """Handle project selection for ACC folder management"""
        try:
            selected = self.project_var.get()
            if not selected or " - " not in selected:
                return
            
            self.current_project_id = int(selected.split(" - ")[0])
            
            # Load ACC folder path for this project
            acc_path = get_acc_folder_path(self.current_project_id)
            if acc_path:
                self.export_path_entry.delete(0, tk.END)
                self.export_path_entry.insert(0, acc_path)
            else:
                self.export_path_entry.delete(0, tk.END)
            
            # Refresh logs for this project
            self.refresh_acc_logs()
            
        except Exception as e:
            logger.error(f"Error selecting project: {e}")
    
    def refresh_acc_logs(self):
        """Refresh ACC import logs"""
        try:
            # Clear existing logs
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            # Get logs for current project if selected
            logs = []
            if hasattr(self, 'current_project_id') and self.current_project_id:
                logs = get_acc_import_logs(self.current_project_id)
            
            # Insert logs into tree view
            if logs:
                for log in logs:
                    # Handle both dictionary and tuple formats for backward compatibility
                    if isinstance(log, dict):
                        values = (
                            log.get('log_id', ''),
                            log.get('project_id', ''),
                            log.get('folder_name', ''),
                            log.get('import_date', ''),
                            log.get('status', ''),
                            log.get('summary', '')
                        )
                    else:
                        # Handle tuple format (legacy support)
                        values = tuple(log) + ('',) * (6 - len(log))  # Pad to 6 columns
                    
                    self.logs_tree.insert("", tk.END, values=values)
            else:
                # Show "No logs found" message
                self.logs_tree.insert("", tk.END, values=('', '', 'No ACC import logs found', '', '', ''))
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing ACC logs: {e}")
            # Show error in the tree view
            try:
                self.logs_tree.insert("", tk.END, values=('', '', f'Error loading logs: {str(e)}', '', '', ''))
            except:
                pass
    
    def refresh_data(self):
        """Refresh all data in the issue management tab"""
        try:
            # Refresh project list
            projects = format_id_name_list(get_projects())
            if hasattr(self, 'project_combo'):
                self.project_combo['values'] = projects
            
            # Refresh Revizto data
            self.refresh_revizto_history()
            
        except Exception as e:
            logger.error(f"Error refreshing issue management data: {e}")
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if hasattr(self, 'project_var') and self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected_local()
    
    def on_project_list_changed(self):
        """Handle notification that the project list has changed"""
        self.refresh_data()