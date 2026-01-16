import { Box, Typography, SxProps, Theme } from '@mui/material';
import React from 'react';

type CellVariant = 'primary' | 'secondary' | 'caption' | 'number';

interface LinearListCellProps {
  children: React.ReactNode;
  variant?: CellVariant;
  align?: 'left' | 'right' | 'center';
  sx?: SxProps<Theme>;
  testId?: string;
}

/**
 * Cell component for LinearList rows.
 * Provides consistent typography and alignment for data cells.
 *
 * Variants:
 * - primary: body2 fontWeight 500 (main content)
 * - secondary: body2 color text.secondary (supporting info)
 * - caption: caption color text.secondary (labels, metadata)
 * - number: body2 textAlign right (currency, percentages)
 *
 * Usage:
 * <LinearListCell variant="primary">Service Name</LinearListCell>
 * <LinearListCell variant="secondary">Development</LinearListCell>
 * <LinearListCell variant="number">$1,250.00</LinearListCell>
 */
export function LinearListCell({
  children,
  variant = 'primary',
  align = 'left',
  sx,
  testId,
}: LinearListCellProps) {
  const typographyProps: {
    variant: 'body2' | 'caption';
    fontWeight?: number;
    color?: string;
  } = {
    variant: 'body2',
  };

  let alignContent: 'left' | 'right' | 'center' = align;

  if (variant === 'primary') {
    typographyProps.fontWeight = 500;
  } else if (variant === 'secondary' || variant === 'caption') {
    typographyProps.variant = 'body2';
    typographyProps.color = 'text.secondary';
    if (variant === 'caption') {
      typographyProps.variant = 'caption';
    }
  } else if (variant === 'number') {
    alignContent = 'right';
  }

  return (
    <Box
      data-testid={testId}
      sx={{
        textAlign: alignContent,
        ...sx,
      }}
    >
      <Typography {...typographyProps}>{children}</Typography>
    </Box>
  );
}
