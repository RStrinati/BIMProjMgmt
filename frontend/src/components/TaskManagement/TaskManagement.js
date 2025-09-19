import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const TaskManagement = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Task Management
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="textSecondary">
          Enhanced task management functionality will be migrated from the Tkinter UI.
          Features will include:
        </Typography>
        <ul>
          <li>Task creation and assignment</li>
          <li>Dependency management</li>
          <li>Progress tracking</li>
          <li>Resource allocation</li>
          <li>Milestone management</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default TaskManagement;