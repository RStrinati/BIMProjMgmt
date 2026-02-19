/**
 * Overview Tab
 * 
 * Displays:
 * - Project summary
 * - Update composer (stub for now)
 * - Latest update (stub for now)
 * - Recent tasks
 */

import { useEffect, useMemo, useState } from 'react';
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
  Menu,
  MenuItem,
  IconButton,
  Divider,
  Link as MuiLink,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { projectsApi, tasksApi, updatesApi, usersApi, resourcesApi } from '@/api';
import type { Project, TaskPayload } from '@/types/api';
import type { ProjectResource } from '@/api/resources';
import type { User } from '@/types/api';
import { getProjectIcon, PROJECT_ICON_OPTIONS } from '@/components/projects/projectIcons';

const PRIORITY_LABELS = ['Low', 'Medium', 'High', 'Critical'] as const;
const PRIORITY_MAP: Record<string, number> = {
  Low: 1,
  Medium: 2,
  High: 3,
  Critical: 4,
};

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
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [isEditingSummary, setIsEditingSummary] = useState(false);
  const [summaryDraft, setSummaryDraft] = useState('');
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [descriptionDraft, setDescriptionDraft] = useState('');
  const [descriptionError, setDescriptionError] = useState<string | null>(null);
  const [emojiAnchorEl, setEmojiAnchorEl] = useState<null | HTMLElement>(null);
  const [iconSearch, setIconSearch] = useState('');
  const [resourceTitle, setResourceTitle] = useState('');
  const [resourceUrl, setResourceUrl] = useState('');
  const [resourceError, setResourceError] = useState<string | null>(null);
  const [resourceDeleteError, setResourceDeleteError] = useState<string | null>(null);
  const [resourceToDelete, setResourceToDelete] = useState<ProjectResource | null>(null);
  const [showUpdateComposer, setShowUpdateComposer] = useState(false);

  useEffect(() => {
    if (!isEditingName) {
      setNameDraft(project?.project_name || '');
    }
  }, [project?.project_name, isEditingName]);

  useEffect(() => {
    if (!isEditingSummary) {
      setSummaryDraft(project?.summary || '');
    }
  }, [project?.summary, isEditingSummary]);

  useEffect(() => {
    if (!isEditingDescription) {
      setDescriptionDraft(project?.description || '');
    }
  }, [project?.description, isEditingDescription]);

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

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const { data: resources = [] } = useQuery<ProjectResource[]>({
    queryKey: ['projectResources', projectId],
    queryFn: () => resourcesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });


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
      setShowUpdateComposer(false);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectUpdatesLatest', projectId] });
      }
    },
    onError: (err: any) => {
      setUpdateError(err?.response?.data?.error || 'Failed to post update.');
    },
  });

  const updateProject = useMutation({
    mutationFn: (payload: Partial<Project>) => projectsApi.patch(projectId, payload),
    onSuccess: () => {
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      }
    },
  });

  const addResource = useMutation({
    mutationFn: (payload: { title: string; url: string }) =>
      resourcesApi.create(projectId, payload),
    onSuccess: () => {
      setResourceTitle('');
      setResourceUrl('');
      setResourceError(null);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectResources', projectId] });
      }
    },
    onError: (err: any) => {
      setResourceError(err?.response?.data?.error || 'Failed to add resource.');
    },
  });

  const deleteResource = useMutation({
    mutationFn: (resourceId: number) => resourcesApi.remove(resourceId),
    onSuccess: () => {
      setResourceDeleteError(null);
      setResourceToDelete(null);
      if (Number.isFinite(projectId)) {
        queryClient.invalidateQueries({ queryKey: ['projectResources', projectId] });
      }
    },
    onError: (err: any) => {
      setResourceDeleteError(err?.response?.data?.error || 'Failed to delete resource.');
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

  const handleSummarySave = () => {
    if (!Number.isFinite(projectId) || updateProject.isPending) return;
    updateProject.mutate(
      { summary: summaryDraft.trim() },
      {
        onSuccess: () => {
          setIsEditingSummary(false);
          setSummaryError(null);
        },
        onError: (err: any) => {
          setSummaryError(err?.response?.data?.error || 'Failed to update summary.');
        },
      },
    );
  };

  const handleSummaryCancel = () => {
    setSummaryDraft(project?.summary || '');
    setSummaryError(null);
    setIsEditingSummary(false);
  };

  const handleNameSave = () => {
    if (!Number.isFinite(projectId) || updateProject.isPending) return;
    const trimmed = nameDraft.trim();
    if (!trimmed) {
      setNameError('Project name is required.');
      return;
    }
    updateProject.mutate(
      { project_name: trimmed },
      {
        onSuccess: () => {
          setIsEditingName(false);
          setNameError(null);
        },
        onError: (err: any) => {
          setNameError(err?.response?.data?.error || 'Failed to update project name.');
        },
      },
    );
  };

  const handleNameCancel = () => {
    setNameDraft(project?.project_name || '');
    setNameError(null);
    setIsEditingName(false);
  };

  const handleDescriptionSave = () => {
    if (!Number.isFinite(projectId) || updateProject.isPending) return;
    updateProject.mutate(
      { description: descriptionDraft.trim() },
      {
        onSuccess: () => {
          setIsEditingDescription(false);
          setDescriptionError(null);
        },
        onError: (err: any) => {
          setDescriptionError(err?.response?.data?.error || 'Failed to update description.');
        },
      },
    );
  };

  const handleDescriptionCancel = () => {
    setDescriptionDraft(project?.description || '');
    setDescriptionError(null);
    setIsEditingDescription(false);
  };

  const handleIconPick = (icon_key: string) => {
    setEmojiAnchorEl(null);
    if (!Number.isFinite(projectId) || updateProject.isPending) return;
    updateProject.mutate({ icon_key });
  };

  const handlePropertyChange = (field: keyof Project, value: string | number | null) => {
    if (!Number.isFinite(projectId) || updateProject.isPending) return;

    if (['status', 'priority', 'start_date', 'end_date'].includes(field)) {
      const currentPriority = project?.priority_label ?? project?.priority ?? 'Medium';
      const priorityValue =
        typeof currentPriority === 'number'
          ? currentPriority
          : PRIORITY_MAP[String(currentPriority)] || PRIORITY_MAP.Medium;

      const payload = {
        status: project?.status ?? null,
        priority: priorityValue,
        start_date: project?.start_date ? project.start_date : null,
        end_date: project?.end_date ? project.end_date : null,
      };

      if (field === 'priority') {
        payload.priority = typeof value === 'number' ? value : PRIORITY_MAP[String(value)] || PRIORITY_MAP.Medium;
      } else {
        payload[field] = value as any;
      }

      updateProject.mutate(payload as Partial<Project>);
      return;
    }

    updateProject.mutate({ [field]: value } as Partial<Project>);
  };

  const handleAddResource = () => {
    const title = resourceTitle.trim();
    const url = resourceUrl.trim();
    if (!title || !url) {
      setResourceError('Title and URL are required.');
      return;
    }
    addResource.mutate({ title, url });
  };

  const handleDeleteResourceConfirm = () => {
    if (!resourceToDelete || deleteResource.isPending) return;
    deleteResource.mutate(resourceToDelete.resource_id);
  };

  const statusOptions = useMemo(() => {
    const defaults = ['Planned', 'In Progress', 'On Hold', 'Complete'];
    const current = project?.status ? [project.status] : [];
    return Array.from(new Set([...current, ...defaults]));
  }, [project?.status]);

  const filteredIconOptions = useMemo(() => {
    const term = iconSearch.trim().toLowerCase();
    if (!term) return PROJECT_ICON_OPTIONS;
    return PROJECT_ICON_OPTIONS.filter((icon) => icon.label.toLowerCase().includes(term));
  }, [iconSearch]);

  return (
    <Box data-testid="workspace-overview-tab">
      <Stack spacing={2}>
        {/* Title + Summary */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={1.5}>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              alignItems={{ xs: 'flex-start', sm: 'center' }}
              justifyContent="space-between"
              spacing={1}
            >
              <Stack direction="row" spacing={1} alignItems="center">
                <IconButton
                  size="small"
                  onClick={(event) => setEmojiAnchorEl(event.currentTarget)}
                  aria-label="Select project icon"
                  sx={{
                    width: 36,
                    height: 36,
                    borderRadius: 1,
                    border: 1,
                    borderColor: 'divider',
                  }}
                >
                  {(() => {
                    const Icon = getProjectIcon(project?.icon_key);
                    return <Icon size={18} />;
                  })()}
                </IconButton>
                <Menu
                  anchorEl={emojiAnchorEl}
                  open={Boolean(emojiAnchorEl)}
                  onClose={() => setEmojiAnchorEl(null)}
                  PaperProps={{ sx: { p: 1.5, width: 320 } }}
                >
                  <Stack spacing={1}>
                    <TextField
                      size="small"
                      placeholder="Search icons..."
                      value={iconSearch}
                      onChange={(e) => setIconSearch(e.target.value)}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">🔍</InputAdornment>,
                      }}
                    />
                    <Divider />
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: 1,
                      }}
                    >
                      {filteredIconOptions.map((icon) => (
                        <IconButton
                          key={icon.key}
                          size="small"
                          onClick={() => handleIconPick(icon.key)}
                          sx={{
                            width: 48,
                            height: 48,
                            borderRadius: 1,
                            border: 1,
                            borderColor: 'divider',
                          }}
                        >
                          <icon.Icon size={20} />
                        </IconButton>
                      ))}
                    </Box>
                    <Divider />
                    <Button variant="text" size="small" onClick={() => handleIconPick('')}>
                      Clear icon
                    </Button>
                  </Stack>
                </Menu>
                <Typography variant="h5">{project?.project_name || 'Untitled project'}</Typography>
              </Stack>
              <Stack direction="row" spacing={1}>
                {!isEditingName && (
                  <Button variant="text" size="small" onClick={() => setIsEditingName(true)}>
                    Edit name
                  </Button>
                )}
                {!isEditingSummary && (
                  <Button variant="text" size="small" onClick={() => setIsEditingSummary(true)}>
                    Edit summary
                  </Button>
                )}
              </Stack>
            </Stack>
            {nameError && <Alert severity="error">{nameError}</Alert>}
            {isEditingName && (
              <Stack spacing={1}>
                <TextField
                  size="small"
                  placeholder="Project name"
                  value={nameDraft}
                  onChange={(e) => setNameDraft(e.target.value)}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="contained" onClick={handleNameSave} disabled={updateProject.isPending}>
                    {updateProject.isPending ? 'Saving...' : 'Save name'}
                  </Button>
                  <Button variant="outlined" onClick={handleNameCancel} disabled={updateProject.isPending}>
                    Cancel
                  </Button>
                </Box>
              </Stack>
            )}
            {summaryError && <Alert severity="error">{summaryError}</Alert>}
            {isEditingSummary ? (
              <Stack spacing={1}>
                <TextField
                  multiline
                  minRows={2}
                  size="small"
                  placeholder="Add a short summary..."
                  value={summaryDraft}
                  onChange={(e) => setSummaryDraft(e.target.value)}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="contained" onClick={handleSummarySave} disabled={updateProject.isPending}>
                    {updateProject.isPending ? 'Saving...' : 'Save summary'}
                  </Button>
                  <Button variant="outlined" onClick={handleSummaryCancel} disabled={updateProject.isPending}>
                    Cancel
                  </Button>
                </Box>
              </Stack>
            ) : (
              <Typography color="text.secondary">
                {project?.summary || 'Add a short summary of the project and services.'}
              </Typography>
            )}
          </Stack>
        </Paper>

        {/* Properties */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Properties
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Box sx={{ minWidth: 160 }}>
              <Typography variant="caption" color="text.secondary">
                Status
              </Typography>
              <TextField
                select
                size="small"
                fullWidth
                value={project?.status || ''}
                onChange={(e) => handlePropertyChange('status', e.target.value)}
              >
                {statusOptions.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            <Box sx={{ minWidth: 160 }}>
              <Typography variant="caption" color="text.secondary">
                Priority
              </Typography>
              <TextField
                select
                size="small"
                fullWidth
                value={project?.priority_label || project?.priority || 'Medium'}
                onChange={(e) => handlePropertyChange('priority', PRIORITY_MAP[e.target.value] || PRIORITY_MAP.Medium)}
              >
                {PRIORITY_LABELS.map((priority) => (
                  <MenuItem key={priority} value={priority}>
                    {priority}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            <Box sx={{ minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Project lead
              </Typography>
              <TextField
                select
                size="small"
                fullWidth
                value={project?.internal_lead ?? ''}
                onChange={(e) =>
                  handlePropertyChange('internal_lead', e.target.value ? Number(e.target.value) : null)
                }
              >
                <MenuItem value="">Unassigned</MenuItem>
                {users.map((user) => (
                  <MenuItem key={user.user_id} value={user.user_id}>
                    {user.name || user.full_name || user.username || `User ${user.user_id}`}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            <Box sx={{ minWidth: 160 }}>
              <Typography variant="caption" color="text.secondary">
                Start date
              </Typography>
              <TextField
                type="date"
                size="small"
                fullWidth
                value={project?.start_date || ''}
                onChange={(e) => handlePropertyChange('start_date', e.target.value)}
              />
            </Box>
            <Box sx={{ minWidth: 160 }}>
              <Typography variant="caption" color="text.secondary">
                End date
              </Typography>
              <TextField
                type="date"
                size="small"
                fullWidth
                value={project?.end_date || ''}
                onChange={(e) => handlePropertyChange('end_date', e.target.value)}
              />
            </Box>
          </Stack>
        </Paper>

        {/* Resources */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Resources
          </Typography>
          {resourceError && <Alert severity="error" sx={{ mb: 1 }}>{resourceError}</Alert>}
          {resourceDeleteError && <Alert severity="error" sx={{ mb: 1 }}>{resourceDeleteError}</Alert>}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 1 }}>
            <TextField
              size="small"
              label="Title"
              value={resourceTitle}
              onChange={(e) => setResourceTitle(e.target.value)}
              sx={{ flex: 1 }}
            />
            <TextField
              size="small"
              label="URL"
              value={resourceUrl}
              onChange={(e) => setResourceUrl(e.target.value)}
              sx={{ flex: 2 }}
            />
            <Button variant="contained" onClick={handleAddResource} disabled={addResource.isPending}>
              {addResource.isPending ? 'Adding...' : 'Add'}
            </Button>
          </Stack>
          {resources.length ? (
            <Stack spacing={0.5}>
              {resources.map((resource) => (
                <Stack
                  key={resource.resource_id}
                  direction="row"
                  alignItems="center"
                  spacing={1}
                  sx={{ justifyContent: 'space-between' }}
                >
                  <MuiLink
                    href={resource.url}
                    target="_blank"
                    rel="noreferrer"
                    underline="hover"
                    sx={{ flex: 1, minWidth: 0 }}
                  >
                    {resource.title}
                  </MuiLink>
                  <Tooltip title="Delete resource link">
                    <span>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => setResourceToDelete(resource)}
                        data-testid={`resource-delete-${resource.resource_id}`}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                </Stack>
              ))}
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Add document links or project resources here.
            </Typography>
          )}
        </Paper>

        <Dialog
          open={Boolean(resourceToDelete)}
          onClose={() => setResourceToDelete(null)}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>Delete resource?</DialogTitle>
          <DialogContent>
            <Typography variant="body2">
              {resourceToDelete?.title
                ? `Remove "${resourceToDelete.title}" from this project?`
                : 'Remove this resource link from the project?'}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setResourceToDelete(null)} disabled={deleteResource.isPending}>
              Cancel
            </Button>
            <Button
              color="error"
              variant="contained"
              onClick={handleDeleteResourceConfirm}
              disabled={deleteResource.isPending}
              data-testid="resource-delete-confirm"
            >
              {deleteResource.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Latest Update */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Latest update
            </Typography>
            <Button size="small" variant="text" onClick={() => setShowUpdateComposer((prev) => !prev)}>
              {showUpdateComposer ? 'Close' : 'New update'}
            </Button>
          </Stack>
          {showUpdateComposer && (
            <Stack spacing={1} sx={{ mb: 1 }}>
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
              <Divider />
            </Stack>
          )}
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

        {/* Description */}
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Description
            </Typography>
            {!isEditingDescription && (
              <Button size="small" variant="text" onClick={() => setIsEditingDescription(true)}>
                Edit description
              </Button>
            )}
          </Stack>
          {descriptionError && <Alert severity="error" sx={{ mb: 1 }}>{descriptionError}</Alert>}
          {isEditingDescription ? (
            <Stack spacing={1}>
              <TextField
                multiline
                minRows={4}
                size="small"
                placeholder="Add description..."
                value={descriptionDraft}
                onChange={(e) => setDescriptionDraft(e.target.value)}
              />
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button variant="contained" onClick={handleDescriptionSave} disabled={updateProject.isPending}>
                  {updateProject.isPending ? 'Saving...' : 'Save description'}
                </Button>
                <Button variant="outlined" onClick={handleDescriptionCancel} disabled={updateProject.isPending}>
                  Cancel
                </Button>
              </Box>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {project?.description || 'Add description...'}
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
