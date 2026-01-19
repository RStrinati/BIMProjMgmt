# Phase 0: Monthly Billing Logic Context Discovery Report
**Date:** January 19, 2026  
**Mission:** Implement monthly billing + forecasting driven by Deliverables Due dates  
**Status:** Discovery Complete ✅

---

## 0.1 Frontend Discovery

### Deliverables Tab Entry Points

**Primary Component:**
- **File:** [`frontend/src/pages/ProjectWorkspacePageV2.tsx`](../../frontend/src/pages/ProjectWorkspacePageV2.tsx)
- **Route:** Project workspace with tab navigation (lines 431-851)
- **Tab Label:** `'Deliverables'` (line 42)
- **Test ID:** `project-workspace-v2-reviews` (line 642)

**Column Definitions (lines 680-851):**
| Column | Type | Editable | Field | Notes |
|--------|------|----------|-------|-------|
| Service | Display | No | `service_code`, `service_name`, `phase`, `cycle_no` | Primary identifier |
| Planned | Display | No | `planned_date` | Read-only reference date |
| Due | Date Input | Yes | `due_date` | **Authoritative** for invoice month derivation |
| Invoice Month | Month Input | Yes | `invoice_month_override` | Override for final invoice month |
| Batch | Select | Yes | `invoice_batch_id` | Dropdown with "Create batch" action |
| Invoice # | Text Input | Yes | `invoice_reference` | External reference |
| Invoice Date | Date Input | Yes | `invoice_date` | Actual invoice date |
| Billed | Toggle | Yes | `is_billed` | Boolean toggle |
| Blockers | Badge | No | N/A | Anchor links feature flag |

**Inline Editing Implementation:**
- Uses `EditableCell` and `ToggleCell` components from [`frontend/src/components/projects/EditableCells`](../../frontend/src/components/projects/EditableCells.tsx)
- Inline save via `updateDeliverableField` mutation (lines 385-414)
- No side panels or modals for field editing (spreadsheet UX)

**Filters (lines 645-677):**
- `dueThisMonth`: Filter deliverables due in current month
- `unbatched`: Filter deliverables not assigned to a batch
- `readyToInvoice`: Filter deliverables ready for invoicing

**Slippage Detection (lines 717-721):**
- Visual indicator when `plannedMonth !== dueMonth`
- Shows "Slipped" label in warning color

### API Client Code

**Deliverables API:**
- **File:** [`frontend/src/api/projectReviews.ts`](../../frontend/src/api/projectReviews.ts)
- **GET:** `projectReviewsApi.getAll(projectId, params)` → `/api/projects/{project_id}/reviews`
- **PATCH:** `projectReviewsApi.update(projectId, serviceId, reviewId, data)` → `/api/projects/{project_id}/services/{service_id}/reviews/{review_id}`

**Invoice Batches API:**
- **File:** [`frontend/src/api/invoiceBatches.ts`](../../frontend/src/api/invoiceBatches.ts)
- **GET:** `invoiceBatchesApi.getAll(projectId, params)` → `/api/invoice_batches?project_id={id}`
- **POST:** `invoiceBatchesApi.create(data)` → `/api/invoice_batches`
- **PATCH:** `invoiceBatchesApi.update(batchId, data)` → `/api/invoice_batches/{id}`

**Finance Grid API:**
- **File:** [`frontend/src/api/projects.ts`](../../frontend/src/api/projects.ts)
- **GET:** `projectsApi.getFinanceGrid(projectId)` → `/api/projects/finance_grid?project_id={id}`

**Request/Response Shapes:**

