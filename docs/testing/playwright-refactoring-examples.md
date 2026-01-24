# Refactoring Examples: Converting Tests to Use Helpers

This document shows before/after examples of converting existing Playwright tests to align with the Golden Set standard and use the new helper utilities.

## Example 1: Projects Home Page Test

### Before (Current Pattern)

```typescript
// frontend/tests/e2e/projects-home-v2.spec.ts (original)

import { test, expect } from '@playwright/test';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Alpha Build',
    project_number: 'P-001',
    client_name: 'Client A',
    status: 'Active',
    internal_lead: 101,
    updated_at: '2024-05-10T10:00:00Z',
    health_pct: 82,
    end_date: '2024-08-01',
  },
  // ... more projects
];

const setupMocks = async (page: any) => {
  await page.route('**/api/projects/summary**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedProjects),
      });
      return;
    }
    await route.continue();
  });

  await page.route('**/api/projects/aggregates**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_count: seedProjects.length,
        sum_agreed_fee: 100000,
        sum_billed_to_date: 25000,
        sum_unbilled_amount: 75000,
        sum_earned_value: 30000,
        weighted_earned_value_pct: 30,
      }),
    });
  });

  // ... more routes
};

test('projects home displays projects in list view', async ({ page }) => {
  await setupMocks(page);
  await page.goto('/projects');
  
  await expect(page.getByTestId('projects-home-table')).toBeVisible();
  await expect(page.getByText('Alpha Build')).toBeVisible();
  await expect(page.getByText('Beta Tower')).toBeVisible();
});

test('clicking project row navigates to workspace', async ({ page }) => {
  await setupMocks(page);
  await page.goto('/projects');
  
  await page.getByTestId('projects-home-row-1').click();
  await expect(page).toHaveURL(/\/workspace\/1/);
});
```

### After (Using Helpers)

```typescript
// frontend/tests/e2e/projects-home-v2.spec.ts (refactored)

import { test, expect } from '@playwright/test';
import { 
  selectors, 
  setupProjectsHomeMocks, 
  assertListItemCount 
} from '../helpers';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Alpha Build',
    project_number: 'P-001',
    client_name: 'Client A',
    status: 'Active',
    internal_lead: 101,
    health_pct: 82,
    end_date: '2024-08-01',
  },
  {
    project_id: 2,
    project_name: 'Beta Tower',
    project_number: 'P-002',
    client_name: 'Client B',
    status: 'On Hold',
    internal_lead: 102,
    health_pct: 45,
    end_date: '2024-12-10',
  },
];

test('projects home displays projects in list view', async ({ page }) => {
  // ✅ Single call to setup all mocks
  await setupProjectsHomeMocks(page, { projects: seedProjects });
  
  await page.goto('/projects');
  
  // ✅ Use selector helpers
  const table = page.locator(selectors.projectsHome.table());
  await expect(table).toBeVisible();
  
  // ✅ Use assertion helper
  await assertListItemCount(page, 'projects-home-table', 2);
  
  // ✅ Verify content
  await expect(page.getByText('Alpha Build')).toBeVisible();
  await expect(page.getByText('Beta Tower')).toBeVisible();
});

test('clicking project row navigates to workspace', async ({ page }) => {
  await setupProjectsHomeMocks(page, { projects: seedProjects });
  
  await page.goto('/projects');
  
  // ✅ Use selector helper
  const projectRow = page.locator(selectors.projectsHome.row(1));
  await projectRow.click();
  
  // ✅ Verify navigation
  await expect(page).toHaveURL(/\/workspace\/1/);
});
```

**Changes:**
- Single `setupProjectsHomeMocks()` instead of multiple `page.route()` calls
- Used `selectors.projectsHome.*` instead of hardcoded test IDs
- Used `assertListItemCount()` helper for verification
- 50% less boilerplate code

---

## Example 2: Service Management Workflow

### Before (Current Pattern)

```typescript
// frontend/tests/e2e/project-workspace-v2-services.spec.ts (excerpt)

test('creating a new service from template', async ({ page }) => {
  // Setup mocks...
  
  await page.goto('/workspace/1');
  
  // Click to add service
  await page.getByTestId('workspace-add-service-menu-button').click();
  await page.getByRole('menuitem', { name: 'From template' }).click();
  
  // Select template
  await page.getByRole('option', { name: 'BIM Coordination' }).click();
  
  // Submit form
  await page.getByRole('button', { name: 'Create Service' }).click();
  
  // Verify service appears
  await expect(page.getByTestId('workspace-service-row-101')).toBeVisible();
  
  // Click edit button
  await page.getByTestId('workspace-edit-service-button').click();
  
  // Verify form has template info
  await expect(page.getByText('Template: BIM Coordination')).toBeVisible();
});
```

### After (Using Helpers)

