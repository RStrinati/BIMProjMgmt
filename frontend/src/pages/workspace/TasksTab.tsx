/**
 * Tasks Tab
 * 
 * Wraps existing TasksNotesView component.
 */

import { Box } from '@mui/material';
import { useOutletContext } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { TasksNotesView } from '@/components/ProjectManagement/TasksNotesView';
import type { Project } from '@/types/api';

type OutletContext = {
  projectId: number;
  project: Project | null;
};

export default function TasksTab() {
  const { projectId } = useOutletContext<OutletContext>();
  const queryClient = useQueryClient();

  return (
    <Box data-testid="workspace-tasks-tab">
      <TasksNotesView
        initialProjectId={Number.isFinite(projectId) ? projectId : undefined}
        hideFilters
        hideHeader
        onTaskCreated={() => {
          if (Number.isFinite(projectId)) {
            queryClient.invalidateQueries({ queryKey: ['projectTasksPreview', projectId] });
          }
        }}
      />
    </Box>
  );
}
