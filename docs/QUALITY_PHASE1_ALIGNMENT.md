# Phase 1A: Inspection & Alignment Report

**Date**: January 16, 2026  
**Status**: ✅ ALIGNMENT DECISIONS CONFIRMED  
**Scope**: Quality Register refactor - Expected-first model with Alias reconciliation

---

## 1. Current Quality Register Behavior (CONFIRMED)

### Endpoint
- **Route**: `GET /api/projects/:projectId/quality/register`
- **Handler**: `get_project_quality_register()` in backend/app.py:5390
- **Database Layer**: `get_model_register()` in database.py:2693

### Data Sources
1. **ProjectManagement DB**:
   - `ControlModels`: control file flags (filename-based matching)
   - `ReviewSchedule`: next review date for freshness calculation

2. **RevitHealthCheckDB**:
   - `vw_LatestRvtFiles`: latest Revit files per project
   - `tblRvtProjHealth`: validation status (LEFT JOIN with ROW_NUMBER dedup)

### Current Behavior (Observed-Only)
1. Queries `vw_LatestRvtFiles` filtered by `pm_project_id`
2. LEFT JOINs to `tblRvtProjHealth` (latest per filename via ROW_NUMBER)
3. Normalizes model names (Phase B):
   - Extracts canonical key (first 3 dash-separated components)
   - Marks MISNAMED if contains `_detached`, `_OLD`, spaces, etc.
   - Deduplicates: keeps latest version per canonical key
4. Computes freshness (days until next review)
5. Maps validation status (Valid→PASS, Invalid→FAIL, null→UNKNOWN)
6. Returns paginated rows with attention filtering

### Current Response Shape
```json
{
  "rows": [
    {
      "modelKey": "filename.rvt",
      "modelName": "filename.rvt",
      "discipline": "MEP",
      "company": "Client Name",
      "lastVersionDateISO": "2026-01-15T10:30:00",
      "source": "REVIT_HEALTH",
      "isControlModel": true,
      "freshnessStatus": "CURRENT",
      "validationOverall": "PASS",
      "primaryServiceId": null,
      "mappingStatus": "UNMAPPED",
      "namingStatus": "CORRECT"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 12,
  "attention_count": 2
}
```

### Current Limitations (Phase 0 Audit)
1. **Never-empty problem**: No expected models → register empty for new projects
2. **Alias gap**: Observed files matched to expected only via filename
3. **Duplication**: Misnamed files appear as separate rows (no grouping)
4. **Service mapping**: primaryServiceId always null (deferred to Phase C)

---

## 2. ProjectAliases Analysis (CONFIRMED)

### Current Purpose
- **Project-level identity mapping**: Maps internal project names to external identifiers
- **Use cases**: Revizto UUID, ACC project code, project nickname variants
- **Table**: `ProjectManagement.dbo.ProjectAliases`
- **Semantics**: One alias entry per (project, alias_name) pair
- **Manager**: `ProjectAliasManager` in services/project_alias_service.py
- **Endpoints**: `/api/project_aliases/*` (CRUD, summary, auto-map, analyze)

### Key Characteristics
- Project-scoped: identifies the project itself across external systems
- NOT model-specific: does not map individual file names
- Well-established: used in warehouse ETL, Revizto mapping, ACC reconciliation
- Active maintenance: OptimizedProjectAliasManager, bulk import/export support

### Schema Excerpt
```sql
-- ProjectManagement.dbo.ProjectAliases
-- Maps project_id → external aliases (Revizto UUID, ACC code, etc.)
-- Does NOT include model-level aliasing
```

### Decision on ProjectAliases
✅ **KEEP ProjectAliases unchanged**
- Do NOT repurpose for model-level aliasing
- Do NOT add model-specific columns
- Maintain project-level semantics for existing workflows
- Create separate ExpectedModelAliases table (see Phase 1B)

---

## 3. Model Alias Concept Search (CONFIRMED)

### Existing Tables Checked
- ❌ ExpectedModels: Does NOT exist
- ❌ ModelAliases: Does NOT exist
- ❌ FileAliases: Does NOT exist
- ❌ AliasPattern: Does NOT exist

### References Found
- Phase 0 Audit mentions ExpectedModels as deferred to Phase 1
- PHASE0_QUICK_REFERENCE.md includes schema blueprint
- QUALITY_REGISTER_PHASE0_AUDIT_B.md Section 8 defines design

### Decision
✅ **CREATE new tables**: ExpectedModels + ExpectedModelAliases
- These are model-level concepts (not project-level)
- No existing equivalent to reuse
- Implement per Phase 0 Audit blueprint

---

## 4. API Contract Decisions

### Backwards Compatibility
✅ **Maintain existing behavior by default**
- Current endpoint `/api/projects/:projectId/quality/register` continues as-is (observed-only mode)
- New mode available via query parameter: `mode=expected`

