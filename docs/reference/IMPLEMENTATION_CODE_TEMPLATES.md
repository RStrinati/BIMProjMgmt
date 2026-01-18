# Implementation Code Templates
## Services + Deliverables Refactor

---

## 1. SQL Migration Template

**File:** `sql/migrations/007_add_deliverables_fields.sql`

```sql
-- Deliverables Enhancement: Add completion tracking and billing fields
-- Safe: All columns are nullable (additive only)
-- Applied: January 2026

-- Phase 1: ServiceReviews table
IF COL_LENGTH('ServiceReviews', 'completion_date') IS NULL
BEGIN
    ALTER TABLE ServiceReviews ADD
        completion_date DATE NULL;
END;

IF COL_LENGTH('ServiceReviews', 'invoice_date') IS NULL
BEGIN
    ALTER TABLE ServiceReviews ADD
        invoice_date DATE NULL;
END;

IF COL_LENGTH('ServiceReviews', 'invoice_number') IS NULL
BEGIN
    ALTER TABLE ServiceReviews ADD
        invoice_number NVARCHAR(100) NULL;
END;

IF COL_LENGTH('ServiceReviews', 'billing_status') IS NULL
BEGIN
    ALTER TABLE ServiceReviews ADD
        billing_status NVARCHAR(50) NULL
        CONSTRAINT chk_billing_status CHECK (billing_status IS NULL OR billing_status IN ('pending', 'invoiced', 'paid', 'overdue'));
END;

-- Phase 2: ServiceItems table
IF COL_LENGTH('ServiceItems', 'completion_date') IS NULL
BEGIN
    ALTER TABLE ServiceItems ADD
        completion_date DATE NULL;
END;

IF COL_LENGTH('ServiceItems', 'invoice_date') IS NULL
BEGIN
    ALTER TABLE ServiceItems ADD
        invoice_date DATE NULL;
END;

IF COL_LENGTH('ServiceItems', 'invoice_number') IS NULL
BEGIN
    ALTER TABLE ServiceItems ADD
        invoice_number NVARCHAR(100) NULL;
END;

IF COL_LENGTH('ServiceItems', 'billing_status') IS NULL
BEGIN
    ALTER TABLE ServiceItems ADD
        billing_status NVARCHAR(50) NULL
        CONSTRAINT chk_item_billing_status CHECK (billing_status IS NULL OR billing_status IN ('pending', 'invoiced', 'paid', 'overdue'));
END;

-- Phase 3: Optional indexes for performance
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ServiceReviews_project_billing')
BEGIN
    CREATE INDEX idx_ServiceReviews_project_billing 
    ON ServiceReviews (service_id, billing_status) INCLUDE (billing_amount, invoice_date);
END;

PRINT 'Migration 007 completed: Added deliverables fields to ServiceReviews and ServiceItems';
```

---

## 2. Schema Constants Update

**File:** `constants/schema.py` (add to existing class definitions)

```python
class ServiceReviews:
    TABLE = "ServiceReviews"
    # ... existing fields ...
    COMPLETION_DATE = "completion_date"
    INVOICE_DATE = "invoice_date"
    INVOICE_NUMBER = "invoice_number"
    BILLING_STATUS = "billing_status"

class ServiceItems:
    TABLE = "ServiceItems"
    # ... existing fields ...
    COMPLETION_DATE = "completion_date"
    INVOICE_DATE = "invoice_date"
    INVOICE_NUMBER = "invoice_number"
    BILLING_STATUS = "billing_status"
```

---

## 3. TypeScript Interfaces Update

**File:** `frontend/src/types/api.ts` (add new interfaces)

```typescript
// New interface for unified deliverables view
export interface DeliverableRow {
  source_type: 'review' | 'item';
  deliverable_id: number;  // review_id or item_id
  service_id: number;
  project_id: number;
  phase?: string;
  cycle_no?: number;
  title: string;
  planned_date: string;
  due_date?: string;
  completion_date?: string;
  status: string;
  assignee?: string;
  assignee_id?: number;
  fee?: number;
  invoice_date?: string;
  invoice_number?: string;
  billing_status?: string;
}

// Extend existing ProjectService with finance fields
export interface ProjectService {
  // ... existing fields ...
  billing_progress_pct?: number;
  billed_amount?: number;
  invoice_date?: string;
  invoice_number?: string;
  billing_status?: string;
}

// Extend existing ServiceReview
export interface ServiceReview {
  // ... existing fields ...
  completion_date?: string;
  invoice_date?: string;
  invoice_number?: string;
  billing_status?: string;
}

// Extend existing ServiceItem
export interface ServiceItem {
  // ... existing fields ...
  completion_date?: string;
  invoice_date?: string;
  invoice_number?: string;
  billing_status?: string;
}
```

