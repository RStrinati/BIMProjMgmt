import { test, expect } from '@playwright/test';
import { setupWorkspaceMocks, switchTab, navigateToProjectWorkspace, waitForLoading } from '../helpers';

const reviews = [
  {
    review_id: 101,
    service_id: 55,
    project_id: 1,
    cycle_no: 1,
    planned_date: '2024-05-10',
    due_date: '2024-05-20',
    status: 'planned',
    service_name: 'Design Review',
    service_code: 'DR-01',
  },
];


test.describe('Project-wide reviews', () => {
  test('renders all reviews for project', async ({ page }) => {
    await setupWorkspaceMocks(page, { reviews });

    // Mock reviews endpoint
    await page.route('**/api/projects/1/reviews**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: reviews, total: 1 }),
      });
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Reviews');

    // Verify reviews are displayed
    await expect(page.getByText('DR-01')).toBeVisible();
    await expect(page.getByText('Design Review')).toBeVisible();
  });

  test('updates review status', async ({ page }) => {
    let statusUpdated = false;

    await setupWorkspaceMocks(page, { reviews });

    // Mock reviews endpoint
    await page.route('**/api/projects/1/reviews**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: reviews, total: 1 }),
      });
    });

    // Mock review status update
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        const payload = await route.request().postDataJSON();
        reviews[0].status = payload.status || 'completed';
        statusUpdated = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Reviews');

    // Click status selector and update
    const statusButton = page.locator('[data-testid="review-status-101"]').first();
    await statusButton.click();
    await page.getByRole('option', { name: 'Completed' }).click();

    await waitForLoading(page);
    expect(statusUpdated).toBe(true);
  });

  test('displays review metadata', async ({ page }) => {
    await setupWorkspaceMocks(page, { reviews });

    // Mock reviews endpoint
    await page.route('**/api/projects/1/reviews**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: reviews, total: 1 }),
      });
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Reviews');

    // Verify review details are visible
    await expect(page.getByText('Cycle 1')).toBeVisible();
    await expect(page.getByText('5/10/2024')).toBeVisible(); // planned date formatted
  });
});
