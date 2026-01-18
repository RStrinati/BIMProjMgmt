# Quality Register Audit & Integration Map

**Prepared**: January 16, 2026  
**Scope**: Implement Quality tab → Model Register in Project Workspace v2  
**Status**: AUDIT COMPLETE - Decision: **Option A** (thin aggregation endpoint)

---

## 1. Existing Tables & Views

### 1.1 Primary Data Sources

#### `tblRvtProjHealth` (RevitHealthCheckDB.dbo)
**Purpose**: Revit model health check records from model extraction  
**Key Fields**:
- `nId` (PK)
- `strRvtFileName` (model filename; human-readable identifier)
- `strProjectName` (extracted from model)
- `strProjectNumber`
- `strClientName`
- `strRvtVersion`, `strRvtBuildVersion`
- `STR_EXTRACTED_PROJECT_NAME` (normalized project name)
- `DISCIPLINE_CODE`, `DISCIPLINE_FULL_NAME`
- `nModelFileSizeMB`
- `ConvertedExportedDate` (model export date; closest to "last version")
- `VALIDATION_STATUS` (enum: e.g., "PASS", "FAIL", "WARN")
- `VALIDATION_REASON` (text)
- `VALIDATED_DATE` (when validation ran)

**Linkage to PM Database**:
- `pm_project_id` (foreign key reference; passed in queries)
- Cross-database: RevitHealthCheckDB → ProjectManagement via application logic

---

#### `tblControlModels` (ProjectManagement.dbo)
**Purpose**: Track control models designated for a project  
**Key Fields**:
- `id` (PK)
- `project_id` (FK → Projects; always required)
- `control_file_name` (filename of control model; e.g., "CTRL_STR_M.rvt")
- `is_active` (boolean; current active state)
- `created_at`, `updated_at` (timestamps)
- `metadata_json` (optional; JSON column if supported; contains zone_code, validation_targets, volume_label, notes)

**Purpose**: `is_active=1` identifies which file in `tblRvtProjHealth` is the control model.

---

#### `vw_LatestRvtFiles` (RevitHealthCheckDB.dbo)
**Purpose**: Materialized or indexed view returning the latest Revit file per logical model per project  
**Probable Structure**:
- `pm_project_id`
- `strRvtFileName` (distinct logical model)
- `ConvertedExportedDate` (max date for that model)
- Other aggregated fields from `tblRvtProjHealth`

**Query Usage**: `get_project_health_files(project_id)` → returns list of distinct file names.

---

### 1.2 Review Schedule (for freshness computation)

#### `ReviewSchedule` (ProjectManagement.dbo)
**Purpose**: Track planned and actual review dates for a project  
**Key Fields**:
- `schedule_id` (PK)
- `project_id` (FK)
- `review_date` (planned review date)
- `status` (enum; tracks if review occurred)
- `cycle_id` (links to review cycle)

**Usage for Freshness**:
- Query next_review_date = MIN(review_date) WHERE review_date > TODAY for a project
- Compare `lastVersionDate` (from `tblRvtProjHealth.ConvertedExportedDate`) to next_review_date

---

### 1.3 Services & Service Items (for mapping)

#### `Services` (ProjectManagement.dbo)
**Purpose**: Track service offerings per project  
**Key Fields**:
- `service_id` (PK)
- `project_id` (FK)
- `service_name`

**Linkage**: If a model's discipline/company can be mapped to a service, use `service_id` as `primaryServiceId`.  
**Current MVP**: Most models will be `UNMAPPED` (service_id = NULL) until manual assignment is added.

---

## 2. Existing Endpoints

### 2.1 Backend Endpoints (current)

#### `GET /api/dashboard/model-register`
**Status**: Exists but **not yet fully implemented** (returns empty placeholder)  
**Current Code** (backend/app.py:3755):
```python
@app.route('/api/dashboard/model-register', methods=['GET'])
def api_dashboard_model_register():
    """Model register (Revit-derived) paginated."""
    # ...calls get_model_register() which is a placeholder
```

**Payload**:
```json
{
  "page": 1,
  "page_size": 50,
  "sort_by": "last_seen_at",
  "sort_dir": "desc"
}
```

**Response** (current placeholder):
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

---

#### `GET /api/projects/<int:project_id>/control-models`
**Status**: Fully implemented  
**Purpose**: Fetch control model configuration for a project  
**Response**:
```json
{
  "control_models": [
    {
      "id": 123,
      "file_name": "CTRL_STR_M.rvt",
      "is_active": true,
      "validation_targets": ["naming", "coordinates"],
      "zone_code": "STR",
      "is_primary": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "available_models": ["STR_M.rvt", "MEP_M.rvt", ...],
  "active_models": [...]
}
```

---

#### `POST /api/projects/<int:project_id>/control-models`
**Status**: Fully implemented  
**Purpose**: Persist control model selections and metadata  
**Payload**:
```json
{
  "control_models": [
    {
      "file_name": "CTRL_STR_M.rvt",
      "validation_targets": ["naming", "coordinates"],
      "zone_code": "STR",
      "is_primary": true,
      "volume_label": "Vol.3",
      "notes": "Primary coordinate control"
    }
  ]
}
```

