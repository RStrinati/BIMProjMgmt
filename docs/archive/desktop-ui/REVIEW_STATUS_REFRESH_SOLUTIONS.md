# Review Status & Refresh - Recommended Solutions

## Overview

This document provides **actionable solutions** to fix the review status update and refresh issues identified in `REVIEW_STATUS_REFRESH_ANALYSIS.md`.

---

## Solution Strategy

We need to implement a **hybrid approach** that supports both:
1. **Automated workflow** - Status auto-updates based on dates (for convenience)
2. **Manual override** - User changes that persist (for flexibility)

---

## Recommended Solution: Manual Override Flag

### Approach

Add a **manual override tracking system** that:
- Allows auto-updates by default (current behavior)
- Respects manual user changes (new behavior)
- Provides clear UI feedback about override state
- Allows users to "reset to auto" if desired

### Database Schema Changes

#### Option A: Add Column to ServiceReviews (Recommended)

```sql
ALTER TABLE ServiceReviews
ADD status_override BIT DEFAULT 0,
    status_override_by VARCHAR(100),
    status_override_at DATETIME2;
```

**Benefits:**
- Simple to implement
- Clear semantics
- Easy to query and filter
- Backward compatible (defaults to 0 = auto)

#### Option B: Use Existing Field Creatively (No Schema Change)

Use the `evidence_links` field to store a special marker:

```
[MANUAL_OVERRIDE]|actual_link_url
```

**Benefits:**
- No schema changes needed
- Works immediately
- Can still store evidence links

**Drawbacks:**
- Hacky solution
- Harder to query
- Not recommended for production

---

## Implementation Plan

### Phase 1: Core Logic Changes (High Priority)

#### 1.1 Update `update_service_statuses_by_date()` Method

**File:** `review_management_service.py`, Lines 3298-3434

**Current Logic:**
```python
# Determine new status based on workflow progression
if due_date < today:
    if current_status != 'completed':
        new_status = 'completed'
```

**New Logic:**
```python
def update_service_statuses_by_date(self, project_id: int = None, respect_overrides: bool = True) -> Dict:
    """Automatically update service review statuses based on meeting dates.
    
    Args:
        project_id: Project to update (None = all projects)
        respect_overrides: If True, skip reviews with manual status overrides
    """
    # ... existing code ...
    
    # Get reviews with override information
    base_query = """
        SELECT sr.review_id, sr.service_id, sr.planned_date, sr.due_date, 
               sr.status, sr.actual_issued_at, ps.service_name,
               ISNULL(sr.status_override, 0) as status_override
        FROM ServiceReviews sr
        INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
    """
    
    for review in reviews:
        review_id, service_id, planned_date, due_date, current_status, \
            actual_issued_at, service_name, status_override = review
        
        # NEW: Skip if manual override is set
        if respect_overrides and status_override == 1:
            print(f"   ⚠️ Review {review_id}: Skipping (manual override)")
            continue
        
        # ... rest of existing logic ...
```

**Impact:**
- ✅ Respects manual status changes
- ✅ Backward compatible (status_override defaults to 0)
- ✅ Can be toggled via parameter

---

#### 1.2 Update `update_review_status_to()` Method

**File:** `review_management_service.py`, Lines 1328-1420

