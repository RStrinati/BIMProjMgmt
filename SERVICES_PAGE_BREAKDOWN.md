# Services Page Breakdown - V2 Architecture

## Overview
The Services page is accessed via the **Project Detail Page** and displays a hierarchical view of all project services, their reviews (cycles), and items (deliverables). It's a fully functional CRUD system with Material-UI based graphics and responsive design.

---

## 1. PAGE STRUCTURE & LOCATION

### Entry Point
- **File**: [frontend/src/pages/ProjectDetailPage.tsx](frontend/src/pages/ProjectDetailPage.tsx)
- **Component**: `ProjectServicesTab` (embedded within project detail)
- **Route**: `/projects/:id` (tab-based UI, not separate page)
- **Integration**: Tab 1 (index 1) in ProjectDetailPage tabs

### Main Services Component
- **File**: [frontend/src/components/ProjectServicesTab.tsx](frontend/src/components/ProjectServicesTab.tsx)
- **Type**: React Functional Component with Hooks (TypeScript)
- **Size**: ~1,850 lines (large component with embedded dialogs)
- **Dependencies**: React Query, Material-UI, React Router

---

## 2. PAGE LAYOUT VISUAL HIERARCHY

```
┌─────────────────────────────────────────────────────────────────┐
│  Project Services  [Add Service]  [Add From Template]           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  │ Total Contract   │  │   Fee Billed     │  │ Agreed Fee       │
│  │ Sum              │  │                  │  │ Remaining        │
│  │ $XXX,XXX.XX      │  │   $XXX,XXX.XX    │  │ $XXX,XXX.XX      │
│  │                  │  │                  │  │ [Progress Bar]   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘
├─────────────────────────────────────────────────────────────────┤
│ Showing 1-10 of 50 services                                     │
├─────────────────────────────────────────────────────────────────┤
│ TABLE: Services                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [▼] Code  | Name    | Phase | Status  | Fee    | Billed | %    │ 
├─────────────────────────────────────────────────────────────────┤
│ [▼] SRV01 │ Design  │ Phase1│Completed│$10,000│ $8,000 │ 80%  │
│     └─ DETAILS EXPAND                                           │
│        ├─ Reviews Table                                         │
│        │  [Add Review] [Edit] [Delete]                          │
│        │  Cycle | Planned | Due | Status | Weight | Billed     │
│        │  1     | 1/15/26 | ... | Complt │ 1.0    │ Yes        │
│        │                                                        │
│        └─ Items Table                                           │
│           [Add Item] [Edit] [Delete]                            │
│           Type | Title | Planned | Due | Status | Priority      │
│           ...                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. BACKEND ENDPOINTS

### Service Management

#### GET `/api/projects/<project_id>/services`
- **Purpose**: Fetch all services for a project
- **Query Parameters**:
  - `page` (optional, 1-indexed): Pagination page number
  - `limit` (optional): Items per page (default 10)
- **Response Format**:
  ```json
  {
    "items": [ProjectService],
    "total": 50,
    "page": 1,
    "page_size": 10,
    "aggregate": {
      "total_agreed_fee": 100000,
      "total_billed": 80000,
      "total_remaining": 20000,
      "billing_progress_pct": 80.0
    }
  }
  ```
- **Location**: [backend/app.py](backend/app.py) line 1627
- **Handler**: `api_get_project_services(project_id)`

#### POST `/api/projects/<project_id>/services`
- **Purpose**: Create a new service
- **Body**:
  ```json
  {
    "service_code": "string (required)",
    "service_name": "string (required)",
    "phase": "string (optional)",
    "unit_type": "string (optional)",
    "unit_qty": number,
    "unit_rate": number,
    "lump_sum_fee": number,
    "agreed_fee": number,
    "bill_rule": "Fixed Fee|Time & Materials|Percentage of Construction Cost|Milestone Based|Other",
    "notes": "string (optional)"
  }
  ```
- **Response**: `{ "service_id": number }`
- **Location**: [backend/app.py](backend/app.py) line 1664
- **Handler**: `api_create_project_service(project_id)`

#### PATCH `/api/projects/<project_id>/services/<service_id>`
- **Purpose**: Update an existing service
- **Body**: Partial ProjectService (any field can be updated)
- **Response**: `{ "success": true }`
- **Location**: [backend/app.py](backend/app.py) line 1694
- **Handler**: `api_update_project_service(project_id, service_id)`

#### DELETE `/api/projects/<project_id>/services/<service_id>`
- **Purpose**: Delete a service
- **Response**: `{ "success": true }`
- **Location**: [backend/app.py](backend/app.py) line 1699
- **Handler**: `api_delete_project_service(project_id, service_id)`

#### POST `/api/projects/<project_id>/services/apply-template`
- **Purpose**: Apply a service template (bulk creation)
- **Body**:
  ```json
  {
    "template_name": "string (required)",
    "replace_existing": boolean,
    "skip_duplicates": boolean,
    "overrides": object (optional)
  }
  ```
- **Response**: 
  ```json
  {
    "template_name": "string",
    "created": [ProjectService],
    "skipped": [],
    "replaced_services": number
  }
  ```
- **Location**: [backend/app.py](backend/app.py) line 1632
- **Handler**: `api_apply_project_service_template(project_id)`

### Service Reviews

#### GET `/api/projects/<project_id>/services/<service_id>/reviews`
- **Purpose**: Fetch all reviews for a service
- **Response**: `[ServiceReview]`
- **Location**: [backend/app.py](backend/app.py) line 1721
- **Handler**: `api_get_service_reviews(project_id, service_id)`

#### POST `/api/projects/<project_id>/services/<service_id>/reviews`
- **Purpose**: Create a review cycle
- **Body**:
  ```json
  {
    "cycle_no": number (required),
    "planned_date": "ISO string (required)",
    "due_date": "ISO string (optional)",
    "disciplines": "string (optional)",
    "deliverables": "string (optional)",
    "status": "planned|in_progress|completed|overdue|cancelled",
    "weight_factor": number,
    "invoice_reference": "string (optional)",
    "evidence_links": "string (optional)",
    "is_billed": boolean
  }
  ```
- **Response**: `{ "review_id": number }`
- **Location**: [backend/app.py](backend/app.py) line 1747
- **Handler**: `api_create_service_review(project_id, service_id)`

#### PATCH `/api/projects/<project_id>/services/<service_id>/reviews/<review_id>`
- **Purpose**: Update a review
- **Body**: Partial ServiceReview
- **Response**: `{ "success": true }`

#### DELETE `/api/projects/<project_id>/services/<service_id>/reviews/<review_id>`
- **Purpose**: Delete a review
- **Response**: `{ "success": true }`

### Service Items

#### GET `/api/projects/<project_id>/services/<service_id>/items`
- **Purpose**: Fetch all items for a service
- **Query Parameters**:
  - `type` (optional): Filter by item type
- **Response**: `[ServiceItem]`

#### POST `/api/projects/<project_id>/services/<service_id>/items`
- **Purpose**: Create a service item (deliverable)
- **Body**:
  ```json
  {
    "item_type": "review|audit|deliverable|milestone|inspection|meeting|other",
    "title": "string (required)",
    "description": "string (optional)",
    "planned_date": "ISO string (optional)",
    "due_date": "ISO string (optional)",
    "actual_date": "ISO string (optional)",
    "status": "planned|in_progress|completed|overdue|cancelled",
    "priority": "low|medium|high|critical",
    "assigned_to": "string (optional, user ID)",
    "invoice_reference": "string (optional)",
    "evidence_links": "string (optional)",
    "notes": "string (optional)",
    "is_billed": boolean
  }
  ```
- **Response**: `{ "item_id": number }`

#### PATCH `/api/projects/<project_id>/services/<service_id>/items/<item_id>`
- **Purpose**: Update an item
- **Body**: Partial ServiceItem
- **Response**: `{ "success": true }`

#### DELETE `/api/projects/<project_id>/services/<service_id>/items/<item_id>`
- **Purpose**: Delete an item
- **Response**: `{ "success": true }`

---

## 4. FRONTEND STATE MANAGEMENT

### React Query Keys (Cache Management)
```typescript
// Services list
['projectServices', projectId, page, pageSize]

