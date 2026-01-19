import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
};

const reviewItem = {
  review_id: 101,
  service_id: 55,
  project_id: 1,
  cycle_no: 1,
  planned_date: '2026-01-05',
  due_date: '2026-01-10',
  status: 'planned',
  disciplines: 'Architecture',
  deliverables: 'Model',
  is_billed: false,
  billing_amount: 5000,
  invoice_reference: null,
  invoice_date: null,
  service_name: 'Design Review',
  service_code: 'DR-01',
  phase: 'Concept',
  invoice_month_override: null,
  invoice_month_auto: '2026-01',
  invoice_month_final: '2026-01',
  invoice_batch_id: null,
};

const projectReviewsPayload = {
  items: [reviewItem],
  total: 1,
};

const invoiceBatches: Array<any> = [];

const financeGridPayload = {
  project_id: 1,
  agreed_fee: 120000,
  billed_to_date: 24000,
  earned_value: 24000,
  earned_value_pct: 20,
  invoice_pipeline: [
    { month: '2026-01', deliverables_count: 1, total_amount: 5000, ready_count: 0, ready_amount: 0, issued_count: 0 },
    { month: '2026-02', deliverables_count: 1, total_amount: 5000, ready_count: 0, ready_amount: 0, issued_count: 0 },
    { month: '2026-03', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
    { month: '2026-04', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
    { month: '2026-05', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
    { month: '2026-06', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
  ],
  ready_this_month: { month: '2026-01', deliverables_count: 1, total_amount: 5000, ready_count: 0, ready_amount: 0, issued_count: 0 },
};

const setupMocks = async (page: any) => {
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
      body: JSON.stringify(projectReviewsPayload),
    });
  });

  await page.route('**/api/invoice_batches**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(invoiceBatches),
      });
      return;
    }
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      const newBatch = {
        invoice_batch_id: 2001,
        project_id: body.project_id,
        service_id: body.service_id ?? null,
        invoice_month: body.invoice_month,
        status: body.status ?? 'draft',
        title: body.title ?? null,
        notes: body.notes ?? null,
      };
      invoiceBatches.push(newBatch);
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ invoice_batch_id: newBatch.invoice_batch_id }),
      });
      return;
    }
    await route.fallback();
  });

  await page.route('**/api/projects/finance_grid**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(financeGridPayload),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Invoice month + batching', () => {
  test('derives invoice month, supports override + batching, and updates overview pipeline', async ({ page }) => {
    let patchCalls = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCalls += 1;
        const data = route.request().postDataJSON();
        if (data.due_date) {
          expect(data.due_date).toBe('2026-02-10');
          reviewItem.due_date = '2026-02-10';
          reviewItem.invoice_month_auto = '2026-02';
          reviewItem.invoice_month_final = '2026-02';
        }
        if (data.invoice_month_override) {
          expect(data.invoice_month_override).toBe('2026-03');
          reviewItem.invoice_month_override = '2026-03';
          reviewItem.invoice_month_final = '2026-03';
          financeGridPayload.invoice_pipeline = financeGridPayload.invoice_pipeline.map((row: any) =>
            row.month === '2026-03'
              ? { ...row, deliverables_count: 1, total_amount: 5000 }
              : row,
          );
        }
        if (data.invoice_batch_id) {
          reviewItem.invoice_batch_id = data.invoice_batch_id;
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(reviewItem),
        });
        return;
      }
      await route.fallback();
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    const invoiceMonthCell = page.getByTestId('cell-invoice-month-101');
    await expect(invoiceMonthCell).toBeVisible();
    await expect(invoiceMonthCell).toContainText('2026-01');

    const dueDateCell = page.getByTestId('cell-due-101');
    await dueDateCell.click();
    const dueInput = dueDateCell.locator('input[type="date"]');
    await dueInput.fill('2026-02-10');
    await dueInput.press('Enter');
    await expect(invoiceMonthCell).toContainText('2026-02');

    await invoiceMonthCell.click();
    const monthInput = invoiceMonthCell.locator('input[type="month"]');
    await monthInput.fill('2026-03');
    await monthInput.press('Enter');
    await expect(invoiceMonthCell).toContainText('2026-03');

    await page.reload();
    await page.getByRole('tab', { name: 'Deliverables' }).click();
    await expect(invoiceMonthCell).toContainText('2026-03');
    await expect(page.getByTestId('cell-due-101')).toContainText('2026-02-10');

    page.once('dialog', async (dialog) => {
      await dialog.accept('March batch');
    });
    const batchSelect = page.getByTestId('cell-invoice-batch-101');
    await batchSelect.click();
    await page.getByRole('option', { name: 'Create new batch' }).click();
    await expect(page.getByText('March batch')).toBeVisible();

    await page.getByRole('tab', { name: 'Overview' }).click();
    await expect(page.getByTestId('project-workspace-v2-invoice-pipeline')).toBeVisible();
    await expect(page.getByText(/2026-03/)).toBeVisible();

    expect(patchCalls).toBeGreaterThanOrEqual(3);
  });
});