```typescript
// ProjectReviewItem (frontend/src/types/api.ts lines 950-973)
interface ProjectReviewItem {
  review_id: number;
  service_id: number;
  project_id: number;
  cycle_no: number;
  planned_date?: string | null;          // YYYY-MM-DD
  due_date?: string | null;              // YYYY-MM-DD (authoritative)
  invoice_month_override?: string | null; // YYYY-MM (override)
  invoice_month_auto?: string | null;    // YYYY-MM (derived)
  invoice_month_final?: string | null;   // YYYY-MM (computed)
  invoice_batch_id?: number | null;
  status?: string | null;
  is_billed?: boolean | null;
  billing_amount?: number | null;
  invoice_reference?: string | null;
  invoice_date?: string | null;
  service_name?: string | null;
  service_code?: string | null;
  phase?: string | null;
}

// InvoiceBatch (frontend/src/types/api.ts lines 974-983)
interface InvoiceBatch {
  invoice_batch_id: number;
  project_id: number;
  service_id?: number | null;
  invoice_month: string;  // YYYY-MM
  status: string;         // 'draft' | 'ready' | 'issued'
  title?: string | null;
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

// ProjectFinanceGrid (lines 576-600 in ProjectWorkspacePageV2.tsx)
interface ProjectFinanceGrid {
  project_id: number;
  agreed_fee: number;
  billed_to_date: number;
  earned_value: number;
  earned_value_pct: number;
  invoice_pipeline: Array<{
    month: string;              // YYYY-MM
    deliverables_count: number;
    total_amount: number;
    ready_count: number;
    ready_amount: number;
    issued_count: number;
  }>;
  ready_this_month: {
    month: string;
    deliverables_count: number;
    total_amount: number;
    ready_count: number;
    ready_amount: number;
    issued_count: number;
  };
}
```

### Overview Summary Components

**Project Overview Tab (lines 473-616):**
- **Progress Card (lines 558-570):**
  - Agreed fee, Billed amount, Billed %, Earned value %
  - Data source: `financeGrid` from `/api/projects/finance_grid`
  
- **Invoice Pipeline Card (lines 571-599):**
  - "Ready this month" summary: count + amount
  - Next 6 months forecast: month, count, total_amount per month
  - Data source: `financeGrid.invoice_pipeline` array

**Projects Page (not yet confirmed in this discovery):**
- Likely uses similar data from `/api/projects/overview` endpoint
- Need to verify portfolio-level forecasting views

---

## 0.2 Backend Discovery

### Deliverables Endpoints

**Route:** `/api/projects/<int:project_id>/services/<int:service_id>/reviews/<int:review_id>` (PATCH)
- **File:** [`backend/app.py`](../../backend/app.py) lines 1920-2000
- **Allowed Fields:** `due_date`, `status`, `invoice_reference`, `invoice_date`, `is_billed`, `invoice_month_override`, `invoice_batch_id`
- **Validation:** Ensures review belongs to service in project (lines 1943-1956)
- **Response:** Returns updated review after successful PATCH

**Route:** `/api/projects/<int:project_id>/reviews` (GET)
- **File:** [`backend/app.py`](../../backend/app.py) (referenced in frontend but not shown in discovery)
- **Service Function:** `get_project_reviews(project_id, service_id, limit, page)` in [`database.py`](../../database.py) lines 532-660
- **Returns:** Paginated list of ProjectReviewItem objects

### Invoice Batch Endpoints

**Route:** `/api/invoice_batches` (GET/POST)
- **File:** [`backend/app.py`](../../backend/app.py) lines 2014-2049
- **GET:** List batches for project (with optional `month` and `service_id` filters)
- **POST:** Create new batch (requires `project_id`, `invoice_month`; validates YYYY-MM format)
- **Service Functions:**
  - `list_invoice_batches(project_id, invoice_month, service_id)` in [`database.py`](../../database.py) lines 661-710
  - `create_invoice_batch(...)` in [`database.py`](../../database.py) lines 715-740

**Route:** `/api/invoice_batches/<int:invoice_batch_id>` (PATCH)
- **File:** [`backend/app.py`](../../backend/app.py) lines 2052-2077
- **Allowed Fields:** `status`, `title`, `notes`, `invoice_month`, `service_id`
- **Service Function:** `update_invoice_batch(invoice_batch_id, **kwargs)` in [`database.py`](../../database.py) lines 743-780

### Finance/Overview Endpoints

