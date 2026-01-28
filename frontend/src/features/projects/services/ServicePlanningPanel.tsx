import { useState, useCallback } from 'react';
import {
  Box,
  Stack,
  Typography,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import type { ProjectService } from '@/types/api';

type ExecutionIntent = 'planned' | 'optional' | 'not_proceeding';

const REASON_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'Optional', label: 'Optional' },
  { value: 'Client deferred', label: 'Client deferred' },
  { value: 'Not proceeding', label: 'Not proceeding' },
  { value: 'TBC', label: 'TBC' },
];

type ServicePlanningPanelProps = {
  service: ProjectService | null;
  onExecutionIntentChange: (intent: ExecutionIntent, reason?: string | null) => Promise<void>;
  isSaving?: boolean;
  saveError?: string | null;
};

export function ServicePlanningPanel({
  service,
  onExecutionIntentChange,
  isSaving = false,
  saveError,
}: ServicePlanningPanelProps) {
  const [showReasonSelect, setShowReasonSelect] = useState(
    service?.execution_intent !== 'planned'
  );
  const [selectedReason, setSelectedReason] = useState<string | null>(
    service?.decision_reason || null
  );

  const isIncluded = service?.execution_intent === 'planned' || !service?.execution_intent;

  const handleToggleIncluded = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const isNowIncluded = event.target.checked;

      if (isNowIncluded) {
        // Switching back to planned
        await onExecutionIntentChange('planned', null);
        setShowReasonSelect(false);
        setSelectedReason(null);
      } else {
        // Switching to not included - show reason selector
        setShowReasonSelect(true);
      }
    },
    [onExecutionIntentChange]
  );

  const handleReasonChange = useCallback(
    async (event: React.ChangeEvent<{ name?: string; value: unknown }>) => {
      const reason = event.target.value as string;
      setSelectedReason(reason);

      // Determine intent based on reason
      let intent: ExecutionIntent = 'optional';
      if (reason === 'Not proceeding') {
        intent = 'not_proceeding';
      }

      await onExecutionIntentChange(intent, reason);
    },
    [onExecutionIntentChange]
  );

  if (!service) {
    return (
      <Typography color="text.secondary" variant="body2">
        Select a service to view planning details.
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1.5 }}>
          Planning
        </Typography>

        {saveError && (
          <Alert severity="error" sx={{ mb: 1.5 }}>
            {saveError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={isIncluded}
                onChange={handleToggleIncluded}
                disabled={isSaving}
                size="small"
              />
            }
            label={
              <Typography variant="body2">
                {isIncluded ? 'Included in plan' : 'Not included in plan'}
              </Typography>
            }
          />
          {isSaving && <CircularProgress size={20} />}
        </Box>

        {showReasonSelect && !isIncluded && (
          <Box sx={{ mt: 2, ml: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Reason for change:
            </Typography>
            <Select
              size="small"
              value={selectedReason || ''}
              onChange={handleReasonChange}
              disabled={isSaving}
              sx={{ width: '100%' }}
            >
              <MenuItem value="">
                <Typography variant="body2" color="text.secondary">
                  Select a reason...
                </Typography>
              </MenuItem>
              {REASON_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </Box>
        )}

        {!isIncluded && selectedReason && (
          <Alert severity="info" sx={{ mt: 1.5 }}>
            <Typography variant="caption">
              This service is excluded from planned deliverables and pipeline calculations, but
              remains part of the contract value.
            </Typography>
          </Alert>
        )}
      </Box>
    </Stack>
  );
}
