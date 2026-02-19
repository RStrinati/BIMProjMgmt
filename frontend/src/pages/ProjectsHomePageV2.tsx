import { useEffect, useMemo, useState, lazy, Suspense, useCallback } from 'react';
import type { MouseEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  MenuItem,
  Popover,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableFooter,
  TableHead,
  TableRow,
  TableSortLabel,
  Card,
  CardContent,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  ViewColumn,
  FilterAlt,
  ChevronRight,
  PersonOutline,
  FlagOutlined,
  BusinessOutlined,
  DonutSmall,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { projectsApi, usersApi } from '@/api';
import type { ProjectSummary, ProjectAggregates, User } from '@/types/api';
import { TimelinePanel } from '@/components/timeline_v2/TimelinePanel';
import { featureFlags } from '@/config/featureFlags';
import {
  PROJECT_FIELD_MAP,
  renderBoardSnippet,
  renderFieldValue,
  type ProjectFieldDefinition,
} from '@/features/projects/fields/ProjectFieldRegistry';
import { useProjectViewLayout } from '@/features/projects/fields/useProjectViewLayout';
import { ProjectColumnsPopover } from '@/features/projects/fields/ProjectColumnsPopover';

const ProjectFormDialog = lazy(() => import('@/components/ProjectFormDialog'));

type DisplayMode = 'list' | 'board' | 'timeline';

type ViewId = 'all' | 'active' | 'on_hold' | 'completed' | 'my_work' | 'recently_updated';

type ViewState = {
  viewId: ViewId;
  searchTerm: string;
};

type SortField = string;
type SortOrder = 'asc' | 'desc';

type FilterCategory = 'lead' | 'status' | 'client' | 'priority';

type FilterSelections = Record<FilterCategory, string[]>;

const VIEW_STORAGE_KEY = 'projects_panel_view_state';
const DISPLAY_STORAGE_KEY = 'projects_home_display_mode';
const FILTER_STORAGE_KEY = 'projects_home_filter_selections';

const VIEW_IDS: ViewId[] = ['all', 'active', 'on_hold', 'completed', 'my_work', 'recently_updated'];

const DEFAULT_VIEW_STATE: ViewState = {
  viewId: 'all',
  searchTerm: '',
};

const safeParseStoredViewState = () => {
  if (typeof window === 'undefined') {
    return DEFAULT_VIEW_STATE;
  }
  const raw = window.localStorage.getItem(VIEW_STORAGE_KEY);
  if (!raw) {
    return DEFAULT_VIEW_STATE;
  }
  try {
    const parsed = JSON.parse(raw) as Partial<ViewState>;
    if (!parsed || typeof parsed !== 'object') {
      return DEFAULT_VIEW_STATE;
    }
    const parsedViewId = VIEW_IDS.includes(parsed.viewId as ViewId)
      ? (parsed.viewId as ViewId)
      : DEFAULT_VIEW_STATE.viewId;
    return {
      viewId: parsedViewId,
      searchTerm: typeof parsed.searchTerm === 'string' ? parsed.searchTerm : DEFAULT_VIEW_STATE.searchTerm,
    };
  } catch {
    return DEFAULT_VIEW_STATE;
  }
};

const safeParseStoredFilters = (): FilterSelections => {
  if (typeof window === 'undefined') {
    return { lead: [], status: [], client: [], priority: [] };
  }
  const raw = window.localStorage.getItem(FILTER_STORAGE_KEY);
  if (!raw) {
    return { lead: [], status: [], client: [], priority: [] };
  }
  try {
    const parsed = JSON.parse(raw) as Partial<FilterSelections> | null;
    return {
      lead: Array.isArray(parsed?.lead) ? parsed!.lead : [],
      status: Array.isArray(parsed?.status) ? parsed!.status : [],
      client: Array.isArray(parsed?.client) ? parsed!.client : [],
      priority: Array.isArray(parsed?.priority) ? parsed!.priority : [],
    };
  } catch {
    return { lead: [], status: [], client: [], priority: [] };
  }
};

const readDisplayMode = (): DisplayMode => {
  if (typeof window === 'undefined') {
    return 'list';
  }
  const raw = window.localStorage.getItem(DISPLAY_STORAGE_KEY);
  if (raw === 'board' || raw === 'timeline' || raw === 'list') {
    return raw;
  }
  return 'list';
};

const parseDateValue = (value?: string | null) => {
  if (!value) {
    return 0;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
};

const useDebouncedValue = <T,>(value: T, delayMs: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(handle);
  }, [value, delayMs]);
  return debouncedValue;
};

const STATUS_OPTIONS = [
  { label: 'Active', value: 'Active' },
  { label: 'On Hold', value: 'On Hold' },
  { label: 'Completed', value: 'Completed' },
];

const PRIORITY_OPTIONS = [
  { label: 'Low', value: 1 },
  { label: 'Medium', value: 2 },
  { label: 'High', value: 3 },
  { label: 'Critical', value: 4 },
];

const toDateInputValue = (value?: string | null) => {
  if (!value) {
    return '';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return '';
  }
  return parsed.toISOString().slice(0, 10);
};

type EditableTextCellProps = {
  value: string;
  onCommit: (nextValue: string) => void;
  type?: 'text' | 'date';
};