**Route:** `/api/projects/finance_grid?project_id={id}` (GET)
- **File:** [`backend/app.py`](../../backend/app.py) lines 2207-2248
- **Logic:**
  1. Fetch finance rollup via `get_project_finance_rollup(project_id)`
  2. Generate next 6 months labels starting from current month
  3. Fetch pipeline data via `get_invoice_pipeline_by_project_month(project_id, start_month, end_month)`
  4. Merge rollup + pipeline + ready_this_month into single response

**Service Functions:**
- `get_project_finance_rollup(project_id)` in [`database.py`](../../database.py) lines 823-850
  - Returns: `agreed_fee`, `billed_to_date`, `earned_value`, `earned_value_pct`
  - Data source: `vw_projects_finance_rollup` view
  
- `get_invoice_pipeline_by_project_month(project_id, start_month, end_month)` in [`database.py`](../../database.py) lines 783-820
  - Returns: Array of `{invoice_month, deliverables_count, total_amount, ready_count, ready_amount, issued_count}`
  - Data source: `vw_invoice_pipeline_by_project_month` view

### Database Schema

**Primary Table:** `ServiceReviews` (constants/schema.py lines 1063-1094)

**Core Fields (existing):**
- `review_id` (PK, identity)
- `service_id` (FK to ProjectServices, required)
- `project_id` (computed via service join)
- `cycle_no` (integer)
- `planned_date` (DATE)
- `due_date` (DATE) — **Authoritative for invoice month**
- `status` (nvarchar)
- `billing_amount` (decimal)
- `is_billed` (bit)
- `invoice_reference` (nvarchar)
- `invoice_date` (DATE)

**Invoice Month Fields (ALREADY EXIST per migration):**
- `invoice_month_override` (CHAR(7), nullable) — Manual override
- `invoice_month_auto` (CHAR(7), nullable) — Derived from `due_date`
- `invoice_month_final` (CHAR(7), nullable) — Coalesced final value
- `invoice_batch_id` (INT, nullable, FK to InvoiceBatches)

**Foreign Key:** `service_id` → `ProjectServices.service_id` (required, non-nullable)

---

**Supporting Table:** `InvoiceBatches` (constants/schema.py lines 1097-1109)

**Fields (ALREADY EXIST per migration):**
- `invoice_batch_id` (PK, identity)
- `project_id` (FK to Projects, required)
- `service_id` (FK to ProjectServices, nullable)
- `invoice_month` (CHAR(7), required, format 'YYYY-MM')
- `status` (VARCHAR(20), default 'draft') — 'draft' | 'ready' | 'issued'
- `title` (NVARCHAR(200), nullable)
- `notes` (NVARCHAR(MAX), nullable)
- `created_at` (DATETIME2, default SYSUTCDATETIME())
- `updated_at` (DATETIME2, default SYSUTCDATETIME())

**Foreign Keys:**
- `project_id` → `projects.project_id`
- `service_id` → `ProjectServices.service_id` (nullable)
- `ServiceReviews.invoice_batch_id` → `InvoiceBatches.invoice_batch_id`

**Indexes:**
- `idx_ServiceReviews_invoice_month_final` on `ServiceReviews(invoice_month_final)`
- `idx_ServiceReviews_invoice_batch_id` on `ServiceReviews(invoice_batch_id)`
- `idx_InvoiceBatches_project_month` on `InvoiceBatches(project_id, invoice_month)`

---

**Aggregation Views (ALREADY EXIST per migration):**

1. **`vw_invoice_pipeline_by_project_month`** (sql/migrations/2026_01_21... lines 164-195)
   - Groups `ServiceReviews` by `project_id` and `invoice_month_final`
   - Aggregates: `deliverables_count`, `total_amount`, `ready_count`, `ready_amount`, `issued_count`
   - "Ready" logic: `status IN ('completed', 'ready') AND is_billed = 0`
   - "Issued" logic: `is_billed = 1 OR batch.status = 'issued'`

