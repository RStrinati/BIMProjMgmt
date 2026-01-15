import React, { useEffect, useMemo, useState } from 'react';
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
  Chip,
} from '@mui/material';
import { projectsApi } from '../api/projects';
import { clientsApi } from '../api/clients';
import { usersApi } from '../api/users';
import { useNamingConventionOptions } from '../hooks/useNamingConventions';
import type { Project, User } from '../types/api';
import type { Client } from '../api/clients';

interface ProjectType {
  type_id: number;
  type_name: string;
}

interface ProjectFormDialogProps {
  open: boolean;
  onClose: () => void;
  project?: Project | null;
  mode: 'create' | 'edit';
  onSuccess?: () => void;
}

type FormState = {
  project_name: string;
  project_number: string;
  client_id: string;
  project_type_id: string;
  status: string;
  priority: string;
  start_date: string;
  end_date: string;
  area_hectares: string;
  mw_capacity: string;
  address: string;
  city: string;
  state: string;
  postcode: string;
  folder_path: string;
  ifc_folder_path: string;
  description: string;
  internal_lead: string;
  naming_convention: string;
};

const emptyFormState: FormState = {
  project_name: '',
  project_number: '',
  client_id: '',
  project_type_id: '',
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
  internal_lead: '',
  naming_convention: '',
};

const REVERSE_PRIORITY_MAP: Record<number, string> = { 1: "Low", 2: "Medium", 3: "High", 4: "Critical" };

