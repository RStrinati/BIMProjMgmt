import { useEffect, useMemo, useState, lazy, Suspense } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  MenuItem,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Card,
  CardContent,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api';
import type { Project } from '@/types/api';
import { ListView } from '@/components/ui/ListView';
import { TimelinePanel } from '@/components/timeline_v2/TimelinePanel';
import { featureFlags } from '@/config/featureFlags';

const ProjectFormDialog = lazy(() => import('@/components/ProjectFormDialog'));

type DisplayMode = 'list' | 'board' | 'timeline';

type ViewId = 'all' | 'active' | 'on_hold' | 'completed' | 'my_work' | 'recently_updated';

type ViewState = {
  viewId: ViewId;
  searchTerm: string;
};

type SortField = 'name' | 'status' | 'target_date' | 'health';
type SortOrder = 'asc' | 'desc';

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

const getStatusColor = (status?: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status?.toLowerCase()) {
    case 'active':
      return 'success';
    case 'on hold':
      return 'warning';
    case 'completed':
      return 'default';
    default:
      return 'default';
  }
};

export default function ProjectsHomePageV2() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const storedViewState = useMemo(() => safeParseStoredViewState(), []);
  const [displayMode, setDisplayMode] = useState<DisplayMode>(readDisplayMode);
  const [viewId, setViewId] = useState<ViewId>(storedViewState.viewId);
  const [searchTerm, setSearchTerm] = useState(storedViewState.searchTerm);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

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

  const { data: projects = [], isLoading, error, refetch } = useQuery({
    queryKey: ['projects-home-v2'],
    queryFn: () => projectsApi.getAllWithHealth(),
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
    
    // Apply table sort
    return [...sorted].sort((a, b) => {
      let aVal: any = '';
      let bVal: any = '';
      
      if (sortField === 'name') {
        aVal = a.project_name || '';
        bVal = b.project_name || '';
      } else if (sortField === 'status') {
        aVal = a.status || '';
        bVal = b.status || '';
      } else if (sortField === 'target_date') {
        aVal = parseDateValue(a.end_date);
        bVal = parseDateValue(b.end_date);
      } else if (sortField === 'health') {
        aVal = a.health_pct ?? -1;
        bVal = b.health_pct ?? -1;
      }
      
      if (typeof aVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });
  }, [projects, searchTerm, activeView, sortField, sortOrder]);

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

  const handleSortClick = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleCreateProject = () => {
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleProjectCreated = () => {
    setDialogOpen(false);
    // Invalidate and refetch projects
    queryClient.invalidateQueries({ queryKey: ['projects-home-v2'] });
    refetch();
  };

  // Get unique statuses for board grouping
  const statusGroups = useMemo(() => {
    const statuses = new Set<string>();
    filteredProjects.forEach((p) => {
      if (p.status) statuses.add(p.status);
    });
    return Array.from(statuses).sort();
  }, [filteredProjects]);

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
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
            data-testid="create-project-button"
          >
            Create Project
          </Button>
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

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* LIST VIEW */}
      {displayMode === 'list' && !isLoading && (
        <TableContainer component={Paper} variant="outlined" data-testid="projects-list-table">
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'name'}
                    direction={sortField === 'name' ? sortOrder : 'asc'}
                    onClick={() => handleSortClick('name')}
                  >
                    Project Name
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'health'}
                    direction={sortField === 'health' ? sortOrder : 'asc'}
                    onClick={() => handleSortClick('health')}
                  >
                    Health %
                  </TableSortLabel>
                </TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Lead</TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'target_date'}
                    direction={sortField === 'target_date' ? sortOrder : 'asc'}
                    onClick={() => handleSortClick('target_date')}
                  >
                    Target Date
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortField === 'status'}
                    direction={sortField === 'status' ? sortOrder : 'asc'}
                    onClick={() => handleSortClick('status')}
                  >
                    Status
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredProjects.map((project) => (
                <TableRow
                  key={project.project_id}
                  data-testid={`project-row-${project.project_id}`}
                  hover
                  onClick={() => navigate(`/projects/${project.project_id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{project.project_name || '—'}</TableCell>
                  <TableCell>
                    {project.health_pct != null ? `${Math.round(project.health_pct)}%` : '—'}
                  </TableCell>
                  <TableCell>{project.priority || '—'}</TableCell>
                  <TableCell>{project.internal_lead || '—'}</TableCell>
                  <TableCell>
                    {project.end_date ? new Date(project.end_date).toLocaleDateString() : '—'}
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{
                        color: getStatusColor(project.status) === 'success' ? 'success.main' : 
                               getStatusColor(project.status) === 'warning' ? 'warning.main' : 'inherit',
                      }}
                    >
                      {project.status || '—'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
              {filteredProjects.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      {isLoading ? 'Loading...' : 'No projects found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* BOARD VIEW */}
      {displayMode === 'board' && !isLoading && (
        <Box
          data-testid="projects-board-view"
          sx={{
            display: 'grid',
            gridTemplateColumns: `repeat(auto-fit, minmax(320px, 1fr))`,
            gap: 2,
          }}
        >
          {statusGroups.map((status) => {
            const statusProjects = filteredProjects.filter((p) => p.status === status);
            return (
              <Paper key={status} variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1.5 }}>
                  {status} ({statusProjects.length})
                </Typography>
                <Stack spacing={1}>
                  {statusProjects.map((project) => (
                    <Card
                      key={project.project_id}
                      data-testid={`project-card-${project.project_id}`}
                      sx={{
                        p: 1.5,
                        cursor: 'pointer',
                        '&:hover': { boxShadow: 1 },
                      }}
                      onClick={() => navigate(`/projects/${project.project_id}`)}
                    >
                      <CardContent sx={{ p: 0 }}>
                        <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                          {project.project_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {project.client_name || 'Unassigned'}
                        </Typography>
                        {project.health_pct != null && (
                          <Typography variant="caption" display="block" sx={{ mt: 0.5, color: 'primary.main' }}>
                            Health: {Math.round(project.health_pct)}%
                          </Typography>
                        )}
                        {project.end_date && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            Target: {new Date(project.end_date).toLocaleDateString()}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                  {statusProjects.length === 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      No projects
                    </Typography>
                  )}
                </Stack>
              </Paper>
            );
          })}
          {statusGroups.length === 0 && (
            <Typography color="text.secondary">No projects found.</Typography>
          )}
        </Box>
      )}

      {/* TIMELINE VIEW */}
      {displayMode === 'timeline' && !isLoading && (
        <Paper variant="outlined" sx={{ p: 2, overflow: 'hidden' }} data-testid="projects-timeline-view">
          {featureFlags.linearTimeline ? (
            <Box sx={{ width: '100%', overflow: 'auto' }}>
              <TimelinePanel
                title="Projects timeline"
                projectIds={timelineProjectIds.length ? timelineProjectIds : undefined}
                searchText={searchTerm}
                onSearchTextChange={setSearchTerm}
                showSearch={false}
              />
            </Box>
          ) : (
            <Typography color="text.secondary">
              Enable `ff_linear_timeline` to view the new timeline.
            </Typography>
          )}
        </Paper>
      )}

      {/* CREATE PROJECT DIALOG */}
      {dialogOpen && (
        <Suspense
          fallback={(
            <Box
              position="fixed"
              top={0}
              left={0}
              right={0}
              bottom={0}
              display="flex"
              alignItems="center"
              justifyContent="center"
              sx={{ bgcolor: 'rgba(0,0,0,0.25)', zIndex: (theme) => theme.zIndex.modal - 1 }}
            >
              <CircularProgress />
            </Box>
          )}
        >
          <ProjectFormDialog
            key="create-new"
            open={dialogOpen}
            onClose={handleDialogClose}
            mode="create"
            onSuccess={handleProjectCreated}
          />
        </Suspense>
      )}
    </Box>
  );
}
