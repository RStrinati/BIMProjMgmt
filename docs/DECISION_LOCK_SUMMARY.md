# Implementation Refinement - Decision Lock Summary

**Date:** January 16, 2026  
**Status:** ✅ FINAL - No revisions permitted  
**Scope:** Services + Deliverables refactor technical requirements  
**Authority:** Senior Implementation Refinement Agent

---

## Core Decisions (LOCKED)

### 1. Billing Status Derivation
- **Source:** `ServiceReviews.is_billed` boolean column (existing)
- **Mapping:**
  - `is_billed = 1` → UI displays "Billed"
  - `is_billed = 0` → UI displays "Not billed"
  - `is_billed = NULL` → UI displays "Not billed" or empty
- **Implementation:** Centralized in `backend/utils/billing_utils.py::derive_billing_status()`
- **NO new enum table** created (decision: reuse boolean)

### 2. Invoice Tracking (Date + Number)
- **Invoice Number:** Use existing `invoice_reference` column (no rename)
  - In API: expose as-is (`invoice_reference`)
  - In UI: label as "Invoice number"
- **Invoice Date:** NEW column `invoice_date DATE NULL`
  - Added to: `ServiceReviews`, `ServiceItems`
  - Separate from existing `planned_date` (not aliased)
  - Purpose: Track when invoice was issued (distinct from completion/due dates)

### 3. Completion vs Due Dates
- **Completion Date:** Treat `planned_date` as "Completion date" in UI (no DB rename)
  - In API: expose as `planned_date` (no alias)
  - In UI: label as "Completion date"
- **Due Date:** Existing `due_date` column, label remains "Due date"
- **NO new `completion_date` column** created

### 4. Phase Ownership & Inheritance
- **Phase Owner:** Services table (`ProjectServices.phase`)
  - Single source of truth
  - NOT on ServiceReviews or ServiceItems
  - If missing, added via additive migration
- **Phase Access:** Reviews/Items inherit phase via join to ProjectServices
  - API query: `INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id SELECT ... ps.phase`
  - Exposed in API response as `phase` field

### 5. UI Interaction Pattern
- **Both tabs use Material-UI Drawer** (consistent UX)
  - Services tab: Click service row → Drawer shows finance detail + related deliverables count
  - Deliverables tab: Click deliverable row → Drawer shows full detail (including inherited phase)
- **NO new panel abstractions** (use Drawer consistently)
- **Tab naming:** "Reviews" → "Deliverables" (alignment with business language)

---

## Schema Changes (Additive Only)

| Change | Column | Table | Type | Nullable | Purpose |
|--------|--------|-------|------|----------|---------|
| ADD | `invoice_date` | `ServiceReviews` | DATE | NULL | Billing date tracking |
| ADD | `invoice_date` | `ServiceItems` | DATE | NULL | Billing date tracking (if items in Deliverables) |
| ADD or CONFIRM | `phase` | `ProjectServices` | NVARCHAR(100) | NULL | Phase single source of truth |

**NO column renames, removals, or modifications to existing foreign keys.**

---

## Backend Contract (API Payload)

**All review endpoints must return:**

```json
{
  "review_id": 123,
  "service_id": 45,
  "planned_date": "2026-01-20",        // Raw column name
  "due_date": "2026-01-25",            // Raw column name
  "invoice_date": "2026-02-01",        // NEW FIELD
  "invoice_reference": "INV-001",      // Raw column name
  "is_billed": true,                   // Raw column name
  "phase": "Design Review",            // NEW FIELD (from ProjectServices join)
  "status": "completed",
  "billing_amount": 2500.00
  // ... other fields ...
}
```

**NO API aliases applied** (only UI applies labels/transformations).

---

## Frontend Contract (TypeScript)

**Updated interfaces:**

```typescript
interface ServiceReview {
  // ... existing fields ...
  invoice_date?: string | null;  // NEW
  phase?: string;                // NEW
}

interface Deliverable {  // NEW TYPE
  id: number;
  type: 'review' | 'item';
  completion_date: string;       // Alias: planned_date
  invoice_number?: string;       // Alias: invoice_reference
  invoice_date?: string | null;  // NEW
  billing_status: 'Billed' | 'Not billed';  // Derived: is_billed
  phase?: string;                // Inherited from ProjectServices
  // ... other fields ...
}
```

