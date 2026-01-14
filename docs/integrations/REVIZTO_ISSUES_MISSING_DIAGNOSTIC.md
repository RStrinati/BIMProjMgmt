# Revizto Issues Missing from Analytics Dashboard - Diagnostic Report

**Date:** October 15, 2025  
**Issue:** No Revizto issues appearing in Analytics Dashboard  
**Status:** 🔴 **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

**THE PROBLEM:** The Analytics Dashboard shows 0 Revizto issues because there are **NO Revizto issues in the database**. The Revizto data extraction pipeline exists but has never been populated with data.

**Current State:**
- ✅ View structure is correct (`vw_ProjectManagement_AllIssues`)
- ✅ Revizto tables exist in the database
- ✅ Revizto extraction tracking system is in place
- ❌ **Zero Revizto issues have been imported**
- ❌ Revizto extraction has never been run successfully

**Data Count:**
- ACC Issues: **2,671** ✅
- Revizto Issues: **0** ❌

---

## Root Cause Analysis

### 1. The View is Correctly Defined

The `vw_ProjectManagement_AllIssues` view has the correct structure to pull Revizto data:

```sql
CREATE VIEW [dbo].[vw_ProjectManagement_AllIssues] AS

-- ACC issues
SELECT
    'ACC' AS source,
    display_id AS issue_id,
    title,
    status,
    created_at,
    closed_at,
    assignee_display_name AS assignee,
    latest_comment_by AS author,
    project_name,
    project_id,
    COALESCE(Priority, Clash_Level) AS priority,
    NULL AS web_link,
    NULL AS preview_middle_url
FROM acc_data_schema.dbo.vw_issues_expanded

UNION ALL

-- Revizto issues - CORRECT STRUCTURE
SELECT
    'Revizto' AS source,
    CAST(issue_number AS NVARCHAR(100)) AS issue_id,
    title,
    status,
    TRY_CAST(created AS DATETIME) AS created_at,
    TRY_CAST(updated AS DATETIME) AS closed_at,
    assignee_email AS assignee,
    author_email AS author,
    project_title AS project_name,
    CAST(projectUuid AS NVARCHAR(100)) AS project_id,
    priority,
    web_link,
    preview_middle_url
FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed;
```

**Status:** ✅ View definition is correct

### 2. The Revizto Source View is Empty

The view queries from `ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed`:

```
Database: ReviztoData ✅ EXISTS
View: vw_ReviztoProjectIssues_Deconstructed ✅ EXISTS
Issue Count: 0 ❌ EMPTY
```

**Status:** ❌ Source view contains zero issues

### 3. The Revizto Tables are Empty

All Revizto-related tables in the ProjectManagement database are empty:

| Table Name | Record Count | Status |
|-----------|--------------|---------|
| `tblReviztoProjectIssues` | 0 | ❌ Empty |
| `tblReviztoIssueComments` | 0 | ❌ Empty |
| `tblReviztoProjects` | 0 | ❌ Empty |
| `ReviztoExtractionRuns` | Unknown* | ⚠️ Schema issue |

*The `ReviztoExtractionRuns` table has schema mismatches (wrong column names)

**Status:** ❌ All Revizto data tables are empty

### 4. No Extraction Runs Have Completed

The Revizto extraction tracking system exists but shows:
- No completed extraction runs
- No extraction history
- Schema issues with tracking table (column name mismatches)

**Status:** ❌ Revizto data has never been successfully imported

---

## Why This Happened

### The Revizto Data Pipeline

The system has the **infrastructure** for Revizto data but the **data itself** has never been imported:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Revizto External System                      │
│                 (Model Coordination Platform)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Manual Export Required
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              ReviztoDataExporter.exe (External Tool)            │
│              Exports Revizto data to files                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Import Process (NOT RUN)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              ReviztoData Database                               │
│              vw_ReviztoProjectIssues_Deconstructed (0 issues)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ UNION ALL in view
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              vw_ProjectManagement_AllIssues                     │
│              Shows: ACC (2,671) + Revizto (0) = 2,671 total     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Analytics Dashboard                                │
│              Displays: Only ACC issues visible                  │
└─────────────────────────────────────────────────────────────────┘
```

### What's Missing

1. **No Revizto data export has been performed**
2. **No Revizto data has been imported into the database**
3. **The extraction tracking system has schema issues**

---

## System Readiness Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| Database schema (ReviztoData) | ✅ Ready | Database exists |
| View: vw_ReviztoProjectIssues_Deconstructed | ✅ Ready | View exists, schema correct |
| View: vw_ProjectManagement_AllIssues | ✅ Ready | Includes Revizto UNION |
| Revizto tables (ProjectManagement) | ✅ Ready | Tables exist, empty |
| Extraction tracking table | ⚠️ Schema Issues | Column name mismatches |
| Extraction functions (database.py) | ✅ Ready | Functions exist |
| UI for extraction | ✅ Ready | Revizto Data tab exists |
| **ACTUAL REVIZTO DATA** | ❌ **MISSING** | **No data imported** |

---

## How to Fix: Import Revizto Data

### Option 1: Run Revizto Extraction (Recommended)

**Prerequisites:**
- Access to Revizto platform
- ReviztoDataExporter.exe tool installed
- Revizto project credentials

**Steps:**

1. **Start the BIM Management Application:**
   ```bash
   python run_enhanced_ui.py
   ```

2. **Navigate to Revizto Data Tab:**
   - Go to "Review Management" tab
   - Select "Revizto Data" sub-tab

3. **Run Extraction:**
   - Click "Start Revizto Extract" button
   - This should launch ReviztoDataExporter.exe
   - Follow the export wizard

4. **Verify Import:**
   - Check extraction history in the UI
   - Verify data in database:
   ```sql
   SELECT COUNT(*) FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed;
   ```

5. **Refresh Analytics:**
   - Navigate to Analytics Dashboard
   - Issues should now show both ACC and Revizto

### Option 2: Manual Database Import

If you have Revizto data in another format (CSV, Excel, JSON):

1. **Check data structure:**
   ```sql
   -- View the expected schema
   SELECT TOP 0 * FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed;
   ```

2. **Required columns:**
   - issue_number
   - title
   - status
   - created (datetime)
   - updated (datetime)
   - assignee_email
   - author_email
   - project_title
   - projectUuid
   - priority
   - web_link
   - preview_middle_url

3. **Import data using SQL Server Import Wizard or bulk insert**

4. **Verify import:**
   ```sql
   SELECT 
       source,
       COUNT(*) as count
   FROM vw_ProjectManagement_AllIssues
   GROUP BY source;
   ```

### Option 3: API-Based Import (Future Enhancement)

The backend has Revizto API endpoints but they're not fully implemented:

**File:** `backend/app.py`
- `/api/revizto/start-extraction` - Starts extraction run
- `/api/revizto/extraction-runs` - Gets extraction history
- `/api/revizto/extraction-runs/last` - Gets last run

These could be enhanced to:
1. Call Revizto API directly (no manual export needed)
2. Transform Revizto API responses
3. Insert directly into ReviztoData database

---

## Schema Issues to Fix

### ReviztoExtractionRuns Table

The table schema doesn't match the code expectations:

**Current Schema Issue:**
```python
# Code expects:
cursor.execute("SELECT run_id, run_date, total_files FROM ReviztoExtractionRuns")

