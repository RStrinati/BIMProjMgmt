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
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CloudDownload as CloudDownloadIcon,
  Upload as UploadIcon,
  BugReport as IssueIcon,
  AccountTree as ReviztoIcon,
  HealthAndSafety as HealthIcon,
  FolderOpen as ProjectIcon,
} from '@mui/icons-material';
import { projectsApi } from '@/api/projects';
import { ACCConnectorPanel } from '@/components/dataImports/ACCConnectorPanel';
import { ACCDataImportPanel } from '@/components/dataImports/ACCDataImportPanel';
import { ACCIssuesPanel } from '@/components/dataImports/ACCIssuesPanel';
import { ReviztoImportPanel } from '@/components/dataImports/ReviztoImportPanel';
import { RevitHealthPanel } from '@/components/dataImports/RevitHealthPanel';
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

const DataImportsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

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
    }
  }, [id]);

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
            icon={<IssueIcon />}
            iconPosition="start"
            label="ACC Issues"
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
              <ACCConnectorPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <ACCDataImportPanel projectId={effectiveProjectId} projectName={project?.project_name} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <ACCIssuesPanel projectId={effectiveProjectId} projectName={project?.project_name} />
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
    </Box>
  );
};

export default DataImportsPage;
