# Analytics Dashboard Data Source Review

**Date:** October 15, 2025  
**Reviewer:** GitHub Copilot  
**Status:** ✅ CONFIRMED

---

## Executive Summary

**CONFIRMED:** The Analytics Dashboard in the React frontend is correctly pulling data from the `vw_ProjectManagement_AllIssues` view in the ProjectManagement database.

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   React Frontend (Analytics Dashboard)          │
│                   File: frontend/src/pages/AnalyticsPage.tsx    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 1. Calls issuesApi.getOverview()
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend API Client                           │
│                   File: frontend/src/api/issues.ts              │
│                   Endpoint: GET /api/issues/overview            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 2. HTTP Request
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Backend Flask API                             │
│                   File: backend/app.py                          │
│                   Route: @app.route('/api/issues/overview')     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 3. Calls get_all_projects_issues_overview()
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Database Layer                                │
│                   File: database.py                             │
│                   Function: get_all_projects_issues_overview()  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 4. SQL Query
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SQL Server Database                           │
│                   Database: ProjectManagement                   │
│                   View: vw_ProjectManagement_AllIssues          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code References

### 1. Frontend Component (React)

**File:** `frontend/src/pages/AnalyticsPage.tsx`

```typescript
// Line 30-50
export function AnalyticsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  // Fetch all projects
  const {
    data: projects,
    isLoading: projectsLoading,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch overall issues overview
  const {
    data: issuesOverview,
    isLoading: issuesLoading,
    error: issuesError,
  } = useQuery({
    queryKey: ['issues', 'overview'],
    queryFn: () => issuesApi.getOverview(),  // <-- THIS CALLS THE API
  });
```

### 2. Frontend API Client

**File:** `frontend/src/api/issues.ts`

```typescript
export const issuesApi = {
  // Get overall issues overview for all projects
  getOverview: async () => {
    const response = await fetch('/api/issues/overview');
    if (!response.ok) {
      throw new Error('Failed to fetch issues overview');
    }
    return response.json();
  },
  // ...
};
```

### 3. Backend API Endpoint

**File:** `backend/app.py` (Line 1251-1258)

```python
@app.route('/api/issues/overview', methods=['GET'])
def get_all_issues_overview():
    """Get combined issues overview for all projects"""
    try:
        overview_data = get_all_projects_issues_overview()
        return jsonify(overview_data)
    except Exception as e:
        logging.exception("Error getting all issues overview")
        return jsonify({'error': str(e)}), 500
```

### 4. Database Query Function

**File:** `database.py` (Line 2584-2694)

```python
def get_all_projects_issues_overview():
    """Get combined ACC and Revizto issues overview for all projects."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get issue summary statistics for all projects
            cursor.execute(f"""
                SELECT 
                    source,
                    status,
                    COUNT(*) as count
                FROM vw_ProjectManagement_AllIssues  # <-- THE VIEW!
                GROUP BY source, status
            """)
            
            # ... (more queries using the same view)
            
            # Get recent issues (last 20 across all projects)
            cursor.execute(f"""
                SELECT TOP 20
                    project_name,
                    source,
                    issue_id,
                    title,
                    status,
                    created_at,
                    assignee,
                    priority
                FROM vw_ProjectManagement_AllIssues  # <-- THE VIEW!
                ORDER BY created_at DESC
            """)
```

---

## Database View Schema

### View Name: `vw_ProjectManagement_AllIssues`

**Location:** ProjectManagement Database

**Columns (13 total):**

| Column Name         | Data Type | Description                                    |
|---------------------|-----------|------------------------------------------------|
| source              | VARCHAR   | Issue source: 'ACC' or 'Revizto'              |
| issue_id            | VARCHAR   | Unique issue identifier from source system     |
| title               | VARCHAR   | Issue title/summary                            |
| status              | VARCHAR   | Issue status (e.g., 'open', 'closed')         |
| created_at          | DATETIME  | Issue creation timestamp                       |
| closed_at           | DATETIME  | Issue closure timestamp (NULL if still open)   |
| assignee            | VARCHAR   | Assigned user/team                             |
| author              | VARCHAR   | Issue creator                                  |
| project_name        | VARCHAR   | Associated project name                        |
| project_id          | VARCHAR   | Associated project ID (can be INT or GUID)     |
| priority            | VARCHAR   | Issue priority level                           |
| web_link            | VARCHAR   | URL to view issue in source system             |
| preview_middle_url  | VARCHAR   | Preview image URL (if applicable)              |

### What This View Contains

This view is a **unified aggregation** of issues from multiple sources:

1. **ACC (Autodesk Construction Cloud) Issues**
   - Imported from: `acc_data_schema.dbo.vw_issues_expanded_pm`
   - Source: ZIP file imports from ACC Desktop Connector
   - Typical project_id format: GUID (e.g., 'E4A8AE56-0988-4D3A-8A53-0D6C2026BCC0')

