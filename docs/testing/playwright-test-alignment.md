# Playwright Test Alignment Guide

This document provides guidance on aligning your Playwright tests with the current frontend design based on the Golden Set UI Standard.

## Current State Analysis

### Test Files Inventory
Your test suite includes **34 test files** in `frontend/tests/e2e/`, organized by feature:

**Projects & Panels:**
- `projects-home-v2.spec.ts` - Projects list view (home page)
- `projects-panel-*.spec.ts` - Panel-based project workflows
- `projects-gate.spec.ts` - Feature flag gating
- `projects-empty-reset.spec.ts` - Empty state handling

**Workspace Tabs (ProjectWorkspacePageV2):**
- `project-workspace-v2-*.spec.ts` - Core workspace functionality
  - `smoke.spec.ts` - Basic navigation and renders
  - `services.spec.ts` - Service management
  - `services-drawer.spec.ts` - Service drawer interactions
  - `reviews-projectwide.spec.ts` - Review cycles
  - `deliverables-*.spec.ts` - Item management
  - `invoice-*.spec.ts` - Billing workflows
  - `tasks.spec.ts` - Task management
  - `data-integrity.spec.ts` - Data validation

**Feature Workflows:**
- `deliverables-workflow.spec.ts` - End-to-end item creation/editing
- `anchor-linking.spec.ts` - Issue anchor linking
- `bids-*.spec.ts` - Bid management
- `quality-register.spec.ts` - Quality tracking

### Current Selector Patterns

Your tests use these primary selector strategies:

```typescript
// 1. Test IDs (most common)
page.getByTestId('project-workspace-v2-reviews')
page.getByTestId('deliverable-row-${reviewId}')
page.getByTestId('workspace-service-row-101')

// 2. Accessible Role selectors
page.getByRole('tab', { name: 'Deliverables' })
page.getByRole('button', { name: 'Save' })
page.getByRole('menuitem', { name: 'From template' })

// 3. Text selectors (less preferred but used for content matching)
page.getByText('Weekly report')
await expect(page.getByText('Custom Title')).toBeVisible();
```

## Alignment with Golden Set Standard

### P0 Golden Primitives

The tests should validate these key components:

| Component | Current Usage | Recommended Test Pattern |
|-----------|---------------|--------------------------|
| **AppButton** | Used in all workflows | Use `getByRole('button')` with accessible labels |
| **AppInput** | Form fields in service/item creation | Use `getByRole('textbox')` or test IDs for inline edits |
| **AppSelect** | Template selection, status updates | Use `getByRole('option')` for options, `getByRole('button')` to open |
| **AppTextarea** | Description fields | Use `getByRole('textbox')` |
| **AppCheckbox/Switch** | Feature flags, toggles | Use `getByRole('checkbox')` or `getByRole('switch')` |
| **AppBadge/Chip** | Status indicators, tags | Use test IDs for assertions, `getByText()` for content |
| **AppCard/AppPanel** | Right panel sections | Use test IDs: `*-panel`, `*-section` |
| **AppDivider** | Visual separators | Generally not tested |
| **AppIconButton** | Action buttons | Use test IDs or `getByRole('button')` |

### P0 Golden Patterns

Your tests already follow these patterns well:

**✅ RightPanel Pattern**
```typescript
// Current: Excellent usage
await page.getByRole('tab', { name: 'Services' }).click();
const servicesList = page.getByTestId('project-workspace-v2-services');
await expect(servicesList).toBeVisible();
```

**✅ LinearListRow Pattern**
```typescript
// Current: Good usage in deliverables workflow
const draftRow = page.getByTestId(/deliverable-item-row/).first();
await draftRow.getByRole('button', { name: 'Save' }).click();
```

**✅ InlineEditableCell Pattern**
```typescript
// Current: Excellent usage
await page.getByTestId('cell-item-title-901').click();
await page.getByTestId('cell-item-title-901-input').fill('Updated report');
await page.getByTestId('cell-item-title-901-save').click();
```

