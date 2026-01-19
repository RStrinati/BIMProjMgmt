import { useMemo, useState, useCallback, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  Divider,
  Link as MuiLink,
  MenuItem,
  Paper,
  Snackbar,
  Stack,
  Tab,
  Tabs,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { invoiceBatchesApi, projectsApi, projectReviewsApi, serviceItemsApi, tasksApi, usersApi } from '@/api';
import { serviceReviewsApi } from '@/api/services';
import type { InvoiceBatch, Project, ProjectFinanceGrid, ProjectReviewItem, ProjectReviewsResponse, ServiceItem, ServiceReview, TaskPayload, User } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';
import { TasksNotesView } from '@/components/ProjectManagement/TasksNotesView';
import { IssuesTabContent } from '@/components/ProjectManagement/IssuesTabContent';
import { QualityTab } from './QualityTab';
import { featureFlags } from '@/config/featureFlags';
import { TimelinePanel } from '@/components/timeline_v2/TimelinePanel';
import { ReviewStatusInline } from '@/components/projects/ReviewStatusInline';
import { EditableCell, ToggleCell } from '@/components/projects/EditableCells';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import { toApiReviewStatus } from '@/utils/reviewStatus';
import { ProjectServicesList } from '@/features/projects/services/ProjectServicesList';
import { BlockerBadge } from '@/components/ui/BlockerBadge';
import { LinkedIssuesList } from '@/components/ui/LinkedIssuesList';
import { LinearListContainer, LinearListHeaderRow, LinearListRow, LinearListCell } from '@/components/ui/LinearList';
import { Dialog, DialogTitle, DialogContent, DialogActions, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { ProjectServicesTab as ProjectServicesTabLinear } from '@/components/ProjectServicesTab_Linear';

const BASE_TABS = ['Overview', 'Services', 'Deliverables', 'Issues', 'Tasks', 'Quality'] as const;
const DISPLAY_MODES = ['Comfortable', 'Compact'] as const;

type DisplayMode = (typeof DISPLAY_MODES)[number];

type ActivityEvent = {
  id: number;
  label: string;
  createdAt: string;
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '--';
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const toMonthString = (date: Date) => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `${date.getFullYear()}-${month}`;
};

const formatInvoiceMonth = (value?: string | null) => {
  if (!value) return null;
  if (/^\d{4}-\d{2}$/.test(value)) {
    return value;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return toMonthString(parsed);
};

export default function ProjectWorkspacePageV2() {
  const navigate = useNavigate();
  const { id } = useParams();
  const projectId = Number(id);
  const queryClient = useQueryClient();
  const showTimeline = featureFlags.linearTimeline;
  const [activeTab, setActiveTab] = useState(0);
  const [displayMode, setDisplayMode] = useState<DisplayMode>('Comfortable');
  const [taskDraft, setTaskDraft] = useState('');
  const [taskError, setTaskError] = useState<string | null>(null);
  const [reviewUpdateError, setReviewUpdateError] = useState<string | null>(null);
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);
  const [isReviewDetailOpen, setIsReviewDetailOpen] = useState(false);
  const [deliverableFilters, setDeliverableFilters] = useState({
    dueThisMonth: false,
    unbatched: false,
    readyToInvoice: false,
  });
  const [isServicesLinearUIEnabled, setIsServicesLinearUIEnabled] = useState(() => {
    return localStorage.getItem('servicesLinearUI') === 'true';
  });
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([{
    id: 1,
    label: 'Workspace opened',
    createdAt: new Date().toISOString(),
  }]);
  const [invoiceMonthNotification, setInvoiceMonthNotification] = useState<{ message: string; open: boolean }>({
    message: '',
    open: false,
  });

  // Handler for opening review detail modal
  const handleOpenReviewDetail = useCallback((reviewId: number) => {
    console.debug('[ProjectWorkspaceV2] Opening review detail modal', { reviewId });
    setSelectedReviewId(reviewId);
    setIsReviewDetailOpen(true);
    console.debug('[ProjectWorkspaceV2] State should be updated', { reviewId, isReviewDetailOpen: true });
  }, []);

  // Listen for localStorage changes (for feature flag updates)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'servicesLinearUI') {
        const newValue = e.newValue === 'true';
        setIsServicesLinearUIEnabled(newValue);
      }
    };

    const handleFocus = () => {
      // Check localStorage on window focus (in case it was changed via dev tools)
      const newValue = localStorage.getItem('servicesLinearUI') === 'true';
      setIsServicesLinearUIEnabled(newValue);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('focus', handleFocus);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  // Log state changes for debugging
  useEffect(() => {
    console.debug('[ProjectWorkspaceV2] State changed', { selectedReviewId, isReviewDetailOpen });
  }, [selectedReviewId, isReviewDetailOpen]);

  // Log modal visibility state
  useEffect(() => {
    console.debug('[ProjectWorkspaceV2] Dialog visibility', {
      anchorLinksFlag: featureFlags.anchorLinks,
      isReviewDetailOpen,
      selectedReviewId,
      shouldDialogBeOpen: featureFlags.anchorLinks && isReviewDetailOpen && selectedReviewId !== null,
    });
  }, [isReviewDetailOpen, selectedReviewId]);

  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.getById(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: financeGrid } = useQuery<ProjectFinanceGrid>({
    queryKey: ['projectFinanceGrid', projectId],
    queryFn: () => projectsApi.getFinanceGrid(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const { data: recentTasksResult, isLoading: isRecentTasksLoading } = useQuery({
    queryKey: ['projectTasksPreview', projectId],
    queryFn: () =>
      tasksApi.getNotesView({
        project_id: projectId,
        page: 1,
        limit: 5,
      }),
    enabled: Number.isFinite(projectId),
  });

  const leadLabel = useMemo(() => {
    if (!project?.internal_lead) {
      return 'Unassigned';
    }
    const match = users.find((user) => user.user_id === project.internal_lead);
    return match?.name || match?.full_name || match?.username || `User ${project.internal_lead}`;
  }, [project, users]);

  const recentTasks = useMemo(
    () => (Array.isArray(recentTasksResult?.tasks) ? recentTasksResult.tasks : []),
    [recentTasksResult],
  );

  const resolveAssignee = (task: { assigned_to?: number | null; assigned_to_name?: string | null }) => {
    if (task.assigned_to_name) {
      return task.assigned_to_name;
    }
    if (!task.assigned_to) {
      return 'Unassigned';
    }
    const match = users.find((user) => user.user_id === task.assigned_to);
    return match?.name || match?.full_name || match?.username || `User ${task.assigned_to}`;
  };

  const createTask = useMutation({
    mutationFn: (payload: TaskPayload) => tasksApi.create(payload),
    onSuccess: (createdTask) => {
      const taskLabel = createdTask?.task_name || taskDraft.trim();
      setTaskDraft('');
      setTaskError(null);
      setActivityEvents((prev) => [
        {
          id: prev.length + 1,
          label: `Created task "${taskLabel}"`,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ]);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectTasksPreview', projectId] });
      }
    },
    onError: (err: any) => {
      setTaskError(err?.response?.data?.error || 'Failed to create task.');
    },
  });

  const handleAddTask = () => {
    if (!project || !taskDraft.trim()) {
      setTaskError('Task name is required.');
      return;
    }
    setTaskError(null);
    createTask.mutate({
      project_id: project.project_id,
      task_name: taskDraft.trim(),
    });
  };

  const progressSummary = useMemo(() => {
    if (!project) {
      return {
        totalAgreed: 0,
        totalBilled: 0,
        billedPct: 0,
      };
    }
    const totalAgreed = Number(project.total_service_agreed_fee ?? project.agreed_fee ?? 0) || 0;
    const totalBilled = Number(project.total_service_billed_amount ?? 0) || 0;
    const billedPctRaw = Number(project.service_billed_pct ?? 0);
    const billedPct = Number.isFinite(billedPctRaw) ? billedPctRaw : totalAgreed > 0 ? (totalBilled / totalAgreed) * 100 : 0;
    return {
      totalAgreed,
      totalBilled,
      billedPct: Math.min(Math.max(billedPct, 0), 100),
    };
  }, [project]);

  const reviewsFilters = useMemo(
    () => ({
      sort_by: 'planned_date' as const,
      sort_dir: 'asc' as const,
    }),
    [],
  );

  const {
    data: projectReviews,
    isLoading: projectReviewsLoading,
    error: projectReviewsError,
  } = useProjectReviews(projectId, reviewsFilters);

  const reviewItems = useMemo<ProjectReviewItem[]>(
    () => projectReviews?.items ?? [],
    [projectReviews],
  );

  const { data: projectItems, isLoading: projectItemsLoading, error: projectItemsError } = useQuery<{
    items: ServiceItem[];
    total: number;
  }>({
    queryKey: ['projectItems', projectId],
    queryFn: () => serviceItemsApi.getProjectItems(projectId),
    enabled: Number.isFinite(projectId),
  });

  const serviceItems = useMemo<ServiceItem[]>(
    () => projectItems?.items ?? [],
    [projectItems],
  );

  const { data: invoiceBatches = [] } = useQuery<InvoiceBatch[]>({
    queryKey: ['invoiceBatches', projectId],
    queryFn: () => invoiceBatchesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });

  const createInvoiceBatch = useMutation({
    mutationFn: (payload: Parameters<typeof invoiceBatchesApi.create>[0]) => invoiceBatchesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoiceBatches', projectId] });
    },
  });

  const filteredReviewItems = useMemo(() => {
    if (!deliverableFilters.dueThisMonth && !deliverableFilters.unbatched && !deliverableFilters.readyToInvoice) {
      return reviewItems;
    }
    const currentMonth = toMonthString(new Date());
    return reviewItems.filter((review) => {
      const invoiceMonth = formatInvoiceMonth(
        review.invoice_month_final
          || review.invoice_month_override
          || review.invoice_month_auto
          || review.due_date,
      ) ?? '';
      const matchesDueThisMonth = !deliverableFilters.dueThisMonth || invoiceMonth === currentMonth;
      const matchesUnbatched = !deliverableFilters.unbatched || review.invoice_batch_id == null;
      const matchesReady =
        !deliverableFilters.readyToInvoice
        || ((review.status || '').toLowerCase() === 'completed' && !review.is_billed);
      return matchesDueThisMonth && matchesUnbatched && matchesReady;
    });
  }, [deliverableFilters, reviewItems]);

  const filteredServiceItems = useMemo(() => {
    if (!deliverableFilters.dueThisMonth && !deliverableFilters.readyToInvoice) {
      return serviceItems;
    }
    const currentMonth = toMonthString(new Date());
    return serviceItems.filter((item) => {
      const dueMonth = formatInvoiceMonth(item.due_date) ?? '';
      const matchesDueThisMonth = !deliverableFilters.dueThisMonth || dueMonth === currentMonth;
      const matchesReady =
        !deliverableFilters.readyToInvoice
        || ((item.status || '').toLowerCase() === 'completed' && !item.is_billed);
      return matchesDueThisMonth && matchesReady;
    });
  }, [deliverableFilters, serviceItems]);

  const unbatchedRiskMetric = useMemo(() => {
    const currentMonth = toMonthString(new Date());
    const unbatchedDueThisMonth = reviewItems.filter((review) => {
      const invoiceMonth = review.invoice_month_final 
        || review.invoice_month_override 
        || review.invoice_month_auto 
        || formatInvoiceMonth(review.due_date);
      return (
        invoiceMonth === currentMonth &&
        review.invoice_batch_id == null &&
        (review.status || '').toLowerCase() !== 'cancelled' &&
        !review.is_billed
      );
    });
    return {
      count: unbatchedDueThisMonth.length,
      totalAmount: unbatchedDueThisMonth.reduce((sum, r) => sum + (r.billing_amount || 0), 0),
    };
  }, [reviewItems]);

  const updateReviewStatus = useMutation<
    Awaited<ReturnType<typeof serviceReviewsApi.update>>,
    Error,
    { review: ProjectReviewItem; status: string | null },
    { previousProjectReviews: Array<[unknown, ProjectReviewsResponse | undefined]>; previousServiceReviews?: ServiceReview[] }
  >({
    mutationFn: ({ review, status }) => {
      const statusValue = toApiReviewStatus(status);
      return serviceReviewsApi.update(projectId, review.service_id, review.review_id, {
        status: statusValue || undefined,
      });
    },
    onMutate: async ({ review, status }) => {
      setReviewUpdateError(null);
      const nextStatus = toApiReviewStatus(status);
      await queryClient.cancelQueries({ queryKey: ['projectReviews', projectId] });

      const previousProjectReviews = queryClient.getQueriesData<ProjectReviewsResponse>({
        queryKey: ['projectReviews', projectId],
      });

      queryClient.setQueriesData<ProjectReviewsResponse>(
        { queryKey: ['projectReviews', projectId] },
        (existing) => {
          if (!existing) return existing;
          return {
            ...existing,
            items: existing.items.map((item) =>
              item.review_id === review.review_id ? { ...item, status: nextStatus } : item,
            ),
          };
        },
      );

      const serviceReviewsKey = ['serviceReviews', projectId, review.service_id];
      const previousServiceReviews = queryClient.getQueryData<ServiceReview[]>(serviceReviewsKey);
      if (previousServiceReviews) {
        queryClient.setQueryData<ServiceReview[]>(serviceReviewsKey, (existing) =>
          existing?.map((item) =>
            item.review_id === review.review_id ? { ...item, status: nextStatus ?? item.status } : item,
          ) ?? existing,
        );
      }

      return { previousProjectReviews, previousServiceReviews };
    },
    onError: (error, { review }, context) => {
      setReviewUpdateError(error.message || 'Failed to update review status.');
      if (context?.previousProjectReviews) {
        context.previousProjectReviews.forEach(([key, data]) => {
          queryClient.setQueryData(key as unknown[], data);
        });
      }
      if (context?.previousServiceReviews) {
        queryClient.setQueryData(['serviceReviews', projectId, review.service_id], context.previousServiceReviews);
      }
    },
    onSettled: (_data, _error, { review }) => {
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, review.service_id] });
    },
  });

  // Generic mutation for deliverables field updates
  const updateDeliverableField = useMutation<
    ProjectReviewItem,
    Error,
    { review: ProjectReviewItem; fieldName: string; value: unknown },
    { previousProjectReviews: Array<[unknown, ProjectReviewsResponse | undefined]> }
  >({
    mutationFn: async ({ review, fieldName, value }) => {
      const payload = { [fieldName]: value };
      return projectReviewsApi.patchProjectReview(projectId, review.review_id, review.service_id, payload as any);
    },
    onSuccess: (updatedReview, { review, fieldName, value }) => {
      // Show notification when due_date change affects invoice_month_auto
      if (fieldName === 'due_date') {
        const oldInvoiceMonth = review.invoice_month_auto || formatInvoiceMonth(review.due_date);
        const newInvoiceMonth = updatedReview.invoice_month_auto || formatInvoiceMonth(value as string);
        if (oldInvoiceMonth && newInvoiceMonth && oldInvoiceMonth !== newInvoiceMonth) {
          const overrideValue = updatedReview.invoice_month_override || review.invoice_month_override;
          setInvoiceMonthNotification({
            message: overrideValue
              ? `Invoice month auto-calculated to ${newInvoiceMonth} but override (${overrideValue}) was preserved`
              : `Invoice month auto-calculated to ${newInvoiceMonth}`,
            open: true,
          });
        }
      }
    },
    onMutate: async ({ review, fieldName, value }) => {
      setReviewUpdateError(null);
      await queryClient.cancelQueries({ queryKey: ['projectReviews', projectId] });

      const previousProjectReviews = queryClient.getQueriesData<ProjectReviewsResponse>({
        queryKey: ['projectReviews', projectId],
      });

      queryClient.setQueriesData<ProjectReviewsResponse>(
        { queryKey: ['projectReviews', projectId] },
        (existing) => {
          if (!existing) return existing;
          return {
            ...existing,
            items: existing.items.map((item) =>
              item.review_id === review.review_id ? { ...item, [fieldName]: value } : item,
            ),
          };
        },
      );

      return { previousProjectReviews };
    },
    onError: (error, _variables, context) => {
      setReviewUpdateError(error.message || 'Failed to update review.');
      if (context?.previousProjectReviews) {
        context.previousProjectReviews.forEach(([key, data]) => {
          queryClient.setQueryData(key as unknown[], data);
        });
      }
    },
    onSettled: (_data, _error, { review }) => {
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, review.service_id] });
    },
  });

  const tabs = useMemo(() => {
    if (showTimeline) {
      return [...BASE_TABS, 'Timeline'];
    }
    return [...BASE_TABS];
  }, [showTimeline]);

  const activeLabel = tabs[activeTab] ?? tabs[0];

  return (
    <Box data-testid="project-workspace-v2-root" sx={{ display: 'grid', gap: 2 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} alignItems={{ md: 'center' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={1}>
          <Breadcrumbs aria-label="breadcrumb">
            <MuiLink underline="hover" color="inherit" onClick={() => navigate('/projects')} sx={{ cursor: 'pointer' }}>
              Projects
            </MuiLink>
            <Typography color="text.primary">Workspace</Typography>
          </Breadcrumbs>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            <Typography variant="h5">{project?.project_name || 'Loading project...'}</Typography>
            {project?.status && <Chip label={project.status} size="small" />}
            {project?.priority_label && <Chip label={`Priority: ${project.priority_label}`} size="small" variant="outlined" />}
            {project?.internal_lead != null && <Chip label={`Lead: ${leadLabel}`} size="small" variant="outlined" />}
          </Stack>
        </Stack>
        <ToggleButtonGroup
          exclusive
          value={displayMode}
          onChange={(_event, nextMode) => {
            if (nextMode) {
              setDisplayMode(nextMode);
            }
          }}
          size="small"
          data-testid="project-workspace-v2-display-mode"
        >
          {DISPLAY_MODES.map((mode) => (
            <ToggleButton key={mode} value={mode}>
              {mode}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Stack>

      {error && <Alert severity="error">Failed to load project.</Alert>}

      <Box data-testid="debug-anchor-links-flag" sx={{ p: 1, background: '#f0f0f0', mb: 2, fontSize: '12px' }}>
        anchorLinksFlag={String(featureFlags.anchorLinks)} | isReviewDetailOpen={String(isReviewDetailOpen)} | selectedReviewId={String(selectedReviewId)}
      </Box>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Tabs value={activeTab} onChange={(_event, value) => setActiveTab(value)}>
          {tabs.map((label) => (
            <Tab key={label} label={label} />
          ))}
        </Tabs>
        <Divider sx={{ my: 2 }} />

        {activeLabel === 'Overview' && (
          <Box
            data-testid="project-workspace-v2-overview"
            sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 2 }}
          >
            <Stack spacing={2}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Summary
                </Typography>
                <Typography color="text.secondary">
                  {project?.description || 'Add a description to summarize scope and outcomes.'}
                </Typography>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Add task
                </Typography>
                <Stack spacing={1}>
                  {taskError && <Alert severity="error">{taskError}</Alert>}
                  <TextField
                    size="small"
                    placeholder="New task"
                    value={taskDraft}
                    onChange={(event) => setTaskDraft(event.target.value)}
                  />
                  <Button variant="contained" onClick={handleAddTask} disabled={createTask.isPending || isLoading}>
                    {createTask.isPending ? 'Saving...' : 'Add task'}
                  </Button>
                </Stack>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Recent tasks
                </Typography>
                {isRecentTasksLoading ? (
                  <Typography color="text.secondary">Loading tasks...</Typography>
                ) : recentTasks.length ? (
                  <Stack spacing={1} data-testid="project-workspace-v2-recent-tasks">
                    {recentTasks.map((task) => (
                      <Box key={task.task_id} sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {task.task_name || 'Untitled task'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {resolveAssignee(task)}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(task.task_date)}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                ) : (
                  <Typography color="text.secondary">No tasks yet.</Typography>
                )}
              </Paper>
            </Stack>

            <Stack spacing={2}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Properties
                </Typography>
                <Stack spacing={1}>
                  <InlineField label="Project #" value={project?.project_number || project?.contract_number} />
                  <InlineField label="Client" value={project?.client_name} />
                  <InlineField label="Type" value={project?.project_type || project?.type_name} />
                  <InlineField label="Manager" value={project?.project_manager} />
                  <InlineField label="Start" value={formatDate(project?.start_date)} />
                  <InlineField label="End" value={formatDate(project?.end_date)} />
                </Stack>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Milestones
                </Typography>
                <Typography color="text.secondary">
                  Milestones will appear here once defined.
                </Typography>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Progress
                </Typography>
                <Stack spacing={1}>
                  <InlineField label="Agreed fee" value={formatCurrency(progressSummary.totalAgreed)} />
                  <InlineField label="Billed" value={formatCurrency(progressSummary.totalBilled)} />
                  <InlineField label="Billed %" value={`${Math.round(progressSummary.billedPct)}%`} />
                  <InlineField
                    label="Earned value %"
                    value={financeGrid ? `${Math.round(financeGrid.earned_value_pct)}%` : '--'}
                  />
                </Stack>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Invoice pipeline
                </Typography>
                {financeGrid ? (
                  <Stack spacing={1} data-testid="project-workspace-v2-invoice-pipeline">
                    <InlineField
                      label="Ready this month"
                      value={`${financeGrid.ready_this_month.ready_count} items · ${formatCurrency(financeGrid.ready_this_month.ready_amount)}`}
                    />
                    {unbatchedRiskMetric.count > 0 && (
                      <InlineField
                        label="Unbatched risk"
                        value={
                          <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box
                              component="span"
                              sx={{
                                display: 'inline-block',
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                bgcolor: 'warning.main',
                              }}
                            />
                            <span data-testid="unbatched-risk-count">
                              {unbatchedRiskMetric.count} due this month · {formatCurrency(unbatchedRiskMetric.totalAmount)}
                            </span>
                          </Box>
                        }
                      />
                    )}
                    <Stack spacing={0.5}>
                      {financeGrid.invoice_pipeline.map((item) => (
                        <Box key={item.month} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" color="text.secondary">
                            {item.month}
                          </Typography>
                          <Typography variant="caption">
                            {item.deliverables_count} · {formatCurrency(item.total_amount)}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Stack>
                ) : (
                  <Typography color="text.secondary">Loading invoice pipeline...</Typography>
                )}
              </Paper>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Activity
                </Typography>
                <Stack spacing={1}>
                  {activityEvents.map((event) => (
                    <Typography key={event.id} variant="body2" color="text.secondary">
                      {event.label} - {formatDate(event.createdAt)}
                    </Typography>
                  ))}
                </Stack>
              </Paper>
            </Stack>
          </Box>
        )}

        {activeLabel === 'Services' && (
          <Box data-testid="project-workspace-v2-services">
            {Number.isFinite(projectId) ? (
              isServicesLinearUIEnabled ? (
                <ProjectServicesTabLinear projectId={projectId} />
              ) : (
                <ProjectServicesList
                  projectId={projectId}
                  testIdPrefix="project-workspace-v2"
                />
              )
            ) : (
              <Typography color="text.secondary">Select a project to view services.</Typography>
            )}
          </Box>
        )}
        {activeLabel === 'Deliverables' && (
          <Box data-testid="project-workspace-v2-reviews">
            {reviewUpdateError && (
              <Alert severity="error" sx={{ mb: 2 }} data-testid="project-workspace-v2-reviews-error">
                {reviewUpdateError}
              </Alert>
            )}
            {projectReviewsError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Failed to load project reviews.
              </Alert>
            )}
            {projectReviewsLoading ? (
              <Typography color="text.secondary">Loading deliverables...</Typography>
            ) : (reviewItems.length || serviceItems.length) ? (
              <>
                <Stack direction="row" spacing={1} sx={{ mb: 2 }} data-testid="deliverables-filters">
                  <Chip
                    label="Due this month"
                    color={deliverableFilters.dueThisMonth ? 'primary' : 'default'}
                    variant={deliverableFilters.dueThisMonth ? 'filled' : 'outlined'}
                    onClick={() => setDeliverableFilters((prev) => ({ ...prev, dueThisMonth: !prev.dueThisMonth }))}
                    size="small"
                  />
                  <Chip
                    label="Unbatched"
                    color={deliverableFilters.unbatched ? 'primary' : 'default'}
                    variant={deliverableFilters.unbatched ? 'filled' : 'outlined'}
                    onClick={() => setDeliverableFilters((prev) => ({ ...prev, unbatched: !prev.unbatched }))}
                    size="small"
                  />
                  <Chip
                    label="Ready to invoice"
                    color={deliverableFilters.readyToInvoice ? 'primary' : 'default'}
                    variant={deliverableFilters.readyToInvoice ? 'filled' : 'outlined'}
                    onClick={() => setDeliverableFilters((prev) => ({ ...prev, readyToInvoice: !prev.readyToInvoice }))}
                    size="small"
                  />
                </Stack>
              <LinearListContainer>
                <LinearListHeaderRow
                  columns={featureFlags.anchorLinks
                    ? ['Service', 'Planned', 'Due', 'Invoice Month', 'Batch', 'Invoice #', 'Billed', 'Blockers']
                    : ['Service', 'Planned', 'Due', 'Invoice Month', 'Batch', 'Invoice #', 'Billed']}
                />
                {filteredReviewItems.map((review) => {
                  const serviceLabel = [review.service_code, review.service_name]
                    .filter(Boolean)
                    .join(' | ');
                  const metadataLabel = [review.phase, review.cycle_no ? `Cycle ${review.cycle_no}` : null]
                    .filter(Boolean)
                    .join(' | ');
                  const invoiceMonth = review.invoice_month_final
                    || review.invoice_month_override
                    || review.invoice_month_auto
                    || formatInvoiceMonth(review.due_date);
                  const plannedMonth = formatInvoiceMonth(review.planned_date);
                  const dueMonth = formatInvoiceMonth(review.due_date);
                  const isSlipped = plannedMonth && dueMonth && plannedMonth !== dueMonth;
                  const batchOptions = invoiceMonth
                    ? invoiceBatches.filter((batch) =>
                        batch.invoice_month === invoiceMonth
                        && (batch.service_id == null || batch.service_id === review.service_id),
                      )
                    : [];
                  const isBatchSaving = updateDeliverableField.isPending
                    && updateDeliverableField.variables?.review.review_id === review.review_id
                    && updateDeliverableField.variables?.fieldName === 'invoice_batch_id';

                  return (
                    <LinearListRow
                      key={review.review_id}
                      testId={`deliverable-row-${review.review_id}`}
                      columns={featureFlags.anchorLinks ? 8 : 7}
                      hoverable
                    >
                      {/* Service + metadata (primary) */}
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {serviceLabel || 'Service'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {metadataLabel}
                        </Typography>
                      </Box>

                      {/* Planned Date (read-only) */}
                      <LinearListCell variant="secondary">
                        {formatDate(review.planned_date)}
                      </LinearListCell>

                      {/* Due Date - Editable */}
                      <Box>
                        <EditableCell
                          value={review.due_date}
                          type="date"
                          testId={`cell-due-${review.review_id}`}
                          isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'due_date'}
                          onSave={async (newValue) => {
                            await updateDeliverableField.mutateAsync({
                              review,
                              fieldName: 'due_date',
                              value: newValue,
                            });
                          }}
                        />
                        {isSlipped && (
                          <Typography variant="caption" color="warning.main" sx={{ ml: 1 }}>
                            Slipped
                          </Typography>
                        )}
                      </Box>

                      {/* Invoice Month - Editable override */}
                      <EditableCell
                        value={invoiceMonth}
                        type="month"
                        testId={`cell-invoice-month-${review.review_id}`}
                        isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_month_override'}
                        onSave={async (newValue) => {
                          await updateDeliverableField.mutateAsync({
                            review,
                            fieldName: 'invoice_month_override',
                            value: newValue,
                          });
                        }}
                      />

                      {/* Invoice Batch - Select */}
                      <Box sx={{ minWidth: 160 }}>
                        <TextField
                          select
                          size="small"
                          fullWidth
                          value={review.invoice_batch_id ? String(review.invoice_batch_id) : ''}
                          disabled={!invoiceMonth || isBatchSaving || createInvoiceBatch.isPending}
                          SelectProps={{
                            displayEmpty: true,
                            renderValue: (selected) => {
                              if (!invoiceMonth) {
                                return 'Set invoice month';
                              }
                              if (!selected) {
                                return 'Unbatched';
                              }
                              const match = batchOptions.find((batch) => String(batch.invoice_batch_id) === selected);
                              return match?.title || `Batch #${selected}`;
                            },
                            inputProps: {
                              'data-testid': `cell-invoice-batch-${review.review_id}`,
                            },
                          }}
                          onChange={async (event) => {
                            const value = event.target.value;
                            if (value === '__create__' && invoiceMonth) {
                              const title = window.prompt('Batch title (optional)') || null;
                              const result = await createInvoiceBatch.mutateAsync({
                                project_id: projectId,
                                service_id: review.service_id,
                                invoice_month: invoiceMonth,
                                title,
                              });
                              if (result?.invoice_batch_id) {
                                await updateDeliverableField.mutateAsync({
                                  review,
                                  fieldName: 'invoice_batch_id',
                                  value: result.invoice_batch_id,
                                });
                              }
                              return;
                            }
                            await updateDeliverableField.mutateAsync({
                              review,
                              fieldName: 'invoice_batch_id',
                              value: value ? Number(value) : null,
                            });
                          }}
                        >
                          <MenuItem value="">Unbatched</MenuItem>
                          {batchOptions.length === 0 && invoiceMonth && (
                            <MenuItem disabled sx={{ fontStyle: 'italic', fontSize: '0.875rem' }}>
                              No batches for {invoiceMonth} - Create first batch below
                            </MenuItem>
                          )}
                          {batchOptions.map((batch) => (
                            <MenuItem key={batch.invoice_batch_id} value={String(batch.invoice_batch_id)}>
                              {batch.title || `Batch #${batch.invoice_batch_id}`}
                            </MenuItem>
                          ))}
                          <MenuItem value="__create__">Create new batch</MenuItem>
                        </TextField>
                      </Box>

                      {/* Invoice Number - Editable */}
                      <EditableCell
                        value={review.invoice_reference}
                        type="text"
                        testId={`cell-invoice-number-${review.review_id}`}
                        isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_reference'}
                        onSave={async (newValue) => {
                          await updateDeliverableField.mutateAsync({
                            review,
                            fieldName: 'invoice_reference',
                            value: newValue,
                          });
                        }}
                      />

                      {/* Billing Status - Toggleable */}
                      <ToggleCell
                        value={review.is_billed}
                        testId={`cell-billing-status-${review.review_id}`}
                        isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'is_billed'}
                        onSave={async (newValue) => {
                          await updateDeliverableField.mutateAsync({
                            review,
                            fieldName: 'is_billed',
                            value: newValue,
                          });
                        }}
                      />

                      {/* Blockers Badge (conditional) */}
                      {featureFlags.anchorLinks && (
                        <BlockerBadge
                          projectId={projectId}
                          anchorType="review"
                          anchorId={review.review_id}
                          enabled={false}
                          onClick={() => handleOpenReviewDetail(review.review_id)}
                          data-testid={`project-workspace-v2-review-blockers-${review.review_id}`}
                        />
                      )}
                    </LinearListRow>
                  );
                })}
              </LinearListContainer>

              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Items
                </Typography>
                {projectItemsError && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    Failed to load service items.
                  </Alert>
                )}
                {projectItemsLoading ? (
                  <Typography color="text.secondary">Loading items...</Typography>
                ) : filteredServiceItems.length ? (
                  <LinearListContainer>
                    <LinearListHeaderRow
                      columns={['Service', 'Planned', 'Due', 'Item', 'Type', 'Status', 'Invoice #', 'Billed']}
                    />
                    {filteredServiceItems.map((item) => {
                      const serviceLabel = [item.service_code, item.service_name]
                        .filter(Boolean)
                        .join(' | ');
                      const metadataLabel = item.phase || '';
                      return (
                        <LinearListRow
                          key={`item-${item.item_id}`}
                          testId={`deliverable-item-row-${item.item_id}`}
                          columns={8}
                          hoverable
                        >
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              {serviceLabel || `Service ${item.service_id}`}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {metadataLabel}
                            </Typography>
                          </Box>
                          <LinearListCell variant="secondary">
                            {formatDate(item.planned_date)}
                          </LinearListCell>
                          <LinearListCell variant="secondary">
                            {formatDate(item.due_date)}
                          </LinearListCell>
                          <Typography variant="body2">
                            {item.title}
                          </Typography>
                          <Typography variant="body2">
                            {item.item_type || '--'}
                          </Typography>
                          <Typography variant="body2">
                            {item.status || '--'}
                          </Typography>
                          <Typography variant="body2">
                            {item.invoice_reference || '--'}
                          </Typography>
                          <Typography variant="body2">
                            {item.is_billed ? 'Billed' : 'Not billed'}
                          </Typography>
                        </LinearListRow>
                      );
                    })}
                  </LinearListContainer>
                ) : (
                  <Typography color="text.secondary">No service items found for this project.</Typography>
                )}
              </Box>
              </>
            ) : (
              <Typography color="text.secondary">No deliverables found for this project.</Typography>
            )}
          </Box>
        )}
        {activeLabel === 'Issues' && (
          <Box data-testid="project-workspace-v2-issues">
            {Number.isFinite(projectId) ? (
              <IssuesTabContent projectId={projectId} />
            ) : (
              <Typography color="text.secondary">Select a project to view issues.</Typography>
            )}
          </Box>
        )}
        {activeLabel === 'Tasks' && (
          <Box data-testid="project-workspace-v2-tasks">
            <TasksNotesView
              initialProjectId={Number.isFinite(projectId) ? projectId : undefined}
              hideFilters
              hideHeader
              onTaskCreated={(task: any) => {
                const label = task?.task_name || 'task';
                setActivityEvents((prev) => [
                  {
                    id: prev.length + 1,
                    label: `Created task "${label}"`,
                    createdAt: new Date().toISOString(),
                  },
                  ...prev,
                ]);
                if (Number.isFinite(projectId)) {
                  queryClient.invalidateQueries({ queryKey: ['projectTasksPreview', projectId] });
                }
              }}
            />
          </Box>
        )}
        {activeLabel === 'Quality' && (
          <Box data-testid="project-workspace-v2-quality">
            {Number.isFinite(projectId) ? (
              <QualityTab projectId={projectId} />
            ) : (
              <Typography color="text.secondary">Select a project to view quality register.</Typography>
            )}
          </Box>
        )}
        {showTimeline && activeLabel === 'Timeline' && (
          <Box data-testid="project-workspace-v2-timeline">
            <TimelinePanel
              title="Project timeline"
              projectIds={Number.isFinite(projectId) ? [projectId] : undefined}
            />
          </Box>
        )}
      </Paper>

      {/* Review Detail Modal for Anchor Links */}
      <Dialog
        open={featureFlags.anchorLinks && isReviewDetailOpen && selectedReviewId !== null}
        onClose={() => {
          console.debug('[ProjectWorkspaceV2] Modal close requested');
          setIsReviewDetailOpen(false);
          setSelectedReviewId(null);
        }}
        maxWidth="md"
        fullWidth
        keepMounted
        PaperProps={{
          'data-testid': 'anchor-links-modal',
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ fontWeight: 600 }}>Linked Issues - Review #{selectedReviewId}</Box>
          <IconButton
            onClick={() => {
              setIsReviewDetailOpen(false);
              setSelectedReviewId(null);
            }}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ minHeight: '400px' }}>
          {selectedReviewId !== null && (
            <LinkedIssuesList
              projectId={projectId}
              anchorType="review"
              anchorId={selectedReviewId}
              enabled={isReviewDetailOpen && selectedReviewId !== null}
              readonly={false}
              data-testid="project-workspace-v2-review-linked-issues"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setIsReviewDetailOpen(false);
              setSelectedReviewId(null);
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invoice Month Change Notification */}
      <Snackbar
        open={invoiceMonthNotification.open}
        autoHideDuration={6000}
        onClose={() => setInvoiceMonthNotification({ message: '', open: false })}
        message={invoiceMonthNotification.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        ContentProps={{ 'data-testid': 'invoice-month-notification' }}
      />
    </Box>
  );
}
