/**
 * Service Item Detail Panel
 *
 * Shows item metadata, evidence, and notes in the workspace right panel.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Box, Chip, Divider, Paper, Stack, Typography } from '@mui/material';
import { serviceItemsApi } from '@/api';
import { InlineField } from '@/components/ui/InlineField';
import type { ServiceItem } from '@/types/api';

type ServiceItemDetailPanelProps = {
  projectId: number;
  itemId: number;
};

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

export function ServiceItemDetailPanel({ projectId, itemId }: ServiceItemDetailPanelProps) {
  const { data: projectItems } = useQuery({
    queryKey: ['projectItems', projectId],
    queryFn: () => serviceItemsApi.getProjectItems(projectId),
    enabled: Number.isFinite(projectId),
  });

  const item = useMemo<ServiceItem | null>(() => {
    const items = projectItems?.items ?? [];
    return items.find((entry) => entry.item_id === itemId) ?? null;
  }, [projectItems, itemId]);

  if (!item) {
    return (
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Item details
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Select an item to view details.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={1.5}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {item.title || 'Untitled item'}
          </Typography>
          {item.status && <Chip label={item.status} size="small" />}
        </Box>
        <Typography variant="caption" color="text.secondary">
          {item.service_code || 'Service'} {item.service_name ? `• ${item.service_name}` : ''}
        </Typography>

        <Divider />

        <Stack spacing={1}>
          <InlineField label="Type" value={item.item_type || '--'} />
          <InlineField label="Priority" value={item.priority || '--'} />
          <InlineField label="Planned" value={formatDate(item.planned_date)} />
          <InlineField label="Due" value={formatDate(item.due_date)} />
          <InlineField label="Assigned" value={item.assigned_to || '--'} />
          <InlineField label="Invoice #" value={item.invoice_reference || '--'} />
          <InlineField label="Billed" value={item.is_billed ? 'Yes' : 'No'} />
        </Stack>

        {item.evidence_links && (
          <>
            <Divider />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Evidence
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-word' }}>
                {item.evidence_links}
              </Typography>
            </Box>
          </>
        )}

        {item.notes && (
          <>
            <Divider />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Notes
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.notes}
              </Typography>
            </Box>
          </>
        )}
      </Stack>
    </Paper>
  );
}
