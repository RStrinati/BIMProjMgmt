# ui/enhanced_data_imports_tab.py
"""
Enhanced Data Imports Tab with React Component Integration

This tab combines:
1. Traditional Tkinter data import functionality
2. Integration with React-based Data Imports components for modern UI testing
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import logging
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_projects,
    save_acc_folder_path,
    get_acc_folder_path,
    get_acc_import_logs,
    get_project_health_files,
    get_last_export_date,
    log_acc_import,
    set_control_file,
    insert_files_into_tblACCDocs,
    get_project_folders,
)
from handlers.acc_handler import run_acc_import
from handlers.rvt_health_importer import import_health_data
from handlers.ideate_health_exporter import export_health_checks_to_sql
from handlers.process_ifc import process_folder
from ui.ui_helpers import (
    create_labeled_entry,
    create_labeled_combobox,
    create_horizontal_button_group,
)
from ui.tooltips import CreateToolTip
from ui.tab_review import open_revizto_csharp_app

logger = logging.getLogger(__name__)


class EnhancedDataImportsTab:
    """
    Enhanced Data Imports Tab with React Integration
    
    Features:
    - Traditional Tkinter data import controls
    - Launch React-based Data Imports UI for modern web interface
    - Server status monitoring
    - Quick access to both Tkinter and React UIs
    """
    
    def __init__(self, parent_notebook):
        """Initialize the enhanced data imports tab"""
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📥 Data Imports")
        
        self.backend_process = None
        self.frontend_process = None
        self.server_status = {
            'backend': False,
            'frontend': False
        }
        
        self.setup_ui()
        logger.info("Enhanced Data Imports tab initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container with scrollbar
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ===== REACT COMPONENTS SECTION =====
        self.create_react_section(scrollable_frame)
        
        # Add separator
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # ===== TRADITIONAL IMPORTS SECTION =====
        self.create_traditional_imports_section(scrollable_frame)
    
    def create_react_section(self, parent):
        """Create React components integration section"""
        react_frame = ttk.LabelFrame(parent, text="🚀 React Data Imports Components (Modern UI)", padding=10)
        react_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info section
        info_frame = ttk.Frame(react_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = """
The React Data Imports interface provides a modern web-based UI with:
• ACC Desktop Connector - File extraction and management
• ACC Data Import - CSV/ZIP import with bookmarks
• ACC Issues - Issues display with statistics and filtering
• Revizto Extraction - Extraction run management
• Revit Health Check - Health metrics and file analysis

