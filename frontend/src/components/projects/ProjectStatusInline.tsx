import { MenuItem, Select, Stack, Typography } from '@mui/material';
import { InlineField } from '@/components/ui/InlineField';

const STATUS_OPTIONS = ['Active', 'On Hold', 'Completed', 'Cancelled'];

type ProjectStatusInlineProps = {
  value?: string | null;
  onChange: (value: string | null) => void;
  isSaving?: boolean;
  disabled?: boolean;
};

export function ProjectStatusInline({
  value,
  onChange,
  isSaving = false,
  disabled = false,
}: ProjectStatusInlineProps) {
  return (
    <InlineField
      label="Status"
      isEditing
      editor={(
        <Stack spacing={0.5} alignItems="flex-end">
          <Select
            size="small"
            value={value ?? ''}
            onChange={(event) => onChange(event.target.value || null)}
            disabled={disabled}
            data-testid="projects-panel-status-select"
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">
              <em>Unset</em>
            </MenuItem>
            {STATUS_OPTIONS.map((status) => (
              <MenuItem key={status} value={status}>
                {status}
              </MenuItem>
            ))}
          </Select>
          {isSaving && (
            <Typography variant="caption" color="text.secondary" data-testid="projects-panel-saving">
              Saving...
            </Typography>
          )}
        </Stack>
      )}
    />
  );
}
