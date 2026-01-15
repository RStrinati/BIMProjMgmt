import { test, expect } from '@playwright/test';

// Mock issues data with mix of ACC and Revizto
const mockIssuesTableResponse = {
  page: 1,
  page_size: 50,
  total_count: 3,
  rows: [
    {
      issue_key: 'acc_uuid_12345',
      source_system: 'ACC',
      source_issue_id: '12345',
      source_project_id: 'acc_proj_1',
      project_id: 'proj_1',
      display_id: 'ACC-924',
      acc_issue_number: 924,
      acc_issue_uuid: 'uuid-12345',
      acc_id_type: 'uuid',
      title: 'Exterior wall thickness inconsistency',
      status_raw: 'Open',
      status_normalized: 'open',
      priority_raw: 'High',
      priority_normalized: 'high',
      discipline_raw: 'Architectural',
      discipline_normalized: 'architectural',
      assignee_user_key: 'user_001',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-18T14:30:00Z',
      closed_at: null,
    },
    {
      issue_key: 'rev_67890',
      source_system: 'Revizto',
      source_issue_id: 'rev_67890',
      source_project_id: 'rev_proj_1',
      project_id: 'proj_1',
      display_id: 'REV-42',
      acc_issue_number: null,
      acc_issue_uuid: null,
      acc_id_type: null,
      title: 'MEP coordination clash detected',
      status_raw: 'In Progress',
      status_normalized: 'in_progress',
      priority_raw: 'Medium',
      priority_normalized: 'medium',
      discipline_raw: 'MEP',
      discipline_normalized: 'mep',
      assignee_user_key: 'user_002',
      created_at: '2024-01-10T08:00:00Z',
      updated_at: '2024-01-17T11:00:00Z',
      closed_at: null,
    },
    {
      issue_key: 'acc_legacy_11111',
      source_system: 'ACC',
      source_issue_id: '11111',
      source_project_id: 'acc_proj_1',
      project_id: 'proj_1',
      display_id: 'ACC-56789012',
      acc_issue_number: null,
      acc_issue_uuid: 'legacy-uuid-11111',
      acc_id_type: 'legacy',
      title: 'Structural beam sizing needs review',
      status_raw: 'Closed',
      status_normalized: 'closed',
      priority_raw: 'Low',
      priority_normalized: 'low',
      discipline_raw: 'Structural',
      discipline_normalized: 'structural',
      assignee_user_key: null,
      created_at: '2024-01-05T09:00:00Z',
      updated_at: '2024-01-12T16:45:00Z',
      closed_at: '2024-01-12T16:45:00Z',
    },
  ],
};

