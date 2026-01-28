# Services & Deliverables Workflow - Quick Reference

## Workflow Overview

```
                    Service Creation
                          │
                ┌─────────┴──────────┐
                │                    │
        BLANK SERVICE        TEMPLATE SERVICE
        (Manual Setup)       (Auto-Expanded)
                │                    │
         [Add Reviews]         [Generated Reviews]
         [Add Items]           [Generated Items]
                │                    │
                └─────────┬──────────┘
                          │
                    Service Created
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
    [Edit Service]    [Add/Edit Reviews] [Add/Edit Items]
    [Update Pricing]  [Manage Billing]    [Manage Delivery]
    [Resync Template] [Batch Invoice]     [Invoice Items]
```

---

## Creation Paths (2 Options)

### 1. Blank Service (Simple)
- User fills service form (code, name, pricing, dates)
- Backend creates `ProjectServices` record
- Service appears in list with **no reviews or items**
- User adds reviews/items manually or applies template later

### 2. Template Service (Comprehensive)
- User selects template from dropdown
- Checks optional features (Advanced Analytics, etc.)
- Overrides specific fields if needed
- Backend **atomically creates**:
  - Service record (with `template_mode='managed'`)
  - All reviews from template (marked `is_template_managed=1`)
  - All items from template (marked `is_template_managed=1`)
  - Binding record (tracks template version + options)
- Service ready to use immediately with full structure

---

## Key Entities

| Entity | Purpose | Linkage |
|--------|---------|---------|
| **ProjectServices** | Billable offering with scope & pricing | `project_id` |
| **ServiceReviews** | Recurring cadence/deliverable cycles | `service_id` |
| **ServiceItems** | Detailed deliverables/milestones | `service_id` |
| **ProjectServiceTemplateBindings** | Tracks which template was applied | `service_id` + `template_id` |

---

## Pricing Models

| Model | Fields Used | Best For |
|-------|-------------|----------|
| **Lump Sum** | `lump_sum_fee` | Fixed price services ("Design Review: $25,000") |
| **Unit-Based** | `unit_qty` × `unit_rate` | Repeating units ("12 weeks @ $2,500/week") |
| **Agreed Fee** | `agreed_fee` | Override any of above ("Actually: $23,000 total") |

---

## Editing Workflow

### Service Edit
- Update pricing, schedule, assignment, status
- Change review cadence (interval, count)
- Resync from template (if template-managed)

### Review Management
- Add manual reviews (if not template-managed)
- Change planned dates
- Link evidence/deliverables
- Batch invoice

### Item Management
- Add custom items
- Update delivery dates
- Assign owners
- Batch invoice separately

---

## Template Synchronization (for Template-Managed Services)

When a service is created from template:
```
Service → Created with template_mode='managed'
  ├─ Reviews marked is_template_managed=1
  └─ Items marked is_template_managed=1
```

Later, **resync** to refresh from evolved template:

```
POST /api/projects/100/services/123/apply-template
{
  "template_id": "design_review_weekly",
  "options_enabled": ["advanced_analytics"],
  "mode": "sync_and_update_managed"  ← Keep user edits, update template parts
}
```

**Modes**:
- `sync_missing_only` - Add new reviews/items only
- `sync_and_update_managed` - Add new + refresh template-managed ones

---

## Review Scheduling

```
Anchor Date: 2026-02-01
Interval: 7 days
Count: 13

↓ Generates:
Review 0 (Kickoff): 2026-02-01
Review 1 (Week 1):  2026-02-08
Review 2 (Week 2):  2026-02-15
Review 3 (Week 3):  2026-02-22
... (10 more)
```

**API**:
```
POST /api/projects/100/services/123/reviews/resequence
{
  "anchor_date": "2026-02-01",
  "interval_days": 7,
  "count": 13
}
```

---

## Billing Integration

### Review Billing
```
Service agreed_fee: $25,000
Review weight_factor: 0.08 (1/12)

→ Review billing_amount = $25,000 × 0.08 = $2,075
```

### Item Billing
```
Item fee_amount: $250
Repeat: 12 times

→ Item billed_amount = $250 × 12 = $3,000
```

**Batch Invoice**:
```
POST /api/projects/100/services/123/reviews/invoice-batch
{
  "invoice_month": "2026-03",
  "review_ids": [789, 790, 791],
  "notes": "March deliverables"
}

→ Creates InvoiceBatches record
→ Updates reviews with invoice_reference, invoice_date
```

---

## Frontend Components

