# Cross-Function Communication - Quick Reference

**Document**: DATA_FLOW_ANALYSIS.md Companion  
**Date**: October 3, 2025

---

## 🎯 Key Findings Summary

### Critical Issues (🔴 High Priority)

| # | Issue | Impact | Solution Location |
|---|-------|--------|-------------------|
| 1 | **Project date changes don't propagate** | Service schedules, reviews, and tasks become out-of-sync | Section 3, Gap #1 |
| 2 | **Client changes not tracked in billing** | Historical claims show wrong client | Section 3, Gap #2 |
| 3 | **No database CASCADE constraints** | Orphaned records if project deleted via SQL | Section 3, Gap #3 |
| 4 | **Limited UI notification system** | Tabs display stale data | Section 3, Gap #4 |
| 5 | **No automatic review→billing flow** | Manual claim generation required | Section 2.3 |

### Medium Issues (🟡 Medium Priority)

| # | Issue | Impact | Solution Location |
|---|-------|--------|-------------------|
| 6 | **Review dates not validated vs project dates** | Reviews scheduled outside project | Section 3, Gap #5 |
| 7 | **Task dates not validated** | Tasks can exist outside project bounds | Section 3, Gap #1 |
| 8 | **No ServiceReview→Task linkage** | Can't track which tasks belong to reviews | Section 2.2 |

---

## 📊 Data Propagation Map

### When Projects.start_date or end_date Changes

**Currently Happens**:
- ✅ Projects table updated

**Should Happen (NOT IMPLEMENTED)**:
- ❌ ServiceScheduleSettings.{start|end}_date adjusted
- ❌ ServiceReviews beyond new end_date cancelled
- ❌ Tasks outside bounds flagged
- ❌ BillingClaims periods validated
- ❌ UI tabs refreshed with new dates

**Fix**: Implement enhanced `update_project_details()` - See Section 3, Gap #1

---

### When Projects.client_id Changes

**Currently Happens**:
- ✅ Projects.client_id updated

**Should Happen (NOT IMPLEMENTED)**:
- ❌ Future BillingClaims snapshot new client
- ❌ Historical claims preserve original client
- ❌ Audit log created
- ❌ UI tabs refreshed

**Fix**: Add client snapshot columns to BillingClaims - See Section 3, Gap #2

---

### When ServiceReviews.status Changes to 'completed'

**Currently Happens**:
- ✅ ServiceReviews.status updated
- ✅ ProjectServices.progress_percentage recalculated

**Should Happen (NOT IMPLEMENTED)**:
- ❌ Related Tasks.status updated
- ❌ ServiceDeliverables.status advanced
- ❌ BillingClaimLines generated automatically
- ❌ UI tabs notified of progress change

**Fix**: Add `on_review_status_changed()` handler - See Section 3, Gap #4

---

### When Project is Deleted

**Currently Happens**:
- ✅ Manual CASCADE delete in `delete_project()` function (25+ DELETE statements)

**Should Happen (NOT IMPLEMENTED)**:
- ❌ Database-level CASCADE constraints enforce deletion
- ❌ Single DELETE FROM Projects triggers all cascades
- ❌ Impossible to orphan records

**Fix**: Add ON DELETE CASCADE to all FK constraints - See Section 3, Gap #3

---

## 🔧 Quick Implementation Guide

### Phase 1: Critical Database Fixes (Week 1-2)

#### 1. Add CASCADE Constraints
```sql
-- Run this migration script
ALTER TABLE ProjectServices
ADD CONSTRAINT FK_ProjectServices_Projects 
    FOREIGN KEY (project_id) REFERENCES Projects(project_id)
    ON DELETE CASCADE;

-- Repeat for all 15+ tables with project_id
```
**Files to modify**: `sql/migrations/add_cascade_constraints.sql` (new file)

---

#### 2. Project Date Propagation
```python
# database.py - update_project_details()

def update_project_details(project_id, start_date, end_date, status, priority):
    # ... existing code ...
    
    # ADD: Propagate dates to services
    if end_date:
        cursor.execute("""
            UPDATE ServiceScheduleSettings 
            SET end_date = ? 
            WHERE service_id IN (
                SELECT service_id FROM ProjectServices WHERE project_id = ?
            ) AND end_date > ?
        """, (end_date, project_id, end_date))
    
    # ADD: Cancel reviews beyond new end date
    if end_date:
        cursor.execute("""
            UPDATE ServiceReviews
            SET status = 'cancelled'
            WHERE service_id IN (
                SELECT service_id FROM ProjectServices WHERE project_id = ?
            ) AND review_date > ? AND manual_override = 0
        """, (project_id, end_date))
```
**Files to modify**: `database.py` (lines 223-250)

---

#### 3. Client Snapshot in Billing
```sql
-- Add columns to BillingClaims
ALTER TABLE BillingClaims 
ADD client_id_snapshot INT NULL,
    client_name_snapshot NVARCHAR(255) NULL,
    contract_number_snapshot NVARCHAR(100) NULL;
```

```python
# review_management_service.py - generate_claim()

def generate_claim(self, project_id, period_start, period_end):
    # ADD: Get project + client data
    self.cursor.execute("""
        SELECT p.*, c.client_name 
        FROM Projects p
        LEFT JOIN Clients c ON p.client_id = c.client_id
        WHERE p.project_id = ?
    """, (project_id,))
    
    project = dict(zip([col[0] for col in self.cursor.description], 
                       self.cursor.fetchone()))
    
    # ADD: Insert with snapshot
    self.cursor.execute("""
        INSERT INTO BillingClaims (
            project_id, period_start, period_end,
            client_id_snapshot, client_name_snapshot
        ) VALUES (?, ?, ?, ?, ?)
    """, (project_id, period_start, period_end, 
          project['client_id'], project['client_name']))
```
**Files to modify**: 
- `sql/migrations/add_client_snapshot.sql` (new)
- `review_management_service.py` (lines 1437-1500)

