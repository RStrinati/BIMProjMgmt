import { test, expect } from '@playwright/test';

const today = new Date();
const formatDate = (value: Date) => value.toISOString().slice(0, 10);
const startDate = new Date(today);
startDate.setDate(today.getDate() - 10);
const endDate = new Date(today);
endDate.setDate(today.getDate() + 20);

const timelinePayload = {
  projects: [
    {
      project_id: 1,
      project_name: 'Alpha Campus',
      start_date: formatDate(startDate),
      end_date: formatDate(endDate),
      project_manager: 'Jordan Lead',
      client_name: 'Acme',
      project_type: 'Data Center',
      priority: 'High',
      internal_lead: 7,
      internal_lead_name: 'Morgan Lead',
      progress_pct: 37,
      review_items: [],
    },
    {
      project_id: 2,
      project_name: 'Beta Expansion',
      start_date: formatDate(startDate),
      end_date: formatDate(endDate),
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
    await expect(page.getByTestId('timeline-grid-root')).toBeVisible();
    await expect(page.getByText('Alpha Campus')).toBeVisible();
    await expect(page.getByTestId('timeline-row-label').first()).toContainText('Alpha Campus');
    await expect(page.getByTestId('timeline-row-label').first()).not.toContainText('Acme');
    await expect(page.getByTestId('timeline-row-priority').first()).toBeVisible();
    await expect(page.getByTestId('timeline-row-lead').first()).toBeVisible();
    await expect(page.getByTestId('timeline-bar-label').first()).toContainText('37%');
    await expect(page.getByTestId('timeline-today-line')).toBeVisible();

    const zoomWeek = page.getByRole('button', { name: 'Week' });
    await zoomWeek.click();
    await expect(page.getByTestId('timeline-day-ticks')).toContainText(String(today.getDate()));

    expect(consoleErrors).toEqual([]);
  });
});
