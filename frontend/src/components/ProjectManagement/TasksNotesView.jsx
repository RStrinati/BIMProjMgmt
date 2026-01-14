import { Fragment, Profiler, useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Checkbox,
  CircularProgress,
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
  TablePagination,
} from '@mui/material';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import FilterListIcon from '@mui/icons-material/FilterList';
import { format } from 'date-fns';
import { tasksApi } from '@/api/tasks';
import { projectsApi } from '@/api/projects';
import { usersApi } from '@/api/users';
import { profilerLog } from '@/utils/perfLogger';

const buildDefaultFilters = (projectId) => ({
  dateFrom: null,
  dateTo: null,
  projectId: projectId ? String(projectId) : '',
  userId: '',
});

const buildDefaultFormState = (projectId) => ({
  task_name: '',
  project_id: projectId ? String(projectId) : '',
  task_date: null,
  time_start: '',
  time_end: '',
  assigned_to: '',
  notes: '',
  task_items: [],
});

const asDisplayDate = (value) => {
  if (!value) {
    return '--';
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
  return '--';
};

const normaliseItems = (items = []) =>
  items
    .filter((item) => item && (item.label || item.title))
    .map((item) => ({
      label: item.label ?? item.title ?? '',
      completed: Boolean(item.completed),
      notes: item.notes ?? '',
    }));

const mapItemsForForm = (items = []) =>
  items.map((item) => ({
    label: item?.label ?? item?.title ?? '',
    completed: Boolean(item?.completed),
    notes: item?.notes ?? '',
  }));

const toTimeInputValue = (value) => {
  if (!value) {
    return '';
  }
  return typeof value === 'string' && value.length > 5 ? value.slice(0, 5) : value;
};

const toApiDate = (value) => {
  if (!value) {
    return undefined;
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return undefined;
  }
  return format(date, 'yyyy-MM-dd');
};

export function TasksNotesView({
  initialProjectId,
  hideFilters = false,
  hideHeader = false,
  hideCreate = false,
  defaultPageSize,
  onTaskCreated,
} = {}) {
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState(() => buildDefaultFilters(initialProjectId));
  const [showFilters, setShowFilters] = useState(!hideFilters);
  const [formState, setFormState] = useState(() => buildDefaultFormState(initialProjectId));
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [pendingToggleKey, setPendingToggleKey] = useState(null);
  const [inlineMode, setInlineMode] = useState(false);
  const [inlineAnchor, setInlineAnchor] = useState(null);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(defaultPageSize ?? 25);
  const [totalTasks, setTotalTasks] = useState(0);
  const defaultFilters = useMemo(() => buildDefaultFilters(initialProjectId), [initialProjectId]);

  useEffect(() => {
    setShowFilters(!hideFilters);
  }, [hideFilters]);

  useEffect(() => {
    if (defaultPageSize && defaultPageSize !== rowsPerPage) {
      setRowsPerPage(defaultPageSize);
      setPage(0);
    }
  }, [defaultPageSize]);

  useEffect(() => {
    if (!initialProjectId) {
      return;
    }
    setFilters((prev) => ({
      ...prev,
      projectId: String(initialProjectId),
    }));
    setFormState((prev) => ({
      ...prev,
      project_id: String(initialProjectId),
    }));
  }, [initialProjectId]);

  const updateFilters = useCallback((updater) => {
    setFilters((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      return next;
    });
    setPage(0);
  }, []);

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

      const requestFilters = {
        project_id: filters.projectId ? Number(filters.projectId) : undefined,
        user_id: filters.userId ? Number(filters.userId) : undefined,
        date_from: toApiDate(filters.dateFrom),
        date_to: toApiDate(filters.dateTo),
        page: page + 1,
        limit: rowsPerPage,
      };

      const result = await tasksApi.getNotesView(requestFilters);
      const fetchedTasks = Array.isArray(result.tasks) ? result.tasks : [];

      setTasks(fetchedTasks);
      setTotalTasks(
        typeof result.total === 'number' && Number.isFinite(result.total)
          ? result.total
          : fetchedTasks.length,
      );

      if (typeof result.page === 'number' && result.page > 0 && result.page - 1 !== page) {
        setPage(result.page - 1);
      }

      if (typeof result.pageSize === 'number' && result.pageSize > 0 && result.pageSize !== rowsPerPage) {
        setRowsPerPage(result.pageSize);
      }
    } catch (error) {
      console.error('Failed to load tasks', error);
      setLoadError('Unable to load tasks. Please try again.');
      setTasks([]);
      setTotalTasks(0);
    } finally {
      setLoadingTasks(false);
    }
  }, [filters, page, rowsPerPage]);

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

  useEffect(() => {
    const maxPage = Math.max(0, Math.ceil(totalTasks / rowsPerPage) - 1);
    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [page, rowsPerPage, totalTasks]);

  const isServerPaginated = totalTasks > tasks.length;

  const paginatedTasks = useMemo(() => {
    if (isServerPaginated) {
      return filteredTasks;
    }
    const start = page * rowsPerPage;
    return filteredTasks.slice(start, start + rowsPerPage);
  }, [filteredTasks, isServerPaginated, page, rowsPerPage]);

  useEffect(() => {
    if (!isServerPaginated) {
      setTotalTasks(filteredTasks.length);
    }
  }, [filteredTasks.length, isServerPaginated]);

  const taskRowsPerPageOptions = useMemo(() => {
    const base = [10, 25, 50, 100];
    if (rowsPerPage > 0 && !base.includes(rowsPerPage)) {
      return [...base, rowsPerPage].sort((a, b) => a - b);
    }
    return base;
  }, [rowsPerPage]);

  const tasksDisplayStart = totalTasks === 0 ? 0 : page * rowsPerPage + 1;
  const tasksDisplayEnd =
    totalTasks === 0 ? 0 : Math.min(tasksDisplayStart + paginatedTasks.length - 1, totalTasks);
  const tasksDisplayRangeText =
    totalTasks === 0
      ? 'No tasks loaded'
      : `Showing ${tasksDisplayStart}-${tasksDisplayEnd} of ${totalTasks} tasks`;

  const resetForm = () => {
    setFormState(buildDefaultFormState(initialProjectId));
    setInlineMode(false);
    setInlineAnchor(null);
    setEditingTaskId(null);
  };

  const handleStartInlineCreate = (anchor = 'top') => {
    const defaultDate =
      filters.dateFrom instanceof Date ? new Date(filters.dateFrom) : new Date();
    const defaultProject = filters.projectId ? String(filters.projectId) : '';
    setFormState({
      ...buildDefaultFormState(initialProjectId),
      task_date: defaultDate,
      project_id: defaultProject,
    });
    if (anchor === 'top') {
      setPage(0);
    } else {
      const targetIndex = filteredTasks.findIndex((task) => task.task_id === anchor);
      if (targetIndex >= 0) {
        setPage(Math.floor(targetIndex / rowsPerPage));
      }
    }
    setInlineAnchor(anchor);
    setInlineMode(true);
    setEditingTaskId(null);
  };

  const handleStartEdit = (task) => {
    const dateValue = task.task_date ? new Date(task.task_date) : null;
    const safeDate =
      dateValue && !Number.isNaN(dateValue.getTime()) ? dateValue : new Date();
    setFormState({
      task_name: task.task_name ?? '',
      project_id: task.project_id ? String(task.project_id) : '',
      task_date: safeDate,
      time_start: toTimeInputValue(task.time_start),
      time_end: toTimeInputValue(task.time_end),
      assigned_to: task.assigned_to ? String(task.assigned_to) : '',
      notes: task.notes ?? '',
      task_items: mapItemsForForm(task.task_items ?? []),
    });
    const targetIndex = filteredTasks.findIndex((item) => item.task_id === task.task_id);
    if (targetIndex >= 0) {
      setPage(Math.floor(targetIndex / rowsPerPage));
    }
    setInlineAnchor(task.task_id);
    setInlineMode(true);
    setEditingTaskId(task.task_id);
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
      const taskDateIso = formState.task_date
        ? format(formState.task_date, 'yyyy-MM-dd')
        : format(new Date(), 'yyyy-MM-dd');
      const payload = {
        task_name: formState.task_name.trim(),
        project_id: Number(formState.project_id),
        task_date: taskDateIso,
        start_date: taskDateIso,
        end_date: taskDateIso,
        time_start: formState.time_start || null,
        time_end: formState.time_end || null,
        assigned_to: formState.assigned_to ? Number(formState.assigned_to) : null,
        notes: formState.notes ?? '',
        task_items: normaliseItems(formState.task_items),
      };

      if (editingTaskId) {
        await tasksApi.update(editingTaskId, payload);
      } else {
        const createdTask = await tasksApi.create(payload);
        if (onTaskCreated) {
          onTaskCreated(createdTask);
        }
      }
      await loadTasks();
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

  const handleInlineKeyDown = (event) => {
    if (!inlineMode) {
      return;
    }
    if (event.ctrlKey && event.key === '1') {
      event.preventDefault();
      handleAddItem();
    } else if (event.shiftKey && event.key === 'Enter') {
      event.preventDefault();
      handleAddItem();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      resetForm();
    }
  };

  const renderInlineCreateRow = (anchorKey) => {
    const isEditing = Boolean(editingTaskId);
    return (
    <TableRow
      key={`inline-${anchorKey}`}
      sx={{ backgroundColor: 'background.paper' }}
      onKeyDown={handleInlineKeyDown}
      tabIndex={-1}
    >
      <TableCell>
        <DatePicker
          value={formState.task_date}
          onChange={(value) => handleFormFieldChange('task_date', value)}
          slotProps={{ textField: { size: 'small', fullWidth: true } }}
        />
      </TableCell>
      <TableCell>
        <Box display="flex" gap={1}>
          <TextField
            label="Start"
            type="time"
            size="small"
            value={formState.time_start}
            onChange={(event) => handleFormFieldChange('time_start', event.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="End"
            type="time"
            size="small"
            value={formState.time_end}
            onChange={(event) => handleFormFieldChange('time_end', event.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </Box>
      </TableCell>
      <TableCell>
        <FormControl fullWidth size="small">
          <InputLabel id="inline-project">Project</InputLabel>
          <Select
            labelId="inline-project"
            label="Project"
            value={formState.project_id}
            onChange={(event) => handleFormFieldChange('project_id', event.target.value)}
            disabled={Boolean(initialProjectId)}
          >
            {projects.map((project) => (
              <MenuItem key={project.project_id} value={project.project_id}>
                {project.project_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </TableCell>
      <TableCell sx={{ minWidth: 220 }}>
        <TextField
          label="Task name"
          value={formState.task_name}
          size="small"
          fullWidth
          autoFocus
          onChange={(event) => handleFormFieldChange('task_name', event.target.value)}
        />
        <FormControl fullWidth size="small" sx={{ mt: 1 }}>
          <InputLabel id="inline-assignee">Assigned to</InputLabel>
          <Select
            labelId="inline-assignee"
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
      </TableCell>
      <TableCell>
        <Box display="flex" flexDirection="column" gap={0.5}>
          {(formState.task_items ?? []).map((item, index) => (
            <Box key={index} display="flex" alignItems="center" gap={1}>
              <Checkbox
                size="small"
                checked={Boolean(item.completed)}
                onChange={(event) => handleItemChange(index, 'completed', event.target.checked)}
              />
              <TextField
                size="small"
                value={item.label}
                placeholder={`Item ${index + 1}`}
                onChange={(event) => handleItemChange(index, 'label', event.target.value)}
              />
              <IconButton size="small" color="error" onClick={() => handleRemoveItem(index)}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={handleAddItem}
            variant="text"
          >
            Add Item
          </Button>
        </Box>
      </TableCell>
      <TableCell>
        <Chip
          label={`${(formState.task_items ?? []).filter((item) => item.completed).length}/${
            formState.task_items?.length ?? 0
          }`}
        />
      </TableCell>
      <TableCell>
        <TextField
          value={formState.notes}
          onChange={(event) => handleFormFieldChange('notes', event.target.value)}
          placeholder="Notes"
          multiline
          minRows={2}
          size="small"
          fullWidth
        />
      </TableCell>
      <TableCell align="right">
        <Box display="flex" gap={1} justifyContent="flex-end">
          <Button variant="outlined" size="small" onClick={resetForm} disabled={formSubmitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleSubmitForm}
            disabled={formSubmitting || !formState.task_name?.trim() || !formState.project_id}
          >
            {formSubmitting ? (
              <CircularProgress size={18} />
            ) : (
              isEditing ? 'Update Task' : 'Create Task'
            )}
          </Button>
        </Box>
      </TableCell>
    </TableRow>
  );
  };

  return (
    <Profiler id="TasksNotesView" onRender={profilerLog}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <Box display="flex" flexDirection="column" gap={3}>
        {!hideHeader && (
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" fontWeight={600}>
              Tasks &amp; Notes
            </Typography>
            <Box display="flex" gap={1}>
              {!hideFilters && (
                <Button
                  variant="outlined"
                  startIcon={<FilterListIcon />}
                  onClick={() => setShowFilters((prev) => !prev)}
                >
                  {showFilters ? 'Hide Filters' : 'Show Filters'}
                </Button>
              )}
              {!hideCreate && (
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => handleStartInlineCreate('top')}
                  disabled={inlineMode}
                >
                  Add Task Row
                </Button>
              )}
            </Box>
          </Box>
        )}

        {!hideFilters && showFilters && (
          <Paper sx={{ p: 2 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="Date from"
                  value={filters.dateFrom}
                  onChange={(value) =>
                    updateFilters((prev) => ({
                      ...prev,
                      dateFrom: value,
                    }))
                  }
                  slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="Date to"
                  value={filters.dateTo}
                  onChange={(value) =>
                    updateFilters((prev) => ({
                      ...prev,
                      dateTo: value,
                    }))
                  }
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
                      updateFilters((prev) => ({
                        ...prev,
                        projectId: event.target.value,
                      }))
                    }
                    disabled={Boolean(initialProjectId)}
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
                      updateFilters((prev) => ({
                        ...prev,
                        userId: event.target.value,
                      }))
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
                <Button onClick={() => updateFilters(() => ({ ...defaultFilters }))}>
                  Reset Filters
                </Button>
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
              ) : (
                <>
                  {inlineMode && inlineAnchor === 'top' && page === 0 && renderInlineCreateRow('top')}
                  {paginatedTasks.length ? (
                    paginatedTasks.map((task) => {
                      const progress = calculateProgress(task);
                      const isEditingRow =
                        inlineMode && inlineAnchor === task.task_id && editingTaskId === task.task_id;
                      return (
                        <Fragment key={task.task_id}>
                          {!isEditingRow && (
                            <TableRow hover>
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
                                  {task.notes || '--'}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <IconButton
                                  size="small"
                                  onClick={() => handleStartInlineCreate(task.task_id)}
                                  color={inlineMode && inlineAnchor === task.task_id && !editingTaskId ? 'primary' : 'default'}
                                  aria-label="Add task below"
                                >
                                  <AddIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  onClick={() => handleStartEdit(task)}
                                  color={editingTaskId === task.task_id ? 'primary' : 'default'}
                                  aria-label="Edit task"
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleDeleteTask(task)}
                                  aria-label="Delete task"
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          )}
                          {inlineMode && inlineAnchor === task.task_id && renderInlineCreateRow(task.task_id)}
                        </Fragment>
                      );
                    })
                  ) : inlineMode && inlineAnchor === 'top' ? null : (
                    <TableRow>
                      <TableCell colSpan={8} align="center">
                        <Typography variant="body2" color="text.secondary">
                          {loadError || 'No tasks match the selected filters.'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Box sx={{ px: 2, pb: 1 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            {tasksDisplayRangeText}
          </Typography>
          {isServerPaginated && (
            <Typography variant="caption" color="text.secondary" display="block">
              Totals reflect the full dataset reported by the API; adjust pagination to review additional pages.
            </Typography>
          )}
        </Box>
        <TablePagination
          component="div"
          count={totalTasks}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(_event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            const nextValue = Number(event.target.value) || 10;
            setRowsPerPage(nextValue);
            setPage(0);
          }}
          rowsPerPageOptions={taskRowsPerPageOptions}
        />
        </Box>
      </LocalizationProvider>
    </Profiler>
  );
}
