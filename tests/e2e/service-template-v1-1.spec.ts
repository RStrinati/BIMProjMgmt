import { test, expect } from '@playwright/test';

const getProjectIdFromUrl = (url: string) => {
  const match = url.match(/projects\/(\d+)/);
  if (!match) {
    throw new Error(`Unable to parse project ID from url: ${url}`);
  }
  return Number(match[1]);
};

const extractServices = (payload: any) => {
  if (Array.isArray(payload)) {
    return payload;
  }
  const candidates = [payload?.items, payload?.services, payload?.results, payload?.data];
  const found = candidates.find((entry) => Array.isArray(entry));
  return Array.isArray(found) ? found : [];
};

test.describe('Service Templates v1.1', () => {
  test('creates, re-syncs, and preserves manual edits', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForSelector('[data-testid="projects-list"]', { timeout: 10000 });

    const firstProjectLink = page.locator('[data-testid="project-card"]').first();
    await firstProjectLink.click();
    await page.waitForSelector('[data-testid="project-workspace-v2-root"]', { timeout: 10000 });

    const projectId = getProjectIdFromUrl(page.url());

    await page.locator('text=Services').click();
    await page.waitForSelector('[data-testid="workspace-services-tab"]', { timeout: 10000 });

    await page.click('[data-testid="workspace-add-service-menu-button"]');
    await page.click('text=From template');

    await page.waitForSelector('[data-testid="workspace-service-create-view"]', { timeout: 10000 });
    await page.click('button:has-text("Create Service")');

    await page.waitForURL(/workspace\/services/);
    const url = new URL(page.url());
    const selection = url.searchParams.get('sel') || '';
    const serviceMatch = selection.match(/service:(\d+)/);
    expect(serviceMatch).not.toBeNull();
    const serviceId = Number(serviceMatch?.[1]);

    const servicesResponse = await page.request.get(`/api/projects/${projectId}/services`);
    expect(servicesResponse.ok()).toBeTruthy();
    const servicesPayload = await servicesResponse.json();
    const services = extractServices(servicesPayload);
    const createdService = services.find((service: any) => service.service_id === serviceId);
    expect(createdService).toBeTruthy();
    expect(Number(createdService.agreed_fee)).toBe(22000);

    const reviewsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/reviews`
    );
    const reviews = await reviewsResponse.json();
    expect(reviews.length).toBeGreaterThan(0);
    const initialReviewCount = reviews.length;

    const itemsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/items`
    );
    const items = await itemsResponse.json();
    expect(items.length).toBeGreaterThan(0);
    const initialItemCount = items.length;

    const updatedDueDate = '2030-01-01';
    const targetItemId = items[0].item_id;
    const updateItemResponse = await page.request.patch(
      `/api/projects/${projectId}/services/${serviceId}/items/${targetItemId}`,
      { data: { due_date: updatedDueDate } }
    );
    expect(updateItemResponse.ok()).toBeTruthy();

    await page.click('[data-testid="workspace-edit-service-button"]');
    await page.waitForSelector('[data-testid="service-edit-view"]', { timeout: 10000 });

    await page.click('[data-testid="service-template-resync-button"]');
    await page.waitForSelector('text=Re-sync Template');

    await page.click('button:has-text("Apply Re-sync")');
    await page.waitForSelector('text=Re-sync Template', { state: 'detached', timeout: 10000 });

    const refreshedItemsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/items`
    );
    const refreshedItems = await refreshedItemsResponse.json();
    expect(refreshedItems.length).toBe(initialItemCount);
    const updatedItem = refreshedItems.find((item: any) => item.item_id === targetItemId);
    expect(updatedItem?.due_date).toBe(updatedDueDate);

    const refreshedReviewsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/reviews`
    );
    const refreshedReviews = await refreshedReviewsResponse.json();
    expect(refreshedReviews.length).toBe(initialReviewCount);

    await page.click('[data-testid="service-template-resync-button"]');
    await page.waitForSelector('text=Re-sync Template');

    await page.click('label:has-text("Revizto Licensing")');
    await page.click('button:has-text("Apply Re-sync")');
    await page.waitForSelector('text=Re-sync Template', { state: 'detached', timeout: 10000 });

    const optionItemsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/items`
    );
    const optionItems = await optionItemsResponse.json();
    expect(optionItems.length).toBe(initialItemCount + 1);

    await page.click('[data-testid="service-template-resync-button"]');
    await page.waitForSelector('text=Re-sync Template');
    await page.click('button:has-text("Apply Re-sync")');
    await page.waitForSelector('text=Re-sync Template', { state: 'detached', timeout: 10000 });

    const finalItemsResponse = await page.request.get(
      `/api/projects/${projectId}/services/${serviceId}/items`
    );
    const finalItems = await finalItemsResponse.json();
    expect(finalItems.length).toBe(initialItemCount + 1);
  });
});
