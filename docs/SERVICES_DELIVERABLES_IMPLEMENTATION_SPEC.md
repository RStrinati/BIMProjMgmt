# Services & Deliverables Implementation Specification

**Status:** FINAL (January 16, 2026)  
**Scope:** Services tab + Deliverables tab UI/UX refinement  
**Authority:** Senior Implementation Refinement Agent

---

## Executive Summary

This document locks the technical requirements for the Services + Deliverables refactor. **No alternatives or design changes are permitted.** All decisions are **FINAL** and translate to precise implementation instructions for developers.

---

## A. Schema Instruction Refinement

### Required Additive Migrations

#### Migration 1: Add `invoice_date` to `ServiceReviews` table

```sql
-- File: sql/migrations/2026_01_16_add_invoice_date_to_service_reviews.sql
ALTER TABLE dbo.ServiceReviews
ADD invoice_date DATE NULL;

-- Index for performance (optional but recommended)
CREATE INDEX idx_ServiceReviews_invoice_date 
  ON dbo.ServiceReviews(invoice_date);
```

**Rationale:**  
- `invoice_reference` alone is insufficient; we need a date to complete billing records
- `DATE` type aligns with existing `planned_date`, `due_date` columns
- `NULL` permits partial data entry (e.g., invoiced but not yet dated)

---

#### Migration 2: Add `invoice_date` to `ServiceItems` table

```sql
-- File: sql/migrations/2026_01_16_add_invoice_date_to_service_items.sql
ALTER TABLE dbo.ServiceItems
ADD invoice_date DATE NULL;

-- Index for performance (optional but recommended)
CREATE INDEX idx_ServiceItems_invoice_date 
  ON dbo.ServiceItems(invoice_date);
```

**Rationale:**  
- If ServiceItems are included in Deliverables unified view, they must support invoice dating
- Schema parity with ServiceReviews

---

#### Migration 3: Confirm or Add `phase` to `ProjectServices` table

```sql
-- File: sql/migrations/2026_01_16_confirm_phase_on_project_services.sql

-- Check if phase column exists
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME='ProjectServices' AND COLUMN_NAME='phase'
)
BEGIN
  ALTER TABLE dbo.ProjectServices
  ADD phase NVARCHAR(100) NULL;
  
  CREATE INDEX idx_ProjectServices_phase 
    ON dbo.ProjectServices(phase);
END
ELSE
BEGIN
  -- Column already exists; log success
  PRINT 'Phase column already exists on ProjectServices';
END;
```

**Rationale:**  
- Phase must be attached to Services (ProjectServices), not Reviews
- Reviews inherit phase via `ProjectServices.phase` join
- No phase column should be added to ServiceReviews or ServiceItems

---

### Schema Invariants (DO NOT VIOLATE)

| Table | Column | Type | Nullability | Purpose | Reason |
|-------|--------|------|-------------|---------|--------|
| `ServiceReviews` | `invoice_date` | DATE | NULL | Billing date for the review | Finance tracking |
| `ServiceItems` | `invoice_date` | DATE | NULL | Billing date for the item | Finance tracking (if items included) |
| `ProjectServices` | `phase` | NVARCHAR(100) | NULL | Single source of truth for phase | Enables phase inheritance to reviews/items |
| **NO NEW COLUMNS** | — | — | — | No `billing_status` enum, no `completion_date` alias | Preserve existing schema patterns |

---

## B. Backend Contract Refinement

### API Response Field Mapping (Aliases Only)

**Principle:** Expose business-friendly names in API payloads **without renaming database columns.**

#### ServiceReview Query Enhancement

**File:** `database.py` → `get_service_reviews()` and `get_project_reviews()`

**Required Changes:**

1. **Add `invoice_date` column to SELECT**
   ```python
   # Already has: invoice_reference
   # ADD:
   {S.ServiceReviews.INVOICE_DATE},
   ```

2. **Join to ProjectServices for `phase`**
   ```python
   # Current: 
   #   SELECT sr.* FROM ServiceReviews sr WHERE sr.service_id = ?
   # 
   # New:
   #   SELECT sr.*, ps.phase
   #   FROM ServiceReviews sr
   #   INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
   ```