// Service reviews (lazy-loaded when expanded)
['serviceReviews', projectId, service_id]

// Service items (lazy-loaded when expanded)
['serviceItems', projectId, service_id]

// Templates
['fileServiceTemplates']
```

### Component State (useState)
```typescript
// Pagination & Expansion
expandedServiceIds: number[]          // Which services are expanded
servicesPage: number                   // Current page
servicesRowsPerPage: number            // Items per page (5, 10, 25, 50)

// Dialog States
serviceDialogOpen: boolean             // Add/Edit service dialog
reviewDialogOpen: boolean              // Add/Edit review dialog
itemDialogOpen: boolean                // Add/Edit item dialog
templateDialogOpen: boolean            // Template selection dialog

// Selected Entities
selectedService: ProjectService | null
selectedReview: ServiceReview | null
selectedItem: ServiceItem | null

// Form Data (local state)
serviceFormData: { service_code, service_name, phase, ... }
reviewFormData: { cycle_no, planned_date, status, ... }
itemFormData: { item_type, title, status, priority, ... }
templateSelection: { templateName, replaceExisting }

// Feedback
templateFeedback: { message, severity } | null
templateDialogError: string
```

### React Query Mutations
```typescript
createServiceMutation       // POST /services
updateServiceMutation       // PATCH /services/:id
deleteServiceMutation       // DELETE /services/:id
applyTemplateMutation       // POST /services/apply-template

