import { test, expect } from '@playwright/test';

const projectId = Number(process.env.SMOKE_TEST_PROJECT_ID || 0);
const reviewId = Number(process.env.SMOKE_TEST_REVIEW_ID || 0);
const newDueDate = process.env.SMOKE_TEST_NEW_DUE_DATE || '';
const overrideMonth = process.env.SMOKE_TEST_OVERRIDE_MONTH || '';

test.describe('ProjectWorkspacePageV2 - Monthly Billing Smoke', () => {
  test.skip(!projectId, 'SMOKE_TEST_PROJECT_ID is required for smoke testing.');

  test('loads workspace and invoice widgets', async ({ page }) => {
    await page.goto(`/workspace/${projectId}`);
    await expect(page.getByTestId('project-workspace-v2-root')).toBeVisible();
    await expect(page.getByTestId('project-workspace-v2-invoice-pipeline')).toBeVisible();

    await page.getByRole('tab', { name: 'Deliverables' }).click();
    await expect(page.getByTestId('project-workspace-v2-reviews')).toBeVisible();

    if (reviewId && newDueDate) {
      const row = page.getByTestId(`deliverable-row-${reviewId}`);
      await expect(row).toBeVisible();

      const dueCell = row.getByTestId(`cell-due-${reviewId}`);
      await dueCell.click();
      const dueInput = page.getByTestId(`cell-due-${reviewId}-input`);
      await dueInput.fill(newDueDate);
      await dueInput.press('Enter');

      await page.waitForTimeout(500);
    }

    if (reviewId && overrideMonth) {
      const row = page.getByTestId(`deliverable-row-${reviewId}`);
      await expect(row).toBeVisible();

      const invoiceMonthCell = row.getByTestId(`cell-invoice-month-${reviewId}`);
      await invoiceMonthCell.click();
      const overrideInput = page.getByTestId(`cell-invoice-month-${reviewId}-input`);
      await overrideInput.fill(overrideMonth);
      await overrideInput.press('Enter');

      await page.waitForTimeout(500);
    }
  });
});
