# Fee Unification Implementation Plan

**Mission**: Make Deliverables, Overview, and the right panel use one consistent fee model.

**Status**: Task 0.1 ✅ Complete – Fee inventory documented  
**Current Phase**: Task 1 – Fee governance and backend logic

---

## Task 1: Fee Governance Using Existing Schema

### 1.1 Backend Fee Resolution Service

**File**: `services/fee_resolver_service.py` (new)

**Purpose**: Centralized logic for resolving "fee_final" for reviews and items.

**Key Functions**:

```python
def resolve_review_fee(review_row: dict) -> tuple[float, str]:
    """
    Resolve the final fee for a single ServiceReview.
    
    Returns: (fee_value, fee_source)
    fee_source in ['override', 'calculated_equal_split', 'calculated_weighted']
    """
    # Implementation using fee resolution logic from FEE_INVENTORY.md

def resolve_item_fee(item_row: dict) -> tuple[float, str]:
    """
    Resolve the final fee for a single ServiceItem.
    
    Returns: (fee_value, fee_source)
    fee_source in ['override', 'explicit']
    """

def can_edit_fee(invoice_status: str, is_billed: bit) -> bool:
    """
    Check if fee can be edited based on invoice status.
    
    Prevents editing when invoice_status IN ('issued', 'paid')
    or is_billed = 1
    """
```

**Database Access**:
- Use `database_pool.py` for all connections
- Use `constants.schema` for all table/column references
- NO raw SQL strings

---

### 1.2 Deliverables Fee Edit Endpoint

**File**: `backend/app.py` → new route

**Endpoint**: `PATCH /api/projects/{project_id}/deliverables/{deliverable_id}/fee`

**Payload**:
```json
{
  "type": "review|item",
  "fee": 12500.00
}
```

**Response Success** (200):
```json
{
  "id": "review_id|item_id",
  "type": "review|item",
  "fee": 12500.00,
  "fee_source": "override",
  "is_user_modified": true,
  "user_modified_at": "2026-01-27T10:30:00Z"
}
```

**Response Error** (400):
```json
{
  "error": "Cannot edit fee for paid invoice",
  "invoice_status": "paid",
  "invoice_reference": "INV-2026-001"
}
```

**Implementation Notes**:
- For reviews: update `ServiceReviews.billing_amount`
- For items: update `ServiceItems.fee_amount`
- Set `is_user_modified = 1`
- Set `user_modified_at = NOW()`
- Append field name to `user_modified_fields` JSON array

---

## Task 2: Unified Finance Endpoints

### 2.1 Line Items Endpoint

**File**: `backend/app.py` → new route

**Endpoint**: `GET /api/projects/{project_id}/finance/line-items`

**Query Parameters**:
- `service_id` (optional): filter by service
- `status` (optional): filter by invoice status

**Response** (200):
```json
{
  "project_id": 123,
  "line_items": [
    {
      "type": "review",
      "id": "rev_1001",
      "service_id": 45,
      "service_code": "SR",
      "service_name": "Structural Reviews",
      "phase": "Design",
      "title": "Design Review Cycle 1",
      "planned_date": "2026-02-01",
      "due_date": "2026-02-15",
      "status": "completed",
      "fee": 12500.00,
      "fee_source": "calculated_equal_split",
      "invoice_status": "ready",
      "invoice_reference": null,
      "invoice_date": null,
      "invoice_month": "2026-02"
    },
    {
      "type": "item",
      "id": "item_2001",
      "service_id": 45,
      "service_code": "SR",
      "service_name": "Structural Reviews",
      "phase": "Design",
      "title": "Weekly Progress Report",
      "planned_date": "2026-02-08",
      "due_date": "2026-02-08",
      "status": "completed",
      "fee": 2500.00,
      "fee_source": "override",
      "invoice_status": "draft",
      "invoice_reference": null,
      "invoice_date": null,
      "invoice_month": "2026-02"
    }
  ],
  "totals": {
    "total_fee": 15000.00,
    "billed_fee": 0.00,
    "outstanding_fee": 15000.00
  }
}
```

