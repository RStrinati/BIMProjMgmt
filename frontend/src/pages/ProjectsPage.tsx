import { Profiler, Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Grid,
  Typography,
  TextField,
  Button,
  Chip,
  IconButton,
  InputAdornment,
  CircularProgress,
  Alert,
  Stack,
  Checkbox,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { projectsApi, usersApi } from '@/api';
import type { Project, User } from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';
import { featureFlags } from '@/config/featureFlags';
import ProjectsPanelPage from '@/pages/ProjectsPanelPage';
import ProjectsHomePageV2 from '@/pages/ProjectsHomePageV2';

const ProjectFormDialog = lazy(() => import('@/components/ProjectFormDialog'));

const REVERSE_PRIORITY_MAP: Record<number, string> = { 1: "Low", 2: "Medium", 3: "High", 4: "Critical" };

const resolvePriorityLabel = (
  priority: Project['priority'],
  fallbackLabel?: string | null
): string | null => {
  if (fallbackLabel && fallbackLabel.trim() !== '') {
    return fallbackLabel;
  }

  if (typeof priority === 'number') {
    return REVERSE_PRIORITY_MAP[priority] || 'Medium';
  }

  if (typeof priority === 'string' && priority.trim() !== '') {
    const trimmed = priority.trim();
    if (/^\d+$/.test(trimmed)) {
      const numericPriority = parseInt(trimmed, 10);
      return REVERSE_PRIORITY_MAP[numericPriority] || 'Medium';
    }
    return trimmed;
  }

  return fallbackLabel ?? null;
};

const formatNumericDisplay = (value: number | string | null | undefined): string => {
  if (value === undefined || value === null || value === '') {
    return '';
  }
  const numericValue = Number(value);
  if (Number.isFinite(numericValue)) {
    return numericValue.toLocaleString();
  }
  return String(value);
};

export function ProjectsPage() {
  // Prefer panel UI when explicitly enabled
  if (featureFlags.projectsPanel) {
    return <ProjectsPanelPage />;
  }
  if (featureFlags.projectsHomeV2) {
    return <ProjectsHomePageV2 />;
  }

  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilters, setStatusFilters] = useState<string[]>([]);
  const [typeFilters, setTypeFilters] = useState<string[]>([]);
  const [managerFilters, setManagerFilters] = useState<string[]>([]);
  const [clientFilters, setClientFilters] = useState<string[]>([]);
  const [selectedProjectIds, setSelectedProjectIds] = useState<number[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [statsEnabled, setStatsEnabled] = useState(false);

  // Fetch projects using React Query
  const projectFilters = {};
  const {
    data: projects,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['projects', projectFilters],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats', projectFilters],
    queryFn: () => projectsApi.getStats(),
    enabled: statsEnabled,
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 60 * 1000,
  });

  // Fetch review statistics
  const { data: reviewStats } = useQuery({
    queryKey: ['projects', 'review-stats', projectFilters],
    queryFn: () => projectsApi.getReviewStats(),
  });

  const { data: users } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const userNameById = useMemo(() => {
    const map = new Map<number, string>();
    (users ?? []).forEach((user) => {
      const label = user.name || user.full_name || user.username || `User ${user.user_id}`;
      map.set(user.user_id, label);
    });
    return map;
  }, [users]);

  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
    []
  );
  const formatCurrency = (value?: number | null) => currencyFormatter.format(value ?? 0);

  // Sync filters with URL to keep header/global search aligned
  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    const trimmedSearch = searchTerm.trim();
    if (trimmedSearch) {
      next.set('search', trimmedSearch);
    } else {
      next.delete('search');
    }

    const setList = (key: string, values: string[]) => {
      if (values.length) {
        next.set(key, values.join(','));
      } else {
        next.delete(key);
      }
    };

    setList('status', statusFilters);
    setList('type', typeFilters);
    setList('manager', managerFilters);
    setList('client', clientFilters);
    setSearchParams(next, { replace: true });
  }, [searchTerm, statusFilters, typeFilters, managerFilters, clientFilters]);

  useEffect(() => {
    const parseList = (key: string) => {
      const raw = searchParams.get(key);
      return raw ? raw.split(',').filter(Boolean) : [];
    };
    setSearchTerm(searchParams.get('search') ?? '');
    setStatusFilters(parseList('status'));
    setTypeFilters(parseList('type'));
    setManagerFilters(parseList('manager'));
    setClientFilters(parseList('client'));
  }, [searchParams.toString()]);

  const toggleFilter = (value: string, current: string[], setter: (val: string[]) => void) => {
    setter(
      current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value],
    );
  };

  const normalizeFilterValue = (value?: string | null) => (value ?? '').trim().toLowerCase();
  const normalizedStatusFilters = statusFilters.map(normalizeFilterValue);
  const normalizedTypeFilters = typeFilters.map(normalizeFilterValue);
  const normalizedManagerFilters = managerFilters.map(normalizeFilterValue);
  const normalizedClientFilters = clientFilters.map(normalizeFilterValue);

  // Filter projects based on search and chips
  const normalizedSearch = searchTerm.trim().toLowerCase();

  const filteredProjects = projects?.filter((project) => {
    if (normalizedSearch) {
      const searchableValues = [
        project.project_name,
        project.project_number,
        project.contract_number,
        project.client_name,
        project.naming_convention,
      ];
      const matchesSearch = searchableValues
        .map((value) => (value ? value.toString().toLowerCase() : ''))
        .some((value) => value.includes(normalizedSearch));
      if (!matchesSearch) {
        return false;
      }
    }

    const status = normalizeFilterValue(project.status?.toString());
    const type = normalizeFilterValue(project.project_type?.toString());
    const manager = normalizeFilterValue(project.project_manager?.toString());
    const client = normalizeFilterValue(project.client_name?.toString());
    if (normalizedStatusFilters.length && !normalizedStatusFilters.includes(status)) return false;
    if (normalizedTypeFilters.length && !normalizedTypeFilters.includes(type)) return false;
    if (normalizedManagerFilters.length && !normalizedManagerFilters.includes(manager)) return false;
    if (normalizedClientFilters.length && !normalizedClientFilters.includes(client)) return false;

    return true;
  });

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

  const handleCreateProject = () => {
    setDialogMode('create');
    setSelectedProject(null);
    setDialogOpen(true);
  };

  const handleEditProject = (project: Project) => {
    setDialogMode('edit');
    setSelectedProject(project);
    setDialogOpen(true);
  };

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}/workspace/overview`);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedProject(null);
  };

  const filterOptions = useMemo(() => {
    const statuses = new Set<string>();
    const types = new Set<string>();
    const managers = new Set<string>();
    const clients = new Set<string>();
    (projects ?? []).forEach((p) => {
      if (p.status) statuses.add(p.status);
      if (p.project_type) types.add(p.project_type);
      if (p.project_manager) managers.add(p.project_manager);
      if (p.client_name) clients.add(p.client_name);
    });
    const sort = (values: Set<string>) => Array.from(values).sort((a, b) => a.localeCompare(b));
    return {
      statuses: sort(statuses),
      types: sort(types),
      managers: sort(managers),
      clients: sort(clients),
    };
  }, [projects]);

  const handleToggleSelect = (projectId: number) => {
    setSelectedProjectIds((prev) =>
      prev.includes(projectId) ? prev.filter((id) => id !== projectId) : [...prev, projectId],
    );
  };

  const handleCopySelection = async () => {
    if (!filteredProjects || selectedProjectIds.length === 0) return;
    const payload = filteredProjects
      .filter((p) => selectedProjectIds.includes(p.project_id))
      .map((p) => `${p.project_name} (${p.project_number ?? 'N/A'})`)
      .join('\n');
    try {
      await navigator.clipboard.writeText(payload);
    } catch (error) {
      console.error('Failed to copy selection', error);
    }
  };

  return (
    <Profiler id="ProjectsPage" onRender={profilerLog}>
      <Box data-testid="projects-legacy-root">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Projects
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage all your BIM construction projects
        </Typography>
      </Box>

      {/* Filter chips and bulk actions */}
      <Stack spacing={2} sx={{ mb: 3 }}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="subtitle2" color="text.secondary">
            Status
          </Typography>
          {filterOptions.statuses.map((status) => (
            <Chip
              key={status}
              label={status}
              size="small"
              color={statusFilters.includes(status) ? 'primary' : 'default'}
              onClick={() => toggleFilter(status, statusFilters, setStatusFilters)}
            />
          ))}
          {!filterOptions.statuses.length && <Chip label="No statuses yet" size="small" variant="outlined" />}
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="subtitle2" color="text.secondary">
            Type
          </Typography>
          {filterOptions.types.map((type) => (
            <Chip
              key={type}
              label={type}
              size="small"
              color={typeFilters.includes(type) ? 'primary' : 'default'}
              onClick={() => toggleFilter(type, typeFilters, setTypeFilters)}
            />
          ))}
          {!filterOptions.types.length && <Chip label="No project types yet" size="small" variant="outlined" />}
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="subtitle2" color="text.secondary">
            Manager
          </Typography>
          {filterOptions.managers.map((manager) => (
            <Chip
              key={manager}
              label={manager}
              size="small"
              color={managerFilters.includes(manager) ? 'primary' : 'default'}
              onClick={() => toggleFilter(manager, managerFilters, setManagerFilters)}
            />
          ))}
          {!filterOptions.managers.length && <Chip label="No managers yet" size="small" variant="outlined" />}
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="subtitle2" color="text.secondary">
            Client
          </Typography>
          {filterOptions.clients.map((client) => (
            <Chip
              key={client}
              label={client}
              size="small"
              color={clientFilters.includes(client) ? 'primary' : 'default'}
              onClick={() => toggleFilter(client, clientFilters, setClientFilters)}
            />
          ))}
          {!filterOptions.clients.length && <Chip label="No clients yet" size="small" variant="outlined" />}
        </Stack>

        {selectedProjectIds.length > 0 && (
          <Alert
            severity="info"
            action={(
              <Stack direction="row" spacing={1}>
                <Tooltip title="Copy selected projects to clipboard">
                  <IconButton color="inherit" size="small" onClick={handleCopySelection}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Button size="small" onClick={() => setSelectedProjectIds([])}>
                  Clear selection
                </Button>
              </Stack>
            )}
          >
            {selectedProjectIds.length} project(s) selected for bulk actions
          </Alert>
        )}
      </Stack>

      {/* Stats Cards */}
      {!statsEnabled && (
        <Box sx={{ mb: 3 }}>
          <Button variant="outlined" onClick={() => setStatsEnabled(true)}>
            Load project stats
          </Button>
        </Box>
      )}

      {statsEnabled && stats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Projects
                </Typography>
                <Typography variant="h3">{stats.total}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active
                </Typography>
                <Typography variant="h3" color="success.main">
                  {stats.active}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Completed
                </Typography>
                <Typography variant="h3" color="info.main">
                  {stats.completed}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  On Hold
                </Typography>
                <Typography variant="h3" color="warning.main">
                  {stats.on_hold}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search and Actions */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ whiteSpace: 'nowrap' }}
          onClick={handleCreateProject}
        >
          New Project
        </Button>
        <Tooltip title="Reset filters">
          <IconButton
            onClick={() => {
              setStatusFilters([]);
              setTypeFilters([]);
              setManagerFilters([]);
              setClientFilters([]);
              setSearchTerm('');
            }}
          >
            <FilterListIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load projects. Please try again.
          <Button size="small" onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Projects Grid */}
      {!isLoading && !error && (
        <Grid container spacing={{ xs: 2, md: 2.5 }}>
          {filteredProjects?.map((project) => {
            const projectNumber =
              project.project_number ?? project.contract_number ?? null;
            const priorityLabel = resolvePriorityLabel(project.priority, project.priority_label) ?? undefined;
            const projectLeadName =
              project.internal_lead !== undefined && project.internal_lead !== null
                ? userNameById.get(project.internal_lead) ?? `User ${project.internal_lead}`
                : null;
            const areaDisplay = formatNumericDisplay(project.area_hectares);
            const capacityDisplay = formatNumericDisplay(project.mw_capacity);
            const totalServiceAgreedRaw = Number(project.total_service_agreed_fee ?? project.agreed_fee ?? 0);
            const totalServiceBilledRaw = Number(project.total_service_billed_amount ?? 0);
            const totalServiceAgreed = Number.isFinite(totalServiceAgreedRaw) ? Math.max(totalServiceAgreedRaw, 0) : 0;
            const totalServiceBilled = Number.isFinite(totalServiceBilledRaw) ? Math.max(totalServiceBilledRaw, 0) : 0;
            const serviceBilledPctRaw =
              project.service_billed_pct !== undefined && project.service_billed_pct !== null
                ? Number(project.service_billed_pct)
                : Number.NaN;
            let billedPercent =
              Number.isFinite(serviceBilledPctRaw) && !Number.isNaN(serviceBilledPctRaw)
                ? serviceBilledPctRaw
                : totalServiceAgreed > 0
                  ? (totalServiceBilled / totalServiceAgreed) * 100
                  : 0;
            if (!Number.isFinite(billedPercent)) {
              billedPercent = 0;
            }
            const clampedBilledPercent = Math.min(Math.max(billedPercent, 0), 100);
            const unbilledAmount = Math.max(totalServiceAgreed - totalServiceBilled, 0);
            const showBillingSummary = totalServiceAgreed > 0.01;

            return (
              <Grid item xs={12} sm={6} md={4} key={project.project_id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1, p: 2, pb: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1.5 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={selectedProjectIds.includes(project.project_id)}
                              onChange={() => handleToggleSelect(project.project_id)}
                            />
                          )}
                          label=""
                          sx={{ m: 0 }}
                        />
                        <Box>
                          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
                            {project.project_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Project #: {projectNumber || 'N/A'}
                          </Typography>
                        </Box>
                      </Box>
                      <Stack direction="column" spacing={0.5} alignItems="flex-end">
                        {project.status && (
                          <Chip
                            label={project.status}
                            color={getStatusColor(project.status)}
                            size="small"
                          />
                        )}
                        {priorityLabel && (
                          <Chip
                            label={`Priority: ${priorityLabel}`}
                            color="info"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </Box>

                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: showBillingSummary ? '1fr auto' : '1fr',
                        gap: 1.5,
                        mt: 1.5,
                        mb: showBillingSummary ? 1.5 : 1,
                      }}
                    >
                      <Stack spacing={0.5}>
                        {project.client_name && (
                          <Typography variant="body2" color="text.secondary">
                            Client: {project.client_name}
                          </Typography>
                        )}

                        {project.project_type && (
                          <Typography variant="body2" color="text.secondary">
                            Type: {project.project_type}
                          </Typography>
                        )}

                        {projectLeadName && (
                          <Typography variant="body2" color="text.secondary">
                            Lead: {projectLeadName}
                          </Typography>
                        )}

                        {areaDisplay && (
                          <Typography variant="body2" color="text.secondary">
                            Area: {areaDisplay} ha
                          </Typography>
                        )}

                        {capacityDisplay && (
                          <Typography variant="body2" color="text.secondary">
                            Capacity: {capacityDisplay} MW
                          </Typography>
                        )}

                        {project.naming_convention && (
                          <Typography variant="body2" color="text.secondary">
                            Naming: {project.naming_convention}
                          </Typography>
                        )}

                        {project.description && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              mt: 1,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                            }}
                          >
                            {project.description}
                          </Typography>
                        )}
                      </Stack>

                      {showBillingSummary && (
                        <Box sx={{ textAlign: 'center', minWidth: 96 }}>
                          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                            <CircularProgress
                              variant="determinate"
                              value={100}
                              size={70}
                              thickness={4}
                              sx={{ color: 'grey.200' }}
                            />
                            <CircularProgress
                              variant="determinate"
                              value={clampedBilledPercent}
                              size={70}
                              thickness={4}
                              sx={{
                                color: clampedBilledPercent >= 99 ? 'success.main' : 'primary.main',
                                position: 'absolute',
                                left: 0,
                                top: 0,
                              }}
                            />
                            <Box
                              sx={{
                                top: 0,
                                left: 0,
                                bottom: 0,
                                right: 0,
                                position: 'absolute',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              <Typography variant="subtitle2" component="span" sx={{ fontWeight: 600 }}>
                                {Math.round(clampedBilledPercent)}%
                              </Typography>
                            </Box>
                          </Box>
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.75 }}>
                            {formatCurrency(totalServiceBilled)} / {formatCurrency(totalServiceAgreed)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {unbilledAmount > 0 ? `Unbilled ${formatCurrency(unbilledAmount)}` : 'Fully billed'}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {/* Review Statistics */}
                    {reviewStats && reviewStats[project.project_id] && (
                      <Box sx={{ mt: 1.5, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.75 }}>
                          Reviews
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Chip
                            label={`${reviewStats[project.project_id].total_reviews} Total`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                          <Chip
                            label={`${reviewStats[project.project_id].completed_reviews} Completed`}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                          {reviewStats[project.project_id].upcoming_reviews_30_days > 0 && (
                            <Chip
                              label={`${reviewStats[project.project_id].upcoming_reviews_30_days} Upcoming`}
                              size="small"
                              color="warning"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    )}
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pt: 0.5, pb: 1.5 }}>
                    <Button
                      size="small"
                      startIcon={<VisibilityIcon />}
                      onClick={() => handleViewProject(project.project_id)}
                    >
                      View
                    </Button>
                    <IconButton size="small" onClick={() => handleEditProject(project)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredProjects?.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm ? 'Try adjusting your search' : 'Get started by creating your first project'}
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreateProject}>
            Create Project
          </Button>
        </Box>
      )}

      {/* Project Form Dialog */}
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
            key={selectedProject?.project_id || 'new'}
            open={dialogOpen}
            onClose={handleCloseDialog}
            project={selectedProject}
            mode={dialogMode}
          />
        </Suspense>
      )}
      </Box>
    </Profiler>
  );
}