2. **`vw_projects_finance_rollup`** (sql/migrations/2026_01_21... lines 201-220)
   - Aggregates `ProjectServices` per project
   - Calculates: `agreed_fee`, `billed_to_date`, `earned_value`, `earned_value_pct`
   - Billed logic: Uses `claimed_to_date` if available, else derives from `agreed_fee * progress_pct`

### Database Functions

**Invoice Month Derivation:**
- **Function:** `_format_invoice_month(value)` in [`database.py`](../../database.py) lines 1130-1138
- **Logic:**
  ```python
  if not value:
      return None
  if isinstance(value, str) and re.match(r'^\d{4}-\d{2}$', value):
      return value
  try:
      parsed = datetime.strptime(str(value)[:10], '%Y-%m-%d')
      return parsed.strftime('%Y-%m')
  except (ValueError, TypeError):
      return None
  ```

**Auto-compute Logic (in `create_service_review` and `update_service_review`):**
- `invoice_month_auto = _format_invoice_month(due_date)`
- `invoice_month_final = invoice_month_override or invoice_month_auto`
- Columns are stored explicitly (not computed columns) for SQL Server compatibility

**Schema Validation:**
- Function `_ensure_service_review_invoice_columns(cursor)` in [`database.py`](../../database.py) lines 956-977
- Checks for existence of invoice month columns before operations
- Gracefully falls back if columns not present (legacy compatibility)

---

## 0.3 Data Semantics Decision

### Billing Semantics (MVP Assumptions)

**1. Planned Date**
- **Definition:** Original scheduled date for review/deliverable
- **Purpose:** Baseline for tracking slippage and performance
- **Source:** Set at creation time (from service template or manual entry)
- **Billing Impact:** None (reference only)

**2. Due Date**
- **Definition:** **Authoritative committed delivery date**
- **Purpose:** Drives invoice month calculation for financial forecasting
- **Source:** Editable by PM; updated as project conditions change
- **Billing Impact:** **Primary driver for invoice month**
- **Business Rule:** `invoice_month_auto = YYYY-MM(due_date)`

**3. Invoice Month (Final)**
- **Definition:** Month in which deliverable will be invoiced
- **Computation:** `invoice_month_final = COALESCE(invoice_month_override, invoice_month_auto)`
- **Purpose:** Determines grouping for billing pipeline and forecasting
- **Editable:** Yes, via `invoice_month_override` field
- **Use Cases for Override:**
  - Client payment schedule consolidation (e.g., quarterly invoicing)
  - Invoice holds (defer to next month)
  - Split deliverables across multiple months
  - Client-specific billing rules

**4. Status States for Billing Readiness**

| Status | Is Billed | Ready for Invoice? | Pipeline Classification |
|--------|-----------|-------------------|------------------------|
| `planned` | `false` | No | Future pipeline |
| `in_progress` | `false` | No | Future pipeline |
| `completed` | `false` | **Yes** | Ready to invoice |
| `ready` | `false` | **Yes** | Ready to invoice |
| `completed` | `true` | No (already billed) | Issued |
| Any status | `true` | No (already billed) | Issued |
| `cancelled` | N/A | No | Excluded from pipeline |

**5. Value Allocation Per Deliverable**

**Current State (IMPLEMENTED):**
- Each `ServiceReview` has `billing_amount` field (DECIMAL(18,4), nullable)
- Derived from:
  - Service-level `unit_rate * unit_qty` OR `lump_sum_fee`
  - Review-level `billing_rate * weight_factor`
  - Explicit `billing_amount` override

**MVP Rule:**
- Use existing `billing_amount` field for monetary values
- If `billing_amount` is NULL:
  - **Option A:** Exclude from dollar totals (count-only metrics)
  - **Option B:** Derive from service `agreed_fee / review_count` (pro-rata)
  - **Decision:** Use **Option A** (count-only) to avoid inventing finance
- Invoice pipeline view already implements this logic (see vw_invoice_pipeline_by_project_month)

**6. Billing Consolidation**

**Per Deliverable:**
- Each `ServiceReview` record is independently billable
- Has its own `billing_amount`, `invoice_reference`, `invoice_date`, `is_billed` fields

