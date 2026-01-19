import { test, expect } from '@playwright/test';

const templatesPayload = {
  templates: [
    {
      template_id: 'bim-coordination',
      name: 'BIM Coordination',
      category: 'Coordination',
      version: '1.0',
      tags: ['review', 'coordination'],
      defaults: {
        service_code: 'BIM_COORD',
        service_name: 'BIM Coordination Review',
        phase: 'Construction',
        unit_type: 'review',
        unit_qty: 4,
        unit_rate: 5500,
        bill_rule: 'per_unit_complete',
        agreed_fee: 22000,
      },
      reviews: [
        {
          review_template_id: 'coord-review',
          name: 'Coordination Review',
          count: 4,
          status: 'planned',
          interval_days: 7,
        },
      ],
      items: [
        {
          item_template_id: 'progress-report',
          title: 'Progress Report',
          item_type: 'deliverable',
          status: 'planned',
          priority: 'medium',
        },
      ],
      options: [
        {
          option_id: 'revizto_licensing',
          name: 'Revizto Licensing',
          items: [
            {
              item_template_id: 'revizto-lic',
              title: 'Revizto Licensing',
              item_type: 'license',
              status: 'planned',
              priority: 'medium',
            },
          ],
        },
      ],
      template_hash: 'mock-hash',
    },
  ],
  catalog: {
    bill_rules: ['per_unit_complete', 'on_setup', 'on_completion'],
    unit_types: ['review', 'lump_sum', 'license'],
    phases: ['Construction', 'Design', 'Handover'],
  },
};

test.describe('Workspace Services - Templates', () => {
  test('create service from template and add optional item', async ({ page }) => {
    const services: any[] = [];
    const generatedItems = [
      {
        item_id: 501,
        generated_key: 'progress-report',
        title: 'Progress Report',
        item_type: 'deliverable',
        status: 'planned',
      },
    ];

    await page.route(/.*\/api\/projects\/\d+$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 7,
            project_name: 'Template Project',
            project_number: 'P-007',
            client_name: 'Test Client',
            status: 'Active',
            internal_lead: 101,
            total_service_agreed_fee: 0,
            total_service_billed_amount: 0,
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/users', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ user_id: 101, name: 'Test User' }]),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/service-templates', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(templatesPayload),
        });
        return;
      }
      await route.continue();
    });

    await page.route(/.*\/api\/projects\/\d+\/services$/, async (route) => {
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

    await page.route(/.*\/api\/projects\/\d+\/services\/from-template$/, async (route) => {
      if (route.request().method() === 'POST') {
        services.push({
          service_id: 101,
          project_id: 7,
          service_code: 'BIM_COORD',
          service_name: 'BIM Coordination Review',
          phase: 'Construction',
          status: 'planned',
          agreed_fee: 22000,
          billed_amount: 0,
          agreed_fee_remaining: 22000,
          billing_progress_pct: 0,
        });

        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            service_id: 101,
            project_id: 7,
            template: {
              template_id: 'bim-coordination',
              name: 'BIM Coordination',
              version: '1.0',
              template_hash: 'mock-hash',
            },
            binding: {
              binding_id: 2001,
              template_id: 'bim-coordination',
              template_version: '1.0',
              template_hash: 'mock-hash',
              options_enabled: ['revizto_licensing'],
              applied_at: '2026-01-19',
              applied_by_user_id: 101,
            },
            generated: {
              review_ids: [1, 2, 3, 4],
              item_ids: [501],
              review_count: 4,
              item_count: 1,
            },
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route(/.*\/api\/projects\/\d+\/services\/101\/generated-structure$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            service: services[0],
            binding: {
              binding_id: 2001,
              template_id: 'bim-coordination',
              template_version: '1.0',
              template_hash: 'mock-hash',
              options_enabled: ['revizto_licensing'],
              applied_at: '2026-01-19',
              applied_by_user_id: 101,
            },
            template: templatesPayload.templates[0],
            options_enabled: ['revizto_licensing'],
            generated_reviews: [],
            generated_items: generatedItems,
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route(/.*\/api\/projects\/\d+\/services\/101\/items$/, async (route) => {
      if (route.request().method() === 'POST') {
        generatedItems.push({
          item_id: 502,
          generated_key: 'revizto_licensing:revizto-lic',
          title: 'Revizto Licensing',
          item_type: 'license',
          status: 'planned',
        });

        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ item_id: 502 }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto('/projects/7/workspace/services');

    await page.getByTestId('workspace-add-service-menu-button').click();
    await page.getByRole('menuitem', { name: 'From template' }).click();

    await expect(page.getByTestId('workspace-service-create-view')).toBeVisible();

    await page.getByLabel('Creation Mode').click();
    await page.getByRole('option', { name: 'From Template' }).click();

    await page.getByLabel('Template').click();
    await page.getByRole('option', { name: 'BIM Coordination' }).click();

    await page.getByLabel('Revizto Licensing').check();

    await page.getByRole('button', { name: 'Create Service' }).click();

    await expect(page.getByTestId('workspace-service-row-101')).toBeVisible();
    await expect(page.getByText('BIM Coordination Review')).toBeVisible();

    await page.getByTestId('workspace-edit-service-button').click();
    await page.waitForURL(/\/workspace\/services\/101/);

    await expect(page.getByText('Template: BIM Coordination')).toBeVisible();

    await page.getByLabel('Add Item From Template').click();
    await page.getByRole('option', { name: /Revizto Licensing/ }).click();
    await page.getByRole('button', { name: 'Add Item' }).click();

    await expect(page.getByText('Revizto Licensing')).toBeVisible();

    await page.reload();
    await expect(page.getByText('Revizto Licensing')).toBeVisible();
  });
});
