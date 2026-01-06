import { Profiler, useDeferredValue, useEffect, useMemo, useState, useTransition, type ReactNode } from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
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
  Button,
  TextField,
  Tabs,
  Tab,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material/Select';
import { useQuery } from '@tanstack/react-query';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Treemap,
  XAxis,
  YAxis,
} from 'recharts';
import { projectsApi } from '@/api';
import { dashboardApi } from '@/api/dashboard';
import DashboardTimelineChart from '@/components/DashboardTimelineChart';
import type {
  DashboardTimelineProject,
  WarehouseDashboardMetrics,
  RevitHealthDashboardMetrics,
  NamingComplianceMetrics,
  DashboardIssuesKpis,
  DashboardIssuesCharts,
  DashboardIssuesTable,
} from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';
import { useNavigate } from 'react-router-dom';
import { chartColorSchemes } from '@/components/dashboards/themes';

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

type TabPanelProps = {
  children: ReactNode;
  value: number;
  index: number;
};

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <Box role="tabpanel" hidden={value !== index} id={`dashboard-tabpanel-${index}`} aria-labelledby={`dashboard-tab-${index}`}>
      {value === index ? children : null}
    </Box>
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
  const [dashboardTab, setDashboardTab] = useState(0);

  const timelineProjects = timelineData?.projects ?? EMPTY_PROJECTS;

  const filterOptions = useMemo(
    () => {
      const managers = new Set<string>();
      const types = new Set<string>();
      const clients = new Set<string>();
      const normalize = (value?: string | null) => (value ?? '').trim();

      timelineProjects.forEach((project) => {
        if (project.project_manager) {
          const cleaned = normalize(project.project_manager);
          if (cleaned) managers.add(cleaned);
        }
        if (project.project_type) {
          const cleaned = normalize(project.project_type);
          if (cleaned) types.add(cleaned);
        }
        if (project.client_name) {
          const cleaned = normalize(project.client_name);
          if (cleaned) clients.add(cleaned);
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
  const [issueStatus, setIssueStatus] = useState<string>('all');
  const [issuePriority, setIssuePriority] = useState<string>('all');
  const [issueDiscipline, setIssueDiscipline] = useState<string>('all');
  const [issueZone, setIssueZone] = useState<string>('all');
  const [issuePage, setIssuePage] = useState(1);
  const [issuePageSize, setIssuePageSize] = useState(25);

  const filteredProjects = useMemo(() => {
    if (!timelineProjects.length) {
      return timelineProjects;
    }
    const normalize = (value?: string | null) => (value ?? '').trim().toLowerCase();

    return timelineProjects.filter((project) => {
      const managerMatches =
        selectedManager === 'all' ||
        normalize(project.project_manager) === normalize(selectedManager);
      const typeMatches =
        selectedType === 'all' || normalize(project.project_type) === normalize(selectedType);
      const clientMatches =
        selectedClient === 'all' || normalize(project.client_name) === normalize(selectedClient);
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

  useEffect(() => {
    setIssuePage(1);
  }, [issueStatus, issuePriority, issueDiscipline, issueZone, targetProjectIds]);

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
    refetchIssuesKpis();
    refetchIssuesCharts();
    refetchIssuesTable();
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
    isError: isWarehouseMetricsError,
    error: warehouseMetricsError,
    refetch: refetchWarehouse,
    dataUpdatedAt: warehouseUpdatedAt,
  } = useQuery<WarehouseDashboardMetrics>({
    queryKey: ['dashboard', 'warehouse-metrics', targetProjectIds],
    queryFn: () =>
      dashboardApi.getWarehouseMetrics({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
      }),
  });

  const { data: issuesKpis, refetch: refetchIssuesKpis } = useQuery<DashboardIssuesKpis>({
    queryKey: ['dashboard', 'issues-kpis', targetProjectIds],
    queryFn: () =>
      dashboardApi.getIssuesKpis({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
      }),
  });

  const { data: issuesCharts, refetch: refetchIssuesCharts } = useQuery<DashboardIssuesCharts>({
    queryKey: ['dashboard', 'issues-charts', targetProjectIds],
    queryFn: () =>
      dashboardApi.getIssuesCharts({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
      }),
  });

  const {
    data: issuesTable,
    isLoading: isIssuesTableLoading,
    refetch: refetchIssuesTable,
  } = useQuery<DashboardIssuesTable>({
    queryKey: [
      'dashboard',
      'issues-table',
      targetProjectIds,
      issueStatus,
      issuePriority,
      issueDiscipline,
      issueZone,
      issuePage,
      issuePageSize,
    ],
    queryFn: () =>
      dashboardApi.getIssuesTable({
        projectIds: targetProjectIds.length ? targetProjectIds : undefined,
        status: issueStatus !== 'all' ? issueStatus : undefined,
        priority: issuePriority !== 'all' ? issuePriority : undefined,
        discipline: issueDiscipline !== 'all' ? issueDiscipline : undefined,
        zone: issueZone !== 'all' ? issueZone : undefined,
        page: issuePage,
        pageSize: issuePageSize,
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

  const warehouseMetricsErrorMessage =
    warehouseMetrics?.error ||
    (warehouseMetricsError instanceof Error ? warehouseMetricsError.message : undefined) ||
    (isWarehouseMetricsError ? 'Failed to load warehouse metrics.' : undefined);
  const hasWarehouseMetrics =
    !isWarehouseMetricsLoading && !isWarehouseMetricsError && !warehouseMetricsErrorMessage && Boolean(warehouseMetrics);

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

  const renderOptionLabel = (option: string) => (option === 'all' ? 'All' : option);

  const issuesPalette = useMemo(
    () => [
      ...chartColorSchemes.disciplines,
      '#ef6c00',
      '#00897b',
      '#5c6bc0',
      '#8d6e63',
      '#78909c',
    ],
    [],
  );

  const getSliceColor = (index: number) => issuesPalette[index % issuesPalette.length];

  const statusData = issuesCharts?.status ?? [];
  const priorityData = issuesCharts?.priority ?? [];
  const disciplineData = issuesCharts?.discipline ?? [];
  const zoneData = issuesCharts?.zone ?? [];
  const trendData = issuesCharts?.trend_90d ?? [];

  const zoneTreemapData = useMemo(
    () =>
      zoneData.map((entry) => ({
        name: entry.label,
        size: entry.value,
      })),
    [zoneData],
  );

  const issueStatusOptions = useMemo(() => ['all', ...statusData.map((row) => row.label)], [statusData]);
  const issuePriorityOptions = useMemo(() => ['all', ...priorityData.map((row) => row.label)], [priorityData]);
  const issueDisciplineOptions = useMemo(
    () => ['all', ...disciplineData.map((row) => row.label)],
    [disciplineData],
  );
  const issueZoneOptions = useMemo(() => ['all', ...zoneData.map((row) => row.label)], [zoneData]);

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
                value={selectedProjects}
                label="Projects"
                onChange={(event) => {
                  const raw = event.target.value;
                  const values = Array.isArray(raw) ? raw : [raw];
                  const ids = values.map((v) => Number(v)).filter((v) => !Number.isNaN(v));
                  startFiltering(() => setSelectedProjects(ids));
                }}
                renderValue={(selected) => {
                  if (!selected.length) return 'All';
                  const names = timelineProjects
                    .filter((p) => selected.includes(p.project_id ?? -1))
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
                {isFiltering && ' updating...'}
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

        {isWarehouseMetricsLoading && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Loading warehouse metrics...
          </Typography>
        )}

        {!isWarehouseMetricsLoading && warehouseMetricsErrorMessage && (
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
            <Typography variant="body2" color="text.secondary">
              Warehouse metrics are unavailable: {warehouseMetricsErrorMessage}
            </Typography>
          </Paper>
        )}

        <Tabs
          value={dashboardTab}
          onChange={(_, value) => setDashboardTab(value)}
          sx={{ mb: 3 }}
        >
          <Tab label="Overview" id="dashboard-tab-0" aria-controls="dashboard-tabpanel-0" />
          <Tab label="Issues" id="dashboard-tab-1" aria-controls="dashboard-tabpanel-1" />
          <Tab label="Health Metrics" id="dashboard-tab-2" aria-controls="dashboard-tabpanel-2" />
        </Tabs>

        <TabPanel value={dashboardTab} index={0}>
          {hasWarehouseMetrics && (
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
                Workload & Risk
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
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
        </TabPanel>

        <TabPanel value={dashboardTab} index={1}>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
            Issues
          </Typography>
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Active"
                value={numberFormatter(issuesKpis?.active_issues)}
                color="primary.main"
                helper="Open across selected projects"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Total"
                value={numberFormatter(issuesKpis?.total_issues)}
                color="info.main"
                helper="Latest snapshot total"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title=">30d"
                value={numberFormatter(issuesKpis?.over_30_days)}
                color="warning.main"
                helper="Backlog aging beyond 30 days"
              />
            </Grid>
            <Grid item xs={12} md={6} lg={3}>
              <StatCard
                title="Closed Since Review"
                value={numberFormatter(issuesKpis?.closed_since_review)}
                color="success.main"
                helper="Closed after last review cycle"
              />
            </Grid>
          </Grid>

            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Status Mix
                    </Typography>
                    {statusData.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <PieChart>
                          <Pie
                            data={statusData}
                            dataKey="value"
                            nameKey="label"
                            innerRadius={60}
                            outerRadius={90}
                            paddingAngle={2}
                          >
                            {statusData.map((entry, idx) => (
                              <Cell key={entry.label} fill={getSliceColor(idx)} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend verticalAlign="bottom" height={48} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No status data available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Priority Mix
                    </Typography>
                    {priorityData.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <PieChart>
                          <Pie data={priorityData} dataKey="value" nameKey="label" outerRadius={100} paddingAngle={2}>
                            {priorityData.map((entry, idx) => (
                              <Cell key={entry.label} fill={getSliceColor(idx)} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend verticalAlign="bottom" height={48} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No priority data available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Discipline Split
                    </Typography>
                    {disciplineData.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={disciplineData} layout="vertical" margin={{ left: 24 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" allowDecimals={false} />
                          <YAxis type="category" dataKey="label" width={90} />
                          <Tooltip />
                          <Bar dataKey="value">
                            {disciplineData.map((entry, idx) => (
                              <Cell key={entry.label} fill={getSliceColor(idx)} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No discipline data available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      Zone Coverage
                    </Typography>
                    {zoneTreemapData.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <Treemap
                          data={zoneTreemapData}
                          dataKey="size"
                          nameKey="name"
                          stroke="#ffffff"
                          fill="#90caf9"
                          content={({ x, y, width, height, index, name, value }) => {
                            const fill = getSliceColor(index);
                            return (
                              <g>
                                <rect x={x} y={y} width={width} height={height} fill={fill} stroke="#ffffff" />
                                {width > 80 && height > 24 ? (
                                  <text x={x + 6} y={y + 18} fill="#ffffff" fontSize={12}>
                                    {name}
                                  </text>
                                ) : null}
                                {width > 80 && height > 40 ? (
                                  <text x={x + 6} y={y + 36} fill="#ffffff" fontSize={12}>
                                    {value}
                                  </text>
                                ) : null}
                              </g>
                            );
                          }}
                        />
                      </ResponsiveContainer>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No zone data available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6} lg={8}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      90 Day Trend
                    </Typography>
                    {trendData.length ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <LineChart data={trendData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tickFormatter={(value) => (value ? new Date(value).toLocaleDateString() : '')}
                          />
                          <YAxis allowDecimals={false} />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="open" stroke="#f57c00" strokeWidth={2} />
                          <Line type="monotone" dataKey="closed" stroke="#2e7d32" strokeWidth={2} />
                          <Line type="monotone" dataKey="total" stroke="#1976d2" strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No trend data available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }}>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Issue Drill-down
                  </Typography>
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ flexWrap: 'wrap', flex: 1 }}>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                      <InputLabel id="issues-status-label">Status</InputLabel>
                      <Select
                        labelId="issues-status-label"
                        value={issueStatus}
                        label="Status"
                        onChange={(event) => setIssueStatus(event.target.value)}
                      >
                        {issueStatusOptions.map((option) => (
                          <MenuItem key={option} value={option}>
                            {renderOptionLabel(option)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                      <InputLabel id="issues-priority-label">Priority</InputLabel>
                      <Select
                        labelId="issues-priority-label"
                        value={issuePriority}
                        label="Priority"
                        onChange={(event) => setIssuePriority(event.target.value)}
                      >
                        {issuePriorityOptions.map((option) => (
                          <MenuItem key={option} value={option}>
                            {renderOptionLabel(option)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                      <InputLabel id="issues-discipline-label">Discipline</InputLabel>
                      <Select
                        labelId="issues-discipline-label"
                        value={issueDiscipline}
                        label="Discipline"
                        onChange={(event) => setIssueDiscipline(event.target.value)}
                      >
                        {issueDisciplineOptions.map((option) => (
                          <MenuItem key={option} value={option}>
                            {renderOptionLabel(option)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                      <InputLabel id="issues-zone-label">Zone</InputLabel>
                      <Select
                        labelId="issues-zone-label"
                        value={issueZone}
                        label="Zone"
                        onChange={(event) => setIssueZone(event.target.value)}
                      >
                        {issueZoneOptions.map((option) => (
                          <MenuItem key={option} value={option}>
                            {renderOptionLabel(option)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <Button
                      variant="outlined"
                      onClick={() => {
                        setIssueStatus('all');
                        setIssuePriority('all');
                        setIssueDiscipline('all');
                        setIssueZone('all');
                      }}
                    >
                      Clear
                    </Button>
                  </Stack>
                </Stack>
                <Divider sx={{ my: 2 }} />
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Clash / Priority</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Latest Comment</TableCell>
                        <TableCell>Company</TableCell>
                        <TableCell>Location / Zone</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(issuesTable?.rows || []).map((row) => {
                        const locationBits = [row.location_root, row.location_building, row.location_level]
                          .filter(Boolean)
                          .join(' / ');
                        return (
                          <TableRow key={`${row.issue_id}-${row.source || 'issue'}`}>
                            <TableCell>{row.issue_id}</TableCell>
                            <TableCell>
                              <Typography variant="body2">{row.clash_level || '--'}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {row.priority || '--'}
                              </Typography>
                            </TableCell>
                            <TableCell>{row.status || '--'}</TableCell>
                            <TableCell>{row.title || '--'}</TableCell>
                            <TableCell sx={{ maxWidth: 320 }}>
                              <Typography variant="body2" noWrap>
                                {row.latest_comment || '--'}
                              </Typography>
                            </TableCell>
                            <TableCell>{row.company || '--'}</TableCell>
                            <TableCell>
                              <Typography variant="body2">{row.zone || '--'}</Typography>
                              {locationBits ? (
                                <Typography variant="caption" color="text.secondary">
                                  {locationBits}
                                </Typography>
                              ) : null}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                      {!isIssuesTableLoading && (issuesTable?.rows || []).length === 0 && (
                        <TableRow>
                          <TableCell colSpan={7}>
                            <Typography variant="body2" color="text.secondary">
                              No issues match the current filters.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                      {isIssuesTableLoading && (
                        <TableRow>
                          <TableCell colSpan={7}>
                            <Typography variant="body2" color="text.secondary">
                              Loading issues...
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
                <TablePagination
                  component="div"
                  count={issuesTable?.total_count ?? 0}
                  page={Math.max(issuePage - 1, 0)}
                  onPageChange={(_, page) => setIssuePage(page + 1)}
                  rowsPerPage={issuePageSize}
                  onRowsPerPageChange={(event) => {
                    const next = parseInt(event.target.value, 10);
                    setIssuePageSize(Number.isNaN(next) ? 25 : next);
                    setIssuePage(1);
                  }}
                  rowsPerPageOptions={[10, 25, 50]}
                />
              </CardContent>
            </Card>
        </TabPanel>

        <TabPanel value={dashboardTab} index={2}>
          {hasWarehouseMetrics && (
            <>
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
            </>
          )}

          {namingCompliance && (
            <>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                File Naming Compliance
              </Typography>
              <Grid container spacing={3} sx={{ mb: 3 }}>
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
              </Grid>
            </>
          )}

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
        </TabPanel>

      </Box>
    </Profiler>
  );
}
