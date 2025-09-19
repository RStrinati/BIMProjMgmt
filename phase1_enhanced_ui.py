import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import threading
import os
import pandas as pd
import logging
import webbrowser
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
    get_review_tasks, get_contractual_links, get_project_bookmarks, add_bookmark,
    update_bookmark, delete_bookmark, get_bookmark_categories
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
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
    clear_treeview,
    format_id_name_list,
    parse_id_from_display,
    set_combo_from_pairs,
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
                    logger.error("Error notifying observer %s: %s", observer, e)
    
    def notify_project_list_changed(self):
        """Notify all registered tabs that the project list has changed"""
        for observer in self.observers:
            try:
                if hasattr(observer, 'on_project_list_changed'):
                    observer.on_project_list_changed()
            except Exception as e:
                logger.error("Error notifying observer %s: %s", observer, e)
    
    def get_current_project(self):
        """Get the currently selected project"""
        return self.current_project

# Global project notification system
project_notification_system = ProjectNotificationSystem()
logger = logging.getLogger(__name__)

class EnhancedTaskManagementTab:
    """Enhanced task management interface with dependencies and progress tracking"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="?? Enhanced Tasks")
        
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
            logger.error("Error showing issues summary: %s", e)
        finally:
            if conn:
                conn.close()
    
    def preview_issues_data(self):
        """Preview issues data from acc_data_schema database"""
        try:
            conn = connect_to_db("acc_data_schema")
            if conn is None:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, "? Cannot connect to acc_data_schema database")
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
            self.preview_text.insert(1.0, f"? Error querying issues data: {str(e)}")
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
        self.sub_notebook.add(service_frame, text="??? Service Setup")
        
        # Project Selection Frame
        project_frame = ttk.LabelFrame(service_frame, text="?? Project Selection", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(project_frame, text="Project:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)
        
        # Service Template Frame
        template_frame = ttk.LabelFrame(service_frame, text="?? Service Templates", padding=10)
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
        services_frame = ttk.LabelFrame(service_frame, text="?? Current Project Services", padding=10)
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
        ttk.Button(service_buttons_frame, text="Generate Reviews", command=self.generate_reviews_from_services).pack(side=tk.LEFT, padx=5)
    

    def setup_review_planning_tab(self):
        """Setup the Review Planning & Scheduling tab with column layout."""
        planning_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(planning_frame, text="?? Review Planning")

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

        cadence_frame = ttk.LabelFrame(context_column, text="?? Cadence Defaults", padding=10)
        cadence_frame.pack(fill=tk.X, expand=False, pady=(12, 0))

        ttk.Label(cadence_frame, text="Default Start Date:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.review_start_date = DateEntry(cadence_frame, width=14, date_pattern='yyyy-mm-dd')
        self.review_start_date.grid(row=0, column=1, sticky="w", pady=2)

        ttk.Label(cadence_frame, text="Default Frequency:").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.default_frequency_var = tk.StringVar(value="weekly")
        ttk.Combobox(
            cadence_frame,
            textvariable=self.default_frequency_var,
            values=["weekly", "bi-weekly", "monthly", "as-required"],
            state="readonly",
            width=12
        ).grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(cadence_frame, text="Default Review Count:").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=2)
        self.default_review_count_var = tk.StringVar(value="4")
        ttk.Entry(cadence_frame, textvariable=self.default_review_count_var, width=6).grid(row=2, column=1, sticky="w", pady=2)

        for col in range(2):
            cadence_frame.columnconfigure(col, weight=1)

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
                  command=self.generate_reviews_from_services_planning).pack(side=tk.LEFT)

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

        cycle_columns = ("Review ID", "Cycle", "Meeting Date", "Due Date", "Actual Start", "Actual End", "Status", "Stage", "Reviewer", "Notes")
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
        """Setup the Review Execution & Tracking tab"""
        tracking_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(tracking_frame, text="?? Review Tracking")
        
        # Summary Frame
        summary_frame = ttk.LabelFrame(tracking_frame, text="?? Project Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Summary fields
        self.summary_vars = {}
        summary_fields = [
            ("Project Name", 0, 0), ("Current Cycle", 0, 2),
            ("Construction Stage", 1, 0), ("License Duration", 1, 2),
            ("Total Services", 2, 0), ("Active Reviews", 2, 2),
            ("Completed Reviews", 3, 0), ("Overall Progress", 3, 2)
        ]

        # Define filter variables
        required_skills = self.skills_entry.get().strip() if hasattr(self, 'skills_entry') else ''
        role_level = self.role_var.get().strip() if hasattr(self, 'role_var') else ''
        try:
            max_utilization = float(self.max_util_var.get()) if hasattr(self, 'max_util_var') else 100
        except Exception:
            max_utilization = 80.0

        status_colors = {
            'Overallocated': '??',
            'High': '??',
            'Medium': '??',
            'Low': '??'
        }

        # Get resources and populate tree
        if self.resource_mgr:
            resources = self.resource_mgr.get_resource_workload(
                start_date=datetime.combine(datetime.now(), datetime.min.time()),
                end_date=datetime.combine(datetime.now() + timedelta(days=30), datetime.min.time())
            )
        else:
            resources = []  # Empty list if resource manager not available
            
        # Only try to update tree if it exists
        if hasattr(self, 'resource_tree'):
            self.resource_tree.delete(*self.resource_tree.get_children())
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

        # Add button frame below text widget
        button_frame2 = ttk.Frame(result_window)
        button_frame2.pack(fill="x", pady=(10, 0))
        ttk.Button(button_frame2, text="?? Open Revizto Exporter", 
                command=getattr(self, 'open_revizto_exporter', lambda: None)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame2, text="?? Update Review Status", 
                command=getattr(self, 'update_review_status', lambda: None)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame2, text="?? Refresh All Data", 
                command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        
        # Review Tasks Frame
        tasks_frame = ttk.LabelFrame(tracking_frame, text="?? Active Review Tasks", padding=10)
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
        self.sub_notebook.add(billing_frame, text="?? Billing")
        
        # Billing Claims Frame
        claims_frame = ttk.LabelFrame(billing_frame, text="?? Billing Claims", padding=10)
        claims_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Claims treeview
        claim_columns = ("Claim ID", "Period Start", "Period End", "PO Ref", "Invoice Ref", "Status", "Total Amount")
        self.claims_tree = ttk.Treeview(claims_frame, columns=claim_columns, show="headings", height=6)
        
        for col in claim_columns:
            self.claims_tree.heading(col, text=col)
            self.claims_tree.column(col, width=120, anchor="w")
        
        self.claims_tree.pack(fill=tk.BOTH, expand=True)
        
        # Service Progress Frame
        progress_frame = ttk.LabelFrame(billing_frame, text="?? Service Progress & Billing", padding=10)
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
            
            if project_list:
                if not self.project_var.get():
                    self.project_combo.current(0)
                self.on_project_selected()
                
        except Exception as e:
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
                db_conn = connect_to_db()
                if db_conn:
                    self.review_service = ReviewManagementService(db_conn)
                    print(f"? Review service initialized for project {self.current_project_id}")
                else:
                    print("? Failed to connect to database for review service")
                    self.review_service = None
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
            
            # NOTE: Removed automatic sync of stages and cycles on project change
            # Users can manually trigger this via "Load Stages from Services" button
            # self.auto_update_stages_and_cycles()
            
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
            print(f"Error in auto_update_stages_and_cycles: {e}")
    
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
                        frequency = "as-required"
                    elif "handover" in phase.lower() or "completion" in phase.lower():
                        frequency = "as-required"
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

            print(f"🔄 Generating review cycles from {len(review_services)} review services...")
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id)

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
    
    def load_project_services(self):
        """Load project services into the services tree"""
        try:
            # Prevent concurrent refreshes
            if hasattr(self, '_refreshing_services') and self._refreshing_services:
                return
            self._refreshing_services = True
            
            # Clear existing services
            for item in self.services_tree.get_children():
                self.services_tree.delete(item)

            if not self.current_project_id or not self.review_service:
                self._refreshing_services = False
                return

            # Get project services
            services = self.review_service.get_project_services(self.current_project_id)

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
            
            self._refreshing_services = False

        except Exception as e:
            print(f"Error loading project services: {e}")
            self._refreshing_services = False
    
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
            
            # Generate reviews
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id)
            
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

                # Calculate completion percentage (placeholder - would need actual progress data)
                # For now, show 0% or get from service status
                status_percent = "0%"  # TODO: Calculate actual completion percentage

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
            
            # Generate reviews
            reviews_created = self.review_service.generate_service_reviews(self.current_project_id)
            
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
            if frequency == 'weekly':
                weeks = duration_days / 7
                return str(max(1, int(weeks)))
            elif frequency == 'bi-weekly':
                biweeks = duration_days / 14
                return str(max(1, int(biweeks)))
            elif frequency == 'monthly':
                months = duration_days / 30
                return str(max(1, int(months)))
            else:
                return "1"  # Default for as-required or unknown

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

                due_display = cycle[4] or ""
                due_flag = False
                if due_display:
                    try:
                        # Handle both string and date object types
                        if isinstance(due_display, str):
                            due_date = datetime.strptime(due_display, '%Y-%m-%d').date()
                        elif isinstance(due_display, datetime):
                            due_date = due_display.date()
                        else:
                            due_date = due_display  # Assume it's already a date object
                        
                        if due_date <= today and cycle_status not in completed_states:
                            due_flag = True
                            
                            # Automatically update status based on due date
                            current_status = cycle[5] or ""
                            if current_status in ['planned', 'in_progress']:
                                # Update to completed if past due
                                success = self.review_service.update_review_status_to(cycle[0], 'completed')
                                if success:
                                    cycle_status = 'completed'
                                    # Update the cycle tuple for display
                                    cycle = list(cycle)
                                    cycle[5] = 'completed'
                                    cycle = tuple(cycle)
                        elif due_date <= today + timedelta(days=7) and (cycle[5] or "") == 'planned':
                            # Update to in_progress if due within 7 days
                            success = self.review_service.update_review_status_to(cycle[0], 'in_progress')
                            if success:
                                cycle_status = 'in_progress'
                                # Update the cycle tuple for display
                                cycle = list(cycle)
                                cycle[5] = 'in_progress'
                                cycle = tuple(cycle)
                    except (ValueError, AttributeError):
                        pass

                notes = "Due for confirmation" if due_flag else ""

                formatted_cycle = (
                    str(cycle[0]),
                    f"{cycle[1]} - Cycle {cycle_no}",
                    cycle[3] or "",
                    due_display,
                    "",
                    "",
                    cycle[5] or "",
                    cycle[6] if len(cycle) > 6 and cycle[6] else "All",
                    "",
                    notes
                )
                self.cycles_tree.insert("", tk.END, values=formatted_cycle)

                if due_flag:
                    self.auto_complete_candidates.append({
                        'review_id': cycle[0],
                        'label': formatted_cycle[1],
                        'due_date': due_display,
                        'status': cycle[5] or ''
                    })

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

            for item in self.claims_tree.get_children():
                self.claims_tree.delete(item)

            for item in self.progress_tree.get_children():
                self.progress_tree.delete(item)

            if not self.current_project_id or not self.review_service:
                return

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
        except Exception as e:
            print(f"Error loading billing data: {e}")

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
            phase_entry = ttk.Entry(form_frame, textvariable=phase_var, width=40)
            phase_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 10), pady=2)
            row += 1

            ttk.Label(form_frame, text="Service Code:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            ttk.Entry(form_frame, textvariable=service_code_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=2)
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
            frequency_combo['values'] = ['weekly', 'bi-weekly', 'monthly']
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

            phase_entry.focus()
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
            
            # Load the full service data from database
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
                    from review_management_service import ReviewManagementService
                    db_conn = connect_to_db()
                    if db_conn:
                        service = ReviewManagementService(db_conn)
                        success = service.update_review_status_to(review_id, new_status, evidence_link)
                    else:
                        messagebox.showerror("Error", "Could not connect to database")
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
            ttk.Label(main_frame, text="Meeting Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
            start_date_var = tk.StringVar(value=planned_start)
            start_date_entry = DateEntry(main_frame, textvariable=start_date_var, width=12, 
                                       background='darkblue', foreground='white', 
                                       borderwidth=2, date_pattern='yyyy-mm-dd')
            start_date_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            
            # Planned end date
            ttk.Label(main_frame, text="Due Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
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
            
            print(f"? Deleted {reviews_deleted} reviews and {services_deleted} auto-generated services")
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


class ProjectSetupTab:
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
            ("Refresh Project Data", self.refresh_data, "Reload project information from database"),
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

        # Simple project details content
        ttk.Label(details_frame, text="Project information will be displayed here",
                 font=("Arial", 12)).pack(pady=50)

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
        """Configure file paths for the current project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        # TODO: Implement path configuration dialog
        messagebox.showinfo("Info", "Path configuration not yet implemented")

    def extract_model_files(self):
        """Extract files from configured model folder"""
        # TODO: Implement model file extraction
        messagebox.showinfo("Info", "Model file extraction not yet implemented")

    def extract_acc_files(self):
        """Extract files from ACC Desktop Connector"""
        # TODO: Implement ACC file extraction
        messagebox.showinfo("Info", "ACC file extraction not yet implemented")

    def refresh_data(self):
        """Reload project information from database"""
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

    def debug_dropdown(self):
        """Debug project dropdown issues"""
        project_count = len(self.project_combo['values']) if self.project_combo['values'] else 0
        current_selection = self.project_var.get()
        messagebox.showinfo("Debug Info", f"Projects in dropdown: {project_count}\nCurrent selection: '{current_selection}'")

    def view_dashboard(self):
        """Open comprehensive project overview"""
        # TODO: Implement project dashboard
        messagebox.showinfo("Info", "Project dashboard not yet implemented")

    def archive_project(self):
        """Archive completed or cancelled project"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        # TODO: Implement project archiving
        messagebox.showinfo("Info", "Project archiving not yet implemented")

    def delete_project(self):
        """Delete the selected project and all related data"""
        if not self.project_var.get():
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        project_selection = self.project_var.get()
        
        # Parse project ID and name from "ID - Name" format
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
        
        # Show confirmation dialog
        confirm_msg = (f"Are you sure you want to delete project '{project_name}'?\n\n"
                      "This action will permanently delete:\n"
                      "• All project data and settings\n"
                      "• All review cycles and schedules\n"
                      "• All tasks and assignments\n"
                      "• All documents and clauses\n"
                      "• All billing and service data\n"
                      "• All ACC imports and logs\n\n"
                      "This action cannot be undone!")
        
        if not messagebox.askyesno("Confirm Project Deletion", confirm_msg, icon="warning"):
            return
        
        # Additional confirmation
        confirm_again = messagebox.askyesno("Final Confirmation", 
                                          f"Type 'YES' to confirm deletion of '{project_name}':")
        if not confirm_again:
            return
        
        try:
            from database import delete_project
            success = delete_project(project_id)
            
            if success:
                messagebox.showinfo("Success", f"Project '{project_name}' has been deleted successfully.")
                # Clear current selection
                self.project_var.set("")
                # Refresh project list
                self.load_projects()
                # Notify all tabs that the project list has changed
                project_notification_system.notify_project_list_changed()
            else:
                messagebox.showerror("Error", "Failed to delete project. Please check the logs for details.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete project: {str(e)}")

    def load_projects(self):
        """Load available projects into the dropdown"""
        try:
            from database import get_projects
            projects = get_projects()
            project_options = [f"{p[0]} - {p[1]}" for p in projects] if projects else []  # Use "ID - Name" format like other tabs
            self.project_combo['values'] = project_options
            print(f"Loaded {len(project_options)} projects: {project_options[:3]}...")  # Show first 3
            # Also show in a message box for debugging
            if not project_options:
                messagebox.showwarning("No Projects", "No projects found in database")
            else:
                messagebox.showinfo("Projects Loaded", f"Loaded {len(project_options)} projects")
        except Exception as e:
            print(f"Error loading projects: {e}")
            messagebox.showerror("Error", f"Failed to load projects: {e}")
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
            from database import insert_project_full

            # Prepare complete project data for insert_project_full
            db_data = {
                S.Projects.NAME: project_data['name'],
                S.Projects.FOLDER_PATH: project_data.get('folder_path', ''),
                S.Projects.IFC_FOLDER_PATH: project_data.get('ifc_folder_path', ''),
                S.Projects.START_DATE: project_data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                S.Projects.END_DATE: project_data.get('end_date', (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
            }

            # Add optional fields if provided
            if project_data.get('client_id'):
                db_data[S.Projects.CLIENT_ID] = project_data['client_id']
            if project_data.get('status'):
                db_data[S.Projects.STATUS] = project_data['status']
            if project_data.get('priority'):
                # Map priority strings to numeric values
                priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
                db_data[S.Projects.PRIORITY] = priority_map.get(project_data['priority'], 2)  # Default to Medium
            
            # Insert the project
            project_id = insert_project_full(db_data)
            
            if project_id:
                messagebox.showinfo("Success", f"Project created successfully! (ID: {project_id})")
                # Refresh the project list
                self.load_projects()
                return project_id
            else:
                messagebox.showerror("Error", "Failed to create project")
                return None
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create project: {str(e)}")
            print(f"Project creation error: {e}")
            return None

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
            from database import insert_project_full

            # Prepare complete project data for insert_project_full
            db_data = {
                S.Projects.NAME: project_data['name'],
                S.Projects.FOLDER_PATH: project_data.get('folder_path', ''),
                S.Projects.IFC_FOLDER_PATH: project_data.get('ifc_folder_path', ''),
                S.Projects.START_DATE: project_data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                S.Projects.END_DATE: project_data.get('end_date', (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
            }

            # Add optional fields if provided
            if project_data.get('client_id'):
                db_data[S.Projects.CLIENT_ID] = project_data['client_id']
            if project_data.get('status'):
                db_data[S.Projects.STATUS] = project_data['status']
            if project_data.get('priority'):
                # Map priority strings to numeric values
                priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
                db_data[S.Projects.PRIORITY] = priority_map.get(project_data['priority'], 2)  # Default to Medium

            # Add project type if provided (this would need mapping to type_id)
            # For now, store as a comment or handle in future enhancement
            if project_data.get('project_type'):
                # TODO: Map project_type to type_id from project_types table
                pass

            # Add capacity/area information (these might need new columns or separate tables)
            if project_data.get('area'):
                db_data[S.Projects.AREA_HECTARES] = project_data['area']
            if project_data.get('mw_capacity'):
                db_data[S.Projects.MW_CAPACITY] = project_data['mw_capacity']

            # Add location information (these might need new columns)
            if project_data.get('address'):
                db_data[S.Projects.ADDRESS] = project_data['address']
            if project_data.get('city'):
                db_data[S.Projects.CITY] = project_data['city']
            if project_data.get('state'):
                db_data[S.Projects.STATE] = project_data['state']
            if project_data.get('postcode'):
                db_data[S.Projects.POSTCODE] = project_data['postcode']

            # Use insert_project_full for complete project creation
            success = insert_project_full(db_data)

            if success:
                print(f"✅ Successfully created project: {project_data['name']}")
                return True
            else:
                print(f"❌ Failed to create project: {project_data['name']}")
                return False

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
            
            print(f"? Successfully updated project {project_id}")
            return True
            
        except Exception as e:
            print(f"? Error updating project {project_id}: {e}")
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
    
    def on_project_selected_local(self, event=None):
        """Handle local project selection and update scope/schedule"""
        try:
            selected = self.project_var.get()
            if not selected:
                return
            
            self.current_project_id = int(selected.split(" - ")[0])
            print(f"?? Loading project data for: {selected}")
            
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
        
        # Toolbar
        toolbar_frame = ttk.Frame(bookmarks_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="Add Bookmark", command=self.add_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Edit Bookmark", command=self.edit_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Delete Bookmark", command=self.delete_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Open in Browser", command=self.open_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Refresh", command=self.refresh_bookmarks).pack(side=tk.RIGHT, padx=5)
        
        # Bookmarks Treeview
        columns = ("Name", "URL", "Description", "Category", "Created")
        self.bookmarks_tree = ttk.Treeview(bookmarks_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.bookmarks_tree.heading("Name", text="Name")
        self.bookmarks_tree.column("Name", width=200)
        
        self.bookmarks_tree.heading("URL", text="URL")
        self.bookmarks_tree.column("URL", width=300)
        
        self.bookmarks_tree.heading("Description", text="Description")
        self.bookmarks_tree.column("Description", width=250)
        
        self.bookmarks_tree.heading("Category", text="Category")
        self.bookmarks_tree.column("Category", width=100)
        
        self.bookmarks_tree.heading("Created", text="Created")
        self.bookmarks_tree.column("Created", width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(bookmarks_frame, orient=tk.VERTICAL, command=self.bookmarks_tree.yview)
        h_scrollbar = ttk.Scrollbar(bookmarks_frame, orient=tk.HORIZONTAL, command=self.bookmarks_tree.xview)
        self.bookmarks_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.bookmarks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to open bookmark
        self.bookmarks_tree.bind("<Double-1>", lambda e: self.open_bookmark())
    
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
        """Refresh the bookmarks list"""
        if not self.current_project_id or not self.bookmarks_tree:
            return
        
        # Clear existing items
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)
        
        # Get bookmarks
        bookmarks = get_project_bookmarks(self.current_project_id)
        
        # Group by category
        categories = {}
        for bookmark in bookmarks:
            category = bookmark['category'] or 'Uncategorized'
            if category not in categories:
                categories[category] = []
            categories[category].append(bookmark)
        
        # Add to treeview
        for category, category_bookmarks in categories.items():
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
                        created_at_str
                    ),
                    tags=(str(bookmark['id']),)
                )
    
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
        
        ttk.Label(dialog, text="Description:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, height=5, width=40)
        desc_text.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        dialog.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def save_bookmark():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get().strip() or "General"
            description = desc_text.get(1.0, tk.END).strip()
            
            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required.")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            success = add_bookmark(self.current_project_id, name, url, description, category)
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
        
        ttk.Label(dialog, text="Description:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, height=5, width=40)
        desc_text.insert(1.0, values[2])
        desc_text.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        dialog.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def update_bookmark_data():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get().strip() or "General"
            description = desc_text.get(1.0, tk.END).strip()
            
            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required.")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            success = update_bookmark(bookmark_id, name=name, url=url, description=description, category=category)
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