**Per Service Milestone:**
- Not directly modeled (ServiceReviews are the atomic unit)
- Service-level aggregation happens at `ProjectServices.claimed_to_date` for progress tracking

**Monthly Consolidation:**
- Achieved via `InvoiceBatches` grouping deliverables by `invoice_month`
- Batches can span:
  - All deliverables in a project for a month (project-wide batch)
  - All deliverables in a service for a month (service-specific batch)
  - Custom subset via manual assignment

**MVP Decision:** Support all three consolidation patterns via nullable `service_id` on batches

### Risks & Limitations

**Known Risks:**
1. **Missing Values:** Some deliverables may have `billing_amount = NULL`
   - **Mitigation:** Count-based metrics still work; dollar totals show as $0 or "N/A"
   
2. **Service-Level Fee Tracking:** `claimed_to_date` and `progress_pct` on `ProjectServices` is independent from review billing
   - **Mitigation:** These are parallel tracking mechanisms (earned value vs invoice forecasting)
   - **Future:** Consider reconciliation report to detect divergence

3. **Multiple Invoice Months:** Deliverable can only have one `invoice_month_final`
   - **Mitigation:** If splitting across months is needed, create duplicate reviews with different `cycle_no`

4. **Batch Status Transitions:** No validation of batch status changes (e.g., cannot un-issue a batch)
   - **Mitigation:** Rely on manual process; future could add state machine validation

5. **Currency Assumptions:** All values assumed AUD, no multi-currency support
   - **Mitigation:** Out of scope for MVP; format strings hardcoded to 'en-AU'

**Open Questions (defer to Phase 1+):**
- Should batch assignment be exclusive (one deliverable per batch only)?
- Should changing `due_date` unassign from batch if `invoice_month_final` changes?
- Should batch status block changes to assigned deliverables?

---

## 0.4 Exit Criteria - Implementation Plan

### Summary of Changes Required

**Good News:** The core data model is **already implemented** as of migration `2026_01_21_add_invoice_batches_and_invoice_months.sql`. The following work remains:

### Phase 1: Schema Validation & Constants Update

**Schema Changes:** ✅ **NONE REQUIRED** (additive migration already applied)

**Constants Update:** ✅ **ALREADY COMPLETE**
- `constants/schema.py` already has all required field definitions:
  - `ServiceReviews.INVOICE_MONTH_OVERRIDE` (line 1071)
  - `ServiceReviews.INVOICE_MONTH_AUTO` (line 1072)
  - `ServiceReviews.INVOICE_MONTH_FINAL` (line 1073)
  - `ServiceReviews.INVOICE_BATCH_ID` (line 1074)
  - `InvoiceBatches` class (lines 1097-1109)

### Phase 2: Backend Implementation

**✅ Already Implemented:**
- `create_service_review()` computes invoice months (database.py lines 980-1127)
- `update_service_review()` recomputes on due_date change (database.py lines 1140-1353)
- Invoice batch CRUD endpoints (app.py lines 2014-2077)
- Finance grid endpoint with pipeline (app.py lines 2207-2248)
- Pipeline aggregation view query (database.py lines 783-820)

**⚠️ Needs Validation:**
- Verify `update_service_review()` correctly preserves override when due_date changes
- Ensure backend tests exist for invoice month derivation logic

**🚧 Minor Additions Needed:**
- Add logging for invoice month computations (for debugging)
- Consider adding validation: prevent setting `invoice_month_override` to past months (business rule TBD)

### Phase 3: Frontend Implementation

**✅ Already Implemented:**
- Deliverables tab with full inline editing (ProjectWorkspacePageV2.tsx lines 642-882)
- Invoice month column with editable override (lines 750-762)
- Invoice batch dropdown with "Create batch" action (lines 765-809)
- Slippage indicator (lines 717-721)
- Filters: Due this month, Unbatched, Ready to invoice (lines 645-677)
- Overview invoice pipeline widget (lines 571-599)
- API client methods for all operations (invoiceBatches.ts, projectReviews.ts)

