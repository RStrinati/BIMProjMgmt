# Quality Register Phase 0 Audit A: Discovery
**Date**: February 27, 2026  
**Scope**: Current quality register endpoints, alias routing, data sources  
**Status**: COMPLETE

---

## 1. Current Quality Register Endpoint

### 1.1 Endpoint Definition
**Route**: `/api/projects/<project_id>/quality/register`  
**Method**: GET  
**Location**: [backend/app.py#L5390](backend/app.py#L5390)

**Query Parameters**:
- `page` (int, default=1): Page number for pagination
- `page_size` (int, default=50): Results per page (capped at 500)
- `sort_by` (str, default='lastVersionDate'): Sort column
  - Valid values: `lastVersionDate`, `modelName`, `freshnessStatus`, `validationOverall`
- `sort_dir` (str, default='desc'): Sort direction
  - Valid values: `asc`, `desc`
- `filter_attention` (bool, default=false): Show only models needing attention

### 1.2 Handler Function
**Function**: `get_project_quality_register(project_id)`  
**Location**: [backend/app.py#L5390-L5428](backend/app.py#L5390-L5428)

**Implementation**:
```python
@app.route('/api/projects/<int:project_id>/quality/register', methods=['GET'])
def get_project_quality_register(project_id):
    # Parses query params
    # Validates pagination (page ≥ 1, page_size ∈ [1, 500])
    # Calls database.get_model_register()
    # Returns JSON: {rows, page, page_size, total, attention_count}
```

**Response Schema**:
```json
{
  "rows": [
    {
      "modelKey": "NFPS-ACO-00-00-M3-C-0001.rvt",
      "modelName": "NFPS-ACO-00-00-M3-C-0001.rvt",
      "discipline": "Architectural",
      "company": "Client Name",
      "lastVersionDateISO": "2026-02-01T14:30:00",
      "source": "REVIT_HEALTH",
      "isControlModel": false,
      "freshnessStatus": "CURRENT|DUE_SOON|OUT_OF_DATE|UNKNOWN",
      "validationOverall": "PASS|FAIL|WARN|UNKNOWN",
      "primaryServiceId": null,
      "mappingStatus": "UNMAPPED",
      "namingStatus": "CORRECT|MISNAMED"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 12,
  "attention_count": 3
}
```

---

## 2. Backend Data Access Function

### 2.1 get_model_register()
**Function**: `get_model_register(project_id, page, page_size, sort_by, sort_dir, filter_attention)`  
**Location**: [database.py#L2693-L3050](database.py#L2693-L3050)

**Data Flow**:
1. **Query ProjectManagement DB**: Fetch control models and next review date
   - Query: Control models via `ControlModels` table
   - Filter: WHERE `project_id` = ?
   - Purpose: Mark which models are control models; determine freshness window

2. **Query RevitHealthCheckDB**: Fetch latest Revit files with validation data
   - Base table: `vw_LatestRvtFiles`
   - Joined table: `tblRvtProjHealth` (LEFT JOIN on filename)
   - Filter: WHERE `pm_project_id` = ?
   - Columns returned: 11 fields (see below)

3. **Phase B Processing**: Normalize and deduplicate
   - Detect misnamed files (trailing spaces, unusual patterns)
   - Group by canonical model key (first 3 dash-separated components)
   - Keep only latest version per key
   - Mark misnamed files explicitly

4. **Phase B Filtering & Pagination**:
   - Apply `filter_attention` if true
   - Attention items: OUT_OF_DATE | FAIL | WARN | MISNAMED | UNMAPPED
   - Paginate results
   - Return with pagination metadata

**Key Implementation Details**:
- **Freshness Computation**:
  ```python
  if days_until_review < 0:
      status = 'OUT_OF_DATE'
  elif days_until_review <= 7:
      status = 'DUE_SOON'
  else:
      status = 'CURRENT'
  ```

- **Validation Mapping**:
  - DB value "Valid" / "VALID" → "PASS"
  - DB value "Invalid" / "INVALID" → "FAIL"
  - DB value "Warn" / "WARN" → "WARN"
  - NULL or unrecognized → "UNKNOWN"

- **Naming Status Logic**:
  ```python
  # Model is MISNAMED if:
  # - Contains '_detached', '_OLD', '_old', '__', '_001', '_0001'
  # - Has leading/trailing spaces after strip()
  # - Doesn't contain dashes (basic structure check)
  # - Can't extract 3+ dash-separated components
  
  # Model is CORRECT if normalized_key extracted successfully
  ```

---

## 3. Alias Route Implementation

### 3.1 Alias Manager Service
**Class**: `ProjectAliasManager`  
**Location**: [services/project_alias_service.py](services/project_alias_service.py)

**Import in app.py**: Line 171
```python
from services.project_alias_service import ProjectAliasManager
```

### 3.2 Alias Endpoints

#### 3.2.1 GET /api/project_aliases/summary
**Location**: [backend/app.py#L2664-L2679](backend/app.py#L2664-L2679)

**Function**: `api_get_project_aliases_summary()`  
**Uses**: `OptimizedProjectAliasManager`  
**Purpose**: Return summary of all project aliases (lightweight)

#### 3.2.2 POST /api/project_aliases/analyze
**Location**: [backend/app.py#L2680-L2700](backend/app.py#L2680-L2700)

**Function**: `api_analyze_project_aliases()`  
**Purpose**: Analyze project aliases for conflicts, duplicates, orphans

#### 3.2.3 GET /api/project_aliases
**Location**: [backend/app.py#L2702](backend/app.py#L2702)

**Function**: List all project aliases

### 3.3 Alias Database Table
**Table**: `ProjectAliases`  
**Location**: Schema constants via [constants/schema.py](constants/schema.py)

**Fields** (inferred from grep results):
- `ALIAS_NAME`: The alias string
- `PM_PROJECT_ID`: Reference to project
- (Other fields via S.ProjectAliases.*)

**Query Pattern** (from grep):
```python
SELECT pa.{S.ProjectAliases.ALIAS_NAME},
       pa.{S.ProjectAliases.PM_PROJECT_ID}
FROM dbo.{S.ProjectAliases.TABLE} pa
LEFT JOIN dbo.{S.Projects.TABLE} p
  ON pa.{S.ProjectAliases.PM_PROJECT_ID} = p.{S.Projects.ID}
ORDER BY p.{S.Projects.NAME}, pa.{S.ProjectAliases.ALIAS_NAME}
```

---

## 4. Health Data Source

### 4.1 Primary Health Database
**Database**: `RevitHealthCheckDB`  
**Tables**: 
- `vw_LatestRvtFiles` (view)
  - Purpose: Provides latest version per logical model key
  - Columns: nId, strRvtFileName, strExtractedProjectName, discipline_full_name, ConvertedExportedDate, pm_project_id, rvt_model_key, etc.
  - Note: Does NOT contain validation_status
  
- `tblRvtProjHealth` (table)
  - Purpose: Health check results per file export
  - Validation columns: validation_status, validation_reason, validated_date
  - Access pattern: LEFT JOIN to vw_LatestRvtFiles on strRvtFileName
  - Deduplication: Use ROW_NUMBER() to select latest per filename

### 4.2 Control Models Source
**Database**: `ProjectManagement`  
**Table**: `ControlModels` (via S.ControlModels.TABLE)  
**Columns**: 
- `ID`
- `CONTROL_FILE_NAME`
- `IS_ACTIVE`
- `PROJECT_ID`

**Query Pattern**:
```python
SELECT {S.ControlModels.ID}, {S.ControlModels.CONTROL_FILE_NAME}, {S.ControlModels.IS_ACTIVE}
FROM ProjectManagement.dbo.{S.ControlModels.TABLE}
WHERE {S.ControlModels.PROJECT_ID} = ?
```

---

## 5. Review Schedule Source

### 5.1 Review Schedule Table
**Database**: `ProjectManagement`  
**Table**: `ReviewSchedule` (via S.ReviewSchedule.TABLE)  
**Purpose**: Determine next review date for freshness calculation  
**Key Columns**:
- `REVIEW_DATE`: The scheduled review date
- `PROJECT_ID`: Reference to project
- (Others via S.ReviewSchedule.*)

### 5.2 Query Pattern (from get_model_register)
```python
SELECT MIN({S.ReviewSchedule.REVIEW_DATE})
FROM ProjectManagement.dbo.{S.ReviewSchedule.TABLE}
WHERE {S.ReviewSchedule.PROJECT_ID} = ?
  AND {S.ReviewSchedule.REVIEW_DATE} > GETDATE()
```

**Purpose**: Find the **nearest future review date** to compute freshness window.

**Freshness Window Logic**:
- If next_review_date exists and is in future:
  - days_until_review = (next_review_date - last_version_date).days
  - Freshness = OUT_OF_DATE (< 0) | DUE_SOON (0-7) | CURRENT (> 7)
- If next_review_date is null or in past:
  - Freshness = UNKNOWN

---

## 6. Summary of Data Dependencies

```
API Request
  ↓
app.py: get_project_quality_register(project_id)
  ↓
database.py: get_model_register(project_id)
  ├─→ ProjectManagement.ControlModels (via S.ControlModels.*)
  │    └─ Purpose: Mark control model flag, determine is_active
  │
  ├─→ ProjectManagement.ReviewSchedule (via S.ReviewSchedule.*)
  │    └─ Purpose: Get next_review_date for freshness calculation
  │
  ├─→ RevitHealthCheckDB.vw_LatestRvtFiles
  │    └─ Base dataset: Latest files per logical model key
  │
  └─→ RevitHealthCheckDB.tblRvtProjHealth (LEFT JOIN)
       └─ Validation data: status, reason, validated_date
```

---

## 7. Current State Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| Quality Register Endpoint | ✅ WORKING | Returns paginated results with Phase B deduplication |
| Alias Service Integration | ✅ IN PLACE | ProjectAliasManager integrated; routes defined |
| Health Data Source | ✅ OPERATIONAL | vw_LatestRvtFiles provides latest models |
| Control Models | ✅ QUERYABLE | ControlModels table accessible via schema constants |
| Review Schedule | ✅ QUERYABLE | ReviewSchedule provides next_review_date |
| Validation Data | ✅ AVAILABLE | tblRvtProjHealth contains validation_status, linked via LEFT JOIN |
| Phase B Deduplication | ✅ IMPLEMENTED | Normalize model names; keep latest per canonical key |
| ExpectedModels Table | ❌ NOT CREATED | Deferred to Phase 1 (Blueprint for never-empty register) |

---

## 8. Known Limitations & Deferred Items

1. **Phase C: Service Mapping**
   - `primaryServiceId` currently NULL in all rows
   - Mapping logic deferred pending service scoping
   - Blueprint in QUALITY_REGISTER_DIAGNOSIS.md (line 260)

2. **Phase D: ExpectedModels Alignment**
   - ExpectedModels table not yet created
   - Will enable "never-empty" register (show missing expected models)
   - Requires schema migration + seed data from observed models

3. **Current Architecture Constraint**
   - Register shows only observed models (from vw_LatestRvtFiles)
   - Missing expected-but-not-observed models invisible
   - Solution: Create ExpectedModels table (Phase 1+)

---

## Audit Sign-Off

✅ **Endpoint**: GET /api/projects/<id>/quality/register fully documented  
✅ **Handler**: get_project_quality_register() integrates with database layer  
✅ **Database**: get_model_register() implements Phase A & B fixes  
✅ **Alias Routes**: ProjectAliasManager service available  
✅ **Health Data**: vw_LatestRvtFiles + tblRvtProjHealth accessible  
✅ **Review Schedule**: ReviewSchedule table queryable for freshness computation  
✅ **Control Models**: ControlModels table marks control files  

**Ready for Phase 1 Implementation**: ExpectedModels table blueprint available in QUALITY_REGISTER_DIAGNOSIS.md
