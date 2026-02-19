import { useEffect, useMemo, useState, useCallback } from 'react';
import type { MouseEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Popover,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  Typography,
} from '@mui/material';
import {
  FilterAlt,
  ViewColumn,
  BusinessOutlined,
  BadgeOutlined,
  PeopleOutline,
  TaskAltOutlined,
  VisibilityOutlined,
  PersonOutline,
  VpnKeyOutlined,
} from '@mui/icons-material';
import { masterUsersApi } from '@/api';
import type { MasterUser } from '@/types/api';
import {
  USER_FIELD_MAP,
  renderFieldValue,
  type UserFieldDefinition,
} from '@/features/users/fields/UserFieldRegistry';
import { useUserViewLayout } from '@/features/users/fields/useUserViewLayout';
import { UserColumnsPopover } from '@/features/users/fields/UserColumnsPopover';

type SortOrder = 'asc' | 'desc';

type FilterCategory =
  | 'source'
  | 'company'
  | 'role'
  | 'status'
  | 'license'
  | 'meeting'
  | 'watcher'
  | 'assignee';

type FilterSelections = Record<FilterCategory, string[]>;

const FILTER_STORAGE_KEY = 'master_users_filter_selections';

const safeParseStoredFilters = (): FilterSelections => {
  if (typeof window === 'undefined') {
    return {
      source: [],
      company: [],
      role: [],
      status: [],
      license: [],
      meeting: [],
      watcher: [],
      assignee: [],
    };
  }
  const raw = window.localStorage.getItem(FILTER_STORAGE_KEY);
  if (!raw) {
    return {
      source: [],
      company: [],
      role: [],
      status: [],
      license: [],
      meeting: [],
      watcher: [],
      assignee: [],
    };
  }
  try {
    const parsed = JSON.parse(raw) as Partial<FilterSelections> | null;
    return {
      source: Array.isArray(parsed?.source) ? parsed!.source : [],
      company: Array.isArray(parsed?.company) ? parsed!.company : [],
      role: Array.isArray(parsed?.role) ? parsed!.role : [],
      status: Array.isArray(parsed?.status) ? parsed!.status : [],
      license: Array.isArray(parsed?.license) ? parsed!.license : [],
      meeting: Array.isArray(parsed?.meeting) ? parsed!.meeting : [],
      watcher: Array.isArray(parsed?.watcher) ? parsed!.watcher : [],
      assignee: Array.isArray(parsed?.assignee) ? parsed!.assignee : [],
    };
  } catch {
    return {
      source: [],
      company: [],
      role: [],
      status: [],
      license: [],
      meeting: [],
      watcher: [],
      assignee: [],
    };
  }
};

const normalizeBooleanFilter = (value?: boolean | null) => {
  if (value === true) return 'yes';
  if (value === false) return 'no';
  return 'unknown';
};

const normalizeText = (value?: string | null) => {
  const trimmed = (value ?? '').trim();
  return trimmed ? trimmed : 'Unassigned';
};

const resolveSortValue = (user: MasterUser, fieldId: string) => {
  const field = USER_FIELD_MAP.get(fieldId);
  if (!field) return '';
  const raw = field.accessor(user);
  if (field.format === 'date') {
    const parsed = raw ? new Date(String(raw)).getTime() : 0;
    return Number.isFinite(parsed) ? parsed : 0;
  }
  if (field.format === 'number') {
    const numeric = Number(raw);
    return Number.isFinite(numeric) ? numeric : 0;
  }
  if (field.format === 'boolean') {
    if (raw === true) return 1;
    if (raw === false) return 0;
    return -1;
  }
  return (raw ?? '').toString().toLowerCase();
};