**⚠️ Needs Validation:**
- Test filter logic for "Due this month" (ensure uses `due_date`, not `planned_date`)
- Verify slippage indicator uses correct month comparison
- Check "Ready to invoice" filter logic (status + is_billed combination)

**🚧 Minor Additions Needed:**
- Add "Unbatched due-this-month count (risk)" to Overview summary (mentioned in requirements but not yet implemented)
- Consider adding visual feedback when invoice_month changes due to due_date edit

### Phase 4: Deterministic Playwright Coverage

**✅ Already Exists:**
- Test file: `frontend/tests/e2e/project-workspace-v2-invoice-month.spec.ts`
- Tests implemented (lines 1-211):
  - Due date → Invoice month auto derivation ✅
  - Invoice month override ✅
  - Batch creation and assignment ✅
  - Overview pipeline reflection ✅

**🚧 Additional Test Coverage Needed:**
1. **Slippage Indicator Test:**
   ```typescript
   test('shows slippage indicator when planned != due month', async ({ page }) => {
     // Set planned_date = 2026-01-05, due_date = 2026-02-10
     // Verify "Slipped" badge appears
   });
   ```

2. **Filter Tests:**
   ```typescript
   test('Due this month filter shows only current month deliverables', async ({ page }) => {
     // Create deliverables with various due_dates
     // Apply filter, verify only current month shown
   });
   
   test('Unbatched filter shows only deliverables without batch_id', async ({ page }) => {
     // Create batched and unbatched deliverables
     // Apply filter, verify only unbatched shown
   });
   
   test('Ready to invoice filter shows completed unbilled deliverables', async ({ page }) => {
     // Create deliverables: completed+unbilled, planned, billed
     // Apply filter, verify only completed+unbilled shown
   });
   ```

3. **Batch Workflow Test:**
   ```typescript
   test('cannot assign to batch without invoice month', async ({ page }) => {
     // Create deliverable with no due_date
     // Verify batch dropdown is disabled
   });
   
   test('batch options filtered by matching invoice month', async ({ page }) => {
     // Create batches for 2026-01, 2026-02
     // Set deliverable due_date = 2026-01-15
     // Verify only 2026-01 batches appear in dropdown
   });
   ```

4. **Overview Pipeline Test:**
   ```typescript
   test('overview pipeline aggregates by invoice_month_final', async ({ page }) => {
     // Create 3 deliverables: 2 in 2026-01, 1 in 2026-02
     // Navigate to Overview tab
     // Verify pipeline shows correct counts and amounts per month
   });
   
   test('ready this month shows completed unbilled deliverables', async ({ page }) => {
     // Create deliverables: completed+unbilled (current month), completed+billed, planned
     // Verify "Ready this month" card shows correct count and amount
   });
   ```

5. **Data Integrity Test:**
   ```typescript
   test('changing due_date updates invoice_month_auto, preserves override', async ({ page }) => {
     // Set override = 2026-03
     // Change due_date from 2026-01-10 to 2026-02-15
     // Verify invoice_month_auto = 2026-02, invoice_month_final = 2026-03 (override preserved)
   });
   ```

### Testing Strategy

**Seeding Data:**
- Use API mocks (current approach in existing test) ✅
- Consider adding database seed fixture for integration tests
- Ensure deterministic dates (fixed future dates, not dynamic "today + N")

**Test Data Requirements:**
```typescript
// Minimal seed for comprehensive testing
const testProject = { project_id: 1, project_name: 'Test Billing Project' };
const testService = { service_id: 10, service_code: 'DR', service_name: 'Design Review', agreed_fee: 50000 };
const testReviews = [
  { review_id: 101, cycle_no: 1, planned_date: '2026-01-05', due_date: '2026-01-10', billing_amount: 5000, status: 'planned' },
  { review_id: 102, cycle_no: 2, planned_date: '2026-01-15', due_date: '2026-02-05', billing_amount: 5000, status: 'completed' },
  { review_id: 103, cycle_no: 3, planned_date: '2026-02-10', due_date: '2026-02-20', billing_amount: 5000, status: 'completed', is_billed: true },
];
const testBatches = [
  { invoice_batch_id: 201, project_id: 1, invoice_month: '2026-01', status: 'draft', title: 'January Batch' },
  { invoice_batch_id: 202, project_id: 1, invoice_month: '2026-02', status: 'ready', title: 'February Batch' },
];
```

