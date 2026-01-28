# Fee + Progress Rollup Audit (Deliver)

Date: 2026-01-27
Scope: Project page, Workspace Overview, Workspace Services, Workspace Deliverables
Owner: Audit only (no code changes in this report)

## 1) Data lineage map (UI -> API -> fields -> filters)

### Project page (ProjectDetailPage)
- Component: `frontend/src/pages/ProjectDetailPage.tsx`
- API calls:
  - `projectsApi.getById` -> `GET /api/projects/:id` -> `shared.project_service.get_project`
  - `projectServicesApi.getAll` -> `GET /api/projects/:id/services` -> `database.get_project_services`
- Fields used for totals:
  - `service.agreed_fee` for agreed total
  - `service.billed_amount ?? service.claimed_to_date` for billed total
- Frontend aggregation:
  - Sum over all services in `billingTotals`.
  - `billedPercent = totalBilled / totalAgreed`.
- Filters:
  - None (all services returned).
- Cache/query keys:
  - `['projectServices', projectId, { scope: 'billing' }]` (scope not used by API)
- Notes:
  - `project.total_service_agreed_fee` is referenced as a fallback but is not present in `/api/projects/:id` payload.

### Workspace Overview
- Component: `frontend/src/pages/workspace/OverviewTab.tsx`
- API calls:
  - `projectsApi.getFinanceLineItems` -> `GET /api/projects/:id/finance/line-items` -> `FinancialDataService.get_line_items`
  - `projectsApi.getFinanceReconciliation` -> `GET /api/projects/:id/finance/reconciliation` -> `FinancialDataService.get_reconciliation`
- Fields used:
  - Invoice pipeline uses `line_items[].fee`, `invoice_status`, `invoice_month`
  - Reconciliation uses `project.agreed_fee`, `line_items_total_fee`, `billed_total_fee`, `outstanding_total_fee`
- Frontend aggregation:
  - Pipeline buckets built client-side from line items.
  - Toggle can exclude items (reviews-only).
- Filters:
  - Optional `service_id`, `invoice_status` (not used in UI by default).
- Cache/query keys:
  - `['projectFinanceLineItems', projectId]`
  - `['projectFinanceReconciliation', projectId]`

### Workspace Services
- Component: `frontend/src/pages/workspace/ServicesTab.tsx`
- API calls:
  - `projectServicesApi.getAll` -> `GET /api/projects/:id/services` -> `database.get_project_services`
- Fields used:
  - `agreed_fee`, `billed_amount ?? claimed_to_date`, `billing_progress_pct ?? progress_pct`
  - `review_count_total`, `item_count_total` (computed in `get_project_services`)
- Frontend aggregation:
  - None (per-service display only).
- Filters:
  - None.
- Cache/query keys:
  - `['projectServices', projectId]`

### Workspace Deliverables
- Component: `frontend/src/pages/workspace/DeliverablesTab.tsx`
- API calls:
  - `useProjectReviews` -> `GET /api/projects/:id/reviews` -> `database.get_project_reviews`
  - `serviceItemsApi.getProjectItems` -> `GET /api/projects/:id/items` -> `database.get_project_items`
- Fields used:
  - Reviews: `fee`, `fee_source` (computed in `get_project_reviews`) OR `fee_amount` fallback
  - Items: `fee_amount`, `fee_source`
  - Status, due/planned dates, invoice fields, is_billed
- Frontend aggregation:
  - None (table display only).
- Filters:
  - Due this month, unbatched, ready to invoice
- Cache/query keys:
  - `['projectReviews', projectId, filtersKey]`
  - `['projectItems', projectId]`
- Notes:
  - Totals shown on Deliverables are actually coming from the right panel, not the table.

### Workspace Right Panel (progress block)
- Component: `frontend/src/components/workspace/RightPanel.tsx`
- API calls:
  - `projectsApi.getFinanceReconciliation` -> `GET /api/projects/:id/finance/reconciliation`
- Fields used:
  - `project.agreed_fee`, `line_items_total_fee`, `billed_total_fee`, `outstanding_total_fee`

---

## 2) Backend endpoint inventory + rollup formulas

### GET `/api/projects/:id/services`
- Source: `database.get_project_services` (`database.py`)
- Formula:
  - Status derived from review/item status counts.
  - Billed amount derived from:
    - `claimed_to_date` (if present)
    - else `agreed_fee * progress_pct` or billed-unit ratio
  - Progress derived from billed vs billable review/item count.