const EditableTextCell = ({ value, onCommit, type = 'text' }: EditableTextCellProps) => {
  const [draft, setDraft] = useState(value);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  const handleBlur = () => {
    if (draft !== value) {
      onCommit(draft);
    }
  };

  return (
    <TextField
      variant="standard"
      size="small"
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={handleBlur}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.currentTarget.blur();
        }
        if (event.key === 'Escape') {
          setDraft(value);
          event.currentTarget.blur();
        }
      }}
      type={type}
      inputProps={{ style: { fontSize: 13 } }}
    />
  );
};

type EditableSelectCellProps<T extends string | number> = {
  value: T | '';
  options: Array<{ label: string; value: T | '' }>;
  onCommit: (nextValue: T | '') => void;
};

const EditableSelectCell = <T extends string | number>({
  value,
  options,
  onCommit,
}: EditableSelectCellProps<T>) => (
  <TextField
    select
    variant="standard"
    size="small"
    value={value}
    onChange={(event) => onCommit(event.target.value as T)}
    onClick={(event) => event.stopPropagation()}
    inputProps={{ style: { fontSize: 13 } }}
    sx={{ minWidth: 120 }}
  >
    {options.map((option) => (
      <MenuItem key={option.label} value={option.value}>
        {option.label}
      </MenuItem>
    ))}
  </TextField>
);

const normalizeStatusValue = (status?: string | null) => {
  const normalized = (status ?? '').toLowerCase().replace(/\s+/g, '_');
  if (normalized === 'active') return 'Active';
  if (normalized === 'on_hold') return 'On Hold';
  if (normalized === 'completed') return 'Completed';
  return status ?? '';
};

const resolvePriorityValue = (value: ProjectSummary['priority']) => {
  if (value == null) {
    return '';
  }
  if (typeof value === 'number') {
    return value;
  }
  const trimmed = value.toString().trim();
  if (!trimmed) {
    return '';
  }
  if (/^\d+$/.test(trimmed)) {
    return Number(trimmed);
  }
  const match = PRIORITY_OPTIONS.find((option) => option.label.toLowerCase() === trimmed.toLowerCase());
  return match ? match.value : '';
};

