import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Paper,
} from '@mui/material';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import FilterListIcon from '@mui/icons-material/FilterList';
import { format } from 'date-fns';
import { tasksApi } from '@/api/tasks';
import { projectsApi } from '@/api/projects';
import { usersApi } from '@/api/users';

const defaultFilters = {
  dateFrom: null,
  dateTo: null,
  projectId: '',
  userId: '',
};

const defaultFormState = {
  task_name: '',
  project_id: '',
  task_date: null,
  time_start: '',
  time_end: '',
  assigned_to: '',
  notes: '',
  task_items: [],
};

const asDisplayDate = (value) => {
  if (!value) {
    return '—';
  }
  try {
    return format(new Date(value), 'EEE, MMM d');
  } catch (error) {
    return value;
  }
};

const trimTime = (timeValue) => {
  if (!timeValue) {
    return null;
  }
  const [hours, minutes] = timeValue.split(':');
  if (minutes === '00') {
    return hours;
  }
  return `${hours}:${minutes}`;
};

const buildTimeRange = (start, end) => {
  const cleanStart = trimTime(start);
  const cleanEnd = trimTime(end);
  if (cleanStart && cleanEnd) {
    return `${cleanStart} - ${cleanEnd}`;
  }
  if (cleanStart) {
    return cleanStart;
  }
  if (cleanEnd) {
    return cleanEnd;
  }
  return '—';
};

const normaliseItems = (items = []) =>
  items
    .filter((item) => item && (item.label || item.title))
    .map((item) => ({
      label: item.label ?? item.title ?? '',
      completed: Boolean(item.completed),
      notes: item.notes ?? '',
    }));

