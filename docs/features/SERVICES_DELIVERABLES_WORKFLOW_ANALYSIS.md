# Services & Deliverables Workflow - Comprehensive Analysis

**Document Purpose**: Deep dive into the complete services and deliverables (items) workflow, including creation, editing, and template integration pathways.

**Last Updated**: January 2026  
**Scope**: Database schema, React frontend, TypeScript API client, Flask backend

---

## Executive Summary

The BIM Project Management system manages **services** (billable scopes of work) and **service items** (deliverables within those services) as independent but related entities. The workflow supports **two creation modes**:

1. **Blank Service Creation** - Manual service definition with optional later template application
2. **Template-Driven Service Creation** - Service, reviews, and items generated in one operation

Both modes feed into an **editing workflow** where users can modify service details, manage reviews (generated or manual), and update items. Templates provide a powerful **generation and synchronization** mechanism using "template-managed" flags and node keys to track provenance.

---

## 1. Core Data Model

### 1.1 Primary Entities

The system uses a **service-centric model** with hierarchical structure:

```
Project (ProjectManagement)
  ├─ Services (ProjectServices) - billable offerings
  │   ├─ Reviews (ServiceReviews) - cadence/deliverables
  │   │   └─ Billing Integration (invoice_reference, invoice_date, billing_amount)
  │   └─ Items (ServiceItems) - detailed deliverables/milestones
  │       └─ Billing Integration (fee_amount, billed_amount, invoice_status)
  └─ Template Bindings (ProjectServiceTemplateBindings) - tracks applied templates
```

### 1.2 Service Record

**Table**: `ProjectServices` (21 fields)

| Category | Fields | Purpose |
|----------|--------|---------|
| **Identity** | service_id, project_id, service_code, service_name | Identify and name the service |
| **Scope** | phase, unit_type, unit_qty, unit_rate, lump_sum_fee, agreed_fee | Define work scope and pricing |
| **Billing** | bill_rule, status, progress_pct, claimed_to_date | Track billing eligibility and progress |
| **Schedule** | start_date, end_date, review_anchor_date, review_interval_days, review_count_planned | Define service timeline and review cadence |
| **Template** | source_template_id, source_template_version, source_template_hash, template_mode | Track template origin |
| **Metadata** | notes, assigned_user_id, created_at, updated_at | Administrative data |

**Pricing Model** (Critical Branch Point):
- **Lump Sum**: Single fixed fee (`lump_sum_fee`) for entire service
- **Unit-Based**: Per-unit pricing (`unit_qty` × `unit_rate`)
- **Agreed Fee Override**: Direct fee specification (`agreed_fee`) overrides both

### 1.3 Service Review Record

**Table**: `ServiceReviews` (26 fields)

| Category | Fields | Purpose |
|----------|--------|---------|
| **Identity** | review_id, project_id, service_id, cycle_no | Identify review cycle |
| **Schedule** | planned_date, due_date, actual_issued_at | Track review timing |
| **Deliverable** | disciplines, deliverables, evidence_links | Define what's delivered |
| **Status** | status, is_billed, invoice_status | Track review completion and billing |
| **Billing** | billing_phase, billing_rate, billing_amount, weight_factor | Calculate review fee |
| **Invoice** | invoice_reference, invoice_date, invoice_batch_id | Link to invoicing |
| **Template** | is_template_managed, template_node_key, generated_from_template_id, generated_key | Track provenance |
| **User Edit** | is_user_modified, user_modified_at, user_modified_fields | Track manual changes |
| **Scheduling** | source_phase, billing_phase, invoice_month_final, sort_order | Advanced scheduling |

**Key Insight**: `is_template_managed` flag controls whether reviews can be re-synced from template.

### 1.4 Service Item Record

**Table**: `ServiceItems` (34 fields)

| Category | Fields | Purpose |
|----------|--------|---------|
| **Identity** | item_id, project_id, service_id, item_type | Identify deliverable item |
| **Content** | title, description, phase | Describe the item |
| **Schedule** | planned_date, due_date, actual_date | Timeline for item |
| **Status** | status, priority, assigned_user_id | Track item progress |
| **Billing** | fee_amount, billed_amount, invoice_status, invoice_reference, invoice_date | Item-level billing |
| **Evidence** | evidence_links, notes | Supporting documentation |
| **Template** | is_template_managed, template_node_key, generated_from_template_id, generated_key | Track provenance |
| **User Edit** | is_user_modified, sort_order | Track modifications |

**Key Insight**: Items have independent billing from reviews - can be billed separately or grouped.

### 1.5 Template Binding Record

**Table**: `ProjectServiceTemplateBindings` (8 fields)

| Field | Purpose |
|-------|---------|
| binding_id | Unique binding identifier |
| project_id, service_id | Link binding to service |
| template_id, template_version, template_hash | Identify template version |
| options_enabled_json, options_enabled | Track which template options were used |
| applied_at, applied_by_user_id | Audit trail |

**Purpose**: When a template is applied to a service, this record tracks **which exact template version** was used and **which optional features** were enabled.

---

## 2. Creation Workflow

### 2.1 Workflow Paths

```
┌──────────────────────────────────────────────────────────────┐
│                     SERVICE CREATION                         │
└──────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
        ┌───────▼────────┐   ┌────────▼──────────┐
        │  BLANK SERVICE │   │ TEMPLATE SERVICE   │
        └───────┬────────┘   └────────┬──────────┘
                │                     │
         ┌──────▼──────┐      ┌───────▼────────┐
         │  Manual     │      │  Auto-generate │
         │  details    │      │  - Reviews     │
         │  - Billing  │      │  - Items       │
         │  - Schedule │      │  (if enabled)  │
         └──────┬──────┘      └───────┬────────┘
                │                     │
        ┌───────▼─────────────────────▼──────┐
        │   Service created & persisted      │
        │   ↓                                 │
        │   Optional: Apply template later   │
        │   (post-creation)                  │
        └───────────────────────────────────┘
```

### 2.2 Path 1: Blank Service Creation

