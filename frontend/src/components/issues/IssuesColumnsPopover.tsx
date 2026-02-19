import {
  Box,
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Popover,
  Stack,
  Typography,
  Checkbox,
} from '@mui/material';
import { ArrowDownward, ArrowUpward } from '@mui/icons-material';

export type IssueColumnDefinition = {
  id: string;
  label: string;
};

type IssuesColumnsPopoverProps = {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  columns: IssueColumnDefinition[];
  visibleColumnIds: string[];
  orderedColumnIds: string[];
  toggleColumn: (columnId: string) => void;
  moveColumn: (columnId: string, direction: 'up' | 'down') => void;
  resetToDefaults: () => void;
};

export function IssuesColumnsPopover({
  anchorEl,
  onClose,
  columns,
  visibleColumnIds,
  orderedColumnIds,
  toggleColumn,
  moveColumn,
  resetToDefaults,
}: IssuesColumnsPopoverProps) {
  const open = Boolean(anchorEl);
  const columnMap = new Map(columns.map((col) => [col.id, col]));
  const orderedColumns = orderedColumnIds.map((id) => columnMap.get(id)).filter(Boolean) as IssueColumnDefinition[];

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
          <Typography variant="subtitle1">Columns</Typography>
          <Button size="small" onClick={resetToDefaults}>
            Reset
          </Button>
        </Stack>
        <Divider />
        <List dense>
          {orderedColumns.map((column) => {
            const checked = visibleColumnIds.includes(column.id);
            return (
              <ListItem
                key={column.id}
                secondaryAction={(
                  <Stack direction="row" spacing={0.5}>
                    <IconButton size="small" onClick={() => moveColumn(column.id, 'up')} aria-label={`move-up-${column.id}`}>
                      <ArrowUpward fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => moveColumn(column.id, 'down')} aria-label={`move-down-${column.id}`}>
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
                    onChange={() => toggleColumn(column.id)}
                    tabIndex={-1}
                    inputProps={{ 'aria-label': column.label }}
                  />
                </ListItemIcon>
                <ListItemText primary={column.label} />
              </ListItem>
            );
          })}
        </List>
        <Divider />
        <Box sx={{ px: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Column visibility and order are saved for this page.
          </Typography>
        </Box>
      </Stack>
    </Popover>
  );
}
