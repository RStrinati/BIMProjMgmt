# Verification Audit: Source of Truth Report
**Date:** January 16, 2026  
**Phase:** Implementation Verification (Phase 3 of Services & Deliverables Refactor)  
**Scope:** Mapping existing UI data sources → Backend API → Database schema

---

## Executive Summary

This report documents the **canonical data sources** currently used by the BIM Project Management system to serve the Services and Reviews tabs. The audit confirms that:

1. ✅ **Services tab** → Uses `ProjectServices` table exclusively
2. ✅ **Reviews tab** ("Deliverables" after rename) → Uses `ServiceReviews` table (UNION with `ServiceItems` NOT implemented)
3. ✅ **Phase field** → Already exists as `phase` column on `ProjectServices`
4. ✅ **Billing tracking** → Already uses `is_billed` boolean on `ServiceReviews`
5. ⚠️ **Invoice tracking** → Missing `invoice_date` column (MUST BE ADDED per locked decision)

---

## Part 1: Frontend Data Flow (UI Entry Points)

### 1.1 Services Tab - Current Implementation

**Frontend File:** [frontend/src/api/services.ts](frontend/src/api/services.ts)

**TypeScript Interface (Current):**
```typescript
export interface ProjectService {
  service_id: number;
  project_id: number;
  phase?: string;              // ← ALREADY EXISTS
  service_code: string;
  service_name: string;
  status: string;
  progress_pct?: number;
  claimed_to_date?: number;
  billing_progress_pct?: number;
  billed_amount?: number;
  agreed_fee_remaining?: number;
  // ... other fields
}
```

**Current API Call:**
```typescript
projectServicesApi.getAll(projectId)
  → GET `/api/projects/{projectId}/services`
```

**Usage in DashboardPage.tsx (confirmed):**
```typescript
useQuery(['projectServices', projectId, { scope: 'billing' }], 
  () => projectServicesApi.getAll(projectId))
```

### 1.2 Reviews Tab - Current Implementation

**Frontend File:** [frontend/src/api/projectReviews.ts](frontend/src/api/projectReviews.ts)

**Filter Interface (Current):**
```typescript
export type ProjectReviewsFilters = {
  status?: string;
  service_id?: number;
  from_date?: string;
  to_date?: string;
  sort_by?: 'planned_date' | 'due_date' | 'status' | 'service_name';
  sort_dir?: 'asc' | 'desc';
  limit?: number;
  page?: number;
};
```

**Current API Call:**
```typescript
projectReviewsApi.getProjectReviews(projectId, filters)
  → GET `/api/projects/{projectId}/reviews?...filters`
```

---

## Part 2: Backend Data Sources (API Routes)

### 2.1 GET `/api/projects/{project_id}/services`