**Utility functions:**

```typescript
derive_billing_status(is_billed: boolean | null): 'Billed' | 'Not billed'
format_service_review_as_deliverable(review: ServiceReview): Deliverable
```

---

## Acceptance Criteria (Services Tab)

✅ Phase column rendered from `ProjectServices.phase`  
✅ Finance-focused columns: Service Name, Phase, Assigned To, Agreed Fee, Progress %, Claimed to Date  
✅ Row click opens Material-UI Drawer deterministically  
✅ Drawer displays all finance fields correctly  
✅ Drawer close button works  

---

## Acceptance Criteria (Deliverables Tab)

✅ 8 columns render: Service Name, Phase, Completion Date, Due Date, Invoice Number, Invoice Date, Billing Status, Status  
✅ Phase inherited correctly via ProjectServices join  
✅ "Completion date" label shows `planned_date`  
✅ "Invoice date" column shows `invoice_date` (NEW)  
✅ Billing Status derived: "Billed" / "Not billed" from `is_billed`  
✅ Row click opens Deliverable Drawer with all fields  
✅ Drawer close deterministic  

---

## Guardrails (STRICT ENFORCEMENT)

### ✅ ALLOWED
- ✅ Add new columns (`invoice_date`, confirm `phase`)
- ✅ Create utility functions for derivation
- ✅ Update API serialization (expose existing fields)
- ✅ Create new TypeScript interfaces
- ✅ Use Material-UI Drawer for both tabs
- ✅ Rename UI tabs (Reviews → Deliverables)

### ❌ FORBIDDEN
- ❌ Rename database columns
- ❌ Remove/modify existing columns
- ❌ Add `billing_status` enum
- ❌ Add `completion_date` as separate column
- ❌ Move `phase` to ServiceReviews/ServiceItems
- ❌ Create new panel abstractions
- ❌ Propose alternative semantics
- ❌ Widen scope beyond Services & Deliverables

---

## Implementation Order

1. **Database** → Run 3 migration scripts
2. **Backend** → Update `database.py` + create `backend/utils/billing_utils.py`
3. **Frontend Types** → Update `frontend/src/types/api.ts` interfaces
4. **Frontend UI** → Build Services tab + Deliverables tab with Drawers
5. **Test** → Verify acceptance criteria
6. **Deploy** → Migrate DB first, then backend, then frontend

---

## Definition of Done (Abbreviated)

- [ ] 3 SQL migrations merged to `sql/migrations/`
- [ ] `database.py` updated with `invoice_date` + `phase` fields
- [ ] `backend/utils/billing_utils.py` created with derivation logic
- [ ] TypeScript interfaces updated (ServiceReview) + new (Deliverable)
- [ ] Services tab renders + Drawer works
- [ ] Deliverables tab renders 8 columns + Drawer works
- [ ] Phase displayed correctly from ProjectServices
- [ ] Billing status derivation correct
- [ ] No breaking API changes
- [ ] All acceptance criteria verified

---

## Questions Resolved

**Q: Why not rename `planned_date` to `completion_date`?**  
A: Preserves backward compatibility. Rename applied only in UI label, not in schema.

**Q: Why add `invoice_date` instead of using `invoice_reference` for dates?**  
A: `invoice_reference` is a string identifier (e.g., "INV-001"). Date must be separate column.

**Q: Why JOIN ProjectServices for phase instead of adding phase to ServiceReviews?**  
A: Services are the logical phase owner. Reviews inherit phase to enable single-source-of-truth updates.

**Q: Can we use an enum for billing_status?**  
A: No. Existing schema uses boolean `is_billed`. Derivation happens in application layer.

**Q: Can we widen scope to include Tasks or other entities?**  
A: No. Scope is strictly Services + Deliverables only. Tasks follow separate data model (Option A core model).

---

## Finality Statement

**This specification is FINAL.**

- No revisions without formal Change Control Board (CCB) approval
- No alternatives to decisions listed above
- No scope expansion
- Developers must follow this spec exactly

Any deviations require escalation to project technical leadership.

---

**Document:** Services & Deliverables Implementation Specification (LOCKED)  
**Prepared by:** Senior Implementation Refinement Agent  
**Date:** January 16, 2026  
**Effective:** Immediately upon developer assignment

