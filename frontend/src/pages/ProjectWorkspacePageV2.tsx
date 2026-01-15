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
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { projectsApi, tasksApi, usersApi } from '@/api';
import { serviceReviewsApi } from '@/api/services';
import type { Project, ProjectReviewItem, ProjectReviewsResponse, ServiceReview, TaskPayload, User } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';
import { TasksNotesView } from '@/components/ProjectManagement/TasksNotesView';
import { featureFlags } from '@/config/featureFlags';
import { TimelinePanel } from '@/components/timeline_v2/TimelinePanel';
import { ReviewStatusInline } from '@/components/projects/ReviewStatusInline';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import { toApiReviewStatus } from '@/utils/reviewStatus';
import { ProjectServicesList } from '@/features/projects/services/ProjectServicesList';
import { BlockerBadge } from '@/components/ui/BlockerBadge';
import { LinkedIssuesList } from '@/components/ui/LinkedIssuesList';
import { Dialog, DialogTitle, DialogContent, DialogActions, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const BASE_TABS = ['Overview', 'Services', 'Reviews', 'Tasks'] as const;
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
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([{
    id: 1,
    label: 'Workspace opened',
    createdAt: new Date().toISOString(),
  }]);

  // Handler for opening review detail modal
  const handleOpenReviewDetail = useCallback((reviewId: number) => {
    console.debug('[ProjectWorkspaceV2] Opening review detail modal', { reviewId });
    setSelectedReviewId(reviewId);
    setIsReviewDetailOpen(true);
    console.debug('[ProjectWorkspaceV2] State should be updated', { reviewId, isReviewDetailOpen: true });
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

  const updateReviewStatus = useMutation<
    Awaited<ReturnType<typeof serviceReviewsApi.update>>,
    Error,
    { review: ProjectReviewItem; status: string | null },
    { previousProjectReviews: Array<[unknown, ProjectReviewsResponse | undefined]>; previousServiceReviews?: ServiceReview[] }
  >({
    mutationFn: ({ review, status }) =>
      serviceReviewsApi.update(projectId, review.service_id, review.review_id, {
        status: toApiReviewStatus(status),
      }),
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
            item.review_id === review.review_id ? { ...item, status: nextStatus } : item,
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
                </Stack>
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
              <ProjectServicesList
                projectId={projectId}
                testIdPrefix="project-workspace-v2"
              />
            ) : (
              <Typography color="text.secondary">Select a project to view services.</Typography>
            )}
          </Box>
        )}
        {activeLabel === 'Reviews' && (
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
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: '2fr 0.7fr 0.9fr 0.9fr 0.8fr 0.6fr' },
                  gap: 2,
                  mb: 1,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  Service
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Cycle
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Planned
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Due
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Status
                </Typography>
                {featureFlags.anchorLinks && (
                  <Typography variant="caption" color="text.secondary">
                    Blockers
                  </Typography>
                )}
              </Box>
              {projectReviewsLoading ? (
                <Typography color="text.secondary">Loading reviews...</Typography>
              ) : reviewItems.length ? (
                <Stack spacing={1}>
                  {reviewItems.map((review) => {
                    const isSaving =
                      updateReviewStatus.isPending &&
                      updateReviewStatus.variables?.review.review_id === review.review_id;
                    const serviceLabel = [review.service_code, review.service_name]
                      .filter(Boolean)
                      .join(' | ');
                    return (
                      <Box
                        key={review.review_id}
                        data-testid={`project-workspace-v2-review-row-${review.review_id}`}
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '2fr 0.7fr 0.9fr 0.9fr 0.8fr 0.6fr' },
                          gap: 2,
                          alignItems: 'center',
                          p: 1,
                          borderRadius: 1,
                          border: (theme) => `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {serviceLabel || 'Service'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {[review.phase, review.disciplines, review.deliverables]
                              .filter(Boolean)
                              .join(' | ') || 'No metadata'}
                          </Typography>
                        </Box>
                        <Typography variant="body2">#{review.cycle_no}</Typography>
                        <Typography variant="body2">{formatDate(review.planned_date)}</Typography>
                        <Typography variant="body2">{formatDate(review.due_date)}</Typography>
                        <ReviewStatusInline
                          value={review.status ?? null}
                          onChange={(nextStatus) =>
                            updateReviewStatus.mutate({ review, status: nextStatus })
                          }
                          isSaving={isSaving}
                          disabled={updateReviewStatus.isPending}
                        />
                        {featureFlags.anchorLinks && (
                          <BlockerBadge
                            projectId={projectId}
                            anchorType="review"
                            anchorId={review.review_id}
                            enabled={true}
                            onClick={() => handleOpenReviewDetail(review.review_id)}
                            data-testid={`project-workspace-v2-review-blockers-${review.review_id}`}
                          />
                        )}
                      </Box>
                    );
                  })}
                </Stack>
              ) : (
                <Typography color="text.secondary">No reviews found for this project.</Typography>
              )}
            </Paper>
          </Box>
        )}
        {activeLabel === 'Tasks' && (
          <Box data-testid="project-workspace-v2-tasks">
            <TasksNotesView
              initialProjectId={Number.isFinite(projectId) ? projectId : undefined}
              hideFilters
              hideHeader
              onTaskCreated={(task) => {
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
    </Box>
  );
}
