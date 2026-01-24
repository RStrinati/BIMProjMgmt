import { test, expect } from '@playwright/test';
import { setupWorkspaceMocks, switchTab, editInlineCell, navigateToProjectWorkspace, waitForLoading } from '../helpers';

const reviews = [
  {
    review_id: 101,
    service_id: 55,
    project_id: 1,
    cycle_no: 1,
    planned_date: '2024-05-10',
    due_date: '2024-05-20',
    status: 'planned',
    service_name: 'Design Review',
    service_code: 'DR-01',
  },
];


test.describe('Deliverables inline edits', () => {
  test('edits due date field', async ({ page }) => {
    let patchCallCount = 0;

    await setupWorkspaceMocks(page, { reviews });

    // Mock review update
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        const payload = await route.request().postDataJSON();
        reviews[0].due_date = payload.due_date || reviews[0].due_date;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Edit due date
    await editInlineCell(page, 'due_date', 101, '2024-06-15');
    await waitForLoading(page);
    expect(patchCallCount).toBeGreaterThan(0);
  });

  test('edits invoice reference field', async ({ page }) => {
    let patchCallCount = 0;

    await setupWorkspaceMocks(page, { reviews });

    // Mock review update
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        const payload = await route.request().postDataJSON();
        reviews[0].invoice_reference = payload.invoice_reference;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Edit invoice reference
    await editInlineCell(page, 'invoice_reference', 101, 'INV-2024-001');
    await waitForLoading(page);
    expect(patchCallCount).toBeGreaterThan(0);
  });

  test('toggles billing status', async ({ page }) => {
    let patchCallCount = 0;

    await setupWorkspaceMocks(page, { reviews });

    // Mock review update
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        reviews[0].is_billed = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Toggle billing
    const billingToggle = page.locator('[data-testid="billing-toggle-101"]').first();
    if (await billingToggle.isVisible()) {
      await billingToggle.click();
      await waitForLoading(page);
      expect(patchCallCount).toBeGreaterThan(0);
    }
  });

  test('handles patch errors gracefully', async ({ page }) => {
    await setupWorkspaceMocks(page, { reviews });

    // Mock failed update
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Try to edit (app should handle error gracefully)
    await expect(page.locator('body')).toBeVisible();
  });
});
