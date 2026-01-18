# ACC Issue Number Reconciliation Report
## Unifying ACC UUID vs Numeric Issue Identifiers

**Date**: January 15, 2026  
**Status**: Complete Analysis + Implementation Strategy  
**Scope**: ProjectManagement DB + Warehouse Impact  

---

## A) FACT-FINDING REPORT

### Executive Summary

**The Problem**: `dbo.Issues_Current` stores ACC issue identifiers inconsistently:
- **77.84%** (3,696 issues) have UUID-style `source_issue_id` (e.g., `66C8A7AA-48B7-4BE6-BDF6-9AE99F169326`)
- **22.16%** (1,052 issues) have numeric-style `source_issue_id` (e.g., `524`, `523`, `535`)

ACC's authoritative table (`acc_data_schema.dbo.issues_issues`) has **both**:
- `issue_id` = UUID (the true primary key)
- `display_id` = numeric (human-facing issue number shown in ACC UI)

**Current Mismatch**: The numeric `source_issue_id` values in Issues_Current are essentially **orphaned**—they don't match anything in the ACC source table and can't be reliably joined.

---

### Schema Inspection

#### ProjectManagement.dbo.Issues_Current
**Relevant columns**:
```
- issue_key              NVARCHAR(255)    → Composite key: source_system|source_project_id|source_issue_id
- source_system          NVARCHAR(32)     → 'ACC' or 'Revizto'
- source_issue_id        NVARCHAR(255)    → VARIES (UUID or numeric)
- source_project_id      NVARCHAR(100)    → Project identifier from source
- project_id             INT              → PM project_id (if mapped)
- title                  NVARCHAR(MAX)
- status_raw             NVARCHAR(255)
- status_normalized      NVARCHAR(50)
- created_at             DATETIME2
- updated_at             DATETIME2
- import_run_id          INT              → Link to IssueImportRuns (metadata on import)
```

#### acc_data_schema.dbo.issues_issues
**Relevant columns**:
```
- issue_id               UNIQUEIDENTIFIER → The authoritative ACC UUID
- display_id             INT              → Human-facing issue number (shown in UI)
- bim360_project_id      UNIQUEIDENTIFIER → The ACC project UUID
- title                  NVARCHAR(500)
- status                 NVARCHAR(50)
- created_at             DATETIME2
- updated_at             DATETIME2
```

**Key insight**: `issue_id` is stored as `UNIQUEIDENTIFIER`, which is why Issues_Current's UUID values match when cast to NVARCHAR.

---

### Match Rate Analysis

| Scenario | Count | Percentage | Status |
|----------|-------|------------|--------|
| **UUID-style source_issue_id** | 3,696 | 77.84% | ✅ **Matches ACC.issue_id** |
| **Numeric-style source_issue_id** | 1,052 | 22.16% | ⚠️ **Unmatchable** (no joins found) |
| **Total ACC issues** | 4,748 | 100% | |

**UUID Match Test**:
```sql
SELECT COUNT(*) FROM Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
  ON ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
WHERE ic.source_system = 'ACC'
-- Result: 3,696 matches (77.84%) ✅
```

**Numeric Match Test**:
```sql
SELECT COUNT(*) FROM Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
  ON TRY_CAST(ic.source_issue_id AS INT) = acc.display_id
  AND ic.source_project_id = CAST(acc.bim360_project_id AS NVARCHAR(100))
WHERE ic.source_system = 'ACC'
  AND ic.source_issue_id NOT LIKE '%-%'
-- Result: 0 matches ❌ (no valid joins)
```

**Interpretation**: The 22.16% numeric issues have been stored incorrectly or imported from a different source format. They should ideally be re-mapped to their UUIDs.

---

### CRITICAL FINDING: Numeric IDs Are Not ACC Display IDs

**What we tested**: We attempted to join the 1,052 numeric `source_issue_id` values (e.g., '159', '162', '163') to `acc_data_schema.dbo.issues_issues.display_id` using:

```sql
TRY_CAST(ic.source_issue_id AS INT) = acc.display_id 
  AND ic.source_project_id = CAST(acc.bim360_project_id AS NVARCHAR(100))
```

**Result**: **0 matches** across all 1,052 numeric records.

**Conclusion**: The numeric `source_issue_id` values stored in Issues_Current are **NOT ACC display IDs**. They are orphaned identifiers from an unknown source or corrupted during import. 

**Implication for Implementation**:
- vw_acc_issue_id_map will return **only 3,696 rows** (UUID path only)
- The 1,052 numeric IDs will NOT appear in the mapping view
- These records remain in Issues_Current but are marked as unmapped
- They can be recovered only by:
  1. Extracting correct UUIDs from raw ACC API logs (Phase 2 investigation)
  2. Manual lookup in ACC system (if still available)
  3. Treating them as legacy/archived (if no longer relevant)

---

### Downstream Dependencies

#### Views

| View | Location | Impact | Action |
|------|----------|--------|--------|
| `vw_ProjectManagement_AllIssues` | ProjectManagement.dbo | **MEDIUM** - Combines ACC + Revizto; used by dashboards | ADD new columns (acc_issue_uuid, acc_issue_number, acc_id_type) |
| `vw_issues_expanded` | acc_data_schema.dbo | **LOW** - ACC-only view; data source | No change needed (already has display_id) |
| `vw_ProjectManagement_AllIssues_Metrics` | (if exists) | **MEDIUM** - Aggregations | Test query results after view update |

#### Warehouse Dimensions & Bridges

| Table | Location | Impact | Action |
|-------|----------|--------|--------|
| `dim.issue` | warehouse.dbo | **MEDIUM** - Stores all issue attributes; used by facts and marts | ADD columns: acc_issue_number, acc_issue_uuid |
| `brg.review_issue` | warehouse.brg | **LOW** - Bridge uses issue_sk (surrogate key), not source_issue_id | No change needed |
| `fact.issue_snapshot` | warehouse.fact | **LOW** - Uses issue_sk, issue_bk; source_issue_id is attribute | No change needed |
| `v_review_performance` | warehouse.mart | **MEDIUM** - May filter/group by issue attributes | Verify post-update (should not break) |

#### API Endpoints

| Endpoint | Impact | Change |
|----------|--------|--------|
| `GET /api/dashboard/issues-table` | **MEDIUM** | Can now expose acc_issue_number in display |
| `GET /api/projects/{id}/issues/overview` | **LOW** | Data from view; additive fields only |
| `GET /api/dashboard/issues-charts` | **LOW** | Aggregations unaffected |

---

## B) RECOMMENDED CANONICAL KEY STRATEGY

### Decision: UUID as Canonical Machine ID, Display_ID as Display Number

**Rationale**:
1. **UUID (issue_id) is the authoritative ACC primary key** — stable, never changes, unique across all ACC systems
2. **Display_ID (display_id) is the human-facing number** — what users see in ACC UI, expected in reports/filters
3. **77.84% of our data already uses UUID** — minimal breaking changes needed
4. **22.16% numeric issue_ids are orphaned** — cannot be reliably re-mapped without raw ACC logs; mark as legacy

### Proposed Schema Changes

#### Level 1: Normalized View (vw_acc_issue_id_map)

**Purpose**: Single source of truth for ACC issue resolution.

**Columns**:
- `issue_key` (NVARCHAR(255)) — composite key from Issues_Current
- `source_system` (NVARCHAR(32)) — 'ACC'
- `source_issue_id` (NVARCHAR(255)) — original value from Issues_Current (UUID or numeric)
- `source_project_id` (NVARCHAR(100)) — original project ID
- `acc_issue_uuid` (NVARCHAR(MAX)) — resolved to ACC.issue_id (canonical)
- `acc_issue_number` (INT) — resolved to ACC.display_id (for human display)
- `acc_project_uuid` (NVARCHAR(100)) — resolved to ACC.bim360_project_id
- `source_id_type` (NVARCHAR(20)) — 'uuid' or 'display_id' (indicates which path was used)
- `acc_title`, `acc_status`, `acc_created_at`, `acc_updated_at` — enriched attributes