export default function MasterUsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [columnsAnchorEl, setColumnsAnchorEl] = useState<HTMLElement | null>(null);
  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(null);
  const [activeFilterCategory, setActiveFilterCategory] = useState<FilterCategory>('source');
  const [filterSearch, setFilterSearch] = useState('');
  const [filterSelections, setFilterSelections] = useState<FilterSelections>(safeParseStoredFilters);
  const [refreshing, setRefreshing] = useState(false);

  const listLayout = useUserViewLayout('list');

  const { data: users = [], isLoading, error, refetch } = useQuery<MasterUser[]>({
    queryKey: ['master-users'],
    queryFn: () => masterUsersApi.list(),
    staleTime: 60_000,
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filterSelections));
  }, [filterSelections]);

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
      source: [],
      company: [],
      role: [],
      status: [],
      license: [],
      meeting: [],
      watcher: [],
      assignee: [],
    });
  };

  const handleSortClick = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const filteredUsers = useMemo(() => {
    const filtered = users.filter((user) => {
      const search = searchTerm.trim().toLowerCase();
      if (search) {
        const haystack = [
          user.name,
          user.email,
          user.company,
          user.role,
          user.source_system,
          user.license_type,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(search)) {
          return false;
        }
      }

      if (filterSelections.source.length) {
        const key = normalizeText(user.source_system);
        if (!filterSelections.source.includes(key)) return false;
      }
      if (filterSelections.company.length) {
        const key = normalizeText(user.company);
        if (!filterSelections.company.includes(key)) return false;
      }
      if (filterSelections.role.length) {
        const key = normalizeText(user.role);
        if (!filterSelections.role.includes(key)) return false;
      }
      if (filterSelections.status.length) {
        const key = normalizeText(user.status);
        if (!filterSelections.status.includes(key)) return false;
      }
      if (filterSelections.license.length) {
        const key = normalizeText(user.license_type);
        if (!filterSelections.license.includes(key)) return false;
      }
      if (filterSelections.meeting.length) {
        const key = normalizeBooleanFilter(user.invited_to_bim_meetings);
        if (!filterSelections.meeting.includes(key)) return false;
      }
      if (filterSelections.watcher.length) {
        const key = normalizeBooleanFilter(user.is_watcher);
        if (!filterSelections.watcher.includes(key)) return false;
      }
      if (filterSelections.assignee.length) {
        const key = normalizeBooleanFilter(user.is_assignee);
        if (!filterSelections.assignee.includes(key)) return false;
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
  }, [users, searchTerm, filterSelections, sortField, sortOrder]);

  const listFieldIds = listLayout.orderedVisibleFieldIds;
  const listFields = listFieldIds
    .map((id) => USER_FIELD_MAP.get(id))
    .filter(Boolean) as UserFieldDefinition[];

  const pinnedFieldIds = listLayout.pinnedFieldIds.filter((id) => listFieldIds.includes(id));
  const pinnedOffsets = useMemo(() => {
    const offsets = new Map<string, number>();
    let currentLeft = 0;
    listFieldIds.forEach((id) => {
      if (!pinnedFieldIds.includes(id)) return;
      const field = USER_FIELD_MAP.get(id);
      const width = field?.width ?? 160;
      offsets.set(id, currentLeft);
      currentLeft += width;
    });
    return offsets;
  }, [listFieldIds, pinnedFieldIds]);

  const getStickyStyles = (fieldId: string, zIndex: number) => {
    if (!pinnedOffsets.has(fieldId)) return {};
    return {
      position: 'sticky' as const,
      left: pinnedOffsets.get(fieldId),
      zIndex,
      backgroundColor: 'background.paper',
    };
  };

  const filterCategories = useMemo(
    () => [
      { id: 'source' as const, label: 'Source', icon: <PeopleOutline fontSize="small" /> },
      { id: 'company' as const, label: 'Company', icon: <BusinessOutlined fontSize="small" /> },
      { id: 'role' as const, label: 'Role', icon: <BadgeOutlined fontSize="small" /> },
      { id: 'status' as const, label: 'Status', icon: <TaskAltOutlined fontSize="small" /> },
      { id: 'license' as const, label: 'License', icon: <VpnKeyOutlined fontSize="small" /> },
      { id: 'meeting' as const, label: 'BIM Meetings', icon: <PersonOutline fontSize="small" /> },
      { id: 'watcher' as const, label: 'Watcher', icon: <VisibilityOutlined fontSize="small" /> },
      { id: 'assignee' as const, label: 'Assignee', icon: <PersonOutline fontSize="small" /> },
    ],
    [],
  );

  const activeFilterCount = useMemo(
    () =>
      filterSelections.source.length +
      filterSelections.company.length +
      filterSelections.role.length +
      filterSelections.status.length +
      filterSelections.license.length +
      filterSelections.meeting.length +
      filterSelections.watcher.length +
      filterSelections.assignee.length,
    [filterSelections],
  );

  const filterOptions = useMemo(() => {
    const source = new Set<string>();
    const company = new Set<string>();
    const role = new Set<string>();
    const status = new Set<string>();
    const license = new Set<string>();

    users.forEach((user) => {
      source.add(normalizeText(user.source_system));
      company.add(normalizeText(user.company));
      role.add(normalizeText(user.role));
      status.add(normalizeText(user.status));
      license.add(normalizeText(user.license_type));
    });

    const booleanOptions = [
      { value: 'yes', label: 'Yes' },
      { value: 'no', label: 'No' },
      { value: 'unknown', label: 'Unknown' },
    ];

    const toOptions = (values: Set<string>) =>
      Array.from(values)
        .map((value) => ({ value, label: value }))
        .sort((a, b) => a.label.localeCompare(b.label));

    return {
      source: toOptions(source),
      company: toOptions(company),
      role: toOptions(role),
      status: toOptions(status),
      license: toOptions(license),
      meeting: booleanOptions,
      watcher: booleanOptions,
      assignee: booleanOptions,
    };
  }, [users]);

  const activeOptions = filterOptions[activeFilterCategory];

  const filteredOptions = useMemo(() => {
    const trimmed = filterSearch.trim().toLowerCase();
    if (!trimmed) return activeOptions;
    return activeOptions.filter((option) => option.label.toLowerCase().includes(trimmed));
  }, [activeOptions, filterSearch]);

  const updateFlag = useCallback(
    async (
      userKey: string,
      fieldId: 'invited_to_bim_meetings' | 'is_watcher' | 'is_assignee',
      value: boolean,
    ) => {
      await masterUsersApi.updateFlags(userKey, { [fieldId]: value });
      refetch();
    },
    [refetch],
  );

  const renderCellValue = useCallback(
    (fieldId: string, user: MasterUser) => {
      const field = USER_FIELD_MAP.get(fieldId);
      if (!field) return '--';
      if (fieldId === 'invited_to_bim_meetings' || fieldId === 'is_watcher' || fieldId === 'is_assignee') {
        const currentValue = user[fieldId];
        return (
          <Checkbox
            checked={currentValue === true}
            indeterminate={currentValue == null}
            onChange={(event) => updateFlag(user.user_key, fieldId, event.target.checked)}
            inputProps={{ 'aria-label': field.label }}
          />
        );
      }
      return renderFieldValue(field, user);
    },
    [updateFlag],
  );

  return (
    <Box data-testid="master-users-root" sx={{ display: 'grid', gap: 2, p: 2 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} justifyContent="space-between">
        <Stack spacing={0.5}>
          <Typography variant="h4">Master Users</Typography>
          <Typography variant="body2" color="text.secondary">
            Unified directory across ACC and Revizto users with BIM meeting visibility.
          </Typography>
        </Stack>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
          <Button
            variant="outlined"
            size="small"
            disabled={refreshing}
            onClick={async () => {
              try {
                setRefreshing(true);
                await masterUsersApi.refreshReviztoUsers();
              } finally {
                await refetch();
                setRefreshing(false);
              }
            }}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<FilterAlt />}
            onClick={handleFiltersOpen}
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
            placeholder="Search users"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            sx={{ minWidth: 220 }}
            inputProps={{ 'data-testid': 'master-users-search' }}
          />
          <Button
            variant="outlined"
            size="small"
            startIcon={<ViewColumn />}
            onClick={handleColumnsOpen}
            data-testid="master-users-columns-button"
          >
            Columns
          </Button>
        </Stack>
      </Stack>

      <UserColumnsPopover
        view="list"
        anchorEl={columnsAnchorEl}
        onClose={handleColumnsClose}
        visibleFieldIds={listLayout.visibleFieldIds}
        orderedFieldIds={listLayout.orderedFieldIds}
        pinnedFieldIds={listLayout.pinnedFieldIds}
        toggleField={listLayout.toggleField}
        moveField={listLayout.moveField}
        togglePinnedField={listLayout.togglePinnedField}
        resetToDefaults={listLayout.resetToDefaults}
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
                Narrow the master users list
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

      {error && (
        <Alert severity="error">Failed to load master users.</Alert>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!isLoading && !error && (
        <Paper sx={{ p: 1.5 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ px: 1, py: 0.5 }}>
            <Typography variant="subtitle2">
              Showing {filteredUsers.length} of {users.length} users
            </Typography>
            {activeFilterCount > 0 && (
              <Button size="small" onClick={clearAllFilters} sx={{ textTransform: 'none' }}>
                Clear filters
              </Button>
            )}
          </Stack>
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  {listFields.map((field) => (
                    <TableCell
                      key={field.id}
                      sx={{
                        fontWeight: 600,
                        minWidth: field.width ?? 140,
                        ...(field.align ? { textAlign: field.align } : null),
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
                {filteredUsers.map((user) => (
                  <TableRow key={user.user_key} hover sx={{ '&:hover': { backgroundColor: '#fafafa' } }}>
                    {listFields.map((field) => (
                      <TableCell
                        key={`${user.user_key}-${field.id}`}
                        sx={{
                          fontSize: '0.875rem',
                          ...(field.align ? { textAlign: field.align } : null),
                          ...getStickyStyles(field.id, 2),
                        }}
                      >
                        {renderCellValue(field.id, user)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {filteredUsers.length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              No users found. Try adjusting your filters.
            </Alert>
          )}
        </Paper>
      )}
    </Box>
  );
}
