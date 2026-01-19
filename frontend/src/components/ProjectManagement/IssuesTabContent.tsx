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
  Stack,
  Chip,
} from '@mui/material';
import { issuesApi } from '@/api';
import { useWorkspaceSelection } from '@/hooks/useWorkspaceSelection';
import type { Selection } from '@/hooks/useWorkspaceSelection';

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
  selection: Selection | null;
}

export function IssuesTabContent({ projectId, selection }: IssuesTabContentProps) {
  const [sortField, setSortField] = useState<SortField>('updated_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const { setSelection } = useWorkspaceSelection();

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
    setSelection({ type: 'issue', id: issueKey });
  }, [setSelection]);

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
                  selected={selection?.type === 'issue' && selection.id === issue.issue_key}
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
    </Box>
  );
}
