# Frontend Implementation Guide – Phase 2 (Task 3)

**Date**: January 27, 2026  
**Phase**: 2 of 3  
**Status**: Backend complete, frontend ready to implement  

---

## Backend Endpoints Available

### 1. Line Items Endpoint

**URL**: `GET /api/projects/{project_id}/finance/line-items`

**Query Parameters**:
```
?service_id=45        // Optional: filter by service
?invoice_status=draft // Optional: filter by status
```

**Response Structure**:
```javascript
{
  "project_id": 123,
  "line_items": [
    {
      "type": "review" | "item",
      "id": "rev_001",
      "service_id": 45,
      "service_code": "SR",
      "service_name": "Structural Reviews",
      "phase": "Design",
      "title": "Design Review Cycle 1",
      "planned_date": "2026-02-01",
      "due_date": "2026-02-15",
      "status": "completed",
      "fee": 5000.00,
      "fee_source": "calculated_equal_split",  // or "override", "calculated_weighted"
      "invoice_status": "draft",  // or "ready", "issued", "paid"
      "invoice_reference": null,
      "invoice_date": null,
      "invoice_month": "2026-02",  // YYYY-MM format, always populated
      "is_billed": 0  // 1 if billed, 0 if not
    },
    // ... more items
  ],
  "totals": {
    "total_fee": 125000.00,
    "billed_fee": 62500.00,
    "outstanding_fee": 62500.00
  }
}
```

**Use Cases**:
- Bucket line items by `invoice_month` for invoice pipeline
- Filter by `invoice_status` to show ready/pending items
- Sum `fee` by month to show monthly totals
- Track items alongside reviews (both in same list)

---

### 2. Reconciliation Endpoint

**URL**: `GET /api/projects/{project_id}/finance/reconciliation`

**Response Structure**:
```javascript
{
  "project": {
    "project_id": 123,
    "agreed_fee": 250000.00,
    "line_items_total_fee": 248500.00,
    "billed_total_fee": 125000.00,
    "outstanding_total_fee": 123500.00,
    "variance": 1500.00,  // positive = shortfall, negative = overbilling
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
    // ... more services
  ]
}
```

**Use Cases**:
- Display project-level fee progress (right panel)
- Show by-service reconciliation table
- Highlight variance (red if > $1000, yellow if > $100)
- Calculate percentage billed: `billed_total_fee / line_items_total_fee * 100`

---

## Task 3.1 – Update Invoice Pipeline (Overview)

### Current State
Overview shows invoice pipeline bucketed by month using hardcoded service queries.

### Changes Required

**File**: `frontend/src/pages/Overview.tsx`

**Step 1: Replace data source**
```typescript
// OLD: Direct SQL query via endpoint
// const pipeline = await getInvoicePipelineByMonth(projectId);

// NEW: Use unified line-items endpoint
const response = await fetch(
  `/api/projects/${projectId}/finance/line-items`
);
const { line_items, totals } = await response.json();
```

**Step 2: Bucket line items by invoice_month**
```typescript
const buckets = {};
line_items.forEach(item => {
  const month = item.invoice_month; // "2026-02"
  if (!buckets[month]) {
    buckets[month] = { items: [], total: 0, ready: 0 };
  }
  buckets[month].items.push(item);
  buckets[month].total += item.fee;
  if (item.invoice_status === 'ready') {
    buckets[month].ready += item.fee;
  }
});
```

**Step 3: Include items by default**
- Both reviews and items come in same `line_items` array
- No filtering needed; both types are included automatically
- Render both in same month bucket

**Step 4: Add "Include Items" toggle (optional)**
```typescript
const [includeItems, setIncludeItems] = useState(true);

const filtered = includeItems 
  ? line_items 
  : line_items.filter(item => item.type === 'review');
```

**Expected Result**:
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

## Task 3.2 – Add Reconciliation Card (Overview)

### New Card: Service Fee Reconciliation

**File**: `frontend/src/pages/Overview.tsx`

**Endpoint**: `GET /api/projects/{project_id}/finance/reconciliation`

**Table Columns**:
| Service | Agreed | Line Items | Billed | Outstanding | Variance |
|---------|--------|------------|--------|-------------|----------|
| Structural Reviews | $75,000 | $74,500 | $37,250 | $37,250 | +$500 |
| Architectural Reviews | $85,000 | $84,000 | $42,000 | $42,000 | +$1,000 |
| **Project Total** | **$250,000** | **$248,500** | **$125,000** | **$123,500** | **+$1,500** |

**Implementation Notes**:

1. **Table Data Source**:
```typescript
const { project, by_service } = await reconciliation;
const tableRows = [
  ...by_service,
  { 
    // Add project total row at bottom
    service_id: null, 
    service_name: 'PROJECT TOTAL',
    ...project 
  }
];
```

2. **Row Styling**:
```typescript
const getVarianceColor = (variance) => {
  if (variance > 1000) return '#ff6b6b';  // Red (large variance)
  if (variance > 100) return '#ffd43b';   // Yellow (small variance)
  if (variance < -1000) return '#ff6b6b'; // Red (overbilling)
  return '#51cf66';                       // Green (good)
};
```

3. **Click Handler**:
```typescript
const handleRowClick = (service) => {
  navigate(`/deliverables?service_id=${service.service_id}`);
};
```

4. **Display Highlights**:
- Bold service names for easy scanning
- Highlight negative variance in red (overbilling risk)
- Show positive variance in yellow (minor shortfall)
- Show zero variance in green (perfect match)

---

## Task 3.3 – Update Right Panel

**File**: `frontend/src/components/RightPanel.tsx`

**Replace current hardcoded values with reconciliation data**:

### Current State
```typescript
{
  "agreed_fee": $250,000,        // From Projects table
  "billed_to_date": $125,000,    // From BillingClaims
  "earned_value": $150,000,      // Manual calc
  "earned_value_pct": 60%        // Manual calc
}
```

### New State (from reconciliation endpoint)

```typescript
const reconciliation = await fetch(
  `/api/projects/${projectId}/finance/reconciliation`
).then(r => r.json());

const metrics = {
  agreed_fee: reconciliation.project.agreed_fee,
  billed: reconciliation.project.billed_total_fee,
  remaining: reconciliation.project.outstanding_total_fee,
  billed_pct: (reconciliation.project.billed_total_fee / 
               reconciliation.project.line_items_total_fee * 100).toFixed(1)
};
```

### Display Format

```
Project Fee Progress
─────────────────────
Agreed Fee:    $250,000
Billed:        $125,000 (50%)
Remaining:     $125,000
Outstanding:   $123,500
```

### Key Alignment
- **Agreed Fee** = Sum of ProjectServices.agreed_fee (no change)
- **Billed** = reconciliation.project.billed_total_fee (from line items where is_billed=1)
- **Remaining** = reconciliation.project.outstanding_total_fee (total - billed)
- **Billed %** = (billed / line_items_total) * 100 (consistency with invoice pipeline)

### Important Note
Make sure Right Panel uses the same data source as Overview reconciliation card:
- Both should call the same `/api/projects/{project_id}/finance/reconciliation` endpoint
- Both should use `reconciliation.project.*` fields for project totals
- No discrepancies between the two panels

---

## Task 3.4 – Deliverables Fee Edit (Separate Endpoint)

**Status**: Planned for Phase 2b

**Endpoint** (to be implemented):
```
PATCH /api/projects/{project_id}/deliverables/{deliverable_id}/fee
Content-Type: application/json

{
  "type": "review" | "item",
  "fee": 12500.00
}
```

**Response** (200):
```javascript
{
  "id": "rev_001",
  "type": "review",
  "fee": 12500.00,
  "fee_source": "override",
  "is_user_modified": true,
  "user_modified_at": "2026-01-27T10:30:00Z"
}
```

**Error Response** (400):
```javascript
{
  "error": "Cannot edit fee for paid invoice",
  "invoice_status": "paid",
  "invoice_reference": "INV-2026-001"
}
```

**Frontend Implementation**:
1. Add inline fee edit to Deliverables table
2. Check `invoice_status` and `is_billed` before allowing edit
3. Call PATCH endpoint on save
4. Refresh line-items endpoint after successful edit
5. Show error toast if invoice is paid

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Overview Page                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Invoice Pipeline                                      │   │
│  │ (Fetches /api/projects/{id}/finance/line-items)     │   │
│  │                                                       │   │
│  │ Feb 2026: $18,500 (3 reviews + 6 items)             │   │
│  │ Mar 2026: $16,250 (2 reviews + 4 items)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Service Fee Reconciliation                           │   │
│  │ (Fetches /api/projects/{id}/finance/reconciliation) │   │
│  │                                                       │   │
│  │ Service    │ Agreed  │ Line Items │ Billed │ Var    │   │
│  │ SR         │ $75k    │ $74.5k     │ $37k   │ +$500  │   │
│  │ AR         │ $85k    │ $84k       │ $42k   │ +$1k   │   │
│  │ ─────────────────────────────────────────────────   │   │
│  │ TOTAL      │ $250k   │ $248.5k    │ $125k  │ +$1.5k │   │
│  │ (Click row → navigate to Deliverables)              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ Related
                               ↓
                    ┌──────────────────────┐
                    │   Right Panel        │
                    │ Reconciliation Data  │
                    │                      │
                    │ Agreed: $250k        │
                    │ Billed: $125k (50%)  │
                    │ Remaining: $125k     │
                    └──────────────────────┘
