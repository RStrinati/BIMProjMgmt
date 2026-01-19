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
import type { Project, ProjectFinanceGrid, TaskPayload } from '@/types/api';

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

  const { data: financeGrid } = useQuery<ProjectFinanceGrid>({
    queryKey: ['projectFinanceGrid', projectId],
    queryFn: () => projectsApi.getFinanceGrid(projectId),
    enabled: Number.isFinite(projectId),
  });

  const formatCurrency = (value?: number | null) => {
    if (value == null || Number.isNaN(Number(value))) {
      return '--';
    }
    return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
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
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectUpdatesLatest', projectId] });
      }
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
    if (!updateDraft.trim()) return;
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
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Invoice pipeline
          </Typography>
          {financeGrid ? (
            <Stack spacing={1} data-testid="workspace-invoice-pipeline">
              <Typography variant="body2">
                Ready this month: {financeGrid.ready_this_month.ready_count} · {formatCurrency(financeGrid.ready_this_month.ready_amount)}
              </Typography>
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

        {/* Update Composer */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
            Post an update
          </Typography>
          <Stack spacing={1}>
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
                disabled={!updateDraft.trim()}
                data-testid="workspace-post-update-button"
              >
                Post update
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
