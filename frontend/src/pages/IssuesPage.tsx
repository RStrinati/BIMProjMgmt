import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Popover,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Stack,
  Typography,
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';
import ChevronRight from '@mui/icons-material/ChevronRight';
import { issuesApi } from '../api/issues';
import { projectsApi } from '../api/projects';
import type { Project } from '../types/api';
import { IssuesColumnsPopover } from '../components/issues/IssuesColumnsPopover';

interface IssueRow {
  issue_key: string;
  source_system: string;
  display_id: string;
  title: string;
  status_normalized: string;
  priority_normalized: string;
  discipline_normalized: string;
  assignee_user_key: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  closed_by?: string | null;
  linked_document_urn?: string | null;
  snapshot_urn?: string | null;
  web_link?: string | null;
  preview_middle_url?: string | null;
  issue_link?: string | null;
  snapshot_preview_url?: string | null;
  [key: string]: any;
}

interface ViewState {
  searchText: string;
  projectIds?: string[];
  sourceSystems?: string[];
  statusNormalized?: string[];
  priorityNormalized?: string[];
  disciplineNormalized?: string[];
  assigneeUserKey?: string;
  page: number;
  pageSize: number;
  sortBy: string;
  sortDir: 'asc' | 'desc';
}

const DEFAULT_VIEW_STATE: ViewState = {
  searchText: '',
  page: 0,
  pageSize: 50,
  sortBy: 'updated_at',
  sortDir: 'desc',
};

const STATUS_COLORS: Record<string, 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  open: 'warning',
  'in_progress': 'info',
  'in_review': 'info',
  closed: 'success',
  resolved: 'success',
};

const PRIORITY_COLORS: Record<string, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  high: 'error',
  medium: 'warning',
  low: 'info',
};

const ISSUE_COLUMNS = [
  { id: 'display_id', label: 'Display ID' },
  { id: 'title', label: 'Title' },
  { id: 'project', label: 'Project' },
  { id: 'source_system', label: 'Source' },
  { id: 'status_normalized', label: 'Status' },
  { id: 'priority_normalized', label: 'Priority' },
  { id: 'discipline_normalized', label: 'Discipline' },
  { id: 'assignee_user_key', label: 'Assignee' },
  { id: 'created_at', label: 'Created' },
  { id: 'updated_at', label: 'Updated' },
  { id: 'closed_at', label: 'Closed' },
  { id: 'created_by', label: 'Created By' },
  { id: 'updated_by', label: 'Updated By' },
  { id: 'closed_by', label: 'Closed By' },
  { id: 'linked_document_urn', label: 'Linked Document URN' },
  { id: 'snapshot_urn', label: 'Snapshot URN' },
  { id: 'web_link', label: 'Web Link' },
  { id: 'preview_middle_url', label: 'Preview Image' },
  { id: 'issue_link', label: 'Issue Link' },
  { id: 'snapshot_preview_url', label: 'Snapshot Preview' },
  { id: 'issue_key', label: 'Issue Key' },
  { id: 'source_issue_id', label: 'Source Issue ID' },
  { id: 'source_project_id', label: 'Source Project ID' },
  { id: 'project_id', label: 'Project ID' },
  { id: 'acc_issue_number', label: 'ACC Issue #' },
  { id: 'acc_issue_uuid', label: 'ACC Issue UUID' },
  { id: 'acc_id_type', label: 'ACC ID Type' },
  { id: 'status_raw', label: 'Status Raw' },
  { id: 'priority_raw', label: 'Priority Raw' },
  { id: 'discipline_raw', label: 'Discipline Raw' },
  { id: 'location_root', label: 'Location Root' },
  { id: 'location_building', label: 'Location Building' },
  { id: 'location_level', label: 'Location Level' },
  { id: 'acc_status', label: 'ACC Status' },
  { id: 'acc_created_at', label: 'ACC Created' },
  { id: 'acc_updated_at', label: 'ACC Updated' },
  { id: 'is_deleted', label: 'Deleted' },
  { id: 'import_run_id', label: 'Import Run' },
] as const;

