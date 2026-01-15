import React, { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  CircularProgress,
  Alert,
  Paper,
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
import { issuesApi } from '../api/issues';

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
  [key: string]: any;
}

interface ViewState {
  searchText: string;
  sourceSystem?: string;
  statusNormalized?: string;
  priorityNormalized?: string;
  disciplineNormalized?: string;
  assigneeUserKey?: string;
  page: number;
  pageSize: number;
  sortBy: string;
  sortDir: 'asc' | 'desc';
}

const PRESET_VIEWS = {
  ALL: 'all',
  OPEN: 'open',
  CLOSED: 'closed',
  ACC_ONLY: 'acc_only',
  REVIZTO_ONLY: 'revizto_only',
};

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

export function IssuesPage() {
  const [viewState, setViewState] = useState<ViewState>(() => {
    const saved = localStorage.getItem('issues_view_state');
    if (saved) {
      try {
        return { ...DEFAULT_VIEW_STATE, ...JSON.parse(saved) };
      } catch {
        return DEFAULT_VIEW_STATE;
      }
    }
    return DEFAULT_VIEW_STATE;
  });

  const [activePreset, setActivePreset] = useState<string | null>(null);

  // Persist view state to localStorage
  const updateViewState = useCallback((updates: Partial<ViewState>) => {
    setViewState((prev) => {
      const next = { ...prev, ...updates, page: updates.page !== undefined ? updates.page : 0 };
      localStorage.setItem('issues_view_state', JSON.stringify(next));
      return next;
    });
  }, []);

  // Apply preset filters
  const applyPreset = useCallback(
    (preset: string) => {
      setActivePreset(preset);
      const updates: Partial<ViewState> = { page: 0, searchText: '' };

      switch (preset) {
        case PRESET_VIEWS.OPEN:
          updates.statusNormalized = 'open';
          break;
        case PRESET_VIEWS.CLOSED:
          updates.statusNormalized = 'closed';
          break;
        case PRESET_VIEWS.ACC_ONLY:
          updates.sourceSystem = 'ACC';
          break;
        case PRESET_VIEWS.REVIZTO_ONLY:
          updates.sourceSystem = 'Revizto';
          break;
        case PRESET_VIEWS.ALL:
        default:
          updates.sourceSystem = undefined;
          updates.statusNormalized = undefined;
          setActivePreset(null);
          break;
      }

      updateViewState(updates);
    },
    [updateViewState],
  );

  // Fetch issues using the normalized /api/issues/table endpoint
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: [
      'issues-table',
      viewState.searchText,
      viewState.sourceSystem,
      viewState.statusNormalized,
      viewState.priorityNormalized,
      viewState.disciplineNormalized,
      viewState.assigneeUserKey,
      viewState.page,
      viewState.pageSize,
      viewState.sortBy,
      viewState.sortDir,
    ],
    queryFn: async () => {
      return issuesApi.getIssuesTable({
        search: viewState.searchText || undefined,
        source_system: viewState.sourceSystem as 'ACC' | 'Revizto' | undefined,
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

  const rows: IssueRow[] = useMemo(() => data?.rows ?? [], [data?.rows]);
  const totalCount = useMemo(() => data?.total_count ?? 0, [data?.total_count]);

  const clearFilters = useCallback(() => {
    setActivePreset(null);
    updateViewState({
      searchText: '',
      sourceSystem: undefined,
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
      viewState.sourceSystem ||
      viewState.statusNormalized ||
      viewState.priorityNormalized ||
      viewState.disciplineNormalized ||
      viewState.assigneeUserKey
    );
  }, [viewState]);

  const getIssueRowId = (issue: IssueRow): string => {
    return `${issue.source_system}-${issue.display_id}`.replace(/[^a-zA-Z0-9-]/g, '_');
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
            {/* Preset buttons */}
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant={activePreset === null && !hasActiveFilters ? 'contained' : 'outlined'}
                onClick={() => applyPreset(PRESET_VIEWS.ALL)}
              >
                All
              </Button>
              <Button
                size="small"
                variant={activePreset === PRESET_VIEWS.OPEN ? 'contained' : 'outlined'}
                onClick={() => applyPreset(PRESET_VIEWS.OPEN)}
              >
                Open
              </Button>
              <Button
                size="small"
                variant={activePreset === PRESET_VIEWS.CLOSED ? 'contained' : 'outlined'}
                onClick={() => applyPreset(PRESET_VIEWS.CLOSED)}
              >
                Closed
              </Button>
              <Button
                size="small"
                variant={activePreset === PRESET_VIEWS.ACC_ONLY ? 'contained' : 'outlined'}
                onClick={() => applyPreset(PRESET_VIEWS.ACC_ONLY)}
              >
                ACC Only
              </Button>
              <Button
                size="small"
                variant={activePreset === PRESET_VIEWS.REVIZTO_ONLY ? 'contained' : 'outlined'}
                onClick={() => applyPreset(PRESET_VIEWS.REVIZTO_ONLY)}
              >
                Revizto Only
              </Button>
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
            </Stack>

            {/* Filter inputs */}
            <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start', flexWrap: 'wrap' }}>
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

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Priority</InputLabel>
                <Select
                  label="Priority"
                  value={viewState.priorityNormalized || ''}
                  onChange={(e) =>
                    updateViewState({ priorityNormalized: e.target.value || undefined, page: 0 })
                  }
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Discipline</InputLabel>
                <Select
                  label="Discipline"
                  value={viewState.disciplineNormalized || ''}
                  onChange={(e) =>
                    updateViewState({ disciplineNormalized: e.target.value || undefined, page: 0 })
                  }
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="architectural">Architectural</MenuItem>
                  <MenuItem value="structural">Structural</MenuItem>
                  <MenuItem value="mep">MEP</MenuItem>
                  <MenuItem value="civil">Civil</MenuItem>
                  <MenuItem value="general">General</MenuItem>
                </Select>
              </FormControl>
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
                  <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>Display ID</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 300 }}>Title</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 80 }}>Priority</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>Discipline</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>Assignee</TableCell>
                  <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>Updated</TableCell>
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
                    <TableCell sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                      {issue.display_id}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.875rem' }}>
                      {issue.title || issue.issue_key}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={issue.status_normalized || 'Unknown'}
                        size="small"
                        color={
                          STATUS_COLORS[issue.status_normalized?.toLowerCase()] || 'default'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={issue.priority_normalized || 'N/A'}
                        size="small"
                        color={
                          PRIORITY_COLORS[issue.priority_normalized?.toLowerCase()] || 'default'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.875rem' }}>
                      {issue.discipline_normalized || '-'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.875rem' }}>
                      {issue.assignee_user_key || '-'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                      {new Date(issue.updated_at).toLocaleDateString()}
                    </TableCell>
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
    </Box>
  );
}