**Add Manual Override Flag:**
```python
def update_review_status_to(self, review_id: int, new_status: str, 
                            evidence_link: str = None, 
                            is_manual_override: bool = True) -> bool:
    """Update review status to any valid status with optional evidence link
    
    Args:
        review_id: Review to update
        new_status: New status value
        evidence_link: Optional evidence URL
        is_manual_override: If True, marks this as a manual status change
    """
    try:
        # ... existing validation ...
        
        # Build query with override tracking
        if new_status in ['completed', 'report_issued', 'closed']:
            query = """
            UPDATE ServiceReviews 
            SET status = ?, 
                actual_issued_at = COALESCE(actual_issued_at, SYSDATETIME()),
                evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END,
                status_override = ?,
                status_override_by = CASE WHEN ? = 1 THEN SYSTEM_USER ELSE NULL END,
                status_override_at = CASE WHEN ? = 1 THEN SYSDATETIME() ELSE NULL END
            WHERE review_id = ?
            """
            override_flag = 1 if is_manual_override else 0
            self.cursor.execute(query, (
                new_status, 
                evidence_link, evidence_link,
                override_flag,
                override_flag,
                override_flag,
                review_id
            ))
        else:
            # Similar for other statuses...
            query = """
            UPDATE ServiceReviews 
            SET status = ?,
                evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END,
                status_override = ?,
                status_override_by = CASE WHEN ? = 1 THEN SYSTEM_USER ELSE NULL END,
                status_override_at = CASE WHEN ? = 1 THEN SYSDATETIME() ELSE NULL END
            WHERE review_id = ?
            """
            override_flag = 1 if is_manual_override else 0
            self.cursor.execute(query, (
                new_status,
                evidence_link, evidence_link,
                override_flag,
                override_flag,
                override_flag,
                review_id
            ))
        
        self.db.commit()
        return self.cursor.rowcount > 0
```

**Impact:**
- ✅ Tracks who made manual changes
- ✅ Tracks when manual changes were made
- ✅ Can distinguish manual vs automatic updates

---

#### 1.3 Fix `update_review_in_database()` Method

**File:** `phase1_enhanced_ui.py`, Lines 5422-5450

**Current Issues:**
1. Updates `planned_date` instead of `due_date`
2. Doesn't set override flag
3. Missing notes field in database

**Fixed Version:**
```python
def update_review_in_database(self, review_id, planned_start, status, stage, notes):
    """Update review cycle in database"""
    try:
        conn = connect_to_db()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # FIX 1: Update BOTH planned_date AND due_date
        # FIX 2: Add status_override flag
        # FIX 3: Store notes in evidence_links if no notes field exists
        update_sql = """
        UPDATE ServiceReviews 
        SET planned_date = ?, 
            due_date = ?,  -- FIX: Also update due_date
            status = ?, 
            disciplines = ?,
            evidence_links = CASE 
                WHEN evidence_links IS NULL OR evidence_links = '' THEN ?
                ELSE evidence_links + CHAR(10) + ?
            END,
            status_override = 1,  -- FIX: Mark as manual override
            status_override_by = SYSTEM_USER,
            status_override_at = SYSDATETIME()
        WHERE review_id = ?
        """
        
        # Format notes with timestamp
        note_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}" if notes else ""
        
        cursor.execute(update_sql, (
            planned_start, 
            planned_start,  # Use same date for due_date
            status, 
            stage,
            note_entry,
            note_entry,
            review_id
        ))
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Error updating review in database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
```

**Impact:**
- ✅ Updates the correct date field used by refresh logic
- ✅ Sets override flag to prevent auto-updates
- ✅ Preserves notes history

---

### Phase 2: UI Enhancements (Medium Priority)

#### 2.1 Add Override Indicator to Cycles Tree

**File:** `phase1_enhanced_ui.py`, Lines 4298-4370

**Add Override Column:**
```python
def refresh_cycles(self):
    """Refresh the review cycles display"""
    # ... existing code ...
    
    # Add override indicator to display
    for cycle in cycles:
        # ... existing formatting ...
        
        # Check if manual override is set
        override_icon = "🔒" if cycle[7] else ""  # Assuming index 7 is status_override
        
        formatted_cycle = (
            str(cycle[0]),
            f"{cycle[1]} - Cycle {cycle_no}",
            cycle[3] or "",
            f"{override_icon} {cycle[5] or ''}",  # Add lock icon to status
            cycle[6] if len(cycle) > 6 and cycle[6] else "All",
            "",
            notes
        )
        self.cycles_tree.insert("", tk.END, values=formatted_cycle)
```

