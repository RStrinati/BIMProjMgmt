# Playwright Alignment - Quick Reference Card

## Import Helpers
```typescript
import { 
  selectors, 
  createService, 
  editInlineCell, 
  switchTab, 
  setupWorkspaceMocks,
  assertStatusIntent 
} from '../helpers';
```

---

## Common Selectors

### Workspace Navigation
```typescript
selectors.workspace.servicesTab(page)
selectors.workspace.deliverablesTab(page)
selectors.workspace.reviewsTab(page)
```

### Services
```typescript
selectors.services.addButton(page)
selectors.services.row(55)           // returns string for locator()
selectors.services.editButton(page)
```

### Deliverables
```typescript
selectors.deliverables.addButton(page)
selectors.deliverables.row(901)
selectors.deliverables.cell('title', 901)
selectors.deliverables.cellInput('title', 901)
selectors.deliverables.cellSave('title', 901)
```

### Forms
```typescript
selectors.forms.dialog(page)
selectors.forms.submitButton(page)
selectors.forms.cancelButton(page)
selectors.forms.nameInput(page)
```

---

## Common Interactions

### Create a Service
```typescript
await createService(page, {
  name: 'Design Review',
  code: 'BIM',
  description: 'Weekly coordination'
});
```

### Edit Inline Cell
```typescript
await editInlineCell(page, 'title', 901, 'New Title');
// Handles: click → fill → save
```

### Switch Tab
```typescript
await switchTab(page, 'Services');
await switchTab(page, 'Deliverables');
await switchTab(page, 'Reviews');
```

### Add Deliverable Item
```typescript
await addDeliverableItem(page, { 
  title: 'Weekly Progress Report' 
});
```

### Delete Item
```typescript
await deleteDeliverableItem(page, 901);
```

---

## Common Mocks

### Workspace
```typescript
await setupWorkspaceMocks(page, {
  projects: [/* ... */],
  services: [/* ... */],
  items: [/* ... */],
  users: [/* ... */]
});
```

### Projects Home
```typescript
await setupProjectsHomeMocks(page, {
  projects: [/* ... */],
  users: [/* ... */]
});
```

---

## Common Assertions

### Status Visual Intent
```typescript
await assertStatusIntent(page, projectId, 'active');
// Options: 'draft' | 'active' | 'blocked' | 'done' | 'overdue' | 'on-hold'
```

### Saved Successfully
```typescript
await assertSavedSuccessfully(page, 'title', 901, 'New Title');
```

### In Edit Mode
```typescript
await assertInEditMode(page, 'title', 901);
```

### Empty State
```typescript
await assertEmptyState(page, 'workspace-services');
```

### List Item Count
```typescript
await assertListItemCount(page, 'project-workspace-v2-services', 3);
```

---

## Test ID Naming Convention

```
data-testid="[feature]-[component]-[type]-[id]-[state]"

Examples:
  workspace-service-row-123
  deliverable-item-row-901
  cell-title-901-input
  status-badge-123
  blocker-badge-456
  form-dialog-service-create
```

---

## Migration Checklist

### For Each Test File:

- [ ] Import helpers at top
- [ ] Replace setupMocks with setupWorkspaceMocks/setupProjectsHomeMocks
- [ ] Replace hardcoded test IDs with selectors.*
- [ ] Replace multi-step interactions with helpers (editInlineCell, etc.)
- [ ] Add status validation tests using assertStatusIntent
- [ ] Run test, verify passes

### For Each Component:

- [ ] Add data-testid following convention
- [ ] Verify test selector can find it
- [ ] Update tests to use selector helper
- [ ] Run test suite, confirm no failures

---

## Golden Set Status Mapping

| Status   | Visual Intent | Test Value |
|----------|---------------|-----------|
| Draft    | neutral       | `'draft'` |
| Active   | primary       | `'active'` |
| Blocked  | destructive   | `'blocked'` |
| Done     | success       | `'done'` |
| Overdue  | destructive   | `'overdue'` |
| On Hold  | muted         | `'on-hold'` |

---

## Debugging Commands

### Find missing test IDs
```bash
grep -r '<AppButton' frontend/src/components/ | grep -v 'data-testid'
grep -r '<AppInput' frontend/src/components/ | grep -v 'data-testid'
```

### Run single test
```bash
npx playwright test tests/e2e/projects-home-v2.spec.ts
```

### Run with UI
```bash
npx playwright test --headed
```

### Debug mode
```bash
npx playwright test --debug
```

---

## Common Patterns

### Create → Edit → Delete Workflow
```typescript
// Create
await createService(page, { name: 'Test Service' });

// Edit - find the row and edit a cell
const row = page.locator(selectors.services.row(101));
await editInlineCell(page, 'name', 101, 'Updated Service');

// Delete
const deleteBtn = row.getByRole('button', { name: /delete/i });
await deleteBtn.click();
await page.getByRole('button', { name: /confirm/i }).click();
```

### Form Fill & Submit
```typescript
const dialog = page.locator(selectors.forms.dialog());
await dialog.getByRole('textbox', { name: /name/i }).fill('Test');
await selectors.forms.submitButton(page).click();
```

### Tab Navigation
```typescript
await switchTab(page, 'Services');
const servicesList = page.locator(selectors.services.list());
await expect(servicesList).toBeVisible();
```

---

## Status Validation Template

```typescript
test('statuses display correct visual intents', async ({ page }) => {
  const projects = [
    { project_id: 1, status: 'Draft' },
    { project_id: 2, status: 'Active' },
    { project_id: 3, status: 'Blocked' },
  ];
  
  await setupProjectsHomeMocks(page, { projects });
  await page.goto('/projects');
  
  // Draft → neutral/muted
  await assertStatusIntent(page, 1, 'draft');
  
  // Active → primary
  await assertStatusIntent(page, 2, 'active');
  
  // Blocked → destructive
  await assertStatusIntent(page, 3, 'blocked');
});
```

---

## Inline Edit Template

```typescript
test('edit item inline', async ({ page }) => {
  await setupWorkspaceMocks(page);
  await navigateToProjectWorkspace(page, 1);
  await switchTab(page, 'Deliverables');
  
  // Single line to edit
  await editInlineCell(page, 'title', 901, 'New Title');
  
  // Verify
  await assertSavedSuccessfully(page, 'title', 901, 'New Title');
});
```

---

## Documentation Links

- **Full Guide:** docs/testing/PLAYWRIGHT-ALIGNMENT-GUIDE.md
- **Alignment Details:** docs/testing/playwright-test-alignment.md  
- **Refactoring Examples:** docs/testing/playwright-refactoring-examples.md
- **Test ID Audit:** docs/testing/test-id-audit.md
- **Helpers Library:** frontend/tests/helpers.ts

---

## When You're Stuck

1. **Check helpers.ts** - 30+ utilities documented
2. **Search refactoring-examples.md** - Real scenarios
3. **Run audit commands** - From test-id-audit.md
4. **Use --debug mode** - `npx playwright test --debug`
5. **Screenshot failures** - `page.screenshot()` in test

---

**Print this card and keep it handy while refactoring!**
