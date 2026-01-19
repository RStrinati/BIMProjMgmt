# Monthly Billing Test Suite Reference

Quick reference for running and understanding the monthly billing Playwright test suite.

## Test Files Overview

| File | Tests | Focus Area | Duration |
|------|-------|------------|----------|
| `project-workspace-v2-invoice-filters.spec.ts` | 4 | Filter functionality | ~30s |
| `project-workspace-v2-batch-workflows.spec.ts` | 4 | Batch management | ~30s |
| `project-workspace-v2-invoice-overview.spec.ts` | 3 | Overview metrics | ~30s |
| `project-workspace-v2-data-integrity.spec.ts` | 2 | Data consistency | ~30s |
| **TOTAL** | **13** | **End-to-end coverage** | **~2min** |

## Running Tests

### Run All Monthly Billing Tests
```bash
cd frontend
npx playwright test tests/e2e/project-workspace-v2-*.spec.ts
```

### Run Individual Test Files
```bash
# Filter tests
npx playwright test tests/e2e/project-workspace-v2-invoice-filters.spec.ts

# Batch workflow tests
npx playwright test tests/e2e/project-workspace-v2-batch-workflows.spec.ts

# Overview pipeline tests
npx playwright test tests/e2e/project-workspace-v2-invoice-overview.spec.ts

# Data integrity tests
npx playwright test tests/e2e/project-workspace-v2-data-integrity.spec.ts
```

### Run Specific Test
```bash
npx playwright test tests/e2e/project-workspace-v2-invoice-filters.spec.ts -g "due this month"
```

### Debug Mode
```bash
npx playwright test tests/e2e/project-workspace-v2-invoice-filters.spec.ts --debug
```

## Test Scenarios by File

### 1. Invoice Filters (`invoice-filters.spec.ts`)

**Test 1: Due this month filter**
- Given: Deliverables with various invoice_month_final values
- When: "Due this month" filter applied
- Then: Shows only deliverables with invoice_month_final = current month

**Test 2: Unbatched filter**
- Given: Mix of batched and unbatched deliverables
- When: "Unbatched" filter applied
- Then: Shows only deliverables with invoice_batch_id = null

**Test 3: Ready to invoice filter**
- Given: Deliverables in various states (planned, in-progress, completed, billed)
- When: "Ready to invoice" filter applied
- Then: Shows only completed + unbilled deliverables

**Test 4: Combined filters (AND logic)**
- Given: Diverse deliverable set
- When: Multiple filters applied (e.g., due this month + unbatched + ready)
- Then: Shows deliverables matching ALL filter criteria

### 2. Batch Workflows (`batch-workflows.spec.ts`)

**Test 1: Batch dropdown disabled without invoice month**
- Given: Deliverable with invoice_month_final = null
- When: User attempts to assign batch
- Then: Batch dropdown is disabled with tooltip "Set invoice month first"

**Test 2: Batch dropdown filtered by matching month**
- Given: Multiple batches with different invoice_month values
- When: Deliverable has invoice_month_final = 2026-01
- Then: Dropdown shows only batches with invoice_month = 2026-01

**Test 3: Helper text when no batches exist**
- Given: No batches exist for invoice_month_final
- When: User opens batch dropdown
- Then: Shows "No batches for [month] - create one"

**Test 4: Create new batch via dropdown**
- Given: Deliverable with invoice_month_final set
- When: User selects "Create new batch" from dropdown
- Then: Batch creation dialog opens with pre-filled invoice_month

### 3. Overview Pipeline (`invoice-overview.spec.ts`)

**Test 1: Pipeline aggregation by invoice_month_final**
- Given: Deliverables with various invoice_month_final values
- When: User views Overview tab
- Then: Pipeline widget shows aggregated counts and amounts by month

**Test 2: Ready this month metric**
- Given: Mix of completed/billed/planned deliverables for current month
- When: User views Overview tab
- Then: "Ready this month" shows only completed + unbilled count/amount

**Test 3: Unbatched risk metric**
- Given: Mix of batched/unbatched deliverables due current month
- When: User views Overview tab
- Then: "Unbatched risk" shows count and total amount with warning indicator

### 4. Data Integrity (`data-integrity.spec.ts`)

**Test 1: Due date changes update invoice_month_auto and preserve override**
- Given: Deliverable with due_date and no override
- When: User changes due_date to new month
- Then: invoice_month_auto updates, invoice_month_final reflects new month
- When: User sets invoice_month_override
- Then: invoice_month_final shows override
- When: User changes due_date again
- Then: invoice_month_auto updates, but invoice_month_final preserves override
- When: User clears override
- Then: invoice_month_final falls back to invoice_month_auto

**Test 2: Override takes precedence over auto**
- Given: Deliverable with invoice_month_override = 2026-03, due_date in 2026-01
- When: User changes due_date to 2026-05
- Then: invoice_month_auto updates to 2026-05
- And: invoice_month_final stays 2026-03 (override preserved)
- And: Snackbar notification shows "auto-calculated to 2026-05 but override (2026-03) was preserved"

## Business Rules Validated

### Invoice Month Computation
- ✅ invoice_month_auto = YYYY-MM of due_date
- ✅ invoice_month_final = COALESCE(override, auto)
- ✅ Override preserved when due_date changes
- ✅ Clearing override falls back to auto

