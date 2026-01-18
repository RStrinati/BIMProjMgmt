# Services Tab Linear UI - Deployment & Testing Guide

## Quick Start (5 minutes)

### 1. Copy New Files
```bash
# Already created:
# - frontend/src/components/ProjectServices/ServicesSummaryStrip.tsx
# - frontend/src/components/ProjectServices/ServicesListRow.tsx
# - frontend/src/components/ProjectServices/ServiceDetailDrawer.tsx
# - frontend/src/components/ProjectServices/index.ts
# - frontend/src/components/ProjectServicesTab_Linear.tsx
```

### 2. Update Import in ProjectDetailPage
**File**: `frontend/src/pages/ProjectDetailPage.tsx`

Find this line (around line 34):
```typescript
import { ProjectServicesTab } from '@/components/ProjectServicesTab';
```

Change to:
```typescript
import { ProjectServicesTab } from '@/components/ProjectServicesTab_Linear';
```

### 3. Test in Browser
```bash
cd frontend
npm install   # if needed
npm run dev
```

Navigate to `/projects/{id}` and click the Services tab. Click a service row to open the drawer.

---

## Detailed Testing Guide

### Unit Test Template (add to test suite)

```typescript
// tests/components/ProjectServices/ServicesSummaryStrip.test.tsx
import { render, screen } from '@testing-library/react';
import { ServicesSummaryStrip } from '@/components/ProjectServices/ServicesSummaryStrip';

describe('ServicesSummaryStrip', () => {
  const mockProps = {
    totalAgreed: 100000,
    totalBilled: 80000,
    totalRemaining: 20000,
    progress: 80,
    isPartialSummary: false,
    formatCurrency: (val) => `$${val?.toLocaleString()}`,
    formatPercent: (val) => `${val?.toFixed(1)}%`,
  };

  test('renders summary values correctly', () => {
    render(<ServicesSummaryStrip {...mockProps} />);
    expect(screen.getByText('$100,000')).toBeInTheDocument();
    expect(screen.getByText('$80,000')).toBeInTheDocument();
    expect(screen.getByText('$20,000')).toBeInTheDocument();
  });

  test('displays progress percentage', () => {
    render(<ServicesSummaryStrip {...mockProps} />);
    expect(screen.getByText('80.0%')).toBeInTheDocument();
  });

  test('shows partial summary warning when isPartialSummary=true', () => {
    render(<ServicesSummaryStrip {...mockProps} isPartialSummary={true} />);
    expect(screen.getByText(/Totals reflect the current page/)).toBeInTheDocument();
  });
});

// tests/components/ProjectServices/ServicesListRow.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ServicesListRow } from '@/components/ProjectServices/ServicesListRow';

describe('ServicesListRow', () => {
  const mockService = {
    service_id: 1,
    service_code: 'SRV001',
    service_name: 'Design Review',
    phase: 'Phase 1',
    status: 'completed',
    agreed_fee: 10000,
    billed_amount: 8000,
    billing_progress_pct: 80,
    agreed_fee_remaining: 2000,
  };

  test('renders service data', () => {
    render(
      <table>
        <tbody>
          <ServicesListRow
            service={mockService}
            onRowClick={jest.fn()}
            onEditService={jest.fn()}
            onDeleteService={jest.fn()}
            formatCurrency={(v) => `$${v}`}
            formatPercent={(v) => `${v}%`}
            getStatusColor={() => 'success'}
          />
        </tbody>
      </table>
    );
    expect(screen.getByText('SRV001')).toBeInTheDocument();
    expect(screen.getByText('Design Review')).toBeInTheDocument();
  });

  test('calls onRowClick when row is clicked', () => {
    const mockClick = jest.fn();
    const { getByRole } = render(
      <table>
        <tbody>
          <ServicesListRow
            service={mockService}
            onRowClick={mockClick}
            onEditService={jest.fn()}
            onDeleteService={jest.fn()}
            formatCurrency={(v) => `$${v}`}
            formatPercent={(v) => `${v}%`}
            getStatusColor={() => 'success'}
          />
        </tbody>
      </table>
    );
    fireEvent.click(getByRole('row'));
    expect(mockClick).toHaveBeenCalledWith(mockService);
  });
});

// tests/components/ProjectServices/ServiceDetailDrawer.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ServiceDetailDrawer } from '@/components/ProjectServices/ServiceDetailDrawer';

describe('ServiceDetailDrawer', () => {
  const mockService = {
    service_id: 1,
    service_code: 'SRV001',
    service_name: 'Design Review',
    phase: 'Phase 1',
    status: 'completed',
    agreed_fee: 10000,
    billed_amount: 8000,
    billing_progress_pct: 80,
    agreed_fee_remaining: 2000,
  };

  test('renders drawer with service info when open', () => {
    render(
      <ServiceDetailDrawer
        open={true}
        service={mockService}
        projectId={1}
        onClose={jest.fn()}
        onEditService={jest.fn()}
        onDeleteService={jest.fn()}
        onAddReview={jest.fn()}
        onEditReview={jest.fn()}
        onDeleteReview={jest.fn()}
        onAddItem={jest.fn()}
        onEditItem={jest.fn()}
        onDeleteItem={jest.fn()}
        formatCurrency={(v) => `$${v}`}
        formatPercent={(v) => `${v}%`}
        getStatusColor={() => 'success'}
      />
    );
    expect(screen.getByText('SRV001')).toBeInTheDocument();
    expect(screen.getByText('Design Review')).toBeInTheDocument();
  });

  test('does not render when open=false', () => {
    const { container } = render(
      <ServiceDetailDrawer
        open={false}
        service={mockService}
        projectId={1}
        onClose={jest.fn()}
        onEditService={jest.fn()}
        onDeleteService={jest.fn()}
        onAddReview={jest.fn()}
        onEditReview={jest.fn()}
        onDeleteReview={jest.fn()}
        onAddItem={jest.fn()}
        onEditItem={jest.fn()}
        onDeleteItem={jest.fn()}
        formatCurrency={(v) => `$${v}`}
        formatPercent={(v) => `${v}%`}
        getStatusColor={() => 'success'}
      />
    );
    expect(container.firstChild).toBeEmptyDOMElement();
  });

  test('calls onClose when close button clicked', () => {
    const mockClose = jest.fn();
    render(
      <ServiceDetailDrawer
        open={true}
        service={mockService}
        projectId={1}
        onClose={mockClose}
        onEditService={jest.fn()}
        onDeleteService={jest.fn()}
        onAddReview={jest.fn()}
        onEditReview={jest.fn()}
        onDeleteReview={jest.fn()}
        onAddItem={jest.fn()}
        onEditItem={jest.fn()}
        onDeleteItem={jest.fn()}
        formatCurrency={(v) => `$${v}`}
        formatPercent={(v) => `${v}%`}
        getStatusColor={() => 'success'}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(mockClose).toHaveBeenCalled();
  });

  test('switches between Reviews and Items tabs', () => {
    render(
      <ServiceDetailDrawer
        open={true}
        service={mockService}
        projectId={1}
        onClose={jest.fn()}
        onEditService={jest.fn()}
        onDeleteService={jest.fn()}
        onAddReview={jest.fn()}
        onEditReview={jest.fn()}
        onDeleteReview={jest.fn()}
        onAddItem={jest.fn()}
        onEditItem={jest.fn()}
        onDeleteItem={jest.fn()}
        formatCurrency={(v) => `$${v}`}
        formatPercent={(v) => `${v}%`}
        getStatusColor={() => 'success'}
      />
    );
    
    // Initially on Reviews tab
    expect(screen.getByText('Review Cycles')).toBeInTheDocument();
    
    // Click Items tab
    fireEvent.click(screen.getByRole('tab', { name: /items/i }));
    expect(screen.getByText('Items / Deliverables')).toBeInTheDocument();
  });
});
```

