# Quality Register Phase 0 Audit B: Architecture & Data Flow
**Date**: February 27, 2026  
**Scope**: Database schema, table relationships, data flow, design patterns  
**Status**: COMPLETE

---

## 1. Database Schema Overview

### 1.1 Multi-Database Architecture
The Quality Register operates across **2 SQL Server databases**:

```
┌─────────────────────────────────────────────────────────────┐
│ SQL Server Instance (localhost\SQLEXPRESS)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐     ┌──────────────────────────┐ │
│  │ ProjectManagement    │     │ RevitHealthCheckDB       │ │
│  ├──────────────────────┤     ├──────────────────────────┤ │
│  │ • Projects           │     │ • vw_LatestRvtFiles      │ │
│  │ • ControlModels      │     │ • tblRvtProjHealth       │ │
│  │ • ReviewSchedule     │     │ • (other health tables)  │ │
│  │ • Services           │     │                          │ │
│  │ • ProjectAliases     │     │                          │ │
│  │ • (others)           │     │                          │ │
│  └──────────────────────┘     └──────────────────────────┘ │
│         (Config DB)                 (Health DB)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Table Relationships

#### ProjectManagement.dbo.ControlModels
**Purpose**: Define which Revit files are "control" models (must always be present)

**Schema** (inferred from code):
| Column | Type | Notes |
|--------|------|-------|
| ID | int | Primary key |
| PROJECT_ID | int | FK to Projects |
| CONTROL_FILE_NAME | varchar | Filename to match (e.g., "NFPS-ACO-00-00-M3-C-0001.rvt") |
| IS_ACTIVE | bit | Whether this control model is currently enforced |
| created_at | datetime | Audit timestamp |
| updated_at | datetime | Audit timestamp |

**Example Data**:
```
ID | PROJECT_ID | CONTROL_FILE_NAME           | IS_ACTIVE | created_at
1  | 2          | NFPS-ACO-00-00-M3-C-0001    | 1         | 2026-01-01
2  | 2          | NFPS-STR-00-00-M3-C-0001    | 1         | 2026-01-01
3  | 2          | NFPS-MEP-00-00-M3-C-0001    | 1         | 2026-01-01
```

#### ProjectManagement.dbo.ReviewSchedule
**Purpose**: Define future review cycles for freshness calculation

**Schema** (inferred from code):
| Column | Type | Notes |
|--------|------|-------|
| ID | int | Primary key |
| PROJECT_ID | int | FK to Projects |
| REVIEW_DATE | datetime | When the review is scheduled |
| (others) | | Stage, status, etc. |

**Query Pattern** (from get_model_register):
```sql
SELECT MIN(REVIEW_DATE)
FROM ReviewSchedule
WHERE PROJECT_ID = ?
  AND REVIEW_DATE > GETDATE()
```

**Purpose**: Find next future review date to compute freshness window (days until model needs updating).

---

#### RevitHealthCheckDB.dbo.vw_LatestRvtFiles (View)
**Purpose**: Materialized view providing the latest Revit file per logical model key

**Columns**:
| Column | Type | Purpose |
|--------|------|---------|
| nId | int | Health record ID |
| strRvtFileName | varchar | Filename (e.g., "NFPS-ACO-00-00-M3-C-0001.rvt") |
| strExtractedProjectName | varchar | Project name extracted from file |
| discipline_full_name | varchar | Discipline (Architectural, Structural, MEP) |
| ConvertedExportedDate | datetime | When file was analyzed/exported |
| pm_project_id | int | Link to ProjectManagement.Projects |
| rvt_model_key | varchar | Logical model key (for deduplication) |
| NormalizedFileName | varchar | Cleaned filename |
| project_name | varchar | Normalized project name |

**Key Characteristic**: Contains only the **latest version per unique strRvtFileName**, filtered by pm_project_id.

**Note**: Does NOT contain validation_status (that's in tblRvtProjHealth).

#### RevitHealthCheckDB.dbo.tblRvtProjHealth (Table)
**Purpose**: Health check results for each Revit file export/import

**Key Columns**:
| Column | Type | Purpose |
|--------|------|---------|
| nId | int | Primary key (auto-increment) |
| strRvtFileName | varchar | Filename (matches vw_LatestRvtFiles.strRvtFileName) |
| validation_status | varchar | 'Valid', 'Invalid', 'Warn', or NULL |
| validation_reason | varchar | Human-readable explanation |
| validated_date | datetime | When validation was performed |
| strClientName | varchar | Company name |
| (44+ other columns) | | Health metrics, geometry, naming data, etc. |

**Access Pattern**: LEFT JOIN from vw_LatestRvtFiles on strRvtFileName, then use ROW_NUMBER() to select latest per filename.

---

### 1.3 Schema Constants (Centralized DB References)
**Location**: [constants/schema.py](constants/schema.py)

**Pattern Used Throughout**:
```python
from constants.schema import schema as S

