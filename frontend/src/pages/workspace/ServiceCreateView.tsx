/**
 * Service Create View
 *
 * Full-screen form for creating a new service.
 * Supports blank services and template-driven creation.
 */

import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { useNavigate, useOutletContext, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectServicesApi, serviceTemplateCatalogApi, usersApi } from '@/api';
import type { Project } from '@/types/api';
import type { ServiceTemplateCatalogResponse, ServiceTemplateDefinition, User } from '@/types/api';

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const formatBillRuleLabel = (value: string) =>
  value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

type OutletContext = {
  projectId: number;
  project: Project | null;
};

export default function ServiceCreateView() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { projectId } = useOutletContext<OutletContext>();
  const [searchParams, setSearchParams] = useSearchParams();

  const mode = searchParams.get('mode') === 'template' ? 'template' : 'blank';

  const [formData, setFormData] = useState({
    service_code: '',
    service_name: '',
    phase: '',
    unit_type: '',
    unit_qty: '',
    unit_rate: '',
    lump_sum_fee: '',
    agreed_fee: '',
    bill_rule: '',
    notes: '',
    assigned_user_id: '' as number | '',
  });

  const [templateId, setTemplateId] = useState('');
  const [optionsEnabled, setOptionsEnabled] = useState<string[]>([]);
  const [templateOverrides, setTemplateOverrides] = useState({
    service_code: '',
    service_name: '',
    phase: '',
    assigned_user_id: '' as number | '',
    agreed_fee: '' as number | '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data: users = [] } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  const { data: templateCatalog } = useQuery({
    queryKey: ['serviceTemplateCatalog'],
    queryFn: async () => {
      const response = await serviceTemplateCatalogApi.getAll();
      return response.data as ServiceTemplateCatalogResponse;
    },
  });

  const templates = templateCatalog?.templates ?? [];
  const catalog = templateCatalog?.catalog;

  const selectedTemplate = useMemo<ServiceTemplateDefinition | null>(() => {
    return templates.find((template) => template.template_id === templateId) ?? null;
  }, [templates, templateId]);

  const pricingSummary = useMemo(() => {
    if (!selectedTemplate?.pricing) {
      return null;
    }
    const pricing = selectedTemplate.pricing;
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
  }, [selectedTemplate]);

  useEffect(() => {
    if (mode !== 'template') {
      return;
    }
    if (templates.length && !templateId) {
      setTemplateId(templates[0].template_id);
    }
  }, [mode, templates, templateId]);

  useEffect(() => {
    if (!selectedTemplate) {
      return;
    }
    const defaults = selectedTemplate.defaults || {};
    setTemplateOverrides({
      service_code: defaults.service_code || '',
      service_name: defaults.service_name || '',
      phase: defaults.phase || '',
      assigned_user_id: defaults.assigned_user_id ?? '',
      agreed_fee: defaults.agreed_fee ?? '',
    });
    setOptionsEnabled([]);
  }, [selectedTemplate]);

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => {
      const payload = {
        service_code: data.service_code,
        service_name: data.service_name,
        phase: data.phase || undefined,
        unit_type: data.unit_type || undefined,
        unit_qty: data.unit_qty ? Number(data.unit_qty) : undefined,
        unit_rate: data.unit_rate ? Number(data.unit_rate) : undefined,
        lump_sum_fee: data.lump_sum_fee ? Number(data.lump_sum_fee) : undefined,
        agreed_fee: data.agreed_fee ? Number(data.agreed_fee) : undefined,
        bill_rule: data.bill_rule || undefined,
        notes: data.notes || undefined,
        assigned_user_id: data.assigned_user_id === '' ? undefined : data.assigned_user_id,
      };
      return projectServicesApi.create(projectId, payload);
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      const serviceId = response.data?.service_id;
      if (serviceId) {
        navigate(`/projects/${projectId}/workspace/services?sel=service:${serviceId}`);
      } else {
        navigate(`/projects/${projectId}/workspace/services`);
      }
    },
  });

  const createFromTemplateMutation = useMutation({
    mutationFn: () => {
      if (!templateId) {
        throw new Error('Select a template to continue.');
      }
      return projectServicesApi.createFromTemplate(projectId, {
        template_id: templateId,
        options_enabled: optionsEnabled,
        overrides: {
          service_code: templateOverrides.service_code || undefined,
          service_name: templateOverrides.service_name || undefined,
          phase: templateOverrides.phase || undefined,
          assigned_user_id: templateOverrides.assigned_user_id === ''
            ? undefined
            : Number(templateOverrides.assigned_user_id),
          agreed_fee: templateOverrides.agreed_fee === ''
            ? undefined
            : Number(templateOverrides.agreed_fee),
        },
      });
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      const serviceId = response.data?.service_id;
      if (serviceId) {
        navigate(`/projects/${projectId}/workspace/services?sel=service:${serviceId}`);
      } else {
        navigate(`/projects/${projectId}/workspace/services`);
      }
    },
  });

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (mode === 'blank') {
      if (!formData.service_code.trim()) {
        newErrors.service_code = 'Service code is required';
      }
      if (!formData.service_name.trim()) {
        newErrors.service_name = 'Service name is required';
      }
    } else {
      if (!templateOverrides.service_code.trim()) {
        newErrors.service_code = 'Service code is required';
      }
      if (!templateOverrides.service_name.trim()) {
        newErrors.service_name = 'Service name is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) {
      return;
    }
    if (mode === 'template') {
      createFromTemplateMutation.mutate();
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: event.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const handleModeChange = (nextMode: 'blank' | 'template') => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (nextMode === 'template') {
        next.set('mode', 'template');
      } else {
        next.delete('mode');
      }
      return next;
    });
  };

  return (
    <Box data-testid="workspace-service-create-view">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/projects/${projectId}/workspace/services`)}
        >
          Back
        </Button>
        <Typography variant="h6">Create New Service</Typography>
      </Box>

      {(createMutation.isError || createFromTemplateMutation.isError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to create service. Please try again.
        </Alert>
      )}

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={3} component="form" onSubmit={handleSubmit}>
          <FormControl fullWidth>
            <InputLabel id="service-create-mode-label">Creation Mode</InputLabel>
            <Select
              labelId="service-create-mode-label"
              label="Creation Mode"
              value={mode}
              onChange={(event) => handleModeChange(event.target.value as 'blank' | 'template')}
            >
              <MenuItem value="blank">Blank Service</MenuItem>
              <MenuItem value="template">From Template</MenuItem>
            </Select>
          </FormControl>

          {mode === 'template' ? (
            <Stack spacing={2}>
              <TextField
                select
                fullWidth
                label="Template"
                value={templateId}
                onChange={(event) => setTemplateId(event.target.value)}
                required
              >
                {templates.map((template) => (
                  <MenuItem key={template.template_id} value={template.template_id}>
                    {template.name}
                  </MenuItem>
                ))}
              </TextField>

              {pricingSummary && (
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Pricing Summary
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {pricingSummary}
                  </Typography>
                </Paper>
              )}

              {selectedTemplate?.options?.length ? (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    Optional scope
                  </Typography>
                  <Stack spacing={1}>
                    {selectedTemplate.options.map((option) => (
                      <FormControlLabel
                        key={option.option_id}
                        control={(
                          <Checkbox
                            checked={optionsEnabled.includes(option.option_id)}
                            onChange={() =>
                              setOptionsEnabled((prev) =>
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

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                  Template Defaults (editable)
                </Typography>
                <Stack spacing={2}>
                  <TextField
                    fullWidth
                    required
                    label="Service Code"
                    value={templateOverrides.service_code}
                    onChange={(event) =>
                      setTemplateOverrides((prev) => ({ ...prev, service_code: event.target.value }))
                    }
                    error={!!errors.service_code}
                    helperText={errors.service_code}
                  />
                  <TextField
                    fullWidth
                    required
                    label="Service Name"
                    value={templateOverrides.service_name}
                    onChange={(event) =>
                      setTemplateOverrides((prev) => ({ ...prev, service_name: event.target.value }))
                    }
                    error={!!errors.service_name}
                    helperText={errors.service_name}
                  />
                  <TextField
                    fullWidth
                    select
                    label="Phase"
                    value={templateOverrides.phase}
                    onChange={(event) =>
                      setTemplateOverrides((prev) => ({ ...prev, phase: event.target.value }))
                    }
                  >
                    <MenuItem value="">None</MenuItem>
                    {catalog?.phases?.map((phase) => (
                      <MenuItem key={phase} value={phase}>
                        {phase}
                      </MenuItem>
                    ))}
                  </TextField>

                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="body2">Additional overrides</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Stack spacing={2}>
                        <FormControl fullWidth>
                          <InputLabel id="service-template-assignee-label">Assigned User</InputLabel>
                          <Select
                            labelId="service-template-assignee-label"
                            label="Assigned User"
                            value={templateOverrides.assigned_user_id}
                            onChange={(event) =>
                              setTemplateOverrides((prev) => ({
                                ...prev,
                                assigned_user_id: event.target.value === '' ? '' : Number(event.target.value),
                              }))
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
                          fullWidth
                          type="number"
                          label="Agreed Fee Override"
                          value={templateOverrides.agreed_fee}
                          onChange={(event) =>
                            setTemplateOverrides((prev) => ({
                              ...prev,
                              agreed_fee: event.target.value === '' ? '' : Number(event.target.value),
                            }))
                          }
                        />
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                </Stack>
              </Paper>
            </Stack>
          ) : (
            <Stack spacing={2}>
              <TextField
                fullWidth
                required
                label="Service Code"
                value={formData.service_code}
                onChange={handleChange('service_code')}
                error={!!errors.service_code}
                helperText={errors.service_code}
                placeholder="e.g., D.01"
              />
              <TextField
                fullWidth
                required
                label="Service Name"
                value={formData.service_name}
                onChange={handleChange('service_name')}
                error={!!errors.service_name}
                helperText={errors.service_name}
                placeholder="e.g., Design Development"
              />
              <TextField
                fullWidth
                label="Phase"
                value={formData.phase}
                onChange={handleChange('phase')}
              />
              <FormControl fullWidth>
                <InputLabel id="service-create-assignee-label">Assigned User</InputLabel>
                <Select
                  labelId="service-create-assignee-label"
                  label="Assigned User"
                  value={formData.assigned_user_id}
                  onChange={(event) =>
                    setFormData((prev) => ({
                      ...prev,
                      assigned_user_id: event.target.value === '' ? '' : Number(event.target.value),
                    }))
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
                fullWidth
                select
                label="Billing Rule"
                value={formData.bill_rule}
                onChange={handleChange('bill_rule')}
              >
                <MenuItem value="">None</MenuItem>
                {catalog?.bill_rules?.map((rule) => (
                  <MenuItem key={rule} value={rule}>
                    {formatBillRuleLabel(rule)}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                fullWidth
                label="Unit Type"
                value={formData.unit_type}
                onChange={handleChange('unit_type')}
              />
              <TextField
                fullWidth
                type="number"
                label="Unit Quantity"
                value={formData.unit_qty}
                onChange={handleChange('unit_qty')}
              />
              <TextField
                fullWidth
                type="number"
                label="Unit Rate"
                value={formData.unit_rate}
                onChange={handleChange('unit_rate')}
              />
              <TextField
                fullWidth
                type="number"
                label="Lump Sum Fee"
                value={formData.lump_sum_fee}
                onChange={handleChange('lump_sum_fee')}
              />
              <TextField
                fullWidth
                type="number"
                label="Agreed Fee"
                value={formData.agreed_fee}
                onChange={handleChange('agreed_fee')}
              />
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                value={formData.notes}
                onChange={handleChange('notes')}
              />
            </Stack>
          )}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate(`/projects/${projectId}/workspace/services`)}
              disabled={createMutation.isPending || createFromTemplateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending || createFromTemplateMutation.isPending}
            >
              {createMutation.isPending || createFromTemplateMutation.isPending
                ? 'Creating...'
                : 'Create Service'}
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}
