import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Chip, Paper, Stack, Typography } from '@mui/material';
import { projectsApi } from '@/api';
import type { FinanceLineItem, FinanceLineItemsResponse } from '@/types/api';

const READY_STATUSES = new Set(['ready', 'draft', 'unbilled']);

type InvoicePipelinePanelProps = {
  projectId: number;
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const formatMonthLabel = (value: string) => {
  if (!value) return 'Unscheduled';
  const parsed = new Date(`${value}-01`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
};

export function InvoicePipelinePanel({ projectId }: InvoicePipelinePanelProps) {
  const [includeItems, setIncludeItems] = useState(true);

  const { data: lineItemsResult, isLoading: isLineItemsLoading, error: lineItemsError } = useQuery<FinanceLineItemsResponse>({
    queryKey: ['projectFinanceLineItems', projectId],
    queryFn: () => projectsApi.getFinanceLineItems(projectId),
    enabled: Number.isFinite(projectId),
  });

  const filteredLineItems = useMemo<FinanceLineItem[]>(() => {
    const items = lineItemsResult?.line_items ?? [];
    if (includeItems) return items;
    return items.filter((item) => item.type === 'review');
  }, [lineItemsResult, includeItems]);

  const pipelineBuckets = useMemo(() => {
    const buckets = new Map<string, {
      month: string;
      deliverables_count: number;
      total_amount: number;
      ready_count: number;
      ready_amount: number;
    }>();

    filteredLineItems.forEach((item) => {
      const month = item.invoice_month || 'Unscheduled';
      const existing = buckets.get(month) || {
        month,
        deliverables_count: 0,
        total_amount: 0,
        ready_count: 0,
        ready_amount: 0,
      };

      const fee = Number(item.fee ?? 0);
      existing.deliverables_count += 1;
      existing.total_amount += fee;

      const normalizedStatus = (item.invoice_status || '').toLowerCase();
      if (READY_STATUSES.has(normalizedStatus)) {
        existing.ready_count += 1;
        existing.ready_amount += fee;
      }

      buckets.set(month, existing);
    });

    return Array.from(buckets.values()).sort((a, b) => a.month.localeCompare(b.month));
  }, [filteredLineItems]);

  const currentMonthKey = useMemo(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }, []);

  const readyThisMonth = useMemo(() => {
    return (
      pipelineBuckets.find((bucket) => bucket.month === currentMonthKey) || {
        month: currentMonthKey,
        deliverables_count: 0,
        total_amount: 0,
        ready_count: 0,
        ready_amount: 0,
      }
    );
  }, [pipelineBuckets, currentMonthKey]);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Invoice pipeline
        </Typography>
        <Chip
          label={includeItems ? 'Including items' : 'Reviews only'}
          color={includeItems ? 'primary' : 'default'}
          variant={includeItems ? 'filled' : 'outlined'}
          size="small"
          onClick={() => setIncludeItems((prev) => !prev)}
        />
      </Stack>
      {lineItemsError ? (
        <Alert severity="error">Failed to load invoice pipeline.</Alert>
      ) : isLineItemsLoading ? (
        <Typography color="text.secondary">Loading invoice pipeline...</Typography>
      ) : pipelineBuckets.length ? (
        <Stack spacing={1} data-testid="workspace-invoice-pipeline">
          <Typography variant="body2">
            Ready this month: {readyThisMonth.ready_count} · {formatCurrency(readyThisMonth.ready_amount)}
          </Typography>
          <Stack spacing={0.5}>
            {pipelineBuckets.map((item) => (
              <Box key={item.month} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {formatMonthLabel(item.month)}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="caption">
                    {item.deliverables_count} · {formatCurrency(item.total_amount)}
                  </Typography>
                  {item.ready_count > 0 && (
                    <Chip
                      label={`Ready ${item.ready_count} · ${formatCurrency(item.ready_amount)}`}
                      size="small"
                      color="success"
                      variant="outlined"
                      sx={{ height: 22, fontSize: '0.7rem' }}
                    />
                  )}
                </Stack>
              </Box>
            ))}
          </Stack>
        </Stack>
      ) : (
        <Typography color="text.secondary">No line items yet.</Typography>
      )}
    </Paper>
  );
}
