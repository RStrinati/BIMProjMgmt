import { List, ListItemButton, ListItemText, Box, Typography } from '@mui/material';
import { ReactNode } from 'react';

type ListViewProps<T> = {
  items: T[];
  getItemId: (item: T) => number | string;
  getItemTestId?: (item: T) => string;
  renderPrimary: (item: T) => ReactNode;
  renderSecondary?: (item: T) => ReactNode;
  selectedId?: number | string | null;
  onSelect?: (item: T) => void;
  onHover?: (item: T) => void;
  header?: ReactNode;
  emptyState?: ReactNode;
};

export function ListView<T>({
  items,
  getItemId,
  getItemTestId,
  renderPrimary,
  renderSecondary,
  selectedId,
  onSelect,
  onHover,
  header,
  emptyState,
}: ListViewProps<T>) {
  if (!items.length) {
    return (
      <Box>
        {header}
        {emptyState ?? (
          <Typography color="text.secondary" sx={{ p: 2 }}>
            No results.
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Box>
      {header}
      <List dense>
        {items.map((item) => {
          const id = getItemId(item);
          const selected = selectedId === id;
          return (
            <ListItemButton
              key={id}
              selected={selected}
              onClick={() => onSelect?.(item)}
              onMouseEnter={() => onHover?.(item)}
              data-testid={getItemTestId ? getItemTestId(item) : undefined}
              data-item-id={id}
            >
              <ListItemText primary={renderPrimary(item)} secondary={renderSecondary?.(item)} />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
}
