/**
 * Test Helpers for Playwright
 *
 * This file provides utility functions for common test operations
 * aligned with the Golden Set UI Standard.
 *
 * Usage:
 *   import { createService, editInlineCell, setupMocks } from './helpers';
 */

import { Page, expect } from '@playwright/test';

/* ============================================================================
   SELECTORS - Consistent accessor functions
   ============================================================================ */

export const selectors = {
  // Workspace Navigation
  workspace: {
    root: () => '[data-testid="project-workspace-v2-root"]',
    overviewTab: (page: Page) => page.getByRole('tab', { name: 'Overview' }),
    servicesTab: (page: Page) => page.getByRole('tab', { name: 'Services' }),
    deliverablesTab: (page: Page) => page.getByRole('tab', { name: 'Deliverables' }),
    reviewsTab: (page: Page) => page.getByRole('tab', { name: 'Reviews' }),
    invoiceTab: (page: Page) => page.getByRole('tab', { name: 'Invoice' }),
    tasksTab: (page: Page) => page.getByRole('tab', { name: 'Tasks' }),
  },

  // Service Management
  services: {
    list: (page: Page) => page.getByTestId('project-workspace-v2-services'),
    addButton: (page: Page) => page.getByRole('button', { name: /add service|new service/i }),
    row: (serviceId: number) => `[data-testid="workspace-service-row-${serviceId}"]`,
    editButton: (page: Page) => page.getByTestId('workspace-edit-service-button'),
    deleteButton: (serviceId: number) => `[data-testid="service-delete-${serviceId}"]`,
  },

  // Deliverables (Items)
  deliverables: {
    list: (page: Page) => page.getByTestId('project-workspace-v2-deliverables'),
    addButton: (page: Page) => page.getByTestId('deliverables-add-item-button'),
    row: (itemId: number | RegExp) =>
      typeof itemId === 'number'
        ? `[data-testid="deliverable-item-row-${itemId}"]`
        : `[data-testid*="${itemId}"]`,
    cell: (field: string, recordId: number) => `[data-testid="cell-${field}-${recordId}"]`,
    cellInput: (field: string, recordId: number) => `[data-testid="cell-${field}-${recordId}-input"]`,
    cellSave: (field: string, recordId: number) => `[data-testid="cell-${field}-${recordId}-save"]`,
    deleteButton: (page: Page) => page.getByRole('button', { name: /delete item/i }),
  },

  // Reviews
  reviews: {
    list: (page: Page) => page.getByTestId('project-workspace-v2-reviews'),
    row: (reviewId: number) => `[data-testid="project-workspace-v2-review-row-${reviewId}"]`,
    linkedIssues: (page: Page) => page.getByTestId('project-workspace-v2-review-linked-issues'),
  },

  // Projects Home
  projectsHome: {
    table: (page: Page) => page.getByTestId('projects-home-table'),
    row: (projectId: number) => `[data-testid="projects-home-row-${projectId}"]`,
    newProjectButton: (page: Page) => page.getByRole('button', { name: /new project|add project/i }),
  },

  // Forms & Dialogs
  forms: {
    dialog: (page: Page) => page.getByRole('dialog'),
    submitButton: (page: Page) => page.getByRole('button', { name: /submit|save|create/i }),
    cancelButton: (page: Page) => page.getByRole('button', { name: /cancel/i }),
    nameInput: (page: Page) => page.getByRole('textbox', { name: /name/i }),
    descriptionInput: (page: Page) => page.getByRole('textbox', { name: /description/i }),
    deleteConfirmButton: (page: Page) => page.getByRole('button', { name: /delete|confirm/i }),
  },

  // Status & Badges
  status: {
    badge: (recordId: number) => `[data-testid="status-badge-${recordId}"]`,
    blockerBadge: (reviewId: number) => `[data-testid="blocker-badge-${reviewId}"]`,
  },
};

/* ============================================================================
   INTERACTION HELPERS - Common user workflows
   ============================================================================ */

/**
 * Navigate to a project workspace
 */
export async function navigateToProjectWorkspace(page: Page, projectId: number) {
  await page.goto(`/workspace/${projectId}`);
  await expect(page.locator(selectors.workspace.root())).toBeVisible();
}

/**
 * Create a new service
 */
