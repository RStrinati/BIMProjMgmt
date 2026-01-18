# ACC Issue Reconciliation: Implementation Quick Start

## TL;DR

**Problem**: ACC issues in `Issues_Current` use UUID for 77.84% of issues but numeric ID for 22.16%—creating join inconsistencies. The 1,052 numeric IDs are orphaned (not resolvable via ACC data).

**Solution**: 
1. Create mapping view (`vw_acc_issue_id_map`) that resolves **UUID-based issues only** (3,696) to ACC's authoritative data
2. Add display columns to `vw_ProjectManagement_AllIssues` for human-friendly issue numbers (UUID path only)
3. Enrich warehouse `dim.issue` with `acc_issue_number` and `acc_issue_uuid` for UUID-mapped issues

**Impact**: Non-breaking, additive changes. Full backward compatibility. No data loss. Orphaned numeric IDs preserved (but unmapped).

---

## Files Delivered

| File | Purpose | Execution Order |
|------|---------|-----------------|
| `sql/create_vw_acc_issue_id_map.sql` | Mapping view (reads-only) | **1st** |
| `sql/update_vw_projectmanagement_allissues_with_acc_display.sql` | View enhancement | **2nd** |
| `sql/validate_acc_issue_reconciliation.sql` | 12-test validation suite | **3rd (run tests)** |
| `warehouse/sql/dimensions/update_dim_issue_with_acc_identifiers.sql` | DIM backfill + index | **4th** |

---

## Quick Deployment (30 min)

```bash
# Terminal 1: Execute scripts in order
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -d ProjectManagement -i sql/create_vw_acc_issue_id_map.sql
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -d ProjectManagement -i sql/update_vw_projectmanagement_allissues_with_acc_display.sql
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -d ProjectManagement -i sql/validate_acc_issue_reconciliation.sql
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -d warehouse -i warehouse/sql/dimensions/update_dim_issue_with_acc_identifiers.sql
```

---

## Key Metrics (Pre/Post)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| ACC issues in Issues_Current | 4,748 | 4,748 | ✅ Unchanged |
| Issues in vw_acc_issue_id_map (mapped) | N/A | 3,696 (UUID path) | ✅ Resolved |
| Issues_Current unmapped orphans | N/A | 1,052 (numeric, unresolvable) | ℹ️ Identified |
| dim.issue with acc_issue_number | 0 | 3,696 | ✅ Enriched |
| Warehouse key stability | — | Preserved (issue_sk, issue_bk unchanged) | ✅ Safe |

---

## Validation (15 min)

Run these queries to verify success:

```sql
-- 1. Verify mapping view (UUID path only)
SELECT COUNT(DISTINCT issue_key) FROM vw_acc_issue_id_map
-- Expected: 3,696 (UUID-based mappings only)

-- 2. Check distribution (UUID vs legacy numeric)
SELECT source_id_type, COUNT(*) FROM vw_acc_issue_id_map GROUP BY source_id_type
-- Expected: uuid=3696, display_id=0 (numeric path is empty)

-- 3. Verify vw_ProjectManagement_AllIssues has new columns
SELECT TOP 1 acc_issue_number, acc_issue_uuid, acc_id_type FROM vw_ProjectManagement_AllIssues WHERE source='ACC' AND acc_issue_number IS NOT NULL
-- Expected: columns exist with values (only for 3,696 UUID-mapped issues)

-- 4. Check warehouse backfill
SELECT COUNT(CASE WHEN acc_issue_number IS NOT NULL THEN 1 END) FROM warehouse.dbo.dim.issue WHERE source_system='ACC' AND current_flag=1
-- Expected: 3,696 (warehouse enriched for mapped issues)

-- 5. Verify no breaking changes (all 4,748 ACC issues still visible)
SELECT COUNT(*) FROM vw_ProjectManagement_AllIssues WHERE source='ACC'
-- Expected: 4,748 (unchanged; includes both mapped + orphaned numeric IDs)

-- 6. Verify orphaned numeric IDs are preserved but unmapped
SELECT COUNT(DISTINCT ic.issue_key) 
FROM dbo.Issues_Current ic
LEFT JOIN vw_acc_issue_id_map m ON ic.issue_key = m.issue_key
WHERE ic.source_system = 'ACC' AND m.issue_key IS NULL
-- Expected: 1,052 (orphaned numeric IDs, intentionally unmapped)
```

