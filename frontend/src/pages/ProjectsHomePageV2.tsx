import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  MenuItem,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api';
import type { Project } from '@/types/api';
import { ListView } from '@/components/ui/ListView';
import { TimelinePanel } from '@/components/timeline_v2/TimelinePanel';
import { featureFlags } from '@/config/featureFlags';

type DisplayMode = 'list' | 'board' | 'timeline';

type ViewId = 'all' | 'active' | 'on_hold' | 'completed' | 'my_work' | 'recently_updated';

type ViewState = {
  viewId: ViewId;
  searchTerm: string;
};

const VIEW_STORAGE_KEY = 'projects_panel_view_state';
const DISPLAY_STORAGE_KEY = 'projects_home_display_mode';

const VIEW_IDS: ViewId[] = ['all', 'active', 'on_hold', 'completed', 'my_work', 'recently_updated'];

const DEFAULT_VIEW_STATE: ViewState = {
  viewId: 'all',
  searchTerm: '',
};

const safeParseStoredViewState = () => {
  if (typeof window === 'undefined') {
    return DEFAULT_VIEW_STATE;
  }
  const raw = window.localStorage.getItem(VIEW_STORAGE_KEY);
  if (!raw) {
    return DEFAULT_VIEW_STATE;
  }
  try {
    const parsed = JSON.parse(raw) as Partial<ViewState>;
    if (!parsed || typeof parsed !== 'object') {
      return DEFAULT_VIEW_STATE;
    }
    const parsedViewId = VIEW_IDS.includes(parsed.viewId as ViewId)
      ? (parsed.viewId as ViewId)
      : DEFAULT_VIEW_STATE.viewId;
    return {
      viewId: parsedViewId,
      searchTerm: typeof parsed.searchTerm === 'string' ? parsed.searchTerm : DEFAULT_VIEW_STATE.searchTerm,
    };
  } catch {
    return DEFAULT_VIEW_STATE;
  }
};

const readDisplayMode = (): DisplayMode => {
  if (typeof window === 'undefined') {
    return 'list';
  }
  const raw = window.localStorage.getItem(DISPLAY_STORAGE_KEY);
  if (raw === 'board' || raw === 'timeline' || raw === 'list') {
    return raw;
  }
  return 'list';
};

const normaliseStatus = (value?: string | null) =>
  value ? value.trim().toLowerCase().replace(/\s+/g, '_') : '';

