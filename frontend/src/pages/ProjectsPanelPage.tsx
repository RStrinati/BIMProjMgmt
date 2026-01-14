import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { projectsApi, usersApi, serviceReviewsApi } from '@/api';
import { projectServicesApi } from '@/api/services';
import type { Project, User } from '@/types/api';
import type { ProjectService, ProjectServicesListResponse } from '@/api/services';
import type { ServiceReview } from '@/types/api';
import { ListView } from '@/components/ui/ListView';
import { DetailsPanel } from '@/components/ui/DetailsPanel';
import { InlineField } from '@/components/ui/InlineField';
import { useNavigate } from 'react-router-dom';
import { ProjectStatusInline } from '@/components/projects/ProjectStatusInline';
import { ProjectLeadInline } from '@/components/projects/ProjectLeadInline';
import { ServiceStatusInline } from '@/components/projects/ServiceStatusInline';
import { ReviewStatusInline } from '@/components/projects/ReviewStatusInline';
import { useUpdateProject } from '@/hooks/useUpdateProject';
import { useUpdateServiceStatus } from '@/hooks/useUpdateServiceStatus';
import { useUpdateReviewStatus } from '@/hooks/useUpdateReviewStatus';
import { formatServiceStatusLabel } from '@/utils/serviceStatus';
import { formatReviewStatusLabel } from '@/utils/reviewStatus';

const VIEW_STORAGE_KEY = 'projects_panel_view_state';

type ViewId = 'all' | 'active' | 'on_hold' | 'completed' | 'my_work' | 'recently_updated';

type ViewState = {
  viewId: ViewId;
  searchTerm: string;
};

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

const stableSerialize = (value: Record<string, unknown>) =>
  JSON.stringify(value, Object.keys(value).sort());

const normaliseStatus = (value?: string | null) =>
  value ? value.trim().toLowerCase().replace(/\s+/g, '_') : '';

