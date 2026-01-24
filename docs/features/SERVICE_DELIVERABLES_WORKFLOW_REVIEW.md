# Service & Deliverables Workflow - User Perspective Review

**Date**: January 23, 2026  
**Reviewer**: AI Agent  
**Purpose**: Comprehensive user workflow analysis for creating and editing services with their dependent deliverables

---

## Table of Contents
1. [Workflow 1: Creating a New Service with Deliverables](#workflow-1-creating-a-new-service-with-deliverables)
2. [Workflow 2: Editing an Existing Service and Its Deliverables](#workflow-2-editing-an-existing-service-and-its-deliverables)
3. [Core Architectural Principles](#core-architectural-principles)
4. [Issues and Observations](#issues-and-observations)
5. [Recommendations](#recommendations)

---

## Workflow 1: Creating a New Service with Deliverables

### Starting Point
**User Action**: Navigate to project workspace → Services tab → Click "Create New Service" button

**Entry Point**: `frontend/src/pages/workspace/ServicesTab.tsx`  
**Destination**: `frontend/src/pages/workspace/ServiceCreateView.tsx`

### Step-by-Step User Journey

#### 1. Choose Service Creation Mode

**User sees two options:**
- **Blank Service** (default): Manual entry of all service details
- **From Template**: Apply a pre-defined service template with items and reviews

**UI Elements:**
- Toggle buttons to switch between modes
- Current mode indicated by active styling

**Backend**: No API call at this stage

---

#### 2a. Create Blank Service (Manual Entry)

**User fills out the form:**

##### Basic Information
- **Service Code** (required) - e.g., "D.01"
- **Service Name** (required) - e.g., "Design Development"
- **Phase** (optional) - e.g., "Design"
- **Start Date** (required) - Date picker, defaults to project start date
- **End Date** (optional) - Date picker
- **Assigned User** (optional) - Dropdown of available users

**Data Source**: `GET /api/users` (loaded via React Query)

##### Billing Model Selection
User selects one of two billing models:

**Option 1: Lump Sum**
- **Lump Sum Fee** (optional) - Numeric input
- **Agreed Fee** (required) - Numeric input, total billable amount

**Option 2: Unit Based**
- **Billing Rule** (required) - Dropdown, e.g., "on_completion", "monthly"
- **Unit Type** (required) - Text input, e.g., "hours", "drawings"
- **Unit Quantity** (required) - Numeric input
- **Unit Rate** (required) - Numeric input, $ per unit

**Data Source**: Billing rules from `GET /api/service_templates` → catalog

##### Additional Fields
- **Notes** (optional) - Multi-line text area for service description

**Form Validation:**
```typescript
// Required fields check
- service_code: Must not be empty
- service_name: Must not be empty
- start_date: Must be set

// Billing model check
if (billing_model === 'lump_sum'):
  - agreed_fee: Required
else if (billing_model === 'unit_based'):
  - unit_type, unit_qty, unit_rate, bill_rule: All required
```

**User Action**: Click "Create Service" button

**API Call**: `POST /api/projects/{project_id}/services`
```json
{
  "service_code": "D.01",
  "service_name": "Design Development",
  "phase": "Design",
  "start_date": "2026-02-01",
  "end_date": "2026-06-30",
  "assigned_user_id": 5,
  "billing_model": "lump_sum",
  "lump_sum_fee": 50000,
  "agreed_fee": 50000,
  "notes": "Complete design development phase"
}
```

**Backend Processing**: `backend/app.py:api_create_project_service()`
- Validates required fields
- Validates billing model consistency
- Defaults start_date if not provided
- Calls `create_project_service()` in `database.py`
- Inserts into `ProjectServices` table
- Returns `service_id`

**Success Response**:
```json
{
  "service_id": 123
}
```

**User Navigation**: Redirects to Services tab with new service selected
`/projects/{project_id}/workspace/services?sel=service:123`

**Deliverables Note**: At this stage, NO deliverables/items are created. The service exists but is empty.

---

#### 2b. Create Service from Template

**User Experience:**

##### Template Selection
- **Template Dropdown** - Shows all available service templates
- Auto-selects first template if available
- Displays template metadata:
  - Name
  - Description
  - Default pricing model
  - Available optional features

**Data Source**: `GET /api/service_templates` via `serviceTemplateCatalogApi.getAll()`

**Template Structure Preview:**
```typescript
{
  template_id: "design-review-weekly",
  name: "Weekly Design Review",
  description: "Standard weekly review cycle with submittal items",
  defaults: {
    service_code: "DR.01",
    service_name: "Design Reviews",
    phase: "Design",
    bill_rule: "on_completion"
  },
  pricing: {
    model: "per_unit",  // or "lump_sum"
    unit_type: "review",
    unit_qty: 20,
    unit_rate: 500
  },
  options: [
    {
      option_id: "rfi-response",
      name: "Include RFI Response Items",
      enabled_by_default: false
    }
  ],
  items: [...],  // Pre-defined service items
  reviews: [...] // Pre-defined review cycles
}
```

##### Template Overrides (Accordion - "Overrides & Options")
User can override template defaults:
- **Service Code** - Pre-filled from template, editable
- **Service Name** - Pre-filled from template, editable
- **Phase** - Pre-filled from template, editable
- **Start Date** - Pre-filled from project start, editable
- **Assigned User** - Dropdown to select user
- **Agreed Fee Override** - Numeric input to override calculated fee
- **Notes Override** - Multi-line text for additional notes

##### Optional Features
- **Checkboxes** for each template option
- Pre-checked if `enabled_by_default: true`
- User can enable/disable before creating service

**Example**: "Include RFI Response Items" checkbox adds 3 additional service items to the generated structure

**Form Validation:**
- Same as blank service validation
- Template values are merged with overrides

**User Action**: Click "Create Service" button

**API Call**: `POST /api/projects/{project_id}/services/from-template`
```json
{
  "template_id": "design-review-weekly",
  "options_enabled": ["rfi-response"],
  "overrides": {
    "service_code": "DR.02",
    "service_name": "Weekly Design Review - Tower B",
    "phase": "Design",
    "assigned_user_id": 5,
    "start_date": "2026-02-01",
    "agreed_fee": 12000
  }
}
```

**Backend Processing**: `backend/app.py:api_apply_service_template_to_project()`
- Loads template definition from `ServiceTemplateDefinitions` table
- Merges template defaults with user overrides
- Creates service in `ProjectServices` table
- **Generates dependent structures:**
  - **Service Reviews** - If template has review cycle definitions
    - Inserts into `Reviews` table
    - Links via `service_id` foreign key
    - Sets review cadence (weekly, monthly, etc.)
  - **Service Items** - If template has item definitions
    - Inserts into `ServiceItems` table
    - Links via `service_id` foreign key
    - Marks with `generated_from_template_id` and `is_template_managed` flags
- Returns `service_id`

**Success Response**:
```json
{
  "service_id": 124,
  "message": "Service created from template with 15 items and 20 reviews"
}
```

**User Navigation**: Redirects to Services tab with new service selected
`/projects/{project_id}/workspace/services?sel=service:124`

**Deliverables Result**: Service is created WITH pre-populated items and review cycles ready for use.

---

### Step 3: Viewing Created Service

**User sees:**
- Service listed in the Services tab
- Service card/row showing:
  - Service code and name
  - Phase
  - Start/end dates
  - Status badge (default: "planned")
  - Assigned user
  - Progress indicators
  - Pricing information

**User can now:**
1. Click service to view details
2. Navigate to edit view
3. Add manual deliverables/items
4. Create review cycles
5. Link issues and imports

---

## Workflow 2: Editing an Existing Service and Its Deliverables

### Starting Point
**User Action**: Navigate to project workspace → Services tab → Select service → Click "Edit" button or icon

**Entry Point**: `frontend/src/pages/workspace/ServicesTab.tsx`  
**Destination**: `frontend/src/pages/workspace/ServiceEditView.tsx`

**API Calls on Page Load:**
1. `GET /api/projects/{project_id}/services` - Load all services
2. `GET /api/projects/{project_id}/services/{service_id}/generated-structure` - Load template metadata
3. `GET /api/projects/{project_id}/services/{service_id}/reviews` - Load review cycles
4. `GET /api/projects/{project_id}/services/{service_id}/items` - Load service items
5. `GET /api/users` - Load assignable users
6. `GET /api/service_templates` - Load template catalog for bill rules

---

### Section 1: Edit Service Basics (Accordion - "Basics")

**User can edit:**
- **Service Code** - Text input
- **Service Name** - Text input
- **Phase** - Text input
- **Start Date** - Date picker
- **End Date** - Date picker
- **Status** - Dropdown: `planned | in_progress | completed | overdue | cancelled`
- **Assigned User** - Dropdown of users
- **Notes** - Multi-line text area

**User Action**: Make changes → Click "Save Changes" button

**API Call**: `PATCH /api/projects/{project_id}/services/{service_id}`
```json
{
  "service_code": "DR.02-UPDATED",
  "status": "in_progress",
  "notes": "Updated notes"
}
```

**Backend Processing**: `backend/app.py:api_update_project_service()`
- Maps frontend field names to database columns
  - `serviceCode` → `service_code`
  - `serviceDescription` → `notes`
  - etc.
- Validates only allowed fields are updated
- Calls `update_project_service()` in `database.py`
- Updates `ProjectServices` table with SQL UPDATE
- Returns success status

**Success Feedback**: Toast notification or success alert

---

### Section 2: Edit Pricing (Accordion - "Pricing")

**User can edit:**
- **Unit Type** - Text input
- **Unit Quantity** - Numeric input
- **Unit Rate** - Numeric input
- **Lump Sum Fee** - Numeric input
- **Bill Rule** - Dropdown from catalog
- **Agreed Fee** - Numeric input (read-only calculated or manual override)

**User Action**: Make changes → Click "Save Changes" button

**API Call**: Same as above, `PATCH /api/projects/{project_id}/services/{service_id}`
```json
{
  "unit_qty": 25,
  "unit_rate": 600,
  "agreed_fee": 15000
}
```

**Backend**: Updates same `ProjectServices` record

---

### Section 3: Edit Progress (Accordion - "Progress")

**User sees:**
- **Completion Percentage** - Calculated or manual override
- **Review Cycle Management**
  - List of review cycles linked to this service
  - Status of each review (planned, completed, cancelled)
  - Planned vs actual dates
  - **Re-sequence Button** - Adjust review cycle dates

**Re-sequence Reviews Dialog:**
1. User clicks "Re-sequence Reviews" button
2. Dialog opens with fields:
   - **Anchor Date** - Starting date for sequence
   - **Interval (days)** - Days between reviews (e.g., 7 for weekly)
   - **Count (optional)** - Number of reviews to create/update
3. User fills and clicks "Apply"

**API Call**: `POST /api/projects/{project_id}/services/{service_id}/reviews/resequence`
```json
{
  "anchor_date": "2026-02-01",
  "interval_days": 7,
  "count": 20
}
```

**Backend Processing**: `backend/app.py:api_resequence_service_reviews()`
- Loads all `planned` reviews for the service
- Only updates reviews that are:
  - Status = "planned"
  - Not manually modified by user
- Updates `planned_date` and `due_date` in sequence
- Preserves user modifications

---

### Section 4: Template Synchronization (Accordion - "Template Metadata")

**Visible only if**: Service was generated from a template

**User sees:**
- **Template Name** - Read-only
- **Template Version** - Read-only
- **Generated Date** - Read-only
- **Re-sync Template Button** - Primary action

#### Re-sync Template Workflow

**Purpose**: Pull latest template changes into existing service

**User Action**: Click "Re-sync Template" button

**Re-sync Dialog Opens:**

##### Step 1: Configure Re-sync
- **Enabled Options** - Checkboxes for template optional features
- **Re-sync Mode** - Dropdown:
  - `sync_missing_only` - Only add new items/reviews that don't exist
  - `sync_and_update_managed` - Add new + update existing template-managed items

##### Step 2: Preview Diff
**API Call**: `POST /api/projects/{project_id}/services/{service_id}/apply-template`
```json
{
  "template_id": "design-review-weekly",
  "options_enabled": ["rfi-response"],
  "mode": "sync_and_update_managed",
  "dry_run": true
}
```

**Response - Diff Preview**:
```json
{
  "added_reviews": [
    {"review_title": "Week 21 Review", "planned_date": "2026-06-15"}
  ],
  "updated_reviews": [
    {"review_id": 456, "field": "cycle_no", "old": 10, "new": 11}
  ],
  "skipped_reviews": [
    {"review_id": 789, "reason": "user_modified"}
  ],
  "added_items": [
    {"title": "RFI Response Set 3", "item_type": "report"}
  ],
  "updated_items": [],
  "skipped_items": [
    {"item_id": 321, "reason": "status_not_planned"}
  ]
}
```

**User sees:**
- Reviews: +1 added / 1 updated / 15 skipped
- Items: +1 added / 0 updated / 12 skipped
- Warning: "Updates only apply to planned, template-managed, and unmodified rows. No deletions are performed."

##### Step 3: Apply Re-sync
**User Action**: Click "Apply Re-sync" button

**API Call**: Same endpoint with `dry_run: false`

**Backend Processing**: `backend/app.py:api_apply_service_template_to_service()`
- Validates service exists and was generated from template
- Loads current template definition
- Compares existing reviews/items with template
- **Review Sync Logic:**
  - Adds new reviews from template
  - Updates template-managed reviews if `sync_and_update_managed`
  - Preserves user-modified reviews (checks `is_user_modified` flag)
  - Never deletes existing reviews
- **Item Sync Logic:**
  - Adds new items from template
  - Updates template-managed items if mode permits
  - Preserves user-added items (checks `origin != 'template_generated'`)
  - Never deletes existing items
- Returns sync result summary

**Success Feedback**: Dialog shows success message with counts

**User Navigation**: Dialog closes, page data refreshes

---

### Section 5: Add Individual Service Item from Template

**Purpose**: Add a single deliverable item without full re-sync

**User sees:**
- **Autocomplete Dropdown** - "Add Item From Template / Catalog"
- Lists all template items grouped by category
- Items already added are disabled with "Already added" label

**User Action**: 
1. Search/select item from dropdown
2. Click "Add Item" button

**API Call**: `POST /api/projects/{project_id}/services/{service_id}/items`
```json
{
  "item_type": "report",
  "title": "RFI Response Set 3",
  "planned_date": "2026-03-15",
  "status": "planned",
  "priority": "medium",
  "origin": "template_generated",
  "generated_from_template_id": "design-review-weekly",
  "template_node_key": "items.rfi_response_set",
  "is_template_managed": true
}
```

**Backend Processing**: `backend/app.py:api_create_service_item()`
- Validates service exists in project
- Validates required fields: `item_type`, `title`
- Defaults `planned_date` to service start date if not provided
- Inserts into `ServiceItems` table
- Links via `service_id` foreign key
- Returns `item_id`

**Success Response**:
```json
{
  "item_id": 456,
  "message": "Service item created successfully"
}
```

**UI Update**: Item appears in "Generated Items" list immediately (optimistic update via React Query)

---

### Section 6: View and Manage Generated Items (In Edit View)

**User sees:**
- **Generated Items List** - Read-only preview
- Each item shows:
  - Title
  - Generated key (e.g., `items.weekly_report_01`)
  - Item type

**Note**: This is a preview only. Full editing happens in the Deliverables Tab.

---

### Section 7: Edit Service Items (Deliverables Tab)

**Navigation**: Project Workspace → Deliverables Tab

**Entry Point**: `frontend/src/pages/workspace/DeliverablesTab.tsx`

**API Calls on Load:**
1. `GET /api/projects/{project_id}/reviews` - All project reviews
2. `GET /api/projects/{project_id}/services` - All services
3. `GET /api/projects/{project_id}/services/{service_id}/items` - Items for selected service
4. `GET /api/projects/{project_id}/invoice-batches` - Invoice batches for billing

#### View Modes

**User can switch between:**
1. **Review Cycles** (deliverables from review system)
2. **Service Items** (deliverables from item system)

Both are displayed in a unified table/list with filters.

#### Filters (Chip buttons)
- **Due this month** - Shows items due in current month
- **Unbatched** - Shows items not assigned to invoice batch
- **Ready to invoice** - Shows completed but unbilled items

#### Service Selector
- **Dropdown** - Select which service's items to view/edit
- Defaults to first service or selection from URL

---

#### Edit Service Item - Inline Editing

**Table Columns:**
| Column | Type | Editable |
|--------|------|----------|
| Title | Text | ✅ Click to edit |
| Type | Dropdown | ✅ Click to edit |
| Planned Date | Date | ✅ Date picker |
| Due Date | Date | ✅ Date picker |
| Status | Dropdown | ✅ planned/in_progress/completed/overdue/cancelled |
| Priority | Dropdown | ✅ low/medium/high/critical |
| Assigned To | Text | ✅ Click to edit |
| Invoice Reference | Text | ✅ Click to edit |
| Billed | Toggle | ✅ Checkbox |

**User Action**: Click any editable cell

**Edit Interaction**:
1. Cell becomes editable (text field, date picker, or dropdown appears)
2. User makes change
3. Field auto-saves on blur/change

**API Call**: `PATCH /api/projects/{project_id}/services/{service_id}/items/{item_id}`
```json
{
  "status": "completed",
  "actual_date": "2026-03-20"
}
```

**Backend Processing**: `backend/app.py:api_update_service_item()`
- Validates item exists in service and project (security check)
- Filters allowed fields (prevents updating system fields)
- Updates `ServiceItems` table with SQL UPDATE
- Returns success or error

**Optimistic Update**: UI updates immediately, rolls back on error

**Error Handling**: If API call fails:
- Previous value is restored
- Error alert displayed: "Failed to update item."

---

#### Add New Service Item (Manual)

**User Action**: Click "Add Deliverable" button (or similar)

**UI Interaction**:
1. New draft row appears at top of table
2. All fields are editable
3. Required fields: `item_type`, `title`, `planned_date`
4. Other fields optional

**User fills:**
- **Title** - Required, e.g., "Design Submittal Package 3"
- **Type** - Required dropdown, e.g., "deliverable", "report", "meeting"
- **Planned Date** - Required, defaults to service start date
- **Due Date** - Optional
- **Priority** - Defaults to "medium"
- **Status** - Defaults to "planned"

**User Action**: Blur from last field or click "Save" (depends on implementation)

**API Call**: `POST /api/projects/{project_id}/services/{service_id}/items`
```json
{
  "item_type": "deliverable",
  "title": "Design Submittal Package 3",
  "planned_date": "2026-03-15",
  "due_date": "2026-03-20",
  "status": "planned",
  "priority": "high",
  "origin": "user_created"
}
```

**Backend**: Same as template-generated item creation, but `origin: 'user_created'` and no template metadata

**Success**: Item ID returned, draft row replaced with permanent row

---

#### Delete Service Item

**User Action**: Click delete icon/button on item row

**Confirmation**: Dialog or inline confirmation (depending on implementation)

**API Call**: `DELETE /api/projects/{project_id}/services/{service_id}/items/{item_id}`

**Backend Processing**: `backend/app.py:api_delete_service_item()`
- Validates item exists in service and project
- Calls `delete_service_item()` in `database.py`
- Deletes from `ServiceItems` table
- Returns success

**UI Update**: Row removed from table

---

## Core Architectural Principles

### Critical: Items vs Tasks Distinction

**MUST PRESERVE**: The system uses this hierarchy:
```
Project → Services → {Reviews, Items}
Project → Tasks
```

**Items (Service Deliverables):**
- **Foreign Key**: `service_id` (REQUIRED)
- **Purpose**: Deliverables, offerings, scopes tied to services
- **Examples**: "Weekly progress report", "RFI submittal review set"
- **NOT**: Execution tasks

**Tasks (Project Execution):**
- **Foreign Key**: `project_id` (REQUIRED)
- **Purpose**: Work to be done, execution tracking
- **Examples**: "Coordinate HVAC ductwork", "Prepare submittal response"
- **Independent of**: Services, Reviews, and Items

**Reviews (Service Cycles):**
- **Foreign Key**: `service_id` (REQUIRED)
- **Purpose**: Recurring review cycles/meetings
- **Examples**: "Week 5 Design Review", "Monthly Progress Review"
- **Independent of**: Items (no FK between Reviews and Items)

### Import Linking Priority

When linking external data (ACC issues, Revizto, health checks):
```
1. project_id (ALWAYS REQUIRED)
   ↓
2. service_id (PRIMARY - use when scope is clear)
   ↓
3. review_id (OPTIONAL - context only)
   ↓
4. item_id (OPTIONAL - context only)
   ↓
5. UNMAPPED (VALID STATE - when mapping is undefined)
```

**Unmapped imports are valid** and awaiting manual assignment.

---

## Issues and Observations

### 🟢 Strengths

1. **Template System is Powerful**
   - Pre-configured services with items and reviews
   - Optional feature toggles
   - Re-sync capability maintains connection to template
   - Significantly reduces setup time

2. **Flexible Billing Models**
   - Supports lump sum and unit-based billing
   - User can override template pricing
   - Billing rules are configurable

3. **Inline Editing Experience**
   - Fast, low-friction editing in Deliverables tab
   - Optimistic updates for snappy UX
   - Auto-save on blur reduces clicks

4. **Template Sync Safety**
   - Diff preview before applying changes
   - Never deletes user data
   - Respects user modifications (`is_user_modified` flag)
   - Multiple sync modes for different scenarios

5. **Separation of Concerns**
   - Services, Items, Reviews, and Tasks are properly separated
   - Clear foreign key relationships
   - No conflation of deliverables with execution tasks

### 🟡 Moderate Issues

1. **Discoveryability of Deliverables Tab**
   - Service edit view shows "Generated Items" list but it's read-only
   - User might not know to navigate to Deliverables Tab for full editing
   - **Recommendation**: Add prominent link/button from Service Edit View to Deliverables Tab filtered to current service

2. **Service Item Addition Ambiguity**
   - Two ways to add items:
     1. From template/catalog (in Service Edit View)
     2. Manual creation (in Deliverables Tab)
   - Not clear which method to use when
   - **Recommendation**: Add guidance text or split into "Add from Template" vs "Add Custom Item" buttons

3. **No Bulk Operations**
   - User must edit items one by one
   - No bulk status updates (e.g., mark all as completed)
   - No bulk date adjustments
   - **Recommendation**: Add multi-select and bulk action toolbar

4. **Limited Item Metadata**
   - Items have basic fields but no rich metadata:
     - No file attachments UI
     - No comments/discussion thread
     - No activity log
   - Evidence links are plain text, not structured
   - **Recommendation**: Consider adding:
     - Attachment management
     - Comment thread per item
     - Activity/audit trail

5. **Service Status is Manual**
   - Service status must be manually updated
   - Not automatically derived from item/review completion
   - Risk of status drift
   - **Recommendation**: Add auto-calculated status with manual override option

### 🔴 Critical Issues

1. **No Validation for Template Compatibility**
   - User can re-sync template even if service was heavily modified
   - No warning if re-sync will cause unexpected changes
   - **Risk**: User confusion or accidental overwrites
   - **Recommendation**: Add compatibility check and warning if service diverged significantly

2. **Missing Service-Item Dependencies**
   - Items can be deleted without checking if they're referenced elsewhere:
     - Issues linked to items
     - Invoice batches referencing items
     - Tasks that mention items
   - **Risk**: Broken references, data integrity issues
   - **Recommendation**: Add dependency checks before deletion with warning or prevent deletion

3. **No Undo/Redo for Edits**
   - Inline edits are immediately saved
   - No way to undo accidental changes
   - **Risk**: User mistakes are permanent
   - **Recommendation**: Add:
     - Confirmation dialogs for critical changes
     - Undo queue (last 10 actions)
     - Audit trail with restore capability

4. **Concurrent Edit Conflicts Not Handled**
   - Multiple users can edit same service/item simultaneously
   - Last write wins, no conflict detection
   - **Risk**: Data loss from concurrent edits
   - **Recommendation**: Add:
     - Optimistic locking with version numbers
     - Conflict detection and merge UI
     - Real-time indicators of other users editing

5. **Template Re-sync Preview is Limited**
   - Diff shows counts but not detailed field-level changes
   - User cannot see exactly what will be updated
   - No option to selectively apply changes
   - **Risk**: Unexpected changes applied in bulk
   - **Recommendation**: Show detailed diff:
     - Field-by-field comparison
     - Checkbox per item to include/exclude
     - Preview final state before committing

---

## Recommendations

### High Priority (Critical for Data Integrity)

1. **Add Dependency Checks**
   - Before deleting service or item, check for:
     - Linked issues
     - Linked tasks
     - Invoice batches
     - Review cycles
   - Show warning dialog with list of dependencies
   - Offer cascade delete or prevent deletion

2. **Implement Conflict Detection**
   - Add `version` or `last_modified` timestamp to services and items
   - On update, check if version matches server
   - If conflict, show merge dialog with both versions
   - Allow user to choose which to keep or merge manually

3. **Add Undo/Redo System**
   - Maintain action history per session
   - Add "Undo" and "Redo" buttons in toolbar
   - Store last 10 actions with rollback SQL
   - Clear history on page reload or after 1 hour

### Medium Priority (Improves User Experience)

4. **Enhanced Template Re-sync Preview**
   ```
   Current: "Reviews: +1 / updated 2 / skipped 15"
   
   Improved:
   ┌─────────────────────────────────────────────────────┐
   │ Review: Week 21 Review                              │
   │ Action: Add new                                     │
   │ Planned Date: 2026-06-15                            │
   │ [✓] Include in sync                                 │
   └─────────────────────────────────────────────────────┘
   
   ┌─────────────────────────────────────────────────────┐
   │ Review: Week 10 Review                              │
   │ Action: Update cycle_no                             │
   │ Current: 10  →  New: 11                             │
   │ [✓] Include in sync                                 │
   └─────────────────────────────────────────────────────┘
   ```

5. **Bulk Operations for Items**
   - Add checkbox column for multi-select
   - Bulk actions toolbar appears when items selected:
     - Change status
     - Change assigned user
     - Update due dates (relative or absolute)
     - Mark as billed
     - Delete selected

6. **Link from Service Edit to Deliverables**
   - In Service Edit View, "Generated Items" section:
     - Add button: "Edit Items in Deliverables Tab →"
     - Opens Deliverables Tab with service pre-selected
     - Preserves context for smooth navigation

7. **Automatic Service Status Calculation**
   ```typescript
   function calculateServiceStatus(service, items, reviews) {
     const itemsCompleted = items.filter(i => i.status === 'completed').length;
     const reviewsCompleted = reviews.filter(r => r.status === 'completed').length;
     const totalWork = items.length + reviews.length;
     const completedWork = itemsCompleted + reviewsCompleted;
     
     if (completedWork === 0) return 'planned';
     if (completedWork === totalWork) return 'completed';
     if (hasOverdue(items, reviews)) return 'overdue';
     return 'in_progress';
   }
   ```
   - Show calculated status with manual override option
   - Display progress percentage

### Low Priority (Nice to Have)

8. **Rich Item Metadata**
   - Add Attachments panel per item
   - Add Comments/Discussion thread
   - Add Activity Log (audit trail of all changes)
   - Add Related Items (link items to each other)

9. **Keyboard Shortcuts**
   - `Ctrl+S` - Save changes
   - `Ctrl+Z` - Undo
   - `Ctrl+Shift+Z` - Redo
   - `Escape` - Cancel inline edit
   - Arrow keys - Navigate between cells

10. **Export/Import Capabilities**
    - Export service with items to Excel
    - Import items from CSV/Excel
    - Export template definition to JSON
    - Share templates between projects

11. **Item Templates (Distinct from Service Templates)**
    - Define reusable item templates
    - Quick-add common items without service template
    - Example: "Standard RFI Response" item template

---

## Conclusion

The Services and Deliverables workflow demonstrates a **well-architected system** with clear separation of concerns and powerful template-driven creation. The core model (Services → Items, Services → Reviews, Projects → Tasks) is correctly implemented and enforced.

**Key Strengths:**
- Template system significantly reduces setup time
- Re-sync capability maintains template connection
- Inline editing provides fast, low-friction UX
- Proper architectural separation prevents data model confusion

**Critical Areas for Improvement:**
- Dependency checking before deletions
- Conflict detection for concurrent edits
- Enhanced template sync preview
- Undo/redo capability

**Overall Assessment**: The workflow is functional and powerful, but needs **data integrity safeguards** and **enhanced preview/confirmation dialogs** to prevent user errors and data loss. Once these are addressed, the system will provide a robust, enterprise-grade service and deliverables management experience.

---

**Next Steps:**
1. Implement dependency checks (highest priority)
2. Add conflict detection for concurrent edits
3. Enhance template re-sync preview with detailed diff
4. Add undo/redo system
5. Improve navigation between Service Edit and Deliverables views

