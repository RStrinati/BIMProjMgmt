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
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectAliasesApi } from '../../api/projectAliases';
import { projectsApi } from '../../api/projects';
import type {
  Project,
  ProjectAlias,
  ProjectAliasStats,
  ProjectAliasValidationResult,
  UnmappedProjectAlias,
} from '../../types/api';

const ProjectAliasesTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [validationDialogOpen, setValidationDialogOpen] = useState(false);
  const [editingAlias, setEditingAlias] = useState<ProjectAlias | null>(null);
  const [formData, setFormData] = useState({
    alias_name: '',
    project_id: '',
  });
  const [error, setError] = useState('');

  const {
    data: aliases,
    isLoading: aliasesLoading,
    isFetching: aliasesFetching,
    refetch: refetchAliases,
  } = useQuery<ProjectAlias[]>({
    queryKey: ['projectAliases'],
    queryFn: projectAliasesApi.getAll,
  });

  const {
    data: projects,
    refetch: refetchProjects,
  } = useQuery<Project[]>({
    queryKey: ['projectAliases', 'projects'],
    queryFn: () => projectsApi.getAll(),
  });
  const {
    data: aliasStats,
    isFetching: statsFetching,
    refetch: refetchAliasStats,
  } = useQuery<ProjectAliasStats[]>({
    queryKey: ['projectAliases', 'stats'],
    queryFn: projectAliasesApi.getStats,
  });
  const {
    data: unmapped,
    isFetching: unmappedFetching,
    refetch: refetchUnmapped,
  } = useQuery<UnmappedProjectAlias[]>({
    queryKey: ['projectAliases', 'unmapped'],
    queryFn: projectAliasesApi.getUnmapped,
  });
  const {
    data: validation,
    isFetching: validationFetching,
    refetch: refetchValidation,
  } = useQuery<ProjectAliasValidationResult>({
    queryKey: ['projectAliases', 'validation'],
    queryFn: projectAliasesApi.getValidation,
  });

  const projectOptions = useMemo(
    () =>
      (projects ?? []).map((project) => ({
        value: project.project_id,
        label: `${project.project_id} - ${project.project_name}`,
      })),
    [projects],
  );

  const invalidateAliasQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['projectAliases'] });
    queryClient.invalidateQueries({ queryKey: ['projectAliases', 'stats'] });
    queryClient.invalidateQueries({ queryKey: ['projectAliases', 'unmapped'] });
    queryClient.invalidateQueries({ queryKey: ['projectAliases', 'validation'] });
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingAlias(null);
    setFormData({ alias_name: '', project_id: '' });
    setError('');
  };

  const openDialog = (
    alias?: ProjectAlias,
    defaults?: { alias_name?: string; project_id?: string },
  ) => {
    if (alias) {
      setEditingAlias(alias);
      setFormData({
        alias_name: alias.alias_name,
        project_id: String(alias.project_id),
      });
    } else {
      setEditingAlias(null);
      setFormData({
        alias_name: defaults?.alias_name ?? '',
        project_id: defaults?.project_id ?? '',
      });
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
          project_id:
            projectId !== editingAlias.project_id ? projectId : undefined,
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
  const totalAliases = aliases?.length ?? 0;
  const totalIssues = aliasStats?.reduce((sum, stat) => sum + stat.total_issues, 0) ?? 0;
  const totalOrphaned = validation?.orphaned_aliases.length ?? 0;
  const totalDuplicates = validation?.duplicate_aliases.length ?? 0;
  const totalUnusedProjects = validation?.unused_projects.length ?? 0;

  const handleRefreshAll = () => {
    refetchAliases();
    refetchProjects();
    refetchAliasStats();
    refetchUnmapped();
    refetchValidation();
  };

  const openCreateFromUnmapped = (item: UnmappedProjectAlias) => {
    const suggestedProjectName = item.suggested_match?.project_name ?? '';
    const matchedProjectId = projects?.find(
      (project) =>
        project.project_name?.trim().toLowerCase() === suggestedProjectName.trim().toLowerCase(),
    )?.project_id;

    openDialog(undefined, {
      alias_name: item.project_name,
      project_id: matchedProjectId ? String(matchedProjectId) : '',
    });
  };

  if (aliasesLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} mb={2}>
        <Alert severity="info" sx={{ flex: 1 }}>
          Tracking <strong>{totalAliases}</strong> aliases with <strong>{totalIssues}</strong> total issues.
        </Alert>
        {validation && (
          <Alert
            severity={totalOrphaned > 0 || totalDuplicates > 0 ? 'warning' : 'success'}
            sx={{ flex: 1 }}
          >
            {totalOrphaned > 0 || totalDuplicates > 0 || totalUnusedProjects > 0 ? (
              <>
                Validation found{' '}
                <strong>{totalOrphaned + totalDuplicates + totalUnusedProjects}</strong>{' '}
                potential issues.
              </>
            ) : (
              'All aliases passed validation checks.'
            )}{' '}
            <Button
              size="small"
              onClick={() => setValidationDialogOpen(true)}
              sx={{ ml: 2 }}
              variant="outlined"
            >
              View details
            </Button>
          </Alert>
        )}
      </Stack>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} mb={2}>
        {unmapped && unmapped.length > 0 && (
          <Alert severity="info" sx={{ flex: 1 }}>
            {unmapped.slice(0, 3).map((item) => item.project_name).join(', ')}
            {unmapped.length > 3 ? ` and ${unmapped.length - 3} more` : ''} projects have issues with no aliases.
          </Alert>
        )}
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefreshAll}
          disabled={aliasesFetching || statsFetching || unmappedFetching || validationFetching}
        >
          {aliasesFetching || statsFetching || unmappedFetching || validationFetching ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Stack>

      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Project Aliases</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => openDialog()}>
          Add Alias
        </Button>
      </Stack>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Alias</TableCell>
              <TableCell>Project</TableCell>
              <TableCell>Issues</TableCell>
              <TableCell>Open</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {aliases?.map((alias) => (
              <TableRow key={alias.alias_name}>
                <TableCell>{alias.alias_name}</TableCell>
                <TableCell>
                  <Stack spacing={0.5}>
                    <Typography variant="body2">{alias.project_name ?? 'Unknown'}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {alias.project_id}
                    </Typography>
                  </Stack>
                </TableCell>
                <TableCell>{alias.issue_summary.total_issues}</TableCell>
                <TableCell>{alias.issue_summary.open_issues}</TableCell>
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
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={4}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Alias Usage Summary</Typography>
        </Stack>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Project</TableCell>
                <TableCell>Alias Count</TableCell>
                <TableCell>Aliases</TableCell>
                <TableCell>Total Issues</TableCell>
                <TableCell>Open Issues</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {aliasStats?.map((stat) => (
                <TableRow key={stat.project_id}>
                  <TableCell>{stat.project_name}</TableCell>
                  <TableCell>{stat.alias_count}</TableCell>
                  <TableCell>{stat.aliases || 'None'}</TableCell>
                  <TableCell>{stat.total_issues}</TableCell>
                  <TableCell>{stat.open_issues}</TableCell>
                </TableRow>
              ))}
              {!aliasStats?.length && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Typography variant="body2" color="text.secondary" align="center">
                      No usage statistics available.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <Box mt={4}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Unmapped Project Names</Typography>
        </Stack>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Unmapped Name</TableCell>
                <TableCell>Total Issues</TableCell>
                <TableCell>Open Issues</TableCell>
                <TableCell>Sources</TableCell>
                <TableCell>Suggested Match</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {unmapped?.map((item) => (
                <TableRow key={item.project_name}>
                  <TableCell>{item.project_name}</TableCell>
                  <TableCell>{item.total_issues}</TableCell>
                  <TableCell>{item.open_issues}</TableCell>
                  <TableCell>{item.sources}</TableCell>
                  <TableCell>
                    {item.suggested_match
                      ? `${item.suggested_match.project_name} (${item.suggested_match.match_type}${
                          typeof item.suggested_match.confidence === 'number'
                            ? `, ${(item.suggested_match.confidence * 100).toFixed(0)}%`
                            : ''
                        })`
                      : 'No suggestion'}
                  </TableCell>
                  <TableCell align="right">
                    <Button size="small" variant="outlined" onClick={() => openCreateFromUnmapped(item)}>
                      Create Alias
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!unmapped?.length && (
                <TableRow>
                  <TableCell colSpan={6}>
                    <Typography variant="body2" color="text.secondary" align="center">
                      No unmapped project names detected.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

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
            />
            <TextField
              select
              label="Project"
              value={formData.project_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, project_id: e.target.value }))}
              required
              helperText="Select the project the alias should map to."
            >
              {projectOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
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

      <Dialog
        open={validationDialogOpen}
        onClose={() => setValidationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Alias Validation Details</DialogTitle>
        <DialogContent dividers>
          {!validation ? (
            <Typography variant="body2" color="text.secondary">
              Validation data is not available. Please refresh to fetch the latest results.
            </Typography>
          ) : (
            <Stack spacing={3} mt={1}>
              <Box>
                <Typography variant="subtitle1">Summary</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total aliases: {validation.total_aliases}  |  Projects with aliases: {validation.total_projects_with_aliases}
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle1">Orphaned Aliases</Typography>
                {validation.orphaned_aliases.length ? (
                  <Stack component="ul" sx={{ pl: 3 }} spacing={1}>
                    {validation.orphaned_aliases.map((item) => (
                      <Typography component="li" key={item.alias_name}>
                        {item.alias_name} {'->'} Project ID {item.invalid_project_id}
                      </Typography>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No orphaned aliases detected.
                  </Typography>
                )}
              </Box>
              <Box>
                <Typography variant="subtitle1">Duplicate Aliases</Typography>
                {validation.duplicate_aliases.length ? (
                  <Stack component="ul" sx={{ pl: 3 }} spacing={1}>
                    {validation.duplicate_aliases.map((item) => (
                      <Typography component="li" key={item.alias_name}>
                        {item.alias_name} appears {item.count} times
                      </Typography>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No duplicate aliases detected.
                  </Typography>
                )}
              </Box>
              <Box>
                <Typography variant="subtitle1">Unused Projects</Typography>
                {validation.unused_projects.length ? (
                  <Stack component="ul" sx={{ pl: 3 }} spacing={1}>
                    {validation.unused_projects.map((item) => (
                      <Typography component="li" key={item.project_id}>
                        {item.project_id}: {item.project_name}
                      </Typography>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    All projects have aliases.
                  </Typography>
                )}
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setValidationDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectAliasesTab;