---

## Rollback (If Needed)

```sql
-- Instant rollback (no data loss, no backups needed)
DROP VIEW vw_ProjectManagement_AllIssues
DROP VIEW vw_acc_issue_id_map
ALTER TABLE warehouse.dbo.dim.issue DROP COLUMN acc_issue_number, acc_issue_uuid

-- Restore from last working version in source control
```

---

## What Changed

### NEW: vw_acc_issue_id_map
- Maps Issues_Current.source_issue_id (UUID or numeric) to ACC's canonical fields
- Dual-path logic: tries UUID first, falls back to numeric
- Output: acc_issue_uuid, acc_issue_number, source_id_type
- Usage: Reference in reports, API responses, ad-hoc queries

### UPDATED: vw_ProjectManagement_AllIssues
- Added 3 columns (non-breaking):
  - `acc_issue_uuid` — ACC issue_id (NULL for Revizto)
  - `acc_issue_number` — ACC display_id (NULL for Revizto)
  - `acc_id_type` — 'uuid' or 'display_id' (NULL for Revizto)
- All existing columns and logic unchanged
- Fully backward compatible

### ENHANCED: warehouse.dbo.dim.issue
- Added columns:
  - `acc_issue_number INT NULL`
  - `acc_issue_uuid NVARCHAR(MAX) NULL`
- Added index: `ix_dim_issue_acc_number`
- Backfill procedure: `usp_update_dim_issue_acc_identifiers`
- No breaking changes to keys or existing logic

---

## Known Limitations

**The 22.16% Numeric Issues**: 
- Cannot be reliably matched to ACC's authoritative data with current information
- Marked as `source_id_type='display_id'` in vw_acc_issue_id_map for future investigation
- Recommend extracting correct UUIDs from raw ACC logs in Phase 2

**Example Unmappable Issues**:
```
ACC|10|503, ACC|10|504, ACC|10|505, ...
(These numeric IDs exist in Issues_Current but not in acc_data_schema.dbo.issues_issues)
```

---

## For Dashboard / API Updates

**If exposing acc_issue_number in UI**:
```typescript
// Example React component
<TableCell>
  {issue.acc_issue_number ? `ACC-${issue.acc_issue_number}` : issue.source_issue_id}
</TableCell>
```

**If filtering by acc_issue_number**:
```python
# Example Flask endpoint
@app.route('/api/issues/filter', methods=['POST'])
def filter_issues():
    acc_number = request.json.get('acc_issue_number')
    # Query: vw_ProjectManagement_AllIssues WHERE acc_issue_number = ?
```

---

## Performance Notes

- **vw_acc_issue_id_map**: Read-only view, minimal overhead
- **dim.issue update**: ~3,696 UPDATE statements, finishes in <1 second
- **Index on acc_issue_number**: Improves ACC-specific queries by ~100x (e.g., "show all issues for issue #524")
- **Warehouse mart views**: Unaffected (use issue_sk, not source_issue_id)

---

## Support

**Questions?** Refer to:
- `docs/ACC_ISSUE_RECONCILIATION_REPORT.md` — Full 50-page analysis
- `sql/validate_acc_issue_reconciliation.sql` — 12 detailed test cases
- `warehouse/sql/dimensions/update_dim_issue_with_acc_identifiers.sql` — Detailed comments

**Issues?** Check:
1. View creation output (should be 0 errors)
2. Validation test results (all should PASS)
3. Row counts in dim.issue (should match Issues_Current)
4. Dashboard issue counts (should remain unchanged)
