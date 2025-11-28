import { Profiler, useDeferredValue, useMemo, useState, useTransition } from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material/Select';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';
import { dashboardApi } from '@/api/dashboard';
import DashboardTimelineChart from '@/components/DashboardTimelineChart';
import type { DashboardTimelineProject, WarehouseDashboardMetrics, IssueHistoryPoint } from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';

const EMPTY_PROJECTS: DashboardTimelineProject[] = [];
const TIMELINE_WINDOW_MONTHS = 12;

type StatCardProps = {
  title: string;
  value: string;
  color?: string;
  helper?: string;
};

function StatCard({ title, value, color, helper }: StatCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" gutterBottom variant="h6">
          {title}
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: color || 'text.primary' }}>
          {value}
        </Typography>
        {helper ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {helper}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

type SparklineProps = {
  points: number[];
  color?: string;
};

function Sparkline({ points, color = '#1976d2' }: SparklineProps) {
  if (!points.length) return null;
  const width = 120;
  const height = 40;
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = Math.max(max - min, 1);
  const scaleX = width / Math.max(points.length - 1, 1);
  const path = points
    .map((p, idx) => {
      const x = idx * scaleX;
      const y = height - ((p - min) / range) * height;
      return `${idx === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <path d={path} fill="none" stroke={color} strokeWidth={2} />
    </svg>
  );
}

type StackedBarProps = {
  segments: { value: number; color: string }[];
};

function StackedBar({ segments }: StackedBarProps) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  return (
    <Box sx={{ display: 'flex', width: '100%', height: 10, borderRadius: 999, overflow: 'hidden' }}>
      {segments.map((s, idx) => {
        const width = total > 0 ? `${(s.value / total) * 100}%` : '0%';
        return <Box key={idx} sx={{ width, bgcolor: s.color }} />;
      })}
    </Box>
  );
}

type RadialGaugeProps = {
  value: number;
  color?: string;
};

function RadialGauge({ value, color = '#2e7d32' }: RadialGaugeProps) {
  const normalized = Math.max(0, Math.min(100, value));
  return (
    <Box sx={{ position: 'relative', width: 120, height: 120 }}>
      <svg viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
        <path
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="#e0e0e0"
          strokeWidth="3.2"
        />
        <path
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831"
          fill="none"
          stroke={color}
          strokeWidth="3.2"
          strokeDasharray={`${normalized}, 100`}
        />
      </svg>
      <Box
        sx={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
        }}
      >
        <Typography variant="h6">{Math.round(normalized)}%</Typography>
      </Box>
    </Box>
  );
}

export function DashboardPage() {
  const { data: timelineData, isLoading: isTimelineLoading } = useQuery({
    queryKey: ['dashboard', 'timeline', TIMELINE_WINDOW_MONTHS],
    queryFn: () => projectsApi.getTimeline({ months: TIMELINE_WINDOW_MONTHS }),
  });

  const [selectedManager, setSelectedManager] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedClient, setSelectedClient] = useState<string>('all');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [isFiltering, startFiltering] = useTransition();

  const timelineProjects = timelineData?.projects ?? EMPTY_PROJECTS;

  const filterOptions = useMemo(
    () => {
      const managers = new Set<string>();
      const types = new Set<string>();
      const clients = new Set<string>();

      timelineProjects.forEach((project) => {
        if (project.project_manager) {
          managers.add(project.project_manager);
        }
        if (project.project_type) {
          types.add(project.project_type);
        }
        if (project.client_name) {
          clients.add(project.client_name);
        }
      });

      const sortStrings = (values: Set<string>) =>
        Array.from(values).sort((a, b) => a.localeCompare(b));

      return {
        managers: sortStrings(managers),
        types: sortStrings(types),
        clients: sortStrings(clients),
      };
    },
    [timelineProjects],
  );

  const filteredProjects = useMemo(() => {
    if (!timelineProjects.length) {
      return timelineProjects;
    }

    return timelineProjects.filter((project) => {
      const managerMatches =
        selectedManager === 'all' || project.project_manager === selectedManager;
      const typeMatches = selectedType === 'all' || project.project_type === selectedType;
      const clientMatches = selectedClient === 'all' || project.client_name === selectedClient;
      const projectMatches =
        selectedProjects.length === 0 || selectedProjects.includes(project.project_id ?? -1);
      return managerMatches && typeMatches && clientMatches && projectMatches;
    });
  }, [timelineProjects, selectedManager, selectedType, selectedClient, selectedProjects]);

  const filteredProjectIds = useMemo(
    () =>
      filteredProjects
        .map((p) => p.project_id)
        .filter((id): id is number => typeof id === 'number' && !Number.isNaN(id)),
    [filteredProjects],
  );

  const targetProjectIds = useMemo(() => {
    if (selectedProjects.length) return selectedProjects;
    return filteredProjectIds;
  }, [filteredProjectIds, selectedProjects]);

  const deferredProjects = useDeferredValue(filteredProjects);
  const hasActiveFilters =
    selectedManager !== 'all' ||
    selectedType !== 'all' ||
    selectedClient !== 'all' ||
    selectedProjects.length > 0;

  const {
    data: warehouseMetrics,
    isLoading: isWarehouseMetricsLoading,
  } = useQuery<WarehouseDashboardMetrics>({
    queryKey: ['dashboard', 'warehouse-metrics', targetProjectIds],
    queryFn: () =>
      dashboardApi.getWarehouseMetrics({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
      }),
  });

  const { data: issuesHistory } = useQuery<IssueHistoryPoint[]>({
    queryKey: ['dashboard', 'issues-history', targetProjectIds],
    queryFn: () =>
      dashboardApi.getIssuesHistory({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
      }),
  });

  const latestIssueTrend = useMemo(() => {
    const rows = warehouseMetrics?.issue_trends ?? [];
    if (!rows.length) {
      return null;
    }
    const ordered = rows
      .filter((row) => row.date)
      .sort((a, b) => new Date(a.date || '').getTime() - new Date(b.date || '').getTime());
    if (!ordered.length) {
      return null;
    }
    const last = ordered[ordered.length - 1];
    const previous = ordered.length > 1 ? ordered[ordered.length - 2] : undefined;
    return { last, previous };
  }, [warehouseMetrics]);

  const onTimeRatePct =
    warehouseMetrics?.review_performance?.on_time_rate != null
      ? Math.round(warehouseMetrics.review_performance.on_time_rate * 1000) / 10
      : null;

  const numberFormatter = (value?: number | null, options?: Intl.NumberFormatOptions) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '--';
    return value.toLocaleString(undefined, options);
  };

  const stackedHistory = useMemo(() => {
    if (!issuesHistory?.length) return null;
    const statuses = ['Closed', 'Completed', 'In progress', 'Open'];
    const byWeek: Record<string, Record<string, number>> = {};
    issuesHistory.forEach((row) => {
      const week = row.week_start || 'unknown';
      if (!byWeek[week]) byWeek[week] = {};
      byWeek[week][row.status] = row.count;
    });
    const weeks = Object.keys(byWeek).sort();
    const width = Math.max(720, weeks.length * 80);
    const height = 360;
    const padding = 40;
    const step = weeks.length > 1 ? (width - padding * 2) / (weeks.length - 1) : 0;
    const maxY = Math.max(
      ...weeks.map((w) => statuses.reduce((sum, st) => sum + (byWeek[w][st] || 0), 0)),
      1,
    );
    const gridLines = Array.from({ length: 5 }, (_, idx) => Math.round((maxY / 4) * idx));
    const scaleY = (val: number) =>
      height - padding - (Math.min(val, maxY) / maxY) * (height - padding * 2);

    const series = statuses.map((status) => {
      const color =
        status === 'Closed'
          ? '#9e9e9e'
          : status === 'Completed'
          ? '#4caf50'
          : status === 'In progress'
          ? '#5c6bc0'
          : '#f57c00';
      const points = weeks.map((week, idx) => ({
        x: padding + idx * step,
        y: scaleY(byWeek[week][status] || 0),
        value: byWeek[week][status] || 0,
        week,
      }));
      const path =
        points.length === 0
          ? ''
          : points
              .map((p, idx) => `${idx === 0 ? 'M' : 'L'}${p.x},${p.y}`)
              .join(' ')
              .concat(
                ` L${points[points.length - 1].x},${height - padding} L${points[0].x},${height - padding} Z`,
              );
      return { status, color, points, path };
    });

    return { width, height, padding, series, weeks, gridLines, maxY };
  }, [issuesHistory]);

  return (
    <Profiler id="DashboardPage" onRender={profilerLog}>
      <Box>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
          BIM Project Management Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Slice live warehouse metrics across issues, reviews, and services.
        </Typography>

        <Paper
          elevation={0}
          sx={{
            p: 2,
            mb: 3,
            borderRadius: 2,
            border: (theme) => `1px solid ${theme.palette.divider}`,
            background: (theme) => theme.palette.background.paper,
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Filters
          </Typography>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 220 } }} disabled={isTimelineLoading}>
              <InputLabel id="filter-manager-label">Project Manager</InputLabel>
              <Select
                labelId="filter-manager-label"
                value={selectedManager}
                label="Project Manager"
                onChange={(event: SelectChangeEvent<string>) => {
                  const value = event.target.value;
                  startFiltering(() => setSelectedManager(value));
                }}
              >
                <MenuItem value="all">All</MenuItem>
                {filterOptions.managers.map((manager) => (
                  <MenuItem key={manager} value={manager}>
                    {manager}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 200 } }} disabled={isTimelineLoading}>
              <InputLabel id="filter-type-label">Project Type</InputLabel>
              <Select
                labelId="filter-type-label"
                value={selectedType}
                label="Project Type"
                onChange={(event: SelectChangeEvent<string>) => {
                  const value = event.target.value;
                  startFiltering(() => setSelectedType(value));
                }}
              >
                <MenuItem value="all">All</MenuItem>
                {filterOptions.types.map((projectType) => (
                  <MenuItem key={projectType} value={projectType}>
                    {projectType}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 220 } }} disabled={isTimelineLoading}>
              <InputLabel id="filter-client-label">Client</InputLabel>
              <Select
                labelId="filter-client-label"
                value={selectedClient}
                label="Client"
                onChange={(event: SelectChangeEvent<string>) => {
                  const value = event.target.value;
                  startFiltering(() => setSelectedClient(value));
                }}
              >
                <MenuItem value="all">All</MenuItem>
                {filterOptions.clients.map((client) => (
                  <MenuItem key={client} value={client}>
                    {client}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 260 } }} disabled={isTimelineLoading}>
              <InputLabel id="filter-projects-label">Projects</InputLabel>
              <Select
                labelId="filter-projects-label"
                multiple
                value={selectedProjects.map(String)}
                label="Projects"
                onChange={(event) => {
                  const values = event.target.value as string[];
                  const ids = values.map((v) => Number(v)).filter((v) => !Number.isNaN(v));
                  startFiltering(() => setSelectedProjects(ids));
                }}
                renderValue={(selected) => {
                  if (!selected.length) return 'All';
                  const names = timelineProjects
                    .filter((p) => selected.includes(String(p.project_id)))
                    .map((p) => p.project_name);
                  return names.join(', ');
                }}
              >
                <MenuItem value="__all" disabled>
                  Select projects
                </MenuItem>
                {timelineProjects.map((project) => (
                  <MenuItem key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ alignSelf: { xs: 'flex-start', md: 'center' }, color: 'text.secondary' }}>
              <Typography variant="caption">
                Showing {deferredProjects.length} of {timelineProjects.length} projects
                {isFiltering && ' · updating...'}
              </Typography>
            </Box>
          </Stack>

          {hasActiveFilters && (
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
              {selectedManager !== 'all' && <Chip size="small" label={`Manager: ${selectedManager}`} />}
              {selectedType !== 'all' && <Chip size="small" label={`Type: ${selectedType}`} />}
              {selectedClient !== 'all' && <Chip size="small" label={`Client: ${selectedClient}`} />}
              {selectedProjects.length > 0 && (
                <Chip size="small" label={`Projects: ${selectedProjects.length}`} />
              )}
              <Chip
                size="small"
                label="Clear filters"
                onClick={() => {
                  startFiltering(() => {
                    setSelectedManager('all');
                    setSelectedType('all');
                    setSelectedClient('all');
                    setSelectedProjects([]);
                  });
                }}
                variant="outlined"
              />
            </Stack>
          )}
        </Paper>

        {!isWarehouseMetricsLoading && warehouseMetrics && !warehouseMetrics.error && (
          <>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Open Issues"
                  value={numberFormatter(warehouseMetrics.project_health?.open_issues)}
                  color="primary.main"
                  helper="Current month (warehouse)"
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="High Priority"
                  value={numberFormatter(warehouseMetrics.project_health?.high_priority_issues)}
                  color="error.main"
                  helper="Issues flagged critical"
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Overdue Reviews"
                  value={numberFormatter(warehouseMetrics.project_health?.overdue_reviews)}
                  color="warning.main"
                  helper="Review cycles past due"
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Services In Progress"
                  value={numberFormatter(warehouseMetrics.project_health?.services_in_progress)}
                  color="info.main"
                  helper="Active services this month"
                />
              </Grid>
            </Grid>

            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Issue Trend (last 60d)
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {numberFormatter(latestIssueTrend?.last.open_issues)} open
                      </Typography>
                      <Typography component="span" variant="h6" color="text.secondary">
                        / {numberFormatter(latestIssueTrend?.last.closed_issues)} closed
                      </Typography>
                    </Stack>
                    <Sparkline
                      points={(warehouseMetrics.issue_trends || []).map((row) => row.open_issues || 0)}
                      color="#1976d2"
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Date: {latestIssueTrend?.last.date ?? '--'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Change vs prior: {numberFormatter(
                        (latestIssueTrend?.last.open_issues ?? 0) - (latestIssueTrend?.previous?.open_issues ?? 0)
                      )}{' '}
                      open /{' '}
                      {numberFormatter(
                        (latestIssueTrend?.last.closed_issues ?? 0) - (latestIssueTrend?.previous?.closed_issues ?? 0)
                      )}{' '}
                      closed
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg resolution days: {numberFormatter(latestIssueTrend?.last.avg_resolution_days, {
                        maximumFractionDigits: 1,
                      })}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Review Performance
                    </Typography>
                    <Stack spacing={1} sx={{ mb: 1 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {numberFormatter(warehouseMetrics.review_performance?.completed_reviews)} completed
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        On-time rate: {onTimeRatePct != null ? `${onTimeRatePct}%` : '--'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Overdue: {numberFormatter(warehouseMetrics.review_performance?.overdue_reviews)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg plan vs actual: {numberFormatter(
                          warehouseMetrics.review_performance?.avg_planned_vs_actual_days,
                          { maximumFractionDigits: 1 }
                        )}{' '}
                        days
                      </Typography>
                    </Stack>
                    <StackedBar
                      segments={[
                        { value: warehouseMetrics.review_performance?.completed_reviews || 0, color: '#2e7d32' },
                        { value: warehouseMetrics.review_performance?.overdue_reviews || 0, color: '#ed6c02' },
                        {
                          value:
                            (warehouseMetrics.review_performance?.total_reviews || 0) -
                            (warehouseMetrics.review_performance?.completed_reviews || 0),
                          color: '#90a4ae',
                        },
                      ]}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Services & Financials
                    </Typography>
                    <Stack direction="row" spacing={2} alignItems="center">
                      <RadialGauge
                        value={warehouseMetrics.service_financials?.avg_progress_pct ?? 0}
                        color="#0288d1"
                      />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h5" sx={{ fontWeight: 700 }}>
                          ${numberFormatter(warehouseMetrics.service_financials?.earned_value, {
                            maximumFractionDigits: 0,
                          })}{' '}
                          <Typography component="span" variant="subtitle1" color="text.secondary">
                            earned value
                          </Typography>
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Claimed to date: ${numberFormatter(warehouseMetrics.service_financials?.claimed_to_date, {
                            maximumFractionDigits: 0,
                          })}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Variance fee: ${numberFormatter(warehouseMetrics.service_financials?.variance_fee, {
                            maximumFractionDigits: 0,
                          })}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </>
        )}

        {stackedHistory && (
          <Card sx={{ mt: 4 }}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">Historical Issues (weekly)</Typography>
                <Stack direction="row" spacing={1}>
                  <Chip size="small" label="Closed" sx={{ bgcolor: '#e0e0e0', color: '#424242' }} />
                  <Chip size="small" label="Completed" sx={{ bgcolor: '#4caf50', color: '#fff' }} />
                  <Chip size="small" label="In progress" sx={{ bgcolor: '#5c6bc0', color: '#fff' }} />
                  <Chip size="small" label="Open" sx={{ bgcolor: '#f57c00', color: '#fff' }} />
                </Stack>
              </Stack>
              <Box sx={{ mt: 2, overflowX: 'auto' }}>
                <svg width={stackedHistory.width} height={stackedHistory.height}>
                  {stackedHistory.gridLines.map((g) => {
                    const y = stackedHistory.padding + (1 - g / stackedHistory.maxY) * (stackedHistory.height - stackedHistory.padding * 2);
                    return (
                      <g key={g}>
                        <line
                          x1={0}
                          x2={stackedHistory.width}
                          y1={y}
                          y2={y}
                          stroke="#cfd8dc"
                          strokeDasharray="4 6"
                          strokeWidth={1}
                        />
                        <text x={4} y={y - 4} fontSize="10" fill="#78909c">
                          {g}
                        </text>
                      </g>
                    );
                  })}

                  {stackedHistory.series.map((series) => (
                    <g key={series.status}>
                      <path d={series.path} fill={series.color} opacity={0.25} />
                      <polyline
                        fill="none"
                        stroke={series.color}
                        strokeWidth={3}
                        points={series.points.map((p) => `${p.x},${p.y}`).join(' ')}
                      />
                      {series.points.map((p, idx) => (
                        <text
                          key={idx}
                          x={p.x}
                          y={p.y - 6}
                          fontSize="10"
                          textAnchor="middle"
                          fill="#424242"
                        >
                          {p.value}
                        </text>
                      ))}
                    </g>
                  ))}

                  {stackedHistory.series[0].points.map((p, idx) => (
                    <g key={idx}>
                      <text
                        x={p.x}
                        y={stackedHistory.height - 12}
                        fontSize="10"
                        textAnchor="middle"
                        fill="#616161"
                        transform={`rotate(25 ${p.x} ${stackedHistory.height - 12})`}
                      >
                        {stackedHistory.weeks[idx]}
                      </text>
                    </g>
                  ))}
                </svg>
              </Box>
            </CardContent>
          </Card>
        )}

        {timelineProjects.length > 0 && (
          <>
            <Typography variant="h5" gutterBottom sx={{ mt: 4, fontWeight: 700 }}>
              Project Timeline
            </Typography>
            <DashboardTimelineChart
              projects={deferredProjects}
              isLoading={isTimelineLoading || isFiltering}
              hasActiveFilters={hasActiveFilters}
            />
          </>
        )}
      </Box>
    </Profiler>
  );
}