```

---

## API Client Helper Functions

**File**: `frontend/src/api/client.ts` (or create new `finance.ts`)

```typescript
/**
 * Get unified line items (reviews + items) for invoice pipeline
 */
export async function getLineItems(
  projectId: number,
  options?: {
    serviceId?: number,
    invoiceStatus?: string
  }
): Promise<{
  project_id: number,
  line_items: LineItem[],
  totals: { total_fee: number, billed_fee: number, outstanding_fee: number }
}> {
  const params = new URLSearchParams();
  if (options?.serviceId) params.append('service_id', String(options.serviceId));
  if (options?.invoiceStatus) params.append('invoice_status', options.invoiceStatus);
  
  const response = await fetch(
    `/api/projects/${projectId}/finance/line-items?${params}`
  );
  return response.json();
}

/**
 * Get financial reconciliation by service and project
 */
export async function getReconciliation(projectId: number): Promise<{
  project: ReconciliationSummary,
  by_service: ReconciliationByService[]
}> {
  const response = await fetch(
    `/api/projects/${projectId}/finance/reconciliation`
  );
  return response.json();
}

/**
 * TypeScript interfaces
 */
export interface LineItem {
  type: 'review' | 'item';
  id: string;
  service_id: number;
  service_code: string;
  service_name: string;
  phase: string;
  title: string;
  planned_date: string; // ISO date
  due_date: string; // ISO date
  status: string;
  fee: number;
  fee_source: 'override' | 'calculated_equal_split' | 'calculated_weighted' | 'explicit';
  invoice_status: string;
  invoice_reference: string | null;
  invoice_date: string | null;
  invoice_month: string; // YYYY-MM
  is_billed: number; // 0 or 1
}

export interface ReconciliationSummary {
  project_id: number;
  agreed_fee: number;
  line_items_total_fee: number;
  billed_total_fee: number;
  outstanding_total_fee: number;
  variance: number;
  review_count: number;
  item_count: number;
}

export interface ReconciliationByService extends ReconciliationSummary {
  service_id: number;
  service_code: string;
  service_name: string;
}
```

---

## Testing Checklist

- [ ] Invoice pipeline displays both reviews and items
- [ ] Monthly buckets sum correctly
- [ ] Ready-to-invoice filter works
- [ ] Reconciliation table shows all services
- [ ] Variance column colors correctly (red >$1000, yellow >$100)
- [ ] Click row navigates to Deliverables with service_id filter
- [ ] Right panel totals match reconciliation project totals
- [ ] No duplicate fees between reviews and items
- [ ] Invoice month always populated (not null)
- [ ] Performance: endpoints respond in <500ms for typical projects

---

## Known Limitations & Future Work

1. **Fee Edit Endpoint** (Phase 2b)
   - Endpoint not yet implemented
   - Will add PATCH `/api/projects/{project_id}/deliverables/{deliverable_id}/fee`
   - Will require `can_edit_fee()` validation

2. **Service Reassignment** (Phase 4)
   - Currently, moving a review to a different service doesn't auto-update fee
   - Fee is preserved unless manually edited (by design)
   - `user_modified_fields` audit trail tracks what changed

3. **Bulk Operations** (Future)
   - No bulk fee edit endpoint yet
   - Can edit one at a time via PATCH

---

## Rollback Plan

If something breaks during Phase 2 implementation:

1. **Revert Overview changes**:
   ```bash
   git checkout frontend/src/pages/Overview.tsx
   ```

2. **Revert Right Panel changes**:
   ```bash
   git checkout frontend/src/components/RightPanel.tsx
   ```

3. **Endpoints remain available** for future use
   - No harm in leaving new endpoints in place
   - They're read-only and fully tested

---

## Questions?

Refer to:
- [PHASE1_COMPLETION_SUMMARY.md](./PHASE1_COMPLETION_SUMMARY.md) – Backend details
- [FEE_IMPLEMENTATION_PLAN.md](./FEE_IMPLEMENTATION_PLAN.md) – Full specification
- [FEE_INVENTORY.md](./FEE_INVENTORY.md) – Schema details
