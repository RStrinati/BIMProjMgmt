# API ↔ UI Field Mapping Reference

**Purpose:** Complete field traceability from database → API → UI  
**Audience:** Frontend developers, QA, documentation  
**Status:** FINAL (January 16, 2026)

---

## Complete Field Mapping Table

| # | Database Column | Table | API Field | API Type | UI Label | UI Component | Notes |
|---|---|---|---|---|---|---|---|
| 1 | `service_id` | ServiceReviews | `service_id` | number | (not displayed) | (mapping only) | Joins to ProjectServices |
| 2 | `review_id` | ServiceReviews | `review_id` | number | (not displayed) | (row identifier) | Primary key |
| 3 | `cycle_no` | ServiceReviews | `cycle_no` | number | Cycle # | Text | Display as "Cycle 1", "Cycle 2" |
| 4 | `planned_date` | ServiceReviews | `planned_date` | string (ISO 8601) | **Completion Date** | Date Picker | ← Changed label in UI |
| 5 | `due_date` | ServiceReviews | `due_date` | string (ISO 8601) | **Due Date** | Date Picker | ← Label unchanged |
| 6 | `invoice_reference` | ServiceReviews | `invoice_reference` | string | **Invoice Number** | Text | ← Changed label in UI |
| 7 | `invoice_date` | ServiceReviews | `invoice_date` | string (ISO 8601) \| null | **Invoice Date** | Date Picker | ← NEW FIELD |
| 8 | `is_billed` | ServiceReviews | `is_billed` | boolean \| null | **Billing Status** | Badge | ← Derived in frontend |
| 9 | N/A (derived) | N/A | `billing_status` | "Billed" \| "Not billed" | **Billing Status** | Badge | Applied only in API response if serializer used |
| 10 | `billing_amount` | ServiceReviews | `billing_amount` | number \| null | Billing Amount | Currency | Optional detail view |
| 11 | `billing_rate` | ServiceReviews | `billing_rate` | number \| null | Billing Rate | Currency | Optional detail view |
| 12 | `status` | ServiceReviews | `status` | string | **Status** | Badge | Values: Planned, In Progress, Completed, Overdue |
| 13 | `disciplines` | ServiceReviews | `disciplines` | string | Disciplines | Text | Semi-colon separated list |
| 14 | `deliverables` | ServiceReviews | `deliverables` | string (JSON) | Deliverables | Expandable | Raw JSON from database |
| 15 | `evidence_links` | ServiceReviews | `evidence_links` | string (JSON) | Evidence Links | Expandable | Raw JSON from database |
| 16 | `actual_issued_at` | ServiceReviews | `actual_issued_at` | string (ISO 8601) \| null | Issued Date | Date | Optional metadata |
| 17 | `weight_factor` | ServiceReviews | `weight_factor` | number \| null | Weight | Number | Optional for calculations |
| 18 | `service_name` | ProjectServices | `service_name` | string | **Service** | Text | Joined via ProjectServices |
| 19 | `phase` | ProjectServices | `phase` | string \| null | **Phase** | Text | ← NEW FIELD (joined) |

---

## Deliverables Table Column Order (8 Columns)

| Order | Field (API) | Label (UI) | Source | Type | Example |
|-------|---|---|---|---|---|
| 1 | `service_name` | Service Name | ServiceReviews.service_id → ProjectServices.service_name | Text | "Design Review" |
| 2 | `phase` | Phase | ProjectServices.phase (via join) | Text | "Schematic Design" |
| 3 | `planned_date` | Completion Date | ServiceReviews.planned_date | Date | "2026-01-20" |
| 4 | `due_date` | Due Date | ServiceReviews.due_date | Date | "2026-01-25" |
| 5 | `invoice_reference` | Invoice Number | ServiceReviews.invoice_reference | Text | "INV-2026-001" |
| 6 | `invoice_date` | Invoice Date | ServiceReviews.invoice_date | Date | "2026-02-01" |
| 7 | `is_billed` (derived) | Billing Status | ServiceReviews.is_billed → "Billed" \| "Not billed" | Badge | "Billed" |
| 8 | `status` | Status | ServiceReviews.status | Badge | "Completed" |

---

## Services Tab Column Order (6 Columns)

| Order | Field (API) | Label (UI) | Source | Type | Example |
|-------|---|---|---|---|---|
| 1 | `service_name` | Service Name | ProjectServices.service_name | Text | "Design Review" |
| 2 | `phase` | Phase | ProjectServices.phase | Text | "Schematic Design" |
| 3 | `assigned_to` \| `assigned_user_id` | Assigned To | ProjectServices.assigned_user_id → lookup | Text | "John Smith" |
| 4 | `agreed_fee` | Agreed Fee | ProjectServices.agreed_fee | Currency | "$25,000.00" |
| 5 | `progress_pct` | Progress % | ProjectServices.progress_pct | Percentage | "60%" |
| 6 | `claimed_to_date` | Claimed to Date | ProjectServices.claimed_to_date | Currency | "$15,000.00" |

