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
  {
    project_id: 2,
    project_name: 'Mock Project Beta',
    project_number: 'P-002',
    client_name: 'Mock Client 2',
    status: 'On Hold',
    internal_lead: 102,
    project_type: 'Infrastructure',
  },
];

const seedUsers = [
  { user_id: 101, name: 'Alex Lead' },
  { user_id: 102, name: 'Jordan Lead' },
  { user_id: 103, name: 'Casey Lead' },
];

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
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    area_hectares: 12,
    mw_capacity: 5,
    naming_convention: 'ISO',
    address: '123 Mock St',
    city: 'Sydney',
    state: 'NSW',
    postcode: '2000',
    folder_path: 'C:\\Projects\\Mock',
    ifc_folder_path: 'C:\\Projects\\Mock\\IFC',
    description: 'Mock project for tests',
  };
};

const setupMocks = async (page: any, options?: { forcePutFailure?: boolean; updatedStatus?: string }) => {
  const updatedStatus = options?.updatedStatus || 'Completed';
  const projects = seedProjects.map((project) => ({ ...project }));

  await page.route('**/api/projects', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(projects),
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
      const current = projects.find((project) => project.project_id === id);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...baseProjectDetails(id),
          status: current?.status ?? baseProjectDetails(id).status,
          internal_lead: current?.internal_lead ?? baseProjectDetails(id).internal_lead,
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+/, async (route) => {
    if (route.request().method() === 'PUT') {
      if (options?.forcePutFailure) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Simulated failure' }),
        });
        return;
      }
      const url = route.request().url();
      const id = Number(url.split('/').pop());
      const payload = (await route.request().postDataJSON()) as Record<string, any>;
      const base = baseProjectDetails(id);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...base,
          ...payload,
          status: payload.status ?? updatedStatus,
        }),
      });
      const index = projects.findIndex((project) => project.project_id === id);
      if (index >= 0) {
        projects[index] = {
          ...projects[index],
          ...payload,
          status: payload.status ?? updatedStatus,
        };
      }
      return;
    }
    await route.continue();
  });
};

test.describe('Projects panel inline edit', () => {
  test('happy path updates status and reflects in detail page', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_projects_panel', 'true');
    });
    await setupMocks(page, { updatedStatus: 'Completed' });

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();

    const row = page.getByTestId('projects-panel-list-row-1');
    await row.click();

    const statusSelect = page.getByTestId('projects-panel-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(statusSelect).toContainText('Completed');

    const openButton = page.getByRole('button', { name: 'Open full project' });
    await openButton.click();
    await expect(page).toHaveURL(/\/projects\/\d+/);
    await expect(page.getByRole('heading', { name: 'Mock Project Alpha' })).toBeVisible();
    await expect(page.getByText('Completed').first()).toBeVisible();
  });

  test('rollback on failed status update', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_projects_panel', 'true');
    });
    await setupMocks(page, { forcePutFailure: true });

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();

    const row = page.getByTestId('projects-panel-list-row-1');
    await row.click();

    const statusSelect = page.getByTestId('projects-panel-status-select');
    await expect(statusSelect).toBeVisible();

    await statusSelect.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await expect(page.getByTestId('projects-panel-save-error')).toBeVisible();
    await expect(statusSelect).toContainText('Active');
  });
});
