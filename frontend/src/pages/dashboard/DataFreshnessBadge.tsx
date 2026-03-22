import { Chip } from '@mui/material';

export function DataFreshnessBadge({ asOf }: { asOf?: string | null }) {
  if (!asOf) {
    return <Chip label="Data freshness: unknown" size="small" variant="outlined" />;
  }
  const parsed = new Date(asOf);
  const label = Number.isNaN(parsed.getTime()) ? asOf : parsed.toLocaleString();
  return <Chip label={`Data as of ${label}`} size="small" variant="outlined" />;
}