---

### 2.2 Database Functions (backend/database.py)

#### `get_project_health_files(project_id: int) → List[str]`
**Purpose**: Fetch distinct Revit file names from `vw_LatestRvtFiles` for a project  
**Returns**: List of unique filenames  
**Source**: RevitHealthCheckDB.dbo.vw_LatestRvtFiles

---

#### `get_control_models(project_id: int) → List[Dict[str, Any]]`
**Purpose**: Fetch control model records with optional metadata  
**Returns**: 
```python
[
  {
    'id': 1,
    'control_file_name': 'CTRL_STR_M.rvt',
    'is_active': True,
    'created_at': datetime(...),
    'updated_at': datetime(...),
    'metadata': {...}  # if metadata_json column exists
  }
]
```
**Source**: ProjectManagement.dbo.tblControlModels

---

#### `get_model_register(...) → Dict[str, Any]`
**Status**: **Placeholder - returns empty**  
**Intended Purpose**: Return paginated + filtered register rows  
**Current Implementation**: Stub that returns `{"items": [], "total": 0, ...}`

---

## 3. Data Flow: Retrieving Register Rows per Project

### Current Flow (Gaps Identified)

```
Request: GET /projects/123/quality/register

1. Backend queries tblControlModels WHERE project_id = 123
   → Get list of control model file names + is_active status

2. Backend queries vw_LatestRvtFiles WHERE pm_project_id = 123
   → Get distinct latest Revit files (one per logical model)

3. For each model file:
   - Look up in tblRvtProjHealth for health data (discipline, export date, validation)
   - Cross-reference with tblControlModels to get is_active + metadata
   - Determine next review date from ReviewSchedule
   - Compute freshness status
   - Look up service mapping (if rule exists; else UNMAPPED)

4. Build register row contract
5. Return paginated + sorted response
```

---

## 4. Gaps for MVP Register

| Gap | Impact | MVP Solution |
|-----|--------|--------------|
| `get_model_register()` is a stub | Cannot fetch register data | **Implement as CTE-based single query** |
| No per-model service mapping table | Cannot auto-link models to services | **Return `UNMAPPED` for all; add manual UI later** |
| Freshness logic not implemented | Cannot compute DUE_SOON / OUT_OF_DATE | **Implement in backend; use ReviewSchedule.review_date** |
| No validation status aggregation | Cannot surface pass/warn/fail clearly | **Use existing VALIDATION_STATUS from tblRvtProjHealth** |
| Model key not standardized | Register rows may be ambiguous | **Use `strRvtFileName` as modelKey (stable + unique per project)** |

---

## 5. Decision: Option A (Thin Aggregation Endpoint)

### Why Option A

✅ **Single Deterministic Query**: CTE-based join of tblRvtProjHealth + tblControlModels + ReviewSchedule eliminates multiple round-trips  
✅ **Performance**: One call from frontend instead of 3–4 calls  
✅ **Freshness Guarantee**: Backend computes freshness using consistent SQL logic (no time-zone surprises)  
✅ **Scalability**: Pagination + sorting offloaded to database  
✅ **Maintainability**: All register logic in one place (backend endpoint)

### Implementation: New Endpoint

```
GET /projects/:projectId/quality/register
  ?page=1
  &page_size=50
  &sort_by=lastVersionDate
  &sort_dir=desc
  &filter_attention=true  (optional; if true, only Attention rows)

Response:
{
  "rows": [
    {
      "modelKey": "STR_M.rvt",
      "modelName": "STR_M.rvt",
      "discipline": "Structural",
      "company": "Structural Contractor Inc.",
      "lastVersionDate": "2025-01-14T10:30:00Z",
      "source": "REVIT_HEALTH",
      "isControlModel": true,
      "freshnessStatus": "CURRENT",
      "validationOverall": "PASS",
      "primaryServiceId": null,
      "mappingStatus": "UNMAPPED"
    },
    {
      "modelKey": "MEP_M.rvt",
      "modelName": "MEP_M.rvt",
      "discipline": "Mechanical",
      "company": null,
      "lastVersionDate": "2024-12-10T14:00:00Z",
      "source": "REVIT_HEALTH",
      "isControlModel": false,
      "freshnessStatus": "OUT_OF_DATE",
      "validationOverall": "WARN",
      "primaryServiceId": null,
      "mappingStatus": "UNMAPPED"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 42,
  "attention_count": 3
}
```

---

## 6. MVP Register Row Contract

### TypeScript Definition

```typescript
export type QualityRegisterRow = {
  modelKey: string;                 // e.g., "STR_M.rvt" (stable per logical model)
  modelName: string;                // e.g., "STR_M.rvt" (human-readable)
  
  discipline?: string;              // e.g., "Structural" (from extracted project)
  company?: string;                 // e.g., "Structural Contractor Inc."
  
  lastVersionDate?: string;         // ISO 8601 date (ConvertedExportedDate)
  source?: string;                  // e.g., "REVIT_HEALTH"
  
  isControlModel: boolean;          // true if in tblControlModels.is_active=1
  
  freshnessStatus: "CURRENT" | "DUE_SOON" | "OUT_OF_DATE" | "UNKNOWN";
  
  validationOverall: "PASS" | "WARN" | "FAIL" | "UNKNOWN";
  
  primaryServiceId?: number | null; // FK → Services; null = UNMAPPED
  mappingStatus: "MAPPED" | "UNMAPPED";
};
```

