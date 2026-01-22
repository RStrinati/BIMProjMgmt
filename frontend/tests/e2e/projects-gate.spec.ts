import { test, expect } from '@playwright/test';

const attachConsoleGuard = (page: any) => {
  const errors: string[] = [];
  page.on('console', (msg: any) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  page.on('pageerror', (err: any) => {
    errors.push(err.message);
  });
  return errors;
};

test.describe('Projects feature flag gate', () => {
  test('flag OFF renders legacy UI and project detail', async ({ page }) => {
    const consoleErrors = attachConsoleGuard(page);
    await page.addInitScript(() => {
      window.localStorage.removeItem('ff_projects_panel');
    });

    await page.goto('/projects');
    await expect(page.getByTestId('projects-legacy-root')).toBeVisible();
    await expect(page.getByTestId('projects-panel-root')).toHaveCount(0);

    const legacyRoot = page.getByTestId('projects-legacy-root');
    const viewButtons = legacyRoot.getByRole('button', { name: 'View' });
    const viewCount = await viewButtons.count();
    if (viewCount > 0) {
      const firstView = viewButtons.first();
      await firstView.scrollIntoViewIfNeeded();
      await firstView.click();
      await page.waitForURL(/\/projects\/\d+/, { timeout: 10000 });
      await expect(page.getByText('Project #', { exact: false })).toBeVisible();
    } else {
      const emptyState = page.getByText('No projects found');
      if (await emptyState.count()) {
        await expect(emptyState).toBeVisible();
      }
    }

    expect(consoleErrors).toEqual([]);
  });

  test('flag ON renders panel UI and opens full project', async ({ page }) => {
    const consoleErrors = attachConsoleGuard(page);
    const projectRequests: string[] = [];

    page.on('request', (req) => {
      if (req.url().includes('/api/projects/')) {
        projectRequests.push(req.url());
      }
    });

    await page.addInitScript(() => {
      window.localStorage.setItem('ff_projects_panel', 'true');
    });

    await page.goto('/projects');
    await expect(page.getByTestId('projects-panel-root')).toBeVisible();
    await expect(page.getByTestId('projects-panel-details')).toBeVisible();

    const row = page.locator('[data-testid^="projects-panel-list-row-"]').first();
    await expect(row).toBeVisible();
    const projectId = await row.getAttribute('data-item-id');
    const beforeHoverCount = projectRequests.length;
    await row.hover();
    await page.waitForTimeout(750);
    const afterHoverCount = projectRequests.length;
    expect(afterHoverCount - beforeHoverCount).toBeLessThanOrEqual(2);

    await row.click();
    const openButton = page.getByRole('button', { name: 'Open full project' });
    await expect(openButton).toBeVisible();
    await openButton.click();
    await expect(page).toHaveURL(new RegExp(`/projects/${projectId}`));

    expect(consoleErrors).toEqual([]);
  });
});