### Manual Testing Checklist

#### Phase A: Visual (5 minutes)
- [ ] Navigate to `/projects/{id}`
- [ ] Open Services tab
- [ ] Verify summary strip appears (not 3 cards)
- [ ] Verify summary strip has: Total Contract, Billed, Remaining, Progress %
- [ ] Verify progress bar is thin (~4px)
- [ ] Verify table has 1px border (not Paper elevation)
- [ ] Verify table header has no background color
- [ ] Hover over service row → subtle background change (action.hover)
- [ ] Verify row height is compact
- [ ] Verify pagination works
- [ ] Click next page → summary recalculates

#### Phase B: Interaction (10 minutes)
- [ ] Click a service row → Drawer opens on right
- [ ] Drawer shows: service code, name, status, phase
- [ ] Drawer shows Finance section: Agreed Fee, Billed, Remaining, Progress
- [ ] Drawer has 2 tabs: Reviews, Items
- [ ] Click "Reviews" tab → Shows existing reviews in compact table
- [ ] Click "Items" tab → Shows existing items in compact table
- [ ] Click "+ Add" in Reviews → Dialog opens (original dialog, preserved)
- [ ] Create review → Drawer re-fetches and shows new review
- [ ] Click "Edit" on review → Dialog opens with pre-filled data
- [ ] Click "Delete" on review → Confirmation dialog, then removes
- [ ] Same for Items (add/edit/delete)
- [ ] Click "Edit Service" in drawer footer → Service edit dialog opens
- [ ] Edit service name → Drawer closes, list updates, re-open drawer → new name shown
- [ ] Click "Delete Service" in drawer footer → Confirmation, then drawer closes
- [ ] Re-open services list → Service no longer there

