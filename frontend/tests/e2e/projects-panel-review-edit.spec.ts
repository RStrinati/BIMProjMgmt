import { test, expect } from '@playwright/test';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Mock Project Alpha',
    project_number: 'P-001',
    client_name: 'Mock Client',
    status: 'Active',
    internal_lead: 101,
    project_type: 'Data Center',
  },
];

const baseProjectDetails = (projectId: number) => ({
  project_id: projectId,
  project_name: 'Mock Project Alpha',
  project_number: 'P-001',
  client_name: 'Mock Client',
  status: 'Active',
  internal_lead: 101,
  project_type: 'Data Center',
});

const seedServices = [
  {
    service_id: 101,
    project_id: 1,
    service_code: 'SVC-001',
    service_name: 'Design Coordination',
    phase: 'Phase 1',
    status: 'planned',
    progress_pct: 25,
    agreed_fee: 120000,
  },
];

const seedReviews = [
  {
    review_id: 201,
    service_id: 101,
    cycle_no: 1,
    planned_date: '2024-02-01',
    due_date: '2024-02-05',
    disciplines: 'Architecture',
    deliverables: 'Model update',
    status: 'planned',
    is_billed: false,
  },
  {
    review_id: 202,
    service_id: 101,
    cycle_no: 2,
    planned_date: '2024-03-01',
    due_date: '2024-03-05',
    disciplines: 'MEP',
    deliverables: 'QA report',
    status: 'in_progress',
    is_billed: true,
  },
];

const setupMocks = async (page: any, options?: { forcePatchFailure?: boolean }) => {
  const reviews = seedReviews.map((review) => ({ ...review }));

  await page.route('**/api/projects', async (route) => {
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

  await page.route(/.*\/api\/project\/\d+/, async (route) => {
    if (route.request().method() === 'GET') {
      const url = route.request().url();
      const id = Number(url.split('/').pop());
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(baseProjectDetails(id)),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+\/services$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedServices),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+\/services\/\d+\/reviews$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(reviews),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+\/services\/\d+\/reviews\/\d+/, async (route) => {
    if (route.request().method() === 'PATCH') {
      if (options?.forcePatchFailure) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Simulated failure' }),
        });
        return;
      }
      const url = route.request().url();
      const reviewId = Number(url.split('/').pop());
      const payload = (await route.request().postDataJSON()) as Record<string, any>;
      const index = reviews.findIndex((review) => review.review_id === reviewId);
      if (index >= 0) {
        reviews[index] = { ...reviews[index], ...payload };
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
      return;
    }
    await route.continue();
  });
};

test.describe('Projects panel review status edit', () => {
  test('optimistic update and success persists status', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_projects_panel', 'true');
    });
    await setupMocks(page);

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();

    await page.getByTestId('projects-panel-list-row-1').click();
    await page.getByRole('tab', { name: 'Services' }).click();

    await page.getByTestId('projects-panel-service-row-101').click();
    await page.getByTestId('projects-panel-review-row-201').click();

    const statusSelect = page.getByTestId('projects-panel-review-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(statusSelect).toContainText('Completed');
    await expect(page.getByTestId('projects-panel-review-row-201')).toContainText('Completed');
    await expect(page.getByTestId('projects-panel-review-save-error')).toHaveCount(0);
  });

  test('rollback on failed status update', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_projects_panel', 'true');
    });
    await setupMocks(page, { forcePatchFailure: true });

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();

    await page.getByTestId('projects-panel-list-row-1').click();
    await page.getByRole('tab', { name: 'Services' }).click();

    await page.getByTestId('projects-panel-service-row-101').click();
    await page.getByTestId('projects-panel-review-row-201').click();

    const statusSelect = page.getByTestId('projects-panel-review-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(page.getByTestId('projects-panel-review-save-error')).toBeVisible();
    await expect(statusSelect).toContainText('Planned');
    await expect(page.getByTestId('projects-panel-review-row-201')).toContainText('Planned');
  });
});
