# ACC Issue Reconciliation - Warehouse Backfill Guide

**Date**: January 2025  
**Status**: Phase 4 (App Delivery) - Warehouse Follow-up  
**Audience**: Data Engineering, Analytics, Application Teams

---

## Executive Summary

The vw_Issues_Reconciled view (deployed in Phase 4) serves as the **unified source of truth** for all ACC and Revizto issues with reconciled display_ids for application consumption. However, the **warehouse dim.issue** currently contains only **37 distinct ACC issues** out of **3,696 mapped ACC identifiers**, creating a data consistency gap.

This document explains:
1. **Why the gap exists** (ETL design, not a bug)
2. **Current state** (vw_Issues_Reconciled is production-ready for app)
3. **Backfill strategy** (how to populate warehouse dim.issue completely)
4. **Timeline** (non-blocking follow-up, can execute after app delivery)

---

## Current State

### Application Layer (Phase 4 - Production Ready ✅)
- **View**: `dbo.vw_Issues_Reconciled` (ProjectManagement DB, normalized layer)
- **Row Count**: 12,840 total issues
  - 4,748 ACC issues (3,696 mapped + 1,052 unmapped)
  - 8,092 Revizto issues
- **Display IDs**: ✅ Fully reconciled
  - ACC mapped: "ACC-" + numeric ID (e.g., "ACC-924")
  - ACC unmapped: "ACC-" + UUID prefix (e.g., "ACC-66C8A7AA")
  - Revizto: "REV-" + ID (e.g., "REV-12345")
- **API Endpoint**: `GET /api/issues/table` (new in Phase 4)
- **Performance**: <1 second per page request

### Warehouse Layer (Current State ⚠️)
- **Table**: `warehouse.dim.issue`
- **Current Rows**: 37 distinct ACC issues (only 37 / 3,696 = 1.0%)
- **Missing**: 3,659 ACC issues (98% gap)
- **Root Cause**: Warehouse ETL was scoped to load subset of issues
- **Impact on App**: **NONE** - Application queries ProjectManagement DB directly

---

## Why The Gap Exists

### Warehouse ETL Design

The warehouse `dim.issue` table is populated by an ETL pipeline that runs during data imports:

```
Issues_Current (normalized, 12,840 rows)
    ↓
[ETL Filter] - Filters by import_run_id + active project list
    ↓
warehouse.dim.issue (37 rows for ACC)
```

**Key Points:**
1. **ETL Scope**: Warehouse is designed to load only "active" or "recent" issues
2. **Filter Criteria**: Issues filtered by:
   - `import_run_id` (latest successful run only)
   - Active project list (subset of all projects)
   - Possibly other business rules (e.g., non-deleted, within date range)
3. **By Design**: Warehouse is a **curated subset**, not a full replica of source
4. **Not a Bug**: This is intentional architecture (data warehouse vs. operational DB)

### Evidence

From last investigation (Phase 3):
- `warehouse.dim.issue` has 37 ACC rows (only those in latest successful import_run)
- `dbo.Issues_Current` has 4,748 ACC rows (all accumulated)
- `dbo.vw_acc_issue_id_map` has 3,696 ACC mapped rows (reference data)

**Conclusion**: Warehouse ETL filters successfully; it just doesn't load all historical/inactive issues.

---

## Current Solution (Phase 4 - Production Ready)

### For Application Delivery
**Use**: `dbo.vw_Issues_Reconciled` (ProjectManagement DB)
- Contains **all** issues with reconciled display_ids
- Lightweight LEFT JOIN (no expensive aggregations)
- Direct ProjectManagement DB query (faster than warehouse)
- No additional ETL required

**API Endpoint**: `GET /api/issues/table`
```python
# Backend: database.get_reconciled_issues_table()
# Queries: dbo.vw_Issues_Reconciled directly
```

**Why This Works:**
- Application doesn't need warehouse for this feature
- Normalized layer (ProjectManagement DB) is source of truth
- Dashboard queries can continue using warehouse (separate concern)

---

## Backfill Strategy (Non-Blocking Follow-Up)

### Option A: Selective Backfill (Recommended)

**Goal**: Populate warehouse dim.issue with ACC issues, keeping warehouse architecture intact

