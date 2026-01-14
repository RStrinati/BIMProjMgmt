import { test, expect } from '@playwright/test';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Alpha Build',
    project_number: 'P-001',
    client_name: 'Client A',
    status: 'active',
    internal_lead: 101,
    updated_at: '2024-05-10T10:00:00Z',
  },
  {
    project_id: 2,
    project_name: 'Beta Tower',
    project_number: 'P-002',
    client_name: 'Client B',
    status: 'on_hold',
    internal_lead: 102,
    updated_at: '2024-05-15T10:00:00Z',
  },
  {
    project_id: 3,
    project_name: 'Gamma Park',
    project_number: 'P-003',
    client_name: 'Client C',
    status: 'completed',
    internal_lead: 101,
    updated_at: '2024-04-01T10:00:00Z',
  },
  {
    project_id: 4,
    project_name: 'Delta Yard',
    project_number: 'P-004',
    client_name: 'Client D',
    status: 'cancelled',
    internal_lead: 103,
    updated_at: '2024-05-01T10:00:00Z',
  },
];

const setupMocks = async (page: any) => {
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
};

test.describe('Projects panel views', () => {
  test('switching views filters rows and persists after reload', async ({ page }) => {
    await page.addInitScript(() => {
      const initKey = '__projects_panel_views_init';
      if (!window.localStorage.getItem(initKey)) {
        window.localStorage.clear();
        window.localStorage.setItem(initKey, 'true');
      }
      window.localStorage.setItem('ff_projects_panel', 'true');
      window.localStorage.setItem('current_user_id', '101');
    });
    await setupMocks(page);

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();

    await expect(page.getByTestId('projects-panel-list-row-1')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-2')).toBeVisible();

    await page.getByTestId('projects-panel-view-active').click();
    await expect(page.getByTestId('projects-panel-list-row-1')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-2')).toHaveCount(0);
    await expect(page.getByTestId('projects-panel-list-row-3')).toHaveCount(0);

    await page.getByTestId('projects-panel-view-completed').click();
    await expect(page.getByTestId('projects-panel-list-row-3')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-1')).toHaveCount(0);

    await page.getByTestId('projects-panel-view-my_work').click();
    await expect(page.getByTestId('projects-panel-list-row-1')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-3')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-2')).toHaveCount(0);

    const searchInput = page.getByPlaceholder('Search projects...');
    await page.getByTestId('projects-panel-view-on_hold').click();
    await searchInput.fill('Beta');

    await page.reload();
    await expect(page.getByTestId('projects-panel-view-on_hold')).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByPlaceholder('Search projects...')).toHaveValue('Beta');
    await expect(page.getByTestId('projects-panel-list-row-2')).toBeVisible();
    await expect(page.getByTestId('projects-panel-list-row-1')).toHaveCount(0);
  });
});
