/**
 * Overview Tab
 * 
 * Displays:
 * - Project summary
 * - Update composer (stub for now)
 * - Latest update (stub for now)
 * - Recent tasks
 */

import { useMemo, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
  Chip,
} from '@mui/material';
import { projectsApi, tasksApi, updatesApi } from '@/api';
import type {
  Project,
  FinanceLineItemsResponse,
  FinanceReconciliationResponse,
  FinanceLineItem,
  TaskPayload,
} from '@/types/api';

const READY_STATUSES = new Set(['ready', 'draft', 'unbilled']);

type OutletContext = {
  projectId: number;
  project: Project | null;
};

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatDateTime = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
};

export default function OverviewTab() {
  const navigate = useNavigate();
  const { projectId, project } = useOutletContext<OutletContext>();
  const queryClient = useQueryClient();
  const [taskDraft, setTaskDraft] = useState('');
  const [taskError, setTaskError] = useState<string | null>(null);
  const [updateDraft, setUpdateDraft] = useState('');
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [includeItems, setIncludeItems] = useState(true);

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

  // Fetch latest update
  const { data: latestUpdateResult } = useQuery({
    queryKey: ['projectUpdatesLatest', projectId],
    queryFn: () => updatesApi.getProjectUpdates(projectId, { limit: 1 }),
    enabled: Number.isFinite(projectId),
  });

  const { data: lineItemsResult, isLoading: isLineItemsLoading, error: lineItemsError } = useQuery<FinanceLineItemsResponse>({
    queryKey: ['projectFinanceLineItems', projectId],
    queryFn: () => projectsApi.getFinanceLineItems(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: reconciliation, isLoading: isReconciliationLoading, error: reconciliationError } = useQuery<FinanceReconciliationResponse>({
    queryKey: ['projectFinanceReconciliation', projectId],
    queryFn: () => projectsApi.getFinanceReconciliation(projectId),
    enabled: Number.isFinite(projectId),
  });

  const formatCurrency = (value?: number | null) => {
    if (value == null || Number.isNaN(Number(value))) {
      return '--';
    }
    return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
  };

  const formatMonthLabel = (value: string) => {
    if (!value) return 'Unscheduled';
    const parsed = new Date(`${value}-01`);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
  };

  const filteredLineItems = useMemo<FinanceLineItem[]>(() => {
    const items = lineItemsResult?.line_items ?? [];
    if (includeItems) return items;
    return items.filter((item) => item.type === 'review');
  }, [lineItemsResult, includeItems]);

  const pipelineBuckets = useMemo(() => {
    const buckets = new Map<string, {
      month: string;
      deliverables_count: number;
      total_amount: number;
      ready_count: number;
      ready_amount: number;
    }>();

    filteredLineItems.forEach((item) => {
      const month = item.invoice_month || 'Unscheduled';
      const existing = buckets.get(month) || {
        month,
        deliverables_count: 0,
        total_amount: 0,
        ready_count: 0,
        ready_amount: 0,
      };

      const fee = Number(item.fee ?? 0);
      existing.deliverables_count += 1;
      existing.total_amount += fee;

      const normalizedStatus = (item.invoice_status || '').toLowerCase();
      if (READY_STATUSES.has(normalizedStatus)) {
        existing.ready_count += 1;
        existing.ready_amount += fee;
      }

      buckets.set(month, existing);
    });

    return Array.from(buckets.values()).sort((a, b) => a.month.localeCompare(b.month));
  }, [filteredLineItems]);

  const currentMonthKey = useMemo(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }, []);

  const readyThisMonth = useMemo(() => {
    return (
      pipelineBuckets.find((bucket) => bucket.month === currentMonthKey) || {
        month: currentMonthKey,
        deliverables_count: 0,
        total_amount: 0,
        ready_count: 0,
        ready_amount: 0,
      }
    );
  }, [pipelineBuckets, currentMonthKey]);

  const reconciliationRows = useMemo(() => {
    if (!reconciliation) return [];
    const { by_service, project: projectTotals } = reconciliation;
    return [
      ...by_service,
      {
        ...projectTotals,
        service_id: -1,
        service_code: '',
        service_name: 'PROJECT TOTAL',
      },
    ];
  }, [reconciliation]);

  const varianceColor = (variance: number) => {
    if (variance > 1000 || variance < -1000) return 'error.main';
    if (variance > 100 || variance < -100) return 'warning.main';
    return 'success.main';
  };

  const latestUpdate = useMemo(
    () => (latestUpdateResult?.updates && latestUpdateResult.updates.length > 0 
      ? latestUpdateResult.updates[0] 
      : null),
    [latestUpdateResult],
  );

  const recentTasks = useMemo(
    () => (Array.isArray(recentTasksResult?.tasks) ? recentTasksResult.tasks : []),
    [recentTasksResult],
  );

  const createTask = useMutation({
    mutationFn: (payload: TaskPayload) => tasksApi.create(payload),
    onSuccess: () => {
      setTaskDraft('');
      setTaskError(null);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectTasksPreview', projectId] });
      }
    },
    onError: (err: any) => {
      setTaskError(err?.response?.data?.error || 'Failed to create task.');
    },
  });

  const createUpdate = useMutation({
    mutationFn: (body: string) => updatesApi.createProjectUpdate(projectId, body),
    onSuccess: () => {
      setUpdateDraft('');
      setUpdateError(null);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectUpdatesLatest', projectId] });
      }
    },
    onError: (err: any) => {
      setUpdateError(err?.response?.data?.error || 'Failed to post update.');
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

  const handlePostUpdate = () => {
    if (!updateDraft.trim() || createUpdate.isPending) return;
    createUpdate.mutate(updateDraft.trim());
  };

  return (
    <Box data-testid="workspace-overview-tab">
      <Stack spacing={2}>
        {/* Summary */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Summary
          </Typography>
          <Typography color="text.secondary">
            {project?.description || 'Add a description to summarize scope and outcomes.'}
          </Typography>
        </Paper>

        {/* Invoice Pipeline */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Invoice pipeline
            </Typography>
            <Chip
              label={includeItems ? 'Including items' : 'Reviews only'}
              color={includeItems ? 'primary' : 'default'}
              variant={includeItems ? 'filled' : 'outlined'}
              size="small"
              onClick={() => setIncludeItems((prev) => !prev)}
            />
          </Stack>
          {lineItemsError ? (
            <Alert severity="error">Failed to load invoice pipeline.</Alert>
          ) : isLineItemsLoading ? (
            <Typography color="text.secondary">Loading invoice pipeline...</Typography>
          ) : pipelineBuckets.length ? (
            <Stack spacing={1} data-testid="workspace-invoice-pipeline">
              <Typography variant="body2">
                Ready this month: {readyThisMonth.ready_count} · {formatCurrency(readyThisMonth.ready_amount)}
              </Typography>
              <Stack spacing={0.5}>
                {pipelineBuckets.map((item) => (
                  <Box key={item.month} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatMonthLabel(item.month)}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="caption">
                        {item.deliverables_count} · {formatCurrency(item.total_amount)}
                      </Typography>
                      {item.ready_count > 0 && (
                        <Chip
                          label={`Ready ${item.ready_count} · ${formatCurrency(item.ready_amount)}`}
                          size="small"
                          color="success"
                          variant="outlined"
                          sx={{ height: 22, fontSize: '0.7rem' }}
                        />
                      )}
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </Stack>
          ) : (
            <Typography color="text.secondary">No line items yet.</Typography>
          )}
        </Paper>

        {/* Reconciliation */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Service fee reconciliation
          </Typography>
          {reconciliationError ? (
            <Alert severity="error">Failed to load reconciliation.</Alert>
          ) : isReconciliationLoading ? (
            <Typography color="text.secondary">Loading reconciliation...</Typography>
          ) : reconciliationRows.length ? (
            <Stack spacing={0.5} data-testid="workspace-reconciliation">
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '2fr repeat(5, 1fr)',
                  typography: 'caption',
                  fontWeight: 600,
                  color: 'text.secondary',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                <Box>Service</Box>
                <Box>Agreed</Box>
                <Box>Line items</Box>
                <Box>Billed</Box>
                <Box>Outstanding</Box>
                <Box>Variance</Box>
              </Box>
              {reconciliationRows.map((row) => {
                const isTotal = row.service_id === -1;
                return (
                  <Box
                    key={`${row.service_id}-${row.service_name}`}
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: '2fr repeat(5, 1fr)',
                      gap: 1,
                      alignItems: 'center',
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      backgroundColor: isTotal ? 'action.hover' : 'transparent',
                    }}
                  >
                    <Typography variant="body2" fontWeight={isTotal ? 700 : 600} noWrap>
                      {row.service_name || row.service_code || 'Service'}
                    </Typography>
                    <Typography variant="body2">{formatCurrency(row.agreed_fee)}</Typography>
                    <Typography variant="body2">{formatCurrency(row.line_items_total_fee)}</Typography>
                    <Typography variant="body2">{formatCurrency(row.billed_total_fee)}</Typography>
                    <Typography variant="body2">{formatCurrency(row.outstanding_total_fee)}</Typography>
                    <Typography variant="body2" sx={{ color: varianceColor(row.variance) }}>
                      {formatCurrency(row.variance)}
                    </Typography>
                  </Box>
                );
              })}
            </Stack>
          ) : (
            <Typography color="text.secondary">No reconciliation data yet.</Typography>
          )}
        </Paper>

        {/* Update Composer */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Post an update
          </Typography>
          <Stack spacing={1}>
            {updateError && <Alert severity="error">{updateError}</Alert>}
            <TextField
              multiline
              rows={3}
              size="small"
              placeholder="What's the latest progress on this project?"
              value={updateDraft}
              onChange={(e) => setUpdateDraft(e.target.value)}
              data-testid="workspace-update-composer"
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Button 
                variant="contained" 
                onClick={handlePostUpdate}
                disabled={!updateDraft.trim() || createUpdate.isPending}
                data-testid="workspace-post-update-button"
              >
                {createUpdate.isPending ? 'Posting...' : 'Post update'}
              </Button>
              <Button 
                variant="text" 
                size="small"
                onClick={() => navigate(`/projects/${projectId}/workspace/updates`)}
              >
                View all updates →
              </Button>
            </Box>
          </Stack>
        </Paper>

        {/* Latest Update (stub) */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Latest update
          </Typography>
          {latestUpdate ? (
            <Box data-testid="latest-update-card">
              <Stack spacing={0.5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {latestUpdate.created_by_name || latestUpdate.created_by_full_name || 'Unknown'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    · {formatDateTime(latestUpdate.created_at)}
                  </Typography>
                  {latestUpdate.comment_count !== undefined && latestUpdate.comment_count > 0 && (
                    <Chip 
                      label={`${latestUpdate.comment_count} comment${latestUpdate.comment_count > 1 ? 's' : ''}`} 
                      size="small" 
                      variant="outlined"
                    />
                  )}
                </Box>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {latestUpdate.body}
                </Typography>
              </Stack>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No updates yet. Post the first one above!
            </Typography>
          )}
        </Paper>

        {/* Add Task */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Add task
          </Typography>
          <Stack spacing={1}>
            {taskError && <Alert severity="error">{taskError}</Alert>}
            <TextField
              size="small"
              placeholder="New task"
              value={taskDraft}
              onChange={(e) => setTaskDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAddTask();
                }
              }}
            />
            <Button 
              variant="contained" 
              onClick={handleAddTask} 
              disabled={createTask.isPending}
            >
              {createTask.isPending ? 'Saving...' : 'Add task'}
            </Button>
          </Stack>
        </Paper>

        {/* Recent Tasks */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Recent tasks
          </Typography>
          {isRecentTasksLoading ? (
            <Typography color="text.secondary">Loading tasks...</Typography>
          ) : recentTasks.length ? (
            <Stack spacing={1} data-testid="workspace-recent-tasks">
              {recentTasks.map((task) => (
                <Box key={task.task_id} sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      {task.task_name || 'Untitled task'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {task.assigned_to_name || 'Unassigned'}
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
    </Box>
  );
}
