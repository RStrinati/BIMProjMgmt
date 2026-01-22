import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Alert, Box, Chip, Divider, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';
import type { DashboardTimelineProject, ProjectSummary } from '@/types/api';
import { TimelineGrid } from './TimelineGrid';
import { type TimelinePreset, type TimelineZoom, useTimelineModel } from './useTimelineModel';
import { PROJECT_FIELD_MAP, formatProjectValue, renderTimelineMeta } from '@/features/projects/fields/ProjectFieldRegistry';

type TimelinePanelProps = {
  projectIds?: number[];
  clientIds?: number[];
  typeIds?: number[];
  manager?: string;
  type?: string;
  client?: string;
  title?: string;
  searchText?: string;
  onSearchTextChange?: (value: string) => void;
  showSearch?: boolean;
  summaryById?: Record<number, ProjectSummary>;
  metaFieldIds?: string[];
};

const TIMELINE_MONTHS = 12;

export function TimelinePanel({
  projectIds,
  clientIds,
  typeIds,
  manager,
  type,
  client,
  title = 'Timeline',
  searchText,
  onSearchTextChange,
  showSearch = true,
  summaryById,
  metaFieldIds,
}: TimelinePanelProps) {
  const navigate = useNavigate();
  const [internalSearchText, setInternalSearchText] = useState('');
  const [preset, setPreset] = useState<TimelinePreset>('all');
  const [zoom, setZoom] = useState<TimelineZoom>('month');

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['timeline-v2', TIMELINE_MONTHS, projectIds, clientIds, typeIds, manager],
    queryFn: () =>
      projectsApi.getTimeline({
        months: TIMELINE_MONTHS,
        projectIds: projectIds?.length ? projectIds : undefined,
        clientIds: clientIds?.length ? clientIds : undefined,
        typeIds: typeIds?.length ? typeIds : undefined,
        manager: manager || undefined,
      }),
    staleTime: 60_000,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  const projects: DashboardTimelineProject[] = data?.projects ?? [];

  const enrichedProjects = useMemo(() => {
    if (!summaryById) {
      return projects;
    }
    return projects.map((project) => ({
      ...project,
      ...(summaryById[project.project_id] ?? {}),
    }));
  }, [projects, summaryById]);

  const resolvedSearchText = searchText ?? internalSearchText;
  const handleSearchChange = onSearchTextChange ?? setInternalSearchText;

  const resolvedMetaFieldIds = useMemo(
    () => (metaFieldIds ?? []).filter((id) => id !== 'project_name'),
    [metaFieldIds],
  );

  const resolveMetaLines = useMemo(() => {
    if (!resolvedMetaFieldIds.length) {
      return undefined;
    }
    return (project: DashboardTimelineProject) => {
      return resolvedMetaFieldIds
        .map((fieldId) => PROJECT_FIELD_MAP.get(fieldId))
        .filter(Boolean)
        .map((field) => {
          if (!field) return null;
          const value = formatProjectValue(field, project as ProjectSummary);
          if (value === '--') {
            return null;
          }
          return renderTimelineMeta(field, project as ProjectSummary);
        })
        .filter(Boolean) as ReactNode[];
    };
  }, [resolvedMetaFieldIds]);

  const model = useTimelineModel({
    projects: enrichedProjects,
    projectIds,
    manager,
    type,
    client,
    searchText: resolvedSearchText,
    preset,
    zoom,
    resolveMetaLines,
  });

  const activeFilters = useMemo(() => {
    const list = [];
    if (manager) list.push(`Manager: ${manager}`);
    if (type) list.push(`Type: ${type}`);
    if (client) list.push(`Client: ${client}`);
    if (projectIds?.length) list.push(`Projects: ${projectIds.length}`);
    return list;
  }, [manager, type, client, projectIds]);

  return (
    <Box data-testid="linear-timeline-panel">
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} sx={{ mb: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
          {activeFilters.length ? (
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
              {activeFilters.map((label) => (
                <Chip key={label} size="small" label={label} />
              ))}
            </Stack>
          ) : null}
        </Box>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <ToggleButtonGroup
            size="small"
            value={preset}
            exclusive
            onChange={(_, next) => {
              if (next) setPreset(next);
            }}
            aria-label="Timeline presets"
          >
            <ToggleButton value="all">All</ToggleButton>
            <ToggleButton value="active">Active</ToggleButton>
            <ToggleButton value="overdue">Overdue</ToggleButton>
          </ToggleButtonGroup>
          <ToggleButtonGroup
            size="small"
            value={zoom}
            exclusive
            onChange={(_, next) => {
              if (next) setZoom(next);
            }}
            aria-label="Timeline zoom"
          >
            <ToggleButton value="week">Week</ToggleButton>
            <ToggleButton value="month">Month</ToggleButton>
            <ToggleButton value="quarter">Quarter</ToggleButton>
          </ToggleButtonGroup>
          {showSearch && (
            <TextField
              size="small"
              placeholder="Search projects"
              value={resolvedSearchText}
              onChange={(event) => handleSearchChange(event.target.value)}
              sx={{ minWidth: 200 }}
            />
          )}
        </Stack>
      </Stack>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Timeline data unavailable: {error instanceof Error ? error.message : 'Request failed.'}
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ border: (theme) => `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
          {Array.from({ length: 8 }).map((_, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                height: 36,
                px: 1,
                borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
              }}
            >
              <Box sx={{ width: 180, height: 12, bgcolor: 'action.hover', borderRadius: 1 }} />
              <Box sx={{ flex: 1, height: 10, mx: 2, bgcolor: 'action.hover', borderRadius: 999 }} />
            </Box>
          ))}
        </Box>
      ) : model.rows.length ? (
        <TimelineGrid
          model={model}
          onRowClick={(row) => navigate(`/projects/${row.id}`)}
        />
      ) : (
        <Box
          sx={{
            border: (theme) => `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            p: 2,
            backgroundColor: 'background.paper',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            No timeline rows match the current filters.
          </Typography>
        </Box>
      )}

      <Divider sx={{ mt: 2 }} />
    </Box>
  );
}