**SQL Implementation**:
```sql
-- Combine reviews + items using UNION
SELECT 
    'review' as type,
    review_id as id,
    service_id,
    service_code,
    service_name,
    phase,
    -- ... more columns
    billing_amount as fee,  -- resolve using fee_resolver_service
    -- invoice_month_final for bucketing
FROM ServiceReviews sr
JOIN ProjectServices ps ON sr.service_id = ps.service_id
WHERE sr.project_id = @project_id

UNION ALL

SELECT 
    'item' as type,
    item_id as id,
    service_id,
    service_code,
    service_name,
    phase,
    title,
    planned_date,
    due_date,
    status,
    fee_amount as fee,  -- resolve using fee_resolver_service
    invoice_month_final,
    -- ... more columns
FROM ServiceItems si
JOIN ProjectServices ps ON si.service_id = ps.service_id
WHERE si.project_id = @project_id
```

**Key Implementation Detail**:
- After SQL fetch, call `resolve_review_fee()` or `resolve_item_fee()` on each row
- Populate `fee` and `fee_source` in the response
- For `invoice_month`, use `invoice_month_final` (already resolved in schema)

---

### 2.2 Reconciliation Endpoint

**File**: `backend/app.py` → new route

**Endpoint**: `GET /api/projects/{project_id}/finance/reconciliation`

**Response** (200):
```json
{
  "project": {
    "project_id": 123,
    "agreed_fee": 250000.00,
    "line_items_total_fee": 248500.00,
    "billed_total_fee": 125000.00,
    "outstanding_total_fee": 123500.00,
    "variance": 1500.00,
    "review_count": 12,
    "item_count": 24
  },
  "by_service": [
    {
      "service_id": 45,
      "service_code": "SR",
      "service_name": "Structural Reviews",
      "agreed_fee": 75000.00,
      "line_items_total_fee": 74500.00,
      "billed_total_fee": 37250.00,
      "outstanding_total_fee": 37250.00,
      "variance": 500.00,
      "review_count": 4,
      "item_count": 8
    },
    {
      "service_id": 46,
      "service_code": "AR",
      "service_name": "Architectural Reviews",
      "agreed_fee": 85000.00,
      "line_items_total_fee": 84000.00,
      "billed_total_fee": 42000.00,
      "outstanding_total_fee": 42000.00,
      "variance": 1000.00,
      "review_count": 5,
      "item_count": 10
    }
  ]
}
```

**SQL Implementation**:

```sql
-- Aggregate by service
WITH service_line_items AS (
  SELECT 
    ps.service_id,
    ps.service_code,
    ps.service_name,
    SUM(sr.billing_amount) as review_total,
    SUM(CASE WHEN sr.is_billed = 1 THEN sr.billing_amount ELSE 0 END) as review_billed,
    COUNT(*) as review_count
  FROM ServiceReviews sr
  JOIN ProjectServices ps ON sr.service_id = ps.service_id
  WHERE sr.project_id = @project_id
  GROUP BY ps.service_id, ps.service_code, ps.service_name
),
service_items AS (
  SELECT 
    ps.service_id,
    SUM(si.fee_amount) as item_total,
    SUM(CASE WHEN si.is_billed = 1 THEN si.fee_amount ELSE 0 END) as item_billed,
    COUNT(*) as item_count
  FROM ServiceItems si
  JOIN ProjectServices ps ON si.service_id = ps.service_id
  WHERE si.project_id = @project_id
  GROUP BY ps.service_id
)
SELECT 
  ps.service_id,
  ps.service_code,
  ps.service_name,
  ps.agreed_fee,
  ISNULL(sli.review_total, 0) + ISNULL(sit.item_total, 0) as line_items_total_fee,
  ISNULL(sli.review_billed, 0) + ISNULL(sit.item_billed, 0) as billed_total_fee,
  ISNULL(sli.review_count, 0) as review_count,
  ISNULL(sit.item_count, 0) as item_count
FROM ProjectServices ps
LEFT JOIN service_line_items sli ON ps.service_id = sli.service_id
LEFT JOIN service_items sit ON ps.service_id = sit.service_id
WHERE ps.project_id = @project_id
```

