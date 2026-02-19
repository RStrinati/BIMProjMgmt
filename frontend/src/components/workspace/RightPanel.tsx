/**
 * Workspace Right Panel
 * 
 * Renders context-aware content based on current tab and selection.
 * Displays shared blocks (Properties, Progress, Activity) + tab-specific content.
 */

import { Alert, Box, Paper, Stack, Typography, Divider } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { ReactNode, useMemo } from 'react';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import type { FinanceReconciliationResponse, Project } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';

type RightPanelProps = {
  project: Project | null;
  currentTab: string;
  selection: Selection | null;
  children?: ReactNode;
};

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const varianceColor = (variance: number) => {
  if (variance > 1000 || variance < -1000) return 'error.main';
  if (variance > 100 || variance < -100) return 'warning.main';
  return 'success.main';
};

function ServiceFeeReconciliationBlock({ projectId, enabled }: { projectId: number; enabled: boolean }) {
  const { data: reconciliation, isLoading, error } = useQuery<FinanceReconciliationResponse>({
    queryKey: ['projectFinanceReconciliation', projectId],
    queryFn: () => projectsApi.getFinanceReconciliation(projectId),
    enabled: enabled && Number.isFinite(projectId),
  });

  const reconciliationRows = useMemo(() => {
    if (!reconciliation) return [];
    const { by_service, project: projectTotals } = reconciliation;
    return [
      ...by_service,
      {
        ...projectTotals,
        service_id: -1,
        service_code: '',
        service_name: 'PROJECT TOTAL',
      },
    ];
  }, [reconciliation]);

  if (!enabled || !Number.isFinite(projectId)) {
    return null;
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Service fee reconciliation
      </Typography>
      {error ? (
        <Alert severity="error">Failed to load reconciliation.</Alert>
      ) : isLoading ? (
        <Typography color="text.secondary">Loading reconciliation...</Typography>
      ) : reconciliationRows.length ? (
        <Stack spacing={0.5} data-testid="workspace-reconciliation">
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: '2fr repeat(3, 1fr)',
              typography: 'caption',
              fontWeight: 600,
              color: 'text.secondary',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            <Box>Service</Box>
            <Box>Agreed</Box>
            <Box>Line items</Box>
            <Box>Variance</Box>
          </Box>
          {reconciliationRows.map((row) => {
            const isTotal = row.service_id === -1;
            return (
              <Box
                key={`${row.service_id}-${row.service_name}`}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '2fr repeat(3, 1fr)',
                  gap: 1,
                  alignItems: 'center',
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  backgroundColor: isTotal ? 'action.hover' : 'transparent',
                }}
              >
                <Typography variant="body2" fontWeight={isTotal ? 700 : 600} noWrap>
                  {row.service_name || row.service_code || 'Service'}
                </Typography>
                <Typography variant="body2">{formatCurrency(row.agreed_fee)}</Typography>
                <Typography variant="body2">{formatCurrency(row.line_items_total_fee)}</Typography>
                <Typography variant="body2" sx={{ color: varianceColor(row.variance) }}>
                  {formatCurrency(row.variance)}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      ) : (
        <Typography color="text.secondary">No reconciliation data yet.</Typography>
      )}
    </Paper>
  );
}

/**
 * Shared Properties Block (visible on all tabs)
 */
function PropertiesBlock({ project }: { project: Project | null }) {
  if (!project) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Properties
      </Typography>
      <Stack spacing={1}>
        <InlineField label="Project #" value={project.project_number || project.contract_number} />
        <InlineField label="Client" value={project.client_name} />
        <InlineField label="Type" value={project.project_type || project.type_name} />
        <InlineField label="Manager" value={project.project_manager} />
        <InlineField label="Start" value={formatDate(project.start_date)} />
        <InlineField label="End" value={formatDate(project.end_date)} />
      </Stack>
    </Paper>
  );
}

/**
 * Shared Progress Block (visible on all tabs)
 */
function ProgressBlock({ project }: { project: Project | null }) {
  if (!project) return null;

  const projectId = project.project_id;
  const { data: reconciliation } = useQuery<FinanceReconciliationResponse>({
    queryKey: ['projectFinanceReconciliation', projectId],
    queryFn: () => projectsApi.getFinanceReconciliation(projectId),
    enabled: Number.isFinite(projectId),
  });

  const projectTotals = reconciliation?.project;
  const totalAgreed = Number(projectTotals?.agreed_fee ?? project.total_service_agreed_fee ?? project.agreed_fee ?? 0) || 0;
  const lineItemsTotal = Number(projectTotals?.line_items_total_fee ?? 0) || 0;
  const totalBilled = Number(projectTotals?.billed_total_fee ?? project.total_service_billed_amount ?? 0) || 0;
  const outstanding = Number(projectTotals?.outstanding_total_fee ?? Math.max(lineItemsTotal - totalBilled, 0)) || 0;
  const billedPct = lineItemsTotal > 0
    ? (totalBilled / lineItemsTotal) * 100
    : totalAgreed > 0
      ? (totalBilled / totalAgreed) * 100
      : 0;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Progress
      </Typography>
      <Stack spacing={1}>
        <InlineField label="Agreed fee" value={formatCurrency(totalAgreed)} />
        <InlineField label="Line items" value={formatCurrency(lineItemsTotal || totalAgreed)} />
        <InlineField
          label="Billed"
          value={`${formatCurrency(totalBilled)} (${Math.round(Math.min(Math.max(billedPct, 0), 100))}%)`}
        />
        <InlineField label="Outstanding" value={formatCurrency(outstanding)} />
      </Stack>
    </Paper>
  );
}

/**
 * Shared Activity Block (visible on all tabs)
 */
function ActivityBlock() {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Activity
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Recent activity will appear here.
      </Typography>
    </Paper>
  );
}

/**
 * Main Right Panel Component
 */
export function RightPanel({ project, currentTab, selection, children }: RightPanelProps) {
  return (
    <Box
      sx={{
        position: 'sticky',
        top: 0,
        height: '100vh',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
      data-testid="workspace-right-panel"
    >
      <Stack spacing={2} sx={{ p: 2 }}>
        {/* Shared blocks - always visible */}
        <PropertiesBlock project={project} />
        <ProgressBlock project={project} />
        <ActivityBlock />
        <ServiceFeeReconciliationBlock
          projectId={project?.project_id ?? Number.NaN}
          enabled={currentTab === 'services'}
        />

        {/* Tab-specific or selection-specific content */}
        {children && (
          <>
            <Divider />
            {children}
          </>
        )}

        {/* Placeholder for no selection */}
        {!selection && !children && (
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Select an item to view details.
            </Typography>
          </Paper>
        )}
      </Stack>
    </Box>
  );
}
