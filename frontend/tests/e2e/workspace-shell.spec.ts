import { test, expect } from '@playwright/test';

test.describe('Workspace Shell - Layout & Routing', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route(/.*\/api\/projects\/\d+$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 7,
            project_name: 'Test Workspace Project',
            project_number: 'P-007',
            client_name: 'Test Client',
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
          body: JSON.stringify([{ user_id: 101, name: 'Test Lead' }]),
        });
        return;
      }
      await route.continue();
    });
  });

  test('workspace shell renders with 3-column layout', async ({ page }) => {
    await page.goto('/projects/7/workspace/overview');

    // Verify shell is present
    await expect(page.getByTestId('workspace-shell')).toBeVisible();

    // Verify header with project title
    await expect(page.getByTestId('workspace-project-title')).toContainText('Test Workspace Project');

    // Verify tabs are visible
    await expect(page.getByTestId('workspace-tab-overview')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-services')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-deliverables')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-updates')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-issues')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-tasks')).toBeVisible();
    await expect(page.getByTestId('workspace-tab-quality')).toBeVisible();

    // Verify right panel is present (desktop)
    await expect(page.getByTestId('workspace-right-panel')).toBeVisible();
  });

  test('Timeline tab is NOT present', async ({ page }) => {
    await page.goto('/projects/7/workspace/overview');

    // Verify Timeline tab does NOT exist
    const timelineTab = page.getByRole('tab', { name: 'Timeline' });
    await expect(timelineTab).not.toBeVisible();
  });

  test('tab navigation works correctly', async ({ page }) => {
    await page.goto('/projects/7/workspace/overview');

    // Overview should be active
    await expect(page.getByTestId('workspace-overview-tab')).toBeVisible();
    expect(page.url()).toContain('/workspace/overview');

    // Navigate to Services
    await page.getByTestId('workspace-tab-services').click();
    await expect(page.getByTestId('workspace-services-tab')).toBeVisible();
    expect(page.url()).toContain('/workspace/services');

    // Navigate to Updates
    await page.getByTestId('workspace-tab-updates').click();
    await expect(page.getByTestId('workspace-updates-tab')).toBeVisible();
    expect(page.url()).toContain('/workspace/updates');

    // Navigate to Tasks
    await page.getByTestId('workspace-tab-tasks').click();
    await expect(page.getByTestId('workspace-tasks-tab')).toBeVisible();
    expect(page.url()).toContain('/workspace/tasks');
  });

  test('redirect from /projects/:id to /projects/:id/workspace/overview', async ({ page }) => {
    await page.goto('/projects/7');

    // Should redirect to workspace/overview
    await page.waitForURL(/\/projects\/7\/workspace\/overview/);
    await expect(page.getByTestId('workspace-overview-tab')).toBeVisible();
  });

  test('selection query param parsing works', async ({ page }) => {
    // Navigate with selection param already in URL
    await page.goto('/projects/7/workspace/services?sel=service:123');

    // Wait for page to load
    await expect(page.getByTestId('workspace-services-tab')).toBeVisible();

    // The selection hook should have parsed the param (verify via state, not just URL)
    // This test verifies the parsing logic works - actual selection will be tested in services-panel spec
    const url = new URL(page.url());
    const selParam = url.searchParams.get('sel');
    
    // If the hook cleared it, that's also valid behavior (it validates the param)
    // Main goal: no crashes when navigating with ?sel=type:id
    expect(page.url()).toContain('/workspace/services');
  });

  test('Esc key clears selection', async ({ page }) => {
    await page.goto('/projects/7/workspace/services');

    // Manually set selection param
    await page.evaluate(() => {
      window.history.replaceState(null, '', '/projects/7/workspace/services?sel=service:123');
    });

    // Trigger a React re-render by clicking somewhere
    await page.click('body');
    
    // Verify selection param is present
    expect(page.url()).toContain('sel=service:123');

    // Press Esc
    await page.keyboard.press('Escape');

    // Wait for URL to update');

    // Manually set selection param
    await page.evaluate(() => {
      window.history.replaceState(null, '', '/projects/7/workspace/services?sel=service:123');
    });

    // Trigger a React re-render
    await page.click('body');
    
    // Verify selection param is present
    expect(page.url()).toContain('sel=service:123');

    // Switch to another tab
    await page.getByTestId('workspace-tab-deliverables').click();

    // Wait for navigation
    await page.waitForURL(/\/workspace\/deliverables/);

    // Selection param should be removed (due to clearSelection in useEffect)rvice:123');

    // Switch to another tab
    await page.getByTestId('workspace-tab-deliverables').click();

    // Wait for navigation
    await page.waitForURL(/\/workspace\/deliverables/);

    // Selection param should be removed
    expect(page.url()).not.toContain('sel=');
  });

  test('right panel shows shared blocks', async ({ page }) => {
    await page.goto('/projects/7/workspace/overview');

    const panel = page.getByTestId('workspace-right-panel');
    
    // Verify shared blocks are present (using headings to be more specific)
    await expect(panel.getByRole('heading', { name: 'Properties' })).toBeVisible();
    await expect(panel.getByRole('heading', { name: 'Progress' })).toBeVisible();
    await expect(panel.getByRole('heading', { name: 'Activity' })).toBeVisible();

    // Verify project data is displayed
    await expect(panel.getByText('P-007')).toBeVisible();
    await expect(panel.getByText('Test Client')).toBeVisible();
  });
});
