import { test, expect, type Page } from '@playwright/test';

const projectPayload = {
  project_id: 1,
  project_name: 'Delta Hub',
  status: 'active',
  start_date: '2026-01-05',
};

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
      pricing: {
        model: 'per_unit',
        unit_type: 'review',
        unit_qty: 4,
        unit_rate: 5500,
      },
      reviews: [
        {
          review_template_id: 'coord-review',
          count: 2,
          interval_days: 7,
        },
      ],
      items: [
        {
          item_template_id: 'progress-report',
          title: 'Progress Report',
          item_type: 'deliverable',
        },
      ],
      template_hash: 'mock-hash',
    },
  ],
  catalog: {
    bill_rules: ['per_unit_complete'],
    unit_types: ['review', 'deliverable'],
    phases: ['Construction'],
  },
};

const setupBaseMocks = async (page: Page) => {
  await page.route('**/api/projects/1', async (route) => {
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

  await page.route('**/api/invoice_batches**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/projects/1/finance-summary', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_agreed_fee: 0,
        total_claimed_or_billed: 0,
        progress_pct: 0,
        by_service: [],
      }),
    });
  });

  await page.route('**/api/projects/finance_grid**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        agreed_fee: 0,
        billed_to_date: 0,
        earned_value: 0,
        earned_value_pct: 0,
        invoice_pipeline: [],
        ready_this_month: { month: '2026-01', deliverables_count: 0, total_amount: 0, ready_count: 0, ready_amount: 0, issued_count: 0 },
      }),
    });
  });
};

