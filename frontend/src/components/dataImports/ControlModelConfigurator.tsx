import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  LinearProgress,
  Paper,
  Radio,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  CheckCircleOutline as ReadyIcon,
  WarningAmber as WarningIcon,
  Layers as LayersIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { controlModelsApi } from '@/api/dataImports';
import type {
  ControlModelConfiguration,
  ControlModelInput,
  ValidationTarget,
} from '@/types/dataImports';

const VALIDATION_TARGETS: ValidationTarget[] = ['naming', 'coordinates', 'levels'];
const DEFAULT_TARGETS: ValidationTarget[] = ['naming', 'coordinates', 'levels'];

interface ControlModelConfiguratorProps {
  projectId: number;
  projectName?: string;
}

interface EditableControlModel {
  fileName: string;
  validationTargets: ValidationTarget[];
  volumeLabel: string;
  notes: string;
  isPrimary: boolean;
  zoneCode: string;
}

const sanitiseTargets = (targets?: ValidationTarget[]): ValidationTarget[] => {
  if (!targets || !targets.length) {
    return [...DEFAULT_TARGETS];
  }
  const unique: ValidationTarget[] = [];
  targets.forEach((target) => {
    const normalised = target.toLowerCase() as ValidationTarget;
    if (VALIDATION_TARGETS.includes(normalised) && !unique.includes(normalised)) {
      unique.push(normalised);
    }
  });
  return unique.length ? unique : [...DEFAULT_TARGETS];
};

const deriveZoneCode = (fileName: string): string => {
  if (!fileName) {
    return '';
  }
  const normalised = fileName.replace(/\[.*?\]$/, '').replace(/\.rvt$/i, '');
  const parts = normalised.split(/[-_]/).filter(Boolean);
  if (parts.length >= 3) {
    return parts[2].toUpperCase();
  }
  return '';
};

const toEditableModels = (config: ControlModelConfiguration): EditableControlModel[] => {
  const active = config.control_models.filter((model) => model.is_active);
  if (!active.length) {
    return [];
  }
  return active.map((model) => ({
    fileName: model.file_name,
    validationTargets: sanitiseTargets(model.metadata?.validation_targets as ValidationTarget[]),
    volumeLabel: model.metadata?.volume_label ?? '',
    notes: model.metadata?.notes ?? '',
    isPrimary: Boolean(model.metadata?.is_primary),
    zoneCode: (model.metadata?.zone_code as string | undefined) ?? deriveZoneCode(model.file_name),
  }));
};