---

## Drawer Detail View - Deliverables

**Drawer Layout** (right-side panel, 400-500px wide)

```
┌──────────────────────────────────┐
│ Deliverable Detail               │
├──────────────────────────────────┤
│                                  │
│ Service:           Design Review │
│ Phase:             Schematic     │
│ Type:              Review        │
│ Cycle:             1             │
│                                  │
│ DELIVERY DATES:                  │
│ ├─ Completion Date: 2026-01-20   │
│ ├─ Due Date:       2026-01-25    │
│ └─ Issued:        2026-01-22     │
│                                  │
│ BILLING:                         │
│ ├─ Status:        Billed         │
│ ├─ Invoice #:     INV-2026-001   │
│ ├─ Invoice Date:  2026-02-01     │
│ ├─ Amount:        $2,500.00      │
│ └─ Rate:          $50/hr         │
│                                  │
│ METADATA:                        │
│ ├─ Status:        Completed      │
│ ├─ Disciplines:   Structural, MEP│
│ ├─ Assigned To:   Jane Doe       │
│ └─ Weight:        1.0            │
│                                  │
│ [Edit] [Close]                   │
└──────────────────────────────────┘
```

---

## Drawer Detail View - Services

**Drawer Layout** (right-side panel, 400-500px wide)

```
┌──────────────────────────────────┐
│ Service Detail                   │
├──────────────────────────────────┤
│                                  │
│ Service Name:   Design Review    │
│ Phase:          Schematic Design │
│ Status:         In Progress      │
│                                  │
│ FINANCE:                         │
│ ├─ Agreed Fee:      $25,000.00   │
│ ├─ Progress:        60%          │
│ ├─ Claimed to Date: $15,000.00   │
│ ├─ Remaining:       $10,000.00   │
│ └─ Bill Rule:       By Deliverable│
│                                  │
│ ASSIGNMENT:                      │
│ └─ Assigned To: John Smith       │
│                                  │
│ RELATED DELIVERABLES:            │
│ ├─ Reviews:  3 completed         │
│ ├─ Items:    2 pending           │
│ └─ Total:    5                   │
│                                  │
│ [View All] [Edit] [Close]        │
└──────────────────────────────────┘
```

---

## API Response Examples

### Example 1: ServiceReview (from `/projects/{id}/reviews`)

```json
{
  "review_id": 1001,
  "service_id": 45,
  "cycle_no": 1,
  "planned_date": "2026-01-20",
  "due_date": "2026-01-25",
  "invoice_reference": "INV-2026-001",
  "invoice_date": "2026-02-01",
  "is_billed": true,
  "billing_amount": 2500.00,
  "billing_rate": 50.00,
  "status": "completed",
  "disciplines": "Structural; MEP",
  "deliverables": "{\"items\": [\"submittal review\", \"RFI response\"]}",
  "evidence_links": "{\"links\": []}",
  "actual_issued_at": "2026-01-22",
  "weight_factor": 1.0,
  "service_name": "Design Review Service",
  "phase": "Schematic Design"
}
```

### Example 2: Deliverable (after transformation in frontend)

```json
{
  "id": 1001,
  "type": "review",
  "service_id": 45,
  "service_name": "Design Review Service",
  "title": "Cycle 1",
  "completion_date": "2026-01-20",
  "due_date": "2026-01-25",
  "invoice_number": "INV-2026-001",
  "invoice_date": "2026-02-01",
  "billing_status": "Billed",
  "phase": "Schematic Design",
  "status": "completed",
  "disciplines": "Structural; MEP",
  "billing_amount": 2500.00,
  "is_billed": true,
  "planned_date": "2026-01-20",
  "invoice_reference": "INV-2026-001"
}
```

---

## Derived Fields (Frontend Logic)

### Billing Status Derivation

```typescript
// Input: is_billed (boolean | null | undefined)
// Output: "Billed" | "Not billed"

function derive_billing_status(is_billed) {
  return is_billed ? "Billed" : "Not billed";
}

// Examples:
derive_billing_status(true)   // → "Billed"
derive_billing_status(false)  // → "Not billed"
derive_billing_status(null)   // → "Not billed"
derive_billing_status(undefined) // → "Not billed"
```

### Deliverable Transformation

```typescript
// Input: ServiceReview (from API)
// Output: Deliverable (for UI)

function format_service_review_as_deliverable(review) {
  return {
    id: review.review_id,
    type: 'review',
    service_id: review.service_id,
    service_name: review.service_name,
    title: `Cycle ${review.cycle_no}`,
    
    // Aliases applied here (API → UI names)
    completion_date: review.planned_date,
    due_date: review.due_date,
    invoice_number: review.invoice_reference,
    invoice_date: review.invoice_date,
    
    // Derivation applied here
    billing_status: derive_billing_status(review.is_billed),
    
    // Inheritance applied here
    phase: review.phase,
    
    // Metadata
    status: review.status,
    disciplines: review.disciplines,
    billing_amount: review.billing_amount,
    
    // Keep raw values for reference
    is_billed: review.is_billed,
    planned_date: review.planned_date,
    invoice_reference: review.invoice_reference,
  };
}
```

