import {
  Box,
  Button,
  Checkbox,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Popover,
  Stack,
  Typography,
} from '@mui/material';
import {
  ArrowDownward,
  ArrowUpward,
  PushPin,
  PushPinOutlined,
} from '@mui/icons-material';
import type { ProjectFieldView } from './ProjectFieldRegistry';
import { PROJECT_FIELD_MAP } from './ProjectFieldRegistry';

type ProjectColumnsPopoverProps = {
  view: ProjectFieldView;
  anchorEl: HTMLElement | null;
  onClose: () => void;
  visibleFieldIds: string[];
  orderedFieldIds: string[];
  pinnedFieldIds: string[];
  toggleField: (fieldId: string) => void;
  moveField: (fieldId: string, direction: 'up' | 'down') => void;
  togglePinnedField: (fieldId: string) => void;
  resetToDefaults: () => void;
};

export function ProjectColumnsPopover({
  view,
  anchorEl,
  onClose,
  visibleFieldIds,
  orderedFieldIds,
  pinnedFieldIds,
  toggleField,
  moveField,
  togglePinnedField,
  resetToDefaults,
}: ProjectColumnsPopoverProps) {
  const open = Boolean(anchorEl);
  const orderedFields = orderedFieldIds
    .map((id) => PROJECT_FIELD_MAP.get(id))
    .filter(Boolean);

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      PaperProps={{ sx: { width: 320, p: 1 } }}
    >
      <Stack spacing={1} sx={{ p: 1 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="subtitle1">Fields</Typography>
          <Button size="small" onClick={resetToDefaults}>
            Reset
          </Button>
        </Stack>
        <Divider />
        <List dense>
          {orderedFields.map((field) => {
            if (!field) return null;
            const checked = visibleFieldIds.includes(field.id);
            const isPinned = pinnedFieldIds.includes(field.id);
            return (
              <ListItem
                key={field.id}
                secondaryAction={(
                  <Stack direction="row" spacing={0.5}>
                    {view === 'list' && (
                      <IconButton
                        size="small"
                        onClick={() => togglePinnedField(field.id)}
                        aria-label={`pin-${field.id}`}
                      >
                        {isPinned ? <PushPin fontSize="small" /> : <PushPinOutlined fontSize="small" />}
                      </IconButton>
                    )}
                    <IconButton size="small" onClick={() => moveField(field.id, 'up')} aria-label={`move-up-${field.id}`}>
                      <ArrowUpward fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => moveField(field.id, 'down')} aria-label={`move-down-${field.id}`}>
                      <ArrowDownward fontSize="small" />
                    </IconButton>
                  </Stack>
                )}
                sx={{ py: 0.5 }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <Checkbox
                    edge="start"
                    checked={checked}
                    onChange={() => toggleField(field.id)}
                    tabIndex={-1}
                    inputProps={{ 'aria-label': field.label }}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={field.label}
                  secondary={field.format}
                />
              </ListItem>
            );
          })}
        </List>
        <Divider />
        <Box sx={{ px: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Changes apply to {view} view only.
          </Typography>
        </Box>
      </Stack>
    </Popover>
  );
}
