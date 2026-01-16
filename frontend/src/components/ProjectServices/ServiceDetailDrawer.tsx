import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Drawer,
  Box,
  Typography,
  Button,
  IconButton,
  Stack,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import { Close as CloseIcon, Edit as EditIcon, Delete as DeleteIcon, Add as AddIcon } from '@mui/icons-material';
import { serviceReviewsApi, serviceItemsApi } from '@/api';
import type { ProjectService, ServiceReview, ServiceItem } from '@/api/services';

interface ServiceDetailDrawerProps {
  open: boolean;
  service: ProjectService | null;
  projectId: number;
  onClose: () => void;
  onEditService: (service: ProjectService) => void;
  onDeleteService: (serviceId: number) => void;
  onAddReview: (service: ProjectService, existingReviewCount: number) => void;
  onEditReview: (service: ProjectService, review: ServiceReview, existingReviewCount: number) => void;
  onDeleteReview: (service: ProjectService, reviewId: number) => void;
  onAddItem: (service: ProjectService) => void;
  onEditItem: (service: ProjectService, item: ServiceItem) => void;
  onDeleteItem: (service: ProjectService, itemId: number) => void;
  formatCurrency: (value?: number | null) => string;
  formatPercent: (value?: number | null) => string;
  getStatusColor: (
    status: string
  ) => 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
}

/**
 * Linear-style right drawer for service details.
 * Shows service info, finance, reviews, and items.
 */
