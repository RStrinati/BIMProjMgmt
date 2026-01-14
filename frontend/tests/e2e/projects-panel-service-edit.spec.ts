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

const seedUsers = [{ user_id: 101, name: 'Alex Lead' }];

const baseProjectDetails = (projectId: number) => {
  const base = seedProjects.find((project) => project.project_id === projectId);
  return {
    project_id: projectId,
    project_name: base?.project_name || `Project ${projectId}`,
    project_number: base?.project_number || `P-${projectId}`,
    client_name: base?.client_name || 'Mock Client',
    status: base?.status || 'Active',
    internal_lead: base?.internal_lead ?? null,
    project_type: base?.project_type || 'Data Center',
  };
};

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
  {
    service_id: 102,
    project_id: 1,
    service_code: 'SVC-002',
    service_name: 'QA Reviews',
    phase: 'Phase 2',
    status: 'overdue',
    progress_pct: 0,
    agreed_fee: 80000,
  },
];

const setupMocks = async (page: any, options?: { forcePatchFailure?: boolean }) => {
  const services = seedServices.map((service) => ({ ...service }));

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

  await page.route('**/api/users', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedUsers),
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
        body: JSON.stringify(services),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+\/services\/\d+/, async (route) => {
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
      await new Promise((resolve) => setTimeout(resolve, 300));
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

test.describe('Projects panel service status edit', () => {
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

    const statusSelect = page.getByTestId('projects-panel-service-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'In progress' }).click();

    await expect(statusSelect).toContainText('In progress');
    await expect(page.getByTestId('projects-panel-service-row-101')).toContainText('Status: In progress');
    await expect(page.getByTestId('projects-panel-service-save-error')).toHaveCount(0);
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

    const statusSelect = page.getByTestId('projects-panel-service-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(page.getByTestId('projects-panel-service-save-error')).toBeVisible();
    await expect(statusSelect).toContainText('Planned');
    await expect(page.getByTestId('projects-panel-service-row-101')).toContainText('Status: Planned');
  });
});
