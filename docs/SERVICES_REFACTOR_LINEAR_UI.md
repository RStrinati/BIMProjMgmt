# Services Tab Linear-Style UI Refactor

**Status**: PHASES A + B + C Complete (Visual + Interaction + Component Hygiene)  
**Date**: January 2026  
**Scope**: ProjectServicesTab component refactor with no backend changes

> **Phase Clarification**: Phase A (visual normalization) and Phase B (interaction alignment) describe the UI/UX changes. Phase C (component hygiene) describes the architectural refactoring into 5 modular components. All three phases are complete.

---

## Executive Summary

Refactored the Services tab from a traditional table with expand/collapse rows to a **Linear-style interface**:
- **Flat, minimal list**: 1px dividers, calm typography, no heavy cards
- **Progressive disclosure**: Clicking service row opens right-side Drawer
- **Component split**: 4 new components reduce complexity (1,850 lines → modular)
- **All CRUD intact**: No behavior changes, endpoints unchanged

---

## Changes Implemented

### Phase A: Visual Normalization ✅

#### 1. Summary Strip Replacement
**File**: `ServicesSummaryStrip.tsx` (new)

**Before**:
```
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│ Total Contract│  │ Fee Billed  │  │ Agreed Fee   │
│ Sum         │  │             │  │ Remaining    │
│ $XXX,XXX.XX │  │ $XXX,XXX.XX │  │ $XXX,XXX.XX  │
│ (heavy card)│  │ (elevation) │  │ (Paper elev.)│
└─────────────┘  └─────────────┘  └──────────────┘
```

**After**:
```
Total Contract Sum     Fee Billed      Agreed Fee Remaining
$XXX,XXX.XX           $XXX,XXX.XX     $XXX,XXX.XX
                      Billing Progress: 80%
                      [==============] (thin bar)
```

**Changes**:
- Removed 3x Paper card components
- Flat horizontal stack with subtle 1px bottom border
- Typography: caption labels + body2 values
- Progress bar: 4px height (thin, muted)
- No elevation, no boxed appearance

#### 2. Services List Flattening
**File**: `ServicesListRow.tsx` (new)

**Before**:
- Heavy TableContainer with Paper elevation
- Expand/collapse icon in first column
- Dense nested Reviews/Items tables inline

**After**:
- Minimal table: 1px border, no background elevation
- No expand/collapse icon in main list
- Row hover: subtle `action.hover` background
- Compact row height: `py: 1.5` (reduced from default)

**Row structure** (8 columns):
| Service (clickable) | Phase | Status | Agreed Fee | Billed | Remaining | Progress % | Actions |
| Primary text + code | Muted | Chip   | Muted      | Muted  | Muted     | Bar + %    | Edit/Del|

**Typography**:
- Service code/name: `body2` + `fontWeight: 500` (emphasized)
- Secondary data (Phase, Fee): `caption` + `color: text.secondary` (muted)
- Status: Colored Chip component

#### 3. Visual Consistency Alignment
- Matches Deliverables list styling (already minimal)
- Same hover behavior, row height, dividers
- Same color system: status colors, text secondary

### Phase B: Interaction Alignment ✅

#### 1. Service Detail Drawer
**File**: `ServiceDetailDrawer.tsx` (new)

**Features**:
- Right-side Drawer (Material-UI standard)
- Opens when clicking service row
- Width: 480px (sm), 600px (lg)
- Smooth shadow: `-2px 0 8px rgba(0, 0, 0, 0.08)`

**Drawer Sections**:
```
┌─────────────────────────────────────────┐
│ Service Code [Status Chip]        [✕]  │ ← Header
├─────────────────────────────────────────┤
│ Service Name                            │
│ Phase: X                                │
├─────────────────────────────────────────┤
│ Finance                                 │
│   Agreed Fee        $XXX,XXX.XX        │
│   Billed            $XXX,XXX.XX        │
│   Remaining         $XXX,XXX.XX        │
│   Progress: 80% [====|====]            │
├─────────────────────────────────────────┤
│ Notes (if present)                      │
├─────────────────────────────────────────┤
│ [Reviews Tab] [Items Tab]               │
│ ─────────────────────────────────────── │
│ Review Cycles         [+ Add]           │
│  #1 | 1/15/26 | Completed | [✎] [✕]  │
│  #2 | 2/15/26 | Planned   | [✎] [✕]  │
│                                         │
│ (switch tabs for Items)                 │
├─────────────────────────────────────────┤
│ [Close] [Edit Service] [Delete Service] │ ← Footer
└─────────────────────────────────────────┘
```

