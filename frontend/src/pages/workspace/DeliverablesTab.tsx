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
import type { InvoiceBatch, Project, ProjectReviewItem, ProjectReviewsResponse, ServiceItem, ServiceReview } from '@/types/api';
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
const INVOICE_STATUS_OPTIONS = ['unbilled', 'invoiced', 'paid'] as const;

const PHASE_ORDER = ['Initiation', 'Design', 'Construction', 'As-Built'];
const phaseIndex = (p?: string | null) => {
  if (!p) return Number.POSITIVE_INFINITY;
  const idx = PHASE_ORDER.findIndex((x) => x.toLowerCase() === p.toLowerCase());
  return idx >= 0 ? idx : Number.POSITIVE_INFINITY;
};

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

  type UnifiedDeliverable = {
    kind: 'review' | 'item';
    id: number;
    service_id: number;
    service_label: string;
    phase?: string | null;
    title: string;
    planned_date?: string | null;
    due_date?: string | null;
    status?: string | null;
    fee_amount?: number | null;
    invoice_status?: string | null;
    invoice_reference?: string | null;
    raw: ProjectReviewItem | ServiceItem;
  };

  const serviceLabelById = useMemo(() => {
    const map = new Map<number, string>();
    services.forEach((s) => {
      map.set(s.service_id, [s.service_code, s.service_name].filter(Boolean).join(' · '));
    });
    return map;
  }, [services]);

  const reviewsForSelectedService = useMemo(
    () => filteredReviewItems.filter((r) => !selectedServiceId || r.service_id === selectedServiceId),
    [filteredReviewItems, selectedServiceId],
  );

  const unifiedDeliverables = useMemo<UnifiedDeliverable[]>(() => {
    const reviewRows: UnifiedDeliverable[] = reviewsForSelectedService.map((r) => ({
      kind: 'review',
      id: r.review_id,
      service_id: r.service_id,
      service_label: serviceLabelById.get(r.service_id) || [r.service_code, r.service_name].filter(Boolean).join(' · '),
      phase: r.phase,
      title: r.deliverables || (r.cycle_no ? `Review Cycle ${r.cycle_no}` : 'Review'),
      planned_date: r.planned_date,
      due_date: r.due_date,
      status: r.status || null,
      fee_amount: (r as any).fee_amount ?? null,
      invoice_status: (r as any).invoice_status ?? null,
      invoice_reference: r.invoice_reference || null,
      raw: r,
    }));
    const itemRows: UnifiedDeliverable[] = [...itemDrafts, ...filteredServiceItems].map((i) => ({
      kind: 'item',
      id: i.item_id,
      service_id: i.service_id,
      service_label: serviceLabelById.get(i.service_id) || [i.service_code, i.service_name].filter(Boolean).join(' · '),
      phase: i.phase,
      title: i.title,
      planned_date: i.planned_date || null,
      due_date: i.due_date || null,
      status: i.status,
      fee_amount: i.fee_amount ?? null,
      invoice_status: i.invoice_status ?? null,
      invoice_reference: i.invoice_reference || null,
      raw: i,
    }));
    const all = [...reviewRows, ...itemRows];
    return all.sort((a, b) => {
      const pa = phaseIndex(a.phase);
      const pb = phaseIndex(b.phase);
      if (pa !== pb) return pa - pb;
      const da = (a.planned_date || a.due_date || '') as string;
      const db = (b.planned_date || b.due_date || '') as string;
      if (da && db) return da.localeCompare(db);
      return (a.title || '').localeCompare(b.title || '');
    });
  }, [reviewsForSelectedService, itemDrafts, filteredServiceItems, serviceLabelById]);

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
      {projectReviewsLoading && serviceItemsLoading ? (
        <Typography color="text.secondary">Loading deliverables...</Typography>
      ) : unifiedDeliverables.length ? (
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
            <LinearListHeaderRow columns={[
              'Phase','Type','Service','Title','Planned','Due','Status','Fee','Invoice Status','Invoice #'
            ]} />
            {unifiedDeliverables.map((d) => {
              const isReview = d.kind === 'review';
              const review = isReview ? (d.raw as ProjectReviewItem) : null;
              const item = !isReview ? (d.raw as ServiceItem) : null;
              const plannedLabel = formatDate(d.planned_date || null);
              const dueLabel = formatDate(d.due_date || null);
              return (
                <LinearListRow key={`${d.kind}-${d.id}`} testId={`deliverable-row-${d.kind}-${d.id}`} columns={10} hoverable>
                  {/* Phase */}
                  <Box sx={{ minWidth: 140 }}>
                    <TextField
                      size="small"
                      value={d.phase || ''}
                      placeholder="Phase"
                      onChange={async (event) => {
                        const value = event.target.value || null;
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'phase', value });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'phase', value });
                        }
                      }}
                    />
                  </Box>
                  {/* Type */}
                  <LinearListCell>{isReview ? 'Review' : (item?.item_type || 'Item')}</LinearListCell>
                  {/* Service */}
                  <LinearListCell>{d.service_label || 'Service'}</LinearListCell>
                  {/* Title */}
                  <Box sx={{ minWidth: 220 }}>
                    {item ? (
                      <EditableCell
                        value={d.title}
                        type="text"
                        testId={`cell-title-${d.kind}-${d.id}`}
                        isSaving={updateServiceItemField.isPending && updateServiceItemField.variables?.item.item_id === d.id && updateServiceItemField.variables?.fieldName === 'title'}
                        onSave={async (value) => {
                          await updateServiceItemField.mutateAsync({ item: item!, fieldName: 'title', value });
                        }}
                      />
                    ) : (
                      <LinearListCell variant="secondary">{d.title}</LinearListCell>
                    )}
                  </Box>
                  {/* Planned */}
                  <Box>
                    {item ? (
                      <EditableCell
                        value={item.planned_date}
                        type="date"
                        testId={`cell-planned-${d.kind}-${d.id}`}
                        isSaving={updateServiceItemField.isPending && updateServiceItemField.variables?.item.item_id === d.id && updateServiceItemField.variables?.fieldName === 'planned_date'}
                        onSave={async (value) => {
                          await updateServiceItemField.mutateAsync({ item: item!, fieldName: 'planned_date', value });
                        }}
                      />
                    ) : (
                      <LinearListCell variant="secondary">{plannedLabel}</LinearListCell>
                    )}
                  </Box>
                  {/* Due */}
                  <Box>
                    <EditableCell
                      value={d.due_date || ''}
                      type="date"
                      testId={`cell-due-${d.kind}-${d.id}`}
                      isSaving={
                        isReview
                          ? (updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === d.id && updateDeliverableField.variables?.fieldName === 'due_date')
                          : (updateServiceItemField.isPending && updateServiceItemField.variables?.item.item_id === d.id && updateServiceItemField.variables?.fieldName === 'due_date')
                      }
                      onSave={async (value) => {
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'due_date', value });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'due_date', value });
                        }
                      }}
                    />
                  </Box>
                  {/* Status */}
                  <Box sx={{ minWidth: 140 }}>
                    <TextField
                      select
                      size="small"
                      value={(d.status || 'planned')}
                      onChange={async (event) => {
                        const value = event.target.value;
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'status', value });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'status', value });
                        }
                      }}
                    >
                      {ITEM_STATUS_OPTIONS.map((s) => (
                        <MenuItem key={s} value={s}>{s}</MenuItem>
                      ))}
                    </TextField>
                  </Box>
                  {/* Fee */}
                  <Box sx={{ minWidth: 120 }}>
                    <EditableCell
                      value={d.fee_amount ?? null}
                      type="number"
                      testId={`cell-fee-${d.kind}-${d.id}`}
                      isSaving={
                        isReview
                          ? (updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === d.id && updateDeliverableField.variables?.fieldName === 'fee_amount')
                          : (updateServiceItemField.isPending && updateServiceItemField.variables?.item.item_id === d.id && updateServiceItemField.variables?.fieldName === 'fee_amount')
                      }
                      onSave={async (value) => {
                        const parsed = value === '' ? null : Number(value);
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'fee_amount', value: parsed });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'fee_amount', value: parsed });
                        }
                      }}
                    />
                  </Box>
                  {/* Invoice Status */}
                  <Box sx={{ minWidth: 140 }}>
                    <TextField
                      select
                      size="small"
                      value={d.invoice_status || ''}
                      onChange={async (event) => {
                        const value = event.target.value || null;
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'invoice_status', value });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'invoice_status', value });
                        }
                      }}
                    >
                      <MenuItem value="">--</MenuItem>
                      {INVOICE_STATUS_OPTIONS.map((s) => (
                        <MenuItem key={s} value={s}>{s}</MenuItem>
                      ))}
                    </TextField>
                  </Box>
                  {/* Invoice # */}
                  <Box sx={{ minWidth: 160 }}>
                    <EditableCell
                      value={d.invoice_reference || ''}
                      type="text"
                      testId={`cell-invref-${d.kind}-${d.id}`}
                      isSaving={
                        isReview
                          ? (updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === d.id && updateDeliverableField.variables?.fieldName === 'invoice_reference')
                          : (updateServiceItemField.isPending && updateServiceItemField.variables?.item.item_id === d.id && updateServiceItemField.variables?.fieldName === 'invoice_reference')
                      }
                      onSave={async (value) => {
                        if (isReview && review) {
                          await updateDeliverableField.mutateAsync({ review, fieldName: 'invoice_reference', value });
                        } else if (item) {
                          await updateServiceItemField.mutateAsync({ item, fieldName: 'invoice_reference', value });
                        }
                      }}
                    />
                  </Box>
                </LinearListRow>
              );
            })}
          </LinearListContainer>
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Add Deliverable (Item)
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
