/**
 * Deliverables Tab
 * 
 * Displays project reviews (deliverables).
 * Reuses existing deliverables UI from ProjectWorkspacePageV2.
 */

import { useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Chip,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { invoiceBatchesApi, serviceItemsApi, serviceReviewsApi } from '@/api';
import type { InvoiceBatch, Project, ProjectReviewItem, ProjectReviewsResponse, ServiceItem, ServiceReview } from '@/types/api';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import { toApiReviewStatus } from '@/utils/reviewStatus';
import { EditableCell, ToggleCell } from '@/components/projects/EditableCells';
import { LinearListContainer, LinearListHeaderRow, LinearListRow, LinearListCell } from '@/components/ui/LinearList';

type OutletContext = {
  projectId: number;
  project: Project | null;
};

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const toMonthString = (date: Date) => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `${date.getFullYear()}-${month}`;
};

const formatInvoiceMonth = (value?: string | null) => {
  if (!value) return null;
  if (/^\d{4}-\d{2}$/.test(value)) {
    return value;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return toMonthString(parsed);
};

export default function DeliverablesTab() {
  const { projectId } = useOutletContext<OutletContext>();
  const queryClient = useQueryClient();
  const [reviewUpdateError, setReviewUpdateError] = useState<string | null>(null);
  const [deliverableFilters, setDeliverableFilters] = useState({
    dueThisMonth: false,
    unbatched: false,
    readyToInvoice: false,
  });

  const reviewsFilters = useMemo(
    () => ({
      sort_by: 'planned_date' as const,
      sort_dir: 'asc' as const,
    }),
    [],
  );

  const {
    data: projectReviews,
    isLoading: projectReviewsLoading,
    error: projectReviewsError,
  } = useProjectReviews(projectId, reviewsFilters);

  const reviewItems = useMemo<ProjectReviewItem[]>(
    () => projectReviews?.items ?? [],
    [projectReviews],
  );

  const { data: projectItems, isLoading: projectItemsLoading, error: projectItemsError } = useQuery<{
    items: ServiceItem[];
    total: number;
  }>({
    queryKey: ['projectItems', projectId],
    queryFn: () => serviceItemsApi.getProjectItems(projectId),
    enabled: Number.isFinite(projectId),
  });

  const serviceItems = useMemo<ServiceItem[]>(
    () => projectItems?.items ?? [],
    [projectItems],
  );

  const { data: invoiceBatches = [] } = useQuery<InvoiceBatch[]>({
    queryKey: ['invoiceBatches', projectId],
    queryFn: () => invoiceBatchesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });

  const createInvoiceBatch = useMutation({
    mutationFn: (payload: Parameters<typeof invoiceBatchesApi.create>[0]) => invoiceBatchesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoiceBatches', projectId] });
    },
  });

  const filteredReviewItems = useMemo(() => {
    if (!deliverableFilters.dueThisMonth && !deliverableFilters.unbatched && !deliverableFilters.readyToInvoice) {
      return reviewItems;
    }
    const currentMonth = toMonthString(new Date());
    return reviewItems.filter((review) => {
      const invoiceMonth = formatInvoiceMonth(
        review.invoice_month_final
          || review.invoice_month_override
          || review.invoice_month_auto
          || review.due_date,
      ) ?? '';
      const matchesDueThisMonth = !deliverableFilters.dueThisMonth || invoiceMonth === currentMonth;
      const matchesUnbatched = !deliverableFilters.unbatched || review.invoice_batch_id == null;
      const matchesReady =
        !deliverableFilters.readyToInvoice
        || ((review.status || '').toLowerCase() === 'completed' && !review.is_billed);
      return matchesDueThisMonth && matchesUnbatched && matchesReady;
    });
  }, [deliverableFilters, reviewItems]);

  const filteredServiceItems = useMemo(() => {
    if (!deliverableFilters.dueThisMonth && !deliverableFilters.readyToInvoice) {
      return serviceItems;
    }
    const currentMonth = toMonthString(new Date());
    return serviceItems.filter((item) => {
      const dueMonth = formatInvoiceMonth(item.due_date) ?? '';
      const matchesDueThisMonth = !deliverableFilters.dueThisMonth || dueMonth === currentMonth;
      const matchesReady =
        !deliverableFilters.readyToInvoice
        || ((item.status || '').toLowerCase() === 'completed' && !item.is_billed);
      return matchesDueThisMonth && matchesReady;
    });
  }, [deliverableFilters, serviceItems]);

  const updateDeliverableField = useMutation<
    ProjectReviewItem,
    Error,
    { review: ProjectReviewItem; fieldName: string; value: unknown },
    { previousProjectReviews: Array<[unknown, ProjectReviewsResponse | undefined]> }
  >({
    mutationFn: async ({ review, fieldName, value }) => {
      const payload = { [fieldName]: value };
      const { default: projectReviewsApi } = await import('@/api/projectReviews');
      return projectReviewsApi.patchProjectReview(projectId, review.review_id, review.service_id, payload as any);
    },
    onMutate: async ({ review, fieldName, value }) => {
      setReviewUpdateError(null);
      await queryClient.cancelQueries({ queryKey: ['projectReviews', projectId] });

      const previousProjectReviews = queryClient.getQueriesData<ProjectReviewsResponse>({
        queryKey: ['projectReviews', projectId],
      });

      queryClient.setQueriesData<ProjectReviewsResponse>(
        { queryKey: ['projectReviews', projectId] },
        (existing) => {
          if (!existing) return existing;
          return {
            ...existing,
            items: existing.items.map((item) =>
              item.review_id === review.review_id ? { ...item, [fieldName]: value } : item,
            ),
          };
        },
      );

      return { previousProjectReviews };
    },
    onError: (error, _variables, context) => {
      setReviewUpdateError(error.message || 'Failed to update review.');
      if (context?.previousProjectReviews) {
        context.previousProjectReviews.forEach(([key, data]) => {
          queryClient.setQueryData(key as unknown[], data);
        });
      }
    },
    onSettled: (_data, _error, { review }) => {
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, review.service_id] });
    },
  });

  return (
    <Box data-testid="workspace-deliverables-tab">
      {reviewUpdateError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {reviewUpdateError}
        </Alert>
      )}
      {projectReviewsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load project reviews.
        </Alert>
      )}
      {projectReviewsLoading ? (
        <Typography color="text.secondary">Loading deliverables...</Typography>
      ) : (reviewItems.length || serviceItems.length) ? (
        <>
          <Stack direction="row" spacing={1} sx={{ mb: 2 }} data-testid="deliverables-filters">
            <Chip
              label="Due this month"
              color={deliverableFilters.dueThisMonth ? 'primary' : 'default'}
              variant={deliverableFilters.dueThisMonth ? 'filled' : 'outlined'}
              onClick={() => setDeliverableFilters((prev) => ({ ...prev, dueThisMonth: !prev.dueThisMonth }))}
              size="small"
            />
            <Chip
              label="Unbatched"
              color={deliverableFilters.unbatched ? 'primary' : 'default'}
              variant={deliverableFilters.unbatched ? 'filled' : 'outlined'}
              onClick={() => setDeliverableFilters((prev) => ({ ...prev, unbatched: !prev.unbatched }))}
              size="small"
            />
            <Chip
              label="Ready to invoice"
              color={deliverableFilters.readyToInvoice ? 'primary' : 'default'}
              variant={deliverableFilters.readyToInvoice ? 'filled' : 'outlined'}
              onClick={() => setDeliverableFilters((prev) => ({ ...prev, readyToInvoice: !prev.readyToInvoice }))}
              size="small"
            />
          </Stack>
          <LinearListContainer>
            <LinearListHeaderRow columns={['Service', 'Planned', 'Due', 'Invoice Month', 'Batch', 'Invoice #', 'Billed']} />
            {filteredReviewItems.map((review) => {
              const serviceLabel = [review.service_code, review.service_name]
                .filter(Boolean)
                .join(' | ');
              const metadataLabel = [review.phase, review.cycle_no ? `Cycle ${review.cycle_no}` : null]
                .filter(Boolean)
                .join(' | ');
              const invoiceMonth = review.invoice_month_final
                || review.invoice_month_override
                || review.invoice_month_auto
                || formatInvoiceMonth(review.due_date);
              const plannedMonth = formatInvoiceMonth(review.planned_date);
              const dueMonth = formatInvoiceMonth(review.due_date);
              const isSlipped = plannedMonth && dueMonth && plannedMonth !== dueMonth;
              const batchOptions = invoiceMonth
                ? invoiceBatches.filter((batch) =>
                    batch.invoice_month === invoiceMonth
                    && (batch.service_id == null || batch.service_id === review.service_id),
                  )
                : [];
              const isBatchSaving = updateDeliverableField.isPending
                && updateDeliverableField.variables?.review.review_id === review.review_id
                && updateDeliverableField.variables?.fieldName === 'invoice_batch_id';

              return (
                <LinearListRow
                  key={review.review_id}
                  testId={`deliverable-row-${review.review_id}`}
                  columns={7}
                  hoverable
                >
                  {/* Service + metadata */}
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {serviceLabel || 'Service'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {metadataLabel}
                    </Typography>
                  </Box>

                  {/* Planned Date (read-only) */}
                  <LinearListCell variant="secondary">
                    {formatDate(review.planned_date)}
                  </LinearListCell>

                  {/* Due Date - Editable */}
                  <Box>
                    <EditableCell
                      value={review.due_date}
                      type="date"
                      testId={`cell-due-${review.review_id}`}
                      isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'due_date'}
                      onSave={async (newValue) => {
                        await updateDeliverableField.mutateAsync({
                          review,
                          fieldName: 'due_date',
                          value: newValue,
                        });
                      }}
                    />
                    {isSlipped && (
                      <Typography variant="caption" color="warning.main" sx={{ ml: 1 }}>
                        Slipped
                      </Typography>
                    )}
                  </Box>

                  {/* Invoice Month - Editable override */}
                  <EditableCell
                    value={invoiceMonth}
                    type="month"
                    testId={`cell-invoice-month-${review.review_id}`}
                    isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_month_override'}
                    onSave={async (newValue) => {
                      await updateDeliverableField.mutateAsync({
                        review,
                        fieldName: 'invoice_month_override',
                        value: newValue,
                      });
                    }}
                  />

                  {/* Invoice Batch - Select */}
                  <Box sx={{ minWidth: 160 }}>
                    <TextField
                      select
                      size="small"
                      fullWidth
                      value={review.invoice_batch_id ? String(review.invoice_batch_id) : ''}
                      disabled={!invoiceMonth || isBatchSaving || createInvoiceBatch.isPending}
                      SelectProps={{
                        displayEmpty: true,
                        renderValue: (selected) => {
                          if (!invoiceMonth) {
                            return 'Set invoice month';
                          }
                          if (!selected) {
                            return 'Unbatched';
                          }
                          const match = batchOptions.find((batch) => String(batch.invoice_batch_id) === selected);
                          return match?.title || `Batch #${selected}`;
                        },
                        inputProps: {
                          'data-testid': `cell-invoice-batch-${review.review_id}`,
                        },
                      }}
                      onChange={async (event) => {
                        const value = event.target.value;
                        if (value === '__create__' && invoiceMonth) {
                          const title = window.prompt('Batch title (optional)') || null;
                          const result = await createInvoiceBatch.mutateAsync({
                            project_id: projectId,
                            service_id: review.service_id,
                            invoice_month: invoiceMonth,
                            title,
                          });
                          if (result?.invoice_batch_id) {
                            await updateDeliverableField.mutateAsync({
                              review,
                              fieldName: 'invoice_batch_id',
                              value: result.invoice_batch_id,
                            });
                          }
                          return;
                        }
                        await updateDeliverableField.mutateAsync({
                          review,
                          fieldName: 'invoice_batch_id',
                          value: value ? Number(value) : null,
                        });
                      }}
                    >
                      <MenuItem value="">Unbatched</MenuItem>
                      {batchOptions.map((batch) => (
                        <MenuItem key={batch.invoice_batch_id} value={String(batch.invoice_batch_id)}>
                          {batch.title || `Batch #${batch.invoice_batch_id}`}
                        </MenuItem>
                      ))}
                      <MenuItem value="__create__">Create new batch</MenuItem>
                    </TextField>
                  </Box>

                  {/* Invoice Number - Editable */}
                  <EditableCell
                    value={review.invoice_reference}
                    type="text"
                    testId={`cell-invoice-number-${review.review_id}`}
                    isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_reference'}
                    onSave={async (newValue) => {
                      await updateDeliverableField.mutateAsync({
                        review,
                        fieldName: 'invoice_reference',
                        value: newValue,
                      });
                    }}
                  />

                  {/* Billing Status - Toggleable */}
                  <ToggleCell
                    value={review.is_billed}
                    testId={`cell-billing-status-${review.review_id}`}
                    isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'is_billed'}
                    onSave={async (newValue) => {
                      await updateDeliverableField.mutateAsync({
                        review,
                        fieldName: 'is_billed',
                        value: newValue,
                      });
                    }}
                  />
                </LinearListRow>
              );
            })}
          </LinearListContainer>
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Items
            </Typography>
            {projectItemsError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Failed to load service items.
              </Alert>
            )}
            {projectItemsLoading ? (
              <Typography color="text.secondary">Loading items...</Typography>
            ) : filteredServiceItems.length ? (
              <LinearListContainer>
                <LinearListHeaderRow columns={['Service', 'Planned', 'Due', 'Item', 'Type', 'Status', 'Invoice #', 'Billed']} />
                {filteredServiceItems.map((item) => {
                  const serviceLabel = [item.service_code, item.service_name]
                    .filter(Boolean)
                    .join(' | ');
                  const metadataLabel = item.phase || '';
                  return (
                    <LinearListRow
                      key={`item-${item.item_id}`}
                      testId={`deliverable-item-row-${item.item_id}`}
                      columns={8}
                      hoverable
                    >
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {serviceLabel || `Service ${item.service_id}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {metadataLabel}
                        </Typography>
                      </Box>
                      <LinearListCell variant="secondary">
                        {formatDate(item.planned_date)}
                      </LinearListCell>
                      <LinearListCell variant="secondary">
                        {formatDate(item.due_date)}
                      </LinearListCell>
                      <Typography variant="body2">
                        {item.title}
                      </Typography>
                      <Typography variant="body2">
                        {item.item_type || '--'}
                      </Typography>
                      <Typography variant="body2">
                        {item.status || '--'}
                      </Typography>
                      <Typography variant="body2">
                        {item.invoice_reference || '--'}
                      </Typography>
                      <Typography variant="body2">
                        {item.is_billed ? 'Billed' : 'Not billed'}
                      </Typography>
                    </LinearListRow>
                  );
                })}
              </LinearListContainer>
            ) : (
              <Typography color="text.secondary">No service items found for this project.</Typography>
            )}
          </Box>
        </>
      ) : (
        <Typography color="text.secondary">No deliverables found for this project.</Typography>
      )}
    </Box>
  );
}
