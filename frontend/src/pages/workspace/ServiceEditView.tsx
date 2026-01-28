/**
 * Service Edit View
 *
 * Full-page editor for modifying service details including:
 * - Basics, pricing, progress, and template metadata
 */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import { Save as SaveIcon, Cancel as CancelIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { projectServicesApi, serviceItemsApi, serviceReviewsApi, serviceTemplateCatalogApi, usersApi } from '@/api';
import type {
  ProjectService,
  ProjectServicesListResponse,
  GeneratedServiceStructure,
  ServiceItem,
  ServiceReview,
  ServiceTemplateItemDefinition,
  ServiceTemplateResyncResult,
  User,
} from '@/types/api';
import type { Project } from '@/types/api';

const SERVICE_STATUS_OPTIONS = ['planned', 'in_progress', 'completed', 'overdue', 'cancelled'];

const formatBillRuleLabel = (value: string) =>
  value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const todayIso = () => new Date().toISOString().slice(0, 10);

type OutletContext = {
  projectId: number;
  project: Project | null;
};

type TemplateItemOption = {
  key: string;
  label: string;
  item: ServiceTemplateItemDefinition;
  optionId: string;
  group: string;
  sortOrder?: number;
};

export default function ServiceEditView() {
  const navigate = useNavigate();
  const { serviceId: serviceIdParam } = useParams();
  const { projectId } = useOutletContext<OutletContext>();
  const serviceId = Number(serviceIdParam);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<Partial<ProjectService>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [templateItemSelection, setTemplateItemSelection] = useState<TemplateItemOption | null>(null);
  const [resyncDialogOpen, setResyncDialogOpen] = useState(false);
  const [resyncMode, setResyncMode] = useState<'sync_missing_only' | 'sync_and_update_managed'>(
    'sync_and_update_managed'
  );
  const [resyncOptions, setResyncOptions] = useState<string[]>([]);
  const [resyncError, setResyncError] = useState<string | null>(null);
  const [resyncPreview, setResyncPreview] = useState<ServiceTemplateResyncResult | null>(null);
  const [resequenceDialogOpen, setResequenceDialogOpen] = useState(false);
  const [resequenceForm, setResequenceForm] = useState({
    anchor_date: '',
    interval_days: '',
    count: '',
  });

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const { data: templateCatalog } = useQuery({
    queryKey: ['serviceTemplateCatalog'],
    queryFn: async () => {
      const response = await serviceTemplateCatalogApi.getAll();
      return response.data;
    },
  });

  const billRules = templateCatalog?.catalog?.bill_rules ?? [];

  const { data: servicesPayload, isLoading, error } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', projectId],
    queryFn: () => projectServicesApi.getAll(projectId),
    enabled: Number.isFinite(projectId),
  });

  const { data: generatedStructure } = useQuery<GeneratedServiceStructure>({
    queryKey: ['serviceGeneratedStructure', projectId, serviceId],
    queryFn: () => projectServicesApi.getGeneratedStructure(projectId, serviceId),
    enabled: Number.isFinite(projectId) && Number.isFinite(serviceId),
  });

  const { data: serviceReviews = [] } = useQuery<ServiceReview[]>({
    queryKey: ['serviceReviews', projectId, serviceId],
    queryFn: async () => {
      const response = await serviceReviewsApi.getAll(projectId, serviceId);
      return response.data;
    },
    enabled: Number.isFinite(projectId) && Number.isFinite(serviceId),
  });

  const activeServiceReviews = useMemo(
    () => serviceReviews.filter((review) => (review.status || '').toLowerCase() !== 'cancelled'),
    [serviceReviews],
  );

  const { data: serviceItems = [] } = useQuery<ServiceItem[]>({
    queryKey: ['serviceItems', projectId, serviceId],
    queryFn: async () => {
      const response = await serviceItemsApi.getAll(projectId, serviceId);
      return response.data;
    },
    enabled: Number.isFinite(projectId) && Number.isFinite(serviceId),
  });

  const service = useMemo(() => {
    if (!servicesPayload) return null;

    let servicesList: ProjectService[] = [];
    if (Array.isArray(servicesPayload)) {
      servicesList = servicesPayload;
    } else {
      const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
      servicesList = Array.isArray(items) ? items : [];
    }

    return servicesList.find((s) => s.service_id === serviceId) || null;
  }, [servicesPayload, serviceId]);

  useEffect(() => {
    if (service) {
      setFormData(service);
    }
  }, [service]);

  useEffect(() => {
    if (!service) return;
    setResequenceForm({
      anchor_date: service.review_anchor_date || service.start_date || '',
      interval_days: service.review_interval_days != null ? String(service.review_interval_days) : '',
      count: service.review_count_planned != null ? String(service.review_count_planned) : '',
    });
  }, [service]);

  const templateDefinition = generatedStructure?.template || null;
  const templateBinding = generatedStructure?.binding || null;
  const generatedItems = generatedStructure?.generated_items || [];

  useEffect(() => {
    if (templateBinding?.options_enabled) {
      setResyncOptions(templateBinding.options_enabled);
    } else {
      setResyncOptions([]);
    }
  }, [templateBinding?.options_enabled]);

  const templatePricingSummary = useMemo(() => {
    if (!templateDefinition?.pricing) {
      return null;
    }
    const pricing = templateDefinition.pricing;
    const unitQty = pricing.unit_qty ?? null;
    const unitRate = pricing.unit_rate ?? null;
    const derivedTotal =
      unitQty != null && unitRate != null ? Number(unitQty) * Number(unitRate) : null;
    if (pricing.model === 'per_unit' && unitQty != null && unitRate != null && derivedTotal != null) {
      const derivedLabel = pricing.derive_agreed_fee ? ' (derived)' : '';
      return `${unitQty} x ${formatCurrency(unitRate)} = ${formatCurrency(derivedTotal)}${derivedLabel}`;
    }
    if (pricing.model === 'lump_sum' && pricing.lump_sum_fee != null) {
      return formatCurrency(pricing.lump_sum_fee);
    }
    return null;
  }, [templateDefinition]);

  const existingGeneratedKeys = useMemo(() => {
    return new Set(generatedItems.map((item) => item.generated_key));
  }, [generatedItems]);

  const buildItemKey = (optionId: string, item: ServiceTemplateItemDefinition) => {
    const base = item.item_template_id || item.template_id || 'item';
    if (optionId === 'base') {
      return base;
    }
    return `${optionId}:${base}`;
  };

  const availableTemplateItems = useMemo<TemplateItemOption[]>(() => {
    if (!templateDefinition) return [];

    const options: TemplateItemOption[] = [];
    (templateDefinition.items || []).forEach((item, index) => {
      const key = buildItemKey('base', item);
      options.push({
        key,
        label: item.title,
        item,
        optionId: 'base',
        group: 'Template Items',
        sortOrder: item.sort_order ?? index + 1,
      });
    });

    (templateDefinition.options || []).forEach((option) => {
      (option.items || []).forEach((item, index) => {
        const key = buildItemKey(option.option_id, item);
        options.push({
          key,
          label: `${item.title} (Optional: ${option.name})`,
          item,
          optionId: option.option_id,
          group: `Optional: ${option.name}`,
          sortOrder: item.sort_order ?? index + 1,
        });
      });
    });

    return options;
  }, [templateDefinition, existingGeneratedKeys]);

  const addItemMutation = useMutation({
    mutationFn: async () => {
      const selected = templateItemSelection;
      if (!selected || !templateDefinition) {
        throw new Error('Select a template item to add.');
      }

      return serviceItemsApi.create(projectId, serviceId, {
        item_type: selected.item.item_type,
        title: selected.item.title,
        description: selected.item.description,
        planned_date: selected.item.planned_date || service?.start_date || todayIso(),
        due_date: selected.item.due_date,
        status: selected.item.status || 'planned',
        priority: selected.item.priority || 'medium',
        notes: selected.item.notes,
        project_id: projectId,
        generated_from_template_id: templateDefinition.template_id,
        generated_from_template_version: templateDefinition.version,
        generated_key: selected.key,
        origin: 'template_generated',
        is_template_managed: true,
        sort_order: selected.sortOrder,
      });
    },
    onSuccess: () => {
      setTemplateItemSelection(null);
      queryClient.invalidateQueries({ queryKey: ['serviceGeneratedStructure', projectId, serviceId] });
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, serviceId] });
    },
  });

  const resyncPreviewMutation = useMutation({
    mutationFn: async () => {
      if (!templateDefinition) {
        throw new Error('Template details not available.');
      }
      return projectServicesApi.applyTemplateToService(projectId, serviceId, {
        template_id: templateDefinition.template_id,
        options_enabled: resyncOptions,
        dry_run: true,
        mode: resyncMode,
      });
    },
    onSuccess: (response) => {
      setResyncError(null);
      setResyncPreview(response.data);
    },
    onError: (err: any) => {
      setResyncError(err?.response?.data?.error || 'Failed to load template diff.');
    },
  });

  const resyncApplyMutation = useMutation({
    mutationFn: async () => {
      if (!templateDefinition) {
        throw new Error('Template details not available.');
      }
      return projectServicesApi.applyTemplateToService(projectId, serviceId, {
        template_id: templateDefinition.template_id,
        options_enabled: resyncOptions,
        dry_run: false,
        mode: resyncMode,
      });
    },
    onSuccess: () => {
      setResyncDialogOpen(false);
      setResyncError(null);
      queryClient.invalidateQueries({ queryKey: ['serviceGeneratedStructure', projectId, serviceId] });
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, serviceId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, serviceId] });
    },
    onError: (err: any) => {
      setResyncError(err?.response?.data?.error || 'Failed to re-sync template.');
    },
  });

  const resequenceMutation = useMutation({
    mutationFn: async () => {
      const desiredCount = resequenceForm.count ? Number(resequenceForm.count) : null;
      if (desiredCount !== null) {
        await projectServicesApi.setReviewCount(projectId, serviceId, {
          desired_count: desiredCount,
          anchor_date: resequenceForm.anchor_date || undefined,
          interval_days: resequenceForm.interval_days ? Number(resequenceForm.interval_days) : undefined,
        });
      }
      return projectServicesApi.resequenceReviews(projectId, serviceId, {
        anchor_date: resequenceForm.anchor_date || undefined,
        interval_days: resequenceForm.interval_days ? Number(resequenceForm.interval_days) : undefined,
        count: desiredCount ?? undefined,
        mode: 'update_existing_planned',
      });
    },
    onSuccess: () => {
      setResequenceDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, serviceId] });
    },
    onError: (err: any) => {
      setSaveError(err?.response?.data?.error || 'Failed to resequence reviews');
    },
  });

  const resetReviewsMutation = useMutation({
    mutationFn: async () => {
      const desiredCount = resequenceForm.count ? Number(resequenceForm.count) : null;
      if (desiredCount === null) {
        throw new Error('Enter a planned review count to reset.');
      }
      return projectServicesApi.resetReviews(projectId, serviceId, {
        desired_count: desiredCount,
        anchor_date: resequenceForm.anchor_date || undefined,
        interval_days: resequenceForm.interval_days ? Number(resequenceForm.interval_days) : undefined,
      });
    },
    onSuccess: () => {
      setResequenceDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, serviceId] });
    },
    onError: (err: any) => {
      setSaveError(err?.response?.data?.error || err?.message || 'Failed to reset reviews');
    },
  });

  useEffect(() => {
    if (!resyncDialogOpen || !templateDefinition) {
      return;
    }
    resyncPreviewMutation.mutate();
  }, [resyncDialogOpen, resyncMode, resyncOptions.join('|'), templateDefinition?.template_id]);

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<ProjectService>) => {
      return projectServicesApi.update(projectId, serviceId, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      navigate(`/projects/${projectId}/workspace/services?sel=service:${serviceId}`);
    },
    onError: (err: any) => {
      setSaveError(err?.response?.data?.error || 'Failed to update service');
    },
  });

  const handleChange = (field: keyof ProjectService, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveError(null);
  };

  const handleSave = () => {
    const payload: Partial<ProjectService> = {
      service_code: formData.service_code,
      service_name: formData.service_name,
      notes: formData.notes,
      status: formData.status,
      phase: formData.phase,
      start_date: formData.start_date,
      end_date: formData.end_date,
      unit_type: formData.unit_type,
      unit_qty: formData.unit_qty,
      unit_rate: formData.unit_rate,
      lump_sum_fee: formData.lump_sum_fee,
      bill_rule: formData.bill_rule,
      agreed_fee: formData.agreed_fee,
      assigned_user_id: formData.assigned_user_id,
    };
    updateMutation.mutate(payload);
  };

  const handleCancel = () => {
    navigate(`/projects/${projectId}/workspace/services?sel=service:${serviceId}`);
  };

  const handleOpenResyncDialog = () => {
    setResyncError(null);
    setResyncPreview(null);
    setResyncDialogOpen(true);
  };

  const handleCloseResyncDialog = () => {
    setResyncDialogOpen(false);
    setResyncError(null);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !service) {
    return <Alert severity="error">Failed to load service details.</Alert>;
  }

  return (
    <Box data-testid="service-edit-view">
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">Edit Service: {service.service_code}</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={handleCancel}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>

        {saveError && (
          <Alert severity="error" onClose={() => setSaveError(null)}>
            {saveError}
          </Alert>
        )}

        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={2}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Basics
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  <TextField
                    label="Service Code"
                    value={formData.service_code || ''}
                    onChange={(e) => handleChange('service_code', e.target.value)}
                    fullWidth
                    required
                  />
                  <TextField
                    label="Service Name"
                    value={formData.service_name || ''}
                    onChange={(e) => handleChange('service_name', e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Phase"
                    value={formData.phase || ''}
                    onChange={(e) => handleChange('phase', e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Start Date"
                    type="date"
                    value={formData.start_date || ''}
                    onChange={(e) => handleChange('start_date', e.target.value)}
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                  <TextField
                    label="End Date"
                    type="date"
                    value={formData.end_date || ''}
                    onChange={(e) => handleChange('end_date', e.target.value)}
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                  <TextField
                    select
                    label="Status"
                    value={formData.status || 'planned'}
                    onChange={(e) => handleChange('status', e.target.value)}
                    fullWidth
                  >
                    {SERVICE_STATUS_OPTIONS.map((status) => (
                      <MenuItem key={status} value={status}>
                        {status}
                      </MenuItem>
                    ))}
                  </TextField>
                  <FormControl fullWidth>
                    <InputLabel id="service-edit-assigned-user-label">Assigned User</InputLabel>
                    <Select
                      labelId="service-edit-assigned-user-label"
                      label="Assigned User"
                      value={formData.assigned_user_id ?? ''}
                      onChange={(event) =>
                        handleChange(
                          'assigned_user_id',
                          event.target.value === '' ? null : Number(event.target.value)
                        )
                      }
                    >
                      <MenuItem value="">Unassigned</MenuItem>
                      {users.map((user) => (
                        <MenuItem key={user.user_id} value={user.user_id}>
                          {user.name || user.full_name || user.username || `User ${user.user_id}`}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    label="Notes"
                    value={formData.notes || ''}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    fullWidth
                    multiline
                    rows={3}
                  />
                </Stack>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Progress
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  <TextField
                    label="Progress % (derived)"
                    type="number"
                    value={formData.progress_pct ?? ''}
                    fullWidth
                    disabled
                  />
                  <TextField
                    label="Claimed To Date (derived)"
                    type="number"
                    value={formData.claimed_to_date ?? ''}
                    fullWidth
                    disabled
                  />
                </Stack>
              </AccordionDetails>
            </Accordion>

            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Review Plan (Pricing + Cadence)
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  <Typography variant="body2" color="text.secondary">
                    Define pricing and review schedule as one coherent plan. Changes are calculated in real-time.
                  </Typography>

                  {/* Pricing Inputs */}
                  <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Service Pricing
                    </Typography>
                    <Stack spacing={1.5} sx={{ ml: 1 }}>
                      <TextField
                        label="Agreed Fee (Total)"
                        type="number"
                        value={formData.agreed_fee ?? ''}
                        onChange={(e) => handleChange('agreed_fee', Number(e.target.value) || 0)}
                        fullWidth
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        Total agreed fee for this service across all reviews
                      </Typography>
                    </Stack>
                  </Box>

                  {/* Cadence Inputs */}
                  <Box sx={{ borderBottom: 1, borderColor: 'divider', pb: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Review Schedule
                    </Typography>
                    <Stack spacing={1.5} sx={{ ml: 1 }}>
                      <TextField
                        label="Anchor Date (Start)"
                        type="date"
                        value={resequenceForm.anchor_date || ''}
                        onChange={(e) => setResequenceForm({ ...resequenceForm, anchor_date: e.target.value })}
                        fullWidth
                        size="small"
                        InputLabelProps={{ shrink: true }}
                      />
                      <TextField
                        label="Interval (days)"
                        type="number"
                        value={resequenceForm.interval_days}
                        onChange={(e) => setResequenceForm({ ...resequenceForm, interval_days: e.target.value })}
                        fullWidth
                        size="small"
                      />
                      <TextField
                        label="Planned Review Count"
                        type="number"
                        value={resequenceForm.count}
                        onChange={(e) => setResequenceForm({ ...resequenceForm, count: e.target.value })}
                        fullWidth
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        Number of planned review cycles for this service
                      </Typography>
                    </Stack>
                  </Box>

                  {/* Preview & Calculated Metrics */}
                  <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Calculated Metrics
                    </Typography>
                    <Stack spacing={1} sx={{ ml: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Fee per review:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {(() => {
                            const total = Number(formData.agreed_fee) || 0;
                            const count = Number(resequenceForm.count) || 1;
                            const perReview = total / (count > 0 ? count : 1);
                            return formatCurrency(perReview);
                          })()}
                        </Typography>
                      </Box>
                      {resequenceForm.count && Number(resequenceForm.count) > 0 && (
                        <Box>
                          <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
                            Calculated Review Dates:
                          </Typography>
                          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 0.5 }}>
                            {Array.from({ length: Number(resequenceForm.count) || 0 }).map((_, i) => {
                              if (!resequenceForm.anchor_date || !resequenceForm.interval_days) return null;
                              const baseDate = new Date(resequenceForm.anchor_date);
                              const reviewDate = new Date(baseDate);
                              reviewDate.setDate(reviewDate.getDate() + i * Number(resequenceForm.interval_days));
                              return (
                                <Box
                                  key={i}
                                  sx={{
                                    p: 0.75,
                                    bgcolor: 'background.paper',
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    borderRadius: 0.5,
                                    textAlign: 'center',
                                  }}
                                >
                                  <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                    Review {i + 1}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                    {reviewDate.toLocaleDateString()}
                                  </Typography>
                                </Box>
                              );
                            })}
                          </Box>
                        </Box>
                      )}
                    </Stack>
                  </Box>

                  {/* Action Button */}
                  <Button
                    variant="contained"
                    onClick={() => setResequenceDialogOpen(true)}
                    disabled={resequenceMutation.isPending}
                  >
                    {resequenceMutation.isPending ? 'Applying...' : 'Apply Review Schedule'}
                  </Button>

                  {/* Review List */}
                  {activeServiceReviews.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                        Existing Reviews ({activeServiceReviews.length})
                      </Typography>
                      <Stack spacing={0.5} sx={{ ml: 1, maxHeight: 200, overflow: 'auto' }}>
                        {activeServiceReviews.map((review) => (
                          <Box key={review.review_id} sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <Typography variant="caption" sx={{ minWidth: 80 }}>
                              Cycle #{review.cycle_no}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatDate(review.planned_date)}
                            </Typography>
                            {review.is_user_modified && (
                              <Chip size="small" label="Modified" color="warning" variant="outlined" />
                            )}
                          </Box>
                        ))}
                      </Stack>
                    </Box>
                  )}
                </Stack>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Deliverables (Reviews)
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  {activeServiceReviews.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
                      No reviews yet. Use the Review Plan section above to set up your review schedule.
                    </Typography>
                  ) : (
                    <Stack spacing={1}>
                      {activeServiceReviews.map((review) => (
                        <Box
                          key={review.review_id}
                          sx={{ border: '1px solid', borderColor: 'divider', p: 1, borderRadius: 1 }}
                        >
                          <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              Cycle #{review.cycle_no}
                            </Typography>
                            <Stack direction="row" spacing={1}>
                              {review.is_template_managed && <Chip size="small" label="Template" />}
                              {review.is_user_modified && <Chip size="small" color="warning" label="User-modified" />}
                              <Chip size="small" label={review.status || 'planned'} />
                            </Stack>
                          </Stack>
                          <Typography variant="caption" color="text.secondary">
                            Planned: {formatDate(review.planned_date)} · Due: {formatDate(review.due_date)}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  )}
                </Stack>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Items
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {serviceItems.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No items yet.
                  </Typography>
                ) : (
                  <Stack spacing={1}>
                    {serviceItems.map((item) => (
                      <Box
                        key={item.item_id}
                        sx={{ border: '1px solid', borderColor: 'divider', p: 1, borderRadius: 1 }}
                      >
                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {item.title}
                          </Typography>
                          <Stack direction="row" spacing={1}>
                            {item.is_template_managed && <Chip size="small" label="Template" />}
                            {item.is_user_modified && <Chip size="small" color="warning" label="User-modified" />}
                            <Chip size="small" label={item.status || 'planned'} />
                          </Stack>
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          Planned: {formatDate(item.planned_date)} · Due: {formatDate(item.due_date)}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                )}
              </AccordionDetails>
            </Accordion>

            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Template
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {templateDefinition && templateBinding ? (
                  <Stack spacing={2}>
                    <Stack spacing={1}>
                      <Typography variant="body2">
                        Template: {templateDefinition.name} (v{templateDefinition.version})
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Applied: {formatDate(templateBinding.applied_at)}
                      </Typography>
                      {templatePricingSummary && (
                        <Typography variant="caption" color="text.secondary">
                          Pricing: {templatePricingSummary}
                        </Typography>
                      )}
                      {templateBinding.options_enabled?.length ? (
                        <Typography variant="caption" color="text.secondary">
                          Options: {templateBinding.options_enabled.join(', ')}
                        </Typography>
                      ) : null}
                    </Stack>

                    <Button
                      variant="contained"
                      onClick={handleOpenResyncDialog}
                      disabled={resyncPreviewMutation.isPending || resyncApplyMutation.isPending}
                      data-testid="service-template-resync-button"
                    >
                      Re-sync Template
                    </Button>

                    <Autocomplete
                      options={availableTemplateItems}
                      groupBy={(option) => option.group}
                      getOptionLabel={(option) => option.label}
                      value={templateItemSelection}
                      onChange={(_event, value) => setTemplateItemSelection(value)}
                      getOptionDisabled={(option) => existingGeneratedKeys.has(option.key)}
                      renderOption={(props, option) => {
                        const disabled = existingGeneratedKeys.has(option.key);
                        return (
                          <li {...props} aria-disabled={disabled}>
                            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                              <Typography variant="body2">{option.label}</Typography>
                              {disabled && (
                                <Typography variant="caption" color="text.secondary">
                                  Already added
                                </Typography>
                              )}
                            </Box>
                          </li>
                        );
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Add Item From Template / Catalog"
                          placeholder="Search items"
                        />
                      )}
                      noOptionsText="No template items available"
                    />

                    <Button
                      variant="outlined"
                      onClick={() => addItemMutation.mutate()}
                      disabled={!templateItemSelection || addItemMutation.isPending}
                    >
                      {addItemMutation.isPending ? 'Adding...' : 'Add Item'}
                    </Button>

                    {addItemMutation.isError && (
                      <Alert severity="error">
                        {addItemMutation.error instanceof Error
                          ? addItemMutation.error.message
                          : 'Failed to add item.'}
                      </Alert>
                    )}

                    <Stack spacing={1}>
                      <Typography variant="subtitle2">Generated Items</Typography>
                      {generatedItems.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          No generated items yet.
                        </Typography>
                      ) : (
                        generatedItems.map((item) => (
                          <Box key={item.generated_key} sx={{ border: '1px solid', borderColor: 'divider', p: 1, borderRadius: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {item.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.generated_key} {item.item_type ? `- ${item.item_type}` : ''}
                            </Typography>
                          </Box>
                        ))
                      )}
                    </Stack>
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    This service is not bound to a template.
                  </Typography>
                )}
              </AccordionDetails>
            </Accordion>
          </Stack>
        </Paper>
      </Stack>

      <Dialog
        open={resyncDialogOpen}
        onClose={handleCloseResyncDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Re-sync Template</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {resyncError && (
            <Alert severity="error" onClose={() => setResyncError(null)}>
              {resyncError}
            </Alert>
          )}

          {templateDefinition?.options?.length ? (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Enabled options
              </Typography>
              <Stack spacing={1}>
                {templateDefinition.options.map((option) => (
                  <FormControlLabel
                    key={option.option_id}
                    control={(
                      <Checkbox
                        checked={resyncOptions.includes(option.option_id)}
                        onChange={() =>
                          setResyncOptions((prev) =>
                            prev.includes(option.option_id)
                              ? prev.filter((id) => id !== option.option_id)
                              : [...prev, option.option_id]
                          )
                        }
                      />
                    )}
                    label={option.name}
                  />
                ))}
              </Stack>
            </Box>
          ) : null}

          <FormControl fullWidth>
            <InputLabel id="resync-mode-label">Re-sync mode</InputLabel>
            <Select
              labelId="resync-mode-label"
              label="Re-sync mode"
              value={resyncMode}
              onChange={(event) =>
                setResyncMode(event.target.value as 'sync_missing_only' | 'sync_and_update_managed')
              }
            >
              <MenuItem value="sync_missing_only">Sync missing only</MenuItem>
              <MenuItem value="sync_and_update_managed">Sync and update managed</MenuItem>
            </Select>
          </FormControl>

          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Diff preview
            </Typography>
            {resyncPreviewMutation.isPending ? (
              <Typography variant="body2" color="text.secondary">
                Loading diff...
              </Typography>
            ) : resyncPreview ? (
              <Stack spacing={1}>
                <Typography variant="body2">
                  Reviews: +{resyncPreview.added_reviews.length} / updated {resyncPreview.updated_reviews.length} / skipped {resyncPreview.skipped_reviews.length}
                </Typography>
                <Typography variant="body2">
                  Items: +{resyncPreview.added_items.length} / updated {resyncPreview.updated_items.length} / skipped {resyncPreview.skipped_items.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Updates only apply to planned, template-managed, and unmodified rows. No deletions are performed.
                </Typography>
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No preview available.
              </Typography>
            )}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseResyncDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => resyncApplyMutation.mutate()}
            disabled={resyncApplyMutation.isPending || resyncPreviewMutation.isPending}
          >
            {resyncApplyMutation.isPending ? 'Re-syncing...' : 'Apply Re-sync'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={resequenceDialogOpen}
        onClose={() => setResequenceDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Re-sequence planned reviews</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Only planned reviews that are not user-modified will be updated.
          </Typography>
          <TextField
            label="Anchor date"
            type="date"
            value={resequenceForm.anchor_date}
            onChange={(event) =>
              setResequenceForm((prev) => ({ ...prev, anchor_date: event.target.value }))
            }
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Interval (days)"
            type="number"
            value={resequenceForm.interval_days}
            onChange={(event) =>
              setResequenceForm((prev) => ({ ...prev, interval_days: event.target.value }))
            }
          />
          <TextField
            label="Count (optional)"
            type="number"
            value={resequenceForm.count}
            onChange={(event) =>
              setResequenceForm((prev) => ({ ...prev, count: event.target.value }))
            }
            helperText="Leave blank to resequence existing planned reviews. If set, extra planned reviews will be cancelled and missing ones added."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResequenceDialogOpen(false)}>Cancel</Button>
          <Button
            color="warning"
            variant="outlined"
            onClick={() => {
              setSaveError(null);
              if (!resequenceForm.count) {
                setSaveError('Enter a planned review count before resetting.');
                return;
              }
              if (!window.confirm('Reset planned reviews? This will cancel all planned reviews and recreate a clean schedule.')) {
                return;
              }
              resetReviewsMutation.mutate();
            }}
            disabled={resetReviewsMutation.isPending}
          >
            {resetReviewsMutation.isPending ? 'Resetting...' : 'Reset Planned Reviews'}
          </Button>
          <Button
            variant="contained"
            onClick={() => resequenceMutation.mutate()}
            disabled={resequenceMutation.isPending}
          >
            {resequenceMutation.isPending ? 'Re-sequencing...' : 'Apply'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