**Location**: [frontend/src/pages/workspace/ServiceCreateView.tsx](frontend/src/pages/workspace/ServiceCreateView.tsx) → [backend/app.py](backend/app.py#L1861) `api_create_project_service()`

**User Interaction Flow**:

```
1. Click "New Service" in Services tab
   ↓
2. Form appears with mode selector:
   - [Blank Service] (default)
   - [From Template]
   ↓
3. Fill form (Blank mode):
   ┌─────────────────────────────────────┐
   │ Service Code                        │
   │ Service Name                        │
   │ Phase                               │
   ├─────────────────────────────────────┤
   │ Billing Model: [Lump Sum / Unit]    │
   │ if Lump Sum:                        │
   │   └─ Lump Sum Fee: $______          │
   │ if Unit:                            │
   │   ├─ Unit Type: [____]              │
   │   ├─ Unit Qty: [__]                 │
   │   ├─ Unit Rate: $[__]               │
   │   └─ Bill Rule: [____]              │
   ├─────────────────────────────────────┤
   │ Agreed Fee (optional override): $   │
   │ Notes: [_______________]            │
   │ Assigned User: [User dropdown]      │
   │ Start Date: [____-__-__]            │
   │ End Date: [____-__-__]              │
   └─────────────────────────────────────┘
   ↓
4. Submit → Backend creates service
   ↓
5. Service appears in list (empty reviews/items)
   ↓
6. User can:
   - Add reviews manually (via detail panel)
   - Add items manually (via detail panel)
   - Apply template later to generate reviews/items
```

**Backend Logic** (`api_create_project_service`):

1. Parse request JSON (form data)
2. **Validate billing model**:
   - If `lump_sum_fee`: require non-null fee
   - If unit-based: require unit_type, unit_qty, unit_rate, bill_rule
   - If `agreed_fee`: validate against total_service_agreed_fee not exceeding project value
3. **Auto-calculate start_date**: if not provided, use `project.start_date`
4. **Create service**: Call `database.create_project_service()` with:
   - All form fields mapped to database columns
   - Default `template_mode = None` (no template)
5. **Return created service** with ID for UI refresh

**Key Characteristics**:
- ✅ Minimal initial data entry
- ✅ Service exists immediately (can manually add reviews/items)
- ✅ No automatic structure generation
- ✅ Flexible for custom workflows

### 2.3 Path 2: Template-Driven Service Creation

**Location**: [frontend/src/pages/workspace/ServiceCreateView.tsx](frontend/src/pages/workspace/ServiceCreateView.tsx) → [backend/app.py](backend/app.py#L1802) `api_create_project_service()` + `api_create_service_from_template()`

**User Interaction Flow**:

```
1. Click "New Service" in Services tab
   ↓
2. Mode selector: [Blank Service] / [From Template] ← USER SELECTS
   ↓
3. Form appears in Template mode:
   ┌──────────────────────────────────────┐
   │ Template Selection: [Dropdown ↓]     │
   │ (shows available templates)          │
   ├──────────────────────────────────────┤
   │ Template Options (if available):     │
   │ ☐ Include Advanced Analytics         │
   │ ☐ Weekly Status Reports              │
   │ ☐ Compliance Audits                  │
   ├──────────────────────────────────────┤
   │ Override Fields (optional):          │
   │ Service Name: [______________]       │
   │ Agreed Fee: $[____]                  │
   │ Start Date: [____-__-__]             │
   │ Review Interval (days): [__]         │
   │ Number of Reviews: [__]              │
   └──────────────────────────────────────┘
   ↓
4. Submit → Backend EXPANDS template
   ↓
5. Creates:
   ├─ Service record (with template_mode='managed')
   ├─ Reviews (from template review blueprint)
   ├─ Items (from template items blueprint)
   └─ Template binding (tracks version & options)
   ↓
6. Service appears in list with:
   ✓ Reviews auto-generated
   ✓ Items auto-generated
   ✓ Ready to use immediately
```

**Backend Logic** (`api_create_service_from_template` via `create_service_from_template`):

1. **Load template** by ID (from `ServiceTemplates` table or file-based `templates.json`)
2. **Resolve service payload**:
   - Start with template defaults
   - Apply user overrides
   - Merge pricing model
3. **Create service record**: Insert into `ProjectServices` with `template_mode='managed'`
4. **Derive review cadence**:
   - Extract review blueprint from template
   - Calculate `review_anchor_date` (defaults to service start_date)
   - Calculate `review_interval_days` from template or override
   - Calculate `review_count_planned` from template or override
5. **Generate reviews** via `_generate_reviews_and_items()`:
   - For each review in template blueprint:
     - Create `ServiceReview` record
     - Set `is_template_managed = 1`
     - Store `template_node_key` (identifies this item in template tree)
     - Store `generated_key` (tracks this generation run)
6. **Generate items** via `_generate_reviews_and_items()`:
   - For each item in template blueprint:
     - Create `ServiceItem` record
     - Set `is_template_managed = 1`
     - Store `template_node_key`
     - Store `generated_key`
7. **Create binding**: Insert `ProjectServiceTemplateBindings` record linking template to service
8. **Return comprehensive response**:
   ```json
   {
     "service_id": 123,
     "template": { "id": "abc", "name": "...", "version": "1.0" },
     "binding": { "binding_id": 456, "options_enabled": [...] },
     "generated": {
       "review_ids": [789, 790, 791],
       "item_ids": [101, 102, 103],
       "review_count": 3,
       "item_count": 3
     }
   }
   ```

**Key Characteristics**:
- ✅ Entire service structure created atomically
- ✅ Reviews automatically generated on review cadence
- ✅ Items automatically generated with scheduling
- ✅ Template binding tracks version and options
- ✅ All generated items marked `is_template_managed=1`
- ⚠️ Cannot be undone without manual cleanup

### 2.4 Template Definition Structure

**Source**: `templates.json` (file-based) or `ServiceTemplates` table (database-based)

```json
{
  "template_id": "design_review_weekly",
  "name": "Weekly Design Review Service",
  "version": "1.0",
  "description": "Standard weekly design review with coordination & closeout",
  "service_type": "design_coordination",
  "schema_version": "1.0",
  
  "defaults": {
    "unit_type": "weekly",
    "unit_qty": 1,
    "phase": "Design Development",
    "bill_rule": "percentage"
  },
  
  "pricing": {
    "unit_type": "weekly",
    "lump_sum_fee": 2500,
    "unit_rate": 2500
  },
  
  "reviews": [
    {
      "review_id": "dr_kickoff",
      "cycle_no": 0,
      "title": "Kickoff",
      "deliverables": ["Project overview", "Coordination plan"],
      "weight_factor": 0.1,
      "disciplines": ["architect", "mep"]
    },
    {
      "review_id": "dr_weekly",
      "cycle_no": 1,
      "title": "Weekly Coordination",
      "deliverables": ["Status report", "RFI log"],
      "weight_factor": 0.9,
      "disciplines": ["all"],
      "repeat": 12  // Generate 12 copies
    }
  ],
  
  "items": [
    {
      "item_id": "dr_status",
      "title": "Weekly Status Report",
      "item_type": "deliverable",
      "description": "Consolidated progress update",
      "repeat": 12
    }
  ],
  
  "options": [
    {
      "id": "advanced_analytics",
      "name": "Advanced Analytics",
      "description": "Include trend analysis in reports",
      "affects": ["items"]  // Which sections this enables/disables
    },
    {
      "id": "weekly_video",
      "name": "Weekly Video Walkthroughs",
      "affects": ["reviews"]
    }
  ]
}
```

---

## 3. Editing Workflow

### 3.1 Service Edit Flow

**Location**: [frontend/src/pages/workspace/ServiceEditView.tsx](frontend/src/pages/workspace/ServiceEditView.tsx) → [backend/app.py](backend/app.py#L1911) `api_update_project_service()`

**Entry Point**:
1. User clicks service in Services list
2. ServiceEditView loads with service data
3. Form populated from service record

**Editable Fields**:

| Field | Editable | Notes |
|-------|----------|-------|
| service_code | ✅ Yes | Can rename/update code |
| service_name | ✅ Yes | Full name |
| phase | ✅ Yes | Update project phase |
| unit_type | ✅ Yes | Change pricing unit |
| unit_qty | ✅ Yes | Update quantity |
| unit_rate | ✅ Yes | Update per-unit cost |
| lump_sum_fee | ✅ Yes | Update fixed fee |
| agreed_fee | ✅ Yes | Override total fee |
| bill_rule | ✅ Yes | Update billing trigger |
| notes | ✅ Yes | Add service notes |
| assigned_user_id | ✅ Yes | Reassign user |
| start_date | ✅ Yes | Modify service window |
| end_date | ✅ Yes | Modify service window |
| status | ✅ Yes | Mark complete/archived |
| progress_pct | ✅ Yes | Update progress % |
| claimed_to_date | ✅ Yes | Update billed-to amount |
| review_anchor_date | ✅ Yes | Change review schedule base date |
| review_interval_days | ✅ Yes | Change review cadence |
| review_count_planned | ✅ Yes | Adjust # of reviews |
| template_mode | ⚠️ Conditional | If empty, can be set. If managed, can be cleared |

**User Interaction**:

```
1. Open ServiceEditView for service_id=123
   ↓
2. Form populated:
   ┌──────────────────────────────────────┐
   │ Service Code: [Design Review  ▼]     │ ← Edit
   │ Service Name: [Weekly DR      ▼]     │ ← Edit
   ├──────────────────────────────────────┤
   │ PRICING SECTION                      │
   │ Billing Model: [Lump Sum ▼]          │ ← Edit
   │ Lump Sum Fee: $2500                  │ ← Edit
   ├──────────────────────────────────────┤
   │ SCHEDULE SECTION                     │
   │ Review Anchor: 2026-02-01            │ ← Edit
   │ Review Interval (days): 7            │ ← Edit
   │ Number of Reviews: 12                │ ← Edit
   ├──────────────────────────────────────┤
   │ [SAVE] [RESEQUENCE REVIEWS] [DELETE] │
   └──────────────────────────────────────┘
   ↓
3. User makes changes (e.g., change review_interval_days to 14)
   ↓
4a. If template-managed service:
    ┌─────────────────────────────────────┐
    │ [SAVE]         [RESYNC FROM TEMPLATE]│
    │ Save basic    Generate/update reviews│
    │ details only  and items from template│
    └─────────────────────────────────────┘
    ↓
4b. Click [RESEQUENCE REVIEWS]:
    ┌──────────────────────────────────────┐
    │ RESEQUENCE DIALOG                    │
    │ Anchor Date: [2026-02-01] (auto)     │
    │ Interval (days): [7] (update 14 →)   │
    │ Count: [12] (existing)               │
    ├──────────────────────────────────────┤
    │ [CALCULATE] → Shows preview          │
    │ Review 1: 2026-02-01                 │
    │ Review 2: 2026-02-08                 │
    │ Review 3: 2026-02-15                 │
    │ ...                                  │
    ├──────────────────────────────────────┤
    │ [Apply Resequence] [Cancel]          │
    └──────────────────────────────────────┘
    ↓
5. Submit PATCH to backend
   ↓
6. Backend updates ProjectServices record
   ↓
7. UI refreshes, shows updated service
```

**Backend Update Logic** (`api_update_project_service`):

1. Parse request JSON with field mapping:
   ```python
   {
     "serviceCode": "xyz",       → "service_code"
     "serviceName": "new name",  → "service_name"
     "serviceDescription": "...", → "notes"
     "unitType": "weekly",       → "unit_type"
     "unitQty": 4,              → "unit_qty"
     "unitRate": 1000,          → "unit_rate"
     "lumpSumFee": 5000,        → "lump_sum_fee"
     "agreedFee": 4500,         → "agreed_fee"
     "billRule": "percentage",  → "bill_rule"
     ...
   }
   ```
2. Update `ProjectServices` record with provided fields
3. Return updated service object
4. Frontend cache invalidated, view refreshes

**Special Case: Review Resequencing**

When `review_interval_days` or `review_count_planned` change:

```
POST /api/projects/<project_id>/services/<service_id>/reviews/resequence
{
  "anchor_date": "2026-02-01",
  "interval_days": 14,
  "count": 13
}
```

Backend logic:
1. Fetch existing reviews for service
2. Calculate new planned_dates based on anchor + interval:
   ```
   Review 1: 2026-02-01
   Review 2: 2026-02-15
   Review 3: 2026-03-01
   ...
   ```
3. Update each review's `planned_date`
4. Return updated review list

### 3.2 Template-Managed Service Resync

When a service was created from template (`is_template_managed=1`):

**Location**: [backend/app.py](backend/app.py#L1774) `api_apply_service_template_to_service()`

**Concept**: Refresh generated reviews/items to match template evolution.

```
POST /api/projects/<project_id>/services/<service_id>/apply-template
{
  "template_id": "design_review_weekly",
  "options_enabled": ["advanced_analytics", "weekly_video"],
  "mode": "sync_and_update_managed",  // or "sync_missing_only"
  "dry_run": false
}
```

**Sync Modes**:

| Mode | Behavior |
|------|----------|
| `sync_missing_only` | Only add new reviews/items from template. Don't touch existing ones. |
| `sync_and_update_managed` | Add new + update existing items marked `is_template_managed=1`. Leave user-created items alone. |

**Response**:

```json
{
  "service_id": 123,
  "template": { "template_id": "...", "version": "1.0" },
  "binding": { "binding_id": 456, "options_enabled": [...] },
  "generated": {
    "review_ids": [789, 790],
    "item_ids": [101, 102],
    "review_count": 2,
    "item_count": 2
  },
  "added_reviews": [...],
  "updated_reviews": [...],
  "skipped_reviews": [...],
  "added_items": [...],
  "updated_items": [...],
  "skipped_items": [...],
  "mode": "sync_and_update_managed"
}
```

**Key Logic** (in `apply_template_to_service`):

1. Load existing template binding for service
2. Fetch current reviews/items with `template_node_key` values
3. Load template definition by `template_id`
4. For each review in template:
   - If exists with same `template_node_key`:
     - If `mode == "sync_and_update_managed"`: update it
     - Else skip (unless `sync_missing_only`)
   - Else: create new review
5. Same for items
6. Update binding record to track new template version
7. Return summary of changes

### 3.3 Review Detail Panel

**Location**: [frontend/src/components/workspace/ServiceDetailPanel.tsx](frontend/src/components/workspace/ServiceDetailPanel.tsx)

Shows service details with tabbed interface:

**Tab 1: Service Overview**
- Service code, name, phase
- Pricing summary
- Billing status
- Template info (if template-managed)

**Tab 2: Reviews**
- List of service reviews
- Add review button (if not template-managed or if manual reviews enabled)
- Edit/delete reviews (depending on status and template flags)
- Columns: Cycle #, Planned Date, Status, Disciplines, Billed?, Actions

**Tab 3: Items**
- List of service items
- Add item button
- Edit/delete items
- Columns: Title, Type, Planned Date, Status, Assigned, Billed?, Actions

**Tab 4: Template Info** (if template-managed)
- Template name, version
- Applied date, applied by
- Options enabled
- Resync from template button
- Template change history

---

## 4. Review Management

### 4.1 Review Lifecycle

```
┌─────────┐
│ CREATED │ ← Service created with reviews, or review manually added
└────┬────┘
     │
     ├─ planned_date: Service start + (cycle_no * review_interval_days)
     ├─ status: 'planned'
     └─ is_billed: false
     │
     ▼
┌──────────────┐
│ IN_PROGRESS  │ ← Review work underway
└────┬─────────┘
     │
     ├─ actual_issued_at: null (until completion)
     ├─ evidence_links: []
     └─ deliverables: []
     │
     ▼
┌──────────┐
│ COMPLETE │ ← Evidence submitted
└────┬─────┘
     │
     ├─ actual_issued_at: current_date
     ├─ status: 'complete' or 'submitted'
     ├─ evidence_links: [url1, url2, ...]
     └─ deliverables: ['Report', 'Meeting Notes', ...]
     │
     ▼
┌────────────────┐
│ BILLED         │ ← Invoice submitted
└────────────────┘
     │
     ├─ is_billed: true
     ├─ invoice_reference: 'INV-2026-0123'
     ├─ invoice_date: '2026-03-15'
     ├─ billing_amount: 2084.33 (weighted portion of service fee)
     └─ invoice_batch_id: 789
```

### 4.2 Review Billing

**Pricing Logic**:

Given service with:
- `agreed_fee`: $25,000
- `review_count_planned`: 12
- Individual review: `weight_factor` = 0.083 (default 1/12)

**Calculated Amounts**:
```
review.billing_amount = agreed_fee * weight_factor
                      = 25,000 * 0.083
                      = 2,075
```

**Invoice Batch Creation**:
```
POST /api/projects/<project_id>/services/<service_id>/reviews/invoice-batch
{
  "invoice_month": "2026-03",
  "review_ids": [789, 790, 791],
  "notes": "March deliverables"
}
```

Creates `InvoiceBatches` record + updates reviews:
- `invoice_batch_id`: Linked to batch
- `is_billed`: true
- `invoice_reference`: Populated if batch issued
- `invoice_date`: Populated if batch issued

---

## 5. Service Item Management

### 5.1 Item Hierarchy

Service items are **deliverables** within a service, independent of reviews:

```
Service: "Weekly Design Review"
├─ Review 1 (Kickoff)
├─ Review 2 (Week 1)
├─ Review 3 (Week 2)
├─ ...
└─ Items (generated or manual):
   ├─ Item 1: "Weekly Status Report" (deliverable)
   │  - Planned: 2026-02-08, Due: 2026-02-09
   │  - Repeat: 12 times
   │
   ├─ Item 2: "Coordination Memo" (deliverable)
   │  - Planned: 2026-02-15, Due: 2026-02-20
   │  - Repeat: 12 times
   │
   └─ Item 3: "Final Closeout Report" (milestone)
      - Planned: 2026-05-15, Due: 2026-05-20
      - Single occurrence
```

### 5.2 Item Creation & Linking

**Options**:

1. **Template-Generated Items** (`create_service_from_template`):
   - Automatically created with template structure
   - Marked `is_template_managed=1`
   - Can be re-synced from template

2. **Manual Items** (Add button in ServiceDetailPanel):
   ```
   POST /api/projects/<project_id>/services/<service_id>/items
   {
     "title": "Custom Report",
     "item_type": "deliverable",
     "description": "...",
     "planned_date": "2026-03-01",
     "due_date": "2026-03-05",
     "assigned_user_id": 5
   }
   ```
   - Created with `is_template_managed=0`
   - Not affected by template resync

### 5.3 Item Billing

Items have **independent billing** from reviews:

```
Service Item: "Weekly Status Report"
├─ fee_amount: 250 (per occurrence)
├─ billed_amount: 3000 (for 12 weeks)
├─ invoice_status: 'ready_for_invoice' or 'billed'
└─ invoice_reference: 'INV-2026-0145'
```

**Item Batch Invoicing**:
```
POST /api/projects/<project_id>/services/<service_id>/items/invoice-batch
{
  "invoice_month": "2026-03",
  "item_ids": [101, 102, 103],
  "notes": "March items"
}
```

---

## 6. Template System Architecture

### 6.1 Template Formats

**File-Based Templates** (`templates.json`):
- Location: `backend/templates/service_templates.json`
- Loaded on startup via `template_loader.py`
- Cached in memory with mtime checking
- YAML schema validation

**Database Templates** (`ServiceTemplates` table):
- Stored as JSON in `parameters` column
- Loaded via `_get_template_by_id(template_id)`
- Used for dynamic template creation

### 6.2 Template Application Flow

```
Template Definition
       │
       ├─ Template Loader (CANONICAL_TEMPLATE_PATH)
       │
       ├─ Database Load (_get_template_by_id)
       │
       ▼
Template Validation
       │
       ├─ Schema version check
       ├─ Required fields (template_id, name, defaults)
       └─ Item array validation
       │
       ▼
Option Resolution
       │
       ├─ Filter items by options_enabled
       ├─ Expand repeat directives
       └─ Calculate review cadence
       │
       ▼
Service Payload Resolution
       │
       ├─ Merge template defaults + overrides
       ├─ Calculate pricing (unit vs lump sum)
       └─ Derive review schedule
       │
       ▼
Database Insertion (_insert_service, _insert_review, _insert_item)
       │
       ├─ Insert service record
       ├─ Insert reviews with template_node_key
       ├─ Insert items with template_node_key
       └─ Create template binding
       │
       ▼
Generated Structure Response
       │
       └─ Return service_id, review_ids, item_ids, generated keys
```

### 6.3 Template Node Keys

**Purpose**: Track identity of reviews/items through template generations.

**Structure**:
```
template_node_key = f"{template_id}:{template_version}:{option_id}:{node_id}:{index}"
                  = "design_review_weekly:1.0:basic:dr_weekly:3"
                  = Template week 3 review
```

**Used For**:
- Matching existing records during resync
- Detecting user modifications (if modified, `is_user_modified` flag set)
- Preventing duplicate generation
- Rollback/version tracking

---

## 7. Current Workflow Efficiency Analysis

### 7.1 Strengths ✅

| Aspect | Strength | Impact |
|--------|----------|--------|
| **Dual Creation Modes** | Blank + template provides flexibility | Fast setup for common patterns, manual control when needed |
| **Atomic Template Generation** | Entire service structure created in one transaction | No partial states, reliable data |
| **Template Binding** | Tracks template version + options | Can resync with evolution, audit trail |
| **Independent Items & Reviews** | Separate billing, scheduling, status | Maximum flexibility in deliverable management |
| **Resequencing Logic** | Change review cadence without manual recalculation | Single operation updates all dates |
| **Dry-Run Mode** | Template application preview before commit | Low-risk experimentation |

### 7.2 Potential Inefficiencies ⚠️

| Aspect | Issue | Current Workaround |
|--------|-------|-------------------|
| **Template Application Complexity** | Multiple sync modes (sync_missing_only vs sync_and_update_managed) | Clear documentation + UX guidance |
| **Manual Review Creation** | Form-based review creation is step-by-step | Can apply template post-creation |
| **Item Repeat Expansion** | Template items with `repeat: 12` expanded individually | Bulk insert operations used, so performant |
| **No Template Preview** | Users can't see expanded structure before applying | `dry_run` mode + API response provides preview |
| **Binding Records** | One binding per service, but needs table query | Indexed on service_id, fast lookup |
| **Option Handling** | Options stored as JSON, parsed each time | Acceptable for typical 2-5 options per template |
| **Manual vs Template Mixing** | User items + template items can conflict conceptually | Clear `is_template_managed` flag prevents collision |

### 7.3 User Friction Points

1. **Creating Review Manually** (currently step-by-step in panel):
   - User must click "Add Review" button
   - Opens dialog for each review
   - Tedious for services with 12+ reviews

2. **Template Options Not Obvious**:
   - UI shows checkboxes but doesn't preview impact
   - No "before/after" comparison

3. **Resequencing Requires Separate Dialog**:
   - Not integrated into main edit form
   - Extra click/modal overhead

4. **No Bulk Edit**:
   - Changes to reviews (e.g., assigning user) require individual updates
   - No "apply to all reviews" button

---

## 8. Recommended Optimizations

### 8.1 Short-Term (Low Effort, High Impact)

#### 1.1 Add Template Preview

**Goal**: Show users what reviews/items will be created before applying.

**Implementation**:
```typescript
// frontend/src/api/services.ts
previewTemplate: (
  projectId: number,
  templateId: string,
  options: string[]
) => apiClient.post(
  `/projects/${projectId}/templates/${templateId}/preview`,
  { options_enabled: options }
)

// Response:
{
  "service": { "name": "Weekly Design Review", ... },
  "reviews": [
    { "cycle_no": 1, "title": "Kickoff", "planned_date": "2026-02-01" },
    { "cycle_no": 2, "title": "Week 1", "planned_date": "2026-02-08" },
    ...
  ],
  "items": [
    { "title": "Status Report", "item_type": "deliverable", "repeat": 12 },
    ...
  ],
  "summary": {
    "review_count": 13,
    "item_count": 2,
    "total_fee": 25000
  }
}
```

**Benefit**: Users see exactly what they'll get. No surprises after creation.

#### 1.2 Inline Review Addition

**Goal**: Add reviews directly in edit form without dialog popup.

**Current**: Click "Add Review" → Dialog opens → Fill fields → Submit

**Proposed**:
```
Review List
├─ Review 1: Kickoff | 2026-02-01 | [Edit] [Delete]
├─ Review 2: Week 1  | 2026-02-08 | [Edit] [Delete]
└─ [+ Add Review] (expands inline form)
   ├─ Cycle: [__]
   ├─ Title: [______________]
   ├─ Date: [____-__-__]
   └─ [Save] [Cancel]
```

**Benefit**: Faster review creation, less context switching.

#### 1.3 Bulk Review Resequencing

**Goal**: Make review date recalculation easier to understand and apply.

**Current**: Separate dialog with 3 fields, shows preview

**Proposed**: Add to main form with inline preview:
```
┌─ Review Schedule ─────────────────────┐
│ Anchor Date: [2026-02-01] (auto)      │
│ Interval (days): [7]                  │
│ Number of Reviews: [12]               │
│                                        │
│ Preview (calculated):                 │
│ ✓ Review 1: Feb 1   Review 2: Feb 8   │
│ ✓ Review 3: Feb 15  Review 4: Feb 22  │
│ ✓ ... (10 more)                       │
│                                        │
│ [Apply Dates] [Clear]                 │
└────────────────────────────────────────┘
```

**Benefit**: See impact before committing, integrated into main workflow.

#### 1.4 Template Options Impact Visualization

**Goal**: Show what each template option enables/disables.

**Proposed**:
```
Template Options:
☐ Advanced Analytics
  Adds: Analysis items + Trend report
  Cost: +$500/review
  
☐ Weekly Video Walkthroughs
  Adds: Video meeting item + Recording storage
  Cost: +$250/meeting
  
Estimated Total Reviews: 13
Estimated Total Items: 4
Estimated Service Cost: $25,500
```

**Benefit**: Transparent option impact, cost awareness.

### 8.2 Medium-Term (Moderate Effort, Significant Impact)

#### 2.1 Bulk Item Operations

**Goal**: Manage multiple items at once.

**Add API**:
```python
PATCH /api/projects/<project_id>/services/<service_id>/items/bulk
{
  "item_ids": [101, 102, 103, 104],
  "updates": {
    "assigned_user_id": 5,
    "priority": "high"
  }
}
```

**Benefit**: Assign all weekly reports to same person in one operation.

#### 2.2 Smart Template Recommendations

**Goal**: Suggest templates based on service characteristics.

**Logic**:
```python
def recommend_templates(service_name, phase, unit_type):
    # Match service_name keywords to template tags
    # Return templates matching phase + unit_type
    # Rank by usage frequency
```

**Benefit**: New users guided to appropriate templates.

#### 2.3 Template Versioning with Migration

**Goal**: Support template evolution without breaking existing services.

**Current**: Services link to template version via binding record

**Proposed**:
```python
# Track template changes
templates.json version 1.0 → 1.1
└─ Added "Advanced Analytics" option
└─ Changed Review 3 title
└─ Added 2 new items

# Migration path
def migrate_template_binding(binding_id, from_version, to_version):
    # Understand changes between versions
    # Apply transformations to existing generated items
    # Flag user for manual review if needed
    # Create audit record
```

**Benefit**: Keep services up-to-date as templates evolve.

#### 2.4 Review Template Customization

**Goal**: Allow users to modify review template before generation.

**UI**:
```
Apply Template Dialog:
┌──────────────────────────────────┐
│ Template: Design Review Weekly   │
├──────────────────────────────────┤
│ Reviews (editable before apply): │
│ ☑ Kickoff Review (cycle 0)       │
│   Title: [Kickoff ______]         │
│   Disciplines: [all_____]         │
│   Weight: [0.08]                  │
│                                  │
│ ☑ Week 1 (cycle 1-12, repeat)   │
│   Title: [Weekly Coord]           │
│   Weight: [0.077]                 │
│                                  │
│ [+ Add Custom Review]            │
│ [- Remove] [Duplicate]           │
│                                  │
│ [Apply] [Preview] [Cancel]       │
└──────────────────────────────────┘
```

**Benefit**: Customize template structure without creating new template.

### 8.3 Long-Term (Significant Effort, Strategic Impact)

#### 3.1 Template Marketplace

**Goal**: Share templates across projects/organizations.

**Architecture**:
```python
# Export service as template
POST /api/services/<service_id>/export-as-template
{
  "template_name": "Design Review - Custom",
  "description": "Based on successful project X",
  "is_shared": true,
  "tags": ["design", "weekly", "12-reviews"]
}

# Browse & import templates
GET /api/template-marketplace?tags=design
[
  {
    "template_id": "design_review_weekly",
    "name": "Design Review - Weekly",
    "version": "1.0",
    "uses": 23,
    "created_by": "admin",
    "tags": ["design", "weekly", "popular"]
  }
]
```

**Benefit**: Organizational knowledge sharing, faster adoption.

#### 3.2 Service Cloning with Template Binding

**Goal**: Clone existing service (copy+modify).

**Implementation**:
```python
POST /api/projects/<target_project_id>/services/clone
{
  "source_service_id": 123,
  "source_project_id": 100,
  "name_suffix": "- Phase 2",
  "date_offset_days": 180,  # Shift all dates forward
  "clear_billing": true     # New service starts unbilled
}
```

**Response**:
```json
{
  "service_id": 456,
  "project_id": 101,
  "reviews_cloned": 13,
  "items_cloned": 4,
  "template_binding": { "binding_id": 789, "template_id": "..." }
}
```

**Benefit**: Repeat similar workflows quickly (Phase 1 → Phase 2).

#### 3.3 Workflow Rules Engine

**Goal**: Automate common follow-up tasks.

**Examples**:
```javascript
// Rule: Auto-create items when review is complete
{
  "trigger": "review_status == 'complete'",
  "actions": [
    {
      "action": "create_items",
      "template": "closeout_items",
      "copy_values": ["assigned_user_id", "service_id"]
    }
  ]
}

// Rule: Auto-bill when all reviews complete
{
  "trigger": "all_reviews_complete && is_billed == false",
  "actions": [
    {
      "action": "create_billing_batch",
      "invoice_month": "NEXT_MONTH",
      "notify": ["project_manager"]
    }
  ]
}
```

**Benefit**: Reduce manual coordination tasks.

---

## 9. Data Dictionary

### ProjectServices

| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| service_id | INT | PK, auto | Unique service identifier |
| project_id | INT | FK→Projects | Parent project |
| service_code | VARCHAR(50) | Unique/project | Service identifier code |
| service_name | VARCHAR(255) | | Human-readable name |
| phase | VARCHAR(100) | | Project phase (Design, Execution, Closeout) |
| unit_type | VARCHAR(100) | | Billing unit (weekly, monthly, per-item) |
| unit_qty | DECIMAL | | Number of units |
| unit_rate | DECIMAL | | Price per unit |
| lump_sum_fee | DECIMAL | | Fixed fee option |
| agreed_fee | DECIMAL | | Override fee |
| bill_rule | VARCHAR(100) | | Billing trigger (percentage, milestone, date) |
| notes | TEXT | | Service description/notes |
| start_date | DATE | | Service start |
| end_date | DATE | | Service end |
| review_anchor_date | DATE | | Base date for review schedule |
| review_interval_days | INT | | Days between reviews |
| review_count_planned | INT | | Planned number of reviews |
| source_template_id | VARCHAR(255) | FK→ServiceTemplates | Origin template ID |
| source_template_version | VARCHAR(20) | | Template version applied |
| source_template_hash | VARCHAR(64) | | Template content hash |
| template_mode | VARCHAR(50) | NULL/'managed' | Indicates if template-managed |
| status | VARCHAR(50) | | Service status (active, complete, archived) |
| progress_pct | INT | DEFAULT 0 | Completion percentage |
| claimed_to_date | DECIMAL | DEFAULT 0 | Amount billed to date |
| assigned_user_id | INT | FK→Users | Responsible party |
| created_at | DATETIME | | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

### ServiceReviews

| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| review_id | INT | PK, auto | Unique review identifier |
| project_id | INT | FK→Projects | Parent project |
| service_id | INT | FK→ProjectServices | Parent service |
| phase | VARCHAR(100) | | Project phase |
| cycle_no | INT | | Review cycle number (0-based) |
| planned_date | DATE | | Scheduled review date |
| due_date | DATE | | Deliverable due date |
| actual_issued_at | DATETIME | NULL | When actually issued |
| status | VARCHAR(50) | | Review status (planned, in_progress, complete, submitted) |
| disciplines | VARCHAR(500) | | CSV/JSON of involved disciplines |
| deliverables | VARCHAR(1000) | | Description of deliverables |
| evidence_links | TEXT | | JSON array of evidence URLs |
| weight_factor | DECIMAL | DEFAULT 0.0833 | Billing weight (0-1) |
| is_billed | BIT | DEFAULT 0 | Billed flag |
| billing_phase | VARCHAR(100) | | Billing phase label |
| billing_rate | DECIMAL | | Rate applied to this review |
| billing_amount | DECIMAL | | Amount for this review |
| invoice_reference | VARCHAR(100) | NULL | Invoice number |
| invoice_date | DATE | NULL | Invoice date |
| invoice_batch_id | INT | FK→InvoiceBatches | Batch reference |
| invoice_status | VARCHAR(50) | | Status (ready, issued, paid) |
| is_template_managed | BIT | DEFAULT 0 | Can be resync'd from template |
| template_node_key | VARCHAR(255) | | Node identity in template |
| generated_from_template_id | VARCHAR(255) | | Source template |
| generated_from_template_version | VARCHAR(20) | | Template version |
| generated_key | VARCHAR(255) | | Generation run identifier |
| is_user_modified | BIT | DEFAULT 0 | User has edited this review |
| user_modified_at | DATETIME | NULL | When user last modified |
| user_modified_fields | VARCHAR(500) | | Fields user edited |
| origin | VARCHAR(50) | | 'generated' or 'manual' |
| sort_order | INT | | Display order |
| created_at | DATETIME | | Record creation |
| updated_at | DATETIME | | Last modification |

### ServiceItems

| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| item_id | INT | PK, auto | Unique item identifier |
| project_id | INT | FK→Projects | Parent project |
| service_id | INT | FK→ProjectServices | Parent service |
| phase | VARCHAR(100) | | Project phase |
| item_type | VARCHAR(50) | | Type (deliverable, milestone, audit, report) |
| title | VARCHAR(255) | | Item title |
| description | TEXT | | Item description |
| planned_date | DATE | | Planned delivery date |
| due_date | DATE | | Due date |
| actual_date | DATE | NULL | Actual delivery date |
| status | VARCHAR(50) | | Status (planned, in_progress, complete, overdue) |
| priority | VARCHAR(50) | | Priority (low, medium, high, critical) |
| assigned_user_id | INT | FK→Users | Assigned to |
| fee_amount | DECIMAL | | Fee per item (or total if not repeat) |
| billed_amount | DECIMAL | | Amount billed |
| invoice_status | VARCHAR(50) | | Status (ready, issued, paid) |
| invoice_reference | VARCHAR(100) | NULL | Invoice number |
| invoice_date | DATE | NULL | Invoice date |
| evidence_links | TEXT | | JSON array of evidence URLs |
| notes | TEXT | | Item notes |
| is_template_managed | BIT | DEFAULT 0 | Can be resync'd from template |
| template_node_key | VARCHAR(255) | | Node identity in template |
| generated_from_template_id | VARCHAR(255) | | Source template |
| generated_from_template_version | VARCHAR(20) | | Template version |
| generated_key | VARCHAR(255) | | Generation run identifier |
| is_user_modified | BIT | DEFAULT 0 | User has edited this item |
| sort_order | INT | | Display order |
| created_at | DATETIME | | Record creation |
| updated_at | DATETIME | | Last modification |

---

## 10. API Reference

### Service Creation

**POST** `/api/projects/<project_id>/services`

Create blank service.

**Request**:
```json
{
  "service_code": "DR-001",
  "service_name": "Weekly Design Review",
  "phase": "Design Development",
  "unit_type": "weekly",
  "unit_qty": 1,
  "unit_rate": 2500,
  "lump_sum_fee": null,
  "agreed_fee": 30000,
  "bill_rule": "percentage",
  "notes": "Coordination and review meetings",
  "assigned_user_id": 5,
  "start_date": "2026-02-01",
  "end_date": "2026-05-31"
}
```

**Response**:
```json
{
  "service_id": 123,
  "project_id": 100,
  "service_code": "DR-001",
  "service_name": "Weekly Design Review",
  "status": "active",
  "created_at": "2026-01-15T10:30:00Z"
}
```

---

### Service Creation from Template

**POST** `/api/projects/<project_id>/services/from-template`

Create service with auto-generated reviews and items.

**Request**:
```json
{
  "template_id": "design_review_weekly",
  "options_enabled": ["advanced_analytics"],
  "overrides": {
    "service_name": "Design Review - Phase 2",
    "agreed_fee": 35000,
    "start_date": "2026-06-01",
    "review_interval_days": 10,
    "review_count_planned": 15
  }
}
```

**Response**:
```json
{
  "service_id": 124,
  "project_id": 100,
  "template": {
    "template_id": "design_review_weekly",
    "name": "Weekly Design Review Service",
    "version": "1.0"
  },
  "binding": {
    "binding_id": 456,
    "options_enabled": ["advanced_analytics"]
  },
  "generated": {
    "review_ids": [789, 790, 791, 792, 793],
    "item_ids": [101, 102],
    "review_count": 5,
    "item_count": 2
  }
}
```

---

### Service Update

**PATCH** `/api/projects/<project_id>/services/<service_id>`

Update service fields.

**Request**:
```json
{
  "serviceCode": "DR-001-REV",
  "serviceName": "Weekly Design Review - Updated",
  "agreed_fee": 32000,
  "status": "active",
  "reviewIntervalDays": 14
}
```

**Response**:
```json
{
  "service_id": 123,
  "service_code": "DR-001-REV",
  "service_name": "Weekly Design Review - Updated",
  "agreed_fee": 32000,
  "review_interval_days": 14,
  "updated_at": "2026-01-15T11:45:00Z"
}
```

---

### Service Review Resequencing

**POST** `/api/projects/<project_id>/services/<service_id>/reviews/resequence`

Recalculate review dates based on cadence.

**Request**:
```json
{
  "anchor_date": "2026-02-01",
  "interval_days": 14,
  "count": 13
}
```

**Response**:
```json
{
  "reviews_updated": 13,
  "reviews": [
    { "review_id": 789, "cycle_no": 0, "planned_date": "2026-02-01" },
    { "review_id": 790, "cycle_no": 1, "planned_date": "2026-02-15" },
    { "review_id": 791, "cycle_no": 2, "planned_date": "2026-03-01" },
    ...
  ]
}
```

---

### Service Template Resync

**POST** `/api/projects/<project_id>/services/<service_id>/apply-template`

Refresh service structure from template.

**Request**:
```json
{
  "template_id": "design_review_weekly",
  "options_enabled": ["advanced_analytics", "weekly_video"],
  "mode": "sync_and_update_managed",
  "dry_run": false
}
```

**Response**:
```json
{
  "service_id": 123,
  "binding": {
    "binding_id": 456,
    "options_enabled": ["advanced_analytics", "weekly_video"]
  },
  "generated": {
    "review_count": 15,
    "item_count": 3
  },
  "added_reviews": 2,
  "updated_reviews": 13,
  "skipped_reviews": 0,
  "added_items": 1,
  "updated_items": 2,
  "skipped_items": 0,
  "mode": "sync_and_update_managed",
  "dry_run": false
}
```

---

### Get Generated Service Structure

**GET** `/api/projects/<project_id>/services/<service_id>/generated-structure`

Retrieve template binding and generated items.

**Response**:
```json
{
  "service": {
    "service_id": 123,
    "service_name": "Weekly Design Review",
    "template_mode": "managed"
  },
  "template": {
    "template_id": "design_review_weekly",
    "name": "Weekly Design Review Service",
    "version": "1.0"
  },
  "binding": {
    "binding_id": 456,
    "template_id": "design_review_weekly",
    "options_enabled": ["advanced_analytics"],
    "applied_at": "2026-01-15T10:30:00Z"
  },
  "generated_reviews": [
    { "review_id": 789, "cycle_no": 0, "title": "Kickoff", "is_template_managed": true },
    ...
  ],
  "generated_items": [
    { "item_id": 101, "title": "Status Report", "is_template_managed": true },
    ...
  ]
}
```

---

## 11. Conclusion

The services and deliverables workflow is **well-architected** with clear separation of concerns, template support, and independent billing for reviews and items. The system balances **automation** (template-driven creation) with **flexibility** (manual review/item creation).

### Key Achievements
✅ Atomic template application  
✅ Editable review cadence with resequencing  
✅ Template versioning via binding records  
✅ Independent billing for reviews and items  
✅ User modification tracking  

### Recommended Focus Areas
🎯 **Quick Wins**: Template preview, inline review addition, bulk resequencing  
🎯 **Medium-Term**: Bulk item operations, template recommendations, migration path  
🎯 **Strategic**: Template marketplace, service cloning, workflow rules engine  

The workflow is **production-ready** and mature. Optimizations focus on UX improvements and organizational scaling (marketplace, sharing, automation).

---

**End of Document**
