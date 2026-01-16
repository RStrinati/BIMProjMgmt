import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
};

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
    billed_amount: 3000,
    claimed_to_date: 3000,
    agreed_fee_remaining: 9000,
    billing_progress_pct: 25,
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
    billed_amount: 4000,
    claimed_to_date: 4000,
    agreed_fee_remaining: 4000,
    billing_progress_pct: 50,
  },
];

const seedReviews = [
  {
    review_id: 101,
    service_id: 55,
    review_cycle: 1,
    planned_date: '2026-01-15',
    actual_date: '2026-01-15',
    status: 'completed',
    assigned_to: 'John Doe',
  },
  {
    review_id: 102,
    service_id: 55,
    review_cycle: 2,
    planned_date: '2026-02-15',
    actual_date: null,
    status: 'planned',
    assigned_to: null,
  },
];

const seedItems = [
  {
    item_id: 201,
    service_id: 55,
    item_type: 'report',
    item_title: 'Weekly Progress Report',
    status: 'pending',
  },
  {
    item_id: 202,
    service_id: 55,
    item_type: 'submittal',
    item_title: 'Design RFI Response',
    status: 'completed',
  },
];

const setupMocks = async (page: any) => {
  const services = seedServices.map((s) => ({ ...s }));
  const reviews = seedReviews.map((r) => ({ ...r }));
  const items = seedItems.map((i) => ({ ...i }));

  await page.route('**/api/project/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(projectPayload),
    });
  });

  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/tasks/notes-view**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tasks: [], total: 0, page: 1, page_size: 5 }),
    });
  });

  await page.route('**/api/projects/1/reviews**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });

  await page.route('**/api/projects/1/services$', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(services),
      });
      return;
    }
    await route.continue();
  });

  // Lazy-loaded: Reviews only on drawer open
  await page.route('**/api/projects/1/services/55/reviews**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(reviews),
      });
      return;
    }
    await route.continue();
  });

  // Lazy-loaded: Items only on drawer open
  await page.route('**/api/projects/1/services/55/items**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(items),
      });
      return;
    }
    await route.continue();
  });

  // Reviews for service 56
  await page.route('**/api/projects/1/services/56/reviews**', async (route) => {
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

  // Items for service 56
  await page.route('**/api/projects/1/services/56/items**', async (route) => {
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
};

test.describe('Services drawer interaction (Linear UI)', () => {
  test('clicking service row opens drawer with details', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    // Navigate to Services tab
    await page.getByRole('tab', { name: 'Services' }).click();
    await expect(page.getByTestId('project-workspace-v2-service-row-55')).toBeVisible();

    // Click service row → Drawer should open
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    await expect(page.getByTestId('service-detail-drawer')).toBeVisible();

    // Verify drawer content
    await expect(page.getByText('SVC-01')).toBeVisible();
    await expect(page.getByText('Coordination')).toBeVisible();
    await expect(page.getByText('Design')).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });

  test('drawer tabs switch between reviews and items', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    await expect(page.getByTestId('service-detail-drawer')).toBeVisible();

    // Default: Reviews tab should be visible with review data
    await expect(page.getByText('Weekly Progress Report')).toHaveCount(0); // Items not shown yet
    const reviewsTab = page.getByTestId('service-drawer-tab-reviews');
    await expect(reviewsTab).toBeVisible();

    // Switch to Items tab
    const itemsTab = page.getByTestId('service-drawer-tab-items');
    await itemsTab.click();
    await expect(page.getByText('Weekly Progress Report')).toBeVisible();
    await expect(page.getByText('Design RFI Response')).toBeVisible();

    // Switch back to Reviews
    await reviewsTab.click();
    // Should show review cycle data (cycle number or assigned_to info)
    await expect(page.getByText('Coordination')).toBeVisible(); // Service name still visible
  });

  test('edit button on row opens dialog without affecting drawer state', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();

    // Drawer should NOT be open initially
    const drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toHaveCount(0);

    // Get the row and find the first button (Edit)
    const row = page.getByTestId('project-workspace-v2-service-row-55');
    const buttons = row.getByRole('button');
    const editButton = buttons.first();

    // Click Edit button
    await editButton.click();

    // Drawer should STILL not be open (edit button has stopPropagation)
    await expect(drawer).toHaveCount(0);

    // Row should still be visible and clickable
    await expect(row).toBeVisible();
  });

  test('clicking row multiple times maintains consistent drawer state', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();

    // Click row 1 → Drawer opens with service 55
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    const drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toBeVisible();
    await expect(page.getByText('SVC-01')).toBeVisible();

    // Click row 2 → Drawer updates with service 56
    await page.getByTestId('project-workspace-v2-service-row-56').click();
    await expect(drawer).toBeVisible();
    await expect(page.getByText('SVC-02')).toBeVisible();
    await expect(page.getByText('Audit')).toBeVisible();

    // Click row 1 again → Drawer updates back to service 55
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    await expect(drawer).toBeVisible();
    await expect(page.getByText('SVC-01')).toBeVisible();
    await expect(page.getByText('Coordination')).toBeVisible();
  });

  test('drawer finance section displays billing information correctly', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    const drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toBeVisible();

    // Finance section should show: Agreed Fee, Billed, Remaining
    // (Text may vary, check for currency formatted values)
    await expect(drawer).toContainText('12000'); // Agreed fee
    await expect(drawer).toContainText('3000'); // Billed
    await expect(drawer).toContainText('9000'); // Remaining
  });

  test('drawer close button closes drawer and allows reopening', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);
    await page.goto('/projects/1');

    await page.getByRole('tab', { name: 'Services' }).click();

    // Open drawer
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    let drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toBeVisible();

    // Close drawer via close button (X icon)
    const closeButton = drawer.locator('[aria-label="close"], [data-testid*="close"]').first();
    await closeButton.click();

    // Drawer should be gone
    drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toHaveCount(0);

    // Click row again → Drawer reopens
    await page.getByTestId('project-workspace-v2-service-row-55').click();
    drawer = page.getByTestId('service-detail-drawer');
    await expect(drawer).toBeVisible();
  });
});
