import { useMemo, useState } from 'react';
import {
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { useDashboardFilters } from '../DashboardFiltersContext';
import { useDashboardProjectFilter } from '../useDashboardProjectFilter';
import { SummaryCard } from '../components/SummaryCard';
import { DashboardCard } from '../components/DashboardCard';
import { DataFreshnessBadge } from '../DataFreshnessBadge';
import { LastRefreshStatus } from '../LastRefreshStatus';
import { formatDate, formatNumber } from '../utils';

const STALE_DAYS = 14;

export function ModelRegisterPanel() {
  const { filters } = useDashboardFilters();
  const { projectIds } = useDashboardProjectFilter();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const registerQuery = useQuery({
    queryKey: ['dashboard', 'model-register', projectIds, filters.discipline, page, pageSize],
    queryFn: () =>
      dashboardApi.getModelRegister({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        page,
        pageSize,
        sortBy: 'lastVersionDate',
        sortDir: 'desc',
      }),
  });

  const rows = registerQuery.data?.rows ?? [];

  const kpis = useMemo(() => {
    const total = registerQuery.data?.total_count ?? rows.length;
    const last7 = rows.filter((row) => {
      if (!row.lastVersionDateISO) return false;
      const date = new Date(row.lastVersionDateISO);
      if (Number.isNaN(date.getTime())) return false;
      const diff = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24);
      return diff <= 7;
    }).length;
    const stale = rows.filter((row) => {
      if (!row.lastVersionDateISO) return false;
      const date = new Date(row.lastVersionDateISO);
      if (Number.isNaN(date.getTime())) return false;
      const diff = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24);
      return diff > STALE_DAYS;
    }).length;
    const awaitingValidation = rows.filter((row) => row.validationOverall === 'UNKNOWN').length;
    return { total, last7, stale, awaitingValidation };
  }, [rows, registerQuery.data]);

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography variant="h4">Model Register</Typography>
          <Typography variant="body2" color="text.secondary">
            Freshness and validation signals for current models.
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <DataFreshnessBadge asOf={registerQuery.data?.as_of} />
          <LastRefreshStatus updatedAt={registerQuery.dataUpdatedAt} />
        </Stack>
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <SummaryCard label="Models" value={formatNumber(kpis.total)} />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard label="Published Last 7 Days" value={formatNumber(kpis.last7)} />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard label={`Stale > ${STALE_DAYS} Days`} value={formatNumber(kpis.stale)} accent="warning.main" />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard label="Awaiting Validation" value={formatNumber(kpis.awaitingValidation)} />
        </Grid>
      </Grid>

      <DashboardCard title="Model Register" subtitle="Sortable file metadata and freshness">
        <TableContainer>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Project</TableCell>
                <TableCell>Discipline</TableCell>
                <TableCell>File Name</TableCell>
                <TableCell>Date Modified</TableCell>
                <TableCell>File Location</TableCell>
                <TableCell>Published Last Week</TableCell>
                <TableCell>Validation</TableCell>
                <TableCell>Naming</TableCell>
                <TableCell>Freshness</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={`${row.project_id}-${row.modelKey}`}> 
                  <TableCell>{row.project_name ?? '--'}</TableCell>
                  <TableCell>{row.discipline ?? '--'}</TableCell>
                  <TableCell>{row.modelName ?? row.modelKey ?? '--'}</TableCell>
                  <TableCell>{formatDate(row.lastVersionDateISO)}</TableCell>
                  <TableCell>{row.fileLocation ?? '--'}</TableCell>
                  <TableCell>{row.published_last_week ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{row.validationOverall ?? '--'}</TableCell>
                  <TableCell>{row.namingStatus ?? '--'}</TableCell>
                  <TableCell>{row.freshnessStatus ?? '--'}</TableCell>
                </TableRow>
              ))}
              {!rows.length && (
                <TableRow>
                  <TableCell colSpan={9}>
                    <Typography variant="body2" color="text.secondary">
                      No model register rows available for the current filters.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={registerQuery.data?.total_count ?? 0}
          page={Math.max(page - 1, 0)}
          onPageChange={(_, next) => setPage(next + 1)}
          rowsPerPage={pageSize}
          onRowsPerPageChange={(event) => {
            const next = parseInt(event.target.value, 10);
            setPageSize(Number.isNaN(next) ? 25 : next);
            setPage(1);
          }}
          rowsPerPageOptions={[10, 25, 50]}
        />
      </DashboardCard>
    </Stack>
  );
}
