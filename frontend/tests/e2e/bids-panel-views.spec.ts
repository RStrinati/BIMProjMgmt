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
    created_at: '2024-05-01T10:00:00Z',
    updated_at: '2024-05-05T10:00:00Z',
    validity_days: 30,
  },
  {
    bid_id: 2,
    bid_name: 'Bid Beta',
    client_name: 'Client B',
    project_name: 'Project B',
    status: 'SUBMITTED',
    bid_type: 'PROPOSAL',
    probability: 80,
    owner_user_id: 102,
    created_at: '2024-05-10T10:00:00Z',
    updated_at: '2024-05-11T10:00:00Z',
    validity_days: 7,
  },
  {
    bid_id: 3,
    bid_name: 'Bid Gamma',
    client_name: 'Client C',
    project_name: 'Project C',
    status: 'AWARDED',
    bid_type: 'FEE_UPDATE',
    probability: 95,
    owner_user_id: 101,
    created_at: '2024-03-01T10:00:00Z',
    updated_at: '2024-03-05T10:00:00Z',
    validity_days: 14,
  },
  {
    bid_id: 4,
    bid_name: 'Bid Delta',
    client_name: 'Client D',
    project_name: 'Project D',
    status: 'LOST',
    bid_type: 'VARIATION',
    probability: 10,
    owner_user_id: 103,
    created_at: '2024-04-01T10:00:00Z',
    updated_at: '2024-04-02T10:00:00Z',
    validity_days: 21,
  },
];

const setupMocks = async (page: any) => {
  await page.route('**/api/health/schema', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ bid_module_ready: true }),
    });
  });

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
        body: JSON.stringify([
          { user_id: 101, name: 'Alex Lead' },
          { user_id: 102, name: 'Jordan Lead' },
          { user_id: 103, name: 'Casey Lead' },
        ]),
      });
      return;
    }
    await route.continue();
  });
};

test.describe('Bids panel views', () => {
  test('switching views filters rows and persists after reload', async ({ page }) => {
    await page.addInitScript(() => {
      const initKey = '__bids_panel_views_init';
      if (!window.localStorage.getItem(initKey)) {
        window.localStorage.clear();
        window.localStorage.setItem(initKey, 'true');
      }
      window.localStorage.setItem('ff_bids_panel', 'true');
      window.localStorage.setItem('current_user_id', '101');
    });
    await setupMocks(page);

    await page.goto('/bids');
    await expect(page.getByTestId('bids-panel-root')).toBeVisible();

    await page.getByTestId('bids-panel-view-pipeline').click();
    await expect(page.getByTestId('bids-panel-list-row-1')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-2')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-3')).toHaveCount(0);

    await page.getByTestId('bids-panel-view-high_probability').click();
    await expect(page.getByTestId('bids-panel-list-row-2')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-3')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-4')).toHaveCount(0);

    await page.getByTestId('bids-panel-view-my_bids').click();
    await expect(page.getByTestId('bids-panel-list-row-1')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-3')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-2')).toHaveCount(0);

    const searchInput = page.getByPlaceholder('Search bids...');
    await page.getByTestId('bids-panel-view-pipeline').click();
    await searchInput.fill('Beta');

    await page.reload();
    await expect(page.getByTestId('bids-panel-view-pipeline')).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByPlaceholder('Search bids...')).toHaveValue('Beta');
    await expect(page.getByTestId('bids-panel-list-row-2')).toBeVisible();
    await expect(page.getByTestId('bids-panel-list-row-1')).toHaveCount(0);
  });
});
