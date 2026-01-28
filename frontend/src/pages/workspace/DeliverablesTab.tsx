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
  MenuItem,
  useMediaQuery,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { invoiceBatchesApi, projectServicesApi, serviceItemsApi } from '@/api';
import { projectReviewsApi } from '@/api/projectReviews';
import type { InvoiceBatch, Project, ProjectReviewItem, ProjectReviewsResponse, ServiceItem, ServiceReview } from '@/types/api';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import type { Selection } from '@/hooks/useWorkspaceSelection';
import { EditableCell } from '@/components/projects/EditableCells';
import { LinearListContainer, LinearListRow, LinearListCell } from '@/components/ui/LinearList';

type OutletContext = {
  projectId: number;
  project: Project | null;
  selection: Selection | null;
};

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  if (value === '1900-01-01') return '—';
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
  // Table-level service filter ('all' shows all services). Stored per-project in localStorage.
  const [tableServiceFilter, setTableServiceFilter] = useState<'all' | number>('all');
  const [sortKey, setSortKey] = useState<'phase' | 'service' | 'planned' | 'due' | 'status' | 'fee' | 'invoice_status' | 'invoice_reference'>('due');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const theme = useTheme();
  const isLgUp = useMediaQuery(theme.breakpoints.up('lg'));
  const isXlUp = useMediaQuery(theme.breakpoints.up('xl'));

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

  useEffect(() => {
    const storageKey = `deliverables.tableServiceFilter.${projectId}`;
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem(storageKey) : null;
    let next: 'all' | number = 'all';
    if (stored === 'all') {
      next = 'all';
    } else if (stored) {
      const parsed = Number(stored);
      if (Number.isFinite(parsed) && services.some((s) => s.service_id === parsed)) {
        next = parsed;
      }
    }
    if (next !== tableServiceFilter) {
      setTableServiceFilter(next);
    }
    if (typeof window !== 'undefined' && stored == null) {
      window.localStorage.setItem(storageKey, 'all');
    }
  }, [projectId, services, tableServiceFilter]);

  const {
    data: projectItems = { items: [] as ServiceItem[], total: 0 },
    isLoading: projectItemsLoading,
    error: projectItemsError,
  } = useQuery<{ items: ServiceItem[]; total: number }>({
    queryKey: ['projectItems', projectId],
    queryFn: async () => {
      const response = await serviceItemsApi.getProjectItems(projectId);
      return response ?? { items: [], total: 0 };
    },
    enabled: Number.isFinite(projectId),
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

  const allServiceItems = useMemo(() => projectItems?.items ?? [], [projectItems]);

  const filteredServiceItems = useMemo(() => {
    if (!deliverableFilters.dueThisMonth && !deliverableFilters.readyToInvoice) {
      return allServiceItems;
    }
    const currentMonth = toMonthString(new Date());
    return allServiceItems.filter((item) => {
      const dueMonth = formatInvoiceMonth(item.due_date) ?? '';
      const matchesDueThisMonth = !deliverableFilters.dueThisMonth || dueMonth === currentMonth;
      const matchesReady =
        !deliverableFilters.readyToInvoice
        || ((item.status || '').toLowerCase() === 'completed' && !item.is_billed);
      return matchesDueThisMonth && matchesReady;
    });
  }, [allServiceItems, deliverableFilters]);

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
      if (!item.service_id) {
        throw new Error('Missing service for this item.');
      }
      await serviceItemsApi.update(projectId, item.service_id, item.item_id, {
        [fieldName]: value,
      } as Partial<ServiceItem>);
      return { ...item, [fieldName]: value };
    },
    onMutate: async ({ item, fieldName, value }) => {
      setItemUpdateError(null);
      await queryClient.cancelQueries({ queryKey: ['projectItems', projectId] });
      const previousItems = queryClient.getQueryData<{ items: ServiceItem[]; total: number }>(['projectItems', projectId]);
      queryClient.setQueryData(['projectItems', projectId], (existing: { items: ServiceItem[]; total: number } | undefined) => {
        if (!existing) return existing;
        return {
          ...existing,
          items: existing.items.map((entry) =>
            entry.item_id === item.item_id ? { ...entry, [fieldName]: value } : entry,
          ),
        };
      });
      return { previousItems: previousItems?.items };
    },
    onError: (error, _variables, context) => {
      setItemUpdateError(error.message || 'Failed to update item.');
      if (context?.previousItems) {
        queryClient.setQueryData(['projectItems', projectId], {
          items: context.previousItems,
          total: context.previousItems.length,
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['projectItems', projectId] });
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
      queryClient.setQueryData(['projectItems', projectId], (existing: { items: ServiceItem[]; total: number } | undefined) => {
        const nextItems = existing?.items ? [...existing.items] : [];
        nextItems.unshift({
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
        return { items: nextItems, total: (existing?.total ?? 0) + 1 };
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
      queryClient.invalidateQueries({ queryKey: ['projectItems', projectId] });
    },
  });

  const deleteServiceItem = useMutation({
    mutationFn: async ({ itemId, serviceId }: { itemId: number; serviceId: number }) => {
      return serviceItemsApi.delete(projectId, serviceId, itemId);
    },
    onSuccess: (_response, { itemId }) => {
      queryClient.setQueryData(['projectItems', projectId], (existing: { items: ServiceItem[]; total: number } | undefined) => {
        if (!existing) return existing;
        const items = existing.items.filter((item) => item.item_id !== itemId);
        return { items, total: Math.max(0, (existing.total ?? items.length) - 1) };
      });
    },
    onError: (error: any) => {
      setItemUpdateError(error?.message || 'Failed to delete item.');
    },
  });

  const moveReview = useMutation({
    mutationFn: async ({ review, toServiceId }: { review: ProjectReviewItem; toServiceId: number }) => {
      return projectReviewsApi.moveServiceReview(projectId, review.review_id, { to_service_id: toServiceId });
    },
    onSuccess: () => {
      // Invalidate all reviews queries to refresh data with updated service_id
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] });
    },
    onError: (error: any) => {
      setReviewUpdateError(error?.message || 'Failed to move review to another service.');
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

  // Helper to handle sort column click
  const handleSortClick = (key: typeof sortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  // Helper to parse dates for comparison
  const parseDate = (dateStr?: string | null) => {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  // Helper to check if date is a placeholder
  const isPlaceholderDate = (dateStr?: string | null) => {
    return dateStr === '1900-01-01';
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
    fee?: number | null;
    fee_source?: string | null;
    is_user_modified?: boolean | null;
    user_modified_at?: string | null;
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

  const reviewsForTable = useMemo(
    () => (tableServiceFilter === 'all'
      ? filteredReviewItems
      : filteredReviewItems.filter((r) => r.service_id === tableServiceFilter)),
    [filteredReviewItems, tableServiceFilter],
  );

  const itemsForTable = useMemo(() => {
    const items = [...itemDrafts, ...filteredServiceItems];
    if (tableServiceFilter === 'all') return items;
    return items.filter((i) => i.service_id === tableServiceFilter);
  }, [filteredServiceItems, itemDrafts, tableServiceFilter]);

  const unifiedDeliverables = useMemo<UnifiedDeliverable[]>(() => {
    const reviewRows: UnifiedDeliverable[] = reviewsForTable.map((r) => ({
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
      fee: r.fee ?? null,
      fee_source: r.fee_source ?? null,
      is_user_modified: r.is_user_modified ?? null,
      user_modified_at: r.user_modified_at ?? null,
      invoice_status: (r as any).invoice_status ?? null,
      invoice_reference: r.invoice_reference || null,
      raw: r,
    }));
    const itemRows: UnifiedDeliverable[] = itemsForTable.map((i) => ({
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
      fee: (i as any).fee ?? null,
      fee_source: (i as any).fee_source ?? null,
      invoice_status: i.invoice_status ?? null,
      invoice_reference: i.invoice_reference || null,
      raw: i,
    }));
    const all = [...reviewRows, ...itemRows];

    // Apply sorting based on sortKey and sortDir
    const sorted = all.sort((a, b) => {
      let cmp = 0;

      switch (sortKey) {
        case 'phase':
          cmp = phaseIndex(a.phase) - phaseIndex(b.phase);
          break;
        case 'service':
          cmp = (a.service_label || '').localeCompare(b.service_label || '');
          break;
        case 'planned': {
          const dateA = parseDate(a.planned_date);
          const dateB = parseDate(b.planned_date);
          const aHasFake = isPlaceholderDate(a.planned_date);
          const bHasFake = isPlaceholderDate(b.planned_date);
          if (aHasFake && !bHasFake) cmp = sortDir === 'asc' ? 1 : -1;
          else if (!aHasFake && bHasFake) cmp = sortDir === 'asc' ? -1 : 1;
          else if (dateA && dateB) cmp = dateA.getTime() - dateB.getTime();
          break;
        }
        case 'due': {
          const dateA = parseDate(a.due_date);
          const dateB = parseDate(b.due_date);
          const aHasFake = isPlaceholderDate(a.due_date);
          const bHasFake = isPlaceholderDate(b.due_date);
          if (aHasFake && !bHasFake) cmp = sortDir === 'asc' ? 1 : -1;
          else if (!aHasFake && bHasFake) cmp = sortDir === 'asc' ? -1 : 1;
          else if (dateA && dateB) cmp = dateA.getTime() - dateB.getTime();
          break;
        }
        case 'status':
          cmp = (a.status || '').localeCompare(b.status || '');
          break;
        case 'fee':
          cmp = (a.fee ?? 0) - (b.fee ?? 0);
          break;
        case 'invoice_status':
          cmp = (a.invoice_status || '').localeCompare(b.invoice_status || '');
          break;
        case 'invoice_reference':
          cmp = (a.invoice_reference || '').localeCompare(b.invoice_reference || '');
          break;
        default:
          cmp = 0;
      }

      // Reverse if desc
      if (sortDir === 'desc') cmp = -cmp;
      return cmp;
    });

    return sorted;
  }, [reviewsForTable, itemsForTable, serviceLabelById, sortKey, sortDir]);

  const noWrap = { whiteSpace: 'nowrap' } as const;
  const columnGap = Number(theme.spacing(2).replace('px', '')) || 16;
  const columnWidths = {
    phase: 140,
    type: 110,
    service: 220,
    title: 260,
    planned: 120,
    due: 120,
    status: 140,
    fee: 120,
    invoice_status: 140,
    invoice_reference: 160,
  } as const;
  const stickyOffsets = {
    phase: 0,
    type: columnWidths.phase + columnGap,
    service: columnWidths.phase + columnWidths.type + columnGap * 2,
    title: columnWidths.phase + columnWidths.type + columnWidths.service + columnGap * 3,
  };
  const showInvoiceNumber = isXlUp;
  const showInvoiceStatus = isLgUp;
  const showPlannedDate = isLgUp;
  const columns = [
    { id: 'phase', label: 'Phase', minWidth: columnWidths.phase, stickyLeft: stickyOffsets.phase, sortKey: 'phase' as const },
    { id: 'type', label: 'Type', minWidth: columnWidths.type, stickyLeft: stickyOffsets.type },
    { id: 'service', label: 'Service', minWidth: columnWidths.service, stickyLeft: stickyOffsets.service, sortKey: 'service' as const },
    { id: 'title', label: 'Title', minWidth: columnWidths.title, stickyLeft: stickyOffsets.title },
    { id: 'planned', label: 'Planned', minWidth: columnWidths.planned, sortKey: 'planned' as const, hidden: !showPlannedDate },
    { id: 'due', label: 'Due', minWidth: columnWidths.due, sortKey: 'due' as const },
    { id: 'status', label: 'Status', minWidth: columnWidths.status, sortKey: 'status' as const },
    { id: 'fee', label: 'Fee', minWidth: columnWidths.fee, sortKey: 'fee' as const },
    { id: 'invoice_status', label: 'Invoice Status', minWidth: columnWidths.invoice_status, sortKey: 'invoice_status' as const, hidden: !showInvoiceStatus },
    { id: 'invoice_reference', label: 'Invoice #', minWidth: columnWidths.invoice_reference, sortKey: 'invoice_reference' as const, hidden: !showInvoiceNumber },
  ];
  const visibleColumns = columns.filter((column) => !column.hidden);
  const gridTemplateColumns = visibleColumns
    .map((column) => (column.id === 'title' ? `minmax(${column.minWidth}px, 1fr)` : `${column.minWidth}px`))
    .join(' ');
  const tableMinWidth = visibleColumns.reduce((sum, column) => sum + column.minWidth, 0);
  const stickyHeaderCell = (left: number) => ({
    position: 'sticky' as const,
    left,
    zIndex: 3,
    backgroundColor: 'background.paper',
  });
  const stickyBodyCell = (left: number) => ({
    position: 'sticky' as const,
    left,
    zIndex: 2,
    backgroundColor: 'inherit',
  });

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
      {projectItemsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load service items.
        </Alert>
      )}
      {projectReviewsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load project reviews.
        </Alert>
      )}
      {projectReviewsLoading && projectItemsLoading ? (
        <Typography color="text.secondary">Loading deliverables...</Typography>
      ) : (
        <>
          {/* Add Item Controls */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Add Deliverable (Item)
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
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
          </Box>

          {/* Filters */}
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
            <TextField
              select
              size="small"
              label="Show"
              value={tableServiceFilter === 'all' ? 'all' : String(tableServiceFilter)}
              onChange={(event) => {
                const value = event.target.value;
                const storageKey = `deliverables.tableServiceFilter.${projectId}`;
                if (value === 'all') {
                  setTableServiceFilter('all');
                  if (typeof window !== 'undefined') {
                    window.localStorage.setItem(storageKey, 'all');
                  }
                  return;
                }
                const nextId = Number(value);
                setTableServiceFilter(nextId);
                if (typeof window !== 'undefined') {
                  window.localStorage.setItem(storageKey, String(nextId));
                }
              }}
              sx={{ minWidth: 220 }}
            >
              <MenuItem value="all">All services</MenuItem>
              {services.map((service) => (
                <MenuItem key={service.service_id} value={service.service_id}>
                  {service.service_code} · {service.service_name}
                </MenuItem>
              ))}
            </TextField>
            <Stack direction="row" spacing={1} data-testid="deliverables-filters">
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
          </Stack>
          {/* Unified Deliverables Table */}
          {unifiedDeliverables.length ? (
            <Box
              sx={{
                width: '100%',
                overflowX: 'auto',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
              }}
            >
              <LinearListContainer variant="elevation" elevation={0} sx={{ minWidth: tableMinWidth, border: 'none', overflow: 'visible' }}>
                {/* Custom Sortable Header */}
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns,
                    gap: 2,
                    px: 2,
                    py: 1,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    backgroundColor: 'background.paper',
                    position: 'sticky',
                    top: 0,
                    zIndex: 2,
                  }}
                >
                  {visibleColumns.map((column) => (
                    <Box
                      key={`header-${column.id}`}
                      onClick={() => column.sortKey && handleSortClick(column.sortKey)}
                      sx={{
                        typography: 'caption',
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        cursor: column.sortKey ? 'pointer' : 'default',
                        userSelect: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                        ...noWrap,
                        ...(column.stickyLeft != null ? stickyHeaderCell(column.stickyLeft) : {}),
                        '&:hover': column.sortKey ? { color: 'text.primary' } : {},
                      }}
                    >
                      {column.label}
                      {column.sortKey && sortKey === column.sortKey && (
                        <span style={{ fontSize: '0.75rem' }}>{sortDir === 'asc' ? '^' : 'v'}</span>
                      )}
                    </Box>
                  ))}
                </Box>
                {unifiedDeliverables.map((d) => {
                  const isReview = d.kind === 'review';
                  const review = isReview ? (d.raw as ProjectReviewItem) : null;
                  const item = !isReview ? (d.raw as ServiceItem) : null;
                  const plannedLabel = formatDate(d.planned_date || null);
                  const dueLabel = formatDate(d.due_date || null);
                  return (
                    <LinearListRow
                      key={`${d.kind}-${d.id}`}
                      testId={`deliverable-row-${d.kind}-${d.id}`}
                      columns={visibleColumns.length}
                      hoverable
                      sx={{ gridTemplateColumns }}
                    >
                      {/* Phase */}
                      <Box sx={{ minWidth: columnWidths.phase, ...stickyBodyCell(stickyOffsets.phase) }}>
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
                      <Box sx={{ minWidth: columnWidths.type, ...stickyBodyCell(stickyOffsets.type), ...noWrap }}>
                        <LinearListCell>
                          {isReview ? 'Review' : (item?.item_type || 'Item')}
                          {isReview && d.is_user_modified && (
                            <Chip
                              label="Modified"
                              size="small"
                              color="warning"
                              sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                            />
                          )}
                        </LinearListCell>
                      </Box>
                      {/* Service */}
                      <Box
                        sx={{
                          minWidth: columnWidths.service,
                          maxWidth: columnWidths.service,
                          overflow: 'hidden',
                          ...noWrap,
                          textOverflow: 'ellipsis',
                          ...stickyBodyCell(stickyOffsets.service),
                        }}
                      >
                        {isReview && review ? (
                          <TextField
                            select
                            size="small"
                            fullWidth
                            value={review.service_id || ''}
                            disabled={moveReview.isPending}
                            onChange={async (event) => {
                              const toServiceId = parseInt(event.target.value, 10);
                              await moveReview.mutateAsync({ review, toServiceId });
                            }}
                            error={moveReview.isError}
                            sx={{ maxWidth: '100%' }}
                            SelectProps={{
                              MenuProps: {
                                PaperProps: { sx: { maxWidth: 420 } },
                              },
                              sx: {
                                maxWidth: '100%',
                                overflow: 'hidden',
                                ...noWrap,
                                textOverflow: 'ellipsis',
                                display: 'block',
                              },
                            }}
                          >
                            {services.map((service) => (
                              <MenuItem key={service.service_id} value={service.service_id}>
                                {service.service_name
                                  ? `${service.service_name}${service.service_code ? ` (${service.service_code})` : ''}`
                                  : service.service_code || `Service ${service.service_id}`}
                              </MenuItem>
                            ))}
                          </TextField>
                        ) : (
                          <LinearListCell sx={{ overflow: 'hidden', textOverflow: 'ellipsis', ...noWrap }}>
                            {d.service_label || 'Service'}
                          </LinearListCell>
                        )}
                      </Box>
                      {/* Title */}
                      <Box
                        sx={{
                          minWidth: columnWidths.title,
                          maxWidth: 320,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          ...noWrap,
                          ...stickyBodyCell(stickyOffsets.title),
                        }}
                      >
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
                      {showPlannedDate && (
                        <Box sx={{ minWidth: columnWidths.planned, ...noWrap }}>
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
                            <LinearListCell variant="secondary" sx={noWrap}>{plannedLabel}</LinearListCell>
                          )}
                        </Box>
                      )}
                      {/* Due */}
                      <Box sx={{ minWidth: columnWidths.due, ...noWrap }}>
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
                      <Box sx={{ minWidth: columnWidths.status }}>
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
                      <Box sx={{ minWidth: columnWidths.fee, ...noWrap }}>
                        {isReview && d.fee !== null && d.fee_source ? (
                          <Tooltip title={`Fee source: ${d.fee_source}`} arrow>
                            <Box sx={{ cursor: 'help' }}>
                              <EditableCell
                                value={d.fee ?? null}
                                type="number"
                                testId={`cell-fee-${d.kind}-${d.id}`}
                                isSaving={
                                  updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === d.id && updateDeliverableField.variables?.fieldName === 'fee_amount'
                                }
                                onSave={async (value) => {
                                  const parsed = value === '' ? null : Number(value);
                                  if (isReview && review) {
                                    await updateDeliverableField.mutateAsync({ review, fieldName: 'fee_amount', value: parsed });
                                  }
                                }}
                              />
                            </Box>
                          </Tooltip>
                        ) : (
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
                        )}
                      </Box>
                      {/* Invoice Status */}
                      {showInvoiceStatus && (
                        <Box sx={{ minWidth: columnWidths.invoice_status }}>
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
                      )}
                      {/* Invoice # */}
                      {showInvoiceNumber && (
                        <Box sx={{ minWidth: columnWidths.invoice_reference, ...noWrap }}>
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
                      )}
                    </LinearListRow>
                  );
                })}
              </LinearListContainer>
            </Box>
          ) : (
            <Typography color="text.secondary">No deliverables found for this project.</Typography>
          )}
        </>
      )}
    </Box>
  );
}
