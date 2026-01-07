import React, { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  SyncAlt as SyncIcon,
  Login as LoginIcon,
  Hub as HubIcon,
  Folder as FolderIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  ErrorOutline as ErrorIcon,
  Description as FileIcon,
  People as PeopleIcon,
  BugReport as IssueIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { apsSyncApi } from '@/api/apsSync';
import type { ApsHub, ApsProject } from '@/types/apsSync';

interface ACCSyncPanelProps {
  projectId?: number;
  projectName?: string;
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
      id={`aps-tabpanel-${index}`}
      aria-labelledby={`aps-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

export const ACCSyncPanel: React.FC<ACCSyncPanelProps> = ({ projectName }) => {
  const [selectedHubId, setSelectedHubId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<ApsProject | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [showProjectDetails, setShowProjectDetails] = useState(false);

  const { data: loginInfo } = useQuery({
    queryKey: ['aps-sync', 'login-url'],
    queryFn: apsSyncApi.getLoginUrl,
    staleTime: Infinity,
  });

  const {
    data: hubsData,
    isLoading: hubsLoading,
    isFetching: hubsFetching,
    refetch: refetchHubs,
  } = useQuery({
    queryKey: ['aps-sync', 'hubs'],
    queryFn: apsSyncApi.getHubs,
    refetchOnWindowFocus: false,
  });

  const {
    data: projectsData,
    isLoading: projectsLoading,
    isFetching: projectsFetching,
    refetch: refetchProjects,
  } = useQuery({
    queryKey: ['aps-sync', 'projects', selectedHubId],
    queryFn: () => apsSyncApi.getProjects(selectedHubId || ''),
    enabled: !!selectedHubId,
    refetchOnWindowFocus: false,
  });

  // Project details query
  const {
    data: projectDetails,
    isLoading: detailsLoading,
    refetch: refetchDetails,
  } = useQuery({
    queryKey: ['aps-sync', 'project-details', selectedHubId, selectedProjectId],
    queryFn: () => apsSyncApi.getProjectDetails(selectedHubId || '', selectedProjectId || ''),
    enabled: !!selectedHubId && !!selectedProjectId,
    refetchOnWindowFocus: false,
  });

  // Project files query
  const {
    data: projectFiles,
    isLoading: filesLoading,
  } = useQuery({
    queryKey: ['aps-sync', 'project-files', selectedHubId, selectedProjectId],
    queryFn: () => apsSyncApi.getProjectFolders(selectedHubId || '', selectedProjectId || ''),
    enabled: !!selectedHubId && !!selectedProjectId,
    refetchOnWindowFocus: false,
  });

  // Project issues query
  const {
    data: projectIssues,
    isLoading: issuesLoading,
  } = useQuery({
    queryKey: ['aps-sync', 'project-issues', selectedHubId, selectedProjectId],
    queryFn: () => apsSyncApi.getProjectIssues(selectedHubId || '', selectedProjectId || ''),
    enabled: !!selectedHubId && !!selectedProjectId,
    refetchOnWindowFocus: false,
  });

  // Project users query
  const {
    data: projectUsers,
    isLoading: usersLoading,
  } = useQuery({
    queryKey: ['aps-sync', 'project-users', selectedHubId, selectedProjectId],
    queryFn: () => apsSyncApi.getProjectUsers(selectedHubId || '', selectedProjectId || ''),
    enabled: !!selectedHubId && !!selectedProjectId,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (selectedHubId) {
      refetchProjects();
    }
  }, [selectedHubId, refetchProjects]);

  const hubs = hubsData?.hubs ?? [];
  const projects = projectsData?.projects ?? [];

  const authHint = useMemo(() => {
    if (!hubsData) return null;
    if (hubsData.userToken) {
      return 'User token detected (3-legged OAuth) - full hub visibility';
    }
    if (hubsData.fallback_used) {
      return 'Falling back to app token (2-legged) - hub list may be limited';
    }
    return hubsData.authMethod;
  }, [hubsData]);

  const handleAuthenticate = () => {
    if (loginInfo?.login_url) {
      window.open(loginInfo.login_url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleProjectSelect = (project: ApsProject) => {
    setSelectedProjectId(project.id);
    setSelectedProject(project);
    setShowProjectDetails(true);
    setActiveTab(0);
  };

  const renderHubItem = (hub: ApsHub) => (
    <ListItemButton
      key={hub.id}
      selected={hub.id === selectedHubId}
      onClick={() => {
        setSelectedHubId(hub.id);
        setSelectedProjectId(null);
        setSelectedProject(null);
        setShowProjectDetails(false);
      }}
    >
      <ListItemIcon>
        <HubIcon color={hub.id === selectedHubId ? 'primary' : 'action'} />
      </ListItemIcon>
      <ListItemText
        primary={
          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography variant="subtitle1">{hub.name}</Typography>
            {hub.region && (
              <Chip size="small" label={hub.region} variant="outlined" color="default" />
            )}
          </Stack>
        }
        secondary={`Hub ID: ${hub.id}`}
      />
    </ListItemButton>
  );

  return (
    <Stack spacing={2}>
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} alignItems="center" spacing={2}>
          <SyncIcon color="primary" />
          <Box flex={1}>
            <Typography variant="h6">ACC Sync (Autodesk APS)</Typography>
            <Typography variant="body2" color="text.secondary">
              Authenticate with Autodesk, then pull hubs and projects with detailed model data, issues, and users
              {projectName ? ` for ${projectName}` : ''}.
            </Typography>
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button
              variant="contained"
              startIcon={<LoginIcon />}
              onClick={handleAuthenticate}
              disabled={!loginInfo}
            >
              Authenticate
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetchHubs()}
              disabled={hubsLoading}
            >
              Load hubs
            </Button>
          </Stack>
        </Stack>
        {loginInfo && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Login URL: {loginInfo.login_url}
          </Typography>
        )}
      </Paper>

      {hubsData?.error && (
        <Alert severity="warning" icon={<ErrorIcon fontSize="small" />}>
          {hubsData.error}. {hubsData.message || hubsData.nextStep}
        </Alert>
      )}

      {authHint && (
        <Alert
          severity={hubsData?.userToken ? 'success' : 'info'}
          icon={hubsData?.userToken ? <CheckCircleIcon fontSize="small" /> : undefined}
          sx={{ alignItems: 'center' }}
        >
          {authHint}
        </Alert>
      )}

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <HubIcon color="primary" />
          <Typography variant="subtitle1">
            Hubs {hubsData?.hubCount != null ? `(${hubsData.hubCount})` : ''}
          </Typography>
          {hubsFetching && <CircularProgress size={18} />}
        </Stack>
        <Divider sx={{ mb: 1 }} />
        {hubsLoading ? (
          <Box display="flex" justifyContent="center" py={3}>
            <CircularProgress />
          </Box>
        ) : hubs.length ? (
          <List dense>{hubs.map(renderHubItem)}</List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No hubs returned yet. Authenticate first, then click "Load hubs".
          </Typography>
        )}
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <FolderIcon color="primary" />
          <Typography variant="subtitle1">
            Projects {selectedHubId ? `for hub ${selectedHubId}` : ''}
          </Typography>
          {projectsFetching && <CircularProgress size={18} />}
        </Stack>
        <Divider sx={{ mb: 1 }} />
        {projectsData?.error && (
          <Alert severity="warning" icon={<ErrorIcon fontSize="small" />} sx={{ mb: 1 }}>
            {projectsData.error} {projectsData.message || ''}
          </Alert>
        )}
        {!selectedHubId ? (
          <Typography variant="body2" color="text.secondary">
            Select a hub to see its projects.
          </Typography>
        ) : projectsLoading ? (
          <Box display="flex" justifyContent="center" py={3}>
            <CircularProgress />
          </Box>
        ) : projects.length ? (
          <List dense>
            {projects.map((project) => (
              <ListItemButton key={project.id} onClick={() => handleProjectSelect(project)}>
                <ListItemText
                  primary={
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography variant="subtitle1">{project.name}</Typography>
                      {project.status && (
                        <Chip size="small" label={project.status} variant="outlined" />
                      )}
                      {selectedProjectId === project.id && (
                        <Chip size="small" label="Selected" color="primary" />
                      )}
                    </Stack>
                  }
                  secondary={`Project ID: ${project.id}`}
                />
              </ListItemButton>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No projects returned for this hub. Ensure the authenticated user has access.
          </Typography>
        )}
      </Paper>

      {showProjectDetails && selectedProject && (
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <InfoIcon color="primary" />
              <Typography variant="h6">{selectedProject.name}</Typography>
            </Stack>
            <IconButton size="small" onClick={() => setShowProjectDetails(!showProjectDetails)}>
              {showProjectDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Stack>
          <Divider sx={{ mb: 2 }} />

          <Collapse in={showProjectDetails}>
            <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
              <Tab icon={<InfoIcon />} label="Overview" iconPosition="start" />
              <Tab icon={<FileIcon />} label="Files" iconPosition="start" />
              <Tab icon={<IssueIcon />} label="Issues" iconPosition="start" />
              <Tab icon={<PeopleIcon />} label="Users" iconPosition="start" />
            </Tabs>

            {/* Overview Tab */}
            <TabPanel value={activeTab} index={0}>
              {detailsLoading ? (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress />
                </Box>
              ) : projectDetails?.error ? (
                <Alert severity="error">{projectDetails.error}</Alert>
              ) : projectDetails ? (
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Project Info</Typography>
                    <Stack spacing={1} mt={1}>
                      <Typography variant="body2">
                        <strong>Status:</strong> {projectDetails.projectInfo.status}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Created:</strong> {new Date(projectDetails.projectInfo.created).toLocaleDateString()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Updated:</strong> {new Date(projectDetails.projectInfo.updated).toLocaleDateString()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Total Folders:</strong> {projectDetails.projectInfo.totalTopLevelFolders}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Total Files:</strong> {projectDetails.projectInfo.totalFiles}
                      </Typography>
                    </Stack>
                  </Box>
                  {projectDetails.projectInfo.modelFolders.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">Model Folders</Typography>
                      <List dense>
                        {projectDetails.projectInfo.modelFolders.map((folder, index) => (
                          <ListItemText
                            key={index}
                            primary={folder.name}
                            secondary={`${folder.fileCount} files - Last modified: ${new Date(folder.lastModified).toLocaleDateString()}`}
                          />
                        ))}
                      </List>
                    </Box>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">No project details available</Typography>
              )}
            </TabPanel>

            {/* Files Tab */}
            <TabPanel value={activeTab} index={1}>
              {filesLoading ? (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress />
                </Box>
              ) : projectFiles?.error ? (
                <Alert severity="error">{projectFiles.error}</Alert>
              ) : projectFiles ? (
                <Stack spacing={2}>
                  <Alert severity="info" icon={<InfoIcon />}>
                    Total Files: {projectFiles.totalFiles} | Model Files: {projectFiles.modelFiles.length}
                  </Alert>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Name</strong></TableCell>
                          <TableCell><strong>Type</strong></TableCell>
                          <TableCell><strong>Version</strong></TableCell>
                          <TableCell><strong>Folder</strong></TableCell>
                          <TableCell><strong>Modified</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {projectFiles.modelFiles.slice(0, 50).map((file) => (
                          <TableRow key={file.id}>
                            <TableCell>{file.name}</TableCell>
                            <TableCell>
                              <Chip size="small" label={file.extension || 'unknown'} />
                            </TableCell>
                            <TableCell>{file.version || '-'}</TableCell>
                            <TableCell>{file.folder}</TableCell>
                            <TableCell>{new Date(file.modified).toLocaleDateString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  {projectFiles.modelFiles.length > 50 && (
                    <Typography variant="caption" color="text.secondary">
                      Showing first 50 model files of {projectFiles.modelFiles.length}
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">No files available</Typography>
              )}
            </TabPanel>

            {/* Issues Tab */}
            <TabPanel value={activeTab} index={2}>
              {issuesLoading ? (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress />
                </Box>
              ) : projectIssues?.error ? (
                <Alert severity="error">{projectIssues.error}</Alert>
              ) : projectIssues && projectIssues.issues.length > 0 ? (
                <Stack spacing={2}>
                  <Alert severity="info" icon={<InfoIcon />}>
                    Total Issues: {projectIssues.totalIssues || projectIssues.issueCount || projectIssues.issues.length}
                  </Alert>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Title</strong></TableCell>
                          <TableCell><strong>Status</strong></TableCell>
                          <TableCell><strong>Priority</strong></TableCell>
                          <TableCell><strong>Assigned To</strong></TableCell>
                          <TableCell><strong>Created</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {projectIssues.issues.slice(0, 25).map((issue) => (
                          <TableRow key={issue.id}>
                            <TableCell>{issue.title}</TableCell>
                            <TableCell>
                              <Chip size="small" label={issue.status} color={issue.status === 'open' ? 'warning' : 'default'} />
                            </TableCell>
                            <TableCell>
                              <Chip size="small" label={issue.priority || 'N/A'} />
                            </TableCell>
                            <TableCell>{issue.assigned_to || '-'}</TableCell>
                            <TableCell>{new Date(issue.created).toLocaleDateString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  {projectIssues.issues.length > 25 && (
                    <Typography variant="caption" color="text.secondary">
                      Showing first 25 issues of {projectIssues.issues.length}
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">No issues found</Typography>
              )}
            </TabPanel>

            {/* Users Tab */}
            <TabPanel value={activeTab} index={3}>
              {usersLoading ? (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress />
                </Box>
              ) : projectUsers?.error ? (
                <Alert severity="error">{projectUsers.error}</Alert>
              ) : projectUsers && projectUsers.users.length > 0 ? (
                <Stack spacing={2}>
                  <Alert severity="info" icon={<InfoIcon />}>
                    Total Users: {projectUsers.userCount}
                  </Alert>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Name</strong></TableCell>
                          <TableCell><strong>Email</strong></TableCell>
                          <TableCell><strong>Role</strong></TableCell>
                          <TableCell><strong>Company</strong></TableCell>
                          <TableCell><strong>Status</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {projectUsers.users.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell>{user.name}</TableCell>
                            <TableCell>{user.email || '-'}</TableCell>
                            <TableCell>
                              <Chip size="small" label={user.role || 'N/A'} />
                            </TableCell>
                            <TableCell>{user.company || '-'}</TableCell>
                            <TableCell>
                              <Chip 
                                size="small" 
                                label={user.status || 'active'} 
                                color={user.status === 'active' ? 'success' : 'default'}
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">No users found</Typography>
              )}
            </TabPanel>
          </Collapse>
        </Paper>
      )}
    </Stack>
  );
};
