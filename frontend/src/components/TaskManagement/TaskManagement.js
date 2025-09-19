import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  CheckCircle as CompleteIcon,
  ExpandMore as ExpandMoreIcon,
  Assignment as TaskIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  TrendingUp as ProgressIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useProject } from '../../context/ProjectContext';
import { apiService } from '../../services/apiService';

const TaskManagement = () => {
  const { projects, currentProject } = useProject();
  const [activeTab, setActiveTab] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Task form state
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [taskForm, setTaskForm] = useState({
    task_name: '',
    project_id: currentProject?.project_id || '',
    priority: 'Medium',
    status: 'Not Started',
    assigned_to: '',
    start_date: null,
    end_date: null,
    estimated_hours: '',
    description: '',
    predecessor_task_id: '',
  });

  useEffect(() => {
    loadResources();
    if (currentProject?.project_id) {
      loadTasks(currentProject.project_id);
    }
  }, [currentProject]);

  const loadTasks = async (projectId) => {
    try {
      setLoading(true);
      const tasksData = await apiService.request(`/tasks?project_id=${projectId}`);
      setTasks(tasksData);
    } catch (err) {
      setError('Failed to load tasks');
      console.error('Error loading tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadResources = async () => {
    try {
      const resourcesData = await apiService.request('/resources');
      setResources(resourcesData);
    } catch (err) {
      console.error('Error loading resources:', err);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleInputChange = (field) => (event) => {
    setTaskForm(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleDateChange = (field) => (date) => {
    setTaskForm(prev => ({
      ...prev,
      [field]: date
    }));
  };

  const handleOpenDialog = (task = null) => {
    if (task) {
      setEditingTask(task);
      setTaskForm({
        task_name: task.task_name || '',
        project_id: task.project_id || currentProject?.project_id || '',
        priority: task.priority || 'Medium',
        status: task.status || 'Not Started',
        assigned_to: task.assigned_to || '',
        start_date: task.start_date ? new Date(task.start_date) : null,
        end_date: task.end_date ? new Date(task.end_date) : null,
        estimated_hours: task.estimated_hours || '',
        description: task.description || '',
        predecessor_task_id: task.predecessor_task_id || '',
      });
    } else {
      setEditingTask(null);
      setTaskForm({
        task_name: '',
        project_id: currentProject?.project_id || '',
        priority: 'Medium',
        status: 'Not Started',
        assigned_to: '',
        start_date: null,
        end_date: null,
        estimated_hours: '',
        description: '',
        predecessor_task_id: '',
      });
    }
    setOpenDialog(true);
    setError('');
    setSuccess('');
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTask(null);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async () => {
    try {
      if (!taskForm.task_name.trim()) {
        setError('Task name is required');
        return;
      }

      if (!taskForm.project_id) {
        setError('Please select a project');
        return;
      }

      const taskData = {
        ...taskForm,
        start_date: taskForm.start_date ? taskForm.start_date.toISOString().split('T')[0] : null,
        end_date: taskForm.end_date ? taskForm.end_date.toISOString().split('T')[0] : null,
        estimated_hours: taskForm.estimated_hours ? parseInt(taskForm.estimated_hours) : 0,
      };

      if (editingTask) {
        await apiService.request(`/tasks/${editingTask.task_id}`, {
          method: 'PATCH',
          body: JSON.stringify(taskData),
        });
        setSuccess('Task updated successfully');
      } else {
        await apiService.request('/tasks', {
          method: 'POST',
          body: JSON.stringify(taskData),
        });
        setSuccess('Task created successfully');
      }

      setTimeout(() => {
        handleCloseDialog();
        if (currentProject?.project_id) {
          loadTasks(currentProject.project_id);
        }
      }, 1500);
    } catch (err) {
      setError('Failed to save task');
      console.error('Error saving task:', err);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await apiService.request(`/tasks/${taskId}`, { method: 'DELETE' });
      setSuccess('Task deleted successfully');
      if (currentProject?.project_id) {
        loadTasks(currentProject.project_id);
      }
    } catch (err) {
      setError('Failed to delete task');
      console.error('Error deleting task:', err);
    }
  };

  const updateTaskStatus = async (taskId, newStatus) => {
    try {
      await apiService.request(`/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      if (currentProject?.project_id) {
        loadTasks(currentProject.project_id);
      }
    } catch (err) {
      setError('Failed to update task status');
      console.error('Error updating task status:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'In Progress': return 'info';
      case 'On Hold': return 'warning';
      case 'Not Started': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': return 'error';
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  const TaskDialog = () => (
    <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
      <DialogTitle>
        {editingTask ? 'Edit Task' : 'Create New Task'}
      </DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Task Name"
              value={taskForm.task_name}
              onChange={handleInputChange('task_name')}
              required
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={taskForm.priority}
                label="Priority"
                onChange={handleInputChange('priority')}
              >
                <MenuItem value="Low">Low</MenuItem>
                <MenuItem value="Medium">Medium</MenuItem>
                <MenuItem value="High">High</MenuItem>
                <MenuItem value="Critical">Critical</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={taskForm.status}
                label="Status"
                onChange={handleInputChange('status')}
              >
                <MenuItem value="Not Started">Not Started</MenuItem>
                <MenuItem value="In Progress">In Progress</MenuItem>
                <MenuItem value="On Hold">On Hold</MenuItem>
                <MenuItem value="Completed">Completed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Assigned To</InputLabel>
              <Select
                value={taskForm.assigned_to}
                label="Assigned To"
                onChange={handleInputChange('assigned_to')}
              >
                <MenuItem value="">Unassigned</MenuItem>
                {resources.map((resource) => (
                  <MenuItem key={resource.user_id} value={resource.name}>
                    {resource.name} {!resource.available && '(Unavailable)'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Start Date"
                value={taskForm.start_date}
                onChange={handleDateChange('start_date')}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item xs={12} md={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="End Date"
                value={taskForm.end_date}
                onChange={handleDateChange('end_date')}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Estimated Hours"
              type="number"
              value={taskForm.estimated_hours}
              onChange={handleInputChange('estimated_hours')}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Predecessor Task</InputLabel>
              <Select
                value={taskForm.predecessor_task_id}
                label="Predecessor Task"
                onChange={handleInputChange('predecessor_task_id')}
              >
                <MenuItem value="">None</MenuItem>
                {tasks.filter(t => t.task_id !== editingTask?.task_id).map((task) => (
                  <MenuItem key={task.task_id} value={task.task_id}>
                    {task.task_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={taskForm.description}
              onChange={handleInputChange('description')}
              multiline
              rows={3}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCloseDialog}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          {editingTask ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  const TaskList = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Task Name</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Assigned To</TableCell>
            <TableCell>Due Date</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.task_id}>
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  {task.task_name}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {task.description}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={task.priority}
                  color={getPriorityColor(task.priority)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={task.status}
                  color={getStatusColor(task.status)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Box sx={{ minWidth: 100 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={task.progress_percentage || 0} 
                    sx={{ mb: 0.5 }}
                  />
                  <Typography variant="caption">
                    {task.progress_percentage || 0}%
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>{task.assigned_to || 'Unassigned'}</TableCell>
              <TableCell>
                {task.end_date ? new Date(task.end_date).toLocaleDateString() : '-'}
              </TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={() => handleOpenDialog(task)}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleDeleteTask(task.task_id)}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
                {task.status === 'Not Started' && (
                  <IconButton
                    size="small"
                    onClick={() => updateTaskStatus(task.task_id, 'In Progress')}
                    color="success"
                  >
                    <StartIcon />
                  </IconButton>
                )}
                {task.status === 'In Progress' && (
                  <IconButton
                    size="small"
                    onClick={() => updateTaskStatus(task.task_id, 'Completed')}
                    color="success"
                  >
                    <CompleteIcon />
                  </IconButton>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const TaskDashboard = () => {
    const taskStats = {
      total: tasks.length,
      notStarted: tasks.filter(t => t.status === 'Not Started').length,
      inProgress: tasks.filter(t => t.status === 'In Progress').length,
      completed: tasks.filter(t => t.status === 'Completed').length,
      overdue: tasks.filter(t => t.end_date && new Date(t.end_date) < new Date() && t.status !== 'Completed').length,
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TaskIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h4">{taskStats.total}</Typography>
                  <Typography color="textSecondary">Total Tasks</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ScheduleIcon color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h4">{taskStats.notStarted}</Typography>
                  <Typography color="textSecondary">Not Started</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ProgressIcon color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h4">{taskStats.inProgress}</Typography>
                  <Typography color="textSecondary">In Progress</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CompleteIcon color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h4">{taskStats.completed}</Typography>
                  <Typography color="textSecondary">Completed</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ScheduleIcon color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h4">{taskStats.overdue}</Typography>
                  <Typography color="textSecondary">Overdue</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Task Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          disabled={!currentProject}
        >
          New Task
        </Button>
      </Box>

      {!currentProject && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please select a project from the Project Setup tab to manage tasks.
        </Alert>
      )}

      {currentProject && (
        <Paper sx={{ width: '100%' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="Dashboard" />
            <Tab label="Task List" />
            <Tab label="Gantt View" />
            <Tab label="Resources" />
          </Tabs>

          <Box sx={{ p: 3 }}>
            {activeTab === 0 && <TaskDashboard />}
            {activeTab === 1 && <TaskList />}
            {activeTab === 2 && (
              <Typography variant="body1" color="textSecondary">
                Gantt chart view coming soon...
              </Typography>
            )}
            {activeTab === 3 && (
              <Typography variant="body1" color="textSecondary">
                Resource allocation view coming soon...
              </Typography>
            )}
          </Box>
        </Paper>
      )}

      <TaskDialog />
    </Box>
  );
};

export default TaskManagement;