**Usage**: 
```sql
-- Dashboard: Get human-friendly issue number
SELECT acc_issue_number, title FROM vw_acc_issue_id_map WHERE issue_key = 'ACC|10|524'

-- Reconciliation: Identify mapping type
SELECT * FROM vw_acc_issue_id_map WHERE source_id_type = 'display_id' -- Check legacy issues
```

#### Level 2: View Enhancement (vw_ProjectManagement_AllIssues)

**Changes**: Add three new columns (non-breaking):
- `acc_issue_uuid` (NVARCHAR(MAX), nullable) — NULL for Revizto
- `acc_issue_number` (INT, nullable) — NULL for Revizto
- `acc_id_type` (NVARCHAR(20), nullable) — NULL for Revizto; 'uuid' or 'display_id' for ACC

**Backward Compatibility**: Fully preserved. Existing queries unaffected. New columns at end of SELECT.

#### Level 3: Warehouse Dimension (dim.issue)

**Changes**: Add two new columns to `dim.issue`:
- `acc_issue_number` (INT, nullable)
- `acc_issue_uuid` (NVARCHAR(MAX), nullable)

**Impact**: 
- No breaking changes (columns are additive, nullable)
- Existing issue_sk, issue_bk, issue_key remain stable
- Bridges (brg.review_issue) use issue_sk, unaffected
- Marts can now report using acc_issue_number for ACC issues

**CRITICAL GUARANTEE: Warehouse Key Stability**

This implementation does **NOT** change:
- ✅ `issue_sk` (surrogate key) — warehouse primary key unchanged
- ✅ `issue_bk` (business key) — composite business key unchanged
- ✅ `issue_key` (source composite identifier) — de-duplication logic unchanged
- ✅ De-duplication strategy — still based on (source_system, source_project_id, source_issue_id)
- ✅ Bridge table joins — brg.review_issue still keys on issue_sk
- ✅ Fact table joins — fact.issue_snapshot still uses issue_sk, issue_bk

**What changes**: Only additive columns. The warehouse dimension is enriched, not restructured.

---

## C) IMPLEMENTATION PLAN

### Phase 1: Create Mapping View (SQL Server)

**File**: `sql/create_vw_acc_issue_id_map.sql`

**Logic**:
1. Try to join Issues_Current.source_issue_id to acc.issue_id (UUID path)
2. If source_issue_id lacks '-', try to join to acc.display_id (numeric path, with project validation)
3. Return both canonical fields + metadata

**Test Command**:
```sql
CREATE VIEW dbo.vw_acc_issue_id_map AS ...
SELECT COUNT(*) FROM vw_acc_issue_id_map WHERE source_id_type='uuid'   -- expect 3,696
SELECT COUNT(*) FROM vw_acc_issue_id_map WHERE source_id_type='display_id'  -- expect 0 (no valid joins)
```

**Risk**: None. View is read-only, doesn't modify data.

---

### Phase 2: Update vw_ProjectManagement_AllIssues

**File**: `sql/update_vw_projectmanagement_allissues_with_acc_display.sql`

**Changes**:
- Add three new columns to the SELECT for ACC issues
- Use conditional expression to set acc_id_type based on source_issue_id format
- Set all three columns to NULL for Revizto rows

**Test Command**:
```sql
-- Verify column presence
SELECT TOP 1 acc_issue_number, acc_issue_uuid, acc_id_type 
FROM vw_ProjectManagement_AllIssues 
WHERE source = 'ACC'

-- Verify counts
SELECT COUNT(CASE WHEN acc_issue_number IS NOT NULL THEN 1 END) FROM vw_ProjectManagement_AllIssues WHERE source='ACC'
-- expect 3,696 (all UUIDs now have display_id)
```

**Risk**: Very low. View recreation is non-breaking; existing queries use positional or named columns that are preserved.

---

### Phase 3: Warehouse Dimension Update

