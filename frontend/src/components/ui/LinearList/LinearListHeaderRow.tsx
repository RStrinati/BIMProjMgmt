import { Box, SxProps, Theme } from '@mui/material';

interface LinearListHeaderRowProps {
  columns: string[];
  sx?: SxProps<Theme>;
  sticky?: boolean;
}

/**
 * Header row for a LinearList.
 * Displays column labels with consistent typography and styling.
 *
 * Features:
 * - Bottom divider (1px solid)
 * - Compact padding (py ~1)
 * - Header-specific typography (fontWeight 600, caption/body2)
 * - Optional sticky positioning
 *
 * Usage:
 * <LinearListHeaderRow columns={['Name', 'Status', 'Amount']} />
 */
export function LinearListHeaderRow({
  columns,
  sx,
  sticky = false,
}: LinearListHeaderRowProps) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns.length}, 1fr)`,
        gap: 2,
        px: 2,
        py: 1,
        borderBottom: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        ...(sticky && {
          position: 'sticky',
          top: 0,
          zIndex: 2,
        }),
        ...sx,
      }}
    >
      {columns.map((column, idx) => (
        <Box
          key={`${column}-${idx}`}
          sx={{
            typography: 'caption',
            fontWeight: 600,
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {column}
        </Box>
      ))}
    </Box>
  );
}
