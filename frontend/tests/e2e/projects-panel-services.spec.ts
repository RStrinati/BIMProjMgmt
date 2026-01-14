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

const seedServices = [
  {
    service_id: 55,
    project_id: 1,
    service_code: 'BIM',
    service_name: 'Coordination Reviews',
    phase: 'Design',
    status: 'Active',
    progress_pct: 45,
    agreed_fee: 12000,
    created_at: '2024-01-01',
    updated_at: '2024-01-02',
  },
  {
    service_id: 56,
    project_id: 1,
    service_code: 'AUD',
    service_name: 'Milestone Audit',
    phase: 'Construction',
    status: 'Planned',
    progress_pct: 0,
    agreed_fee: 8000,
    created_at: '2024-01-03',
    updated_at: '2024-01-04',
  },
];

const baseProjectDetails = {
  project_id: 1,
  project_name: 'Mock Project Alpha',
  project_number: 'P-001',
  client_name: 'Mock Client',
  status: 'Active',
  internal_lead: 101,
  project_type: 'Data Center',
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
  description: 'Mock project for services tests',
};

test('projects panel services tab renders services list', async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('ff_projects_panel', 'true');
  });

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
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(baseProjectDetails),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/projects\/\d+\/services/, async (route) => {
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

  await page.goto('/projects');
  await expect(page.getByTestId('projects-panel-root')).toBeVisible();

  await page.getByTestId('projects-panel-list-row-1').click();
  await page.getByRole('tab', { name: 'Services' }).click();

  await expect(page.getByText('BIM - Coordination Reviews')).toBeVisible();
  await expect(page.getByText('AUD - Milestone Audit')).toBeVisible();
});