export const ControlModelConfigurator: React.FC<ControlModelConfiguratorProps> = ({
  projectId,
  projectName,
}) => {
  const queryClient = useQueryClient();
  const [models, setModels] = useState<EditableControlModel[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    data: configuration,
    isLoading,
    isFetching,
    error,
  } = useQuery<ControlModelConfiguration>({
    queryKey: ['controlModels', projectId],
    queryFn: () => controlModelsApi.getConfiguration(projectId),
    enabled: projectId > 0,
  });

  useEffect(() => {
    if (configuration) {
      setModels(toEditableModels(configuration));
    }
  }, [configuration]);

  useEffect(() => {
    if (!models.length) {
      return;
    }
    if (models.some((model) => model.isPrimary)) {
      return;
    }
    setModels((prev) =>
      prev.map((model, index) => ({
        ...model,
        isPrimary: index === 0,
      })),
    );
  }, [models]);

  const isBusy = isFetching;
  const availableOptions = useMemo(() => {
    const options = new Set<string>();
    configuration?.available_models.forEach((item) => options.add(item));
    models.forEach((model) => options.add(model.fileName));
    return Array.from(options).sort((a, b) => a.localeCompare(b));
  }, [configuration, models]);

  type MutationPayload = {
    controlModels: ControlModelInput[];
    primary: string | null;
  };

  const mutation = useMutation({
    mutationFn: (payload: MutationPayload) =>
      controlModelsApi.saveConfiguration(projectId, {
        control_models: payload.controlModels,
        primary_control_model: payload.primary,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['controlModels', projectId], updated);
      setModels(toEditableModels(updated));
      setStatusMessage(updated.message || 'Control models updated successfully.');
      setErrorMessage(null);
    },
    onError: (err: unknown) => {
      const message =
        err instanceof Error ? err.message : 'Failed to save control model configuration.';
      setErrorMessage(message);
      setStatusMessage(null);
    },
  });

  const handleSelectionChange = (_: unknown, selected: string[]) => {
    setStatusMessage(null);
    setErrorMessage(null);
    setModels((prev) =>
      selected.map((fileName) => {
        const existing = prev.find((model) => model.fileName === fileName);
        if (existing) {
          return existing;
        }
        return {
          fileName,
          validationTargets: [...DEFAULT_TARGETS],
          volumeLabel: '',
          notes: '',
          isPrimary: false,
          zoneCode: deriveZoneCode(fileName),
        };
      }),
    );
  };

  const handlePrimaryChange = (fileName: string) => {
    setStatusMessage(null);
    setErrorMessage(null);
    setModels((prev) =>
      prev.map((model) => ({
        ...model,
        isPrimary: model.fileName === fileName,
      })),
    );
  };

  const handleTargetToggle = (fileName: string, target: ValidationTarget) => {
    setStatusMessage(null);
    setErrorMessage(null);
    setModels((prev) =>
      prev.map((model) => {
        if (model.fileName !== fileName) {
          return model;
        }
        const hasTarget = model.validationTargets.includes(target);
        let nextTargets = hasTarget
          ? model.validationTargets.filter((value) => value !== target)
          : [...model.validationTargets, target];
        if (!nextTargets.length) {
          nextTargets = [...DEFAULT_TARGETS];
        }
        return {
          ...model,
          validationTargets: nextTargets,
        };
      }),
    );
  };

  const handleFieldChange = (
    fileName: string,
    field: 'volumeLabel' | 'notes' | 'zoneCode',
    value: string,
  ) => {
    setStatusMessage(null);
    setErrorMessage(null);
    setModels((prev) =>
      prev.map((model) =>
        model.fileName === fileName
          ? {
              ...model,
              [field]: value,
            }
          : model,
      ),
    );
  };

  const handleSave = () => {
    if (!models.length) {
      setErrorMessage('Add at least one control model before saving.');
      return;
    }
    const isMultiVolume = models.length > 1;
    for (const model of models) {
      const expectedZone = deriveZoneCode(model.fileName);
      const providedZoneRaw = model.zoneCode.trim();
      const providedZone = providedZoneRaw ? providedZoneRaw.toUpperCase() : '';
      if (expectedZone && providedZone && providedZone !== expectedZone) {
        setErrorMessage(`Zone code for ${model.fileName} must match ${expectedZone}.`);
        return;
      }
      if (isMultiVolume && !providedZone) {
        setErrorMessage(`Enter a zone code for ${model.fileName}.`);
        return;
      }
    }
    setStatusMessage(null);
    setErrorMessage(null);
    const primaryModel = models.find((model) => model.isPrimary)?.fileName ?? models[0].fileName;
    const payload: ControlModelInput[] = models.map((model) => ({
      file_name: model.fileName,
      validation_targets: sanitiseTargets(model.validationTargets),
      volume_label: model.volumeLabel.trim() || undefined,
      notes: model.notes.trim() || undefined,
      is_primary: model.isPrimary,
      zone_code: model.zoneCode.trim() ? model.zoneCode.trim().toUpperCase() : undefined,
    }));
    mutation.mutate({ controlModels: payload, primary: primaryModel });
  };

  const mutationPending = mutation.isPending;

  const summary = configuration?.validation_summary;

  if (isLoading) {
    return (
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  if (error instanceof Error) {
    return (
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Box sx={{ p: 3 }}>
          <Alert severity="error">
            Failed to load control model configuration. {error.message}
          </Alert>
        </Box>
      </Paper>
    );
  }

  const readinessChips = summary
    ? [
        {
          label: 'Naming',
          ready: summary.naming_ready,
          description: summary.naming_ready
            ? 'Naming convention validation is configured.'
            : 'Naming validation requires a control model.',
        },
        {
          label: 'Coordinates',
          ready: summary.coordinates_ready,
          description: summary.coordinates_ready
            ? 'Coordinate validation is configured.'
            : 'Coordinate validation requires a control model.',
        },
        {
          label: 'Levels',
          ready: summary.levels_ready,
          description: summary.levels_ready
            ? 'Level validation is configured.'
            : 'Level validation requires a control model.',
        },
      ]
    : [];

  return (
    <Paper variant="outlined" sx={{ mb: 3 }}>
      {isBusy || mutationPending ? <LinearProgress /> : null}
      <Box sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            justifyContent="space-between"
            gap={2}
          >
            <Box>
              <Typography variant="h6">Validation Control Models</Typography>
              <Typography variant="body2" color="text.secondary">
                Define the models used to validate naming, coordinates, and level alignment
                {projectName ? ` for ${projectName}` : ''}.
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              disabled={mutationPending}
              onClick={handleSave}
              color="primary"
            >
              {mutationPending ? 'Saving...' : 'Save Configuration'}
            </Button>
          </Stack>

          {summary ? (
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {readinessChips.map((chip) => (
                <Tooltip key={chip.label} title={chip.description}>
                  <Chip
                    icon={chip.ready ? <ReadyIcon fontSize="small" /> : <WarningIcon fontSize="small" />}
                    color={chip.ready ? 'success' : 'warning'}
                    label={`${chip.label} ${chip.ready ? 'Ready' : 'Pending'}`}
                  />
                </Tooltip>
              ))}
              <Tooltip
                title={
                  summary.multi_volume_ready
                    ? 'Multiple control models configured for volume-based validation.'
                    : 'Add additional control models if volumes are split.'
                }
              >
                <Chip
                  icon={<LayersIcon fontSize="small" />}
                  color={summary.multi_volume_ready ? 'success' : 'default'}
                  label={summary.multi_volume_ready ? 'Multi-volume Ready' : 'Single Model'}
                />
              </Tooltip>
            </Stack>
          ) : null}

          {statusMessage ? <Alert severity="success">{statusMessage}</Alert> : null}
          {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
          {summary?.issues?.length ? (
            <Alert severity="warning">
              {summary.issues.map((issue) => (
                <Box key={issue} component="span" display="block">
                  {issue}
                </Box>
              ))}
            </Alert>
          ) : null}

          <Autocomplete
            multiple
            options={availableOptions}
            value={models.map((model) => model.fileName)}
            onChange={handleSelectionChange}
            disabled={mutationPending}
            filterSelectedOptions
            renderInput={(params) => (
              <TextField
                {...params}
                label="Control models"
                placeholder={
                  availableOptions.length
                    ? 'Select models to validate against'
                    : 'No Revit health files detected yet'
                }
              />
            )}
          />

          {!models.length ? (
            <Alert severity="info">
              Select one or more Revit models to act as validation controls. These models will be used
              when checking naming conventions, coordinates, and levels.
            </Alert>
          ) : null}

          {models.map((model) => (
            <Paper
              variant="outlined"
              key={model.fileName}
              sx={{ p: 2, borderColor: model.isPrimary ? 'primary.light' : 'divider' }}
            >
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                spacing={1}
                sx={{ mb: 2 }}
              >
                <Typography variant="subtitle1">{model.fileName}</Typography>
                <FormControlLabel
                  control={
                    <Radio
                      checked={model.isPrimary}
                      onChange={() => handlePrimaryChange(model.fileName)}
                      disabled={mutationPending}
                    />
                  }
                  label="Primary control"
                />
              </Stack>

              <Stack
                direction={{ xs: 'column', md: 'row' }}
                spacing={2}
                alignItems={{ xs: 'flex-start', md: 'center' }}
                sx={{ mb: 2 }}
              >
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {VALIDATION_TARGETS.map((target) => {
                    const selected = model.validationTargets.includes(target);
                    return (
                      <Chip
                        key={target}
                        label={target.charAt(0).toUpperCase() + target.slice(1)}
                        color={selected ? 'primary' : 'default'}
                        variant={selected ? 'filled' : 'outlined'}
                        clickable
                        disabled={mutationPending}
                        onClick={() => handleTargetToggle(model.fileName, target)}
                        sx={{ opacity: mutationPending ? 0.75 : 1 }}
                      />
                    );
                  })}
                </Box>
              </Stack>

              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <TextField
                  label="Zone Code"
                  value={model.zoneCode}
                  onChange={(event) =>
                    handleFieldChange(model.fileName, 'zoneCode', event.target.value.toUpperCase())
                  }
                  disabled={mutationPending}
                  fullWidth
                  placeholder="Auto-detected from file name"
                  helperText={`Expected: ${deriveZoneCode(model.fileName) || 'N/A'}`}
                />
                <TextField
                  label="Volume / Area"
                  value={model.volumeLabel}
                  onChange={(event) =>
                    handleFieldChange(model.fileName, 'volumeLabel', event.target.value)
                  }
                  disabled={mutationPending}
                  fullWidth
                  placeholder="e.g. Tower A, Basement, West Wing"
                />
                <TextField
                  label="Notes"
                  value={model.notes}
                  onChange={(event) => handleFieldChange(model.fileName, 'notes', event.target.value)}
                  disabled={mutationPending}
                  fullWidth
                  placeholder="Optional context for this control model"
                  multiline
                  minRows={1}
                />
              </Stack>
            </Paper>
          ))}
        </Stack>
      </Box>
    </Paper>
  );
};