export function ServiceDetailDrawer({
  open,
  service,
  projectId,
  onClose,
  onEditService,
  onDeleteService,
  onAddReview,
  onEditReview,
  onDeleteReview,
  onAddItem,
  onEditItem,
  onDeleteItem,
  formatCurrency,
  formatPercent,
  getStatusColor,
}: ServiceDetailDrawerProps) {
  const [tabValue, setTabValue] = useState(0);

  const {
    data: reviewsData = [],
    isLoading: reviewsLoading,
    isError: reviewsIsError,
    error: reviewsError,
  } = useQuery({
    queryKey: ['serviceReviews', projectId, service?.service_id],
    queryFn: async () => {
      if (!service) return [];
      const response = await serviceReviewsApi.getAll(projectId, service.service_id);
      return response.data;
    },
    enabled: open && !!service,
    staleTime: 60 * 1000,
  });

  const {
    data: itemsData = [],
    isLoading: itemsLoading,
    isError: itemsIsError,
    error: itemsError,
  } = useQuery({
    queryKey: ['serviceItems', projectId, service?.service_id],
    queryFn: async () => {
      if (!service) return [];
      const response = await serviceItemsApi.getAll(projectId, service.service_id);
      return response.data;
    },
    enabled: open && !!service,
    staleTime: 60 * 1000,
  });

  if (!service) return null;

  const billedAmount = service.billed_amount ?? service.claimed_to_date ?? 0;
  const progressValue = service.billing_progress_pct ?? service.progress_pct ?? 0;
  const reviewsErrorMessage = reviewsError instanceof Error ? reviewsError.message : 'Failed to load reviews';
  const itemsErrorMessage = itemsError instanceof Error ? itemsError.message : 'Failed to load items';

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 480, lg: 600 },
          boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.08)',
        },
      }}
      data-testid="service-detail-drawer"
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Drawer Header */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                {service.service_code}
              </Typography>
              <Chip label={service.status} color={getStatusColor(service.status)} size="small" />
            </Box>
            <Typography variant="h6" sx={{ mb: 0.5 }}>
              {service.service_name}
            </Typography>
            {service.phase && (
              <Typography variant="caption" color="text.secondary">
                Phase: {service.phase}
              </Typography>
            )}
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              ml: 1,
              color: 'text.secondary',
              '&:hover': { backgroundColor: 'action.hover' },
            }}
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Drawer Body (scrollable) */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {/* Finance Section */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
              Finance
            </Typography>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Agreed Fee
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 500 }}>
                  {formatCurrency(service.agreed_fee)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Billed
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 500 }}>
                  {formatCurrency(billedAmount)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Remaining
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 500 }}>
                  {formatCurrency(service.agreed_fee_remaining)}
                </Typography>
              </Box>
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
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Notes Section */}
          {service.notes && (
            <>
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Notes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {service.notes}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
            </>
          )}

          {/* Tabs: Reviews & Items */}
          <Box sx={{ mb: 2 }}>
            <Tabs
              value={tabValue}
              onChange={(_e, newValue) => setTabValue(newValue)}
              sx={{ borderBottom: '1px solid', borderColor: 'divider', mb: 2 }}
            >
              <Tab label="Reviews" data-testid="service-drawer-tab-reviews" />
              <Tab label="Items" data-testid="service-drawer-tab-items" />
            </Tabs>

            {/* Reviews Tab */}
            {tabValue === 0 && (
              <Box>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 1.5,
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Review Cycles
                  </Typography>
                  <Button
                    variant="text"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => onAddReview(service, reviewsData.length)}
                  >
                    Add
                  </Button>
                </Box>

                {reviewsLoading ? (
                  <Box display="flex" justifyContent="center" py={2}>
                    <CircularProgress size={24} />
                  </Box>
                ) : reviewsIsError ? (
                  <Alert severity="error">{reviewsErrorMessage}</Alert>
                ) : reviewsData.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No reviews yet.
                  </Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ py: 1, px: 0.5 }}>Cycle</TableCell>
                        <TableCell sx={{ py: 1, px: 0.5 }}>Planned</TableCell>
                        <TableCell sx={{ py: 1, px: 0.5 }}>Status</TableCell>
                        <TableCell sx={{ py: 1, px: 0.5 }} align="right">
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reviewsData.map((review) => (
                        <TableRow key={review.review_id} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                          <TableCell sx={{ py: 0.75, px: 0.5 }}>
                            <Typography variant="caption">#{review.cycle_no}</Typography>
                          </TableCell>
                          <TableCell sx={{ py: 0.75, px: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {review.planned_date
                                ? new Date(review.planned_date).toLocaleDateString()
                                : '—'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ py: 0.75, px: 0.5 }}>
                            <Chip
                              label={review.status}
                              color={
                                review.status === 'completed'
                                  ? 'success'
                                  : review.status === 'in_progress'
                                    ? 'primary'
                                    : 'default'
                              }
                              size="small"
                            />
                          </TableCell>
                          <TableCell sx={{ py: 0.75, px: 0.5 }} align="right">
                            <IconButton
                              size="small"
                              onClick={() => onEditReview(service, review, reviewsData.length)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => onDeleteReview(service, review.review_id)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </Box>
            )}

            {/* Items Tab */}
            {tabValue === 1 && (
              <Box>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 1.5,
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Items / Deliverables
                  </Typography>
                  <Button
                    variant="text"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => onAddItem(service)}
                  >
                    Add
                  </Button>
                </Box>

                {itemsLoading ? (
                  <Box display="flex" justifyContent="center" py={2}>
                    <CircularProgress size={24} />
                  </Box>
                ) : itemsIsError ? (
                  <Alert severity="error">{itemsErrorMessage}</Alert>
                ) : itemsData.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No items yet.
                  </Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ py: 1, px: 0.5 }}>Title</TableCell>
                        <TableCell sx={{ py: 1, px: 0.5 }}>Status</TableCell>
                        <TableCell sx={{ py: 1, px: 0.5 }} align="right">
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {itemsData.map((item) => (
                        <TableRow key={item.item_id} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                          <TableCell sx={{ py: 0.75, px: 0.5 }}>
                            <Typography variant="caption">{item.title}</Typography>
                          </TableCell>
                          <TableCell sx={{ py: 0.75, px: 0.5 }}>
                            <Chip
                              label={item.status}
                              color={
                                item.status === 'completed'
                                  ? 'success'
                                  : item.status === 'in_progress'
                                    ? 'primary'
                                    : 'default'
                              }
                              size="small"
                            />
                          </TableCell>
                          <TableCell sx={{ py: 0.75, px: 0.5 }} align="right">
                            <IconButton size="small" onClick={() => onEditItem(service, item)}>
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => onDeleteItem(service, item.item_id)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </Box>
            )}
          </Box>
        </Box>

        {/* Drawer Footer (actions) */}
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            gap: 1,
            justifyContent: 'flex-end',
          }}
        >
          <Button variant="text" onClick={onClose}>
            Close
          </Button>
          <Button
            variant="outlined"
            onClick={() => onEditService(service)}
          >
            Edit Service
          </Button>
          <Button
            variant="outlined"
            color="error"
            onClick={() => {
              if (window.confirm('Delete this service?')) {
                onDeleteService(service.service_id);
                onClose();
              }
            }}
          >
            Delete
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}