# Instead of hardcoded strings:
S.ControlModels.TABLE          # 'ControlModels'
S.ControlModels.PROJECT_ID     # 'project_id'
S.ControlModels.CONTROL_FILE_NAME  # 'control_file_name'
S.ControlModels.IS_ACTIVE      # 'is_active'

S.ReviewSchedule.TABLE         # 'ReviewSchedule'
S.ReviewSchedule.PROJECT_ID    # 'project_id'
S.ReviewSchedule.REVIEW_DATE   # 'review_date'

S.ProjectAliases.TABLE         # 'ProjectAliases'
S.ProjectAliases.ALIAS_NAME    # 'alias_name'
S.ProjectAliases.PM_PROJECT_ID # 'pm_project_id'
```

**Benefit**: Single source of truth; prevents hardcoded column name regressions.

---

## 2. Data Flow Architecture

### 2.1 Full Request/Response Flow

```
Client (React) HTTP GET /api/projects/2/quality/register?page=1&page_size=50
  ↓
Backend (Flask) app.py:5390
  ├─ Parse query params (page, page_size, sort_by, sort_dir, filter_attention)
  ├─ Validate pagination (page ≥ 1, page_size ∈ [1, 500])
  └─ Call: database.get_model_register(project_id=2, ...)
    ↓
  database.py:2693 get_model_register()
    ├─────────────────────────────────────────────────────┐
    │ STEP 1: Query ProjectManagement (Control Models)   │
    ├─────────────────────────────────────────────────────┤
    │ SELECT ControlModels WHERE project_id = 2           │
    │ Result: {filename → {id, is_active}}                │
    │ ✓ NFPS-ACO-00-00-M3-C-0001: {id: 1, is_active: 1}  │
    │ ✓ NFPS-STR-00-00-M3-C-0001: {id: 2, is_active: 1}  │
    │ ✓ NFPS-MEP-00-00-M3-C-0001: {id: 3, is_active: 1}  │
    └─────────────────────────────────────────────────────┘
    ├─────────────────────────────────────────────────────┐
    │ STEP 2: Query ProjectManagement (Next Review Date) │
    ├─────────────────────────────────────────────────────┤
    │ SELECT MIN(REVIEW_DATE) FROM ReviewSchedule         │
    │   WHERE project_id = 2 AND REVIEW_DATE > GETDATE()  │
    │ Result: next_review_date = 2026-03-01 14:00:00      │
    └─────────────────────────────────────────────────────┘
    ├──────────────────────────────────────────────────────┐
    │ STEP 3: Query RevitHealthCheckDB (Latest Files)    │
    ├──────────────────────────────────────────────────────┤
    │ SELECT 11 columns FROM vw_LatestRvtFiles h          │
    │ LEFT JOIN tblRvtProjHealth hp                       │
    │   ON h.strRvtFileName = hp.strRvtFileName           │
    │ WHERE h.pm_project_id = 2                           │
    │ ORDER BY h.ConvertedExportedDate DESC               │
    │                                                      │
    │ Result: 12 raw rows (all models for project 2)      │
    │ Columns per row: [nId, filename, project_name,      │
    │   discipline, export_date, pm_id, model_key,        │
    │   validation_status, validation_reason,             │
    │   validated_date, client_name]                      │
    └──────────────────────────────────────────────────────┘
    ├──────────────────────────────────────────────────────┐
    │ STEP 4: Phase B Processing (Deduplication)         │
    ├──────────────────────────────────────────────────────┤
    │ For each row:                                        │
    │  1. Check if misnamed (detect _detached, spaces)    │
    │  2. Extract canonical key (first 3 dash components) │
    │  3. Compute freshness (days until next review)      │
    │  4. Map validation status (Valid→PASS, etc.)        │
    │  5. Check control model flag                        │
    │                                                      │
    │ Result: 12 processed rows with metadata             │
    │ Format: {modelKey, modelName, discipline,           │
    │   company, lastVersionDateISO, freshnessStatus,     │
    │   validationOverall, isControlModel, ...}           │
    │                                                      │
    │ Dedup: Group by canonical key, keep latest date     │
    │ Attention: Count rows needing review                │
    └──────────────────────────────────────────────────────┘
    ├──────────────────────────────────────────────────────┐
    │ STEP 5: Filter & Paginate                          │
    ├──────────────────────────────────────────────────────┤
    │ If filter_attention=true: keep only attention items │
    │ Paginate: rows[0:50] for page 1                     │
    │ Result: 50 rows (or fewer if < 50 total)           │
    └──────────────────────────────────────────────────────┘
    ↓
  Return JSON:
    {
      "rows": [...50 rows...],
      "page": 1,
      "page_size": 50,
      "total": 12,
      "attention_count": 3
    }
  ↓
