/**
 * Deliverables Tab
 * 
 * Displays project reviews (deliverables).
 * Reuses existing deliverables UI from ProjectWorkspacePageV2.
 */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { invoiceBatchesApi, projectServicesApi, serviceItemsApi } from '@/api';
import { projectReviewsApi } from '@/api/projectReviews';
import type { InvoiceBatch, Project, ProjectReviewItem, ProjectReviewsResponse, ServiceItem } from '@/types/api';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import { EditableCell, ToggleCell } from '@/components/projects/EditableCells';
import { LinearListContainer, LinearListHeaderRow, LinearListRow, LinearListCell } from '@/components/ui/LinearList';

type OutletContext = {
  projectId: number;
  project: Project | null;
  selection: Selection | null;
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

const ITEM_STATUS_OPTIONS = ['planned', 'in_progress', 'completed', 'overdue', 'cancelled'] as const;
const ITEM_PRIORITY_OPTIONS = ['low', 'medium', 'high', 'critical'] as const;

export default function DeliverablesTab() {
  const navigate = useNavigate();
  const { projectId, selection } = useOutletContext<OutletContext>();
  const queryClient = useQueryClient();
  const [reviewUpdateError, setReviewUpdateError] = useState<string | null>(null);
  const [itemUpdateError, setItemUpdateError] = useState<string | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(
    selection?.type === 'service' && typeof selection.id === 'number' ? selection.id : null,
  );
  const [itemDrafts, setItemDrafts] = useState<Array<ServiceItem & { isDraft: boolean }>>([]);
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

  const { data: servicesPayload } = useQuery({
    queryKey: ['projectServices', projectId],
    queryFn: () => projectServicesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });

  const services = useMemo(() => {
    if (!servicesPayload) return [];
    if (Array.isArray(servicesPayload)) {
      return servicesPayload;
    }
    return servicesPayload.items || servicesPayload.services || servicesPayload.results || [];
  }, [servicesPayload]);

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) || null,
    [services, selectedServiceId],
  );

  useEffect(() => {
    if (selection?.type === 'service' && typeof selection.id === 'number') {
      setSelectedServiceId(selection.id);
      return;
    }
    if (!selectedServiceId && services.length) {
      setSelectedServiceId(services[0].service_id);
    }
  }, [selection, selectedServiceId, services]);

  const { data: serviceItems = [], isLoading: serviceItemsLoading, error: serviceItemsError } = useQuery<ServiceItem[]>({
    queryKey: ['serviceItems', projectId, selectedServiceId],
    queryFn: async () => {
      if (!selectedServiceId) return [];
      const response = await serviceItemsApi.getAll(projectId, selectedServiceId);
      return response.data;
    },
    enabled: Number.isFinite(projectId) && Number.isFinite(selectedServiceId ?? NaN),
  });

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

  const updateServiceItemField = useMutation<
    ServiceItem,
    Error,
    { item: ServiceItem; fieldName: keyof ServiceItem; value: unknown },
    { previousItems?: ServiceItem[] }
  >({
    mutationFn: async ({ item, fieldName, value }) => {
      if (!selectedServiceId) {
        throw new Error('Select a service to edit items.');
      }
      await serviceItemsApi.update(projectId, selectedServiceId, item.item_id, {
        [fieldName]: value,
      } as Partial<ServiceItem>);
      return { ...item, [fieldName]: value };
    },
    onMutate: async ({ item, fieldName, value }) => {
      setItemUpdateError(null);
      await queryClient.cancelQueries({ queryKey: ['serviceItems', projectId, selectedServiceId] });
      const previousItems = queryClient.getQueryData<ServiceItem[]>(['serviceItems', projectId, selectedServiceId]);
      queryClient.setQueryData<ServiceItem[]>(['serviceItems', projectId, selectedServiceId], (existing) => {
        if (!existing) return existing;
        return existing.map((entry) =>
          entry.item_id === item.item_id ? { ...entry, [fieldName]: value } : entry,
        );
      });
      return { previousItems };
    },
    onError: (error, _variables, context) => {
      setItemUpdateError(error.message || 'Failed to update item.');
      if (context?.previousItems) {
        queryClient.setQueryData(['serviceItems', projectId, selectedServiceId], context.previousItems);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, selectedServiceId] });
    },
  });

  const createServiceItem = useMutation({
    mutationFn: async (payload: Partial<ServiceItem>) => {
      if (!selectedServiceId) {
        throw new Error('Select a service to add items.');
      }
      return serviceItemsApi.create(projectId, selectedServiceId, payload as any);
    },
    onSuccess: (response, variables) => {
      const itemId = response.data?.item_id;
      if (!itemId) {
        return;
      }
      queryClient.setQueryData<ServiceItem[]>(['serviceItems', projectId, selectedServiceId], (existing) => {
        const next = existing ? [...existing] : [];
        next.unshift({
          item_id: itemId,
          project_id: projectId,
          service_id: selectedServiceId as number,
          item_type: variables.item_type || 'deliverable',
          title: variables.title || 'Untitled',
          description: variables.description,
          planned_date: variables.planned_date,
          due_date: variables.due_date,
          status: (variables.status as ServiceItem['status']) || 'planned',
          priority: (variables.priority as ServiceItem['priority']) || 'medium',
          assigned_to: variables.assigned_to,
          evidence_links: variables.evidence_links,
          notes: variables.notes,
          invoice_reference: variables.invoice_reference,
          is_billed: variables.is_billed,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
        return next;
      });
      if (variables && typeof (variables as ServiceItem).item_id === 'number') {
        const draftId = (variables as ServiceItem).item_id;
        setItemDrafts((prev) => prev.filter((draft) => draft.item_id !== draftId));
      }
    },
    onError: (error: any) => {
      setItemUpdateError(error?.message || 'Failed to create item.');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, selectedServiceId] });
    },
  });

  const deleteServiceItem = useMutation({
    mutationFn: async (itemId: number) => {
      if (!selectedServiceId) {
        throw new Error('Select a service to delete items.');
      }
      return serviceItemsApi.delete(projectId, selectedServiceId, itemId);
    },
    onSuccess: (_response, itemId) => {
      queryClient.setQueryData<ServiceItem[]>(['serviceItems', projectId, selectedServiceId], (existing) =>
        existing ? existing.filter((item) => item.item_id !== itemId) : existing,
      );
    },
    onError: (error: any) => {
      setItemUpdateError(error?.message || 'Failed to delete item.');
    },
  });

  const handleAddDraft = () => {
    if (!selectedServiceId) {
      setItemUpdateError('Select a service to add items.');
      return;
    }
    const draft: ServiceItem & { isDraft: boolean } = {
      item_id: Date.now(),
      project_id: projectId,
      service_id: selectedServiceId,
      item_type: 'deliverable',
      title: '',
      planned_date: selectedService?.start_date || new Date().toISOString().slice(0, 10),
      status: 'planned',
      priority: 'medium',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      isDraft: true,
    } as ServiceItem & { isDraft: boolean };
    setItemDrafts((prev) => [draft, ...prev]);
  };

  return (
    <Box data-testid="workspace-deliverables-tab">
      {reviewUpdateError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {reviewUpdateError}
        </Alert>
      )}
      {itemUpdateError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {itemUpdateError}
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
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
              <TextField
                select
                size="small"
                label="Service"
                value={selectedServiceId ?? ''}
                onChange={(event) => {
                  const nextId = Number(event.target.value);
                  setSelectedServiceId(nextId);
                  if (Number.isFinite(nextId)) {
                    navigate(`/projects/${projectId}/workspace/deliverables?sel=service:${nextId}`, { replace: true });
                  }
                }}
                sx={{ minWidth: 240 }}
              >
                {services.map((service) => (
                  <MenuItem key={service.service_id} value={service.service_id}>
                    {service.service_code} · {service.service_name}
                  </MenuItem>
                ))}
              </TextField>
              <Button variant="outlined" onClick={handleAddDraft} data-testid="deliverables-add-item-button">
                Add item
              </Button>
            </Stack>
            {serviceItemsError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Failed to load service items.
              </Alert>
            )}
            {serviceItemsLoading ? (
              <Typography color="text.secondary">Loading items...</Typography>
            ) : selectedServiceId ? (
              <LinearListContainer>
                <LinearListHeaderRow
                  columns={['Title', 'Planned', 'Due', 'Status', 'Priority', 'Assignee', 'Evidence', 'Actions']}
                />
                {[...itemDrafts, ...filteredServiceItems].map((item) => {
                  const isDraft = (item as any).isDraft;
                  return (
                    <LinearListRow
                      key={`item-${item.item_id}`}
                      testId={`deliverable-item-row-${item.item_id}`}
                      columns={8}
                      hoverable
                      onClick={() => {
                        if (!isDraft) {
                          navigate(`/projects/${projectId}/workspace/deliverables?sel=item:${item.item_id}`, { replace: true });
                        }
                      }}
                    >
                      <Box>
                        {isDraft ? (
                          <TextField
                            size="small"
                            placeholder="Item title"
                            value={item.title || ''}
                            onChange={(event) => {
                              const value = event.target.value;
                              setItemDrafts((prev) =>
                                prev.map((draft) => (draft.item_id === item.item_id ? { ...draft, title: value } : draft)),
                              );
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={item.title}
                            type="text"
                            testId={`cell-item-title-${item.item_id}`}
                            isSaving={
                              updateServiceItemField.isPending
                              && updateServiceItemField.variables?.item.item_id === item.item_id
                              && updateServiceItemField.variables?.fieldName === 'title'
                            }
                            onSave={async (value) => {
                              await updateServiceItemField.mutateAsync({
                                item,
                                fieldName: 'title',
                                value,
                              });
                            }}
                          />
                        )}
                      </Box>
                      <Box>
                        {isDraft ? (
                          <TextField
                            type="date"
                            size="small"
                            value={item.planned_date || ''}
                            onChange={(event) => {
                              const value = event.target.value;
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, planned_date: value } : draft,
                                ),
                              );
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={item.planned_date}
                            type="date"
                            testId={`cell-item-planned-${item.item_id}`}
                            isSaving={
                              updateServiceItemField.isPending
                              && updateServiceItemField.variables?.item.item_id === item.item_id
                              && updateServiceItemField.variables?.fieldName === 'planned_date'
                            }
                            onSave={async (value) => {
                              await updateServiceItemField.mutateAsync({
                                item,
                                fieldName: 'planned_date',
                                value,
                              });
                            }}
                          />
                        )}
                      </Box>
                      <Box>
                        {isDraft ? (
                          <TextField
                            type="date"
                            size="small"
                            value={item.due_date || ''}
                            onChange={(event) => {
                              const value = event.target.value;
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, due_date: value } : draft,
                                ),
                              );
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={item.due_date}
                            type="date"
                            testId={`cell-item-due-${item.item_id}`}
                            isSaving={
                              updateServiceItemField.isPending
                              && updateServiceItemField.variables?.item.item_id === item.item_id
                              && updateServiceItemField.variables?.fieldName === 'due_date'
                            }
                            onSave={async (value) => {
                              await updateServiceItemField.mutateAsync({
                                item,
                                fieldName: 'due_date',
                                value,
                              });
                            }}
                          />
                        )}
                      </Box>
                      <Box sx={{ minWidth: 140 }}>
                        <TextField
                          select
                          size="small"
                          value={item.status || 'planned'}
                          onChange={async (event) => {
                            const value = event.target.value;
                            if (isDraft) {
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, status: value as ServiceItem['status'] } : draft,
                                ),
                              );
                              return;
                            }
                            await updateServiceItemField.mutateAsync({
                              item,
                              fieldName: 'status',
                              value,
                            });
                          }}
                        >
                          {ITEM_STATUS_OPTIONS.map((status) => (
                            <MenuItem key={status} value={status}>
                              {status}
                            </MenuItem>
                          ))}
                        </TextField>
                      </Box>
                      <Box sx={{ minWidth: 140 }}>
                        <TextField
                          select
                          size="small"
                          value={item.priority || 'medium'}
                          onChange={async (event) => {
                            const value = event.target.value;
                            if (isDraft) {
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, priority: value as ServiceItem['priority'] } : draft,
                                ),
                              );
                              return;
                            }
                            await updateServiceItemField.mutateAsync({
                              item,
                              fieldName: 'priority',
                              value,
                            });
                          }}
                        >
                          {ITEM_PRIORITY_OPTIONS.map((priority) => (
                            <MenuItem key={priority} value={priority}>
                              {priority}
                            </MenuItem>
                          ))}
                        </TextField>
                      </Box>
                      <Box>
                        {isDraft ? (
                          <TextField
                            size="small"
                            placeholder="Assignee"
                            value={item.assigned_to || ''}
                            onChange={(event) => {
                              const value = event.target.value;
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, assigned_to: value } : draft,
                                ),
                              );
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={item.assigned_to}
                            type="text"
                            testId={`cell-item-assignee-${item.item_id}`}
                            isSaving={
                              updateServiceItemField.isPending
                              && updateServiceItemField.variables?.item.item_id === item.item_id
                              && updateServiceItemField.variables?.fieldName === 'assigned_to'
                            }
                            onSave={async (value) => {
                              await updateServiceItemField.mutateAsync({
                                item,
                                fieldName: 'assigned_to',
                                value,
                              });
                            }}
                          />
                        )}
                      </Box>
                      <Box>
                        {isDraft ? (
                          <TextField
                            size="small"
                            placeholder="Evidence links"
                            value={item.evidence_links || ''}
                            onChange={(event) => {
                              const value = event.target.value;
                              setItemDrafts((prev) =>
                                prev.map((draft) =>
                                  draft.item_id === item.item_id ? { ...draft, evidence_links: value } : draft,
                                ),
                              );
                            }}
                          />
                        ) : (
                          <EditableCell
                            value={item.evidence_links}
                            type="text"
                            testId={`cell-item-evidence-${item.item_id}`}
                            isSaving={
                              updateServiceItemField.isPending
                              && updateServiceItemField.variables?.item.item_id === item.item_id
                              && updateServiceItemField.variables?.fieldName === 'evidence_links'
                            }
                            onSave={async (value) => {
                              await updateServiceItemField.mutateAsync({
                                item,
                                fieldName: 'evidence_links',
                                value,
                              });
                            }}
                          />
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {isDraft ? (
                          <Button
                            size="small"
                            variant="contained"
                            disabled={!item.title}
                            onClick={() => createServiceItem.mutate(item)}
                          >
                            Save
                          </Button>
                        ) : (
                          <IconButton
                            aria-label="Delete item"
                            onClick={(event) => {
                              event.stopPropagation();
                              deleteServiceItem.mutate(item.item_id);
                            }}
                          >
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Box>
                    </LinearListRow>
                  );
                })}
              </LinearListContainer>
            ) : (
              <Typography color="text.secondary">Select a service to view items.</Typography>
            )}
          </Box>
        </>
      ) : (
        <Typography color="text.secondary">No deliverables found for this project.</Typography>
      )}
    </Box>
  );
}