**Steps**:
1. **Identify ETL Filter Criteria**
   - Review warehouse ETL code to understand current filter logic
   - Document: "Which projects/dates/statuses are included?"
   - Example: Latest import_run_id + projects with recent activity

2. **Create Backfill Script** (`tools/backfill_warehouse_issue_dimension.py`)
   ```python
   # Pseudocode
   def backfill_dim_issue_from_vw_acc_issue_id_map():
       # Get 3,696 ACC issues from vw_acc_issue_id_map (reference data)
       # Filter using same criteria as ETL (if any additional filtering desired)
       # INSERT or UPDATE into warehouse.dim.issue
       # Log row counts before/after
   ```

3. **Execute Backfill**
   - Run script once to populate ~3,696 ACC issue rows
   - Verify row counts match expectations
   - Update dashboard/analytics queries if they depend on dim.issue

4. **Maintain Backfill**
   - Add backfill step to regular ETL (if issues keep changing)
   - Or run quarterly to sync any new ACC issues

### Option B: Full Historical Load (Alternative)

**If**: Warehouse should be a complete replica of all issues

**Action**:
- Modify ETL to remove filters (load all Issues_Current rows)
- Trade-off: Larger warehouse storage, broader scope

**Not Recommended** for initial backfill (better to keep selective approach).

---

## Implementation Timeline

### Phase 4 ✅ (Current - Complete)
- ✅ vw_Issues_Reconciled deployed (normalized layer)
- ✅ GET /api/issues/table endpoint active (application ready)
- ✅ Display_id logic verified (15 tests passing)
- ✅ Row counts validated (12,840 total, 4,748 ACC, 8,092 Revizto)

### Phase 5 (Future - Non-Blocking)
- ⏳ Review warehouse ETL code
- ⏳ Create backfill script
- ⏳ Execute backfill (30 min to 2 hours depending on approach)
- ⏳ Validate warehouse dim.issue row counts
- ⏳ Update any warehouse-dependent dashboards

**Timeline**: Can be done in parallel with other work, or after app is live

---

## How to Execute Backfill

### Find ETL Code
```bash
# Search for warehouse ETL scripts
find . -name "*etl*.py" -o -name "*warehouse*" -type f | grep -E "\.(py|sql)$"
# Look for imports of dim.issue
grep -r "dim\.issue" --include="*.py" --include="*.sql"
```

### Create Backfill Script

File: `tools/backfill_warehouse_issue_dimension.py`

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
from config import Config
from datetime import datetime

