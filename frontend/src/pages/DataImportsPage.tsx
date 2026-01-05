/**
 * Data Imports Page
 * Main page with tabs for all data import features
 * Includes project selector for filtering data by project
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Breadcrumbs,
  Link,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  Grid,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CloudDownload as CloudDownloadIcon,
  Upload as UploadIcon,
  AccountTree as ReviztoIcon,
  HealthAndSafety as HealthIcon,
  FolderOpen as ProjectIcon,
  SyncAlt as SyncIcon,
} from '@mui/icons-material';
import { projectsApi } from '@/api/projects';
import { ACCConnectorPanel } from '@/components/dataImports/ACCConnectorPanel';
import { ACCDataImportPanel } from '@/components/dataImports/ACCDataImportPanel';
import { ReviztoImportPanel } from '@/components/dataImports/ReviztoImportPanel';
import { RevitHealthPanel } from '@/components/dataImports/RevitHealthPanel';
import { ACCSyncPanel } from '@/components/dataImports/ACCSyncPanel';
import type { Project } from '@/types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

type RunStatus = 'success' | 'error' | 'running';
type RunHistory = {
  id: string;
  projectId: number | null;
  source: string;
  status: RunStatus;
  startedAt: string;
  duration?: string;
  notes?: string;
};

const DataImportsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(() => {
    const stored = localStorage.getItem('data_import_selected_project');
    if (!stored) return null;
    const parsed = Number(stored);
    return Number.isFinite(parsed) ? parsed : null;
  });
  const tabLabels = ['ACC Sync', 'ACC Desktop Connector', 'ACC Data Import', 'Revizto Extraction', 'Revit Health Check'];
  const [runHistory, setRunHistory] = useState<RunHistory[]>(() => {
    try {
      const stored = localStorage.getItem('data_import_run_history');
      return stored ? (JSON.parse(stored) as RunHistory[]) : [];
    } catch {
      return [];
    }
  });

  // Use URL project ID if available, otherwise use selected project ID
  const effectiveProjectId = id ? Number(id) : selectedProjectId;

  // Fetch all projects for the dropdown
  const {
    data: allProjects,
    isLoading: projectsLoading,
  } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch specific project details if ID is provided
  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
  } = useQuery<Project>({
    queryKey: ['project', effectiveProjectId],
    queryFn: () => projectsApi.getById(effectiveProjectId!),
    enabled: !!effectiveProjectId,
  });

  // Set default project if coming from URL
  useEffect(() => {
    if (id) {
      setSelectedProjectId(Number(id));
      localStorage.setItem('data_import_selected_project', id);
    }
  }, [id]);

  useEffect(() => {
    if (selectedProjectId !== null && !Number.isNaN(selectedProjectId)) {
      localStorage.setItem('data_import_selected_project', String(selectedProjectId));
    }
  }, [selectedProjectId]);

  useEffect(() => {
    localStorage.setItem('data_import_run_history', JSON.stringify(runHistory));
  }, [runHistory]);

  const recordRun = (status: RunStatus) => {
    const now = new Date();
    const newRun: RunHistory = {
      id: `${now.getTime()}-${Math.random().toString(16).slice(2, 6)}`,
      projectId: effectiveProjectId ?? null,
      source: tabLabels[tabValue] || 'Data Import',
      status,
      startedAt: now.toISOString(),
            duration: status === 'running' ? undefined : '--',
      notes: project ? `Logged for ${project.project_name}` : undefined,
    };
    setRunHistory((prev) => [newRun, ...prev].slice(0, 25));
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleProjectChange = (event: SelectChangeEvent<number>) => {
    const newProjectId = Number(event.target.value);
    setSelectedProjectId(newProjectId);
    // Update URL to reflect selected project
    navigate(`/projects/${newProjectId}/data-imports`);
  };

  if (effectiveProjectId && projectLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (effectiveProjectId && (projectError || !project)) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load project details. {projectError instanceof Error ? projectError.message : ''}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mt: 2 }}>
          Back to Projects
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header with Breadcrumbs */}
      <Box sx={{ p: 3, pb: 0 }}>
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/')}
            sx={{ cursor: 'pointer', textDecoration: 'none' }}
          >
            Dashboard
          </Link>
          {effectiveProjectId && project && (
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate('/projects')}
              sx={{ cursor: 'pointer', textDecoration: 'none' }}
            >
              Projects
            </Link>
          )}
          {effectiveProjectId && project && (
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate(`/projects/${effectiveProjectId}`)}
              sx={{ cursor: 'pointer', textDecoration: 'none' }}
            >
              {project.project_name}
            </Link>
          )}
          <Typography color="text.primary">Data Imports</Typography>
        </Breadcrumbs>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Data Imports
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {project
                ? `Import and manage data for ${project.project_name}`
                : 'Select a project to import and manage data'}
            </Typography>
          </Box>
          {effectiveProjectId && (
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(`/projects/${effectiveProjectId}`)}
              variant="outlined"
            >
              Back to Project
            </Button>
          )}
        </Box>

        {/* Project Selector */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <FormControl sx={{ minWidth: 300 }} size="small">
              <InputLabel id="project-select-label">Select Project</InputLabel>
              <Select
                labelId="project-select-label"
                id="project-select"
                value={effectiveProjectId || ''}
                label="Select Project"
                onChange={handleProjectChange}
                disabled={projectsLoading}
                startAdornment={<ProjectIcon sx={{ mr: 1, color: 'action.active' }} />}
              >
                {projectsLoading ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Loading projects...
                  </MenuItem>
                ) : (
                  allProjects?.map((proj) => (
                    <MenuItem key={proj.project_id} value={proj.project_id}>
                      {proj.project_number} - {proj.project_name}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>

            {project && (
              <Box display="flex" gap={1} flexWrap="wrap">
                {project.project_type && (
                  <Chip
                    label={project.project_type}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {project.status && (
                  <Chip
                    label={project.status}
                    size="small"
                    color={
                      project.status === 'Active'
                        ? 'success'
                        : project.status === 'Completed'
                        ? 'default'
                        : 'warning'
                    }
                  />
                )}
              </Box>
            )}
          </Box>
        </Paper>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mx: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': { minHeight: 64 },
          }}
        >
          <Tab
            icon={<SyncIcon />}
            iconPosition="start"
            label="ACC Sync"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<CloudDownloadIcon />}
            iconPosition="start"
            label="ACC Desktop Connector"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<UploadIcon />}
            iconPosition="start"
            label="ACC Data Import"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<ReviztoIcon />}
            iconPosition="start"
            label="Revizto Extraction"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<HealthIcon />}
            iconPosition="start"
            label="Revit Health Check"
            sx={{ textTransform: 'none' }}
          />
        </Tabs>

        {/* Tab Panels */}
        {effectiveProjectId ? (
          <>
            <TabPanel value={tabValue} index={0}>
              <ACCSyncPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <ACCConnectorPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <ACCDataImportPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={3}>
              <ReviztoImportPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={4}>
              <RevitHealthPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
          </>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <ProjectIcon sx={{ fontSize: 64, color: 'action.disabled', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Project Selected
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              Please select a project from the dropdown above to view and manage data imports.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You can also navigate to a project from the{' '}
              <Link
                component="button"
                onClick={() => navigate('/projects')}
                sx={{ cursor: 'pointer' }}
              >
                Projects page
              </Link>
              .
            </Typography>
          </Box>
        )}
      </Paper>

      <Grid container spacing={2} sx={{ mx: 3, mt: 3 }}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="h6">Recent Runs</Typography>
              <Box display="flex" gap={1}>
                <Button
                  size="small"
                  variant="contained"
                  disabled={!effectiveProjectId}
                  onClick={() => recordRun('success')}
                >
                  Record run for current tab
                </Button>
                <Button
                  size="small"
                  variant="text"
                  onClick={() => setRunHistory([])}
                >
                  Clear
                </Button>
              </Box>
            </Box>
            {runHistory.length === 0 ? (
              <Alert severity="info">No runs logged yet. Record your first run to keep a trail.</Alert>
            ) : (
              <List dense>
                {runHistory.map((run) => (
                  <React.Fragment key={run.id}>
                    <ListItem
                      secondaryAction={(
                        <Chip
                          label={run.status}
                          color={
                            run.status === 'success'
                              ? 'success'
                              : run.status === 'error'
                              ? 'error'
                              : 'warning'
                          }
                          size="small"
                        />
                      )}
                    >
                      <ListItemText
                        primary={`${run.source} • ${run.projectId ? `Project ${run.projectId}` : 'No project'}`}
                        secondary={`${new Date(run.startedAt).toLocaleString()} ${run.notes ? `— ${run.notes}` : ''}`}
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Guidance & Checks
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Confirm the project scope and data source before syncing." />
              </ListItem>
              <ListItem>
                <ListItemText primary="Run ACC Sync before ACC Data Import to keep models current." />
              </ListItem>
              <ListItem>
                <ListItemText primary="Use Revizto extraction for issue triage, then log the run above." />
              </ListItem>
              <ListItem>
                <ListItemText primary="Track Revit Health Check results weekly to catch model decay." />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DataImportsPage;