3. **Expose aliases in serialized output (Python dict)**
   ```python
   # Existing fields:
   'invoice_reference': row[10],  # ← Keep as-is (DB column name)
   'is_billed': bool(row[16]) if row[16] is not None else False,  # ← Keep
   'planned_date': row[3],  # ← Keep
   
   # NEW fields:
   'invoice_date': row[N],  # ← Add invoice_date from DB
   'phase': row[M],  # ← Add phase from ProjectServices join
   ```

4. **Apply in ALL review queries:**
   - `get_service_reviews(service_id)`
   - `get_project_reviews(project_id, ...)`
   - Any custom review endpoints

---

### API Response Contract (Final Field Names)

**All review payloads MUST include these fields:**

```typescript
// Example JSON response structure
{
  "review_id": 123,
  "service_id": 45,
  "cycle_no": 1,
  
  // Dates (raw column names, no aliases)
  "planned_date": "2026-01-20",     // ← Treated as "Completion date" in UI
  "due_date": "2026-01-25",          // ← "Due date"
  "invoice_date": "2026-02-01",      // ← NEW FIELD
  "actual_issued_at": "2026-01-22",
  
  // Billing (raw column names)
  "invoice_reference": "INV-2026-001",  // ← "Invoice number" in UI
  "is_billed": true,                     // ← Derived to "Billed" / "Not billed" in UI
  "billing_amount": 5000.00,
  "billing_rate": null,
  
  // Metadata
  "status": "completed",
  "disciplines": "Structural, MEP",
  "deliverables": "...json...",
  "evidence_links": "...json...",
  
  // Inheritance from Service
  "phase": "Design Review",  // ← NEW FIELD (from ProjectServices.phase)
  "service_name": "Design Review Service",
  "service_id": 45
}
```

---

### Backend Serializer / Utility Function

**Purpose:** Centralize billing status derivation logic (no scattered if-statements)

**File Location:** `backend/utils/billing_utils.py` (create if not exists)

```python
def derive_billing_status(is_billed: bool) -> str:
    """
    Derive UI billing status from database boolean.
    
    Args:
        is_billed: Boolean from ServiceReviews.is_billed
    
    Returns:
        str: "Billed" or "Not billed" for UI display
    """
    return "Billed" if is_billed else "Not billed"


def serialize_service_review_for_api(row: tuple, column_indices: dict) -> dict:
    """
    Serialize a ServiceReview database row to API-friendly dict.
    Applies aliases (e.g., invoice_reference → invoice_number in API).
    
    Args:
        row: Database cursor row result
        column_indices: Dict mapping column names to 0-based indices in row
    
    Returns:
        dict: API response payload
    """
    return {
        "review_id": row[column_indices["review_id"]],
        "service_id": row[column_indices["service_id"]],
        "cycle_no": row[column_indices["cycle_no"]],
        "planned_date": row[column_indices["planned_date"]],
        "due_date": row[column_indices["due_date"]],
        "invoice_date": row[column_indices["invoice_date"]],  # NEW
        "invoice_reference": row[column_indices["invoice_reference"]],
        "billing_status": derive_billing_status(row[column_indices["is_billed"]]),
        "phase": row[column_indices["phase"]],  # NEW (from join)
        # ... other fields ...
    }
```

**Usage in `get_project_reviews()` and `get_service_reviews()`:**
```python
from backend.utils.billing_utils import serialize_service_review_for_api

# In your query handler:
reviews = [serialize_service_review_for_api(row, column_map) for row in cursor.fetchall()]
```

---

## C. Frontend Contract Refinement

### TypeScript Interfaces

#### 1. Update `ServiceReview` interface

**File:** `frontend/src/types/api.ts`

