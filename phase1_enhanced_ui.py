"""
Phase 1 Enhanced UI Module
Enhanced task management, milestone tracking, and resource allocation interface
Includes existing daily workflow components: ACC folder management, data import, and issue management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
    update_project_details, update_project_folders
)
from review_management_service import ReviewManagementService
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
        
        project_id = self.project_combo.get().split(" - ")[0]
        
        try:
            # Refresh predecessor tasks
            tasks = self.task_mgr.get_tasks_by_project(project_id)
            task_names = [f"{task.get('task_id', '')} - {task.get('name', '')}" for task in tasks]
            self.predecessor_combo['values'] = [""] + task_names
            
            # Refresh task display
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
            
            for task in tasks:
                self.tasks_tree.insert("", "end", values=(
                    task.get('task_id', ''),
                    task.get('name', ''),
                    task.get('priority', ''),
                    task.get('status', ''),
                    task.get('start_date', ''),
                    task.get('end_date', ''),
                    task.get('assigned_to', ''),
                    task.get('progress', '0%')
                ))
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
            dialog.transient(self.frame.winfo_toplevel())
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
                                   text=f"Project: {project_data.get('name', 'Unknown')} (ID: {project_id})",
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
        """Handle local project selection"""
        self.on_project_selected()
        
        # Notify other tabs about the project change
        project_notification_system.notify_project_changed(self.project_var.get())
    
    def on_project_changed(self, new_project):
        """Handle project change notification from other tabs"""
        if self.project_var.get() != new_project:
            self.project_var.set(new_project)
            self.on_project_selected()

class ReviewManagementTab:
    """Comprehensive Review Management System - Scope → Schedule → Progress → Billing workflow"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📅 Review Management")
        
        # Initialize backend service
        try:
            db_conn = connect_to_db()
            if db_conn:
                self.review_service = ReviewManagementService(db_conn)
            else:
                self.review_service = None
        except Exception as e:
            print(f"Error initializing review service: {e}")
            self.review_service = None
        
        # Initialize state variables
        self.current_project_id = None
        self.current_project_data = None
        
        # Reference data for the comprehensive system
        self.load_available_templates()
        self.service_codes = {
            "INIT": "Digital Initiation",
            "PROD": "Digital Production", 
            "REVI": "Review Services",
            "REPO": "Reporting",
            "SUPP": "Support Services"
        }
        self.unit_types = ["lump_sum", "review", "drawing", "area", "linear", "hourly"]
        self.bill_rules = ["on_setup", "on_delivery", "progressive", "on_approval", "monthly"]
        
        # Setup UI and register for notifications
        self.setup_ui()
        self.refresh_data()
        project_notification_system.register_observer(self)
    
    def load_available_templates(self):
        """Load available templates from the service"""
        if self.review_service:
            try:
                templates = self.review_service.get_available_templates()
                self.available_templates = [t['name'] for t in templates] if templates else []
                print(f"✅ Loaded {len(self.available_templates)} templates: {self.available_templates}")
            except Exception as e:
                print(f"❌ Error loading templates: {e}")
                self.available_templates = ["SINSW – Melrose Park HS", "AWS – MEL081 STOCKMAN (Day 1)", "NEXTDC S5 – Spatial & Technical Design"]
        else:
            print("❌ No review service available, using fallback templates")
            self.available_templates = ["SINSW – Melrose Park HS", "AWS – MEL081 STOCKMAN (Day 1)", "NEXTDC S5 – Spatial & Technical Design"]
    
    def setup_ui(self):
        """Setup the comprehensive review management UI - Scope → Schedule → Progress → Billing"""
        
        # Initialize status variable
        self.status_var = tk.StringVar(value="Ready - Select project to begin")
        
        # Main 3-panel layout: Left (Scope), Right (Schedule), Bottom (Claims)
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Top paned window for left/right split
        top_paned = ttk.PanedWindow(main_frame, orient='horizontal')
        top_paned.pack(fill="both", expand=True)
        
        # === LEFT PANEL: SCOPE & FEES ===
        left_panel = ttk.Frame(top_paned, width=600)
        top_paned.add(left_panel, weight=1)
        
        # Project Selection
        project_frame = ttk.LabelFrame(left_panel, text="📊 Project Selection", padding=10)
        project_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(project_frame, text="Project:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50)
        self.project_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected_local)
        
        project_frame.columnconfigure(1, weight=1)
        
        # Template Application
        template_frame = ttk.LabelFrame(left_panel, text="⚡ Apply Template", padding=10)
        template_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(template_frame, text="Template:").grid(row=0, column=0, sticky="w", padx=5)
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, 
                                    values=self.available_templates, width=30)
        template_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Button(template_frame, text="Apply Template", 
                  command=self.apply_template).grid(row=0, column=2, padx=10)
        ttk.Button(template_frame, text="Clear All Services", 
                  command=self.clear_all_services).grid(row=0, column=3, padx=5)
        
        # Scope & Fees Grid (ProjectServices)
        scope_frame = ttk.LabelFrame(left_panel, text="📋 Project Scope & Fees", padding=10)
        scope_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Toolbar for scope management
        scope_toolbar = ttk.Frame(scope_frame)
        scope_toolbar.pack(fill="x", pady=(0, 5))
        
        ttk.Button(scope_toolbar, text="➕ Add Service", 
                  command=self.add_service_dialog).pack(side="left", padx=5)
        ttk.Button(scope_toolbar, text="✏️ Edit Service", 
                  command=self.edit_service_dialog).pack(side="left", padx=5)
        ttk.Button(scope_toolbar, text="🔄 Generate Cycles", 
                  command=self.generate_cycles_dialog).pack(side="left", padx=5)
        ttk.Button(scope_toolbar, text="📈 Update Progress", 
                  command=self.update_all_progress).pack(side="left", padx=5)
        
        # Services TreeView - Left Grid
        scope_columns = ("Phase", "Service", "Type", "Qty", "Rate", "Agreed Fee", 
                        "Progress", "Claimed", "Remaining", "Status")
        self.scope_tree = ttk.Treeview(scope_frame, columns=scope_columns, show="headings", height=12)
        
        # Configure columns with appropriate widths
        column_widths = {
            "Phase": 200, "Service": 250, "Type": 80, "Qty": 60, 
            "Rate": 100, "Agreed Fee": 100, "Progress": 80, 
            "Claimed": 100, "Remaining": 100, "Status": 80
        }
        
        for col in scope_columns:
            self.scope_tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.scope_tree.column(col, width=width, minwidth=50)
        
        scope_tree_container = ttk.Frame(scope_frame)
        scope_tree_container.pack(fill="both", expand=True)
        
        self.scope_tree.pack(side="left", fill="both", expand=True)
        
        scope_scroll = ttk.Scrollbar(scope_tree_container, orient="vertical", command=self.scope_tree.yview)
        self.scope_tree.configure(yscrollcommand=scope_scroll.set)
        scope_scroll.pack(side="right", fill="y")
        
        # Add inline editing capabilities
        self.setup_inline_editing()
        
        # Add right-click context menu for scope tree
        self.setup_scope_context_menu()
        
        # Service management buttons
        service_buttons_frame = ttk.Frame(scope_frame)
        service_buttons_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(service_buttons_frame, text="➕ Add Service", 
                  command=self.add_service).pack(side="left", padx=(0, 5))
        ttk.Label(service_buttons_frame, text="💡 Double-click any cell to edit", 
                 foreground="blue", font=("Arial", 9)).pack(side="left", padx=5)
        ttk.Button(service_buttons_frame, text="🗑️ Remove Service", 
                  command=self.remove_selected_service).pack(side="right", padx=5)
        
        # === RIGHT PANEL: SCHEDULE & REVIEWS ===
        right_panel = ttk.Frame(top_paned, width=600)
        top_paned.add(right_panel, weight=1)
        
        # Schedule Controls
        schedule_controls = ttk.LabelFrame(right_panel, text="🗓️ Schedule Controls", padding=10)
        schedule_controls.pack(fill="x", pady=(0, 5))
        
        ttk.Label(schedule_controls, text="View:").grid(row=0, column=0, sticky="w", padx=5)
        self.view_var = tk.StringVar(value="List")
        view_combo = ttk.Combobox(schedule_controls, textvariable=self.view_var, 
                                values=["List", "Calendar", "Gantt"], width=15)
        view_combo.grid(row=0, column=1, padx=5)
        view_combo.bind("<<ComboboxSelected>>", self.change_schedule_view)
        
        ttk.Label(schedule_controls, text="Filter:").grid(row=0, column=2, sticky="w", padx=15)
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(schedule_controls, textvariable=self.filter_var,
                                  values=["All", "Planned", "In Progress", "Completed", "Overdue"], width=15)
        filter_combo.grid(row=0, column=3, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_schedule)
        
        ttk.Button(schedule_controls, text="📊 Gantt Chart", 
                  command=self.open_gantt_chart).grid(row=0, column=4, padx=10)
        
        # Schedule Grid (ServiceReviews)
        schedule_frame = ttk.LabelFrame(right_panel, text="📅 Review Schedule", padding=10)
        schedule_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Schedule toolbar
        schedule_toolbar = ttk.Frame(schedule_frame)
        schedule_toolbar.pack(fill="x", pady=(0, 5))
        
        ttk.Button(schedule_toolbar, text="✅ Mark Issued", 
                  command=self.mark_review_issued).pack(side="left", padx=5)
        ttk.Button(schedule_toolbar, text="✏️ Edit Review", 
                  command=self.edit_review_dialog).pack(side="left", padx=5)
        ttk.Button(schedule_toolbar, text="🔗 Add Evidence", 
                  command=self.add_evidence_dialog).pack(side="left", padx=5)
        ttk.Button(schedule_toolbar, text="📅 Reschedule", 
                  command=self.reschedule_dialog).pack(side="left", padx=5)
        
        # Reviews TreeView - Right Grid
        schedule_columns = ("Cycle", "Service", "Planned", "Due", "Disciplines", 
                          "Status", "Weight", "Evidence", "Action")
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=schedule_columns, show="headings", height=12)
        
        for col in schedule_columns:
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=90)
        
        schedule_tree_container = ttk.Frame(schedule_frame)
        schedule_tree_container.pack(fill="both", expand=True)
        
        self.schedule_tree.pack(side="left", fill="both", expand=True)
        
        schedule_scroll = ttk.Scrollbar(schedule_tree_container, orient="vertical", command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scroll.set)
        schedule_scroll.pack(side="right", fill="y")
        
        # === BOTTOM PANEL: BILLING CLAIMS ===
        claims_frame = ttk.LabelFrame(self.frame, text="💰 Billing Claims & Export", padding=10)
        claims_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Claims controls
        claims_control_frame = ttk.Frame(claims_frame)
        claims_control_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(claims_control_frame, text="Period Start:").grid(row=0, column=0, sticky="w", padx=5)
        self.claim_start_date = DateEntry(claims_control_frame, width=12, date_pattern='yyyy-mm-dd')
        self.claim_start_date.grid(row=0, column=1, padx=5)
        
        ttk.Label(claims_control_frame, text="Period End:").grid(row=0, column=2, sticky="w", padx=15)
        self.claim_end_date = DateEntry(claims_control_frame, width=12, date_pattern='yyyy-mm-dd')
        self.claim_end_date.grid(row=0, column=3, padx=5)
        
        ttk.Label(claims_control_frame, text="PO Ref:").grid(row=0, column=4, sticky="w", padx=15)
        self.po_ref_entry = ttk.Entry(claims_control_frame, width=15)
        self.po_ref_entry.grid(row=0, column=5, padx=5)
        
        ttk.Button(claims_control_frame, text="🧮 Generate Claim", 
                  command=self.generate_claim).grid(row=0, column=6, padx=10)
        ttk.Button(claims_control_frame, text="📤 Export CSV", 
                  command=self.export_claim_csv).grid(row=0, column=7, padx=5)
        
        # Claims summary
        claims_summary_frame = ttk.Frame(claims_frame)
        claims_summary_frame.pack(fill="x", pady=(0, 5))
        
        self.claims_summary_vars = {
            "total_services": tk.StringVar(value="0"),
            "total_value": tk.StringVar(value="$0.00"),
            "claimed_to_date": tk.StringVar(value="$0.00"), 
            "this_claim": tk.StringVar(value="$0.00"),
            "remaining": tk.StringVar(value="$0.00")
        }
        
        summary_labels = [
            ("Services:", "total_services"),
            ("Total Value:", "total_value"),
            ("Claimed to Date:", "claimed_to_date"),
            ("This Claim:", "this_claim"),
            ("Remaining:", "remaining")
        ]
        
        for i, (label, var_key) in enumerate(summary_labels):
            ttk.Label(claims_summary_frame, text=label, font=("Arial", 9, "bold")).grid(row=0, column=i*2, sticky="w", padx=5)
            ttk.Label(claims_summary_frame, textvariable=self.claims_summary_vars[var_key], 
                     font=("Arial", 9)).grid(row=0, column=i*2+1, sticky="w", padx=5)
        
        # Claims TreeView
        claims_columns = ("Phase", "Service", "Previous %", "Current %", "Delta %", "Amount")
        self.claims_tree = ttk.Treeview(claims_frame, columns=claims_columns, show="headings", height=6)
        
        for col in claims_columns:
            self.claims_tree.heading(col, text=col)
            self.claims_tree.column(col, width=120)
        
        claims_tree_container = ttk.Frame(claims_frame)
        claims_tree_container.pack(fill="both", expand=True)
        
        self.claims_tree.pack(side="left", fill="both", expand=True)
        
        claims_scroll = ttk.Scrollbar(claims_tree_container, orient="vertical", command=self.claims_tree.yview)
        self.claims_tree.configure(yscrollcommand=claims_scroll.set)
        claims_scroll.pack(side="right", fill="y")
        
        # === STATUS BAR ===
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill="x", side="bottom", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Status:", font=("Arial", 8, "bold")).pack(side="left")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 8))
        self.status_label.pack(side="left", padx=5)

    def refresh_data(self):
        """Refresh all data for the new workflow"""
        try:
            # Update project dropdown
            projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
            self.project_combo['values'] = projects
            
            # If we have the new UI elements, refresh them
            if hasattr(self, 'template_var'):
                # Template combo already set in __init__
                pass
                
        except Exception as e:
            print(f"Error refreshing data: {e}")
                
            # Clear status indicators when no project selected
            if not self.project_var.get():
                if hasattr(self, 'status_var'):
                    self.status_var.set("Ready - Select a project to begin")
                    
        except Exception as e:
            print(f"Error refreshing data: {e}")
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Error: {str(e)}")
    
    def apply_template(self):
        """Apply selected service template to project"""
        if not self.current_project_id:
            messagebox.showerror("Error", "Please select a project first")
            return
        
        template_name = self.template_var.get()
        print(f"🔍 Attempting to apply template: '{template_name}'")
        if not template_name:
            messagebox.showerror("Error", "Please select a template")
            return
        
        if not self.review_service:
            messagebox.showerror("Error", "Review service not available. Check database connection.")
            return
        
        try:
            # Show confirmation dialog with template details
            if not self.show_template_confirmation(template_name):
                return
            
            # Apply template through service
            services = self.review_service.apply_template(self.current_project_id, template_name)
            
            if services and len(services) > 0:
                messagebox.showinfo("Success", f"Applied template '{template_name}' - created {len(services)} services")
                self.load_project_scope()
                self.status_var.set(f"Applied template: {template_name}")
            else:
                messagebox.showwarning("Warning", "Template applied but no services were created")
                
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            messagebox.showerror("Error", f"Failed to apply template: {str(e)}")
    
    def show_template_confirmation(self, template_name: str) -> bool:
        """Show template details and confirm application"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Confirm Template Application")
        dialog.geometry("600x400")
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()
        
        # Load template data
        print(f"🔍 Loading template data for: '{template_name}'")
        template = self.review_service.load_template(template_name)
        if not template:
            print(f"❌ Template '{template_name}' not found")
            messagebox.showerror("Error", "Template not found")
            return False
        
        print(f"✅ Template loaded successfully: {template.get('name', 'Unknown')}")
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"Apply Template: {template_name}", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(main_frame, text=f"Sector: {template.get('sector', 'General')}", 
                 font=("Arial", 10)).pack()
        ttk.Label(main_frame, text=template.get('notes', ''), 
                 font=("Arial", 9), wraplength=500).pack(pady=5)
        
        # Preview table
        preview_frame = ttk.LabelFrame(main_frame, text="Services to be Created", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Phase", "Service", "Type", "Units", "Rate/Fee", "Total")
        preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            preview_tree.heading(col, text=col)
            preview_tree.column(col, width=100)
        
        preview_tree.pack(fill="both", expand=True)
        
        total_value = 0
        for item in template['items']:
            if item['unit_type'] == 'lump_sum':
                fee = item.get('lump_sum_fee', 0)
                rate_display = f"${fee:,.0f}"
            else:
                units = item.get('default_units', 1)
                rate = item.get('unit_rate', 0)
                fee = units * rate
                rate_display = f"${rate:,.0f}"
            
            preview_tree.insert("", "end", values=(
                item['phase'],
                item['service_name'],
                item['unit_type'],
                item.get('default_units', 1),
                rate_display,
                f"${fee:,.0f}"
            ))
            total_value += fee
        
        ttk.Label(main_frame, text=f"Total Project Value: ${total_value:,.0f}", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # Buttons
        result = tk.BooleanVar(value=False)
        
        def confirm():
            result.set(True)
            dialog.destroy()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Apply Template", command=confirm).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        
        dialog.wait_window()
        return result.get()
    
    def load_project_scope(self):
        """Load project services into scope grid"""
        # Clear existing items
        for item in self.scope_tree.get_children():
            self.scope_tree.delete(item)
        
        if not self.review_service or not self.current_project_id:
            return
        
        try:
            services = self.review_service.get_project_services(self.current_project_id)
            
            if not services:
                self.status_var.set("No services found - try applying a template")
                return
            
            for service in services:
                # Format display values with None checking
                qty = f"{service['unit_qty']:.0f}" if service['unit_qty'] is not None else "1"
                
                if service['unit_rate'] is not None:
                    rate = f"${service['unit_rate']:,.0f}"
                elif service['lump_sum_fee'] is not None:
                    rate = f"${service['lump_sum_fee']:,.0f}"
                else:
                    rate = "$0"
                
                agreed_fee = f"${service['agreed_fee']:,.0f}" if service['agreed_fee'] is not None else "$0"
                progress = f"{service['progress_pct']:.1f}%" if service['progress_pct'] is not None else "0.0%"
                claimed = f"${service['claimed_to_date']:,.0f}" if service['claimed_to_date'] is not None else "$0"
                
                # Calculate remaining safely
                agreed_val = service['agreed_fee'] if service['agreed_fee'] is not None else 0
                claimed_val = service['claimed_to_date'] if service['claimed_to_date'] is not None else 0
                remaining = f"${agreed_val - claimed_val:,.0f}"
                
                self.scope_tree.insert("", "end", values=(
                    service['phase'] or '',
                    service['service_name'] or '',
                    service['unit_type'] or '',
                    qty,
                    rate,
                    agreed_fee,
                    progress,
                    claimed,
                    remaining,
                    service['status'] or 'Active'
                ), tags=(service['service_id'],))
            
            self.status_var.set(f"Loaded {len(services)} services")
            
        except Exception as e:
            print(f"Error loading scope: {e}")
            self.status_var.set(f"Error loading scope: {str(e)}")
    
    def load_project_schedule(self):
        """Load project reviews into schedule grid"""
        # Clear existing items
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        if not self.review_service or not self.current_project_id:
            return
        
        try:
            services = self.review_service.get_project_services(self.current_project_id)
            
            for service in services:
                if service['unit_type'] == 'review':
                    reviews = self.review_service.get_service_reviews(service['service_id'])
                    
                    for review in reviews:
                        # Format display values
                        evidence = "Yes" if review['evidence_links'] else "No"
                        
                        # Color coding based on status
                        tags = []
                        if review['status'] == 'planned':
                            # Check if overdue
                            from datetime import datetime
                            planned_date = datetime.strptime(review['planned_date'], '%Y-%m-%d')
                            if planned_date < datetime.now():
                                tags.append('overdue')
                        elif review['status'] == 'report_issued':
                            tags.append('completed')
                        
                        self.schedule_tree.insert("", "end", values=(
                            f"{review['cycle_no']}/{len(reviews)}",
                            service['service_name'][:20] + "...",
                            review['planned_date'],
                            review['due_date'],
                            review['disciplines'],
                            review['status'],
                            f"{review['weight_factor']:.1f}",
                            evidence,
                            "Mark Issued" if review['status'] == 'planned' else "View"
                        ), tags=(review['review_id'],) + tuple(tags))
            
            # Configure tag colors
            self.schedule_tree.tag_configure('overdue', background='#ffcccc')
            self.schedule_tree.tag_configure('completed', background='#ccffcc')
            
        except Exception as e:
            print(f"Error loading schedule: {e}")
            self.status_var.set(f"Error loading schedule: {str(e)}")
    
    # Comprehensive method implementations
    def add_service_dialog(self, event=None): pass
    def generate_cycles_dialog(self):
        """Show dialog to generate review cycles for services"""
        if not self.current_project_id:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Get services that can have cycles generated (review and audit types)
        services = self.review_service.get_project_services(self.current_project_id)
        eligible_services = [s for s in services if s['unit_type'] in ['review', 'audit']]
        
        if not eligible_services:
            messagebox.showinfo("Info", "No review or audit services found to generate cycles for")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Generate Review Cycles")
        dialog.geometry("600x500")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        ttk.Label(main_frame, text="Generate Review Cycles", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Services selection frame
        services_frame = ttk.LabelFrame(main_frame, text="Select Services", padding="10")
        services_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Services listbox with checkboxes (using Treeview for checkboxes)
        services_tree = ttk.Treeview(services_frame, columns=("service", "type", "qty"), 
                                   show="tree headings", height=8)
        services_tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Configure columns
        services_tree.heading("#0", text="Select")
        services_tree.heading("service", text="Service")
        services_tree.heading("type", text="Type")
        services_tree.heading("qty", text="Cycles")
        
        services_tree.column("#0", width=80)
        services_tree.column("service", width=300)
        services_tree.column("type", width=80)
        services_tree.column("qty", width=80)
        
        # Add services to tree
        selected_services = set()
        
        def toggle_selection(event):
            item = services_tree.selection()[0] if services_tree.selection() else None
            if item:
                if item in selected_services:
                    selected_services.remove(item)
                    services_tree.item(item, text="☐")
                else:
                    selected_services.add(item)
                    services_tree.item(item, text="☑")
        
        services_tree.bind("<Double-1>", toggle_selection)
        
        for service in eligible_services:
            # Check if service already has cycles
            existing_cycles = self.review_service.get_service_reviews(service['service_id'])
            cycle_info = f"{int(service['unit_qty'] or 1)}"
            if existing_cycles:
                cycle_info += f" ({len(existing_cycles)} exist)"
            
            item = services_tree.insert("", "end", 
                                      text="☐",
                                      values=(
                                          service['service_name'],
                                          service['unit_type'],
                                          cycle_info
                                      ),
                                      tags=(service['service_id'],))
        
        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="Cycle Parameters", padding="10")
        params_frame.pack(fill="x", pady=(0, 10))
        
        # Date range
        date_frame = ttk.Frame(params_frame)
        date_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        start_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        start_date_entry = ttk.Entry(date_frame, textvariable=start_date_var, width=12)
        start_date_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'))
        end_date_entry = ttk.Entry(date_frame, textvariable=end_date_var, width=12)
        end_date_entry.grid(row=0, column=3)
        
        # Disciplines
        disciplines_frame = ttk.Frame(params_frame)
        disciplines_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(disciplines_frame, text="Disciplines:").pack(side="left")
        disciplines_var = tk.StringVar(value="Architecture,Structure,Services,Landscape")
        disciplines_entry = ttk.Entry(disciplines_frame, textvariable=disciplines_var, width=50)
        disciplines_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        # Clear existing cycles option
        clear_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Clear existing cycles before generating new ones", 
                       variable=clear_existing_var).pack(anchor="w", pady=(5, 0))
        
        # Instructions
        ttk.Label(params_frame, text="💡 Double-click services to select/deselect them", 
                 foreground="gray").pack(pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        def generate_cycles():
            if not selected_services:
                messagebox.showwarning("Warning", "Please select at least one service")
                return
            
            try:
                start_date = datetime.strptime(start_date_var.get(), '%Y-%m-%d')
                end_date = datetime.strptime(end_date_var.get(), '%Y-%m-%d')
                
                if end_date <= start_date:
                    messagebox.showerror("Error", "End date must be after start date")
                    return
                
                disciplines = disciplines_var.get().strip()
                if not disciplines:
                    disciplines = "All"
                
                total_cycles = 0
                
                # Generate cycles for each selected service
                for item in selected_services:
                    service_id = int(services_tree.item(item, 'tags')[0])
                    service = next(s for s in eligible_services if s['service_id'] == service_id)
                    
                    # Clear existing cycles if requested
                    if clear_existing_var.get():
                        self.review_service.cursor.execute(
                            "DELETE FROM ServiceReviews WHERE service_id = ?", 
                            (service_id,)
                        )
                        self.review_service.db.commit()
                    
                    # Generate new cycles
                    cycles = self.review_service.generate_review_cycles(
                        service_id=service_id,
                        unit_qty=int(service['unit_qty'] or 1),
                        start_date=start_date,
                        end_date=end_date,
                        cadence='weekly',
                        disciplines=disciplines
                    )
                    
                    total_cycles += len(cycles)
                
                messagebox.showinfo("Success", 
                                  f"Generated {total_cycles} review cycles for {len(selected_services)} services")
                
                # Refresh the schedule view
                self.load_project_schedule()
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid date format. Use YYYY-MM-DD")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate cycles: {e}")
        
        ttk.Button(button_frame, text="Generate Cycles", 
                  command=generate_cycles).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side="right")
    def mark_review_issued(self): pass
    def generate_claim(self): pass
    def display_claim(self, claim_data: dict): pass
    def export_claim_csv(self): pass
    def update_all_progress(self): pass
    def update_claims_summary(self): pass
    def clear_all_services(self):
        """Clear all project services after confirmation"""
        if not self.current_project_id:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        if not self.review_service:
            messagebox.showerror("Error", "Review service not available")
            return
        
        # Get current services count for confirmation
        try:
            services = self.review_service.get_project_services(self.current_project_id)
            service_count = len(services)
            
            if service_count == 0:
                messagebox.showinfo("Info", "No services to clear")
                return
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Clear All Services", 
                f"Are you sure you want to delete ALL {service_count} services for this project?\n\n"
                f"This action cannot be undone."):
                return
            
            # Clear services
            cleared_count = self.review_service.clear_all_project_services(self.current_project_id)
            
            if cleared_count > 0:
                messagebox.showinfo("Success", f"Cleared {cleared_count} services")
                # Refresh the scope display
                self.load_project_scope()
                self.status_var.set(f"Cleared {cleared_count} services")
            else:
                messagebox.showwarning("Warning", "No services were cleared")
                
        except Exception as e:
            print(f"❌ Error clearing services: {e}")
            messagebox.showerror("Error", f"Failed to clear services: {str(e)}")
    
    def setup_scope_context_menu(self):
        """Setup right-click context menu for scope tree"""
        self.scope_context_menu = tk.Menu(self.scope_tree, tearoff=0)
        self.scope_context_menu.add_command(label="🗑️ Remove Service", command=self.remove_selected_service)
        self.scope_context_menu.add_separator()
        self.scope_context_menu.add_command(label="� Refresh", command=self.load_project_scope)
        self.scope_context_menu.add_separator()
        self.scope_context_menu.add_command(label="� Double-click any cell to edit", state="disabled")
        
        # Bind right-click event
        self.scope_tree.bind("<Button-3>", self.show_scope_context_menu)
    
    def setup_inline_editing(self):
        """Setup inline editing for scope tree"""
        # Bind double-click event for editing
        self.scope_tree.bind("<Double-1>", self.on_item_double_click)
        
        # Track current edit widget
        self.current_edit_widget = None
        self.current_edit_item = None
        self.current_edit_column = None
        
        # Define which columns are editable and their types
        self.editable_columns = {
            "Phase": "dropdown",
            "Service": "text", 
            "Type": "dropdown",
            "Qty": "number",
            "Rate": "number",
            "Status": "dropdown"
        }
        
        # Define dropdown values for each column
        self.dropdown_values = {
            "Phase": [
                "Phase 1 - Concept Design",
                "Phase 2 - Schematic Design", 
                "Phase 3 - Design Development",
                "Phase 4/5 - Digital Initiation",
                "Phase 4/5 - Digital Production",
                "Phase 6 - Construction Documentation",
                "Phase 7 - Digital Production",
                "Phase 8 - Digital Handover",
                "Phase 9 - Post-Occupancy"
            ],
            "Type": ["lump_sum", "review", "drawing", "area", "linear", "hourly"],
            "Status": ["Active", "On Hold", "Completed", "Cancelled"]
        }
    
    def on_item_double_click(self, event):
        """Handle double-click on tree item for inline editing"""
        # Close any existing edit widget
        self.close_edit_widget()
        
        # Get the item and column that was clicked
        item = self.scope_tree.selection()[0] if self.scope_tree.selection() else None
        if not item:
            return
        
        # Get the column that was clicked
        column = self.scope_tree.identify_column(event.x)
        if not column:
            return
        
        # Convert column number to column name
        column_index = int(column.replace('#', '')) - 1
        column_names = list(self.scope_tree['columns'])
        if column_index >= len(column_names):
            return
        
        column_name = column_names[column_index]
        
        # Check if this column is editable
        if column_name not in self.editable_columns:
            return
        
        # Get current value
        current_value = self.scope_tree.item(item, 'values')[column_index]
        
        # Create edit widget
        self.create_edit_widget(item, column_name, column_index, current_value, event)
    
    def create_edit_widget(self, item, column_name, column_index, current_value, event):
        """Create appropriate edit widget based on column type"""
        # Get the bounding box of the cell
        x, y, width, height = self.scope_tree.bbox(item, column_name)
        
        # Adjust coordinates relative to the tree widget
        x += self.scope_tree.winfo_x()
        y += self.scope_tree.winfo_y()
        
        # Store current edit info
        self.current_edit_item = item
        self.current_edit_column = column_index
        
        edit_type = self.editable_columns[column_name]
        
        if edit_type == "dropdown":
            # Create combobox for dropdown columns
            self.current_edit_widget = ttk.Combobox(
                self.scope_tree.master,
                values=self.dropdown_values[column_name],
                font=("Arial", 9)
            )
            self.current_edit_widget.set(current_value)
            self.current_edit_widget.place(x=x, y=y, width=width, height=height)
            self.current_edit_widget.bind('<Return>', self.save_edit)
            self.current_edit_widget.bind('<Escape>', self.cancel_edit)
            self.current_edit_widget.bind('<FocusOut>', self.save_edit)
            
        elif edit_type in ["text", "number"]:
            # Create entry for text/number columns
            self.current_edit_widget = tk.Entry(
                self.scope_tree.master,
                font=("Arial", 9)
            )
            self.current_edit_widget.insert(0, current_value)
            self.current_edit_widget.place(x=x, y=y, width=width, height=height)
            self.current_edit_widget.bind('<Return>', self.save_edit)
            self.current_edit_widget.bind('<Escape>', self.cancel_edit)
            self.current_edit_widget.bind('<FocusOut>', self.save_edit)
            
            # Select all text for easy editing
            self.current_edit_widget.select_range(0, tk.END)
        
        # Focus the widget
        self.current_edit_widget.focus_set()
    
    def save_edit(self, event=None):
        """Save the edited value and update the service"""
        if not self.current_edit_widget or not self.current_edit_item:
            return
        
        try:
            # Get the new value
            new_value = self.current_edit_widget.get()
            
            # Get the service ID from the item tags
            service_id = int(self.scope_tree.item(self.current_edit_item, 'tags')[0])
            
            # Get current service data
            services = self.review_service.get_project_services(self.current_project_id)
            service = next((s for s in services if s['service_id'] == service_id), None)
            
            if not service:
                messagebox.showerror("Error", "Service not found")
                self.close_edit_widget()
                return
            
            # Map column index to field name
            column_names = list(self.scope_tree['columns'])
            column_name = column_names[self.current_edit_column]
            
            # Update the appropriate field
            update_data = dict(service)  # Copy current service data
            
            if column_name == "Phase":
                update_data['phase'] = new_value
            elif column_name == "Service":
                update_data['service_name'] = new_value
            elif column_name == "Type":
                update_data['unit_type'] = new_value
            elif column_name == "Qty":
                try:
                    update_data['unit_qty'] = float(new_value) if new_value else 1
                    # Recalculate agreed fee if not lump sum
                    if update_data['unit_type'] != 'lump_sum':
                        qty = float(update_data['unit_qty'])
                        rate = float(update_data['unit_rate'] or 0)
                        update_data['agreed_fee'] = qty * rate
                except ValueError:
                    messagebox.showerror("Error", "Invalid quantity format")
                    self.close_edit_widget()
                    return
            elif column_name == "Rate":
                try:
                    # Extract numeric value from currency format
                    rate_str = new_value.replace('$', '').replace(',', '')
                    update_data['unit_rate'] = float(rate_str) if rate_str else 0
                    # Recalculate agreed fee if not lump sum
                    if update_data['unit_type'] != 'lump_sum':
                        qty = float(update_data['unit_qty'] or 1)
                        rate = float(update_data['unit_rate'])
                        update_data['agreed_fee'] = qty * rate
                except ValueError:
                    messagebox.showerror("Error", "Invalid rate format")
                    self.close_edit_widget()
                    return
            elif column_name == "Status":
                update_data['status'] = new_value
            
            # Update the service in database
            success = self.review_service.update_project_service(service_id, update_data)
            
            if success:
                # Refresh the display to show updated values
                self.load_project_scope()
                self.status_var.set(f"Updated {column_name}: {new_value}")
            else:
                messagebox.showerror("Error", "Failed to update service")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save edit: {e}")
        
        finally:
            self.close_edit_widget()
    
    def cancel_edit(self, event=None):
        """Cancel the current edit operation"""
        self.close_edit_widget()
    
    def close_edit_widget(self):
        """Close and cleanup the current edit widget"""
        if self.current_edit_widget:
            self.current_edit_widget.destroy()
            self.current_edit_widget = None
            self.current_edit_item = None
            self.current_edit_column = None
    
    def show_scope_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under cursor
        item = self.scope_tree.identify_row(event.y)
        if item:
            self.scope_tree.selection_set(item)
            self.scope_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_service_id(self):
        """Get the service_id of the selected item in scope tree"""
        selection = self.scope_tree.selection()
        if not selection:
            return None
        
        # Get the service_id from the tags
        item = selection[0]
        tags = self.scope_tree.item(item, 'tags')
        if tags:
            return int(tags[0])
        return None
    
    def remove_selected_service(self):
        """Remove the selected service"""
        service_id = self.get_selected_service_id()
        if not service_id:
            messagebox.showwarning("Warning", "Please select a service to remove")
            return
        
        if not self.review_service:
            messagebox.showerror("Error", "Review service not available")
            return
        
        # Get service details for confirmation
        try:
            services = self.review_service.get_project_services(self.current_project_id)
            service = next((s for s in services if s['service_id'] == service_id), None)
            
            if not service:
                messagebox.showerror("Error", "Service not found")
                return
            
            # Confirm deletion
            service_name = service.get('service_name', 'Unknown Service')
            agreed_fee = service.get('agreed_fee', 0)
            
            if not messagebox.askyesno("Confirm Remove Service", 
                f"Are you sure you want to remove this service?\n\n"
                f"Service: {service_name}\n"
                f"Agreed Fee: ${agreed_fee:,.0f}\n\n"
                f"This action cannot be undone."):
                return
            
            # Remove service
            if self.review_service.delete_project_service(service_id):
                messagebox.showinfo("Success", f"Removed service: {service_name}")
                # Refresh the scope display
                self.load_project_scope()
                self.status_var.set(f"Removed service: {service_name}")
            else:
                messagebox.showerror("Error", "Failed to remove service")
                
        except Exception as e:
            print(f"❌ Error removing service: {e}")
            messagebox.showerror("Error", f"Failed to remove service: {str(e)}")
    
    def add_service(self):
        """Add a new service (placeholder for now)"""
        messagebox.showinfo("Feature", "Add Service dialog will be implemented")
    
    def edit_selected_service(self):
        """Edit the selected service with comprehensive dialog"""
        service_id = self.get_selected_service_id()
        if not service_id:
            messagebox.showwarning("Warning", "Please select a service to edit")
            return
        
        if not self.review_service:
            messagebox.showerror("Error", "Review service not available")
            return
        
        try:
            # Get current service data
            services = self.review_service.get_project_services(self.current_project_id)
            service = next((s for s in services if s['service_id'] == service_id), None)
            
            if not service:
                messagebox.showerror("Error", "Service not found")
                return
            
            # Show edit dialog
            self.show_edit_service_dialog(service)
            
        except Exception as e:
            print(f"❌ Error loading service for edit: {e}")
            messagebox.showerror("Error", f"Failed to load service: {str(e)}")
    
    def show_edit_service_dialog(self, service):
        """Show comprehensive service edit dialog"""
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Edit Service - {service['service_name']}")
        dialog.geometry("600x700")
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()
        
        # Main frame with scrollbar
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Service edit form
        form_frame = ttk.LabelFrame(scrollable_frame, text="Service Details", padding=20)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Phase dropdown
        ttk.Label(form_frame, text="Phase:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        phase_var = tk.StringVar(value=service['phase'] or '')
        phase_values = [
            "Phase 1 - Concept Design",
            "Phase 2 - Schematic Design", 
            "Phase 3 - Design Development",
            "Phase 4/5 - Digital Initiation",
            "Phase 4/5 - Digital Production",
            "Phase 6 - Construction Documentation",
            "Phase 7 - Digital Production",
            "Phase 8 - Digital Handover",
            "Phase 9 - Post-Occupancy"
        ]
        phase_combo = ttk.Combobox(form_frame, textvariable=phase_var, values=phase_values, width=40)
        phase_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Service Code dropdown
        ttk.Label(form_frame, text="Service Code:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        service_code_var = tk.StringVar(value=service['service_code'] or '')
        service_codes = list(self.service_codes.keys())
        service_code_combo = ttk.Combobox(form_frame, textvariable=service_code_var, values=service_codes, width=15)
        service_code_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Service Name
        ttk.Label(form_frame, text="Service Name:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        service_name_var = tk.StringVar(value=service['service_name'] or '')
        service_name_entry = ttk.Entry(form_frame, textvariable=service_name_var, width=50)
        service_name_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Unit Type dropdown
        ttk.Label(form_frame, text="Unit Type:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        unit_type_var = tk.StringVar(value=service['unit_type'] or 'lump_sum')
        unit_type_combo = ttk.Combobox(form_frame, textvariable=unit_type_var, values=self.unit_types, width=15)
        unit_type_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        unit_type_combo.bind("<<ComboboxSelected>>", lambda e: self.on_unit_type_changed(unit_type_var.get(), unit_qty_var, unit_rate_var, lump_sum_var))
        
        # Quantity
        ttk.Label(form_frame, text="Quantity:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        unit_qty_var = tk.StringVar(value=str(service['unit_qty'] or 1))
        unit_qty_entry = ttk.Entry(form_frame, textvariable=unit_qty_var, width=15)
        unit_qty_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Unit Rate
        ttk.Label(form_frame, text="Unit Rate ($):", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        unit_rate_var = tk.StringVar(value=str(service['unit_rate'] or 0))
        unit_rate_entry = ttk.Entry(form_frame, textvariable=unit_rate_var, width=15)
        unit_rate_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Lump Sum Fee
        ttk.Label(form_frame, text="Lump Sum ($):", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=5)
        lump_sum_var = tk.StringVar(value=str(service['lump_sum_fee'] or 0))
        lump_sum_entry = ttk.Entry(form_frame, textvariable=lump_sum_var, width=15)
        lump_sum_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        
        # Bill Rule dropdown
        ttk.Label(form_frame, text="Bill Rule:", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky="w", pady=5)
        bill_rule_var = tk.StringVar(value=service['bill_rule'] or 'on_delivery')
        bill_rule_combo = ttk.Combobox(form_frame, textvariable=bill_rule_var, values=self.bill_rules, width=20)
        bill_rule_combo.grid(row=7, column=1, sticky="w", padx=5, pady=5)
        
        # Status dropdown
        ttk.Label(form_frame, text="Status:", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w", pady=5)
        status_var = tk.StringVar(value=service['status'] or 'Active')
        status_values = ["Active", "On Hold", "Completed", "Cancelled"]
        status_combo = ttk.Combobox(form_frame, textvariable=status_var, values=status_values, width=15)
        status_combo.grid(row=8, column=1, sticky="w", padx=5, pady=5)
        
        # Progress
        ttk.Label(form_frame, text="Progress (%):", font=("Arial", 10, "bold")).grid(row=9, column=0, sticky="w", pady=5)
        progress_var = tk.StringVar(value=str(service['progress_pct'] or 0))
        progress_entry = ttk.Entry(form_frame, textvariable=progress_var, width=15)
        progress_entry.grid(row=9, column=1, sticky="w", padx=5, pady=5)
        
        # Claimed to Date
        ttk.Label(form_frame, text="Claimed ($):", font=("Arial", 10, "bold")).grid(row=10, column=0, sticky="w", pady=5)
        claimed_var = tk.StringVar(value=str(service['claimed_to_date'] or 0))
        claimed_entry = ttk.Entry(form_frame, textvariable=claimed_var, width=15)
        claimed_entry.grid(row=10, column=1, sticky="w", padx=5, pady=5)
        
        # Notes
        ttk.Label(form_frame, text="Notes:", font=("Arial", 10, "bold")).grid(row=11, column=0, sticky="nw", pady=5)
        notes_text = tk.Text(form_frame, height=4, width=50)
        notes_text.grid(row=11, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        notes_text.insert("1.0", service['notes'] or '')
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def save_service():
            try:
                # Validate and collect data
                unit_qty = float(unit_qty_var.get()) if unit_qty_var.get() else 1
                unit_rate = float(unit_rate_var.get()) if unit_rate_var.get() else 0
                lump_sum = float(lump_sum_var.get()) if lump_sum_var.get() else 0
                progress = float(progress_var.get()) if progress_var.get() else 0
                claimed = float(claimed_var.get()) if claimed_var.get() else 0
                
                # Calculate agreed fee based on unit type
                if unit_type_var.get() == 'lump_sum':
                    agreed_fee = lump_sum
                else:
                    agreed_fee = unit_qty * unit_rate
                
                # Update service in database
                success = self.review_service.update_project_service(service['service_id'], {
                    'phase': phase_var.get(),
                    'service_code': service_code_var.get(),
                    'service_name': service_name_var.get(),
                    'unit_type': unit_type_var.get(),
                    'unit_qty': unit_qty,
                    'unit_rate': unit_rate,
                    'lump_sum_fee': lump_sum,
                    'agreed_fee': agreed_fee,
                    'bill_rule': bill_rule_var.get(),
                    'status': status_var.get(),
                    'progress_pct': progress,
                    'claimed_to_date': claimed,
                    'notes': notes_text.get("1.0", "end-1c")
                })
                
                if success:
                    messagebox.showinfo("Success", "Service updated successfully!")
                    dialog.destroy()
                    self.load_project_scope()  # Refresh the display
                    self.status_var.set(f"Updated service: {service_name_var.get()}")
                else:
                    messagebox.showerror("Error", "Failed to update service")
                    
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid number format: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save service: {e}")
        
        def cancel_edit():
            dialog.destroy()
        
        ttk.Button(button_frame, text="💾 Save Changes", command=save_service).pack(side="left", padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=cancel_edit).pack(side="left", padx=5)
        
        # Set initial state based on unit type
        self.on_unit_type_changed(unit_type_var.get(), unit_qty_var, unit_rate_var, lump_sum_var)
    
    def on_unit_type_changed(self, unit_type, unit_qty_var, unit_rate_var, lump_sum_var):
        """Handle unit type change to enable/disable appropriate fields"""
        # This method will enable/disable fields based on unit type
        # For now it's a placeholder - full implementation would control field states
        pass
    
    def edit_service_dialog(self, event=None): pass
    def change_schedule_view(self, event=None): pass
    def filter_schedule(self, event=None): pass
    def open_gantt_chart(self): pass
    def edit_review_dialog(self, event=None): pass
    def add_evidence_dialog(self): pass
    def reschedule_dialog(self): pass
    
    def show_scope_context_menu(self, event):
        """Show context menu for scope tree"""
        pass
    
    def show_schedule_context_menu(self, event):
        """Show context menu for schedule tree"""
        pass
    
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

def create_phase1_enhanced_ui(root):
    """Create the Phase 1 enhanced UI with new tabs and existing daily workflow components"""
    
    # Create main notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Add tabs in logical order for daily workflow
    project_setup_tab = ProjectSetupTab(notebook)          # 🏗️ Project Setup - First for project creation/management
    acc_folder_tab = ACCFolderManagementTab(notebook)      # 📂 ACC Folders - Daily ACC operations and data import
    review_management_tab = ReviewManagementTab(notebook)  # 📅 Review Management - Review scheduling and billing
    
    # Add enhanced Phase 1 tabs
    enhanced_tasks_tab = EnhancedTaskManagementTab(notebook)  # 📋 Enhanced Tasks - Advanced task management
    resources_tab = ResourceManagementTab(notebook)          # 👥 Resources - Resource allocation
    
    return notebook

if __name__ == "__main__":
    """Run the Phase 1 Enhanced UI standalone for testing"""
    
    root = tk.Tk()
    root.title("BIM Project Management - Enhanced Phase 1")
    root.geometry("1400x900")
    
    # Create and configure the enhanced UI
    notebook = create_phase1_enhanced_ui(root)
    
    # Start the GUI event loop
    root.mainloop()
