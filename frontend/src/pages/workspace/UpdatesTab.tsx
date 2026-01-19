/**
 * Updates Tab
 * 
 * Displays project update history with comments.
 * Integrates with workspace right panel selection.
 */

import { useMemo, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Stack,
  Typography,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { updatesApi } from '@/api';
import { useWorkspaceSelection } from '@/hooks/useWorkspaceSelection';
import type { Project } from '@/types/api';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import type { ProjectUpdate } from '@/api/updates';

type OutletContext = {
  projectId: number;
  project: Project | null;
  selection: Selection | null;
};

const formatDateTime = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
};

export default function UpdatesTab() {
  const { projectId, selection } = useOutletContext<OutletContext>();
  const { setSelection } = useWorkspaceSelection();

  const {
    data: updatesResult,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['projectUpdates', projectId],
    queryFn: () => updatesApi.getProjectUpdates(projectId, { limit: 50 }),
    enabled: Number.isFinite(projectId),
  });

  const updates = useMemo(
    () => updatesResult?.updates || [],
    [updatesResult],
  );

  const handleUpdateClick = useCallback((updateId: number) => {
    setSelection({ type: 'update', id: updateId });
  }, [setSelection]);

  return (
    <Box data-testid="workspace-updates-tab">
      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load updates. Please try again.
        </Alert>
      )}

      {isLoading ? (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <CircularProgress size={40} />
        </Paper>
      ) : updates.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No updates yet. Post the first one from the Overview tab!
          </Typography>
        </Paper>
      ) : (
        <Stack spacing={1.5} data-testid="updates-list">
          {updates.map((update: ProjectUpdate) => (
            <Paper
              key={update.update_id}
              variant="outlined"
              data-testid={`update-row-${update.update_id}`}
              onClick={() => handleUpdateClick(update.update_id)}
              sx={{
                p: 2,
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: selection?.type === 'update' && selection.id === update.update_id
                  ? 'action.selected'
                  : 'background.paper',
                '&:hover': {
                  backgroundColor: 'action.hover',
                  borderColor: 'primary.main',
                },
              }}
            >
              <Stack spacing={0.5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" fontWeight={600}>
                    {update.created_by_name || update.created_by_full_name || 'Unknown'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    · {formatDateTime(update.created_at)}
                  </Typography>
                  {update.comment_count !== undefined && update.comment_count > 0 && (
                    <Chip
                      label={`${update.comment_count} comment${update.comment_count > 1 ? 's' : ''}`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {update.body}
                </Typography>
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
    </Box>
  );
}
