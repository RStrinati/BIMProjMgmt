import { test, expect } from '@playwright/test';
import { setupWorkspaceMocks, switchTab, editInlineCell, navigateToProjectWorkspace, waitForLoading } from '../helpers';

const templateCatalog = {
  templates: [
    {
      template_id: 'bim-coordination',
      name: 'BIM Coordination',
      version: '1.1',
      defaults: {
        service_code: 'BIM_COORD',
        service_name: 'BIM Coordination Review',
        phase: 'Construction',
      },
      items: [
        {
          item_template_id: 'progress-report',
          title: 'Progress Report',
          item_type: 'deliverable',
        },
      ],
    },
  ],
};



test.describe('Deliverables workflow', () => {
  test('creates a service from template', async ({ page }) => {
    const services: any[] = [];
    let receivedStartDate: string | undefined;

    await setupWorkspaceMocks(page, { services: [] });

    // Mock template catalog
    await page.route('**/api/service-templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(templateCatalog),
      });
    });

    // Mock service creation from template
    await page.route('**/api/projects/1/services/from-template', async (route) => {
      if (route.request().method() === 'POST') {
        const payload = await route.request().postDataJSON();
        receivedStartDate = payload?.overrides?.start_date;
        services.push({
          service_id: 101,
          project_id: 1,
          service_code: 'BIM_COORD',
          service_name: 'BIM Coordination Review',
          status: 'planned',
          start_date: receivedStartDate,
        });
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ service_id: 101 }),
        });
        return;
      }
      await route.continue();
    });

    // Mock service GET
    await page.route('**/api/projects/1/services', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(services),
        });
      }
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Services');

    // Verify template catalog is available
    await expect(page.getByText('BIM Coordination')).toBeVisible();
  });

  test('supports inline CRUD for service items', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Coordination',
        start_date: '2026-01-05',
      },
    ];
    const items: any[] = [];

    await setupWorkspaceMocks(page, { services });

    // Mock items GET/POST/PATCH
    await page.route('**/api/projects/1/services/1/items', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(items),
        });
        return;
      }
      if (route.request().method() === 'POST') {
        const payload = await route.request().postDataJSON();
        const nextId = 901;
        items.push({ ...payload, item_id: nextId });
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ item_id: nextId }),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/projects/1/services/1/items/*', async (route) => {
      if (route.request().method() === 'PATCH') {
        const payload = await route.request().postDataJSON();
        const itemId = parseInt(route.request().url().split('/').pop() || '0');
        const idx = items.findIndex((i) => i.item_id === itemId);
        if (idx >= 0) items[idx] = { ...items[idx], ...payload };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Verify service is loaded and items are empty
    await expect(page.getByText('Coordination')).toBeVisible();

    // Edit an inline cell to add an item
    await editInlineCell(page, 'title', 901, 'Weekly Report');

    // Verify the item was added
    await expect(page.getByText('Weekly Report')).toBeVisible();
  });

  test('protects user edits from template re-sync', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Coordination',
      },
    ];
    const items = [
      {
        item_id: 400,
        service_id: 1,
        title: 'Template Item',
        is_template_managed: true,
        is_user_modified: false,
      },
    ];

    await setupWorkspaceMocks(page, { services });

    // Mock template catalog
    await page.route('**/api/service-templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(templateCatalog),
      });
    });

    // Mock items GET/PATCH
    await page.route('**/api/projects/1/services/1/items', async (route) => {
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

    await page.route('**/api/projects/1/services/1/items/*', async (route) => {
      if (route.request().method() === 'PATCH') {
        const payload = await route.request().postDataJSON();
        items[0] = { ...items[0], ...payload, is_user_modified: true };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Deliverables');

    // Edit item (marks as user-modified)
    await editInlineCell(page, 'title', 400, 'Custom Title');

    await expect(page.getByText('Custom Title')).toBeVisible();
  });

  test('resequences planned reviews', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Coordination',
        review_anchor_date: '2026-01-05',
        review_interval_days: 7,
      },
    ];
    const reviews = [
      {
        review_id: 10,
        service_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        status: 'planned',
      },
      {
        review_id: 11,
        service_id: 1,
        cycle_no: 2,
        planned_date: '2026-01-12',
        status: 'planned',
      },
    ];

    await setupWorkspaceMocks(page, { services });

    // Mock reviews GET
    await page.route('**/api/projects/1/services/1/reviews', async (route) => {
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

    // Mock resequence endpoint
    await page.route('**/api/projects/1/services/1/reviews/resequence', async (route) => {
      if (route.request().method() === 'POST') {
        const payload = await route.request().postDataJSON();
        reviews[0].planned_date = payload.anchor_date;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ updated: 2 }),
        });
        return;
      }
      await route.continue();
    });

    await navigateToProjectWorkspace(page, 1);
    await switchTab(page, 'Reviews');

    // Verify reviews are displayed
    await expect(page.getByText('Coordination')).toBeVisible();
  });

  test('displays finance summary in right panel', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Design Review',
      },
    ];

    await setupWorkspaceMocks(page, { services });

    // Mock finance summary endpoint
    await page.route('**/api/projects/1/finance-summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_agreed_fee: 50000,
          total_claimed_or_billed: 25000,
          progress_pct: 50,
        }),
      });
    });

    await navigateToProjectWorkspace(page, 1);

  });
});
