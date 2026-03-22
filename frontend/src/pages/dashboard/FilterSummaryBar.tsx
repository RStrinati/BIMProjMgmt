import { Chip, Stack, Typography } from '@mui/material';
import { useDashboardFilters } from './DashboardFiltersContext';

const formatValue = (value: string) => (value && value !== 'all' ? value : 'All');

export function FilterSummaryBar() {
  const { filters } = useDashboardFilters();
  const chips = [
    { label: `Projects: ${filters.projectIds.length || 'All'}` },
    { label: `Manager: ${formatValue(filters.manager)}` },
    { label: `Client: ${formatValue(filters.client)}` },
    { label: `Type: ${formatValue(filters.projectType)}` },
    { label: `Discipline: ${formatValue(filters.discipline)}` },
    filters.location ? { label: `Location / Building: ${filters.location}` } : null,
  ].filter(Boolean) as { label: string }[];

  return (
    <Stack direction="row" spacing={1} flexWrap="wrap" alignItems="center">
      <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
        Active filters
      </Typography>
      {chips.map((chip) => (
        <Chip key={chip.label} label={chip.label} size="small" />
      ))}
    </Stack>
  );
}
