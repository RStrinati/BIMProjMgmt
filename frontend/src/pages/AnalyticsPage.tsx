import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { ACCIssuesPanel } from '@/components/dataImports/ACCIssuesPanel';
import { projectsApi } from '@/api';
import { issuesApi } from '@/api';

export function AnalyticsPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  // Fetch all projects
  const {
    data: projects,
    isLoading: projectsLoading,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  // Fetch overall issues overview
  const {
    data: issuesOverview,
    isLoading: issuesLoading,
    error: issuesError,
  } = useQuery({
    queryKey: ['issues', 'overview'],
    queryFn: () => issuesApi.getOverview(),
  });

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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Analytics Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor ongoing model issues and project analytics across all projects
        </Typography>
      </Box>

      {/* Overall Issues Summary */}
      {issuesOverview && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Overall Issues Summary
            </Typography>

            <Grid container spacing={3}>
              {/* Total Issues */}
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="h6" gutterBottom>
                    Total Issues
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {issuesOverview.summary?.total_issues || 0}
                  </Typography>
                  <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.3, mt: 1 }} />
                </Box>
              </Grid>

              {/* ACC Issues */}
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="h6" gutterBottom>
                    ACC Issues
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {issuesOverview.summary?.acc_issues?.total || 0}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
                    <Chip
                      label={`Open: ${issuesOverview.summary?.acc_issues?.open || 0}`}
                      color="error"
                      size="small"
                    />
                    <Chip
                      label={`Closed: ${issuesOverview.summary?.acc_issues?.closed || 0}`}
                      color="success"
                      size="small"
                    />
                  </Box>
                </Box>
              </Grid>

              {/* Revizto Issues */}
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="h6" gutterBottom>
                    Revizto Issues
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {issuesOverview.summary?.revizto_issues?.total || 0}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
                    <Chip
                      label={`Open: ${issuesOverview.summary?.revizto_issues?.open || 0}`}
                      color="error"
                      size="small"
                    />
                    <Chip
                      label={`Closed: ${issuesOverview.summary?.revizto_issues?.closed || 0}`}
                      color="success"
                      size="small"
                    />
                  </Box>
                </Box>
              </Grid>

              {/* Overall Status */}
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="h6" gutterBottom>
                    Overall Status
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                    <Box>
                      <ErrorIcon color="error" />
                      <Typography variant="body2">Open</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                        {issuesOverview.summary?.overall?.open || 0}
                      </Typography>
                    </Box>
                    <Box>
                      <CheckCircleIcon color="success" />
                      <Typography variant="body2">Closed</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                        {issuesOverview.summary?.overall?.closed || 0}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Grid>
            </Grid>

            {/* Recent Issues */}
            {issuesOverview.recent_issues && issuesOverview.recent_issues.length > 0 && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Issues
                </Typography>
                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {issuesOverview.recent_issues.map((issue: any, index: number) => (
                    <div key={index}>
                      <ListItem>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                label={issue.source}
                                size="small"
                                color={issue.source === 'ACC' ? 'primary' : 'secondary'}
                              />
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {issue.title}
                              </Typography>
                              <Chip
                                label={issue.status}
                                size="small"
                                color={issue.status === 'open' ? 'error' : 'success'}
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                              <Typography variant="body2" color="text.secondary">
                                {issue.project_name} • {issue.assignee || 'Unassigned'}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {formatDate(issue.created_at)}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < issuesOverview.recent_issues.length - 1 && <Divider />}
                    </div>
                  ))}
                </List>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Per-Project Issues */}
      {issuesOverview?.projects && Object.keys(issuesOverview.projects).length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Issues by Project
            </Typography>

            {Object.entries(issuesOverview.projects).map(([projectName, projectData]: [string, any]) => (
              <Accordion key={projectName} sx={{ mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    <Typography variant="h6" sx={{ flex: 1 }}>
                      {projectName}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label={`Total: ${projectData.total_issues}`}
                        size="small"
                        color="primary"
                      />
                      <Chip
                        label={`Open: ${projectData.overall?.open || 0}`}
                        size="small"
                        color="error"
                      />
                      <Chip
                        label={`Closed: ${projectData.overall?.closed || 0}`}
                        size="small"
                        color="success"
                      />
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        ACC Issues
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={`Total: ${projectData.acc_issues?.total || 0}`}
                          size="small"
                        />
                        <Chip
                          label={`Open: ${projectData.acc_issues?.open || 0}`}
                          size="small"
                          color="error"
                        />
                        <Chip
                          label={`Closed: ${projectData.acc_issues?.closed || 0}`}
                          size="small"
                          color="success"
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Revizto Issues
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={`Total: ${projectData.revizto_issues?.total || 0}`}
                          size="small"
                        />
                        <Chip
                          label={`Open: ${projectData.revizto_issues?.open || 0}`}
                          size="small"
                          color="error"
                        />
                        <Chip
                          label={`Closed: ${projectData.revizto_issues?.closed || 0}`}
                          size="small"
                          color="success"
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ACC Issues Panel */}
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            ACC Issues Management
          </Typography>

          {/* Project Selector for ACC Issues */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" gutterBottom>
              Select a project to view and manage ACC issues:
            </Typography>
            <Grid container spacing={2}>
              {projects?.map((project) => (
                <Grid item xs={12} sm={6} md={4} key={project.project_id}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedProjectId === project.project_id ? 2 : 1,
                      borderColor: selectedProjectId === project.project_id ? 'primary.main' : 'divider',
                    }}
                    onClick={() => setSelectedProjectId(project.project_id)}
                  >
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
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
                      {project.project_number && (
                        <Typography variant="body2" color="text.secondary">
                          #{project.project_number}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>

          {/* ACC Issues Panel */}
          {selectedProjectId && (
            <ACCIssuesPanel
              projectId={selectedProjectId}
              projectName={projects?.find(p => p.project_id === selectedProjectId)?.project_name}
            />
          )}

          {!selectedProjectId && (
            <Alert severity="info">
              Please select a project above to view ACC issues.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Loading States */}
      {(projectsLoading || issuesLoading) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error States */}
      {(projectsError || issuesError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load analytics data. Please try again.
        </Alert>
      )}
    </Box>
  );
}