Click 'Launch React UI' to open the web interface in your browser.
        """
        
        info_label = ttk.Label(info_frame, text=info_text.strip(), justify=tk.LEFT, 
                               foreground='#666', wraplength=750)
        info_label.pack(anchor='w')
        
        # Server status section
        status_frame = ttk.LabelFrame(react_frame, text="Server Status", padding=5)
        status_frame.pack(fill=tk.X, pady=10)
        
        # Backend status
        backend_frame = ttk.Frame(status_frame)
        backend_frame.pack(fill=tk.X, pady=2)
        ttk.Label(backend_frame, text="Backend (Flask):").pack(side=tk.LEFT, padx=(0, 10))
        self.backend_status_label = ttk.Label(backend_frame, text="● Stopped", foreground='red')
        self.backend_status_label.pack(side=tk.LEFT)
        
        # Frontend status
        frontend_frame = ttk.Frame(status_frame)
        frontend_frame.pack(fill=tk.X, pady=2)
        ttk.Label(frontend_frame, text="Frontend (React):").pack(side=tk.LEFT, padx=(0, 10))
        self.frontend_status_label = ttk.Label(frontend_frame, text="● Stopped", foreground='red')
        self.frontend_status_label.pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(react_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Start servers button
        self.start_btn = ttk.Button(button_frame, text="🚀 Start Development Servers", 
                                     command=self.start_dev_servers, style='Accent.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.start_btn, "Start Flask backend (port 5000) and React frontend (port 5173)")
        
        # Launch React UI button
        self.launch_btn = ttk.Button(button_frame, text="🌐 Launch React UI", 
                                      command=self.launch_react_ui)
        self.launch_btn.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.launch_btn, "Open React Data Imports UI in browser (http://localhost:5173/data-imports)")
        
        # Stop servers button
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop Servers", 
                                    command=self.stop_dev_servers)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        CreateToolTip(self.stop_btn, "Stop both backend and frontend servers")
        
        # Check status button
        check_btn = ttk.Button(button_frame, text="🔄 Check Status", 
                               command=self.check_server_status)
        check_btn.pack(side=tk.LEFT, padx=5)
        CreateToolTip(check_btn, "Check if servers are running")
        
        # Quick links
        links_frame = ttk.Frame(react_frame)
        links_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(links_frame, text="Quick Links:", font=('Arial', 9, 'bold')).pack(anchor='w')
        
        link_buttons = [
            ("📖 Implementation Guide", lambda: self.open_doc("REACT_DATA_IMPORTS_IMPLEMENTATION_COMPLETE.md")),
            ("🚀 Quick Start Guide", lambda: self.open_doc("REACT_DATA_IMPORTS_QUICK_START.md")),
            ("📊 API Reference", lambda: self.open_doc("DATA_IMPORTS_API_REFERENCE.md")),
        ]
        
        for text, cmd in link_buttons:
            btn = ttk.Button(links_frame, text=text, command=cmd, width=30)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_traditional_imports_section(self, parent):
        """Create traditional Tkinter import controls"""
        traditional_frame = ttk.LabelFrame(parent, text="📦 Traditional Data Import Tools", padding=10)
        traditional_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ACC Desktop Connector Section
        acc_frame = ttk.LabelFrame(traditional_frame, text="ACC Desktop Connector", padding=10)
        acc_frame.pack(fill=tk.X, pady=5)
        
        # Project selection
        projects = [f"{p[0]} - {p[1]}" for p in get_projects()]
        ttk.Label(acc_frame, text="Project:").pack(anchor='w', padx=10)
        self.cmb_projects = ttk.Combobox(acc_frame, values=projects, state='readonly', width=40)
        self.cmb_projects.pack(anchor='w', padx=10, pady=2)
        
        # Folder path
        ttk.Label(acc_frame, text="ACC Folder Path:").pack(anchor='w', padx=10, pady=(10, 0))
        self.entry_acc_folder = ttk.Entry(acc_frame, width=60)
        self.entry_acc_folder.pack(anchor='w', padx=10, pady=2)
        
        acc_buttons = ttk.Frame(acc_frame)
        acc_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(acc_buttons, text="Load Folder Path", 
                   command=self.load_acc_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(acc_buttons, text="Save Folder Path", 
                   command=self.save_acc_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(acc_buttons, text="Extract Files", 
                   command=self.extract_acc_files).pack(side=tk.LEFT, padx=5)
        
        # ACC Data Import Section
        import_frame = ttk.LabelFrame(traditional_frame, text="ACC Data Import (CSV/ZIP)", padding=10)
        import_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(import_frame, text="File Path:").pack(anchor='w', padx=10)
        self.entry_import_path = ttk.Entry(import_frame, width=60)
        self.entry_import_path.pack(anchor='w', padx=10, pady=2)
        
        import_buttons = ttk.Frame(import_frame)
        import_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(import_buttons, text="Browse", 
                   command=self.browse_import_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_buttons, text="Import CSV", 
                   command=lambda: self.run_import('csv')).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_buttons, text="Import ZIP", 
                   command=lambda: self.run_import('zip')).pack(side=tk.LEFT, padx=5)
        
        # Revizto Extraction Section
        revizto_frame = ttk.LabelFrame(traditional_frame, text="Revizto Extraction", padding=10)
        revizto_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(revizto_frame, text="Open Revizto Extraction Tool", 
                   command=self.open_revizto_tool).pack(padx=10, pady=10)
        
        # Revit Health Import Section
        health_frame = ttk.LabelFrame(traditional_frame, text="Revit Health Check Import", padding=10)
        health_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(health_frame, text="Excel Folder:").pack(anchor='w', padx=10)
        self.entry_health_folder = ttk.Entry(health_frame, width=60)
        self.entry_health_folder.pack(anchor='w', padx=10, pady=2)
        
        health_buttons = ttk.Frame(health_frame)
        health_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(health_buttons, text="Browse Folder", 
                   command=self.browse_health_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(health_buttons, text="Import Health Checks", 
                   command=self.import_health_data).pack(side=tk.LEFT, padx=5)
    
    # ===== REACT UI METHODS =====
    
    def start_dev_servers(self):
        """Start both backend and frontend development servers"""
        try:
            # Start backend
            backend_path = Path(__file__).parent.parent / "backend"
            self.backend_process = subprocess.Popen(
                ["python", "app.py"],
                cwd=str(backend_path),
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            logger.info("Backend server started")
            
            # Start frontend
            frontend_path = Path(__file__).parent.parent / "frontend"
            self.frontend_process = subprocess.Popen(
                ["npm.cmd", "run", "dev"],
                cwd=str(frontend_path),
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            logger.info("Frontend server started")
            
            # Update status after a delay
            self.frame.after(3000, self.check_server_status)
            
            messagebox.showinfo("Servers Started", 
                              "Backend and Frontend servers are starting...\n"
                              "Backend: http://localhost:5000\n"
                              "Frontend: http://localhost:5173\n\n"
                              "Please wait a few seconds for them to be ready.")
        
        except Exception as e:
            logger.error(f"Error starting servers: {e}")
            messagebox.showerror("Error", f"Failed to start servers:\n{str(e)}")
    
    def stop_dev_servers(self):
        """Stop both development servers"""
        try:
            if self.backend_process:
                self.backend_process.terminate()
                self.backend_process = None
                logger.info("Backend server stopped")
            
            if self.frontend_process:
                self.frontend_process.terminate()
                self.frontend_process = None
                logger.info("Frontend server stopped")
            
            self.update_server_status(backend=False, frontend=False)
            messagebox.showinfo("Servers Stopped", "All development servers have been stopped.")
        
        except Exception as e:
            logger.error(f"Error stopping servers: {e}")
            messagebox.showerror("Error", f"Failed to stop servers:\n{str(e)}")
    
    def check_server_status(self):
        """Check if development servers are running"""
        import socket
        
        def check_port(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        
        backend_running = check_port(5000)
        frontend_running = check_port(5173)
        
        self.update_server_status(backend=backend_running, frontend=frontend_running)
        
        return backend_running and frontend_running
    
    def update_server_status(self, backend=None, frontend=None):
        """Update server status indicators"""
        if backend is not None:
            self.server_status['backend'] = backend
            if backend:
                self.backend_status_label.config(text="● Running", foreground='green')
            else:
                self.backend_status_label.config(text="● Stopped", foreground='red')
        
        if frontend is not None:
            self.server_status['frontend'] = frontend
            if frontend:
                self.frontend_status_label.config(text="● Running", foreground='green')
            else:
                self.frontend_status_label.config(text="● Stopped", foreground='red')
    
    def launch_react_ui(self):
        """Launch React Data Imports UI in browser"""
        if not self.check_server_status():
            response = messagebox.askyesno(
                "Servers Not Running",
                "Development servers are not running.\n"
                "Would you like to start them now?"
            )
            if response:
                self.start_dev_servers()
                # Wait a bit for servers to start
                self.frame.after(5000, lambda: webbrowser.open('http://localhost:5173/data-imports'))
        else:
            webbrowser.open('http://localhost:5173/data-imports')
    
    def open_doc(self, filename):
        """Open documentation file"""
        doc_path = Path(__file__).parent.parent / "docs" / filename
        if doc_path.exists():
            os.startfile(str(doc_path))
        else:
            messagebox.showerror("Error", f"Documentation file not found:\n{filename}")
    
    # ===== TRADITIONAL IMPORT METHODS =====
    
    def load_acc_folder(self):
        """Load ACC folder path for selected project"""
        if not self.cmb_projects.get():
            messagebox.showerror("Error", "Please select a project first")
            return
        
        project_id = self.cmb_projects.get().split(" - ")[0]
        folder_path = get_acc_folder_path(project_id)
        
        if folder_path:
            self.entry_acc_folder.delete(0, tk.END)
            self.entry_acc_folder.insert(0, folder_path)
        else:
            messagebox.showinfo("Info", "No folder path saved for this project")
    
    def save_acc_folder(self):
        """Save ACC folder path for selected project"""
        if not self.cmb_projects.get():
            messagebox.showerror("Error", "Please select a project first")
            return
        
        project_id = self.cmb_projects.get().split(" - ")[0]
        folder_path = self.entry_acc_folder.get().strip()
        
        if not folder_path:
            messagebox.showerror("Error", "Please enter a folder path")
            return
        
        if save_acc_folder_path(project_id, folder_path):
            messagebox.showinfo("Success", "Folder path saved successfully")
        else:
            messagebox.showerror("Error", "Failed to save folder path")
    
    def extract_acc_files(self):
        """Extract files from ACC folder to database"""
        if not self.cmb_projects.get():
            messagebox.showerror("Error", "Please select a project first")
            return
        
        project_id = self.cmb_projects.get().split(" - ")[0]
        folder_path = self.entry_acc_folder.get().strip()
        
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Invalid folder path")
            return
        
        try:
            if insert_files_into_tblACCDocs(project_id, folder_path):
                messagebox.showinfo("Success", "Files extracted successfully")
            else:
                messagebox.showerror("Error", "Failed to extract files")
        except Exception as e:
            messagebox.showerror("Error", f"Error extracting files:\n{str(e)}")
    
    def browse_import_file(self):
        """Browse for import file"""
        file_path = filedialog.askopenfilename(
            title="Select Import File",
            filetypes=[("CSV Files", "*.csv"), ("ZIP Files", "*.zip"), ("All Files", "*.*")]
        )
        if file_path:
            self.entry_import_path.delete(0, tk.END)
            self.entry_import_path.insert(0, file_path)
    
    def run_import(self, import_type):
        """Run ACC data import"""
        file_path = self.entry_import_path.get().strip()
        
        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror("Error", "Invalid file path")
            return
        
        if not self.cmb_projects.get():
            messagebox.showerror("Error", "Please select a project first")
            return
        
        project_id = self.cmb_projects.get().split(" - ")[0]
        
        try:
            result = run_acc_import(project_id, file_path, import_type)
            if result:
                messagebox.showinfo("Success", f"Import completed successfully\n{result}")
            else:
                messagebox.showerror("Error", "Import failed")
        except Exception as e:
            messagebox.showerror("Error", f"Error during import:\n{str(e)}")
    
    def open_revizto_tool(self):
        """Open Revizto extraction tool"""
        try:
            open_revizto_csharp_app()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Revizto tool:\n{str(e)}")
    
    def browse_health_folder(self):
        """Browse for health check folder"""
        folder_path = filedialog.askdirectory(title="Select Health Check Excel Folder")
        if folder_path:
            self.entry_health_folder.delete(0, tk.END)
            self.entry_health_folder.insert(0, folder_path)
    
    def import_health_data(self):
        """Import Revit health check data"""
        folder_path = self.entry_health_folder.get().strip()
        
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Invalid folder path")
            return
        
        if not self.cmb_projects.get():
            messagebox.showerror("Error", "Please select a project first")
            return
        
        project_id = self.cmb_projects.get().split(" - ")[0]
        
        try:
            result = import_health_data(project_id, folder_path)
            messagebox.showinfo("Success", f"Health data imported:\n{result}")
        except Exception as e:
            messagebox.showerror("Error", f"Error importing health data:\n{str(e)}")


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Enhanced Data Imports Tab Test")
    root.geometry("1000x800")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    EnhancedDataImportsTab(notebook)
    
    root.mainloop()
