import { Box, Typography } from '@mui/material';
import { ReactNode } from 'react';

type InlineFieldProps = {
  label: string;
  value?: ReactNode;
  fallback?: string;
  editor?: ReactNode;
  isEditing?: boolean;
};

export function InlineField({ label, value, fallback = '--', editor, isEditing = false }: InlineFieldProps) {
  const displayValue =
    value === null || value === undefined || value === '' ? fallback : value;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, alignItems: 'center' }}>
      <Typography color="text.secondary">{label}</Typography>
      {isEditing && editor ? (
        <Box>{editor}</Box>
      ) : (
        <Typography sx={{ textAlign: 'right' }}>{displayValue}</Typography>
      )}
    </Box>
  );
}
