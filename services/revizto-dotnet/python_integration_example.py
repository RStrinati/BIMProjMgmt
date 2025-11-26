"""
Python Tkinter Integration Example for Revizto Data Exporter

This example shows how to integrate the Revizto Data Exporter executable
into your Python tkinter application.

Requirements:
- ReviztoDataExporter.exe (located in the same directory or specify full path)
- ReviztoDataExporter.exe must have appsettings.json in the same directory
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import json
import os
import threading
from datetime import datetime


class ReviztoExporterInterface:
    def __init__(self, exporter_path="./ReviztoDataExporter.exe"):
        self.exporter_path = exporter_path
        self.projects = []
        
    def execute_command(self, command, *args):
        """Execute a command with the Revizto exporter and return JSON result"""
        try:
            cmd = [self.exporter_path, command] + list(args)
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False,
                cwd=os.path.dirname(self.exporter_path)
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"success": False, "error": result.stderr or result.stdout}
                
        except FileNotFoundError:
            return {"success": False, "error": f"Exporter not found at: {self.exporter_path}"}
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON response from exporter"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self):
        """Get application status"""
        return self.execute_command("status")
    
    def list_projects(self):
        """Get list of all projects"""
        return self.execute_command("list-projects")
    
    def refresh_projects(self):
        """Refresh projects from API"""
        return self.execute_command("refresh")
    
    def export_project(self, project_id, output_path=""):
        """Export a specific project"""
        if output_path:
            return self.execute_command("export", project_id, output_path)
        else:
            return self.execute_command("export", project_id)
    
    def export_all_projects(self, output_path=""):
        """Export all projects"""
        if output_path:
            return self.execute_command("export-all", output_path)
        else:
            return self.execute_command("export-all")


class ReviztoExporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Revizto Data Exporter - Python Interface")
        self.root.geometry("800x600")
        
        # Initialize the exporter interface
        # Update this path to where your ReviztoDataExporter.exe is located
        exporter_path = os.path.join(os.getcwd(), "publish", "ReviztoDataExporter.exe")
        self.exporter = ReviztoExporterInterface(exporter_path)
        
        self.projects = []
        self.setup_ui()
        
    def setup_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_text = tk.Text(status_frame, height=4, width=70)
        self.status_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(status_frame, text="Get Status", command=self.get_status).grid(row=1, column=0, pady=5)
        ttk.Button(status_frame, text="Refresh Projects", command=self.refresh_projects).grid(row=1, column=1, pady=5)
        
        # Projects section
        projects_frame = ttk.LabelFrame(main_frame, text="Projects", padding="5")
        projects_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Projects listbox with scrollbar
        listbox_frame = ttk.Frame(projects_frame)
        listbox_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.projects_listbox = tk.Listbox(listbox_frame, height=15)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.projects_listbox.yview)
        self.projects_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.projects_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(projects_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Load Projects", command=self.load_projects).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Export Selected", command=self.export_selected).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Export All", command=self.export_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Choose Output Dir", command=self.choose_output_dir).grid(row=0, column=3, padx=5)
        
        # Output directory
        self.output_dir = tk.StringVar(value="")
        ttk.Label(main_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, textvariable=self.output_dir, background="white", relief="sunken").grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        projects_frame.columnconfigure(0, weight=1)
        projects_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        # Load initial status
        self.get_status()
        
    def get_status(self):
        """Get and display status"""
        def run_status():
            result = self.exporter.get_status()
            self.root.after(0, lambda: self.update_status_display(result))
        
        threading.Thread(target=run_status, daemon=True).start()
        
    def update_status_display(self, result):
        """Update status display"""
        self.status_text.delete(1.0, tk.END)
        
        if result["success"]:
            status = result["status"]
            text = f"Connected: {status['databaseConnected']}\\n"
            text += f"Projects: {status['projectCount']}\\n"
            text += f"Last Refresh: {status.get('lastRefresh', 'Never')}\\n"
            text += f"Timestamp: {result['timestamp']}"
            self.status_text.insert(tk.END, text)
        else:
            self.status_text.insert(tk.END, f"Error: {result.get('error', 'Unknown error')}")
    
    def refresh_projects(self):
        """Refresh projects from API"""
        def run_refresh():
            result = self.exporter.refresh_projects()
            self.root.after(0, lambda: self.handle_refresh_result(result))
        
        threading.Thread(target=run_refresh, daemon=True).start()
        messagebox.showinfo("Refresh", "Refreshing projects from API... This may take a moment.")
        
    def handle_refresh_result(self, result):
        """Handle refresh result"""
        if result["success"]:
            messagebox.showinfo("Success", f"Projects refreshed successfully. Found {result['projectCount']} projects.")
            self.load_projects()
        else:
            messagebox.showerror("Error", f"Failed to refresh projects: {result.get('error')}")
    
    def load_projects(self):
        """Load projects list"""
        def run_load():
            result = self.exporter.list_projects()
            self.root.after(0, lambda: self.update_projects_display(result))
        
        threading.Thread(target=run_load, daemon=True).start()
        
    def update_projects_display(self, result):
        """Update projects display"""
        self.projects_listbox.delete(0, tk.END)
        self.projects = []
        
        if result["success"]:
            for project in result["projects"]:
                display_text = f"{project['name']} ({project['id']})"
                self.projects_listbox.insert(tk.END, display_text)
                self.projects.append(project)
        else:
            messagebox.showerror("Error", f"Failed to load projects: {result.get('error')}")
    
    def export_selected(self):
        """Export selected project"""
        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to export.")
            return
            
        project = self.projects[selection[0]]
        
        def run_export():
            result = self.exporter.export_project(project["id"], self.output_dir.get())
            self.root.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=run_export, daemon=True).start()
        messagebox.showinfo("Export", f"Exporting project: {project['name']}...")
        
    def export_all(self):
        """Export all projects"""
        if not self.projects:
            messagebox.showwarning("Warning", "No projects loaded. Please load projects first.")
            return
            
        confirm = messagebox.askyesno("Confirm", f"Export all {len(self.projects)} projects?")
        if not confirm:
            return
            
        def run_export_all():
            result = self.exporter.export_all_projects(self.output_dir.get())
            self.root.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=run_export_all, daemon=True).start()
        messagebox.showinfo("Export", "Exporting all projects... This may take several minutes.")
        
    def handle_export_result(self, result):
        """Handle export result"""
        if result["success"]:
            if "results" in result:  # Bulk export
                successful = result["successfulExports"]
                total = result["totalProjects"]
                messagebox.showinfo("Export Complete", f"Bulk export completed: {successful}/{total} projects exported successfully.")
            else:  # Single export
                messagebox.showinfo("Export Complete", f"Project exported successfully to: {result['exportedFile']}")
        else:
            messagebox.showerror("Export Error", f"Export failed: {result.get('error')}")
    
    def choose_output_dir(self):
        """Choose output directory"""
        directory = filedialog.askdirectory(title="Choose Export Directory")
        if directory:
            self.output_dir.set(directory)


def main():
    root = tk.Tk()
    app = ReviztoExporterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()