import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
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
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectAliasesApi } from '../../api/projectAliases';
import { projectsApi } from '../../api/projects';
import type { Project, ProjectAlias } from '../../types/api';

const ProjectAliasesTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAlias, setEditingAlias] = useState<ProjectAlias | null>(null);
  const [formData, setFormData] = useState({
    alias_name: '',
    project_id: '',
  });
  const [filterText, setFilterText] = useState('');
  const [error, setError] = useState('');

  const {
    data: aliases,
    isLoading: aliasesLoading,
    error: aliasesError,
    refetch: refetchAliases,
  } = useQuery({
    queryKey: ['projectAliases'],
    queryFn: projectAliasesApi.getAll,
  });

  const {
    data: projects,
    isLoading: projectsLoading,
  } = useQuery<Project[]>({
    queryKey: ['projectAliases', 'projects'],
    queryFn: () => projectsApi.getAll(),
    enabled: dialogOpen,
  });

  const projectOptions = useMemo(
    () =>
      (projects ?? []).map((project) => ({
        value: project.project_id,
        label: `${project.project_name} (ID: ${project.project_id})`,
      })),
    [projects],
  );

  const filteredAliases = useMemo(() => {
    if (!aliases) return [];
    const needle = filterText.trim().toLowerCase();
    if (!needle) return aliases;
    return aliases.filter((alias) => {
      const aliasName = (alias.alias_name ?? '').toLowerCase();
      const projectName = (alias.project_name ?? '').toLowerCase();
      return aliasName.includes(needle) || projectName.includes(needle);
    });
  }, [aliases, filterText]);

  const invalidateAliasQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['projectAliases'] });
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingAlias(null);
    setFormData({ alias_name: '', project_id: '' });
    setError('');
  };

  const openDialog = (alias?: ProjectAlias) => {
    if (alias) {
      setEditingAlias(alias);
      setFormData({
        alias_name: alias.alias_name,
        project_id: String(alias.project_id),
      });
    } else {
      setEditingAlias(null);
      setFormData({ alias_name: '', project_id: '' });
    }
    setError('');
    setDialogOpen(true);
  };

  const createMutation = useMutation<ProjectAlias, Error, { alias_name: string; project_id: number }>({
    mutationFn: projectAliasesApi.create,
    onSuccess: () => {
      invalidateAliasQueries();
      closeDialog();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to create alias');
    },
  });

  const updateMutation = useMutation<
    ProjectAlias,
    Error,
    { aliasName: string; payload: { alias_name?: string; project_id?: number } }
  >({
    mutationFn: ({
      aliasName,
      payload,
    }: {
      aliasName: string;
      payload: { alias_name?: string; project_id?: number };
    }) => projectAliasesApi.update(aliasName, payload),
    onSuccess: () => {
      invalidateAliasQueries();
      closeDialog();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to update alias');
    },
  });

  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: projectAliasesApi.delete,
    onSuccess: () => {
      invalidateAliasQueries();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to delete alias');
    },
  });

  const handleSubmit = () => {
    if (!formData.alias_name.trim()) {
      setError('Alias name is required');
      return;
    }
    if (!formData.project_id) {
      setError('Project selection is required');
      return;
    }

    const projectId = Number(formData.project_id);
    if (Number.isNaN(projectId)) {
      setError('Invalid project selection');
      return;
    }

    if (editingAlias) {
      updateMutation.mutate({
        aliasName: editingAlias.alias_name,
        payload: {
          alias_name:
            formData.alias_name.trim() !== editingAlias.alias_name
              ? formData.alias_name.trim()
              : undefined,
          project_id: projectId !== editingAlias.project_id ? projectId : undefined,
        },
      });
    } else {
      createMutation.mutate({
        alias_name: formData.alias_name.trim(),
        project_id: projectId,
      });
    }
  };

  const handleDelete = (alias: ProjectAlias) => {
    if (window.confirm(`Delete alias "${alias.alias_name}"?`)) {
      deleteMutation.mutate(alias.alias_name);
    }
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" mb={2} alignItems="center">
        <Stack spacing={1}>
          <Typography variant="h6">Project Aliases ({filteredAliases.length})</Typography>
          <TextField
            size="small"
            placeholder="Filter aliases or project names"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            sx={{ minWidth: 260 }}
          />
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Button variant="outlined" onClick={() => refetchAliases()}>
            Refresh
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => openDialog()}>
            Add Alias
          </Button>
        </Stack>
      </Stack>

      {aliasesLoading && (
        <Box display="flex" alignItems="center" justifyContent="center" minHeight="200px">
          <CircularProgress size={24} />
          <Typography ml={2}>Loading aliases...</Typography>
        </Box>
      )}

      {aliasesError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load aliases: {aliasesError.message || 'Unknown error'}
        </Alert>
      )}

      {!aliasesLoading && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Alias Name</TableCell>
                <TableCell>Mapped Project</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAliases.map((alias) => (
                <TableRow key={alias.alias_name}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {alias.alias_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">{alias.project_name ?? 'Unknown'}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {alias.project_id}
                      </Typography>
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => openDialog(alias)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(alias)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {!filteredAliases.length && !aliasesLoading && (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No aliases match the current filter.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingAlias ? 'Edit Alias' : 'Add Alias'}</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}
          <Stack spacing={2} mt={1}>
            <TextField
              label="Alias Name"
              value={formData.alias_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, alias_name: e.target.value }))}
              required
              fullWidth
            />
            <FormControl fullWidth required>
              <InputLabel id="alias-project-label">Project</InputLabel>
              <Select
                labelId="alias-project-label"
                label="Project"
                value={formData.project_id}
                onChange={(e) => setFormData((prev) => ({ ...prev, project_id: e.target.value }))}
              >
                <MenuItem value="" disabled>
                  {projectsLoading ? 'Loading projects...' : 'Select a project'}
                </MenuItem>
                {projectOptions.map((option) => (
                  <MenuItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectAliasesTab;