| Component | Purpose | Path |
|-----------|---------|------|
| **ServiceCreateView** | Create blank or template service | `frontend/src/pages/workspace/ServiceCreateView.tsx` |
| **ServiceEditView** | Edit service details & reviews | `frontend/src/pages/workspace/ServiceEditView.tsx` |
| **ServiceDetailPanel** | View/edit reviews & items | `frontend/src/components/workspace/ServiceDetailPanel.tsx` |
| **serviceTemplatesApi** | API client for templates & services | `frontend/src/api/services.ts` |

---

## Backend Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/projects/<pid>/services` | Create blank service |
| POST | `/projects/<pid>/services/from-template` | Create from template |
| PATCH | `/projects/<pid>/services/<sid>` | Update service |
| DELETE | `/projects/<pid>/services/<sid>` | Delete service |
| POST | `/projects/<pid>/services/<sid>/reviews/resequence` | Recalculate review dates |
| POST | `/projects/<pid>/services/<sid>/apply-template` | Resync from template |
| POST | `/projects/<pid>/services/<sid>/reviews` | Add review |
| POST | `/projects/<pid>/services/<sid>/items` | Add item |
| POST | `/projects/<pid>/services/<sid>/reviews/invoice-batch` | Create invoice batch |

---

## Template Structure

```json
{
  "template_id": "design_review_weekly",
  "name": "Weekly Design Review",
  "defaults": {
    "phase": "Design Development",
    "unit_type": "weekly",
    "bill_rule": "percentage"
  },
  "pricing": {
    "lump_sum_fee": 2500
  },
  "reviews": [
    {
      "review_id": "dr_kickoff",
      "cycle_no": 0,
      "title": "Kickoff",
      "weight_factor": 0.1
    },
    {
      "review_id": "dr_weekly",
      "cycle_no": 1,
      "title": "Weekly Coordination",
      "weight_factor": 0.9,
      "repeat": 12  ← Generates 12 copies
    }
  ],
  "items": [
    {
      "item_id": "status_report",
      "title": "Status Report",
      "item_type": "deliverable",
      "repeat": 12
    }
  ],
  "options": [
    {
      "id": "advanced_analytics",
      "name": "Advanced Analytics"
    }
  ]
}
```

---

## Current Strengths ✅

- Atomic template application (no partial states)
- Independent reviews and items (flexible billing)
- Resequencing recalculates all dates automatically
- Template binding tracks version + options (audit trail)
- Template-managed flag enables safe resync
- Dry-run mode for preview before commit

---

## Improvement Opportunities 🎯

### Quick Wins (1-2 days each)
- Add template preview before applying
- Inline review addition (no dialog popup)
- Bulk resequencing integrated into main form
- Show option impact on cost

### Medium-Term (3-5 days each)
- Bulk item operations (assign user to all items at once)
- Template recommendations based on service type
- Template versioning with migration path
- Customizable template before applying

### Strategic (1-2 weeks each)
- Template marketplace (share across org)
- Service cloning with date/phase offset
- Workflow rules (auto-create items, auto-invoice, etc.)

---

## Key Data Fields Reference

**ProjectServices** (21 fields):
- Identity: service_id, project_id, service_code, service_name
- Scope: phase, unit_type, unit_qty, unit_rate, agreed_fee
- Schedule: start_date, end_date, review_anchor_date, review_interval_days
- Template: source_template_id, template_mode (null or 'managed')
- Billing: bill_rule, claimed_to_date, progress_pct

**ServiceReviews** (26 fields):
- Identity: review_id, service_id, cycle_no
- Schedule: planned_date, due_date, actual_issued_at
- Template: is_template_managed, template_node_key, generated_key
- Billing: billing_amount, weight_factor, invoice_reference, is_billed
- User Edit: is_user_modified, user_modified_fields

**ServiceItems** (34 fields):
- Identity: item_id, service_id, item_type
- Schedule: planned_date, due_date, actual_date
- Template: is_template_managed, template_node_key, generated_key
- Billing: fee_amount, billed_amount, invoice_status, invoice_reference
- Management: status, priority, assigned_user_id

---

## Quick Start (New Service)

```
1. Click "New Service"
   ↓
2. Choose: [Blank Service] or [From Template]
   ↓
3. If Blank:
   - Fill form (code, name, pricing, dates)
   - Submit → Service created empty
   - Manually add reviews/items, OR apply template later
   
   If Template:
   - Select template → Check options → Override fields
   - Submit → Service + reviews + items created atomically
   ↓
4. Review created → Edit if needed → Invoice when ready
```

---

For detailed information, see: [SERVICES_DELIVERABLES_WORKFLOW_ANALYSIS.md](./SERVICES_DELIVERABLES_WORKFLOW_ANALYSIS.md)