const parseDateValue = (value?: string | null) => {
  if (!value) {
    return 0;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
};

export default function ProjectsHomePageV2() {
  const navigate = useNavigate();
  const storedViewState = useMemo(() => safeParseStoredViewState(), []);
  const [displayMode, setDisplayMode] = useState<DisplayMode>(readDisplayMode);
  const [viewId, setViewId] = useState<ViewId>(storedViewState.viewId);
  const [searchTerm, setSearchTerm] = useState(storedViewState.searchTerm);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  const currentUserId = useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    const raw = window.localStorage.getItem('current_user_id') || window.localStorage.getItem('user_id');
    if (!raw) {
      return null;
    }
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, []);

  useEffect(() => {
    if (viewId === 'my_work' && currentUserId == null) {
      setViewId('all');
    }
  }, [viewId, currentUserId]);

  const viewDefinitions = useMemo(
    () => [
      { id: 'all' as const, label: 'All projects', filter: (_: Project) => true },
      {
        id: 'active' as const,
        label: 'Active',
        filter: (project: Project) => normaliseStatus(project.status) === 'active',
      },
      {
        id: 'on_hold' as const,
        label: 'On Hold',
        filter: (project: Project) => normaliseStatus(project.status) === 'on_hold',
      },
      {
        id: 'completed' as const,
        label: 'Completed',
        filter: (project: Project) => normaliseStatus(project.status) === 'completed',
      },
      {
        id: 'my_work' as const,
        label: 'My Work',
        filter: (project: Project) => (currentUserId != null ? project.internal_lead === currentUserId : false),
      },
      {
        id: 'recently_updated' as const,
        label: 'Recently Updated',
        filter: (_: Project) => true,
        sort: (a: Project, b: Project) =>
          parseDateValue(b.updated_at || b.created_at) - parseDateValue(a.updated_at || a.created_at),
      },
    ],
    [currentUserId],
  );

  const activeView = viewDefinitions.find((view) => view.id === viewId) ?? viewDefinitions[0];

  const { data: projects = [], isLoading, error } = useQuery({
    queryKey: ['projects-home-v2'],
    queryFn: () => projectsApi.getAll(),
  });

  const filteredProjects = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();
    const viewFiltered = projects.filter(activeView.filter);
    const searched = normalized
      ? viewFiltered.filter((project) =>
          [
            project.project_name,
            project.project_number,
            project.contract_number,
            project.client_name,
          ]
            .map((value) => (value ? String(value).toLowerCase() : ''))
            .some((value) => value.includes(normalized)),
        )
      : viewFiltered;
    const sorted = activeView.sort ? [...searched].sort(activeView.sort) : searched;
    return sorted;
  }, [projects, searchTerm, activeView]);

  const timelineProjectIds = useMemo(
    () => filteredProjects.map((project) => project.project_id),
    [filteredProjects],
  );

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(
      VIEW_STORAGE_KEY,
      JSON.stringify({ viewId, searchTerm } satisfies ViewState),
    );
  }, [viewId, searchTerm]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(DISPLAY_STORAGE_KEY, displayMode);
  }, [displayMode]);

  const showMyWorkHint = activeView.id === 'my_work' && currentUserId == null;

  return (
    <Box data-testid="projects-home-v2-root" sx={{ display: 'grid', gap: 2 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} justifyContent="space-between">
        <Stack spacing={0.5}>
          <Typography variant="h4">Projects</Typography>
          <Typography variant="body2" color="text.secondary">
            Track project status across list, board, and timeline.
          </Typography>
        </Stack>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <TextField
            select
            size="small"
            label="View"
            value={viewId}
            onChange={(event) => setViewId(event.target.value as ViewId)}
            sx={{ minWidth: 180 }}
            data-testid="projects-home-view-select"
          >
            {viewDefinitions.map((view) => (
              <MenuItem key={view.id} value={view.id}>
                {view.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            size="small"
            placeholder="Search projects"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            sx={{ minWidth: 220 }}
            inputProps={{ 'data-testid': 'projects-home-search' }}
          />
          <ToggleButtonGroup
            exclusive
            value={displayMode}
            onChange={(_event, nextMode) => {
              if (nextMode) {
                setDisplayMode(nextMode);
              }
            }}
            size="small"
            data-testid="projects-home-display-mode"
          >
            <ToggleButton value="list">List</ToggleButton>
            <ToggleButton value="board">Board</ToggleButton>
            <ToggleButton value="timeline">Timeline</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Stack>

      {showMyWorkHint && (
        <Alert severity="info">Set `current_user_id` in localStorage to enable My Work filtering.</Alert>
      )}

      {error && (
        <Alert severity="error">
          Failed to load projects. Please try again.
        </Alert>
      )}

      {displayMode === 'list' && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <ListView<Project>
            items={filteredProjects}
            getItemId={(project) => project.project_id}
            getItemTestId={(project) => `projects-home-list-row-${project.project_id}`}
            selectedId={selectedProjectId}
            onSelect={(project) => {
              setSelectedProjectId(project.project_id);
              navigate(`/projects/${project.project_id}`);
            }}
            renderPrimary={(project) => project.project_name}
            renderSecondary={(project) => project.client_name || project.project_number || 'Unassigned client'}
            emptyState={
              <Typography color="text.secondary" sx={{ px: 2 }}>
                {isLoading ? 'Loading projects...' : 'No projects found.'}
              </Typography>
            }
          />
        </Paper>
      )}

      {displayMode === 'board' && (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            Board view
          </Typography>
          <Typography color="text.secondary">
            Board layout is coming next. Switch to List or Timeline for now.
          </Typography>
        </Paper>
      )}

      {displayMode === 'timeline' && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          {featureFlags.linearTimeline ? (
            <TimelinePanel
              title="Projects timeline"
              projectIds={timelineProjectIds.length ? timelineProjectIds : undefined}
              searchText={searchTerm}
              onSearchTextChange={setSearchTerm}
              showSearch={false}
            />
          ) : (
            <Typography color="text.secondary">
              Enable `ff_linear_timeline` to view the new timeline.
            </Typography>
          )}
        </Paper>
      )}
    </Box>
  );
}