**✅ EmptyState Pattern**
```typescript
// Current: Used in projects-empty-reset.spec.ts
// Should verify empty state messages and CTAs
```

**✅ KPI Cards**
```typescript
// Current: Used in ProjectsHomePageV2 aggregates display
// Tests verify visibility of KPI metrics
```

## Identified Test-Design Misalignments

### 1. **Missing Test IDs for New Components**

**Issue:** New Golden Set components may not have consistent test ID patterns.

**Solution:** Ensure these naming conventions in your component code:
```typescript
// AppButton variants
<AppButton data-testid="action-primary-save" variant="primary">Save</AppButton>
<AppButton data-testid="action-secondary-cancel" variant="secondary">Cancel</AppButton>
<AppButton data-testid="action-outline-edit" variant="outline">Edit</AppButton>

// AppPanel and RightPanel
<AppPanel data-testid="service-details-panel">
  <RightPanelSection data-testid="service-details-section-info" title="Info">
    {/* content */}
  </RightPanelSection>
</AppPanel>

// LinearListRow (used in tables/lists)
<LinearListRow data-testid={`service-row-${service.service_id}`}>

// InlineEditableCell
<InlineEditableCell
  data-testid={`cell-${fieldName}-${rowId}`}
  onEdit={() => {}}
/>
```

### 2. **Overly Specific Mocking in Tests**

**Issue:** Tests mock many specific endpoints separately, making them brittle.

**Current pattern:**
```typescript
await page.route('**/api/projects/summary**', async (route) => { /* ... */ });
await page.route('**/api/projects/aggregates**', async (route) => { /* ... */ });
await page.route('**/api/dashboard/timeline**', async (route) => { /* ... */ });
// ... 10+ more routes
```

**Recommendation:** Create reusable mock setup functions:
```typescript
// In a helpers file: frontend/tests/helpers/setupMocks.ts
export const setupProjectsMocks = async (page, {
  projects = [],
  aggregates = {},
  timeline = {},
  users = [],
} = {}) => {
  // Setup all related mocks in one call
};
```

### 3. **Status Mapping Not Explicitly Tested**

**Issue:** The Golden Set defines status visual intents, but tests don't validate styling/appearance.

**Current:** Tests check presence but not visual state
```typescript
await expect(page.getByText('Active')).toBeVisible();
```

**Recommendation:** Add visual assertions:
```typescript
// Check that status displays with correct visual intent
const statusBadge = page.getByTestId(`status-badge-${projectId}`);
await expect(statusBadge).toHaveClass(/status-(draft|active|blocked|done|overdue|on-hold)/);
```

### 4. **Dialog/Modal Patterns Underutilized**

**Issue:** AppDialog component not consistently tested with proper role selectors.

**Current pattern:**
```typescript
// Sometimes found in tests, but not standard
```

**Recommendation:** Use accessibility roles for dialogs:
```typescript
// Open dialog
await page.getByRole('button', { name: 'Delete item' }).click();

// Verify dialog appears
const dialog = page.getByRole('dialog');
await expect(dialog).toBeVisible();

// Confirm or cancel
await page.getByRole('button', { name: 'Confirm' }).click();
```

### 5. **Form Pattern Testing Gaps**

**Issue:** Complex form patterns (accordion-like sections) not tested consistently.

**Current:** Some tests create services/items but don't validate all form states.

**Recommendation:** Create form testing helpers:
```typescript
// frontend/tests/helpers/formHelpers.ts
export const fillServiceForm = async (page, formData) => {
  // Fill name
  await page.getByRole('textbox', { name: /service name/i }).fill(formData.name);
  // Fill description
  await page.getByRole('textbox', { name: /description/i }).fill(formData.description);
  // etc.
};

// Usage in test
await fillServiceForm(page, { name: 'Design Review', description: '...' });
```

## Recommended Test Improvements

### 1. **Align Test ID Naming Convention**

Create a consistent naming schema across all components:

