/**
 * Services Tab
 * 
 * Displays project services list using LinearList (consistent with Deliverables).
 * Row selection updates right panel via useWorkspaceSelection.
 */

import { useMemo, useState } from 'react';
import {
  Box,
  Button,
  ButtonGroup,
  Typography,
  Alert,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Stack,
  IconButton,
  Menu,
} from '@mui/material';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon, ArrowDropDown as ArrowDropDownIcon } from '@mui/icons-material';
import { projectServicesApi } from '@/api';
import type { ProjectServicesListResponse } from '@/api/services';
import type { ProjectService } from '@/types/api';
import type { Project } from '@/types/api';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import { LinearListContainer, LinearListHeaderRow, LinearListRow, LinearListCell } from '@/components/ui/LinearList';

type OutletContext = {
  projectId: number;
  project: Project | null;
  selection: Selection | null;
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const formatPercent = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return `${Math.round(Number(value))}%`;
};

const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
  const normalized = String(status || '').toLowerCase();
  if (normalized.includes('complete') || normalized.includes('done')) return 'success';
  if (normalized.includes('progress') || normalized.includes('active')) return 'primary';
  if (normalized.includes('hold') || normalized.includes('pause')) return 'warning';
  if (normalized.includes('cancel') || normalized.includes('stop')) return 'error';
  return 'default';
};

