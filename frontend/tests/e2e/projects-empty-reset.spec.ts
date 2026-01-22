import { test, expect } from '@playwright/test';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Alpha Build',
    project_number: 'P-001',
    client_name: 'Client A',
    status: 'active',
    internal_lead: 101,
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

  await page.route('**/api/users', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }
    await route.continue();
  });
};

test.describe('Projects panel empty reset', () => {
  test('shows reset banner when filters yield no results', async ({ page }) => {
    await page.addInitScript(() => {
      const initKey = '__projects_panel_empty_reset_init';
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

    await page.getByTestId('projects-panel-view-completed').click();

    await expect(page.getByTestId('projects-panel-empty-banner')).toBeVisible();
    await page.getByTestId('projects-panel-empty-reset').click();

    await expect(page.getByTestId('projects-panel-list-row-1')).toBeVisible();
  });
});