### Option A (CHOSEN): Query Parameter Mode Flag
```http
GET /api/projects/:projectId/quality/register?mode=expected
GET /api/projects/:projectId/quality/register?mode=observed  # default
```

**Rationale**:
- No breaking changes to existing API
- Clear upgrade path for frontend
- Single endpoint for both modes
- Easy to A/B test or sunset observed mode later

### Response Shapes

#### Mode: observed (DEFAULT - existing behavior)
```json
{
  "rows": [ /* existing row structure */ ],
  "page": 1,
  "page_size": 50,
  "total": 12,
  "attention_count": 2
}
```

#### Mode: expected (NEW)
```json
{
  "expected_rows": [
    {
      "expected_model_id": 45,
      "expected_model_key": "NFPS-ACO-00",
      "display_name": "Architectural Core",
      "discipline": "Architecture",
      "is_required": true,
      "observed_filename": "NFPS-ACO-00-M3-001.rvt",
      "lastVersionDateISO": "2026-01-15T10:30:00",
      "observed_discipline": "Architecture",
      "validationOverall": "PASS",
      "namingStatus": "CORRECT",
      "isControlModel": true,
      "freshnessStatus": "CURRENT",
      "mappingStatus": "MAPPED"
    }
  ],
  "unmatched_observed": [
    {
      "observed_filename": "NFPS-OLD-BACKUP.rvt",
      "discipline": "Architecture",
      "lastVersionDateISO": "2025-11-20T09:00:00",
      "validationOverall": "FAIL",
      "namingStatus": "MISNAMED",
      "note": "No matching expected model"
    }
  ],
  "counts": {
    "expected_total": 10,
    "expected_missing": 2,
    "unmatched_total": 1,
    "attention_count": 3
  }
}
```

### New Endpoints

#### Expected Model CRUD
```http
GET    /api/projects/:projectId/quality/expected-models
POST   /api/projects/:projectId/quality/expected-models
```

#### Expected Model Alias Management
```http
POST   /api/projects/:projectId/quality/expected-model-aliases
GET    /api/projects/:projectId/quality/expected-model-aliases
```

#### Mapping Action
```http
POST   /api/projects/:projectId/quality/unmatched/:filename/map-to-expected
```

---

## 5. Schema Design Decisions

### New Tables (ProjectManagement DB)

#### Table: ExpectedModels
- **Purpose**: Authoritative register of expected Revit models for a project
- **Scope**: Project-owned, manually created and maintained
- **Lifecycle**: Never-empty register; always exists even if no observed files
- **Philosophy**: Represents intended deliverables, not current state

**Columns**:
| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| `expected_model_id` | INT PK | IDENTITY(1,1) | Primary key |
| `project_id` | INT | FK→Projects, NOT NULL | Scoping |
| `expected_model_key` | NVARCHAR(100) | UNIQUE(project_id, key), NOT NULL | Canonical identifier |
| `display_name` | NVARCHAR(255) | Nullable | User-friendly name (e.g., "Arch Core") |
| `discipline` | NVARCHAR(50) | Nullable | Hard-coded discipline (manual authority) |
| `company_id` | INT | FK→Companies, Nullable | Optional: linked company |
| `is_required` | BIT | DEFAULT 1 | Marks critical models |
| `created_at` | DATETIME | DEFAULT GETDATE() | Audit |
| `updated_at` | DATETIME | DEFAULT GETDATE() | Audit |

#### Table: ExpectedModelAliases
- **Purpose**: Map observed filenames/keys to expected models
- **Scope**: Project-scoped; multiple aliases per expected model allowed
- **Lifecycle**: Built incrementally as observed files are mapped
- **Philosophy**: Reconciles naming variations without modifying observed data

**Columns**:
| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| `expected_model_alias_id` | INT PK | IDENTITY(1,1) | Primary key |
| `expected_model_id` | INT | FK→ExpectedModels, NOT NULL | Linkage |
| `project_id` | INT | Denormalized, Nullable | Perf/scoping |
| `alias_pattern` | NVARCHAR(255) | NOT NULL | Pattern to match (filename, model key, regex) |
| `match_type` | NVARCHAR(50) | DEFAULT 'exact', NOT NULL | exact, contains, regex |
| `target_field` | NVARCHAR(50) | DEFAULT 'filename', NOT NULL | filename, rvt_model_key |
| `is_active` | BIT | DEFAULT 1 | Enable/disable without delete |
| `created_at` | DATETIME | DEFAULT GETDATE() | Audit |
| **Indexes** | | | |
| | | INDEX (project_id, is_active) | Fast lookup by project |
| | | INDEX (expected_model_id) | Fast lookup by expected |

### No Changes to Existing Tables
- ✅ ProjectAliases: Unchanged
- ✅ ControlModels: Unchanged
- ✅ ReviewSchedule: Unchanged
- ✅ vw_LatestRvtFiles: Unchanged (RevitHealthCheckDB)
- ✅ tblRvtProjHealth: Unchanged (RevitHealthCheckDB)

---