def backfill_warehouse_dim_issue():
    """
    Backfill warehouse.dim.issue with ACC issues from vw_acc_issue_id_map.
    
    This script populates missing ACC issue records in the warehouse while
    maintaining the existing selective ETL design (by import_run_id).
    """
    
    try:
        # Get latest successful import_run_id for ACC
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 import_run_id 
                FROM fact.issue_import_runs
                WHERE source_system = 'ACC'
                  AND status = 'Success'
                ORDER BY created_at DESC
            """)
            result = cursor.fetchone()
            latest_import_run_id = result[0] if result else None
        
        if not latest_import_run_id:
            print("No successful ACC import run found. Skipping backfill.")
            return
        
        print(f"Using import_run_id: {latest_import_run_id}")
        
        # Backfill ACC issues from vw_acc_issue_id_map
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            pm_cursor = conn.cursor()
            
            # Get all ACC issues from vw_acc_issue_id_map
            pm_cursor.execute("""
                SELECT
                    issue_key,
                    acc_issue_number,
                    acc_issue_uuid,
                    source_project_id,
                    acc_title,
                    acc_status,
                    acc_created_at,
                    acc_updated_at
                FROM dbo.vw_acc_issue_id_map
            """)
            
            acc_issues = pm_cursor.fetchall()
            print(f"Found {len(acc_issues)} ACC issues to backfill")
        
        # Insert into warehouse
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            
            inserted = 0
            updated = 0
            
            for issue in acc_issues:
                issue_key, acc_num, acc_uuid, proj_id, title, status, created, updated_at = issue
                
                # Try to insert, or update if exists
                cursor.execute("""
                    MERGE INTO warehouse.dim.issue di
                    USING (SELECT ? as source_system, ? as source_issue_id, ? as source_project_id) src
                    ON di.source_system = src.source_system
                       AND di.source_issue_id = src.source_issue_id
                       AND di.source_project_id = src.source_project_id
                    WHEN MATCHED THEN
                        UPDATE SET
                            issue_bk = ?,
                            title = ?,
                            import_run_id = ?,
                            updated_at = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (source_system, source_issue_id, source_project_id, issue_bk, title, import_run_id, created_at, updated_at, current_flag)
                        VALUES ('ACC', ?, ?, ?, ?, ?, GETDATE(), GETDATE(), 1);
                """, (
                    'ACC', str(acc_uuid), proj_id,  # Merge keys
                    acc_num, title, latest_import_run_id,  # Update values
                    str(acc_uuid), proj_id, acc_num, title, latest_import_run_id  # Insert values
                ))
            
            conn.commit()
            
        print(f"Backfill complete: {len(acc_issues)} ACC issues processed")
        
    except Exception as e:
        print(f"Backfill failed: {e}")
        raise

if __name__ == '__main__':
    backfill_warehouse_dim_issue()
```

### Run Backfill
```bash
cd c:\path\to\BIMProjMngmt
python tools/backfill_warehouse_issue_dimension.py
```

### Verify
```sql
-- Check row counts after backfill
SELECT COUNT(*) as total, COUNT(CASE WHEN source_system='ACC' THEN 1 END) as acc_count
FROM warehouse.dim.issue;

-- Expected: 3,696+ ACC rows (plus any Revizto rows previously loaded)
```

---

## FAQs

**Q: Will the backfill block the app launch?**  
A: No. vw_Issues_Reconciled is already in ProjectManagement DB and serving the API.

**Q: Do I need to change the app code?**  
A: No. Application queries vw_Issues_Reconciled directly. Warehouse is separate.

**Q: Should I run this immediately?**  
A: Optional. Priority is app delivery (Phase 4 complete). Backfill is Phase 5 (future work).

**Q: What if the warehouse ETL runs after backfill?**  
A: ETL will overwrite with its filtered set. Either make backfill part of regular ETL, or run after ETL concludes.

**Q: What about Revizto issues in warehouse?**  
A: Already being loaded by warehouse ETL. Only ACC issues have the gap (3,659 missing rows).

---

## Related Documents

- **Phase 1**: [ACC_ISSUE_RECONCILIATION_AUDIT_REPORT.md](../docs/ACC_ISSUE_RECONCILIATION_AUDIT_REPORT.md) - Initial audit & discovery
- **Phase 2**: [ACC_ISSUE_RECONCILIATION_REVIEW_CORRECTIONS.md](../docs/ACC_ISSUE_RECONCILIATION_REVIEW_CORRECTIONS.md) - Corrections & validation
- **Phase 3**: [ACC_ISSUE_RECONCILIATION_DEPLOYMENT_SUMMARY.md](../docs/ACC_ISSUE_RECONCILIATION_DEPLOYMENT_SUMMARY.md) - SQL views deployed
- **Phase 4**: [EXECUTION_MISSION_COMPLETE.md](../docs/EXECUTION_MISSION_COMPLETE.md) - App delivery (vw_Issues_Reconciled + API + tests)

---

## Appendix: View References

### dbo.vw_Issues_Reconciled
- **Location**: ProjectManagement DB (normalized layer)
- **Query**: ProjectManagement.dbo.vw_Issues_Reconciled
- **Used By**: GET /api/issues/table endpoint
- **Rows**: 12,840 (all ACC + Revizto)
- **Display_id**: ✅ Fully reconciled for all rows

### warehouse.dim.issue
- **Location**: Warehouse DB (analytical layer)
- **Query**: warehouse.dim.issue
- **Current Rows**: 37 ACC (1.0% of available)
- **Status**: Incomplete (backfill candidate in Phase 5)

### dbo.vw_acc_issue_id_map
- **Location**: ProjectManagement DB (mapping reference)
- **Rows**: 3,696 (UUID-to-number mappings)
- **Used For**: Creating display_ids in vw_Issues_Reconciled

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Owner**: Data/Analytics Team  
**Status**: Non-Blocking, Future Work
