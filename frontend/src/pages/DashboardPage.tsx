import { Box, Typography, Grid, Card, CardContent, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: () => projectsApi.getStats(),
  });

  const { data: reviewStats } = useQuery({
    queryKey: ['projects', 'review-stats'],
    queryFn: () => projectsApi.getReviewStats(),
  });

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
    </Box>
  );
}