```typescript
export interface ServiceReview {
  review_id: number;
  service_id: number;
  cycle_no: number;
  
  // Dates
  planned_date: string;           // UI label: "Completion date"
  due_date?: string;               // UI label: "Due date"
  invoice_date?: string | null;    // NEW FIELD
  actual_issued_at?: string;
  
  // Billing
  invoice_reference?: string;      // Mapped to: invoice_number (UI)
  is_billed?: boolean;             // Mapped to: billing_status (UI via derive_billing_status)
  billing_amount?: number | null;
  billing_rate?: number | null;
  
  // Metadata
  status: string;
  disciplines?: string;
  deliverables?: string;
  evidence_links?: string;
  weight_factor?: number | null;
  actual_issued_at?: string;
  
  // Inherited from Service
  phase?: string;                  // NEW FIELD (from ProjectServices.phase)
  service_name?: string;
  service_phase?: string;          // (deprecate if redundant with phase)
  
  // Legacy billing fields (keep for backward compatibility)
  source_phase?: string | null;
  billing_phase?: string | null;
}
```

#### 2. Create `Deliverable` interface (unified view type)

**File:** `frontend/src/types/api.ts`

```typescript
/**
 * Unified Deliverable row for Services & Deliverables table.
 * Can represent either a ServiceReview or ServiceItem.
 * 
 * Source mapping:
 *   - ServiceReview.planned_date → completion_date
 *   - ServiceReview.is_billed → billing_status
 *   - ServiceReview.invoice_reference → invoice_number
 *   - ServiceReview.invoice_date → invoice_date
 *   - ProjectServices.phase → phase
 */
export interface Deliverable {
  // Identity
  id: number;                          // review_id or item_id
  type: 'review' | 'item';            // Source type (ServiceReview vs ServiceItem)
  
  // Service & Phase
  service_id: number;
  service_name?: string;
  phase?: string;                      // Inherited from ProjectServices.phase
  
  // Delivery
  title?: string;                      // review cycle_no or item title
  description?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'overdue';
  
  // Key Finance Fields (final UI names)
  completion_date: string;             // Alias: planned_date
  due_date?: string;
  invoice_number?: string;             // Alias: invoice_reference
  invoice_date?: string | null;        // NEW FIELD
  billing_status: 'Billed' | 'Not billed';  // Derived from is_billed
  
  // Finance Detail
  billing_amount?: number | null;
  billing_rate?: number | null;
  
  // Metadata
  disciplines?: string;
  deliverables?: string;
  evidence_links?: string;
  assigned_to?: string;
  assigned_user_id?: number;
  
  // Raw columns (for advanced access if needed)
  is_billed?: boolean;                 // Raw column value
  planned_date?: string;               // Raw column value
  invoice_reference?: string;          // Raw column value
  
  // Timestamps
  created_at?: string;
  updated_at?: string;
}
```

#### 3. Update `ProjectReviewItem` interface

**File:** `frontend/src/types/api.ts`

```typescript
export interface ProjectReviewItem {
  review_id: number;
  service_id: number;
  project_id: number;
  cycle_no: number;
  
  planned_date?: string | null;       // UI: "Completion date"
  due_date?: string | null;
  invoice_date?: string | null;       // NEW FIELD
  
  status?: string | null;
  disciplines?: string | null;
  deliverables?: string | null;
  
  is_billed?: boolean | null;         // UI: billing_status
  billing_amount?: number | null;
  invoice_reference?: string | null;  // UI: invoice_number
  
  service_name?: string | null;
  service_code?: string | null;
  phase?: string | null;              // NEW FIELD (from ProjectServices.phase)
}
```

---

### Frontend Utility Functions

#### Billing Status Derivation

**File:** `frontend/src/utils/billingUtils.ts` (create if not exists)

```typescript
/**
 * Derive UI billing status from database boolean.
 */
export const derive_billing_status = (is_billed: boolean | undefined | null): 'Billed' | 'Not billed' => {
  return is_billed ? 'Billed' : 'Not billed';
};

/**
 * Format a Deliverable from a ServiceReview API response.
 */
export const format_service_review_as_deliverable = (review: ServiceReview): Deliverable => {
  return {
    id: review.review_id,
    type: 'review',
    service_id: review.service_id,
    service_name: review.service_name,
    phase: review.phase,  // From ProjectServices.phase join
    
    title: `Cycle ${review.cycle_no}`,
    status: (review.status?.toLowerCase() as any) || 'planned',
    
    completion_date: review.planned_date,
    due_date: review.due_date,
    invoice_number: review.invoice_reference,
    invoice_date: review.invoice_date,
    billing_status: derive_billing_status(review.is_billed),
    
    billing_amount: review.billing_amount,
    disciplines: review.disciplines,
    deliverables: review.deliverables,
    evidence_links: review.evidence_links,
    
    is_billed: review.is_billed,
    planned_date: review.planned_date,
    invoice_reference: review.invoice_reference,
  };
};
```

