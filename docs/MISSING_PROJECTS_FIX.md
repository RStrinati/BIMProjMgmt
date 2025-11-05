# Missing Projects in Marts - Root Cause & Fix

## Problem Summary
Only 3 of 17 projects appear in `mart.v_project_overview`, despite all 17 being in `dim.project`.

## Root Causes (2 Issues)

### Issue 1: Fact Loader Requires Issues
**Problem**: `warehouse.usp_load_fact_project_kpi_monthly` started from `fact.issue_snapshot`:
```sql
FROM fact.issue_snapshot snapshot
JOIN dim.project proj ON snapshot.project_sk = proj.project_sk
```

**Impact**: 
- Only projects with issue snapshots got a KPI fact row
- 14 projects have 0 issues → excluded from facts → excluded from marts
- Many of those 14 projects DO have services and reviews (MEL071, MEL081, NFPS, etc. have 5-16 reviews each)

### Issue 2: ACC Issues Not Mapping to PM Projects
**Problem**: `stg.issues (distinct project_id_raw): 0`
- ALL 4,761 ACC issues are failing to map to valid PM project IDs
- They end up with `project_sk = -1` (Unknown)

**Impact**:
- Even projects that SHOULD have issues (from ACC) show 0 issue counts
- The 3 projects that DO appear (MEL01A, MEL01CD, Unknown) are likely hardcoded test data or have a different source

## Fixes Applied

### Fix 1: Enhanced Fact Loader ✓
**File**: `warehouse/sql/create_load_procs.sql` → `warehouse.usp_load_fact_project_kpi_monthly`

**Changes**:
- Start from `dim.project` with LEFT JOINs to facts (not INNER JOIN from facts)
- Populate a row for EVERY current project, even if metrics are 0/NULL
- Now includes review counts (was NULL before)
- Uses `COUNT(DISTINCT snapshot.issue_sk)` to avoid counting NULL as 1

**Result**: All 17 projects will get a `fact.project_kpi_monthly` row

### Fix 2: Enhanced Mart View ✓
**File**: `warehouse/sql/marts/create_mart_views.sql` → `mart.v_project_overview`

**Changes**:
- Changed from `FROM fact.project_kpi_monthly k JOIN dim.project p` 
- To `FROM dim.project p LEFT JOIN fact.project_kpi_monthly k`
- Wrapped metrics in `ISNULL(..., 0)` for clean 0 defaults

**Result**: All projects in `dim.project` appear in the mart, regardless of fact availability

### Fix 3: ACC Project Mapping (Manual Step Required)
**Diagnostic tool**: `tools/diagnose_acc_project_mapping.sql`

**Problem**: ACC issues use project names or IDs that don't match PM project identifiers.

**Solution Steps**:
1. Run `tools/diagnose_acc_project_mapping.sql` to see:
   - Which ACC project names need aliases
   - Suggested INSERT statements for `dbo.project_aliases`
   
2. Review the suggested aliases and add them:
   ```sql
   INSERT INTO dbo.project_aliases (pm_project_id, alias_name) 
   VALUES (1, 'ACC Project Name 1');
   
   INSERT INTO dbo.project_aliases (pm_project_id, alias_name) 
   VALUES (2, 'ACC Project Name 2');
   ```

3. Re-seed ACC issues:
   ```sql
   TRUNCATE TABLE stg.issues;
   -- Run: warehouse/sql/staging/seed_from_acc.sql
   ```

4. Re-run dimension loaders (issues will now map correctly):
   ```sql
   EXEC warehouse.usp_load_dim_issue;
   ```

## Execution Steps

### Immediate Fix (Get All Projects in Marts)
```sql
-- 1. Recreate the enhanced fact loader
warehouse/sql/create_load_procs.sql

-- 2. Recreate the enhanced mart view
warehouse/sql/marts/create_mart_views.sql

-- 3. Truncate and reload facts to pick up all projects
TRUNCATE TABLE fact.project_kpi_monthly;
EXEC warehouse.usp_load_fact_project_kpi_monthly;

-- 4. Verify all 17 projects now appear
SELECT project_name, total_issues, review_count, services_in_progress
FROM mart.v_project_overview
ORDER BY project_name;
```

### Complete Fix (Get Actual Issue Counts)
```sql
-- 1. Diagnose ACC mapping issues
tools/diagnose_acc_project_mapping.sql

-- 2. Add missing aliases based on diagnostic output
-- (Manual INSERTs into dbo.project_aliases)

-- 3. Re-seed ACC issues
TRUNCATE TABLE stg.issues;
-- Run: warehouse/sql/staging/seed_from_acc.sql

-- 4. Reload dimensions and facts
EXEC warehouse.usp_load_dim_issue;
EXEC warehouse.usp_load_fact_issue_snapshot;
TRUNCATE TABLE fact.project_kpi_monthly;
EXEC warehouse.usp_load_fact_project_kpi_monthly;

-- 5. Verify issue counts are now correct
SELECT project_name, total_issues, open_issues, closed_issues
FROM mart.v_project_overview
WHERE total_issues > 0
ORDER BY total_issues DESC;
```

## Expected Results

### Before Fix
- dim.project: 17 projects
- mart.v_project_overview: 3 projects
- fact.project_kpi_monthly: 3 projects
- Most projects with services/reviews not visible

### After Immediate Fix
- dim.project: 17 projects
- mart.v_project_overview: 17 projects ✓
- fact.project_kpi_monthly: 17 projects ✓
- All projects visible with 0 issues (until ACC mapping fixed)

### After Complete Fix
- All 17 projects visible
- 4,761 ACC issues correctly distributed to their PM projects
- Issue counts accurate in marts
- Reviews linked to projects via services

## Notes
- The "Unknown" project (sk=-1, bk=-1) with 4,761 issues is where all unmapped ACC issues landed
- Once aliases are added and issues re-seeded, those will redistribute to the correct projects
- Projects with 0 issues will remain at 0 if they genuinely have no ACC issues
