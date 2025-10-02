#!/usr/bin/env python3
"""
Demo script to run the Phase 1 Enhanced UI
This shows how to properly use the classes from phase1_enhanced_ui.py
"""

import logging
import tkinter as tk
from tkinter import ttk
from utils.log import setup_logging


def main():
    """Main function to launch the enhanced UI"""
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting Phase 1 Enhanced UI...")

        # Import the UI classes
        from phase1_enhanced_ui import (
            EnhancedTaskManagementTab,
            ResourceManagementTab,
            ReviewManagementTab,
            DocumentManagementTab,
            ProjectSetupTab,
            ProjectBookmarksTab,
            IssueManagementTab,
        )
        from ui.project_alias_tab import ProjectAliasManagementTab

        # Create main window
        root = tk.Tk()
        root.title("BIM Project Management - Phase 1 Enhanced UI")
        root.geometry("1200x800")

        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create and add tabs in proper order - Project Setup first
        logger.info("Creating Project Setup tab...")
        ProjectSetupTab(notebook)

        logger.info("Creating Enhanced Task Management tab...")
        EnhancedTaskManagementTab(notebook)

        logger.info("Creating Resource Management tab...")
        ResourceManagementTab(notebook)

        logger.info("Creating Issue Management tab...")
        IssueManagementTab(notebook)

        logger.info("Creating Review Management tab...")
        ReviewManagementTab(notebook)

        logger.info("Creating Document Management tab...")
        DocumentManagementTab(notebook)

        logger.info("Creating Project Bookmarks tab...")
        ProjectBookmarksTab(notebook)

        logger.info("Creating Project Alias Management tab...")
        ProjectAliasManagementTab(notebook)
        logger.info("Project Alias Management tab created successfully!")

        logger.info("UI initialized successfully! Starting main loop...")
        root.mainloop()

    except ImportError as e:
        logger.error("Import error: %s", e)
        logger.info("Make sure all required packages are installed:")
        logger.info("  pip install tkcalendar pandas pyodbc")

    except Exception as e:
        logger.exception("Error starting UI: %s", e)


if __name__ == "__main__":
    main()