#### Phase C: Template & Pagination (5 minutes)
- [ ] Click "Add From Template" button
- [ ] Select template, click Apply
- [ ] Verify new services appear in list
- [ ] Verify summary totals updated
- [ ] Change pagination to 5 items/page
- [ ] Verify list shows 5 rows
- [ ] Verify page control works

#### Edge Cases (5 minutes)
- [ ] Service with no reviews → Items tab shows "No items yet"
- [ ] Service with no notes → Notes section not shown in drawer
- [ ] Service with no phase → Shows "—"
- [ ] Click drawer close → Drawer slides out
- [ ] Click Edit service → Dialog opens, drawer still visible (correct, no overlap)
- [ ] High number of reviews (50+) → Scroll works in drawer, no lag
- [ ] Very long service name → Text wraps, drawer expands (responsive)

---

## E2E Test Script (Playwright)

```typescript
// tests/e2e/services-linear.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Services Tab Linear UI', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to a project's services
    await page.goto('/projects/1');
    // Assuming you have some setup/login logic
  });

  test('should render summary strip with correct values', async ({ page }) => {
    await expect(page.getByText('Total Contract Sum')).toBeVisible();
    await expect(page.getByText('Fee Billed')).toBeVisible();
    await expect(page.getByText('Agreed Fee Remaining')).toBeVisible();
    
    // Verify progress bar exists
    await expect(page.locator('[role="progressbar"]').first()).toBeVisible();
  });

  test('should open drawer when clicking service row', async ({ page }) => {
    // Find first service row (using data-testid or selector)
    const serviceRow = page.locator('[data-testid^="service-row-"]').first();
    await serviceRow.click();
    
    // Verify drawer opened
    const drawer = page.locator('[data-testid="service-detail-drawer"]');
    await expect(drawer).toBeVisible();
    
    // Verify drawer content
    await expect(drawer.getByText(/Finance/)).toBeVisible();
    await expect(drawer.locator('[data-testid="service-drawer-tab-reviews"]')).toBeVisible();
    await expect(drawer.locator('[data-testid="service-drawer-tab-items"]')).toBeVisible();
  });

  test('should add review via drawer', async ({ page }) => {
    // Open first service
    const serviceRow = page.locator('[data-testid^="service-row-"]').first();
    await serviceRow.click();
    
    const drawer = page.locator('[data-testid="service-detail-drawer"]');
    
    // Click Reviews tab (should be selected by default)
    const reviewsTab = drawer.locator('[data-testid="service-drawer-tab-reviews"]');
    await reviewsTab.click();
    
    // Click Add button
    await drawer.getByRole('button', { name: /add/i }).click();
    
    // Dialog should appear
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog.getByLabel(/cycle number/i)).toBeVisible();
    
    // Fill form
    await dialog.getByLabel(/cycle number/i).fill('1');
    await dialog.getByLabel(/planned date/i).fill('2026-01-15');
    await dialog.getByRole('button', { name: /create review/i }).click();
    
    // Dialog closes, drawer re-fetches
    await expect(dialog).not.toBeVisible();
    
    // Verify new review appears in drawer
    await expect(drawer.getByText('#1')).toBeVisible();
  });

  test('should close drawer on close button click', async ({ page }) => {
    const serviceRow = page.locator('[data-testid^="service-row-"]').first();
    await serviceRow.click();
    
    const drawer = page.locator('[data-testid="service-detail-drawer"]');
    await expect(drawer).toBeVisible();
    
    // Click close button
    await drawer.locator('button:has-text("Close")').click();
    
    // Drawer should be hidden
    await expect(drawer).not.toBeVisible();
  });

  test('should delete service from drawer', async ({ page }) => {
    // Get initial service count
    const initialCount = await page.locator('[data-testid^="service-row-"]').count();
    
    const serviceRow = page.locator('[data-testid^="service-row-"]').first();
    const serviceCode = await serviceRow.getByRole('cell').first().textContent();
    
    await serviceRow.click();
    
    const drawer = page.locator('[data-testid="service-detail-drawer"]');
    
    // Click Delete Service button
    await drawer.getByRole('button', { name: /delete service/i }).click();
    
    // Confirm deletion
    await page.on('dialog', dialog => dialog.accept());
    
    // Drawer should close
    await expect(drawer).not.toBeVisible();
    
    // Service should be removed from list
    const newCount = await page.locator('[data-testid^="service-row-"]').count();
    expect(newCount).toBe(initialCount - 1);
  });

  test('pagination should work correctly', async ({ page }) => {
    // Change rows per page to 5
    const rowsPerPageSelect = page.locator('[aria-label="Rows per page:"]');
    await rowsPerPageSelect.selectOption('5');
    
    // Verify only 5 rows shown
    const rows = page.locator('[data-testid^="service-row-"]');
    await expect(rows).toHaveCount(5);
    
    // Go to next page
    await page.getByRole('button', { name: /next page/i }).click();
    
    // Verify drawer closed (if open)
    const drawer = page.locator('[data-testid="service-detail-drawer"]');
    await expect(drawer).not.toBeVisible();
    
    // Verify new rows shown
    const newRows = page.locator('[data-testid^="service-row-"]');
    await expect(newRows).toHaveCount(5);
  });
});
```