## 6. Data Resolution Logic (Expected Mode)

### Flow Diagram
```
Observed Dataset (from health)
    ↓
    ├─→ Query vw_LatestRvtFiles (pm_project_id)
    └─→ LEFT JOIN tblRvtProjHealth (latest per filename)
        ↓
        Build Observed List (in-memory):
          observed_filename
          observed_rvt_model_key
          observed_discipline
          validationOverall
          lastVersionDate
        ↓
        Alias Resolution Loop:
          For each observed record:
            1. Find ALL matching aliases (by pattern + match_type)
            2. Apply priority: exact_filename > exact_rvt_key > contains > regex
            3. If tie: choose newest (created_at DESC) or lowest ID
            4. Log conflicts (don't crash)
            5. Populate observed_filename in expected row
        ↓
Build Expected Rows:
  For each ExpectedModel:
    1. Look up matched observed file (if any)
    2. Populate observed fields (nullable if no match)
    3. Mark mappingStatus = MAPPED or UNMAPPED
    4. Include freshnessStatus, validationOverall, control flag
        ↓
Build Unmatched List:
  Observed files with NO matching alias
        ↓
Return Response:
  expected_rows: all expected (regardless of match)
  unmatched_observed: orphaned observed files
  counts: totals and attention markers
```

### Match Priority (Deterministic)
1. **Exact filename match** (case-insensitive)
2. **Exact rvt_model_key match**
3. **Contains substring** (case-insensitive, first match)
4. **Regex pattern** (Python regex, first match)

If multiple aliases match at same priority:
- Choose most recently created (or lowest ID for ties)
- Log warning to server logs (include both filenames)
- Continue without crashing

### Attention Count (Expected Mode)
Include rows with ANY of:
- `freshnessStatus` = OUT_OF_DATE
- `validationOverall` IN (FAIL, WARN)
- `mappingStatus` = UNMAPPED
- unmatched_observed count

---

## 7. Implementation Approach

### Database Changes
1. Create ExpectedModels table in ProjectManagement
2. Create ExpectedModelAliases table in ProjectManagement
3. Add both to constants/schema.py
4. Update check_schema.py to verify new tables

### Backend Changes
1. Create `ExpectedModelAliasManager` class (new, separate from ProjectAliasManager)
2. Update `get_model_register()` to support `mode=expected` parameter
3. Add helper function: alias resolution logic
4. Add three new CRUD endpoints
5. Maintain backwards compatibility (mode=observed default)

### Frontend Changes
1. Update Quality tab to call `?mode=expected`
2. Add segmented control (Register | Unmatched)
3. Update columns per spec
4. Add minimal mapping modal

### Tests
1. Seed 2+ ExpectedModels per test project
2. Verify expected rows appear even with no observed files
3. Verify MISSING status when expected has no match
4. Verify MAPPED when alias finds observed
5. Verify unmatched observed list

---

## 8. Decision Summary

| Item | Decision | Rationale |
|------|----------|-----------|
| **ProjectAliases Usage** | Keep unchanged, project-level only | Separate concern; don't break existing workflows |
| **New Model Alias Tables** | Create ExpectedModels + ExpectedModelAliases | No existing equivalent; required for Phase 1 |
| **API Versioning** | Query param `mode=expected` vs `mode=observed` | Backwards compatible; single endpoint |
| **Database Scope** | ProjectManagement DB (both tables) | Models are workflow config, not telemetry |
| **Alias Matching Priority** | exact > contains > regex | Deterministic; manual control via priority order |
| **Conflict Handling** | Log warning, continue (don't crash) | Fail-safe; operator can fix manually |
| **Freshness Calculation** | Reuse existing ReviewSchedule logic | Same semantics; no breaking changes |
| **Control Model Matching** | Keep filename-based (Phase B) | Sufficient for MVP; can enhance later |
| **Service Mapping** | Defer to Phase C (placeholder only) | Out of scope for Phase 1 |

---

## 9. Risk Assessment

### Low Risk (✅ Mitigated)
1. **Breaking changes**: Query param mode ensures backwards compatibility
2. **ProjectAliases confusion**: New tables clearly separate project vs model aliasing
3. **Duplication**: Explicit schema design prevents mixing concerns
4. **Data migration**: No changes to existing tables; pure addition

### Non-Blocking Items
1. **Performance at scale**: Monitor with large project (500+ models), optimize if needed
2. **UI complexity**: Minimal modal per spec; can iterate post-MVP
3. **Service mapping logic**: Deferred to Phase C; placeholder in Phase 1

---

## 10. Go/No-Go for Phase 1B

**Status**: ✅ **GO**

**Confidence**: 100%

**Next Action**: Implement Phase 1B (Create ExpectedModels tables)

**Deliverable**: QUALITY_PHASE1_ALIGNMENT.md (this document)

---

**Approved by**: Senior Full-Stack Engineer  
**Date**: January 16, 2026  
**Phase**: 1A ✅ Complete → Ready for Phase 1B
