/**
 * Service Detail Panel
 * 
 * Static panel content for service details (Finance, Notes, Reviews, Items).
 * Displayed in workspace right panel when a service is selected.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Stack,
  Divider,
  LinearProgress,
  Tabs,
  Tab,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
} from '@mui/material';
import { serviceReviewsApi, serviceItemsApi } from '@/api';
import type { ProjectService } from '@/api/services';
import { InlineField } from '@/components/ui/InlineField';

type ServiceDetailPanelProps = {
  projectId: number;
  service: ProjectService;
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

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const todayIso = () => new Date().toISOString().slice(0, 10);

export function ServiceDetailPanel({ projectId, service }: ServiceDetailPanelProps) {
  const [tabValue, setTabValue] = useState(0);
  const queryClient = useQueryClient();
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    cycle_no: '',
    planned_date: '',
    due_date: '',
  });

  const {
    data: reviewsData = [],
    isLoading: reviewsLoading,
    isError: reviewsIsError,
  } = useQuery({
    queryKey: ['serviceReviews', projectId, service.service_id],
    queryFn: async () => {
      const response = await serviceReviewsApi.getAll(projectId, service.service_id);
      return response.data;
    },
    staleTime: 60 * 1000,
  });

  const {
    data: itemsData = [],
    isLoading: itemsLoading,
    isError: itemsIsError,
  } = useQuery({
    queryKey: ['serviceItems', projectId, service.service_id],
    queryFn: async () => {
      const response = await serviceItemsApi.getAll(projectId, service.service_id);
      return response.data;
    },
    staleTime: 60 * 1000,
  });

  const createReviewMutation = useMutation({
    mutationFn: async () => {
      const cycleNo = Number(reviewForm.cycle_no);
      if (!cycleNo || !reviewForm.planned_date) {
        throw new Error('Cycle number and planned date are required.');
      }
      return serviceReviewsApi.create(projectId, service.service_id, {
        cycle_no: cycleNo,
        planned_date: reviewForm.planned_date,
        due_date: reviewForm.due_date || undefined,
        status: 'planned',
        origin: 'user_created',
        is_template_managed: false,
        sort_order: reviewsData.length + 1,
      });
    },
    onSuccess: () => {
      setReviewDialogOpen(false);
      setReviewForm({ cycle_no: '', planned_date: '', due_date: '' });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, service.service_id] });
    },
  });

  const handleOpenReviewDialog = () => {
    const nextCycle = reviewsData.length + 1;
    setReviewForm({
      cycle_no: String(nextCycle),
      planned_date: todayIso(),
      due_date: '',
    });
    setReviewDialogOpen(true);
  };

  const billedAmount = service.billed_amount ?? service.claimed_to_date ?? 0;
  const progressValue = service.billing_progress_pct ?? service.progress_pct ?? 0;

  return (
    <Stack spacing={2}>
      {/* Service Header */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            {service.service_code}
          </Typography>
          <Chip label={service.status} size="small" />
        </Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
          {service.service_name}
        </Typography>
        {service.phase && (
          <Typography variant="caption" color="text.secondary">
            Phase: {service.phase}
          </Typography>
        )}
      </Paper>

      {/* Finance Block */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Finance
        </Typography>
        <Stack spacing={1}>
          <InlineField label="Agreed Fee" value={formatCurrency(service.agreed_fee)} />
          <InlineField label="Billed" value={formatCurrency(billedAmount)} />
          <InlineField label="Remaining" value={formatCurrency(service.agreed_fee_remaining)} />
          <Box sx={{ mt: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Billing Progress
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                {formatPercent(progressValue)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressValue}
              sx={{
                height: 4,
                borderRadius: 2,
                backgroundColor: 'action.disabledBackground',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 'primary.main',
                  borderRadius: 2,
                },
              }}
            />
          </Box>
        </Stack>
      </Paper>

      {/* Notes Block (if present) */}
      {service.notes && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Notes
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {service.notes}
          </Typography>
        </Paper>
      )}

      {/* Reviews & Items Tabs */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(_e, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: '1px solid', borderColor: 'divider', mb: 2 }}
        >
          <Tab label={`Reviews (${reviewsData.length})`} />
          <Tab label={`Items (${itemsData.length})`} />
        </Tabs>

        {/* Reviews Tab */}
        {tabValue === 0 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
              <Button
                size="small"
                variant="outlined"
                onClick={handleOpenReviewDialog}
                data-testid="service-add-manual-review-button"
              >
                Add Review
              </Button>
            </Box>
            {reviewsLoading ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress size={24} />
              </Box>
            ) : reviewsIsError ? (
              <Alert severity="error">Failed to load reviews</Alert>
            ) : reviewsData.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No reviews yet.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {reviewsData.map((review) => (
                  <Box
                    key={review.review_id}
                    sx={{
                      p: 1,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      '&:hover': { backgroundColor: 'action.hover' },
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" fontWeight={600}>
                        Cycle #{review.cycle_no}
                      </Typography>
                      <Chip label={review.status} size="small" />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Planned: {formatDate(review.planned_date)}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
        )}

        {/* Items Tab */}
        {tabValue === 1 && (
          <Box>
            {itemsLoading ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress size={24} />
              </Box>
            ) : itemsIsError ? (
              <Alert severity="error">Failed to load items</Alert>
            ) : itemsData.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No items yet.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {itemsData.map((item) => (
                  <Box
                    key={item.item_id}
                    sx={{
                      p: 1,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      '&:hover': { backgroundColor: 'action.hover' },
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" fontWeight={600}>
                        {item.item_name || 'Untitled'}
                      </Typography>
                      <Chip label={item.status || 'Unknown'} size="small" />
                    </Box>
                    {item.item_type && (
                      <Typography variant="caption" color="text.secondary">
                        Type: {item.item_type}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
        )}
      </Paper>

      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Add Manual Review</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {createReviewMutation.isError && (
            <Alert severity="error">
              {createReviewMutation.error instanceof Error
                ? createReviewMutation.error.message
                : 'Failed to create review.'}
            </Alert>
          )}
          <TextField
            label="Cycle Number"
            type="number"
            value={reviewForm.cycle_no}
            onChange={(event) => setReviewForm((prev) => ({ ...prev, cycle_no: event.target.value }))}
            required
          />
          <TextField
            label="Planned Date"
            type="date"
            value={reviewForm.planned_date}
            onChange={(event) => setReviewForm((prev) => ({ ...prev, planned_date: event.target.value }))}
            InputLabelProps={{ shrink: true }}
            required
          />
          <TextField
            label="Due Date"
            type="date"
            value={reviewForm.due_date}
            onChange={(event) => setReviewForm((prev) => ({ ...prev, due_date: event.target.value }))}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createReviewMutation.mutate()}
            disabled={createReviewMutation.isPending}
          >
            {createReviewMutation.isPending ? 'Adding...' : 'Add Review'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
