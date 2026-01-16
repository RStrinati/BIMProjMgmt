# BIM Project Management System - Codebase Audit Report
## Services Tab + Deliverables Tab Refactor

**Audit Date:** January 16, 2026  
**Scope:** Update Services tab for finance + alignment with side panel; Rename Reviews → Deliverables with unified table  
**Status:** ✅ Complete Audit, Ready for Implementation Planning

---

## Executive Summary

The codebase audit reveals a **well-structured foundation** with clear separation of concerns:

- ✅ **ProjectWorkspacePageV2** is the target workspace with tabs: Overview, Services, Reviews, Issues, Tasks, Timeline
- ✅ **Services tab** already exists with expandable rows; requires finance-focused columns and a detail side panel
- ✅ **Reviews tab** shows review cycles; will be renamed to **Deliverables** with unified data model
- ✅ **DetailsPanel** component (UI abstraction) and **Drawer** pattern (IssuesTabContent) both exist
- ✅ **Schema constants** prevent hardcoded DB identifiers; **database_pool.py** centralizes connections
- ⚠️ **Missing schema fields**: `completion_date`, `invoice_date`, `billing_status`, `invoice_number` require additive migration
- ⚠️ **Type mismatch**: `ProjectReviewItem` vs `ServiceReview` vs `ServiceItem` — requires unified deliverables data view

---

## A) Frontend Audit: Routing, Tabs, Components

### 1. Project Workspace v2 Tab Configuration