```typescript
// Pattern: [feature]-[component]-[identifier]-[optional-subpart]

// Examples:
data-testid="projects-home-table"
data-testid="projects-home-row-${projectId}"
data-testid="workspace-service-row-${serviceId}"
data-testid="workspace-deliverables-table"
data-testid="workspace-deliverable-row-${itemId}"
data-testid="workspace-reviews-panel"
data-testid="workspace-reviews-section-scheduled"
data-testid="workspace-reviews-cycle-row-${cycleId}"
data-testid="cell-${fieldName}-${recordId}"
data-testid="cell-${fieldName}-${recordId}-input"
data-testid="cell-${fieldName}-${recordId}-save"
data-testid="form-dialog-service-create"
data-testid="status-badge-${recordId}"
```

### 2. **Create Test Utilities Library**

Build helpers in `frontend/tests/helpers/` for:

```typescript
// helpers/selectors.ts - Consistent selector getters
export const selectors = {
  workspace: {
    reviewsTab: () => page.getByRole('tab', { name: 'Reviews' }),
    servicesTab: () => page.getByRole('tab', { name: 'Services' }),
    deliverableRow: (id) => page.getByTestId(`workspace-deliverable-row-${id}`),
  },
  forms: {
    submitButton: () => page.getByRole('button', { name: /submit|save/i }),
    cancelButton: () => page.getByRole('button', { name: /cancel/i }),
  },
};

// helpers/interactions.ts - Common user flows
export async function createService(page, data) {
  await page.getByRole('button', { name: 'Add Service' }).click();
  await page.getByRole('textbox', { name: /name/i }).fill(data.name);
  await page.getByRole('button', { name: 'Create' }).click();
}

export async function editInlineCell(page, testId, newValue) {
  await page.getByTestId(testId).click();
  await page.getByTestId(`${testId}-input`).fill(newValue);
  await page.getByTestId(`${testId}-save`).click();
}

// helpers/mocks.ts - Mock setup
export async function setupCompleteMocks(page, testData = {}) {
  // Setup all project-related mocks
}
```

### 3. **Enhance Golden Primitives Test Coverage**

Add dedicated primitive tests in `frontend/tests/e2e/primitives/`:

```typescript
// primitives/app-button.spec.ts
test('AppButton renders all variants correctly', async ({ page }) => {
  await page.goto('/ui'); // Navigate to UI playground
  
  const primaryBtn = page.getByTestId('btn-primary');
  await expect(primaryBtn).toHaveClass(/primary/);
  
  const secondaryBtn = page.getByTestId('btn-secondary');
  await expect(secondaryBtn).toHaveClass(/secondary/);
  
  // Test all variants: primary, secondary, outline, ghost, link, destructive
});

// primitives/app-input.spec.ts
test('AppInput displays error states correctly', async ({ page }) => {
  await page.goto('/ui');
  
  const input = page.getByRole('textbox', { name: /error input/i });
  await expect(input).toHaveClass(/error/);
  
  const errorMsg = page.getByTestId('input-error-message');
  await expect(errorMsg).toContainText('This field is required');
});
```

### 4. **Validate Status Styling**

Add visual regression or class-based assertions:

```typescript
// In any workflow test
test('projects display correct status visual intent', async ({ page }) => {
  await page.goto('/projects');
  
  // Draft - neutral/muted
  const draftProject = page.getByTestId('status-badge-draft-1');
  await expect(draftProject).toHaveClass(/status-neutral|status-muted/);
  
  // Active - primary
  const activeProject = page.getByTestId('status-badge-active-2');
  await expect(activeProject).toHaveClass(/status-primary/);
  
  // Blocked - destructive
  const blockedProject = page.getByTestId('status-badge-blocked-3');
  await expect(blockedProject).toHaveClass(/status-destructive|status-warning/);
});
```

## Migration Checklist

Use this checklist to systematically align existing tests:

- [ ] **Phase 1: Test ID Standardization**
  - [ ] Audit all components for test ID naming consistency
  - [ ] Create naming convention document
  - [ ] Update all component test IDs to follow pattern
  
- [ ] **Phase 2: Selector Modernization**
  - [ ] Replace hardcoded test IDs with selector helpers
  - [ ] Convert text selectors to role selectors where possible
  - [ ] Update tests to use helpers library

