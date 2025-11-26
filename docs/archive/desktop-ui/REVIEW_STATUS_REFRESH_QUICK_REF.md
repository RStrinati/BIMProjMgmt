# Review Status & Refresh Issues - Quick Reference

## TL;DR - The Problem

**When you manually update a review's status or date, clicking "Refresh Status" resets your changes.**

This happens because the refresh function **automatically recalculates** all statuses based on meeting dates, overwriting any manual changes you made.

---

## Root Causes

### 1. Auto-Calculation Logic Overwrites Manual Changes

**Location:** `review_management_service.py`, method `update_service_statuses_by_date()`

**What it does:**
- Compares each review's `due_date` with today's date
- Automatically sets status:
  - Past dates → `'completed'`
  - Today/near future → `'in_progress'`
  - Far future → `'planned'`

**The problem:**
- No distinction between manual vs automatic status changes
- No "lock" or "override" flag to preserve user edits
- Runs every time you click "Refresh Status"

### 2. Edit Dialog Updates Wrong Date Field

**Location:** `phase1_enhanced_ui.py`, method `update_review_in_database()`

**What it does:**
- Updates `planned_date` when you edit a review
- Updates `status` field

**The problem:**
- Refresh logic uses `due_date`, not `planned_date`
- Even though status is saved, it gets recalculated from `due_date`
- No override flag is set when you manually edit

### 3. Two Different Update Mechanisms Don't Coordinate

**Method 1:** Status Update Dialog (`show_status_update_dialog`)
- Updates status only
- Calls `review_service.update_review_status_to()`
- Works correctly BUT...

**Method 2:** Edit Review Dialog (`show_edit_review_dialog`)
- Updates date + status + disciplines
- Calls `update_review_in_database()` directly
- Updates wrong date field

**The problem:**
- Neither method sets an "override" flag
- Refresh logic doesn't know the change was manual

---

## Quick Fix (Temporary)

### Option 1: Don't Click "Refresh Status" After Manual Edits

**Workaround:**
1. Make your manual status/date changes
2. **Don't** click "Refresh Status" button
3. Changes will persist until next refresh

**Limitation:** Doesn't protect against background sync (runs every 60 seconds)

### Option 2: Disable Background Sync

**File:** `phase1_enhanced_ui.py`, line 2511

**Comment out this line:**
```python
# self.frame.after(5000, self.start_background_sync)  # DISABLED
```

**Impact:** No automatic updates, but manual changes persist

---

## Proper Solution

### Add Manual Override Tracking

**Required Changes:**

1. **Database Schema** - Add 3 columns to `ServiceReviews`:
   ```sql
   ALTER TABLE ServiceReviews
   ADD status_override BIT DEFAULT 0,
       status_override_by VARCHAR(100),
       status_override_at DATETIME2;
   ```

2. **Service Layer** - Update refresh logic to skip overrides:
   ```python
   # In update_service_statuses_by_date()
   if status_override == 1:
       continue  # Skip this review
   ```

3. **UI Layer** - Set override flag on manual edits:
   ```python
   # In update_review_in_database()
   UPDATE ServiceReviews 
   SET status = ?, 
       due_date = ?,  -- Fix: update correct field
       status_override = 1,
       status_override_by = SYSTEM_USER,
       status_override_at = SYSDATETIME()
   WHERE review_id = ?
   ```

4. **Visual Indicator** - Show lock icon for manual overrides:
   ```python
   # In refresh_cycles()
   status_display = f"🔒 {status}" if has_override else status
   ```

**See full implementation in:** `docs/REVIEW_STATUS_REFRESH_SOLUTIONS.md`

---

## Files Affected

| File | Issue | Fix Required |
|------|-------|--------------|
| `review_management_service.py` | Auto-refresh overwrites changes | Add override checking |
| `phase1_enhanced_ui.py` | Updates wrong date field | Fix `update_review_in_database()` |
| `phase1_enhanced_ui.py` | No override flag set | Update both dialog methods |
| `database.py` | Missing override column | Add to queries |
| SQL Server | No override tracking | Run migration script |

---

## Test Scenario

**Before Fix:**
1. ✅ Manually set future review to "completed"
2. ✅ Save successful, status shows "completed"
3. ❌ Click "Refresh Status"
4. ❌ Status reverts to "planned" (PROBLEM!)

**After Fix:**
1. ✅ Manually set future review to "completed"
2. ✅ Save successful, status shows "🔒 completed" (override indicator)
3. ✅ Click "Refresh Status"
4. ✅ Status remains "completed" (override protected)
5. ✅ Option to "Reset to Auto" if needed

---

## Implementation Priority

**HIGH PRIORITY** - This affects core workflow functionality

**Estimated Effort:**
- Quick fix (workaround): 15 minutes
- Proper solution: 3-4 hours
- Testing: 1 hour

**Risk:** LOW - Backward compatible, defaults preserve current behavior

---

## Next Steps

1. **Immediate:** Review analysis documents
   - `docs/REVIEW_STATUS_REFRESH_ANALYSIS.md` - Detailed problem analysis
   - `docs/REVIEW_STATUS_REFRESH_SOLUTIONS.md` - Complete solution design

2. **Decision:** Choose implementation approach
   - Full solution with database changes (recommended)
   - Quick fix with evidence_links workaround (temporary)

3. **Implementation:** Follow solution document step-by-step

4. **Testing:** Run test cases from solutions document

5. **Deployment:** Update production after UAT

---

## Questions?

See the detailed documents:
- **Problem Analysis:** `docs/REVIEW_STATUS_REFRESH_ANALYSIS.md`
- **Solution Design:** `docs/REVIEW_STATUS_REFRESH_SOLUTIONS.md`

Or ask the development team for clarification on specific sections.

---

*Quick Reference - October 1, 2025*