- Filters:
  - None by status/phase/execution intent.
- Implication:
  - Billing totals are derived from status flags, not line-item fees.

### GET `/api/projects/:id/reviews`
- Source: `database.get_project_reviews` (`database.py`)
- Fee formula: `_calculate_review_fee` (local helper)
  - If `billing_amount` > 0 -> fee = billing_amount
  - Else if `fee_amount` set -> fee = fee_amount
  - Else if `agreed_fee` + `review_count_planned` -> equal split
  - Else fee = null
- Uses `review_count_planned` (not actual review count).

### GET `/api/projects/:id/items`
- Source: `database.get_project_items` (`database.py`)
- Fee formula:
  - Uses `fee_amount` directly if column exists.

### GET `/api/projects/:id/finance/line-items`
- Source: `FinancialDataService.get_line_items` (`services/financial_data_service.py`)
- Fee formula (deterministic):
  - Reviews: `FeeResolverService.resolve_review_fee` (fee_amount or equal split across actual reviews)
  - Items: `FeeResolverService.resolve_item_fee` (fee_amount or 0)
- Filters:
  - `execution_intent = 'planned'` at service level.

### GET `/api/projects/:id/finance/reconciliation`
- Source: `FinancialDataService.get_reconciliation`
- Rollup:
  - Aggregates line-items per service and project.
  - Only services that have at least one line item are included in `agreed_fee` total.

### GET `/api/projects/:id/finance-summary`
- Source: `database.get_project_finance_summary`
- Rollup:
  - Uses counts of billed vs billable reviews/items to derive claimed and progress.
  - Not fee-weighted.

### GET `/api/projects/finance_grid`
- Source: `database.get_project_finance_rollup` -> `vw_projects_finance_rollup`
- Rollup:
  - View-based; logic not guaranteed to match other endpoints.

---
## 3) Deterministic dataset reproduction (project 33)

### Dataset selection
Project `33` has:
- 6 services (includes Phase 8 - Digital Handover)
- 16 reviews (all under service `272`)
- 3 items (no fee_amount set)

### Raw rows (abridged but exact)
```
Services:
{'service_id': 270, 'service_code': 'AUDIT_DES', 'service_name': 'Design Model Audit (Pre-Construction)', 'phase': 'Phase 7 - Construction (Design Model Audit)', 'agreed_fee': 10000.0, 'status': 'completed', 'review_count_planned': None, 'execution_intent': 'planned'}
{'service_id': 271, 'service_code': 'INIT', 'service_name': 'Digital Initiation (DEXP, Workshops, Platform Setup)', 'phase': 'Phase 4/5 - Digital Initiation', 'agreed_fee': 17500.0, 'status': 'completed', 'review_count_planned': None, 'execution_intent': 'planned'}
{'service_id': 272, 'service_code': 'PROD', 'service_name': 'BIM Coordination Review Cycles (Day 1)', 'phase': 'Phase 7 - Digital Production', 'agreed_fee': 120000.0, 'status': 'in_progress', 'review_count_planned': None, 'execution_intent': 'planned'}
{'service_id': 273, 'service_code': 'MILE_AUD', 'service_name': 'Milestone Audit Report', 'phase': 'Phase 7 - Digital Production', 'agreed_fee': 15000.0, 'status': 'Active', 'review_count_planned': None, 'execution_intent': 'planned'}
{'service_id': 274, 'service_code': 'ASBUILT', 'service_name': 'Point Cloud Survey & As-Built Validation (Day 1)', 'phase': 'Phase 8 - Digital Handover', 'agreed_fee': 155000.0, 'status': 'Active', 'review_count_planned': None, 'execution_intent': 'planned'}
{'service_id': 275, 'service_code': 'PC_REP', 'service_name': 'PC Compliance Report (Day 1)', 'phase': 'Phase 8 - Digital Handover', 'agreed_fee': 15000.0, 'status': 'Active', 'review_count_planned': None, 'execution_intent': 'planned'}

ServiceReviews (all under service 272):
(5658, 272, 'completed', due=2025-11-21, planned=2025-11-21, billing_amount=0.00, fee_amount=NULL, is_user_modified=False, is_billed=True)
(5659, 272, 'completed', due=2025-11-28, planned=2025-11-28, billing_amount=0.00, fee_amount=NULL, is_user_modified=False, is_billed=True)
(5660, 272, 'completed', due=2025-12-05, planned=2025-12-05, billing_amount=0.00, fee_amount=NULL, is_user_modified=False, is_billed=True)
(5661, 272, 'completed', due=2025-12-12, planned=2025-12-12, billing_amount=0.00, fee_amount=NULL, is_user_modified=False, is_billed=True)
(5662, 272, 'planned',   due=2025-12-19, planned=2025-12-19, billing_amount=0.00, fee_amount=NULL, is_user_modified=False, is_billed=True)
(5663, 272, 'planned',   due=2026-02-06, planned=2026-01-09, billing_amount=0.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5664, 272, 'planned',   due=2026-01-23, planned=2026-01-01, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5665, 272, 'planned',   due=2026-01-30, planned=2026-01-08, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5666, 272, 'planned',   due=2026-02-13, planned=2026-01-15, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5667, 272, 'planned',   due=2026-02-20, planned=2026-01-22, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5668, 272, 'planned',   due=2026-02-27, planned=2026-01-29, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5669, 272, 'planned',   due=2026-03-06, planned=2026-02-05, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5670, 272, 'planned',   due=2026-03-13, planned=2026-02-12, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5671, 272, 'planned',   due=2026-03-20, planned=2026-02-19, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5672, 272, 'planned',   due=2026-03-27, planned=2026-02-26, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)
(5673, 272, 'planned',   due=2026-04-03, planned=2026-03-05, billing_amount=6000.00, fee_amount=NULL, is_user_modified=True,  is_billed=False)

ServiceItems:
(15, 270, 'completed', due=2025-10-31, planned=1900-01-01, fee_amount=NULL, is_user_modified=False, is_billed=True,  title='Model Audit')
(13, 271, 'completed', due=2025-10-31, planned=1900-01-01, fee_amount=NULL, is_user_modified=False, is_billed=True,  title='Platform Setup')
(14, 271, 'completed', due=2025-10-31, planned=1900-01-01, fee_amount=NULL, is_user_modified=False, is_billed=True,  title='DEXP update')
```