const DEFAULT_VISIBLE_COLUMNS = [
  'display_id',
  'title',
  'project',
  'status_normalized',
  'priority_normalized',
  'discipline_normalized',
  'assignee_user_key',
  'updated_at',
  'issue_link',
  'snapshot_preview_url',
];

const COLUMN_STORAGE_KEY = 'issues_columns_visible';
const COLUMN_ORDER_STORAGE_KEY = 'issues_columns_order';

export function IssuesPage() {
  const [viewState, setViewState] = useState<ViewState>(() => {
    const saved = localStorage.getItem('issues_view_state');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        const normalizeList = (value?: string | string[]) => {
          if (!value) return undefined;
          if (Array.isArray(value)) return value;
          return value.split(',').map((item) => item.trim()).filter(Boolean);
        };
        return {
          ...DEFAULT_VIEW_STATE,
          ...parsed,
          projectIds: normalizeList(parsed.projectIds),
          sourceSystems: normalizeList(parsed.sourceSystems ?? parsed.sourceSystem),
          statusNormalized: normalizeList(parsed.statusNormalized),
          priorityNormalized: normalizeList(parsed.priorityNormalized),
          disciplineNormalized: normalizeList(parsed.disciplineNormalized),
        };
      } catch {
        return DEFAULT_VIEW_STATE;
      }
    }
    return DEFAULT_VIEW_STATE;
  });

  const [columnsAnchorEl, setColumnsAnchorEl] = useState<HTMLElement | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(() => {
    const saved = localStorage.getItem(COLUMN_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return DEFAULT_VISIBLE_COLUMNS;
      }
    }
    return DEFAULT_VISIBLE_COLUMNS;
  });
  const [columnOrder, setColumnOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem(COLUMN_ORDER_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return ISSUE_COLUMNS.map((col) => col.id);
      }
    }
    return ISSUE_COLUMNS.map((col) => col.id);
  });

  // Persist view state to localStorage
  const updateViewState = useCallback((updates: Partial<ViewState>) => {
    setViewState((prev) => {
      const next = { ...prev, ...updates, page: updates.page !== undefined ? updates.page : 0 };
      localStorage.setItem('issues_view_state', JSON.stringify(next));
      return next;
    });
  }, []);

  // Fetch issues using the normalized /api/issues/table endpoint
  const { data, isLoading, error } = useQuery({
    queryKey: [
      'issues-table',
      viewState.searchText,
      viewState.projectIds?.join(',') || '',
      viewState.sourceSystems?.join(',') || '',
      viewState.statusNormalized?.join(',') || '',
      viewState.priorityNormalized?.join(',') || '',
      viewState.disciplineNormalized?.join(',') || '',
      viewState.assigneeUserKey,
      viewState.page,
      viewState.pageSize,
      viewState.sortBy,
      viewState.sortDir,
    ],
    queryFn: async () => {
      return issuesApi.getIssuesTable({
        search: viewState.searchText || undefined,
        project_id: viewState.projectIds,
        source_system: viewState.sourceSystems as Array<'ACC' | 'Revizto'> | undefined,
        status_normalized: viewState.statusNormalized,
        priority_normalized: viewState.priorityNormalized,
        discipline_normalized: viewState.disciplineNormalized,
        assignee_user_key: viewState.assigneeUserKey,
        page: viewState.page + 1, // API uses 1-based pagination
        page_size: viewState.pageSize,
        sort_by: viewState.sortBy,
        sort_dir: viewState.sortDir,
      });
    },
    staleTime: 60_000, // 1 minute
    keepPreviousData: true,
    retry: 1,
  });

  const { data: projects } = useQuery<Project[]>({
    queryKey: ['issues', 'projects'],
    queryFn: () => projectsApi.getAll(),
  });

  const rows: IssueRow[] = useMemo(() => data?.rows ?? [], [data?.rows]);
  const totalCount = useMemo(() => data?.total_count ?? 0, [data?.total_count]);

  const projectNameById = useMemo(() => {
    const map = new Map<string, string>();
    (projects ?? []).forEach((project) => {
      map.set(String(project.project_id), project.project_name);
    });
    return map;
  }, [projects]);

  const issueFilterOptions = useMemo(() => {
    const statuses = new Set<string>();
    const priorities = new Set<string>();
    const disciplines = new Set<string>();
    const sources = new Set<string>();
    const projectOptions = new Map<string, string>();

    rows.forEach((issue) => {
      if (issue.status_normalized) statuses.add(issue.status_normalized);
      if (issue.priority_normalized) priorities.add(issue.priority_normalized);
      if (issue.discipline_normalized) disciplines.add(issue.discipline_normalized);
      if (issue.source_system) sources.add(issue.source_system);
    });

    (projects ?? []).forEach((project) => {
      projectOptions.set(String(project.project_id), project.project_name);
    });

    const sort = (values: Set<string>) => Array.from(values).sort((a, b) => a.localeCompare(b));
    return {
      projects: Array.from(projectOptions.entries())
        .map(([value, label]) => ({ value, label }))
        .sort((a, b) => a.label.localeCompare(b.label)),
      statuses: sort(statuses),
      priorities: sort(priorities),
      disciplines: sort(disciplines),
      sources: sort(sources),
    };
  }, [rows, projects]);

  const clearFilters = useCallback(() => {
    updateViewState({
      searchText: '',
      projectIds: undefined,
      sourceSystems: undefined,
      statusNormalized: undefined,
      priorityNormalized: undefined,
      disciplineNormalized: undefined,
      assigneeUserKey: undefined,
      page: 0,
    });
  }, [updateViewState]);

  const hasActiveFilters = useMemo(() => {
    return (
      viewState.searchText ||
      (viewState.projectIds && viewState.projectIds.length > 0) ||
      (viewState.sourceSystems && viewState.sourceSystems.length > 0) ||
      (viewState.statusNormalized && viewState.statusNormalized.length > 0) ||
      (viewState.priorityNormalized && viewState.priorityNormalized.length > 0) ||
      (viewState.disciplineNormalized && viewState.disciplineNormalized.length > 0) ||
      viewState.assigneeUserKey
    );
  }, [viewState]);

  const getIssueRowId = (issue: IssueRow): string => {
    return `${issue.source_system}-${issue.display_id}`.replace(/[^a-zA-Z0-9-]/g, '_');
  };

  const formatDate = (value?: string | null) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString();
  };

  const isHttpUrl = (value?: string | null) => {
    if (!value) return false;
    return value.startsWith('http://') || value.startsWith('https://');
  };

  const formatProjectLabel = (issue: IssueRow) => {
    const projectId = issue.project_id ? String(issue.project_id) : '';
    if (projectId && projectNameById.has(projectId)) {
      return projectNameById.get(projectId) as string;
    }
    if (projectId) {
      return `Unmapped (${projectId})`;
    }
    return '-';
  };

  const toggleMultiFilterValue = (value: string, current?: string[]) => {
    if (!current || current.length === 0) return [value];
    if (current.includes(value)) {
      const next = current.filter((item) => item !== value);
      return next.length ? next : undefined;
    }
    return [...current, value];
  };

  const filterSelections = useMemo(
    () => ({
      project: viewState.projectIds ?? [],
      source: viewState.sourceSystems ?? [],
      priority: viewState.priorityNormalized ?? [],
      discipline: viewState.disciplineNormalized ?? [],
      status: viewState.statusNormalized ?? [],
    }),
    [viewState],
  );

  const activeFilterCount = useMemo(
    () =>
      filterSelections.project.length +
      filterSelections.source.length +
      filterSelections.priority.length +
      filterSelections.discipline.length +
      filterSelections.status.length,
    [filterSelections],
  );

  const filterCategories = useMemo(
    () => [
      { id: 'project', label: 'Projects' },
      { id: 'source', label: 'Source' },
      { id: 'priority', label: 'Priority' },
      { id: 'discipline', label: 'Discipline' },
      { id: 'status', label: 'Status' },
    ],
    [],
  );

  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(null);
  const [activeFilterCategory, setActiveFilterCategory] = useState<string>('project');
  const [filterSearch, setFilterSearch] = useState('');

  const handleFiltersOpen = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFiltersClose = () => {
    setFilterAnchorEl(null);
    setFilterSearch('');
  };

  const clearFilterCategory = (categoryId: string) => {
    if (categoryId === 'project') {
      updateViewState({ projectIds: undefined, page: 0 });
      return;
    }
    if (categoryId === 'source') {
      updateViewState({ sourceSystems: undefined, page: 0 });
      return;
    }
    if (categoryId === 'priority') {
      updateViewState({ priorityNormalized: undefined, page: 0 });
      return;
    }
    if (categoryId === 'discipline') {
      updateViewState({ disciplineNormalized: undefined, page: 0 });
      return;
    }
    if (categoryId === 'status') {
      updateViewState({ statusNormalized: undefined, page: 0 });
    }
  };

  const toggleFilterValue = (categoryId: string, value: string) => {
    if (categoryId === 'project') {
      updateViewState({ projectIds: toggleMultiFilterValue(value, viewState.projectIds), page: 0 });
      return;
    }
    if (categoryId === 'source') {
      updateViewState({ sourceSystems: toggleMultiFilterValue(value, viewState.sourceSystems), page: 0 });
      return;
    }
    if (categoryId === 'priority') {
      updateViewState({
        priorityNormalized: toggleMultiFilterValue(value, viewState.priorityNormalized),
        page: 0,
      });
      return;
    }
    if (categoryId === 'discipline') {
      updateViewState({
        disciplineNormalized: toggleMultiFilterValue(value, viewState.disciplineNormalized),
        page: 0,
      });
      return;
    }
    if (categoryId === 'status') {
      updateViewState({
        statusNormalized: toggleMultiFilterValue(value, viewState.statusNormalized),
        page: 0,
      });
    }
  };

  const filteredOptions = useMemo(() => {
    const searchLower = filterSearch.trim().toLowerCase();
    let options: Array<{ value: string; label: string }> = [];
    if (activeFilterCategory === 'project') {
      options = issueFilterOptions.projects;
    } else if (activeFilterCategory === 'source') {
      options = issueFilterOptions.sources.map((value) => ({ value, label: value }));
    } else if (activeFilterCategory === 'priority') {
      options = issueFilterOptions.priorities.map((value) => ({ value, label: value }));
    } else if (activeFilterCategory === 'discipline') {
      options = issueFilterOptions.disciplines.map((value) => ({ value, label: value }));
    } else if (activeFilterCategory === 'status') {
      options = issueFilterOptions.statuses.map((value) => ({ value, label: value }));
    }

    if (!searchLower) {
      return options;
    }
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(searchLower) ||
        option.value.toLowerCase().includes(searchLower),
    );
  }, [activeFilterCategory, filterSearch, issueFilterOptions]);

  const handleColumnsOpen = (event: React.MouseEvent<HTMLElement>) => {
    setColumnsAnchorEl(event.currentTarget);
  };

  const handleColumnsClose = () => {
    setColumnsAnchorEl(null);
  };

  const toggleColumn = (columnId: string) => {
    setVisibleColumns((prev) => {
      const next = prev.includes(columnId)
        ? prev.filter((id) => id !== columnId)
        : [...prev, columnId];
      localStorage.setItem(COLUMN_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const moveColumn = (columnId: string, direction: 'up' | 'down') => {
    setColumnOrder((prev) => {
      const index = prev.indexOf(columnId);
      if (index === -1) return prev;
      const next = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= next.length) return prev;
      const [removed] = next.splice(index, 1);
      next.splice(targetIndex, 0, removed);
      localStorage.setItem(COLUMN_ORDER_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const resetColumns = () => {
    setVisibleColumns(DEFAULT_VISIBLE_COLUMNS);
    setColumnOrder(ISSUE_COLUMNS.map((col) => col.id));
    localStorage.setItem(COLUMN_STORAGE_KEY, JSON.stringify(DEFAULT_VISIBLE_COLUMNS));
    localStorage.setItem(
      COLUMN_ORDER_STORAGE_KEY,
      JSON.stringify(ISSUE_COLUMNS.map((col) => col.id)),
    );
  };

  const orderedVisibleColumns = useMemo(
    () => columnOrder.filter((id) => visibleColumns.includes(id)),
    [columnOrder, visibleColumns],
  );

  useEffect(() => {
    if (totalCount > 0 && rows.length === 0 && viewState.page > 0) {
      updateViewState({ page: 0 });
    }
  }, [totalCount, rows.length, viewState.page, updateViewState]);

  const renderCellValue = (issue: IssueRow, columnId: string) => {
    switch (columnId) {
      case 'display_id':
        return issue.display_id;
      case 'title':
        return issue.title || issue.issue_key;
      case 'project':
        return formatProjectLabel(issue);
      case 'source_system':
        return issue.source_system || '-';
      case 'status_normalized':
        return (
          <Chip
            label={issue.status_normalized || 'Unknown'}
            size="small"
            color={STATUS_COLORS[issue.status_normalized?.toLowerCase()] || 'default'}
            variant="outlined"
          />
        );
      case 'priority_normalized':
        return (
          <Chip
            label={issue.priority_normalized || 'N/A'}
            size="small"
            color={PRIORITY_COLORS[issue.priority_normalized?.toLowerCase()] || 'default'}
            variant="outlined"
          />
        );
      case 'discipline_normalized':
        return issue.discipline_normalized || '-';
      case 'assignee_user_key':
        return issue.assignee_user_key || '-';
      case 'created_at':
        return formatDate(issue.created_at);
      case 'updated_at':
        return formatDate(issue.updated_at);
      case 'closed_at':
        return formatDate(issue.closed_at);
      case 'created_by':
        return issue.created_by || '-';
      case 'updated_by':
        return issue.updated_by || '-';
      case 'closed_by':
        return issue.closed_by || '-';
      case 'linked_document_urn':
        return issue.linked_document_urn || '-';
      case 'snapshot_urn':
        return issue.snapshot_urn || '-';
      case 'web_link':
        return issue.web_link || '-';
      case 'preview_middle_url':
        return issue.preview_middle_url || '-';
      case 'issue_link':
        if (!issue.issue_link) return '-';
        return isHttpUrl(issue.issue_link) ? (
          <a href={issue.issue_link} target="_blank" rel="noreferrer">
            Open
          </a>
        ) : (
          issue.issue_link
        );
      case 'snapshot_preview_url':
        if (!issue.snapshot_preview_url) return '-';
        return isHttpUrl(issue.snapshot_preview_url) ? (
          <a href={issue.snapshot_preview_url} target="_blank" rel="noreferrer">
            Preview
          </a>
        ) : (
          issue.snapshot_preview_url
        );
      case 'issue_key':
        return issue.issue_key || '-';
      case 'source_issue_id':
        return issue.source_issue_id || '-';
      case 'source_project_id':
        return issue.source_project_id || '-';
      case 'project_id':
        return issue.project_id || '-';
      case 'acc_issue_number':
        return issue.acc_issue_number ?? '-';
      case 'acc_issue_uuid':
        return issue.acc_issue_uuid || '-';
      case 'acc_id_type':
        return issue.acc_id_type || '-';
      case 'status_raw':
        return issue.status_raw || '-';
      case 'priority_raw':
        return issue.priority_raw || '-';
      case 'discipline_raw':
        return issue.discipline_raw || '-';
      case 'location_root':
        return issue.location_root || '-';
      case 'location_building':
        return issue.location_building || '-';
      case 'location_level':
        return issue.location_level || '-';
      case 'acc_status':
        return issue.acc_status || '-';
      case 'acc_created_at':
        return formatDate(issue.acc_created_at);
      case 'acc_updated_at':
        return formatDate(issue.acc_updated_at);
      case 'is_deleted':
        return issue.is_deleted ? 'Yes' : 'No';
      case 'import_run_id':
        return issue.import_run_id || '-';
      default:
        return issue[columnId] ?? '-';
    }
  };

  return (
    <Box sx={{ p: 2 }} data-testid="issues-hub-root">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          Issues Hub
        </Typography>

        {/* Filter Bar */}
        <Paper sx={{ p: 2 }} data-testid="issues-hub-filters">
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {hasActiveFilters && (
                <Button
                  size="small"
                  startIcon={<ClearIcon />}
                  onClick={clearFilters}
                  color="error"
                >
                  Clear Filters
                </Button>
              )}
              <Button size="small" startIcon={<FilterListIcon />} onClick={handleFiltersOpen}>
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
              <Button size="small" startIcon={<ViewColumnIcon />} onClick={handleColumnsOpen}>
                Columns
              </Button>
            </Stack>

            {/* Filter inputs */}
            <Stack spacing={2}>
              <TextField
                label="Search"
                placeholder="Title, ID, or key..."
                size="small"
                value={viewState.searchText}
                onChange={(e) => updateViewState({ searchText: e.target.value, page: 0 })}
                sx={{ minWidth: 200 }}
                InputProps={{
                  startAdornment: <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Stack>
          </Stack>
        </Paper>
      </Box>

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load issues: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      )}

      {/* Loading state */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Issues table */}
      {!isLoading && rows.length > 0 && (
        <>
          <TableContainer component={Paper} sx={{ mb: 2 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  {orderedVisibleColumns.map((columnId) => {
                    const label = ISSUE_COLUMNS.find((col) => col.id === columnId)?.label ?? columnId;
                    return (
                      <TableCell key={columnId} sx={{ fontWeight: 600, minWidth: 120 }}>
                        {label}
                      </TableCell>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((issue) => (
                  <TableRow
                    key={getIssueRowId(issue)}
                    data-testid={`issues-row-${getIssueRowId(issue)}`}
                    sx={{
                      height: 40,
                      '&:hover': { backgroundColor: '#fafafa' },
                      cursor: 'pointer',
                    }}
                    hover
                  >
                    {orderedVisibleColumns.map((columnId) => (
                      <TableCell key={`${getIssueRowId(issue)}-${columnId}`} sx={{ fontSize: '0.875rem' }}>
                        {renderCellValue(issue, columnId)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <TablePagination
            rowsPerPageOptions={[25, 50, 100]}
            component="div"
            count={totalCount}
            rowsPerPage={viewState.pageSize}
            page={viewState.page}
            onPageChange={(event, newPage) => updateViewState({ page: newPage })}
            onRowsPerPageChange={(event) =>
              updateViewState({ pageSize: parseInt(event.target.value, 10), page: 0 })
            }
          />
        </>
      )}

      {/* Empty state */}
      {!isLoading && rows.length === 0 && (
        <Alert severity="info">No issues found. Try adjusting your filters.</Alert>
      )}

      <IssuesColumnsPopover
        anchorEl={columnsAnchorEl}
        onClose={handleColumnsClose}
        columns={ISSUE_COLUMNS as { id: string; label: string }[]}
        visibleColumnIds={visibleColumns}
        orderedColumnIds={columnOrder}
        toggleColumn={toggleColumn}
        moveColumn={moveColumn}
        resetToDefaults={resetColumns}
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
              background: 'linear-gradient(180deg, rgba(17,24,39,0.04) 0%, rgba(17,24,39,0.0) 100%)',
            }}
          >
            <Box sx={{ px: 2, py: 1.5 }}>
              <Typography variant="subtitle2" fontWeight={700}>
                Filters
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Narrow the issues list
              </Typography>
            </Box>
            <Divider />
            <List dense disablePadding>
              {filterCategories.map((category) => {
                const count = (filterSelections as any)[category.id]?.length ?? 0;
                const active = activeFilterCategory === category.id;
                return (
                  <ListItemButton
                    key={category.id}
                    onClick={() => setActiveFilterCategory(category.id)}
                    selected={active}
                    sx={{
                      px: 2,
                      py: 1,
                      '&.Mui-selected': { backgroundColor: 'rgba(25,118,210,0.08)' },
                    }}
                  >
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
              {(filterSelections as any)[activeFilterCategory]?.length > 0 && (
                <Button size="small" onClick={() => clearFilterCategory(activeFilterCategory)} sx={{ textTransform: 'none' }}>
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
                    <ListItemButton key={option.value} onClick={() => toggleFilterValue(activeFilterCategory, option.value)}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Checkbox
                          edge="start"
                          checked={(filterSelections as any)[activeFilterCategory]?.includes(option.value)}
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
                <Button size="small" onClick={clearFilters} sx={{ textTransform: 'none' }}>
                  Clear all
                </Button>
              )}
            </Stack>
          </Box>
        </Box>
      </Popover>
    </Box>
  );
}