---

### Phase 2: Enhanced Notifications (Week 3-4)

#### 4. Expand Notification System
```python
# phase1_enhanced_ui.py

class ProjectNotificationSystem:
    EVENT_TYPES = {
        'PROJECT_SELECTED': 'on_project_changed',
        'PROJECT_DATES_CHANGED': 'on_project_dates_changed',  # NEW
        'CLIENT_CHANGED': 'on_client_changed',                # NEW
        'REVIEW_STATUS_CHANGED': 'on_review_status_changed',  # NEW
        'SERVICE_PROGRESS_CHANGED': 'on_service_progress_changed',  # NEW
        # ... more events ...
    }
    
    def notify(self, event_type, **kwargs):
        """Generic notification dispatcher."""
        callback_name = self.EVENT_TYPES[event_type]
        for observer in self.observers:
            if hasattr(observer, callback_name):
                getattr(observer, callback_name)(**kwargs)
```
**Files to modify**: `phase1_enhanced_ui.py` (lines 79-95)

---

#### 5. Implement Tab Handlers
```python
# ui/tab_review.py (example)

class ReviewManagementTab:
    def on_project_dates_changed(self, project_id, start_date, end_date):
        """NEW: Handle project date changes."""
        if project_id == self.current_project_id:
            self.refresh_review_schedules()
            messagebox.showinfo(
                "Dates Updated",
                f"Review schedules adjusted:\n{start_date} to {end_date}"
            )
    
    def on_service_progress_changed(self, project_id, service_id, 
                                    old_progress, new_progress):
        """NEW: Handle service progress updates."""
        if project_id == self.current_project_id:
            self.update_service_display(service_id, new_progress)
```
**Files to modify**: 
- `ui/tab_review.py`
- `ui/tab_project.py`
- `ui/enhanced_task_management.py`
- All other tab files

---

## 📋 Testing Checklist

### Before Deployment

- [ ] Test project date change → services update
- [ ] Test project date change → reviews cancelled
- [ ] Test project date change → tasks flagged
- [ ] Test client change → new claims snapshot new client
- [ ] Test client change → old claims preserve original
- [ ] Test review completion → service progress updates
- [ ] Test review completion → UI refreshes
- [ ] Test project deletion → all related records deleted
- [ ] Test project deletion → no orphans remain
- [ ] Test cross-tab notification → all tabs refresh

### Manual Verification Queries

```sql
-- Check for orphaned services
SELECT ps.* 
FROM ProjectServices ps
LEFT JOIN Projects p ON ps.project_id = p.project_id
WHERE p.project_id IS NULL;

-- Check for reviews outside project dates
SELECT sr.*, p.start_date, p.end_date
FROM ServiceReviews sr
JOIN ProjectServices ps ON sr.service_id = ps.service_id
JOIN Projects p ON ps.project_id = p.project_id
WHERE sr.review_date < p.start_date OR sr.review_date > p.end_date;

-- Check for tasks outside project dates
SELECT t.*, p.start_date, p.end_date
FROM Tasks t
JOIN Projects p ON t.project_id = p.project_id
WHERE t.start_date < p.start_date OR t.end_date > p.end_date;
```

---

## 🚀 Deployment Plan

### Step 1: Backup Database
```bash
# Create full backup before any changes
sqlcmd -S SERVER -d ProjectManagement -Q "BACKUP DATABASE ProjectManagement TO DISK='backup_pre_cascade.bak'"
```

### Step 2: Run Migrations (in order)
```bash
# 1. Add CASCADE constraints
sqlcmd -S SERVER -d ProjectManagement -i sql/migrations/add_cascade_constraints.sql

# 2. Add client snapshot columns
sqlcmd -S SERVER -d ProjectManagement -i sql/migrations/add_client_snapshot.sql

# 3. Backfill existing claims (optional)
sqlcmd -S SERVER -d ProjectManagement -i sql/migrations/backfill_client_snapshots.sql
```

### Step 3: Deploy Code Changes
```bash
# Stop application
# Update codebase
git pull origin master

# Update Python environment
pip install -r requirements.txt

# Restart application
python run_enhanced_ui.py
```

### Step 4: Validation
```bash
# Run test suite
python -m pytest tests/ -v

# Manual smoke tests (see Testing Checklist above)
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: "FK constraint error when adding CASCADE"  
**Solution**: Drop existing FK first, then add new one with CASCADE

**Issue**: "Reviews still showing after project end date change"  
**Solution**: Run `refresh_review_statuses(project_id)` manually

**Issue**: "Tabs not refreshing after project change"  
**Solution**: Check that tab implements `on_project_dates_changed()` callback

---

## 📚 Related Documentation

- **Full Analysis**: `docs/DATA_FLOW_ANALYSIS.md`
- **Database Schema**: `docs/database_schema.md`
- **Review Management**: `docs/enhanced_review_management_overview.md`
- **API Reference**: `docs/api_reference.md` (to be created)

---

**Last Updated**: October 3, 2025  
**Maintainer**: Development Team
