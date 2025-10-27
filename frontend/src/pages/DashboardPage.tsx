import { Profiler, useDeferredValue, useMemo, useState, useTransition } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material/Select';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';
import DashboardTimelineChart from '@/components/DashboardTimelineChart';
import type { DashboardTimelineProject } from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';

const EMPTY_PROJECTS: DashboardTimelineProject[] = [];
const TIMELINE_WINDOW_MONTHS = 12;

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: () => projectsApi.getStats(),
  });

  const { data: reviewStats } = useQuery({
    queryKey: ['projects', 'review-stats'],
    queryFn: () => projectsApi.getReviewStats(),
  });

  const { data: timelineData, isLoading: isTimelineLoading } = useQuery({
    queryKey: ['dashboard', 'timeline', TIMELINE_WINDOW_MONTHS],
    queryFn: () => projectsApi.getTimeline({ months: TIMELINE_WINDOW_MONTHS }),
  });

  const [selectedManager, setSelectedManager] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedClient, setSelectedClient] = useState<string>('all');
  const [isFiltering, startFiltering] = useTransition();

  const timelineProjects = timelineData?.projects ?? EMPTY_PROJECTS;

  const filterOptions = useMemo(
    () => {
      const managers = new Set<string>();
      const types = new Set<string>();
      const clients = new Set<string>();

      timelineProjects.forEach((project) => {
        if (project.project_manager) {
          managers.add(project.project_manager);
        }
        if (project.project_type) {
          types.add(project.project_type);
        }
        if (project.client_name) {
          clients.add(project.client_name);
        }
      });

      const sortStrings = (values: Set<string>) =>
        Array.from(values).sort((a, b) => a.localeCompare(b));

      return {
        managers: sortStrings(managers),
        types: sortStrings(types),
        clients: sortStrings(clients),
      };
    },
    [timelineProjects],
  );

  const filteredProjects = useMemo(() => {
    if (!timelineProjects.length) {
      return timelineProjects;
    }

    return timelineProjects.filter((project) => {
      const managerMatches =
        selectedManager === 'all' || project.project_manager === selectedManager;
      const typeMatches = selectedType === 'all' || project.project_type === selectedType;
      const clientMatches = selectedClient === 'all' || project.client_name === selectedClient;
      return managerMatches && typeMatches && clientMatches;
    });
  }, [timelineProjects, selectedManager, selectedType, selectedClient]);

  const deferredProjects = useDeferredValue(filteredProjects);
  const hasActiveFilters =
    selectedManager !== 'all' || selectedType !== 'all' || selectedClient !== 'all';

  // Calculate aggregate review statistics
  const aggregateReviewStats = reviewStats
    ? Object.values(reviewStats).reduce(
        (acc, projectStats) => ({
          total_reviews: acc.total_reviews + projectStats.total_reviews,
          completed_reviews: acc.completed_reviews + projectStats.completed_reviews,
          planned_reviews: acc.planned_reviews + projectStats.planned_reviews,
          in_progress_reviews: acc.in_progress_reviews + projectStats.in_progress_reviews,
          overdue_reviews: acc.overdue_reviews + projectStats.overdue_reviews,
          upcoming_reviews_30_days:
            acc.upcoming_reviews_30_days + projectStats.upcoming_reviews_30_days,
        }),
        {
          total_reviews: 0,
          completed_reviews: 0,
          planned_reviews: 0,
          in_progress_reviews: 0,
          overdue_reviews: 0,
          upcoming_reviews_30_days: 0,
        }
      )
    : null;

  return (
    <Profiler id="DashboardPage" onRender={profilerLog}>
      <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Welcome to BIM Project Management System
      </Typography>

      <Alert severity="info" sx={{ mb: 4 }}>
        🎉 Welcome to your new modern React UI! This replaces the Tkinter interface.
      </Alert>

      {stats && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="h6">
                  Total Projects
                </Typography>
                <Typography variant="h2" sx={{ fontWeight: 600 }}>
                  {stats.total}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="h6">
                  Active
                </Typography>
                <Typography variant="h2" color="success.main" sx={{ fontWeight: 600 }}>
                  {stats.active}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="h6">
                  Completed
                </Typography>
                <Typography variant="h2" color="info.main" sx={{ fontWeight: 600 }}>
                  {stats.completed}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom variant="h6">
                  On Hold
                </Typography>
                <Typography variant="h2" color="warning.main" sx={{ fontWeight: 600 }}>
                  {stats.on_hold}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Review Statistics */}
      {aggregateReviewStats && (
        <>
          <Typography variant="h5" gutterBottom sx={{ mt: 4, fontWeight: 600 }}>
            Review Overview
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Total Reviews
                  </Typography>
                  <Typography variant="h2" sx={{ fontWeight: 600 }}>
                    {aggregateReviewStats.total_reviews}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Completed
                  </Typography>
                  <Typography variant="h2" color="success.main" sx={{ fontWeight: 600 }}>
                    {aggregateReviewStats.completed_reviews}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    In Progress
                  </Typography>
                  <Typography variant="h2" color="warning.main" sx={{ fontWeight: 600 }}>
                    {aggregateReviewStats.in_progress_reviews}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Upcoming (30 days)
                  </Typography>
                  <Typography variant="h2" color="info.main" sx={{ fontWeight: 600 }}>
                    {aggregateReviewStats.upcoming_reviews_30_days}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}

      {timelineProjects.length > 0 && (
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ mb: 3, mt: 4, flexWrap: 'wrap' }}
        >
          <FormControl
            size="small"
            sx={{ minWidth: { xs: '100%', md: 200 } }}
            disabled={isTimelineLoading}
          >
            <InputLabel id="timeline-manager-filter-label">Manager</InputLabel>
            <Select
              labelId="timeline-manager-filter-label"
              value={selectedManager}
              label="Manager"
              onChange={(event: SelectChangeEvent<string>) => {
                const value = event.target.value;
                startFiltering(() => {
                  setSelectedManager(value);
                });
              }}
            >
              <MenuItem value="all">All</MenuItem>
              {filterOptions.managers.map((manager) => (
                <MenuItem key={manager} value={manager}>
                  {manager}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl
            size="small"
            sx={{ minWidth: { xs: '100%', md: 200 } }}
            disabled={isTimelineLoading}
          >
            <InputLabel id="timeline-type-filter-label">Type</InputLabel>
            <Select
              labelId="timeline-type-filter-label"
              value={selectedType}
              label="Type"
              onChange={(event: SelectChangeEvent<string>) => {
                const value = event.target.value;
                startFiltering(() => {
                  setSelectedType(value);
                });
              }}
            >
              <MenuItem value="all">All</MenuItem>
              {filterOptions.types.map((projectType) => (
                <MenuItem key={projectType} value={projectType}>
                  {projectType}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl
            size="small"
            sx={{ minWidth: { xs: '100%', md: 220 } }}
            disabled={isTimelineLoading}
          >
            <InputLabel id="timeline-client-filter-label">Client</InputLabel>
            <Select
              labelId="timeline-client-filter-label"
              value={selectedClient}
              label="Client"
              onChange={(event: SelectChangeEvent<string>) => {
                const value = event.target.value;
                startFiltering(() => {
                  setSelectedClient(value);
                });
              }}
            >
              <MenuItem value="all">All</MenuItem>
              {filterOptions.clients.map((client) => (
                <MenuItem key={client} value={client}>
                  {client}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ alignSelf: { xs: 'flex-start', md: 'center' }, color: 'text.secondary' }}>
            <Typography variant="caption">
              Showing {deferredProjects.length} of {timelineProjects.length} projects
              {isFiltering && ' · Updating…'}
            </Typography>
          </Box>
        </Stack>
      )}

      <DashboardTimelineChart
        projects={deferredProjects}
        isLoading={isTimelineLoading || isFiltering}
        hasActiveFilters={hasActiveFilters}
      />
      </Box>
    </Profiler>
  );
}
