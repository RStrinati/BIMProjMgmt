import { MenuItem, Select, Stack, Typography } from '@mui/material';
import type { User } from '@/types/api';
import { InlineField } from '@/components/ui/InlineField';

type ProjectLeadInlineProps = {
  value?: number | null;
  users: User[];
  onChange: (value: number | null) => void;
  isSaving?: boolean;
  disabled?: boolean;
};

const getUserLabel = (user: User) =>
  user.name || user.full_name || user.username || `User ${user.user_id}`;

export function ProjectLeadInline({
  value,
  users,
  onChange,
  isSaving = false,
  disabled = false,
}: ProjectLeadInlineProps) {
  return (
    <InlineField
      label="Project lead"
      isEditing
      editor={(
        <Stack spacing={0.5} alignItems="flex-end">
          <Select
            size="small"
            value={value ?? ''}
            onChange={(event) =>
              onChange(event.target.value === '' ? null : Number(event.target.value))
            }
            disabled={disabled}
            data-testid="projects-panel-lead-select"
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="">
              <em>Unassigned</em>
            </MenuItem>
            {users.map((user) => (
              <MenuItem key={user.user_id} value={user.user_id}>
                {getUserLabel(user)}
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