test.describe('Deliverables workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });
  });

  test('creates a service from template with template metadata', async ({ page }) => {
    const services: any[] = [];
    const serviceItems: any[] = [];
    let receivedStartDate: string | undefined;

    await setupBaseMocks(page);

    await page.route('**/api/service-templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(templateCatalog),
      });
    });

    await page.route('**/api/projects/1/services', async (route) => {
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

    await page.route('**/api/projects/1/services/from-template', async (route) => {
      if (route.request().method() === 'POST') {
        const payload = await route.request().postDataJSON();
        receivedStartDate = payload?.overrides?.start_date;
        services.push({
          service_id: 101,
          project_id: 1,
          service_code: 'BIM_COORD',
          service_name: 'BIM Coordination Review',
          phase: 'Construction',
          status: 'planned',
          start_date: receivedStartDate,
          source_template_id: 'bim-coordination',
          source_template_version: '1.1',
          source_template_hash: 'mock-hash',
          template_mode: 'managed',
        });
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            service_id: 101,
            project_id: 1,
            template: {
              template_id: 'bim-coordination',
              name: 'BIM Coordination',
              version: '1.1',
              template_hash: 'mock-hash',
            },
            generated: {
              review_ids: [1, 2],
              item_ids: [201],
              review_count: 2,
              item_count: 1,
            },
          }),
        });
      }
    });

    await page.route('**/api/projects/1/services/101/generated-structure', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          service: services[0],
          binding: {
            binding_id: 500,
            template_id: 'bim-coordination',
            template_version: '1.1',
            template_hash: 'mock-hash',
            options_enabled: [],
            applied_at: '2026-01-19',
            applied_by_user_id: 1,
          },
          template: templateCatalog.templates[0],
          options_enabled: [],
          generated_reviews: [
            {
              review_id: 1,
              generated_key: 'coord-review:1',
              template_node_key: 'bim-coordination:1.1:base:coord-review:1',
              cycle_no: 1,
              planned_date: '2026-01-05',
              status: 'planned',
            },
          ],
          generated_items: [
            {
              item_id: 201,
              generated_key: 'progress-report',
              template_node_key: 'bim-coordination:1.1:base:progress-report',
              title: 'Progress Report',
              item_type: 'deliverable',
              status: 'planned',
            },
          ],
        }),
      });
    });

    await page.route('**/api/projects/1/services/101/reviews', async (route) => {
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

    await page.route('**/api/projects/1/services/101/items', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(serviceItems),
        });
        return;
      }
      await route.continue();
    });

    await page.goto('/projects/1/workspace/services');
    await page.getByTestId('workspace-add-service-menu-button').click();
    await page.getByRole('menuitem', { name: 'From template' }).click();

    await page.getByLabel('Creation Mode').click();
    await page.getByRole('option', { name: 'From Template' }).click();

    await page.getByLabel('Template').click();
    await page.getByRole('option', { name: 'BIM Coordination' }).click();

    await page.getByLabel('Start Date').fill('2026-01-15');
    await page.getByRole('button', { name: 'Create Service' }).click();

    await expect(page.getByTestId('workspace-service-row-101')).toBeVisible();
    await page.getByTestId('workspace-edit-service-button').click();
    await page.waitForURL(/\/workspace\/services\/101/);

    await expect(page.getByText('Template: BIM Coordination')).toBeVisible();
    expect(receivedStartDate).toBe('2026-01-15');
  });

  test('supports inline CRUD for service items in Deliverables', async ({ page }) => {
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

    await setupBaseMocks(page);

    await page.route('**/api/projects/1/services', async (route) => {
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
        items.unshift({ ...payload, item_id: nextId });
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ item_id: nextId }),
        });
        return;
      }
      if (route.request().method() === 'PATCH') {
        const url = route.request().url();
        const itemId = Number(url.split('/').pop());
        const payload = await route.request().postDataJSON();
        const index = items.findIndex((item) => item.item_id === itemId);
        if (index >= 0) {
          items[index] = { ...items[index], ...payload };
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      if (route.request().method() === 'DELETE') {
        const url = route.request().url();
        const itemId = Number(url.split('/').pop());
        const index = items.findIndex((item) => item.item_id === itemId);
        if (index >= 0) {
          items.splice(index, 1);
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/projects/1/services/1/reviews', async (route) => {
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

    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();
    await page.getByTestId('deliverables-add-item-button').click();

    const draftRow = page.getByTestId(/deliverable-item-row/).first();
    await draftRow.getByPlaceholder('Item title').fill('Weekly report');
    await draftRow.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Weekly report')).toBeVisible();

    await page.getByTestId('cell-item-title-901').click();
    await page.getByTestId('cell-item-title-901-input').fill('Updated report');
    await page.getByTestId('cell-item-title-901-save').click();

    await expect(page.getByText('Updated report')).toBeVisible();

    await page.getByRole('button', { name: 'Delete item' }).click();
    await expect(page.getByText('Updated report')).toHaveCount(0);
  });

  test('protects user edits from template re-sync', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Coordination',
        start_date: '2026-01-05',
      },
    ];
    const items = [
      {
        item_id: 400,
        service_id: 1,
        item_type: 'deliverable',
        title: 'Template Item',
        planned_date: '2026-01-05',
        status: 'planned',
        priority: 'medium',
        is_template_managed: true,
        is_user_modified: false,
      },
    ];

    await setupBaseMocks(page);

    await page.route('**/api/service-templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(templateCatalog),
      });
    });

    await page.route('**/api/projects/1/services', async (route) => {
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

    await page.route('**/api/projects/1/services/1/items', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(items),
        });
        return;
      }
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

    await page.route('**/api/projects/1/services/1/apply-template', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          added_reviews: [],
          updated_reviews: [],
          skipped_reviews: [{ review_id: 1, template_node_key: 'coord-review' }],
          added_items: [],
          updated_items: [],
          skipped_items: [{ item_id: 400, template_node_key: 'bim-coordination:1.1:base:progress-report' }],
          dry_run: false,
          mode: 'sync_and_update_managed',
        }),
      });
    });

    await page.route('**/api/projects/1/services/1/generated-structure', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          service: services[0],
          binding: {
            binding_id: 1,
            template_id: 'bim-coordination',
            template_version: '1.1',
            template_hash: 'mock-hash',
            options_enabled: [],
            applied_at: '2026-01-20',
          },
          template: templateCatalog.templates[0],
          options_enabled: [],
          generated_reviews: [],
          generated_items: [],
        }),
      });
    });

    await page.goto('/projects/1/workspace/deliverables');
    await page.getByTestId('cell-item-title-400').click();
    await page.getByTestId('cell-item-title-400-input').fill('Custom Title');
    await page.getByTestId('cell-item-title-400-save').click();

    await page.goto('/projects/1/workspace/services/1');
    await page.getByRole('button', { name: 'Re-sync Template' }).click();
    await page.getByRole('button', { name: 'Apply Re-sync' }).click();

    await expect(page.getByText('Custom Title')).toBeVisible();
  });

  test('resequences planned reviews without touching user-modified rows', async ({ page }) => {
    const services = [
      {
        service_id: 1,
        project_id: 1,
        service_code: 'SVC-01',
        service_name: 'Coordination',
        start_date: '2026-01-05',
        review_anchor_date: '2026-01-05',
        review_interval_days: 7,
        review_count_planned: 2,
      },
    ];
    const reviews = [
      {
        review_id: 10,
        service_id: 1,
        cycle_no: 1,
        planned_date: '2026-01-05',
        due_date: '2026-01-10',
        status: 'planned',
        is_user_modified: false,
      },
      {
        review_id: 11,
        service_id: 1,
        cycle_no: 2,
        planned_date: '2026-01-12',
        due_date: '2026-01-17',
        status: 'completed',
        is_user_modified: true,
      },
    ];

    await setupBaseMocks(page);

    await page.route('**/api/service-templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(templateCatalog),
      });
    });

    await page.route('**/api/projects/1/services', async (route) => {
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

    await page.route('**/api/projects/1/services/1/items', async (route) => {
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

    await page.route('**/api/projects/1/services/1/generated-structure', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          service: services[0],
          binding: {
            binding_id: 1,
            template_id: 'bim-coordination',
            template_version: '1.1',
            template_hash: 'mock-hash',
            options_enabled: [],
            applied_at: '2026-01-20',
          },
          template: templateCatalog.templates[0],
          options_enabled: [],
          generated_reviews: [],
          generated_items: [],
        }),
      });
    });

    await page.route('**/api/projects/1/services/1/reviews/resequence', async (route) => {
      const payload = await route.request().postDataJSON();
      if (payload.anchor_date === '2026-02-01') {
        reviews[0] = { ...reviews[0], planned_date: '2026-02-01' };
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          updated: 1,
          anchor_date: payload.anchor_date,
          interval_days: payload.interval_days,
          count: payload.count,
        }),
      });
    });

    await page.goto('/projects/1/workspace/services/1');
    await page.getByRole('button', { name: 'Re-sequence planned reviews' }).click();
    await page.getByLabel('Anchor date').fill('2026-02-01');
    await page.getByRole('button', { name: 'Apply' }).click();

    await expect(page.getByText('Planned: 2/1/2026')).toBeVisible();
  });

  test('uses finance summary rollups in the right panel', async ({ page }) => {
    await setupBaseMocks(page);

    await page.route('**/api/projects/1/services', async (route) => {
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

    await page.route('**/api/projects/1/finance-summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_agreed_fee: 10000,
          total_claimed_or_billed: 2500,
          progress_pct: 25,
          by_service: [],
        }),
      });
    });

    await page.goto('/projects/1');
    await expect(page.getByText('Agreed fee')).toBeVisible();
    await expect(page.getByText('$10,000.00')).toBeVisible();
    await expect(page.getByText('$2,500.00')).toBeVisible();
    await expect(page.getByText('25%')).toBeVisible();
  });
});
