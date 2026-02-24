/**
 * Workspace Shell - Linear-style 3-column layout
 * 
 * Layout:
 * - Left: Workspace tabs (vertical navigation)
 * - Center: Tab content (scrollable)
 * - Right: Context panel (sticky, scrollable)
 * 
 * Features:
 * - Nested routing for tabs
 * - Selection state synchronized with URL (?sel=type:id)
 * - Esc clears selection
 * - Tab switches clear selection
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Outlet, useNavigate, useParams, useLocation } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Breadcrumbs,
  Link as MuiLink,
  Stack,
  Tab,
  Tabs,
  Typography,
  Alert,
  Paper,
  Button,
} from '@mui/material';
import { projectsApi, projectServicesApi } from '@/api';
import type { Project, ProjectOverviewSummary } from '@/types/api';
import { getProjectIcon } from '@/components/projects/projectIcons';
import type { ProjectServicesListResponse } from '@/api/services';
import type { ProjectService } from '@/api/services';
import { useWorkspaceSelection } from '@/hooks/useWorkspaceSelection';
import { RightPanel } from '@/components/workspace/RightPanel';
import { ServiceDetailPanel } from '@/components/workspace/ServiceDetailPanel';
import { ServiceItemDetailPanel } from '@/components/workspace/ServiceItemDetailPanel';
import { IssueDetailPanel } from '@/components/workspace/IssueDetailPanel';
import { UpdateDetailPanel } from '@/components/workspace/UpdateDetailPanel';
import { QualityModelDetailPanel } from '@/components/workspace/QualityModelDetailPanel';
import { InvoicePipelinePanel } from '@/components/workspace/InvoicePipelinePanel';

const WORKSPACE_TABS = [
  { label: 'Overview', path: 'overview' },
  { label: 'Services', path: 'services' },
  { label: 'Deliverables', path: 'deliverables' },
  { label: 'Updates', path: 'updates' },
  { label: 'Issues', path: 'issues' },
  { label: 'Tasks', path: 'tasks' },
  { label: 'Quality', path: 'quality' },
] as const;

export default function WorkspaceShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const projectId = Number(id);
  const { selection, clearSelection } = useWorkspaceSelection();
  const queryClient = useQueryClient();
  const [rightPanelWidth, setRightPanelWidth] = useState(() => {
    const stored = localStorage.getItem('workspaceRightPanelWidth');
    const parsed = stored ? Number(stored) : 360;
    return Number.isFinite(parsed) ? parsed : 360;
  });
  const isResizingRef = useRef(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(360);

  // Debug logging for selection state
  console.log('[WorkspaceShell] Rendered with selection:', selection, 'URL search:', location.search);

  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.getById(projectId),
    enabled: Number.isFinite(projectId),
  });

  // Determine current tab from path (MUST come before using it in queries)
  const currentTab = useMemo(() => {
    // Handle nested routes (e.g., /services/new)
    const tabPath = WORKSPACE_TABS.find((tab) => 
      location.pathname.includes(`/workspace/${tab.path}`)
    );
    
    return tabPath?.path || 'overview';
  }, [location.pathname]);

  // Fetch services if on services tab or have a service selection
  const { data: servicesPayload } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', projectId],
    queryFn: () => projectServicesApi.getAll(projectId),
    enabled: Number.isFinite(projectId) && (currentTab === 'services' || selection?.type === 'service'),
    staleTime: 60_000,
  });

  const { data: overviewSummaryResult, isLoading: isOverviewSummaryLoading } = useQuery({
    queryKey: ['projectOverviewSummary', projectId],
    queryFn: () => projectsApi.getOverviewSummary(projectId),
    enabled: Number.isFinite(projectId) && currentTab === 'overview',
  });

  const runOverviewSummary = useMutation({
    mutationFn: () => projectsApi.runOverviewSummary(projectId),
    onSuccess: () => {
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectOverviewSummary', projectId] });
      }
    },
  });

  const services = useMemo<ProjectService[]>(() => {
    if (!servicesPayload) return [];
    if (Array.isArray(servicesPayload)) return servicesPayload;
    const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
    return Array.isArray(items) ? items : [];
  }, [servicesPayload]);

  const selectedService = useMemo(() => {
    if (selection?.type !== 'service') return null;
    return services.find((s) => s.service_id === selection.id) ?? null;
  }, [services, selection]);

  const overviewSummary = (overviewSummaryResult?.summary ?? null) as ProjectOverviewSummary | null;
  const formatDateTime = (value?: string | null) => {
    if (!value) return '--';
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
  };

  const activeTabIndex = useMemo(() => {
    const index = WORKSPACE_TABS.findIndex((tab) => tab.path === currentTab);
    return index >= 0 ? index : 0;
  }, [currentTab]);

  // Track previous tab to detect actual changes
  const previousTabRef = useRef(currentTab);
  
  // Clear selection ONLY when tab actually changes (not on every render)
  useEffect(() => {
    if (previousTabRef.current !== currentTab) {
      console.log('[WorkspaceShell] Tab changed from', previousTabRef.current, 'to', currentTab, '- clearing selection');
      clearSelection();
      previousTabRef.current = currentTab;
    }
  }, [currentTab, clearSelection]);

  // Redirect to overview if on workspace root
  useEffect(() => {
    if (location.pathname === `/projects/${projectId}/workspace` || 
        location.pathname === `/projects/${projectId}/workspace/`) {
      navigate(`/projects/${projectId}/workspace/overview`, { replace: true });
    }
  }, [location.pathname, projectId, navigate]);

  const handleTabChange = (_event: React.SyntheticEvent, newIndex: number) => {
    const tab = WORKSPACE_TABS[newIndex];
    if (tab) {
      navigate(`/projects/${projectId}/workspace/${tab.path}`);
    }
  };

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!isResizingRef.current) return;
      const delta = startXRef.current - event.clientX;
      const nextWidth = Math.min(520, Math.max(280, startWidthRef.current + delta));
      setRightPanelWidth(nextWidth);
    };

    const handleMouseUp = () => {
      if (!isResizingRef.current) return;
      isResizingRef.current = false;
      localStorage.setItem('workspaceRightPanelWidth', String(rightPanelWidth));
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [rightPanelWidth]);

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading project...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load project.</Alert>
      </Box>
    );
  }

  return (
    <Box data-testid="workspace-shell" sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box sx={{ px: 3, pt: 2, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Stack spacing={1}>
          <Breadcrumbs aria-label="breadcrumb">
            <MuiLink
              underline="hover"
              color="inherit"
              onClick={() => navigate('/projects')}
              sx={{ cursor: 'pointer' }}
            >
              Projects
            </MuiLink>
            <Typography color="text.primary">Workspace</Typography>
          </Breadcrumbs>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            alignItems={{ xs: 'flex-start', md: 'center' }}
            justifyContent="space-between"
          >
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
              {project && (
                <Box
                  sx={{
                    width: 28,
                    height: 28,
                    borderRadius: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: 1,
                    borderColor: 'divider',
                  }}
                >
                  {(() => {
                    const Icon = getProjectIcon(project.icon_key);
                    return <Icon size={18} />;
                  })()}
                </Box>
              )}
              <Typography variant="h5" data-testid="workspace-project-title">
                {project?.project_name || 'Loading project...'}
              </Typography>
            </Stack>
            <Tabs
              value={activeTabIndex}
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minHeight: 32 }}
            >
              {WORKSPACE_TABS.map((tab) => (
                <Tab
                  key={tab.path}
                  label={tab.label}
                  data-testid={`workspace-tab-${tab.path}`}
                  sx={{ minHeight: 32 }}
                />
              ))}
            </Tabs>
          </Stack>
        </Stack>
      </Box>

      {/* 3-column layout */}
      <Box
        sx={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          minWidth: 0,
        }}
      >
        {/* Center: Content */}
        <Box sx={{ flex: '1 1 auto', minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tab Content */}
          <Box sx={{ flex: 1, minWidth: 0, overflow: 'auto', p: 2 }}>
            <Outlet context={{ projectId, project, selection }} />
          </Box>
        </Box>

        {/* Right: Panel */}
        <Box
          sx={{
            borderLeft: { xs: 0, lg: 1 },
            borderColor: 'divider',
            display: { xs: 'none', lg: 'block' },
            width: rightPanelWidth,
            flexShrink: 0,
            position: 'relative',
          }}
        >
          <Box
            role="separator"
            aria-orientation="vertical"
            onMouseDown={(event) => {
              isResizingRef.current = true;
              startXRef.current = event.clientX;
              startWidthRef.current = rightPanelWidth;
              document.body.style.cursor = 'col-resize';
              document.body.style.userSelect = 'none';
            }}
            sx={{
              position: 'absolute',
              left: -6,
              top: 0,
              width: 12,
              height: '100%',
              cursor: 'col-resize',
              zIndex: 10,
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          />
          <RightPanel project={project || null} currentTab={currentTab} selection={selection}>
            {/* Content router based on selection type */}
            {selection?.type === 'service' && selectedService ? (
              <ServiceDetailPanel projectId={projectId} service={selectedService} />
            ) : selection?.type === 'item' && typeof selection.id === 'number' ? (
              <ServiceItemDetailPanel projectId={projectId} itemId={selection.id} />
            ) : selection?.type === 'issue' && typeof selection.id === 'string' ? (
              <IssueDetailPanel projectId={projectId} issueKey={selection.id} />
            ) : selection?.type === 'update' && typeof selection.id === 'number' ? (
              <UpdateDetailPanel updateId={selection.id} />
            ) : selection?.type === 'model' && typeof selection.id === 'number' ? (
              <QualityModelDetailPanel projectId={projectId} expectedModelId={selection.id} />
            ) : !selection ? (
              // Tab summary panels when no selection
              <>
                {currentTab === 'overview' && (
                  <Stack spacing={2}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          Overview Summary
                        </Typography>
                        <Button
                          size="small"
                          variant="text"
                          onClick={() => runOverviewSummary.mutate()}
                          disabled={runOverviewSummary.isPending || !Number.isFinite(projectId)}
                        >
                          {runOverviewSummary.isPending ? 'Running...' : 'Run report'}
                        </Button>
                      </Stack>
                      {isOverviewSummaryLoading ? (
                        <Typography variant="body2" color="text.secondary">
                          Loading overview summary...
                        </Typography>
                      ) : overviewSummary ? (
                        <Stack spacing={1}>
                          <Typography variant="caption" color="text.secondary">
                            Last generated: {formatDateTime(overviewSummary.generated_at)}
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {overviewSummary.summary_text}
                          </Typography>
                        </Stack>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Run the report to generate an overview summary.
                        </Typography>
                      )}
                    </Paper>
                    <InvoicePipelinePanel projectId={projectId} />
                  </Stack>
                )}
                {currentTab === 'services' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Services Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total services: {services.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Select a service to view details.
                    </Typography>
                  </Paper>
                )}
                {currentTab === 'issues' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Issues Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Select an issue to view details.
                    </Typography>
                  </Paper>
                )}
                {currentTab === 'deliverables' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Deliverables Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Select a deliverable to view details.
                    </Typography>
                  </Paper>
                )}
                {currentTab === 'tasks' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Tasks Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Select a task to view details.
                    </Typography>
                  </Paper>
                )}
                {currentTab === 'updates' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Updates Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Select an update to view details.
                    </Typography>
                  </Paper>
                )}
                {currentTab === 'quality' && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Quality Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Quality register overview will appear here.
                    </Typography>
                  </Paper>
                )}
              </>
            ) : null}
          </RightPanel>
        </Box>
      </Box>
    </Box>
  );
}
