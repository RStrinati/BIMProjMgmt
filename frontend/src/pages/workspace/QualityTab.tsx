/**
 * Quality Tab
 * 
 * Wraps existing QualityTab component.
 */

import { Box, Typography } from '@mui/material';
import { useOutletContext } from 'react-router-dom';
import { QualityTab as QualityTabContent } from '@/pages/QualityTab';
import type { Project } from '@/types/api';

type OutletContext = {
  projectId: number;
  project: Project | null;
};

export default function QualityTab() {
  const { projectId } = useOutletContext<OutletContext>();

  if (!Number.isFinite(projectId)) {
    return (
      <Typography color="text.secondary">
        Select a project to view quality register.
      </Typography>
    );
  }

  return (
    <Box data-testid="workspace-quality-tab">
      <QualityTabContent projectId={projectId} />
    </Box>
  );
}