- [ ] **Phase 3: Mock Consolidation**
  - [ ] Create reusable mock setup functions
  - [ ] Consolidate per-test mocks into shared fixtures
  - [ ] Reduce route handling boilerplate

- [ ] **Phase 4: Golden Primitives Coverage**
  - [ ] Add primitive component tests
  - [ ] Test all variants and states
  - [ ] Add visual regression tests

- [ ] **Phase 5: Status & Visual Assertions**
  - [ ] Add class-based status assertions
  - [ ] Validate visual intents match Golden Set
  - [ ] Test error/success/warning states

## Key Test Files by Category

### High Priority (Core Workflows)
1. `projects-home-v2.spec.ts` - Primary entry point
2. `project-workspace-v2-smoke.spec.ts` - Basic navigation
3. `project-workspace-v2-services.spec.ts` - Service CRUD
4. `project-workspace-v2-deliverables-edit.spec.ts` - Item management
5. `deliverables-workflow.spec.ts` - End-to-end workflow

### Medium Priority (Feature-Specific)
1. `project-workspace-v2-reviews-projectwide.spec.ts` - Review cycles
2. `project-workspace-v2-invoice-*.spec.ts` - Billing workflows
3. `anchor-linking.spec.ts` - Issue linking
4. `bids-*.spec.ts` - Bid management

### Lower Priority (Edge Cases)
1. `projects-panel-*.spec.ts` - Alternative UI (may be legacy)
2. `projects-gate.spec.ts` - Feature flag gating
3. `project-workspace-v2-data-integrity.spec.ts` - Validation

## Testing Best Practices for This Codebase

### 1. Always Use Test Data Setup
```typescript
const seedData = {
  projects: [...],
  services: [...],
  items: [...],
};

test('workflow', async ({ page }) => {
  // Setup mocks with seed data
  await setupMocks(page, seedData);
});
```

### 2. Mock API Endpoints Comprehensively
```typescript
// Always mock the full API surface needed for the page
const requiredApis = [
  'GET /api/projects/:id',
  'GET /api/projects/:id/services',
  'GET /api/projects/:id/reviews',
  'GET /api/users',
];
```

### 3. Use Testid for Complex Identifiers
```typescript
// ✅ Good: Stable, intentional test ID
await page.getByTestId(`deliverable-row-${itemId}`).click();

// ❌ Avoid: Fragile, implementation-dependent
await page.locator('tr').nth(3).click();
```

### 4. Prefer Role Selectors for Interactions
```typescript
// ✅ Good: Matches accessibility intent
await page.getByRole('button', { name: 'Save' }).click();

// ❌ Less ideal: May break with styling changes
await page.getByClass('btn-save').click();
```

### 5. Test User-Visible Behavior
```typescript
// ✅ Good: Tests what user sees
await expect(page.getByText('Service created successfully')).toBeVisible();

// ❌ Implementation detail: Tests internal state
await expect(page.evaluate(() => window.__state__.serviceCount)).toBe(1);
```

## Debugging Test Issues

### Selector Not Found
```bash
# Check what test ID exists
await page.locator('[data-testid*="deliverable"]').screenshot('selectors.png');
```

### Flaky Tests
- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Use `waitFor` for dynamic content: `await page.getByTestId('item').waitFor()`
- Increase timeout if needed: `await expect(...).toBeVisible({ timeout: 10000 })`

### Mock Issues
- Use `page.on('requestfailed')` to catch failed requests
- Log intercepted routes: `console.log(route.request().url())`
- Verify mock response structure matches component expectations

## Summary

Your test suite is well-structured and comprehensive. The key alignment tasks are:

1. **Standardize test IDs** across all components following the naming pattern
2. **Create helper utilities** to reduce boilerplate and improve maintainability
3. **Add primitive component tests** to validate the Golden Set is correctly implemented
4. **Enhance assertions** to validate visual intents and status styling
5. **Consolidate mocks** using shared setup functions

This will ensure tests remain aligned with frontend design as components evolve.