### Freshness Logic (Backend SQL)

```sql
DECLARE @tolerance_days INT = 0;
DECLARE @due_soon_days INT = 7;

CASE
  WHEN next_review_date IS NULL THEN 'UNKNOWN'
  WHEN lastVersionDate IS NULL THEN 'UNKNOWN'
  WHEN DATEDIFF(DAY, lastVersionDate, next_review_date) <= 0 THEN 'OUT_OF_DATE'
  WHEN DATEDIFF(DAY, lastVersionDate, next_review_date) <= @due_soon_days THEN 'DUE_SOON'
  ELSE 'CURRENT'
END AS freshnessStatus
```

**Where**:
- `next_review_date` = MIN(ReviewSchedule.review_date) WHERE review_date > GETDATE() AND project_id = ?
- `lastVersionDate` = tblRvtProjHealth.ConvertedExportedDate

---

## 7. Attention Filter Definition

**Show models where ANY of**:
- `freshnessStatus` = `OUT_OF_DATE`
- `validationOverall` = `FAIL` or `WARN`
- `isControlModel = FALSE` and control is expected (rule not defined in MVP; skip for now)
- `mappingStatus` = `UNMAPPED`

---

## 8. UI Implementation Plan

### 8.1 Quality Tab in Project Workspace v2

**Tab Label**: "Quality"  
**Route**: `/projects/:id/workspace?tab=Quality` (or linear tab system)

**Layout**:
- Top: Segmented control (Attention | All models)
- Optional quick chips: Out-of-date, Unmapped, No control (filtered counts)
- Dense table with columns:
  - Freshness (pill)
  - Model name (link-ready)
  - Discipline
  - Company
  - Last version date
  - Control indicator (badge or icon)
  - Validation overall (pill)
  - Service mapping (chip or text)

### 8.2 Row Click Behavior

**Drawer** (prefer for MVP speed):
- Right-side detail panel
- Shows:
  - Model name + filename
  - Discipline + Company
  - Last version date + validation date
  - Control status + zone code (if applicable)
  - Validation details (pass/warn/fail reason)
  - Service mapping (chip; "Unmapped" if null)
  - Quick link to "Manage Control Models" if control model

---

## 9. Constants & Tolerances

**Added to frontend config** (src/config/quality.ts):
```typescript
export const QUALITY_REGISTER_CONFIG = {
  DUE_SOON_WINDOW_DAYS: 7,
  TOLERANCE_DAYS: 0,
};
```

---

## 10. Schema & No Changes Required

✅ **No new tables** (uses existing tblRvtProjHealth + tblControlModels + ReviewSchedule)  
✅ **No new columns** (all data available)  
⚠️ **Assumption**: metadata_json column in tblControlModels exists or is supported (check via _control_model_metadata_column_exists helper)

---

## 11. Deliverables Checklist

- [ ] docs/QUALITY_REGISTER_AUDIT.md ← **YOU ARE HERE**
- [ ] backend/app.py: `GET /projects/:projectId/quality/register` endpoint
- [ ] database.py: Refactor `get_model_register()` from stub to real implementation
- [ ] frontend/src/types/api.ts: Add QualityRegisterRow type
- [ ] frontend/src/api/quality.ts: New qualityApi with getRegister(projectId)
- [ ] frontend/src/pages/ProjectWorkspacePageV2.tsx: Add Quality tab
- [ ] frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx: Register table + filters
- [ ] tests/e2e/project-quality-register.spec.ts: Playwright E2E tests
- [ ] frontend/src/config/quality.ts: Constants (DUE_SOON_WINDOW_DAYS, TOLERANCE_DAYS)

---

## 12. Next Steps

1. **Phase 1**: Implement backend endpoint `GET /projects/:projectId/quality/register`
2. **Phase 2**: Create TypeScript types and frontend api client
3. **Phase 3**: Add Quality tab to ProjectWorkspacePageV2
4. **Phase 4**: Implement register table + filters + drawer detail
5. **Phase 5**: Write Playwright E2E tests

---

## References

- **Schema**: [constants/schema.py](../constants/schema.py) → `TblRvtProjHealth`, `ControlModels`, `ReviewSchedule`
- **Existing Endpoints**: [backend/app.py](../backend/app.py#L3755) → `/api/dashboard/model-register`, `/api/projects/<id>/control-models`
- **Database Functions**: [database.py](../database.py#L2611) → `get_project_health_files`, `get_control_models`, `get_model_register`
- **Current UI**: [frontend/src/pages/ProjectWorkspacePageV2.tsx](../frontend/src/pages/ProjectWorkspacePageV2.tsx)
- **Current Imports UI**: [frontend/src/pages/DataImportsPage.tsx](../frontend/src/pages/DataImportsPage.tsx) (reference for similar data-heavy views)