**File:** [frontend/src/pages/ProjectWorkspacePageV2.tsx](frontend/src/pages/ProjectWorkspacePageV2.tsx#L28)

**Current State:**
```typescript
const BASE_TABS = ['Overview', 'Services', 'Reviews', 'Issues', 'Tasks'] as const;

// Feature flag gate:
// featureFlags.projectWorkspaceV2 → uses ProjectWorkspacePageV2
// else → uses ProjectDetailPage (legacy)
```

**Tab routing:**
- Line 456-466: Services tab renders `<ProjectServicesList projectId={projectId} />`
- Line 469-583: Reviews tab shows review list (grid layout, no side panel)
- Each tab controlled by `activeTab` state + `tabs` array

**Feature Flag:**
- Stored in `localStorage` key: `ff_project_workspace_v2`
- [frontend/src/config/featureFlags.ts](frontend/src/config/featureFlags.ts#L43) reads it
- Checked in [App.tsx](frontend/src/App.tsx#L42) for route resolution

✅ **Finding:** Tab structure is flexible; renaming requires only string literal change.

---

### 2. Services Tab Current UI

**Component:** [frontend/src/components/ProjectServicesTab.tsx](frontend/src/components/ProjectServicesTab.tsx)

**Current Structure:**
- Wraps entire service CRUD: list, create, edit, delete
- Uses Material-UI **Dialog** (not Drawer) for Create/Edit forms
- Services table shows columns: Service Code, Name, Phase, Unit Type, Unit Qty, Unit Rate, Lump Sum Fee, Status
- Expandable rows reveal nested sections for reviews + items (accordion style)

**Key State:**
```typescript
const [selectedService, setSelectedService] = useState<ProjectService | null>(null);
const [selectedReview, setSelectedReview] = useState<ServiceReview | null>(null);
const [selectedItem, setSelectedItem] = useState<ServiceItem | null>(null);
const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
const [itemDialogOpen, setItemDialogOpen] = useState(false);
```

**Data fetched:**
- Services list (React Query: `['projectServices', projectId]`)
- Nested reviews + items loaded per service (separate queries)

**Finance columns currently present:**
- `agreed_fee` (optional)
- `unit_rate`, `unit_qty`, `lump_sum_fee` (inline)
- `billing_progress_pct` (computed)
- `billed_amount` (from ProjectService interface)

❌ **Gap:** No dedicated side panel for service detail view (only inline expansion).

---

### 3. Reviews Tab Current UI

**Location:** [frontend/src/pages/ProjectWorkspacePageV2.tsx](frontend/src/pages/ProjectWorkspacePageV2.tsx#L469-L583)

**Current Structure:**
- Queries `useProjectReviews()` hook to fetch project-wide reviews
- Grid layout showing: Service label | Cycle # | Planned | Due | Status | Blockers (optional, if anchorLinks flag)
- Status updatable inline via `ReviewStatusInline` dropdown
- Row click triggers a **Dialog** (anchor linking detail, if flag enabled)

**Data shape (ProjectReviewItem):**
```typescript
interface ProjectReviewItem {
  review_id, service_id, project_id, cycle_no, planned_date, due_date, status,
  disciplines, deliverables, is_billed, billing_amount, invoice_reference,
  service_name, service_code, phase
}
```

**Missing fields for "Deliverables" table:**
- `completion_date`, `planned_date` (label rename needed), `assignee`, `fee`, `invoice_date`, `billing_status`, `invoice_number`

❌ **Gap:** Does not include `ServiceItem` data (separate table); view does not unify review cycles + items.

---

### 4. Existing Side Panel / Drawer Pattern

**DetailsPanel Component:** [frontend/src/components/ui/DetailsPanel.tsx](frontend/src/components/ui/DetailsPanel.tsx)

- Simple **presentational** wrapper (not state management)
- Takes `title`, `subtitle`, `actions`, `children`, `emptyState` props
- Used in: [ProjectsPanelPage](frontend/src/pages/ProjectsPanelPage.tsx#L348), [BidsPanelPage](frontend/src/pages/BidsPanelPage.tsx#L343)
- **Not** a modal/drawer; renders inline within a layout column

**Drawer Pattern:** [IssuesTabContent.tsx](frontend/src/components/ProjectManagement/IssuesTabContent.tsx#L278-L481)

- Uses Material-UI `<Drawer>` component
- State: `isDetailOpen`, `selectedIssueKey`
- Triggered by row click
- Displays issue detail with linked issues list (`LinkedIssuesList`)

```typescript
<Drawer
  anchor="right"
  open={isDetailOpen}
  onClose={handleDetailClose}
  data-testid="issue-detail-drawer"
>
  {/* Issue detail content */}
</Drawer>
```

✅ **Pattern found:** Drawer is the right abstraction for side panel.

---

## B) Data Contract Audit: API Layer

### 1. API Client Methods

**Services API:** [frontend/src/api/services.ts](frontend/src/api/services.ts)

```typescript
projectServicesApi.getAll(projectId)
  → /api/projects/{id}/services

serviceReviewsApi.getAll(projectId, serviceId)
  → /api/projects/{id}/services/{service_id}/reviews

serviceItemsApi.getAll(projectId, serviceId)
  → /api/projects/{id}/services/{service_id}/items
```

**Project-wide Reviews API:**

```typescript
useProjectReviews(projectId, filters)
  → internal hook querying /api/projects/{id}/reviews
  → returns { items: ProjectReviewItem[], total }
```

### 2. Response Shapes

**ProjectService:**
```typescript
{
  service_id, project_id, phase, service_code, service_name, unit_type, 
  unit_qty, unit_rate, lump_sum_fee, agreed_fee, bill_rule, notes,
  status, progress_pct, claimed_to_date, billing_progress_pct, billed_amount,
  agreed_fee_remaining, created_at, updated_at
}
```

**ServiceReview:**
```typescript
{
  review_id, service_id, cycle_no, planned_date, due_date, disciplines, 
  deliverables, status, weight_factor, invoice_reference, evidence_links,
  actual_issued_at, source_phase, billing_phase, billing_rate, 
  billing_amount, service_name, service_phase, is_billed
}
```

**ServiceItem:**
```typescript
{
  item_id, service_id, item_type, title, description, planned_date, due_date,
  actual_date, status, priority, assigned_to, invoice_reference, evidence_links,
  notes, created_at, updated_at, is_billed
}
```

**ProjectReviewItem (project-wide view):**
```typescript
{
  review_id, service_id, project_id, cycle_no, planned_date, due_date, status,
  disciplines, deliverables, is_billed, billing_amount, invoice_reference,
  service_name, service_code, phase
}
```

❌ **Gap Analysis:**
- **No assignee field** in ServiceReview or ProjectReviewItem (only `assigned_user_id` in schema)
- **No completion_date** (only planned_date, due_date, actual_issued_at)
- **No invoice_date** (only invoice_reference string)
- **No billing_status** enum (only is_billed boolean)
- **No invoice_number** (only invoice_reference which is generic)

---

## C) Backend + Database Audit

### 1. Schema Constants (constants/schema.py)

**ServiceReviews table fields:**
```python
class ServiceReviews:
  review_id, service_id, cycle_no, planned_date, due_date, disciplines,
  deliverables, status, weight_factor, evidence_links, invoice_reference,
  actual_issued_at, is_billed, source_phase, billing_phase, billing_rate,
  billing_amount, assigned_user_id
```

**ServiceItems table fields:**
```python
class ServiceItems:
  item_id, service_id, item_type, title, description, planned_date, due_date,
  actual_date, status, priority, assigned_to, assigned_user_id,
  invoice_reference, evidence_links, notes, created_at, updated_at, is_billed
```

**Services (ProjectService) table fields:**
```python
class Services:
  service_id, project_id, phase, service_code, service_name, unit_type,
  unit_qty, unit_rate, lump_sum_fee, agreed_fee, bill_rule, notes, status,
  progress_pct, claimed_to_date, assigned_user_id, created_at, updated_at
  [+ billing fields from database.py logic]
```

✅ **Finding:** Schema constants are comprehensive; ready for aliasing.

### 2. "Planned Completion Date" Field Mapping

**Current naming in DB:**
- `ServiceReviews.planned_date` (column)
- SQL scripts reference: `planned_completion_date` (in views like `vw_review_schedule_details.sql`)
- UI currently labels it as "Planned"

**Requirement:** UI label should be "Planned date" (already matches; just an alias in code).

### 3. Missing Fields Analysis

| Field Required | Currently Available? | Source Table | Action Needed |
|---|---|---|---|
| **Phase name** | ✅ Yes | `ServiceReviews.deliverables` or `ServiceItems.title` | Map existing |
| **Deliverable title** | ✅ Yes (ServiceItem.title or ServiceReview.deliverables) | ServiceItems OR ServiceReviews | Union query |
| **Cycle number** | ✅ Yes | `ServiceReviews.cycle_no` | Map existing |
| **Assignee** | ⚠️ Partial | `ServiceReviews.assigned_user_id` → Users.name | Join needed |
| **Due date** | ✅ Yes | `ServiceReviews.due_date` | Map existing |
| **Status** | ✅ Yes | `ServiceReviews.status` | Map existing |
| **Completion date** | ❌ No | — | **Add column** |
| **Planned date** | ✅ Yes (label rename) | `ServiceReviews.planned_date` | Alias in code |
| **Fee** | ✅ Partial | `Services.lump_sum_fee` or `ServiceReviews.billing_amount` | Determine logic |
| **Invoice date** | ❌ No | — | **Add column** |
| **Billing status** | ⚠️ Partial | `ServiceReviews.is_billed` (boolean) | Add enum field |
| **Invoice number** | ⚠️ Partial | `ServiceReviews.invoice_reference` | Rename/clarify |

---

### 4. Proposed Additive Schema Changes

**All changes are additive (no drops/renames):**

#### Migration 1: ServiceReviews Enhancement
```sql
-- Add completion tracking fields
ALTER TABLE ServiceReviews ADD
  completion_date DATE NULL,
  actual_completion_date DATE NULL;

-- Clarify billing fields
ALTER TABLE ServiceReviews ADD
  invoice_date DATE NULL,
  invoice_number NVARCHAR(100) NULL;  -- distinct from invoice_reference

-- Add billing status enum
ALTER TABLE ServiceReviews ADD
  billing_status NVARCHAR(50) NULL  -- 'pending', 'invoiced', 'paid', 'overdue'
  CHECK (billing_status IN ('pending', 'invoiced', 'paid', 'overdue'));
```

#### Migration 2: ServiceItems Enhancement
```sql
ALTER TABLE ServiceItems ADD
  completion_date DATE NULL,
  invoice_date DATE NULL,
  invoice_number NVARCHAR(100) NULL,
  billing_status NVARCHAR(50) NULL
  CHECK (billing_status IN ('pending', 'invoiced', 'paid', 'overdue'));
```

#### Migration 3: Schema Constants Update
```python
class ServiceReviews:
    # ... existing ...
    COMPLETION_DATE = "completion_date"
    ACTUAL_COMPLETION_DATE = "actual_completion_date"
    INVOICE_DATE = "invoice_date"
    INVOICE_NUMBER = "invoice_number"
    BILLING_STATUS = "billing_status"

class ServiceItems:
    # ... existing ...
    COMPLETION_DATE = "completion_date"
    INVOICE_DATE = "invoice_date"
    INVOICE_NUMBER = "invoice_number"
    BILLING_STATUS = "billing_status"
```

---

### 5. API Endpoints Needing Updates

**Current endpoints:**

| Endpoint | Current Behavior | Updates Required |
|----------|---|---|
| `GET /api/projects/{id}/reviews` | Fetch project-wide reviews (ProjectReviewItem) | Include new fields + join assignee name |
| `GET /api/projects/{id}/services/{id}/reviews` | Fetch service reviews | Include completion_date, invoice fields |
| `GET /api/projects/{id}/services/{id}/items` | Fetch service items | Include billing_status, invoice fields |
| `PATCH /api/projects/{id}/services/{id}/reviews/{id}` | Update review | Support new fields in request payload |
| `PATCH /api/projects/{id}/services/{id}/items/{id}` | Update item | Support new fields in request payload |

---

## D) UX Mapping Decisions

### 1. "Deliverable Instance" Model for UI

**Problem:** Current UI has separate concepts:
- **ServiceReview** = recurring cycle (e.g., "Weekly design review")
- **ServiceItem** = one-off or bundled deliverable (e.g., "Submittal review set")
- **ProjectReviewItem** = flattened view joining service + review metadata

**Solution:** Create a **unified Deliverables table** that shows **both** review cycles and items:

```
Deliverables Row = (ServiceReview OR ServiceItem) with consistent schema
├─ review_id / item_id (distinguish type)
├─ phase, title (map from phase/service_name + cycle_no OR item_type/title)
├─ cycle_no / cycle (ServiceReview.cycle_no OR ServiceItem.planned_period)
├─ assignee (from assigned_user_id joined to Users)
├─ due_date, status, completion_date
├─ planned_date (label from planned_date)
├─ fee (mapping logic: billing_amount for review, service fee for item)
├─ invoice_date, billing_status, invoice_number
└─ source_type: 'review' | 'item' (for detail routing)
```

### 2. Unified View Strategy

**Option A (Preferred): SQL View**
Create a database view `vw_project_deliverables` that unions ServiceReviews + ServiceItems with consistent column names:

```sql
CREATE VIEW vw_project_deliverables AS
SELECT
  'review' AS source_type,
  sr.review_id AS deliverable_id,
  sr.service_id, p.project_id,
  s.phase, sr.cycle_no,
  CONCAT(s.service_code, ' - Cycle ', sr.cycle_no) AS title,
  sr.planned_date, sr.due_date, sr.actual_issued_at AS completion_date,
  sr.status, u.name AS assignee,
  sr.billing_amount AS fee,
  sr.invoice_date, sr.invoice_number, sr.billing_status
FROM ServiceReviews sr
JOIN Services s ON sr.service_id = s.service_id
JOIN Projects p ON s.project_id = p.project_id
LEFT JOIN Users u ON sr.assigned_user_id = u.user_id

UNION ALL

SELECT
  'item' AS source_type,
  si.item_id AS deliverable_id,
  si.service_id, s.project_id,
  s.phase, NULL AS cycle_no,
  si.title,
  si.planned_date, si.due_date, si.actual_date AS completion_date,
  si.status, u.name AS assignee,
  (SELECT agreed_fee FROM Services WHERE service_id = si.service_id) AS fee,
  si.invoice_date, si.invoice_number, si.billing_status
FROM ServiceItems si
JOIN Services s ON si.service_id = s.service_id
LEFT JOIN Users u ON si.assigned_user_id = u.user_id;
```

**Option B (If view creation blocked): Application-level union**
- Fetch both queries (`getServiceReviews` + `getServiceItems`)
- Map to common interface `DeliverableRow`
- Filter/sort in React

---

## E) Test Impact (Playwright)

### 1. Existing Test Coverage

**Tests found:**
- [project-workspace-v2.spec.ts](frontend/tests/e2e/project-workspace-v2.spec.ts) — Tab navigation, basic render
- [project-workspace-v2-services.spec.ts](frontend/tests/e2e/project-workspace-v2-services.spec.ts) — Services mocking
- [project-workspace-v2-reviews-projectwide.spec.ts](frontend/tests/e2e/project-workspace-v2-reviews-projectwide.spec.ts) — Reviews tab

❌ **Gap:** No tests for:
- Services side panel detail view
- Deliverables (renamed Reviews) table with required columns
- Row click → side panel open/close behavior

### 2. New / Updated Tests Required

**Test 1: Services tab side panel opening**
```typescript
test('Services: row click opens detail panel', async ({ page }) => {
  // Navigate to Services tab
  // Click on a service row
  // Assert detail drawer opens (data-testid="service-detail-drawer")
  // Assert key fields visible: service_code, agreed_fee, billing_pct
  // Click close button; assert drawer closes
})
```

**Test 2: Reviews → Deliverables tab rename + columns**
```typescript
test('Deliverables: tab renamed, table renders required columns', async ({ page }) => {
  // Navigate to workspace
  // Assert tab labeled "Deliverables" (not "Reviews")
  // Click Deliverables tab
  // Assert columns visible: Phase, Deliverable, Cycle, Assignee, Due, Status, Completion, Planned, Fee, Invoice Date, Billing Status, Invoice #
  // Assert test-id selectors follow pattern: deliverable-row-{review_id|item_id}
})
```

**Test 3: Deliverables side panel detail**
```typescript
test('Deliverables: row click opens side panel with related data', async ({ page }) => {
  // Navigate to Deliverables tab
  // Click on a deliverable row
  // Assert side panel opens (data-testid="deliverable-detail-drawer")
  // Assert detail shows:
  //   - Review/Item associations
  //   - Linked issues
  //   - Comments/attachments (if available)
  //   - History timeline
  // Click close; assert drawer closes
})
```

---

## Change Inventory

### Frontend Files to Edit

| File | Change | Scope |
|------|--------|-------|
| **ProjectWorkspacePageV2.tsx** | 1. Rename "Reviews" tab to "Deliverables" (line 28) 2. Update activeLabel conditional (line 469) 3. Import new DeliverableRow interface | Small: 3 changes |
| **ProjectServicesTab.tsx** | 1. Add finance columns (fee, invoice date, billing status) 2. Replace Dialog with Drawer for service detail side panel 3. Import new drawer component | Medium: Restructure detail view |
| **[NEW] DeliverableSidePanel.tsx** | Create new component for deliverable detail view showing: review/item metadata, linked issues, comments, history | Medium: ~200 lines |
| **[NEW] ServiceDetailDrawer.tsx** | Create new component for service detail side panel (finance focused) | Small: ~150 lines |
| **[NEW] vw_project_deliverables.ts** (API hook) | Create hook to fetch unified deliverables query (or compose from two queries) | Small: ~50 lines |
| **types/api.ts** | Add `DeliverableRow`, `ServiceDetailPayload` interfaces; extend ProjectService with finance fields | Small: +30 lines |
| **project-workspace-v2.spec.ts** | Update tab label expectation ("Deliverables" instead of "Reviews") | Tiny: 1 line |
| **[NEW] services-side-panel.spec.ts** | Playwright test: services row click → drawer open | Small: ~80 lines |
| **[NEW] deliverables-side-panel.spec.ts** | Playwright test: deliverable row click → drawer open + detail fields visible | Small: ~100 lines |

### Backend Files to Edit

| File | Change | Scope |
|------|--------|-------|
| **backend/app.py** | 1. Add/update endpoint: `GET /api/projects/{id}/deliverables` (unified view) 2. Update endpoints to return new fields (completion_date, invoice_date, billing_status, billing_number) 3. Add assignee name in response via JOIN | Medium: ~100 lines |
| **database.py** | 1. Add query functions: `get_project_deliverables()` 2. Update `get_project_reviews()` to include new fields + user join | Small: ~50 lines |
| **[NEW] warehouse/etl/pipeline.py** (optional) | If backfilling warehouse: add new fields to stg/fact loads | Optional |

### Database / Schema Files

| File | Change |
|------|--------|
| **sql/migrations/007_add_completion_and_billing_fields.sql** | Additive: Add columns to ServiceReviews + ServiceItems |
| **constants/schema.py** | Add new field constants: COMPLETION_DATE, INVOICE_DATE, INVOICE_NUMBER, BILLING_STATUS |
| **sql/views/vw_project_deliverables.sql** | Optional: Create unified view (recommended for performance) |

### Test Files

| File | Change |
|------|--------|
| **frontend/tests/e2e/project-workspace-v2.spec.ts** | Update: Tab label expectation |
| **[NEW] frontend/tests/e2e/services-side-panel.spec.ts** | New: Services detail panel interaction |
| **[NEW] frontend/tests/e2e/deliverables-side-panel.spec.ts** | New: Deliverables detail panel + columns |

---

## Implementation Plan (Ordered Steps)

### Phase 1: Database & Schema (Safe, Isolated)
**Duration:** 30 mins | **Risk:** Low | **PR:** `db-migration/deliverables-fields`

1. Create migration SQL: `sql/migrations/007_*.sql`
2. Update `constants/schema.py` with new field constants
3. Run migration locally; verify columns exist
4. ✅ Checkpoint: Schema ready; no code breaks (additive only)

### Phase 2: Backend API (Contract Changes)
**Duration:** 1-2 hrs | **Risk:** Low-Medium | **PR:** `backend/deliverables-api`

1. Update `database.py`:
   - `get_project_reviews()` → include new fields + assignee join
   - Add `get_project_deliverables()` (unified or composed)
2. Update `backend/app.py`:
   - Endpoint: `GET /api/projects/{id}/deliverables` (or reuse `reviews` endpoint)
   - Response payload includes all required fields
3. Update `frontend/src/types/api.ts`:
   - Add `DeliverableRow` interface
   - Extend `ProjectService` with finance fields
4. Test locally: Verify API responses include new fields
5. ✅ Checkpoint: Backend API contract stable; Frontend can consume

### Phase 3: Frontend UI - Label + Routing
**Duration:** 30 mins | **Risk:** Very Low | **PR:** `frontend/tab-rename`

1. [ProjectWorkspacePageV2.tsx](frontend/src/pages/ProjectWorkspacePageV2.tsx#L28):
   - Change `BASE_TABS` from `'Reviews'` → `'Deliverables'`
   - Update conditional on line 469 to reference new label
2. Update test expectation: [project-workspace-v2.spec.ts](frontend/tests/e2e/project-workspace-v2.spec.ts#L61)
3. ✅ Checkpoint: Tab label updated; tests pass

### Phase 4: Frontend UI - Services Detail Drawer
**Duration:** 2-3 hrs | **Risk:** Medium | **PR:** `frontend/services-detail-drawer`

1. Create [frontend/src/components/ServiceDetailDrawer.tsx](frontend/src/components/ServiceDetailDrawer.tsx) (~150 lines):
   - Material-UI `<Drawer>` with right anchor
   - Display service fields: code, name, phase, agreed_fee, unit_rate, billing_pct, billed_amount
   - Show nested reviews count badge
   - Close button (X icon)
2. Refactor [ProjectServicesTab.tsx](frontend/src/components/ProjectServicesTab.tsx):
   - Replace service detail Dialog with new Drawer
   - Connect row click → `setSelectedService` + `setServiceDrawerOpen(true)`
3. Add test IDs: `data-testid="service-detail-drawer"`, `service-row-{service_id}`
4. Update Playwright test: [services-side-panel.spec.ts](frontend/tests/e2e/services-side-panel.spec.ts) (new file)
5. ✅ Checkpoint: Services side panel works; Playwright test passes

### Phase 5: Frontend UI - Deliverables Table + Drawer
**Duration:** 3-4 hrs | **Risk:** Medium-High | **PR:** `frontend/deliverables-table`

1. Create [frontend/src/components/DeliverableSidePanel.tsx](frontend/src/components/DeliverableSidePanel.tsx) (~200 lines):
   - Drawer component for deliverable detail
   - Show: review/item metadata, linked issues (via `LinkedIssuesList`), comments stub, history stub
   - Link to parent service + review (breadcrumb)
2. Update [ProjectWorkspacePageV2.tsx](frontend/src/pages/ProjectWorkspacePageV2.tsx):
   - Import `DeliverableRow` type
   - Replace Reviews grid with new Deliverables table using Material-UI `<Table>`
   - Table columns: Phase, Deliverable, Cycle, Assignee, Due, Status, Completion, Planned, Fee, Invoice Date, Billing Status, Invoice #
   - Row click → `setSelectedDeliverableId` + `setDeliverableDrawerOpen(true)`
3. Create API hook (or enhance `useProjectReviews`):
   - Fetch unified deliverables (reviews + items, if needed)
   - Include all new fields
4. Add test IDs: `data-testid="deliverable-row-{id}"`, `deliverable-detail-drawer`
5. Update/Create Playwright test: [deliverables-side-panel.spec.ts](frontend/tests/e2e/deliverables-side-panel.spec.ts) (new file)
6. ✅ Checkpoint: Deliverables table renders; drawer opens on row click

### Phase 6: Integration Testing & Fixes
**Duration:** 1-2 hrs | **Risk:** Medium | **PR:** `frontend/integration-tests`

1. Run all Playwright tests: `npm run test:e2e` (in frontend/)
2. Verify tab navigation, column rendering, side panel interactions
3. Fix any regressions (type errors, data binding issues)
4. ✅ Checkpoint: All tests pass; no console errors

### Phase 7: Documentation & Release
**Duration:** 30 mins | **PR:** `docs/deliverables-refactor`

1. Update README.md: Document new Deliverables tab columns
2. Create DELIVERABLES_IMPLEMENTATION_GUIDE.md: Usage examples, API contract
3. Tag PR with labels: `refactor`, `ui`, `feature`
4. ✅ Checkpoint: Ready for merge

---

## Risk List & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Type mismatch**: ProjectReviewItem vs ServiceReview vs ServiceItem | Medium | Create `DeliverableRow` union type; map all three sources consistently |
| **Performance**: Unified view joins 3+ tables | Medium | Add indexes on service_id, project_id; lazy-load detail drawer (not all rows) |
| **Feature flag conflicts**: anchorLinks + new drawer | Low | Isolate drawer open logic; anchor linking can remain independent |
| **DB migration blocking**: Alter Table on large ServiceReviews table | Low | Use `ALTER TABLE ... ADD` (non-blocking in SQL Server); run off-peak |
| **API contract backward compatibility**: New fields in response | Low | New fields are optional (nullable); old clients ignore them |
| **Assignee field join**: Users table may not exist or be slow | Medium | Add eager join in `get_project_reviews`; cache Users list if needed |
| **Billing status enum check** constraint on existing data | Low | Use `CHECK (billing_status IS NULL OR billing_status IN (...))` to allow legacy nulls |

---

## Data Gap Resolution Table

| Required Field | Currently Available? | Source | Action | Complexity |
|---|---|---|---|---|
| Phase name | ✅ Yes | Services.phase or ServiceItems.title | Map from service record | Low |
| Deliverable title | ✅ Yes | ServiceItems.title or ServiceReviews.deliverables | Extract/concat | Low |
| Cycle number | ✅ Yes | ServiceReviews.cycle_no | Map directly | Low |
| Assignee | ⚠️ Partial | ServiceReviews.assigned_user_id (FK) | JOIN Users; resolve name | Medium |
| Due date | ✅ Yes | ServiceReviews.due_date | Map directly | Low |
| Status | ✅ Yes | ServiceReviews.status or ServiceItems.status | Map directly | Low |
| Completion date | ❌ No | — | ADD column (additive) | Low |
| Planned date | ✅ Yes | ServiceReviews.planned_date | Rename label in code (alias) | Low |
| Fee | ✅ Partial | Services.lump_sum_fee or ServiceReviews.billing_amount | Select based on context | Low |
| Invoice date | ❌ No | — | ADD column (additive) | Low |
| Billing status | ⚠️ Partial | ServiceReviews.is_billed (boolean) | ADD enum column (additive) | Low |
| Invoice number | ⚠️ Partial | ServiceReviews.invoice_reference (generic) | ADD distinct column (additive) | Low |

---

## Next Steps

1. **Approve audit findings** with product/stakeholder
2. **Schedule Phase 1 (DB migration)** — no UI risk, can be done immediately
3. **Create feature branch:** `feature/deliverables-refactor`
4. **Follow implementation plan steps** in order (Phases 1-7)
5. **Each phase = separate PR** for easier review + rollback if needed
6. **After all phases merge**, coordinate with QA for full regression testing

---

## Appendix: File Path Reference

### Frontend Core
- Entry: `frontend/src/pages/ProjectWorkspacePageV2.tsx`
- Services tab: `frontend/src/components/ProjectServicesTab.tsx`
- Existing side panel: `frontend/src/components/ui/DetailsPanel.tsx`
- Existing drawer pattern: `frontend/src/components/ProjectManagement/IssuesTabContent.tsx`

### Backend Core
- Flask app: `backend/app.py`
- DB functions: `database.py`
- Schema constants: `constants/schema.py`

### Tests
- Existing: `frontend/tests/e2e/project-workspace-v2*.spec.ts`
- New: `frontend/tests/e2e/{services,deliverables}-*.spec.ts`

### SQL
- Migrations: `sql/migrations/`
- Views (optional): `sql/views/vw_project_deliverables.sql`

---

**Audit Completed:** 2026-01-16  
**Auditor:** Senior Full-Stack Codebase Audit Agent  
**Status:** ✅ Ready for Implementation
