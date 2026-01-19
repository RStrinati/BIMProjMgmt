import { Box, Paper, SxProps, Theme } from '@mui/material';
import React from 'react';

interface LinearListContainerProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
  variant?: 'outlined' | 'elevation';
  elevation?: number;
}

/**
 * Container wrapper for a linear list (table-like structure).
 * Provides consistent padding, borders, and styling.
 *
 * Typical usage:
 * <LinearListContainer>
 *   <LinearListHeaderRow columns={...} />
 *   <LinearListRow>...</LinearListRow>
 *   <LinearListRow>...</LinearListRow>
 * </LinearListContainer>
 */
export function LinearListContainer({
  children,
  sx,
  variant = 'outlined',
  elevation = 0,
}: LinearListContainerProps) {
  return (
    <Paper
      variant={variant}
      elevation={elevation}
      component={Box}
      data-testid="linear-list-container"
      sx={{
        borderRadius: 1,
        border: variant === 'outlined' ? '1px solid' : 'none',
        borderColor: 'divider',
        overflow: 'hidden',
        ...sx,
      }}
    >
      {children}
    </Paper>
  );
}