**Update Query in database.py:**
```python
def get_review_cycles(project_id):
    """Return review cycles for the given project from ServiceReviews table."""
    # ... existing code ...
    cursor.execute(
        """
        SELECT sr.review_id, ps.service_name, sr.cycle_no, sr.planned_date, 
               sr.due_date, sr.status, sr.disciplines, 
               ISNULL(sr.status_override, 0) as status_override
        FROM ServiceReviews sr
        LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
        WHERE ps.project_id = ?
        ORDER BY sr.planned_date, sr.cycle_no;
        """,
        (project_id,),
    )
    # ... rest of code ...
```

**Impact:**
- ✅ Users can see which reviews have manual overrides
- ✅ Visual feedback prevents confusion
- ✅ Lock icon (🔒) indicates "protected from auto-update"

---

#### 2.2 Add "Reset to Auto" Option

**File:** `phase1_enhanced_ui.py`, add new method

```python
def reset_review_to_auto(self):
    """Reset selected review to automatic status management"""
    try:
        selection = self.cycles_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a review first")
            return
        
        item = self.cycles_tree.item(selection[0])
        review_data = item['values']
        review_id = review_data[0]
        
        # Confirm action
        result = messagebox.askyesno(
            "Reset to Auto", 
            "This will reset the review to automatic status management.\n"
            "The status will be recalculated based on the meeting date.\n\n"
            "Continue?"
        )
        
        if not result:
            return
        
        # Clear override flag
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ServiceReviews 
                SET status_override = 0,
                    status_override_by = NULL,
                    status_override_at = NULL
                WHERE review_id = ?
            """, (review_id,))
            conn.commit()
            conn.close()
            
            # Trigger refresh to recalculate status
            if self.review_service:
                self.review_service.update_service_statuses_by_date(
                    self.current_project_id, 
                    respect_overrides=False  # Force recalculation
                )
            
            messagebox.showinfo("Success", "Review reset to automatic status management")
            self.refresh_cycles()
        
    except Exception as e:
        messagebox.showerror("Error", f"Error resetting to auto: {e}")
```

**Add to Context Menu:**
```python
# In setup_review_planning_tab() or wherever cycles_tree context menu is defined
def show_cycles_context_menu(event):
    menu = tk.Menu(self.frame, tearoff=0)
    menu.add_command(label="Update Status", command=self.update_review_status)
    menu.add_command(label="Edit Review", command=self.edit_review_cycle)
    menu.add_separator()
    menu.add_command(label="🔓 Reset to Auto Status", command=self.reset_review_to_auto)
    menu.add_separator()
    menu.add_command(label="Delete Review", command=self.delete_review_cycle)
    # ... etc
```

**Impact:**
- ✅ Users can revert to automatic mode if needed
- ✅ Provides escape hatch for mistakes
- ✅ Clear workflow for both modes

---

#### 2.3 Improve Refresh Status Dialog

**File:** `phase1_enhanced_ui.py`, Lines 5692-5725

