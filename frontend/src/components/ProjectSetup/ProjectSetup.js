import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Chip,
  Alert,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FolderOpen as FolderIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useProject } from '../../context/ProjectContext';
import { apiService } from '../../services/apiService';

const ProjectSetup = () => {
  const { projects, loading, createProject, updateProject, loadProjects } = useProject();
  const [activeTab, setActiveTab] = useState(0);
  const [open, setOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [formData, setFormData] = useState({
    project_name: '',
    project_description: '',
    client_name: '',
    project_manager: '',
    start_date: null,
    end_date: null,
    status: 'Planning',
    priority: 'Medium',
    folder_path: '',
    ifc_folder_path: '',
    data_export_path: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleInputChange = (field) => (event) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleDateChange = (field) => (date) => {
    setFormData(prev => ({
      ...prev,
      [field]: date
    }));
  };

  const handleOpenDialog = (project = null) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        project_name: project.project_name || '',
        project_description: project.project_description || '',
        client_name: project.client_name || '',
        project_manager: project.project_manager || '',
        start_date: project.start_date ? new Date(project.start_date) : null,
        end_date: project.end_date ? new Date(project.end_date) : null,
        status: project.status || 'Planning',
        priority: project.priority || 'Medium',
        folder_path: project.folder_path || '',
        ifc_folder_path: project.ifc_folder_path || '',
        data_export_path: project.data_export_path || '',
      });
    } else {
      setEditingProject(null);
      setFormData({
        project_name: '',
        project_description: '',
        client_name: '',
        project_manager: '',
        start_date: null,
        end_date: null,
        status: 'Planning',
        priority: 'Medium',
        folder_path: '',
        ifc_folder_path: '',
        data_export_path: '',
      });
    }
    setOpen(true);
    setError('');
    setSuccess('');
  };

  const handleCloseDialog = () => {
    setOpen(false);
    setEditingProject(null);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async () => {
    try {
      if (!formData.project_name.trim()) {
        setError('Project name is required');
        return;
      }

      const projectData = {
        ...formData,
        start_date: formData.start_date ? formData.start_date.toISOString().split('T')[0] : null,
        end_date: formData.end_date ? formData.end_date.toISOString().split('T')[0] : null,
      };

      let success;
      if (editingProject) {
        success = await updateProject(editingProject.project_id, projectData);
      } else {
        success = await createProject(projectData);
      }

      if (success) {
        setSuccess(editingProject ? 'Project updated successfully' : 'Project created successfully');
        setTimeout(() => {
          handleCloseDialog();
          loadProjects();
        }, 1500);
      } else {
        setError('Failed to save project');
      }
    } catch (err) {
      setError('An error occurred while saving the project');
      console.error('Error saving project:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'success';
      case 'Planning': return 'info';
      case 'On Hold': return 'warning';
      case 'Completed': return 'default';
      case 'Cancelled': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  const ProjectDialog = () => (
    <Dialog open={open} onClose={handleCloseDialog} maxWidth="md" fullWidth>
      <DialogTitle>
        {editingProject ? 'Edit Project' : 'Create New Project'}
      </DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {/* Basic Information */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Project Name"
              value={formData.project_name}
              onChange={handleInputChange('project_name')}
              required
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Client Name"
              value={formData.client_name}
              onChange={handleInputChange('client_name')}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Project Description"
              value={formData.project_description}
              onChange={handleInputChange('project_description')}
              multiline
              rows={3}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Project Manager"
              value={formData.project_manager}
              onChange={handleInputChange('project_manager')}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={handleInputChange('status')}
              >
                <MenuItem value="Planning">Planning</MenuItem>
                <MenuItem value="Active">Active</MenuItem>
                <MenuItem value="On Hold">On Hold</MenuItem>
                <MenuItem value="Completed">Completed</MenuItem>
                <MenuItem value="Cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={formData.priority}
                label="Priority"
                onChange={handleInputChange('priority')}
              >
                <MenuItem value="Low">Low</MenuItem>
                <MenuItem value="Medium">Medium</MenuItem>
                <MenuItem value="High">High</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {/* Dates */}
          <Grid item xs={12} md={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Start Date"
                value={formData.start_date}
                onChange={handleDateChange('start_date')}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item xs={12} md={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="End Date"
                value={formData.end_date}
                onChange={handleDateChange('end_date')}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          
          {/* Folder Paths */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Project Folder Path"
              value={formData.folder_path}
              onChange={handleInputChange('folder_path')}
              InputProps={{
                endAdornment: (
                  <IconButton>
                    <FolderIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="IFC Folder Path"
              value={formData.ifc_folder_path}
              onChange={handleInputChange('ifc_folder_path')}
              InputProps={{
                endAdornment: (
                  <IconButton>
                    <FolderIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Data Export Path"
              value={formData.data_export_path}
              onChange={handleInputChange('data_export_path')}
              InputProps={{
                endAdornment: (
                  <IconButton>
                    <FolderIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCloseDialog}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          {editingProject ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  const ProjectsList = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Project Name</TableCell>
            <TableCell>Client</TableCell>
            <TableCell>Manager</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Start Date</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {projects.map((project) => (
            <TableRow key={project.project_id || project.id}>
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  {project.project_name || project.name}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {project.project_description}
                </Typography>
              </TableCell>
              <TableCell>{project.client_name || '-'}</TableCell>
              <TableCell>{project.project_manager || '-'}</TableCell>
              <TableCell>
                <Chip
                  label={project.status || 'Planning'}
                  color={getStatusColor(project.status)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={project.priority || 'Medium'}
                  color={getPriorityColor(project.priority)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                {project.start_date ? new Date(project.start_date).toLocaleDateString() : '-'}
              </TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={() => handleOpenDialog(project)}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Project Setup
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Project
        </Button>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Projects List" />
          <Tab label="Project Templates" />
          <Tab label="Client Management" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && <ProjectsList />}
          {activeTab === 1 && (
            <Typography variant="body1" color="textSecondary">
              Project templates functionality coming soon...
            </Typography>
          )}
          {activeTab === 2 && (
            <Typography variant="body1" color="textSecondary">
              Client management functionality coming soon...
            </Typography>
          )}
        </Box>
      </Paper>

      <ProjectDialog />
    </Box>
  );
};

export default ProjectSetup;