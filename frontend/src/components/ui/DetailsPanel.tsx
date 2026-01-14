import { Box, Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

type DetailsPanelProps = {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children?: ReactNode;
  emptyState?: ReactNode;
};

export function DetailsPanel({ title, subtitle, actions, children, emptyState }: DetailsPanelProps) {
  if (!children && emptyState) {
    return <Box>{emptyState}</Box>;
  }

  return (
    <Stack spacing={2}>
      {(title || subtitle || actions) && (
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            {title && <Typography variant="h6">{title}</Typography>}
            {subtitle && <Typography color="text.secondary">{subtitle}</Typography>}
          </Box>
          {actions}
        </Stack>
      )}
      {children}
    </Stack>
  );
}
