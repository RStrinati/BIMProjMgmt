import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const ACCIntegration = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ACC Integration
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="textSecondary">
          Autodesk Construction Cloud integration functionality will be migrated from the Tkinter UI.
          Features will include:
        </Typography>
        <ul>
          <li>ACC folder management and synchronization</li>
          <li>Data import from ACC exports</li>
          <li>File validation and processing</li>
          <li>ACC project linking and mapping</li>
          <li>Automated data refresh capabilities</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default ACCIntegration;