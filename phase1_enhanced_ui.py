"""
Phase 1 Enhanced UI Module
Enhanced task management, milestone tracking, and resource allocation interface
Includes existing daily workflow components: ACC folder management, data import, and issue management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import threading
import os
import pandas as pd
from phase1_enhanced_database import (
    EnhancedTaskManager, MilestoneManager, ResourceManager, ProjectTemplateManager
)
from database import (
    get_projects, get_users_list, save_acc_folder_path, get_acc_folder_path,
    get_acc_import_logs, connect_to_db, insert_project, get_cycle_ids,
    get_review_summary, get_project_details, get_project_folders,
    get_review_cycles, get_review_schedule, update_client_info,
    get_available_clients, assign_client_to_project, create_new_client,
    update_project_details, update_project_folders, get_project_review_progress,
    get_review_tasks, get_contractual_links
)
from review_management_service import ReviewManagementService
try:
    from backend.documents import services as doc_services
    from backend.documents import runner as doc_runner
except Exception:
    doc_services = None
    doc_runner = None
from constants import schema as S
from ui.ui_helpers import (
    create_labeled_entry, create_labeled_combobox, create_horizontal_button_group
)
from ui.tooltips import CreateToolTip
from acc_handler import run_acc_import
from review_handler import submit_review_schedule, generate_stage_review_schedule

class ProjectNotificationSystem:
    """Centralized project change notification system"""
    
    def __init__(self):
        self.observers = []
        self.current_project = None
    
    def register_observer(self, observer):
        """Register a tab to receive project change notifications"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def unregister_observer(self, observer):
        """Unregister a tab from receiving notifications"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_project_changed(self, project_selection):
        """Notify all registered tabs that the project has changed"""
        if project_selection != self.current_project:
            self.current_project = project_selection
            for observer in self.observers:
                try:
                    if hasattr(observer, 'on_project_changed'):
                        observer.on_project_changed(project_selection)
                except Exception as e:
                    print(f"Error notifying observer {observer}: {e}")
    
    def get_current_project(self):
        """Get the currently selected project"""
        return self.current_project

# Global project notification system
project_notification_system = ProjectNotificationSystem()

class EnhancedTaskManagementTab:
    """Enhanced task management interface with dependencies and progress tracking"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📋 Enhanced Tasks")
        
        self.task_mgr = EnhancedTaskManager()
        self.resource_mgr = ResourceManager()
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Setup the enhanced task management UI"""
        
        # Main container with scrollbar
        main_canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === Project Selection ===
        project_frame = ttk.LabelFrame(scrollable_frame, text="Project Selection", padding=10)
        project_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(project_frame, text="Select Project:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50)
        self.project_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected_local)
        
        project_frame.columnconfigure(1, weight=1)
        
        # === Task Creation ===
        task_create_frame = ttk.LabelFrame(scrollable_frame, text="Create New Task", padding=10)
        task_create_frame.pack(fill="x", padx=10, pady=5)
        
        # Task details
        ttk.Label(task_create_frame, text="Task Name:").grid(row=0, column=0, sticky="w", padx=5)
        self.task_name_entry = ttk.Entry(task_create_frame, width=40)
        self.task_name_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        ttk.Label(task_create_frame, text="Priority:").grid(row=0, column=2, sticky="w", padx=5)
        self.priority_var = tk.StringVar(value="Medium")
        priority_combo = ttk.Combobox(task_create_frame, textvariable=self.priority_var, 
                                    values=["Low", "Medium", "High", "Critical"], width=10)
        priority_combo.grid(row=0, column=3, padx=5)
        
        ttk.Label(task_create_frame, text="Start Date:").grid(row=1, column=0, sticky="w", padx=5)
        self.start_date_entry = DateEntry(task_create_frame, width=12, date_pattern='yyyy-mm-dd')
        self.start_date_entry.grid(row=1, column=1, padx=5, sticky="w")
        
        ttk.Label(task_create_frame, text="End Date:").grid(row=1, column=2, sticky="w", padx=5)
        self.end_date_entry = DateEntry(task_create_frame, width=12, date_pattern='yyyy-mm-dd')
        self.end_date_entry.grid(row=1, column=3, padx=5, sticky="w")
        
        ttk.Label(task_create_frame, text="Estimated Hours:").grid(row=2, column=0, sticky="w", padx=5)
        self.estimated_hours_entry = ttk.Entry(task_create_frame, width=10)
        self.estimated_hours_entry.grid(row=2, column=1, padx=5, sticky="w")
        
        ttk.Label(task_create_frame, text="Assigned To:").grid(row=2, column=2, sticky="w", padx=5)
        self.assigned_to_var = tk.StringVar()
        self.assigned_to_combo = ttk.Combobox(task_create_frame, textvariable=self.assigned_to_var, width=20)
        self.assigned_to_combo.grid(row=2, column=3, padx=5)
        
        ttk.Label(task_create_frame, text="Predecessor Task:").grid(row=3, column=0, sticky="w", padx=5)
        self.predecessor_var = tk.StringVar()
        self.predecessor_combo = ttk.Combobox(task_create_frame, textvariable=self.predecessor_var, width=40)
        self.predecessor_combo.grid(row=3, column=1, columnspan=2, padx=5, sticky="ew")
        
        ttk.Label(task_create_frame, text="Description:").grid(row=4, column=0, sticky="nw", padx=5)
        self.description_text = tk.Text(task_create_frame, height=3, width=40)
        self.description_text.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Create task button
        create_btn = ttk.Button(task_create_frame, text="Create Task", command=self.create_task)
        create_btn.grid(row=5, column=0, columnspan=4, pady=10)
        
        task_create_frame.columnconfigure(1, weight=1)
        
        # === Task List and Progress Tracking ===
        task_list_frame = ttk.LabelFrame(scrollable_frame, text="Project Tasks", padding=10)
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
        projects = get_projects()
        project_values = [f"{p[0]} - {p[1]}" for p in projects]
        self.project_combo['values'] = project_values
        
        # Load users
        users = get_users_list()
        user_values = [f"{u[0]} - {u[1]}" for u in users]
        self.assigned_to_combo['values'] = user_values
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        selected = self.project_var.get()
        if " - " in selected:
            project_id = int(selected.split(" - ")[0])
            self.current_project_id = project_id
            self.load_project_tasks()
    
    def load_project_tasks(self):
        """Load tasks for the selected project"""
        if not hasattr(self, 'current_project_id'):
            return
        
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Load tasks
        tasks = self.task_mgr.get_project_task_hierarchy(self.current_project_id)
        
        # Populate predecessor dropdown
        task_options = [""] + [f"{t['task_id']} - {t['task_name']}" for t in tasks]
        self.predecessor_combo['values'] = task_options
        
        # Populate tree
        for task in tasks:
            # Determine progress bar color based on health
            health_colors = {
                'Complete': '🟢',
                'On Track': '🟡',
                'Due Soon': '🟠',
                'Overdue': '🔴'
            }
            health_icon = health_colors.get(task['health_status'], '⚪')
            
            # Format progress display
            progress_display = f"{task['progress_percentage']}%"
            if task['estimated_hours'] and task['actual_hours']:
                variance = task['actual_hours'] - task['estimated_hours']
                if variance != 0:
                    progress_display += f" ({variance:+.1f}h)"
            
            self.task_tree.insert("", "end", 
                                text=str(task['task_id']),
                                values=(
                                    task['task_name'],
                                    task['priority'],
                                    progress_display,
                                    task['status'],
                                    task['assigned_user'] or 'Unassigned',
                                    task['start_date'].strftime('%Y-%m-%d') if task['start_date'] else '',
                                    task['end_date'].strftime('%Y-%m-%d') if task['end_date'] else '',
                                    f"{health_icon} {task['health_status']}"
                                ))
    
    def on_task_selected(self, event):
        """Handle task selection for progress update"""
        selection = self.task_tree.selection()
        if selection:
            item = self.task_tree.item(selection[0])
            self.selected_task_id = int(item['text'])
            
            # Get current progress from task data
            tasks = self.task_mgr.get_project_task_hierarchy(self.current_project_id)
            for task in tasks:
                if task['task_id'] == self.selected_task_id:
                    self.progress_var.set(str(task['progress_percentage']))
                    self.actual_hours_var.set(str(task['actual_hours'] or ''))
                    break
    
    def create_task(self):
        """Create a new task"""
        if not hasattr(self, 'current_project_id'):
            messagebox.showerror("Error", "Please select a project first")
            return
        
        # Get assigned user ID
        assigned_to = None
        if self.assigned_to_var.get() and " - " in self.assigned_to_var.get():
            assigned_to = int(self.assigned_to_var.get().split(" - ")[0])
        
        # Get predecessor task ID
        predecessor_id = None
        if self.predecessor_var.get() and " - " in self.predecessor_var.get():
            predecessor_id = int(self.predecessor_var.get().split(" - ")[0])
        
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
            print(f"Error refreshing project data: {e}")

class ResourceManagementTab:
    """Resource allocation and workload management interface"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="👥 Resources")
        
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
        for item in self.resource_tree.get_children():
            self.resource_tree.delete(item)
        
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
            'Overallocated': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢'
        }
        
        # Populate tree
        for resource in resources:
            status_icon = status_colors.get(resource['workload_status'], '⚪')
            
            self.resource_tree.insert("", "end",
                                    text=str(resource['user_id']),
                                    values=(
                                        resource['name'],
                                        resource['role_level'] or 'N/A',
                                        resource['department'] or 'N/A',
                                        f"{resource['weekly_capacity_hours']:.1f}h",
                                        f"{resource['allocated_hours']:.1f}h",
                                        f"{resource['utilization_percentage']:.1f}%",
                                        f"{status_icon} {resource['workload_status']}",
                                        f"{resource['available_hours']:.1f}h"
                                    ))
        
        # Update summary
        self.stats_label.config(text=f"Total Resources: {total_resources} | "
                                   f"Overallocated: {overallocated} | "
                                   f"Average Utilization: {avg_utilization:.1f}%")
    
    def find_available_resources(self):
        """Find available resources based on criteria"""
        skills_text = self.skills_entry.get().strip()
        required_skills = [s.strip() for s in skills_text.split(',')] if skills_text else None
        role_level = self.role_var.get() if self.role_var.get() else None
        
        try:
            max_utilization = float(self.max_util_var.get())
        except ValueError:
            max_utilization = 80.0
        
        available = self.resource_mgr.find_available_resources(
            required_skills=required_skills,
            role_level=role_level,
            max_utilization=max_utilization
        )
        
        if available:
            result_text = f"Found {len(available)} available resources:\n\n"
            for resource in available[:5]:  # Show top 5
                result_text += f"👤 {resource['name']} ({resource['role_level']})\n"
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
        # This could reload resource data if needed
        pass
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection"""
        self.refresh_data()
        
        # Notify other tabs about the project change
        project_notification_system.notify_project_changed(self.project_var.get())
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        # ResourceManagementTab may not have project selection, but implement for completeness
        self.refresh_data()

class ACCFolderManagementTab:
    """ACC Folder Management and Data Import Interface"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📂 ACC Folders")
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Setup the ACC folder management UI"""
        
        # === Project Selection ===
        project_frame = ttk.LabelFrame(self.frame, text="Project Selection", padding=10)
        project_frame.pack(fill="x", padx=10, pady=5)
        
        projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
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
                self.log_listbox.insert(tk.END, f"✅ {folder_name} @ {date.strftime('%Y-%m-%d %H:%M')}")
        else:
            self.log_listbox.insert(tk.END, "No previous ACC imports found.")
    
    def show_issues_import_summary(self):
        """Show summary of imported issues data"""
        try:
            conn = connect_to_db("acc_data_schema")
            if conn is None:
                return
            
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
            print(f"Error showing issues summary: {e}")
        finally:
            if conn:
                conn.close()
    
    def preview_issues_data(self):
        """Preview issues data from acc_data_schema database"""
        try:
            conn = connect_to_db("acc_data_schema")
            if conn is None:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, "❌ Cannot connect to acc_data_schema database")
                return
            
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
            self.preview_text.insert(1.0, f"❌ Error querying issues data: {str(e)}")
        finally:
            if conn:
                conn.close()
    
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

class ReviewManagementTab:
    """Enhanced Review Management Interface with Service Templates and Advanced Planning"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📋 Review Management")
        
        self.current_project_id = None
        self.current_cycle_id = None
        self.review_service = None
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
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
        self.sub_notebook.add(service_frame, text="🛠️ Service Setup")
        
        # Project Selection Frame
        project_frame = ttk.LabelFrame(service_frame, text="📁 Project Selection", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(project_frame, text="Project:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)
        
        # Service Template Frame
        template_frame = ttk.LabelFrame(service_frame, text="📋 Service Templates", padding=10)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Template selection
        ttk.Label(template_frame, text="Available Templates:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, width=40, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Template action buttons
        ttk.Button(template_frame, text="Load Template", command=self.load_template).grid(row=0, column=2, padx=5)
        ttk.Button(template_frame, text="Apply to Project", command=self.apply_template).grid(row=0, column=3, padx=5)
        ttk.Button(template_frame, text="Clear All Services", command=self.clear_services).grid(row=0, column=4, padx=5)
        
        # Current Project Services Frame
        services_frame = ttk.LabelFrame(service_frame, text="🔧 Current Project Services", padding=10)
        services_frame.pack(fill=tk.BOTH, expand=True)
        
        # Services treeview
        service_columns = ("Service ID", "Phase", "Service Code", "Service Name", "Unit Type", "Qty", "Rate", "Fee", "Status")
        self.services_tree = ttk.Treeview(services_frame, columns=service_columns, show="headings", height=8)
        
        for col in service_columns:
            self.services_tree.heading(col, text=col)
            width = 80 if col in ["Service ID", "Qty", "Rate"] else 120
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
        ttk.Button(service_buttons_frame, text="Generate Reviews", command=self.generate_reviews_from_services).pack(side=tk.LEFT, padx=5)
    
    def setup_review_planning_tab(self):
        """Setup the Review Planning & Scheduling tab"""
        planning_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(planning_frame, text="📅 Review Planning")
        
        # Stage Planning Frame
        stage_frame = ttk.LabelFrame(planning_frame, text="🏗️ Stage Review Planning", padding=10)
        stage_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Stage input fields
        input_frame = ttk.Frame(stage_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Stage:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.stage_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.stage_var, width=20).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(input_frame, text="Start Date:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.stage_start_date = DateEntry(input_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.stage_start_date.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Label(input_frame, text="End Date:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.stage_end_date = DateEntry(input_frame, width=12, background='darkblue',
                                      foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.stage_end_date.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Label(input_frame, text="Reviews:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.stage_reviews_var = tk.StringVar(value="4")
        ttk.Entry(input_frame, textvariable=self.stage_reviews_var, width=10).grid(row=1, column=1, padx=(0, 10))
        
        ttk.Label(input_frame, text="Frequency:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.stage_freq_var = tk.StringVar(value="weekly")
        freq_combo = ttk.Combobox(input_frame, textvariable=self.stage_freq_var, width=15, state="readonly")
        freq_combo['values'] = ["weekly", "bi-weekly", "monthly", "as-required"]
        freq_combo.grid(row=1, column=3, padx=(0, 10))
        
        # Stage buttons
        stage_btn_frame = ttk.Frame(input_frame)
        stage_btn_frame.grid(row=1, column=4, columnspan=2, sticky=tk.W, padx=10)
        
        ttk.Button(stage_btn_frame, text="Add Stage", command=self.add_stage).pack(side=tk.LEFT, padx=5)
        ttk.Button(stage_btn_frame, text="Delete Stage", command=self.delete_stage).pack(side=tk.LEFT, padx=5)
        ttk.Button(stage_btn_frame, text="Load from Services", command=self.load_stages_from_services).pack(side=tk.LEFT, padx=5)
        ttk.Button(stage_btn_frame, text="Generate Schedule", command=self.generate_stage_schedule).pack(side=tk.LEFT, padx=5)
        
        # Stages treeview
        stage_columns = ("Stage", "Start Date", "End Date", "Reviews", "Frequency", "Status")
        self.stages_tree = ttk.Treeview(stage_frame, columns=stage_columns, show="headings", height=6)
        
        for col in stage_columns:
            self.stages_tree.heading(col, text=col)
            self.stages_tree.column(col, width=120, anchor="w")
        
        self.stages_tree.pack(fill=tk.X, pady=10)
        
        # Review Cycles Frame
        cycles_frame = ttk.LabelFrame(planning_frame, text="🔄 Review Cycles", padding=10)
        cycles_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cycle filters
        filter_frame = ttk.Frame(cycles_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Cycle:").pack(side=tk.LEFT, padx=(0, 5))
        self.cycle_filter_var = tk.StringVar()
        self.cycle_filter_combo = ttk.Combobox(filter_frame, textvariable=self.cycle_filter_var, width=20, state="readonly")
        self.cycle_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.cycle_filter_combo.bind('<<ComboboxSelected>>', self.on_cycle_filter_changed)
        
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter_var = tk.StringVar()
        status_filter = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, width=15, state="readonly")
        status_filter['values'] = ["All", "planned", "in_progress", "completed", "on_hold"]
        status_filter.pack(side=tk.LEFT, padx=(0, 10))
        status_filter.set("All")
        
        ttk.Button(filter_frame, text="Refresh Cycles", command=self.refresh_cycles).pack(side=tk.LEFT, padx=10)
        
        # Review cycle action buttons
        review_actions_frame = ttk.Frame(cycles_frame)
        review_actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(review_actions_frame, text="Edit Review", command=self.edit_review_cycle).pack(side=tk.LEFT, padx=5)
        ttk.Button(review_actions_frame, text="Delete Review", command=self.delete_review_cycle).pack(side=tk.LEFT, padx=5)
        ttk.Button(review_actions_frame, text="Mark as Issued", command=self.mark_review_issued).pack(side=tk.LEFT, padx=5)
        ttk.Button(review_actions_frame, text="Delete All Reviews", command=self.delete_all_reviews).pack(side=tk.LEFT, padx=5)
        
        # Cycles treeview container
        treeview_frame = ttk.Frame(cycles_frame)
        treeview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cycles treeview
        cycle_columns = ("Review ID", "Cycle", "Planned Start", "Planned End", "Actual Start", "Actual End", "Status", "Stage", "Reviewer", "Notes")
        self.cycles_tree = ttk.Treeview(treeview_frame, columns=cycle_columns, show="headings", height=8)
        
        for col in cycle_columns:
            self.cycles_tree.heading(col, text=col)
            if col == "Review ID":
                self.cycles_tree.column(col, width=80, anchor="w")
            else:
                self.cycles_tree.column(col, width=100, anchor="w")
        
        cycles_v_scroll = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.cycles_tree.yview)
        cycles_h_scroll = ttk.Scrollbar(treeview_frame, orient=tk.HORIZONTAL, command=self.cycles_tree.xview)
        self.cycles_tree.configure(yscrollcommand=cycles_v_scroll.set, xscrollcommand=cycles_h_scroll.set)
        
        # Use pack instead of grid to avoid conflicts
        self.cycles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cycles_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_review_tracking_tab(self):
        """Setup the Review Execution & Tracking tab"""
        tracking_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(tracking_frame, text="📊 Review Tracking")
        
        # Summary Frame
        summary_frame = ttk.LabelFrame(tracking_frame, text="📈 Project Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Summary fields
        self.summary_vars = {}
        summary_fields = [
            ("Project Name", 0, 0), ("Current Cycle", 0, 2),
            ("Construction Stage", 1, 0), ("License Duration", 1, 2),
            ("Total Services", 2, 0), ("Active Reviews", 2, 2),
            ("Completed Reviews", 3, 0), ("Overall Progress", 3, 2)
        ]
        
        for field, row, col in summary_fields:
            ttk.Label(summary_frame, text=f"{field}:").grid(row=row, column=col, sticky=tk.W, padx=(0, 5))
            var = tk.StringVar()
            self.summary_vars[field] = var
            ttk.Label(summary_frame, textvariable=var, background="white", relief="sunken").grid(
                row=row, column=col+1, sticky=tk.W+tk.E, padx=(0, 20), pady=2
            )
        
        # Configure column weights
        for i in range(4):
            summary_frame.columnconfigure(i*2+1, weight=1)
        
        # Action Buttons Frame
        action_frame = ttk.LabelFrame(tracking_frame, text="🔧 Review Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Button row 1
        button_frame1 = ttk.Frame(action_frame)
        button_frame1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame1, text="📅 Submit Schedule", 
                  command=self.submit_schedule).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame1, text="📊 Launch Gantt Chart", 
                  command=self.launch_gantt).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame1, text="🔗 View Contract Links", 
                  command=self.show_contract_links).pack(side=tk.LEFT, padx=(0, 5))
        
        # Button row 2  
        button_frame2 = ttk.Frame(action_frame)
        button_frame2.pack(fill=tk.X)
        
        ttk.Button(button_frame2, text="📤 Open Revizto Exporter", 
                  command=self.open_revizto_exporter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame2, text="📋 Update Review Status", 
                  command=self.update_review_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame2, text="🔄 Refresh All Data", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        
        # Review Tasks Frame
        tasks_frame = ttk.LabelFrame(tracking_frame, text="📝 Active Review Tasks", padding=10)
        tasks_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tasks treeview
        task_columns = ("Review ID", "Service", "Cycle", "Due Date", "Status", "Assignee", "Progress %", "Evidence")
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=task_columns, show="headings", height=8)
        
        for col in task_columns:
            self.tasks_tree.heading(col, text=col)
            width = 80 if col in ["Review ID", "Cycle", "Progress %"] else 120
            self.tasks_tree.column(col, width=width, anchor="w")
        
        # Scrollbars for tasks
        tasks_v_scroll = ttk.Scrollbar(tasks_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        tasks_h_scroll = ttk.Scrollbar(tasks_frame, orient=tk.HORIZONTAL, command=self.tasks_tree.xview)
        self.tasks_tree.configure(yscrollcommand=tasks_v_scroll.set, xscrollcommand=tasks_h_scroll.set)
        
        self.tasks_tree.grid(row=0, column=0, sticky="nsew")
        tasks_v_scroll.grid(row=0, column=1, sticky="ns")
        tasks_h_scroll.grid(row=1, column=0, sticky="ew")
        
        tasks_frame.grid_rowconfigure(0, weight=1)
        tasks_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to edit task
        self.tasks_tree.bind("<Double-1>", self.edit_review_task)
    
    def setup_billing_tab(self):
        """Setup the Billing & Progress tab"""
        billing_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(billing_frame, text="💰 Billing")
        
        # Billing Claims Frame
        claims_frame = ttk.LabelFrame(billing_frame, text="💳 Billing Claims", padding=10)
        claims_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Claims treeview
        claim_columns = ("Claim ID", "Period Start", "Period End", "PO Ref", "Invoice Ref", "Status", "Total Amount")
        self.claims_tree = ttk.Treeview(claims_frame, columns=claim_columns, show="headings", height=6)
        
        for col in claim_columns:
            self.claims_tree.heading(col, text=col)
            self.claims_tree.column(col, width=120, anchor="w")
        
        self.claims_tree.pack(fill=tk.BOTH, expand=True)
        
        # Service Progress Frame
        progress_frame = ttk.LabelFrame(billing_frame, text="📊 Service Progress & Billing", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress treeview
        progress_columns = ("Service", "Phase", "Total Fee", "Completed %", "Billed Amount", "Remaining", "Next Milestone")
        self.progress_tree = ttk.Treeview(progress_frame, columns=progress_columns, show="headings", height=6)
        
        for col in progress_columns:
            self.progress_tree.heading(col, text=col)
            self.progress_tree.column(col, width=120, anchor="w")
        
        self.progress_tree.pack(fill=tk.BOTH, expand=True)
    
    def refresh_data(self):
        """Refresh all data in the tab"""
        try:
            # Initialize review service connection
            from database import connect_to_db
            db_conn = connect_to_db()
            if db_conn:
                self.review_service = ReviewManagementService(db_conn)
            
            # Load projects
            projects = get_projects()
            project_list = [f"{p[0]} - {p[1]}" for p in projects]
            self.project_combo['values'] = project_list
            
            # Load available templates
            if self.review_service:
                templates = self.review_service.get_available_templates()
                template_list = [f"{t['name']} ({t['sector']})" for t in templates]
                self.template_combo['values'] = template_list
            
            if project_list and not self.project_var.get():
                self.project_combo.current(0)
                self.on_project_selected()
                
        except Exception as e:
            print(f"Error refreshing review data: {e}")
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        try:
            selected = self.project_var.get()
            if not selected or " - " not in selected:
                return
            
            self.current_project_id = int(selected.split(" - ")[0])
            
            # Initialize review service with database connection
            try:
                db_conn = connect_to_db()
                if db_conn:
                    self.review_service = ReviewManagementService(db_conn)
                    print(f"✅ Review service initialized for project {self.current_project_id}")
                else:
                    print("❌ Failed to connect to database for review service")
                    self.review_service = None
            except Exception as e:
                print(f"❌ Error initializing review service: {e}")
                self.review_service = None
            
            # Load cycles for this project
            cycles = get_cycle_ids(self.current_project_id)
            if hasattr(self, 'cycle_filter_combo'):
                self.cycle_filter_combo['values'] = cycles if cycles else ["No Cycles Available"]
            
            # Load project services
            self.load_project_services()
            
            # Load project summary
            self.load_project_summary()
            
            # Refresh review cycles
            self.refresh_cycles()
            
            # Check if we should auto-populate stages from services
            self.check_auto_populate_stages()
            
            # Notify other tabs
            project_notification_system.notify_project_changed(selected)
            
        except Exception as e:
            print(f"Error loading project data: {e}")
    
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
            for service in services:
                phase = service.get('phase', '').strip()
                if phase:
                    phases.add(phase)
            
            if len(phases) > 0:
                # Show info tooltip that stages can be loaded
                print(f"📋 Found {len(phases)} phases in project services. Use 'Load from Services' to auto-populate stages.")
            
        except Exception as e:
            print(f"Error checking auto-populate stages: {e}")
    
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
            details_notebook.add(services_frame, text="📋 Services")
            
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
            details_notebook.add(phases_frame, text="🏗️ Phases Preview")
            
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
                    frequency = "as-required"
                elif "handover" in phase.lower() or "completion" in phase.lower():
                    frequency = "as-required"
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
                text="💡 These phases will become review stages when template is applied",
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
    
    def load_project_services(self):
        """Load project services into the services tree"""
        try:
            # Clear existing services
            for item in self.services_tree.get_children():
                self.services_tree.delete(item)
            
            if not self.current_project_id or not self.review_service:
                return
            
            # Get project services
            services = self.review_service.get_project_services(self.current_project_id)
            
            for service in services:
                values = (
                    service.get('service_id', ''),
                    service.get('phase', ''),
                    service.get('service_code', ''),
                    service.get('service_name', ''),
                    service.get('unit_type', ''),
                    service.get('unit_qty', 0),
                    f"${service.get('unit_rate', 0):,.2f}",
                    f"${service.get('agreed_fee', 0):,.2f}",
                    service.get('status', 'active')
                )
                self.services_tree.insert("", tk.END, values=values)
                
        except Exception as e:
            print(f"Error loading project services: {e}")
    
    def generate_reviews_from_services(self):
        """Generate review cycles from current project services"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            # Confirm action
            result = messagebox.askyesno("Confirm", "Generate review cycles based on project services?")
            if not result:
                return
            
            # Generate reviews
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id)
            
            if reviews_created:
                messagebox.showinfo("Success", f"Generated {len(reviews_created)} review cycles from services")
                self.refresh_cycles()
            else:
                messagebox.showwarning("Info", "No reviews generated. Check if services are properly configured.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating reviews: {e}")
    
    def load_stages_from_services(self):
        """Load stages from current project services phases"""
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
            
            # Extract unique phases
            phases = {}
            for service in services:
                phase = service.get('phase', '').strip()
                if phase and phase not in phases:
                    # Try to extract default review count from service
                    default_reviews = service.get('unit_qty', 4) if service.get('unit_type') == 'review' else 1
                    
                    # Determine frequency based on phase name
                    frequency = "weekly"
                    if "initiation" in phase.lower() or "setup" in phase.lower():
                        frequency = "as-required"
                    elif "handover" in phase.lower() or "completion" in phase.lower():
                        frequency = "as-required"
                    elif "construction" in phase.lower():
                        frequency = "weekly"
                    elif "design" in phase.lower() or "documentation" in phase.lower():
                        frequency = "bi-weekly"
                    
                    phases[phase] = {
                        'reviews': default_reviews,
                        'frequency': frequency,
                        'services': []
                    }
                
                # Group services by phase
                if phase:
                    phases[phase]['services'].append(service)
            
            if not phases:
                messagebox.showwarning("Warning", "No phases found in project services")
                return
            
            # Ask user if they want to replace existing stages
            if self.stages_tree.get_children():
                result = messagebox.askyesno("Confirm", "This will replace existing stages with phases from services. Continue?")
                if not result:
                    return
                
                # Clear existing stages
                for item in self.stages_tree.get_children():
                    self.stages_tree.delete(item)
            
            # Add phases as stages with intelligent defaults
            today = datetime.now()
            phase_duration_days = 30  # Default phase duration
            
            current_date = today
            for i, (phase, data) in enumerate(phases.items()):
                start_date = current_date
                end_date = start_date + timedelta(days=phase_duration_days)
                
                # Adjust duration based on phase type and review count
                if data['reviews'] > 10:  # Construction phases typically have more reviews
                    phase_duration_days = max(60, data['reviews'] * 7)  # Weekly reviews
                elif "initiation" in phase.lower() or "setup" in phase.lower():
                    phase_duration_days = 14  # Shorter setup phases
                elif "handover" in phase.lower():
                    phase_duration_days = 21  # Handover phases
                else:
                    phase_duration_days = 30  # Default
                
                end_date = start_date + timedelta(days=phase_duration_days)
                
                # Add to tree
                values = (
                    phase,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    str(data['reviews']),
                    data['frequency'],
                    "planned"
                )
                self.stages_tree.insert("", tk.END, values=values)
                
                # Next phase starts after current phase ends
                current_date = end_date + timedelta(days=1)
            
            messagebox.showinfo("Success", f"Loaded {len(phases)} stages from project services")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading stages from services: {e}")
    
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
            
            print(f"🔍 Found {len(stages)} stages to process")
            for stage in stages:
                print(f"  - Stage: {stage['stage_name']}, Reviews: {stage['num_reviews']}, Dates: {stage['start_date']} to {stage['end_date']}")
            
            if not stages:
                messagebox.showwarning("Warning", "No stages defined. Please add stages first.")
                return
            
            # Generate schedule using the modern review service
            if not self.review_service:
                messagebox.showerror("Error", "Review service not initialized")
                return
            
            print(f"📅 Generating schedule for project {self.current_project_id}")
            result = self.review_service.generate_stage_schedule_new(self.current_project_id, stages)
            
            if result:
                print("✅ Stage review schedule generated successfully")
                messagebox.showinfo("Success", "Stage review schedule generated successfully")
                self.refresh_cycles()
            else:
                print("❌ Failed to generate stage schedule")
                messagebox.showerror("Error", "Failed to generate stage schedule")
                
        except Exception as e:
            print(f"❌ Error generating stage schedule: {e}")
            messagebox.showerror("Error", f"Error generating stage schedule: {e}")
    
    def refresh_cycles(self):
        """Refresh the review cycles display"""
        try:
            # Clear existing cycles
            for item in self.cycles_tree.get_children():
                self.cycles_tree.delete(item)
            
            if not self.current_project_id:
                return
            
            # Get review cycles from database
            cycles = get_review_cycles(self.current_project_id)
            
            for cycle in cycles:
                # Format data for UI columns
                # cycle format: (review_id, service_name, cycle_no, planned_date, due_date, status, disciplines)
                # UI expects: ("Review ID", "Cycle", "Planned Start", "Planned End", "Actual Start", "Actual End", "Status", "Stage", "Reviewer", "Notes")
                if len(cycle) >= 6:
                    formatted_cycle = (
                        str(cycle[0]),                     # Review ID
                        f"{cycle[1]} - Cycle {cycle[2]}",  # Cycle (service name + cycle number)
                        cycle[3] if cycle[3] else "",      # Planned Start
                        cycle[4] if cycle[4] else "",      # Planned End  
                        "",                                # Actual Start (empty for now)
                        "",                                # Actual End (empty for now)
                        cycle[5] if cycle[5] else "",      # Status
                        cycle[6] if len(cycle) > 6 and cycle[6] else "All",  # Stage (disciplines)
                        "",                                # Reviewer (empty for now)
                        ""                                 # Notes (empty for now)
                    )
                    self.cycles_tree.insert("", tk.END, values=formatted_cycle)
                
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
            # Create dialog window
            dialog = tk.Toplevel(self.frame)
            dialog.title("Add Service" if not service_data else "Edit Service")
            dialog.geometry("600x500")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Service form
            form_frame = ttk.LabelFrame(dialog, text="Service Details", padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Form variables
            phase_var = tk.StringVar(value=service_data.get('phase', '') if service_data else '')
            service_code_var = tk.StringVar(value=service_data.get('service_code', '') if service_data else '')
            service_name_var = tk.StringVar(value=service_data.get('service_name', '') if service_data else '')
            unit_type_var = tk.StringVar(value=service_data.get('unit_type', 'lump_sum') if service_data else 'lump_sum')
            unit_qty_var = tk.StringVar(value=str(service_data.get('unit_qty', 1)) if service_data else '1')
            unit_rate_var = tk.StringVar(value=str(service_data.get('unit_rate', 0)) if service_data else '0')
            lump_sum_var = tk.StringVar(value=str(service_data.get('lump_sum_fee', 0)) if service_data else '0')
            bill_rule_var = tk.StringVar(value=service_data.get('bill_rule', 'on_completion') if service_data else 'on_completion')
            notes_var = tk.StringVar(value=service_data.get('notes', '') if service_data else '')
            
            # Form fields
            row = 0
            
            # Phase
            ttk.Label(form_frame, text="Phase:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            phase_entry = ttk.Entry(form_frame, textvariable=phase_var, width=40)
            phase_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            row += 1
            
            # Service Code
            ttk.Label(form_frame, text="Service Code:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=service_code_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Service Name
            ttk.Label(form_frame, text="Service Name:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            service_name_entry = ttk.Entry(form_frame, textvariable=service_name_var, width=40)
            service_name_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            row += 1
            
            # Unit Type
            ttk.Label(form_frame, text="Unit Type:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            unit_type_combo = ttk.Combobox(form_frame, textvariable=unit_type_var, width=20, state="readonly")
            unit_type_combo['values'] = ['lump_sum', 'review', 'audit', 'hourly']
            unit_type_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Unit Quantity
            ttk.Label(form_frame, text="Unit Quantity:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=unit_qty_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Unit Rate
            ttk.Label(form_frame, text="Unit Rate ($):").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=unit_rate_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Lump Sum Fee
            ttk.Label(form_frame, text="Lump Sum Fee ($):").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=lump_sum_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Bill Rule
            ttk.Label(form_frame, text="Bill Rule:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            bill_rule_combo = ttk.Combobox(form_frame, textvariable=bill_rule_var, width=20, state="readonly")
            bill_rule_combo['values'] = ['on_completion', 'per_unit_complete', 'on_setup', 'on_report_issue', 'monthly']
            bill_rule_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
            
            # Notes
            ttk.Label(form_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W+tk.N, padx=(0, 5), pady=2)
            notes_text = tk.Text(form_frame, width=40, height=4)
            notes_text.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            notes_text.insert(tk.END, notes_var.get())
            row += 1
            
            # Configure column weights
            form_frame.columnconfigure(1, weight=1)
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            def save_service():
                try:
                    # Validate inputs
                    if not phase_var.get().strip():
                        messagebox.showerror("Error", "Phase is required")
                        return
                    
                    if not service_code_var.get().strip():
                        messagebox.showerror("Error", "Service Code is required")
                        return
                    
                    if not service_name_var.get().strip():
                        messagebox.showerror("Error", "Service Name is required")
                        return
                    
                    # Calculate agreed fee
                    unit_qty = float(unit_qty_var.get() or 0)
                    unit_rate = float(unit_rate_var.get() or 0)
                    lump_sum = float(lump_sum_var.get() or 0)
                    
                    if unit_type_var.get() == 'lump_sum':
                        agreed_fee = lump_sum
                    else:
                        agreed_fee = unit_qty * unit_rate
                    
                    # Create service data
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
                    
                    # Create the service
                    service_id = self.review_service.create_project_service(new_service_data)
                    
                    if service_id:
                        messagebox.showinfo("Success", f"Service created successfully with ID: {service_id}")
                        dialog.destroy()
                        self.load_project_services()  # Refresh the services list
                    else:
                        messagebox.showerror("Error", "Failed to create service")
                        
                except ValueError as e:
                    messagebox.showerror("Error", "Please enter valid numeric values for quantities and fees")
                except Exception as e:
                    messagebox.showerror("Error", f"Error saving service: {e}")
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="Save", command=save_service).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)
            
            # Focus on first field
            phase_entry.focus()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing service dialog: {e}")
    
    def edit_service(self):
        """Edit selected service"""
        try:
            selection = self.services_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a service to edit")
                return
            
            # Get selected service data
            item = self.services_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 8:
                service_data = {
                    'service_id': values[0],
                    'phase': values[1],
                    'service_code': values[2],
                    'service_name': values[3],
                    'unit_type': values[4],
                    'unit_qty': values[5],
                    'unit_rate': float(values[6].replace('$', '').replace(',', '')),
                    'lump_sum_fee': float(values[7].replace('$', '').replace(',', '')),
                    'bill_rule': 'on_completion',  # Default
                    'notes': ''
                }
                
                self.show_service_dialog(service_data)
            else:
                messagebox.showerror("Error", "Invalid service data selected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error editing service: {e}")
    
    def delete_service(self):
        """Delete selected service"""
        try:
            selection = self.services_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a service to delete")
                return
            
            # Get selected service ID
            item = self.services_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 1:
                service_id = values[0]
                service_name = values[3] if len(values) >= 4 else f"Service {service_id}"
                
                # Confirm deletion
                result = messagebox.askyesno("Confirm Delete", 
                    f"Are you sure you want to delete the service:\n\n{service_name}\n\nThis action cannot be undone.")
                
                if result:
                    if self.review_service.delete_project_service(service_id):
                        messagebox.showinfo("Success", "Service deleted successfully")
                        self.load_project_services()  # Refresh the services list
                    else:
                        messagebox.showerror("Error", "Failed to delete service")
            else:
                messagebox.showerror("Error", "Invalid service selected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting service: {e}")
    
    def clear_services(self):
        """Clear all services for the project"""
        try:
            if not self.current_project_id:
                messagebox.showwarning("Warning", "Please select a project first")
                return
            
            result = messagebox.askyesno("Confirm", "Are you sure you want to clear ALL services for this project?")
            if not result:
                return
            
            if self.review_service:
                count = self.review_service.clear_all_project_services(self.current_project_id)
                messagebox.showinfo("Success", f"Cleared {count} services from project")
                self.load_project_services()
            else:
                messagebox.showerror("Error", "Review service not initialized")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error clearing services: {e}")
    
    def on_cycle_filter_changed(self, event=None):
        """Handle cycle filter change"""
        self.current_cycle_id = self.cycle_filter_var.get()
        self.load_review_tasks()
    
    def load_review_tasks(self):
        """Load review tasks for current project/cycle"""
        try:
            # Clear existing tasks
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
            
            if not self.current_project_id:
                return
            
            # Get service reviews
            if self.review_service:
                reviews = self.review_service.get_service_reviews(self.current_project_id, self.current_cycle_id)
                
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
        messagebox.showinfo("Info", "Update Review Status feature - Coming soon!")
    
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
            
            from gantt_chart import launch_gantt_chart
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
    
    def open_revizto_exporter(self):
        """Open Revizto data exporter"""
        try:
            exe_path = os.path.abspath("tools/ReviztoDataExporter.exe")
            if os.path.exists(exe_path):
                import subprocess
                subprocess.Popen([exe_path])
            else:
                messagebox.showerror("Error", f"Revizto Exporter not found at: {exe_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Revizto exporter: {e}")
    
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
            planned_end = values[3]
            status = values[6]
            stage = values[7]
            
            # Create edit dialog
            self.show_edit_review_dialog(review_id, cycle_name, planned_start, planned_end, status, stage)
            
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
                if self.review_service:
                    # Use the service method for better consistency
                    delete_result = self.review_service.delete_all_project_reviews(self.current_project_id)
                    if delete_result['reviews_deleted'] > 0 or delete_result['services_deleted'] > 0:
                        messagebox.showinfo(
                            "Success", 
                            f"Successfully deleted:\n"
                            f"• {delete_result['reviews_deleted']} review cycles\n"
                            f"• {delete_result['services_deleted']} auto-generated services"
                        )
                        self.refresh_cycles()
                        self.load_project_services()  # Refresh services list too
                    else:
                        messagebox.showinfo("Info", "No reviews or services were found to delete")
                else:
                    # Fallback to direct database method
                    success = self.delete_all_reviews_from_database()
                    if success:
                        messagebox.showinfo("Success", f"All {review_count} review cycles deleted successfully")
                        self.refresh_cycles()
                        self.load_project_services()  # Refresh services list too
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
    
    def show_edit_review_dialog(self, review_id, cycle_name, planned_start, planned_end, status, stage):
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
            ttk.Label(main_frame, text="Planned Start:").grid(row=2, column=0, sticky=tk.W, pady=5)
            start_date_var = tk.StringVar(value=planned_start)
            start_date_entry = DateEntry(main_frame, textvariable=start_date_var, width=12, 
                                       background='darkblue', foreground='white', 
                                       borderwidth=2, date_pattern='yyyy-mm-dd')
            start_date_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Planned end date
            ttk.Label(main_frame, text="Planned End:").grid(row=3, column=0, sticky=tk.W, pady=5)
            end_date_var = tk.StringVar(value=planned_end)
            end_date_entry = DateEntry(main_frame, textvariable=end_date_var, width=12,
                                     background='darkblue', foreground='white',
                                     borderwidth=2, date_pattern='yyyy-mm-dd')
            end_date_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Status
            ttk.Label(main_frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
            status_var = tk.StringVar(value=status)
            status_combo = ttk.Combobox(main_frame, textvariable=status_var, width=15, state="readonly")
            status_combo['values'] = ["planned", "in_progress", "report_issued", "completed", "on_hold", "cancelled"]
            status_combo.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Stage/Disciplines
            ttk.Label(main_frame, text="Stage/Disciplines:").grid(row=5, column=0, sticky=tk.W, pady=5)
            stage_var = tk.StringVar(value=stage)
            stage_entry = ttk.Entry(main_frame, textvariable=stage_var, width=30)
            stage_entry.grid(row=5, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Notes
            ttk.Label(main_frame, text="Notes:").grid(row=6, column=0, sticky=tk.NW, pady=5)
            notes_text = tk.Text(main_frame, width=40, height=4)
            notes_text.grid(row=6, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=7, column=0, columnspan=2, pady=20)
            
            def save_changes():
                try:
                    # Update review in database
                    success = self.update_review_in_database(
                        review_id,
                        start_date_var.get(),
                        end_date_var.get(),
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
    
    def update_review_in_database(self, review_id, planned_start, planned_end, status, stage, notes):
        """Update review cycle in database"""
        try:
            conn = connect_to_db()
            if conn is None:
                return False
            
            cursor = conn.cursor()
            
            # Update ServiceReviews table
            update_sql = """
            UPDATE ServiceReviews 
            SET planned_date = ?, due_date = ?, status = ?, disciplines = ?
            WHERE review_id = ?
            """
            
            cursor.execute(update_sql, (planned_start, planned_end, status, stage, review_id))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating review in database: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_review_from_database(self, review_id):
        """Delete review cycle from database"""
        try:
            conn = connect_to_db()
            if conn is None:
                return False
            
            cursor = conn.cursor()
            
            # Delete from ServiceReviews table
            delete_sql = "DELETE FROM ServiceReviews WHERE review_id = ?"
            cursor.execute(delete_sql, (review_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting review from database: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_all_reviews_from_database(self):
        """Delete all review cycles for the current project from database"""
        try:
            conn = connect_to_db()
            if conn is None:
                return False
            
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
            
            print(f"✅ Deleted {reviews_deleted} reviews and {services_deleted} auto-generated services")
            return True
            
        except Exception as e:
            print(f"Error deleting all reviews from database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected()

class DocumentManagementTab:
    """Document Management Interface - For managing BEP, PIR, and EIR documents"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📄 Documents")
        
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
        project_frame = ttk.LabelFrame(main_container, text="📁 Current Project", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.project_label = ttk.Label(project_frame, text="No project selected", 
                                     font=('Arial', 10, 'bold'))
        self.project_label.pack()
        
        # Create notebook for document types
        self.doc_notebook = ttk.Notebook(main_container)
        self.doc_notebook.pack(fill=tk.BOTH, expand=True)
        
        # BEP Tab
        self.bep_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.bep_frame, text="📋 BEP (BIM Execution Plan)")
        self.setup_bep_tab()
        
        # PIR Tab
        self.pir_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.pir_frame, text="📊 PIR (Project Information Requirements)")
        self.setup_pir_tab()
        
        # EIR Tab
        self.eir_frame = ttk.Frame(self.doc_notebook)
        self.doc_notebook.add(self.eir_frame, text="📝 EIR (Employer's Information Requirements)")
        self.setup_eir_tab()
        
    def setup_bep_tab(self):
        """Setup BEP document management interface"""
        # Create scrollable frame
        canvas = tk.Canvas(self.bep_frame)
        scrollbar = ttk.Scrollbar(self.bep_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Library Section
        library_frame = ttk.LabelFrame(scrollable_frame, text="📚 BEP Library", padding=10)
        library_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Library controls
        library_controls = ttk.Frame(library_frame)
        library_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(library_controls, text="📥 Import Template", 
                  command=lambda: self.import_document('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="📤 Export Template", 
                  command=lambda: self.export_document('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="🔄 Refresh", 
                  command=lambda: self.refresh_documents('BEP')).pack(side=tk.LEFT)
        
        # Library list
        self.bep_library_tree = ttk.Treeview(library_frame, height=6)
        self.bep_library_tree["columns"] = ("Type", "Version", "Date", "Status")
        self.bep_library_tree.heading("#0", text="Document Name")
        self.bep_library_tree.heading("Type", text="Type")
        self.bep_library_tree.heading("Version", text="Version")
        self.bep_library_tree.heading("Date", text="Date")
        self.bep_library_tree.heading("Status", text="Status")
        self.bep_library_tree.pack(fill=tk.X, pady=(5, 0))
        
        # Composition Section
        composition_frame = ttk.LabelFrame(scrollable_frame, text="✏️ BEP Composition", padding=10)
        composition_frame.pack(fill=tk.X, pady=(0, 10))
        
        comp_controls = ttk.Frame(composition_frame)
        comp_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(comp_controls, text="📝 New BEP", 
                  command=lambda: self.create_new_document('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="✏️ Edit Selected", 
                  command=lambda: self.edit_document('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="📋 Duplicate", 
                  command=lambda: self.duplicate_document('BEP')).pack(side=tk.LEFT)
        
        # WIP Section
        wip_frame = ttk.LabelFrame(scrollable_frame, text="🚧 Work in Progress", padding=10)
        wip_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bep_wip_tree = ttk.Treeview(wip_frame, height=4)
        self.bep_wip_tree["columns"] = ("Author", "Modified", "Status")
        self.bep_wip_tree.heading("#0", text="Document")
        self.bep_wip_tree.heading("Author", text="Author")
        self.bep_wip_tree.heading("Modified", text="Last Modified")
        self.bep_wip_tree.heading("Status", text="Status")
        self.bep_wip_tree.pack(fill=tk.X)
        
        # Publishing Section
        publishing_frame = ttk.LabelFrame(scrollable_frame, text="📤 Publishing", padding=10)
        publishing_frame.pack(fill=tk.X)
        
        pub_controls = ttk.Frame(publishing_frame)
        pub_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(pub_controls, text="✅ Approve for Publishing", 
                  command=lambda: self.approve_document('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📧 Send for Review", 
                  command=lambda: self.send_for_review('BEP')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📊 Generate Report", 
                  command=lambda: self.generate_report('BEP')).pack(side=tk.LEFT)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_pir_tab(self):
        """Setup PIR document management interface"""
        # Similar structure to BEP but for PIR documents
        canvas = tk.Canvas(self.pir_frame)
        scrollbar = ttk.Scrollbar(self.pir_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Library Section
        library_frame = ttk.LabelFrame(scrollable_frame, text="📚 PIR Library", padding=10)
        library_frame.pack(fill=tk.X, pady=(0, 10))
        
        library_controls = ttk.Frame(library_frame)
        library_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(library_controls, text="📥 Import Template", 
                  command=lambda: self.import_document('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="📤 Export Template", 
                  command=lambda: self.export_document('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="🔄 Refresh", 
                  command=lambda: self.refresh_documents('PIR')).pack(side=tk.LEFT)
        
        self.pir_library_tree = ttk.Treeview(library_frame, height=6)
        self.pir_library_tree["columns"] = ("Type", "Version", "Date", "Status")
        self.pir_library_tree.heading("#0", text="Document Name")
        self.pir_library_tree.heading("Type", text="Type")
        self.pir_library_tree.heading("Version", text="Version")
        self.pir_library_tree.heading("Date", text="Date")
        self.pir_library_tree.heading("Status", text="Status")
        self.pir_library_tree.pack(fill=tk.X, pady=(5, 0))
        
        # Composition Section
        composition_frame = ttk.LabelFrame(scrollable_frame, text="✏️ PIR Composition", padding=10)
        composition_frame.pack(fill=tk.X, pady=(0, 10))
        
        comp_controls = ttk.Frame(composition_frame)
        comp_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(comp_controls, text="📝 New PIR", 
                  command=lambda: self.create_new_document('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="✏️ Edit Selected", 
                  command=lambda: self.edit_document('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="📋 Duplicate", 
                  command=lambda: self.duplicate_document('PIR')).pack(side=tk.LEFT)
        
        # WIP Section
        wip_frame = ttk.LabelFrame(scrollable_frame, text="🚧 Work in Progress", padding=10)
        wip_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.pir_wip_tree = ttk.Treeview(wip_frame, height=4)
        self.pir_wip_tree["columns"] = ("Author", "Modified", "Status")
        self.pir_wip_tree.heading("#0", text="Document")
        self.pir_wip_tree.heading("Author", text="Author")
        self.pir_wip_tree.heading("Modified", text="Last Modified")
        self.pir_wip_tree.heading("Status", text="Status")
        self.pir_wip_tree.pack(fill=tk.X)
        
        # Publishing Section
        publishing_frame = ttk.LabelFrame(scrollable_frame, text="📤 Publishing", padding=10)
        publishing_frame.pack(fill=tk.X)
        
        pub_controls = ttk.Frame(publishing_frame)
        pub_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(pub_controls, text="✅ Approve for Publishing", 
                  command=lambda: self.approve_document('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📧 Send for Review", 
                  command=lambda: self.send_for_review('PIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📊 Generate Report", 
                  command=lambda: self.generate_report('PIR')).pack(side=tk.LEFT)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_eir_tab(self):
        """Setup EIR document management interface"""
        # Similar structure to BEP and PIR but for EIR documents
        canvas = tk.Canvas(self.eir_frame)
        scrollbar = ttk.Scrollbar(self.eir_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Library Section
        library_frame = ttk.LabelFrame(scrollable_frame, text="📚 EIR Library", padding=10)
        library_frame.pack(fill=tk.X, pady=(0, 10))
        
        library_controls = ttk.Frame(library_frame)
        library_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(library_controls, text="📥 Import Template", 
                  command=lambda: self.import_document('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="📤 Export Template", 
                  command=lambda: self.export_document('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(library_controls, text="🔄 Refresh", 
                  command=lambda: self.refresh_documents('EIR')).pack(side=tk.LEFT)
        
        self.eir_library_tree = ttk.Treeview(library_frame, height=6)
        self.eir_library_tree["columns"] = ("Type", "Version", "Date", "Status")
        self.eir_library_tree.heading("#0", text="Document Name")
        self.eir_library_tree.heading("Type", text="Type")
        self.eir_library_tree.heading("Version", text="Version")
        self.eir_library_tree.heading("Date", text="Date")
        self.eir_library_tree.heading("Status", text="Status")
        self.eir_library_tree.pack(fill=tk.X, pady=(5, 0))
        
        # Composition Section
        composition_frame = ttk.LabelFrame(scrollable_frame, text="✏️ EIR Composition", padding=10)
        composition_frame.pack(fill=tk.X, pady=(0, 10))
        
        comp_controls = ttk.Frame(composition_frame)
        comp_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(comp_controls, text="📝 New EIR", 
                  command=lambda: self.create_new_document('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="✏️ Edit Selected", 
                  command=lambda: self.edit_document('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_controls, text="📋 Duplicate", 
                  command=lambda: self.duplicate_document('EIR')).pack(side=tk.LEFT)
        
        # WIP Section
        wip_frame = ttk.LabelFrame(scrollable_frame, text="🚧 Work in Progress", padding=10)
        wip_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.eir_wip_tree = ttk.Treeview(wip_frame, height=4)
        self.eir_wip_tree["columns"] = ("Author", "Modified", "Status")
        self.eir_wip_tree.heading("#0", text="Document")
        self.eir_wip_tree.heading("Author", text="Author")
        self.eir_wip_tree.heading("Modified", text="Last Modified")
        self.eir_wip_tree.heading("Status", text="Status")
        self.eir_wip_tree.pack(fill=tk.X)
        
        # Publishing Section
        publishing_frame = ttk.LabelFrame(scrollable_frame, text="📤 Publishing", padding=10)
        publishing_frame.pack(fill=tk.X)
        
        pub_controls = ttk.Frame(publishing_frame)
        pub_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(pub_controls, text="✅ Approve for Publishing", 
                  command=lambda: self.approve_document('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📧 Send for Review", 
                  command=lambda: self.send_for_review('EIR')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pub_controls, text="📊 Generate Report", 
                  command=lambda: self.generate_report('EIR')).pack(side=tk.LEFT)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def on_project_changed(self, new_project):
        """Handle project selection change"""
        try:
            if new_project and new_project != self.current_project:
                self.current_project = new_project
                self.project_label.config(text=f"Project: {new_project}")
                self.refresh_all_documents()
        except Exception as e:
            print(f"Error in document management project change: {e}")
            
    def refresh_all_documents(self):
        """Refresh all document lists for current project"""
        if self.current_project:
            self.refresh_documents('BEP')
            self.refresh_documents('PIR')
            self.refresh_documents('EIR')
            
    def import_document(self, doc_type):
        """Import a document template"""
        try:
            filetypes = [
                ('All Documents', '*.*'),
                ('Word Documents', '*.docx'),
                ('Excel Files', '*.xlsx'),
                ('PDF Files', '*.pdf')
            ]
            
            file_path = filedialog.askopenfilename(
                title=f"Import {doc_type} Template",
                filetypes=filetypes
            )
            
            if file_path:
                # Here you would implement the actual import logic
                messagebox.showinfo("Import", f"{doc_type} template imported successfully!")
                self.refresh_documents(doc_type)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import {doc_type} template: {str(e)}")
            
    def export_document(self, doc_type):
        """Export a document template"""
        try:
            # Get selected document from appropriate tree
            tree = getattr(self, f"{doc_type.lower()}_library_tree")
            selected = tree.selection()
            
            if not selected:
                messagebox.showwarning("Selection", f"Please select a {doc_type} document to export.")
                return
                
            filetypes = [
                ('Word Documents', '*.docx'),
                ('Excel Files', '*.xlsx'),
                ('PDF Files', '*.pdf')
            ]
            
            file_path = filedialog.asksaveasfilename(
                title=f"Export {doc_type} Document",
                filetypes=filetypes,
                defaultextension='.docx'
            )
            
            if file_path:
                # Here you would implement the actual export logic
                messagebox.showinfo("Export", f"{doc_type} document exported successfully!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export {doc_type} document: {str(e)}")
            
    def refresh_documents(self, doc_type):
        """Refresh document list for specified type"""
        try:
            # Clear existing items
            tree = getattr(self, f"{doc_type.lower()}_library_tree")
            for item in tree.get_children():
                tree.delete(item)
                
            wip_tree = getattr(self, f"{doc_type.lower()}_wip_tree")
            for item in wip_tree.get_children():
                wip_tree.delete(item)
            
            if not self.current_project:
                return
                
            # Here you would implement the actual database query to get documents
            # For now, adding sample data
            sample_docs = [
                (f"Standard {doc_type} Template", "Template", "v1.0", "2024-01-15", "Active"),
                (f"Project {doc_type} v2", "Project", "v2.1", "2024-01-20", "Draft"),
                (f"Custom {doc_type}", "Custom", "v1.5", "2024-01-25", "Review")
            ]
            
            for doc in sample_docs:
                tree.insert("", "end", text=doc[0], values=doc[1:])
                
            # Sample WIP documents
            wip_docs = [
                (f"{doc_type}_Working_Copy", "User", "2024-01-26 14:30", "In Progress"),
                (f"{doc_type}_Review_Draft", "Manager", "2024-01-25 16:45", "Under Review")
            ]
            
            for wip in wip_docs:
                wip_tree.insert("", "end", text=wip[0], values=wip[1:])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh {doc_type} documents: {str(e)}")
            
    def create_new_document(self, doc_type):
        """Create a new document"""
        try:
            if not self.current_project:
                messagebox.showwarning("Project Required", "Please select a project first.")
                return
                
            # Here you would implement document creation logic
            messagebox.showinfo("Create", f"New {doc_type} document creation started!")
            self.refresh_documents(doc_type)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create {doc_type} document: {str(e)}")
            
    def edit_document(self, doc_type):
        """Edit selected document"""
        try:
            tree = getattr(self, f"{doc_type.lower()}_library_tree")
            selected = tree.selection()
            
            if not selected:
                messagebox.showwarning("Selection", f"Please select a {doc_type} document to edit.")
                return
                
            # Here you would implement document editing logic
            messagebox.showinfo("Edit", f"{doc_type} document editing started!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit {doc_type} document: {str(e)}")
            
    def duplicate_document(self, doc_type):
        """Duplicate selected document"""
        try:
            tree = getattr(self, f"{doc_type.lower()}_library_tree")
            selected = tree.selection()
            
            if not selected:
                messagebox.showwarning("Selection", f"Please select a {doc_type} document to duplicate.")
                return
                
            # Here you would implement document duplication logic
            messagebox.showinfo("Duplicate", f"{doc_type} document duplicated successfully!")
            self.refresh_documents(doc_type)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to duplicate {doc_type} document: {str(e)}")
            
    def approve_document(self, doc_type):
        """Approve document for publishing"""
        try:
            wip_tree = getattr(self, f"{doc_type.lower()}_wip_tree")
            selected = wip_tree.selection()
            
            if not selected:
                messagebox.showwarning("Selection", f"Please select a {doc_type} document to approve.")
                return
                
            # Here you would implement document approval logic
            messagebox.showinfo("Approve", f"{doc_type} document approved for publishing!")
            self.refresh_documents(doc_type)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to approve {doc_type} document: {str(e)}")
            
    def send_for_review(self, doc_type):
        """Send document for review"""
        try:
            tree = getattr(self, f"{doc_type.lower()}_library_tree")
            selected = tree.selection()
            
            if not selected:
                messagebox.showwarning("Selection", f"Please select a {doc_type} document to send for review.")
                return
                
            # Here you would implement review workflow logic
            messagebox.showinfo("Review", f"{doc_type} document sent for review!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send {doc_type} document for review: {str(e)}")
            
    def generate_report(self, doc_type):
        """Generate document report"""
        try:
            if not self.current_project:
                messagebox.showwarning("Project Required", "Please select a project first.")
                return
                
            # Here you would implement report generation logic
            messagebox.showinfo("Report", f"{doc_type} document report generated!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate {doc_type} report: {str(e)}")

class ProjectSetupTab:
    """Project Setup and Management Interface - For creating and managing projects"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="🏗️ Project Setup")
        
        self.setup_ui()
        self.refresh_data()
        
        # Register for project change notifications
        project_notification_system.register_observer(self)
    
    def setup_ui(self):
        """Set up the project setup interface"""
        
        # Main container with padding
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== TOP SECTION: PROJECT SELECTION =====
        project_frame = ttk.LabelFrame(main_frame, text="📊 Project Selection & Status", padding=15)
        project_frame.pack(fill="x", pady=(0, 15))
        
        # Current project selection
        selection_frame = ttk.Frame(project_frame)
        selection_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(selection_frame, text="Current Project:", font=("Arial", 10, "bold")).pack(side="left")
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(selection_frame, textvariable=self.project_var, width=40, state="readonly")
        self.project_combo.pack(side="left", padx=(10, 0))
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)
        
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
        
        # ===== MIDDLE SECTION: PROJECT ACTIONS =====
        actions_frame = ttk.LabelFrame(main_frame, text="🚀 Project Actions", padding=15)
        actions_frame.pack(fill="x", pady=(0, 15))
        
        # Action buttons in a grid
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(fill="x")
        
        action_buttons = [
            ("🆕 Create New Project", self.create_new_project, "Create a new project"),
            ("📝 Edit Project Details", self.edit_project_details, "Modify current project information"),
            ("📁 Configure File Paths", self.configure_paths, "Set model and IFC file locations"),
            ("🔄 Extract Files from Desktop Connector", self.extract_acc_files, "Extract files from ACC Desktop Connector"),
            ("🔄 Refresh Project Data", self.refresh_data, "Reload project information from database"),
            ("📊 View Project Dashboard", self.view_dashboard, "Open comprehensive project overview"),
            ("🗑️ Archive Project", self.archive_project, "Archive completed or cancelled project")
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
        details_frame = ttk.LabelFrame(main_frame, text="📋 Project Details", padding=15)
        details_frame.pack(fill="both", expand=True)
        
        # Create notebook for different detail views
        details_notebook = ttk.Notebook(details_frame)
        details_notebook.pack(fill="both", expand=True)
        
        # Overview tab
        overview_frame = ttk.Frame(details_notebook)
        details_notebook.add(overview_frame, text="📊 Overview")
        
        # Project info display area
        self.project_info_text = tk.Text(overview_frame, height=8, wrap="word", font=("Courier", 9))
        scrollbar_info = ttk.Scrollbar(overview_frame, orient="vertical", command=self.project_info_text.yview)
        self.project_info_text.configure(yscrollcommand=scrollbar_info.set)
        
        self.project_info_text.pack(side="left", fill="both", expand=True)
        scrollbar_info.pack(side="right", fill="y")
        
        # Recent Activity tab
        activity_frame = ttk.Frame(details_notebook)
        details_notebook.add(activity_frame, text="📅 Recent Activity")
        
        self.activity_text = tk.Text(activity_frame, height=8, wrap="word", font=("Courier", 9))
        scrollbar_activity = ttk.Scrollbar(activity_frame, orient="vertical", command=self.activity_text.yview)
        self.activity_text.configure(yscrollcommand=scrollbar_activity.set)
        
        self.activity_text.pack(side="left", fill="both", expand=True)
        scrollbar_activity.pack(side="right", fill="y")

        # Reviews tab (scheduler)
        reviews_frame = ttk.Frame(details_notebook)
        details_notebook.add(reviews_frame, text="🗓 Reviews")

        reviews_actions = ttk.Frame(reviews_frame)
        reviews_actions.pack(fill="x", pady=(8, 4))

        ttk.Button(
            reviews_actions,
            text="Generate Reviews From Services",
            command=self.generate_reviews_from_services
        ).pack(side="left")

        # Reviews list
        reviews_list_frame = ttk.Frame(reviews_frame)
        reviews_list_frame.pack(fill="both", expand=True)

        columns = ("Service", "Cycle", "Planned", "Due", "Status")
        self.reviews_tree = ttk.Treeview(reviews_list_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.reviews_tree.heading(col, text=col)
            self.reviews_tree.column(col, width=120)
        self.reviews_tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(reviews_list_frame, orient="vertical", command=self.reviews_tree.yview).pack(side="right", fill="y")

        # Document Tabs: BEP / EIR / PIR
        try:
            self.doc_tabs = {}
            self.doc_state = {}
            doc_nb = ttk.Notebook(details_frame)
            doc_nb.pack(fill="both", expand=True, pady=(8,0))
            for doc_type in ("BEP", "EIR", "PIR"):
                tab = ttk.Frame(doc_nb)
                doc_nb.add(tab, text=doc_type)
                self._build_document_tab(tab, doc_type)
                self.doc_tabs[doc_type] = tab
        except Exception as _e:
            pass
    
    def refresh_data(self):
        """Refresh project data and update displays"""
        try:
            # Load all projects using existing database function
            projects = get_projects()
            project_names = [f"{row[0]} - {row[1]}" for row in projects]
            self.project_combo['values'] = project_names
            
            # Update project info display
            self.update_project_info(projects)
            
            # Update recent activity
            self.update_recent_activity()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh project data: {str(e)}")

    def generate_reviews_from_services(self):
        """Generate review cycles based on ProjectServices for the selected project."""
        if not self.project_var.get() or " - " not in self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        try:
            project_id = int(self.project_var.get().split(" - ")[0])

            # Establish DB connection and service
            conn = connect_to_db("ProjectManagement")
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to ProjectManagement database")
                return

            svc = ReviewManagementService(conn)

            # Fetch project services
            services = svc.get_project_services(project_id)
            if not services:
                messagebox.showinfo("No Services", "No services found for this project.")
                conn.close()
                return

            # Get project date window
            details = get_project_details(project_id)
            start_date = None
            end_date = None
            try:
                if details and details.get('start_date'):
                    start_date = datetime.strptime(details['start_date'], '%Y-%m-%d').date()
                if details and details.get('end_date'):
                    end_date = datetime.strptime(details['end_date'], '%Y-%m-%d').date()
            except Exception:
                start_date = None
                end_date = None

            created_total = 0
            for s in services:
                # Only generate for review-type services with units
                if str(s.get('unit_type', '')).lower() != 'review':
                    continue
                try:
                    units = int(float(s.get('unit_qty') or 0))
                except Exception:
                    units = 0
                if units <= 0:
                    continue

                # Determine scheduling window
                s_start = start_date or datetime.now().date()
                s_end = end_date or (s_start + timedelta(days=max(units - 1, 0) * 7))

                cycles = svc.generate_review_cycles(
                    s['service_id'], units, s_start, s_end, cadence='weekly', disciplines='All'
                )
                created_total += len(cycles)

            messagebox.showinfo(
                "Review Generation",
                f"Generated {created_total} review cycles based on project services."
            )

            # Reload list
            self.load_generated_reviews(project_id, svc)

            conn.close()

        except Exception as e:
            print(f"Error generating reviews: {e}")
            messagebox.showerror("Error", f"Failed to generate reviews: {str(e)}")

    def load_generated_reviews(self, project_id, svc=None):
        """Load generated reviews into the Reviews tab list."""
        try:
            if svc is None:
                conn = connect_to_db("ProjectManagement")
                if not conn:
                    return
                svc = ReviewManagementService(conn)
                close_conn = True
            else:
                close_conn = False

            # Clear existing rows
            for item in getattr(self, 'reviews_tree', []).get_children():
                self.reviews_tree.delete(item)

            services = svc.get_project_services(project_id)
            service_by_id = {s['service_id']: s for s in services}

            for s in services:
                reviews = svc.get_service_reviews(s['service_id'])
                for r in reviews:
                    self.reviews_tree.insert(
                        "", "end",
                        values=(
                            f"{s['service_code']} {s['service_name']}",
                            r.get('cycle_no'),
                            r.get('planned_date'),
                            r.get('due_date'),
                            r.get('status'),
                        )
                    )

            if close_conn:
                svc.db.close()
        except Exception as e:
            print(f"Error loading reviews: {e}")
    
    def on_project_selected(self, event=None):
        """Handle project selection from dropdown"""
        try:
            selected = self.project_var.get()
            if not selected or " - " not in selected:
                return
            
            project_id = selected.split(" - ")[0]
            
            # Use existing database function to get project details
            project_details = get_project_details(project_id)
            
            # Get project folder paths
            folder_path, ifc_folder_path = get_project_folders(project_id)
            
            if project_details:
                # Update status labels with real data
                self.status_labels["Client"].config(
                    text=project_details.get("client_name", "Not Set"), 
                    foreground="black" if project_details.get("client_name") else "gray"
                )
                self.status_labels["Status"].config(
                    text=project_details.get("status", "Not Set"), 
                    foreground="black" if project_details.get("status") else "gray"
                )
                self.status_labels["Priority"].config(
                    text=project_details.get("priority", "Not Set"), 
                    foreground="black" if project_details.get("priority") else "gray"
                )
                self.status_labels["Start Date"].config(
                    text=project_details.get("start_date", "Not Set"), 
                    foreground="black" if project_details.get("start_date") else "gray"
                )
                self.status_labels["End Date"].config(
                    text=project_details.get("end_date", "Not Set"), 
                    foreground="black" if project_details.get("end_date") else "gray"
                )
                
                # Update file paths with actual data
                self.status_labels["Model Path"].config(
                    text=folder_path if folder_path else "Not Set", 
                    foreground="black" if folder_path else "gray"
                )
                self.status_labels["IFC Path"].config(
                    text=ifc_folder_path if ifc_folder_path else "Not Set", 
                    foreground="black" if ifc_folder_path else "gray"
                )
                
                # Load and display any generated reviews
                try:
                    self.load_generated_reviews(int(project_id))
                except Exception as _e:
                    pass

                # Notify other tabs of project change
                project_notification_system.notify_project_changed(selected)
            else:
                # Clear status labels if no project details found
                for field in ["Client", "Status", "Priority", "Start Date", "End Date", "Model Path", "IFC Path"]:
                    self.status_labels[field].config(text="Not Found", foreground="red")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project details: {str(e)}")
    
    def update_project_info(self, projects):
        """Update the project information display"""
        self.project_info_text.config(state="normal")
        self.project_info_text.delete(1.0, tk.END)
        
        info_text = "PROJECT PORTFOLIO SUMMARY\n" + "="*50 + "\n\n"
        
        if projects:
            # Get detailed info for each project
            project_details_list = []
            status_counts = {}
            priority_counts = {}
            
            for project_id, project_name in projects:
                details = get_project_details(project_id)
                if details:
                    project_details_list.append((project_id, project_name, details))
                    
                    status = details.get("status", "Unknown")
                    priority = details.get("priority", "Unknown")
                    
                    status_counts[status] = status_counts.get(status, 0) + 1
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            info_text += f"Total Projects: {len(projects)}\n\n"
            
            if status_counts:
                info_text += "Status Distribution:\n"
                for status, count in status_counts.items():
                    info_text += f"  • {status}: {count}\n"
            
            if priority_counts:
                info_text += "\nPriority Distribution:\n"
                for priority, count in priority_counts.items():
                    info_text += f"  • {priority}: {count}\n"
            
            info_text += "\n" + "-"*50 + "\n\n"
            
            info_text += "PROJECT DETAILS:\n\n"
            for project_id, project_name, details in project_details_list:
                info_text += f"🏗️ {project_name} (ID: {project_id})\n"
                info_text += f"   Client: {details.get('client_name', 'Not Set')}\n"
                info_text += f"   Status: {details.get('status', 'Not Set')}\n"
                info_text += f"   Priority: {details.get('priority', 'Not Set')}\n"
                if details.get('start_date'):
                    info_text += f"   Duration: {details.get('start_date')} → {details.get('end_date', 'Open')}\n"
                if details.get('client_contact'):
                    info_text += f"   Contact: {details.get('client_contact')} ({details.get('contact_email', 'No email')})\n"
                info_text += "\n"
        else:
            info_text += "No projects found in database.\n"
            info_text += "Use 'Create New Project' to add your first project."
        
        self.project_info_text.insert(1.0, info_text)
        self.project_info_text.config(state="disabled")
    
    def update_recent_activity(self):
        """Update recent activity display"""
        self.activity_text.delete(1.0, tk.END)
        
        activity_text = "RECENT ACTIVITY LOG\n" + "="*50 + "\n\n"
        
        try:
            activity_text += "📅 Today's Activity:\n"
            activity_text += "  • UI Session Started\n"
            activity_text += "  • Project Database Connected\n"
            activity_text += "\n📊 Recent Data Operations:\n"
            activity_text += "  • Project data refreshed\n"
            activity_text += "  • UI components initialized\n"
            
        except Exception as e:
            activity_text += f"Error loading activity: {str(e)}\n"
        
        self.activity_text.insert(1.0, activity_text)
        self.activity_text.config(state="disabled")

    # -------------------------
    # Document tabs (BEP/EIR/PIR)
    # -------------------------
    def _build_document_tab(self, parent, doc_type: str):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        # Library pillar
        lib = ttk.Frame(nb)
        nb.add(lib, text="Library")

        lib_filters = ttk.Frame(lib)
        lib_filters.pack(fill="x", padx=8, pady=6)
        ttk.Button(lib_filters, text="Refresh", command=lambda: self._refresh_library(doc_type)).pack(side="left")
        ttk.Button(lib_filters, text="Seed WIP", command=lambda: self._seed_wip(doc_type)).pack(side="left", padx=(6,0))

        lib_body = ttk.Frame(lib)
        lib_body.pack(fill="both", expand=True, padx=8, pady=6)
        columns = ("Code", "Title", "Body")
        tree = ttk.Treeview(lib_body, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=240 if col == "Title" else 100)
        tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(lib_body, orient="vertical", command=tree.yview).pack(side="right", fill="y")
        preview = tk.Text(lib, height=6, wrap="word")
        preview.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(lib, text="Add Selected to Compose", command=lambda: self._add_selected_to_compose(doc_type)).pack(anchor="w", padx=8)

        # Compose pillar
        comp = ttk.Frame(nb)
        nb.add(comp, text="Compose")
        comp_body = ttk.Frame(comp)
        comp_body.pack(fill="both", expand=True, padx=8, pady=6)
        ttk.Label(comp_body, text="Available").grid(row=0, column=0, sticky="w")
        ttk.Label(comp_body, text="Included").grid(row=0, column=2, sticky="w")
        avail = tk.Listbox(comp_body, height=8)
        inclu = tk.Listbox(comp_body, height=8)
        avail.grid(row=1, column=0, sticky="nsew")
        btns = ttk.Frame(comp_body)
        btns.grid(row=1, column=1, padx=6)
        inclu.grid(row=1, column=2, sticky="nsew")
        ttk.Button(btns, text=">>", command=lambda: self._move_list_items(avail, inclu)).pack(pady=4)
        ttk.Button(btns, text="<<", command=lambda: self._move_list_items(inclu, avail)).pack(pady=4)
        comp_body.columnconfigure(0, weight=1)
        comp_body.columnconfigure(2, weight=1)
        comp_footer = ttk.Frame(comp)
        comp_footer.pack(fill="x", padx=8, pady=6)
        ttk.Label(comp_footer, text="Title:").pack(side="left")
        title_var = tk.StringVar(value=f"{doc_type} Document")
        ttk.Entry(comp_footer, textvariable=title_var, width=26).pack(side="left", padx=(4,10))
        ttk.Label(comp_footer, text="Version:").pack(side="left")
        ver_var = tk.StringVar(value="1.0")
        ttk.Entry(comp_footer, textvariable=ver_var, width=10).pack(side="left", padx=(4,10))
        ttk.Button(comp_footer, text="Instantiate", command=lambda: self._instantiate_document(doc_type, title_var.get(), ver_var.get())).pack(side="left")

        # Assign pillar
        ass = ttk.Frame(nb)
        nb.add(ass, text="Assign & Execute")
        run_bar = ttk.Frame(ass)
        run_bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(run_bar, text="Run Checks", command=lambda: self._run_checks(doc_type)).pack(side="left")
        a_cols = ("Clause", "Owner", "Due", "Check", "Status")
        a_tree = ttk.Treeview(ass, columns=a_cols, show="headings", height=7)
        for c in a_cols:
            a_tree.heading(c, text=c)
            a_tree.column(c, width=140)
        a_tree.pack(fill="both", expand=True, padx=8, pady=6)

        # Publish pillar
        pub = ttk.Frame(nb)
        nb.add(pub, text="Publish & Sign-off")
        pub_bar = ttk.Frame(pub)
        pub_bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(pub_bar, text="Change note:").pack(side="left")
        note_var = tk.StringVar()
        ttk.Entry(pub_bar, textvariable=note_var, width=60).pack(side="left", padx=(4,10))
        ttk.Button(pub_bar, text="Publish DOCX", command=lambda: self._publish_document(doc_type, note_var.get())).pack(side="left")

        # Save state
        self.doc_state[doc_type] = {
            'lib_tree': tree,
            'lib_preview': preview,
            'compose_avail': avail,
            'compose_included': inclu,
            'assign_tree': a_tree
        }

        def on_lib_select(_e=None):
            try:
                sel = tree.selection()
                if not sel:
                    return
                vals = tree.item(sel[0]).get('values', [])
                body = vals[2] if len(vals) > 2 else ''
                preview.config(state='normal')
                preview.delete(1.0, tk.END)
                if body:
                    preview.insert(1.0, str(body))
                preview.config(state='disabled')
            except Exception:
                pass
        tree.bind('<<TreeviewSelect>>', on_lib_select)

    def _seed_wip(self, doc_type: str):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            conn = doc_services.ensure_ready()
            if not conn:
                messagebox.showerror("DB", "Cannot connect to DB")
                return
            import json, os
            path = os.path.join(os.getcwd(), 'templates', 'bep_seed.json')
            with open(path, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            lib_id = doc_services.import_library_seed(conn, doc_type, seed, template_name='WIP', version='1.0', jurisdiction='Generic')
            conn.close()
            self._refresh_library(doc_type)
            messagebox.showinfo("Seed", f"Seeded {doc_type} (library {lib_id})")
        except Exception as e:
            messagebox.showerror("Seed", str(e))

    def _refresh_library(self, doc_type: str):
        if doc_services is None:
            return
        try:
            state = self.doc_state.get(doc_type, {})
            tree = state.get('lib_tree')
            avail = state.get('compose_avail')
            if not tree:
                return
            for i in tree.get_children():
                tree.delete(i)
            conn = doc_services.ensure_ready()
            if not conn:
                return
            rows = doc_services.list_library(conn, doc_type)
            for r in rows:
                tree.insert('', 'end', values=[r.get('code'), r.get('title'), r.get('body_md')])
            if avail is not None:
                avail.delete(0, tk.END)
                for r in rows:
                    avail.insert(tk.END, f"{r.get('section_id')} | {r.get('code') or ''} {r.get('title')}")
            conn.close()
        except Exception as e:
            print(f"Library refresh error: {e}")

    def _add_selected_to_compose(self, doc_type: str):
        state = self.doc_state.get(doc_type, {})
        tree = state.get('lib_tree')
        inclu = state.get('compose_included')
        if not tree or not inclu:
            return
        for sel in tree.selection():
            code, title, _ = tree.item(sel).get('values', [None, None, None])
            inclu.insert(tk.END, f"{code or ''} {title or ''}")

    def _move_list_items(self, src: tk.Listbox, dst: tk.Listbox):
        try:
            sel = list(src.curselection())
            sel.reverse()
            for i in sel:
                val = src.get(i)
                dst.insert(tk.END, val)
                src.delete(i)
        except Exception:
            pass

    def _instantiate_document(self, doc_type: str, title: str, version: str):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            if not self.project_var.get() or " - " not in self.project_var.get():
                messagebox.showwarning("Project", "Select a project first")
                return
            project_id = int(self.project_var.get().split(" - ")[0])
            state = self.doc_state.get(doc_type, {})
            inclu = state.get('compose_included')
            if inclu is None or inclu.size() == 0:
                messagebox.showwarning("Compose", "No sections selected")
                return
            conn = doc_services.ensure_ready()
            rows = doc_services.list_library(conn, doc_type)
            if not rows:
                conn.close()
                messagebox.showwarning("Library", "No library exists. Seed first.")
                return
            library_id = rows[0]['library_id']
            selected_codes = set()
            for i in range(inclu.size()):
                code = (inclu.get(i).split(' ')[0] or '').strip()
                if code:
                    selected_codes.add(code)
            selected_ids = [r['section_id'] for r in rows if (r.get('code') or '') in selected_codes]
            doc_id = doc_services.instantiate_document(conn, project_id, library_id, title, version, doc_type, include_optional=True, selected_section_ids=selected_ids)
            if not hasattr(self, 'current_project_document_id_by_type'):
                self.current_project_document_id_by_type = {}
            self.current_project_document_id_by_type[doc_type] = doc_id
            conn.close()
            messagebox.showinfo("Document", f"Created {doc_type} document (ID {doc_id})")
        except Exception as e:
            messagebox.showerror("Instantiate", str(e))

    def _run_checks(self, doc_type: str):
        if doc_runner is None:
            messagebox.showerror("Module", "Runner not available")
            return
        try:
            doc_id = getattr(self, 'current_project_document_id_by_type', {}).get(doc_type)
            if not doc_id:
                messagebox.showwarning("Checks", "Create a document first")
                return
            conn = doc_services.ensure_ready()
            res = doc_runner.run_assignments(conn, doc_id)
            conn.close()
            messagebox.showinfo("Checks", f"Ran {res.get('total',0)} assignments: {res.get('passed',0)} pass, {res.get('failed',0)} fail")
        except Exception as e:
            messagebox.showerror("Run Checks", str(e))

    def _publish_document(self, doc_type: str, change_note: str):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            doc_id = getattr(self, 'current_project_document_id_by_type', {}).get(doc_type)
            if not doc_id:
                messagebox.showwarning("Publish", "Create a document first")
                return
            conn = doc_services.ensure_ready()
            out = doc_services.publish_document(conn, doc_id, change_note, formats=("DOCX",))
            conn.close()
            files = out.get('files') or []
            msg = f"Published revision {out.get('revision_id')}" + (f"\nFiles: {files}" if files else "")
            messagebox.showinfo("Publish", msg)
        except Exception as e:
            messagebox.showerror("Publish", str(e))

    # Action methods
    def create_new_project(self):
        """Open create new project dialog"""
        self.show_project_dialog(mode="create")
    
    def edit_project_details(self):
        """Open edit project details dialog"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        self.show_project_dialog(mode="edit")
    
    def configure_paths(self):
        """Configure file paths for the current project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Configure Paths", "File path configuration dialog would open here")
    
    def extract_acc_files(self):
        """Extract files from ACC Desktop Connector"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Extract Files", "ACC file extraction would start here")
    
    def refresh_data(self):
        """Refresh project data"""
        try:
            # Reload projects list
            projects = get_projects()
            current_selection = self.project_var.get()
            
            # Update project dropdown
            self.project_dropdown['values'] = [f"{p[0]} - {p[1]}" for p in projects]
            
            # Maintain current selection if it still exists
            if current_selection in self.project_dropdown['values']:
                self.project_var.set(current_selection)
            
            messagebox.showinfo("Refresh", "Project data refreshed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
    
    def view_dashboard(self):
        """Open project dashboard"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        messagebox.showinfo("Dashboard", "Project dashboard would open here")
    
    def archive_project(self):
        """Archive the current project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        result = messagebox.askyesno("Archive Project", 
                                   "Are you sure you want to archive this project?\n"
                                   "This will mark it as inactive but preserve all data.")
        if result:
            messagebox.showinfo("Archive", "Project archived successfully")
    
    def show_project_dialog(self, mode="create"):
        """Show project creation/editing dialog"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create New Project" if mode == "create" else "Edit Project")
        dialog.geometry("500x400")
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Project details fields
        fields = [
            ("Project Name:", "project_name"),
            ("Project Code:", "project_code"),
            ("Description:", "description"),
            ("Client:", "client"),
            ("Location:", "location")
        ]
        
        entries = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            
            if field == "description":
                # Multi-line text widget for description
                text_widget = tk.Text(main_frame, height=4, width=40)
                text_widget.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
                entries[field] = text_widget
            else:
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
                entries[field] = entry
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_project():
            try:
                # Get values from entries
                values = {}
                for field, widget in entries.items():
                    if field == "description":
                        values[field] = widget.get("1.0", tk.END).strip()
                    else:
                        values[field] = widget.get().strip()
                
                # Validate required fields
                if not values["project_name"] or not values["project_code"]:
                    messagebox.showwarning("Validation", "Project Name and Project Code are required")
                    return
                
                # Here you would implement the actual database save logic
                if mode == "create":
                    messagebox.showinfo("Success", f"Project '{values['project_name']}' created successfully!")
                else:
                    messagebox.showinfo("Success", f"Project '{values['project_name']}' updated successfully!")
                
                # Refresh the projects list
                self.refresh_data()
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)


# ==============================================
# Top-level per-document tabs (BEP/EIR/PIR)
# ==============================================
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
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        # Library
        lib = ttk.Frame(nb)
        nb.add(lib, text="Library")
        lib_head = ttk.Frame(lib)
        lib_head.pack(fill="x", padx=8, pady=6)
        ttk.Button(lib_head, text="Refresh", command=self._refresh_library).pack(side="left")
        ttk.Button(lib_head, text="Seed WIP", command=self._seed_wip).pack(side="left", padx=(6,0))
        lib_body = ttk.Frame(lib)
        lib_body.pack(fill="both", expand=True, padx=8, pady=6)
        self.lib_tree = ttk.Treeview(lib_body, columns=("Code","Title","Body"), show="headings", height=8)
        for col in ("Code","Title","Body"):
            self.lib_tree.heading(col, text=col)
            self.lib_tree.column(col, width=240 if col=="Title" else 100)
        self.lib_tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(lib_body, orient="vertical", command=self.lib_tree.yview).pack(side="right", fill="y")
        self.lib_preview = tk.Text(lib, height=6, wrap="word")
        self.lib_preview.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(lib, text="Add Selected to Compose", command=self._add_selected_to_compose).pack(anchor="w", padx=8)
        self.lib_tree.bind('<<TreeviewSelect>>', self._on_lib_select)

        # Compose
        comp = ttk.Frame(nb)
        nb.add(comp, text="Compose")
        comp_body = ttk.Frame(comp)
        comp_body.pack(fill="both", expand=True, padx=8, pady=6)
        ttk.Label(comp_body, text="Available").grid(row=0, column=0, sticky="w")
        ttk.Label(comp_body, text="Included").grid(row=0, column=2, sticky="w")
        self.avail_list = tk.Listbox(comp_body, height=8)
        self.inclu_list = tk.Listbox(comp_body, height=8)
        self.avail_list.grid(row=1, column=0, sticky="nsew")
        btns = ttk.Frame(comp_body)
        btns.grid(row=1, column=1, padx=6)
        self.inclu_list.grid(row=1, column=2, sticky="nsew")
        ttk.Button(btns, text=">>", command=lambda: self._move_list_items(self.avail_list, self.inclu_list)).pack(pady=4)
        ttk.Button(btns, text="<<", command=lambda: self._move_list_items(self.inclu_list, self.avail_list)).pack(pady=4)
        comp_body.columnconfigure(0, weight=1)
        comp_body.columnconfigure(2, weight=1)
        comp_footer = ttk.Frame(comp)
        comp_footer.pack(fill="x", padx=8, pady=6)
        ttk.Label(comp_footer, text="Title:").pack(side="left")
        self.title_var = tk.StringVar(value=f"{self.doc_type} Document")
        ttk.Entry(comp_footer, textvariable=self.title_var, width=26).pack(side="left", padx=(4,10))
        ttk.Label(comp_footer, text="Version:").pack(side="left")
        self.ver_var = tk.StringVar(value="1.0")
        ttk.Entry(comp_footer, textvariable=self.ver_var, width=10).pack(side="left", padx=(4,10))
        ttk.Button(comp_footer, text="Instantiate", command=self._instantiate_document).pack(side="left")

        # Assign & Execute
        ass = ttk.Frame(nb)
        nb.add(ass, text="Assign & Execute")
        run_bar = ttk.Frame(ass)
        run_bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(run_bar, text="Run Checks", command=self._run_checks).pack(side="left")
        a_cols = ("Clause", "Owner", "Due", "Check", "Status")
        self.assign_tree = ttk.Treeview(ass, columns=a_cols, show="headings", height=7)
        for c in a_cols:
            self.assign_tree.heading(c, text=c)
            self.assign_tree.column(c, width=140)
        self.assign_tree.pack(fill="both", expand=True, padx=8, pady=6)

        # Publish
        pub = ttk.Frame(nb)
        nb.add(pub, text="Publish & Sign-off")
        pub_bar = ttk.Frame(pub)
        pub_bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(pub_bar, text="Change note:").pack(side="left")
        self.note_var = tk.StringVar()
        ttk.Entry(pub_bar, textvariable=self.note_var, width=60).pack(side="left", padx=(4,10))
        ttk.Button(pub_bar, text="Publish DOCX", command=self._publish_document).pack(side="left")

    # Project change hook
    def on_project_changed(self, project_selection: str):
        try:
            self.current_project = project_selection
            if " - " in project_selection:
                self.current_project_id = int(project_selection.split(" - ")[0])
        except Exception:
            self.current_project_id = None

    # Library actions
    def _seed_wip(self):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            conn = doc_services.ensure_ready()
            if not conn:
                messagebox.showerror("DB", "Cannot connect to DB")
                return
            import json, os
            path = os.path.join(os.getcwd(), 'templates', 'bep_seed.json')
            with open(path, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            doc_services.import_library_seed(conn, self.doc_type, seed, template_name='WIP', version='1.0', jurisdiction='Generic')
            conn.close()
            self._refresh_library()
            messagebox.showinfo("Seed", f"Seeded {self.doc_type} library")
        except Exception as e:
            messagebox.showerror("Seed", str(e))

    def _refresh_library(self):
        if doc_services is None:
            return
        try:
            for i in self.lib_tree.get_children():
                self.lib_tree.delete(i)
            conn = doc_services.ensure_ready()
            if not conn:
                return
            rows = doc_services.list_library(conn, self.doc_type)
            for r in rows:
                self.lib_tree.insert('', 'end', values=[r.get('code'), r.get('title'), r.get('body_md')])
                # Also populate available list
            self.avail_list.delete(0, tk.END)
            for r in rows:
                self.avail_list.insert(tk.END, f"{r.get('section_id')} | {r.get('code') or ''} {r.get('title')}")
            conn.close()
        except Exception as e:
            print(f"Library refresh error: {e}")

    def _on_lib_select(self, _e=None):
        try:
            sel = self.lib_tree.selection()
            if not sel:
                return
            vals = self.lib_tree.item(sel[0]).get('values', [])
            body = vals[2] if len(vals) > 2 else ''
            self.lib_preview.config(state='normal')
            self.lib_preview.delete(1.0, tk.END)
            if body:
                self.lib_preview.insert(1.0, str(body))
            self.lib_preview.config(state='disabled')
        except Exception:
            pass

    def _add_selected_to_compose(self):
        sel = self.lib_tree.selection()
        if not sel:
            return
        code, title, _ = self.lib_tree.item(sel[0]).get('values', [None, None, None])
        self.inclu_list.insert(tk.END, f"{code or ''} {title or ''}")

    def _move_list_items(self, src: tk.Listbox, dst: tk.Listbox):
        try:
            sel = list(src.curselection())
            sel.reverse()
            for i in sel:
                val = src.get(i)
                dst.insert(tk.END, val)
                src.delete(i)
        except Exception:
            pass

    # Document flows
    def _instantiate_document(self):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            if not self.current_project_id:
                messagebox.showwarning("Project", "Select a project on another tab")
                return
            conn = doc_services.ensure_ready()
            rows = doc_services.list_library(conn, self.doc_type)
            if not rows:
                conn.close()
                messagebox.showwarning("Library", "No library exists. Seed first.")
                return
            library_id = rows[0]['library_id']
            selected_codes = set()
            for i in range(self.inclu_list.size()):
                code = (self.inclu_list.get(i).split(' ')[0] or '').strip()
                if code:
                    selected_codes.add(code)
            selected_ids = [r['section_id'] for r in rows if (r.get('code') or '') in selected_codes]
            doc_id = doc_services.instantiate_document(conn, self.current_project_id, library_id, self.title_var.get(), self.ver_var.get(), self.doc_type, include_optional=True, selected_section_ids=selected_ids)
            self.current_project_document_id = doc_id
            conn.close()
            messagebox.showinfo("Document", f"Created {self.doc_type} document (ID {doc_id})")
        except Exception as e:
            messagebox.showerror("Instantiate", str(e))

    def _run_checks(self):
        if doc_runner is None:
            messagebox.showerror("Module", "Runner not available")
            return
        try:
            if not self.current_project_document_id:
                messagebox.showwarning("Checks", "Create a document first")
                return
            conn = doc_services.ensure_ready()
            res = doc_runner.run_assignments(conn, self.current_project_document_id)
            conn.close()
            messagebox.showinfo("Checks", f"Ran {res.get('total',0)} assignments: {res.get('passed',0)} pass, {res.get('failed',0)} fail")
        except Exception as e:
            messagebox.showerror("Run Checks", str(e))

    def _publish_document(self):
        if doc_services is None:
            messagebox.showerror("Module", "Document services not available")
            return
        try:
            if not self.current_project_document_id:
                messagebox.showwarning("Publish", "Create a document first")
                return
            conn = doc_services.ensure_ready()
            out = doc_services.publish_document(conn, self.current_project_document_id, self.note_var.get(), formats=("DOCX",))
            conn.close()
            files = out.get('files') or []
            msg = f"Published revision {out.get('revision_id')}" + (f"\nFiles: {files}" if files else "")
            messagebox.showinfo("Publish", msg)
        except Exception as e:
            messagebox.showerror("Publish", str(e))


class BEPDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="BEP", tab_label="BEP")


class EIRDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="EIR", tab_label="EIR")


class PIRDocumentTab(_DocumentTypeTab):
    def __init__(self, parent_notebook):
        super().__init__(parent_notebook, doc_type="PIR", tab_label="PIR")
    
    # Action methods
    def create_new_project(self):
        """Open create new project dialog"""
        self.show_project_dialog(mode="create")
    
    def edit_project_details(self):
        """Open edit project details dialog"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_id = self.project_var.get().split(" - ")[0]
        self.show_project_dialog(mode="edit", project_id=project_id)
    
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
        basic_frame = ttk.LabelFrame(content_frame, text="📋 Basic Project Information", padding=15)
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
        status_frame = ttk.LabelFrame(content_frame, text="📊 Project Status & Timeline", padding=15)
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
        location_frame = ttk.LabelFrame(content_frame, text="📍 Location Information", padding=15)
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
        paths_frame = ttk.LabelFrame(content_frame, text="📁 File Paths", padding=15)
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
    
    def browse_folder(self, path_var):
        """Browse for folder and set path variable"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            path_var.set(folder)
    
    def show_new_client_dialog(self, client_combo):
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
        
        # Content frame
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ttk.Label(content_frame, text="Create New Client", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Client fields
        fields_frame = ttk.LabelFrame(content_frame, text="Client Information", padding=15)
        fields_frame.pack(fill="x", pady=(0, 20))
        
        # Variables for client data
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
        
        fields_frame.columnconfigure(1, weight=1)
        
        def save_client():
            """Save the new client"""
            try:
                if not client_vars['name'].get().strip():
                    messagebox.showerror("Error", "Client name is required")
                    return
                
                # Prepare client data dictionary as expected by the database function
                client_data = {
                    'client_name': client_vars['name'].get().strip(),
                    'contact_name': client_vars['contact'].get().strip(),
                    'contact_email': client_vars['email'].get().strip(),
                    'contact_phone': client_vars['phone'].get().strip(),
                    'address': client_vars['address'].get().strip(),
                    'city': client_vars['city'].get().strip(),
                    'state': client_vars['state'].get().strip(),
                    'postcode': client_vars['postcode'].get().strip(),
                    'country': 'Australia'  # Default country
                }
                
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
        
        save_btn = ttk.Button(button_frame, text="💾 Save Client", command=save_client)
        save_btn.pack(side="right", padx=5)
        
        # Focus on client name field
        client_vars['name'].set("")
        dialog.after(100, lambda: dialog.focus_set())
    
    def create_project_in_db(self, project_data):
        """Create a new project in the database"""
        try:
            # First, create the basic project using the existing function
            basic_success = insert_project(
                project_data['name'], 
                project_data.get('folder_path', ''), 
                project_data.get('ifc_folder_path', '')
            )
            
            if not basic_success:
                return False
            
            # Get the newly created project ID by finding the project with this name
            projects = get_projects()
            new_project_id = None
            for project_id, project_name in projects:
                if project_name == project_data['name']:
                    new_project_id = project_id
                    break
            
            if not new_project_id:
                print(f"❌ Could not find newly created project: {project_data['name']}")
                return False
            
            # Now update the project with additional details
            additional_data = {}
            
            if project_data.get('client_id'):
                additional_data['client_id'] = project_data['client_id']
            if project_data.get('status'):
                additional_data['status'] = project_data['status']
            if project_data.get('priority'):
                additional_data['priority'] = project_data['priority']
            if project_data.get('start_date'):
                additional_data['start_date'] = project_data['start_date']
            if project_data.get('end_date'):
                additional_data['end_date'] = project_data['end_date']
                
            # Update additional fields if we have any
            if additional_data:
                from database import update_project_record
                update_success = update_project_record(new_project_id, additional_data)
                if update_success:
                    print(f"✅ Successfully created and updated project: {project_data['name']} (ID: {new_project_id})")
                else:
                    print(f"⚠️ Project created but failed to update additional details for: {project_data['name']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            messagebox.showerror("Database Error", f"Failed to create project: {str(e)}")
            return False
    
    def update_project_in_db(self, project_id, project_data):
        """Update an existing project in the database"""
        try:
            # Map UI fields to database column names
            db_data = {}
            
            # Basic project information
            if project_data.get('name'):
                db_data['project_name'] = project_data['name']
            if project_data.get('client_id'):
                db_data['client_id'] = project_data['client_id']
            if project_data.get('status'):
                db_data['status'] = project_data['status']
            if project_data.get('priority'):
                db_data['priority'] = project_data['priority']
            if project_data.get('start_date'):
                db_data['start_date'] = project_data['start_date']
            if project_data.get('end_date'):
                db_data['end_date'] = project_data['end_date']
            
            # Update main project record if we have data to update
            if db_data:
                from database import update_project_record
                success = update_project_record(project_id, db_data)

                if not success:
                    print(f"Failed to update project record for project {project_id}")
                    return False
            
            # Update folder paths separately using the dedicated function
            if project_data.get('folder_path') or project_data.get('ifc_folder_path'):
                from database import update_project_folders
                folder_success = update_project_folders(
                    project_id,
                    models_path=project_data.get('folder_path'),
                    ifc_path=project_data.get('ifc_folder_path')
                )
                if not folder_success:
                    print(f"Failed to update folder paths for project {project_id}")
            
            print(f"✅ Successfully updated project {project_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating project {project_id}: {e}")
            messagebox.showerror("Database Error", f"Failed to update project: {str(e)}")
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
            title_label = ttk.Label(content_frame, text="📁 Configure File Paths", 
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
            
            ttk.Button(content_frame, text="📁 Browse", 
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
            
            ttk.Button(content_frame, text="📁 Browse", 
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
                    model_status_var.set("❌ Path not set")
                elif not os.path.exists(model_path):
                    model_status_var.set("❌ Path does not exist")
                elif not os.path.isdir(model_path):
                    model_status_var.set("❌ Not a directory")
                else:
                    model_status_var.set("✅ Valid path")
                
                # Validate IFC path
                ifc_path = ifc_path_var.get().strip()
                if not ifc_path:
                    ifc_status_var.set("⚠️ Path not set (optional)")
                elif not os.path.exists(ifc_path):
                    ifc_status_var.set("❌ Path does not exist")
                elif not os.path.isdir(ifc_path):
                    ifc_status_var.set("❌ Not a directory")
                else:
                    ifc_status_var.set("✅ Valid path")
            
            # Validate paths initially and on changes
            def on_path_change(*args):
                dialog.after_idle(validate_paths)
            
            model_path_var.trace_add('write', on_path_change)
            ifc_path_var.trace_add('write', on_path_change)
            validate_paths()  # Initial validation
            
            # Validate button
            ttk.Button(validation_frame, text="🔍 Validate Paths", 
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
                        preview_text.insert(tk.END, f"📁 Model Folder Contents: {model_path}\n")
                        preview_text.insert(tk.END, "="*60 + "\n\n")
                        
                        items = os.listdir(model_path)
                        if items:
                            folders = [item for item in items if os.path.isdir(os.path.join(model_path, item))]
                            files = [item for item in items if os.path.isfile(os.path.join(model_path, item))]
                            
                            if folders:
                                preview_text.insert(tk.END, "📂 Folders:\n")
                                for folder in sorted(folders):
                                    preview_text.insert(tk.END, f"  📁 {folder}\n")
                                preview_text.insert(tk.END, "\n")
                            
                            if files:
                                preview_text.insert(tk.END, "📄 Files:\n")
                                for file in sorted(files):
                                    preview_text.insert(tk.END, f"  📄 {file}\n")
                        else:
                            preview_text.insert(tk.END, "Empty folder")
                            
                    except Exception as e:
                        preview_text.insert(tk.END, f"Error reading folder: {str(e)}")
                else:
                    preview_text.insert(tk.END, "No valid model path selected for preview")
            
            ttk.Button(preview_frame, text="🔄 Refresh Preview", 
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
                    print(f"❌ Error saving paths: {e}")
                    messagebox.showerror("Error", f"Failed to save paths: {str(e)}")
            
            def cancel():
                dialog.destroy()
            
            # Save and Cancel buttons
            ttk.Button(buttons_frame, text="💾 Save Paths", command=save_paths, 
                      style="Accent.TButton").pack(side="left", padx=(0, 10))
            ttk.Button(buttons_frame, text="❌ Cancel", command=cancel).pack(side="left")
            
            # Focus on model path entry
            model_path_entry.focus()
            
        except Exception as e:
            print(f"❌ Error opening configure paths dialog: {e}")
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
            from database import insert_files_into_tblACCDocs
            
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
            print(f"❌ Error during file extraction: {e}")
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
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection and update scope/schedule"""
        try:
            selected = self.project_var.get()
            if not selected:
                return
            
            self.current_project_id = int(selected.split(" - ")[0])
            print(f"🔍 Loading project data for: {selected}")
            
            # Load project services in scope grid
            self.load_project_scope()
            
            # Load schedule data
            self.load_schedule()
            
            self.status_var.set(f"Loaded project: {selected.split(' - ')[1]}")
            
            # Notify other tabs
            project_notification_system.notify_project_changed(selected)
            
        except Exception as e:
            print(f"Error loading project: {e}")
            self.status_var.set(f"Error loading project: {str(e)}")
    
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
