import { Profiler, type ChangeEvent, useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  Stack,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { projectServicesApi, serviceReviewsApi, serviceItemsApi, fileServiceTemplatesApi } from '@/api';
import type { ProjectServicesListResponse } from '@/api/services';
import type { ProjectService, ServiceReview, ServiceItem, FileServiceTemplate, ApplyTemplateResult } from '@/types/api';
import { profilerLog } from '@/utils/perfLogger';
import { ServicesSummaryStrip } from './ProjectServices/ServicesSummaryStrip';
import { ServicesListRow } from './ProjectServices/ServicesListRow';
import { ServiceDetailDrawer } from './ProjectServices/ServiceDetailDrawer';

interface ProjectServicesTabProps {
  projectId: number;
}

const BILL_RULES = [
  'Fixed Fee',
  'Time & Materials',
  'Percentage of Construction Cost',
  'Milestone Based',
  'Other'
];

const REVIEW_STATUSES = [
  'planned',
  'in_progress',
  'completed',
  'overdue',
  'cancelled'
];

const ITEM_TYPES = [
  'review',
  'audit',
  'deliverable',
  'milestone',
  'inspection',
  'meeting',
  'other'
];

const ITEM_STATUSES = [
  'planned',
  'in_progress',
  'completed',
  'overdue',
  'cancelled'
];

const ITEM_PRIORITIES = [
  'low',
  'medium',
  'high',
  'critical'
];

type BillingSummary = {
  totalAgreed: number;
  totalBilled: number;
  totalRemaining: number;
  progress: number;
};

const pickNumber = (...candidates: Array<unknown>): number | undefined => {
  for (const candidate of candidates) {
    const numeric = typeof candidate === 'number' ? candidate : Number(candidate);
    if (Number.isFinite(numeric)) {
      return numeric;
    }
  }
  return undefined;
};

const unwrapServicesPayload = (input: unknown): unknown => {
  let current = input;
  let depth = 0;
  while (
    current &&
    typeof current === 'object' &&
    'data' in (current as Record<string, unknown>) &&
    depth < 3
  ) {
    const next = (current as Record<string, unknown>).data;
    if (next === current) {
      break;
    }
    current = next;
    depth += 1;
  }
  return current;
};

const normaliseServicesPayload = (
  payload: ProjectServicesListResponse | undefined,
  defaults: { page: number; pageSize: number },
) => {
  const base = unwrapServicesPayload(payload);

  const candidateArrays: Array<ProjectService[] | null> = [
    Array.isArray(base) ? (base as ProjectService[]) : null,
    Array.isArray((base as any)?.services) ? ((base as any)?.services as ProjectService[]) : null,
    Array.isArray((base as any)?.items) ? ((base as any)?.items as ProjectService[]) : null,
    Array.isArray((base as any)?.results) ? ((base as any)?.results as ProjectService[]) : null,
  ];

  const items = candidateArrays.find((value): value is ProjectService[] => Array.isArray(value)) ?? [];

  const total =
    pickNumber(
      (base as any)?.total,
      (base as any)?.total_count,
      (base as any)?.count,
      (base as any)?.meta?.total,
      items.length,
    ) ?? items.length;

  const page =
    pickNumber((base as any)?.page, (base as any)?.current_page, (base as any)?.meta?.page) ??
    defaults.page;

  const pageSize =
    pickNumber(
      (base as any)?.page_size,
      (base as any)?.limit,
      (base as any)?.meta?.page_size,
      defaults.pageSize,
      items.length || defaults.pageSize,
    ) ?? defaults.pageSize;

  const aggregate = ((base as any)?.aggregate ?? (base as any)?.summary ?? (base as any)?.totals ?? (base as any)?.meta?.aggregate) as Record<string, unknown> | undefined;

  return {
    items,
    total: total < 0 ? items.length : total,
    aggregate,
    isServerPaginated: total > items.length,
    page: page > 0 ? page : defaults.page,
    pageSize: pageSize > 0 ? pageSize : defaults.pageSize,
  };
};

const mapAggregateToSummary = (aggregate?: Record<string, unknown>): BillingSummary | undefined => {
  if (!aggregate) {
    return undefined;
  }

  const totalAgreed =
    pickNumber(
      (aggregate as any).total_agreed_fee,
      (aggregate as any).totalAgreed,
      (aggregate as any).total_agreed,
      (aggregate as any).contract_sum,
    ) ?? 0;

  const totalBilled =
    pickNumber(
      (aggregate as any).total_billed,
      (aggregate as any).billed_amount,
      (aggregate as any).total_billed_amount,
      (aggregate as any).billed_sum,
    ) ?? 0;

  const totalRemainingCandidate =
    pickNumber(
      (aggregate as any).total_remaining,
      (aggregate as any).remaining_fee,
      (aggregate as any).total_remaining_fee,
    ) ?? totalAgreed - totalBilled;

  let progress =
    pickNumber(
      (aggregate as any).billing_progress_pct,
      (aggregate as any).progress_pct,
      typeof (aggregate as any).billed_ratio === 'number'
        ? (aggregate as any).billed_ratio * 100
        : Number((aggregate as any).billed_ratio) * 100,
    ) ?? 0;

  if (!Number.isFinite(progress) && totalAgreed > 0) {
    progress = (totalBilled / totalAgreed) * 100;
  }

  return {
    totalAgreed,
    totalBilled,
    totalRemaining: Math.max(Number.isFinite(totalRemainingCandidate) ? totalRemainingCandidate : totalAgreed - totalBilled, 0),
    progress: Math.min(Math.max(Number.isFinite(progress) ? progress : 0, 0), 100),
  };
};

export function ProjectServicesTab({ projectId }: ProjectServicesTabProps) {
  const queryClient = useQueryClient();
  
  // Drawer state (Phase B)
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Dialog states (CRUD)
  const [selectedService, setSelectedService] = useState<ProjectService | null>(null);
  const [selectedReview, setSelectedReview] = useState<ServiceReview | null>(null);
  const [selectedItem, setSelectedItem] = useState<ServiceItem | null>(null);
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [itemDialogOpen, setItemDialogOpen] = useState(false);

  // Pagination
  const [servicesPage, setServicesPage] = useState(0);
  const [servicesRowsPerPage, setServicesRowsPerPage] = useState(10);

  // Form data
  const [serviceFormData, setServiceFormData] = useState({
    service_code: '',
    service_name: '',
    phase: '',
    unit_type: '',
    unit_qty: 0,
    unit_rate: 0,
    lump_sum_fee: 0,
    agreed_fee: 0,
    bill_rule: '',
    notes: '',
  });

  const [reviewFormData, setReviewFormData] = useState({
    cycle_no: 1,
    planned_date: '',
    due_date: '',
    disciplines: '',
    deliverables: '',
    status: 'planned',
    weight_factor: 1.0,
    invoice_reference: '',
    evidence_links: '',
    is_billed: false,
  });

  const [itemFormData, setItemFormData] = useState({
    item_type: 'review',
    title: '',
    description: '',
    planned_date: '',
    due_date: '',
    actual_date: '',
    status: 'planned',
    priority: 'medium',
    assigned_to: '',
    invoice_reference: '',
    evidence_links: '',
    notes: '',
    is_billed: false,
  });

  // Template dialog
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [templateSelection, setTemplateSelection] = useState({
    templateName: '',
    replaceExisting: false,
  });
  const [templateDialogError, setTemplateDialogError] = useState('');
  const [templateFeedback, setTemplateFeedback] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);

  // Fetch services
  const {
    data: servicesPayload,
    isLoading: servicesLoading,
    error: servicesError,
  } = useQuery({
    queryKey: ['projectServices', projectId, servicesPage, servicesRowsPerPage],
    queryFn: () =>
      projectServicesApi.getAll(projectId, {
        page: servicesPage + 1,
        limit: servicesRowsPerPage,
      }),
    placeholderData: (previousData) => previousData,
  });

  // Fetch templates
  const { data: fileTemplates, isLoading: fileTemplatesLoading } = useQuery({
    queryKey: ['fileServiceTemplates'],
    queryFn: async () => {
      const response = await fileServiceTemplatesApi.getAll();
      return response.data;
    },
  });

  const normalizedServices = useMemo(
    () =>
      normaliseServicesPayload(servicesPayload as ProjectServicesListResponse | undefined, {
        page: servicesPage + 1,
        pageSize: servicesRowsPerPage,
      }),
    [servicesPayload, servicesPage, servicesRowsPerPage],
  );

  const {
    items: servicesData,
    total: totalServices,
    aggregate: servicesAggregate,
    isServerPaginated,
    page: serverPage,
    pageSize: serverPageSize,
  } = normalizedServices;

  const serverPageIndex = Math.max(0, serverPage - 1);
  const fileTemplateOptions: FileServiceTemplate[] = fileTemplates ?? [];

  useEffect(() => {
    setServicesPage(0);
  }, [projectId]);

  useEffect(() => {
    const maxPage = Math.max(0, Math.ceil(totalServices / servicesRowsPerPage) - 1);
    if (servicesPage > maxPage) {
      setServicesPage(maxPage);
    }
  }, [totalServices, servicesPage, servicesRowsPerPage]);

  useEffect(() => {
    if (isServerPaginated && serverPageIndex !== servicesPage) {
      setServicesPage(serverPageIndex);
    }
  }, [isServerPaginated, serverPageIndex, servicesPage]);

  useEffect(() => {
    if (isServerPaginated && serverPageSize > 0 && serverPageSize !== servicesRowsPerPage) {
      setServicesRowsPerPage(serverPageSize);
    }
  }, [isServerPaginated, serverPageSize, servicesRowsPerPage]);

  const paginatedServices = useMemo(() => {
    if (isServerPaginated) {
      return servicesData;
    }
    const start = servicesPage * servicesRowsPerPage;
    return servicesData.slice(start, start + servicesRowsPerPage);
  }, [isServerPaginated, servicesData, servicesPage, servicesRowsPerPage]);

  const handleChangeServicesPage = (_event: unknown, newPage: number) => {
    setServicesPage(newPage);
  };

  const handleChangeServicesRowsPerPage = (event: ChangeEvent<HTMLInputElement>) => {
    const nextValue = Number(event.target.value) || 10;
    setServicesRowsPerPage(nextValue);
    setServicesPage(0);
  };

  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
    []
  );

  const formatCurrency = (value?: number | null) =>
    currencyFormatter.format(value === undefined || value === null ? 0 : value);

  const formatPercent = (value?: number | null) => {
    const numeric = value === undefined || value === null ? 0 : value;
    return `${numeric.toFixed(1)}%`;
  };

  const rowsPerPageOptions = useMemo(() => {
    const base = [5, 10, 25, 50];
    if (isServerPaginated && serverPageSize > 0 && !base.includes(serverPageSize)) {
      return [...base, serverPageSize].sort((a, b) => a - b);
    }
    return base;
  }, [isServerPaginated, serverPageSize]);

  const aggregatedSummary = useMemo(
    () => mapAggregateToSummary(servicesAggregate),
    [servicesAggregate],
  );

  const billingSummary = useMemo<BillingSummary>(() => {
    if (aggregatedSummary) {
      return aggregatedSummary;
    }

    const totals = servicesData.reduce(
      (acc, service) => {
        const agreed = service.agreed_fee ?? 0;
        const billed = service.billed_amount ?? service.claimed_to_date ?? 0;
        return {
          totalAgreed: acc.totalAgreed + agreed,
          totalBilled: acc.totalBilled + billed,
        };
      },
      { totalAgreed: 0, totalBilled: 0 },
    );

    const totalRemaining = Math.max(totals.totalAgreed - totals.totalBilled, 0);
    const progress =
      totals.totalAgreed > 0 ? (totals.totalBilled / totals.totalAgreed) * 100 : 0;

    return {
      totalAgreed: totals.totalAgreed,
      totalBilled: totals.totalBilled,
      totalRemaining,
      progress: Math.min(Math.max(progress, 0), 100),
    };
  }, [aggregatedSummary, servicesData]);

  const isPartialSummary = isServerPaginated && !aggregatedSummary;

  const effectivePageSize = isServerPaginated ? serverPageSize : servicesRowsPerPage;
  const safePageSize = effectivePageSize > 0 ? effectivePageSize : servicesRowsPerPage;
  const displayPageIndex = isServerPaginated ? serverPageIndex : servicesPage;
  const displayStart = totalServices === 0 ? 0 : displayPageIndex * safePageSize + 1;
  const displayEnd =
    totalServices === 0
      ? 0
      : Math.min(displayStart + paginatedServices.length - 1, totalServices);
  const displayRangeText =
    totalServices === 0
      ? 'No services loaded'
      : `Showing ${displayStart}-${displayEnd} of ${totalServices} services`;

  const getStatusColor = (
    status: string
  ): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'overdue':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Mutations
  const createServiceMutation = useMutation({
    mutationFn: (data: typeof serviceFormData) => projectServicesApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      handleCloseServiceDialog();
    },
  });

  const updateServiceMutation = useMutation({
    mutationFn: ({ serviceId, data }: { serviceId: number; data: Partial<typeof serviceFormData> }) =>
      projectServicesApi.update(projectId, serviceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      handleCloseServiceDialog();
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: (serviceId: number) => projectServicesApi.delete(projectId, serviceId),
    onSuccess: (_result) => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      setSelectedService(null);
      setIsDrawerOpen(false);
      setSelectedServiceId(null);
    },
  });

  const applyTemplateMutation = useMutation<ApplyTemplateResult, any, { template_name: string; replace_existing: boolean; skip_duplicates: boolean }>({
    mutationFn: (payload) =>
      projectServicesApi.applyTemplate(projectId, payload).then((res) => res.data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId] });
      setSelectedService(null);

      const createdCount = result.created?.length ?? 0;
      const skippedCount = result.skipped?.length ?? 0;
      const replacedCount = result.replaced_services ?? 0;

      const summaryParts = [`created ${createdCount} service${createdCount === 1 ? '' : 's'}`];
      if (skippedCount) {
        summaryParts.push(`skipped ${skippedCount} duplicate${skippedCount === 1 ? '' : 's'}`);
      }
      if (replacedCount) {
        summaryParts.push(`replaced ${replacedCount} existing service${replacedCount === 1 ? '' : 's'}`);
      }

      setTemplateFeedback({
        message: `Template '${result.template_name}' applied: ${summaryParts.join(', ')}.`,
        severity: 'success',
      });
      setTemplateSelection({
        templateName: '',
        replaceExisting: false,
      });
      setTemplateDialogError('');
      setTemplateDialogOpen(false);
    },
    onError: (err: any) => {
      setTemplateDialogError(err?.response?.data?.error || 'Failed to apply template');
    },
  });

  const createReviewMutation = useMutation({
    mutationFn: ({ serviceId, data }: { serviceId: number; data: typeof reviewFormData }) =>
      serviceReviewsApi.create(projectId, serviceId, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, variables.serviceId] });
      handleCloseReviewDialog();
    },
  });

  const updateReviewMutation = useMutation({
    mutationFn: ({
      serviceId,
      reviewId,
      data,
    }: {
      serviceId: number;
      reviewId: number;
      data: Partial<typeof reviewFormData>;
    }) => serviceReviewsApi.update(projectId, serviceId, reviewId, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, variables.serviceId] });
      handleCloseReviewDialog();
    },
  });

  const deleteReviewMutation = useMutation({
    mutationFn: ({ serviceId, reviewId }: { serviceId: number; reviewId: number }) =>
      serviceReviewsApi.delete(projectId, serviceId, reviewId),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, variables.serviceId] });
    },
  });

  const createItemMutation = useMutation({
    mutationFn: ({ serviceId, data }: { serviceId: number; data: typeof itemFormData }) =>
      serviceItemsApi.create(projectId, serviceId, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, variables.serviceId] });
      handleCloseItemDialog();
    },
  });

  const updateItemMutation = useMutation({
    mutationFn: ({
      serviceId,
      itemId,
      data,
    }: {
      serviceId: number;
      itemId: number;
      data: Partial<ServiceItem>;
    }) => serviceItemsApi.update(projectId, serviceId, itemId, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, variables.serviceId] });
      handleCloseItemDialog();
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: ({ serviceId, itemId }: { serviceId: number; itemId: number }) =>
      serviceItemsApi.delete(projectId, serviceId, itemId),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, variables.serviceId] });
    },
  });

  // Handlers
  const handleOpenTemplateDialog = () => {
    if (fileTemplateOptions.length > 0) {
      const firstName = fileTemplateOptions[0].name;
      const currentExists = fileTemplateOptions.some(
        (template) => template.name === templateSelection.templateName,
      );
      setTemplateSelection((prev) => ({
        templateName: currentExists && prev.templateName ? prev.templateName : firstName,
        replaceExisting: prev.replaceExisting,
      }));
    }
    setTemplateDialogError('');
    setTemplateDialogOpen(true);
  };

  const handleCloseTemplateDialog = () => {
    setTemplateDialogOpen(false);
    setTemplateDialogError('');
  };

  const handleApplyTemplate = () => {
    if (!templateSelection.templateName) {
      setTemplateDialogError('Please select a template');
      return;
    }
    setTemplateDialogError('');
    applyTemplateMutation.mutate({
      template_name: templateSelection.templateName,
      replace_existing: templateSelection.replaceExisting,
      skip_duplicates: !templateSelection.replaceExisting,
    });
  };

  const handleOpenServiceDialog = (service?: ProjectService) => {
    if (service) {
      setSelectedService(service);
      setServiceFormData({
        service_code: service.service_code,
        service_name: service.service_name,
        phase: service.phase || '',
        unit_type: service.unit_type || '',
        unit_qty: service.unit_qty || 0,
        unit_rate: service.unit_rate || 0,
        lump_sum_fee: service.lump_sum_fee || 0,
        agreed_fee: service.agreed_fee || 0,
        bill_rule: service.bill_rule || '',
        notes: service.notes || '',
      });
    } else {
      setSelectedService(null);
      setServiceFormData({
        service_code: '',
        service_name: '',
        phase: '',
        unit_type: '',
        unit_qty: 0,
        unit_rate: 0,
        lump_sum_fee: 0,
        agreed_fee: 0,
        bill_rule: '',
        notes: '',
      });
    }
    setServiceDialogOpen(true);
  };

  const handleCloseServiceDialog = () => {
    setServiceDialogOpen(false);
    setSelectedService(null);
  };

  const handleOpenReviewDialog = (
    service: ProjectService,
    review?: ServiceReview,
    existingReviewCount?: number,
  ) => {
    const reviewObj = review;
    const count = existingReviewCount ?? 0;
    setSelectedService(service);

    if (reviewObj) {
      setSelectedReview(reviewObj);
      setReviewFormData({
        cycle_no: reviewObj.cycle_no,
        planned_date: reviewObj.planned_date,
        due_date: reviewObj.due_date || '',
        disciplines: reviewObj.disciplines || '',
        deliverables: reviewObj.deliverables || '',
        status: reviewObj.status,
        weight_factor: reviewObj.weight_factor ?? 1,
        invoice_reference: reviewObj.invoice_reference || '',
        evidence_links: reviewObj.evidence_links || '',
        is_billed: reviewObj.is_billed ?? (reviewObj.status === 'completed'),
      });
    } else {
      setSelectedReview(null);
      setReviewFormData({
        cycle_no: count + 1,
        planned_date: '',
        due_date: '',
        disciplines: '',
        deliverables: '',
        status: 'planned',
        weight_factor: 1.0,
        invoice_reference: '',
        evidence_links: '',
        is_billed: false,
      });
    }
    setReviewDialogOpen(true);
  };

  // Wrapper for drawer onAddReview signature
  const handleAddReview = (service: ProjectService, existingReviewCount: number) => {
    handleOpenReviewDialog(service, undefined, existingReviewCount);
  };

  // Wrapper for drawer onEditReview signature
  const handleEditReview = (service: ProjectService, review: ServiceReview, existingReviewCount: number) => {
    handleOpenReviewDialog(service, review, existingReviewCount);
  };

  const handleCloseReviewDialog = () => {
    setReviewDialogOpen(false);
    setSelectedReview(null);
    setSelectedService(null);
  };

  const handleOpenItemDialog = (service: ProjectService, item?: ServiceItem) => {
    setSelectedService(service);
    if (item) {
      setSelectedItem(item);
      setItemFormData({
        item_type: item.item_type,
        title: item.title,
        description: item.description || '',
        planned_date: item.planned_date || '',
        due_date: item.due_date || '',
        actual_date: item.actual_date || '',
        status: item.status,
        priority: item.priority,
        assigned_to: item.assigned_to || '',
        invoice_reference: item.invoice_reference || '',
        evidence_links: item.evidence_links || '',
        notes: item.notes || '',
        is_billed: item.is_billed ?? (item.status === 'completed'),
      });
    } else {
      setSelectedItem(null);
      setItemFormData({
        item_type: 'review',
        title: '',
        description: '',
        planned_date: '',
        due_date: '',
        actual_date: '',
        status: 'planned',
        priority: 'medium',
        assigned_to: '',
        invoice_reference: '',
        evidence_links: '',
        notes: '',
        is_billed: false,
      });
    }
    setItemDialogOpen(true);
  };

  const handleCloseItemDialog = () => {
    setItemDialogOpen(false);
    setSelectedItem(null);
    setSelectedService(null);
  };

  const handleServiceSubmit = () => {
    if (selectedService) {
      updateServiceMutation.mutate({ serviceId: selectedService.service_id, data: serviceFormData });
    } else {
      createServiceMutation.mutate(serviceFormData);
    }
  };

  const handleReviewSubmit = () => {
    if (!selectedService) return;

    if (selectedReview) {
      updateReviewMutation.mutate({
        serviceId: selectedService.service_id,
        reviewId: selectedReview.review_id,
        data: reviewFormData,
      });
    } else {
      createReviewMutation.mutate({
        serviceId: selectedService.service_id,
        data: reviewFormData,
      });
    }
  };

  const handleItemSubmit = () => {
    if (!selectedService) return;

    if (selectedItem) {
      updateItemMutation.mutate({
        serviceId: selectedService.service_id,
        itemId: selectedItem.item_id,
        data: itemFormData as Partial<ServiceItem>,
      });
    } else {
      createItemMutation.mutate({
        serviceId: selectedService.service_id,
        data: itemFormData,
      });
    }
  };

  const handleDeleteService = (serviceId: number) => {
    if (window.confirm('Are you sure you want to delete this service?')) {
      deleteServiceMutation.mutate(serviceId);
    }
  };

  const handleDeleteReview = (service: ProjectService, reviewId: number) => {
    if (window.confirm('Are you sure you want to delete this review?')) {
      deleteReviewMutation.mutate({ serviceId: service.service_id, reviewId });
    }
  };

  const handleDeleteItem = (service: ProjectService, itemId: number) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      deleteItemMutation.mutate({ serviceId: service.service_id, itemId });
    }
  };

  // Phase B: Drawer handlers
  const handleServiceRowClick = (service: ProjectService) => {
    setSelectedServiceId(service.service_id);
    setSelectedService(service);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setSelectedServiceId(null);
    setSelectedService(null);
  };

  const selectedServiceFromDrawer = selectedServiceId
    ? servicesData.find((s) => s.service_id === selectedServiceId)
    : null;

  if (servicesLoading) {
    return (
      <Profiler id="ProjectServicesTab:loading" onRender={profilerLog}>
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      </Profiler>
    );
  }

  if (servicesError) {
    return (
      <Profiler id="ProjectServicesTab:error" onRender={profilerLog}>
        <Alert severity="error" sx={{ m: 2 }}>
          Failed to load services: {servicesError.message}
        </Alert>
      </Profiler>
    );
  }

  return (
    <Profiler id="ProjectServicesTab" onRender={profilerLog}>
      <Box>
        {/* Header Section */}
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
          mb={2}
        >
          <Typography variant="h6">Project Services</Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenServiceDialog()}
            >
              Add Service
            </Button>
            <Button
              variant="outlined"
              onClick={handleOpenTemplateDialog}
              disabled={fileTemplatesLoading}
            >
              Add From Template
            </Button>
          </Stack>
        </Box>

        {templateFeedback && (
          <Alert
            severity={templateFeedback.severity}
            sx={{ mb: 2 }}
            onClose={() => setTemplateFeedback(null)}
          >
            {templateFeedback.message}
          </Alert>
        )}

        {/* Phase A: Summary Strip (minimal, discreet) */}
        <ServicesSummaryStrip
          totalAgreed={billingSummary.totalAgreed}
          totalBilled={billingSummary.totalBilled}
          totalRemaining={billingSummary.totalRemaining}
          progress={billingSummary.progress}
          isPartialSummary={isPartialSummary}
          formatCurrency={formatCurrency}
          formatPercent={formatPercent}
        />

        {/* Pagination info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {displayRangeText}
          </Typography>
        </Box>

        {/* Phase A: Flat, minimal table */}
        <TableContainer component={Paper} sx={{ boxShadow: 'none', border: '1px solid', borderColor: 'divider' }}>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'transparent' }}>
                <TableCell sx={{ fontWeight: 600 }}>Service</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Phase</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Agreed Fee</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Billed</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Remaining</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Progress</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedServices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 3 }}>
                      No services added yet. Use "Add Service" to create one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedServices.map((service) => (
                  <ServicesListRow
                    key={service.service_id}
                    service={service}
                    onRowClick={handleServiceRowClick}
                    onEditService={handleOpenServiceDialog}
                    onDeleteService={handleDeleteService}
                    formatCurrency={formatCurrency}
                    formatPercent={formatPercent}
                    getStatusColor={getStatusColor}
                    data-testid={`service-row-${service.service_id}`}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={totalServices}
          page={servicesPage}
          onPageChange={handleChangeServicesPage}
          rowsPerPage={servicesRowsPerPage}
          onRowsPerPageChange={handleChangeServicesRowsPerPage}
          rowsPerPageOptions={rowsPerPageOptions}
        />

        {/* Phase B: Service Detail Drawer */}
        {selectedServiceFromDrawer && (
          <ServiceDetailDrawer
            open={isDrawerOpen}
            service={selectedServiceFromDrawer}
            projectId={projectId}
            onClose={handleCloseDrawer}
            onEditService={handleOpenServiceDialog}
            onDeleteService={handleDeleteService}
            onAddReview={handleAddReview}
            onEditReview={handleEditReview}
            onDeleteReview={handleDeleteReview}
            onAddItem={handleOpenItemDialog}
            onEditItem={handleOpenItemDialog}
            onDeleteItem={handleDeleteItem}
            formatCurrency={formatCurrency}
            formatPercent={formatPercent}
            getStatusColor={getStatusColor}
          />
        )}

        {/* ===== DIALOGS ===== */}

        {/* Apply Template Dialog */}
        <Dialog open={templateDialogOpen} onClose={handleCloseTemplateDialog} maxWidth="sm" fullWidth>
          <DialogTitle>Apply Service Template</DialogTitle>
          <DialogContent dividers>
            {templateDialogError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setTemplateDialogError('')}>
                {templateDialogError}
              </Alert>
            )}
            {fileTemplatesLoading ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress size={24} />
              </Box>
            ) : fileTemplateOptions.length === 0 ? (
              <Alert severity="info">
                No file-based templates available. Create one in Settings → Service Templates.
              </Alert>
            ) : (
              <Stack spacing={2} mt={1}>
                <TextField
                  select
                  fullWidth
                  label="Template"
                  value={templateSelection.templateName}
                  onChange={(e) =>
                    setTemplateSelection((prev) => ({
                      ...prev,
                      templateName: e.target.value,
                    }))
                  }
                  required
                >
                  {fileTemplateOptions.map((template) => (
                    <MenuItem key={template.key} value={template.name}>
                      {template.name}
                    </MenuItem>
                  ))}
                </TextField>
                <FormControlLabel
                  control={(
                    <Checkbox
                      checked={templateSelection.replaceExisting}
                      onChange={(e) =>
                        setTemplateSelection((prev) => ({
                          ...prev,
                          replaceExisting: e.target.checked,
                        }))
                      }
                    />
                  )}
                  label="Replace existing services for this project"
                />
                <Typography variant="body2" color="text.secondary">
                  When unchecked, the template will add new services and skip any duplicates that already exist.
                </Typography>
              </Stack>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseTemplateDialog}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleApplyTemplate}
              disabled={
                applyTemplateMutation.isPending ||
                fileTemplatesLoading ||
                fileTemplateOptions.length === 0
              }
            >
              {applyTemplateMutation.isPending ? 'Applying...' : 'Apply Template'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Service Dialog */}
        <Dialog open={serviceDialogOpen} onClose={handleCloseServiceDialog} maxWidth="md" fullWidth>
          <DialogTitle>
            {selectedService ? 'Edit Service' : 'Create Service'}
          </DialogTitle>
          <DialogContent>
            <Box component="form" sx={{ mt: 2 }}>
              <TextField
                fullWidth
                label="Service Code"
                value={serviceFormData.service_code}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, service_code: e.target.value }))}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Service Name"
                value={serviceFormData.service_name}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, service_name: e.target.value }))}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Phase"
                value={serviceFormData.phase}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, phase: e.target.value }))}
                margin="normal"
              />
              <TextField
                fullWidth
                select
                label="Bill Rule"
                value={serviceFormData.bill_rule}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, bill_rule: e.target.value }))}
                margin="normal"
              >
                {BILL_RULES.map((rule) => (
                  <MenuItem key={rule} value={rule}>
                    {rule}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                fullWidth
                type="number"
                label="Agreed Fee"
                value={serviceFormData.agreed_fee}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, agreed_fee: parseFloat(e.target.value) || 0 }))}
                margin="normal"
              />
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                value={serviceFormData.notes}
                onChange={(e) => setServiceFormData(prev => ({ ...prev, notes: e.target.value }))}
                margin="normal"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseServiceDialog}>Cancel</Button>
            <Button
              onClick={handleServiceSubmit}
              variant="contained"
              disabled={createServiceMutation.isPending || updateServiceMutation.isPending}
            >
              {createServiceMutation.isPending || updateServiceMutation.isPending ? (
                <CircularProgress size={20} />
              ) : (
                selectedService ? 'Update' : 'Create'
              )}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Review Dialog */}
        <Dialog open={reviewDialogOpen} onClose={handleCloseReviewDialog} maxWidth="md" fullWidth>
          <DialogTitle>
            {selectedReview ? `Edit Review for ${selectedService?.service_name}` : `Add Review for ${selectedService?.service_name}`}
          </DialogTitle>
          <DialogContent>
            <Box component="form" sx={{ mt: 2 }}>
              <TextField
                fullWidth
                type="number"
                label="Cycle Number"
                value={reviewFormData.cycle_no}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, cycle_no: parseInt(e.target.value) || 1 }))}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                type="date"
                label="Planned Date"
                value={reviewFormData.planned_date}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, planned_date: e.target.value }))}
                margin="normal"
                required
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                type="date"
                label="Due Date"
                value={reviewFormData.due_date}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, due_date: e.target.value }))}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                select
                label="Status"
                value={reviewFormData.status}
                onChange={(e) => {
                  const nextStatus = e.target.value;
                  setReviewFormData(prev => ({
                    ...prev,
                    status: nextStatus,
                    is_billed: nextStatus === 'completed'
                      ? true
                      : (prev.status === 'completed' ? false : prev.is_billed),
                  }));
                }}
                margin="normal"
              >
                {REVIEW_STATUSES.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </TextField>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={reviewFormData.is_billed}
                    onChange={(e) =>
                      setReviewFormData(prev => ({
                        ...prev,
                        is_billed: e.target.checked,
                      }))
                    }
                  />
                }
                label="Count this review as billed"
                sx={{ mt: 1 }}
              />
              <TextField
                fullWidth
                type="number"
                label="Weight Factor"
                value={reviewFormData.weight_factor}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, weight_factor: parseFloat(e.target.value) || 1.0 }))}
                margin="normal"
                inputProps={{ step: 0.1 }}
              />
              <TextField
                fullWidth
                label="Disciplines"
                value={reviewFormData.disciplines}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, disciplines: e.target.value }))}
                margin="normal"
              />
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Deliverables"
                value={reviewFormData.deliverables}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, deliverables: e.target.value }))}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Invoice Reference or Folder Link"
                value={reviewFormData.invoice_reference}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, invoice_reference: e.target.value }))}
                margin="normal"
                helperText="Add an invoice number or a shared folder URL so the billing trail stays accessible."
              />
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Evidence Links"
                value={reviewFormData.evidence_links}
                onChange={(e) => setReviewFormData(prev => ({ ...prev, evidence_links: e.target.value }))}
                margin="normal"
                placeholder="https://..."
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseReviewDialog}>Cancel</Button>
            <Button
              onClick={handleReviewSubmit}
              variant="contained"
              disabled={createReviewMutation.isPending || updateReviewMutation.isPending}
            >
              {createReviewMutation.isPending || updateReviewMutation.isPending ? (
                <CircularProgress size={20} />
              ) : (
                selectedReview ? 'Update Review' : 'Create Review'
              )}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Item Dialog */}
        <Dialog open={itemDialogOpen} onClose={handleCloseItemDialog} maxWidth="md" fullWidth>
          <DialogTitle>
            {selectedItem ? `Edit Item for ${selectedService?.service_name}` : `Add Item for ${selectedService?.service_name}`}
          </DialogTitle>
          <DialogContent>
            <Box component="form" sx={{ mt: 2 }}>
              <TextField
                fullWidth
                select
                label="Item Type"
                value={itemFormData.item_type}
                onChange={(e) => setItemFormData(prev => ({ ...prev, item_type: e.target.value }))}
                margin="normal"
              >
                {ITEM_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                fullWidth
                label="Title"
                value={itemFormData.title}
                onChange={(e) => setItemFormData(prev => ({ ...prev, title: e.target.value }))}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Description"
                value={itemFormData.description}
                onChange={(e) => setItemFormData(prev => ({ ...prev, description: e.target.value }))}
                margin="normal"
              />
              <TextField
                fullWidth
                type="date"
                label="Planned Date"
                value={itemFormData.planned_date}
                onChange={(e) => setItemFormData(prev => ({ ...prev, planned_date: e.target.value }))}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                type="date"
                label="Due Date"
                value={itemFormData.due_date}
                onChange={(e) => setItemFormData(prev => ({ ...prev, due_date: e.target.value }))}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                select
                label="Status"
                value={itemFormData.status}
                onChange={(e) => {
                  const nextStatus = e.target.value;
                  setItemFormData(prev => ({
                    ...prev,
                    status: nextStatus,
                    is_billed: nextStatus === 'completed'
                      ? true
                      : (prev.status === 'completed' ? false : prev.is_billed),
                  }));
                }}
                margin="normal"
              >
                {ITEM_STATUSES.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </TextField>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={itemFormData.is_billed}
                    onChange={(e) =>
                      setItemFormData(prev => ({
                        ...prev,
                        is_billed: e.target.checked,
                      }))
                    }
                  />
                }
                label="Count this item as billed"
                sx={{ mt: 1 }}
              />
              <TextField
                fullWidth
                select
                label="Priority"
                value={itemFormData.priority}
                onChange={(e) => setItemFormData(prev => ({ ...prev, priority: e.target.value }))}
                margin="normal"
              >
                {ITEM_PRIORITIES.map((priority) => (
                  <MenuItem key={priority} value={priority}>
                    {priority}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                fullWidth
                label="Invoice Reference or Folder Link"
                value={itemFormData.invoice_reference}
                onChange={(e) => setItemFormData(prev => ({ ...prev, invoice_reference: e.target.value }))}
                margin="normal"
                helperText="Add an invoice number or a shared folder URL to keep billing context with the item."
              />
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Evidence Links"
                value={itemFormData.evidence_links}
                onChange={(e) => setItemFormData(prev => ({ ...prev, evidence_links: e.target.value }))}
                margin="normal"
                placeholder="https://..."
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseItemDialog}>Cancel</Button>
            <Button
              onClick={handleItemSubmit}
              variant="contained"
              disabled={createItemMutation.isPending || updateItemMutation.isPending}
            >
              {createItemMutation.isPending || updateItemMutation.isPending ? (
                <CircularProgress size={20} />
              ) : (
                selectedItem ? 'Update Item' : 'Create Item'
              )}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Item Detail Modal (Anchor Links) - DISABLED FOR NOW */}
        {/*
        {featureFlags.anchorLinks && selectedItemId !== null && (
          <Dialog
            open={isItemDetailOpen}
            onClose={() => {
              setIsItemDetailOpen(false);
              setSelectedItemId(null);
            }}
            maxWidth="md"
            fullWidth
            data-testid="project-services-tab-item-detail-modal"
          >
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Linked Issues - Item #{selectedItemId}</Typography>
              <IconButton
                onClick={() => {
                  setIsItemDetailOpen(false);
                  setSelectedItemId(null);
                }}
                size="small"
              >
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers sx={{ minHeight: '400px' }}>
              <LinkedIssuesList
                projectId={projectId}
                anchorType="item"
                anchorId={selectedItemId}
                enabled={isItemDetailOpen && selectedItemId !== null}
                readonly={false}
                data-testid="project-services-tab-item-linked-issues"
              />
            </DialogContent>
            <DialogActions>
              <Button
                onClick={() => {
                  setIsItemDetailOpen(false);
                  setSelectedItemId(null);
                }}
              >
                Close
              </Button>
            </DialogActions>
          </Dialog>
        )}
        */}
      </Box>
    </Profiler>
  );
}
