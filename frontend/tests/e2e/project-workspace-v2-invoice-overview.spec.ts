import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Overview Pipeline Test Project',
  status: 'active',
};

const setupMocks = async (page: any, reviewItems: any[], financeGrid: any) => {
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
      body: JSON.stringify(financeGrid),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Overview Invoice Pipeline', () => {
  test('overview pipeline shows aggregated counts and amounts by invoice_month_final', async ({ page }) => {
    const reviewItems = [
      {
        review_id: 901,
        service_id: 55,
        project_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-10',
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-01',
        invoice_batch_id: null,
        billing_amount: 5000,
        is_billed: false,
      },
      {
        review_id: 902,
        service_id: 55,
        project_id: 1,
        cycle_no: 2,
        planned_date: '2026-01-15',
        due_date: '2026-01-20',
        status: 'completed',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-01',
        invoice_batch_id: null,
        billing_amount: 3000,
        is_billed: false,
      },
      {
        review_id: 903,
        service_id: 55,
        project_id: 1,
        cycle_no: 3,
        planned_date: '2026-02-05',
        due_date: '2026-02-10',
        status: 'planned',
        service_name: 'Design Review',
        service_code: 'DR-01',
        phase: 'Concept',
        invoice_month_final: '2026-02',
        invoice_batch_id: null,
        billing_amount: 7000,
        is_billed: false,
      },
    ];

    const financeGrid = {
      project_id: 1,
      agreed_fee: 100000,
      billed_to_date: 20000,
      earned_value: 20000,
      earned_value_pct: 20,
      invoice_pipeline: [
        { month: '2026-01', deliverables_count: 2, total_amount: 8000, ready_count: 2, ready_amount: 8000, issued_count: 0 },
        { month: '2026-02', deliverables_count: 1, total_amount: 7000, ready_count: 0, ready_amount: 0, issued_count: 0 },
        { month: '2026-03', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
        { month: '2026-04', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
        { month: '2026-05', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
        { month: '2026-06', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
      ],
      ready_this_month: { month: '2026-01', deliverables_count: 2, total_amount: 8000, ready_count: 2, ready_amount: 8000, issued_count: 0 },
    };

    await setupMocks(page, reviewItems, financeGrid);
    await page.goto('/workspace/1');

    // Should be on Overview tab by default
    await expect(page.getByTestId('project-workspace-v2-overview')).toBeVisible();

    // Verify invoice pipeline widget
    const pipelineWidget = page.getByTestId('project-workspace-v2-invoice-pipeline');
    await expect(pipelineWidget).toBeVisible();

    // Check 2026-01 entry: 2 deliverables, $8,000
    await expect(pipelineWidget.getByText('2026-01')).toBeVisible();
    await expect(pipelineWidget.getByText(/2 ·.*8,000/)).toBeVisible();

    // Check 2026-02 entry: 1 deliverable, $7,000
    await expect(pipelineWidget.getByText('2026-02')).toBeVisible();
    await expect(pipelineWidget.getByText(/1 ·.*7,000/)).toBeVisible();

    // Months with no deliverables should show 0
    await expect(pipelineWidget.getByText('2026-03')).toBeVisible();
    await expect(pipelineWidget.getByText(/0 ·.*0\.00/)).toBeVisible();
  });

  test('ready this month shows completed unbilled deliverables for current month', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 1001,
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
        billing_amount: 5000,
        is_billed: false, // Ready
      },
      {
        review_id: 1002,
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
        billing_amount: 3000,
        is_billed: true, // Already billed
      },
      {
        review_id: 1003,
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
        billing_amount: 2000,
        is_billed: false, // Not completed
      },
    ];

    const financeGrid = {
      project_id: 1,
      agreed_fee: 100000,
      billed_to_date: 20000,
      earned_value: 20000,
      earned_value_pct: 20,
      invoice_pipeline: [
        { month: currentMonth, deliverables_count: 3, total_amount: 10000, ready_count: 1, ready_amount: 5000, issued_count: 1 },
      ],
      ready_this_month: { month: currentMonth, deliverables_count: 3, total_amount: 10000, ready_count: 1, ready_amount: 5000, issued_count: 1 },
    };

    await setupMocks(page, reviewItems, financeGrid);
    await page.goto('/workspace/1');

    // Check "Ready this month" metric
    const pipelineWidget = page.getByTestId('project-workspace-v2-invoice-pipeline');
    await expect(pipelineWidget).toBeVisible();

    // Should show: 1 item (only completed + unbilled), $5,000
    await expect(pipelineWidget.getByText(/Ready this month/i)).toBeVisible();
    await expect(pipelineWidget.getByText(/1 items ·.*5,000/)).toBeVisible();
  });

  test('unbatched risk metric shows unbatched deliverables due current month', async ({ page }) => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    
    const reviewItems = [
      {
        review_id: 1101,
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
        invoice_batch_id: null, // Unbatched
        billing_amount: 5000,
        is_billed: false,
      },
      {
        review_id: 1102,
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
        billing_amount: 3000,
        is_billed: false,
      },
      {
        review_id: 1103,
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
        invoice_batch_id: null, // Unbatched but not ready
        billing_amount: 2000,
        is_billed: false,
      },
    ];

    const financeGrid = {
      project_id: 1,
      agreed_fee: 100000,
      billed_to_date: 20000,
      earned_value: 20000,
      earned_value_pct: 20,
      invoice_pipeline: [
        { month: currentMonth, deliverables_count: 3, total_amount: 10000, ready_count: 2, ready_amount: 8000, issued_count: 0 },
      ],
      ready_this_month: { month: currentMonth, deliverables_count: 3, total_amount: 10000, ready_count: 2, ready_amount: 8000, issued_count: 0 },
    };

    await setupMocks(page, reviewItems, financeGrid);
    await page.goto('/workspace/1');

    // Check "Unbatched risk" metric
    const pipelineWidget = page.getByTestId('project-workspace-v2-invoice-pipeline');
    await expect(pipelineWidget).toBeVisible();

    // Should show: 2 due this month unbatched (1101 and 1103), $7,000
    await expect(pipelineWidget.getByText(/Unbatched risk/i)).toBeVisible();
    const unbatchedRiskCount = page.getByTestId('unbatched-risk-count');
    await expect(unbatchedRiskCount).toContainText('2 due this month');
    await expect(unbatchedRiskCount).toContainText('7,000');
  });
});
