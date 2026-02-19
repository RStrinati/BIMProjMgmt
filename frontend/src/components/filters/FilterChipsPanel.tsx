import React from 'react';
import { Chip, Stack, Typography } from '@mui/material';

export interface FilterChipGroup {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  emptyLabel?: string;
}

interface FilterChipsPanelProps {
  groups: FilterChipGroup[];
}

export default function FilterChipsPanel({ groups }: FilterChipsPanelProps) {
  return (
    <Stack spacing={2}>
      {groups.map((group) => (
        <Stack
          key={group.label}
          direction="row"
          spacing={1}
          alignItems="center"
          flexWrap="wrap"
        >
          <Typography variant="subtitle2" color="text.secondary">
            {group.label}
          </Typography>
          {group.options.map((option) => (
            <Chip
              key={`${group.label}-${option}`}
              label={option}
              size="small"
              color={group.selected.includes(option) ? 'primary' : 'default'}
              onClick={() => group.onToggle(option)}
            />
          ))}
          {!group.options.length && (
            <Chip label={group.emptyLabel ?? `No ${group.label.toLowerCase()} yet`} size="small" variant="outlined" />
          )}
        </Stack>
      ))}
    </Stack>
  );
}
