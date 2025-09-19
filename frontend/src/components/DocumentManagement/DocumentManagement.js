import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const DocumentManagement = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Document Management
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="textSecondary">
          Document management functionality will be migrated from the Tkinter UI.
          Features will include:
        </Typography>
        <ul>
          <li>BEP (BIM Execution Plan) management</li>
          <li>EIR (Employer Information Requirements) handling</li>
          <li>PIR (Project Information Requirements) management</li>
          <li>Document templates and workflows</li>
          <li>Version control and approval workflows</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default DocumentManagement;