---

## Verification Checklist

After deployment, verify:

- [ ] All services display in flat list
- [ ] Summary strip shows (not 3 cards)
- [ ] Row click opens drawer
- [ ] Drawer shows Finance, Reviews, Items
- [ ] Add/edit/delete still works (all endpoints)
- [ ] Pagination functional
- [ ] Template apply works
- [ ] No console errors
- [ ] No regression in billing calculations
- [ ] Responsive on mobile (drawer full width)

---

## Rollback Plan

If issues occur:

1. Revert import in `ProjectDetailPage.tsx`:
```typescript
import { ProjectServicesTab } from '@/components/ProjectServicesTab';
```

2. Keep new files for reference (don't delete immediately)

3. File issue with details

---

## Performance Metrics

**Before** (estimated):
- List render: ~200ms (all rows with inline tables)
- Memory: ~5MB per 50 services

**After** (estimated):
- List render: ~100ms (flat table only)
- Memory: ~2MB per 50 services (reviews/items lazy-loaded)
- Drawer open: +100ms (initial reviews/items fetch)

**No regressions expected.**

---

## Support & Questions

If drawer doesn't open:
1. Check browser console for errors
2. Verify `selectedServiceId` state updates on row click
3. Verify `onRowClick` handler connected

If reviews don't show in drawer:
1. Check network tab for review API response
2. Verify `enabled: open && !!service` in useQuery
3. Check cache keys in React Query DevTools

If styling looks off:
1. Verify theme context is loaded
2. Check if other Material-UI components render correctly
3. Clear browser cache and reload

