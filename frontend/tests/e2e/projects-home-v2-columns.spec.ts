import { test, expect } from '@playwright/test';

const projectsAll = [
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
    agreed_fee: 100000,
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
    agreed_fee: 50000,
  },
];

const projectsActive = [projectsAll[0]];

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
    const url = new URL(route.request().url());
    const viewId = url.searchParams.get('viewId');
    const payload = viewId === 'active' ? projectsActive : projectsAll;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });

  await page.route('**/api/projects/aggregates**', async (route) => {
    const url = new URL(route.request().url());
    const viewId = url.searchParams.get('viewId');
    const aggregate =
      viewId === 'active'
        ? {
            project_count: 1,
            sum_agreed_fee: 100000,
            sum_billed_to_date: 25000,
            sum_unbilled_amount: 75000,
            sum_earned_value: 30000,
            weighted_earned_value_pct: 30,
          }
        : {
            project_count: 2,
            sum_agreed_fee: 150000,
            sum_billed_to_date: 40000,
            sum_unbilled_amount: 110000,
            sum_earned_value: 50000,
            weighted_earned_value_pct: 33,
          };
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(aggregate),
    });
  });

  await page.route('**/api/dashboard/timeline**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(timelinePayload),
    });
  });

  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
};

test.describe('Projects home v2 columns/totals', () => {
  test('column visibility persists across reloads', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('ff_projects_home_v2', 'true');
    });
    await setupMocks(page);

    await page.goto('/projects');

    await page.getByTestId('projects-columns-button').click();
    await page.getByRole('checkbox', { name: 'Agreed Fee' }).check();
    await page.keyboard.press('Escape');

    await expect(page.getByRole('columnheader', { name: 'Agreed Fee' })).toBeVisible();

    await page.reload();
    await expect(page.getByRole('columnheader', { name: 'Agreed Fee' })).toBeVisible();
  });

  test('column ordering persists across reloads', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('ff_projects_home_v2', 'true');
    });
    await setupMocks(page);

    await page.goto('/projects');

    const readHeaders = async () =>
      page.$$eval('[data-testid=\"projects-list-table\"] thead th', (ths) =>
        ths.map((th) => th.textContent?.trim()),
      );

    const original = await readHeaders();
    await page.getByTestId('projects-columns-button').click();
    await page.getByLabel('move-down-status').click();
    await page.keyboard.press('Escape');

    const updated = await readHeaders();
    expect(updated).not.toEqual(original);

    await page.reload();
    const reloaded = await readHeaders();
    expect(reloaded).toEqual(updated);
  });

  test('totals footer reflects view filters', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('ff_projects_home_v2', 'true');
    });
    await setupMocks(page);

    await page.goto('/projects');
    await expect(page.locator('[data-testid=\"projects-list-table\"] tfoot')).toContainText('2 projects');

    await page.getByTestId('projects-home-view-select').click();
    await page.getByRole('option', { name: 'Active' }).click();

    await expect(page.locator('[data-testid=\"projects-list-table\"] tfoot')).toContainText('1 projects');
  });

  test('timeline left metadata renders registry fields', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('ff_projects_home_v2', 'true');
      window.localStorage.setItem('ff_linear_timeline', 'true');
      window.localStorage.setItem(
        'projects.v2.layout.timeline.visibleFieldIds',
        JSON.stringify(['project_name', 'agreed_fee']),
      );
      window.localStorage.setItem(
        'projects.v2.layout.timeline.order',
        JSON.stringify(['project_name', 'agreed_fee']),
      );
    });
    await setupMocks(page);

    await page.goto('/projects');
    await page.getByRole('button', { name: 'Timeline' }).click();
    await expect(page.getByTestId('linear-timeline-panel')).toBeVisible();
    await expect(page.getByText('Agreed Fee: $100,000.00')).toBeVisible();
  });
});