2. **Revizto Issues**
   - Imported from: Revizto extraction runs
   - Source: Revizto model coordination platform
   - Typical project_id format: Integer

**Total Issues:** ~5,882 (as of last documentation update)

---

## Analytics Dashboard Features Using This Data

The Analytics Dashboard displays the following information from `vw_ProjectManagement_AllIssues`:

### 1. Overall Issues Summary
- **Total Issues:** Count of all issues across all projects
- **ACC Issues:** Total/Open/Closed counts from ACC
- **Revizto Issues:** Total/Open/Closed counts from Revizto
- **Overall Status:** Combined open/closed counts

### 2. Issues by Project
- **Project-level breakdown:** Issues grouped by `project_name`
- **Per-project statistics:** Total, ACC, Revizto, Open, Closed

### 3. Recent Issues
- **Last 20 issues:** Most recently created issues across all projects
- **Displayed fields:** Project name, source, issue ID, title, status, created date, assignee, priority

### 4. Project-Specific Views
When a user selects a project, the dashboard also shows:
- Issues filtered by `project_id`
- ACC Issues Panel with detailed issue data

---

## Data Quality & Integrity Notes

### ✅ Strengths

1. **Single Source of Truth:** All analytics queries use the same view
2. **Multi-source Support:** Handles both ACC and Revizto issues seamlessly
3. **Flexible project_id:** Supports both integer and GUID project identifiers
4. **Proper Joins:** Backend uses `TRY_CAST()` to safely join with projects table
5. **Error Handling:** Fallback queries and graceful degradation

### ⚠️ Known Limitations

1. **Missing Project Metadata in View:**
   - The view does NOT include: `client_id`, `client_name`, `project_type`
   - Backend must JOIN with `projects`, `clients`, `project_types` tables separately
   - Documented in: `docs/ERROR_FIXES_2025-10-10.md`

2. **project_id Type Mismatch:**
   - View contains VARCHAR (can be GUID or INT)
   - Projects table uses INT only
   - Solution: Backend uses `TRY_CAST(pi.project_id AS INT)` for safe conversions

3. **No Direct Issue Description:**
   - The view doesn't include full issue descriptions
   - Only title is available for analytics dashboard
   - Full descriptions are in source tables (ACC, Revizto)

---

## Related Files & Documentation

### Database Files
- `database.py` - Main database access layer
- `database_pool.py` - Connection pooling
- `sql/fix_processedissues_schema.sql` - Schema compatibility fixes

### Frontend Files
- `frontend/src/pages/AnalyticsPage.tsx` - Main dashboard component
- `frontend/src/api/issues.ts` - API client for issues
- `frontend/src/components/dataImports/ACCIssuesPanel.tsx` - ACC issues detail panel

### Backend Files
- `backend/app.py` - Flask API routes
- `services/issue_analytics_service.py` - Advanced analytics processing

### Documentation
- `docs/ISSUE_ANALYTICS_SUMMARY.md` - Comprehensive analytics documentation
- `docs/ERROR_FIXES_2025-10-10.md` - Schema compatibility fixes
- `docs/ISSUE_ANALYTICS_ROADMAP.md` - Future enhancements
- `docs/DATA_FLOW_ANALYSIS.md` - System-wide data flow

---

## Verification Steps

### Manual Verification

1. **Frontend Check:**
   ```bash
   # Inspect Network tab in browser DevTools
   # Look for: GET /api/issues/overview
   # Response should contain: summary, projects, recent_issues
   ```

2. **Backend Check:**
   ```bash
   # Run the Flask app
   python backend/app.py
   
   # Test endpoint directly
   curl http://localhost:5001/api/issues/overview
   ```

3. **Database Check:**
   ```sql
   -- Run in SQL Server Management Studio
   USE ProjectManagement;
   
   SELECT 
       source,
       status,
       COUNT(*) as count
   FROM vw_ProjectManagement_AllIssues
   GROUP BY source, status;
   ```

### Automated Tests

- `tests/test_issues_data.py` - Tests view accessibility and data structure
- `tools/check_view_columns.py` - Validates view schema (see output above)

---

## Conclusion

✅ **CONFIRMED:** The Analytics Dashboard is correctly sourcing data from the `vw_ProjectManagement_AllIssues` view.

The data flow is clean, well-documented, and follows best practices:
- **Separation of Concerns:** UI → API → Backend → Database
- **Error Handling:** Graceful degradation at each layer
- **Data Integrity:** Proper type conversions and NULL handling
- **Documentation:** Comprehensive docs and inline comments

No changes or fixes are required at this time.

---

**Last Reviewed:** October 15, 2025  
**Next Review:** Upon schema changes or new data source integrations
