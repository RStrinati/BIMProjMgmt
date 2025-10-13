import { Box, Typography, Grid, Card, CardContent, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: () => projectsApi.getStats(),
  });

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
    </Box>
  );
}
