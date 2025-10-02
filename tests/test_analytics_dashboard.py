"""
Test script for Issue Analytics Dashboard
Tests the standalone dashboard UI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from ui.tab_issue_analytics import IssueAnalyticsDashboard

def main():
    """Test the analytics dashboard in standalone mode"""
    print("=" * 80)
    print("ISSUE ANALYTICS DASHBOARD - Standalone Test")
    print("=" * 80)
    
    # Create root window
    root = tk.Tk()
    root.title("Issue Analytics Dashboard - Test")
    root.geometry("1400x900")
    
    # Create a notebook (simulating parent)
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create dashboard
    print("\n📊 Initializing Issue Analytics Dashboard...")
    try:
        dashboard = IssueAnalyticsDashboard(notebook)
        print("✅ Dashboard initialized successfully")
        print("✅ Analytics data will auto-load in 100ms")
        print("\n" + "=" * 80)
        print("DASHBOARD FEATURES:")
        print("  - Executive summary cards with key metrics")
        print("  - Projects tab: Pain point scores, issue counts, discipline breakdown")
        print("  - Disciplines tab: Performance metrics by discipline")
        print("  - Patterns tab: Recurring issue patterns from keyword analysis")
        print("  - Recommendations tab: Actionable insights and targets")
        print("  - 🔄 Refresh button: Reload analytics on demand")
        print("  - 📥 Export button: Save report to JSON file")
        print("=" * 80)
        print("\nStarting UI... Close window to exit.\n")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error initializing dashboard: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
