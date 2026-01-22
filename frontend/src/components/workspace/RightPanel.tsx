/**
 * Workspace Right Panel
 * 
 * Renders context-aware content based on current tab and selection.
 * Displays shared blocks (Properties, Progress, Activity) + tab-specific content.
 */

import { Box, Paper, Stack, Typography, Divider } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { ReactNode } from 'react';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import type { Project } from '@/types/api';
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
  const { data: financeSummary } = useQuery({
    queryKey: ['projectFinanceSummary', projectId],
    queryFn: () => projectsApi.getFinanceSummary(projectId),
    enabled: Number.isFinite(projectId),
  });

  const totalAgreed = Number(financeSummary?.total_agreed_fee ?? project.total_service_agreed_fee ?? project.agreed_fee ?? 0) || 0;
  const totalBilled = Number(financeSummary?.total_claimed_or_billed ?? project.total_service_billed_amount ?? 0) || 0;
  const billedPctRaw = financeSummary?.progress_pct ?? project.service_billed_pct ?? 0;
  const billedPct = Number.isFinite(Number(billedPctRaw))
    ? Number(billedPctRaw)
    : totalAgreed > 0 ? (totalBilled / totalAgreed) * 100 : 0;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Progress
      </Typography>
      <Stack spacing={1}>
        <InlineField label="Agreed fee" value={formatCurrency(totalAgreed)} />
        <InlineField label="Billed" value={formatCurrency(totalBilled)} />
        <InlineField label="Billed %" value={`${Math.round(Math.min(Math.max(billedPct, 0), 100))}%`} />
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
