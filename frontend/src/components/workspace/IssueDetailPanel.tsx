/**
 * Issue Detail Panel
 * 
 * Static panel content for issue details (Properties, Comments, Associations).
 * Displayed in workspace right panel when an issue is selected.
 */

import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Stack,
  Paper,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { issuesApi } from '@/api';
import { InlineField } from '@/components/ui/InlineField';

interface IssueDetail {
  issue_key: string;
  display_id: string;
  title: string;
  status_normalized: string;
  priority_normalized: string;
  zone: string | null;
  assignee_user_key: string | null;
  discipline_normalized: string | null;
  created_at: string;
  updated_at: string;
  due_date: string | null;
  service_id: number | null;
  service_name: string | null;
  review_id: number | null;
  review_label: string | null;
  comments: Array<{
    text: string;
    author: string;
    created_at: string;
  }>;
}

type IssueDetailPanelProps = {
  projectId: number;
  issueKey: string;
};

const getStatusColor = (status?: string): 'success' | 'warning' | 'error' | 'default' => {
  const normalized = status?.toLowerCase();
  if (normalized === 'open' || normalized === 'in progress') {
    return 'error';
  }
  if (normalized === 'pending' || normalized === 'on hold') {
    return 'warning';
  }
  if (normalized === 'closed' || normalized === 'resolved') {
    return 'success';
  }
  return 'default';
};

const getPriorityColor = (priority?: string): 'error' | 'warning' | 'info' | 'default' => {
  const normalized = priority?.toLowerCase();
  if (normalized === 'high' || normalized === 'critical') {
    return 'error';
  }
  if (normalized === 'medium') {
    return 'warning';
  }
  if (normalized === 'low') {
    return 'info';
  }
  return 'default';
};

const formatDate = (dateStr?: string | null): string => {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString();
  } catch {
    return dateStr;
  }
};

export function IssueDetailPanel({ projectId, issueKey }: IssueDetailPanelProps) {
  const {
    data: issueDetail,
    isLoading,
    isError,
  } = useQuery<IssueDetail>({
    queryKey: ['issueDetail', projectId, issueKey],
    queryFn: () => issuesApi.getIssueDetail(issueKey, projectId),
    enabled: !!issueKey && Number.isFinite(projectId),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={4}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  if (isError || !issueDetail) {
    return (
      <Alert severity="error">
        Failed to load issue details. Please try again.
      </Alert>
    );
  }

  return (
    <Stack spacing={2} data-testid="issue-detail-panel">
      {/* Issue Header */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          {issueDetail.display_id}
        </Typography>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 0.5 }}>
          {issueDetail.title}
        </Typography>
      </Paper>

      {/* Status & Priority */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Status & Priority
        </Typography>
        <Stack spacing={1}>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Status
            </Typography>
            <Chip
              label={issueDetail.status_normalized || '—'}
              size="small"
              color={getStatusColor(issueDetail.status_normalized)}
            />
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Priority
            </Typography>
            <Chip
              label={issueDetail.priority_normalized || '—'}
              size="small"
              color={getPriorityColor(issueDetail.priority_normalized)}
            />
          </Box>
        </Stack>
      </Paper>

      {/* Properties */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Properties
        </Typography>
        <Stack spacing={1}>
          <InlineField label="Assignee" value={issueDetail.assignee_user_key || 'Unmapped'} />
          <InlineField label="Discipline" value={issueDetail.discipline_normalized || '—'} />
          <InlineField label="Zone" value={issueDetail.zone || '—'} />
          <InlineField label="Due Date" value={formatDate(issueDetail.due_date)} />
        </Stack>
      </Paper>

      {/* Service & Review Association */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Associations
        </Typography>
        <Stack spacing={1}>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Service
            </Typography>
            {issueDetail.service_name ? (
              <Chip label={issueDetail.service_name} size="small" variant="outlined" />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Unmapped
              </Typography>
            )}
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Review
            </Typography>
            {issueDetail.review_label ? (
              <Chip label={issueDetail.review_label} size="small" variant="outlined" />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Unmapped
              </Typography>
            )}
          </Box>
        </Stack>
      </Paper>

      {/* Dates */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Timeline
        </Typography>
        <Stack spacing={1}>
          <InlineField label="Created" value={formatDate(issueDetail.created_at)} />
          <InlineField label="Updated" value={formatDate(issueDetail.updated_at)} />
        </Stack>
      </Paper>

      {/* Comments Section */}
      {issueDetail.comments && issueDetail.comments.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
            Latest Comments
          </Typography>
          <Stack spacing={1.5}>
            {issueDetail.comments.map((comment, idx) => (
              <Box
                key={idx}
                sx={{
                  pb: 1.5,
                  borderBottom: idx < issueDetail.comments.length - 1 ? '1px solid' : 'none',
                  borderColor: 'divider',
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {comment.author} · {formatDate(comment.created_at)}
                </Typography>
                <Typography variant="body2" sx={{ mt: 0.5 }}>
                  {comment.text}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}