**File**: `warehouse/sql/dimensions/update_dim_issue_with_acc_identifiers.sql`

**Steps**:
1. ALTER TABLE dim.issue ADD acc_issue_number, acc_issue_uuid
2. CREATE INDEX on acc_issue_number (for ACC-specific queries)
3. CREATE PROCEDURE usp_update_dim_issue_acc_identifiers to backfill
4. Call the procedure to populate existing records
5. Verify coverage (expect 100% for UUID-style, 0% for legacy numeric)

**Test Command**:
```sql
EXEC warehouse.usp_update_dim_issue_acc_identifiers

-- Verify
SELECT 
    COUNT(*) as total_dim_issue,
    SUM(CASE WHEN acc_issue_number IS NOT NULL THEN 1 ELSE 0 END) as with_number
FROM dim.issue WHERE source_system='ACC' AND current_flag=1
-- expect ~3,696 with numbers
```

**Risk**: Low (column addition is non-breaking, update is additive).

---

## D) VALIDATION QUERIES

### Post-Implementation Checks

**Query 1**: Verify mapping view row count
```sql
SELECT COUNT(DISTINCT issue_key) FROM vw_acc_issue_id_map
-- Should equal count of ACC issues in Issues_Current (currently 4,748, but 1,052 are unfixable)
```

**Query 2**: Verify no duplicate acc_issue_numbers per project
```sql
SELECT acc_project_uuid, acc_issue_number, COUNT(*) FROM vw_acc_issue_id_map
WHERE source_id_type='uuid'
GROUP BY acc_project_uuid, acc_issue_number
HAVING COUNT(*) > 1
-- Should return 0 rows
```

**Query 3**: Verify warehouse dim.issue coverage
```sql
SELECT 
    source_system,
    COUNT(*) as total,
    SUM(CASE WHEN acc_issue_number IS NOT NULL THEN 1 ELSE 0 END) as with_number
FROM dim.issue WHERE current_flag=1
GROUP BY source_system
-- ACC should show ~3,696 with_number
```

**Query 4**: Verify dashboard issue counts unchanged
```sql
-- Before and after
SELECT COUNT(*) FROM Issues_Current WHERE source_system='ACC'           -- e.g., 4,748
SELECT COUNT(CASE WHEN source='ACC' THEN 1 END) FROM vw_ProjectManagement_AllIssues  -- should match
```

**Query 5**: Sample human-readable output
```sql
SELECT TOP 10
    issue_key,
    source_issue_id,
    acc_issue_number,
    title
FROM vw_ProjectManagement_AllIssues
WHERE source = 'ACC'
ORDER BY issue_id
```

---

## E) WAREHOUSE CHANGES (EXACT)

### dim.issue Table

**Current Structure**:
```sql
CREATE TABLE dim.issue (
    issue_sk                INT            PRIMARY KEY IDENTITY(1,1),
    issue_bk                NVARCHAR(255)  NOT NULL,
    source_system           NVARCHAR(32)   NOT NULL,
    source_issue_id         NVARCHAR(255)  NULL,
    ... (other columns unchanged)
)
```

**New Structure** (ADDITIVE ONLY):
```sql
ALTER TABLE dim.issue ADD
    acc_issue_number INT NULL,           -- ACC display_id (human-facing issue number)
    acc_issue_uuid NVARCHAR(MAX) NULL;   -- ACC issue_id (canonical UUID)
```

**Index**:
```sql
CREATE NONCLUSTERED INDEX ix_dim_issue_acc_number
    ON dim.issue(acc_issue_number)
    WHERE source_system = 'ACC' AND current_flag = 1;
```

**Backfill Logic**:
```python
# Pseudo-code for ETL
for each issue in dim.issue where source_system='ACC' and current_flag=1:
    lookup = vw_acc_issue_id_map(source_issue_id)
    if lookup.found:
        issue.acc_issue_number = lookup.acc_issue_number
        issue.acc_issue_uuid = lookup.acc_issue_uuid
```

