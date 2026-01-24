import { test, expect } from '@playwright/test';
import { setupProjectsHomeMocks, selectors, assertListItemCount } from '../helpers';

const seedProjects = [
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

test.describe('Projects home v2', () => {
  test('displays projects list and allows navigation', async ({ page }) => {
    await setupProjectsHomeMocks(page, { projects: seedProjects });
    await page.goto('/projects');

    // Verify home page loads
    await expect(page.getByTestId('projects-home-v2-root')).toBeVisible();

    // Verify projects are displayed
    await assertListItemCount(page, 'projects-home-table', 2);
    await expect(page.getByText('Alpha Build')).toBeVisible();
    await expect(page.getByText('Beta Tower')).toBeVisible();
  });

  test('filters projects by search term', async ({ page }) => {
    await setupProjectsHomeMocks(page, { projects: seedProjects });
    await page.goto('/projects');

    // Search for specific project
    const searchInput = page.getByRole('textbox', { name: /search/i });
    await searchInput.fill('Alpha');

    // Should show only Alpha Build
    await expect(page.getByText('Alpha Build')).toBeVisible();
    await expect(page.getByText('Beta Tower')).not.toBeVisible();
  });

  test('navigates to project detail on row click', async ({ page }) => {
    await setupProjectsHomeMocks(page, { projects: seedProjects });
    await page.goto('/projects');

    // Click first project row
    const projectRow = page.locator(selectors.projectsHome.row(1));
    await projectRow.click();

    // Should navigate to workspace
    await expect(page).toHaveURL(/\/workspace\/1|\/projects\/1/);
  });
});