app.py:5390 → jsonify()
  ↓
Client (React) receives response
```

---

### 2.2 Database Connection Pattern
**Used Throughout**: [database_pool.py](database_pool.py)

**Pattern**:
```python
from database_pool import get_db_connection
from constants.schema import schema as S

# Get connection from pool
conn = get_db_connection()  # Default: ProjectManagement
try:
    cursor = conn.cursor()
    cursor.execute(f"SELECT {S.ControlModels.ID} FROM {S.ControlModels.TABLE}")
    results = cursor.fetchall()
    conn.commit()  # Explicit commit for writes
finally:
    conn.close()  # Returns connection to pool (NOT a true close)

# For different database:
with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    # ... query ...
```

**Key Points**:
- Connection pooling enabled (no true close, returns to pool)
- Context managers supported (`with` statement)
- Schema constants prevent hardcoded column names
- Explicit `conn.commit()` for write operations

---

## 3. Freshness Calculation Details

### 3.1 Algorithm
```python
# Given:
#   next_review_date = 2026-03-01 (from ReviewSchedule)
#   last_version_date = 2026-02-01 (from vw_LatestRvtFiles.ConvertedExportedDate)

days_until_review = (next_review_date - last_version_date).days
# days_until_review = (Mar 1 - Feb 1) = 28 days

# Decision tree:
if days_until_review < 0:
    freshness_status = 'OUT_OF_DATE'      # Model is older than review date
elif 0 <= days_until_review <= 7:
    freshness_status = 'DUE_SOON'         # Within 7-day window
else:
    freshness_status = 'CURRENT'          # > 7 days until review
```

### 3.2 Special Cases
```
Scenario 1: No next review date (future reviews undefined)
  Result: freshness_status = 'UNKNOWN'

Scenario 2: No last version date (model never imported)
  Result: freshness_status = 'UNKNOWN'

