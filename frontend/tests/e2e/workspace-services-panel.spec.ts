import { test, expect } from '@playwright/test';

test.describe('Workspace Services - Panel Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Mock project API
    await page.route(/.*\/api\/projects\/\d+$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 7,
            project_name: 'Test Project',
            project_number: 'P-007',
            client_name: 'Test Client',
            status: 'Active',
            internal_lead: 101,
            total_service_agreed_fee: 150000,
            total_service_billed_amount: 50000,
          }),
        });
        return;
      }
      await route.continue();
    });

    // Mock users API
    await page.route('**/api/users', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ user_id: 101, name: 'Test User' }]),
        });
        return;
      }
      await route.continue();
    });

    // Mock services API
    await page.route(/.*\/api\/projects\/\d+\/services/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              service_id: 1,
              project_id: 7,
              service_code: 'S001',
              service_name: 'Architectural Design',
              phase: 'Design',
              status: 'active',
              agreed_fee: 50000,
              billed_amount: 15000,
              agreed_fee_remaining: 35000,
              billing_progress_pct: 30,
            },
            {
              service_id: 2,
              project_id: 7,
              service_code: 'S002',
              service_name: 'Structural Engineering',
              phase: 'Design',
              status: 'in_progress',
              agreed_fee: 40000,
              billed_amount: 20000,
              agreed_fee_remaining: 20000,
              billing_progress_pct: 50,
            },
          ]),
        });
        return;
      }
      await route.continue();
    });

    // Mock service reviews API
    await page.route(/.*\/api\/projects\/\d+\/services\/\d+\/reviews/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              review_id: 1,
              cycle_no: 1,
              status: 'completed',
              planned_date: '2024-01-15',
            },
          ]),
        });
        return;
      }
      await route.continue();
    });

    // Mock service items API
    await page.route(/.*\/api\/projects\/\d+\/services\/\d+\/items/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
        return;
      }
      await route.continue();
    });
  });

  test('services list uses LinearList table graphics', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    // Verify LinearList container is present
    const container = page.locator('[data-testid*="linear-list-container"]').first();
    await expect(container).toBeVisible();

    // Verify header row with consistent columns
    await expect(page.getByText('Service')).toBeVisible();
    await expect(page.getByText('Phase')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();
    await expect(page.getByText('Agreed')).toBeVisible();
    await expect(page.getByText('Billed')).toBeVisible();
    await expect(page.getByText('Remaining')).toBeVisible();
    await expect(page.getByText('Progress')).toBeVisible();
  });

  test('service rows are clickable and update right panel', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    // Wait for services to load
    await expect(page.getByTestId('workspace-service-row-1')).toBeVisible();

    // Verify right panel shows shared blocks initially
    const panel = page.getByTestId('workspace-right-panel');
    await expect(panel.getByRole('heading', { name: 'Properties' })).toBeVisible();

    // Click first service row
    await page.getByTestId('workspace-service-row-1').click();

    // Wait a moment for state update
    await page.waitForTimeout(200);

    // Verify service detail appears in right panel
    await expect(panel.getByText('S001')).toBeVisible();
    await expect(panel.getByText('Architectural Design')).toBeVisible();
    await expect(panel.getByRole('heading', { name: 'Finance' })).toBeVisible();
  });

  test('service detail panel shows finance data', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    await page.getByTestId('workspace-service-row-1').click();
    await page.waitForTimeout(200);

    const panel = page.getByTestId('workspace-right-panel');

    // Verify finance section
    const financeSection = panel.getByRole('heading', { name: 'Finance' }).locator('..');
    await expect(financeSection.getByText('Agreed Fee')).toBeVisible();
    await expect(financeSection.getByText('$50,000.00')).toBeVisible();
    await expect(financeSection.getByText('Billed')).toBeVisible();
    await expect(financeSection.getByText('$15,000.00')).toBeVisible();
    await expect(financeSection.getByText('Remaining')).toBeVisible();
    await expect(financeSection.getByText('$35,000.00')).toBeVisible();
  });

  test('service detail panel has Reviews and Items tabs', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    await page.getByTestId('workspace-service-row-1').click();
    await page.waitForTimeout(200);

    const panel = page.getByTestId('workspace-right-panel');

    // Verify tabs are present
    await expect(panel.getByRole('tab', { name: /Reviews/ })).toBeVisible();
    await expect(panel.getByRole('tab', { name: /Items/ })).toBeVisible();

    // Click Reviews tab - should show review data
    await panel.getByRole('tab', { name: /Reviews/ }).click();
    await expect(panel.getByText('Cycle #1')).toBeVisible();

    // Click Items tab
    await panel.getByRole('tab', { name: /Items/ }).click();
    await expect(panel.getByText('No items yet.')).toBeVisible();
  });

  test('Add Service button navigates to create view', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    const addButton = page.getByTestId('workspace-add-service-button');
    await expect(addButton).toBeVisible();

    await addButton.click();

    // Should navigate to /services/new
    await page.waitForURL(/\/workspace\/services\/new/);
    await expect(page.getByTestId('workspace-service-create-view')).toBeVisible();
  });

  test('selecting different services updates panel content', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    // Select first service
    await page.getByTestId('workspace-service-row-1').click();
    await page.waitForTimeout(200);

    const panel = page.getByTestId('workspace-right-panel');
    await expect(panel.getByText('S001')).toBeVisible();
    await expect(panel.getByText('Architectural Design')).toBeVisible();

    // Select second service
    await page.getByTestId('workspace-service-row-2').click();
    await page.waitForTimeout(200);

    // Panel should update to show second service
    await expect(panel.getByText('S002')).toBeVisible();
    await expect(panel.getByText('Structural Engineering')).toBeVisible();
  });

  test('switching tabs clears service selection', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    // Select a service
    await page.getByTestId('workspace-service-row-1').click();
    await page.waitForTimeout(200);

    const panel = page.getByTestId('workspace-right-panel');
    await expect(panel.getByText('S001')).toBeVisible();

    // Switch to Deliverables tab
    await page.getByTestId('workspace-tab-deliverables').click();
    await page.waitForURL(/\/workspace\/deliverables/);

    // Panel should no longer show service detail
    await expect(panel.getByText('S001')).not.toBeVisible();
    await expect(panel.getByRole('heading', { name: 'Properties' })).toBeVisible();
  });
});
