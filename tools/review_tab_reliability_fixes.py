#!/usr/bin/env python3
"""
Review Management Tab - Immediate Reliability Fixes

This script provides patches and improvements for the most critical
Review Management tab issues identified in the holistic review.

Run this to apply immediate fixes to the most pressing reliability issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix 1: Template List Refresh with Proper Error Handling
def improved_refresh_template_list(self):
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
        from tkinter import messagebox
        messagebox.showerror("Template Loading Error", 
                           f"Could not load service templates.\n\n{error_msg}")
        return False

# Fix 2: Date Generation Logic Improvements
def fixed_generate_review_cycles(self, service_id: int, unit_qty: int,
                                start_date, end_date, 
                                cadence: str = 'weekly', disciplines: str = 'All'):
    """Fixed review cycle generation with consistent date handling"""
    from datetime import datetime, timedelta
    
    try:
        if unit_qty <= 0:
            print(f"⚠️  Invalid unit quantity: {unit_qty}")
            return []

        freq_key = (cadence or 'weekly').lower().replace('_', '-')
        interval_lookup = {
            'one-off': 0,
            'weekly': 7,
            'bi-weekly': 14,
            'biweekly': 14,
            'fortnightly': 14,
            'monthly': 30
        }
        
        interval_days = interval_lookup.get(freq_key)
        dates = []
        
        print(f"🗓️  Generating {unit_qty} {freq_key} reviews from {start_date} to {end_date}")
        
        if freq_key == 'one-off':
            # One-off: single review at start date
            dates = [start_date]
            print(f"   → One-off review scheduled for {start_date}")
            
        elif interval_days and interval_days > 0:
            # Fixed: Generate exactly unit_qty reviews with proper spacing
            for i in range(unit_qty):
                review_date = start_date + timedelta(days=i * interval_days)
                
                # Only cap if review would be significantly beyond end date
                if review_date > end_date + timedelta(days=7):  # 1 week grace period
                    print(f"   ⚠️  Review {i+1} would be {review_date} (beyond {end_date}), capping")
                    review_date = end_date
                
                dates.append(review_date)
                
        else:
            # Custom frequency: distribute evenly across date range
            total_days = max(1, (end_date - start_date).days)
            if unit_qty == 1:
                dates = [start_date]
            else:
                interval = total_days / (unit_qty - 1)
                dates = [start_date + timedelta(days=int(round(i * interval))) 
                        for i in range(unit_qty)]
        
        # Create cycle records
        cycles_created = []
        for i, planned_date in enumerate(dates):
            cycle_data = {
                'service_id': service_id,
                'cycle_no': i + 1,
                'planned_date': planned_date,
                'due_date': planned_date,  # For BIM meetings
                'status': 'planned',
                'disciplines': disciplines
            }
            cycles_created.append(cycle_data)
            print(f"   ✅ Cycle {i+1}: {planned_date}")
        
        print(f"✅ Generated {len(cycles_created)} review cycles")
        return cycles_created
        
    except Exception as e:
        print(f"❌ Error generating review cycles: {e}")
        return []

# Fix 3: Improved Concurrent Operation Protection
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

# Fix 4: Enhanced Error Dialog System
def show_user_friendly_error(parent, title: str, error: Exception, context: str = ""):
    """Show detailed but user-friendly error dialogs"""
    from tkinter import messagebox
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
        detail_window = tk.Toplevel(parent)
        detail_window.title(f"{title} - Details")
        detail_window.geometry("600x400")
        
        text_widget = tk.Text(detail_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, detailed_message)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(detail_window, text="Close", 
                  command=detail_window.destroy).pack(pady=10)

if __name__ == "__main__":
    print("🔧 Review Management Tab Reliability Fixes")
    print("=" * 50)
    print()
    print("This script provides improved functions for:")
    print("1. ✅ Template list refresh with user feedback")
    print("2. ✅ Fixed date generation logic") 
    print("3. ✅ Concurrent operation protection")
    print("4. ✅ Enhanced error handling")
    print()
    print("To apply these fixes:")
    print("1. Import these functions into phase1_enhanced_ui.py")
    print("2. Replace the existing methods with the improved versions")
    print("3. Add TabOperationManager to ReviewManagementTab.__init__()")
    print("4. Use show_user_friendly_error() in exception handlers")