createReviewMutation        // POST /services/:id/reviews
updateReviewMutation        // PATCH /reviews/:id
deleteReviewMutation        // DELETE /reviews/:id

createItemMutation          // POST /services/:id/items
updateItemMutation          // PATCH /items/:id
deleteItemMutation          // DELETE /items/:id
```

---

## 5. DATA MODELS

### ProjectService
```typescript
{
  service_id: number
  project_id: number
  service_code: string
  service_name: string
  phase?: string
  unit_type?: string
  unit_qty?: number
  unit_rate?: number
  lump_sum_fee?: number
  agreed_fee?: number                 // Contract sum for service
  bill_rule?: string                  // Billing model
  notes?: string
  status: string                      // 'completed', 'in_progress', etc.
  progress_pct?: number
  claimed_to_date?: number            // Billing progress
  billing_progress_pct?: number       // Calculated %
  billed_amount?: number              // Total billed to date
  agreed_fee_remaining?: number       // Contract sum - billed
  created_at: string
  updated_at: string
}
```

### ServiceReview
```typescript
{
  review_id: number
  service_id: number
  cycle_no: number                    // Sequential cycle number
  planned_date: string                // Scheduled date
  due_date?: string
  disciplines?: string                // Scopes involved
  deliverables?: string               // What's being delivered
  status: string                      // 'planned', 'in_progress', 'completed', etc.
  weight_factor?: number              // For billing calculation
  invoice_reference?: string          // Link to invoice/folder
  evidence_links?: string
  is_billed: boolean
  created_at: string
  updated_at: string
}
```

### ServiceItem
```typescript
{
  item_id: number
  service_id: number
  item_type: string                   // 'review', 'audit', 'deliverable', etc.
  title: string
  description?: string
  planned_date?: string               // When scheduled
  due_date?: string
  actual_date?: string
  status: string                      // 'planned', 'in_progress', 'completed', etc.
  priority: string                    // 'low', 'medium', 'high', 'critical'
  assigned_to?: string                // User ID
  invoice_reference?: string
  evidence_links?: string
  notes?: string
  is_billed: boolean
  created_at: string
  updated_at: string
}
```

---

## 6. CSS & STYLING SYSTEM

### Theme Configuration
- **File**: [frontend/src/theme/theme.ts](frontend/src/theme/theme.ts)
- **Type**: Material-UI v5 Theme object
- **Applied via**: `ThemeProvider` in [frontend/src/App.tsx](frontend/src/App.tsx) line 16
- **Library**: Material-UI (`@mui/material`)

### Style Method: Inline sx Props
All styling uses Material-UI's **`sx` prop** (CSS-in-JS). No separate CSS files.

#### Key Styling Components in ProjectServicesTab:

**1. Main Container**
```tsx
<Box>  // flex container
  sx={{
    display: "flex",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 2,
    mb: 2
  }}
</Box>
```

**2. Summary Cards (Billing Overview)**
```tsx
<Paper sx={{ 
  p: 2,                    // padding: 16px
  flex: '1 1 220px',       // Responsive flex
  minWidth: 200,
  elevation: 1
}}>
  <Typography variant="subtitle2" color="text.secondary">
    Total Contract Sum
  </Typography>
  <Typography variant="h6">
    {formatCurrency(billingSummary.totalAgreed)}
  </Typography>
