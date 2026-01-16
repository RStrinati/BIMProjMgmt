import { useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography,
  CircularProgress,
  Alert,
  Drawer,
  Card,
  CardContent,
  Stack,
  Chip,
  IconButton,
  Divider,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { issuesApi } from '@/api';

interface IssueRow {
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
  service_id: number | null;
  service_name: string | null;
  review_id: number | null;
}

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

type SortField = 'title' | 'status_normalized' | 'priority_normalized' | 'zone' | 'updated_at';
type SortOrder = 'asc' | 'desc';

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

interface IssuesTabContentProps {
  projectId: number;
}

export function IssuesTabContent({ projectId }: IssuesTabContentProps) {
  const [sortField, setSortField] = useState<SortField>('updated_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedIssueKey, setSelectedIssueKey] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const {
    data: issuesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['projectIssuesTable', projectId, sortField, sortOrder],
    queryFn: () =>
      issuesApi.getProjectIssuesTable(projectId, {
        page: 1,
        page_size: 50,
        sort_by: sortField,
        sort_dir: sortOrder,
      }),
    enabled: Number.isFinite(projectId),
  });

  const {
    data: issueDetail,
    isLoading: isDetailLoading,
  } = useQuery({
    queryKey: ['issueDetail', projectId, selectedIssueKey],
    queryFn: () =>
      issuesApi.getIssueDetail(selectedIssueKey!, projectId),
    enabled: selectedIssueKey !== null,
  });

  const issues = useMemo(() => (Array.isArray(issuesData?.rows) ? issuesData.rows : []), [issuesData]);

  const handleSortClick = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleRowClick = useCallback((issueKey: string) => {
    setSelectedIssueKey(issueKey);
    setIsDetailOpen(true);
  }, []);

  const handleDetailClose = () => {
    setIsDetailOpen(false);
    setSelectedIssueKey(null);
  };

  return (
    <Box data-testid="project-issues-tab" sx={{ display: 'grid', gap: 2 }}>
      {error && (
        <Alert severity="error">
          Failed to load project issues. Please try again.
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined" data-testid="project-issues-table">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'display_id'}
                  direction={sortField === 'display_id' ? sortOrder : 'asc'}
                  onClick={() => handleSortClick('title')}
                >
                  Issue ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'title'}
                  direction={sortField === 'title' ? sortOrder : 'asc'}
                  onClick={() => handleSortClick('title')}
                >
                  Title
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'status_normalized'}
                  direction={sortField === 'status_normalized' ? sortOrder : 'asc'}
                  onClick={() => handleSortClick('status_normalized')}
                >
                  Status
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'priority_normalized'}
                  direction={sortField === 'priority_normalized' ? sortOrder : 'asc'}
                  onClick={() => handleSortClick('priority_normalized')}
                >
                  Priority
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'zone'}
                  direction={sortField === 'zone' ? sortOrder : 'asc'}
                  onClick={() => handleSortClick('zone')}
                >
                  Zone
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={40} />
                </TableCell>
              </TableRow>
            ) : issues.length > 0 ? (
              issues.map((issue) => (
                <TableRow
                  key={issue.issue_key}
                  data-testid={`issue-row-${issue.display_id}`}
                  hover
                  onClick={() => handleRowClick(issue.issue_key)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell sx={{ fontWeight: 600 }}>
                    {issue.display_id || '—'}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{issue.title || '—'}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={issue.status_normalized || '—'}
                      size="small"
                      color={getStatusColor(issue.status_normalized)}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={issue.priority_normalized || '—'}
                      size="small"
                      color={getPriorityColor(issue.priority_normalized)}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    {issue.zone || '—'}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No issues found for this project.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Issue Detail Drawer */}
      <Drawer
        anchor="right"
        open={isDetailOpen}
        onClose={handleDetailClose}
        data-testid="issue-detail-drawer"
        PaperProps={{
          sx: { width: { xs: '100%', sm: 400 } },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            p: 2,
          }}
        >
          {/* Close Button */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <IconButton
              onClick={handleDetailClose}
              size="small"
              data-testid="issue-detail-close"
            >
              <CloseIcon />
            </IconButton>
          </Box>

          {/* Detail Content */}
          {isDetailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
              <CircularProgress size={40} />
            </Box>
          ) : issueDetail ? (
            <Stack spacing={2} sx={{ flex: 1, overflow: 'auto' }}>
              <Card data-testid="issue-detail-card" variant="outlined">
                <CardContent>
                  <Stack spacing={2}>
                    {/* Header */}
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {issueDetail.display_id}
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 0.5 }}>
                        {issueDetail.title}
                      </Typography>
                    </Box>

                    <Divider />

                    {/* Status & Priority */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Status
                        </Typography>
                        <Chip
                          label={issueDetail.status_normalized || '—'}
                          size="small"
                          color={getStatusColor(issueDetail.status_normalized)}
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Priority
                        </Typography>
                        <Chip
                          label={issueDetail.priority_normalized || '—'}
                          size="small"
                          color={getPriorityColor(issueDetail.priority_normalized)}
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </Box>

                    {/* Assignee & Discipline */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Assignee
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {issueDetail.assignee_user_key || 'Unmapped'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Discipline
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {issueDetail.discipline_normalized || '—'}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Zone & Due Date */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Zone
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {issueDetail.zone || '—'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Due Date
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {formatDate(issueDetail.due_date)}
                        </Typography>
                      </Box>
                    </Box>

                    <Divider />

                    {/* Service & Review Association */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        Associated Service
                      </Typography>
                      <Typography variant="body2">
                        {issueDetail.service_name ? (
                          <Chip
                            label={issueDetail.service_name}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          'Unmapped'
                        )}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        Associated Review
                      </Typography>
                      <Typography variant="body2">
                        {issueDetail.review_label ? (
                          <Chip
                            label={issueDetail.review_label}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          'Unmapped'
                        )}
                      </Typography>
                    </Box>

                    {/* Dates */}
                    <Divider />
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Created
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          {formatDate(issueDetail.created_at)}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Updated
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          {formatDate(issueDetail.updated_at)}
                        </Typography>
                      </Box>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>

              {/* Comments Section */}
              {issueDetail.comments && issueDetail.comments.length > 0 && (
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Latest Comments
                    </Typography>
                    <Stack spacing={1}>
                      {issueDetail.comments.map((comment, idx) => (
                        <Box key={idx} sx={{ pb: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="caption" color="text.secondary">
                            {comment.author} · {formatDate(comment.created_at)}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {comment.text}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              )}
            </Stack>
          ) : null}
        </Box>
      </Drawer>
    </Box>
  );
}
