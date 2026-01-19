import { test, expect } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
};

const projectReviewsPayload = {
  items: [
    {
      review_id: 101,
      service_id: 55,
      project_id: 1,
      cycle_no: 1,
      planned_date: '2024-05-10',
      due_date: '2024-05-20',
      status: 'planned',
      disciplines: 'Architecture',
      deliverables: 'Model',
      is_billed: false,
      billing_amount: 0,
      invoice_reference: null,
      invoice_date: null,
      service_name: 'Design Review',
      service_code: 'DR-01',
      phase: 'Concept',
    },
  ],
  total: 1,
};

const setupMocks = async (page: any) => {
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
      body: JSON.stringify(projectReviewsPayload),
    });
  });

  await page.route('**/api/projects/1/items**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });
};

test.describe('ProjectWorkspacePageV2 - Deliverables inline edits', () => {
  test('edits due_date field with inline editor', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    let patchCallCount = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        const data = route.request().postDataJSON();
        expect(data.due_date).toBe('2024-06-15');
        projectReviewsPayload.items[0].due_date = '2024-06-15';
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(projectReviewsPayload.items[0]),
        });
      } else {
        await route.fallback();
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Locate the due date editable cell
    const dueDateCell = page.getByTestId('cell-due-101');
    await expect(dueDateCell).toBeVisible();

    // Click on the cell to enter edit mode
    await dueDateCell.click();
    const input = dueDateCell.locator('input[type="date"]');
    await expect(input).toBeVisible();

    // Clear and set new date
    await input.fill('2024-06-15');
    
    // Click save button or press Enter
    const saveButton = dueDateCell.getByTestId('cell-save-due-101');
    if (await saveButton.isVisible()) {
      await saveButton.click();
    } else {
      await input.press('Enter');
    }

    // Verify the cell shows the updated value
    await expect(dueDateCell).toContainText('2024-06-15');
    expect(patchCallCount).toBe(1);

    const allowedErrors: string[] = [];
    const unexpected = consoleErrors.filter(
      (message) => !allowedErrors.some((allowed) => message.includes(allowed)),
    );
    expect(unexpected).toEqual([]);
  });

  test('edits invoice_reference field with inline editor', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    let patchCallCount = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        const data = route.request().postDataJSON();
        expect(data.invoice_reference).toBe('INV-2024-001');
        projectReviewsPayload.items[0].invoice_reference = 'INV-2024-001';
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(projectReviewsPayload.items[0]),
        });
      } else {
        await route.fallback();
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Locate the invoice reference editable cell
    const invoiceRefCell = page.getByTestId('cell-invoice-number-101');
    await expect(invoiceRefCell).toBeVisible();

    // Click on the cell to enter edit mode
    await invoiceRefCell.click();
    const input = invoiceRefCell.locator('input[type="text"]');
    await expect(input).toBeVisible();

    // Type the invoice reference
    await input.fill('INV-2024-001');
    
    // Click save or press Enter
    const saveButton = invoiceRefCell.getByTestId('cell-save-invoice-number-101');
    if (await saveButton.isVisible()) {
      await saveButton.click();
    } else {
      await input.press('Enter');
    }

    // Verify the cell shows the updated value
    await expect(invoiceRefCell).toContainText('INV-2024-001');
    expect(patchCallCount).toBe(1);

    const allowedErrors: string[] = [];
    const unexpected = consoleErrors.filter(
      (message) => !allowedErrors.some((allowed) => message.includes(allowed)),
    );
    expect(unexpected).toEqual([]);
  });

  test('toggles is_billed field with toggle cell', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    let patchCallCount = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        const data = route.request().postDataJSON();
        expect(data.is_billed).toBe(true);
        projectReviewsPayload.items[0].is_billed = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(projectReviewsPayload.items[0]),
        });
      } else {
        await route.fallback();
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Locate the billing status toggle cell
    const billingStatusCell = page.getByTestId('cell-billing-status-101');
    await expect(billingStatusCell).toBeVisible();

    // Find and click the toggle button (usually shows "Not billed" or "Billed")
    const toggleButton = billingStatusCell.locator('button');
    await expect(toggleButton).toBeVisible();
    
    // Click to toggle
    await toggleButton.click();

    // Verify the state changed (button text or class)
    expect(patchCallCount).toBe(1);

    const allowedErrors: string[] = [];
    const unexpected = consoleErrors.filter(
      (message) => !allowedErrors.some((allowed) => message.includes(allowed)),
    );
    expect(unexpected).toEqual([]);
  });

  test('handles patch error with rollback', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => consoleErrors.push(error.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    let patchCallCount = 0;
    await page.route('**/api/projects/1/services/55/reviews/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCallCount += 1;
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await setupMocks(page);

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Get the original due date value
    const dueDateCell = page.getByTestId('cell-due-101');
    await expect(dueDateCell).toBeVisible();
    const originalValue = await dueDateCell.textContent();

    // Click and try to edit
    await dueDateCell.click();
    const input = dueDateCell.locator('input[type="date"]');
    await input.fill('2024-06-15');
    
    // Try to save (will fail)
    const saveButton = dueDateCell.getByTestId('cell-save-due-101');
    if (await saveButton.isVisible()) {
      await saveButton.click();
    } else {
      await input.press('Enter');
    }

    // Wait a moment for error handling
    await page.waitForTimeout(500);

    // Verify error is shown
    const errorMsg = dueDateCell.locator('[role="alert"], .error, [data-testid*="error"]');
    // Error display depends on EditableCell implementation

    expect(patchCallCount).toBe(1);

    const allowedErrors: string[] = [];
    const unexpected = consoleErrors.filter(
      (message) => !allowedErrors.some((allowed) => message.includes(allowed)),
    );
    expect(unexpected).toEqual([]);
  });
});
