import { useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { useDashboardFilters } from './DashboardFiltersContext';

export function DashboardFilterRail() {
  const { filters, updateFilters, savedViews, saveView, applySavedView, deleteSavedView } = useDashboardFilters();
  const [viewName, setViewName] = useState('');
  const { data: projects = [] } = useQuery({
    queryKey: ['dashboard', 'project-summary'],
    queryFn: () => projectsApi.getSummary({ viewId: 'all' }),
  });

  const options = useMemo(() => {
    const managers = new Set<string>();
    const clients = new Set<string>();
    const types = new Set<string>();
    projects.forEach((project) => {
      if (project.project_manager) managers.add(project.project_manager);
      if (project.client_name) clients.add(project.client_name);
      if (project.project_type) types.add(project.project_type);
    });
    const toSorted = (values: Set<string>) => Array.from(values).sort((a, b) => a.localeCompare(b));
    return {
      managers: toSorted(managers),
      clients: toSorted(clients),
      types: toSorted(types),
    };
  }, [projects]);

  return (
    <Stack spacing={3} sx={{ position: 'sticky', top: 24 }}>
      <Stack spacing={1}>
        <Typography variant="h6">Filters</Typography>
        <Typography variant="caption" color="text.secondary">
          These filters apply across the current workspace.
        </Typography>
      </Stack>

      <FormControl fullWidth size="small">
        <InputLabel>Saved Views</InputLabel>
        <Select
          value=""
          label="Saved Views"
          onChange={(event) => applySavedView(event.target.value)}
        >
          {savedViews.map((view) => (
            <MenuItem key={view.name} value={view.name}>
              {view.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Stack direction="row" spacing={1}>
        <TextField
          size="small"
          label="Save View"
          value={viewName}
          onChange={(event) => setViewName(event.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          onClick={() => {
            saveView(viewName);
            setViewName('');
          }}
        >
          Save
        </Button>
      </Stack>
      {savedViews.length > 0 ? (
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {savedViews.map((view) => (
            <Chip
              key={view.name}
              label={view.name}
              size="small"
              onDelete={() => deleteSavedView(view.name)}
            />
          ))}
        </Stack>
      ) : null}

      <Divider />

      <FormControl fullWidth size="small">
        <InputLabel>Projects</InputLabel>
        <Select
          multiple
          value={filters.projectIds}
          label="Projects"
          onChange={(event) => {
            const value = event.target.value as number[];
            updateFilters({ projectIds: value });
          }}
          renderValue={(selected) => (selected.length ? `${selected.length} selected` : 'All')}
        >
          {projects.map((project) => (
            <MenuItem key={project.project_id} value={project.project_id}>
              {project.project_name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth size="small">
        <InputLabel>Manager</InputLabel>
        <Select
          value={filters.manager}
          label="Manager"
          onChange={(event) => updateFilters({ manager: event.target.value })}
        >
          <MenuItem value="all">All</MenuItem>
          {options.managers.map((manager) => (
            <MenuItem key={manager} value={manager}>
              {manager}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth size="small">
        <InputLabel>Client</InputLabel>
        <Select
          value={filters.client}
          label="Client"
          onChange={(event) => updateFilters({ client: event.target.value })}
        >
          <MenuItem value="all">All</MenuItem>
          {options.clients.map((client) => (
            <MenuItem key={client} value={client}>
              {client}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth size="small">
        <InputLabel>Type</InputLabel>
        <Select
          value={filters.projectType}
          label="Type"
          onChange={(event) => updateFilters({ projectType: event.target.value })}
        >
          <MenuItem value="all">All</MenuItem>
          {options.types.map((type) => (
            <MenuItem key={type} value={type}>
              {type}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <TextField
        size="small"
        label="Location / Building"
        value={filters.location}
        onChange={(event) => updateFilters({ location: event.target.value })}
      />

      <FormControl fullWidth size="small">
        <InputLabel>Discipline</InputLabel>
        <Select
          value={filters.discipline}
          label="Discipline"
          onChange={(event) => updateFilters({ discipline: event.target.value })}
        >
          <MenuItem value="all">All</MenuItem>
          <MenuItem value="architectural">Architectural</MenuItem>
          <MenuItem value="structural">Structural</MenuItem>
          <MenuItem value="mep">MEP</MenuItem>
          <MenuItem value="electrical">Electrical</MenuItem>
          <MenuItem value="mechanical">Mechanical</MenuItem>
          <MenuItem value="plumbing">Plumbing</MenuItem>
        </Select>
      </FormControl>

      <Box>
        <Typography variant="caption" color="text.secondary">
          Location filtering is currently mapped to issue zones until a canonical building dimension lands.
        </Typography>
      </Box>
    </Stack>
  );
}