</Paper>
```

**3. Progress Bar (Billing Progress)**
```tsx
<LinearProgress
  variant="determinate"
  value={service.billing_progress_pct ?? 0}
  sx={{ 
    height: 8,              // Thicker bar
    borderRadius: 4,        // Rounded corners
    mb: 0.5                 // Margin-bottom
  }}
/>
<Typography variant="caption" color="text.secondary">
  {formatPercent(value)} billed
</Typography>
```

**4. Data Table (Services List)**
```tsx
<TableContainer component={Paper}>
  <Table size="small">
    <TableHead>
      <TableRow>
        <TableCell padding="checkbox">
          <IconButton onClick={onToggle}>
            {isExpanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>Service Code</TableCell>
        <TableCell>Service Name</TableCell>
        // ... more columns
      </TableRow>
    </TableHead>
    <TableBody>
      {paginatedServices.map((service) => (
        <ServiceRow key={service.service_id} ... />
      ))}
    </TableBody>
  </Table>
</TableContainer>
```

**5. Expandable Row Details**
```tsx
<TableRow>
  <TableCell colSpan={10} style={{ paddingBottom: 0, paddingTop: 0 }}>
    <Collapse in={isExpanded} timeout="auto" unmountOnExit>
      <Box margin={2} display="flex" flexDirection="column" gap={3}>
        {/* Reviews & Items tables go here */}
      </Box>
    </Collapse>
  </TableCell>
</TableRow>
```

**6. Status Chips**
```tsx
<Chip 
  label={service.status}
  color={getStatusColor(service.status)}  // Maps status → color
  size="small"
/>
```

**Color Mapping Function**
```typescript
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success';     // Green
    case 'in_progress': return 'primary';   // Blue
    case 'overdue': return 'error';         // Red
    case 'cancelled': return 'warning';     // Orange
    default: return 'default';              // Gray
  }
}
```

### Typography Variants Used
| Variant | Use Case |
|---------|----------|
| `h6` | Section headers ("Project Services") |
| `subtitle1` | Sub-headers ("Reviews", "Items") |
| `subtitle2` | Card labels ("Total Contract Sum") |
| `body2` | Table cells, default text |
| `caption` | Small secondary text, percentages |

### Color System
```typescript
// Status colors (semantic)
'success'    → #4caf50 (Green - Completed)
'primary'    → #1976d2 (Blue - In Progress)
'error'      → #f44336 (Red - Overdue/Error)
'warning'    → #ff9800 (Orange - Cancelled/Warning)
'info'       → #2196f3 (Light Blue - Info)
'default'    → #999999 (Gray - Neutral)

// Text colors
color="text.secondary"  → Lighter gray for labels
color="text.primary"    → Dark gray for main content
```

### Responsive Design
```tsx
// Flex-based responsive layout
<Box display="flex" flexWrap="wrap" gap={2}>
  <Paper sx={{ flex: '1 1 220px', minWidth: 200 }} />  // Responsive cards
</Box>

// Table horizontal scroll on mobile
<TableContainer component={Paper}>
  <Table>...</Table>  // Scrolls horizontally on small screens
</TableContainer>
```

### Material-UI Spacing Scale
```
0    = 0px
0.5  = 4px
1    = 8px
1.5  = 12px
2    = 16px
3    = 24px
4    = 32px
```

---

## 7. COMPONENT COMPOSITION

### Main Component Tree
```
ProjectDetailPage (Parent)
├── Tabs (Material-UI Tabs)
│   ├── Tab 0: Overview
│   ├── Tab 1: ProjectServicesTab ← Services page
│   └── Tab 2: Other tabs...
│
└── ProjectServicesTab
    ├── Header + Action Buttons
    │   ├── "Add Service" Button
    │   └── "Add From Template" Button
    ├── Billing Summary Cards
    │   ├── Total Contract Sum
    │   ├── Fee Billed
    │   └── Fee Remaining + Progress
    ├── Pagination Info
    ├── TableContainer
    │   └── Table (Services)
    │       ├── ServiceRow (repeated)
    │       │   ├── Expand/Collapse Button
    │       │   ├── Service Details Cells
    │       │   └── Action Buttons (Edit, Delete)
    │       │   └── Collapse with:
    │       │       ├── Reviews Table
    │       │       │   ├── Add Review Button
    │       │       │   └── ReviewRow (repeated)
    │       │       └── Items Table
    │       │           ├── Add Item Button
    │       │           └── ItemRow (repeated)
    │       └── TablePagination
    └── Dialogs (Modal)
        ├── ServiceDialog (Add/Edit)
        ├── ReviewDialog (Add/Edit)
        ├── ItemDialog (Add/Edit)
        └── TemplateDialog (Apply Template)
