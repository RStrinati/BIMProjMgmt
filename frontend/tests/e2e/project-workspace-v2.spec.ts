import { test, expect } from '@playwright/test';

test.describe('Project workspace v2', () => {
  test('overview renders and tabs switch', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await page.route(/.*\/api\/project\/\d+/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 7,
            project_name: 'Workspace Project',
            project_number: 'P-007',
            client_name: 'Client X',
            status: 'Active',
            priority_label: 'High',
            internal_lead: 101,
            total_service_agreed_fee: 150000,
            total_service_billed_amount: 50000,
            service_billed_pct: 33,
            created_at: '2024-05-01T10:00:00Z',
            updated_at: '2024-05-10T10:00:00Z',
          }),
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
          body: JSON.stringify([{ user_id: 101, name: 'Alex Lead' }]),
        });
        return;
      }
      await route.continue();
    });

    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/projects/7');

    await expect(page.getByTestId('project-workspace-v2-overview')).toBeVisible();

    await page.getByRole('tab', { name: 'Services' }).click();
    await expect(page.getByTestId('project-workspace-v2-services')).toBeVisible();

    await page.getByRole('tab', { name: 'Deliverables' }).click();
    await expect(page.getByTestId('project-workspace-v2-reviews')).toBeVisible();

    await page.getByRole('tab', { name: 'Tasks' }).click();
    await expect(page.getByTestId('project-workspace-v2-tasks')).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });
});
