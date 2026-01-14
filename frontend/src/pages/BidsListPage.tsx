import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { bidsApi, clientsApi, projectsApi, usersApi } from '@/api';
import type { Bid, Client, Project, User } from '@/types/api';
import { featureFlags } from '@/config/featureFlags';
import BidsPanelPage from '@/pages/BidsPanelPage';

const BID_STATUSES = ['DRAFT', 'SUBMITTED', 'AWARDED', 'LOST', 'ARCHIVED'];
const BID_TYPES = ['PROPOSAL', 'FEE_UPDATE', 'VARIATION'];

const emptyBidDraft: Partial<Bid> = {
  bid_name: '',
  bid_type: 'PROPOSAL',
  status: 'DRAFT',
  currency_code: 'AUD',
  stage_framework: 'CUSTOM',
  gst_included: true,
};

export function BidsListPage() {
  if (featureFlags.bidsPanel) {
    return <BidsPanelPage />;
  }

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [clientFilter, setClientFilter] = useState<number | ''>('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formState, setFormState] = useState<Partial<Bid>>(emptyBidDraft);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: schema } = useQuery({
    queryKey: ['schema-health'],
    queryFn: () => bidsApi.getSchemaHealth(),
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 60 * 1000,
  });

  const schemaReady = schema?.bid_module_ready !== false;

  const { data: bids, isLoading, error } = useQuery({
    queryKey: ['bids', statusFilter, clientFilter, projectFilter],
    queryFn: () =>
      bidsApi.list({
        status: statusFilter || undefined,
        client_id: typeof clientFilter === 'number' ? clientFilter : undefined,
        project_id: typeof projectFilter === 'number' ? projectFilter : undefined,
      }),
    enabled: schemaReady,
  });

  const { data: clients } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: () => clientsApi.getAll(),
  });

  const { data: projects } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  const { data: users } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const ownerLabel = useMemo(() => {
    const map = new Map<number, string>();
    (users ?? []).forEach((user) => {
      const label = user.name || user.full_name || user.username || `User ${user.user_id}`;
      map.set(user.user_id, label);
    });
    return map;
  }, [users]);

  const handleOpenDialog = () => {
    setFormState(emptyBidDraft);
    setFormError(null);
    setDialogOpen(true);
  };

  const handleCreateBid = async () => {
    if (!formState.bid_name || formState.bid_name.trim() === '') {
      setFormError('Bid name is required.');
      return;
    }
    try {
      await bidsApi.create(formState);
      setDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['bids'] });
    } catch (err: any) {
      setFormError(err?.response?.data?.error || 'Failed to create bid.');
    }
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
    <Box data-testid="bids-legacy-root">
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Bids
          </Typography>
          <Typography color="text.secondary">
            Track proposal pipelines, scope, and award workflows.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenDialog}>
          New Bid
        </Button>
      </Stack>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            {BID_STATUSES.map((status) => (
              <MenuItem key={status} value={status}>
                {status}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Client</InputLabel>
          <Select
            label="Client"
            value={clientFilter}
            onChange={(event) => setClientFilter(event.target.value === '' ? '' : Number(event.target.value))}
          >
            <MenuItem value="">All</MenuItem>
            {(clients ?? []).map((client) => (
              <MenuItem key={client.client_id} value={client.client_id}>
                {client.client_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Project</InputLabel>
          <Select
            label="Project"
            value={projectFilter}
            onChange={(event) => setProjectFilter(event.target.value === '' ? '' : Number(event.target.value))}
          >
            <MenuItem value="">All</MenuItem>
            {(projects ?? []).map((project) => (
              <MenuItem key={project.project_id} value={project.project_id}>
                {project.project_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      {error && <Alert severity="error">Failed to load bids.</Alert>}

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Bid</TableCell>
            <TableCell>Client</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Probability</TableCell>
            <TableCell>Owner</TableCell>
            <TableCell>Updated</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(bids ?? []).map((bid) => (
            <TableRow
              key={bid.bid_id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/bids/${bid.bid_id}`)}
            >
              <TableCell>
                <Typography sx={{ fontWeight: 600 }}>{bid.bid_name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {bid.project_name || 'Opportunity'}
                </Typography>
              </TableCell>
              <TableCell>{bid.client_name || 'Unassigned'}</TableCell>
              <TableCell>{bid.bid_type}</TableCell>
              <TableCell>{bid.status}</TableCell>
              <TableCell>{bid.probability != null ? `${bid.probability}%` : '—'}</TableCell>
              <TableCell>
                {bid.owner_name ||
                  (bid.owner_user_id ? ownerLabel.get(bid.owner_user_id) : '') ||
                  '—'}
              </TableCell>
              <TableCell>
                {bid.updated_at ? new Date(bid.updated_at).toLocaleDateString() : '—'}
              </TableCell>
            </TableRow>
          ))}
          {!isLoading && (bids ?? []).length === 0 && (
            <TableRow>
              <TableCell colSpan={7}>
                <Alert severity="info">No bids match the current filters.</Alert>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Bid</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {formError && <Alert severity="error">{formError}</Alert>}
            <TextField
              label="Bid name"
              value={formState.bid_name ?? ''}
              onChange={(event) => setFormState((prev) => ({ ...prev, bid_name: event.target.value }))}
              required
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  label="Type"
                  value={formState.bid_type ?? 'PROPOSAL'}
                  onChange={(event) => setFormState((prev) => ({ ...prev, bid_type: event.target.value }))}
                >
                  {BID_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  label="Status"
                  value={formState.status ?? 'DRAFT'}
                  onChange={(event) => setFormState((prev) => ({ ...prev, status: event.target.value }))}
                >
                  {BID_STATUSES.map((status) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Client</InputLabel>
                <Select
                  label="Client"
                  value={formState.client_id ?? ''}
                  onChange={(event) =>
                    setFormState((prev) => ({
                      ...prev,
                      client_id: event.target.value === '' ? undefined : Number(event.target.value),
                    }))
                  }
                >
                  <MenuItem value="">Unassigned</MenuItem>
                  {(clients ?? []).map((client) => (
                    <MenuItem key={client.client_id} value={client.client_id}>
                      {client.client_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Project</InputLabel>
                <Select
                  label="Project"
                  value={formState.project_id ?? ''}
                  onChange={(event) =>
                    setFormState((prev) => ({
                      ...prev,
                      project_id: event.target.value === '' ? undefined : Number(event.target.value),
                    }))
                  }
                >
                  <MenuItem value="">Opportunity</MenuItem>
                  {(projects ?? []).map((project) => (
                    <MenuItem key={project.project_id} value={project.project_id}>
                      {project.project_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Probability %"
                type="number"
                value={formState.probability ?? ''}
                onChange={(event) =>
                  setFormState((prev) => ({
                    ...prev,
                    probability: event.target.value === '' ? undefined : Number(event.target.value),
                  }))
                }
              />
              <FormControl fullWidth>
                <InputLabel>Owner</InputLabel>
                <Select
                  label="Owner"
                  value={formState.owner_user_id ?? ''}
                  onChange={(event) =>
                    setFormState((prev) => ({
                      ...prev,
                      owner_user_id: event.target.value === '' ? undefined : Number(event.target.value),
                    }))
                  }
                >
                  <MenuItem value="">Unassigned</MenuItem>
                  {(users ?? []).map((user) => (
                    <MenuItem key={user.user_id} value={user.user_id}>
                      {user.name || user.full_name || user.username}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Currency"
                value={formState.currency_code ?? 'AUD'}
                onChange={(event) => setFormState((prev) => ({ ...prev, currency_code: event.target.value }))}
              />
              <TextField
                label="Stage framework"
                value={formState.stage_framework ?? 'CUSTOM'}
                onChange={(event) => setFormState((prev) => ({ ...prev, stage_framework: event.target.value }))}
              />
            </Stack>
            <TextField
              label="Validity days"
              type="number"
              value={formState.validity_days ?? ''}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  validity_days: event.target.value === '' ? undefined : Number(event.target.value),
                }))
              }
            />
            <TextField
              label="PI notes"
              value={formState.pi_notes ?? ''}
              multiline
              minRows={2}
              onChange={(event) => setFormState((prev) => ({ ...prev, pi_notes: event.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateBid}>
            Create Bid
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
