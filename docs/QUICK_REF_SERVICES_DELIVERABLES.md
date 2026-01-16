# Quick Reference: Services + Deliverables Refactor

**Full Audit:** [AUDIT_SERVICES_DELIVERABLES_REFACTOR.md](AUDIT_SERVICES_DELIVERABLES_REFACTOR.md)

---

## What Needs to Change

### 1. **Services Tab** (Already Exists)
- ✅ Currently: Expandable rows with inline reviews/items
- ✅ Update: Add finance-focused columns + **side panel on row click**
- ✅ Pattern: Use Drawer (like IssuesTabContent)
- 📁 File: `frontend/src/components/ProjectServicesTab.tsx`

### 2. **Reviews → Deliverables Tab** (Rename)
- ❌ Currently: "Reviews" tab shows only review cycles
- ✅ Update: Rename to "Deliverables"; unified table with **reviews + items**
- ✅ Required columns: Phase, Deliverable, Cycle, Assignee, Due, Status, Completion, **Planned**, Fee, Invoice Date, Billing Status, Invoice #
- 📁 File: `frontend/src/pages/ProjectWorkspacePageV2.tsx`
- 📁 New component: `DeliverableSidePanel.tsx` (right-side drawer)

### 3. **Services Side Panel** (Detail View)
- ✅ Show: Service code, name, phase, agreed_fee, unit_rate, billing_pct, billed_amount
- 📁 New component: `ServiceDetailDrawer.tsx`

### 4. **Deliverables Side Panel** (Detail View)
- ✅ Show: Review/item metadata, linked issues, comments, history
- 📁 New component: `DeliverableSidePanel.tsx`

---

## Missing Database Fields

**All additions are non-destructive (additive only):**

```sql
ALTER TABLE ServiceReviews ADD
  completion_date DATE NULL,
  invoice_date DATE NULL,
  invoice_number NVARCHAR(100) NULL,
  billing_status NVARCHAR(50) NULL;

ALTER TABLE ServiceItems ADD
  completion_date DATE NULL,
  invoice_date DATE NULL,
  invoice_number NVARCHAR(100) NULL,
  billing_status NVARCHAR(50) NULL;
```

**Update constants:**
```python
class ServiceReviews:
    COMPLETION_DATE = "completion_date"
    INVOICE_DATE = "invoice_date"
    INVOICE_NUMBER = "invoice_number"
    BILLING_STATUS = "billing_status"
```

---

## Key File Touchpoints

### Frontend

| File | Type | Changes |
|------|------|---------|
| `ProjectWorkspacePageV2.tsx` | Edit | 1. Rename "Reviews" → "Deliverables" (line 28) 2. Rebuild Reviews section as table with drawer |
| `ProjectServicesTab.tsx` | Edit | Replace Dialog with Drawer for service detail |
| `ServiceDetailDrawer.tsx` | New | Service detail side panel component (~150 lines) |
| `DeliverableSidePanel.tsx` | New | Deliverable detail side panel component (~200 lines) |
| `types/api.ts` | Edit | Add `DeliverableRow`, extend `ProjectService` with finance fields |
| `project-workspace-v2.spec.ts` | Edit | Update tab label assertion |
| `services-side-panel.spec.ts` | New | Playwright: Services drawer interaction (~80 lines) |
| `deliverables-side-panel.spec.ts` | New | Playwright: Deliverables drawer + columns (~100 lines) |

### Backend

| File | Changes |
|------|---------|
| `backend/app.py` | 1. Add/update `GET /api/projects/{id}/deliverables` (or reuse reviews endpoint) 2. Include new fields + assignee name join |
| `database.py` | 1. Update `get_project_reviews()` 2. Add `get_project_deliverables()` (if creating unified endpoint) |

### Database

| File | Changes |
|------|---------|
| `sql/migrations/007_*.sql` | Additive: Add 4 columns to ServiceReviews + ServiceItems |
| `constants/schema.py` | Add 4 new field constants |
| `sql/views/vw_project_deliverables.sql` | Optional: Create union view (recommended) |

---

## Implementation Sequence (7 Phases)

1. **Phase 1 (30m):** DB migration + schema constants
2. **Phase 2 (1-2h):** Backend API contract changes
3. **Phase 3 (30m):** Frontend tab label rename
4. **Phase 4 (2-3h):** Services detail drawer
5. **Phase 5 (3-4h):** Deliverables table + drawer
6. **Phase 6 (1-2h):** Integration testing
7. **Phase 7 (30m):** Docs + release

**Total:** ~9-13 hours | **Risk:** Low-Medium

---

## Type / Interface Changes

### New: DeliverableRow
```typescript
interface DeliverableRow {
  source_type: 'review' | 'item';
  deliverable_id: number;
  service_id: number;
  project_id: number;
  phase?: string;
  cycle_no?: number;
  title: string;
  planned_date: string;
  due_date?: string;
  completion_date?: string;
  status: string;
  assignee?: string;
  fee?: number;
  invoice_date?: string;
  invoice_number?: string;
  billing_status?: string;
}
```

### Extend: ProjectService
```typescript
// Add fields:
billing_progress_pct?: number;  // Already partially there
billed_amount?: number;
invoice_date?: string;
invoice_number?: string;
billing_status?: string;
```

---

## Existing Patterns to Reuse

| Pattern | File | Usage |
|---------|------|-------|
| **DetailsPanel** | `frontend/src/components/ui/DetailsPanel.tsx` | Simple wrapper for side content (don't use; use Drawer instead) |
| **Drawer** | `frontend/src/components/ProjectManagement/IssuesTabContent.tsx` | ✅ Use this pattern for side panels |
| **Table + Row Click** | IssuesTabContent | ✅ Use Material-UI Table for Deliverables |
| **LinkedIssuesList** | `frontend/src/components/ui/LinkedIssuesList` | ✅ Reuse in DeliverableSidePanel |
| **Schema Constants** | `constants/schema.py` | ✅ Always use for DB identifiers (no hardcodes) |
| **Database Pool** | `database_pool.py` | ✅ Use for all DB connections |

---

## Test IDs to Add

```
Services:
  - service-row-{service_id}
  - service-detail-drawer
  - service-detail-close-button

Deliverables:
  - deliverable-row-{review_id|item_id}
  - deliverable-detail-drawer
  - deliverable-detail-close-button
  - deliverable-table-header-{column_name}
```

---

## Critical Considerations

✅ **Do Use:**
- Schema constants (never hardcode column names)
- Database pool (centralized connections)
- Drawer pattern (proven in IssuesTabContent)
- React Query for data fetching
- Material-UI components

❌ **Don't:**
- Create destructive DB migrations (drops/renames)
- Hardcode DB identifiers in code
- Mix Dialog + Drawer patterns for same feature
- Bypass connection pooling

⚠️ **Watch For:**
- Type mismatches when unifying review_id vs item_id
- Performance: Ensure indexes on service_id, project_id
- Assignee field: May need Users table join optimization
- Feature flag conflicts: Ensure anchorLinks drawer doesn't interfere

---

## Validation Checklist

- [ ] DB migration runs without errors
- [ ] New columns visible in SSMS
- [ ] API returns all required fields
- [ ] Frontend compiles (no type errors)
- [ ] Services drawer opens/closes on row click
- [ ] Deliverables table renders with all 12 columns
- [ ] Deliverables drawer shows linked issues
- [ ] Playwright tests pass (Services + Deliverables)
- [ ] No console errors or TypeScript warnings
- [ ] Review history not broken (backward compat)