export default function ServicesTab() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { projectId, selection } = useOutletContext<OutletContext>();
  const [saveError, setSaveError] = useState<string | null>(null);
  const [templateFeedback, setTemplateFeedback] = useState<{
    message: string;
    severity: 'success' | 'error';
  } | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState<ProjectService | null>(null);
  const [addMenuAnchorEl, setAddMenuAnchorEl] = useState<null | HTMLElement>(null);

  const { data: servicesPayload, isLoading, isError } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', projectId],
    queryFn: async () => {
      const result = await projectServicesApi.getAll(projectId);
      console.log('[ServicesTab] Fetched services:', {
        projectId,
        totalServices: Array.isArray(result) ? result.length : result?.items?.length || result?.services?.length || 0,
        rawResult: result
      });
      return result;
    },
    enabled: Number.isFinite(projectId),
    staleTime: 60_000,
    retry: 1,
  });

  const deleteServiceMutation = useMutation({
    mutationFn: (serviceId: number) => projectServicesApi.delete(projectId, serviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      setTemplateFeedback({
        message: `Service "${serviceToDelete?.service_code}" deleted successfully.`,
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setServiceToDelete(null);
      // Clear selection if deleted service was selected
      if (selectedService?.service_id === serviceToDelete?.service_id) {
        const url = new URL(window.location.href);
        url.searchParams.delete('sel');
        window.history.replaceState(null, '', url.toString());
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    },
    onError: (err: any) => {
      const errorMsg = err?.response?.data?.error || 'Failed to delete service';
      setTemplateFeedback({
        message: `Error: ${errorMsg}`,
        severity: 'error',
      });
      setDeleteDialogOpen(false);
      setServiceToDelete(null);
    },
  });

  const services = useMemo<ProjectService[]>(() => {
    if (!servicesPayload) {
      return [];
    }
    if (Array.isArray(servicesPayload)) {
      console.log('[ServicesTab] Services array length:', servicesPayload.length);
      return servicesPayload;
    }
    const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
    const serviceList = Array.isArray(items) ? items : [];
    console.log('[ServicesTab] Extracted services:', serviceList.length, serviceList);
    return serviceList;
  }, [servicesPayload]);

  const selectedService = useMemo(() => {
    console.log('[ServicesTab] Computing selectedService:', {
      selectionType: selection?.type,
      selectionId: selection?.id,
      servicesCount: services.length,
      serviceIds: services.map(s => s.service_id),
      fullSelection: JSON.stringify(selection)
    });
    if (selection?.type !== 'service') {
      console.log('[ServicesTab] No service selected. selection.type =', selection?.type, '(expected "service")');
      return null;
    }
    const found = services.find((s) => s.service_id === selection.id) ?? null;
    console.log('[ServicesTab] Selected service:', found ? `Found: ${found.service_code}` : 'Not found');
    return found;
  }, [services, selection]);

  const noWrap = { whiteSpace: 'nowrap' } as const;
  const columnWidths = {
    service: 260,
    phase: 120,
    status: 140,
    deliverables: 220,
    agreed: 120,
    billed: 120,
    remaining: 120,
    progress: 100,
  } as const;
  const serviceColumns = [
    { id: 'service', label: 'Service', minWidth: columnWidths.service, flex: true },
    { id: 'phase', label: 'Phase', minWidth: columnWidths.phase },
    { id: 'status', label: 'Status', minWidth: columnWidths.status },
    { id: 'deliverables', label: 'Deliverables', minWidth: columnWidths.deliverables },
    { id: 'agreed', label: 'Agreed', minWidth: columnWidths.agreed },
    { id: 'billed', label: 'Billed', minWidth: columnWidths.billed },
    { id: 'remaining', label: 'Remaining', minWidth: columnWidths.remaining },
    { id: 'progress', label: 'Progress', minWidth: columnWidths.progress },
  ];
  const servicesGridTemplate = serviceColumns
    .map((column) => (column.flex ? `minmax(${column.minWidth}px, 1fr)` : `${column.minWidth}px`))
    .join(' ');
  const servicesMinWidth = serviceColumns.reduce((sum, column) => sum + column.minWidth, 0);


  const handleDeleteClick = () => {
    if (selectedService) {
      setServiceToDelete(selectedService);
      setDeleteDialogOpen(true);
    }
  };

  const handleDeleteConfirm = () => {
    if (serviceToDelete) {
      deleteServiceMutation.mutate(serviceToDelete.service_id);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setServiceToDelete(null);
  };

  const handleOpenAddMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAddMenuAnchorEl(event.currentTarget);
  };

  const handleCloseAddMenu = () => {
    setAddMenuAnchorEl(null);
  };

  const handleAddBlankService = () => {
    handleCloseAddMenu();
    navigate(`/projects/${projectId}/workspace/services/new`);
  };

  const handleAddFromTemplate = () => {
    handleCloseAddMenu();
    navigate(`/projects/${projectId}/workspace/services/new?mode=template`);
  };

  if (!Number.isFinite(projectId)) {
    return (
      <Typography color="text.secondary">
        Select a project to view services.
      </Typography>
    );
  }

  return (
    <Box data-testid="workspace-services-tab">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Services</Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {selectedService && (
            <>
              <IconButton
                color="primary"
                onClick={() => navigate(`/projects/${projectId}/workspace/services/${selectedService.service_id}`)}
                data-testid="workspace-edit-service-button"
                title={`Edit service ${selectedService.service_code}`}
              >
                <EditIcon />
              </IconButton>
              <IconButton
                color="error"
                onClick={handleDeleteClick}
                data-testid="workspace-delete-service-button"
                title={`Delete service ${selectedService.service_code}`}
              >
                <DeleteIcon />
              </IconButton>
            </>
          )}
          <ButtonGroup variant="contained" aria-label="add-service-options">
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddBlankService}
              data-testid="workspace-add-service-button"
            >
              Add Service
            </Button>
            <Button
              size="small"
              onClick={handleOpenAddMenu}
              aria-controls={addMenuAnchorEl ? 'add-service-menu' : undefined}
              aria-expanded={addMenuAnchorEl ? 'true' : undefined}
              aria-haspopup="menu"
              data-testid="workspace-add-service-menu-button"
            >
              <ArrowDropDownIcon />
            </Button>
          </ButtonGroup>
        </Box>
      </Box>

      {saveError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {saveError}
        </Alert>
      )}

      {templateFeedback && (
        <Alert
          severity={templateFeedback.severity}
          sx={{ mb: 2 }}
          onClose={() => setTemplateFeedback(null)}
        >
          {templateFeedback.message}
        </Alert>
      )}

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load services.
        </Alert>
      )}

      {isLoading ? (
        <Typography color="text.secondary">Loading services...</Typography>
      ) : services.length ? (
        <Box sx={{ width: '100%', overflowX: 'auto' }}>
          <LinearListContainer sx={{ minWidth: servicesMinWidth }}>
            <LinearListHeaderRow
              columns={serviceColumns.map((column) => column.label)}
              sx={{ gridTemplateColumns: servicesGridTemplate }}
            />
            {services.map((service) => {
              const billedAmount = service.billed_amount ?? service.claimed_to_date ?? 0;
              const progressValue = service.billing_progress_pct ?? service.progress_pct ?? 0;
              const isSelected = selection?.type === 'service' && selection?.id === service.service_id;
              const reviewCount = service.review_count_total ?? 0;
              const itemCount = service.item_count_total ?? 0;
              const deliverableLabel = `Reviews: ${reviewCount} / Items: ${itemCount}`;

              return (
                <LinearListRow
                  key={service.service_id}
                  testId={`workspace-service-row-${service.service_id}`}
                  columns={serviceColumns.length}
                  hoverable
                  onClick={() => {
                    console.log('[ServicesTab] Row clicked:', {
                      serviceId: service.service_id,
                      serviceCode: service.service_code,
                      currentSelection: selection
                    });
                    // Use React Router navigate to update URL with selection
                    navigate(`/projects/${projectId}/workspace/services?sel=service:${service.service_id}`, {
                      replace: true
                    });
                    console.log('[ServicesTab] Navigated with selection');
                  }}
                  sx={{
                    gridTemplateColumns: servicesGridTemplate,
                    backgroundColor: isSelected ? 'action.selected' : 'transparent',
                  }}
                >
                  {/* Service code + name */}
                  <Box sx={{ minWidth: columnWidths.service }}>
                    <Typography variant="body2" fontWeight={500} sx={noWrap}>
                      {service.service_code}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={noWrap}>
                      {service.service_name}
                    </Typography>
                  </Box>

                  {/* Phase */}
                  <LinearListCell variant="secondary" sx={noWrap}>
                    {service.phase || '???'}
                  </LinearListCell>

                  {/* Status */}
                  <Box sx={noWrap}>
                    <Typography
                      variant="caption"
                      sx={{
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        bgcolor: `${getStatusColor(service.status)}.light`,
                        color: `${getStatusColor(service.status)}.dark`,
                        fontWeight: 500,
                      }}
                    >
                      {service.status}
                    </Typography>
                  </Box>

                  {/* Deliverables (Reviews + Items) */}
                  <LinearListCell variant="secondary" sx={noWrap}>
                    <Typography variant="body2" title={`Reviews: ${reviewCount}, Items: ${itemCount}`} sx={noWrap}>
                      {deliverableLabel}
                    </Typography>
                  </LinearListCell>

                  {/* Agreed Fee */}
                  <LinearListCell variant="number" sx={noWrap}>
                    {formatCurrency(service.agreed_fee)}
                  </LinearListCell>

                  {/* Billed */}
                  <LinearListCell variant="number" sx={noWrap}>
                    {formatCurrency(billedAmount)}
                  </LinearListCell>

                  {/* Remaining */}
                  <LinearListCell variant="number" sx={noWrap}>
                    {formatCurrency(service.agreed_fee_remaining)}
                  </LinearListCell>

                  {/* Progress */}
                  <LinearListCell variant="number" sx={noWrap}>
                    {formatPercent(progressValue)}
                  </LinearListCell>
                </LinearListRow>
              );
            })}
          </LinearListContainer>
        </Box>
      ) : (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No services for this project yet.
          </Typography>
        </Paper>
      )}

      <Menu
        id="add-service-menu"
        anchorEl={addMenuAnchorEl}
        open={Boolean(addMenuAnchorEl)}
        onClose={handleCloseAddMenu}
      >
        <MenuItem onClick={handleAddBlankService}>Blank service</MenuItem>
        <MenuItem onClick={handleAddFromTemplate}>From template</MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Service</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete service <strong>{serviceToDelete?.service_code}</strong> ({serviceToDelete?.service_name})?
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            This action cannot be undone. All associated reviews, items, and billing data will also be deleted.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteConfirm}
            disabled={deleteServiceMutation.isPending}
          >
            {deleteServiceMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
