import { useEffect, useMemo, useState } from 'react';
import {
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
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
import { Pie, PieChart, Cell, Legend, ResponsiveContainer, Tooltip } from 'recharts';
import { dashboardApi } from '@/api/dashboard';
import { useDashboardFilters } from '../DashboardFiltersContext';
import { useDashboardProjectFilter } from '../useDashboardProjectFilter';
import { DashboardCard } from '../components/DashboardCard';
import { GroupedBarCard } from '../components/GroupedBarCard';
import { HorizontalBarCard } from '../components/HorizontalBarCard';
import { TrendChartCard } from '../components/TrendChartCard';
import { KpiStrip } from '../KpiStrip';
import { DataFreshnessBadge } from '../DataFreshnessBadge';
import { LastRefreshStatus } from '../LastRefreshStatus';
import { formatDateTime, formatNumber } from '../utils';
import { dashboardTokens } from '@/components/dashboards/themes';

const STATUS_COLORS = [
  dashboardTokens.compliance.warn,
  dashboardTokens.compliance.pass,
  dashboardTokens.compliance.neutral,
];

export function IssuesPanel() {
  const { filters } = useDashboardFilters();
  const { projectIds } = useDashboardProjectFilter();
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [disciplineFilter, setDisciplineFilter] = useState('all');
  const [zoneFilter, setZoneFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  useEffect(() => {
    if (filters.location) {
      setZoneFilter(filters.location);
    }
  }, [filters.location]);

  useEffect(() => {
    if (filters.discipline && filters.discipline !== 'all') {
      setDisciplineFilter(filters.discipline);
    }
  }, [filters.discipline]);

  useEffect(() => {
    setPage(1);
  }, [statusFilter, priorityFilter, disciplineFilter, zoneFilter, projectIds]);

  const kpisQuery = useQuery({
    queryKey: ['dashboard', 'issues-kpis', projectIds, statusFilter, priorityFilter, disciplineFilter, zoneFilter],
    queryFn: () =>
      dashboardApi.getIssuesKpis({
        projectIds: projectIds.length ? projectIds : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        priority: priorityFilter !== 'all' ? priorityFilter : undefined,
        discipline: disciplineFilter !== 'all' ? disciplineFilter : undefined,
        zone: zoneFilter !== 'all' ? zoneFilter : undefined,
      }),
  });

  const chartsQuery = useQuery({
    queryKey: ['dashboard', 'issues-charts', projectIds, statusFilter, priorityFilter, disciplineFilter, zoneFilter],
    queryFn: () =>
      dashboardApi.getIssuesCharts({
        projectIds: projectIds.length ? projectIds : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        priority: priorityFilter !== 'all' ? priorityFilter : undefined,
        discipline: disciplineFilter !== 'all' ? disciplineFilter : undefined,
        zone: zoneFilter !== 'all' ? zoneFilter : undefined,
      }),
  });

  const tableQuery = useQuery({
    queryKey: ['dashboard', 'issues-table', projectIds, statusFilter, priorityFilter, disciplineFilter, zoneFilter, page, pageSize],
    queryFn: () =>
      dashboardApi.getIssuesTable({
        projectIds: projectIds.length ? projectIds : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        priority: priorityFilter !== 'all' ? priorityFilter : undefined,
        discipline: disciplineFilter !== 'all' ? disciplineFilter : undefined,
        zone: zoneFilter !== 'all' ? zoneFilter : undefined,
        page,
        pageSize,
        sortBy: 'created_at',
        sortDir: 'desc',
      }),
  });

  const statusData = chartsQuery.data?.status ?? [];
  const priorityData = chartsQuery.data?.priority ?? [];
  const statusTotal = useMemo(() => statusData.reduce((sum, row) => sum + (row.value ?? 0), 0), [statusData]);
  const priorityTotal = useMemo(() => priorityData.reduce((sum, row) => sum + (row.value ?? 0), 0), [priorityData]);

  const makePercentLabel =
    (total: number) =>
    ({ percent }: { percent?: number }) =>
      total > 0 && percent !== undefined ? `${Math.round(percent * 100)}%` : '';

  const disciplineBars = useMemo(() => {
    const discipline = chartsQuery.data?.discipline ?? [];
    return discipline.map((row) => ({
      label: row.label,
      open: row.open ?? row.value ?? 0,
      closed: row.closed ?? 0,
    }));
  }, [chartsQuery.data]);

  const zoneBars = useMemo(() => {
    const zone = chartsQuery.data?.zone ?? [];
    return zone.map((row) => ({ label: row.label, value: row.value }));
  }, [chartsQuery.data]);

  const trendData = useMemo(() => {
    const trend = chartsQuery.data?.trend_90d ?? [];
    return trend.map((row) => ({ date: row.date, open: row.open, closed: row.closed }));
  }, [chartsQuery.data]);

  const kpis = kpisQuery.data;
  const closedLabel = kpis?.closed_since_review_label ?? 'Closed Since Last Review';

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography variant="h4">Issues</Typography>
          <Typography variant="body2" color="text.secondary">
            Coordination risks with consistent status grouping across cards, charts, and table.
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <DataFreshnessBadge asOf={kpis?.as_of} />
          <LastRefreshStatus updatedAt={kpisQuery.dataUpdatedAt} />
        </Stack>
      </Stack>

      <KpiStrip
        items={[
          {
            label: 'Active Issues',
            value: formatNumber(kpis?.active_issues),
          },
          {
            label: 'Total Issues',
            value: formatNumber(kpis?.total_issues),
          },
          {
            label: 'Active > 30 Days',
            value: formatNumber(kpis?.over_30_days),
          },
          {
            label: closedLabel,
            value: formatNumber(kpis?.closed_since_review),
          },
        ]}
      />

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <DashboardCard title="Status Distribution" subtitle="Active vs closed vs other">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="label"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  label={makePercentLabel(statusTotal)}
                  labelLine
                  onClick={(entry) => {
                    const label = (entry as { label?: string }).label;
                    if (!label) return;
                    const normalized = label.toLowerCase();
                    if (normalized.includes('active')) setStatusFilter('active');
                    else if (normalized.includes('closed')) setStatusFilter('closed');
                    else setStatusFilter('other');
                  }}
                >
                  {statusData.map((entry, idx) => (
                    <Cell key={entry.label} fill={STATUS_COLORS[idx % STATUS_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  cursor={{ fill: 'transparent' }}
                  contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
                />
                <Legend align="center" verticalAlign="bottom" iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </DashboardCard>
        </Grid>
        <Grid item xs={12} md={6}>
          <DashboardCard title="Priority Distribution" subtitle="Current priority mix">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={priorityData}
                  dataKey="value"
                  nameKey="label"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  label={makePercentLabel(priorityTotal)}
                  labelLine
                >
                  {priorityData.map((entry, idx) => (
                    <Cell key={entry.label} fill={STATUS_COLORS[(idx + 1) % STATUS_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  cursor={{ fill: 'transparent' }}
                  contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
                />
                <Legend align="center" verticalAlign="bottom" iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </DashboardCard>
        </Grid>
        <Grid item xs={12} md={7}>
          <GroupedBarCard title="Active vs Closed by Discipline" data={disciplineBars} />
        </Grid>
        <Grid item xs={12} md={5}>
          <HorizontalBarCard title="Open Issues by Zone" data={zoneBars} />
        </Grid>
        <Grid item xs={12}>
          <TrendChartCard title="Issue Trend" data={trendData} />
        </Grid>
      </Grid>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'stretch', md: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Status</InputLabel>
          <Select value={statusFilter} label="Status" onChange={(event) => setStatusFilter(event.target.value)}>
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
            <MenuItem value="other">Other</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Priority</InputLabel>
          <Select value={priorityFilter} label="Priority" onChange={(event) => setPriorityFilter(event.target.value)}>
            <MenuItem value="all">All</MenuItem>
            {priorityData.map((row) => (
              <MenuItem key={row.label} value={row.label.toLowerCase()}>
                {row.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Discipline</InputLabel>
          <Select value={disciplineFilter} label="Discipline" onChange={(event) => setDisciplineFilter(event.target.value)}>
            <MenuItem value="all">All</MenuItem>
            {disciplineBars.map((row) => (
              <MenuItem key={row.label} value={row.label.toLowerCase()}>
                {row.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Zone</InputLabel>
          <Select value={zoneFilter} label="Zone" onChange={(event) => setZoneFilter(event.target.value)}>
            <MenuItem value="all">All</MenuItem>
            {zoneBars.map((row) => (
              <MenuItem key={row.label} value={row.label.toLowerCase()}>
                {row.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      <DashboardCard title="Issue Drill-Down" subtitle="Numbers reconcile with KPI totals">
        <TableContainer>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Issue #</TableCell>
                <TableCell>Project</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Company</TableCell>
                <TableCell>Zone</TableCell>
                <TableCell>Latest Comment</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(tableQuery.data?.rows ?? []).map((row) => (
                <TableRow key={`${row.issue_id}-${row.project_name}`}>
                  <TableCell>{row.issue_number ?? row.issue_id ?? '--'}</TableCell>
                  <TableCell>{row.project_name ?? '--'}</TableCell>
                  <TableCell>{row.status ?? '--'}</TableCell>
                  <TableCell>{row.priority ?? '--'}</TableCell>
                  <TableCell>{row.title ?? '--'}</TableCell>
                  <TableCell>{row.company ?? '--'}</TableCell>
                  <TableCell>{row.zone ?? '--'}</TableCell>
                  <TableCell>{row.latest_comment ?? '--'}</TableCell>
                  <TableCell>{formatDateTime(row.created_at)}</TableCell>
                </TableRow>
              ))}
              {!tableQuery.isLoading && (tableQuery.data?.rows ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={9}>
                    <Typography variant="body2" color="text.secondary">
                      No issues match the current filters.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={tableQuery.data?.total_count ?? 0}
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
