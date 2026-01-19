import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Filter Test Project',
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
        billed_to_date: 20000,
        earned_value: 20000,
        earned_value_pct: 20,
        invoice_pipeline: [],
        ready_this_month: { month: '2026-01', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
      }),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Deliverables Filters', () => {
  test('Due this month filter shows only current month deliverables', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM
    const nextMonth = new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 101,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: `${currentMonth}-05`,
        due_date: `${currentMonth}-10`,
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: false,
      },
      {
        review_id: 102,
        service_id: 55,
        project_id: 1,
        cycle_no: 2,
        planned_date: `${nextMonth}-05`,
        due_date: `${nextMonth}-15`,
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: nextMonth,
        invoice_batch_id: null,
        is_billed: false,
      },
      {
        review_id: 103,
        service_id: 55,
        project_id: 1,
        cycle_no: 3,
        planned_date: `${currentMonth}-20`,
        due_date: `${currentMonth}-25`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: false,
      },
    ];

    await setupMocks(page, reviewItems);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Initially all 3 deliverables visible
    await expect(page.getByTestId('deliverable-row-101')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-102')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-103')).toBeVisible();

    // Apply "Due this month" filter
    await page.getByRole('button', { name: /due this month/i }).click();

    // Only current month deliverables (101, 103) should be visible
    await expect(page.getByTestId('deliverable-row-101')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-102')).not.toBeVisible();
    await expect(page.getByTestId('deliverable-row-103')).toBeVisible();

    // Clear filter
    await page.getByRole('button', { name: /due this month/i }).click();
    await expect(page.getByTestId('deliverable-row-102')).toBeVisible();
  });

  test('Unbatched filter shows only deliverables without batch assignment', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 201,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: `${currentMonth}-05`,
        due_date: `${currentMonth}-10`,
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null, // Unbatched
        is_billed: false,
      },
      {
        review_id: 202,
        service_id: 55,
        project_id: 1,
        cycle_no: 2,
        planned_date: `${currentMonth}-12`,
        due_date: `${currentMonth}-15`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: 9001, // Batched
        is_billed: false,
      },
      {
        review_id: 203,
        service_id: 55,
        project_id: 1,
        cycle_no: 3,
        planned_date: `${currentMonth}-20`,
        due_date: `${currentMonth}-25`,
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null, // Unbatched
        is_billed: false,
      },
    ];

    await setupMocks(page, reviewItems);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Initially all 3 visible
    await expect(page.getByTestId('deliverable-row-201')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-202')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-203')).toBeVisible();

    // Apply "Unbatched" filter
    await page.getByRole('button', { name: /unbatched/i }).click();

    // Only unbatched deliverables (201, 203) should be visible
    await expect(page.getByTestId('deliverable-row-201')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-202')).not.toBeVisible();
    await expect(page.getByTestId('deliverable-row-203')).toBeVisible();

    // Clear filter
    await page.getByRole('button', { name: /unbatched/i }).click();
    await expect(page.getByTestId('deliverable-row-202')).toBeVisible();
  });

  test('Ready to invoice filter shows only completed unbilled deliverables', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 301,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: `${currentMonth}-05`,
        due_date: `${currentMonth}-10`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: false, // Ready to invoice
      },
      {
        review_id: 302,
        service_id: 55,
        project_id: 1,
        cycle_no: 2,
        planned_date: `${currentMonth}-12`,
        due_date: `${currentMonth}-15`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: true, // Already billed
      },
      {
        review_id: 303,
        service_id: 55,
        project_id: 1,
        cycle_no: 3,
        planned_date: `${currentMonth}-20`,
        due_date: `${currentMonth}-25`,
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: false, // Not completed yet
      },
    ];

    await setupMocks(page, reviewItems);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Initially all 3 visible
    await expect(page.getByTestId('deliverable-row-301')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-302')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-303')).toBeVisible();

    // Apply "Ready to invoice" filter
    await page.getByRole('button', { name: /ready to invoice/i }).click();

    // Only completed + unbilled (301) should be visible
    await expect(page.getByTestId('deliverable-row-301')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-302')).not.toBeVisible();
    await expect(page.getByTestId('deliverable-row-303')).not.toBeVisible();

    // Clear filter
    await page.getByRole('button', { name: /ready to invoice/i }).click();
    await expect(page.getByTestId('deliverable-row-302')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-303')).toBeVisible();
  });

  test('Multiple filters work together (AND logic)', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    const nextMonth = new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 401,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: `${currentMonth}-05`,
        due_date: `${currentMonth}-10`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: null,
        is_billed: false, // Matches all filters
      },
      {
        review_id: 402,
        service_id: 55,
        project_id: 1,
        cycle_no: 2,
        planned_date: `${nextMonth}-05`,
        due_date: `${nextMonth}-15`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: nextMonth,
        invoice_batch_id: null,
        is_billed: false, // Not due this month
      },
      {
        review_id: 403,
        service_id: 55,
        project_id: 1,
        cycle_no: 3,
        planned_date: `${currentMonth}-20`,
        due_date: `${currentMonth}-25`,
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: currentMonth,
        invoice_batch_id: 9001,
        is_billed: false, // Is batched
      },
    ];

    await setupMocks(page, reviewItems);
    await page.goto('/workspace/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Apply all three filters
    await page.getByRole('button', { name: /due this month/i }).click();
    await page.getByRole('button', { name: /unbatched/i }).click();
    await page.getByRole('button', { name: /ready to invoice/i }).click();

    // Only deliverable matching ALL filters (401) should be visible
    await expect(page.getByTestId('deliverable-row-401')).toBeVisible();
    await expect(page.getByTestId('deliverable-row-402')).not.toBeVisible();
    await expect(page.getByTestId('deliverable-row-403')).not.toBeVisible();
  });
});
