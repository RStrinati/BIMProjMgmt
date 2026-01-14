import { MenuItem, Select, Stack, Typography } from '@mui/material';
import { InlineField } from '@/components/ui/InlineField';
import {
  REVIEW_STATUS_OPTIONS,
  formatReviewStatusLabel,
  fromApiReviewStatus,
} from '@/utils/reviewStatus';

type ReviewStatusInlineProps = {
  value?: string | null;
  onChange: (value: string | null) => void;
  isSaving?: boolean;
  disabled?: boolean;
};

export function ReviewStatusInline({
  value,
  onChange,
  isSaving = false,
  disabled = false,
}: ReviewStatusInlineProps) {
  const selectedOption = fromApiReviewStatus(value ?? null);
  const isUnknown = Boolean(value && !selectedOption);

  if (isUnknown && value) {
    return <InlineField label="Review status" value={formatReviewStatusLabel(value)} />;
  }

  return (
    <InlineField
      label="Review status"
      isEditing
      editor={(
        <Stack spacing={0.5} alignItems="flex-end">
          <Select
            size="small"
            value={selectedOption?.value ?? ''}
            onChange={(event) => onChange(event.target.value || null)}
            disabled={disabled}
            data-testid="projects-panel-review-status-select"
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">
              <em>Unset</em>
            </MenuItem>
            {REVIEW_STATUS_OPTIONS.map((status) => (
              <MenuItem key={status.value} value={status.value}>
                {status.label}
              </MenuItem>
            ))}
          </Select>
          {isSaving && (
            <Typography variant="caption" color="text.secondary" data-testid="projects-panel-review-saving">
              Saving...
            </Typography>
          )}
        </Stack>
      )}
    />
  );
}
