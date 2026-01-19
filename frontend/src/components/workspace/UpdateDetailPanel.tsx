/**
 * Update Detail Panel
 * 
 * Static panel content for update details (body + comments).
 * Displayed in workspace right panel when an update is selected.
 */

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Stack,
  Paper,
  CircularProgress,
  Alert,
  TextField,
  Button,
} from '@mui/material';
import { updatesApi } from '@/api';
import type { ProjectUpdate, UpdateComment } from '@/api/updates';

type UpdateDetailPanelProps = {
  updateId: number;
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

export function UpdateDetailPanel({ updateId }: UpdateDetailPanelProps) {
  const queryClient = useQueryClient();
  const [commentDraft, setCommentDraft] = useState('');

  const {
    data: update,
    isLoading: isUpdateLoading,
    isError: isUpdateError,
  } = useQuery<ProjectUpdate>({
    queryKey: ['update', updateId],
    queryFn: () => updatesApi.getUpdate(updateId),
    enabled: !!updateId && Number.isFinite(updateId),
  });

  const {
    data: commentsResult,
    isLoading: isCommentsLoading,
    isError: isCommentsError,
  } = useQuery({
    queryKey: ['updateComments', updateId],
    queryFn: () => updatesApi.getUpdateComments(updateId),
    enabled: !!updateId && Number.isFinite(updateId),
  });

  const comments = useMemo(
    () => commentsResult?.comments || [],
    [commentsResult],
  );

  const createComment = useMutation({
    mutationFn: (body: string) => updatesApi.createUpdateComment(updateId, body),
    onSuccess: () => {
      setCommentDraft('');
      queryClient.invalidateQueries({ queryKey: ['updateComments', updateId] });
      // Also invalidate project updates to refresh comment counts
      if (update?.project_id) {
        queryClient.invalidateQueries({ queryKey: ['projectUpdatesLatest', update.project_id] });
        queryClient.invalidateQueries({ queryKey: ['projectUpdates', update.project_id] });
      }
    },
  });

  const handleAddComment = () => {
    if (!commentDraft.trim()) return;
    createComment.mutate(commentDraft.trim());
  };

  if (isUpdateLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={4}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  if (isUpdateError || !update) {
    return (
      <Alert severity="error">
        Failed to load update details. Please try again.
      </Alert>
    );
  }

  return (
    <Stack spacing={2} data-testid="update-detail-panel">
      {/* Update Header */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          {update.created_by_name || update.created_by_full_name || 'Unknown'}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          {formatDateTime(update.created_at)}
        </Typography>
        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
          {update.body}
        </Typography>
      </Paper>

      {/* Comments Section */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Comments ({comments.length})
        </Typography>

        {isCommentsLoading ? (
          <Box display="flex" justifyContent="center" py={2}>
            <CircularProgress size={24} />
          </Box>
        ) : isCommentsError ? (
          <Alert severity="error">Failed to load comments</Alert>
        ) : comments.length > 0 ? (
          <Stack spacing={1.5} sx={{ mb: 2 }}>
            {comments.map((comment: UpdateComment) => (
              <Box
                key={comment.comment_id}
                sx={{
                  pb: 1.5,
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none', pb: 0 },
                }}
              >
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {comment.created_by_name || comment.created_by_full_name || 'Unknown'}
                  {' · '}
                  {formatDateTime(comment.created_at)}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {comment.body}
                </Typography>
              </Box>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
            No comments yet. Be the first to comment!
          </Typography>
        )}

        {/* Comment Composer */}
        <Stack spacing={1}>
          <TextField
            multiline
            rows={2}
            size="small"
            placeholder="Add a comment..."
            value={commentDraft}
            onChange={(e) => setCommentDraft(e.target.value)}
            disabled={createComment.isPending}
            data-testid="update-comment-composer"
          />
          <Box>
            <Button
              variant="contained"
              size="small"
              onClick={handleAddComment}
              disabled={!commentDraft.trim() || createComment.isPending}
              data-testid="update-add-comment-button"
            >
              {createComment.isPending ? 'Posting...' : 'Add comment'}
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Stack>
  );
}
