import { test, expect } from '@playwright/test';
import { setupWorkspaceMocks, navigateToProjectWorkspace, switchTab } from '../helpers';

const seedServices = [
  {
    service_id: 100,
    project_id: 1,
    service_code: 'SVC-100',
    service_name: 'Design Reviews',
    phase: 'Design',
    status: 'planned',
    progress_pct: 0,
    agreed_fee: 5000,
    review_anchor_date: '2025-02-01',
    review_count_planned: 4,
    review_count_total: 0,
    item_count_total: 0,
  },
  {
    service_id: 101,
    project_id: 1,
    service_code: 'SVC-101',
    service_name: 'Construction Coordination',
    phase: 'Construction',
    status: 'planned',
    progress_pct: 0,
    agreed_fee: 8000,
    review_anchor_date: '2025-03-01',
    review_count_planned: 2,
    review_count_total: 0,
    item_count_total: 0,
  },
];

const seedReviews = [
  {
    review_id: 1001,
    service_id: 100,
    project_id: 1,
    cycle_no: 1,
    planned_date: '2025-02-01',
    due_date: '2025-02-08',
    status: 'planned',
    is_billed: false,
    fee: 1250,
    fee_source: 'equal_split',
  },
  {
    review_id: 1002,
    service_id: 100,
    project_id: 1,
    cycle_no: 2,
    planned_date: '2025-02-08',
    due_date: '2025-02-15',
    status: 'planned',
    is_billed: false,
    fee: 1250,
    fee_source: 'equal_split',
  },
];

test.describe('Review Plan Workflow', () => {
  test('displays review and item counts in services table', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: seedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Services');

    // Verify deliverables column shows review and item counts
    const svc100Row = page.getByTestId('project-workspace-v2-service-row-100');
    await expect(svc100Row).toContainText('Reviews: 2');
    await expect(svc100Row).toContainText('Items: 0');

    const svc101Row = page.getByTestId('project-workspace-v2-service-row-101');
    await expect(svc101Row).toContainText('Reviews: 0');
    await expect(svc101Row).toContainText('Items: 0');
  });

  test('displays Review Plan accordion with pricing and cadence controls', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: seedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Services');

    // Click on a service to open ServiceEditView
    const svc100Row = page.getByTestId('project-workspace-v2-service-row-100');
    await svc100Row.click();

    // Verify Review Plan accordion exists and can be expanded
    const reviewPlanAccordion = page.getByRole('button', { name: /Review Plan/i });
    await expect(reviewPlanAccordion).toBeVisible();

    // Expand the accordion if not already expanded
    if (!(await reviewPlanAccordion.evaluate((el) => (el as any).ariaExpanded === 'true'))) {
      await reviewPlanAccordion.click();
    }

    // Verify pricing and cadence inputs are visible
    const agreedFeeInput = page.getByLabel('Agreed Fee');
    await expect(agreedFeeInput).toBeVisible();

    const anchorDateInput = page.getByLabel('Anchor Date');
    await expect(anchorDateInput).toBeVisible();

    const intervalInput = page.getByLabel('Interval');
    await expect(intervalInput).toBeVisible();

    const countInput = page.getByLabel('Planned Review Count');
    await expect(countInput).toBeVisible();

    // Verify "Apply Review Schedule" button exists
    const applyButton = page.getByRole('button', { name: /Apply Review Schedule/i });
    await expect(applyButton).toBeVisible();
  });

  test('shows fee per review calculation in real-time', async ({ page }) => {
    const seedData = {
      services: [
        {
          ...seedServices[0],
          agreed_fee: 4800,
        },
      ],
      reviews: [],
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Services');

    // Open service edit view
    const svc100Row = page.getByTestId('project-workspace-v2-service-row-100');
    await svc100Row.click();

    // Expand Review Plan accordion
    const reviewPlanAccordion = page.getByRole('button', { name: /Review Plan/i });
    await reviewPlanAccordion.click();

    // Get the fee display area
    const feePerReviewDisplay = page.getByText(/Fee per review/i);
    await expect(feePerReviewDisplay).toBeVisible();

    // With 4800 agreed fee and 4 reviews: 4800 / 4 = 1200
    await expect(feePerReviewDisplay).toContainText('1200');
  });

  test('shows calculated dates preview in Review Plan', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: [],
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Services');

    // Open service edit view
    const svc100Row = page.getByTestId('project-workspace-v2-service-row-100');
    await svc100Row.click();

    // Expand Review Plan accordion
    const reviewPlanAccordion = page.getByRole('button', { name: /Review Plan/i });
    await reviewPlanAccordion.click();

    // Verify calculated dates preview is visible
    const datesPreview = page.getByText(/Calculated Review Dates/i);
    await expect(datesPreview).toBeVisible();

    // Should show date labels for each review
    await expect(page.getByText(/Review 1:/)).toBeVisible();
    await expect(page.getByText(/Review 2:/)).toBeVisible();
  });

  test('displays fees with fee_source tooltip in deliverables tab', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: seedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Verify deliverables table is loaded
    const deliverableTable = page.getByTestId('workspace-deliverables-tab');
    await expect(deliverableTable).toBeVisible();

    // Find first review row
    const reviewRow = page.getByTestId('deliverable-row-review-1001');
    await expect(reviewRow).toBeVisible();

    // Hover over fee cell to see tooltip
    const feeCell = page.getByTestId('cell-fee-review-1001');
    await feeCell.hover();

    // Verify tooltip appears showing fee_source
    const tooltip = page.locator('text=Fee source: equal_split');
    await expect(tooltip).toBeVisible();
  });

  test('allows moving review to different service', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: seedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Find review row
    const reviewRow = page.getByTestId('deliverable-row-review-1001');
    await expect(reviewRow).toBeVisible();

    // Get service column and click to edit
    const serviceCell = reviewRow.locator('text=SVC-100');
    await serviceCell.click();

    // Open service dropdown
    const serviceSelect = reviewRow.getByRole('combobox');
    await serviceSelect.click();

    // Select different service
    await page.getByRole('option', { name: /SVC-101 · Construction Coordination/ }).click();

    // Verify service changed
    await expect(reviewRow).toContainText('SVC-101');
  });

  test('maintains modified state when page is reloaded', async ({ page }) => {
    const seedData = {
      services: seedServices,
      reviews: seedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Move review to different service
    const reviewRow = page.getByTestId('deliverable-row-review-1001');
    const serviceSelect = reviewRow.getByRole('combobox');
    await serviceSelect.click();
    await page.getByRole('option', { name: /SVC-101 · Construction Coordination/ }).click();

    // Wait for mutation to complete
    await page.waitForLoadState('networkidle');

    // Reload page
    await page.reload();

    // Verify review is still in new service after reload
    const refreshedRow = page.getByTestId('deliverable-row-review-1001');
    await expect(refreshedRow).toContainText('SVC-101');
  });

  test('shows modified indicator for user-changed reviews', async ({ page }) => {
    // Seed reviews with user-modified flag set
    const modifiedReviews = [
      {
        ...seedReviews[0],
        is_user_modified: true,
        user_modified_at: new Date().toISOString(),
      },
    ];

    const seedData = {
      services: seedServices,
      reviews: modifiedReviews,
    };

    await setupWorkspaceMocks(page, seedData);
    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Verify modified indicator is shown
    const reviewRow = page.getByTestId('deliverable-row-review-1001');
    const modifiedBadge = reviewRow.getByText(/modified/i);
    await expect(modifiedBadge).toBeVisible();
  });
});