### Batch Assignment
- ✅ Batch dropdown disabled when invoice_month_final is null
- ✅ Batch dropdown filtered by invoice_month_final
- ✅ Helper text shown when no batches exist
- ✅ Create batch pre-fills invoice_month from deliverable

### Filters
- ✅ Due this month: invoice_month_final = current month
- ✅ Unbatched: invoice_batch_id IS NULL
- ✅ Ready to invoice: status = completed AND is_billed = false
- ✅ Combined filters: AND logic (all criteria must match)

### Overview Metrics
- ✅ Pipeline: Aggregate by invoice_month_final
- ✅ Ready this month: completed + unbilled + current month
- ✅ Unbatched risk: unbatched + due current month + warning indicator

## Test Data Patterns

### Deterministic Mocked Data
All tests use mocked API responses with deterministic data:

```typescript
const reviewItems = [
  {
    review_id: 101,
    service_id: 55,
    project_id: 1,
    cycle_no: 1,
    planned_date: '2026-01-05',
    due_date: '2026-01-15',
    status: 'completed',
    invoice_month_override: null,
    invoice_month_auto: '2026-01',
    invoice_month_final: '2026-01',
    invoice_batch_id: null,
    billing_amount: 5000,
    is_billed: false,
  },
  // ... more items
];
```

### State Management in Tests
Tests that mutate data use closure-based state management:

```typescript
let currentReviewItems = [/* initial state */];

await page.route('**/api/service_reviews/101', async (route) => {
  const postData = route.request().postDataJSON();
  
  // Update local state
  currentReviewItems[0] = {
    ...currentReviewItems[0],
    due_date: postData.due_date,
    invoice_month_auto: postData.due_date.slice(0, 7),
    // ... recalculate invoice_month_final
  };
  
  await route.fulfill({
    status: 200,
    body: JSON.stringify(currentReviewItems[0]),
  });
});
```

## Debugging Failed Tests

### Common Failures

**Selector not found**
```
Error: locator.click: Target closed
```
**Resolution:** Element may not be visible, add wait: `await expect(element).toBeVisible()`

**Assertion timeout**
```
Error: expect(locator).toContainText: Timeout 5000ms exceeded
```
**Resolution:** Element may be updating asynchronously, add wait: `await page.waitForTimeout(500)`

**Mock not matching**
```
Error: Route not found for **/api/projects/1/reviews
```
**Resolution:** Check route pattern matches actual request URL, use `**` for wildcards

### Debug Workflow
1. Run with `--debug` flag to open Playwright Inspector
2. Use `await page.pause()` to freeze execution at specific point
3. Check browser console for JavaScript errors
4. Verify mock routes are intercepting requests (Network tab)
5. Check test data matches component expectations

### Useful Debug Commands
```typescript
// Print current page state
await page.screenshot({ path: 'debug.png' });

// Print element text content
console.log(await element.textContent());

// Pause execution
await page.pause();

// Wait for network idle
await page.waitForLoadState('networkidle');
```

## Test Maintenance

### When to Update Tests

**Scenario 1: UI Changes**
- Example: Deliverables table columns reordered
- Action: Update selectors (`getByTestId`, `getByText`, etc.)

**Scenario 2: Business Rule Changes**
- Example: invoice_month_final now includes day (YYYY-MM-DD)
- Action: Update assertions and mock data

**Scenario 3: New Features**
- Example: Batch approval workflow added
- Action: Create new test file or add to existing suite

### Best Practices
- ✅ Use `data-testid` attributes for stable selectors
- ✅ Avoid brittle selectors like CSS classes or nth-child
- ✅ Keep mock data minimal (only what's needed for test)
- ✅ Test one business rule per test case
- ✅ Use descriptive test names that explain the scenario

### Anti-Patterns
- ❌ Testing implementation details (component state)
- ❌ Testing third-party libraries (Material-UI behavior)
- ❌ Hard-coded dates (use current month or relative dates)
- ❌ Excessive waits (use deterministic waits like `expect().toBeVisible()`)
- ❌ Testing multiple unrelated scenarios in one test

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Monthly Billing Tests
  run: |
    cd frontend
    npx playwright test tests/e2e/project-workspace-v2-*.spec.ts
```

### Pre-commit Hook
```bash
#!/bin/bash
cd frontend
npx playwright test tests/e2e/project-workspace-v2-*.spec.ts --reporter=line
```

## Related Documentation
- [Monthly Billing Discovery](./monthly_billing_discovery.md) - Architecture and requirements
- [Monthly Billing Implementation Summary](./monthly-billing-implementation-summary.md) - What was built
- [Playwright Documentation](https://playwright.dev/docs/intro) - Official Playwright docs
- [Testing Best Practices](../testing/TESTING_BEST_PRACTICES.md) - Project testing conventions

## Quick Wins

### Run Headless (Faster)
```bash
npx playwright test --project=chromium
```

### Run in UI Mode (Visual Debugging)
```bash
npx playwright test --ui
```

### Generate Test Report
```bash
npx playwright test
npx playwright show-report
```

### Run Specific Browser
```bash
npx playwright test --project=firefox
npx playwright test --project=webkit
```
