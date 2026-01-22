import { test, expect } from '@playwright/test';

const seedBids = [
  {
    bid_id: 1,
    bid_name: 'Bid Alpha',
    client_name: 'Client A',
    project_name: 'Project A',
    status: 'DRAFT',
    bid_type: 'PROPOSAL',
    probability: 40,
    owner_user_id: 101,
    owner_name: 'Alex Lead',
    created_at: '2024-05-01T10:00:00Z',
    updated_at: '2024-05-05T10:00:00Z',
    validity_days: 30,
  },
];

const setupSchemaMock = async (page: any) => {
  await page.route('**/api/health/schema', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ bid_module_ready: true }),
    });
  });
};

const setupLegacyMocks = async (page: any) => {
  await setupSchemaMock(page);

  await page.route('**/api/bids', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedBids),
      });
      return;
    }
    await route.continue();
  });

  await page.route('**/api/clients', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }
    await route.continue();
  });

  await page.route('**/api/projects', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }
    await route.continue();
  });

  await page.route('**/api/users', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }
    await route.continue();
  });
};

const setupPanelMocks = async (page: any) => {
  await setupSchemaMock(page);

  await page.route('**/api/bids', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedBids),
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
        body: JSON.stringify([{ user_id: 101, name: 'Alex Lead' }]),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/.*\/api\/bids\/\d+/, async (route) => {
    if (route.request().method() === 'GET') {
      const url = route.request().url();
      const id = Number(url.split('/').pop());
      const bid = seedBids.find((item) => item.bid_id === id) ?? seedBids[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(bid),
      });
      return;
    }
    await route.continue();
  });

  const emptyListResponse = [];
  const listRoutes = [
    /.*\/api\/bids\/\d+\/sections/,
    /.*\/api\/bids\/\d+\/scope-items/,
    /.*\/api\/bids\/\d+\/program-stages/,
    /.*\/api\/bids\/\d+\/billing-schedule/,
  ];
  for (const pattern of listRoutes) {
    await page.route(pattern, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(emptyListResponse),
        });
        return;
      }
      await route.continue();
    });
  }

  await page.route('**/api/bid_scope_templates', async (route) => {
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
};

test.describe('Bids feature flag gate', () => {
  test('flag OFF renders legacy UI', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_bids_panel', 'false');
    });
    await setupLegacyMocks(page);

    await page.goto('/bids');
    await expect(page.getByTestId('bids-legacy-root')).toBeVisible();
  });

  test('flag ON renders panel UI and opens full bid', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_bids_panel', 'true');
    });
    await setupPanelMocks(page);

    await page.goto('/bids');
    await expect(page.getByTestId('bids-panel-root')).toBeVisible();

    await page.getByTestId('bids-panel-list-row-1').click();
    const openButton = page.getByRole('button', { name: 'Open full bid' });
    await openButton.click();
    await expect(page).toHaveURL(/\/bids\/\d+/);
  });
});
