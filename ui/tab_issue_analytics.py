"""
Issue Analytics Dashboard - Sub-tab for Issue Management
Visualizes pain points, patterns, and insights from processed issues

Author: BIM Project Management System
Created: 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.issue_analytics_service import IssueAnalyticsService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IssueAnalyticsDashboard:
    """
    Dashboard displaying issue analytics, pain points, and insights.
    Integrated as a sub-tab under Issue Management.
    """
    
    def __init__(self, parent_notebook):
        """
        Initialize the analytics dashboard.
        
        Args:
            parent_notebook: The ttk.Notebook to add this tab to
        """
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📊 Analytics Dashboard")
        
        self.analytics_service = IssueAnalyticsService()
        
        # Data cache
        self.projects_data = []
        self.disciplines_data = []
        self.patterns_data = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dashboard UI components"""
        
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
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Header Section
        self.setup_header(scrollable_frame)
        
        # Summary Cards Section
        self.setup_summary_cards(scrollable_frame)
        
        # Tab Section for detailed views
        self.setup_detail_tabs(scrollable_frame)
        
        # Auto-load data on startup
        self.frame.after(100, self.refresh_analytics)
    
    def setup_header(self, parent):
        """Create header section with title and refresh button"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="📊 Issue Analytics Dashboard",
            font=("Arial", 18, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)
        
        # Last updated
        self.last_updated_var = tk.StringVar(value="Not loaded")
        update_label = tk.Label(
            header_frame,
            textvariable=self.last_updated_var,
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        update_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Refresh button
        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Refresh Analytics",
            command=self.refresh_analytics
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Export button
        export_btn = ttk.Button(
            header_frame,
            text="📥 Export Report",
            command=self.export_report
        )
        export_btn.pack(side=tk.RIGHT, padx=(0, 5))
    
    def setup_summary_cards(self, parent):
        """Create summary cards showing key metrics"""
        cards_frame = ttk.LabelFrame(parent, text="📈 Executive Summary", padding=10)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create 4 metric cards
        metrics_container = ttk.Frame(cards_frame)
        metrics_container.pack(fill=tk.X)
        
        # Card 1: Total Issues
        self.total_issues_var = tk.StringVar(value="0")
        self.create_metric_card(
            metrics_container,
            "Total Issues",
            self.total_issues_var,
            "#3498db",
            0
        )
        
        # Card 2: Open Rate
        self.open_rate_var = tk.StringVar(value="0%")
        self.create_metric_card(
            metrics_container,
            "Open Rate",
            self.open_rate_var,
            "#e74c3c",
            1
        )
        
        # Card 3: Top Pain Point
        self.top_pain_var = tk.StringVar(value="N/A")
        self.create_metric_card(
            metrics_container,
            "Top Pain Point",
            self.top_pain_var,
            "#e67e22",
            2
        )
        
        # Card 4: Patterns Found
        self.patterns_var = tk.StringVar(value="0")
        self.create_metric_card(
            metrics_container,
            "Recurring Patterns",
            self.patterns_var,
            "#9b59b6",
            3
        )
    
    def create_metric_card(self, parent, title, value_var, color, column):
        """Create a single metric card"""
        card = ttk.Frame(parent, relief="solid", borderwidth=1)
        card.grid(row=0, column=column, padx=5, pady=5, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        # Color bar
        color_bar = tk.Frame(card, bg=color, height=4)
        color_bar.pack(fill=tk.X)
        
        # Content
        content = ttk.Frame(card, padding=10)
        content.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            content,
            text=title,
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        title_label.pack(anchor="w")
        
        value_label = tk.Label(
            content,
            textvariable=value_var,
            font=("Arial", 20, "bold"),
            fg="#2c3e50"
        )
        value_label.pack(anchor="w", pady=(5, 0))
    
    def setup_detail_tabs(self, parent):
        """Create tabbed interface for detailed analytics"""
        details_frame = ttk.LabelFrame(parent, text="📊 Detailed Analytics", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different views
        self.detail_notebook = ttk.Notebook(details_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Projects
        self.setup_projects_tab()
        
        # Tab 2: Disciplines
        self.setup_disciplines_tab()
        
        # Tab 3: Recurring Patterns
        self.setup_patterns_tab()
        
        # Tab 4: Recommendations
        self.setup_recommendations_tab()
    
    def setup_projects_tab(self):
        """Setup project pain points view"""
        projects_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(projects_frame, text="🏗️ Projects")
        
        # Control frame
        control_frame = ttk.Frame(projects_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Sort by:").pack(side=tk.LEFT, padx=(0, 5))
        self.project_sort_var = tk.StringVar(value="pain_score")
        sort_combo = ttk.Combobox(
            control_frame,
            textvariable=self.project_sort_var,
            values=["pain_score", "total_issues", "open_rate", "name"],
            state="readonly",
            width=15
        )
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.sort_projects())
        
        # Treeview for projects
        tree_frame = ttk.Frame(projects_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Project", "Source", "Total", "Open", "Closed", "Pain Score", "Elec", "Hydr", "Mech", "Avg Days")
        self.projects_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        widths = [200, 80, 70, 60, 60, 90, 50, 50, 50, 80]
        for col, width in zip(columns, widths):
            self.projects_tree.heading(col, text=col, command=lambda c=col: self.sort_tree_column(self.projects_tree, c))
            self.projects_tree.column(col, width=width, anchor="w")
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.projects_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.projects_tree.xview)
        self.projects_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.projects_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click for details
        self.projects_tree.bind("<Double-1>", self.show_project_details)
    
    def setup_disciplines_tab(self):
        """Setup discipline pain points view"""
        disciplines_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(disciplines_frame, text="⚡ Disciplines")
        
        # Treeview for disciplines
        tree_frame = ttk.Frame(disciplines_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("Discipline", "Total Issues", "Projects", "Issues/Proj", "Open %", "Pain Score", "Clash", "Info", "Design")
        self.disciplines_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        widths = [150, 100, 80, 100, 80, 100, 70, 70, 70]
        for col, width in zip(columns, widths):
            self.disciplines_tree.heading(col, text=col)
            self.disciplines_tree.column(col, width=width, anchor="w")
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.disciplines_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.disciplines_tree.xview)
        self.disciplines_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.disciplines_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Add color coding legend
        legend_frame = ttk.Frame(disciplines_frame)
        legend_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(legend_frame, text="Pain Score:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 5))
        self.create_legend_item(legend_frame, "High (>0.20)", "#e74c3c")
        self.create_legend_item(legend_frame, "Medium (0.10-0.20)", "#f39c12")
        self.create_legend_item(legend_frame, "Low (<0.10)", "#27ae60")
    
    def create_legend_item(self, parent, text, color):
        """Create a color-coded legend item"""
        box = tk.Frame(parent, bg=color, width=15, height=15)
        box.pack(side=tk.LEFT, padx=(5, 2))
        tk.Label(parent, text=text, font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 10))
    
    def setup_patterns_tab(self):
        """Setup recurring patterns view"""
        patterns_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(patterns_frame, text="🔄 Patterns")
        
        # Info label
        info_label = tk.Label(
            patterns_frame,
            text="Recurring issue patterns identified through keyword analysis",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        info_label.pack(anchor="w", pady=(0, 10))
        
        # Treeview for patterns
        tree_frame = ttk.Frame(patterns_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Pattern ID", "Keywords", "Occurrences", "Projects", "Discipline", "Issue Type", "Example")
        self.patterns_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        widths = [80, 250, 100, 80, 150, 150, 300]
        for col, width in zip(columns, widths):
            self.patterns_tree.heading(col, text=col)
            self.patterns_tree.column(col, width=width, anchor="w")
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.patterns_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.patterns_tree.xview)
        self.patterns_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.patterns_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def setup_recommendations_tab(self):
        """Setup recommendations view"""
        rec_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(rec_frame, text="💡 Recommendations")
        
        # Text widget for recommendations
        text_frame = ttk.Frame(rec_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.recommendations_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            padx=15,
            pady=15
        )
        
        # Scrollbar
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.recommendations_text.yview)
        self.recommendations_text.configure(yscrollcommand=scroll.set)
        
        self.recommendations_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text tags for formatting
        self.recommendations_text.tag_configure("heading", font=("Arial", 12, "bold"), foreground="#2c3e50")
        self.recommendations_text.tag_configure("subheading", font=("Arial", 10, "bold"), foreground="#34495e")
        self.recommendations_text.tag_configure("critical", foreground="#e74c3c", font=("Arial", 10, "bold"))
        self.recommendations_text.tag_configure("warning", foreground="#f39c12")
        self.recommendations_text.tag_configure("info", foreground="#3498db")
        self.recommendations_text.tag_configure("bullet", lmargin1=20, lmargin2=30)
    
    def refresh_analytics(self):
        """Refresh all analytics data"""
        try:
            logger.info("Refreshing analytics dashboard...")
            
            # Show loading state
            self.last_updated_var.set("Loading...")
            self.frame.update()
            
            # Fetch data
            self.projects_data = self.analytics_service.calculate_pain_points_by_project()
            self.disciplines_data = self.analytics_service.calculate_pain_points_by_discipline()
            self.patterns_data = self.analytics_service.identify_recurring_patterns()
            
            # Update summary cards
            self.update_summary_cards()
            
            # Update detail views
            self.populate_projects_tree()
            self.populate_disciplines_tree()
            self.populate_patterns_tree()
            self.populate_recommendations()
            
            # Update timestamp
            self.last_updated_var.set(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            logger.info("Analytics dashboard refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing analytics: {e}")
            messagebox.showerror("Error", f"Failed to refresh analytics:\n{str(e)}")
            self.last_updated_var.set("Error loading data")
    
    def update_summary_cards(self):
        """Update summary metric cards"""
        if not self.projects_data:
            return
        
        # Calculate totals
        total_issues = sum(p['total_issues'] for p in self.projects_data)
        total_open = sum(p['open_issues'] for p in self.projects_data)
        open_rate = (total_open / total_issues * 100) if total_issues > 0 else 0
        
        # Find top pain point
        if self.disciplines_data:
            top_discipline = max(self.disciplines_data, key=lambda x: x['pain_point_score'])
            top_pain = f"{top_discipline['discipline']} ({top_discipline['pain_point_score']:.2f})"
        else:
            top_pain = "N/A"
        
        # Update variables
        self.total_issues_var.set(f"{total_issues:,}")
        self.open_rate_var.set(f"{open_rate:.1f}%")
        self.top_pain_var.set(top_pain)
        self.patterns_var.set(f"{len(self.patterns_data)}")
    
    def populate_projects_tree(self):
        """Populate projects treeview"""
        # Clear existing
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        # Sort by pain score (default)
        sorted_projects = sorted(self.projects_data, key=lambda x: x['pain_point_score'], reverse=True)
        
        for project in sorted_projects:
            open_rate = (project['open_issues'] / project['total_issues'] * 100) if project['total_issues'] > 0 else 0
            avg_days = f"{project['avg_resolution_days']:.0f}" if project.get('avg_resolution_days') else "N/A"
            
            values = (
                project['project_name'][:40],
                project['source'],
                f"{project['total_issues']:,}",
                f"{project['open_issues']:,}",
                f"{project['closed_issues']:,}",
                f"{project['pain_point_score']:.2f}",
                project['electrical_issues'],
                project['hydraulic_issues'],
                project['mechanical_issues'],
                avg_days
            )
            
            # Color code by pain score
            item = self.projects_tree.insert("", "end", values=values)
            if project['pain_point_score'] > 0.3:
                self.projects_tree.item(item, tags=('high',))
            elif project['pain_point_score'] > 0.15:
                self.projects_tree.item(item, tags=('medium',))
        
        # Configure tags for color coding
        self.projects_tree.tag_configure('high', background='#ffebee')
        self.projects_tree.tag_configure('medium', background='#fff3e0')
    
    def populate_disciplines_tree(self):
        """Populate disciplines treeview"""
        # Clear existing
        for item in self.disciplines_tree.get_children():
            self.disciplines_tree.delete(item)
        
        # Sort by total issues
        sorted_disciplines = sorted(self.disciplines_data, key=lambda x: x['total_issues'], reverse=True)
        
        for disc in sorted_disciplines:
            open_pct = (disc['open_issues'] / disc['total_issues'] * 100) if disc['total_issues'] > 0 else 0
            
            values = (
                disc['discipline'],
                f"{disc['total_issues']:,}",
                disc['project_count'],
                f"{disc['issues_per_project']:.1f}",
                f"{open_pct:.1f}%",
                f"{disc['pain_point_score']:.2f}",
                disc['clash_issues'],
                disc['info_issues'],
                disc['design_issues']
            )
            
            # Color code by pain score
            item = self.disciplines_tree.insert("", "end", values=values)
            if disc['pain_point_score'] > 0.20:
                self.disciplines_tree.item(item, tags=('high',))
            elif disc['pain_point_score'] > 0.10:
                self.disciplines_tree.item(item, tags=('medium',))
            else:
                self.disciplines_tree.item(item, tags=('low',))
        
        # Configure tags
        self.disciplines_tree.tag_configure('high', background='#ffebee')
        self.disciplines_tree.tag_configure('medium', background='#fff3e0')
        self.disciplines_tree.tag_configure('low', background='#e8f5e9')
    
    def populate_patterns_tree(self):
        """Populate patterns treeview"""
        # Clear existing
        for item in self.patterns_tree.get_children():
            self.patterns_tree.delete(item)
        
        # Show top 50 patterns
        for pattern in self.patterns_data[:50]:
            example = pattern['example_titles'][0][:60] + "..." if pattern['example_titles'] else "N/A"
            
            values = (
                pattern['pattern_id'],
                pattern['common_keywords'][:50],
                pattern['occurrence_count'],
                pattern['project_count'],
                pattern['top_discipline'],
                pattern['top_issue_type'],
                example
            )
            
            item = self.patterns_tree.insert("", "end", values=values)
            if pattern['occurrence_count'] > 100:
                self.patterns_tree.item(item, tags=('critical',))
            elif pattern['occurrence_count'] > 50:
                self.patterns_tree.item(item, tags=('warning',))
        
        # Configure tags
        self.patterns_tree.tag_configure('critical', background='#ffebee')
        self.patterns_tree.tag_configure('warning', background='#fff3e0')
    
    def populate_recommendations(self):
        """Generate and display recommendations"""
        self.recommendations_text.config(state=tk.NORMAL)
        self.recommendations_text.delete(1.0, tk.END)
        
        # Header
        self.recommendations_text.insert(tk.END, "🎯 ACTIONABLE RECOMMENDATIONS\n", "heading")
        self.recommendations_text.insert(tk.END, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n", "info")
        
        # Critical Issues
        self.recommendations_text.insert(tk.END, "🔴 CRITICAL ACTIONS\n", "subheading")
        
        # Find high pain projects
        high_pain_projects = [p for p in self.projects_data if p['pain_point_score'] > 0.25]
        if high_pain_projects:
            self.recommendations_text.insert(tk.END, "\n⚠️  High Pain Score Projects:\n", "critical")
            for p in high_pain_projects[:5]:
                open_rate = (p['open_issues'] / p['total_issues'] * 100) if p['total_issues'] > 0 else 0
                self.recommendations_text.insert(
                    tk.END,
                    f"  • {p['project_name']}: {open_rate:.0f}% open rate, {p['total_issues']:,} issues\n",
                    "bullet"
                )
        
        # High pain disciplines
        high_pain_discs = [d for d in self.disciplines_data if d['pain_point_score'] > 0.20]
        if high_pain_discs:
            self.recommendations_text.insert(tk.END, "\n⚠️  High Pain Score Disciplines:\n", "critical")
            for d in high_pain_discs:
                self.recommendations_text.insert(
                    tk.END,
                    f"  • {d['discipline']}: {d['total_issues']:,} issues across {d['project_count']} projects\n",
                    "bullet"
                )
        
        # Recommendations by discipline
        self.recommendations_text.insert(tk.END, "\n\n💡 DISCIPLINE-SPECIFIC ACTIONS\n", "subheading")
        for disc in sorted(self.disciplines_data, key=lambda x: x['pain_point_score'], reverse=True)[:5]:
            self.recommendations_text.insert(tk.END, f"\n{disc['discipline']}:\n", "warning")
            
            # Clash issues
            if disc['clash_issues'] > disc['total_issues'] * 0.5:
                self.recommendations_text.insert(
                    tk.END,
                    f"  • {disc['clash_issues']/disc['total_issues']*100:.0f}% are clashes - Improve coordination protocols\n",
                    "bullet"
                )
            
            # High open rate
            open_rate = disc['open_issues'] / disc['total_issues']
            if open_rate > 0.35:
                self.recommendations_text.insert(
                    tk.END,
                    f"  • {open_rate*100:.0f}% open rate - Review workflow bottlenecks\n",
                    "bullet"
                )
            
            # Info issues
            if disc['info_issues'] > disc['total_issues'] * 0.1:
                self.recommendations_text.insert(
                    tk.END,
                    f"  • {disc['info_issues']} information requests - Establish better communication\n",
                    "bullet"
                )
        
        # Pattern-based recommendations
        if self.patterns_data:
            self.recommendations_text.insert(tk.END, "\n\n🔄 RECURRING PATTERN ACTIONS\n", "subheading")
            high_freq_patterns = [p for p in self.patterns_data if p['occurrence_count'] > 50]
            if high_freq_patterns:
                self.recommendations_text.insert(
                    tk.END,
                    f"\nFound {len(high_freq_patterns)} high-frequency patterns (>50 occurrences):\n",
                    "info"
                )
                for p in high_freq_patterns[:10]:
                    self.recommendations_text.insert(
                        tk.END,
                        f"  • {p['common_keywords'][:40]}: {p['occurrence_count']} occurrences\n",
                        "bullet"
                    )
                self.recommendations_text.insert(
                    tk.END,
                    "\n  → Create standard checklists for these recurring issues\n",
                    "warning"
                )
        
        # Performance metrics
        self.recommendations_text.insert(tk.END, "\n\n📊 PERFORMANCE TARGETS\n", "subheading")
        total_issues = sum(p['total_issues'] for p in self.projects_data)
        total_open = sum(p['open_issues'] for p in self.projects_data)
        current_open_rate = (total_open / total_issues * 100) if total_issues > 0 else 0
        
        self.recommendations_text.insert(tk.END, f"\nCurrent open rate: {current_open_rate:.1f}%\n", "info")
        self.recommendations_text.insert(tk.END, f"Target open rate: <25%\n", "info")
        issues_to_close = int(total_open - (total_issues * 0.25))
        if issues_to_close > 0:
            self.recommendations_text.insert(
                tk.END,
                f"  → Need to close {issues_to_close:,} issues to reach target\n",
                "warning"
            )
        
        self.recommendations_text.config(state=tk.DISABLED)
    
    def sort_projects(self):
        """Sort projects based on selected criterion"""
        sort_key = self.project_sort_var.get()
        
        if sort_key == "pain_score":
            self.projects_data.sort(key=lambda x: x['pain_point_score'], reverse=True)
        elif sort_key == "total_issues":
            self.projects_data.sort(key=lambda x: x['total_issues'], reverse=True)
        elif sort_key == "open_rate":
            self.projects_data.sort(
                key=lambda x: x['open_issues']/x['total_issues'] if x['total_issues'] > 0 else 0,
                reverse=True
            )
        elif sort_key == "name":
            self.projects_data.sort(key=lambda x: x['project_name'])
        
        self.populate_projects_tree()
    
    def sort_tree_column(self, tree, col):
        """Sort treeview by column"""
        # Simple implementation - just re-populate based on current data
        pass
    
    def show_project_details(self, event):
        """Show detailed project information on double-click"""
        selection = self.projects_tree.selection()
        if not selection:
            return
        
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        
        # Find project in data
        project = next((p for p in self.projects_data if p['project_name'].startswith(project_name)), None)
        if not project:
            return
        
        # Create detail window
        detail_window = tk.Toplevel(self.frame)
        detail_window.title(f"Project Details: {project_name}")
        detail_window.geometry("600x500")
        
        # Add scrollable text
        text_frame = ttk.Frame(detail_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate details
        text.insert(tk.END, f"PROJECT: {project['project_name']}\n", "heading")
        text.insert(tk.END, f"Source: {project['source']}\n\n")
        
        text.insert(tk.END, "ISSUE METRICS:\n", "subheading")
        text.insert(tk.END, f"Total Issues: {project['total_issues']:,}\n")
        text.insert(tk.END, f"Open: {project['open_issues']:,} ({project['open_issues']/project['total_issues']*100:.1f}%)\n")
        text.insert(tk.END, f"Closed: {project['closed_issues']:,} ({project['closed_issues']/project['total_issues']*100:.1f}%)\n")
        text.insert(tk.END, f"Pain Score: {project['pain_point_score']:.2f}/1.00\n\n")
        
        if project.get('avg_resolution_days'):
            text.insert(tk.END, f"Avg Resolution Time: {project['avg_resolution_days']:.0f} days\n\n")
        
        text.insert(tk.END, "DISCIPLINE BREAKDOWN:\n", "subheading")
        text.insert(tk.END, f"Electrical: {project['electrical_issues']:,}\n")
        text.insert(tk.END, f"Hydraulic/Plumbing: {project['hydraulic_issues']:,}\n")
        text.insert(tk.END, f"Mechanical: {project['mechanical_issues']:,}\n")
        text.insert(tk.END, f"Structural: {project['structural_issues']:,}\n")
        text.insert(tk.END, f"Architectural: {project['architectural_issues']:,}\n\n")
        
        text.insert(tk.END, "ISSUE TYPES:\n", "subheading")
        text.insert(tk.END, f"Clash/Coordination: {project['clash_issues']:,}\n")
        text.insert(tk.END, f"Information Request: {project['info_issues']:,}\n")
        text.insert(tk.END, f"Design Issues: {project['design_issues']:,}\n")
        text.insert(tk.END, f"Constructability: {project['constructability_issues']:,}\n")
        
        text.config(state=tk.DISABLED)
    
    def export_report(self):
        """Export analytics report to file"""
        try:
            from tools.generate_analytics_report import generate_report
            import tkinter.filedialog as filedialog
            
            # Ask for output file
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"pain_points_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if filename:
                generate_report(filename)
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            messagebox.showerror("Error", f"Failed to export report:\n{str(e)}")


if __name__ == "__main__":
    # Test the dashboard standalone
    root = tk.Tk()
    root.title("Issue Analytics Dashboard Test")
    root.geometry("1200x800")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    dashboard = IssueAnalyticsDashboard(notebook)
    
    root.mainloop()
