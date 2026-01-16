import { Box, SxProps, Theme } from '@mui/material';
import React from 'react';

interface LinearListRowProps {
  children: React.ReactNode;
  columns?: number;
  sx?: SxProps<Theme>;
  testId?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

/**
 * Data row for a LinearList.
 * Provides consistent styling for grid-aligned rows with proper spacing and hover effects.
 *
 * Features:
 * - Bottom divider (1px solid)
 * - Hover background (theme.palette.action.hover)
 * - Compact padding (py ~ 1)
 * - Grid layout matching LinearListHeaderRow
 * - Optional cursor pointer and hover highlighting
 *
 * Usage:
 * <LinearListRow columns={3}>
 *   <Box>Name</Box>
 *   <Box>Active</Box>
 *   <Box>$1,000</Box>
 * </LinearListRow>
 */
export function LinearListRow({
  children,
  columns,
  sx,
  testId,
  onClick,
  hoverable = true,
}: LinearListRowProps) {
  const childArray = React.Children.toArray(children);
  const colCount = columns || childArray.length;

  return (
    <Box
      data-testid={testId}
      onClick={onClick}
      sx={{
        display: 'grid',
        gridTemplateColumns: `repeat(${colCount}, 1fr)`,
        gap: 2,
        px: 2,
        py: 1,
        alignItems: 'center',
        borderBottom: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        transition: (theme) =>
          theme.transitions.create(['background-color', 'border-color'], {
            duration: theme.transitions.duration.short,
          }),
        ...(hoverable && {
          cursor: onClick ? 'pointer' : 'default',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }),
        ...sx,
      }}
    >
      {children}
    </Box>
  );
}
