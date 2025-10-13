/**
 * ACC Issues Panel Component
 * Displays and filters ACC issues with statistics
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Stack,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { accIssuesApi } from '@/api/dataImports';
import { formatDate } from '@/utils/dateUtils';
import type { ACCIssuesFilters } from '@/types/dataImports';

interface ACCIssuesPanelProps {
  projectId: number;
  projectName?: string;
}

export const ACCIssuesPanel: React.FC<ACCIssuesPanelProps> = ({ projectId, projectName }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [filters, setFilters] = useState<ACCIssuesFilters>({});
  const [searchText, setSearchText] = useState('');

  // Query for issues
  const {
    data: issuesData,
    isLoading: issuesLoading,
    refetch: refetchIssues,
  } = useQuery({
    queryKey: ['accIssues', projectId, page, rowsPerPage, filters],
    queryFn: () => accIssuesApi.getIssues(projectId, filters, page + 1, rowsPerPage),
  });

  // Query for statistics
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['accIssuesStats', projectId],
    queryFn: () => accIssuesApi.getStats(projectId),
  });

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleApplyFilters = () => {
    const newFilters: ACCIssuesFilters = {};
    if (searchText.trim()) {
      newFilters.search = searchText.trim();
    }
    setFilters(newFilters);
    setPage(0);
  };

  const handleClearFilters = () => {
    setFilters({});
    setSearchText('');
    setPage(0);
  };

  const handleRefresh = () => {
    refetchIssues();
    refetchStats();
  };

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('closed') || statusLower.includes('resolved')) return 'success';
    if (statusLower.includes('open') || statusLower.includes('active')) return 'primary';
    if (statusLower.includes('overdue') || statusLower.includes('critical')) return 'error';
    if (statusLower.includes('pending') || statusLower.includes('in progress')) return 'warning';
    return 'default';
  };

  const getTypeColor = (type: string) => {
    const typeLower = type.toLowerCase();
    if (typeLower.includes('rfi') || typeLower.includes('request')) return 'info';
    if (typeLower.includes('defect') || typeLower.includes('issue')) return 'error';
    if (typeLower.includes('observation') || typeLower.includes('note')) return 'warning';
    return 'default';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h5" gutterBottom>
        ACC Issues
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        View and manage ACC issues for {projectName || `Project #${projectId}`}.
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Total Issues
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <CircularProgress size={24} /> : stats?.total_issues || 0}
                  </Typography>
                </Box>
                <TrendingUpIcon color="primary" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Open Issues
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <CircularProgress size={24} /> : stats?.open_issues || 0}
                  </Typography>
                </Box>
                <WarningIcon color="warning" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Closed Issues
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <CircularProgress size={24} /> : stats?.closed_issues || 0}
                  </Typography>
                </Box>
                <CheckCircleIcon color="success" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Overdue Issues
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <CircularProgress size={24} /> : stats?.overdue_issues || 0}
                  </Typography>
                </Box>
                <ErrorIcon color="error" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            label="Search"
            size="small"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search title or description..."
            sx={{ flexGrow: 1 }}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleApplyFilters();
              }
            }}
          />
          <Button
            variant="contained"
            startIcon={<FilterIcon />}
            onClick={handleApplyFilters}
            size="small"
          >
            Apply
          </Button>
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearFilters}
            size="small"
          >
            Clear
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size="small"
            disabled={issuesLoading || statsLoading}
          >
            Refresh
          </Button>
        </Stack>
      </Paper>

      {/* Issues Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Issues ({issuesData?.total_count || 0})
        </Typography>

        {issuesLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : issuesData && issuesData.issues.length > 0 ? (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Issue ID</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Assigned To</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Location</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {issuesData.issues.map((issue) => (
                    <TableRow key={issue.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {issue.issue_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={issue.description || issue.title}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                            {issue.title}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={issue.status}
                          color={getStatusColor(issue.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip label={issue.type} color={getTypeColor(issue.type)} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {issue.assigned_to || 'Unassigned'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {issue.due_date
                            ? formatDate(issue.due_date, 'MMM d, yyyy')
                            : 'No due date'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {formatDate(issue.created_date, 'MMM d, yyyy')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={issue.location || 'No location'}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                            {issue.location || '-'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={issuesData.total_count}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </>
        ) : (
          <Alert severity="info">
            No issues found. Import ACC data to see issues here.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};