---

## Edge Cases & Null Handling

| Field | If NULL | Display |
|-------|---------|---------|
| `planned_date` | Missing (required) | Error / Empty row |
| `due_date` | NULL | Empty cell or "—" |
| `invoice_date` | NULL | Empty cell or "—" |
| `invoice_reference` | NULL | Empty cell or "—" |
| `is_billed` | NULL | "Not billed" (default) |
| `phase` | NULL | Empty cell or "—" |
| `service_name` | NULL | Error (FK constraint) |

---

## TypeScript Type Definitions

```typescript
// ========== ServiceReview (from API) ==========
interface ServiceReview {
  review_id: number;
  service_id: number;
  cycle_no: number;
  planned_date: string;           // ISO 8601
  due_date?: string;               // ISO 8601
  invoice_reference?: string;
  invoice_date?: string | null;    // ISO 8601 or null
  is_billed?: boolean | null;
  billing_amount?: number | null;
  billing_rate?: number | null;
  status: string;
  disciplines?: string;
  deliverables?: string;           // JSON string
  evidence_links?: string;         // JSON string
  actual_issued_at?: string;
  weight_factor?: number | null;
  service_name?: string;
  phase?: string;                  // Inherited from ProjectServices
}

// ========== Deliverable (frontend model) ==========
interface Deliverable {
  id: number;
  type: 'review' | 'item';
  service_id: number;
  service_name?: string;
  title?: string;
  
  // Aliased fields
  completion_date: string;         // from planned_date
  due_date?: string;
  invoice_number?: string;         // from invoice_reference
  invoice_date?: string | null;
  
  // Derived field
  billing_status: 'Billed' | 'Not billed';  // from is_billed
  
  // Inherited field
  phase?: string;
  
  // Metadata
  status: string;
  disciplines?: string;
  billing_amount?: number | null;
  assigned_to?: string;
  
  // Raw values (for advanced access)
  is_billed?: boolean | null;
  planned_date?: string;
  invoice_reference?: string;
}
```

---

## Testing Scenarios

### Scenario 1: Complete Review (All Fields Populated)

| Field | Value | Expected Display |
|-------|-------|------------------|
| `planned_date` | "2026-01-20" | "Completion Date: 2026-01-20" |
| `due_date` | "2026-01-25" | "Due Date: 2026-01-25" |
| `invoice_reference` | "INV-2026-001" | "Invoice Number: INV-2026-001" |
| `invoice_date` | "2026-02-01" | "Invoice Date: 2026-02-01" |
| `is_billed` | `true` | Badge: "Billed" (green) |
| `phase` | "Schematic Design" | "Phase: Schematic Design" |

### Scenario 2: Incomplete Review (Some Nulls)

| Field | Value | Expected Display |
|-------|-------|------------------|
| `planned_date` | "2026-01-20" | "Completion Date: 2026-01-20" |
| `due_date` | `null` | "Due Date: —" (empty) |
| `invoice_reference` | `null` | "Invoice Number: —" (empty) |
| `invoice_date` | `null` | "Invoice Date: —" (empty) |
| `is_billed` | `false` | Badge: "Not billed" (gray) |
| `phase` | `null` | "Phase: —" (empty) |

### Scenario 3: Unbilled Review

| Field | Value | Expected Display |
|-------|-------|------------------|
| `is_billed` | `false` | Badge: "Not billed" |
| `invoice_reference` | `null` | "Invoice Number: —" |
| `invoice_date` | `null` | "Invoice Date: —" |
| `billing_amount` | `0.00` \| `null` | "Billing Amount: $0.00" or "—" |

---

## Verification Checklist

Use this checklist to verify mapping correctness:

- [ ] All 8 Deliverables columns render in correct order
- [ ] Phase displays correctly (test with and without null)
- [ ] Completion Date shows `planned_date` with correct label
- [ ] Invoice Number shows `invoice_reference` with correct label
- [ ] Invoice Date shows `invoice_date` (or empty if null)
- [ ] Billing Status shows "Billed" when `is_billed = true`
- [ ] Billing Status shows "Not billed" when `is_billed = false` or null
- [ ] Drawer opens when clicking deliverable row
- [ ] All fields in drawer match Deliverable interface
- [ ] Phase inherited correctly in drawer
- [ ] No null value errors in console

---

**Reference:** For full implementation details, see [SERVICES_DELIVERABLES_IMPLEMENTATION_SPEC.md](./SERVICES_DELIVERABLES_IMPLEMENTATION_SPEC.md)

