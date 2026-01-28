# Fee Model Inventory - Task 0.1 Complete

**Date**: January 27, 2026  
**Status**: Schema audit complete – existing fee columns identified  
**Next Step**: Implement unified fee governance (Task 1)

---

## Summary

The schema already contains **comprehensive fee fields** across all key tables. **NO new columns are required** to implement a unified fee model.

---

## Existing Fee Columns by Table

### 1. **ProjectServices** (per-service level)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `agreed_fee` | numeric | Contract fee for entire service | **Primary service-level fee source** |
| `unit_rate` | numeric | Per-unit billing rate | Optional; used when billing by quantity |
| `unit_qty` | numeric | Quantity of units | Paired with `unit_rate` |
| `lump_sum_fee` | numeric | One-time flat fee | Alternative to rate-based billing |
| `review_count_planned` | int | Expected number of review cycles | Used for pro-rata fee calculations |

**Fee derivation logic for reviews under this service:**
- Equal split: `agreed_fee / review_count_planned`
- Weighted split (if weight_factor used): `agreed_fee * weight_factor`

---

### 2. **ServiceReviews** (per-review line item)

| Field | Type | Purpose | Existing? | Status |
|-------|------|---------|-----------|--------|
| `billing_amount` | numeric | ✅ YES | Per-review fee override or calculation result | **Line-item fee field (authoritative)** |
| `fee_amount` | numeric | ✅ YES | Alternative per-review fee field | Duplicate of `billing_amount` for clarity |
| `fee` | numeric | ✅ YES | Resolved final fee | Computed field (not stored) |
| `fee_source` | string | ✅ YES | How fee was determined | Computed field (values: `override`, `calculated_equal_split`, `calculated_weighted`) |
| `weight_factor` | numeric | ✅ YES | Proportional weight (0.0-1.0) | Used to split service fees proportionally |
| `invoice_status` | string | ✅ YES | Billing state (`draft`, `ready`, `issued`, `paid`) | Prevents editing paid invoices |
| `invoice_reference` | string | ✅ YES | External invoice number | From accounting system |
| `invoice_date` | datetime | ✅ YES | When invoice was issued | |
| `invoice_month_final` | string | ✅ YES | YYYY-MM format for bucketing | **Preferred date for invoice pipeline** |
| `invoice_month_override` | string | ✅ YES | Manual override to invoice_month_auto | For period corrections |
| `invoice_month_auto` | string | ✅ YES | Auto-derived from `due_date` | Fallback when no override |
| `is_billed` | bit | ✅ YES | Boolean: invoice issued (1) or not (0) | Use for "billed" vs "outstanding" splits |
| `is_user_modified` | bit | ✅ YES | Was this row manually edited? | Tracks data provenance |
| `user_modified_fields` | string | ✅ YES | JSON array of edited fields | Audit trail |
| `billing_phase` | string | ✅ YES | Which project phase for billing | Context |
| `billed_amount` | numeric | ✅ YES | Amount actually invoiced (may differ from fee) | For reconciliation variance |

**Decision: Use `billing_amount` as the per-review fee field** (matches existing UI patterns)

---

### 3. **ServiceItems** (per-item deliverable)

| Field | Type | Purpose | Existing? | Status |
|-------|------|---------|-----------|--------|
| `fee_amount` | numeric | ✅ YES | Per-item fee (stored override) | **Line-item fee field (authoritative)** |
| `fee_source` | string | ✅ YES | How fee was determined | Computed field |
| `invoice_status` | string | ✅ YES | Billing state (`draft`, `ready`, `issued`, `paid`) | Prevents editing paid |
| `invoice_reference` | string | ✅ YES | External invoice number | |
| `invoice_date` | datetime | ✅ YES | When invoiced | |
| `is_billed` | bit | ✅ YES | Boolean: invoiced (1) or not (0) | |
| `billed_amount` | numeric | ✅ YES | Amount actually invoiced | For variance tracking |
| `is_user_modified` | bit | ✅ YES | Was this row manually edited? | Audit trail |
| `user_modified_fields` | string | ✅ YES | JSON array of edited fields | Audit trail |

**Decision: Use `fee_amount` as the per-item fee field**

---

## Key Decisions

### ✅ No New Columns Needed