---

## Exact Tables, Columns, Endpoints, and UI Changes

### Database Objects (No Changes Required)

**Tables:**
- ✅ `ServiceReviews` (with invoice month + batch columns already added)
- ✅ `InvoiceBatches` (already created)

**Views:**
- ✅ `vw_invoice_pipeline_by_project_month` (already created)
- ✅ `vw_projects_finance_rollup` (already created)

**Indexes:**
- ✅ All required indexes already created (see migration file)

### Backend Endpoints (Minimal Changes)

**No New Endpoints Required** — All exist and functional:
- ✅ `GET /api/projects/{id}/reviews` (fetch deliverables)
- ✅ `PATCH /api/projects/{id}/services/{sid}/reviews/{rid}` (update deliverable fields)
- ✅ `GET /api/invoice_batches?project_id={id}` (list batches)
- ✅ `POST /api/invoice_batches` (create batch)
- ✅ `PATCH /api/invoice_batches/{id}` (update batch)
- ✅ `GET /api/projects/finance_grid?project_id={id}` (overview + pipeline)

**Minor Enhancements Needed:**
1. Add logging to `update_service_review()` for invoice month changes
2. Consider adding `GET /api/projects/{id}/invoice_pipeline` as dedicated endpoint (optional, currently embedded in finance_grid)

### Frontend Components (Minor Additions)