export async function createService(
  page: Page,
  data: {
    name: string;
    code?: string;
    description?: string;
    template?: string;
  }
) {
  // Click add service button
  const addBtn = selectors.services.addButton(page);
  await addBtn.click();

  // Wait for form to appear
  const dialog = await page.locator(selectors.forms.dialog()).waitFor();
  await expect(dialog).toBeVisible();

  // Fill form
  if (data.name) {
    const nameInput = page.getByRole('textbox', { name: /name/i });
    await nameInput.fill(data.name);
  }

  if (data.code) {
    const codeInput = page.getByRole('textbox', { name: /code/i });
    await codeInput.fill(data.code);
  }

  if (data.description) {
    const descInput = page.getByRole('textbox', { name: /description/i });
    await descInput.fill(data.description);
  }

  // Submit
  await selectors.forms.submitButton(page).click();

  // Wait for dialog to close
  await expect(page.locator(selectors.forms.dialog())).not.toBeVisible();
}

/**
 * Edit an inline cell
 */
export async function editInlineCell(
  page: Page,
  fieldName: string,
  recordId: number,
  newValue: string
) {
  const cellTestId = `cell-${fieldName}-${recordId}`;

  // Click cell to enter edit mode
  await page.getByTestId(cellTestId).click();

  // Fill new value
  const input = page.getByTestId(`${cellTestId}-input`);
  await input.fill(newValue);

  // Save
  const saveBtn = page.getByTestId(`${cellTestId}-save`);
  await saveBtn.click();

  // Wait for edit to complete
  await page.waitForTimeout(300);
}

/**
 * Add a new deliverable item
 */
export async function addDeliverableItem(page: Page, data: { title: string; type?: string }) {
  // Click add button
  await selectors.deliverables.addButton(page).click();

  // Find the new draft row
  const draftRow = page.getByTestId(/deliverable-item-row/).first();
  await expect(draftRow).toBeVisible();

  // Edit title
  const titleCell = draftRow.getByTestId(/cell-title/);
  await titleCell.click();

  const titleInput = draftRow.getByTestId(/cell-title.*-input/);
  await titleInput.fill(data.title);

  // Save
  const saveBtn = draftRow.getByRole('button', { name: 'Save' });
  await saveBtn.click();

  // Wait for save to complete
  await page.waitForTimeout(300);
}

/**
 * Delete a deliverable item
 */
export async function deleteDeliverableItem(page: Page, itemId: number) {
  const row = page.locator(selectors.deliverables.row(itemId));
  await expect(row).toBeVisible();

  // Open actions menu or click delete button
  const deleteBtn = row.getByRole('button', { name: /delete/i });
  await deleteBtn.click();

  // Confirm deletion if dialog appears
  const confirmBtn = page.getByRole('button', { name: /confirm|delete/i });
  if (await confirmBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
    await confirmBtn.click();
  }

  // Wait for deletion
  await page.waitForTimeout(300);
}

/**
 * Switch to a specific tab
 */
export async function switchTab(page: Page, tabName: 'Services' | 'Deliverables' | 'Reviews' | 'Overview') {
  await page.getByRole('tab', { name: tabName }).click();
  await page.waitForLoadState('networkidle');
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoading(page: Page, timeout = 10000) {
  await page.waitForLoadState('networkidle');
  // If there's a loading spinner, wait for it to disappear
  const spinner = page.getByRole('progressbar');
  if (await spinner.isVisible({ timeout: 1000 }).catch(() => false)) {
    await expect(spinner).not.toBeVisible({ timeout });
  }
}

/* ============================================================================
   MOCK SETUP HELPERS - API mocking for consistent test data
   ============================================================================ */

/**
 * Mock data structure
 */
export interface MockData {
  projects?: any[];
  services?: any[];
  items?: any[];
  reviews?: any[];
  users?: any[];
}

/**
 * Setup complete mock environment for workspace tests
 */
export async function setupWorkspaceMocks(page: Page, data: MockData = {}) {
  const defaultProjects = [
    {
      project_id: 1,
      project_name: 'Test Project Alpha',
      project_number: 'P-001',
      client_name: 'Test Client',
      status: 'Active',
      internal_lead: 101,
      project_type: 'Data Center',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
    },
  ];

  const defaultServices = [
    {
      service_id: 55,
      project_id: 1,
      service_code: 'BIM',
      service_name: 'Coordination Reviews',
      phase: 'Design',
      status: 'Active',
      progress_pct: 45,
      agreed_fee: 12000,
    },
  ];

  const defaultItems = [
    {
      item_id: 901,
      service_id: 55,
      item_name: 'Weekly Progress Report',
      item_type: 'report',
      status: 'Active',
      due_date: '2024-12-31',
    },
  ];

  const defaultUsers = [{ user_id: 101, name: 'Alex Lead' }];

  // Mock projects endpoint
  await page.route('**/api/projects**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data.projects || defaultProjects),
      });
      return;
    }
    await route.continue();
  });

  // Mock services endpoint
  await page.route('**/api/*/services', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data.services || defaultServices),
      });
      return;
    }
    await route.continue();
  });

  // Mock items endpoint
  await page.route('**/api/*/items', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data.items || defaultItems),
      });
      return;
    }
    await route.continue();
  });

  // Mock reviews endpoint
  await page.route('**/api/*/reviews', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data.reviews || []),
      });
      return;
    }
    await route.continue();
  });

  // Mock users endpoint
  await page.route('**/api/users', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data.users || defaultUsers),
      });
      return;
    }
    await route.continue();
  });
}

