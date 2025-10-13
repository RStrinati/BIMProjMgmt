import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { projectsApi } from '../api/projects';
import type { Project } from '../types/api';

interface ReferenceOption {
  id: number;
  name: string;
}

interface ProjectType {
  type_id: number;
  type_name: string;
}

interface ProjectFormDialogProps {
  open: boolean;
  onClose: () => void;
  project?: Project | null;
  mode: 'create' | 'edit';
}

const ProjectFormDialog: React.FC<ProjectFormDialogProps> = ({ open, onClose, project, mode }) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    project_name: '',
    project_number: '',
    client_id: '',
    project_type: '',
    status: 'Active',
    priority: 'Medium',
    start_date: '',
    end_date: '',
    area_hectares: '',
    mw_capacity: '',
    address: '',
    city: '',
    state: '',
    postcode: '',
    folder_path: '',
    ifc_folder_path: '',
    description: '',
  });

  // Load reference data
  const { data: clients = [] } = useQuery<ReferenceOption[]>({
    queryKey: ['reference', 'clients'],
    queryFn: () => fetch('/api/reference/clients').then((r) => r.json()),
  });

  const { data: projectTypes = [] } = useQuery<ProjectType[]>({
    queryKey: ['reference', 'project_types'],
    queryFn: () => fetch('/api/reference/project_types').then((r) => r.json()),
  });

  // Populate form when editing
  useEffect(() => {
    if (mode === 'edit' && project) {
      setFormData({
        project_name: project.project_name || '',
        project_number: project.project_number || '',
        client_id: project.client_id?.toString() || '',
        project_type: project.project_type || '',
        status: project.status || 'Active',
        priority: project.priority || 'Medium',
        start_date: project.start_date ? project.start_date.split('T')[0] : '',
        end_date: project.end_date ? project.end_date.split('T')[0] : '',
        area_hectares: project.area_hectares?.toString() || '',
        mw_capacity: project.mw_capacity?.toString() || '',
        address: project.address || '',
        city: project.city || '',
        state: project.state || '',
        postcode: project.postcode || '',
        folder_path: project.folder_path || '',
        ifc_folder_path: project.ifc_folder_path || '',
        description: project.description || '',
      });
    } else if (mode === 'create') {
      // Reset form for create mode
      setFormData({
        project_name: '',
        project_number: '',
        client_id: '',
        project_type: '',
        status: 'Active',
        priority: 'Medium',
        start_date: '',
        end_date: '',
        area_hectares: '',
        mw_capacity: '',
        address: '',
        city: '',
        state: '',
        postcode: '',
        folder_path: '',
        ifc_folder_path: '',
        description: '',
      });
    }
  }, [mode, project, open]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projectStats'] });
      onClose();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to create project');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => projectsApi.update(project!.project_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', project?.project_id.toString()] });
      onClose();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to update project');
    },
  });

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: event.target.value }));
    setError(null);
  };

  const handleSubmit = () => {
    // Validation
    if (!formData.project_name.trim()) {
      setError('Project name is required');
      return;
    }
    if (!formData.project_number.trim()) {
      setError('Project number is required');
      return;
    }

    // Prepare payload
    const payload = {
      name: formData.project_name,
      project_number: formData.project_number,
      client_id: formData.client_id ? Number(formData.client_id) : null,
      project_type: formData.project_type || null,
      status: formData.status,
      priority: formData.priority,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
      area: formData.area_hectares ? Number(formData.area_hectares) : null,
      mw_capacity: formData.mw_capacity ? Number(formData.mw_capacity) : null,
      address: formData.address || null,
      city: formData.city || null,
      state: formData.state || null,
      postcode: formData.postcode || null,
      folder_path: formData.folder_path || null,
      ifc_folder_path: formData.ifc_folder_path || null,
      description: formData.description || null,
    };

    if (mode === 'create') {
      createMutation.mutate(payload);
    } else {
      updateMutation.mutate(payload);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{mode === 'create' ? 'Create New Project' : 'Edit Project'}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          {/* Basic Information */}
          <Grid item xs={12} sm={6}>
            <TextField
              label="Project Name"
              value={formData.project_name}
              onChange={handleChange('project_name')}
              fullWidth
              required
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Project Number"
              value={formData.project_number}
              onChange={handleChange('project_number')}
              fullWidth
              required
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Client"
              value={formData.client_id}
              onChange={handleChange('client_id')}
              fullWidth
              select
              disabled={isLoading}
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {clients.map((client) => (
                <MenuItem key={client.id} value={client.id}>
                  {client.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Project Type"
              value={formData.project_type}
              onChange={handleChange('project_type')}
              fullWidth
              select
              disabled={isLoading}
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {projectTypes.map((type) => (
                <MenuItem key={type.type_id} value={type.type_name}>
                  {type.type_name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Status"
              value={formData.status}
              onChange={handleChange('status')}
              fullWidth
              select
              disabled={isLoading}
            >
              <MenuItem value="Active">Active</MenuItem>
              <MenuItem value="On Hold">On Hold</MenuItem>
              <MenuItem value="Completed">Completed</MenuItem>
              <MenuItem value="Cancelled">Cancelled</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Priority"
              value={formData.priority}
              onChange={handleChange('priority')}
              fullWidth
              select
              disabled={isLoading}
            >
              <MenuItem value="Low">Low</MenuItem>
              <MenuItem value="Medium">Medium</MenuItem>
              <MenuItem value="High">High</MenuItem>
              <MenuItem value="Critical">Critical</MenuItem>
            </TextField>
          </Grid>

          {/* Dates */}
          <Grid item xs={12} sm={6}>
            <TextField
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={handleChange('start_date')}
              fullWidth
              InputLabelProps={{ shrink: true }}
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={handleChange('end_date')}
              fullWidth
              InputLabelProps={{ shrink: true }}
              disabled={isLoading}
            />
          </Grid>

          {/* Project Specs */}
          <Grid item xs={12} sm={6}>
            <TextField
              label="Area (Hectares)"
              type="number"
              value={formData.area_hectares}
              onChange={handleChange('area_hectares')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="MW Capacity"
              type="number"
              value={formData.mw_capacity}
              onChange={handleChange('mw_capacity')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          {/* Address */}
          <Grid item xs={12}>
            <TextField
              label="Address"
              value={formData.address}
              onChange={handleChange('address')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <TextField
              label="City"
              value={formData.city}
              onChange={handleChange('city')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <TextField
              label="State"
              value={formData.state}
              onChange={handleChange('state')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <TextField
              label="Postcode"
              value={formData.postcode}
              onChange={handleChange('postcode')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          {/* Folders */}
          <Grid item xs={12} sm={6}>
            <TextField
              label="Folder Path"
              value={formData.folder_path}
              onChange={handleChange('folder_path')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="IFC Folder Path"
              value={formData.ifc_folder_path}
              onChange={handleChange('ifc_folder_path')}
              fullWidth
              disabled={isLoading}
            />
          </Grid>

          {/* Description */}
          <Grid item xs={12}>
            <TextField
              label="Description"
              value={formData.description}
              onChange={handleChange('description')}
              fullWidth
              multiline
              rows={3}
              disabled={isLoading}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={isLoading}>
          {isLoading ? <CircularProgress size={24} /> : mode === 'create' ? 'Create' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectFormDialog;
