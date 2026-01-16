import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Project Quality Register Tab
 *
 * Tests the Quality tab in Project Workspace v2, including:
 * - Tab visibility and accessibility
 * - Quality register table rendering
 * - Filter toggle (Attention / All)
 * - Row click and detail drawer
 */

test.describe('Project Quality Register', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to projects page
    await page.goto('/projects');

    // Wait for projects to load
    await page.waitForSelector('[data-testid="projects-list"]', { timeout: 10000 });

    // Click first project in the list to open workspace
    const firstProjectLink = page.locator('[data-testid="project-card"]').first();
    await firstProjectLink.click();

    // Wait for workspace to load
    await page.waitForSelector('[data-testid="project-workspace-v2-root"]', { timeout: 10000 });
  });

  test('should display Quality tab in Project Workspace', async ({ page }) => {
    // Check that Quality tab label is visible
    const qualityTab = page.locator('text=Quality');
    await expect(qualityTab).toBeVisible();
  });

  test('should load and display quality register table', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for register data to load
    await page.waitForSelector('[data-testid="quality-register-table"]', { timeout: 10000 });

    // Verify table is visible
    const registerTable = page.locator('[data-testid="quality-register-table"]');
    await expect(registerTable).toBeVisible();

    // Verify header row exists
    const headerRow = page.locator('[data-testid="quality-register-table"]').first();
    const modelNameHeader = headerRow.locator('text=Model Name');
    await expect(modelNameHeader).toBeVisible();
  });

  test('should display Attention and All filter buttons', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for filters to load
    await page.waitForSelector('[data-testid="quality-register-filter-mode"]', { timeout: 10000 });

    // Check Attention button is visible
    const attentionButton = page.locator('button:has-text("Attention")');
    await expect(attentionButton).toBeVisible();

    // Check All button is visible
    const allButton = page.locator('button:has-text("All")');
    await expect(allButton).toBeVisible();
  });

  test('should toggle between Attention and All filters', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for filters
    await page.waitForSelector('[data-testid="quality-register-filter-mode"]', { timeout: 10000 });

    // Start with Attention filter (default)
    let rowsBefore = page.locator('[data-testid="quality-register-row"]');
    const countBefore = await rowsBefore.count();

    // Click All button
    await page.locator('button:has-text("All models")').click();

    // Wait for UI to update
    await page.waitForTimeout(500);

    // Count rows after filter change
    let rowsAfter = page.locator('[data-testid="quality-register-row"]');
    const countAfter = await rowsAfter.count();

    // Verify count changed (All should have >= Attention count)
    expect(countAfter).toBeGreaterThanOrEqual(countBefore);

    // Toggle back to Attention
    await page.locator('button:has-text("Attention")').click();
    await page.waitForTimeout(500);

    // Verify original state is restored
    let rowsRestored = page.locator('[data-testid="quality-register-row"]');
    const countRestored = await rowsRestored.count();
    expect(countRestored).toBe(countBefore);
  });

  test('should open detail drawer on row click', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for table
    await page.waitForSelector('[data-testid="quality-register-table"]', { timeout: 10000 });

    // Click first data row
    const firstRow = page.locator('[data-testid^="quality-register-row"]').first();
    await firstRow.click();

    // Wait for drawer to open
    await page.waitForSelector('[data-testid="quality-register-detail-drawer"]', { timeout: 5000 });

    // Verify drawer is visible
    const drawer = page.locator('[data-testid="quality-register-detail-drawer"]');
    await expect(drawer).toBeVisible();

    // Verify drawer contains model details
    const modelDetails = page.locator('text=Model Details');
    await expect(modelDetails).toBeVisible();
  });

  test('should display model details in drawer', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for table
    await page.waitForSelector('[data-testid="quality-register-table"]', { timeout: 10000 });

    // Click first row
    const firstRow = page.locator('[data-testid^="quality-register-row"]').first();
    await firstRow.click();

    // Wait for drawer
    await page.waitForSelector('[data-testid="quality-register-detail-drawer"]', { timeout: 5000 });

    // Verify drawer contains expected sections
    const modelName = page.locator('text=MODEL NAME');
    const freshnessStatus = page.locator('text=FRESHNESS STATUS');
    const validationStatus = page.locator('text=VALIDATION STATUS');
    const controlModel = page.locator('text=CONTROL MODEL');

    await expect(modelName).toBeVisible();
    await expect(freshnessStatus).toBeVisible();
    await expect(validationStatus).toBeVisible();
    await expect(controlModel).toBeVisible();
  });

  test('should display correct column data in table', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for table
    await page.waitForSelector('[data-testid="quality-register-table"]', { timeout: 10000 });

    // Verify columns are present (by locating header cells)
    const headers = page.locator('[data-testid="quality-register-table"]').first().locator('>> *');

    // Check for key headers
    const freshnessCells = page.locator('text=Freshness');
    const modelNameCells = page.locator('text=Model Name');
    const disciplineCells = page.locator('text=Discipline');

    await expect(freshnessCells.first()).toBeVisible();
    await expect(modelNameCells.first()).toBeVisible();
    await expect(disciplineCells.first()).toBeVisible();
  });

  test('should display status chips for each model', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for table
    await page.waitForSelector('[data-testid="quality-register-table"]', { timeout: 10000 });

    // Look for status chips in first row
    const firstRow = page.locator('[data-testid^="quality-register-row"]').first();

    // Should have at least a Freshness chip
    const chips = firstRow.locator('div:has(> div):has-text("CURRENT|OUT_OF_DATE|DUE_SOON|UNKNOWN")');

    // Verify at least one chip exists
    const chipCount = await chips.count();
    expect(chipCount).toBeGreaterThan(0);
  });

  test('should show row count in filter controls', async ({ page }) => {
    // Click Quality tab
    await page.locator('text=Quality').click();

    // Wait for filters
    await page.waitForSelector('[data-testid="quality-register-filter-mode"]', { timeout: 10000 });

    // Check that count is displayed
    const countText = page.locator('text=/Showing .* of .* models/');
    await expect(countText).toBeVisible();
  });
});