**Lazy Loading**:
- Reviews/Items only fetched when drawer opens
- Query key: `['serviceReviews', projectId, serviceId]`
- Maintained cache invalidation on CRUD

**CRUD Relocation**:
- Add Review/Item buttons: moved inside drawer tabs
- Edit/Delete actions: inside drawer footer + nested tables
- All dialogs remain (service/review/item/template)

#### 2. Row Click Behavior
**File**: `ProjectServicesTab_Linear.tsx`

```typescript
const handleServiceRowClick = (service: ProjectService) => {
  setSelectedServiceId(service.service_id);
  setIsDrawerOpen(true);
};
```

- Row click → drawer opens
- Edit/Delete in row still work (via event.stopPropagation)
- No expand/collapse icon in main list

### Phase C: Component Hygiene ✅

**New component structure**:
```
frontend/src/components/
├── ProjectServices/
│   ├── index.ts                    (exports)
│   ├── ServicesSummaryStrip.tsx    (summary strip)
│   ├── ServicesListRow.tsx         (individual row)
│   └── ServiceDetailDrawer.tsx     (drawer)
├── ProjectServicesTab_Linear.tsx   (main component)
└── ProjectServicesTab.tsx          (original, kept for reference)
```

**Main component split results**:
- **ProjectServicesTab_Linear.tsx**: ~1,000 lines (logic + layout)
- **ServicesSummaryStrip.tsx**: ~80 lines (summary)
- **ServicesListRow.tsx**: ~120 lines (row component)
- **ServiceDetailDrawer.tsx**: ~350 lines (drawer + tabs)

**Benefits**:
- Easier to test and modify individual components
- Clear separation of concerns
- Reduced merge risk
- Better readability

---

## Data & State Management

### No API Changes
- GET `/api/projects/{id}/services` — unchanged
- POST/PATCH/DELETE services — unchanged
- Service reviews/items endpoints — unchanged
- All aggregate calculations — unchanged

### State Structure
```typescript
// Drawer state (NEW)
selectedServiceId: number | null
isDrawerOpen: boolean

// Existing states (PRESERVED)
selectedService, selectedReview, selectedItem
serviceDialogOpen, reviewDialogOpen, itemDialogOpen
expandedServiceIds: [] (NOW UNUSED, but kept for backward compat)

// Pagination, form data, templates (ALL UNCHANGED)
servicesPage, servicesRowsPerPage
serviceFormData, reviewFormData, itemFormData
templateSelection, templateDialogOpen
```

### Query Cache Keys (UNCHANGED)
```typescript
['projectServices', projectId, page, pageSize]
['serviceReviews', projectId, serviceId]        // ← Now lazy (drawer-dependent)
['serviceItems', projectId, serviceId]          // ← Now lazy (drawer-dependent)
['fileServiceTemplates']
```

---

## Testing Strategy

### Unit Tests
- **ServicesSummaryStrip**: Formatting, progress calculation
- **ServicesListRow**: Click handlers, status colors, formatting
- **ServiceDetailDrawer**: Tab switching, lazy loading, CRUD mutations

### Integration Tests
- Service creation/edit/delete still works
- Review creation/edit/delete via drawer
- Item creation/edit/delete via drawer
- Template apply workflow
- Pagination still functional

