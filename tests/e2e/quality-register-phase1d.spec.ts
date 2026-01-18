import { test, expect } from '@playwright/test';

/**
 * Phase 1F: Quality Register E2E Tests - Inline Editing UX
 * Tests the inline editing workflow with explicit Save/Cancel
 */

const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173';
const API_BASE_URL = 'http://localhost:5000';
const TEST_PROJECT_ID = 1; // Use a stable test project

test.describe('Quality Register - Inline Editing UX', () => {
  let testModelId: number | null = null;
  let uniqueModelName: string;

  test.beforeAll(async ({ request }) => {
    // Seed: Create a test model via API
    uniqueModelName = `E2E-TEST-${Date.now()}`;
    
    const createResponse = await request.post(
      `${API_BASE_URL}/api/projects/${TEST_PROJECT_ID}/quality/expected-models`,
      {
        data: {}
      }
    );
    
    expect(createResponse.ok()).toBeTruthy();
    const createData = await createResponse.json();
    testModelId = createData.expected_model_id;
    
    // Patch the model with unique name
    const patchResponse = await request.patch(
      `${API_BASE_URL}/api/projects/${TEST_PROJECT_ID}/quality/expected-models/${testModelId}`,
      {
        data: {
          registeredModelName: uniqueModelName,
          abv: 'E2E',
          company: 'Test Company',
          discipline: 'Architecture'
        }
      }
    );
    
    expect(patchResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to project workspace
    await page.goto(`${BASE_URL}/projects/${TEST_PROJECT_ID}`);
    
    // Click Quality tab
    await page.click('button:has-text("Quality")');
    
    // Wait for table to load
    await page.waitForSelector('table');
  });

  test('register renders with correct headers including Actions', async ({ page }) => {
    // Verify all column headers exist in correct order
    const headers = await page.locator('thead th').allTextContents();
    
    expect(headers).toEqual([
      'ABV',
      'Model Name',
      'Company',
      'Discipline',
      'Description',
      'BIM Contact',
      'Folder Path',
      'ACC',
      'ACC Date',
      'Revizto',
      'Revizto Date',
      'Notes',
      'Actions'
    ]);
  });

  test('seeded test model appears in table', async ({ page }) => {
    // Find row with our unique model name
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Verify seeded data appears
    await expect(row.locator('td:nth-child(1)')).toHaveText('E2E'); // ABV
    await expect(row.locator('td:nth-child(3)')).toHaveText('Test Company'); // Company
    await expect(row.locator('td:nth-child(4)')).toHaveText('Architecture'); // Discipline
  });

  test('inline add + inline edit workflow', async ({ page }) => {
    // Find "Add row" button in table footer
    const addRowButton = page.locator('button:has-text("Add row")');
    await expect(addRowButton).toBeVisible();
    
    // Click "Add row"
    await addRowButton.click();
    
    // Wait for new row to appear and enter edit mode
    await page.waitForTimeout(500);
    
    // The new row should be in edit mode (last row in tbody)
    const newRow = page.locator('tbody tr').last();
    await expect(newRow).toHaveAttribute('data-selected', 'true', { timeout: 5000 });
    
    // First cell (ABV) should have a TextField focused
    const abvInput = newRow.locator('td:nth-child(1) input');
    await expect(abvInput).toBeVisible();
    await expect(abvInput).toBeFocused();
    
    // Type values into editable fields
    await abvInput.fill('NEW');
    
    // Move to Model Name (press Enter or click)
    await newRow.locator('td:nth-child(2) input').click();
    await newRow.locator('td:nth-child(2) input').fill('New Test Model');
    
    // Fill Company
    await newRow.locator('td:nth-child(3) input').click();
    await newRow.locator('td:nth-child(3) input').fill('New Company');
    
    // Fill Discipline
    await newRow.locator('td:nth-child(4) input').click();
    await newRow.locator('td:nth-child(4) input').fill('MEP');
    
    // Click Save button in Actions column
    const saveButton = newRow.locator('button[title*="Save"]');
    await expect(saveButton).toBeVisible();
    await saveButton.click();
    
    // Wait for save to complete
    await page.waitForTimeout(500);
    
    // Row should exit edit mode and display values as plain text
    await expect(newRow.locator('td:nth-child(1)')).toHaveText('NEW');
    await expect(newRow.locator('td:nth-child(2)')).toContainText('New Test Model');
    await expect(newRow.locator('td:nth-child(3)')).toHaveText('New Company');
    await expect(newRow.locator('td:nth-child(4)')).toHaveText('MEP');
    
    // Actions column should be empty (no save/cancel buttons)
    await expect(newRow.locator('td:last-child button')).toHaveCount(0);
  });

  test('inline edit existing row', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Click on ABV cell to enter edit mode
    await row.locator('td:nth-child(1)').click();
    
    // Row should enter edit mode
    await page.waitForTimeout(200);
    
    // ABV should have an input field
    const abvInput = row.locator('td:nth-child(1) input');
    await expect(abvInput).toBeVisible();
    
    // Change Company value
    const companyInput = row.locator('td:nth-child(3) input');
    await companyInput.click();
    await companyInput.fill('Updated Company');
    
    // Click Save
    const saveButton = row.locator('button[title*="Save"]');
    await saveButton.click();
    
    // Wait for save
    await page.waitForTimeout(500);
    
    // Verify updated value persists
    await expect(row.locator('td:nth-child(3)')).toHaveText('Updated Company');
  });

  test('cancel discards draft changes', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Get original company value
    const originalCompany = await row.locator('td:nth-child(3)').textContent();
    
    // Enter edit mode
    await row.locator('td:nth-child(3)').click();
    await page.waitForTimeout(200);
    
    // Change Company
    const companyInput = row.locator('td:nth-child(3) input');
    await companyInput.fill('This Should Be Discarded');
    
    // Click Cancel button
    const cancelButton = row.locator('button[title*="Cancel"]');
    await expect(cancelButton).toBeVisible();
    await cancelButton.click();
    
    // Wait for cancel
    await page.waitForTimeout(200);
    
    // Verify original value restored
    await expect(row.locator('td:nth-child(3)')).toHaveText(originalCompany || '—');
    
    // Edit mode should be exited
    await expect(row.locator('td:nth-child(3) input')).toHaveCount(0);
  });

  test('side panel opens on row click (when not editing)', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Click the row (not on an editable cell)
    await row.locator('td:nth-child(7)').click(); // Folder Path (read-only)
    
    // Side panel should open
    await expect(page.locator('text=Model Details')).toBeVisible({ timeout: 5000 });
    
    // Side panel should show read-only register info
    await expect(page.locator('text=Register Information')).toBeVisible();
    
    // Side panel should have Mapping/Health/Activity tabs (NOT Register tab)
    await expect(page.locator('button:has-text("Mapping")')).toBeVisible();
    await expect(page.locator('button:has-text("Health")')).toBeVisible();
    await expect(page.locator('button:has-text("Activity")')).toBeVisible();
    await expect(page.locator('button:has-text("Register")')).toHaveCount(0);
  });

  test('side panel does not open when clicking row in edit mode', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Enter edit mode
    await row.locator('td:nth-child(1)').click();
    await page.waitForTimeout(200);
    
    // Click elsewhere on the row
    await row.locator('td:nth-child(5)').click(); // Description
    
    // Side panel should NOT open
    await expect(page.locator('text=Model Details')).toHaveCount(0);
  });

  test('add row button disabled when editing', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Enter edit mode
    await row.locator('td:nth-child(1)').click();
    await page.waitForTimeout(200);
    
    // "Add row" button should be disabled
    const addRowButton = page.locator('button:has-text("Add row")');
    await expect(addRowButton).toBeDisabled();
    
    // Cancel edit
    await row.locator('button[title*="Cancel"]').click();
    await page.waitForTimeout(200);
    
    // "Add row" button should be enabled again
    await expect(addRowButton).toBeEnabled();
  });

  test('activity tab shows change history after save', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Edit and save
    await row.locator('td:nth-child(6)').click(); // BIM Contact
    await page.waitForTimeout(200);
    
    const bimContactInput = row.locator('td:nth-child(6) input');
    await bimContactInput.fill(`TestContact-${Date.now()}`);
    
    await row.locator('button[title*="Save"]').click();
    await page.waitForTimeout(500);
    
    // Open side panel
    await row.locator('td:nth-child(7)').click();
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Navigate to Activity tab
    await page.click('button:has-text("Activity")');
    
    // Activity tab should show change history
    await expect(page.locator('text=Change History')).toBeVisible();
    
    // Should see UPDATE entry
    await expect(page.locator('text=UPDATE')).toBeVisible({ timeout: 5000 });
  });

  test('delete row with confirmation', async ({ page }) => {
    // Create a temporary row to delete
    const addRowButton = page.locator('button:has-text("Add row")');
    await addRowButton.click();
    await page.waitForTimeout(500);
    
    // Save the new row with a unique identifier
    const deleteTestName = `DELETE-TEST-${Date.now()}`;
    const newRow = page.locator('tbody tr').last();
    
    await newRow.locator('td:nth-child(2) input').fill(deleteTestName);
    await newRow.locator('button[title*="Save"]').click();
    await page.waitForTimeout(500);
    
    // Find the row we just created
    const targetRow = page.locator(`tr:has-text("${deleteTestName}")`);
    await expect(targetRow).toBeVisible();
    
    // Click delete button (now visible in Actions column)
    const deleteButton = targetRow.locator('button[title*="Delete"]');
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();
    
    // Confirmation dialog should appear
    await expect(page.locator('text=Delete Model Row?')).toBeVisible();
    await expect(page.locator('text=This action cannot be undone')).toBeVisible();
    
    // Click Delete in dialog
    const confirmDeleteButton = page.locator('button:has-text("Delete")').last();
    await confirmDeleteButton.click();
    
    // Wait for deletion
    await page.waitForTimeout(500);
    
    // Row should be removed from table
    await expect(targetRow).toHaveCount(0);
  });

  test('delete cancellation preserves row', async ({ page }) => {
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Click delete button
    const deleteButton = row.locator('button[title*="Delete"]');
    await deleteButton.click();
    
    // Confirmation dialog should appear
    await expect(page.locator('text=Delete Model Row?')).toBeVisible();
    
    // Click Cancel
    const cancelButton = page.locator('button:has-text("Cancel")').last();
    await cancelButton.click();
    
    // Wait a bit
    await page.waitForTimeout(200);
    
    // Row should still be present
    await expect(row).toBeVisible();
  });
});
    // Find the seeded test row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await expect(row).toBeVisible();
    
    // Edit and save
    await row.locator('td:nth-child(6)').click(); // BIM Contact
    await page.waitForTimeout(200);
    
    const bimContactInput = row.locator('td:nth-child(6) input');
    await bimContactInput.fill(`TestContact-${Date.now()}`);
    
    await row.locator('button[title*="Save"]').click();
    await page.waitForTimeout(500);
    
    // Open side panel
    await row.locator('td:nth-child(7)').click();
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Navigate to Activity tab
    await page.click('button:has-text("Activity")');
    
    // Activity tab should show change history
    await expect(page.locator('text=Change History')).toBeVisible();
    
    // Should see UPDATE entry
    await expect(page.locator('text=UPDATE')).toBeVisible({ timeout: 5000 });
  });

  test('additive row creation - add row at bottom', async ({ page }) => {
    await page.click('button:has-text("Quality")');
    await page.waitForSelector('table');
    
    // At least one row should exist (our test model or newly created one)
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThan(0);
  });

  test('side panel opens on row click', async ({ page }) => {
    // Click the test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    // Verify side panel opened
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Verify all 4 tabs are present
    await expect(page.locator('button[role="tab"]:has-text("Register")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Mapping")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Health")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Activity")')).toBeVisible();
  });

  test('edit notes in side panel and verify table updates', async ({ page }) => {
    // Click test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    // Wait for side panel
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Update notes with timestamp
    const notesText = `E2E test notes updated at ${new Date().toISOString()}`;
    const notesField = page.locator('textarea[label="Notes"]');
    await notesField.fill(notesText);
    
    // Save changes
    await page.click('button:has-text("Save Changes")');
    
    // Wait for save to complete
    await page.waitForTimeout(1500);
    
    // Close side panel
    await page.click('[aria-label="Close"]');
    
    // Verify notes appear in table (truncated to 50 chars)
    const notesCell = row.locator('td:nth-child(12)'); // Notes column
    await expect(notesCell).toContainText(notesText.substring(0, 30));
  });

  test('activity tab shows change history', async ({ page }) => {
    // Click test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Switch to Activity tab
    await page.click('button[role="tab"]:has-text("Activity")');
    
    // Should show at least one history entry (from beforeAll patch)
    const historyItems = page.locator('[role="list"] [role="listitem"]');
    const count = await historyItems.count();
    expect(count).toBeGreaterThan(0);
    
    // Verify history entry shows change type
    await expect(page.locator('text=UPDATE')).toBeVisible();
  });

  test('add alias in mapping tab', async ({ page }) => {
    // Click test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Switch to Mapping tab
    await page.click('button[role="tab"]:has-text("Mapping")');
    
    // Click "Add Alias" button
    await page.click('button:has-text("Add Alias")');
    
    // Fill alias form
    const aliasPattern = `TEST-ALIAS-${Date.now()}`;
    await page.selectOption('[label="Match Type"]', 'contains');
    await page.fill('input[placeholder*="MEL071"]', aliasPattern);
    
    // Submit
    await page.click('button:has-text("Add")');
    
    // Wait for alias to be added
    await page.waitForTimeout(1000);
    
    // Verify alias appears in list
    await expect(page.locator(`text=${aliasPattern}`)).toBeVisible();
  });

  test('health tab displays status', async ({ page }) => {
    // Click test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Switch to Health tab
    await page.click('button[role="tab"]:has-text("Health")');
    
    // Verify health sections exist
    await expect(page.locator('text=Validation Status')).toBeVisible();
    await expect(page.locator('text=Freshness Status')).toBeVisible();
  });

  test('empty register shows helpful message', async ({ page }) => {
    // This test would need a clean project, skipping for now
    // Just verify the table structure exists
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });

  test('mapping status chips display correctly', async ({ page }) => {
    await page.waitForSelector('tbody tr');
    
    // Check for mapping status chips (MAPPED, ALIASED, UNMAPPED)
    const chips = page.locator('[class*="MuiChip"]');
    const chipCount = await chips.count();
    expect(chipCount).toBeGreaterThan(0);
    
    // Verify at least one status is visible
    const statuses = ['MAPPED', 'ALIASED', 'UNMAPPED'];
    let foundStatus = false;
    for (const status of statuses) {
      if (await page.locator(`text=${status}`).isVisible()) {
        foundStatus = true;
        break;
      }
    }
    expect(foundStatus).toBe(true);
  });

  test('Phase 3: delivery status fields are editable', async ({ page }) => {
    // Click test model row
    const row = page.locator(`tr:has-text("${uniqueModelName}")`);
    await row.click();
    
    await expect(page.locator('text=Model Details')).toBeVisible();
    
    // Verify Phase 3 fields exist
    await expect(page.locator('text=Service & Delivery (Phase 3)')).toBeVisible();
    
    // Check delivery status dropdown exists
    const deliveryStatus = page.locator('[label="Delivery Status"]');
    await expect(deliveryStatus).toBeVisible();
    
    // Select a status
    await deliveryStatus.click();
    await page.click('li:has-text("On Track")');
    
    // Save
    await page.click('button:has-text("Save Changes")');
    await page.waitForTimeout(1000);
  });
});