export default function ProjectsHomePageV2() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const storedViewState = useMemo(() => safeParseStoredViewState(), []);
  const [displayMode, setDisplayMode] = useState<DisplayMode>(readDisplayMode);
  const [viewId, setViewId] = useState<ViewId>(storedViewState.viewId);
  const [searchTerm, setSearchTerm] = useState(storedViewState.searchTerm);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sortField, setSortField] = useState<SortField>('project_name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [columnsAnchorEl, setColumnsAnchorEl] = useState<HTMLElement | null>(null);
  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(null);
  const [activeFilterCategory, setActiveFilterCategory] = useState<FilterCategory>('lead');
  const [filterSearch, setFilterSearch] = useState('');
  const [filterSelections, setFilterSelections] = useState<FilterSelections>(safeParseStoredFilters);

  const currentUserId = useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    const raw = window.localStorage.getItem('current_user_id') || window.localStorage.getItem('user_id');
    if (!raw) {
      return null;
    }
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, []);

  const listLayout = useProjectViewLayout('list');
  const boardLayout = useProjectViewLayout('board');
  const timelineLayout = useProjectViewLayout('timeline');

  useEffect(() => {
    if (viewId === 'my_work' && currentUserId == null) {
      setViewId('all');
    }
  }, [viewId, currentUserId]);

  const viewDefinitions = useMemo(
    () => [
      { id: 'all' as const, label: 'All projects', sort: undefined },
      { id: 'active' as const, label: 'Active', sort: undefined },
      { id: 'on_hold' as const, label: 'On Hold', sort: undefined },
      { id: 'completed' as const, label: 'Completed', sort: undefined },
      { id: 'my_work' as const, label: 'My Work', sort: undefined },
      {
        id: 'recently_updated' as const,
        label: 'Recently Updated',
        sort: (a: ProjectSummary, b: ProjectSummary) =>
          parseDateValue(b.updated_at || b.created_at) - parseDateValue(a.updated_at || a.created_at),
      },
    ],
    [currentUserId],
  );

  const activeView = viewDefinitions.find((view) => view.id === viewId) ?? viewDefinitions[0];

  const resolveSortValue = useCallback((project: ProjectSummary, fieldId: string) => {
    const field = PROJECT_FIELD_MAP.get(fieldId);
    if (!field) {
      return '';
    }
    const raw = field.accessor(project);
    if (field.format === 'date') {
      return parseDateValue(raw as string);
    }
    if (field.format === 'currency' || field.format === 'number' || field.format === 'percent') {
      const numeric = Number(raw);
      return Number.isFinite(numeric) ? numeric : 0;
    }
    return (raw ?? '').toString().toLowerCase();
  }, []);

  const debouncedSearchTerm = useDebouncedValue(searchTerm, 300);

  const {
    data: projects = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['projects-summary', viewId, debouncedSearchTerm, currentUserId],
    queryFn: () =>
      projectsApi.getSummary({
        viewId,
        searchTerm: debouncedSearchTerm,
        currentUserId,
      }),
  });

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const { data: aggregates } = useQuery<ProjectAggregates>({
    queryKey: ['projects-aggregates', viewId, debouncedSearchTerm, currentUserId],
    queryFn: () =>
      projectsApi.getAggregates({
        viewId,
        searchTerm: debouncedSearchTerm,
        currentUserId,
      }),
    enabled: displayMode === 'list',
    staleTime: 30_000,
  });

  // Fetch batch finance summary using deterministic fee model
  const { data: financeSummary } = useQuery({
    queryKey: ['projects-finance-summary'],
    queryFn: () => projectsApi.getProjectsFinanceSummary(),
    staleTime: 60_000, // Cache for 1 minute
  });

  // Merge finance data with projects
  const projectsWithFinance = useMemo(() => {
    if (!financeSummary?.projects) {
      return projects;
    }
    const financeMap = new Map(
      financeSummary.projects.map((f) => [f.project_id, f])
    );
    return projects.map((project) => {
      const finance = financeMap.get(project.project_id);
      if (!finance) {
        return project;
      }
      const agreedTotal = Number(finance.agreed_fee_total ?? 0) || 0;
      const earnedValue = Number(finance.earned_value ?? 0) || 0;
      const earnedValuePct = agreedTotal > 0 ? (earnedValue / agreedTotal) * 100 : 0;
      return {
        ...project,
        agreed_fee: finance.agreed_fee_total,
        billed_to_date: finance.billed_total,
        unbilled_amount: finance.unbilled_total,
        earned_value: finance.earned_value,
        earned_value_pct: earnedValuePct,
        invoice_pipeline_this_month: finance.pipeline_this_month,
      };
    });
  }, [projects, financeSummary]);

  const summaryById = useMemo(
    () =>
      projectsWithFinance.reduce<Record<number, ProjectSummary>>((acc, project) => {
        acc[project.project_id] = project;
        return acc;
      }, {}),
    [projectsWithFinance],
  );

  const applyProjectPatch = useCallback(
    async (projectId: number, patch: Record<string, unknown>) => {
      await projectsApi.patch(projectId, patch as any);
      queryClient.invalidateQueries({ queryKey: ['projects-summary'] });
      queryClient.invalidateQueries({ queryKey: ['projects-aggregates'] });
      queryClient.invalidateQueries({ queryKey: ['timeline-v2'] });
    },
    [queryClient],
  );

  const filteredProjects = useMemo(() => {
    const sorted = activeView.sort ? [...projectsWithFinance].sort(activeView.sort) : [...projectsWithFinance];
    const viewFiltered =
      viewId === 'my_work' && currentUserId != null
        ? sorted.filter((project) => {
            if (project.internal_lead == null) {
              return false;
            }
            return Number(project.internal_lead) === currentUserId;
          })
        : sorted;

    const hasLeadFilters = filterSelections.lead.length > 0;
    const hasStatusFilters = filterSelections.status.length > 0;
    const hasClientFilters = filterSelections.client.length > 0;
    const hasPriorityFilters = filterSelections.priority.length > 0;

    const filtered = viewFiltered.filter((project) => {
      if (hasLeadFilters) {
        const leadKey =
          project.internal_lead == null ? 'unassigned' : `id:${project.internal_lead}`;
        if (!filterSelections.lead.includes(leadKey)) {
          return false;
        }
      }
      if (hasStatusFilters) {
        const statusKey = project.status ? normalizeStatusValue(project.status) : 'unassigned';
        if (!filterSelections.status.includes(statusKey)) {
          return false;
        }
      }
      if (hasClientFilters) {
        const clientKey =
          project.client_id != null
            ? `id:${project.client_id}`
            : project.client_name
              ? `name:${project.client_name}`
              : 'unassigned';
        if (!filterSelections.client.includes(clientKey)) {
          return false;
        }
      }
      if (hasPriorityFilters) {
        const priorityValue = resolvePriorityValue(project.priority);
        const priorityKey = priorityValue === '' ? 'unassigned' : String(priorityValue);
        if (!filterSelections.priority.includes(priorityKey)) {
          return false;
        }
      }
      return true;
    });

    return [...filtered].sort((a, b) => {
      const aVal = resolveSortValue(a, sortField);
      const bVal = resolveSortValue(b, sortField);

      if (typeof aVal === 'string' || typeof bVal === 'string') {
        return sortOrder === 'asc'
          ? String(aVal).localeCompare(String(bVal))
          : String(bVal).localeCompare(String(aVal));
      }
      return sortOrder === 'asc' ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal);
    });
  }, [
    projectsWithFinance,
    activeView,
    resolveSortValue,
    sortField,
    sortOrder,
    viewId,
    currentUserId,
    filterSelections,
  ]);

  const derivedAggregates = useMemo(() => {
    if (!filteredProjects.length) {
      return null;
    }
    const totals = filteredProjects.reduce(
      (acc, project) => {
        const agreed = Number(project.agreed_fee ?? 0) || 0;
        const billed = Number(project.billed_to_date ?? 0) || 0;
        const unbilled = Number(project.unbilled_amount ?? 0) || 0;
        const earned = Number(project.earned_value ?? 0) || 0;
        const pipeline = Number(project.invoice_pipeline_this_month ?? 0) || 0;
        const deliverablesTotal = Number(project.deliverables_due_total ?? 0) || 0;
        const deliverablesNextWeek = Number(project.deliverables_due_next_week ?? 0) || 0;
        const deliverablesNextFortnight = Number(project.deliverables_due_next_fortnight ?? 0) || 0;
        const deliverablesNextMonth = Number(project.deliverables_due_next_month ?? 0) || 0;
        const deliverablesNextQuarter = Number(project.deliverables_due_next_quarter ?? 0) || 0;
        acc.sum_agreed_fee += agreed;
        acc.sum_billed_to_date += billed;
        acc.sum_unbilled_amount += unbilled;
        acc.sum_earned_value += earned;
        acc.sum_invoice_pipeline_this_month += pipeline;
        acc.sum_deliverables_due_total += deliverablesTotal;
        acc.sum_deliverables_due_next_week += deliverablesNextWeek;
        acc.sum_deliverables_due_next_fortnight += deliverablesNextFortnight;
        acc.sum_deliverables_due_next_month += deliverablesNextMonth;
        acc.sum_deliverables_due_next_quarter += deliverablesNextQuarter;
        return acc;
      },
      {
        sum_agreed_fee: 0,
        sum_billed_to_date: 0,
        sum_unbilled_amount: 0,
        sum_earned_value: 0,
        sum_invoice_pipeline_this_month: 0,
        sum_deliverables_due_total: 0,
        sum_deliverables_due_next_week: 0,
        sum_deliverables_due_next_fortnight: 0,
        sum_deliverables_due_next_month: 0,
        sum_deliverables_due_next_quarter: 0,
      },
    );
    const weightedPct =
      totals.sum_agreed_fee > 0
        ? (totals.sum_earned_value / totals.sum_agreed_fee) * 100
        : 0;
    return {
      project_count: filteredProjects.length,
      weighted_earned_value_pct: weightedPct,
      ...totals,
    };
  }, [filteredProjects]);

  const aggregateCurrencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
    [],
  );
  const aggregateNumberFormatter = useMemo(() => new Intl.NumberFormat('en-US'), []);

  const formatAggregateValue = useCallback(
    (fieldId: string, value?: number | null) => {
      const field = PROJECT_FIELD_MAP.get(fieldId);
      if (!field || value == null || Number.isNaN(Number(value))) {
        return '--';
      }
      if (field.format === 'currency') {
        return aggregateCurrencyFormatter.format(Number(value));
      }
      if (field.format === 'percent') {
        return `${Math.round(Number(value))}%`;
      }
      if (field.format === 'number') {
        return aggregateNumberFormatter.format(Number(value));
      }
      return String(value);
    },
    [aggregateCurrencyFormatter, aggregateNumberFormatter],
  );

  const resolveAggregateValue = useCallback(
    (fieldId: string) => {
      const source = derivedAggregates ?? aggregates;
      if (!source) {
        return '--';
      }
      switch (fieldId) {
        case 'agreed_fee':
          return formatAggregateValue(fieldId, source.sum_agreed_fee);
        case 'billed_to_date':
          return formatAggregateValue(fieldId, source.sum_billed_to_date);
        case 'unbilled_amount':
          return formatAggregateValue(fieldId, source.sum_unbilled_amount);
        case 'earned_value':
          return formatAggregateValue(fieldId, source.sum_earned_value);
        case 'earned_value_pct':
          return formatAggregateValue(fieldId, source.weighted_earned_value_pct);
        case 'invoice_pipeline_this_month':
          return formatAggregateValue(fieldId, source.sum_invoice_pipeline_this_month);
        case 'deliverables_due_total':
          return formatAggregateValue(fieldId, source.sum_deliverables_due_total);
        case 'deliverables_due_next_week':
          return formatAggregateValue(fieldId, source.sum_deliverables_due_next_week);
        case 'deliverables_due_next_fortnight':
          return formatAggregateValue(fieldId, source.sum_deliverables_due_next_fortnight);
        case 'deliverables_due_next_month':
          return formatAggregateValue(fieldId, source.sum_deliverables_due_next_month);
        case 'deliverables_due_next_quarter':
          return formatAggregateValue(fieldId, source.sum_deliverables_due_next_quarter);
        default:
          return '--';
      }
    },
    [aggregates, derivedAggregates, formatAggregateValue],
  );

  const timelineProjectIds = useMemo(
    () => filteredProjects.map((project) => project.project_id),
    [filteredProjects],
  );

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(
      VIEW_STORAGE_KEY,
      JSON.stringify({ viewId, searchTerm } satisfies ViewState),
    );
  }, [viewId, searchTerm]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(DISPLAY_STORAGE_KEY, displayMode);
  }, [displayMode]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filterSelections));
  }, [filterSelections]);

  const showMyWorkHint = activeView.id === 'my_work' && currentUserId == null;

  const activeLayout = displayMode === 'list' ? listLayout : displayMode === 'board' ? boardLayout : timelineLayout;

  const handleColumnsOpen = (event: MouseEvent<HTMLElement>) => {
    setColumnsAnchorEl(event.currentTarget);
  };

  const handleColumnsClose = () => {
    setColumnsAnchorEl(null);
  };

  const handleFiltersOpen = (event: MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFiltersClose = () => {
    setFilterAnchorEl(null);
    setFilterSearch('');
  };

  const toggleFilterValue = (category: FilterCategory, value: string) => {
    setFilterSelections((prev) => {
      const next = new Set(prev[category]);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return { ...prev, [category]: Array.from(next) };
    });
  };

  const clearFilterCategory = (category: FilterCategory) => {
    setFilterSelections((prev) => ({ ...prev, [category]: [] }));
  };

  const clearAllFilters = () => {
    setFilterSelections({
      lead: [],
      status: [],
      client: [],
      priority: [],
    });
  };

  const handleSortClick = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleCreateProject = () => {
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleProjectCreated = () => {
    setDialogOpen(false);
    // Invalidate and refetch projects
    queryClient.invalidateQueries({ queryKey: ['projects-summary'] });
    queryClient.invalidateQueries({ queryKey: ['projects-aggregates'] });
    refetch();
  };

  // Get unique statuses for board grouping
  const statusGroups = useMemo(() => {
    const statuses = new Set<string>();
    filteredProjects.forEach((p) => {
      if (p.status) statuses.add(p.status);
    });
    return Array.from(statuses).sort();
  }, [filteredProjects]);

  const listFieldIds = listLayout.orderedVisibleFieldIds;
  const listFields = listFieldIds
    .map((id) => PROJECT_FIELD_MAP.get(id))
    .filter(Boolean) as ProjectFieldDefinition[];
  const boardFieldIds = boardLayout.orderedVisibleFieldIds.filter((id) => id !== 'project_name');
  const timelineFieldIds = timelineLayout.orderedVisibleFieldIds.filter((id) => id !== 'project_name');

  const pinnedFieldIds = listLayout.pinnedFieldIds.filter((id) => listFieldIds.includes(id));
  const pinnedOffsets = useMemo(() => {
    const offsets = new Map<string, number>();
    let currentLeft = 0;
    listFieldIds.forEach((id) => {
      if (!pinnedFieldIds.includes(id)) {
        return;
      }
      const field = PROJECT_FIELD_MAP.get(id);
      const width = field?.width ?? 160;
      offsets.set(id, currentLeft);
      currentLeft += width;
    });
    return offsets;
  }, [listFieldIds, pinnedFieldIds]);

  const getStickyStyles = (fieldId: string, zIndex: number) => {
    if (!pinnedOffsets.has(fieldId)) {
      return {};
    }
    return {
      position: 'sticky' as const,
      left: pinnedOffsets.get(fieldId),
      zIndex,
    };
  };

  const buildDetailsPatch = useCallback(
    (project: ProjectSummary, overrides: Partial<ProjectSummary>) => {
      const resolvedPriority = resolvePriorityValue(overrides.priority ?? project.priority);
      return {
        start_date: overrides.start_date ?? project.start_date ?? null,
        end_date: overrides.end_date ?? project.end_date ?? null,
        status: normalizeStatusValue(overrides.status ?? project.status ?? null) || null,
        priority: resolvedPriority === '' ? null : resolvedPriority,
      };
    },
    [],
  );

  const renderListCellContent = useCallback(
    (fieldId: string, project: ProjectSummary) => {
      const field = PROJECT_FIELD_MAP.get(fieldId);
      if (!field) {
        return '--';
      }

      if (!field.editable) {
        return renderFieldValue(field, project);
      }

      if (fieldId === 'status') {
        return (
          <EditableSelectCell
            value={normalizeStatusValue(project.status)}
            options={STATUS_OPTIONS}
            onCommit={(nextValue) => {
              applyProjectPatch(project.project_id, buildDetailsPatch(project, { status: nextValue }));
            }}
          />
        );
      }

      if (fieldId === 'priority') {
        const priorityValue = resolvePriorityValue(project.priority);
        return (
          <EditableSelectCell
            value={priorityValue}
            options={PRIORITY_OPTIONS}
            onCommit={(nextValue) => {
              applyProjectPatch(project.project_id, buildDetailsPatch(project, { priority: nextValue }));
            }}
          />
        );
      }

      if (fieldId === 'internal_lead') {
        const options = [{ label: 'Unassigned', value: '' }].concat(
          users.map((user) => ({
            label: user.name || user.full_name || user.username || `User ${user.user_id}`,
            value: user.user_id,
          })),
        );
        return (
          <EditableSelectCell
            value={project.internal_lead ?? ''}
            options={options}
            onCommit={(nextValue) => {
              const next =
                nextValue === '' || nextValue === null || nextValue === undefined
                  ? null
                  : Number(nextValue);
              applyProjectPatch(project.project_id, { internal_lead: next });
            }}
          />
        );
      }

      if (fieldId === 'start_date') {
        return (
          <EditableTextCell
            type="date"
            value={toDateInputValue(project.start_date)}
            onCommit={(nextValue) => {
              applyProjectPatch(
                project.project_id,
                buildDetailsPatch(project, { start_date: nextValue || null }),
              );
            }}
          />
        );
      }

      if (fieldId === 'end_date') {
        return (
          <EditableTextCell
            type="date"
            value={toDateInputValue(project.end_date)}
            onCommit={(nextValue) => {
              applyProjectPatch(
                project.project_id,
                buildDetailsPatch(project, { end_date: nextValue || null }),
              );
            }}
          />
        );
      }

      if (fieldId === 'project_name') {
        return (
          <EditableTextCell
            value={project.project_name || ''}
            onCommit={(nextValue) => {
              applyProjectPatch(project.project_id, { project_name: nextValue });
            }}
          />
        );
      }

      if (fieldId === 'project_number') {
        const currentValue = project.project_number ?? project.contract_number ?? '';
        return (
          <EditableTextCell
            value={currentValue}
            onCommit={(nextValue) => {
              applyProjectPatch(project.project_id, { project_number: nextValue });
            }}
          />
        );
      }

      return renderFieldValue(field, project);
    },
    [applyProjectPatch, buildDetailsPatch, users],
  );

  const leadOptions = useMemo(() => {
    const options = new Map<string, string>();
    users.forEach((user) => {
      const label = user.name || user.full_name || user.username || `User ${user.user_id}`;
      options.set(`id:${user.user_id}`, label);
    });
    projectsWithFinance.forEach((project) => {
      if (project.internal_lead == null) {
        return;
      }
      const key = `id:${project.internal_lead}`;
      if (!options.has(key)) {
        options.set(key, project.internal_lead_name || `User ${project.internal_lead}`);
      }
    });
    const entries = Array.from(options.entries()).sort((a, b) => a[1].localeCompare(b[1]));
    const hasUnassigned = projectsWithFinance.some((project) => project.internal_lead == null);
    const mapped = entries.map(([value, label]) => ({ value, label }));
    return hasUnassigned ? [{ value: 'unassigned', label: 'Unassigned' }, ...mapped] : mapped;
  }, [projectsWithFinance, users]);

  const statusOptions = useMemo(() => {
    const options = new Map<string, string>();
    STATUS_OPTIONS.forEach((option) => options.set(option.value, option.label));
    projectsWithFinance.forEach((project) => {
      const normalized = normalizeStatusValue(project.status ?? '');
      if (normalized) {
        options.set(normalized, normalized);
      }
    });
    const entries = Array.from(options.entries()).map(([value, label]) => ({ value, label }));
    entries.sort((a, b) => a.label.localeCompare(b.label));
    const hasUnassigned = projectsWithFinance.some((project) => !project.status);
    return hasUnassigned ? [{ value: 'unassigned', label: 'Unassigned' }, ...entries] : entries;
  }, [projectsWithFinance]);

  const clientOptions = useMemo(() => {
    const options = new Map<string, string>();
    projectsWithFinance.forEach((project) => {
      if (project.client_id != null) {
        const label = project.client_name || `Client ${project.client_id}`;
        options.set(`id:${project.client_id}`, label);
        return;
      }
      if (project.client_name) {
        options.set(`name:${project.client_name}`, project.client_name);
      }
    });
    const entries = Array.from(options.entries()).map(([value, label]) => ({ value, label }));
    entries.sort((a, b) => a.label.localeCompare(b.label));
    const hasUnassigned = projectsWithFinance.some((project) => !project.client_id && !project.client_name);
    return hasUnassigned ? [{ value: 'unassigned', label: 'Unassigned' }, ...entries] : entries;
  }, [projectsWithFinance]);

  const priorityOptions = useMemo(() => {
    const entries = PRIORITY_OPTIONS.map((option) => ({
      value: String(option.value),
      label: option.label,
    }));
    const hasUnassigned = projectsWithFinance.some(
      (project) => resolvePriorityValue(project.priority) === '',
    );
    return hasUnassigned ? [{ value: 'unassigned', label: 'Unassigned' }, ...entries] : entries;
  }, [projectsWithFinance]);

  const filterCategories = useMemo(
    () => [
      { id: 'lead' as const, label: 'Lead', icon: <PersonOutline fontSize="small" /> },
      { id: 'status' as const, label: 'Status', icon: <DonutSmall fontSize="small" /> },
      { id: 'client' as const, label: 'Client', icon: <BusinessOutlined fontSize="small" /> },
      { id: 'priority' as const, label: 'Priority', icon: <FlagOutlined fontSize="small" /> },
    ],
    [],
  );

  const activeFilterCount = useMemo(
    () =>
      filterSelections.lead.length +
      filterSelections.status.length +
      filterSelections.client.length +
      filterSelections.priority.length,
    [filterSelections],
  );

  const activeOptions =
    activeFilterCategory === 'lead'
      ? leadOptions
      : activeFilterCategory === 'status'
        ? statusOptions
        : activeFilterCategory === 'client'
          ? clientOptions
          : priorityOptions;

  const filteredOptions = useMemo(() => {
    const trimmed = filterSearch.trim().toLowerCase();
    if (!trimmed) {
      return activeOptions;
    }
    return activeOptions.filter((option) => option.label.toLowerCase().includes(trimmed));
  }, [activeOptions, filterSearch]);

  return (
    <Box data-testid="projects-home-v2-root" sx={{ display: 'grid', gap: 2 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} justifyContent="space-between">
        <Stack spacing={0.5}>
          <Typography variant="h4">Projects</Typography>
          <Typography variant="body2" color="text.secondary">
            Track project status across list, board, and timeline.
          </Typography>
        </Stack>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
            data-testid="create-project-button"
          >
            Create Project
          </Button>
          <TextField
            select
            size="small"
            label="View"
            value={viewId}
            onChange={(event) => setViewId(event.target.value as ViewId)}
            sx={{ minWidth: 180 }}
            data-testid="projects-home-view-select"
          >
            {viewDefinitions.map((view) => (
              <MenuItem key={view.id} value={view.id}>
                {view.label}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant="outlined"
            size="small"
            startIcon={<FilterAlt />}
            onClick={handleFiltersOpen}
            data-testid="projects-home-filter-button"
            sx={{
              textTransform: 'none',
              borderColor: activeFilterCount ? 'primary.main' : 'divider',
              boxShadow: activeFilterCount ? '0 0 0 1px rgba(25,118,210,0.35)' : 'none',
              gap: 1,
            }}
          >
            Filters
            {activeFilterCount > 0 && (
              <Box
                component="span"
                sx={{
                  ml: 0.5,
                  px: 1,
                  py: 0.15,
                  borderRadius: 999,
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {activeFilterCount}
              </Box>
            )}
          </Button>
          <TextField
            size="small"
            placeholder="Search projects"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            sx={{ minWidth: 220 }}
            inputProps={{ 'data-testid': 'projects-home-search' }}
          />
          <Button
            variant="outlined"
            size="small"
            startIcon={<ViewColumn />}
            onClick={handleColumnsOpen}
            data-testid="projects-columns-button"
          >
            Columns
          </Button>
          <ToggleButtonGroup
            exclusive
            value={displayMode}
            onChange={(_event, nextMode) => {
              if (nextMode) {
                setDisplayMode(nextMode);
              }
            }}
            size="small"
            data-testid="projects-home-display-mode"
          >
            <ToggleButton value="list">List</ToggleButton>
            <ToggleButton value="board">Board</ToggleButton>
            <ToggleButton value="timeline">Timeline</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Stack>

      <ProjectColumnsPopover
        view={displayMode}
        anchorEl={columnsAnchorEl}
        onClose={handleColumnsClose}
        visibleFieldIds={activeLayout.visibleFieldIds}
        orderedFieldIds={activeLayout.orderedFieldIds}
        pinnedFieldIds={activeLayout.pinnedFieldIds}
        toggleField={activeLayout.toggleField}
        moveField={activeLayout.moveField}
        togglePinnedField={activeLayout.togglePinnedField}
        resetToDefaults={activeLayout.resetToDefaults}
      />

      <Popover
        open={Boolean(filterAnchorEl)}
        anchorEl={filterAnchorEl}
        onClose={handleFiltersClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        PaperProps={{
          sx: {
            mt: 1,
            width: { xs: '90vw', sm: 520 },
            maxWidth: 640,
            borderRadius: 2,
            overflow: 'hidden',
            border: '1px solid',
            borderColor: 'divider',
          },
        }}
      >
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '200px 1fr' } }}>
          <Box
            sx={{
              borderRight: { sm: '1px solid' },
              borderColor: 'divider',
              background:
                'linear-gradient(180deg, rgba(17,24,39,0.04) 0%, rgba(17,24,39,0.0) 100%)',
            }}
          >
            <Box sx={{ px: 2, py: 1.5 }}>
              <Typography variant="subtitle2" fontWeight={700}>
                Filters
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Narrow the projects list
              </Typography>
            </Box>
            <Divider />
            <List dense disablePadding>
              {filterCategories.map((category) => {
                const count = filterSelections[category.id].length;
                const active = activeFilterCategory === category.id;
                return (
                  <ListItemButton
                    key={category.id}
                    onClick={() => setActiveFilterCategory(category.id)}
                    selected={active}
                    sx={{
                      px: 2,
                      py: 1,
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(25,118,210,0.08)',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 32 }}>{category.icon}</ListItemIcon>
                    <ListItemText primary={category.label} />
                    {count > 0 && (
                      <Box
                        component="span"
                        sx={{
                          px: 0.75,
                          py: 0.15,
                          borderRadius: 999,
                          backgroundColor: 'rgba(25,118,210,0.12)',
                          color: 'primary.main',
                          fontSize: 12,
                          fontWeight: 600,
                          mr: 1,
                        }}
                      >
                        {count}
                      </Box>
                    )}
                    <ChevronRight fontSize="small" />
                  </ListItemButton>
                );
              })}
            </List>
          </Box>
          <Box sx={{ px: 2, py: 2, display: 'grid', gap: 1.5 }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="subtitle1" fontWeight={700}>
                  {filterCategories.find((cat) => cat.id === activeFilterCategory)?.label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Select one or more values
                </Typography>
              </Box>
              {filterSelections[activeFilterCategory].length > 0 && (
                <Button
                  size="small"
                  onClick={() => clearFilterCategory(activeFilterCategory)}
                  sx={{ textTransform: 'none' }}
                >
                  Clear
                </Button>
              )}
            </Stack>
            <TextField
              size="small"
              placeholder="Add filter..."
              value={filterSearch}
              onChange={(event) => setFilterSearch(event.target.value)}
            />
            <Box sx={{ maxHeight: 280, overflowY: 'auto' }}>
              {filteredOptions.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  No matching options.
                </Typography>
              ) : (
                <List dense>
                  {filteredOptions.map((option) => (
                    <ListItemButton
                      key={option.value}
                      onClick={() => toggleFilterValue(activeFilterCategory, option.value)}
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Checkbox
                          edge="start"
                          checked={filterSelections[activeFilterCategory].includes(option.value)}
                          tabIndex={-1}
                          disableRipple
                        />
                      </ListItemIcon>
                      <ListItemText primary={option.label} />
                    </ListItemButton>
                  ))}
                </List>
              )}
            </Box>
            <Divider />
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="caption" color="text.secondary">
                {activeFilterCount
                  ? `${activeFilterCount} active filter${activeFilterCount === 1 ? '' : 's'}`
                  : 'No active filters'}
              </Typography>
              {activeFilterCount > 0 && (
                <Button size="small" onClick={clearAllFilters} sx={{ textTransform: 'none' }}>
                  Clear all
                </Button>
              )}
            </Stack>
          </Box>
        </Box>
      </Popover>

      {showMyWorkHint && (
        <Alert severity="info">Set `current_user_id` in localStorage to enable My Work filtering.</Alert>
      )}

      {error && (
        <Alert severity="error">
          Failed to load projects. Please try again.
        </Alert>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* LIST VIEW */}
      {displayMode === 'list' && !isLoading && (
        <TableContainer component={Paper} variant="outlined" data-testid="projects-list-table">
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                {listFields.map((field) => (
                  <TableCell
                    key={field.id}
                    align={field.align ?? 'left'}
                    sx={{
                      minWidth: field.width ?? 140,
                      backgroundColor: 'grey.100',
                      ...getStickyStyles(field.id, 3),
                    }}
                  >
                    <TableSortLabel
                      active={sortField === field.id}
                      direction={sortField === field.id ? sortOrder : 'asc'}
                      onClick={() => handleSortClick(field.id)}
                    >
                      {field.label}
                    </TableSortLabel>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredProjects.map((project) => (
                <TableRow
                  key={project.project_id}
                  data-testid={`projects-home-list-row-${project.project_id}`}
                  hover
                  onClick={() => navigate(`/projects/${project.project_id}/workspace/overview`)}
                  sx={{ cursor: 'pointer' }}
                >
                  {listFields.map((field) => (
                    <TableCell
                      key={field.id}
                      align={field.align ?? 'left'}
                      sx={{
                        minWidth: field.width ?? 140,
                        backgroundColor: 'background.paper',
                        ...getStickyStyles(field.id, 2),
                      }}
                    >
                      {renderListCellContent(field.id, project)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
              {filteredProjects.length === 0 && (
                <TableRow>
                  <TableCell colSpan={listFields.length || 1} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      {isLoading ? 'Loading...' : 'No projects found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
            <TableFooter>
              <TableRow sx={{ backgroundColor: 'grey.50' }}>
                {listFields.map((field, index) => (
                  <TableCell
                    key={field.id}
                    align={field.align ?? 'left'}
                    sx={{
                      fontWeight: 600,
                      position: 'sticky',
                      bottom: 0,
                      backgroundColor: 'grey.50',
                      ...getStickyStyles(field.id, 4),
                    }}
                  >
                    {index === 0
                      ? `${(derivedAggregates ?? aggregates)?.project_count ?? 0} projects`
                      : field.aggregatable === 'none'
                        ? ''
                        : resolveAggregateValue(field.id)}
                  </TableCell>
                ))}
              </TableRow>
            </TableFooter>
          </Table>
        </TableContainer>
      )}

      {/* BOARD VIEW */}
      {displayMode === 'board' && !isLoading && (
        <Box
          data-testid="projects-board-view"
          sx={{
            display: 'grid',
            gridTemplateColumns: `repeat(auto-fit, minmax(320px, 1fr))`,
            gap: 2,
          }}
        >
          {statusGroups.map((status) => {
            const statusProjects = filteredProjects.filter((p) => p.status === status);
            return (
              <Paper key={status} variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1.5 }}>
                  {status} ({statusProjects.length})
                </Typography>
                <Stack spacing={1}>
                  {statusProjects.map((project) => (
                    <Card
                      key={project.project_id}
                      data-testid={`project-card-${project.project_id}`}
                      sx={{
                        p: 1.5,
                        cursor: 'pointer',
                        '&:hover': { boxShadow: 1 },
                      }}
                      onClick={() => navigate(`/projects/${project.project_id}/workspace/overview`)}
                    >
                      <CardContent sx={{ p: 0 }}>
                        <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                          {project.project_name}
                        </Typography>
                        <Stack spacing={0.5}>
                          {boardFieldIds.map((fieldId) => {
                            const field = PROJECT_FIELD_MAP.get(fieldId);
                            if (!field) return null;
                            return (
                              <Box key={field.id}>
                                {renderBoardSnippet(field, project)}
                              </Box>
                            );
                          })}
                        </Stack>
                      </CardContent>
                    </Card>
                  ))}
                  {statusProjects.length === 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      No projects
                    </Typography>
                  )}
                </Stack>
              </Paper>
            );
          })}
          {statusGroups.length === 0 && (
            <Typography color="text.secondary">No projects found.</Typography>
          )}
        </Box>
      )}

      {/* TIMELINE VIEW */}
      {displayMode === 'timeline' && !isLoading && (
        <Paper variant="outlined" sx={{ p: 2, overflow: 'hidden' }} data-testid="projects-timeline-view">
          {featureFlags.linearTimeline ? (
            <Box sx={{ width: '100%', overflow: 'auto' }}>
              <TimelinePanel
                title="Projects timeline"
                projectIds={timelineProjectIds.length ? timelineProjectIds : undefined}
                searchText={searchTerm}
                onSearchTextChange={setSearchTerm}
                showSearch={false}
                summaryById={summaryById}
                metaFieldIds={timelineFieldIds}
              />
            </Box>
          ) : (
            <Typography color="text.secondary">
              Enable `ff_linear_timeline` to view the new timeline.
            </Typography>
          )}
        </Paper>
      )}

      {/* CREATE PROJECT DIALOG */}
      {dialogOpen && (
        <Suspense
          fallback={(
            <Box
              position="fixed"
              top={0}
              left={0}
              right={0}
              bottom={0}
              display="flex"
              alignItems="center"
              justifyContent="center"
              sx={{ bgcolor: 'rgba(0,0,0,0.25)', zIndex: (theme) => theme.zIndex.modal - 1 }}
            >
              <CircularProgress />
            </Box>
          )}
        >
          <ProjectFormDialog
            key="create-new"
            open={dialogOpen}
            onClose={handleDialogClose}
            mode="create"
            onSuccess={handleProjectCreated}
          />
        </Suspense>
      )}
    </Box>
  );
}
