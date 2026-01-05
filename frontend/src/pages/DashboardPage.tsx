import { Profiler, useDeferredValue, useEffect, useMemo, useState, useTransition } from 'react';
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
  Button,
  TextField,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material/Select';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api';
import { dashboardApi } from '@/api/dashboard';
import DashboardTimelineChart from '@/components/DashboardTimelineChart';
import type {
  DashboardTimelineProject,
  WarehouseDashboardMetrics,
  IssueHistoryPoint,
  RevitHealthDashboardMetrics,
  NamingComplianceMetrics,
} from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';
import { useNavigate } from 'react-router-dom';

const EMPTY_PROJECTS: DashboardTimelineProject[] = [];
const TIMELINE_WINDOW_MONTHS = 12;

type SavedView = {
  name: string;
  manager: string;
  type: string;
  client: string;
  projects: number[];
};

type StatCardProps = {
  title: string;
  value: string;
  color?: string;
  helper?: string;
  onClick?: () => void;
};

function StatCard({ title, value, color, helper, onClick }: StatCardProps) {
  return (
    <Card
      sx={{
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        border: onClick ? (theme) => `1px solid ${theme.palette.primary.light}` : undefined,
      }}
      onClick={onClick}
    >
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

type WireframeCardProps = {
  title: string;
  description: string;
  checklist: string[];
  accent?: string;
};

function WireframeCard({ title, description, checklist, accent = '#1976d2' }: WireframeCardProps) {
  return (
    <Card sx={{ height: '100%', borderStyle: 'dashed', borderColor: (theme) => theme.palette.divider }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {description}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 54,
              height: 54,
              borderRadius: '50%',
              border: `3px dashed ${accent}`,
              display: 'grid',
              placeItems: 'center',
              fontWeight: 700,
              color: accent,
            }}
            aria-label="placeholder chart"
          >
            UI
          </Box>
        </Stack>
        <Stack spacing={0.75} sx={{ mt: 2 }}>
          {checklist.map((item, idx) => (
            <Stack key={idx} direction="row" spacing={1} alignItems="flex-start">
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  mt: 0.5,
                  borderRadius: 0.5,
                  bgcolor: accent,
                  opacity: 0.5,
                }}
              />
              <Typography variant="body2">{item}</Typography>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    data: timelineData,
    isLoading: isTimelineLoading,
    refetch: refetchTimeline,
    dataUpdatedAt: timelineUpdatedAt,
  } = useQuery({
    queryKey: ['dashboard', 'timeline', TIMELINE_WINDOW_MONTHS],
    queryFn: () => projectsApi.getTimeline({ months: TIMELINE_WINDOW_MONTHS }),
  });

  const [savedViews, setSavedViews] = useState<SavedView[]>(() => {
    try {
      const stored = localStorage.getItem('dashboard_saved_views');
      return stored ? (JSON.parse(stored) as SavedView[]) : [];
    } catch {
      return [];
    }
  });
  const [viewName, setViewName] = useState('');
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

  const [selectedDiscipline, setSelectedDiscipline] = useState<string>('all');

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
    selectedProjects.length > 0 ||
    selectedDiscipline !== 'all';

  useEffect(() => {
    localStorage.setItem('dashboard_saved_views', JSON.stringify(savedViews));
  }, [savedViews]);

  const handleSaveView = () => {
    const trimmed = viewName.trim();
    if (!trimmed) return;
    const newView: SavedView = {
      name: trimmed,
      manager: selectedManager,
      type: selectedType,
      client: selectedClient,
      projects: selectedProjects,
    };
    setSavedViews((prev) => {
      const withoutDuplicate = prev.filter((v) => v.name !== trimmed);
      return [...withoutDuplicate, newView];
    });
    setViewName('');
  };

  const applySavedView = (view: SavedView) => {
    startFiltering(() => {
      setSelectedManager(view.manager);
      setSelectedType(view.type);
      setSelectedClient(view.client);
      setSelectedProjects(view.projects);
    });
  };

  const handleRefresh = () => {
    refetchTimeline();
    refetchWarehouse();
  };

  const navigateProjectsWithFilters = (filters: { status?: string; manager?: string; type?: string; client?: string }) => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.manager) params.set('manager', filters.manager);
    if (filters.type) params.set('type', filters.type);
    if (filters.client) params.set('client', filters.client);
    navigate(`/projects?${params.toString()}`);
  };

  const {
    data: warehouseMetrics,
    isLoading: isWarehouseMetricsLoading,
    refetch: refetchWarehouse,
    dataUpdatedAt: warehouseUpdatedAt,
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

  const { data: revitHealthMetrics } = useQuery<RevitHealthDashboardMetrics>({
    queryKey: ['dashboard', 'revit-health', targetProjectIds, selectedDiscipline],
    queryFn: () =>
      dashboardApi.getRevitHealthMetrics({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
        discipline: selectedDiscipline !== 'all' ? selectedDiscipline : undefined,
      }),
  });

  const { data: namingCompliance } = useQuery<NamingComplianceMetrics>({
    queryKey: ['dashboard', 'naming-compliance', targetProjectIds, selectedDiscipline],
    queryFn: () =>
      dashboardApi.getNamingCompliance({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
        discipline: selectedDiscipline !== 'all' ? selectedDiscipline : undefined,
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

  const controlCoveragePct = useMemo(() => {
    if (!warehouseMetrics?.control_models) return null;
    const total =
      (warehouseMetrics.project_health?.projects ?? 0) ||
      warehouseMetrics.control_models.projects_with_control_models +
        warehouseMetrics.control_models.projects_missing;
    if (!total) return null;
    return Math.round((warehouseMetrics.control_models.projects_with_control_models / total) * 1000) / 10;
  }, [warehouseMetrics]);

  const backlogAgeTotal = useMemo(() => {
    const b = warehouseMetrics?.backlog_age;
    if (!b) return 0;
    return (b.bucket_0_7 ?? 0) + (b.bucket_8_30 ?? 0) + (b.bucket_31_90 ?? 0) + (b.bucket_90_plus ?? 0);
  }, [warehouseMetrics]);

  const numberFormatter = (value?: number | null, options?: Intl.NumberFormatOptions) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '--';
    return value.toLocaleString(undefined, options);
  };

  const formatDateTime = (value?: string | null) => {
    if (!value) return '--';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
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

  const lastUpdated = useMemo(() => {
    const timestamps = [timelineUpdatedAt, warehouseUpdatedAt].filter((t): t is number => Boolean(t));
    if (!timestamps.length) return null;
    return new Date(Math.max(...timestamps));
  }, [timelineUpdatedAt, warehouseUpdatedAt]);

  const healthTrendPoints = useMemo(() => {
    const trend = revitHealthMetrics?.trend ?? [];
    const values = trend
      .slice()
      .reverse()
      .map((t) => t.avg_health_score ?? 0);
    return values;
  }, [revitHealthMetrics]);

  const namingCompliancePct =
    namingCompliance?.summary?.compliance_pct != null
      ? Math.round(namingCompliance.summary.compliance_pct * 10) / 10
      : null;

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
            border: (theme) => `1px dashed ${theme.palette.divider}`,
            background: (theme) => theme.palette.background.default,
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
            Wireframe Preview (Power BI parity)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Placeholder layout to mirror the PBI pages: slicers remain global (Project, Building, Discipline, Zone/Location, Date).
            Each block notes the data we need to wire from the warehouse/API.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="File Naming + Control Points"
                description="Table-first view of validation status with project/building/discipline slicers."
                checklist={[
                  'Table: file name, validation status, failed field/value, reason, validated date',
                  'Donuts: Project Base Point vs Survey Point compliance (compliant vs non-compliant)',
                  'Tables: Control Project Base/Survey points and per-model Base/Survey points with compliance',
                ]}
                accent="#0288d1"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="Model Register"
                description="ACC desktop connector inventory by discipline."
                checklist={[
                  'Table: project, discipline, file name, modified date, file location, published-last-week flag',
                  'KPI: number of models (filtered)',
                  'Actions: open in file browser / ACC (future)',
                ]}
                accent="#7b1fa2"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="Issues"
                description="Mirrors PBI: high-level stats + drill-down table."
                checklist={[
                  'KPIs: Active, Total, >30d, Closed since review',
                  'Charts: status donut, priority pie, discipline bar, zone treemap, 90d trend line',
                  'Table: id, clash level/priority, status, title, latest comment, company, location/zone',
                ]}
                accent="#c62828"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="Model Health"
                description="Warnings, grids/levels, families per model with compliance flags."
                checklist={[
                  'KPIs: avg health score, critical files, warnings totals',
                  'Trend: monthly avg health score sparkline',
                  'Table: per-model counts (warnings, links, grids/levels, families) with pass/fail',
                ]}
                accent="#2e7d32"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="Financials & Operations"
                description="Keep current earned value/service progress until richer data lands."
                checklist={[
                  'Gauge: earned value vs claimed vs variance',
                  'Table (future): service milestones, billing phases, slipped items',
                  'Drill links: analytics, data imports, services board',
                ]}
                accent="#ff8f00"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={4}>
              <WireframeCard
                title="Global Filters & Saved Views"
                description="Reuse current filter set plus Building/Zone when data is wired."
                checklist={[
                  'Project, Manager, Type, Client, Discipline',
                  'Planned additions: Building, Zone/Location (for issues and control points)',
                  'Saved views persist across pages',
                ]}
                accent="#546e7a"
              />
            </Grid>
          </Grid>
        </Paper>

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
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} sx={{ mb: 2 }}>
            <TextField
              size="small"
              label="Save current view"
              value={viewName}
              onChange={(e) => setViewName(e.target.value)}
              sx={{ minWidth: { xs: '100%', md: 260 } }}
            />
            <Button variant="outlined" onClick={handleSaveView} disabled={!viewName.trim()}>
              Save View
            </Button>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {savedViews.map((view) => (
                <Chip
                  key={view.name}
                  label={view.name}
                  onClick={() => applySavedView(view)}
                  onDelete={() => setSavedViews((prev) => prev.filter((v) => v.name !== view.name))}
                  size="small"
                />
              ))}
              {!savedViews.length && <Chip label="No saved views yet" size="small" variant="outlined" />}
            </Stack>
          </Stack>
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

            <FormControl size="small" sx={{ minWidth: { xs: '100%', md: 200 } }}>
              <InputLabel id="filter-discipline-label">Discipline</InputLabel>
              <Select
                labelId="filter-discipline-label"
                value={selectedDiscipline}
                label="Discipline"
                onChange={(event: SelectChangeEvent<string>) => {
                  const value = event.target.value;
                  startFiltering(() => setSelectedDiscipline(value));
                }}
              >
                <MenuItem value="all">All</MenuItem>
                {(namingCompliance?.by_discipline || [])
                  .map((d) => d.discipline)
                  .filter((val, idx, arr) => arr.indexOf(val) === idx)
                  .map((discipline) => (
                    <MenuItem key={discipline} value={discipline}>
                      {discipline}
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
              {selectedDiscipline !== 'all' && <Chip size="small" label={`Discipline: ${selectedDiscipline}`} />}
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
                    setSelectedDiscipline('all');
                    setSelectedProjects([]);
                  });
                }}
                variant="outlined"
              />
            </Stack>
          )}
        </Paper>

        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          alignItems={{ md: 'center' }}
          sx={{ mb: 3 }}
        >
          <Typography variant="body2" color="text.secondary">
            {lastUpdated ? `Last refreshed ${lastUpdated.toLocaleString()}` : 'Loading fresh data...'}
          </Typography>
          <Button variant="text" size="small" onClick={handleRefresh}>
            Refresh data
          </Button>
        </Stack>

        {!isWarehouseMetricsLoading && warehouseMetrics && !warehouseMetrics.error && (
          <>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
              Health Overview
            </Typography>
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Open Issues"
                  value={numberFormatter(warehouseMetrics.project_health?.open_issues)}
                  color="primary.main"
                  helper="Current month (warehouse)"
                  onClick={() => navigateProjectsWithFilters({ status: 'Active' })}
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="High Priority"
                  value={numberFormatter(warehouseMetrics.project_health?.high_priority_issues)}
                  color="error.main"
                  helper="Issues flagged critical"
                  onClick={() => navigate('/analytics')}
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Overdue Reviews"
                  value={numberFormatter(warehouseMetrics.project_health?.overdue_reviews)}
                  color="warning.main"
                  helper="Review cycles past due"
                  onClick={() => navigateProjectsWithFilters({ status: 'Active' })}
                />
              </Grid>
              <Grid item xs={12} md={6} lg={3}>
                <StatCard
                  title="Services In Progress"
                  value={numberFormatter(warehouseMetrics.project_health?.services_in_progress)}
                  color="info.main"
                  helper="Active services this month"
                  onClick={() => navigate('/projects')}
                />
              </Grid>
            </Grid>

            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
              Model Ops Signals
            </Typography>
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Typography color="text.secondary" gutterBottom variant="h6">
                        Model Readiness
                      </Typography>
                    </Stack>
                    <Stack spacing={1} sx={{ mb: 2 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {controlCoveragePct != null ? `${controlCoveragePct}%` : '--'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Projects with active control models
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        With control models: {numberFormatter(warehouseMetrics.control_models?.projects_with_control_models)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Missing: {numberFormatter(warehouseMetrics.control_models?.projects_missing)}
                      </Typography>
                    </Stack>
                    <StackedBar
                      segments={[
                        { value: warehouseMetrics.control_models?.projects_with_control_models || 0, color: '#2e7d32' },
                        { value: warehouseMetrics.control_models?.projects_missing || 0, color: '#c62828' },
                      ]}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Data Freshness
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="body2" color="text.secondary">
                        Revizto last run: {formatDateTime(warehouseMetrics.data_freshness?.revizto_last_run)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Projects extracted: {numberFormatter(warehouseMetrics.data_freshness?.revizto_projects_extracted)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ACC import: {formatDateTime(warehouseMetrics.data_freshness?.acc_last_import)}
                      </Typography>
                      {warehouseMetrics.data_freshness?.acc_last_import_project_id ? (
                        <Typography variant="body2" color="text.secondary">
                          Project ID: {warehouseMetrics.data_freshness.acc_last_import_project_id}
                        </Typography>
                      ) : null}
                    </Stack>
                    <Button sx={{ mt: 2 }} size="small" onClick={() => navigate('/data-imports')}>
                      Check imports
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              {namingCompliance && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                      File Naming Compliance
                    </Typography>
                  </Grid>

                  <Grid item xs={12} md={6} lg={3}>
                    <StatCard
                      title="Compliance"
                      value={namingCompliancePct != null ? `${namingCompliancePct}%` : '--'}
                      helper={`Valid: ${numberFormatter(namingCompliance.summary.valid_files)} / ${numberFormatter(
                        namingCompliance.summary.total_files,
                      )}`}
                      color="success.main"
                    />
                  </Grid>

                  <Grid item xs={12} md={6} lg={3}>
                    <StatCard
                      title="Invalid Files"
                      value={numberFormatter(namingCompliance.summary.invalid_files)}
                      helper={`Last validated: ${formatDateTime(namingCompliance.summary.latest_validated)}`}
                      color="error.main"
                    />
                  </Grid>

                  <Grid item xs={12} md={6} lg={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom variant="h6">
                          By Discipline
                        </Typography>
                        <Stack spacing={1}>
                          {(namingCompliance.by_discipline || []).map((d) => (
                            <Stack key={d.discipline} direction="row" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2">{d.discipline}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {numberFormatter(d.valid_files)}/{numberFormatter(d.total_files)}{' '}
                                {d.valid_pct != null ? `(${d.valid_pct}%)` : ''}
                              </Typography>
                            </Stack>
                          ))}
                          {(!namingCompliance.by_discipline || namingCompliance.by_discipline.length === 0) && (
                            <Typography variant="body2" color="text.secondary">
                              No discipline data available.
                            </Typography>
                          )}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom variant="h6">
                          Recent Invalid Files
                        </Typography>
                        <Box sx={{ overflowX: 'auto' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                              <tr>
                                <th align="left">File</th>
                                <th align="left">Project</th>
                                <th align="left">Discipline</th>
                                <th align="left">Reason</th>
                                <th align="left">Failed Field</th>
                                <th align="left">Validated</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(namingCompliance.recent_invalid || []).map((row, idx) => (
                                <tr key={idx}>
                                  <td>{row.file_name}</td>
                                  <td>{row.project_name}</td>
                                  <td>{row.discipline}</td>
                                  <td>{row.validation_reason || row.validation_status}</td>
                                  <td>{row.failed_field_reason || row.failed_field_name}</td>
                                  <td>{formatDateTime(row.validated_date)}</td>
                                </tr>
                              ))}
                              {(!namingCompliance.recent_invalid || namingCompliance.recent_invalid.length === 0) && (
                                <tr>
                                  <td colSpan={6}>
                                    <Typography variant="body2" color="text.secondary">
                                      No invalid files recently.
                                    </Typography>
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </>
              )}

              <Grid item xs={12} md={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Backlog Age (open issues)
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="baseline" sx={{ mb: 1 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {numberFormatter(backlogAgeTotal)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        open issues tracked
                      </Typography>
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      Avg age: {numberFormatter(warehouseMetrics.backlog_age?.avg_age_days, { maximumFractionDigits: 1 })} days
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <StackedBar
                        segments={[
                          { value: warehouseMetrics.backlog_age?.bucket_0_7 || 0, color: '#2e7d32' },
                          { value: warehouseMetrics.backlog_age?.bucket_8_30 || 0, color: '#66bb6a' },
                          { value: warehouseMetrics.backlog_age?.bucket_31_90 || 0, color: '#ffa000' },
                          { value: warehouseMetrics.backlog_age?.bucket_90_plus || 0, color: '#c62828' },
                        ]}
                      />
                      <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
                        <Chip size="small" label={`0-7d: ${numberFormatter(warehouseMetrics.backlog_age?.bucket_0_7)}`} />
                        <Chip size="small" label={`8-30d: ${numberFormatter(warehouseMetrics.backlog_age?.bucket_8_30)}`} />
                        <Chip size="small" label={`31-90d: ${numberFormatter(warehouseMetrics.backlog_age?.bucket_31_90)}`} />
                        <Chip size="small" label={`90d+: ${numberFormatter(warehouseMetrics.backlog_age?.bucket_90_plus)}`} />
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {revitHealthMetrics && (
              <>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                  Model Health
                </Typography>
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={6} lg={3}>
                    <StatCard
                      title="Avg Health Score"
                      value={
                        revitHealthMetrics.summary.avg_health_score != null
                          ? `${Math.round(revitHealthMetrics.summary.avg_health_score)}%`
                          : '--'
                      }
                      helper={`Files: ${numberFormatter(revitHealthMetrics.summary.total_files)}`}
                    />
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                    <StatCard
                      title="Good / Critical Files"
                      value={`${numberFormatter(revitHealthMetrics.summary.good_files)} / ${numberFormatter(
                        revitHealthMetrics.summary.critical_files,
                      )}`}
                      helper={`Link issues: ${numberFormatter(revitHealthMetrics.summary.files_with_link_issues)}`}
                      color="info.main"
                    />
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                    <StatCard
                      title="Warnings"
                      value={numberFormatter(revitHealthMetrics.summary.total_warnings)}
                      helper={`Critical: ${numberFormatter(revitHealthMetrics.summary.total_critical_warnings)}`}
                      color="warning.main"
                    />
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom variant="h6">
                          Health Trend (avg score)
                        </Typography>
                        <Sparkline points={healthTrendPoints} color="#2e7d32" />
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Latest check: {formatDateTime(revitHealthMetrics.summary.latest_check_date)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}

            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
              Workload & Risk
            </Typography>
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Box>
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
                      </Box>
                      <Button size="small" onClick={() => navigate('/analytics')}>View in Analytics</Button>
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
                    <Typography variant="body2" color="text.secondary">
                      Backlog days: {numberFormatter(latestIssueTrend?.last.avg_backlog_days, { maximumFractionDigits: 1 })}
                      {' '}| Urgency: {numberFormatter(latestIssueTrend?.last.avg_urgency, { maximumFractionDigits: 1 })}
                      {' '}| Sentiment: {numberFormatter(latestIssueTrend?.last.avg_sentiment, { maximumFractionDigits: 1 })}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Typography color="text.secondary" gutterBottom variant="h6">
                        Review Performance
                      </Typography>
                      <Button size="small" onClick={() => navigateProjectsWithFilters({ status: 'Active' })}>
                        See projects
                      </Button>
                    </Stack>
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

              {stackedHistory && (
                <Grid item xs={12} lg={4}>
                  <Card sx={{ height: '100%' }}>
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
                </Grid>
              )}
            </Grid>

            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
              Financials & Delivery
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Services & Financials
                    </Typography>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }}>
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
                        <Button sx={{ mt: 1 }} size="small" onClick={() => navigate('/projects')}>
                          Go to services
                        </Button>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Drill-down
                    </Typography>
                    <Stack spacing={1}>
                      <Button variant="outlined" size="small" onClick={() => navigate('/analytics')}>
                        Open Analytics
                      </Button>
                      <Button variant="outlined" size="small" onClick={() => navigate('/data-imports')}>
                        Data Imports health
                      </Button>
                      <Button variant="outlined" size="small" onClick={() => navigate('/projects')}>
                        View Services Board
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </>
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
