import { MenuItem, Select, Stack, Typography } from '@mui/material';
import { InlineField } from '@/components/ui/InlineField';
import {
  SERVICE_STATUS_OPTIONS,
  formatServiceStatusLabel,
  fromApiServiceStatus,
} from '@/utils/serviceStatus';

type ServiceStatusInlineProps = {
  value?: string | null;
  onChange: (value: string | null) => void;
  isSaving?: boolean;
  disabled?: boolean;
};

export function ServiceStatusInline({
  value,
  onChange,
  isSaving = false,
  disabled = false,
}: ServiceStatusInlineProps) {
  const selectedOption = fromApiServiceStatus(value ?? null);
  const isUnknown = Boolean(value && !selectedOption);

  if (isUnknown && value) {
    return <InlineField label="Service status" value={formatServiceStatusLabel(value)} />;
  }

  return (
    <InlineField
      label="Service status"
      isEditing
      editor={(
        <Stack spacing={0.5} alignItems="flex-end">
          <Select
            size="small"
            value={selectedOption?.value ?? ''}
            onChange={(event) => onChange(event.target.value || null)}
            disabled={disabled}
            data-testid="projects-panel-service-status-select"
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">
              <em>Unset</em>
            </MenuItem>
            {SERVICE_STATUS_OPTIONS.map((status) => (
              <MenuItem key={status.value} value={status.value}>
                {status.label}
              </MenuItem>
            ))}
          </Select>
          {isSaving && (
            <Typography variant="caption" color="text.secondary" data-testid="projects-panel-service-saving">
              Saving...
            </Typography>
          )}
        </Stack>
      )}
    />
  );
}