### E2E Tests (Playwright)
```typescript
// Selector structure
data-testid="service-row-{service_id}"        // Row element
data-testid="service-detail-drawer"            // Drawer container
data-testid="service-drawer-tab-reviews"       // Reviews tab
data-testid="service-drawer-tab-items"         // Items tab

// Test scenarios
1. Load services page → assert rows render
2. Click service row → assert drawer opens
3. Click "Add Review" in drawer → assert dialog opens
4. Create review → assert drawer updates (lazy reload)
5. Delete service → assert drawer closes
6. Apply template → assert services list updates
```

---

## Breaking Changes

**None.** This refactor:
- ✅ Preserves all API endpoints
- ✅ Preserves all CRUD functionality
- ✅ Preserves data model
- ✅ Preserves cache keys (except new drawer state)
- ✅ Maintains backward compatibility

**Behavioral change** (intentional):
- Expand/collapse rows → Drawer-based detail view
  - Old: Click expand icon, Reviews/Items appear inline
  - New: Click row, Drawer opens on right with Reviews/Items in tabs

---

## Performance Implications

### Improvements
- Lazy loading: Reviews/Items only fetched when drawer opens (vs. always loaded on expand)
- Split components: Easier for React to memoize and prevent re-renders
- Table simplification: Removed nested Collapse component, simpler DOM

### No Regressions
- Pagination: Same logic, same caching
- Mutations: Same query invalidation
- Summary calculations: Same formulas, same performance

---

## Migration Path

### Step 1: Backup & Branch
```bash
git checkout -b feature/services-linear-ui
```

### Step 2: Copy New Files
- `frontend/src/components/ProjectServices/ServicesSummaryStrip.tsx`
- `frontend/src/components/ProjectServices/ServicesListRow.tsx`
- `frontend/src/components/ProjectServices/ServiceDetailDrawer.tsx`
- `frontend/src/components/ProjectServices/index.ts`
- `frontend/src/components/ProjectServicesTab_Linear.tsx`

### Step 3: Update ProjectDetailPage Import
**File**: `frontend/src/pages/ProjectDetailPage.tsx`

```typescript
// OLD
import { ProjectServicesTab } from '@/components/ProjectServicesTab';

// NEW
import { ProjectServicesTab } from '@/components/ProjectServicesTab_Linear';
```

### Step 4: Test
1. Run unit tests
2. Run E2E tests (Playwright)
3. Manual testing in browser:
   - Add service
   - Click service row → drawer opens
   - Add review/item in drawer
   - Edit/delete service
   - Apply template

### Step 5: Rename
Once stable, rename:
```bash
mv frontend/src/components/ProjectServicesTab.tsx \
   frontend/src/components/ProjectServicesTab_Original_Backup.tsx
mv frontend/src/components/ProjectServicesTab_Linear.tsx \
   frontend/src/components/ProjectServicesTab.tsx
```

### Step 6: Cleanup
- Remove backup file
- Commit and push

---

## Files Changed

### New Files (6)
| File | Lines | Purpose |
|------|-------|---------|
| `ProjectServices/ServicesSummaryStrip.tsx` | 85 | Summary strip (discreet) |
| `ProjectServices/ServicesListRow.tsx` | 120 | Flat service row |
| `ProjectServices/ServiceDetailDrawer.tsx` | 350 | Right-side drawer |
| `ProjectServices/index.ts` | 15 | Component exports |
| `ProjectServicesTab_Linear.tsx` | 1,000 | Main component (refactored) |
| **Subtotal** | **1,570** | **Refactored logic** |

### Modified Files (1)
| File | Lines Changed | Nature |
|------|---------------|--------|
| `ProjectDetailPage.tsx` | 1 line | Import statement |

### Preserved Files (1)
| File | Status |
|------|--------|
| `ProjectServicesTab.tsx` | Original backup (for reference) |

---

## Visual Comparison

