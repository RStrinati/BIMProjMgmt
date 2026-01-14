import { test, expect } from '@playwright/test';

const timelinePayload = {
  projects: [
    {
      project_id: 1,
      project_name: 'Alpha Campus',
      start_date: '2024-01-01',
      end_date: '2024-03-15',
      project_manager: 'Jordan Lead',
      client_name: 'Acme',
      project_type: 'Data Center',
      review_items: [],
    },
    {
      project_id: 2,
      project_name: 'Beta Expansion',
      start_date: '2024-02-01',
      end_date: '2024-04-30',
      project_manager: 'Taylor Lead',
      client_name: 'Orbit',
      project_type: 'Health',
      review_items: [],
    },
  ],
};

test.describe('Linear timeline (flagged)', () => {
  test('renders timeline and switches zoom without errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_linear_timeline', 'true');
    });

    await page.route('**/api/dashboard/timeline**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(timelinePayload),
      });
    });

    await page.goto('/');

    await expect(page.getByTestId('linear-timeline-panel')).toBeVisible();
    await expect(page.getByText('Alpha Campus')).toBeVisible();

    const zoomWeek = page.getByRole('button', { name: 'Week' });
    await zoomWeek.click();
    await expect(page.getByText('1 Jan')).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });
});