### Totals by service (FeeResolverService model)
```
270 AUDIT_DES: agreed_fee=10000.00, reviews_fee=0.00, items_fee=0.00, total_fee=0.00, variance=10000.00
271 INIT:      agreed_fee=17500.00, reviews_fee=0.00, items_fee=0.00, total_fee=0.00, variance=17500.00
272 PROD:      agreed_fee=120000.00, reviews_fee=120000.00, items_fee=0.00, total_fee=120000.00, variance=0.00
273 MILE_AUD:  agreed_fee=15000.00, reviews_fee=0.00, items_fee=0.00, total_fee=0.00, variance=15000.00
274 ASBUILT:   agreed_fee=155000.00, reviews_fee=0.00, items_fee=0.00, total_fee=0.00, variance=155000.00
275 PC_REP:    agreed_fee=15000.00, reviews_fee=0.00, items_fee=0.00, total_fee=0.00, variance=15000.00
```

### Totals by phase
```
Phase 7 - Construction (Design Model Audit): agreed_fee=10000.00, total_fee=0.00, variance=10000.00
Phase 4/5 - Digital Initiation:           agreed_fee=17500.00, total_fee=0.00, variance=17500.00
Phase 7 - Digital Production:             agreed_fee=135000.00, total_fee=120000.00, variance=15000.00
Phase 8 - Digital Handover:               agreed_fee=170000.00, total_fee=0.00, variance=170000.00
```

### Totals by status
```
review:completed count=4
review:planned   count=12
item:completed   count=3
```

---

## 4) Confirmed discrepancy patterns + evidence

1) Reconciliation excludes services with no line items
- Evidence: `FinancialDataService.get_reconciliation` only adds services found in line items.
- Effect: project agreed fee on Overview/RightPanel is undercounted.
- Example (project 33):
  - Services agreed total = 332,500 (Project/Services pages)
  - Reconciliation agreed fee = 147,500 (only services with line items)

2) Deliverables fee model differs from Finance line-items
- Evidence: `database.get_project_reviews` uses `_calculate_review_fee` (billing_amount and review_count_planned)
  while `FinancialDataService` uses `FeeResolverService` (fee_amount and actual review count).
- Example (project 33):
  - Deliverables table (review fees using billing_amount) totals = 60,000
  - Finance line-items totals = 120,000