---

## Task 3: Update Overview + Right Panel

### 3.1 Overview Invoice Pipeline

**File**: `frontend/src/pages/Overview.tsx`

**Changes**:
1. Add endpoint call to `GET /api/projects/{project_id}/finance/line-items`
2. Include **items by default** in pipeline buckets (already in endpoint)
3. Optional toggle "Include Items" (default ON)
4. Bucket by `invoice_month` from response

**Visualization**:
```
Invoice Pipeline (with Items)

February 2026
├─ 3 reviews (SR, AR, MEP)
├─ 6 items (weekly reports, submittals)
├─ Total: $18,500
└─ Ready to invoice: $12,000 (4 items)

March 2026
├─ 2 reviews
├─ 4 items
├─ Total: $16,250
└─ Ready to invoice: $8,125
```

---

### 3.2 Add Reconciliation Card

**File**: `frontend/src/pages/Overview.tsx`

**New Card**: "Service Fee Reconciliation"

**Table Columns**:
| Service | Agreed | Line Items | Billed | Outstanding | Variance |
|---------|--------|------------|--------|-------------|----------|
| Structural Reviews | $75,000 | $74,500 | $37,250 | $37,250 | +$500 |
| Architectural Reviews | $85,000 | $84,000 | $42,000 | $42,000 | +$1,000 |
| **Project Total** | **$250,000** | **$248,500** | **$125,000** | **$123,500** | **+$1,500** |

**Interaction**:
- Click row → navigate to `/deliverables?service_id=45` (filtered by service)
- Variance column highlighted red if > $1000, yellow if > $100

---

### 3.3 Right Panel Progress (Update)

**File**: `frontend/src/components/RightPanel.tsx`

**Update Fields**:

| Field | Source | Calculation |
|-------|--------|-------------|
| Agreed Fee | Reconciliation endpoint → `project.agreed_fee` | Sum of `ProjectServices.agreed_fee` |
| Billed | Reconciliation endpoint → `project.billed_total_fee` | Sum where `is_billed = 1` |
| Remaining | Reconciliation endpoint → `project.outstanding_total_fee` | `line_items_total - billed` |
| Billed % | `billed_total_fee / line_items_total_fee * 100` | Consistent with line items |

**Example**:
```
Project Fee Progress
─────────────────────
Agreed Fee:    $250,000
Billed:        $125,000 (50%)
Remaining:     $125,000
Outstanding:   $123,500
```

---

## Task 4: Service Reassignment Policy

**No schema changes required.**

**Behavior**:
1. User moves review from Service A to Service B
2. Review's `billing_amount` remains unchanged
3. Set `is_user_modified = 1` to indicate override
4. Reconciliation now shows:
   - Service A: line items total is less
   - Service B: line items total is more
   - Variance appears in both services
5. Finance team can see audit trail via `user_modified_fields`

---

## Implementation Checklist

### Backend Services (Python)
- [ ] Create `services/fee_resolver_service.py`
  - [ ] `resolve_review_fee(review_row) → (fee, source)`
  - [ ] `resolve_item_fee(item_row) → (fee, source)`
  - [ ] `can_edit_fee(invoice_status, is_billed) → bool`
  - [ ] Unit tests in `tests/test_fee_resolver.py`

### Backend Endpoints (Flask)
- [ ] `GET /api/projects/{project_id}/finance/line-items`
  - [ ] SQL: Union reviews + items
  - [ ] Call fee resolver on each row
  - [ ] Return with `fee` and `fee_source`
  - [ ] Include totals aggregate
  - [ ] Integration test in `tests/test_finance_endpoints.py`

