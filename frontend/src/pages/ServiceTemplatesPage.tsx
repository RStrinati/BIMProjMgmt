import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Typography,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { serviceTemplatesApi } from '@/api';
import type { ServiceTemplate } from '@/types/api';

const SERVICE_TYPES = [
  'Consulting',
  'Design',
  'Documentation',
  'Review',
  'Supervision',
  'Other'
];

export function ServiceTemplatesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ServiceTemplate | null>(null);
  const [formData, setFormData] = useState({
    template_name: '',
    description: '',
    service_type: '',
    parameters: '{}',
  });

  // Fetch service templates
  const {
    data: templates,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['serviceTemplates'],
    queryFn: () => serviceTemplatesApi.getAll(),
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
  });

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => serviceTemplatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates'] });
    },
  });

  const handleOpenDialog = (template?: ServiceTemplate) => {
    if (template) {
      setSelectedTemplate(template);
      setFormData({
        template_name: template.template_name,
        description: template.description,
        service_type: template.service_type,
        parameters: JSON.stringify(template.parameters, null, 2),
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
  };

  const handleSubmit = () => {
    if (selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this service template?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load service templates: {error.message}
      </Alert>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Service Templates
        </Typography>
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
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templates?.data?.map((template) => (
              <TableRow key={template.id}>
                <TableCell>{template.template_name}</TableCell>
                <TableCell>
                  <Chip label={template.service_type} size="small" />
                </TableCell>
                <TableCell>{template.description}</TableCell>
                <TableCell>
                  <Chip
                    label={template.is_active ? 'Active' : 'Inactive'}
                    color={template.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(template.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(template)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(template.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Template Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedTemplate ? 'Edit Service Template' : 'Create Service Template'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Template Name"
                value={formData.template_name}
                onChange={(e) => setFormData(prev => ({ ...prev, template_name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Service Type"
                value={formData.service_type}
                onChange={(e) => setFormData(prev => ({ ...prev, service_type: e.target.value }))}
                required
              >
                {SERVICE_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Parameters (JSON)"
                value={formData.parameters}
                onChange={(e) => setFormData(prev => ({ ...prev, parameters: e.target.value }))}
                placeholder='{"key": "value"}'
                helperText="Enter parameters as JSON"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <CircularProgress size={20} />
            ) : (
              selectedTemplate ? 'Update' : 'Create'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}