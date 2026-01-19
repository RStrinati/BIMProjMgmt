import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Data Integrity Test Project',
  status: 'active',
};

const setupMocks = async (page: any, reviewItems: any[]) => {
  await page.route('**/api/projects/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(projectPayload),
    });
  });

  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/tasks/notes-view**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tasks: [], total: 0, page: 1, page_size: 5 }),
    });
  });

  await page.route('**/api/projects/1/reviews**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: reviewItems, total: reviewItems.length }),
    });
  });

  await page.route('**/api/projects/1/items**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });

  await page.route('**/api/invoice_batches**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/projects/finance_grid**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_id: 1,
        agreed_fee: 100000,
        billed_to_date: 0,
        earned_value: 0,
        earned_value_pct: 0,
        invoice_pipeline: [],
        ready_this_month: null,
      }),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Data Integrity', () => {
  test('changing due_date updates invoice_month_auto and preserves override', async ({ page }) => {
    let currentReviewItems = [
      {
        review_id: 2001,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-15',
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_override: null,
        invoice_month_auto: '2026-01',
        invoice_month_final: '2026-01',
        invoice_batch_id: null,
        billing_amount: 5000,
        is_billed: false,
      },
    ];

    await setupMocks(page, currentReviewItems);

    // Mock the PATCH endpoint to update due_date
    await page.route('**/api/projects/1/services/55/reviews/2001', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();

      if (postData.due_date) {
        // Update due_date triggers invoice_month_auto recalculation
        const newDueDate = postData.due_date;
        const newAutoMonth = newDueDate.slice(0, 7);

        // invoice_month_auto updates to new due_date month
        currentReviewItems[0] = {
          ...currentReviewItems[0],
          due_date: newDueDate,
          invoice_month_auto: newAutoMonth,
          // invoice_month_override remains unchanged
          invoice_month_final: currentReviewItems[0].invoice_month_override || newAutoMonth,
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(currentReviewItems[0]),
        });
      } else if ('invoice_month_override' in postData) {
        // User sets override
        currentReviewItems[0] = {
          ...currentReviewItems[0],
          invoice_month_override: postData.invoice_month_override,
          invoice_month_final: postData.invoice_month_override || currentReviewItems[0].invoice_month_auto,
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(currentReviewItems[0]),
        });
      }
    });

    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: /Deliverables/i }).click();

    const deliverablesTab = page.getByTestId('project-workspace-v2-reviews');
    await expect(deliverablesTab).toBeVisible();

    // Initial state: due_date = 2026-01-15, invoice_month_final = 2026-01
    const row2001 = deliverablesTab.getByTestId('deliverable-row-2001');
    await expect(row2001).toBeVisible();
    await expect(row2001.getByTestId('cell-due-2001')).toContainText('2026-01-15');

    const invoiceMonthCell = row2001.getByTestId('cell-invoice-month-2001');
    await expect(invoiceMonthCell).toContainText('2026-01');

    // Step 1: Change due_date to 2026-02-20 → invoice_month_auto should update to 2026-02
    const dueDateCell = row2001.getByTestId('cell-due-2001');
    await dueDateCell.click();

    const dueDateInput = page.getByTestId('cell-due-2001-input');
    await dueDateInput.fill('2026-02-20');
    await dueDateInput.press('Enter');

    // Wait for update to complete
    await page.waitForTimeout(500);

    // Verify invoice_month_final updated to 2026-02
    await expect(invoiceMonthCell).toContainText('2026-02');

    // Step 2: Set invoice_month_override to 2026-03
    await invoiceMonthCell.click();
    const overrideInput = page.getByTestId('cell-invoice-month-2001-input');
    await overrideInput.fill('2026-03');
    await overrideInput.press('Enter');

    // Wait for update
    await page.waitForTimeout(500);

    // Verify invoice_month_final shows override
    await expect(invoiceMonthCell).toContainText('2026-03');

    // Step 3: Change due_date again to 2026-04-25 → override should be preserved
    await dueDateCell.click();
    const dueDateInput2 = page.getByTestId('cell-due-2001-input');
    await dueDateInput2.fill('2026-04-25');
    await dueDateInput2.press('Enter');

    // Wait for update
    await page.waitForTimeout(500);

    // invoice_month_final should STILL be 2026-03 (override preserved)
    await expect(invoiceMonthCell).toContainText('2026-03');

    // Step 4: Clear override (set to empty) → should fall back to invoice_month_auto (2026-04)
    await invoiceMonthCell.click();
    const overrideInput2 = page.getByTestId('cell-invoice-month-2001-input');
    await overrideInput2.fill('');
    await overrideInput2.press('Enter');

    // Wait for update
    await page.waitForTimeout(500);

    // invoice_month_final should now show invoice_month_auto (2026-04, from due_date)
    await expect(invoiceMonthCell).toContainText('2026-04');
  });

  test('invoice_month_auto updates when due_date changes but override takes precedence', async ({ page }) => {
    let currentReviewItems = [
      {
        review_id: 3001,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-10',
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_override: '2026-03',
        invoice_month_auto: '2026-01',
        invoice_month_final: '2026-03',
        invoice_batch_id: null,
        billing_amount: 5000,
        is_billed: false,
      },
    ];

    await setupMocks(page, currentReviewItems);

    await page.route('**/api/projects/1/services/55/reviews/3001', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();

      if (postData.due_date) {
        const newDueDate = postData.due_date;
        const newAutoMonth = newDueDate.slice(0, 7);

        // invoice_month_auto updates, but invoice_month_final stays on override
        currentReviewItems[0] = {
          ...currentReviewItems[0],
          due_date: newDueDate,
          invoice_month_auto: newAutoMonth,
          // invoice_month_final still uses override
          invoice_month_final: currentReviewItems[0].invoice_month_override || newAutoMonth,
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(currentReviewItems[0]),
        });
      }
    });

    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: /Deliverables/i }).click();

    const deliverablesTab = page.getByTestId('project-workspace-v2-reviews');
    await expect(deliverablesTab).toBeVisible();

    // Initial: override = 2026-03, auto = 2026-01, final = 2026-03
    const row3001 = deliverablesTab.getByTestId('deliverable-row-3001');
    await expect(row3001).toBeVisible();

    const invoiceMonthCell = row3001.getByTestId('cell-invoice-month-3001');
    await expect(invoiceMonthCell).toContainText('2026-03');

    // Change due_date to 2026-05-15 → auto becomes 2026-05, but final stays 2026-03
    const dueDateCell = row3001.getByTestId('cell-due-3001');
    await dueDateCell.click();

    const dueDateInput = page.getByTestId('cell-due-3001-input');
    await dueDateInput.fill('2026-05-15');
    await dueDateInput.press('Enter');

    await page.waitForTimeout(500);

    // invoice_month_final should still be 2026-03 (override preserved)
    await expect(invoiceMonthCell).toContainText('2026-03');

    // Verify notification tells user auto was updated but override was preserved
    const snackbar = page.getByTestId('invoice-month-notification');
    await expect(snackbar).toBeVisible();
    await expect(snackbar).toContainText(/invoice month auto-calculated to.*2026-05.*override.*2026-03/i);
  });
});
