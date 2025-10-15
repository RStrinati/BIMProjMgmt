import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Grid,
  Typography,
  TextField,
  Button,
  Chip,
  IconButton,
  InputAdornment,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { projectsApi } from '@/api';
import type { Project } from '@/types/api';
import ProjectFormDialog from '@/components/ProjectFormDialog';

const REVERSE_PRIORITY_MAP: Record<number, string> = { 1: "Low", 2: "Medium", 3: "High", 4: "Critical" };

export function ProjectsPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');

  // Fetch projects using React Query
  const {
    data: projects,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: () => projectsApi.getStats(),
  });

  // Fetch review statistics
  const { data: reviewStats } = useQuery({
    queryKey: ['projects', 'review-stats'],
    queryFn: () => projectsApi.getReviewStats(),
  });

  // Filter projects based on search
  const filteredProjects = projects?.filter((project) =>
    project.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.project_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.client_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status?: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'on hold':
        return 'warning';
      case 'completed':
        return 'default';
      default:
        return 'default';
    }
  };

  const handleCreateProject = () => {
    setDialogMode('create');
    setSelectedProject(null);
    setDialogOpen(true);
  };

  const handleEditProject = (project: Project) => {
    setDialogMode('edit');
    setSelectedProject(project);
    setDialogOpen(true);
  };

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedProject(null);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Projects
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage all your BIM construction projects
        </Typography>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Projects
                </Typography>
                <Typography variant="h3">{stats.total}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active
                </Typography>
                <Typography variant="h3" color="success.main">
                  {stats.active}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Completed
                </Typography>
                <Typography variant="h3" color="info.main">
                  {stats.completed}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  On Hold
                </Typography>
                <Typography variant="h3" color="warning.main">
                  {stats.on_hold}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search and Actions */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ whiteSpace: 'nowrap' }}
          onClick={handleCreateProject}
        >
          New Project
        </Button>
        <IconButton>
          <FilterListIcon />
        </IconButton>
      </Box>

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load projects. Please try again.
          <Button size="small" onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Projects Grid */}
      {!isLoading && !error && (
        <Grid container spacing={3}>
          {filteredProjects?.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.project_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
                      {project.project_name}
                    </Typography>
                    {project.status && (
                      <Chip
                        label={project.status}
                        color={getStatusColor(project.status)}
                        size="small"
                      />
                    )}
                  </Box>

                  {project.priority && (
                    <Chip
                      label={`Priority: ${(() => {
                        let p = project.priority;
                        if (typeof p === 'number') {
                          return REVERSE_PRIORITY_MAP[p] || 'Medium';
                        } else if (typeof p === 'string' && /^\d+$/.test(p)) {
                          const num = parseInt(p);
                          return REVERSE_PRIORITY_MAP[num] || 'Medium';
                        } else {
                          return p || 'Medium';
                        }
                      })()}`}
                      color="info"
                      size="small"
                      sx={{ mb: 1 }}
                    />
                  )}

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Project #: {project.project_number || 'N/A'}
                  </Typography>

                  {project.client_name && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Client: {project.client_name}
                    </Typography>
                  )}

                  {project.project_type && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Type: {project.project_type}
                    </Typography>
                  )}

                  {project.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        mt: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {project.description}
                    </Typography>
                  )}

                  {/* Review Statistics */}
                  {reviewStats && reviewStats[project.project_id] && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                        Reviews
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          label={`${reviewStats[project.project_id].total_reviews} Total`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Chip
                          label={`${reviewStats[project.project_id].completed_reviews} Completed`}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                        {reviewStats[project.project_id].upcoming_reviews_30_days > 0 && (
                          <Chip
                            label={`${reviewStats[project.project_id].upcoming_reviews_30_days} Upcoming`}
                            size="small"
                            color="warning"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() => handleViewProject(project.project_id)}
                  >
                    View
                  </Button>
                  <IconButton size="small" onClick={() => handleEditProject(project)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredProjects?.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm ? 'Try adjusting your search' : 'Get started by creating your first project'}
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreateProject}>
            Create Project
          </Button>
        </Box>
      )}

      {/* Project Form Dialog */}
      <ProjectFormDialog
        key={selectedProject?.project_id || 'new'}
        open={dialogOpen}
        onClose={handleCloseDialog}
        project={selectedProject}
        mode={dialogMode}
      />
    </Box>
  );
}
