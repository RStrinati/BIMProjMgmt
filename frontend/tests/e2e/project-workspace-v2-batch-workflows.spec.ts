import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Batch Workflow Test Project',
  status: 'active',
};

const setupMocks = async (page: any, reviewItems: any[], batches: any[]) => {
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
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(batches),
      });
      return;
    }
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      const newBatch = {
        invoice_batch_id: 9999,
        project_id: body.project_id,
        service_id: body.service_id ?? null,
        invoice_month: body.invoice_month,
        status: body.status ?? 'draft',
        title: body.title ?? null,
        notes: body.notes ?? null,
      };
      batches.push(newBatch);
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ invoice_batch_id: newBatch.invoice_batch_id }),
      });
      return;
    }
    await route.fallback();
  });

  let patchCallCount = 0;
  await page.route('**/api/projects/1/services/55/reviews/**', async (route) => {
    if (route.request().method() === 'PATCH') {
      patchCallCount += 1;
      const data = route.request().postDataJSON();
      const reviewId = parseInt(route.request().url().split('/').pop() || '0', 10);
      const review = reviewItems.find((r) => r.review_id === reviewId);
      if (review && data.invoice_batch_id !== undefined) {
        review.invoice_batch_id = data.invoice_batch_id;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(review || {}),
      });
      return;
    }
    await route.fallback();
  });

  await page.route('**/api/projects/finance_grid**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_id: 1,
        agreed_fee: 100000,
        billed_to_date: 20000,
        earned_value: 20000,
        earned_value_pct: 20,
        invoice_pipeline: [],
        ready_this_month: { month: '2026-01', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
      }),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Batch Workflows', () => {
  test('batch dropdown is disabled when no invoice month is set', async ({ page }) => {
    const reviewItems = [
      {
        review_id: 501,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: null, // No due date = no invoice month
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: null,
        invoice_month_auto: null,
        invoice_batch_id: null,
        is_billed: false,
      },
    ];

    await setupMocks(page, reviewItems, []);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Batch dropdown should be disabled
    const batchSelect = page.getByTestId('cell-invoice-batch-501').locator('..').locator('input');
    await expect(batchSelect).toBeDisabled();
    
    // Dropdown should show "Set invoice month" message
    await expect(page.getByText('Set invoice month')).toBeVisible();
  });

  test('batch dropdown shows only batches matching the deliverable invoice month', async ({ page }) => {
    const reviewItems = [
      {
        review_id: 601,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-10',
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-01',
        invoice_month_auto: '2026-01',
        invoice_batch_id: null,
        is_billed: false,
      },
    ];

    const batches = [
      {
        invoice_batch_id: 2001,
        project_id: 1,
        service_id: null,
        invoice_month: '2026-01',
        status: 'draft',
        title: 'January Batch',
        notes: null,
      },
      {
        invoice_batch_id: 2002,
        project_id: 1,
        service_id: null,
        invoice_month: '2026-02',
        status: 'draft',
        title: 'February Batch',
        notes: null,
      },
      {
        invoice_batch_id: 2003,
        project_id: 1,
        service_id: 55,
        invoice_month: '2026-01',
        status: 'draft',
        title: 'January Service Batch',
        notes: null,
      },
    ];

    await setupMocks(page, reviewItems, batches);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Click batch dropdown
    const batchSelect = page.getByTestId('cell-invoice-batch-601');
    await batchSelect.click();

    // Should show batches for 2026-01 only (2001, 2003)
    await expect(page.getByRole('option', { name: /January Batch/ })).toBeVisible();
    await expect(page.getByRole('option', { name: /January Service Batch/ })).toBeVisible();
    
    // February batch should NOT be visible (different month)
    await expect(page.getByRole('option', { name: /February Batch/ })).not.toBeVisible();
  });

  test('batch dropdown shows helper text when no batches exist for invoice month', async ({ page }) => {
    const reviewItems = [
      {
        review_id: 701,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-03-05',
        due_date: '2026-03-10',
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-03',
        invoice_month_auto: '2026-03',
        invoice_batch_id: null,
        is_billed: false,
      },
    ];

    const batches = [
      {
        invoice_batch_id: 2001,
        project_id: 1,
        service_id: null,
        invoice_month: '2026-01',
        status: 'draft',
        title: 'January Batch',
        notes: null,
      },
    ];

    await setupMocks(page, reviewItems, batches);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Click batch dropdown
    const batchSelect = page.getByTestId('cell-invoice-batch-701');
    await batchSelect.click();

    // Should show helper text since no batches exist for 2026-03
    await expect(page.getByText(/No batches for 2026-03/i)).toBeVisible();
    await expect(page.getByText(/Create first batch/i)).toBeVisible();
  });

  test('creating a batch via "Create new batch" option works', async ({ page }) => {
    const reviewItems = [
      {
        review_id: 801,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-10',
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-01',
        invoice_month_auto: '2026-01',
        invoice_batch_id: null,
        is_billed: false,
      },
    ];

    const batches: any[] = [];

    await setupMocks(page, reviewItems, batches);
    
    // Mock the window.prompt for batch title
    await page.addInitScript(() => {
      window.prompt = () => 'Test Batch Title';
    });

    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Click batch dropdown
    const batchSelect = page.getByTestId('cell-invoice-batch-801');
    await batchSelect.click();

    // Click "Create new batch" option
    await page.getByRole('option', { name: /Create new batch/i }).click();

    // Wait for batch creation and assignment
    await page.waitForTimeout(500);

    // Verify batch was created and assigned
    // The dropdown should now show the new batch title
    await expect(page.getByText('Test Batch Title')).toBeVisible();
  });
});
