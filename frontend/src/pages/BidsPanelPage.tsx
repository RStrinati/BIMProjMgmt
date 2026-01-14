import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { bidsApi, usersApi } from '@/api';
import type { Bid, User } from '@/types/api';
import { ListView } from '@/components/ui/ListView';
import { DetailsPanel } from '@/components/ui/DetailsPanel';
import { InlineField } from '@/components/ui/InlineField';

const VIEW_STORAGE_KEY = 'bids_panel_view_state';
const DAY_MS = 24 * 60 * 60 * 1000;

type ViewId = 'all' | 'pipeline' | 'high_probability' | 'due_soon' | 'my_bids';

type ViewState = {
  viewId: ViewId;
  searchTerm: string;
};

const VIEW_IDS: ViewId[] = ['all', 'pipeline', 'high_probability', 'due_soon', 'my_bids'];

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

const stableSerialize = (value: Record<string, unknown>) =>
  JSON.stringify(value, Object.keys(value).sort());

const normaliseStatus = (value?: string | null) =>
  value ? value.trim().toUpperCase().replace(/\s+/g, '_') : '';

const parseDateValue = (value?: string | null) => {
  if (!value) {
    return 0;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getTime();
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '--';
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatPercent = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return `${Math.round(Number(value))}%`;
};

const formatDueDate = (bid: Bid) => {
  if (!bid.validity_days) {
    return '--';
  }
  const baseDate = parseDateValue(bid.created_at || bid.updated_at);
  if (!baseDate) {
    return '--';
  }
  const due = new Date(baseDate + bid.validity_days * DAY_MS);
  return due.toLocaleDateString();
};

export default function BidsPanelPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const storedViewState = useMemo(() => safeParseStoredViewState(), []);
  const [viewId, setViewId] = useState<ViewId>(storedViewState.viewId);
  const [searchTerm, setSearchTerm] = useState(storedViewState.searchTerm);
  const [selectedId, setSelectedId] = useState<number | null>(null);

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

  const viewDefinitions = useMemo(() => {
    const terminalStatuses = new Set(['AWARDED', 'LOST', 'ARCHIVED']);
    return [
      { id: 'all' as const, label: 'All', filter: (_: Bid) => true, sort: (a: Bid, b: Bid) => parseDateValue(b.updated_at || b.created_at) - parseDateValue(a.updated_at || a.created_at) },
      {
        id: 'pipeline' as const,
        label: 'Pipeline',
        filter: (bid: Bid) => {
          const status = normaliseStatus(bid.status);
          return !status || !terminalStatuses.has(status);
        },
        sort: (a: Bid, b: Bid) => parseDateValue(b.updated_at || b.created_at) - parseDateValue(a.updated_at || a.created_at),
      },
      {
        id: 'high_probability' as const,
        label: 'High Probability',
        filter: (bid: Bid) => (bid.probability ?? 0) >= 70,
        sort: (a: Bid, b: Bid) => (b.probability ?? 0) - (a.probability ?? 0),
      },
      {
        id: 'due_soon' as const,
        label: 'Due Soon',
        filter: (bid: Bid) => {
          if (!bid.validity_days) {
            return false;
          }
          const baseDate = parseDateValue(bid.created_at || bid.updated_at);
          if (!baseDate) {
            return false;
          }
          const dueDate = baseDate + bid.validity_days * DAY_MS;
          const daysUntil = (dueDate - Date.now()) / DAY_MS;
          return daysUntil >= 0 && daysUntil <= 14;
        },
        sort: (a: Bid, b: Bid) => {
          const aBase = parseDateValue(a.created_at || a.updated_at);
          const bBase = parseDateValue(b.created_at || b.updated_at);
          const aDue = a.validity_days ? aBase + a.validity_days * DAY_MS : 0;
          const bDue = b.validity_days ? bBase + b.validity_days * DAY_MS : 0;
          return aDue - bDue;
        },
      },
      {
        id: 'my_bids' as const,
        label: 'My Bids',
        filter: (bid: Bid) => (currentUserId != null ? bid.owner_user_id === currentUserId : false),
        sort: (a: Bid, b: Bid) => parseDateValue(b.updated_at || b.created_at) - parseDateValue(a.updated_at || a.created_at),
      },
    ];
  }, [currentUserId]);

  const activeView = viewDefinitions.find((view) => view.id === viewId) ?? viewDefinitions[0];

  const bidsFilters = useMemo(
    () => ({
      viewId: activeView.id,
      currentUserId: activeView.id === 'my_bids' ? currentUserId : null,
    }),
    [activeView.id, currentUserId],
  );
  const bidsFiltersKey = useMemo(() => stableSerialize(bidsFilters), [bidsFilters]);

  const { data: schema } = useQuery({
    queryKey: ['schema-health'],
    queryFn: () => bidsApi.getSchemaHealth(),
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 60 * 1000,
  });
  const schemaReady = schema?.bid_module_ready !== false;

  const { data: bids = [], isLoading, error } = useQuery({
    queryKey: ['bids', bidsFiltersKey],
    queryFn: () => bidsApi.list(),
    enabled: schemaReady,
  });

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const ownerLabel = useMemo(() => {
    const map = new Map<number, string>();
    users.forEach((user) => {
      const label = user.name || user.full_name || user.username || `User ${user.user_id}`;
      map.set(user.user_id, label);
    });
    return map;
  }, [users]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(
      VIEW_STORAGE_KEY,
      JSON.stringify({ viewId, searchTerm } satisfies ViewState),
    );
  }, [viewId, searchTerm]);

  const handleResetFilters = () => {
    setViewId(DEFAULT_VIEW_STATE.viewId);
    setSearchTerm(DEFAULT_VIEW_STATE.searchTerm);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(VIEW_STORAGE_KEY);
    }
  };

  const showMyBidsHint = activeView.id === 'my_bids' && currentUserId == null;

  const filtered = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();
    const viewFiltered = bids.filter(activeView.filter);
    const searched = normalized
      ? viewFiltered.filter((bid) =>
          [bid.bid_name, bid.client_name, bid.project_name]
            .map((value) => (value ? String(value).toLowerCase() : ''))
            .some((value) => value.includes(normalized)),
        )
      : viewFiltered;
    const sorted = activeView.sort ? [...searched].sort(activeView.sort) : searched;
    return sorted;
  }, [bids, searchTerm, activeView]);

  const selectedBid = filtered.find((bid) => bid.bid_id === selectedId) ?? filtered[0] ?? null;

  const handleHover = (bid: Bid) => {
    queryClient.prefetchQuery({
      queryKey: ['bid', bid.bid_id],
      queryFn: () => bidsApi.get(bid.bid_id),
    });
  };

  if (schema && !schemaReady) {
    return (
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Bids
        </Typography>
        <Alert severity="warning">
          Module not enabled - pending DB migration. Please run the Bid Management DBA Migration Pack.
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      data-testid="bids-panel-root"
      sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '360px 1fr' }, gap: 2 }}
    >
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Typography variant="h5">Bids</Typography>
          <Stack spacing={1}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Typography variant="subtitle2">Views</Typography>
              <Button size="small" onClick={handleResetFilters} data-testid="bids-panel-view-reset">
                Reset
              </Button>
            </Stack>
            <ToggleButtonGroup
              exclusive
              value={viewId}
              onChange={(_event, nextView) => {
                if (nextView) {
                  setViewId(nextView);
                }
              }}
              size="small"
              fullWidth
              data-testid="bids-panel-view-group"
            >
              {viewDefinitions.map((view) => (
                <ToggleButton key={view.id} value={view.id} data-testid={`bids-panel-view-${view.id}`}>
                  {view.label}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip label={`View: ${activeView.label}`} size="small" variant="outlined" />
              {searchTerm.trim() && (
                <Chip label={`Search: ${searchTerm.trim()}`} size="small" variant="outlined" />
              )}
            </Stack>
            {showMyBidsHint && (
              <Typography variant="caption" color="warning.main">
                Set `current_user_id` in localStorage to enable My Bids filtering.
              </Typography>
            )}
          </Stack>
          <TextField
            placeholder="Search bids..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <Divider />
          <ListView<Bid>
            items={filtered}
            getItemId={(bid) => bid.bid_id}
            getItemTestId={(bid) => `bids-panel-list-row-${bid.bid_id}`}
            selectedId={selectedBid?.bid_id ?? null}
            onSelect={(bid) => setSelectedId(bid.bid_id)}
            onHover={handleHover}
            renderPrimary={(bid) => bid.bid_name}
            renderSecondary={(bid) => bid.client_name || bid.project_name || 'Opportunity'}
            emptyState={
              <Typography color="text.secondary" sx={{ px: 2 }}>
                {isLoading ? 'Loading bids...' : 'No bids found.'}
              </Typography>
            }
          />
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 3 }} data-testid="bids-panel-details">
        <DetailsPanel
          title={selectedBid?.bid_name ?? 'Select a bid'}
          subtitle={selectedBid?.client_name || selectedBid?.project_name || 'Opportunity'}
          actions={
            selectedBid && (
              <Button size="small" onClick={() => navigate(`/bids/${selectedBid.bid_id}`)}>
                Open full bid
              </Button>
            )
          }
          emptyState={<Typography color="text.secondary">Select a bid to view details.</Typography>}
        >
          {selectedBid && (
            <Stack spacing={2}>
              {error && <Alert severity="error">Failed to load bids.</Alert>}
              <InlineField label="Status" value={selectedBid.status} />
              <InlineField label="Type" value={selectedBid.bid_type} />
              <InlineField label="Probability" value={formatPercent(selectedBid.probability)} />
              <InlineField
                label="Owner"
                value={
                  selectedBid.owner_name ||
                  (selectedBid.owner_user_id ? ownerLabel.get(selectedBid.owner_user_id) : '') ||
                  'Unassigned'
                }
              />
              <InlineField label="Stage framework" value={selectedBid.stage_framework} />
              <InlineField label="Validity days" value={selectedBid.validity_days ?? '--'} />
              <InlineField label="Valid until" value={formatDueDate(selectedBid)} />
              <InlineField label="Created" value={formatDate(selectedBid.created_at)} />
              <InlineField label="Updated" value={formatDate(selectedBid.updated_at)} />
              <InlineField label="Notes" value={selectedBid.pi_notes} />
            </Stack>
          )}
        </DetailsPanel>
      </Paper>
    </Box>
  );
}