const setupIssueMocks = async (page: any) => {
  // Mock the issues table endpoint
  await page.route('**/api/issues/table*', async (route) => {
    const url = new URL(route.request().url());
    const sourceSystem = url.searchParams.get('source_system');
    const search = url.searchParams.get('search');

    let response = { ...mockIssuesTableResponse };

    // Filter by source_system if provided
    if (sourceSystem) {
      response.rows = response.rows.filter((row: any) => row.source_system === sourceSystem);
      response.total_count = response.rows.length;
    }

    // Filter by search if provided
    if (search) {
      const lowercaseSearch = search.toLowerCase();
      response.rows = response.rows.filter((row: any) =>
        row.title.toLowerCase().includes(lowercaseSearch) ||
        row.display_id.toLowerCase().includes(lowercaseSearch) ||
        row.issue_key.toLowerCase().includes(lowercaseSearch),
      );
      response.total_count = response.rows.length;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
};

test.describe('Issues Hub Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupIssueMocks(page);
  });

  test('1) Nav shows Issues link when ff_issues_hub enabled', async ({ page }) => {
    // Enable the feature flag before navigating
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/');

    // Check that nav item exists
    const navIssues = page.locator('[data-testid="nav-issues"]');
    await expect(navIssues).toBeVisible();
    await expect(navIssues).toContainText('Issues');
  });

  test('2) Clicking nav navigates to /issues and renders issues-hub-root', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/');

    // Click on Issues nav item
    const navIssues = page.locator('[data-testid="nav-issues"]');
    await navIssues.click();

    // Verify route changed
    await expect(page).toHaveURL('/issues');

    // Verify root element renders
    const root = page.locator('[data-testid="issues-hub-root"]');
    await expect(root).toBeVisible();
  });

  test('3) List loads and displays both ACC and Revizto display_id formats', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Wait for the list to load
    const issuesHubList = page.locator('[data-testid="issues-hub-list"]');
    await expect(issuesHubList).toBeVisible();

    // Check for ACC display_id (ACC-924)
    await expect(page.locator('text=ACC-924')).toBeVisible();

    // Check for Revizto display_id (REV-42)
    await expect(page.locator('text=REV-42')).toBeVisible();

    // Check for legacy ACC display_id
    await expect(page.locator('text=ACC-56789012')).toBeVisible();

    // Verify all rows are present
    const rows = page.locator('[data-testid^="issues-row-"]');
    await expect(rows).toHaveCount(3);
  });

  test('4) Preset filter "ACC only" adds param and updates rows', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Wait for the page to load
    await expect(page.locator('[data-testid="issues-hub-root"]')).toBeVisible();

    // Click "ACC Only" button
    await page.locator('button:has-text("ACC Only")').click();

    // Wait for rows to update (after filter is applied)
    // Should have 2 ACC rows
    const rows = page.locator('[data-testid^="issues-row-"]');
    await expect(rows).toHaveCount(2);

    // Verify only ACC display_ids are shown
    await expect(page.locator('text=ACC-924')).toBeVisible();
    await expect(page.locator('text=ACC-56789012')).toBeVisible();

    // Revizto should not be present
    await expect(page.locator('text=REV-42')).not.toBeVisible();

    // Verify the request included source_system=ACC
    const requests = page.context().requests.filter((req) =>
      req.url().includes('/api/issues/table') && req.url().includes('source_system=ACC'),
    );
    expect(requests.length).toBeGreaterThan(0);
  });

  test('5) No console errors on load and interaction', async ({ page }) => {
    const errors: string[] = [];

    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Wait for page to fully load
    await expect(page.locator('[data-testid="issues-hub-root"]')).toBeVisible();

    // Interact with filters
    await page.locator('[data-testid="issues-hub-filters"]').scrollIntoViewIfNeeded();
    await page.locator('input[placeholder="Title, ID, or key..."]').fill('wall');

    // Wait a moment for debounce
    await page.waitForTimeout(500);

    // No console errors should have occurred
    expect(errors).toHaveLength(0);
  });

  test('6) Feature flag gate: Issues link NOT visible when ff_issues_hub disabled', async ({
    page,
  }) => {
    // Do NOT enable the feature flag (default is false)
    await page.goto('/');

    // Nav item should not exist
    const navIssues = page.locator('[data-testid="nav-issues"]');
    await expect(navIssues).not.toBeVisible();
  });

  test('7) /issues route redirects when feature flag disabled', async ({ page }) => {
    // Disable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'false');
    });

    // Try to navigate directly to /issues
    await page.goto('/issues');

    // Should redirect to home (due to catch-all route)
    await expect(page).toHaveURL('/');
  });

  test('8) Saved view state persists in localStorage', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Apply a filter (Open preset)
    await page.locator('button:has-text("Open")').click();

    // Wait for the filter to apply
    await page.waitForTimeout(500);

    // Verify localStorage was updated
    const viewState = await page.evaluate(() => {
      return localStorage.getItem('issues_view_state');
    });

    expect(viewState).toBeTruthy();
    const parsed = JSON.parse(viewState!);
    expect(parsed.statusNormalized).toBe('open');
  });

  test('9) Clear filters button resets all filters', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Apply a filter
    await page.locator('button:has-text("ACC Only")').click();
    await page.waitForTimeout(500);

    // Clear filters
    await page.locator('button:has-text("Clear Filters")').click();
    await page.waitForTimeout(500);

    // All rows should be visible again
    const rows = page.locator('[data-testid^="issues-row-"]');
    await expect(rows).toHaveCount(3);
  });

  test('10) Pagination works correctly', async ({ page }) => {
    // Enable the feature flag
    await page.addInitScript(() => {
      localStorage.setItem('ff_issues_hub', 'true');
    });

    await page.goto('/issues');

    // Wait for initial load
    await expect(page.locator('[data-testid="issues-hub-root"]')).toBeVisible();

    // Verify pagination controls exist
    const pagination = page.locator('text=1–3 of 3');
    await expect(pagination).toBeVisible();
  });
});