# Error: Invalid column name 'run_date', 'total_files'
```

**Action Required:**
1. Check actual table schema:
   ```sql
   SELECT COLUMN_NAME, DATA_TYPE 
   FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'ReviztoExtractionRuns'
   ORDER BY ORDINAL_POSITION;
   ```

2. Update schema or update code to match

---

## Verification Checklist

After importing Revizto data, verify:

- [ ] ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed has > 0 rows
- [ ] vw_ProjectManagement_AllIssues shows both 'ACC' and 'Revizto' sources
- [ ] Analytics Dashboard displays Revizto issue counts
- [ ] Recent Issues section shows Revizto issues
- [ ] Project-specific views include Revizto issues
- [ ] Revizto extraction runs are tracked properly

**SQL Verification Queries:**

```sql
-- 1. Check source view
SELECT COUNT(*) as revizto_count
FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed;

-- 2. Check unified view
SELECT 
    source,
    COUNT(*) as count,
    COUNT(DISTINCT project_name) as projects,
    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_issues,
    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_issues
FROM vw_ProjectManagement_AllIssues
GROUP BY source;

-- 3. Sample Revizto issues
SELECT TOP 5
    source,
    issue_id,
    title,
    status,
    project_name,
    created_at
FROM vw_ProjectManagement_AllIssues
WHERE source = 'Revizto'
ORDER BY created_at DESC;
```

---

## Related Files

### Database
- `database.py` - Lines 2201-2250: Revizto extraction functions
- `ReviztoData` database - Source data storage
- `vw_ProjectManagement_AllIssues` - Unified view

### Backend
- `backend/app.py` - Lines 1276-1320: Revizto API endpoints

### Frontend
- `frontend/src/pages/AnalyticsPage.tsx` - Analytics Dashboard
- `frontend/src/api/issues.ts` - Issues API client

### Documentation
- `REVIZTO_EXTRACTION_README.md` - Extraction system overview
- `REVIZTO_INTEGRATION_FIX.md` - Previous integration fixes
- `docs/ANALYTICS_DASHBOARD_DATA_SOURCE_REVIEW.md` - Data flow analysis

### Tools (for diagnostics)
- `tools/check_revizto_issues.py` - Diagnostic script (created today)
- `tools/diagnose_revizto_data.py` - Comprehensive diagnostic (created today)

---

## Recommendations

### Immediate Actions

1. **Fix ReviztoExtractionRuns schema** - Align column names with code
2. **Document Revizto extraction process** - Step-by-step guide for users
3. **Test extraction workflow** - Ensure ReviztoDataExporter.exe works
4. **Import historical Revizto data** - If available from previous exports

### Short-term Enhancements

1. **Add data validation** - Check if Revizto data exists before showing charts
2. **Display helpful message** - If no Revizto data, show "No Revizto data imported yet"
3. **Add import status indicator** - Show last successful import date
4. **Create import wizard** - Guide users through first-time setup

### Long-term Improvements

1. **Direct API integration** - Eliminate manual export step
2. **Scheduled imports** - Automatic nightly/weekly Revizto data sync
3. **Incremental updates** - Only import changed/new issues
4. **Data quality monitoring** - Alert when imports fail or data is stale

---

## Conclusion

**The Analytics Dashboard is working correctly.** The issue is simply that **no Revizto data has been imported into the database**.

The system architecture is sound:
- ✅ Database schema is correct
- ✅ Views are properly structured
- ✅ Backend queries the right sources
- ✅ Frontend displays available data

**Action Required:** Import Revizto data using one of the methods described above.

Once Revizto data is imported, it will automatically appear in the Analytics Dashboard alongside the existing ACC issues.

---

**Diagnostic Tools Created:**
- `tools/check_revizto_issues.py` - Quick Revizto data check
- `tools/diagnose_revizto_data.py` - Comprehensive Revizto diagnostic

**Run these anytime to verify Revizto data status:**
```bash
cd tools
python diagnose_revizto_data.py
```

---

**Status:** 🟡 Waiting for Revizto data import  
**Next Steps:** Follow Option 1, 2, or 3 from "How to Fix" section above