const parseDateValue = (value?: string | null) => {
  if (!value) {
    return 0;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
};

const formatNumber = (value?: number | null, suffix?: string) => {
  if (value === undefined || value === null) {
    return '--';
  }
  const formatted = Number.isFinite(Number(value)) ? Number(value).toLocaleString() : String(value);
  return suffix ? `${formatted} ${suffix}` : formatted;
};

export default function ProjectsPanelPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const storedViewState = useMemo(() => safeParseStoredViewState(), []);
  const [viewId, setViewId] = useState<ViewId>(storedViewState.viewId);
  const [searchTerm, setSearchTerm] = useState(storedViewState.searchTerm);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [serviceSaveError, setServiceSaveError] = useState<string | null>(null);
  const [reviewSaveError, setReviewSaveError] = useState<string | null>(null);
  const [panelTab, setPanelTab] = useState(0);

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
      { id: 'all' as const, label: 'All', filter: (_: Project) => true },
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

  const projectsFilters = useMemo(
    () => ({
      viewId: activeView.id,
      currentUserId: activeView.id === 'my_work' ? currentUserId : null,
    }),
    [activeView.id, currentUserId],
  );
  const projectsFiltersKey = useMemo(() => stableSerialize(projectsFilters), [projectsFilters]);
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects', projectsFiltersKey],
    queryFn: () => projectsApi.getAll(),
  });

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });
  const updateProject = useUpdateProject();
  const updateServiceStatus = useUpdateServiceStatus();
  const updateReviewStatus = useUpdateReviewStatus();

  const filtered = useMemo(() => {
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

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(
      VIEW_STORAGE_KEY,
      JSON.stringify({ viewId, searchTerm } satisfies ViewState),
    );
  }, [viewId, searchTerm]);

  const handleResetFilters = () => {
    setViewId(DEFAULT_VIEW_STATE.viewId);
    setSearchTerm(DEFAULT_VIEW_STATE.searchTerm);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(VIEW_STORAGE_KEY);
    }
  };

  const showMyWorkHint = activeView.id === 'my_work' && currentUserId == null;
  const showEmptyResultsBanner =
    projects.length > 0 &&
    filtered.length === 0 &&
    (activeView.id !== 'all' || Boolean(searchTerm.trim()));

  const selectedProject = filtered.find((project) => project.project_id === selectedId) ?? filtered[0] ?? null;

  const servicesParams = useMemo(() => ({}), []);
  const { data: servicesPayload } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', selectedProject?.project_id, servicesParams],
    queryFn: () =>
      selectedProject ? projectServicesApi.getAll(selectedProject.project_id) : Promise.resolve([]),
    enabled: Boolean(selectedProject),
  });

  const services = useMemo<ProjectService[]>(() => {
    if (!servicesPayload) {
      return [];
    }
    if (Array.isArray(servicesPayload)) {
      return servicesPayload;
    }
    const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
    return Array.isArray(items) ? items : [];
  }, [servicesPayload]);

  useEffect(() => {
    if (!services.length) {
      setSelectedServiceId(null);
      return;
    }
    const stillExists = services.some((service) => service.service_id === selectedServiceId);
    if (!stillExists) {
      setSelectedServiceId(services[0].service_id);
    }
  }, [services, selectedServiceId]);

  const selectedService =
    services.find((service) => service.service_id === selectedServiceId) ?? services[0] ?? null;

  const {
    data: reviews = [],
    isLoading: reviewsLoading,
    isFetching: reviewsFetching,
  } = useQuery<ServiceReview[]>({
    queryKey: ['serviceReviews', selectedProject?.project_id, selectedService?.service_id],
    queryFn: async () => {
      if (!selectedProject || !selectedService) {
        return [];
      }
      const response = await serviceReviewsApi.getAll(
        selectedProject.project_id,
        selectedService.service_id,
      );
      return response.data;
    },
    enabled: Boolean(selectedProject && selectedService),
  });

  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);

  useEffect(() => {
    if (!reviews.length) {
      setSelectedReviewId(null);
      return;
    }
    const stillExists = reviews.some((review) => review.review_id === selectedReviewId);
    if (!stillExists) {
      setSelectedReviewId(reviews[0].review_id);
    }
  }, [reviews, selectedReviewId]);

  const selectedReview =
    reviews.find((review) => review.review_id === selectedReviewId) ?? reviews[0] ?? null;

  const handleHover = (project: Project) => {
    queryClient.prefetchQuery({
      queryKey: ['project', project.project_id],
      queryFn: () => projectsApi.getById(project.project_id),
    });
  };

  const handleStatusChange = (nextStatus: string | null) => {
    if (!selectedProject) {
      return;
    }
    setSaveError(null);
    updateProject.mutate(
      { projectId: selectedProject.project_id, patch: { status: nextStatus || null } },
      {
        onError: (error) => {
          setSaveError(error.message || 'Failed to update status.');
        },
      },
    );
  };

  const handleLeadChange = (nextLead: number | null) => {
    if (!selectedProject) {
      return;
    }
    setSaveError(null);
    updateProject.mutate(
      { projectId: selectedProject.project_id, patch: { internal_lead: nextLead } },
      {
        onError: (error) => {
          setSaveError(error.message || 'Failed to update project lead.');
        },
      },
    );
  };

  const handleServiceStatusChange = (nextStatus: string | null) => {
    if (!selectedProject || !selectedService) {
      return;
    }
    setServiceSaveError(null);
    updateServiceStatus.mutate(
      {
        projectId: selectedProject.project_id,
        serviceId: selectedService.service_id,
        status: nextStatus,
        params: servicesParams,
      },
      {
        onError: (error) => {
          setServiceSaveError(error.message || 'Failed to update service status.');
        },
      },
    );
  };

  const handleReviewStatusChange = (nextStatus: string | null) => {
    if (!selectedProject || !selectedService || !selectedReview) {
      return;
    }
    setReviewSaveError(null);
    updateReviewStatus.mutate(
      {
        projectId: selectedProject.project_id,
        serviceId: selectedService.service_id,
        reviewId: selectedReview.review_id,
        status: nextStatus,
      },
      {
        onError: (error) => {
          setReviewSaveError(error.message || 'Failed to update review status.');
        },
      },
    );
  };

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null) {
      return '--';
    }
    return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(value);
  };

  const formatDate = (value?: string | null) => {
    if (!value) {
      return '--';
    }
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
  };

  return (
    <Box
      data-testid="projects-panel-root"
      sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '360px 1fr' }, gap: 2 }}
    >
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Typography variant="h5">Projects</Typography>
          <Stack spacing={1}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Typography variant="subtitle2">Views</Typography>
              <Button size="small" onClick={handleResetFilters} data-testid="projects-panel-view-reset">
                Reset
              </Button>
            </Stack>
            <ToggleButtonGroup
              exclusive
              value={viewId}
              onChange={(_event, nextView) => {
                if (nextView) {
                  setViewId(nextView);
                }
              }}
              size="small"
              fullWidth
              data-testid="projects-panel-view-group"
            >
              {viewDefinitions.map((view) => (
                <ToggleButton
                  key={view.id}
                  value={view.id}
                  data-testid={`projects-panel-view-${view.id}`}
                >
                  {view.label}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip label={`View: ${activeView.label}`} size="small" variant="outlined" />
              {searchTerm.trim() && (
                <Chip label={`Search: ${searchTerm.trim()}`} size="small" variant="outlined" />
              )}
            </Stack>
            {showMyWorkHint && (
              <Typography variant="caption" color="warning.main">
                Set `current_user_id` in localStorage to enable My Work filtering.
              </Typography>
            )}
          </Stack>
          <TextField
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <Divider />
          {showEmptyResultsBanner && (
            <Alert
              severity="info"
              action={(
                <Button size="small" onClick={handleResetFilters} data-testid="projects-panel-empty-reset">
                  Reset to All
                </Button>
              )}
              sx={{ mx: 2 }}
              data-testid="projects-panel-empty-banner"
            >
              No results for this view. Reset to All.
            </Alert>
          )}
          <ListView<Project>
            items={filtered}
            getItemId={(project) => project.project_id}
            getItemTestId={(project) => `projects-panel-list-row-${project.project_id}`}
            selectedId={selectedProject?.project_id ?? null}
            onSelect={(project) => setSelectedId(project.project_id)}
            onHover={handleHover}
            renderPrimary={(project) => project.project_name}
            renderSecondary={(project) => project.client_name || project.project_number || 'Unassigned client'}
            emptyState={
              <Typography color="text.secondary" sx={{ px: 2 }}>
                {isLoading ? 'Loading projects...' : 'No projects found.'}
              </Typography>
            }
          />
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 3 }} data-testid="projects-panel-details">
        <DetailsPanel
          title={selectedProject?.project_name ?? 'Select a project'}
          subtitle={selectedProject?.client_name || 'Unassigned client'}
          actions={
            selectedProject && (
              <Button size="small" onClick={() => navigate(`/projects/${selectedProject.project_id}`)}>
                Open full project
              </Button>
            )
          }
          emptyState={
            <Typography color="text.secondary">Select a project to view details.</Typography>
          }
        >
          {selectedProject && (
            <Stack spacing={2}>
              <Tabs value={panelTab} onChange={(_event, value) => setPanelTab(value)}>
                <Tab label="Details" />
                <Tab label="Services" />
              </Tabs>
              {panelTab === 0 && (
                <Stack spacing={2}>
                  <InlineField label="Project #" value={selectedProject.project_number || selectedProject.contract_number} />
                  {saveError && (
                    <Alert severity="error" data-testid="projects-panel-save-error">
                      {saveError}
                    </Alert>
                  )}
                  <ProjectStatusInline
                    value={selectedProject.status ?? null}
                    onChange={handleStatusChange}
                    isSaving={updateProject.isPending}
                    disabled={updateProject.isPending}
                  />
                  <InlineField label="Type" value={selectedProject.project_type || selectedProject.type_name} />
                  <InlineField label="Manager" value={selectedProject.project_manager} />
                  <ProjectLeadInline
                    value={selectedProject.internal_lead ?? null}
                    users={users}
                    onChange={handleLeadChange}
                    isSaving={updateProject.isPending}
                    disabled={updateProject.isPending || users.length === 0}
                  />
                  <InlineField label="Start date" value={selectedProject.start_date} />
                  <InlineField label="End date" value={selectedProject.end_date} />
                  <InlineField label="Area" value={formatNumber(selectedProject.area_hectares, 'ha')} />
                  <InlineField label="Capacity" value={formatNumber(selectedProject.mw_capacity, 'MW')} />
                  <InlineField label="Naming convention" value={selectedProject.naming_convention} />
                  <InlineField label="Address" value={selectedProject.address} />
                  <InlineField label="City" value={selectedProject.city} />
                  <InlineField label="State" value={selectedProject.state} />
                  <InlineField label="Postcode" value={selectedProject.postcode} />
                  <InlineField label="Model folder" value={selectedProject.folder_path} />
                  <InlineField label="IFC folder" value={selectedProject.ifc_folder_path} />
                  <InlineField label="Description" value={selectedProject.description} />
                </Stack>
              )}
              {panelTab === 1 && (
                <Stack spacing={2}>
                  <ListView<ProjectService>
                    items={services}
                    getItemId={(service) => service.service_id}
                    getItemTestId={(service) => `projects-panel-service-row-${service.service_id}`}
                    selectedId={selectedService?.service_id ?? null}
                    onSelect={(service) => setSelectedServiceId(service.service_id)}
                    renderPrimary={(service) => `${service.service_code} - ${service.service_name}`}
                    renderSecondary={(service) =>
                      [
                        service.phase ? `Phase: ${service.phase}` : null,
                        service.status ? `Status: ${formatServiceStatusLabel(service.status)}` : null,
                        service.progress_pct != null ? `Progress: ${service.progress_pct}%` : null,
                        service.agreed_fee != null ? `Fee: ${formatCurrency(service.agreed_fee)}` : null,
                      ]
                        .filter(Boolean)
                        .join(' | ')
                    }
                    emptyState={
                      <Typography color="text.secondary" sx={{ px: 2 }}>
                        {selectedProject ? 'No services for this project yet.' : 'Select a project to view services.'}
                      </Typography>
                    }
                  />
                  {selectedService && (
                    <Stack spacing={2}>
                      {serviceSaveError && (
                        <Alert severity="error" data-testid="projects-panel-service-save-error">
                          {serviceSaveError}
                        </Alert>
                      )}
                      <InlineField label="Service code" value={selectedService.service_code} />
                      <InlineField label="Service name" value={selectedService.service_name} />
                      <InlineField label="Phase" value={selectedService.phase} />
                      <ServiceStatusInline
                        value={selectedService.status ?? null}
                        onChange={handleServiceStatusChange}
                        isSaving={updateServiceStatus.isPending}
                        disabled={updateServiceStatus.isPending}
                      />
                      <InlineField label="Progress" value={formatNumber(selectedService.progress_pct, '%')} />
                      <InlineField label="Agreed fee" value={formatCurrency(selectedService.agreed_fee)} />
                      <Stack spacing={1}>
                        <Typography variant="subtitle2">Reviews</Typography>
                        <ListView<ServiceReview>
                          items={reviews}
                          getItemId={(review) => review.review_id}
                          getItemTestId={(review) => `projects-panel-review-row-${review.review_id}`}
                          selectedId={selectedReview?.review_id ?? null}
                          onSelect={(review) => setSelectedReviewId(review.review_id)}
                          renderPrimary={(review) =>
                            `Cycle ${review.cycle_no} · ${formatReviewStatusLabel(review.status)}`
                          }
                          renderSecondary={(review) =>
                            [
                              `Planned: ${formatDate(review.planned_date)}`,
                              review.due_date ? `Due: ${formatDate(review.due_date)}` : null,
                              review.disciplines ? `Disciplines: ${review.disciplines}` : null,
                              review.deliverables ? `Deliverables: ${review.deliverables}` : null,
                              review.is_billed != null ? `Billed: ${review.is_billed ? 'Yes' : 'No'}` : null,
                            ]
                              .filter(Boolean)
                              .join(' | ')
                          }
                          emptyState={
                            <Typography color="text.secondary" sx={{ px: 2 }}>
                              {reviewsLoading || reviewsFetching
                                ? 'Loading reviews...'
                                : 'No reviews for this service yet.'}
                            </Typography>
                          }
                        />
                        {selectedReview && (
                          <Stack spacing={2}>
                            {reviewSaveError && (
                              <Alert severity="error" data-testid="projects-panel-review-save-error">
                                {reviewSaveError}
                              </Alert>
                            )}
                            <InlineField label="Cycle" value={selectedReview.cycle_no} />
                            <InlineField label="Planned date" value={formatDate(selectedReview.planned_date)} />
                            <InlineField label="Due date" value={formatDate(selectedReview.due_date)} />
                            <ReviewStatusInline
                              value={selectedReview.status ?? null}
                              onChange={handleReviewStatusChange}
                              isSaving={updateReviewStatus.isPending}
                              disabled={updateReviewStatus.isPending}
                            />
                            <InlineField label="Disciplines" value={selectedReview.disciplines} />
                            <InlineField label="Deliverables" value={selectedReview.deliverables} />
                            <InlineField label="Billed" value={selectedReview.is_billed ? 'Yes' : 'No'} />
                          </Stack>
                        )}
                      </Stack>
                    </Stack>
                  )}
                </Stack>
              )}
            </Stack>
          )}
        </DetailsPanel>
      </Paper>
    </Box>
  );
}