---

## 4. Backend Database Functions

**File:** `database.py` (add new functions)

```python
def get_project_deliverables(project_id: int, service_id: int | None = None) -> list[dict] | None:
    """
    Fetch unified deliverables view combining ServiceReviews + ServiceItems.
    Returns list of DeliverableRow dicts with consistent schema.
    
    Args:
        project_id: Project ID
        service_id: Optional service ID to filter by specific service
    
    Returns:
        List of deliverables or None if connection fails
    """
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Query both reviews and items, union them with consistent columns
        query = f"""
        SELECT
            'review' AS source_type,
            sr.{S.ServiceReviews.REVIEW_ID} AS deliverable_id,
            sr.{S.ServiceReviews.SERVICE_ID},
            s.{S.Services.PROJECT_ID},
            s.{S.Services.PHASE},
            sr.{S.ServiceReviews.CYCLE_NO},
            CONCAT(s.{S.Services.SERVICE_CODE}, ' - Cycle ', sr.{S.ServiceReviews.CYCLE_NO}) AS title,
            sr.{S.ServiceReviews.PLANNED_DATE},
            sr.{S.ServiceReviews.DUE_DATE},
            sr.{S.ServiceReviews.COMPLETION_DATE},
            sr.{S.ServiceReviews.STATUS},
            u.{S.Users.NAME} AS assignee,
            sr.{S.ServiceReviews.ASSIGNED_USER_ID} AS assignee_id,
            sr.{S.ServiceReviews.BILLING_AMOUNT} AS fee,
            sr.{S.ServiceReviews.INVOICE_DATE},
            sr.{S.ServiceReviews.INVOICE_NUMBER},
            sr.{S.ServiceReviews.BILLING_STATUS}
        FROM {S.ServiceReviews.TABLE} sr
        JOIN {S.Services.TABLE} s ON sr.{S.ServiceReviews.SERVICE_ID} = s.{S.Services.SERVICE_ID}
        LEFT JOIN {S.Users.TABLE} u ON sr.{S.ServiceReviews.ASSIGNED_USER_ID} = u.{S.Users.ID}
        WHERE s.{S.Services.PROJECT_ID} = ?
        {f'AND s.{S.Services.SERVICE_ID} = ?' if service_id else ''}
        
        UNION ALL
        
        SELECT
            'item' AS source_type,
            si.{S.ServiceItems.ITEM_ID} AS deliverable_id,
            si.{S.ServiceItems.SERVICE_ID},
            s.{S.Services.PROJECT_ID},
            s.{S.Services.PHASE},
            NULL AS cycle_no,
            si.{S.ServiceItems.TITLE},
            si.{S.ServiceItems.PLANNED_DATE},
            si.{S.ServiceItems.DUE_DATE},
            si.{S.ServiceItems.COMPLETION_DATE},
            si.{S.ServiceItems.STATUS},
            u.{S.Users.NAME} AS assignee,
            si.{S.ServiceItems.ASSIGNED_USER_ID} AS assignee_id,
            s.{S.Services.AGREED_FEE} AS fee,
            si.{S.ServiceItems.INVOICE_DATE},
            si.{S.ServiceItems.INVOICE_NUMBER},
            si.{S.ServiceItems.BILLING_STATUS}
        FROM {S.ServiceItems.TABLE} si
        JOIN {S.Services.TABLE} s ON si.{S.ServiceItems.SERVICE_ID} = s.{S.Services.SERVICE_ID}
        LEFT JOIN {S.Users.TABLE} u ON si.{S.ServiceItems.ASSIGNED_USER_ID} = u.{S.Users.ID}
        WHERE s.{S.Services.PROJECT_ID} = ?
        {f'AND s.{S.Services.SERVICE_ID} = ?' if service_id else ''}
        
        ORDER BY planned_date ASC, cycle_no ASC NULLS LAST
        """
        
        params = [project_id]
        if service_id:
            params.extend([service_id, project_id, service_id])
        else:
            params.extend([project_id])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            {
                'source_type': row[0],
                'deliverable_id': row[1],
                'service_id': row[2],
                'project_id': row[3],
                'phase': row[4],
                'cycle_no': row[5],
                'title': row[6],
                'planned_date': row[7],
                'due_date': row[8],
                'completion_date': row[9],
                'status': row[10],
                'assignee': row[11],
                'assignee_id': row[12],
                'fee': row[13],
                'invoice_date': row[14],
                'invoice_number': row[15],
                'billing_status': row[16],
            }
            for row in rows
        ]
    finally:
        conn.close()
```