---

### UI Component Structure

#### Services Tab (Finance + Alignment)

**File:** `frontend/src/pages/Services/ServicesTab.tsx` (or equivalent)

**Requirements:**
- Uses Material-UI Drawer for detail view (same pattern as Issues tab)
- Columns: Service Name, Phase, Assigned To, Agreed Fee, Progress %, Claimed to Date
- OnClick row → opens Drawer with full service detail
- Drawer shows: finance fields, linked reviews/items count, status

**Drawer Content:**
```
┌─ Service Drawer ────────────────────┐
│ Service Name: Design Review         │
│ Phase: Design Review                │
│ Assigned To: John Smith             │
│ Agreed Fee: $25,000                 │
│ Progress: 60%                       │
│ Claimed to Date: $15,000            │
│                                     │
│ Related Deliverables:               │
│   - 3 Completed Reviews             │
│   - 2 Pending Items                 │
│                                     │
│ [View All Deliverables]             │
└─────────────────────────────────────┘
```

---

#### Deliverables Tab (Unified View)

**File:** `frontend/src/pages/Deliverables/DeliverablesTab.tsx` (rename from Reviews)

**Columns (in order):**
1. Service Name (text)
2. Phase (text, inherited from ProjectServices)
3. Completion Date (date, `planned_date`)
4. Due Date (date, `due_date`)
5. Invoice Number (text, `invoice_reference`)
6. Invoice Date (date, `invoice_date`)
7. Billing Status (badge, derived from `is_billed`)
8. Status (badge, `status`)

**Row Click → Deliverable Drawer:**

```typescript
const [selectedDeliverable, setSelectedDeliverable] = useState<Deliverable | null>(null);

const handleRowClick = (deliverable: Deliverable) => {
  setSelectedDeliverable(deliverable);
};
```

**Drawer Content:**
```
┌─ Deliverable Drawer ────────────────┐
│ Service: Design Review Service      │
│ Phase: Design Review                │
│ Type: Review (Cycle 1)              │
│                                     │
│ DELIVERY DATES:                     │
│   Completion Date: 2026-01-20       │
│   Due Date: 2026-01-25              │
│                                     │
│ BILLING:                            │
│   Billing Status: Billed            │
│   Invoice Number: INV-2026-001      │
│   Invoice Date: 2026-02-01          │
│   Billing Amount: $2,500            │
│                                     │
│ METADATA:                           │
│   Status: Completed                 │
│   Disciplines: Structural, MEP      │
│   Assigned To: Jane Doe             │
│                                     │
│ [Edit] [Close]                      │
└─────────────────────────────────────┘
```

---

## D. Acceptance Criteria (MUST BE EXPLICIT)

### Services Tab Acceptance Criteria

**Given:** User navigates to Services tab in a project with multiple services  
**When:** Tab loads and renders the services table  
**Then:**

- ✅ **AC-1.1:** Table columns render correctly: Service Name, Phase, Assigned To, Agreed Fee, Progress %, Claimed to Date
- ✅ **AC-1.2:** Phase column is populated from `ProjectServices.phase` (verified by database query)
- ✅ **AC-1.3:** Clicking a service row opens a Material-UI Drawer on the right side
- ✅ **AC-1.4:** Drawer displays all required finance fields: Agreed Fee, Progress %, Claimed to Date
- ✅ **AC-1.5:** Drawer displays "Related Deliverables" section with count of reviews + items
- ✅ **AC-1.6:** Drawer close button (X or Cancel) deterministically removes the Drawer from view
- ✅ **AC-1.7:** Clicking another row changes the Drawer content without flickering

---

### Deliverables Tab Acceptance Criteria

**Given:** User navigates to Deliverables tab in a project with reviews and items  
**When:** Tab loads and queries `/projects/{id}/reviews` and `/projects/{id}/items` (or unified endpoint)  
**Then:**