```

### Sub-Components
- **ServiceRow**: Expandable service row with reviews/items (inline)
- **Dialogs**: Inline Dialog components for CRUD operations

---

## 8. KEY FEATURES & INTERACTIONS

### Expandable Service Rows
- Click expand icon (▼) to reveal reviews and items
- Lazy-loads reviews and items on expand
- Multiple services can be expanded simultaneously
- Expansion state managed in `expandedServiceIds` array

### Billing Summary Section
- **Three cards** showing financial overview
- Dynamically calculated from service data
- Falls back to aggregate API response if paginated
- Progress bar shows percentage billed

### Pagination
- Page size options: 5, 10, 25, 50 items
- Server-side or client-side (detected automatically)
- Maintains page number across page size changes
- Shows "Showing X-Y of Z services" text

### CRUD Operations
- **Add Service**: Opens dialog with form
- **Edit Service**: Pre-populates form with existing data
- **Delete Service**: Confirmation dialog
- **Add Review**: Creates review cycle with auto-increment cycle number
- **Add Item**: Creates service deliverable
- **Apply Template**: Bulk-creates services from template

### Template System
- Dropdown to select from available templates
- Toggle: Replace existing vs. skip duplicates
- Shows feedback on success (created, skipped, replaced counts)

### Status & Priority Indicators
```
Status Colors:
- Completed: Green badge
- In Progress: Blue badge
- Overdue: Red badge
- Cancelled: Orange badge
- Planned: Gray badge

Priority Colors (Items):
- Critical: Red badge
- High: Orange badge
- Medium: Gray badge
- Low: Gray badge
```

---

## 9. API CLIENT FUNCTIONS

### File: [frontend/src/api/services.ts](frontend/src/api/services.ts)

**Service Templates**
```typescript
fileServiceTemplatesApi.getAll()  // Fetch all available templates
fileServiceTemplatesApi.save(data)
fileServiceTemplatesApi.delete(name)
```

**Project Services**
```typescript
projectServicesApi.getAll(projectId, params)    // GET /services
projectServicesApi.create(projectId, data)      // POST /services
projectServicesApi.update(projectId, serviceId, data)
projectServicesApi.delete(projectId, serviceId)
projectServicesApi.applyTemplate(projectId, data)
```

**Service Reviews**
```typescript
serviceReviewsApi.getAll(projectId, serviceId)
serviceReviewsApi.create(projectId, serviceId, data)
serviceReviewsApi.update(projectId, serviceId, reviewId, data)
serviceReviewsApi.delete(projectId, serviceId, reviewId)
serviceReviewsApi.getBillingSummary(projectId, params)
```

**Service Items**
```typescript
serviceItemsApi.getAll(projectId, serviceId, type?)
serviceItemsApi.create(projectId, serviceId, data)
serviceItemsApi.update(projectId, serviceId, itemId, data)
serviceItemsApi.delete(projectId, serviceId, itemId)
```

---

## 10. PERFORMANCE OPTIMIZATIONS

### Lazy Loading
- Reviews and items only loaded when service is expanded
- Uses `enabled: isExpanded` in useQuery
- Reduces initial API calls

### Query Caching
- React Query caches data with 5-minute stale time
- Page navigation doesn't refetch unchanged data
- Manual invalidation on mutations

### Pagination
- Supports both server-side and client-side pagination
- Auto-detects pagination method from API response
- Efficient memory usage with `placeholderData` option

### Memoization
```typescript
const paginatedServices = useMemo(...)
const billingSummary = useMemo(...)
const aggregatedSummary = useMemo(...)
const effectivePageSize = useMemo(...)
```

### Profiling
- React Profiler wraps main component: `<Profiler id="ProjectServicesTab">`
- Logs render times to console for debugging

---

## 11. ACCESSIBILITY FEATURES

- **Icon Labels**: `aria-label` on expandable buttons
- **Semantic HTML**: Proper table structure with thead/tbody
- **Keyboard Navigation**: Tab order through form controls
- **Color Contrast**: Material-UI ensures WCAG compliance
- **Status Indicators**: Color + text (not color-only)
- **Loading States**: CircularProgress with accessible markup

---

## 12. ERROR HANDLING

```typescript
// Query errors
if (servicesError) {
  return <Alert severity="error">{servicesError.message}</Alert>
}