---

## 5. Backend Flask Endpoint

**File:** `backend/app.py` (add new route)

```python
@app.route('/api/projects/<int:project_id>/deliverables', methods=['GET'])
def get_project_deliverables_endpoint(project_id: int):
    """Fetch unified deliverables view (reviews + items) for a project."""
    try:
        service_id = request.args.get('service_id', type=int)
        deliverables = get_project_deliverables(project_id, service_id)
        
        if deliverables is None:
            return jsonify({'error': 'Failed to connect to database'}), 500
        
        return jsonify({
            'items': deliverables,
            'total': len(deliverables),
            'project_id': project_id
        }), 200
    except Exception as e:
        logger.error(f'Error fetching deliverables: {e}')
        return jsonify({'error': str(e)}), 500
```

---

## 6. React Component: ServiceDetailDrawer

**File:** `frontend/src/components/ServiceDetailDrawer.tsx` (new)

```typescript
import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  Button,
  Stack,
  Divider,
  Chip,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import type { ProjectService } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';

interface ServiceDetailDrawerProps {
  open: boolean;
  service: ProjectService | null;
  onClose: () => void;
}

export function ServiceDetailDrawer({ open, service, onClose }: ServiceDetailDrawerProps) {
  if (!service) return null;

  const formatCurrency = (value?: number) => {
    if (!value) return '--';
    return `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
  };

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return `${Number(value).toFixed(1)}%`;
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: { xs: '100%', sm: 400 }, overflow: 'auto' } }}
      data-testid="service-detail-drawer"
    >
      <Box sx={{ p: 2 }}>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h6">{service.service_name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {service.service_code}
            </Typography>
          </Box>
          <IconButton size="small" onClick={onClose} data-testid="service-detail-close-button">
            <CloseIcon />
          </IconButton>
        </Stack>

        <Divider sx={{ mb: 2 }} />

        {/* Service Details */}
        <Stack spacing={2}>
          <InlineField label="Phase" value={service.phase || '--'} />
          <InlineField label="Unit Type" value={service.unit_type || '--'} />
          <InlineField label="Unit Quantity" value={String(service.unit_qty ?? '--')} />
          <InlineField label="Unit Rate" value={formatCurrency(service.unit_rate)} />

          <Divider />

          {/* Financial Summary */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Financial
            </Typography>
            <Stack spacing={1}>
              <InlineField label="Agreed Fee" value={formatCurrency(service.agreed_fee)} />
              <InlineField label="Billed Amount" value={formatCurrency(service.billed_amount)} />
              <InlineField label="Billing Progress" value={formatPercent(service.billing_progress_pct)} />
            </Stack>
          </Box>

          <Divider />

          {/* Status */}
          <Stack direction="row" alignItems="center" gap={1}>
            <Typography variant="body2" fontWeight={600}>Status:</Typography>
            <Chip
              label={service.status || 'Unknown'}
              size="small"
              color={service.status === 'completed' ? 'success' : 'default'}
              variant="outlined"
            />
          </Stack>

          {service.notes && (
            <>
              <Divider />
              <Box>
                <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                  Notes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {service.notes}
                </Typography>
              </Box>
            </>
          )}
        </Stack>

        {/* Action Buttons */}
        <Stack direction="row" gap={1} sx={{ mt: 3 }}>
          <Button variant="outlined" fullWidth onClick={onClose}>
            Close
          </Button>
        </Stack>
      </Box>
    </Drawer>
  );
}
```

---

## 7. React Component: DeliverableSidePanel

**File:** `frontend/src/components/DeliverableSidePanel.tsx` (new)

```typescript
import React, { useMemo } from 'react';
import {
  Drawer,
  Box,
  Typography,
  Button,
  Stack,
  Divider,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import type { DeliverableRow } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';
import { LinkedIssuesList } from '@/components/ui/LinkedIssuesList';

interface DeliverableSidePanelProps {
  open: boolean;
  deliverable: DeliverableRow | null;
  projectId: number;
  onClose: () => void;
  isLoading?: boolean;
}

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatCurrency = (value?: number) => {
  if (!value) return '--';
  return `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
};

export function DeliverableSidePanel({
  open,
  deliverable,
  projectId,
  onClose,
  isLoading,
}: DeliverableSidePanelProps) {
  if (!deliverable) return null;

  const statusColor = useMemo(() => {
    const status = deliverable.status?.toLowerCase();
    if (status === 'completed') return 'success';
    if (status === 'overdue') return 'error';
    if (status === 'in_progress') return 'info';
    return 'default';
  }, [deliverable.status]);

  const billingStatusColor = useMemo(() => {
    const status = deliverable.billing_status?.toLowerCase();
    if (status === 'paid') return 'success';
    if (status === 'overdue') return 'error';
    if (status === 'invoiced') return 'info';
    return 'default';
  }, [deliverable.billing_status]);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: { xs: '100%', sm: 450 }, overflow: 'auto' } }}
      data-testid="deliverable-detail-drawer"
    >
      <Box sx={{ p: 2 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Header */}
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
              <Box>
                <Chip
                  label={deliverable.source_type === 'review' ? 'Review Cycle' : 'Item'}
                  size="small"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
                <Typography variant="h6">{deliverable.title}</Typography>
                {deliverable.phase && (
                  <Typography variant="caption" color="text.secondary">
                    Phase: {deliverable.phase}
                  </Typography>
                )}
              </Box>
              <IconButton size="small" onClick={onClose} data-testid="deliverable-detail-close-button">
                <CloseIcon />
              </IconButton>
            </Stack>

            <Divider sx={{ mb: 2 }} />

            {/* Deliverable Details */}
            <Stack spacing={2}>
              {deliverable.cycle_no && (
                <InlineField label="Cycle #" value={String(deliverable.cycle_no)} />
              )}
              <InlineField label="Assignee" value={deliverable.assignee || 'Unassigned'} />
              <InlineField label="Status" value={
                <Chip label={deliverable.status} size="small" color={statusColor} variant="outlined" />
              } />

              <Divider />

              {/* Date Summary */}
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Dates
                </Typography>
                <Stack spacing={1}>
                  <InlineField label="Planned" value={formatDate(deliverable.planned_date)} />
                  <InlineField label="Due" value={formatDate(deliverable.due_date)} />
                  <InlineField label="Completed" value={formatDate(deliverable.completion_date)} />
                </Stack>
              </Box>

              <Divider />

              {/* Financial Summary */}
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Billing
                </Typography>
                <Stack spacing={1}>
                  <InlineField label="Fee" value={formatCurrency(deliverable.fee)} />
                  <InlineField label="Invoice #" value={deliverable.invoice_number || '--'} />
                  <InlineField label="Invoice Date" value={formatDate(deliverable.invoice_date)} />
                  <InlineField label="Billing Status" value={
                    deliverable.billing_status ? (
                      <Chip label={deliverable.billing_status} size="small" color={billingStatusColor} variant="outlined" />
                    ) : (
                      '--'
                    )
                  } />
                </Stack>
              </Box>

              {/* Linked Issues */}
              {deliverable.source_type === 'review' && (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Linked Issues
                    </Typography>
                    <LinkedIssuesList
                      projectId={projectId}
                      anchorType="review"
                      anchorId={deliverable.deliverable_id}
                      enabled={true}
                      readonly={true}
                      data-testid="deliverable-linked-issues"
                    />
                  </Box>
                </>
              )}
            </Stack>

            {/* Action Buttons */}
            <Stack direction="row" gap={1} sx={{ mt: 3 }}>
              <Button variant="outlined" fullWidth onClick={onClose}>
                Close
              </Button>
            </Stack>
          </>
        )}
      </Box>
    </Drawer>
  );
}
```

---

## 8. Playwright Test: Services Detail Drawer

**File:** `frontend/tests/e2e/services-side-panel.spec.ts` (new)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Services: Side Panel', () => {
  test('service row click opens detail drawer', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    // Mock project data
    await page.route('**/api/project/**', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          project_id: 1,
          project_name: 'Test Project',
          internal_lead: 1,
        }),
      });
    });

    // Mock services data
    await page.route('**/api/projects/1/services', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          items: [
            {
              service_id: 10,
              project_id: 1,
              service_code: 'SVC-001',
              service_name: 'Design Review',
              phase: 'Design',
              agreed_fee: 50000,
              unit_rate: 1000,
              unit_qty: 50,
              status: 'in_progress',
              billing_progress_pct: 50,
              billed_amount: 25000,
            },
          ],
        }),
      });
    });

    await page.route('**/api/users', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify([{ user_id: 1, name: 'Alex Lead' }]),
      });
    });

    // Navigate and open Services tab
    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Services' }).click();
    await expect(page.getByTestId('project-workspace-v2-services')).toBeVisible();

    // Click service row to open detail drawer
    await page.getByTestId('service-row-10').click();
    await expect(page.getByTestId('service-detail-drawer')).toBeVisible();

    // Verify key financial fields
    await expect(page.getByText('Design Review')).toBeVisible();
    await expect(page.getByText('$50,000')).toBeVisible(); // Agreed fee
    await expect(page.getByText('50%')).toBeVisible(); // Billing progress

    // Close drawer
    await page.getByTestId('service-detail-close-button').click();
    await expect(page.getByTestId('service-detail-drawer')).not.toBeVisible();
  });
});
```

---

## 9. Playwright Test: Deliverables Table + Drawer

**File:** `frontend/tests/e2e/deliverables-side-panel.spec.ts` (new)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Deliverables: Table and Side Panel', () => {
  test('tab renamed and table renders required columns', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await page.route('**/api/project/**', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          project_id: 1,
          project_name: 'Test Project',
          internal_lead: 1,
        }),
      });
    });

    await page.route('**/api/users', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify([{ user_id: 1, name: 'Alex Lead' }]),
      });
    });

    // Navigate
    await page.goto('/projects/1');

    // Check tab is renamed to "Deliverables"
    const delivTab = page.getByRole('tab', { name: 'Deliverables' });
    await expect(delivTab).toBeVisible();
    await delivTab.click();

    // Verify table columns are present
    const requiredColumns = [
      'Phase',
      'Deliverable',
      'Cycle',
      'Assignee',
      'Due',
      'Status',
      'Completion',
      'Planned',
      'Fee',
      'Invoice Date',
      'Billing Status',
      'Invoice #',
    ];

    for (const col of requiredColumns) {
      await expect(page.getByTestId(`deliverable-table-header-${col.toLowerCase()}`)).toBeVisible();
    }
  });

  test('deliverable row click opens detail drawer', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    await page.route('**/api/project/**', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          project_id: 1,
          project_name: 'Test Project',
          internal_lead: 1,
        }),
      });
    });

    await page.route('**/api/projects/1/deliverables', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          items: [
            {
              source_type: 'review',
              deliverable_id: 20,
              service_id: 10,
              project_id: 1,
              phase: 'Design',
              cycle_no: 1,
              title: 'Week 1 Design Review',
              planned_date: '2026-01-20',
              due_date: '2026-01-25',
              completion_date: '2026-01-24',
              status: 'completed',
              assignee: 'Alex Lead',
              assignee_id: 1,
              fee: 5000,
              invoice_date: '2026-01-30',
              invoice_number: 'INV-001',
              billing_status: 'invoiced',
            },
          ],
        }),
      });
    });

    await page.route('**/api/users', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify([{ user_id: 1, name: 'Alex Lead' }]),
      });
    });

    // Navigate and open Deliverables
    await page.goto('/projects/1');
    await page.getByRole('tab', { name: 'Deliverables' }).click();

    // Click deliverable row
    await page.getByTestId('deliverable-row-20').click();
    await expect(page.getByTestId('deliverable-detail-drawer')).toBeVisible();

    // Verify detail content
    await expect(page.getByText('Week 1 Design Review')).toBeVisible();
    await expect(page.getByText('Cycle: 1')).toBeVisible();
    await expect(page.getByText('Alex Lead')).toBeVisible();
    await expect(page.getByText('$5,000')).toBeVisible(); // Fee
    await expect(page.getByText('INV-001')).toBeVisible(); // Invoice number

    // Close drawer
    await page.getByTestId('deliverable-detail-close-button').click();
    await expect(page.getByTestId('deliverable-detail-drawer')).not.toBeVisible();
  });
});
```

---

## Summary of Templates

| Template | File | Type | LoC |
|----------|------|------|-----|
| SQL migration | `007_*.sql` | Database | 50 |
| Schema constants | `schema.py` | Python | 8 |
| TypeScript interfaces | `types/api.ts` | TypeScript | 50 |
| DB function | `database.py` | Python | 80 |
| Flask endpoint | `app.py` | Python | 20 |
| ServiceDetailDrawer | New component | React/TSX | 150 |
| DeliverableSidePanel | New component | React/TSX | 200 |
| Services test | New spec | Playwright | 80 |
| Deliverables test | New spec | Playwright | 120 |

**Total new code:** ~750 lines | **Total modifications:** ~150 lines | **Estimated time:** 9-13 hours

---

**Next Step:** Copy these templates and adapt to your codebase patterns (error handling, logging, styling, etc.)
