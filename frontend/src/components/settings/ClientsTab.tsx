import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { clientsApi } from '../../api/clients';
import { useNamingConventionOptions } from '../../hooks/useNamingConventions';
import type { Client } from '../../types/api';

const ClientsTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [formData, setFormData] = useState({
    client_name: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    city: '',
    state: '',
    postcode: '',
    country: 'Australia',
    naming_convention: '',
  });
  const [error, setError] = useState<string | null>(null);

  const { options: namingConventionOptions } = useNamingConventionOptions();

  const {
    data: clients,
    isLoading,
  } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: clientsApi.getAll,
  });

  const resetForm = () => {
    setFormData({
      client_name: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      address: '',
      city: '',
      state: '',
      postcode: '',
      country: 'Australia',
      naming_convention: '',
    });
    setError(null);
  };

  const openDialog = (client?: Client) => {
    if (client) {
      setEditingClient(client);
      setFormData({
        client_name: client.client_name ?? client.name ?? '',
        contact_name: client.contact_name ?? '',
        contact_email: client.contact_email ?? '',
        contact_phone: client.contact_phone ?? '',
        address: client.address ?? '',
        city: client.city ?? '',
        state: client.state ?? '',
        postcode: client.postcode ?? '',
        country: client.country ?? 'Australia',
        naming_convention: client.naming_convention ?? '',
      });
    } else {
      setEditingClient(null);
      resetForm();
    }
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingClient(null);
    resetForm();
  };

  const createMutation = useMutation<Client, Error, Partial<Client>>({
    mutationFn: clientsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      closeDialog();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to create client');
    },
  });

  const updateMutation = useMutation<Client, Error, { id: number; data: Partial<Client> }>({
    mutationFn: ({ id, data }: { id: number; data: Partial<Client> }) =>
      clientsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      closeDialog();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to update client');
    },
  });

  const deleteMutation = useMutation<void, Error, number>({
    mutationFn: (id: number) => clientsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to delete client');
    },
  });

  const handleSubmit = () => {
    if (!formData.client_name.trim()) {
      setError('Client name is required');
      return;
    }

    const payload = {
      ...formData,
      naming_convention: formData.naming_convention || null,
    };

    if (editingClient) {
      const id = editingClient.client_id ?? editingClient.id;
      if (!id) {
        setError('Invalid client identifier');
        return;
      }
      updateMutation.mutate({ id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleDelete = (client: Client) => {
    const id = client.client_id ?? client.id;
    if (!id) {
      setError('Invalid client identifier');
      return;
    }
    if (window.confirm(`Delete client "${client.client_name ?? client.name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ px: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Clients</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => openDialog()}>
          Add Client
        </Button>
      </Stack>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Address</TableCell>
              <TableCell>Naming Convention</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients?.map((client) => (
              <TableRow key={client.client_id ?? client.id}>
                <TableCell>{client.client_name ?? client.name}</TableCell>
                <TableCell>{client.contact_name || 'N/A'}</TableCell>
                <TableCell>{client.contact_email || 'N/A'}</TableCell>
                <TableCell>{client.contact_phone || 'N/A'}</TableCell>
                <TableCell>
                  {client.address ? (
                    <Stack spacing={0.5}>
                      <Typography variant="body2">{client.address}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {[client.city, client.state, client.postcode]
                          .filter(Boolean)
                          .join(', ')}
                      </Typography>
                    </Stack>
                  ) : (
                    'N/A'
                  )}
                </TableCell>
                <TableCell>
                  {client.naming_convention ? (
                    <Chip label={client.naming_convention} size="small" color="primary" />
                  ) : (
                    <Chip label="None" size="small" variant="outlined" />
                  )}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => openDialog(client)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(client)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingClient ? 'Edit Client' : 'Add Client'}</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <Stack spacing={2} mt={1}>
            <TextField
              label="Client Name"
              value={formData.client_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, client_name: e.target.value }))}
              required
              fullWidth
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Contact Name"
                value={formData.contact_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, contact_name: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Contact Email"
                type="email"
                value={formData.contact_email}
                onChange={(e) => setFormData((prev) => ({ ...prev, contact_email: e.target.value }))}
                fullWidth
              />
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Contact Phone"
                value={formData.contact_phone}
                onChange={(e) => setFormData((prev) => ({ ...prev, contact_phone: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Naming Convention"
                select
                value={formData.naming_convention}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, naming_convention: e.target.value }))
                }
                fullWidth
              >
                <MenuItem value="">None</MenuItem>
                {namingConventionOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
            <TextField
              label="Address"
              value={formData.address}
              onChange={(e) => setFormData((prev) => ({ ...prev, address: e.target.value }))}
              fullWidth
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="City"
                value={formData.city}
                onChange={(e) => setFormData((prev) => ({ ...prev, city: e.target.value }))}
                fullWidth
              />
              <TextField
                label="State"
                value={formData.state}
                onChange={(e) => setFormData((prev) => ({ ...prev, state: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Postcode"
                value={formData.postcode}
                onChange={(e) => setFormData((prev) => ({ ...prev, postcode: e.target.value }))}
                fullWidth
              />
            </Stack>
            <TextField
              label="Country"
              value={formData.country}
              onChange={(e) => setFormData((prev) => ({ ...prev, country: e.target.value }))}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ClientsTab;
