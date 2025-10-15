import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import { projectsApi } from '../api/projects';
import type { Project } from '../types/api';
import { ProjectServicesTab } from '@/components/ProjectServicesTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);

  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', id],
    queryFn: () => projectsApi.getById(Number(id)),
    enabled: !!id,
  });

  const handleEdit = () => {
    // TODO: Open edit dialog
    console.log('Edit project:', id);
  };

  const handleDelete = () => {
    // TODO: Confirm and delete
    console.log('Delete project:', id);
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load project details. {error instanceof Error ? error.message : ''}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mt: 2 }}>
          Back to Projects
        </Button>
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'on hold':
        return 'warning';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/projects')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1">
              {project.project_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Project #{project.project_number}
            </Typography>
          </Box>
          <Chip label={project.status} color={getStatusColor(project.status ?? '')} />
        </Box>
        <Box display="flex" gap={1}>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
            Edit
          </Button>
          <Button variant="outlined" color="error" startIcon={<DeleteIcon />} onClick={handleDelete}>
            Delete
          </Button>
        </Box>
      </Box>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Column - Project Details */}
        <Grid item xs={12} md={8}>
          <Paper>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Details" />
              <Tab label="Services" />
              <Tab label="Reviews" />
              <Tab label="Tasks" />
              <Tab label="Files" />
            </Tabs>
            <Divider />

            {/* Details Tab */}
            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Client
                  </Typography>
                  <Typography variant="body1">{project.client_name || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Project Type
                  </Typography>
                  <Typography variant="body1">{project.project_type || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Start Date
                  </Typography>
                  <Typography variant="body1">
                    {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    End Date
                  </Typography>
                  <Typography variant="body1">
                    {project.end_date ? new Date(project.end_date).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Priority
                  </Typography>
                  <Typography variant="body1">{project.priority || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Area (Hectares)
                  </Typography>
                  <Typography variant="body1">{project.area_m2 || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    MW Capacity
                  </Typography>
                  <Typography variant="body1">{project.mw_capacity || 'N/A'}</Typography>
                </Grid>

                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Address
                  </Typography>
                  <Typography variant="body1">
                    {[project.address, project.city, project.state, project.postcode]
                      .filter(Boolean)
                      .join(', ') || 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Folder Path
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <FolderIcon fontSize="small" color="action" />
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {project.folder_path || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    IFC Folder Path
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <FolderIcon fontSize="small" color="action" />
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {project.ifc_folder_path || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>

                {project.description && (
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1">{project.description}</Typography>
                  </Grid>
                )}
              </Grid>
            </TabPanel>

            {/* Services Tab */}
            <TabPanel value={tabValue} index={1}>
              <ProjectServicesTab projectId={Number(id)} />
            </TabPanel>

            {/* Reviews Tab */}
            <TabPanel value={tabValue} index={2}>
              <Alert severity="info">
                Reviews are now managed within the Services tab. Please go to the Services tab and select a service to view and manage its reviews.
              </Alert>
            </TabPanel>

            {/* Tasks Tab */}
            <TabPanel value={tabValue} index={3}>
              <Alert severity="info">Tasks functionality coming soon</Alert>
            </TabPanel>

            {/* Files Tab */}
            <TabPanel value={tabValue} index={4}>
              <Alert severity="info">File management coming soon</Alert>
            </TabPanel>
          </Paper>
        </Grid>

        {/* Right Column - Quick Stats & Actions */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {project.created_at ? new Date(project.created_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body1">
                    {project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button variant="outlined" startIcon={<CalendarIcon />} fullWidth>
                  Schedule Review
                </Button>
                <Button variant="outlined" startIcon={<FolderIcon />} fullWidth>
                  Open Folder
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProjectDetailPage;
