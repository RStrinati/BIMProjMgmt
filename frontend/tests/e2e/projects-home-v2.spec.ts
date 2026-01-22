import { test, expect } from '@playwright/test';

const seedProjects = [
  {
    project_id: 1,
    project_name: 'Alpha Build',
    project_number: 'P-001',
    client_name: 'Client A',
    status: 'Active',
    internal_lead: 101,
    updated_at: '2024-05-10T10:00:00Z',
    health_pct: 82,
    end_date: '2024-08-01',
  },
  {
    project_id: 2,
    project_name: 'Beta Tower',
    project_number: 'P-002',
    client_name: 'Client B',
    status: 'On Hold',
    internal_lead: 102,
    updated_at: '2024-05-15T10:00:00Z',
    health_pct: 45,
    end_date: '2024-12-10',
  },
];

const timelinePayload = {
  projects: [
    {
      project_id: 1,
      project_name: 'Alpha Build',
      start_date: '2024-01-01',
      end_date: '2024-02-15',
      project_manager: 'Jordan Lead',
      client_name: 'Client A',
      project_type: 'Data Center',
      review_items: [],
    },
  ],
};

const setupMocks = async (page: any) => {
  await page.route('**/api/projects/summary**', async (route) => {
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

  await page.route('**/api/projects/aggregates**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_count: seedProjects.length,
        sum_agreed_fee: 100000,
        sum_billed_to_date: 25000,
        sum_unbilled_amount: 75000,
        sum_earned_value: 30000,
        weighted_earned_value_pct: 30,
      }),
    });
  });

  await page.route('**/api/dashboard/timeline**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(timelinePayload),
    });
  });

  await page.route('**/api/projects/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(seedProjects[0]),
    });
  });

  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/projects/1/issues/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ summary: { total_issues: 0 } }),
    });
  });

  await page.route('**/api/projects/1/services**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
};

test.describe('Projects home v2 (flagged)', () => {
  test('switches display modes, persists, and navigates to project detail', async ({ page }) => {
    await page.addInitScript(() => {
      const initKey = '__projects_home_v2_init';
      if (!window.localStorage.getItem(initKey)) {
        window.localStorage.clear();
        window.localStorage.setItem(initKey, 'true');
      }
      window.localStorage.setItem('ff_projects_home_v2', 'true');
      window.localStorage.setItem('ff_linear_timeline', 'true');
    });
    await setupMocks(page);

    await page.goto('/projects');

    await expect(page.getByTestId('projects-home-v2-root')).toBeVisible();
    await expect(page.getByTestId('projects-home-display-mode')).toBeVisible();

    await page.getByTestId('projects-home-search').fill('Alpha');
    await expect(page.getByTestId('projects-home-list-row-1')).toBeVisible();

    await page.getByRole('button', { name: 'Timeline' }).click();
    await expect(page.getByTestId('linear-timeline-panel')).toBeVisible();

    await page.reload();
    await expect(page.getByRole('button', { name: 'Timeline' })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByTestId('projects-home-search')).toHaveValue('Alpha');

    await page.getByRole('button', { name: 'List' }).click();
    await page.getByTestId('projects-home-list-row-1').click();
    await expect(page).toHaveURL(/\/projects\/1$/);
  });
});