- ✅ **AC-2.1:** Table columns render in order: Service Name, Phase, Completion Date, Due Date, Invoice Number, Invoice Date, Billing Status, Status
- ✅ **AC-2.2:** Phase column is populated via `ServiceReview.phase` (inherited from ProjectServices join)
- ✅ **AC-2.3:** Completion Date displays `planned_date` with label "Completion date"
- ✅ **AC-2.4:** Due Date displays `due_date` with label "Due date"
- ✅ **AC-2.5:** Invoice Number displays `invoice_reference` (or empty if null)
- ✅ **AC-2.6:** Invoice Date displays `invoice_date` (or empty if null)
- ✅ **AC-2.7:** Billing Status column displays derived value:
  - `is_billed = true` → Badge: "Billed"
  - `is_billed = false` → Badge: "Not billed"
  - `is_billed = null` → Badge: "Unbilled" or empty
- ✅ **AC-2.8:** Status column displays standardized values: Planned, In Progress, Completed, Overdue
- ✅ **AC-2.9:** Clicking a deliverable row opens a Drawer showing full detail (all fields listed in spec)
- ✅ **AC-2.10:** Drawer displays inherited phase and all finance info correctly
- ✅ **AC-2.11:** Drawer close button deterministically removes the Drawer
- ✅ **AC-2.12:** Sorting and filtering (if present) work on all visible columns

---

### Backend API Contract Acceptance Criteria

**Given:** API endpoint `/projects/{id}/reviews` is called  
**When:** Response is serialized  
**Then:**

- ✅ **AC-3.1:** Response includes `invoice_date` field (null if not set)
- ✅ **AC-3.2:** Response includes `phase` field (inherited from ProjectServices.phase via join)
- ✅ **AC-3.3:** `invoice_reference` field is present (raw column value, no alias applied)
- ✅ **AC-3.4:** `is_billed` field is present (raw boolean, no transformation)
- ✅ **AC-3.5:** `planned_date` field is present (labeled as "Completion date" in UI, not in API)
- ✅ **AC-3.6:** All fields in `ServiceReview` interface match API payload exactly
- ✅ **AC-3.7:** Null/missing values are handled gracefully (no JSON syntax errors)

---

### Schema Acceptance Criteria

**Given:** Database migration scripts are run against ProjectManagement database  
**When:** Migrations complete  
**Then:**

- ✅ **AC-4.1:** `ServiceReviews.invoice_date` column exists with type `DATE` and `NULL` nullability
- ✅ **AC-4.2:** `ServiceItems.invoice_date` column exists with type `DATE` and `NULL` nullability
- ✅ **AC-4.3:** `ProjectServices.phase` column exists with appropriate type (VARCHAR or NVARCHAR)
- ✅ **AC-4.4:** No columns are renamed, removed, or modified (additive only)
- ✅ **AC-4.5:** Indexes are created on new columns for performance
- ✅ **AC-4.6:** All existing foreign keys and constraints remain intact

---

## E. Implementation Guardrails (NO EXCEPTIONS)

### ✅ ALLOWED

- ✅ Add new columns (`invoice_date`, confirm `phase`)
- ✅ Add new indexes for performance
- ✅ Create utility functions for billing status derivation
- ✅ Update API serialization to expose existing fields under different names
- ✅ Create new frontend interfaces (ServiceReview, Deliverable, ProjectReviewItem)
- ✅ Rename UI tabs (Reviews → Deliverables)
- ✅ Use Material-UI Drawer for both Services and Deliverables detail views

### ❌ FORBIDDEN

- ❌ Rename database columns
- ❌ Remove existing columns or fields
- ❌ Add new enum tables (e.g., `billing_status_enum`)
- ❌ Modify existing foreign key relationships
- ❌ Add `completion_date` as a separate column
- ❌ Move phase to ServiceReviews or ServiceItems
- ❌ Create new panel abstractions for the UI
- ❌ Propose alternative data models or semantics
- ❌ Widen scope beyond Services and Deliverables

---

## F. Definition of Done Checklist

### For PR Implementation: Services & Deliverables Refactor

**Use this checklist in your PR description. ALL items must be checked before merging.**

