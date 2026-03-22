import { Stack, Typography } from '@mui/material';

export function LastRefreshStatus({ updatedAt }: { updatedAt?: number }) {
  if (!updatedAt) return null;
  const label = new Date(updatedAt).toLocaleTimeString();
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Typography variant="caption" color="text.secondary">
        Updated at {label}
      </Typography>
    </Stack>
  );
}
