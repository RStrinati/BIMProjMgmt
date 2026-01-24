import { test, expect } from '@playwright/test';
import { setupWorkspaceMocks, navigateToProjectWorkspace, switchTab } from '../helpers';

const seedServices = [
  {
    service_id: 55,
    project_id: 1,
    service_code: 'SVC-01',
    service_name: 'Coordination',
    phase: 'Design',
    status: 'planned',
    progress_pct: 25,
    agreed_fee: 12000,
  },
  {
    service_id: 56,
    project_id: 1,
    service_code: 'SVC-02',
    service_name: 'Audit',
    phase: 'Construction',
    status: 'in_progress',
    progress_pct: 50,
    agreed_fee: 8000,
  },
];

test.describe('Workspace v2 services tab', () => {
  test('renders services list', async ({ page }) => {
    await setupWorkspaceMocks(page, { services: seedServices });
    await navigateToProjectWorkspace(page, 1);

    // Navigate to services tab
    await switchTab(page, 'Services');

    // Verify both services are displayed
    await expect(page.getByTestId('project-workspace-v2-services')).toBeVisible();
    await expect(page.getByText('Coordination')).toBeVisible();
    await expect(page.getByText('Audit')).toBeVisible();
  });

  test('allows status updates', async ({ page }) => {
    await setupWorkspaceMocks(page, { services: seedServices });
    await navigateToProjectWorkspace(page, 1);

    // Navigate to services tab
    await switchTab(page, 'Services');

    // Click on service to open details
    const serviceRow = page.getByTestId('project-workspace-v2-service-row-55');
    await serviceRow.click();

    // Update status
    const statusSelect = page.getByRole('button', { name: /status/i });
    await statusSelect.click();
    await page.getByRole('option', { name: /in.progress|in progress/i }).click();

    // Verify status changed
    await expect(serviceRow).toContainText(/in.progress|in progress/i);
  });
});
