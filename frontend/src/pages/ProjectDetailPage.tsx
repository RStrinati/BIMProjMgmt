import React, { Profiler, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  Tabs,
  Tab,
  Stack,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  CalendarToday as CalendarIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { projectsApi } from '@/api/projects';
import { usersApi } from '@/api/users';
import { issuesApi } from '@/api';
import { projectServicesApi } from '@/api/services';
import type { ProjectService, ProjectServicesListResponse } from '@/api/services';
import type { Project, User } from '@/types/api';
import { ProjectServicesTab } from '@/components/ProjectServicesTab_Linear';
import { profilerLog } from '@/utils/perfLogger';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface ProjectIssuesOverview {
  summary?: {
    total_issues?: number;
    acc_issues?: { total?: number; open?: number; closed?: number };
    revizto_issues?: { total?: number; open?: number; closed?: number };
    overall?: { open?: number; closed?: number };
  };
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const REVERSE_PRIORITY_MAP: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' };

const resolvePriorityLabel = (
  priority: Project['priority'],
  fallbackLabel?: string | null
): string => {
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

  return 'Medium';
};

const formatNumericDisplay = (value: number | string | null | undefined): string => {
  if (value === undefined || value === null || value === '') {
    return 'N/A';
  }

  const numericValue = Number(value);
  if (Number.isFinite(numericValue)) {
    return numericValue.toLocaleString();
  }

  return String(value);
};

const getUserLabel = (user: User): string =>
  user.name || user.full_name || user.username || `User ${user.user_id}`;

const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(1);

  const projectId = Number(id);
  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.getById(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: users } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const {
    data: issuesOverview,
    isLoading: issuesLoading,
    error: issuesError,
  } = useQuery<ProjectIssuesOverview>({
    queryKey: ['project', projectId, 'issues-overview'],
    queryFn: () => issuesApi.getProjectOverview(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: servicesPayload } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', projectId, { scope: 'billing' }],
    queryFn: () => projectServicesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });

  const servicesForBilling = useMemo<ProjectService[]>(() => {
    if (!servicesPayload) {
      return [];
    }
    if (Array.isArray(servicesPayload)) {
      return servicesPayload;
    }
    const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
    return Array.isArray(items) ? items : [];
  }, [servicesPayload]);

  const billingTotals = useMemo(() => {
    if (!servicesForBilling.length) {
      return null;
    }
    return servicesForBilling.reduce(
      (acc, service) => {
        const agreed = service.agreed_fee ?? 0;
        const billed = service.billed_amount ?? service.claimed_to_date ?? 0;
        return {
          totalAgreed: acc.totalAgreed + agreed,
          totalBilled: acc.totalBilled + billed,
        };
      },
      { totalAgreed: 0, totalBilled: 0 },
    );
  }, [servicesForBilling]);

  const projectLeadName = useMemo(() => {
    if (!project || project.internal_lead === undefined || project.internal_lead === null) {
      return null;
    }
    const leadUser = (users ?? []).find((user) => user.user_id === project.internal_lead);
    if (leadUser) {
      return getUserLabel(leadUser);
    }
    return `User ${project.internal_lead}`;
  }, [project, users]);

  const priorityLabel = useMemo(() => {
    if (!project) {
      return 'Medium';
    }
    return resolvePriorityLabel(project.priority, project.priority_label);
  }, [project]);

  const areaDisplay = useMemo(
    () => formatNumericDisplay(project?.area_hectares),
    [project?.area_hectares]
  );

  const capacityDisplay = useMemo(
    () => formatNumericDisplay(project?.mw_capacity),
    [project?.mw_capacity]
  );

  const deleteMutation = useMutation<void, Error, number>({
    mutationFn: (projectId: number) => projectsApi.delete(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'review-stats'] });
      queryClient.removeQueries({ queryKey: ['project', projectId], exact: true });
      navigate('/projects');
    },
  });

  const handleEdit = () => {
    // TODO: Open edit dialog
    console.log('Edit project:', id);
  };

  const handleDelete = () => {
    if (!id) {
      return;
    }

    const projectId = Number(id);
    if (Number.isNaN(projectId)) {
      return;
    }

    const confirmationMessage = project?.project_name
      ? `Delete project "${project.project_name}" and all related data? This action cannot be undone.`
      : 'Delete this project and all related data? This action cannot be undone.';

    if (window.confirm(confirmationMessage)) {
      deleteMutation.mutate(projectId);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load project details. {error instanceof Error ? error.message : ''}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mt: 2 }}>
          Back to Projects
        </Button>
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'on hold':
        return 'warning';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  const totalServiceAgreedRaw = Number(
    billingTotals?.totalAgreed ?? project.total_service_agreed_fee ?? project.agreed_fee ?? 0,
  );
  const totalServiceBilledRaw = Number(
    billingTotals?.totalBilled ?? project.total_service_billed_amount ?? 0,
  );
  const totalServiceAgreed = Number.isFinite(totalServiceAgreedRaw) ? Math.max(totalServiceAgreedRaw, 0) : 0;
  const totalServiceBilled = Number.isFinite(totalServiceBilledRaw) ? Math.max(totalServiceBilledRaw, 0) : 0;
  const serviceBilledPctRaw =
    !billingTotals && project.service_billed_pct !== undefined && project.service_billed_pct !== null
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

  return (
    <Profiler id="ProjectDetailPage" onRender={profilerLog}>
      <Box>
      {deleteMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {deleteMutation.error.message || 'Failed to delete project'}
        </Alert>
      )}

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/projects')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1">
              {project.project_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Project #{project.project_number ?? project.contract_number ?? 'N/A'}
            </Typography>
          </Box>
          <Chip label={project.status} color={getStatusColor(project.status ?? '')} />
        </Box>
        <Box display="flex" gap={1}>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </Box>
      </Box>

      {/* Overview Summary */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Status & Priority
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip label={project.status} color={getStatusColor(project.status ?? '')} />
                <Chip label={`Priority: ${priorityLabel}`} color="info" variant="outlined" />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Client: {project.client_name || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Type: {project.project_type || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Schedule & Lead
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start: {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                End: {project.end_date ? new Date(project.end_date).toLocaleDateString() : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Lead: {projectLeadName || 'Unassigned'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Billing Summary
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <CircularProgress
                  variant="determinate"
                  value={clampedBilledPercent}
                  size={60}
                  thickness={4}
                  sx={{ color: clampedBilledPercent >= 99 ? 'success.main' : 'primary.main' }}
                />
                <Box>
                  <Typography variant="h6">
                    {Math.round(clampedBilledPercent)}% billed
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatNumericDisplay(totalServiceBilled)} / {formatNumericDisplay(totalServiceAgreed)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {unbilledAmount > 0 ? `Unbilled ${formatNumericDisplay(unbilledAmount)}` : 'Fully billed'}
                  </Typography>
                </Box>
              </Stack>
              <Button
                variant="outlined"
                size="small"
                sx={{ mt: 1 }}
                onClick={() => setTabValue(0)}
              >
                Manage services
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Column - Project Details */}
        <Grid item xs={12} md={8}>
          <Paper>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Services" />
              <Tab label="Details" />
              <Tab label="Dashboard" />
              <Tab label="Reviews" />
              <Tab label="Tasks" />
              <Tab label="Files" />
            </Tabs>
            <Divider />

            {/* Services Tab */}
            <TabPanel value={tabValue} index={0}>
              <ProjectServicesTab projectId={projectId} />
            </TabPanel>

            {/* Details Tab */}
            <TabPanel value={tabValue} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Client
                  </Typography>
                  <Typography variant="body1">{project.client_name || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Project Type
                  </Typography>
                  <Typography variant="body1">{project.project_type || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Start Date
                  </Typography>
                  <Typography variant="body1">
                    {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    End Date
                  </Typography>
                  <Typography variant="body1">
                    {project.end_date ? new Date(project.end_date).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Priority
                  </Typography>
                  <Typography variant="body1">{priorityLabel || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Area (ha)
                  </Typography>
                  <Typography variant="body1">
                    {areaDisplay === 'N/A' ? 'N/A' : `${areaDisplay} ha`}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    MW Capacity
                  </Typography>
                  <Typography variant="body1">
                    {capacityDisplay === 'N/A' ? 'N/A' : `${capacityDisplay} MW`}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Naming Convention
                  </Typography>
                  <Typography variant="body1">{project.naming_convention || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Project Lead
                  </Typography>
                  <Typography variant="body1">{projectLeadName || 'Unassigned'}</Typography>
                </Grid>

                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Address
                  </Typography>
                  <Typography variant="body1">
                    {[project.address, project.city, project.state, project.postcode]
                      .filter(Boolean)
                      .join(', ') || 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Folder Path
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <FolderIcon fontSize="small" color="action" />
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {project.folder_path || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    IFC Folder Path
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <FolderIcon fontSize="small" color="action" />
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {project.ifc_folder_path || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>

                {project.description && (
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1">{project.description}</Typography>
                  </Grid>
                )}
              </Grid>
            </TabPanel>

            {/* Dashboard Tab */}
            <TabPanel value={tabValue} index={2}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Issues Overview
                  </Typography>

                  {issuesLoading && (
                    <Box display="flex" alignItems="center" gap={2}>
                      <CircularProgress size={24} />
                      <Typography variant="body2" color="text.secondary">
                        Loading project issues...
                      </Typography>
                    </Box>
                  )}

                  {!issuesLoading && issuesError && (
                    <Alert severity="error">
                      Failed to load issues overview. {issuesError instanceof Error ? issuesError.message : ''}
                    </Alert>
                  )}

                  {!issuesLoading && !issuesError && (
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography color="text.secondary" variant="subtitle2" gutterBottom>
                            Total Issues
                          </Typography>
                          <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                            {issuesOverview?.summary?.total_issues ?? 0}
                          </Typography>
                          <TrendingUpIcon sx={{ fontSize: 28, opacity: 0.3, mt: 1 }} />
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography color="text.secondary" variant="subtitle2" gutterBottom>
                            ACC Issues
                          </Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>
                            {issuesOverview?.summary?.acc_issues?.total ?? 0}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
                            <Chip
                              label={`Open: ${issuesOverview?.summary?.acc_issues?.open ?? 0}`}
                              color="error"
                              size="small"
                            />
                            <Chip
                              label={`Closed: ${issuesOverview?.summary?.acc_issues?.closed ?? 0}`}
                              color="success"
                              size="small"
                            />
                          </Box>
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography color="text.secondary" variant="subtitle2" gutterBottom>
                            Revizto Issues
                          </Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>
                            {issuesOverview?.summary?.revizto_issues?.total ?? 0}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
                            <Chip
                              label={`Open: ${issuesOverview?.summary?.revizto_issues?.open ?? 0}`}
                              color="error"
                              size="small"
                            />
                            <Chip
                              label={`Closed: ${issuesOverview?.summary?.revizto_issues?.closed ?? 0}`}
                              color="success"
                              size="small"
                            />
                          </Box>
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography color="text.secondary" variant="subtitle2" gutterBottom>
                            Overall Status
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                            <Box>
                              <ErrorIcon color="error" />
                              <Typography variant="body2">Open</Typography>
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {issuesOverview?.summary?.overall?.open ?? 0}
                              </Typography>
                            </Box>
                            <Box>
                              <CheckCircleIcon color="success" />
                              <Typography variant="body2">Closed</Typography>
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {issuesOverview?.summary?.overall?.closed ?? 0}
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>
                  )}
                </CardContent>
              </Card>
            </TabPanel>

            {/* Reviews Tab */}
            <TabPanel value={tabValue} index={3}>
              <Alert severity="info">
                Reviews are now managed within the Services tab. Please go to the Services tab and select a service to view and manage its reviews.
              </Alert>
            </TabPanel>

            {/* Tasks Tab */}
            <TabPanel value={tabValue} index={4}>
              <Alert severity="info">Tasks functionality coming soon</Alert>
            </TabPanel>

            {/* Files Tab */}
            <TabPanel value={tabValue} index={5}>
              <Alert severity="info">File management coming soon</Alert>
            </TabPanel>
          </Paper>
        </Grid>

        {/* Right Column - Quick Stats & Actions */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {project.created_at ? new Date(project.created_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body1">
                    {project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button variant="outlined" startIcon={<CalendarIcon />} fullWidth>
                  Schedule Review
                </Button>
                <Button variant="outlined" startIcon={<FolderIcon />} fullWidth>
                  Open Folder
                </Button>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => navigate(`/projects/${projectId}/data-imports`)}
                >
                  Data Imports
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
    </Profiler>
  );
};

export default ProjectDetailPage;