### Bridge Tables (NO CHANGE)

- `brg.review_issue` — uses issue_sk (surrogate), unaffected
- Other bridges — check queries but expect no breaking changes

### Marts (VERIFY POST-UPDATE)

- `v_review_performance` — Uses dim.issue, should work as-is (test queries)
- `v_issue_summary` — Uses dim.issue, should work as-is (test queries)

---

## F) BACKFILL STRATEGY

### No Raw Data Re-import Needed ✅

**Key Advantage**: The 22.16% numeric `source_issue_id` values are already in Issues_Current. We don't need to re-import ACC dumps.

**Backfill Steps**:
1. Create vw_acc_issue_id_map (reads from acc_data_schema.dbo.issues_issues)
2. Join existing Issues_Current.source_issue_id to the ACC table
3. Populate dim.issue.acc_issue_number and acc_issue_uuid
4. Mark unmappable records (22.16%) as "legacy" / "unmatchable"

**For the 22.16% Unmappable Records**:
- Keep them in Issues_Current (no deletion)
- Mark in dim.issue with NULL acc_issue_number
- Flag in a metadata column or logging table for manual review
- Recommend re-mapping from raw ACC logs (out of scope for this phase)

**Expected Outcome**:
- 77.84% fully enriched with acc_issue_number and acc_issue_uuid
- 22.16% marked as incomplete; can be investigated in Phase 2 if high-priority

---

## G) ROLLBACK PLAN

**If issues arise post-deployment**:

1. **View rollback** (instant, no data loss):
   ```sql
   DROP VIEW vw_ProjectManagement_AllIssues
   -- Recreate from last good version in source control
   ```

2. **Column rollback** (instant, no data loss):
   ```sql
   ALTER TABLE dim.issue DROP COLUMN acc_issue_number, acc_issue_uuid
   ```

3. **No risk to core logic** — all changes are additive; existing queries unaffected

---

## H) RECOMMENDATIONS FOR PHASE 2 (FUTURE)

1. **Investigate the 22.16% unmappable issues**
   - Extract from raw ACC logs if available
   - Determine correct UUID for each
   - Update Issues_Current.source_issue_id to UUID

2. **Audit warehouse load**
   - Ensure dim.issue backfill reaches 100% coverage
   - Update load procedure to always join via UUID (once Phase 1 cleanup complete)

3. **Dashboard enhancements**
   - Display acc_issue_number in issue tables (more human-friendly than UUID)
   - Filter by acc_issue_number in faceted search

4. **API enhancement**
   - Expose acc_issue_number in issue endpoint responses
   - Allow filtering by acc_issue_number

---

## I) SIGN-OFF CHECKLIST

- ✅ Schema inspection complete (Issues_Current, issues_issues identified)
- ✅ Match rate analysis done (77.84% UUID, 22.16% numeric)
- ✅ Downstream dependencies mapped (views, warehouse dims, APIs)
- ✅ Canonical strategy defined (UUID machine key, display_id for humans)
- ✅ Implementation scripts ready (3 SQL files + validation queries)
- ✅ Warehouse impact assessed (non-breaking, additive columns)
- ✅ Rollback plan documented
- ✅ No data loss risk identified
- ✅ Backward compatibility guaranteed

---

## Implementation Status

**Ready for Deployment** ✅

**Deliverables**:
1. `sql/create_vw_acc_issue_id_map.sql` — Mapping view
2. `sql/update_vw_projectmanagement_allissues_with_acc_display.sql` — View enhancement
3. `warehouse/sql/dimensions/update_dim_issue_with_acc_identifiers.sql` — DIM update
4. `sql/validate_acc_issue_reconciliation.sql` — Validation test suite

**Next Steps**:
1. Execute scripts in order
2. Run validation test suite
3. Verify dashboard queries continue to work
4. Update API documentation (if new columns are exposed)

---

*Report prepared: 2026-01-15*  
*Estimated implementation time: 30 minutes*  
*Estimated testing time: 15 minutes*  
*Total risk: LOW*
