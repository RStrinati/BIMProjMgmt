# Services & Deliverables Implementation - Quick Reference

**Document:** Implementation Summary (1-page)  
**Audience:** Developers implementing the refactor  
**Authority:** FINAL (January 16, 2026)

---

## What Changed (High Level)

| Item | What | Why |
|------|------|-----|
| **UI Tabs** | Reviews → **Deliverables** | Align with business terminology |
| **Services Tab** | NEW drawer-based detail view | Finance-focused, aligned interaction pattern |
| **Deliverables Tab** | Unified table (reviews + items) | Single source of delivery truth |
| **Schema** | Add `invoice_date` columns + confirm `phase` | Complete billing record + phase inheritance |
| **Backend** | Join ProjectServices for phase; expose `invoice_date` | Enable phase visibility; billing completeness |
| **Frontend** | New `Deliverable` interface; field aliases | Unified API contract |

---

## Schema Additions (SQL)

**File:** `sql/migrations/2026_01_16_*.sql`

```sql
-- 1. ServiceReviews
ALTER TABLE dbo.ServiceReviews ADD invoice_date DATE NULL;

-- 2. ServiceItems
ALTER TABLE dbo.ServiceItems ADD invoice_date DATE NULL;

-- 3. ProjectServices (if missing)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
              WHERE TABLE_NAME='ProjectServices' AND COLUMN_NAME='phase')
BEGIN
  ALTER TABLE dbo.ProjectServices ADD phase NVARCHAR(100) NULL;
END;
```

---

## Backend Changes (Python)

**File:** `database.py`

1. **Update review queries** to include:
   ```python
   # In SELECT clause:
   {S.ServiceReviews.INVOICE_DATE},
   
   # In JOIN:
   INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
   SELECT ... ps.phase ...
   ```

2. **Add to response dict:**
   ```python
   'invoice_date': row[N],
   'phase': row[M],
   ```

**File:** `backend/utils/billing_utils.py` (create)

```python
def derive_billing_status(is_billed: bool | None) -> str:
    return "Billed" if is_billed else "Not billed"
```

---

## Frontend Changes (TypeScript)

**File:** `frontend/src/types/api.ts`

```typescript
// Update ServiceReview interface
interface ServiceReview {
  // ... existing fields ...
  invoice_date?: string | null;    // NEW
  phase?: string;                  // NEW
}

// Create new Deliverable interface
interface Deliverable {
  id: number;
  type: 'review' | 'item';
  service_id: number;
  completion_date: string;         // Alias: planned_date
  invoice_number?: string;         // Alias: invoice_reference
  invoice_date?: string | null;    // NEW
  billing_status: 'Billed' | 'Not billed';  // Derived: is_billed
  phase?: string;
  // ... other fields ...
}
```

**File:** `frontend/src/utils/billingUtils.ts` (create)

```typescript
export const derive_billing_status = (is_billed: boolean | null | undefined): 'Billed' | 'Not billed' => {
  return is_billed ? 'Billed' : 'Not billed';
};
```

---

## UI Changes

### Services Tab
- **Column Order:** Service Name, Phase, Assigned To, Agreed Fee, Progress %, Claimed to Date
- **Interaction:** Click row → Material-UI Drawer (right side)
- **Drawer Content:** Finance fields + related deliverables count

### Deliverables Tab
- **Columns (8 total):** Service Name, Phase, Completion Date, Due Date, Invoice Number, Invoice Date, Billing Status, Status
- **Labels Map:**
  - `planned_date` → "Completion date"
  - `due_date` → "Due date"
  - `invoice_reference` → "Invoice number"
  - `invoice_date` → "Invoice date" (NEW)
  - `is_billed` derived → "Billing status"
  - `phase` → "Phase"
- **Interaction:** Click row → Deliverable Drawer

---

## Field Mapping (DB → API → UI)

```
ServiceReviews.planned_date
  → API: "planned_date"
  → UI: "Completion date" label

ServiceReviews.invoice_reference
  → API: "invoice_reference" (no alias)
  → UI: "Invoice number" label

ServiceReviews.is_billed (boolean)
  → API: "is_billed" (no alias)
  → UI: derive_billing_status(is_billed) → "Billed" / "Not billed" badge

ServiceReviews.invoice_date (NEW)
  → API: "invoice_date"
  → UI: "Invoice date" label

ProjectServices.phase (join)
  → API: "phase"
  → UI: "Phase" column
```

---

## Testing Checklist (Minimal)

- [ ] Migrations run without error
- [ ] `invoice_date` column exists in both tables
- [ ] `phase` column exists in ProjectServices
- [ ] API `/projects/{id}/reviews` returns `invoice_date` and `phase` fields
- [ ] `is_billed` → "Billed" / "Not billed" conversion works
- [ ] Services tab renders and Drawer opens/closes
- [ ] Deliverables tab renders all 8 columns
- [ ] No console errors

---

## Known Constraints

- ❌ Do NOT rename database columns
- ❌ Do NOT add billing_status enum table
- ❌ Do NOT add completion_date as separate column
- ❌ Do NOT move phase to ServiceReviews/ServiceItems
- ✅ Only add new columns (additive only)
- ✅ Only update serialization (aliases in API response)

---

## Implementation Order

1. **Database** → Run migrations
2. **Backend** → Update queries + add billing_utils.py
3. **Frontend Types** → Update interfaces in api.ts
4. **Frontend UI** → Build components
5. **Test** → Verify against acceptance criteria

---

## PR Checklist (Copy to PR Description)

```
## Definition of Done

- [ ] Migrations merged to sql/migrations/
- [ ] database.py updated with invoice_date + phase
- [ ] billing_utils.py created and imported
- [ ] frontend/src/types/api.ts updated (ServiceReview + Deliverable)
- [ ] frontend/src/utils/billingUtils.ts created
- [ ] Services tab renders correctly
- [ ] Deliverables tab renders with all 8 columns
- [ ] Billing status derivation works (is_billed → "Billed"/"Not billed")
- [ ] Phase displayed correctly (inherited from ProjectServices)
- [ ] Drawers open/close without errors
- [ ] No breaking changes to existing APIs
- [ ] Tests pass
```

---

## Questions? See Full Spec

👉 [SERVICES_DELIVERABLES_IMPLEMENTATION_SPEC.md](./SERVICES_DELIVERABLES_IMPLEMENTATION_SPEC.md)

All decisions are final. No alternatives proposed.