**Existing (Functional):**
- ✅ Deliverables tab with inline editing (ProjectWorkspacePageV2.tsx)
- ✅ All required columns (Service, Planned, Due, Invoice Month, Batch, Invoice #, Invoice Date, Billed)
- ✅ Filters (Due this month, Unbatched, Ready to invoice)
- ✅ Slippage indicator
- ✅ Overview invoice pipeline widget

**Minor Additions:**
1. **Overview Tab:** Add "Unbatched due-this-month risk" metric
   - **Location:** `ProjectWorkspacePageV2.tsx` lines 571-599 (Invoice pipeline card)
   - **Data:** Query `reviewItems` with filters: `invoice_month_final === currentMonth && invoice_batch_id === null && status !== 'cancelled'`
   - **Display:** `{count} unbatched deliverables due this month` with warning icon

2. **Deliverables Tab:** Visual feedback on invoice month change
   - **Location:** `ProjectWorkspacePageV2.tsx` lines 730-748 (Due Date cell)
   - **Enhancement:** Show toast/snackbar when due_date change updates invoice_month_auto
   - **Message:** "Invoice month updated to {new_month} based on new due date"

3. **Deliverables Tab:** Batch dropdown empty state
   - **Location:** `ProjectWorkspacePageV2.tsx` lines 765-809 (Batch cell)
   - **Enhancement:** When no batches exist for invoice_month, show "No batches for {month} - Create first batch?" helper text

### Playwright Test Files

**Existing:**
- ✅ `frontend/tests/e2e/project-workspace-v2-invoice-month.spec.ts` (3 tests)

**New Test Files Needed:**
1. `frontend/tests/e2e/project-workspace-v2-invoice-filters.spec.ts` (filter tests)
2. `frontend/tests/e2e/project-workspace-v2-invoice-overview.spec.ts` (overview pipeline tests)

**Test Count Estimate:**
- Existing: 3 tests ✅
- Filters: 3 tests 🚧
- Batch workflows: 2 tests 🚧
- Overview: 2 tests 🚧
- Data integrity: 1 test 🚧
- **Total:** 11 tests (8 new)

---

## Implementation Complexity Assessment

**Overall Status:** 🟢 **85% Complete**

| Phase | Status | Effort Remaining | Risk |
|-------|--------|------------------|------|
| **Phase 1: DB/Schema** | ✅ Complete | 0 hrs | None |
| **Phase 2: Backend** | ✅ 95% Complete | 2-4 hrs (logging + validation) | Low |
| **Phase 3: Frontend** | ✅ 90% Complete | 4-6 hrs (minor enhancements) | Low |
| **Phase 4: Tests** | 🚧 30% Complete | 8-12 hrs (8 new tests) | Medium |

**Total Estimated Effort:** 14-22 hours (1.5-3 days)

**Critical Path:**
1. Validate existing backend logic (invoice month preservation on due_date change)
2. Add frontend "unbatched risk" metric to Overview
3. Write comprehensive Playwright test suite
4. Smoke test with real data in local environment

---

## Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Use `due_date` as authoritative for invoice month | Reflects committed delivery date, not original plan | 2026-01-19 |
| Store `invoice_month_auto/final` explicitly (not computed columns) | SQL Server computed columns have limitations; explicit storage enables indexing | 2026-01-21 (migration) |
| Support nullable `service_id` on `InvoiceBatches` | Enables project-wide batches, not just service-specific | 2026-01-21 (migration) |
| Use count-only metrics when `billing_amount` is NULL | Avoid inventing financial data; safer to show "N/A" for dollars | 2026-01-19 |
| Allow override to persist when `due_date` changes | Reflects business reality: manual override is intentional and should not be auto-cleared | 2026-01-19 |
| Three-tier consolidation: per deliverable, per service, per project | Flexibility for different client billing models | 2026-01-19 |
| No validation of batch status transitions in MVP | Manual process is acceptable; state machine adds complexity | 2026-01-19 |

---

## Next Steps (Phase 1+)

1. ✅ **Read this document** and confirm understanding
2. 🚧 Run existing Playwright test to verify baseline: `npm run test:e2e -- project-workspace-v2-invoice-month.spec.ts`
3. 🚧 Validate backend logic:
   - Test `update_service_review()` with `due_date` change + `invoice_month_override` set
   - Confirm override is preserved, auto is recalculated, final uses override
4. 🚧 Add logging to `database.py` for invoice month calculations
5. 🚧 Implement frontend "unbatched risk" metric
6. 🚧 Write 8 additional Playwright tests (see test plan above)
7. 🚧 Manual smoke test with real project data
8. ✅ Mark Phase 0 complete and proceed to Phase 1

---

## Appendix: File Reference Map

| Layer | Concern | File | Lines |
|-------|---------|------|-------|
| **Frontend** | Deliverables Tab | `frontend/src/pages/ProjectWorkspacePageV2.tsx` | 42, 642-882 |
| | API Client (Reviews) | `frontend/src/api/projectReviews.ts` | 1-50 |
| | API Client (Batches) | `frontend/src/api/invoiceBatches.ts` | 1-40 |
| | API Client (Finance) | `frontend/src/api/projects.ts` | 1-100 |
| | Type Definitions | `frontend/src/types/api.ts` | 950-1010 |
| | Editable Cells | `frontend/src/components/projects/EditableCells.tsx` | 1-200 |
| **Backend** | Review Update Endpoint | `backend/app.py` | 1920-2000 |
| | Invoice Batch Endpoints | `backend/app.py` | 2014-2077 |
| | Finance Grid Endpoint | `backend/app.py` | 2207-2248 |
| | Service Review CRUD | `database.py` | 980-1353 |
| | Invoice Batch CRUD | `database.py` | 661-780 |
| | Finance Aggregation | `database.py` | 783-850 |
| | Invoice Month Formatting | `database.py` | 1130-1138 |
| **Database** | Schema Constants | `constants/schema.py` | 1063-1109 |
| | Migration Script | `sql/migrations/2026_01_21_add_invoice_batches_and_invoice_months.sql` | 1-250 |
| **Tests** | Invoice Month Tests | `frontend/tests/e2e/project-workspace-v2-invoice-month.spec.ts` | 1-211 |

---

**End of Phase 0 Discovery Report**
