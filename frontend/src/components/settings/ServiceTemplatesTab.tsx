import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  ContentCopy as DuplicateIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fileServiceTemplatesApi, serviceTemplatesApi } from '../../api/services';
import type { FileServiceTemplate, ServiceTemplate } from '../../types/api';

const SERVICE_TYPES = [
  'Consulting',
  'Design',
  'Documentation',
  'Review',
  'Supervision',
  'Other',
];

const ServiceTemplatesTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ServiceTemplate | null>(null);
  const [formData, setFormData] = useState({
    template_name: '',
    description: '',
    service_type: '',
    parameters: '{}',
  });
  const [error, setError] = useState('');

  const [fileDialogOpen, setFileDialogOpen] = useState(false);
  const [fileDialogMode, setFileDialogMode] = useState<'create' | 'edit' | 'duplicate'>('create');
  const [fileOriginalName, setFileOriginalName] = useState<string | undefined>();
  const [fileFormData, setFileFormData] = useState({
    name: '',
    sector: '',
    notes: '',
    itemsJson: '[]',
  });
  const [fileError, setFileError] = useState('');

  const {
    data: dbTemplates,
    isLoading: dbLoading,
  } = useQuery<ServiceTemplate[]>({
    queryKey: ['serviceTemplates', 'database'],
    queryFn: () => serviceTemplatesApi.getAll().then((res) => res.data),
  });

  const fileTemplatesQuery = useQuery<FileServiceTemplate[]>({
    queryKey: ['serviceTemplates', 'file'],
    queryFn: () => fileServiceTemplatesApi.getAll().then((res) => res.data),
  });

  const createMutation = useMutation<unknown, Error, typeof formData>({
    mutationFn: (data: typeof formData) =>
      serviceTemplatesApi.create({
        ...data,
        parameters: JSON.parse(data.parameters),
        created_by: 1,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates', 'database'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to create service template');
    },
  });

  const updateMutation = useMutation<unknown, Error, { id: number; data: Partial<typeof formData> }>({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) =>
      serviceTemplatesApi.update(id, {
        ...data,
        parameters: data.parameters ? JSON.parse(data.parameters) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates', 'database'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to update service template');
    },
  });

  const deleteMutation = useMutation<unknown, Error, number>({
    mutationFn: (id: number) => serviceTemplatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates', 'database'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to delete service template');
    },
  });

  const fileSaveMutation = useMutation<unknown, Error, {
    template: {
      name: string;
      sector?: string;
      notes?: string;
      items: Record<string, any>[];
    };
    overwrite?: boolean;
    original_name?: string;
  }>({
    mutationFn: (payload: {
      template: { name: string; sector?: string; notes?: string; items: Record<string, any>[] };
      overwrite?: boolean;
      original_name?: string;
    }) => fileServiceTemplatesApi.save(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates', 'file'] });
      handleCloseFileDialog();
    },
    onError: (err: any) => {
      setFileError(err?.response?.data?.error ?? 'Failed to save file template');
    },
  });

  const fileDeleteMutation = useMutation<unknown, Error, string>({
    mutationFn: (name: string) => fileServiceTemplatesApi.delete(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceTemplates', 'file'] });
    },
    onError: (err: any) => {
      setFileError(err?.response?.data?.error ?? 'Failed to delete file template');
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

  const handleOpenFileDialog = (
    mode: 'create' | 'edit' | 'duplicate',
    template?: FileServiceTemplate,
  ) => {
    setFileDialogMode(mode);
    setFileError('');

    if (template) {
      const nextName = mode === 'duplicate' ? `${template.name} Copy` : template.name;
      setFileFormData({
        name: nextName,
        sector: template.sector ?? '',
        notes: template.notes ?? '',
        itemsJson: JSON.stringify(template.items ?? [], null, 2),
      });
      setFileOriginalName(mode === 'edit' ? template.name : undefined);
    } else {
      setFileOriginalName(undefined);
      setFileFormData({
        name: '',
        sector: '',
        notes: '',
        itemsJson: '[]',
      });
    }

    setFileDialogOpen(true);
  };

  const handleCloseFileDialog = () => {
    setFileDialogOpen(false);
    setFileOriginalName(undefined);
    setFileError('');
    setFileFormData({
      name: '',
      sector: '',
      notes: '',
      itemsJson: '[]',
    });
  };

  const handleFileSubmit = () => {
    if (!fileFormData.name.trim()) {
      setFileError('Template name is required');
      return;
    }

    let items: Record<string, any>[];
    try {
      const parsed = JSON.parse(fileFormData.itemsJson || '[]');
      if (!Array.isArray(parsed)) {
        throw new Error('Items must be an array');
      }
      items = parsed;
    } catch (err) {
      setFileError('Items must be a valid JSON array');
      return;
    }

    fileSaveMutation.mutate({
      template: {
        name: fileFormData.name.trim(),
        sector: fileFormData.sector || undefined,
        notes: fileFormData.notes || '',
        items,
      },
      overwrite: fileDialogMode === 'edit',
      original_name: fileDialogMode === 'edit' ? fileOriginalName : undefined,
    });
  };

  const handleFileDelete = (template: FileServiceTemplate) => {
    if (window.confirm(`Delete template "${template.name}" from file storage?`)) {
      fileDeleteMutation.mutate(template.name);
    }
  };

  const formatEstimatedValue = (value: number) =>
    new Intl.NumberFormat(undefined, { style: 'currency', currency: 'AUD' }).format(value);

  if (dbLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  const fileTemplates = (fileTemplatesQuery.data ?? []) as FileServiceTemplate[];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Service Templates</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
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
            {dbTemplates?.map((template) => (
              <TableRow key={template.id}>
                <TableCell>{template.id}</TableCell>
                <TableCell>{template.template_name}</TableCell>
                <TableCell>
                  <Chip label={template.service_type} size="small" />
                </TableCell>
                <TableCell>{template.description}</TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleOpenDialog(template)} color="primary">
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDelete(template)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

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

      <Divider sx={{ my: 4 }} />

      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">File Templates (service_templates.json)</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <Tooltip title="Refresh">
            <span>
              <IconButton
                onClick={() => fileTemplatesQuery.refetch()}
                disabled={fileTemplatesQuery.isFetching}
              >
                {fileTemplatesQuery.isFetching ? <CircularProgress size={20} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenFileDialog('create')}
          >
            Add File Template
          </Button>
        </Stack>
      </Stack>

      {fileTemplatesQuery.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(fileTemplatesQuery.error as any)?.message || 'Failed to load file templates'}
        </Alert>
      )}

      {fileTemplatesQuery.isLoading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Sector</TableCell>
                <TableCell>Items</TableCell>
                <TableCell>Reviews</TableCell>
                <TableCell>Estimated Value</TableCell>
                <TableCell>Validity</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {fileTemplates.length > 0 ? (
                fileTemplates.map((template) => (
                  <TableRow key={template.key}>
                    <TableCell>{template.name}</TableCell>
                    <TableCell>{template.sector || 'N/A'}</TableCell>
                    <TableCell>{template.summary.total_items}</TableCell>
                    <TableCell>{template.summary.total_reviews}</TableCell>
                    <TableCell>{formatEstimatedValue(template.summary.estimated_value)}</TableCell>
                    <TableCell>
                      {template.is_valid ? (
                        <Chip label="Valid" color="success" size="small" />
                      ) : (
                        <Tooltip
                          title={
                             template.validation_errors.length
                               ? template.validation_errors.join('\\n')
                               : 'Validation errors detected'
                          }
                        >
                          <Chip label="Needs Review" color="warning" size="small" />
                        </Tooltip>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenFileDialog('edit', template)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Duplicate">
                        <IconButton size="small" onClick={() => handleOpenFileDialog('duplicate', template)}>
                          <DuplicateIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" color="error" onClick={() => handleFileDelete(template)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No file templates found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={fileDialogOpen} onClose={handleCloseFileDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {fileDialogMode === 'edit'
            ? 'Edit File Template'
            : fileDialogMode === 'duplicate'
            ? 'Duplicate File Template'
            : 'Create File Template'}
        </DialogTitle>
        <DialogContent>
          {fileError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setFileError('')}>
              {fileError}
            </Alert>
          )}
          <Stack spacing={2} mt={1}>
            <TextField
              label="Template Name"
              value={fileFormData.name}
              onChange={(e) => setFileFormData((prev) => ({ ...prev, name: e.target.value }))}
              required
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Sector"
                value={fileFormData.sector}
                onChange={(e) => setFileFormData((prev) => ({ ...prev, sector: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Notes / Description"
                value={fileFormData.notes}
                onChange={(e) => setFileFormData((prev) => ({ ...prev, notes: e.target.value }))}
                fullWidth
              />
            </Stack>
            <TextField
              label="Items (JSON Array)"
              value={fileFormData.itemsJson}
              onChange={(e) => setFileFormData((prev) => ({ ...prev, itemsJson: e.target.value }))}
              multiline
              minRows={10}
              helperText="Provide service items as a JSON array."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseFileDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleFileSubmit}
            disabled={fileSaveMutation.isPending}
          >
            {fileSaveMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ServiceTemplatesTab;
