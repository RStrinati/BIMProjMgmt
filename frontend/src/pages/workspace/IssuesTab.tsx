/**
 * Issues Tab
 * 
 * Wraps existing IssuesTabContent component.
 */

import { Box, Typography } from '@mui/material';
import { useOutletContext } from 'react-router-dom';
import { IssuesTabContent } from '@/components/ProjectManagement/IssuesTabContent';
import type { Project } from '@/types/api';
import type { Selection } from '@/hooks/useWorkspaceSelection';

type OutletContext = {
  projectId: number;
  project: Project | null;
  selection: Selection | null;
};

export default function IssuesTab() {
  const { projectId, selection } = useOutletContext<OutletContext>();

  if (!Number.isFinite(projectId)) {
    return (
      <Typography color="text.secondary">
        Select a project to view issues.
      </Typography>
    );
  }

  return (
    <Box data-testid="workspace-issues-tab">
      <IssuesTabContent projectId={projectId} selection={selection} />
    </Box>
  );
}