```typescript
// frontend/tests/e2e/project-workspace-v2-services.spec.ts (refactored)

import { test, expect } from '@playwright/test';
import { 
  selectors, 
  navigateToProjectWorkspace, 
  setupWorkspaceMocks,
  waitForLoading 
} from '../helpers';

test('creating a new service from template', async ({ page }) => {
  await setupWorkspaceMocks(page);
  
  // ✅ Use helper to navigate
  await navigateToProjectWorkspace(page, 1);
  
  // ✅ Use selector helper
  const addBtn = selectors.services.addButton(page);
  await addBtn.click();
  
  // Select template option
  await page.getByRole('option', { name: 'BIM Coordination' }).click();
  
  // ✅ Use selector helper for submit
  await selectors.forms.submitButton(page).click();
  
  // ✅ Wait for loading
  await waitForLoading(page);
  
  // ✅ Verify service appears using selector
  const serviceRow = page.locator(selectors.services.row(101));
  await expect(serviceRow).toBeVisible();
  
  // ✅ Use selector helper for edit
  const editBtn = selectors.services.editButton(page);
  await editBtn.click();
  
  // Verify template display
  await expect(page.getByText('Template: BIM Coordination')).toBeVisible();
});
```

**Changes:**
- Used `navigateToProjectWorkspace()` to reduce setup code
- Used consistent `selectors.services.*` pattern
- Added `waitForLoading()` for reliability
- Removed comment clutter - code is self-documenting
- Easier to update selectors centrally

---

## Example 3: Inline Edit Workflow (Deliverables)

### Before (Current Pattern)

```typescript
// frontend/tests/e2e/deliverables-workflow.spec.ts (excerpt)

test('editing deliverable item properties inline', async ({ page }) => {
  // Setup...
  
  await page.getByRole('tab', { name: 'Deliverables' }).click();
  
  // Add new item
  await page.getByTestId('deliverables-add-item-button').click();
  
  const draftRow = page.getByTestId(/deliverable-item-row/).first();
  await draftRow.getByRole('button', { name: 'Save' }).click();
  
  // Edit title
  await page.getByTestId('cell-item-title-901').click();
  await page.getByTestId('cell-item-title-901-input').fill('Updated report');
  await page.getByTestId('cell-item-title-901-save').click();
  
  await expect(page.getByText('Updated report')).toBeVisible();
  
  // Edit due date
  await page.getByTestId('cell-due-date-901').click();
  const dueInput = page.getByTestId('cell-due-date-901-input');
  await dueInput.fill('2024-12-31');
  await page.getByTestId('cell-due-date-901-save').click();
  
  // Delete item
  const deleteButton = page.getByRole('button', { name: 'Delete item' });
  await deleteButton.click();
  
  await expect(page.getByText('Updated report')).toHaveCount(0);
});
```

### After (Using Helpers)

```typescript
// frontend/tests/e2e/deliverables-workflow.spec.ts (refactored)

import { test, expect } from '@playwright/test';
import { 
  switchTab, 
  addDeliverableItem, 
  editInlineCell, 
  deleteDeliverableItem,
  assertSavedSuccessfully,
  setupWorkspaceMocks 
} from '../helpers';

test('editing deliverable item properties inline', async ({ page }) => {
  await setupWorkspaceMocks(page);
  
  // ✅ Use helper to switch tabs
  await switchTab(page, 'Deliverables');
  
  // ✅ Use helper to add item
  await addDeliverableItem(page, { title: 'New report' });
  
  // ✅ Use helper to edit inline
  await editInlineCell(page, 'item-title', 901, 'Updated report');
  
  // ✅ Use assertion helper
  await assertSavedSuccessfully(page, 'item-title', 901, 'Updated report');
  
  // Edit another field
  await editInlineCell(page, 'due-date', 901, '2024-12-31');
  
  // ✅ Use helper to delete
  await deleteDeliverableItem(page, 901);
  
  // Verify deletion
  await expect(page.getByText('Updated report')).toHaveCount(0);
});
```

**Changes:**
- `switchTab()` instead of `getByRole('tab').click()`
- `addDeliverableItem()` instead of manual button clicking
- `editInlineCell()` consolidates the 3-step edit/fill/save pattern
- `assertSavedSuccessfully()` combines visibility + content checks
- `deleteDeliverableItem()` handles the delete workflow
- **70% reduction in boilerplate** - 11 lines vs 30+ lines
- Much more readable and maintainable

---

## Example 4: Status Validation (Golden Set Alignment)

### Before (No Status Validation)

```typescript
test('project list displays all project statuses', async ({ page }) => {
  const projects = [
    { project_id: 1, project_name: 'Draft Project', status: 'Draft' },
    { project_id: 2, project_name: 'Active Project', status: 'Active' },
    { project_id: 3, project_name: 'Blocked Project', status: 'Blocked' },
  ];
  
  await setupProjectsHomeMocks(page, { projects });
  await page.goto('/projects');
  
  // Just verify presence, not visual intent
  await expect(page.getByText('Draft Project')).toBeVisible();
  await expect(page.getByText('Active Project')).toBeVisible();
  await expect(page.getByText('Blocked Project')).toBeVisible();
});
```

