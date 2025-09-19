import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Assignment,
  People,
  TrendingUp,
  Schedule,
} from '@mui/icons-material';
import { useProject } from '../../context/ProjectContext';
import { apiService } from '../../services/apiService';

const Dashboard = () => {
  const { projects, currentProject, loading } = useProject();
  const [dashboardData, setDashboardData] = useState({
    totalProjects: 0,
    activeReviews: 0,
    pendingTasks: 0,
    completedTasks: 0,
    recentActivities: [],
  });

  useEffect(() => {
    loadDashboardData();
  }, [currentProject]);

  const loadDashboardData = async () => {
    try {
      // Calculate summary statistics
      const totalProjects = projects.length;
      const activeProjects = projects.filter(p => p.status === 'Active').length;
      
      // For demonstration, create mock data
      setDashboardData({
        totalProjects,
        activeProjects,
        pendingTasks: 15,
        completedTasks: 42,
        recentActivities: [
          { id: 1, title: 'Project Alpha review completed', date: '2024-01-15', type: 'review' },
          { id: 2, title: 'New ACC data imported', date: '2024-01-14', type: 'import' },
          { id: 3, title: 'Task assigned to John Doe', date: '2024-01-13', type: 'task' },
          { id: 4, title: 'BEP document updated', date: '2024-01-12', type: 'document' },
        ],
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Project Selector */}
      {currentProject && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Current Project: {currentProject.project_name || currentProject.name}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Status: {currentProject.status || 'Active'}
          </Typography>
        </Paper>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Projects"
            value={dashboardData.totalProjects}
            icon={<Assignment fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Projects"
            value={dashboardData.activeProjects}
            icon={<TrendingUp fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Tasks"
            value={dashboardData.pendingTasks}
            icon={<Schedule fontSize="large" />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed Tasks"
            value={dashboardData.completedTasks}
            icon={<People fontSize="large" />}
            color="info"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Activities */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activities
            </Typography>
            <List>
              {dashboardData.recentActivities.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem>
                    <ListItemText
                      primary={activity.title}
                      secondary={activity.date}
                    />
                    <Chip 
                      label={activity.type} 
                      size="small" 
                      variant="outlined" 
                    />
                  </ListItem>
                  {index < dashboardData.recentActivities.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Project Status Overview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Project Overview
            </Typography>
            <Box sx={{ mt: 2 }}>
              {projects.slice(0, 5).map((project) => (
                <Box key={project.project_id || project.id} sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body1">
                      {project.project_name || project.name}
                    </Typography>
                    <Chip 
                      label={project.status || 'Active'} 
                      size="small"
                      color={project.status === 'Active' ? 'success' : 'default'}
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                    {project.description || 'No description available'}
                  </Typography>
                  {/* Mock progress bar */}
                  <LinearProgress 
                    variant="determinate" 
                    value={Math.random() * 100} 
                    sx={{ mt: 1 }}
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button variant="contained" startIcon={<Assignment />}>
            Create New Project
          </Button>
          <Button variant="outlined" startIcon={<Schedule />}>
            Schedule Review
          </Button>
          <Button variant="outlined" startIcon={<People />}>
            Manage Users
          </Button>
          <Button variant="outlined" startIcon={<TrendingUp />}>
            View Reports
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default Dashboard;