import { test, expect } from '@playwright/test';

test.describe('Workspace Issues - Panel Integration', () => {
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

    // Mock project issues table API
    await page.route(/.*\/api\/projects\/\d+\/issues\/table/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            rows: [
              {
                issue_key: 'ACC-001',
                display_id: 'ACC-001',
                title: 'Structural column misalignment',
                status_normalized: 'Open',
                priority_normalized: 'High',
                zone: 'Level 2',
                assignee_user_key: 'user@example.com',
                discipline_normalized: 'Structural',
                created_at: '2024-01-15T10:00:00Z',
                updated_at: '2024-01-20T14:30:00Z',
                service_id: 1,
                service_name: 'Structural Engineering',
                review_id: 5,
              },
              {
                issue_key: 'RVZ-042',
                display_id: 'RVZ-042',
                title: 'MEP coordination issue in basement',
                status_normalized: 'In Progress',
                priority_normalized: 'Medium',
                zone: 'Basement',
                assignee_user_key: 'engineer@example.com',
                discipline_normalized: 'MEP',
                created_at: '2024-01-16T09:00:00Z',
                updated_at: '2024-01-21T16:45:00Z',
                service_id: 2,
                service_name: 'MEP Design',
                review_id: null,
              },
            ],
            total_count: 2,
            page: 1,
            page_size: 50,
          }),
        });
        return;
      }
      await route.continue();
    });

    // Mock issue detail API
    await page.route(/.*\/api\/issues\/ACC-001\/detail/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            issue_key: 'ACC-001',
            display_id: 'ACC-001',
            title: 'Structural column misalignment',
            status_normalized: 'Open',
            priority_normalized: 'High',
            zone: 'Level 2',
            assignee_user_key: 'user@example.com',
            discipline_normalized: 'Structural',
            description: 'Column grid misalignment detected during coordination review.',
            created_at: '2024-01-15T10:00:00Z',
            updated_at: '2024-01-20T14:30:00Z',
            due_date: '2024-02-15',
            service_id: 1,
            service_name: 'Structural Engineering',
            review_id: 5,
            review_label: 'Coordination Review #5',
            comments: [
              {
                text: 'This needs immediate attention from the structural team.',
                author: 'Project Manager',
                created_at: '2024-01-16T08:30:00Z',
              },
              {
                text: 'Structural engineer has been notified.',
                author: 'Coordinator',
                created_at: '2024-01-17T10:15:00Z',
              },
            ],
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route(/.*\/api\/issues\/RVZ-042\/detail/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            issue_key: 'RVZ-042',
            display_id: 'RVZ-042',
            title: 'MEP coordination issue in basement',
            status_normalized: 'In Progress',
            priority_normalized: 'Medium',
            zone: 'Basement',
            assignee_user_key: 'engineer@example.com',
            discipline_normalized: 'MEP',
            description: 'HVAC ductwork conflicts with electrical conduit.',
            created_at: '2024-01-16T09:00:00Z',
            updated_at: '2024-01-21T16:45:00Z',
            due_date: '2024-02-28',
            service_id: 2,
            service_name: 'MEP Design',
            review_id: null,
            review_label: null,
            comments: [],
          }),
        });
        return;
      }
      await route.continue();
    });
  });

  test('should display issues list on issues tab', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Verify issues tab is active
    const issuesTab = page.getByTestId('workspace-tab-issues');
    await expect(issuesTab).toBeVisible();

    // Verify issues table is displayed
    const issuesTable = page.getByTestId('project-issues-table');
    await expect(issuesTable).toBeVisible();

    // Verify issue rows are present
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await expect(firstIssue).toBeVisible();
    await expect(firstIssue).toContainText('Structural column misalignment');

    const secondIssue = page.getByTestId('issue-row-RVZ-042');
    await expect(secondIssue).toBeVisible();
    await expect(secondIssue).toContainText('MEP coordination issue in basement');
  });

  test('should update right panel when issue is selected', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Initially, right panel should show issues summary
    const rightPanel = page.getByTestId('workspace-right-panel');
    await expect(rightPanel).toBeVisible();

    // Click on first issue row
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();

    // Wait for URL to update
    await expect(page).toHaveURL(/.*\?sel=issue:ACC-001/);

    // Verify issue detail panel is displayed in right panel
    const issueDetailPanel = page.getByTestId('issue-detail-panel');
    await expect(issueDetailPanel).toBeVisible();

    // Verify issue details are displayed
    await expect(issueDetailPanel).toContainText('ACC-001');
    await expect(issueDetailPanel).toContainText('Structural column misalignment');
    await expect(issueDetailPanel).toContainText('Open');
    await expect(issueDetailPanel).toContainText('High');
    await expect(issueDetailPanel).toContainText('Level 2');
    await expect(issueDetailPanel).toContainText('Structural Engineering');
    await expect(issueDetailPanel).toContainText('Coordination Review #5');

    // Verify comments are displayed
    await expect(issueDetailPanel).toContainText('Latest Comments');
    await expect(issueDetailPanel).toContainText('This needs immediate attention from the structural team.');
  });

  test('should NOT display legacy drawer when issue is selected', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Click on first issue row
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();

    // Wait for panel to update
    await page.waitForTimeout(500);

    // Verify legacy drawer is NOT present
    const legacyDrawer = page.getByTestId('issue-detail-drawer');
    await expect(legacyDrawer).not.toBeVisible();

    // Verify no MUI drawer/modal overlay
    const drawerBackdrop = page.locator('.MuiDrawer-root');
    await expect(drawerBackdrop).not.toBeVisible();
  });

  test('should highlight selected issue row', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Click on first issue
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();
    await page.waitForTimeout(200);

    // Verify row is highlighted (has selected class)
    await expect(firstIssue).toHaveClass(/Mui-selected/);

    // Click on second issue
    const secondIssue = page.getByTestId('issue-row-RVZ-042');
    await secondIssue.click();
    await page.waitForTimeout(200);

    // Verify second row is now highlighted
    await expect(secondIssue).toHaveClass(/Mui-selected/);

    // Verify first row is no longer highlighted
    await expect(firstIssue).not.toHaveClass(/Mui-selected/);
  });

  test('should clear selection and return to summary when Escape is pressed', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Select an issue
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();

    // Verify issue detail panel is visible
    const issueDetailPanel = page.getByTestId('issue-detail-panel');
    await expect(issueDetailPanel).toBeVisible();

    // Press Escape key
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    // Verify URL selection is cleared
    await expect(page).toHaveURL(/^(?!.*\?sel=)/);

    // Verify issue detail panel is no longer visible
    await expect(issueDetailPanel).not.toBeVisible();

    // Verify summary panel is shown
    const rightPanel = page.getByTestId('workspace-right-panel');
    await expect(rightPanel).toContainText('Issues Summary');

    // Verify no row is highlighted
    await expect(firstIssue).not.toHaveClass(/Mui-selected/);
  });

  test('should switch between issue selections', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Select first issue
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();
    await page.waitForTimeout(200);

    // Verify first issue details are shown
    const issueDetailPanel = page.getByTestId('issue-detail-panel');
    await expect(issueDetailPanel).toContainText('ACC-001');
    await expect(issueDetailPanel).toContainText('Structural column misalignment');

    // Select second issue
    const secondIssue = page.getByTestId('issue-row-RVZ-042');
    await secondIssue.click();
    await page.waitForTimeout(200);

    // Verify second issue details are shown
    await expect(page).toHaveURL(/.*\?sel=issue:RVZ-042/);
    await expect(issueDetailPanel).toContainText('RVZ-042');
    await expect(issueDetailPanel).toContainText('MEP coordination issue in basement');
    await expect(issueDetailPanel).toContainText('In Progress');
    await expect(issueDetailPanel).toContainText('Medium');
  });

  test('should clear selection when navigating to different tab', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Select an issue
    const firstIssue = page.getByTestId('issue-row-ACC-001');
    await firstIssue.click();
    await page.waitForTimeout(200);

    // Verify issue is selected
    await expect(page).toHaveURL(/.*\?sel=issue:ACC-001/);

    // Navigate to services tab
    const servicesTab = page.getByTestId('workspace-tab-services');
    await servicesTab.click();
    await page.waitForTimeout(200);

    // Verify selection is cleared
    await expect(page).toHaveURL(/^(?!.*\?sel=)/);

    // Navigate back to issues tab
    const issuesTab = page.getByTestId('workspace-tab-issues');
    await issuesTab.click();
    await page.waitForTimeout(200);

    // Verify no issue is selected
    await expect(firstIssue).not.toHaveClass(/Mui-selected/);
  });

  test('should handle issue with no comments', async ({ page }) => {
    await page.goto('http://localhost:5173/projects/7/workspace/issues');
    await page.waitForLoadState('networkidle');

    // Select second issue (has no comments)
    const secondIssue = page.getByTestId('issue-row-RVZ-042');
    await secondIssue.click();
    await page.waitForTimeout(200);

    const issueDetailPanel = page.getByTestId('issue-detail-panel');
    await expect(issueDetailPanel).toBeVisible();

    // Verify basic details are shown
    await expect(issueDetailPanel).toContainText('RVZ-042');
    await expect(issueDetailPanel).toContainText('MEP coordination issue in basement');

    // Verify comments section is not shown (since no comments)
    await expect(issueDetailPanel).not.toContainText('Latest Comments');
  });
});