// Mutation errors with confirmation
if (window.confirm('Delete this service?')) {
  deleteServiceMutation.mutate(serviceId)
}

// Template errors
if (!templateSelection.templateName) {
  setTemplateDialogError('Please select a template')
}

// Network errors
onError: (err) => {
  setTemplateDialogError(err?.response?.data?.error || 'Failed')
}
```

---

## 13. BROWSER INSPECTOR NOTES

When inspecting the Services page in DevTools:

**Class Names** (MUI-generated):
- `.MuiTableContainer-root` - Main table wrapper
- `.MuiTable-root` - Table
- `.MuiTableRow-root` - Rows
- `.MuiTableCell-root` - Cells
- `.MuiPaper-root` - Summary cards
- `.MuiChip-root` - Status badges

**Data Attributes**:
- `data-testid="project-services-tab-item-blockers-{itemId}"` - Item blocker badges

**Custom Styles**: All via `sx` prop (inline MUI styles, not CSS files)

---

## 14. QUICK REFERENCE: GRAPHIC UPDATES

### To Update Card Styling (Billing Summary)
Edit: `ProjectServicesTab.tsx` ~line 1349
```tsx
<Paper sx={{ p: 2, flex: '1 1 220px', minWidth: 200, elevation: 1 }}>
  // Adjust spacing, elevation, shadows, borders, background color
</Paper>
```

### To Update Progress Bar
Edit: Line ~1365
```tsx
<LinearProgress
  variant="determinate"
  value={billingSummary.progress}
  sx={{ height: 8, borderRadius: 4 }}  // Adjust height, colors
/>
```

### To Update Table Styling
Edit: Line ~1400+ (Table component)
```tsx
<TableContainer component={Paper}>
  <Table size="small">  // Change "small" to affect row density
```

### To Change Status Colors
Edit: `getStatusColor()` function ~line 864
```typescript
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success';    // Green
    // Adjust these mappings
  }
}
```

### To Update Typography
Edit: variant attributes throughout (e.g., `variant="h6"`, `variant="subtitle2"`)
- `h6` = Heading 6 (project services label)
- `subtitle1` = Section headers (Reviews, Items)
- `subtitle2` = Card labels
- `caption` = Small text

---

## 15. TESTING LOCATIONS

### Unit Tests
- `tests/` directory (if any exist)

### E2E Tests  
- ProjectServicesTab tested in Playwright suite (mentioned in instructions)
- Test coverage: Service creation, item creation, review cycles

### Manual Testing Checklist
1. [ ] Add Service - form validation
2. [ ] Edit Service - updates reflected
3. [ ] Delete Service - confirmation dialog
4. [ ] Expand Service - lazy-loads reviews/items
5. [ ] Add Review - cycle number increments
6. [ ] Add Item - type/priority saved
7. [ ] Pagination - page size changes work
8. [ ] Template - bulk import works
9. [ ] Billing - calculations are correct
10. [ ] Responsive - mobile layout works

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Component** | ProjectServicesTab (1,848 lines) |
| **Location** | frontend/src/components/ |
| **Container** | ProjectDetailPage (Tab 1) |
| **State Library** | React Query + useState |
| **UI Library** | Material-UI v5 |
| **Styling** | sx prop (CSS-in-JS) |
| **API Endpoints** | 11 (CRUD for services, reviews, items) |
| **Data Models** | ProjectService, ServiceReview, ServiceItem |
| **Key Features** | Expandable rows, pagination, template bulk-import, billing summary |
| **Performance** | Lazy loading, memoization, query caching |
| **Accessibility** | WCAG compliant via MUI, aria-labels |