All required fee fields already exist in the schema:

- ✅ Per-review fee storage: `ServiceReviews.billing_amount`
- ✅ Per-item fee storage: `ServiceItems.fee_amount`
- ✅ Service-level fee: `ProjectServices.agreed_fee`
- ✅ Invoice tracking: `invoice_status`, `invoice_reference`, `invoice_date`
- ✅ Invoice bucketing: `invoice_month_final`, `invoice_month_override`, `invoice_month_auto`
- ✅ Override indicators: `is_user_modified`, `user_modified_fields`
- ✅ Weight factors: `weight_factor` (for proportional splits)
- ✅ Variance tracking: `billing_amount` vs `billed_amount`

### Fee Resolution Logic

**For ServiceReviews (per-review fee):**

```
IF ServiceReviews.is_user_modified = 1
    fee = ServiceReviews.billing_amount (override)
    fee_source = 'override'
ELSE
    IF ProjectServices.review_count_planned > 0
        IF ServiceReviews.weight_factor IS NOT NULL AND weight_factor > 0
            fee = ProjectServices.agreed_fee * ServiceReviews.weight_factor
            fee_source = 'calculated_weighted'
        ELSE
            fee = ProjectServices.agreed_fee / ProjectServices.review_count_planned
            fee_source = 'calculated_equal_split'
        END IF
    ELSE
        fee = ServiceReviews.billing_amount (fallback to stored value)
        fee_source = 'override'
    END IF
END IF
```

**For ServiceItems (per-item fee):**

```
IF ServiceItems.is_user_modified = 1
    fee = ServiceItems.fee_amount (override)
    fee_source = 'override'
ELSE
    fee = ServiceItems.fee_amount (explicit item fee)
    fee_source = 'explicit'
END IF
```

---

## Invoice Pipeline Bucketing

### Current Schema Supports Three-Tier Invoice Month Logic

| Level | Field | Source | Fallback |
|-------|-------|--------|----------|
| 1 (Override) | `invoice_month_override` | Manual user entry | → Level 2 |
| 2 (Auto) | `invoice_month_auto` | Auto-derived from `due_date` | → Level 3 |
| 3 (Final) | `invoice_month_final` | Materialized result | Always populated |

**Implementation**: Always use `invoice_month_final` for bucketing (already resolved).

---

## Reconciliation Capability

The schema supports full financial reconciliation **without new columns**:

### Line Items Totals
```sql
SUM(billing_amount) FROM ServiceReviews WHERE service_id = X
+ SUM(fee_amount) FROM ServiceItems WHERE service_id = X
= Line Items Total for Service
```

### Billed Total
```sql
SUM(billing_amount) FROM ServiceReviews WHERE service_id = X AND is_billed = 1
+ SUM(fee_amount) FROM ServiceItems WHERE service_id = X AND is_billed = 1
= Billed Total for Service
```

### Outstanding
```sql
Line Items Total - Billed Total = Outstanding for Service
```

### Variance
```sql
ProjectServices.agreed_fee - Line Items Total = Variance
```

---

## Existing Guardrails in Schema

✅ `invoice_status` in ServiceReviews/ServiceItems  
- Use to prevent editing when `status IN ('issued', 'paid')`

✅ `is_user_modified` in ServiceReviews/ServiceItems  
- Use to track which rows have been manually edited

✅ `user_modified_fields` in ServiceReviews/ServiceItems  
- Use to audit which specific fields were changed

---

## Next Steps (Task 1)

1. **Implement fee resolution logic** in backend service
2. **Create unified endpoints**:
   - `GET /api/projects/{project_id}/finance/line-items`
   - `GET /api/projects/{project_id}/finance/reconciliation`
3. **Update Deliverables UI** to use `billing_amount` (reviews) and `fee_amount` (items)
4. **Update Overview** to use reconciliation data
5. **Update Right Panel** to match reconciliation totals

---

## Testing Checklist (Covered by Task 5)

- [ ] Fee resolution returns correct values for all three sources (override, equal split, weighted)
- [ ] Reconciliation sums match unified line-item endpoint
- [ ] Items included in pipeline totals
- [ ] Invoice status prevents editing paid reviews/items
- [ ] Variance is visible and drill-down works