### After (With Status Validation)

```typescript
// frontend/tests/e2e/projects-home-status.spec.ts (new test file)

import { test, expect } from '@playwright/test';
import { setupProjectsHomeMocks, assertStatusIntent } from '../helpers';

test('project list displays statuses with correct visual intents', async ({ page }) => {
  const projects = [
    { 
      project_id: 1, 
      project_name: 'Draft Project', 
      status: 'Draft',
      // matches golden-set.md status mapping
    },
    { 
      project_id: 2, 
      project_name: 'Active Project', 
      status: 'Active',
    },
    { 
      project_id: 3, 
      project_name: 'Blocked Project', 
      status: 'Blocked',
    },
  ];
  
  await setupProjectsHomeMocks(page, { projects });
  await page.goto('/projects');
  
  // ✅ Verify visual intents match Golden Set
  
  // Draft → neutral/muted
  await assertStatusIntent(page, 1, 'draft');
  
  // Active → primary (strong emphasis)
  await assertStatusIntent(page, 2, 'active');
  
  // Blocked → destructive/warning
  await assertStatusIntent(page, 3, 'blocked');
});

test('status badges have appropriate styling', async ({ page }) => {
  const projects = [
    { project_id: 1, status: 'Done' },
    { project_id: 2, status: 'Overdue' },
    { project_id: 3, status: 'On Hold' },
  ];
  
  await setupProjectsHomeMocks(page, { projects });
  await page.goto('/projects');
  
  // ✅ Done → success
  await assertStatusIntent(page, 1, 'done');
  
  // ✅ Overdue → destructive (urgent)
  await assertStatusIntent(page, 2, 'overdue');
  
  // ✅ On Hold → muted (de-emphasized)
  await assertStatusIntent(page, 3, 'on-hold');
});
```

**Changes:**
- Added dedicated test file for status validation
- Uses `assertStatusIntent()` helper to verify Golden Set compliance
- Tests visual styling, not just presence
- Enables visual regression testing in future
- Documents Golden Set mapping in tests

---

## Migration Strategy

### Phase 1: Create Helpers (Already Done ✅)
- `helpers.ts` with selectors, interactions, mocks, assertions

### Phase 2: Update High-Priority Tests (Week 1)
1. `projects-home-v2.spec.ts` - Entry point, high impact
2. `project-workspace-v2-smoke.spec.ts` - Core navigation
3. `project-workspace-v2-services.spec.ts` - Service CRUD

**Command to update:**
```bash
# In one test file, replace all setupMocks calls
# Update all getByTestId to use selectors.*
# Update all common patterns to use helpers
```

### Phase 3: Update Medium-Priority Tests (Week 2-3)
1. `deliverables-workflow.spec.ts` - Heavy use of editInlineCell
2. `project-workspace-v2-reviews-projectwide.spec.ts`
3. `project-workspace-v2-invoice-*.spec.ts`

### Phase 4: Add Golden Set Validation Tests (Week 4)
- Create `primitives/` test folder
- Test each Golden Set component
- Validate status intents
- Add visual regression tests

### Phase 5: Consolidate Remaining Tests (Ongoing)
- Update legacy panel tests
- Consolidate duplicated mocks
- Remove obsolete tests

---

## Quick Reference: Find & Replace Patterns

### Convert setupMocks to helper
```bash
# Before
const setupMocks = async (page) => {
  await page.route('**/api/projects/summary**', ...)
  // ... many routes
}

# After (one-liner)
await setupProjectsHomeMocks(page, { projects: seedData });
```

### Convert tab switching
```bash
# Before
await page.getByRole('tab', { name: 'Services' }).click();

# After
await switchTab(page, 'Services');
```

### Convert inline editing
```bash
# Before
await page.getByTestId('cell-title-901').click();
await page.getByTestId('cell-title-901-input').fill('New');
await page.getByTestId('cell-title-901-save').click();

# After
await editInlineCell(page, 'title', 901, 'New');
```

### Convert assertions
```bash
# Before
await expect(page.getByTestId('status-badge-1')).toHaveClass(/primary/);

# After
await assertStatusIntent(page, 1, 'active');
```

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Setup code** | 40+ lines | 2-3 lines |
| **Selector fragility** | High (hard-coded strings) | Low (centralized) |
| **Test readability** | Medium (verbose) | High (intent-clear) |
| **Golden Set compliance** | Not validated | Explicitly tested |
| **Maintenance cost** | High (UI change = many tests update) | Low (update helpers once) |
| **Test reliability** | Medium (timing issues) | High (built-in waits) |
| **Status validation** | None | Complete |