/**
 * Setup projects home page mocks
 */
export async function setupProjectsHomeMocks(page: Page, data: MockData = {}) {
  const defaultProjects = [
    {
      project_id: 1,
      project_name: 'Alpha Build',
      project_number: 'P-001',
      client_name: 'Client A',
      status: 'Active',
      internal_lead: 101,
      health_pct: 82,
      end_date: '2024-08-01',
    },
    {
      project_id: 2,
      project_name: 'Beta Tower',
      project_number: 'P-002',
      client_name: 'Client B',
      status: 'On Hold',
      internal_lead: 102,
      health_pct: 45,
      end_date: '2024-12-10',
    },
  ];

  // Mock projects summary
  await page.route('**/api/projects/summary**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data.projects || defaultProjects),
    });
  });

  // Mock aggregates
  await page.route('**/api/projects/aggregates**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_count: (data.projects || defaultProjects).length,
        sum_agreed_fee: 100000,
        sum_billed_to_date: 25000,
        sum_unbilled_amount: 75000,
        sum_earned_value: 30000,
        weighted_earned_value_pct: 30,
      }),
    });
  });

  // Mock timeline
  await page.route('**/api/dashboard/timeline**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        projects: data.projects || defaultProjects,
      }),
    });
  });

  // Mock users
  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data.users || []),
    });
  });
}

/* ============================================================================
   ASSERTION HELPERS - Common validation patterns
   ============================================================================ */

/**
 * Verify status badge has correct visual intent
 */
export async function assertStatusIntent(
  page: Page,
  recordId: number,
  expectedStatus: 'draft' | 'active' | 'blocked' | 'done' | 'overdue' | 'on-hold'
) {
  const badge = page.locator(selectors.status.badge(recordId));
  await expect(badge).toBeVisible();

  const classMap = {
    draft: /status-(neutral|muted)/,
    active: /status-primary/,
    blocked: /status-(destructive|warning)/,
    done: /status-success/,
    overdue: /status-destructive/,
    'on-hold': /status-(muted|secondary)/,
  };

  await expect(badge).toHaveClass(classMap[expectedStatus]);
}

/**
 * Verify item is in edit mode
 */
export async function assertInEditMode(page: Page, fieldName: string, recordId: number) {
  const input = page.getByTestId(`cell-${fieldName}-${recordId}-input`);
  await expect(input).toBeVisible();
  await expect(input).toBeFocused();
}

/**
 * Verify item saved successfully
 */
export async function assertSavedSuccessfully(page: Page, fieldName: string, recordId: number, expectedValue: string) {
  const cell = page.getByTestId(`cell-${fieldName}-${recordId}`);
  await expect(cell).toContainText(expectedValue);
  await expect(page.getByTestId(`cell-${fieldName}-${recordId}-input`)).not.toBeVisible();
}

/**
 * Verify empty state is displayed
 */
export async function assertEmptyState(page: Page, container: string) {
  const emptyState = page.locator(`[data-testid="${container}"] [data-testid*="empty-state"]`);
  await expect(emptyState).toBeVisible();
}

/**
 * Verify list contains N items
 */
export async function assertListItemCount(page: Page, listTestId: string, expectedCount: number) {
  const items = page.locator(`[data-testid="${listTestId}"] [data-testid*="row"]`);
  await expect(items).toHaveCount(expectedCount);
}

export default {
  selectors,
  navigateToProjectWorkspace,
  createService,
  editInlineCell,
  addDeliverableItem,
  deleteDeliverableItem,
  switchTab,
  waitForLoading,
  setupWorkspaceMocks,
  setupProjectsHomeMocks,
  assertStatusIntent,
  assertInEditMode,
  assertSavedSuccessfully,
  assertEmptyState,
  assertListItemCount,
};
