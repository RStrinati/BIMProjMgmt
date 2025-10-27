import { Profiler, Suspense, lazy, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { projectsApi, usersApi } from '@/api';
import type { Project, User } from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';

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
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');

  // Fetch projects using React Query
  const {
    data: projects,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: () => projectsApi.getStats(),
  });

  // Fetch review statistics
  const { data: reviewStats } = useQuery({
    queryKey: ['projects', 'review-stats'],
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

  // Filter projects based on search
  const normalizedSearch = searchTerm.trim().toLowerCase();

  const filteredProjects = projects?.filter((project) => {
    if (!normalizedSearch) {
      return true;
    }

    const searchableValues = [
      project.project_name,
      project.project_number,
      project.contract_number,
      project.client_name,
      project.naming_convention,
    ];

    return searchableValues
      .map((value) => (value ? value.toString().toLowerCase() : ''))
      .some((value) => value.includes(normalizedSearch));
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
    navigate(`/projects/${projectId}`);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedProject(null);
  };

  return (
    <Profiler id="ProjectsPage" onRender={profilerLog}>
      <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Projects
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage all your BIM construction projects
        </Typography>
      </Box>

      {/* Stats Cards */}
      {stats && (
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
        <IconButton>
          <FilterListIcon />
        </IconButton>
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
        <Grid container spacing={3}>
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
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: 2,
                        mb: showBillingSummary ? 2 : 1.5,
                      }}
                    >
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
                            {project.project_name}
                          </Typography>
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
                            />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Project #: {projectNumber || 'N/A'}
                        </Typography>
                      </Box>
                      {showBillingSummary && (
                        <Box sx={{ textAlign: 'center', minWidth: 100 }}>
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
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                            {formatCurrency(totalServiceBilled)} / {formatCurrency(totalServiceAgreed)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {unbilledAmount > 0 ? `Unbilled ${formatCurrency(unbilledAmount)}` : 'Fully billed'}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {project.client_name && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Client: {project.client_name}
                      </Typography>
                    )}

                    {project.project_type && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Type: {project.project_type}
                      </Typography>
                    )}

                    {areaDisplay && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Area: {areaDisplay} ha
                      </Typography>
                    )}

                    {capacityDisplay && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Capacity: {capacityDisplay} MW
                      </Typography>
                    )}

                    {project.naming_convention && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Naming: {project.naming_convention}
                      </Typography>
                    )}

                    {projectLeadName && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Lead: {projectLeadName}
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

                    {/* Review Statistics */}
                    {reviewStats && reviewStats[project.project_id] && (
                      <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
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

                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
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