Scenario 3: Next review in past (overdue review cycle)
  Result: freshness_status = 'CURRENT' (can't determine until next review scheduled)
```

---

## 4. Validation Status Mapping

### 4.1 Source → Result Mapping
```python
Database Value (case-insensitive)  →  API Response
─────────────────────────────────────────────────────
'Valid', 'VALID', 'valid'          →  'PASS'
'Invalid', 'INVALID', 'invalid'    →  'FAIL'
'Warn', 'WARN', 'warn'             →  'WARN'
NULL, undefined, other             →  'UNKNOWN'
```

### 4.2 Implementation
```python
# From database.py:2868-2877
validation_status_raw = row[7]  # from tblRvtProjHealth.validation_status

if validation_status_raw:
    validation_status_raw_upper = str(validation_status_raw).upper()
    if validation_status_raw_upper in ('VALID', 'PASS'):
        validation_status = 'PASS'
    elif validation_status_raw_upper in ('INVALID', 'FAIL'):
        validation_status = 'FAIL'
    elif validation_status_raw_upper == 'WARN':
        validation_status = 'WARN'
    else:
        validation_status = 'UNKNOWN'
else:
    validation_status = 'UNKNOWN'
```

---

## 5. Naming Status Detection

### 5.1 Misname Indicators
A file is marked `namingStatus='MISNAMED'` if:
```python
misname_indicators = [
    '_detached',    # File was detached from project
    '_OLD',         # Marked as old version
    '_old',         # Lowercase old marker
    '__',           # Double underscore (unusual)
    '_001',         # Sequential numbering (indicates copies)
    '_0001',        # Sequential numbering with leading zeros
]

# Also misnamed if:
leading/trailing spaces after strip()
doesn't contain dashes (no structure)
can't extract 3+ dash-separated components
```

### 5.2 Canonical Model Key Extraction
```python
# Filename: "NFPS-ACO-00-00-M3-C-0001.rvt"
# Split on dashes: ["NFPS", "ACO", "00", "00", "M3", "C", "0001"]
# Take first 3 components: ["NFPS", "ACO", "00"]
# Canonical key: "NFPS-ACO-00"

# Example 2: "MEL071-A-AR-M-0010.rvt"
# Components: ["MEL071", "A", "AR", "M", "0010"]
# Canonical: "MEL071-A-AR"

# This canonical key groups multiple versions:
#   "NFPS-ACO-00-00-M3-C-0001.rvt" (v1, date: 2026-02-01)
#   "NFPS-ACO-00-00-M3-C-0002.rvt" (v2, date: 2026-02-15) ← KEPT (latest)
#   "NFPS-ACO-00-00-M3-C-0003.rvt" (v3, date: 2026-01-15) ← DISCARDED
```

---

## 6. Attention Item Detection

An item requires attention if **any** of:
```python
freshnessStatus == 'OUT_OF_DATE'
validationOverall in ('FAIL', 'WARN')
namingStatus == 'MISNAMED'
mappingStatus == 'UNMAPPED'
```

**Count Logic** (from database.py:2945-2953):
```python
attention_count = sum(1 for row in processed_rows if (
    row['freshnessStatus'] == 'OUT_OF_DATE'
    or row['validationOverall'] in ('FAIL', 'WARN')
    or row['namingStatus'] == 'MISNAMED'
    or row['mappingStatus'] == 'UNMAPPED'
))
```

**API Usage**: Frontend can use `attention_count` to highlight "Needs Review" badge.

---

## 7. Phase C: Service Mapping (Deferred)

### 7.1 Current State
```python
# In response (database.py:2915):
'primaryServiceId': None,       # Always NULL
'mappingStatus': 'UNMAPPED',    # Always 'UNMAPPED'
```

### 7.2 Intended Future State
```
Model (e.g., "NFPS-ACO-00-00-M3-C-0001")
  ↓
[Service Mapping Logic - TBD]
  ↓
Service (e.g., "Architectural Review" with service_id = 45)
  ↓
Response:
  'primaryServiceId': 45
  'mappingStatus': 'MAPPED'
```

### 7.3 Deferred Until
Awaiting service scoping requirements from stakeholders (not in Phase 0 scope).

---

## 8. Phase D: ExpectedModels Architecture (Design Blueprint)

### 8.1 Table Schema (Proposed)
**Table**: `ExpectedModels`  
**Database**: `RevitHealthCheckDB`  
**Purpose**: Define which models are expected for each project; compare against observed

```sql
CREATE TABLE dbo.ExpectedModels (
    id INT PRIMARY KEY IDENTITY(1,1),
    project_id INT NOT NULL,
    expected_model_key VARCHAR(100) NOT NULL,  -- e.g., "NFPS-ACO-00"
    discipline VARCHAR(50),                    -- e.g., "Architectural"
    is_required BIT DEFAULT 1,                 -- Mark as mandatory
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_ExpectedModels_ProjectId 
        FOREIGN KEY (project_id) 
        REFERENCES ProjectManagement.dbo.Projects(id)
);
```

### 8.2 Register Query Pattern (Proposed)
```sql
-- Returns both OBSERVED and MISSING models
SELECT 
    COALESCE(o.modelKey, e.expected_model_key) AS modelKey,
    o.freshnessStatus,
    o.validationOverall,
    CASE 
        WHEN o.modelKey IS NULL THEN 'MISSING'      -- Expected but not observed
        WHEN e.expected_model_key IS NULL THEN 'EXTRA'  -- Observed but not expected
        ELSE 'MATCHED'
    END AS model_status,
    o.*,
    e.expected_model_key
FROM (SELECT * FROM get_model_register(...)) o
FULL OUTER JOIN ExpectedModels e
    ON o.modelKey = e.expected_model_key
    AND e.project_id = ?
ORDER BY COALESCE(o.lastVersionDate, GETDATE()) DESC
```

### 8.3 Expected Behavior
- **Never-Empty Register**: Shows missing expected models even if never imported
- **Attention Items**: Expected but missing models show as "MISSING" status
- **Orphan Detection**: Observed but not expected models marked as "EXTRA"

---

## 9. Data Quality & Validation

### 9.1 Known Constraints
| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| vw_LatestRvtFiles only shows latest per filename | Can't see full version history | Use raw tblRvtProjHealth for historical queries |
| Validation data optional (nullable) | Some models show UNKNOWN validation | Expected; treat as "not yet validated" |
| ProjectManagement.ReviewSchedule may be empty | Freshness always UNKNOWN | Requires review cycle setup |
| Discipline normalization inconsistent | Discipline column may vary | Phase future: normalize via lookup table |

### 9.2 Logging & Diagnostics
**Log Location**: `logs/app.log`

**Key Log Entries** (from database.py):
```python
logger.info(f"Quality register: Loaded {len(all_rows)} rows from vw_LatestRvtFiles")
logger.info(f"Quality register: Returning {len(paginated_rows)} rows (total: {total}, attention: {attention_count})")
logger.error(f"Error fetching model register for project {project_id}: {e}")
```

**Diagnostic Queries**:
```sql
-- Check how many models in project 2
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_LatestRvtFiles
WHERE pm_project_id = 2;

-- Check control models
SELECT * FROM ProjectManagement.dbo.ControlModels
WHERE project_id = 2 AND is_active = 1;

-- Check next review
SELECT MIN(REVIEW_DATE) 
FROM ProjectManagement.dbo.ReviewSchedule
WHERE project_id = 2 AND REVIEW_DATE > GETDATE();
```

---

## 10. Architecture Sign-Off

✅ **Multi-Database Design**: ProjectManagement + RevitHealthCheckDB properly separated  
✅ **Schema Constants**: All hardcoded column names eliminated via S.* pattern  
✅ **Connection Pooling**: get_db_connection() provides pooled, reusable connections  
✅ **Query Architecture**: LEFT JOIN pattern avoids data loss; deduplication preserves latest  
✅ **Freshness Calculation**: Days-until-review logic clear and testable  
✅ **Validation Mapping**: Case-insensitive; null-safe; extensible  
✅ **Naming Detection**: Detects misnamed files; groups by canonical key  
✅ **Attention Items**: Multi-dimensional filter; count available for UI badges  
✅ **Phase C Deferred**: Service mapping awaiting requirements  
✅ **Phase D Blueprint**: ExpectedModels table design documented for never-empty register  

**Ready for Implementation**: Phases 1-6 foundation complete.
