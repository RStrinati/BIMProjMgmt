import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';

interface IssueReliabilityCheck {
  check_name: string;
  severity: string;
  passed: boolean;
  details?: string | null;
  checked_at?: string | null;
}

interface IssueReliabilityRun {
  import_run_id: number;
  status: string | null;
  started_at: string | null;
  completed_at: string | null;
  row_count: number | null;
  notes: string | null;
}

interface IssueReliabilityReport {
  run: IssueReliabilityRun | null;
  checks: IssueReliabilityCheck[];
  counts: {
    issues_current?: number;
    issues_snapshots?: number;
  };
  unmapped_statuses: Array<{
    source_system: string;
    raw_status: string;
    issue_count: number;
  }>;
}

const severityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'info':
      return 'info';
    default:
      return 'default';
  }
};

export default function IssueReliabilityTab() {
  const { data, isLoading, error } = useQuery<IssueReliabilityReport>({
    queryKey: ['settings', 'issue-reliability'],
    queryFn: async () => {
      const response = await apiClient.get<IssueReliabilityReport>('/settings/issue-reliability');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ py: 6, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load issue reliability report.</Alert>;
  }

  if (!data || !data.run) {
    return <Alert severity="warning">No issue reliability run available.</Alert>;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Latest Issue Import Run
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Run ID
              </Typography>
              <Typography>{data.run.import_run_id}</Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Status
              </Typography>
              <Chip label={data.run.status ?? 'unknown'} color={data.run.status === 'success' ? 'success' : 'warning'} />
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Row Count
              </Typography>
              <Typography>{data.run.row_count ?? '—'}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Started At
              </Typography>
              <Typography>{data.run.started_at ?? '—'}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Completed At
              </Typography>
              <Typography>{data.run.completed_at ?? '—'}</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Canonical Counts
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Issues_Current
              </Typography>
              <Typography>{data.counts.issues_current ?? 0}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Issues_Snapshots (latest run)
              </Typography>
              <Typography>{data.counts.issues_snapshots ?? 0}</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Quality Checks
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Check</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Passed</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>Checked At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.checks.map((check) => (
                  <TableRow key={check.check_name}>
                    <TableCell>{check.check_name}</TableCell>
                    <TableCell>
                      <Chip label={check.severity} color={severityColor(check.severity)} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip label={check.passed ? 'Pass' : 'Fail'} color={check.passed ? 'success' : 'error'} size="small" />
                    </TableCell>
                    <TableCell>{check.details ?? '—'}</TableCell>
                    <TableCell>{check.checked_at ?? '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Unmapped Statuses
          </Typography>
          {data.unmapped_statuses.length === 0 ? (
            <Alert severity="success">No unmapped statuses detected.</Alert>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Source</TableCell>
                    <TableCell>Raw Status</TableCell>
                    <TableCell>Issue Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.unmapped_statuses.map((row) => (
                    <TableRow key={`${row.source_system}-${row.raw_status}`}>
                      <TableCell>{row.source_system}</TableCell>
                      <TableCell>{row.raw_status}</TableCell>
                      <TableCell>{row.issue_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
