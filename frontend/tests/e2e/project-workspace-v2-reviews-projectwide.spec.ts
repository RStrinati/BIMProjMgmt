import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
};

const projectReviewsPayload = {
  items: [
    {
      review_id: 101,
      service_id: 55,
      project_id: 1,
      cycle_no: 1,
      planned_date: '2024-05-10',
      due_date: '2024-05-20',
      status: 'planned',
      disciplines: 'Architecture',
      deliverables: 'Model',
      is_billed: false,
      billing_amount: 0,
      invoice_reference: null,
      invoice_date: null,
      service_name: 'Design Review',
      service_code: 'DR-01',
      phase: 'Concept',
    },
  ],
  total: 1,
};

const setupMocks = async (page: any) => {
  await page.route('**/api/project/1', async (route) => {
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

  await page.route('**/api/projects/1/items**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });
};

test.describe('Workspace v2 project-wide reviews', () => {
  test('renders reviews and handles status updates with rollback', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    let patchCount = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      patchCount += 1;
      if (patchCount === 1) {
        projectReviewsPayload.items[0].status = 'completed';
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
      } else {
        await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'fail' }) });
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    const reviewRow = page.getByTestId('project-workspace-v2-review-row-101');
    await expect(reviewRow).toBeVisible();
    await expect(reviewRow).toContainText('DR-01');

    const statusSelect = reviewRow.getByTestId('projects-panel-review-status-select');
    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();
    await expect(statusSelect).toHaveText('Completed');

    await statusSelect.click();
    await page.getByRole('option', { name: 'Overdue' }).click();
    await expect(page.getByTestId('project-workspace-v2-reviews-error')).toBeVisible();
    await expect(statusSelect).toHaveText('Completed');

    const allowedErrors = [
      'Failed to load resource: the server responded with a status of 500',
      'API Error: 500',
    ];
    const unexpected = consoleErrors.filter(
      (message) => !allowedErrors.some((allowed) => message.includes(allowed)),
    );
    expect(unexpected).toEqual([]);
  });
});
