import { test, expect } from '@playwright/test';
import { navigateToProjectWorkspace, switchTab, editInlineCell, waitForLoading } from '../helpers';

const projectId = Number(process.env.SMOKE_TEST_PROJECT_ID || 0);
const reviewId = Number(process.env.SMOKE_TEST_REVIEW_ID || 0);
const newDueDate = process.env.SMOKE_TEST_NEW_DUE_DATE || '';
const overrideMonth = process.env.SMOKE_TEST_OVERRIDE_MONTH || '';

test.describe('ProjectWorkspacePageV2 - Smoke Tests', () => {
  test.skip(!projectId, 'SMOKE_TEST_PROJECT_ID is required for smoke testing.');

  test('loads workspace and navigates tabs', async ({ page }) => {
    await navigateToProjectWorkspace(page, projectId);
    await expect(page.getByTestId('project-workspace-v2-root')).toBeVisible();

    // Navigate to deliverables tab
    await switchTab(page, 'Deliverables');
    await expect(page.getByTestId('project-workspace-v2-deliverables')).toBeVisible();

    // If test data provided, update deliverable
    if (reviewId && newDueDate) {
      await editInlineCell(page, 'due-date', reviewId, newDueDate);
    }

    if (reviewId && overrideMonth) {
      await editInlineCell(page, 'invoice-month', reviewId, overrideMonth);
    }
  });

  test('navigates between workspace tabs', async ({ page }) => {
    await navigateToProjectWorkspace(page, projectId);

    // Test tab navigation
    await switchTab(page, 'Services');
    await expect(page.getByTestId('project-workspace-v2-services')).toBeVisible();

    await switchTab(page, 'Deliverables');
    await expect(page.getByTestId('project-workspace-v2-deliverables')).toBeVisible();

    await switchTab(page, 'Reviews');
    await expect(page.getByTestId('project-workspace-v2-reviews')).toBeVisible();
  });
});
