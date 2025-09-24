"""
Project Alias Management Tab

This module provides a comprehensive UI for managing project aliases that map
internal project names to external system names (Revizto, ACC, etc.).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from services.project_alias_service import ProjectAliasManager
from database import get_projects
from ui.ui_helpers import format_id_name_list

class ProjectAliasManagementTab:
    """Tab for managing project aliases and mappings"""
    
    def __init__(self, parent_notebook):
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="🔗 Project Aliases")
        
        self.alias_manager = ProjectAliasManager()
        self.current_aliases = []
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Controls and Statistics
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=1)
        
        # Control buttons frame
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Refresh", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="➕ Add Alias", 
                  command=self.show_add_alias_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="✏️ Edit Selected", 
                  command=self.edit_selected_alias).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🗑️ Delete Selected", 
                  command=self.delete_selected_alias).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(control_frame, text="📊 Validate Aliases", 
                  command=self.validate_aliases).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🔍 Discover Unmapped", 
                  command=self.discover_unmapped).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(control_frame, text="📤 Export CSV", 
                  command=self.export_csv).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="📥 Import CSV", 
                  command=self.import_csv).pack(side=tk.LEFT, padx=(0, 5))
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(top_frame, text="📊 Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.stats_text.pack(fill=tk.X)
        
        # Middle section - Alias table
        middle_frame = ttk.Frame(main_paned)
        main_paned.add(middle_frame, weight=3)
        
        # Alias list
        alias_list_frame = ttk.LabelFrame(middle_frame, text="🏷️ Project Aliases", padding=5)
        alias_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ('alias_name', 'project_id', 'project_name', 'status', 'issues', 'manager')
        self.alias_tree = ttk.Treeview(alias_list_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.alias_tree.heading('alias_name', text='Alias Name')
        self.alias_tree.heading('project_id', text='Project ID')
        self.alias_tree.heading('project_name', text='Project Name')
        self.alias_tree.heading('status', text='Status')
        self.alias_tree.heading('issues', text='Issues')
        self.alias_tree.heading('manager', text='Manager')
        
        self.alias_tree.column('alias_name', width=250)
        self.alias_tree.column('project_id', width=80)
        self.alias_tree.column('project_name', width=150)
        self.alias_tree.column('status', width=100)
        self.alias_tree.column('issues', width=100)
        self.alias_tree.column('manager', width=150)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(alias_list_frame, orient=tk.VERTICAL, command=self.alias_tree.yview)
        h_scrollbar = ttk.Scrollbar(alias_list_frame, orient=tk.HORIZONTAL, command=self.alias_tree.xview)
        self.alias_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.alias_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to edit
        self.alias_tree.bind('<Double-1>', lambda e: self.edit_selected_alias())
        
        # Bottom section - Details and actions
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=2)
        
        # Details notebook
        self.details_notebook = ttk.Notebook(bottom_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Usage statistics tab
        usage_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(usage_frame, text="📈 Usage Statistics")
        
        self.usage_tree = ttk.Treeview(usage_frame, 
                                      columns=('project', 'aliases', 'issues', 'sources'),
                                      show='headings', height=8)
        
        self.usage_tree.heading('project', text='Project')
        self.usage_tree.heading('aliases', text='Alias Count')
        self.usage_tree.heading('issues', text='Total Issues')
        self.usage_tree.heading('sources', text='Has Issues')
        
        usage_scroll = ttk.Scrollbar(usage_frame, orient=tk.VERTICAL, command=self.usage_tree.yview)
        self.usage_tree.configure(yscrollcommand=usage_scroll.set)
        
        self.usage_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        usage_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Unmapped projects tab
        unmapped_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(unmapped_frame, text="❓ Unmapped Projects")
        
        self.unmapped_tree = ttk.Treeview(unmapped_frame,
                                         columns=('project_name', 'issues', 'sources', 'suggested'),
                                         show='headings', height=8)
        
        self.unmapped_tree.heading('project_name', text='Project Name')
        self.unmapped_tree.heading('issues', text='Issues')
        self.unmapped_tree.heading('sources', text='Sources')
        self.unmapped_tree.heading('suggested', text='Suggested Match')
        
        unmapped_scroll = ttk.Scrollbar(unmapped_frame, orient=tk.VERTICAL, command=self.unmapped_tree.yview)
        self.unmapped_tree.configure(yscrollcommand=unmapped_scroll.set)
        
        self.unmapped_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        unmapped_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to create mapping
        self.unmapped_tree.bind('<Double-1>', lambda e: self.create_mapping_from_unmapped())
    
    def load_data(self):
        """Load all alias data"""
        try:
            # Load aliases
            self.current_aliases = self.alias_manager.get_all_aliases()
            self.refresh_alias_tree()
            
            # Load usage statistics
            self.refresh_usage_stats()
            
            # Load unmapped projects
            self.refresh_unmapped_projects()
            
            # Update summary statistics
            self.update_statistics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading alias data: {str(e)}")
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_data()
    
    def refresh_alias_tree(self):
        """Refresh the alias tree view"""
        # Clear existing items
        for item in self.alias_tree.get_children():
            self.alias_tree.delete(item)
        
        # Add aliases
        for alias in self.current_aliases:
            issue_info = f"{alias.get('total_issues', 0)} issues"
            self.alias_tree.insert("", tk.END, values=(
                alias['alias_name'],
                alias['pm_project_id'],
                alias['project_name'],
                alias.get('project_status', 'Unknown'),
                issue_info,
                alias.get('project_manager', 'N/A')
            ))
    
    def refresh_usage_stats(self):
        """Refresh usage statistics"""
        try:
            stats = self.alias_manager.get_alias_usage_stats()
            
            # Clear existing items
            for item in self.usage_tree.get_children():
                self.usage_tree.delete(item)
            
            # Add stats
            for stat in stats:
                self.usage_tree.insert("", tk.END, values=(
                    stat['project_name'],
                    stat['alias_count'],
                    f"{stat['total_issues']} ({stat['open_issues']} open)",
                    "✅" if stat['has_issues'] else "❌"
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading usage stats: {str(e)}")
    
    def refresh_unmapped_projects(self):
        """Refresh unmapped projects"""
        try:
            unmapped = self.alias_manager.discover_unmapped_projects()
            
            # Clear existing items
            for item in self.unmapped_tree.get_children():
                self.unmapped_tree.delete(item)
            
            # Add unmapped projects
            for project in unmapped:
                suggested = project.get('suggested_match')
                suggested_text = suggested['project_name'] if suggested else "No suggestion"
                
                self.unmapped_tree.insert("", tk.END, values=(
                    project['project_name'],
                    f"{project['total_issues']} ({project['open_issues']} open)",
                    project['sources'],
                    suggested_text
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading unmapped projects: {str(e)}")
    
    def update_statistics(self):
        """Update summary statistics"""
        try:
            total_aliases = len(self.current_aliases)
            unique_projects = len(set(alias['pm_project_id'] for alias in self.current_aliases))
            
            # Get validation results
            validation = self.alias_manager.validate_aliases()
            orphaned = len(validation.get('orphaned_aliases', []))
            unused_projects = len(validation.get('unused_projects', []))
            
            # Get unmapped count
            unmapped = len(self.alias_manager.discover_unmapped_projects())
            
            stats_text = f"Total Aliases: {total_aliases} | Projects with Aliases: {unique_projects} | Orphaned: {orphaned} | Unused Projects: {unused_projects} | Unmapped: {unmapped}"
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
    
    def show_add_alias_dialog(self):
        """Show dialog to add a new alias"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Project Alias")
        dialog.geometry("500x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Project selection
        ttk.Label(dialog, text="Select Project:").pack(pady=(10, 5))
        
        project_var = tk.StringVar()
        project_combo = ttk.Combobox(dialog, textvariable=project_var, width=50)
        
        # Load projects
        projects = format_id_name_list(get_projects())
        project_combo['values'] = projects
        project_combo.pack(pady=(0, 10))
        
        # Alias name
        ttk.Label(dialog, text="Alias Name:").pack(pady=(10, 5))
        alias_var = tk.StringVar()
        alias_entry = ttk.Entry(dialog, textvariable=alias_var, width=50)
        alias_entry.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_alias():
            try:
                project_text = project_var.get().strip()
                alias_name = alias_var.get().strip()
                
                if not project_text or not alias_name:
                    messagebox.showerror("Error", "Please fill in all fields")
                    return
                
                # Extract project ID
                project_id = int(project_text.split(' - ')[0])
                
                if self.alias_manager.add_alias(project_id, alias_name):
                    messagebox.showinfo("Success", f"Alias '{alias_name}' added successfully!")
                    dialog.destroy()
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to add alias")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error adding alias: {str(e)}")
        
        ttk.Button(button_frame, text="Save", command=save_alias).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Focus on project combo
        project_combo.focus()
    
    def edit_selected_alias(self):
        """Edit the selected alias"""
        selected = self.alias_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an alias to edit")
            return
        
        item = self.alias_tree.item(selected[0])
        values = item['values']
        
        old_alias_name = values[0]
        current_project_id = values[1]
        
        # Show edit dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Edit Project Alias")
        dialog.geometry("500x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Project selection
        ttk.Label(dialog, text="Select Project:").pack(pady=(10, 5))
        
        project_var = tk.StringVar()
        project_combo = ttk.Combobox(dialog, textvariable=project_var, width=50)
        
        # Load projects and set current
        projects = format_id_name_list(get_projects())
        project_combo['values'] = projects
        
        # Find and set current project
        for project in projects:
            if project.startswith(f"{current_project_id} - "):
                project_var.set(project)
                break
        
        project_combo.pack(pady=(0, 10))
        
        # Alias name
        ttk.Label(dialog, text="Alias Name:").pack(pady=(10, 5))
        alias_var = tk.StringVar(value=old_alias_name)
        alias_entry = ttk.Entry(dialog, textvariable=alias_var, width=50)
        alias_entry.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def update_alias():
            try:
                project_text = project_var.get().strip()
                new_alias_name = alias_var.get().strip()
                
                if not project_text or not new_alias_name:
                    messagebox.showerror("Error", "Please fill in all fields")
                    return
                
                # Extract project ID
                new_project_id = int(project_text.split(' - ')[0])
                
                if self.alias_manager.update_alias(old_alias_name, new_alias_name, new_project_id):
                    messagebox.showinfo("Success", f"Alias updated successfully!")
                    dialog.destroy()
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to update alias")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error updating alias: {str(e)}")
        
        ttk.Button(button_frame, text="Update", command=update_alias).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Focus on alias entry
        alias_entry.focus()
        alias_entry.select_range(0, tk.END)
    
    def delete_selected_alias(self):
        """Delete the selected alias"""
        selected = self.alias_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an alias to delete")
            return
        
        item = self.alias_tree.item(selected[0])
        alias_name = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the alias '{alias_name}'?"):
            if self.alias_manager.delete_alias(alias_name):
                messagebox.showinfo("Success", "Alias deleted successfully!")
                self.refresh_data()
            else:
                messagebox.showerror("Error", "Failed to delete alias")
    
    def validate_aliases(self):
        """Validate all aliases and show results"""
        try:
            validation = self.alias_manager.validate_aliases()
            
            # Create results dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Alias Validation Results")
            dialog.geometry("600x400")
            dialog.transient(self.frame)
            
            # Results text
            results_text = tk.Text(dialog, wrap=tk.WORD)
            results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format results
            results = f"""Alias Validation Results
{'='*50}

Total Aliases: {validation['total_aliases']}
Projects with Aliases: {validation['total_projects_with_aliases']}

Orphaned Aliases: {len(validation['orphaned_aliases'])}
Duplicate Aliases: {len(validation['duplicate_aliases'])}
Unused Projects: {len(validation['unused_projects'])}

"""
            
            if validation['orphaned_aliases']:
                results += "\\n🔴 ORPHANED ALIASES (point to non-existent projects):\\n"
                for orphan in validation['orphaned_aliases']:
                    results += f"  - '{orphan['alias_name']}' -> Project ID {orphan['invalid_project_id']}\\n"
            
            if validation['duplicate_aliases']:
                results += "\\n🔴 DUPLICATE ALIASES:\\n"
                for dup in validation['duplicate_aliases']:
                    results += f"  - '{dup['alias_name']}' appears {dup['count']} times\\n"
            
            if validation['unused_projects']:
                results += "\\n⚠️ UNUSED PROJECTS (no aliases):\\n"
                for unused in validation['unused_projects']:
                    results += f"  - {unused['project_id']}: {unused['project_name']}\\n"
            
            if not validation['orphaned_aliases'] and not validation['duplicate_aliases']:
                results += "\\n✅ All aliases are valid!\\n"
            
            results_text.insert(1.0, results)
            results_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error validating aliases: {str(e)}")
    
    def discover_unmapped(self):
        """Discover and refresh unmapped projects"""
        self.refresh_unmapped_projects()
        self.details_notebook.select(1)  # Switch to unmapped tab
        messagebox.showinfo("Discovery Complete", "Unmapped projects have been refreshed!")
    
    def create_mapping_from_unmapped(self):
        """Create a mapping from selected unmapped project"""
        selected = self.unmapped_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an unmapped project")
            return
        
        item = self.unmapped_tree.item(selected[0])
        unmapped_name = item['values'][0]
        suggested_project = item['values'][3]
        
        # Show mapping dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Create Alias Mapping")
        dialog.geometry("500x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Create alias for: {unmapped_name}").pack(pady=(10, 20))
        
        # Project selection
        ttk.Label(dialog, text="Select Project:").pack(pady=(10, 5))
        
        project_var = tk.StringVar()
        project_combo = ttk.Combobox(dialog, textvariable=project_var, width=50)
        
        # Load projects
        projects = format_id_name_list(get_projects())
        project_combo['values'] = projects
        
        # Pre-select suggested project if available
        if suggested_project != "No suggestion":
            for project in projects:
                if suggested_project in project:
                    project_var.set(project)
                    break
        
        project_combo.pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def create_mapping():
            try:
                project_text = project_var.get().strip()
                
                if not project_text:
                    messagebox.showerror("Error", "Please select a project")
                    return
                
                # Extract project ID
                project_id = int(project_text.split(' - ')[0])
                
                if self.alias_manager.add_alias(project_id, unmapped_name):
                    messagebox.showinfo("Success", f"Alias mapping created successfully!")
                    dialog.destroy()
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to create alias mapping")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error creating mapping: {str(e)}")
        
        ttk.Button(button_frame, text="Create Mapping", command=create_mapping).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Focus on project combo
        project_combo.focus()
    
    def export_csv(self):
        """Export aliases to CSV file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Project Aliases"
            )
            
            if filename:
                if self.alias_manager.export_aliases_to_csv(filename):
                    messagebox.showinfo("Success", f"Aliases exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export aliases")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting: {str(e)}")
    
    def import_csv(self):
        """Import aliases from CSV file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Import Project Aliases"
            )
            
            if filename:
                update_existing = messagebox.askyesno(
                    "Import Options", 
                    "Update existing aliases with same name?\\n\\nYes: Update existing\\nNo: Skip existing"
                )
                
                results = self.alias_manager.import_aliases_from_csv(filename, update_existing)
                
                message = f"""Import Results:
                
Imported: {results['imported']}
Updated: {results['updated']}
Skipped: {results['skipped']}
Errors: {len(results['errors'])}"""
                
                if results['errors']:
                    message += f"\\n\\nFirst 5 errors:\\n" + "\\n".join(results['errors'][:5])
                
                messagebox.showinfo("Import Complete", message)
                self.refresh_data()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error importing: {str(e)}")
    
    def __del__(self):
        """Cleanup when tab is destroyed"""
        if hasattr(self, 'alias_manager'):
            self.alias_manager.close_connection()