**Enhanced Version:**
```python
def manual_refresh_statuses(self):
    """Manual refresh button handler for status updates"""
    try:
        if not self.current_project_id:
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        if not self.review_service:
            messagebox.showerror("Error", "Review service not initialized")
            return
        
        # NEW: Show confirmation dialog with override info
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ServiceReviews sr
            INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
            WHERE ps.project_id = ? AND sr.status_override = 1
        """, (self.current_project_id,))
        override_count = cursor.fetchone()[0]
        conn.close()
        
        if override_count > 0:
            result = messagebox.askyesno(
                "Refresh Status", 
                f"This will auto-update review statuses based on meeting dates.\n\n"
                f"⚠️  {override_count} review(s) have manual status overrides.\n"
                f"These will NOT be changed.\n\n"
                f"Continue with refresh?"
            )
            if not result:
                return
        
        # Perform refresh with override protection
        results = self.review_service.refresh_all_project_statuses(self.current_project_id)
        
        # Enhanced results dialog
        summary = f"""Status Refresh Results:

📋 Reviews Auto-Updated: {results['reviews_updated']}
🔒 Manual Overrides Preserved: {override_count}
🔧 Services Updated: {results['services_updated']}
📊 Overall Status: {results['overall_status'].get('status_summary', 'Unknown')}
📈 Progress: {results['overall_status'].get('progress_percentage', 0):.1f}%

Completed: {results['overall_status'].get('completed_reviews', 0)}
In Progress: {results['overall_status'].get('in_progress_reviews', 0)}
Planned: {results['overall_status'].get('planned_reviews', 0)}"""

        if results['errors']:
            summary += f"\n\n❌ Errors:\n" + "\n".join(results['errors'])
            
        messagebox.showinfo("Status Refresh Complete", summary)
        
        # Refresh UI
        self.load_project_services()
        self.load_billing_data()
        self.refresh_cycles()
        
    except Exception as e:
        messagebox.showerror("Error", f"Error refreshing statuses: {e}")
```

**Impact:**
- ✅ Users know how many overrides exist
- ✅ Clear feedback that overrides will be preserved
- ✅ Results show how many were protected

---

### Phase 3: Background Sync Improvements (Low Priority)

#### 3.1 Disable Background Sync During Active Editing

**File:** `phase1_enhanced_ui.py`, Lines 3409-3450

```python
def start_background_sync(self):
    """Start background sync mechanism for automatic updates"""
    try:
        # NEW: Check if user is actively editing
        if self.is_user_editing():
            print("⏸️  Background sync paused - user is editing")
            self.frame.after(60000, self.start_background_sync)
            return
        
        if hasattr(self, 'current_project_id') and self.current_project_id:
            self.check_service_changes_and_update()
        
        self.frame.after(60000, self.start_background_sync)
        
    except Exception as e:
        print(f"Error in background sync: {e}")
        self.frame.after(60000, self.start_background_sync)

def is_user_editing(self):
    """Check if user is actively editing data"""
    # Check if any dialog windows are open
    if hasattr(self, 'frame') and self.frame.winfo_toplevel().focus_get():
        focused = self.frame.winfo_toplevel().focus_get()
        # Check if focused widget is in a Toplevel (dialog)
        if focused and isinstance(focused.winfo_toplevel(), tk.Toplevel):
            return True
    return False
```

**Impact:**
- ✅ Prevents background sync during active editing
- ✅ Reduces user confusion and conflicts
- ✅ Improves user experience

---

## Migration Script

**File:** `tools/migrate_review_override_tracking.py`

```python
"""
Migration script to add status_override tracking to ServiceReviews table
Run this ONCE to add the new columns
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

def migrate_add_override_columns():
    """Add status_override tracking columns to ServiceReviews"""
    conn = connect_to_db()
    if not conn:
        print("❌ Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("📋 Checking if columns already exist...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ServiceReviews' 
            AND COLUMN_NAME = 'status_override'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ Columns already exist, migration not needed")
            return True
        
        print("🔧 Adding status_override tracking columns...")
        cursor.execute("""
            ALTER TABLE ServiceReviews
            ADD status_override BIT DEFAULT 0,
                status_override_by VARCHAR(100),
                status_override_at DATETIME2;
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Set default values for existing records
        print("🔧 Setting defaults for existing records...")
        cursor.execute("""
            UPDATE ServiceReviews
            SET status_override = 0
            WHERE status_override IS NULL
        """)
        conn.commit()
        
        print(f"✅ Updated {cursor.rowcount} existing records")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("ServiceReviews Status Override Migration")
    print("=" * 60)
    
    result = migrate_add_override_columns()
    
    if result:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update review_management_service.py methods")
        print("2. Update phase1_enhanced_ui.py UI methods")
        print("3. Test with a sample project")
    else:
        print("\n❌ Migration failed - check error messages above")
    
    input("\nPress Enter to exit...")
```