```markdown
## Services & Deliverables Implementation - Definition of Done

### Database & Schema
- [ ] Migration `2026_01_16_add_invoice_date_to_service_reviews.sql` is merged to `sql/migrations/`
- [ ] Migration `2026_01_16_add_invoice_date_to_service_items.sql` is merged to `sql/migrations/`
- [ ] Migration `2026_01_16_confirm_phase_on_project_services.sql` is merged to `sql/migrations/`
- [ ] Run migrations locally and confirm no errors
- [ ] Verify `ServiceReviews.invoice_date` column exists in database
- [ ] Verify `ServiceItems.invoice_date` column exists in database
- [ ] Verify `ProjectServices.phase` column exists and is populated

### Backend API
- [ ] Updated `get_service_reviews()` to include `invoice_date` and `phase` in response
- [ ] Updated `get_project_reviews()` to include `invoice_date` and `phase` in response
- [ ] Added JOIN to ProjectServices in review queries for phase inheritance
- [ ] Created `backend/utils/billing_utils.py` with:
  - `derive_billing_status(is_billed)` function
  - `serialize_service_review_for_api()` function (optional, for consistency)
- [ ] Tested API response by calling `/projects/{id}/reviews` and verifying:
  - `invoice_date` field present (null OK)
  - `phase` field present
  - `is_billed` boolean present
  - `invoice_reference` present
- [ ] No breaking changes to existing review endpoints

### Frontend Types
- [ ] Updated `frontend/src/types/api.ts` - `ServiceReview` interface
  - Added `invoice_date?: string | null`
  - Added `phase?: string`
- [ ] Updated `frontend/src/types/api.ts` - `ProjectReviewItem` interface
  - Added `invoice_date?: string | null`
  - Added `phase?: string | null`
- [ ] Created `frontend/src/types/api.ts` - `Deliverable` interface (new type)
- [ ] Created `frontend/src/utils/billingUtils.ts` with:
  - `derive_billing_status(is_billed)` function
  - `format_service_review_as_deliverable(review)` function

### Frontend UI - Services Tab
- [ ] Services tab renders with columns: Service Name, Phase, Assigned To, Agreed Fee, Progress %, Claimed to Date
- [ ] Phase column displays correctly for all services
- [ ] Row click opens Material-UI Drawer (right-side panel)
- [ ] Drawer displays all finance fields correctly
- [ ] Drawer close button works deterministically
- [ ] Drawer updates when switching between service rows
- [ ] No console errors in browser DevTools

### Frontend UI - Deliverables Tab (renamed from Reviews)
- [ ] Tab renamed from "Reviews" to "Deliverables"
- [ ] Table renders with 8 columns: Service Name, Phase, Completion Date, Due Date, Invoice Number, Invoice Date, Billing Status, Status
- [ ] Phase column populated correctly via API
- [ ] Completion Date shows `planned_date` with correct label
- [ ] Due Date shows `due_date`
- [ ] Invoice Number shows `invoice_reference` (or empty)
- [ ] Invoice Date shows `invoice_date` (or empty)
- [ ] Billing Status column displays:
  - "Billed" for `is_billed = true`
  - "Not billed" for `is_billed = false`
- [ ] Row click opens Deliverable Drawer
- [ ] Drawer displays all required fields from `Deliverable` interface
- [ ] Drawer displays inherited phase correctly
- [ ] Sorting and filtering work correctly (if implemented)
- [ ] No console errors

### Integration Tests
- [ ] Run local API tests for `/projects/{id}/reviews` endpoint
- [ ] Verify response includes all new fields
- [ ] Test with projects that have:
  - Multiple services with and without phase set
  - Reviews with null invoice_date
  - Mixed is_billed values
- [ ] Frontend loads without crashing
- [ ] Drawer open/close cycles work 5+ times without memory leaks

### Documentation
- [ ] Updated `backend/utils/billing_utils.py` docstrings are clear
- [ ] Updated `frontend/src/utils/billingUtils.ts` docstrings are clear
- [ ] TypeScript interfaces include inline JSDoc comments for non-obvious fields
- [ ] No TODO or FIXME comments left in implementation code

### Code Quality
- [ ] Python code follows PEP8 (use `flake8` or `pylint`)
- [ ] TypeScript code follows project ESLint config
- [ ] No unused imports or variables
- [ ] Functions are properly typed (TypeScript)
- [ ] Error handling is present for database queries and API calls
- [ ] Logging includes context (e.g., `logger.info(f"Loaded {len(reviews)} reviews for service {service_id}")`)

### Backward Compatibility
- [ ] No breaking changes to existing API contracts
- [ ] Existing frontend code that uses `ServiceReview` still works
- [ ] Database columns are added, never removed or renamed
- [ ] Existing views and stored procedures remain unchanged

### Deployment Readiness
- [ ] All migrations are idempotent (safe to re-run)
- [ ] Migration scripts include comments explaining purpose
- [ ] Rollback plan is documented (if applicable)
- [ ] Feature flag or phased rollout plan (if applicable)

---

## Acceptance Criteria Met
- [ ] All AC-1.x (Services Tab) criteria verified
- [ ] All AC-2.x (Deliverables Tab) criteria verified
- [ ] All AC-3.x (Backend API) criteria verified
- [ ] All AC-4.x (Schema) criteria verified

---

## Sign-Off
- **Implemented By:** [Developer Name]
- **Reviewed By:** [Code Reviewer Name]
- **Date:** [Date]
- **PR Link:** [PR URL]
```

