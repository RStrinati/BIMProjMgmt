import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  MenuItem,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { serviceTemplatesApi } from '../api/services';
import type { ServiceTemplate } from '../types/api';

interface ProjectType {
  type_id: number;
  type_name: string;
}

interface Client {
  client_id: number;
  client_name: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SettingsPage() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Paper sx={{ width: '100%', mt: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="settings tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Project Types" />
          <Tab label="Clients" />
          <Tab label="Service Templates" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <ProjectTypesTab />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ClientsTab />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ServiceTemplatesTab />
        </TabPanel>
      </Paper>
    </Container>
  );
}

// Project Types Tab Component
function ProjectTypesTab() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingType, setEditingType] = useState<ProjectType | null>(null);
  const [typeName, setTypeName] = useState('');
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  // Fetch project types
  const { data: projectTypes, isLoading } = useQuery<ProjectType[]>({
    queryKey: ['reference', 'project_types'],
    queryFn: async () => {
      const response = await apiClient.get<ProjectType[]>('/reference/project_types');
      return response.data;
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      const response = await apiClient.post('/reference/project_types', { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to create project type');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, name }: { id: number; name: string }) => {
      const response = await apiClient.put(`/reference/project_types/${id}`, { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to update project type');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/reference/project_types/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.error || 'Failed to delete project type');
    },
  });

  const handleOpenCreate = () => {
    setEditingType(null);
    setTypeName('');
    setError('');
    setDialogOpen(true);
  };

  const handleOpenEdit = (type: ProjectType) => {
    setEditingType(type);
    setTypeName(type.type_name);
    setError('');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingType(null);
    setTypeName('');
    setError('');
  };

  const handleSave = () => {
    if (!typeName.trim()) {
      setError('Project type name is required');
      return;
    }

    if (editingType) {
      updateMutation.mutate({ id: editingType.type_id, name: typeName.trim() });
    } else {
      createMutation.mutate(typeName.trim());
    }
  };

  const handleDelete = (type: ProjectType) => {
    if (window.confirm(`Are you sure you want to delete "${type.type_name}"?`)) {
      deleteMutation.mutate(type.type_id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ px: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Project Types</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
        >
          Add Project Type
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projectTypes?.map((type) => (
              <TableRow key={type.type_id}>
                <TableCell>{type.type_id}</TableCell>
                <TableCell>{type.type_name}</TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleOpenEdit(type)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(type)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingType ? 'Edit Project Type' : 'Create Project Type'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Project Type Name"
            type="text"
            fullWidth
            variant="outlined"
            value={typeName}
            onChange={(e) => setTypeName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSave();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <CircularProgress size={24} />
            ) : (
              'Save'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// Clients Tab Component (Placeholder)
function ClientsTab() {
  const { data: clients, isLoading } = useQuery<Client[]>({
    queryKey: ['reference', 'clients'],
    queryFn: async () => {
      const response = await apiClient.get<Client[]>('/reference/clients');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ px: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Clients</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          disabled
        >
          Add Client (Coming Soon)
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients?.map((client) => (
              <TableRow key={client.client_id}>
                <TableCell>{client.client_id}</TableCell>
                <TableCell>{client.client_name}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

// Service Templates Tab Component
function ServiceTemplatesTab() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ServiceTemplate | null>(null);
  const [formData, setFormData] = useState({
    template_name: '',
    description: '',
    service_type: '',
    parameters: '{}',
  });
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const SERVICE_TYPES = [
    'Consulting',
    'Design',
    'Documentation',
    'Review',
    'Supervision',
    'Other'
  ];

  // Fetch service templates
  const {
    data: templates,
    isLoading,
  } = useQuery({
    queryKey: ['serviceTemplates'],
    queryFn: () => serviceTemplatesApi.getAll().then(res => res.data),
  });

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => serviceTemplatesApi.create({
      ...data,
      parameters: JSON.parse(data.parameters),
      created_by: 1, // TODO: Get from auth context
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to create service template');
    },
  });

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) =>
      serviceTemplatesApi.update(id, {
        ...data,
        parameters: data.parameters ? JSON.parse(data.parameters) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to update service template');
    },
  });

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => serviceTemplatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to delete service template');
    },
  });

  const handleOpenDialog = (template?: ServiceTemplate) => {
    if (template) {
      setSelectedTemplate(template);
      setFormData({
        template_name: template.template_name,
        description: template.description || '',
        service_type: template.service_type,
        parameters: JSON.stringify(template.parameters || {}, null, 2),
      });
    } else {
      setSelectedTemplate(null);
      setFormData({
        template_name: '',
        description: '',
        service_type: '',
        parameters: '{}',
      });
    }
    setDialogOpen(true);
    setError('');
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedTemplate(null);
    setFormData({
      template_name: '',
      description: '',
      service_type: '',
      parameters: '{}',
    });
    setError('');
  };

  const handleSubmit = () => {
    if (!formData.template_name.trim()) {
      setError('Template name is required');
      return;
    }
    if (!formData.service_type) {
      setError('Service type is required');
      return;
    }

    if (selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (template: ServiceTemplate) => {
    if (window.confirm(`Are you sure you want to delete "${template.template_name}"?`)) {
      deleteMutation.mutate(template.id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Service Templates</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Template
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templates?.map((template) => (
              <TableRow key={template.id}>
                <TableCell>{template.id}</TableCell>
                <TableCell>{template.template_name}</TableCell>
                <TableCell>
                  <Chip label={template.service_type} size="small" />
                </TableCell>
                <TableCell>{template.description}</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(template)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(template)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedTemplate ? 'Edit Service Template' : 'Create Service Template'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            label="Template Name"
            value={formData.template_name}
            onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
          <TextField
            fullWidth
            select
            label="Service Type"
            value={formData.service_type}
            onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
            margin="normal"
            required
          >
            {SERVICE_TYPES.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            fullWidth
            label="Parameters (JSON)"
            value={formData.parameters}
            onChange={(e) => setFormData({ ...formData, parameters: e.target.value })}
            margin="normal"
            multiline
            rows={4}
            helperText="Enter parameters as JSON object"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
