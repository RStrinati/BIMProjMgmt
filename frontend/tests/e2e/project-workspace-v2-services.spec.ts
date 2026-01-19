import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
};

const seedServices = [
  {
    service_id: 55,
    project_id: 1,
    service_code: 'SVC-01',
    service_name: 'Coordination',
    phase: 'Design',
    status: 'planned',
    progress_pct: 25,
    agreed_fee: 12000,
  },
  {
    service_id: 56,
    project_id: 1,
    service_code: 'SVC-02',
    service_name: 'Audit',
    phase: 'Construction',
    status: 'in_progress',
    progress_pct: 50,
    agreed_fee: 8000,
  },
];

const setupMocks = async (page: any, options?: { forcePatchFailure?: boolean }) => {
  const services = seedServices.map((service) => ({ ...service }));

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
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });

  await page.route('**/api/projects/1/items**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });

  await page.route('**/api/projects/1/services**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(services),
      });
      return;
    }
    await route.continue();
  });

  await page.route('**/api/projects/1/services/*', async (route) => {
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
      const serviceId = Number(url.split('/').pop());
      const payload = (await route.request().postDataJSON()) as Record<string, any>;
      const index = services.findIndex((service) => service.service_id === serviceId);
      if (index >= 0) {
        services[index] = { ...services[index], ...payload };
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

test.describe('Workspace v2 services tab', () => {
  test('renders list and persists status updates', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();
    await expect(page.getByTestId('project-workspace-v2-service-row-55')).toBeVisible();
    await expect(page.getByTestId('project-workspace-v2-service-row-56')).toBeVisible();

    await page.getByTestId('project-workspace-v2-service-row-55').click();
    const statusSelect = page.getByTestId('projects-panel-service-status-select');
    await statusSelect.click();
    await page.getByRole('option', { name: 'In progress' }).click();

    await expect(statusSelect).toContainText('In progress');
    await expect(page.getByTestId('project-workspace-v2-service-row-55')).toContainText('Status: In progress');
    await expect(page.getByTestId('project-workspace-v2-service-save-error')).toHaveCount(0);

    expect(consoleErrors).toEqual([]);
  });

  test('rolls back on failed status update', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page, { forcePatchFailure: true });
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();
    await page.getByTestId('project-workspace-v2-service-row-55').click();

    const statusSelect = page.getByTestId('projects-panel-service-status-select');
    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(page.getByTestId('project-workspace-v2-service-save-error')).toBeVisible();
    await expect(statusSelect).toContainText('Planned');
    await expect(page.getByTestId('project-workspace-v2-service-row-55')).toContainText('Status: Planned');
  });
});