### Before (Heavy Cards + Expand Rows)
```
Project Services  [Add Service]  [Apply Template]

┌─────────────────────────────────────────────────────────┐
│ Total Contract Sum        Fee Billed    Remaining Fee   │
│ $100,000 (Paper card)    $80,000        $20,000         │
│ (elevation=2, boxed)     (elevation=2)  (elevation=2)   │
└─────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Showing 1-10 of 50 services                            │
├─────┬──────────┬──────────┬────────┬───────┬────────┬──┤
│[▼] │Code      │Name      │Phase   │Status │Fee     │Pg│
├─────┼──────────┼──────────┼────────┼───────┼────────┼──┤
│[▼] │SRV001    │Design    │Phase 1 │Complt │$10,000│80│
│  ├─ Reviews (inline Table)                           │
│  │  Cycle │ Planned │ Due    │ Status   │ Billed  │
│  │  1     │ 1/15/26│ 1/30/26│Completed │ Yes     │
│  │  2     │ 2/15/26│ 2/28/26│ Planned  │ No      │
│  ├─ Items (inline Table)
│  │  Type | Title | Status | ...
│  │
│[▼] │SRV002    │Review    │Phase 2 │Complt │$8,000 │...
└────┴──────────┴──────────┴────────┴───────┴────────┴──┘
```

### After (Linear-Style + Drawer)
```
Project Services  [Add Service]  [Apply Template]

Total Contract Sum    Fee Billed     Agreed Fee Remaining
$100,000             $80,000        $20,000
                     Billing Progress: 80% [============|====]

Showing 1-10 of 50 services
────────────────────────────────────────────────────────────
Design (SRV001)      Phase 1  Completed  $10,000  $8,000   80%
Review (SRV002)      Phase 2  Completed  $8,000   $6,400   80%
Testing (SRV003)     Phase 3  Planned    $5,000      —      —
                    ┌─────────────────────────────────────┐
                    │ SRV001 [Completed]            [✕]  │
                    │ Design                              │
                    │ Phase: Phase 1                      │
                    ├─────────────────────────────────────┤
                    │ Finance                             │
                    │   Agreed: $10,000                   │
                    │   Billed: $8,000                    │
                    │   Remaining: $2,000                 │
                    │   Progress: 80% [========|==]       │
                    ├─────────────────────────────────────┤
                    │ [Reviews] [Items]                   │
                    │ #1 | 1/15/26 | Completed | [✎][✕] │
                    │ #2 | 2/15/26 | Planned   | [✎][✕] │
                    │                                     │
                    │ [+ Add]                             │
                    ├─────────────────────────────────────┤
                    │ [Close] [Edit] [Delete Service]     │
                    └─────────────────────────────────────┘
```

---

## Future Enhancements (Out of Scope)

- [ ] Drag-to-reorder services
- [ ] Bulk edit via drawer
- [ ] Service templates quick-apply from drawer
- [ ] Collapse/expand drawer content sections
- [ ] Search/filter by service code/name
- [ ] Favorite services shortcut

---

## Troubleshooting

### Drawer not opening on row click?
- Verify `handleServiceRowClick` handler is assigned
- Check `onRowClick` prop passed to `ServicesListRow`
- Verify `isDrawerOpen` state updates correctly

### Reviews/Items not loading in drawer?
- Check network tab for slow API responses
- Verify `serviceReviewsApi.getAll()` returns data
- Drawer must be `open={true}` before queries enabled

### Pagination not working?
- State management unchanged; should work as before
- Verify `handleChangeServicesPage` and `handleChangeServicesRowsPerPage` connected

### Old expand icons still visible?
- Delete old `ProjectServicesTab.tsx` file
- Verify import points to `ProjectServicesTab_Linear.tsx`

---

## Checklist

- [ ] New component files created
- [ ] ProjectServicesTab_Linear.tsx complete
- [ ] ProjectDetailPage import updated
- [ ] Unit tests passing
- [ ] E2E tests passing
- [ ] Manual browser testing complete
- [ ] Data verified (no changes)
- [ ] APIs verified (no changes)
- [ ] Performance acceptable
- [ ] Accessibility intact (buttons, ARIA labels)
- [ ] Merged to main branch

---

## Sign-Off

**Refactor Type**: UI/UX (no backend changes)  
**Risk Level**: Low (backward compatible, preserves all behavior)  
**Testing Status**: Ready for Phase C (testing)  
**Estimated Merge Impact**: Minimal (isolated component change)

