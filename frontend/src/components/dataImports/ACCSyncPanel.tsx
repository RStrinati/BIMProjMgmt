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
  Typography,
} from '@mui/material';
import {
  SyncAlt as SyncIcon,
  Login as LoginIcon,
  Hub as HubIcon,
  Folder as FolderIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  ErrorOutline as ErrorIcon,
} from '@mui/icons-material';
import { apsSyncApi } from '@/api/apsSync';
import type { ApsHub } from '@/types/apsSync';

interface ACCSyncPanelProps {
  projectId?: number;
  projectName?: string;
}

export const ACCSyncPanel: React.FC<ACCSyncPanelProps> = ({ projectName }) => {
  const [selectedHubId, setSelectedHubId] = useState<string | null>(null);

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

  const renderHubItem = (hub: ApsHub) => (
    <ListItemButton
      key={hub.id}
      selected={hub.id === selectedHubId}
      onClick={() => setSelectedHubId(hub.id)}
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
              Authenticate with Autodesk, then pull hubs and projects into the Data Imports workspace
              {projectName ? ` for ${projectName}` : ''}. Data stays in-session for now; database sync
              comes next.
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
              <ListItemButton key={project.id}>
                <ListItemText
                  primary={
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography variant="subtitle1">{project.name}</Typography>
                      {project.status && (
                        <Chip size="small" label={project.status} variant="outlined" />
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
    </Stack>
  );
};