---

## Testing Strategy

### Test Cases

#### TC1: Manual Status Update Persists
1. Select a future review (status = 'planned')
2. Manually set status to 'completed'
3. Click "Refresh Status" button
4. **Expected:** Status remains 'completed' (not reverted to 'planned')
5. **Expected:** Lock icon (🔒) appears next to status

#### TC2: Auto Status Update Works
1. Create a review with due_date = yesterday
2. Status = 'planned'
3. Click "Refresh Status" button
4. **Expected:** Status changes to 'completed' automatically
5. **Expected:** No lock icon (auto-managed)

#### TC3: Edit Dialog Updates Persist
1. Select a review
2. Click "Edit Review"
3. Change status to 'in_progress', date to tomorrow
4. Save changes
5. Click "Refresh Status"
6. **Expected:** Status remains 'in_progress'
7. **Expected:** Due date is tomorrow (not recalculated)

#### TC4: Reset to Auto Works
1. Select a review with manual override (has 🔒 icon)
2. Right-click → "Reset to Auto Status"
3. Confirm action
4. **Expected:** Lock icon disappears
5. **Expected:** Status recalculated based on date
6. Click "Refresh Status"
7. **Expected:** Status updates automatically

#### TC5: Background Sync Respects Overrides
1. Set a manual status override
2. Wait 60 seconds for background sync
3. **Expected:** Manual status unchanged
4. **Expected:** No user interruption

---

## Rollout Plan

### Step 1: Database Migration (15 min)
- Run migration script to add columns
- Verify columns exist
- Test on dev database first

### Step 2: Update Service Layer (30 min)
- Update `update_service_statuses_by_date()` to respect overrides
- Update `update_review_status_to()` to set override flag
- Test both methods

### Step 3: Update UI Layer (45 min)
- Fix `update_review_in_database()` to update correct fields
- Add override indicator to cycles tree
- Update refresh dialog
- Test all UI flows

### Step 4: Add Enhancement Features (30 min)
- Add "Reset to Auto" option
- Improve background sync logic
- Add user documentation

### Step 5: Testing (1 hour)
- Run all test cases
- Test with real project data
- User acceptance testing

**Total Estimated Time:** 3-4 hours for complete implementation

---

## Quick Fix Option (No Schema Changes)

If database schema changes are not possible immediately, use this workaround:

### Use Evidence Links Field as Override Marker

```python
# In update_review_status_to()
if is_manual_override:
    # Prepend special marker to evidence_links
    current_evidence = self.get_review_evidence_links(review_id) or ""
    if not current_evidence.startswith("[MANUAL_OVERRIDE]"):
        new_evidence = f"[MANUAL_OVERRIDE]|{evidence_link or ''}"
        # Update with marker
    else:
        # Already has override marker, just update link
        pass

# In update_service_statuses_by_date()
# Check for marker
if evidence_links and evidence_links.startswith("[MANUAL_OVERRIDE]"):
    print(f"   ⚠️ Review {review_id}: Skipping (manual override)")
    continue
```

**Pros:**
- No schema changes needed
- Works immediately
- Can be implemented in 1 hour

**Cons:**
- Hacky solution
- Pollutes evidence_links field
- No audit trail (who/when)
- Harder to query

---

## Conclusion

The **recommended solution** is to implement the manual override flag system with proper database columns. This provides:

✅ Clear semantics and audit trail  
✅ User control over status management  
✅ Automatic workflow when desired  
✅ Visual feedback and transparency  
✅ Backward compatibility  

The **quick fix** using evidence_links can be used as a temporary solution if immediate action is needed before database changes can be approved.

---

*Solution Design Date: October 1, 2025*  
*Implementation Priority: HIGH*  
*Estimated Effort: 3-4 hours for full solution, 1 hour for quick fix*
