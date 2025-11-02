import React, { useMemo, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  AlertTitle,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  AutoFixHigh as AutoFixHighIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Sort as SortIcon,
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
      id={`alias-tabpanel-${index}`}
      aria-labelledby={`alias-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectAliasesTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [analyzeDialogOpen, setAnalyzeDialogOpen] = useState(false);
  const [autoMapDialogOpen, setAutoMapDialogOpen] = useState(false);
  const [editingAlias, setEditingAlias] = useState<ProjectAlias | null>(null);
  const [formData, setFormData] = useState({
    alias_name: '',
    project_id: '',
  });
  const [error, setError] = useState('');
  const [autoMapMinConfidence, setAutoMapMinConfidence] = useState(85);
  const [autoMapResults, setAutoMapResults] = useState<any>(null);
  const [sortByConfidence, setSortByConfidence] = useState(false);
  const [quickAssignMap, setQuickAssignMap] = useState<Record<string, number>>({});

  // INSTANT LOAD: Just get summary counts
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['projectAliases', 'summary'],
    queryFn: projectAliasesApi.getSummary,
    staleTime: 30000, // Cache for 30 seconds
    retry: 1, // Only retry once
  });

  // LAZY LOAD: Only fetch when needed
  const {
    data: aliases,
    isFetching: aliasesFetching,
    error: aliasesError,
    refetch: refetchAliases,
  } = useQuery({
    queryKey: ['projectAliases'],
    queryFn: projectAliasesApi.getAll,
    enabled: tabValue === 0, // Only load when on aliases tab
  });

  const {
    data: projects,
  } = useQuery<Project[]>({
    queryKey: ['projectAliases', 'projects'],
    queryFn: () => projectsApi.getAll(),
    enabled: dialogOpen || tabValue === 0 || tabValue === 1, // Only when needed for aliases or unmapped tabs
  });

  const {
    data: aliasStats,
    isFetching: statsFetching,
    refetch: refetchAliasStats,
  } = useQuery<ProjectAliasStats[]>({
    queryKey: ['projectAliases', 'stats'],
    queryFn: projectAliasesApi.getStats,
    enabled: tabValue === 2, // Only on stats tab
  });

  const {
    data: unmapped,
    isFetching: unmappedFetching,
    refetch: refetchUnmapped,
  } = useQuery<UnmappedProjectAlias[]>({
    queryKey: ['projectAliases', 'unmapped'],
    queryFn: projectAliasesApi.getUnmapped,
    enabled: tabValue === 1, // Only on unmapped tab
  });

  const {
    data: validation,
    isFetching: validationFetching,
    refetch: refetchValidation,
  } = useQuery<ProjectAliasValidationResult>({
    queryKey: ['projectAliases', 'validation'],
    queryFn: projectAliasesApi.getValidation,
    enabled: tabValue === 3, // Only on validation tab
  });

  // Run analysis mutation
  const analyzeMutation = useMutation({
    mutationFn: projectAliasesApi.analyze,
    onSuccess: (data) => {
      setAnalyzeDialogOpen(true);
      setAutoMapResults(data);
    },
  });

  const projectOptions = useMemo(
    () =>
      (projects ?? []).map((project) => ({
        value: project.project_id,
        label: `${project.project_name}`,
        id: project.project_id,
      })),
    [projects],
  );

  const invalidateAliasQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['projectAliases'] });
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

  const autoMapMutation = useMutation({
    mutationFn: async (params: { min_confidence: number; dry_run: boolean }) => {
      const response = await projectAliasesApi.autoMap(params);
      return response;
    },
    onSuccess: (data) => {
      setAutoMapResults(data);
      if (!data.summary.dry_run) {
        invalidateAliasQueries();
      }
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Auto-mapping failed');
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

  const handleAutoMapPreview = () => {
    setAutoMapResults(null);
    autoMapMutation.mutate({
      min_confidence: autoMapMinConfidence / 100,
      dry_run: true,
    });
  };

  const handleAutoMapExecute = () => {
    autoMapMutation.mutate({
      min_confidence: autoMapMinConfidence / 100,
      dry_run: false,
    });
  };

  const handleQuickAssign = (aliasName: string, projectId: number) => {
    createMutation.mutate({
      alias_name: aliasName,
      project_id: projectId,
    });
  };

  const getConfidenceColor = (confidence: number): 'success' | 'warning' | 'default' => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.75) return 'warning';
    return 'default';
  };

  const sortedUnmapped = useMemo(() => {
    if (!unmapped || !sortByConfidence) return unmapped;
    
    return [...unmapped].sort((a, b) => {
      const confA = a.suggested_match?.confidence ?? 0;
      const confB = b.suggested_match?.confidence ?? 0;
      return confB - confA;
    });
  }, [unmapped, sortByConfidence]);

  const highConfidenceCount = useMemo(() => {
    if (!unmapped) return 0;
    return unmapped.filter(u => (u.suggested_match?.confidence ?? 0) >= autoMapMinConfidence / 100).length;
  }, [unmapped, autoMapMinConfidence]);

  const totalAliases = summary?.total_aliases ?? 0;
  const totalProjects = summary?.total_projects ?? 0;

  if (summaryLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography ml={2}>Loading aliases...</Typography>
      </Box>
    );
  }

  if (summaryError) {
    return (
      <Box p={3}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <AlertTitle>Backend Connection Error</AlertTitle>
          Unable to connect to the backend server. Please ensure the Flask server is running on port 5000.
          <br />
          <strong>Error:</strong> {summaryError.message}
        </Alert>
        <Button variant="outlined" onClick={() => refetchSummary()}>
          Retry Connection
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Summary Header - Instant Load */}
      <Paper sx={{ p: 2, mb: 2 }}>
        {summaryError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load summary: {(summaryError as Error)?.message || 'Unknown error'}
          </Alert>
        )}
        {summaryLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <Stack direction="row" spacing={4} alignItems="center">
          <Box>
            <Typography variant="h6">{totalAliases}</Typography>
            <Typography variant="caption" color="text.secondary">Total Aliases</Typography>
          </Box>
          <Box>
            <Typography variant="h6">{summary?.projects_with_aliases ?? 0}</Typography>
            <Typography variant="caption" color="text.secondary">Projects Mapped</Typography>
          </Box>
          <Box>
            <Typography variant="h6">{totalProjects - (summary?.projects_with_aliases ?? 0)}</Typography>
            <Typography variant="caption" color="text.secondary">Unmapped Projects</Typography>
          </Box>
          <Box flex={1} />
          <Button
            variant="contained"
            startIcon={analyzeMutation.isPending ? <CircularProgress size={20} /> : <PlayArrowIcon />}
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
          >
            Run Analysis
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              refetchSummary();
              if (tabValue === 0) refetchAliases();
              if (tabValue === 1) refetchUnmapped();
              if (tabValue === 2) refetchAliasStats();
              if (tabValue === 3) refetchValidation();
            }}
          >
            Refresh
          </Button>
        </Stack>
      </Paper>

      {/* Tabbed Interface - Lazy Loading */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Existing Aliases" />
          <Tab label="Unmapped Projects" />
          <Tab label="Usage Statistics" />
          <Tab label="Validation" />
        </Tabs>
      </Box>

      {/* Tab 0: Existing Aliases */}
      <TabPanel value={tabValue} index={0}>
        <Stack direction="row" justifyContent="space-between" mb={2}>
          <Typography variant="h6">Configured Aliases ({aliases?.length ?? 0})</Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => openDialog()}>
            Add Alias
          </Button>
        </Stack>

        {aliasesError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load aliases: {aliasesError.message || 'Unknown error'}
          </Alert>
        )}

        {aliasesFetching && <LinearProgress />}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Alias Name</TableCell>
                <TableCell>Mapped Project</TableCell>
                <TableCell>Total Issues</TableCell>
                <TableCell>Open Issues</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {aliases?.map((alias) => (
                <TableRow key={alias.alias_name}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">{alias.alias_name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">{alias.project_name ?? 'Unknown'}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {alias.project_id}
                      </Typography>
                    </Stack>
                  </TableCell>
                  <TableCell>{alias.issue_summary?.total_issues ?? 0}</TableCell>
                  <TableCell>{alias.issue_summary?.open_issues ?? 0}</TableCell>
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
              {!aliases?.length && !aliasesFetching && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No aliases configured yet. Click "Add Alias" to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Tab 1: Unmapped Projects - WITH QUICK ASSIGN */}
      <TabPanel value={tabValue} index={1}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Unmapped Projects ({sortedUnmapped?.length ?? 0})</Typography>
          <Stack direction="row" spacing={1}>
            {highConfidenceCount > 0 && (
              <Button
                variant="contained"
                color="success"
                startIcon={<AutoFixHighIcon />}
                onClick={() => setAutoMapDialogOpen(true)}
              >
                Auto-Map {highConfidenceCount}
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={sortByConfidence ? <SortIcon color="primary" /> : <SortIcon />}
              onClick={() => setSortByConfidence(!sortByConfidence)}
            >
              {sortByConfidence ? 'Sorted' : 'Sort'} by Confidence
            </Button>
          </Stack>
        </Stack>

        {unmappedFetching && <LinearProgress />}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>File/Project Name</TableCell>
                <TableCell>Issues</TableCell>
                <TableCell>Suggested Match</TableCell>
                <TableCell width="350">Quick Assign to Project</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedUnmapped?.map((item) => (
                <TableRow key={item.project_name}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">{item.project_name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {item.sources} source(s)
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">{item.total_issues} total</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.open_issues} open
                      </Typography>
                    </Stack>
                  </TableCell>
                  <TableCell>
                    {item.suggested_match ? (
                      <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap">
                        <Chip
                          label={`${(item.suggested_match.confidence * 100).toFixed(0)}%`}
                          size="small"
                          color={getConfidenceColor(item.suggested_match.confidence)}
                        />
                        <Typography variant="body2" noWrap maxWidth="200px">
                          {item.suggested_match.project_name}
                        </Typography>
                        <Chip
                          label={item.suggested_match.match_type}
                          size="small"
                          variant="outlined"
                        />
                      </Stack>
                    ) : (
                      <Typography variant="caption" color="text.secondary">No suggestion</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Autocomplete
                      size="small"
                      options={projectOptions}
                      getOptionLabel={(option) => option.label}
                      defaultValue={
                        item.suggested_match
                          ? projectOptions.find(p => p.label === item.suggested_match!.project_name)
                          : undefined
                      }
                      onChange={(_, value) => {
                        if (value) {
                          setQuickAssignMap(prev => ({
                            ...prev,
                            [item.project_name]: value.id
                          }));
                        }
                      }}
                      renderInput={(params) => (
                        <TextField {...params} placeholder="Select project..." />
                      )}
                      sx={{ minWidth: 250 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<SaveIcon />}
                      disabled={!quickAssignMap[item.project_name]}
                      onClick={() => {
                        const projectId = quickAssignMap[item.project_name];
                        if (projectId) {
                          handleQuickAssign(item.project_name, projectId);
                        }
                      }}
                    >
                      Assign
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!sortedUnmapped?.length && !unmappedFetching && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      ✅ All projects are mapped!
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Tab 2: Usage Statistics */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" mb={2}>Alias Usage by Project</Typography>
        {statsFetching && <LinearProgress />}
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
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Tab 3: Validation */}
      <TabPanel value={tabValue} index={3}>
        <Typography variant="h6" mb={2}>Validation Results</Typography>
        {validationFetching && <LinearProgress />}
        {validation && (
          <Stack spacing={2}>
            <Alert severity={validation.orphaned_aliases?.length ? 'warning' : 'success'}>
              {validation.orphaned_aliases?.length
                ? `Found ${validation.orphaned_aliases.length} orphaned aliases`
                : 'All aliases are valid'}
            </Alert>
            {validation.orphaned_aliases?.length > 0 && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Orphaned Aliases ({validation.orphaned_aliases.length})</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {validation.orphaned_aliases.map((item: any) => (
                      <ListItem key={item.alias_name}>
                        <ListItemText
                          primary={item.alias_name}
                          secondary={`Invalid project ID: ${item.invalid_project_id}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}
          </Stack>
        )}
      </TabPanel>

      {/* Dialogs remain the same but simplified... */}
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
            <Autocomplete
              options={projectOptions}
              getOptionLabel={(option) => option.label}
              value={projectOptions.find(p => p.value === Number(formData.project_id)) || null}
              onChange={(_, value) => {
                setFormData((prev) => ({ ...prev, project_id: value ? String(value.value) : '' }));
              }}
              renderInput={(params) => (
                <TextField {...params} label="Project" required helperText="Select the project to map to" />
              )}
            />
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

      {/* Analysis Results Dialog */}
      <Dialog open={analyzeDialogOpen} onClose={() => setAnalyzeDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Enhanced Matching Analysis Results</DialogTitle>
        <DialogContent>
          {autoMapResults && (
            <Stack spacing={3}>
              <Alert severity="info">
                Analysis complete! Found {autoMapResults.summary?.total_unmapped ?? 0} unmapped projects.
              </Alert>
              
              <Stack direction="row" spacing={2}>
                <Chip label={`🟢 High: ${autoMapResults.summary?.high_confidence ?? 0}`} color="success" />
                <Chip label={`🟡 Medium: ${autoMapResults.summary?.medium_confidence ?? 0}`} color="warning" />
                <Chip label={`🔴 Low: ${autoMapResults.summary?.low_confidence ?? 0}`} />
                <Chip label={`⚪ None: ${autoMapResults.summary?.no_suggestion ?? 0}`} />
              </Stack>

              {autoMapResults.recommendations?.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>Top Recommendations:</Typography>
                  <List dense>
                    {autoMapResults.recommendations.slice(0, 5).map((rec: any) => (
                      <ListItem key={rec.alias_name}>
                        <ListItemText
                          primary={`${rec.alias_name} → ${rec.suggested_project}`}
                          secondary={`${(rec.confidence * 100).toFixed(0)}% confidence (${rec.match_type}) • ${rec.total_issues} issues`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalyzeDialogOpen(false)}>Close</Button>
          {autoMapResults?.summary?.high_confidence > 0 && (
            <Button
              variant="contained"
              onClick={() => {
                setAnalyzeDialogOpen(false);
                setAutoMapDialogOpen(true);
              }}
            >
              Proceed to Auto-Map
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Auto-map dialog */}
      <Dialog open={autoMapDialogOpen} onClose={() => setAutoMapDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Automatic Alias Mapping</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will create aliases for unmapped projects with high-confidence matches.
            Preview the results before committing.
          </Alert>
          
          <TextField
            label="Minimum Confidence (%)"
            type="number"
            value={autoMapMinConfidence}
            onChange={(e) => setAutoMapMinConfidence(Number(e.target.value))}
            inputProps={{ min: 0, max: 100, step: 5 }}
            fullWidth
            sx={{ mb: 2 }}
            helperText={`Will map ${highConfidenceCount} projects at ${autoMapMinConfidence}% threshold`}
          />
          
          {autoMapResults && (
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                {autoMapResults.summary.dry_run ? 'Preview Results:' : 'Execution Results:'}
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary={`✅ Created: ${autoMapResults.summary.successfully_mapped}`}
                    secondary={autoMapResults.created.slice(0, 5).map((c: any) => 
                      `${c.alias_name} → ${c.project_name} (${(c.confidence * 100).toFixed(0)}%)`
                    ).join(', ')}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary={`⏭️ Skipped: ${autoMapResults.skipped.length}`}
                    secondary={`Low confidence or no suggestions`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary={`❌ Errors: ${autoMapResults.errors.length}`}
                    secondary={autoMapResults.errors.length > 0 ? autoMapResults.errors[0].error : 'None'}
                  />
                </ListItem>
              </List>
              
              {autoMapResults.summary.dry_run && autoMapResults.summary.successfully_mapped > 0 && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Preview looks good! Click "Execute Mapping" to create these aliases.
                </Alert>
              )}
              
              {!autoMapResults.summary.dry_run && autoMapResults.summary.successfully_mapped > 0 && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Successfully created {autoMapResults.summary.successfully_mapped} aliases!
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAutoMapDialogOpen(false)}>Close</Button>
          {!autoMapResults || autoMapResults.summary.dry_run ? (
            <>
              <Button
                variant="outlined"
                onClick={handleAutoMapPreview}
                disabled={autoMapMutation.isPending}
              >
                {autoMapMutation.isPending ? 'Processing...' : 'Preview'}
              </Button>
              <Button
                variant="contained"
                onClick={handleAutoMapExecute}
                disabled={autoMapMutation.isPending || highConfidenceCount === 0}
              >
                Execute Mapping
              </Button>
            </>
          ) : (
            <Button variant="contained" onClick={() => {
              setAutoMapDialogOpen(false);
              setAutoMapResults(null);
            }}>
              Done
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectAliasesTab;