3) Project/Services totals use service-level billed derivation, not line-items
- Evidence: `database.get_project_services` derives `billed_amount` from status counts/claimed_to_date.
- Effect: billed totals and progress percent differ from reconciliation.
- Example (project 33):
  - Service-derived billed total = 65,000
  - Reconciliation billed total = 37,500

4) Workspace header progress uses fields not returned by `/api/projects/:id`
- Evidence: `ProjectWorkspacePageV2` expects `project.total_service_agreed_fee` and `total_service_billed_amount`,
  but `shared.project_service.get_project` does not return those fields.
- Effect: header progress can be zero or inconsistent.

5) Handover deliverables appear missing due to data, not filters
- Evidence: Services with Phase 8 - Digital Handover have no reviews/items (project 33),
  so they do not contribute to line-item totals or appear in Deliverables tab.

---
## 5) Canonical rollup rules (single source of truth)

### 5.1 Agreed fee total (authoritative)
- Rule: `agreed_fee_total = SUM(ProjectServices.agreed_fee)` for the project.
- Rationale: Services page is the contract scope source of truth.

### 5.2 Planned fee total (execution plan)
- Rule: `planned_fee_total = SUM(resolved_fee for reviews + items)`
- Reviews:
  - If `fee_amount` set -> use fee_amount
  - Else if `review_count_planned` set -> use `agreed_fee / review_count_planned`
  - Else -> use `agreed_fee / actual_review_count`
- Items:
  - Use `fee_amount` only (items do not inherit from service)
- Scope:
  - Include only services with `execution_intent = 'planned'`
  - Exclude non-actioned deliverables (see decision matrix)

### 5.3 Billed/claimed total
- Rule: `billed_total = SUM(resolved_fee or billed_amount)` for deliverables marked billed
- Use `billed_amount` if present, else `resolved_fee`.
- Billed flag: `is_billed = 1` OR `invoice_status IN ('issued','paid')`.

### 5.4 Progress percent
- Rule (agreed): `billed_total / agreed_fee_total`
- Rule (planned): `billed_total / planned_fee_total`
- Provide both in API; UI chooses which to show (default: agreed).

### 5.5 Remaining
- `remaining_agreed = agreed_fee_total - billed_total`
- `remaining_planned = planned_fee_total - billed_total`

---

## 6) Deliverables inclusion decision matrix

Legend:
- Agreed = agreed_fee_total
- Planned = planned_fee_total
- Progress = used in progress_pct denominator
- Billed = used in billed_total

| Condition | Include in Agreed | Include in Planned | Progress Denominator | Include in Billed | Notes |
|---|---|---|---|---|---|
| Template-managed but not actioned | Yes | No | No | No | Use is_actioned or status to decide |
| Optional deliverable (not actioned) | Yes | No | No | No | Needs a flag or status value |
| Status = not_required/skipped/on_hold | Yes | No | No | No | Status values not yet present in DB |
| Status = cancelled | Yes | No | No | No | Treated as not in execution plan |
| Phase = Handover | Yes | Yes | Yes | Yes | Do not auto-exclude |
| Deleted or unmapped (no service_id) | No | No | No | No | Must be linked to service_id |

---
## 7) Current totals comparison (project 33)

| Page/Source | Agreed Fee | Planned/Line Items | Billed | Notes |
|---|---:|---:|---:|---|
| Project page (services sum) | 332,500 | n/a | 65,000 | Sum of `ProjectServices.agreed_fee` and derived `billed_amount` |
| Services tab (per-service) | 332,500 | n/a | 65,000 | Same as Project page |
| Overview (reconciliation) | 147,500 | 120,000 | 37,500 | Agreed fee excludes services without line items |
| Deliverables table (UI fees) | n/a | 60,000 | n/a | Uses `_calculate_review_fee` (billing_amount) |
| Finance line-items (deterministic) | n/a | 120,000 | 37,500 | Uses `FeeResolverService` |

---

## 8) Conclusions

- The system currently has at least three fee models in production:
  1) Service-level agreed fee totals (Project/Services)
  2) Review fee model in `get_project_reviews` (billing_amount, review_count_planned)
  3) Deterministic line-items model (`FeeResolverService`)
- Reconciliation excludes services with no deliverables, causing a lower agreed fee total.
- Deliverables UI can show a different total from the Overview/RightPanel on the same page.
- A single canonical rollup endpoint is needed to remove ambiguity.