const ProjectFormDialog: React.FC<ProjectFormDialogProps> = ({ open, onClose, project, mode, onSuccess }) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormState>({ ...emptyFormState });
  // Load reference data
  const { data: clients = [] } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: clientsApi.getAll,
  });

  const { options: namingConventionOptions, isLoading: namingConventionsLoading } = useNamingConventionOptions();

  const { data: projectTypes = [] } = useQuery<ProjectType[]>({
    queryKey: ['reference', 'project_types'],
    queryFn: () => fetch('/api/reference/project_types').then((r) => r.json()),
  });

  const { data: users = [], isLoading: usersLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  });

  const clientById = useMemo(() => {
    const map = new Map<number, Client>();
    clients.forEach((client) => {
      const key = client.id ?? client.client_id;
      if (key !== undefined) {
        map.set(key, client);
      }
    });
    return map;
  }, [clients]);

  const userOptions = useMemo(() => {
    const options = users.map((user) => ({
      value: user.user_id.toString(),
      label: user.name || user.full_name || user.username || `User ${user.user_id}`,
    }));

    if (
      formData.internal_lead &&
      !options.some((option) => option.value === formData.internal_lead)
    ) {
      options.unshift({
        value: formData.internal_lead,
        label: `User ${formData.internal_lead}`,
      });
    }

    return options;
  }, [users, formData.internal_lead]);

  // Populate form when editing
  useEffect(() => {
    if (mode === 'edit' && project) {
      const projectClient =
        project.client_id !== undefined && project.client_id !== null
          ? clientById.get(project.client_id)
          : undefined;
      
      setFormData({
        project_name: project.project_name || '',
        project_number: project.project_number || project.contract_number || '',
        client_id: project.client_id?.toString() || '',
        project_type_id: project.type_id?.toString() || '',
        status: project.status || 'Active',
        priority: (() => {
          let p = project.priority;
          if (typeof p === 'number') {
            return REVERSE_PRIORITY_MAP[p] || 'Medium';
          } else if (typeof p === 'string' && /^\d+$/.test(p)) {
            const num = parseInt(p);
            return REVERSE_PRIORITY_MAP[num] || 'Medium';
          } else {
            return p || 'Medium';
          }
        })(),
        start_date: project.start_date ? new Date(project.start_date).toISOString().slice(0, 10) : '',
        end_date: project.end_date ? new Date(project.end_date).toISOString().slice(0, 10) : '',
        area_hectares:
          project.area_hectares !== undefined && project.area_hectares !== null
            ? project.area_hectares.toString()
            : '',
        mw_capacity: project.mw_capacity?.toString() || '',
        address: project.address || '',
        city: project.city || '',
        state: project.state || '',
        postcode: project.postcode || '',
        folder_path: project.folder_path || '',
        ifc_folder_path: project.ifc_folder_path || '',
        description: project.description || '',
        internal_lead: project.internal_lead?.toString() || '',
        // Use project's saved naming convention if it exists, otherwise fall back to client's default
        naming_convention: project.naming_convention || projectClient?.naming_convention || '',
      });
    } else if (mode === 'create') {
      // Reset form for create mode
      setFormData({ ...emptyFormState });
    }
  }, [mode, project, clientById]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'review-stats'] });
      queryClient.invalidateQueries({ queryKey: ['projects-home-v2'] });
      onSuccess?.();
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
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'review-stats'] });
      queryClient.invalidateQueries({ queryKey: ['project', project?.project_id] });
      queryClient.invalidateQueries({ queryKey: ['projects-home-v2'] });
      onSuccess?.();
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

  // Special handler for client changes - auto-populate naming convention
  const handleClientChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const clientId = event.target.value;
    const selectedClient =
      clientId !== '' ? clientById.get(Number(clientId)) : undefined;
    
    setFormData((prev) => ({ 
      ...prev, 
      client_id: clientId,
      naming_convention: selectedClient?.naming_convention || ''
    }));
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
      project_name: formData.project_name,
      project_number: formData.project_number,
      client_id: formData.client_id ? Number(formData.client_id) : null,
      type_id: formData.project_type_id ? Number(formData.project_type_id) : null,
      status: formData.status || null,
      priority: formData.priority,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
      area_hectares: formData.area_hectares ? Number(formData.area_hectares) : null,
      mw_capacity: formData.mw_capacity ? Number(formData.mw_capacity) : null,
      address: formData.address || null,
      city: formData.city || null,
      state: formData.state || null,
      postcode: formData.postcode || null,
      folder_path: formData.folder_path || null,
      ifc_folder_path: formData.ifc_folder_path || null,
      description: formData.description || null,
      internal_lead: formData.internal_lead ? Number(formData.internal_lead) : null,
      naming_convention: formData.naming_convention || null,
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
              onChange={handleClientChange}
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
                  {client.naming_convention && (
                    <span style={{ marginLeft: '8px', fontSize: '0.85em', color: '#666' }}>
                      [{client.naming_convention}]
                    </span>
                  )}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Show naming convention if client has one */}
          {formData.client_id && (() => {
            const selectedClient = clientById.get(Number(formData.client_id));
            return selectedClient?.naming_convention ? (
              <Grid item xs={12}>
                <Chip 
                  label={`File Naming Convention: ${selectedClient.naming_convention}`}
                  color="info"
                  size="small"
                  sx={{ mt: -1 }}
                />
              </Grid>
            ) : null;
          })()}

          <Grid item xs={12} sm={6}>
            <TextField
              label="Project Type"
              value={formData.project_type_id}
              onChange={handleChange('project_type_id')}
              fullWidth
              select
              disabled={isLoading}
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {projectTypes.map((type) => (
                <MenuItem key={type.type_id} value={type.type_id.toString()}>
                  {type.type_name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Optional Naming Convention Override */}
          <Grid item xs={12} sm={6}>
            <TextField
              label="Naming Convention (Override)"
              value={formData.naming_convention}
              onChange={handleChange('naming_convention')}
              fullWidth
              select
              disabled={isLoading || namingConventionsLoading}
              helperText="Optional: Override client's default naming convention"
            >
              <MenuItem value="">
                <em>Use Client Default</em>
              </MenuItem>
              {namingConventionOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
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
              label="Area (ha)"
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

          <Grid item xs={12} sm={6}>
            <TextField
              label="Project Lead"
              value={formData.internal_lead}
              onChange={handleChange('internal_lead')}
              fullWidth
              select
              disabled={isLoading || usersLoading}
              helperText="Assign a primary lead for this project"
            >
              <MenuItem value="">
                <em>Unassigned</em>
              </MenuItem>
              {userOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
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