---

## G. API → UI Field Mapping Table (FINAL)

| Database Column | API Field Name | TypeScript Type | UI Label | UI Component | Example |
|---|---|---|---|---|---|
| `ServiceReviews.planned_date` | `planned_date` | `string` | **Completion date** | Text (date) | "2026-01-20" |
| `ServiceReviews.due_date` | `due_date` | `string \| null` | **Due date** | Text (date) | "2026-01-25" |
| `ServiceReviews.invoice_reference` | `invoice_reference` | `string \| null` | **Invoice number** | Text | "INV-2026-001" |
| `ServiceReviews.invoice_date` | `invoice_date` | `string \| null` | **Invoice date** | Text (date) | "2026-02-01" |
| `ServiceReviews.is_billed` | `is_billed` | `boolean \| null` | **Billing status** | Badge | "Billed" / "Not billed" |
| `ProjectServices.phase` | `phase` | `string \| null` | **Phase** | Text | "Design Review" |
| `ServiceReviews.status` | `status` | `string` | **Status** | Badge | "Completed" |
| `ServiceReviews.billing_amount` | `billing_amount` | `number \| null` | **Billing amount** | Currency | "$2,500.00" |
| `ServiceReviews.service_name` | `service_name` | `string` | **Service** | Text | "Design Review Service" |

---

## Deployment Notes

### Migration Order (If Running Multiple)

1. **Add columns first** (additive, non-blocking)
   - `invoice_date` to ServiceReviews
   - `invoice_date` to ServiceItems
   - `phase` to ProjectServices (if missing)

2. **Backend updates** (must include new query logic)
   - Update `database.py` with new field exposure
   - Deploy billing_utils.py

3. **Frontend updates** (can follow backend)
   - Update TypeScript interfaces
   - Deploy new components
   - UI goes live once backend is ready

### Rollback Plan

- **If columns fail to add:** Run DROP COLUMN script (prepared in advance)
- **If API breaks:** Revert to previous database.py commit
- **If frontend breaks:** Clear browser cache and restart dev server

### Logging & Monitoring

- **Log new field access:** `logger.debug(f"Accessed invoice_date: {invoice_date}")`
- **Monitor API response times:** Ensure JOIN to ProjectServices doesn't degrade performance
- **Frontend errors:** Check `logs/frontend.log` for Drawer interactions

---

## Sign-Off & Authority

**Document Status:** ✅ **FINAL** (No revisions permitted)

**Locked by:** Senior Implementation Refinement Agent  
**Date:** January 16, 2026  
**Scope Locked:** Services + Deliverables UI/UX  
**Authority:** Project Technical Leadership

**Changes permitted after this date only via:**
- Formal change request (CCB)
- Senior architect approval
- User story backlog amendment

---

## Quick Reference Links

- [Copilot Instructions](../.github/copilot-instructions.md) - Core model
- [AGENTS Guidance](../AGENTS.md) - Agent workflow rules
- [Schema Constants](../constants/schema.py) - Database field definitions
- [Database Functions](../database.py) - Query implementations