export function TasksNotesView() {
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState(defaultFilters);
  const [showFilters, setShowFilters] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeTask, setActiveTask] = useState(null);
  const [formState, setFormState] = useState(defaultFormState);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [pendingToggleKey, setPendingToggleKey] = useState(null);

  const loadLookups = useCallback(async () => {
    try {
      const [projectData, userData] = await Promise.all([
        projectsApi.getAll().catch(() => []),
        usersApi.getAll().catch(() => []),
      ]);
      setProjects(projectData ?? []);
      setUsers(userData ?? []);
    } catch (error) {
      console.error('Failed to load lookup data', error);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    try {
      setLoadingTasks(true);
      setLoadError('');
      const data = await tasksApi.getNotesView();
      setTasks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load tasks', error);
      setLoadError('Unable to load tasks. Please try again.');
      setTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  }, []);

  useEffect(() => {
    loadLookups();
    loadTasks();
  }, [loadLookups, loadTasks]);

  const filteredTasks = useMemo(() => {
    if (!tasks.length) {
      return [];
    }

    const projectId = filters.projectId ? Number(filters.projectId) : null;
    const userId = filters.userId ? Number(filters.userId) : null;
    const fromMs = filters.dateFrom ? new Date(filters.dateFrom).setHours(0, 0, 0, 0) : null;
    const toMs = filters.dateTo ? new Date(filters.dateTo).setHours(23, 59, 59, 999) : null;

    return tasks.filter((task) => {
      if (projectId && task.project_id !== projectId) {
        return false;
      }
      if (userId && task.assigned_to !== userId) {
        return false;
      }
      if (fromMs || toMs) {
        if (!task.task_date) {
          return false;
        }
        const taskMs = new Date(task.task_date).setHours(12, 0, 0, 0);
        if (fromMs && taskMs < fromMs) {
          return false;
        }
        if (toMs && taskMs > toMs) {
          return false;
        }
      }
      return true;
    });
  }, [filters, tasks]);

  const resetForm = () => {
    setFormState(defaultFormState);
    setActiveTask(null);
  };

  const handleOpenCreate = () => {
    resetForm();
    setDialogOpen(true);
  };

  const handleOpenEdit = (task) => {
    setActiveTask(task);
    setFormState({
      task_name: task.task_name ?? '',
      project_id: task.project_id ? String(task.project_id) : '',
      task_date: task.task_date ? new Date(task.task_date) : null,
      time_start: task.time_start ?? '',
      time_end: task.time_end ?? '',
      assigned_to: task.assigned_to ? String(task.assigned_to) : '',
      notes: task.notes ?? '',
      task_items: normaliseItems(task.task_items),
    });
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    if (formSubmitting) {
      return;
    }
    setDialogOpen(false);
    resetForm();
  };

  const handleFormFieldChange = (field, value) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleItemChange = (index, key, value) => {
    setFormState((prev) => {
      const nextItems = [...(prev.task_items ?? [])];
      nextItems[index] = {
        ...nextItems[index],
        [key]: value,
      };
      return { ...prev, task_items: nextItems };
    });
  };

  const handleAddItem = () => {
    setFormState((prev) => ({
      ...prev,
      task_items: [...(prev.task_items ?? []), { label: '', completed: false, notes: '' }],
    }));
  };

  const handleRemoveItem = (index) => {
    setFormState((prev) => {
      const nextItems = [...(prev.task_items ?? [])];
      nextItems.splice(index, 1);
      return { ...prev, task_items: nextItems };
    });
  };

  const resolveProjectName = (task) => {
    if (task.project_name) {
      return task.project_name;
    }
    const project = projects.find((p) => p.project_id === task.project_id);
    return project?.project_name ?? `Project ${task.project_id}`;
  };

  const resolveUserName = (task) => {
    if (task.assigned_to_name) {
      return task.assigned_to_name;
    }
    const user = users.find((u) => u.user_id === task.assigned_to);
    return user?.full_name ?? user?.name ?? 'Unassigned';
  };

  const calculateProgress = (task) => {
    const items = Array.isArray(task.task_items) ? task.task_items : [];
    if (!items.length) {
      return { completed: 0, total: 0 };
    }
    const completed = items.filter((item) => item?.completed).length;
    return { completed, total: items.length };
  };

  const handleSubmitForm = async () => {
    if (!formState.task_name?.trim()) {
      return;
    }
    if (!formState.project_id) {
      return;
    }

    setFormSubmitting(true);
    try {
      const payload = {
        task_name: formState.task_name.trim(),
        project_id: Number(formState.project_id),
        task_date: formState.task_date ? format(formState.task_date, 'yyyy-MM-dd') : null,
        time_start: formState.time_start || null,
        time_end: formState.time_end || null,
        assigned_to: formState.assigned_to ? Number(formState.assigned_to) : null,
        notes: formState.notes ?? '',
        task_items: normaliseItems(formState.task_items),
      };

      if (activeTask) {
        await tasksApi.update(activeTask.task_id, payload);
      } else {
        await tasksApi.create(payload);
      }

      await loadTasks();
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Failed to save task', error);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteTask = async (task) => {
    const confirmDelete = window.confirm(`Delete task "${task.task_name}"?`);
    if (!confirmDelete) {
      return;
    }
    try {
      await tasksApi.delete(task.task_id);
      await loadTasks();
    } catch (error) {
      console.error('Failed to delete task', error);
    }
  };

  const handleToggleItem = async (taskId, index) => {
    const toggleKey = `${taskId}-${index}`;
    setPendingToggleKey(toggleKey);
    try {
      const updated = await tasksApi.toggleItem(taskId, index);
      setTasks((prev) =>
        prev.map((task) => (task.task_id === taskId ? updated : task)),
      );
    } catch (error) {
      console.error('Failed to toggle task item', error);
      await loadTasks();
    } finally {
      setPendingToggleKey(null);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box display="flex" flexDirection="column" gap={3}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5" fontWeight={600}>
            Tasks &amp; Notes
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<FilterListIcon />}
              onClick={() => setShowFilters((prev) => !prev)}
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </Button>
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCreate}>
              New Task
            </Button>
          </Box>
        </Box>

        {showFilters && (
          <Paper sx={{ p: 2 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="Date from"
                  value={filters.dateFrom}
                  onChange={(value) => setFilters((prev) => ({ ...prev, dateFrom: value }))}
                  slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="Date to"
                  value={filters.dateTo}
                  onChange={(value) => setFilters((prev) => ({ ...prev, dateTo: value }))}
                  slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel id="tasks-filter-project">Project</InputLabel>
                  <Select
                    labelId="tasks-filter-project"
                    label="Project"
                    value={filters.projectId}
                    onChange={(event) =>
                      setFilters((prev) => ({ ...prev, projectId: event.target.value }))
                    }
                  >
                    <MenuItem value="">All projects</MenuItem>
                    {projects.map((project) => (
                      <MenuItem key={project.project_id} value={project.project_id}>
                        {project.project_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel id="tasks-filter-user">Assigned</InputLabel>
                  <Select
                    labelId="tasks-filter-user"
                    label="Assigned"
                    value={filters.userId}
                    onChange={(event) =>
                      setFilters((prev) => ({ ...prev, userId: event.target.value }))
                    }
                  >
                    <MenuItem value="">All users</MenuItem>
                    {users.map((user) => (
                      <MenuItem key={user.user_id} value={user.user_id}>
                        {user.full_name ?? user.name ?? user.username ?? `User ${user.user_id}`}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Button onClick={() => setFilters(defaultFilters)}>Reset Filters</Button>
              </Grid>
            </Grid>
          </Paper>
        )}

        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Project</TableCell>
                <TableCell>Task</TableCell>
                <TableCell>Items</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loadingTasks ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : filteredTasks.length ? (
                filteredTasks.map((task) => {
                  const progress = calculateProgress(task);
                  return (
                    <TableRow key={task.task_id} hover>
                      <TableCell>{asDisplayDate(task.task_date)}</TableCell>
                      <TableCell>{buildTimeRange(task.time_start, task.time_end)}</TableCell>
                      <TableCell>{resolveProjectName(task)}</TableCell>
                      <TableCell>
                        <Typography variant="subtitle2">{task.task_name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {resolveUserName(task)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" flexDirection="column" gap={0.5}>
                          {(task.task_items ?? []).map((item, index) => {
                            const toggleKey = `${task.task_id}-${index}`;
                            const disabled = pendingToggleKey === toggleKey;
                            return (
                              <Box
                                key={toggleKey}
                                display="flex"
                                alignItems="center"
                                gap={1}
                              >
                                <Checkbox
                                  size="small"
                                  checked={Boolean(item?.completed)}
                                  disabled={disabled}
                                  onChange={() => handleToggleItem(task.task_id, index)}
                                />
                                <Typography variant="body2">
                                  {item?.label ?? item?.title ?? `Item ${index + 1}`}
                                </Typography>
                              </Box>
                            );
                          })}
                          {!(task.task_items ?? []).length && (
                            <Typography variant="body2" color="text.secondary">
                              No checklist items
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={`${progress.completed}/${progress.total}`} color="primary" />
                      </TableCell>
                      <TableCell sx={{ minWidth: 180 }}>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {task.notes || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => handleOpenEdit(task)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteTask(task)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary">
                      {loadError || 'No tasks match the selected filters.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
          <DialogTitle>{activeTask ? 'Edit Task' : 'New Task'}</DialogTitle>
          <DialogContent dividers>
            <Box display="flex" flexDirection="column" gap={2} mt={1}>
              <TextField
                label="Task name"
                value={formState.task_name}
                onChange={(event) => handleFormFieldChange('task_name', event.target.value)}
                fullWidth
              />

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel id="task-dialog-project">Project</InputLabel>
                    <Select
                      labelId="task-dialog-project"
                      label="Project"
                      value={formState.project_id}
                      onChange={(event) => handleFormFieldChange('project_id', event.target.value)}
                    >
                      {projects.map((project) => (
                        <MenuItem key={project.project_id} value={project.project_id}>
                          {project.project_name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <DatePicker
                    label="Task date"
                    value={formState.task_date}
                    onChange={(value) => handleFormFieldChange('task_date', value)}
                    slotProps={{ textField: { fullWidth: true } }}
                  />
                </Grid>
              </Grid>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Start time"
                    type="time"
                    value={formState.time_start}
                    onChange={(event) => handleFormFieldChange('time_start', event.target.value)}
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="End time"
                    type="time"
                    value={formState.time_end}
                    onChange={(event) => handleFormFieldChange('time_end', event.target.value)}
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>

              <FormControl fullWidth>
                <InputLabel id="task-dialog-user">Assigned to</InputLabel>
                <Select
                  labelId="task-dialog-user"
                  label="Assigned to"
                  value={formState.assigned_to}
                  onChange={(event) => handleFormFieldChange('assigned_to', event.target.value)}
                >
                  <MenuItem value="">Unassigned</MenuItem>
                  {users.map((user) => (
                    <MenuItem key={user.user_id} value={user.user_id}>
                      {user.full_name ?? user.name ?? user.username ?? `User ${user.user_id}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle2">Checklist Items</Typography>
                  <Button startIcon={<AddIcon />} size="small" onClick={handleAddItem}>
                    Add Item
                  </Button>
                </Box>
                {(formState.task_items ?? []).map((item, index) => (
                  <Box
                    key={index}
                    display="flex"
                    alignItems="center"
                    gap={1}
                    sx={{ backgroundColor: 'background.paper', p: 1, borderRadius: 1 }}
                  >
                    <Checkbox
                      checked={Boolean(item.completed)}
                      onChange={(event) =>
                        handleItemChange(index, 'completed', event.target.checked)
                      }
                    />
                    <TextField
                      label="Item"
                      value={item.label}
                      onChange={(event) => handleItemChange(index, 'label', event.target.value)}
                      fullWidth
                    />
                    <IconButton
                      color="error"
                      onClick={() => handleRemoveItem(index)}
                      aria-label="Remove item"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
                {!(formState.task_items ?? []).length && (
                  <Typography variant="body2" color="text.secondary">
                    No checklist items yet. Add one to build a task checklist.
                  </Typography>
                )}
              </Box>

              <TextField
                label="Notes"
                value={formState.notes}
                onChange={(event) => handleFormFieldChange('notes', event.target.value)}
                fullWidth
                multiline
                minRows={3}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleDialogClose} disabled={formSubmitting}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmitForm}
              disabled={formSubmitting}
            >
              {formSubmitting ? <CircularProgress size={20} /> : 'Save Task'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
}