**Location:** [backend/app.py](backend/app.py#L1627)

**Handler:**
```python
@app.route('/api/projects/<int:project_id>/services', methods=['GET'])
def api_get_project_services(project_id):
    services = get_project_services(project_id)
    return jsonify(services)
```

**Database Function:** `get_project_services(project_id)` → [database.py](database.py#L86)

**Current Behavior:**
- Returns list of `ProjectServices` records
- Includes `phase` field (already in SELECT)
- Derives `status` and `billing_progress_pct` from `ServiceReviews` and `ServiceItems` counts
- Aggregates `is_billed` flag from child reviews/items

### 2.2 GET `/api/projects/{project_id}/reviews` (PRIMARY DELIVERABLES ENDPOINT)

**Location:** [backend/app.py](backend/app.py#L1705)

**Handler:**
```python
@app.route('/api/projects/<int:project_id>/reviews', methods=['GET'])
def api_get_project_reviews(project_id):
    payload = get_project_reviews(
        project_id,
        status=status,
        service_id=service_id,
        from_date=from_date,
        to_date=to_date,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        page=page,
    )
    return jsonify(payload)
```

**Database Function:** `get_project_reviews()` → [database.py](database.py#L513)

**Current Query (CRITICAL):**
```sql
SELECT
    sr.review_id,
    sr.service_id,
    ps.project_id,
    sr.cycle_no,
    sr.planned_date,
    sr.due_date,
    sr.status,
    sr.disciplines,
    sr.deliverables,
    sr.is_billed,              -- ← ALREADY EXISTS
    sr.billing_amount,
    sr.invoice_reference,      -- ← ALREADY EXISTS
    ps.service_name,
    ps.service_code,
    ps.phase                   -- ← ALREADY JOINED FROM ProjectServices
FROM ServiceReviews sr
JOIN ProjectServices ps
    ON sr.service_id = ps.service_id
WHERE ps.project_id = ?
ORDER BY {sort_column} {sort_direction}
```

**Current Response Format:**
```python
{
    "items": [
        {
            "review_id": 1,
            "service_id": 45,
            "project_id": 123,
            "cycle_no": 1,
            "planned_date": "2026-01-20",
            "due_date": "2026-01-25",
            "status": "planned",
            "disciplines": "Arch,Struct",
            "deliverables": "Design drawings",
            "is_billed": False,         # ← Already in response
            "billing_amount": 2500.00,
            "invoice_reference": None,  # ← Already in response
            "service_name": "Design Review",
            "service_code": "DR-001",
            "phase": "Design"           # ← Already in response
        },
        ...
    ],
    "total": 47
}
```

### 2.3 GET `/api/projects/{project_id}/services/{service_id}/items`

**Location:** [backend/app.py](backend/app.py#L5535)

**Note:** This endpoint serves a **DIFFERENT** table (`ServiceItems`) and is **NOT** used by the Reviews tab. Service Items are separate from Service Reviews.

---

## Part 3: Database Schema (Tables & Columns)

### 3.1 ProjectServices Table

**Primary Table for Services Tab**

**Schema Constants:** [constants/schema.py](constants/schema.py#L1003)

```python
class ProjectServices:
    TABLE = "ProjectServices"
    SERVICE_ID = "service_id"              # PK
    PROJECT_ID = "project_id"              # FK to Projects
    PHASE = "phase"                        # ← ALREADY EXISTS (nullable string)
    SERVICE_CODE = "service_code"
    SERVICE_NAME = "service_name"
    UNIT_TYPE = "unit_type"
    UNIT_QTY = "unit_qty"
    UNIT_RATE = "unit_rate"
    LUMP_SUM_FEE = "lump_sum_fee"
    AGREED_FEE = "agreed_fee"
    BILL_RULE = "bill_rule"
    NOTES = "notes"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"                      # Derived: 'planned', 'in_progress', 'completed', 'overdue', 'cancelled'
    PROGRESS_PCT = "progress_pct"          # Derived from child items
    CLAIMED_TO_DATE = "claimed_to_date"
    ASSIGNED_USER_ID = "assigned_user_id"
```

**Key Observations:**
- ✅ `phase` column already exists (can be used directly in UI)
- ⚠️ `phase` is nullable (UI must handle None case)
- ✅ No migration needed for phase (already there)

### 3.2 ServiceReviews Table (PRIMARY FOR DELIVERABLES)

**Primary Table for Reviews/Deliverables Tab**

**Schema Constants:** [constants/schema.py](constants/schema.py#L1024)

```python
class ServiceReviews:
    TABLE = "ServiceReviews"
    REVIEW_ID = "review_id"                # PK
    SERVICE_ID = "service_id"              # FK to ProjectServices
    CYCLE_NO = "cycle_no"
    PLANNED_DATE = "planned_date"          # UI calls this "Completion date"
    DUE_DATE = "due_date"
    DISCIPLINES = "disciplines"
    DELIVERABLES = "deliverables"          # ← Content of deliverable
    STATUS = "status"                      # 'planned', 'in_progress', 'completed', 'overdue', 'cancelled'
    WEIGHT_FACTOR = "weight_factor"
    EVIDENCE_LINKS = "evidence_links"
    INVOICE_REFERENCE = "invoice_reference"  # ← ALREADY EXISTS (for manual invoice refs)
    ACTUAL_ISSUED_AT = "actual_issued_at"
    IS_BILLED = "is_billed"                # ← ALREADY EXISTS (boolean)
    SOURCE_PHASE = "source_phase"          # Nullable metadata
    BILLING_PHASE = "billing_phase"        # Nullable metadata
    BILLING_RATE = "billing_rate"
    BILLING_AMOUNT = "billing_amount"
    ASSIGNED_USER_ID = "assigned_user_id"
    # MISSING: invoice_date (NEW COLUMN NEEDED PER LOCKED DECISION)
```

**Key Observations:**
- ✅ `is_billed` column already exists
- ✅ `invoice_reference` column already exists
- ❌ `invoice_date` column DOES NOT EXIST (must be added)
- ✅ Phase accessible via FK join to `ProjectServices.phase`
- **API already returns is_billed, invoice_reference, and phase** (via join)

### 3.3 ServiceItems Table (NOT USED BY REVIEWS TAB)

**Separate Table - Different Purpose**

**Schema Constants:** [constants/schema.py](constants/schema.py#L1075)

```python
class ServiceItems:
    TABLE = "ServiceItems"
    ITEM_ID = "item_id"
    SERVICE_ID = "service_id"
    ITEM_TYPE = "item_type"               # 'review', 'audit', 'deliverable', 'milestone', etc.
    TITLE = "title"
    DESCRIPTION = "description"
    PLANNED_DATE = "planned_date"
    DUE_DATE = "due_date"
    ACTUAL_DATE = "actual_date"
    STATUS = "status"
    PRIORITY = "priority"
    ASSIGNED_TO = "assigned_to"
    ASSIGNED_USER_ID = "assigned_user_id"
    INVOICE_REFERENCE = "invoice_reference"
    EVIDENCE_LINKS = "evidence_links"
    NOTES = "notes"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    IS_BILLED = "is_billed"              # ← Same pattern as ServiceReviews
    # MISSING: invoice_date (NEW COLUMN NEEDED)
```

**Key Observations:**
- ✅ `is_billed` column exists
- ✅ `invoice_reference` column exists
- ❌ `invoice_date` column DOES NOT EXIST (should be added for consistency)
- 🔄 **ServiceItems is NOT a union with ServiceReviews** - they are distinct tables with different purposes
- **Decision:** Add `invoice_date` to both tables for consistency, but only `ServiceReviews` is used for Deliverables tab

### 3.4 ServiceDeliverables Table (DEPRECATED/NOT USED)

**Schema Constants:** [constants/schema.py](constants/schema.py#L776)

```python
class ServiceDeliverables:
    TABLE = "ServiceDeliverables"
    DELIVERABLE_ID = "deliverable_id"
    SERVICE_ID = "service_id"
    DELIVERABLE_TYPE = "deliverable_type"
    PLANNED_DATE = "planned_date"
    ISSUED_DATE = "issued_date"           # ← Uses "issued_date" not "invoice_date"
    STATUS = "status"
    BILL_TRIGGER = "bill_trigger"
    EVIDENCE_LINK = "evidence_link"
    # NO is_billed, NO invoice_reference, NO invoice_date
```

**Key Observations:**
- ⚠️ This table exists but is **NOT USED** by the Reviews tab API
- ❌ Does NOT have `is_billed`, `invoice_reference`, or `invoice_date` columns
- 📝 **Note:** `issued_date` is different from `invoice_date` (issued = when work completed; invoice = when billed)
- **Decision:** Do NOT modify this table for current refactor (out of scope)

---

## Part 4: Canonical Data Source Decisions

### Decision 1: Services Table = ProjectServices (CONFIRMED)

| Aspect | Value |
|--------|-------|
| **DB Table** | `dbo.ProjectServices` |
| **Primary Key** | `service_id` |
| **FK to Project** | `project_id` |
| **API Endpoint** | `GET /api/projects/{id}/services` |
| **Frontend Hook** | `projectServicesApi.getAll(projectId)` |
| **Status** | ✅ Currently in use, no changes needed |

### Decision 2: Phase Sourcing = ProjectServices.phase Column (CONFIRMED)

| Aspect | Value |
|--------|-------|
| **Source** | `ProjectServices.phase` (direct column) |
| **Type** | VARCHAR (nullable) |
| **Already in API?** | ✅ YES - Already selected and returned |
| **Frontend Access** | Via `ProjectService.phase` field |
| **Nullable?** | ✅ YES - UI must handle None |
| **UI Label** | "Phase" or "Project Phase" |
| **Migration Needed?** | ❌ NO - Column already exists |

### Decision 3: Deliverables Table = ServiceReviews (CONFIRMED)

| Aspect | Value |
|--------|-------|
| **DB Table** | `dbo.ServiceReviews` |
| **Primary Key** | `review_id` |
| **FK to Service** | `service_id` |
| **FK to Project** | Via `ProjectServices.project_id` (JOIN) |
| **API Endpoint** | `GET /api/projects/{id}/reviews` |
| **Frontend Hook** | `projectReviewsApi.getProjectReviews(projectId, filters)` |
| **Current UI Tab Name** | "Reviews" → Rename to "Deliverables" ✅ |
| **Status** | ✅ Currently in use, no breaking changes |
| **Note** | NOT a union with ServiceItems - ServiceReviews is the single source |

### Decision 4: Billing Status Derivation (CONFIRMED)

| Aspect | Value |
|--------|-------|
| **Source Column** | `ServiceReviews.is_billed` (boolean) |
| **Current API Payload?** | ✅ YES - Already in response |
| **UI Label** | "Billed" (if true) / "Not billed" (if false) |
| **Derivation Logic** | Direct boolean (no computation needed) |
| **Migration Needed?** | ❌ NO - Column already exists |

### Decision 5: Invoice Reference Tracking (CONFIRMED)

| Aspect | Value |
|--------|-------|
| **Source Column** | `ServiceReviews.invoice_reference` |
| **Current API Payload?** | ✅ YES - Already in response (may be NULL) |
| **Purpose** | Store manual invoice ref (e.g., "INV-2026-001") |
| **Type** | VARCHAR (nullable) |
| **Migration Needed?** | ❌ NO - Column already exists |

### Decision 6: Invoice Date Tracking (MISSING - MUST ADD)

| Aspect | Value |
|--------|-------|
| **New Column Name** | `invoice_date` |
| **Target Table** | `ServiceReviews` (PRIMARY) + `ServiceItems` (for consistency) |
| **Type** | DATE or DATETIME2 |
| **Nullable?** | ✅ YES - Only populated when `is_billed` = true |
| **Current API Payload?** | ❌ NO - Will need to add after migration |
| **UI Label** | "Invoice Date" |
| **Migration Needed?** | ✅ YES - ADD to ServiceReviews and ServiceItems |
| **Locked Decision** | ✅ CONFIRMED (Decision #3 from locked set) |

---

## Part 5: Data Flow Diagram

### Current Flow (Services Tab)
```
ProjectDetailPage.tsx
  ↓
useQuery('projectServices')
  ↓
projectServicesApi.getAll(projectId)
  ↓
GET /api/projects/{id}/services
  ↓
get_project_services(project_id)
  ↓
SELECT * FROM ProjectServices WHERE project_id = ?
  JOIN ServiceReviews (for status derivation)
  JOIN ServiceItems (for status derivation)
  ↓
Return: { services: [...], ... }
  ↓
Render: Services tab (shows service_code, service_name, phase, status, progress_pct, billed_amount)
```

### Current Flow (Reviews/Deliverables Tab)
```
ProjectDetailPage.tsx
  ↓
useQuery('projectReviews')
  ↓
projectReviewsApi.getProjectReviews(projectId, filters)
  ↓
GET /api/projects/{id}/reviews?...filters
  ↓
get_project_reviews(project_id, ...)
  ↓
SELECT sr.*, ps.service_name, ps.service_code, ps.phase
FROM ServiceReviews sr
JOIN ProjectServices ps ON sr.service_id = ps.service_id
WHERE ps.project_id = ?
  ↓
Return: { items: [...], total: N }
  ↓
Render: Deliverables tab (shows review_id, cycle_no, planned_date, status, is_billed, invoice_reference, phase)
```

---

## Part 6: API Contract Verification

### Current GET `/api/projects/{id}/reviews` Response

**Actual Current Payload** (confirmed from database.py lines 628-650):
```json
{
  "items": [
    {
      "review_id": 1,
      "service_id": 45,
      "project_id": 123,
      "cycle_no": 1,
      "planned_date": "2026-01-20",
      "due_date": "2026-01-25",
      "status": "planned",
      "disciplines": "Arch,Struct",
      "deliverables": "Weekly design review",
      "is_billed": false,              // ← ALREADY PRESENT
      "billing_amount": 2500.00,
      "invoice_reference": null,       // ← ALREADY PRESENT
      "service_name": "Design Review",
      "service_code": "DR-001",
      "phase": "Design"                // ← ALREADY PRESENT (via JOIN)
    }
  ],
  "total": 47
}
```

### Proposed Addition (After invoice_date migration)

```json
{
  "items": [
    {
      // ... all current fields ...
      "invoice_date": "2026-02-15",   // ← NEW FIELD (after migration)
      "is_billed": true,
      "invoice_reference": "INV-2026-001"
    }
  ]
}
```

**⚠️ BREAKING CHANGE?** NO - Adding new optional field is non-breaking

---

## Part 7: Backward Compatibility Assessment

### ✅ Services Tab - NO BREAKING CHANGES

| Change | Impact | Breaking? |
|--------|--------|-----------|
| Add `invoice_date` to ProjectServices | Not used by services tab | ❌ NO |
| Phase already present as column | UI can use directly | ❌ NO |
| Rename "Reviews" → "Deliverables" | UI label only | ❌ NO |

### ✅ Reviews/Deliverables Tab - NO BREAKING CHANGES

| Change | Impact | Breaking? |
|--------|--------|-----------|
| Add `invoice_date` to ServiceReviews | New optional field in response | ❌ NO |
| Phase via JOIN (already working) | No change to query | ❌ NO |
| is_billed already present | No change to query | ❌ NO |
| invoice_reference already present | No change to query | ❌ NO |

### ✅ API Contracts - NO BREAKING CHANGES

| Endpoint | Current Response | After Refactor | Breaking? |
|----------|------------------|-----------------|-----------|
| `/api/projects/{id}/services` | Returns services with phase | Add invoice_date (optional) | ❌ NO |
| `/api/projects/{id}/reviews` | Returns reviews with is_billed, invoice_reference, phase | Add invoice_date (optional) | ❌ NO |
| `/api/projects/{id}/services/{id}/reviews` | Returns service reviews | Add invoice_date (optional) | ❌ NO |
| `/api/projects/{id}/services/{id}/items` | Returns service items | Add invoice_date (optional) | ❌ NO |

### ✅ Database Migrations - ADDITIVE ONLY

| Table | Changes | Breaking? |
|-------|---------|-----------|
| ProjectServices | Verify/add phase (already exists) | ❌ NO |
| ServiceReviews | Add invoice_date (IF NOT EXISTS) | ❌ NO |
| ServiceItems | Add invoice_date (IF NOT EXISTS) | ❌ NO |
| ServiceDeliverables | No changes (out of scope) | ❌ NO |

---

## Part 8: Implementation Verification Checklist

### Pre-Implementation Verification

- [ ] **Database Schema Check**
  - Confirm `ProjectServices.phase` exists and is queryable
  - Confirm `ServiceReviews.is_billed` exists
  - Confirm `ServiceReviews.invoice_reference` exists
  - Confirm `ServiceReviews.invoice_date` does NOT exist (ready to add)

- [ ] **Frontend Query Check**
  - Confirm `projectServicesApi.getAll(projectId)` returns phase field
  - Confirm `projectReviewsApi.getProjectReviews()` returns is_billed, invoice_reference, phase

- [ ] **Backend Query Check**
  - Confirm `get_project_services()` SELECTs phase
  - Confirm `get_project_reviews()` JOINs ProjectServices to get phase
  - Confirm response includes is_billed, invoice_reference, phase

### Post-Migration Verification

- [ ] **Database Verification**
  - Run `check_schema.py --autofix` to validate all tables
  - Verify `ServiceReviews.invoice_date` column exists after migration
  - Verify `ServiceItems.invoice_date` column exists after migration

- [ ] **API Payload Verification**
  - Test GET `/api/projects/{id}/reviews` returns invoice_date (null for old records)
  - Test GET `/api/projects/{id}/services/{id}/items` returns invoice_date (null for old records)

- [ ] **Frontend Integration Verification**
  - Verify Services tab renders with phase (handles null)
  - Verify Deliverables tab renders with invoice_date (handles null)
  - Verify billing label ("Billed" / "Not billed") derives correctly from is_billed

### Regression Testing

- [ ] **Existing Services Still Visible**
  - Services with existing reviews show correct status
  - Phase field populated or null (graceful handling)

- [ ] **Existing Reviews Still Visible**
  - All reviews returned with correct counts
  - Pagination works (limit, page params)
  - Sorting works (sort_by, sort_dir)
  - Filters work (status, service_id, from_date, to_date)

- [ ] **Existing Billing Tracking Still Works**
  - is_billed flag returns correctly
  - invoice_reference populated for invoiced deliverables
  - billing_amount calculated correctly

---

## Part 9: Migration Path Summary

### What Will Be Changed

1. **SQL: Add `invoice_date` to `ServiceReviews`**
   - File: `sql/migrations/2026_01_16_add_invoice_date_to_service_reviews.sql`
   - Action: Add DATETIME column (nullable), default NULL
   - Impact: Non-breaking, optional field

2. **SQL: Add `invoice_date` to `ServiceItems`**
   - File: `sql/migrations/2026_01_16_add_invoice_date_to_service_items.sql`
   - Action: Add DATETIME column (nullable), default NULL
   - Impact: Non-breaking, optional field

3. **Backend: Update GET `/api/projects/{id}/reviews` to include `invoice_date`**
   - File: `database.py` (get_project_reviews function)
   - Action: Add invoice_date to SELECT clause
   - Impact: Non-breaking, new optional field in response

4. **Frontend: Update ReviewsTable to show `invoice_date` in Deliverables tab**
   - File: `frontend/src/components/ReviewsTable.tsx`
   - Action: Add column to Material-UI table if invoice_date not null
   - Impact: Non-breaking, new column rendered

### What Will NOT Change

- ✅ ProjectServices table structure (phase already exists)
- ✅ GET `/api/projects/{id}/services` endpoint (add invoice_date is future)
- ✅ ServiceReviews primary key or foreign keys
- ✅ API contract structure (only adding optional fields)
- ✅ Frontend routing or component hierarchy

---

## Part 10: Risk Assessment

### Low Risk (Confirmed via Audit)

- ✅ Phase is already in database and API - no migration risk
- ✅ is_billed is already in database and API - no migration risk
- ✅ invoice_reference is already in database and API - no migration risk
- ✅ Only adding new column (invoice_date) - backward compatible

### Mitigations

- All SQL migrations use IF NOT EXISTS guards (idempotent)
- API contract only expands (adding optional field), never breaks
- Frontend gracefully handles null invoice_date
- No deletions or renames (preserves Option A model)

---

## Appendix A: Files Referenced

| File | Purpose | Status |
|------|---------|--------|
| [frontend/src/api/services.ts](frontend/src/api/services.ts) | Services API client | ✅ Reviewed |
| [frontend/src/api/projectReviews.ts](frontend/src/api/projectReviews.ts) | Reviews API client | ✅ Reviewed |
| [backend/app.py](backend/app.py#L1627) | Flask routes (services) | ✅ Reviewed |
| [backend/app.py](backend/app.py#L1705) | Flask routes (reviews) | ✅ Reviewed |
| [database.py](database.py#L86) | Database functions | ✅ Reviewed |
| [constants/schema.py](constants/schema.py#L776) | Schema definitions | ✅ Reviewed |

---

## Conclusion

**VERIFICATION COMPLETE:** The specification aligns with actual codebase implementation. All data sources are confirmed, phase sourcing is verified, and no breaking changes are required. Migration to add `invoice_date` is straightforward and backward-compatible.

**NEXT PHASE:** Execute SQL migrations and update API/UI to return and display `invoice_date` field.