- [ ] `GET /api/projects/{project_id}/finance/reconciliation`
  - [ ] SQL: Aggregate by service + project
  - [ ] Return `by_service` and `project` totals
  - [ ] Include variance, counts
  - [ ] Integration test

- [ ] `PATCH /api/projects/{project_id}/deliverables/{deliverable_id}/fee`
  - [ ] Validate invoice status
  - [ ] Update `billing_amount` (review) or `fee_amount` (item)
  - [ ] Set `is_user_modified = 1`, `user_modified_at = NOW()`
  - [ ] Append to `user_modified_fields` JSON
  - [ ] Return updated row
  - [ ] Integration test

### Frontend Components (React + TypeScript)
- [ ] Update `frontend/src/pages/Overview.tsx`
  - [ ] Call `/api/projects/{project_id}/finance/line-items`
  - [ ] Bucket by `invoice_month`
  - [ ] Include items in pipeline by default
  - [ ] Add "Include Items" toggle
  - [ ] Tests: Playwright test for invoice pipeline with items

- [ ] Add Reconciliation Card to Overview
  - [ ] Call `/api/projects/{project_id}/finance/reconciliation`
  - [ ] Render service-level table
  - [ ] Row click → navigate to Deliverables filtered by service_id
  - [ ] Highlight variance column (red > $1000, yellow > $100)
  - [ ] Tests: Playwright test for reconciliation row click

- [ ] Update `frontend/src/components/RightPanel.tsx`
  - [ ] Fetch reconciliation endpoint
  - [ ] Update Agreed Fee, Billed, Remaining, Billed %
  - [ ] Ensure totals match Overview reconciliation
  - [ ] Tests: Verify totals consistency

### Frontend Deliverables (Edit Fee)
- [ ] Update `frontend/src/pages/Deliverables.tsx`
  - [ ] Add inline fee edit for reviews and items
  - [ ] Call `PATCH /api/projects/{project_id}/deliverables/{deliverable_id}/fee`
  - [ ] Show error if invoice is paid
  - [ ] Refresh line-items after edit
  - [ ] Tests: Playwright test for fee edit and Overview refresh

### Testing
- [ ] Unit tests: `tests/test_fee_resolver.py`
- [ ] Integration tests: `tests/test_finance_endpoints.py`
- [ ] Playwright tests: `frontend/tests/finance.spec.ts`
  - [ ] Invoice pipeline includes items ✓
  - [ ] Reconciliation table shows variance ✓
  - [ ] Fee edit updates Overview totals ✓
  - [ ] Right panel totals match reconciliation ✓

---

## Database Schema (No Changes)

✅ All required columns already exist:
- `ServiceReviews.billing_amount`, `fee_amount`, `weight_factor`
- `ServiceItems.fee_amount`
- `ProjectServices.agreed_fee`, `review_count_planned`
- `ServiceReviews/Items.is_billed`, `invoice_status`, `invoice_month_final`
- `ServiceReviews/Items.is_user_modified`, `user_modified_fields`

**No migration scripts needed.**

---

## Rollback Plan

If any task fails:
1. Fee resolver service is pure logic – no side effects
2. Endpoints are read-only (except fee PATCH)
3. PATCH endpoint safeguards with `can_edit_fee()` check
4. Revert Overview/RightPanel to hardcoded queries (5 min)

---

## Success Criteria

- [x] Task 0.1: Fee inventory complete (existing columns documented)
- [ ] Task 1: Fee resolver service deployed + tested
- [ ] Task 2: Finance endpoints live + returning correct data
- [ ] Task 3: Overview + Right Panel using reconciliation totals
- [ ] Task 4: Service reassignment preserves fee (no action needed)
- [ ] Task 5: All tests passing (unit, integration, Playwright)
- [ ] Variance visible in reconciliation card
- [ ] Click-through from variance to Deliverables works
- [ ] Deliverables fee edit updates Overview after refresh
