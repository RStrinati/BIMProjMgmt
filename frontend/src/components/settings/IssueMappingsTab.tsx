import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Paper,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { mappingsApi } from '@/api/mappings';
import { projectsApi } from '@/api/projects';
import type { Project } from '@/types/api';
import type { IssueAttributeMapping, ReviztoProjectMapping } from '@/api/mappings';

const SOURCE_OPTIONS = ['ACC', 'Revizto'];

const IssueMappingsTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [revDialogOpen, setRevDialogOpen] = useState(false);
  const [attrDialogOpen, setAttrDialogOpen] = useState(false);
  const [editingAttr, setEditingAttr] = useState<IssueAttributeMapping | null>(null);
  const [revForm, setRevForm] = useState({
    revizto_project_uuid: '',
    pm_project_id: '',
    project_name_override: '',
  });
  const [attrForm, setAttrForm] = useState({
    project_id: '',
    source_system: 'ACC',
    raw_attribute_name: '',
    mapped_field_name: '',
    data_type: '',
    priority: '100',
  });
  const [error, setError] = useState('');

  const { data: revMappings = [] } = useQuery({
    queryKey: ['mappings', 'revizto-projects'],
    queryFn: () => mappingsApi.getReviztoProjectMappings(true),
  });

  const { data: attrMappings = [] } = useQuery({
    queryKey: ['mappings', 'issue-attributes'],
    queryFn: () => mappingsApi.getIssueAttributeMappings(true),
  });

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['mappings', 'projects'],
    queryFn: () => projectsApi.getAll(),
  });

  const projectOptions = useMemo(
    () =>
      projects.map((project) => ({
        value: String(project.project_id),
        label: `${project.project_name} (ID: ${project.project_id})`,
      })),
    [projects],
  );

  const refreshMappings = () => {
    queryClient.invalidateQueries({ queryKey: ['mappings', 'revizto-projects'] });
    queryClient.invalidateQueries({ queryKey: ['mappings', 'issue-attributes'] });
  };

  const revUpsert = useMutation({
    mutationFn: mappingsApi.upsertReviztoProjectMapping,
    onSuccess: () => {
      refreshMappings();
      setRevDialogOpen(false);
      setRevForm({ revizto_project_uuid: '', pm_project_id: '', project_name_override: '' });
      setError('');
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to save Revizto mapping');
    },
  });

  const revDelete = useMutation({
    mutationFn: mappingsApi.deleteReviztoProjectMapping,
    onSuccess: refreshMappings,
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to delete Revizto mapping');
    },
  });

  const attrCreate = useMutation({
    mutationFn: mappingsApi.createIssueAttributeMapping,
    onSuccess: () => {
      refreshMappings();
      setAttrDialogOpen(false);
      setEditingAttr(null);
      setAttrForm({
        project_id: '',
        source_system: 'ACC',
        raw_attribute_name: '',
        mapped_field_name: '',
        data_type: '',
        priority: '100',
      });
      setError('');
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to create attribute mapping');
    },
  });

  const attrUpdate = useMutation({
    mutationFn: ({ map_id, payload }: { map_id: number; payload: Partial<IssueAttributeMapping> }) =>
      mappingsApi.updateIssueAttributeMapping(map_id, payload),
    onSuccess: () => {
      refreshMappings();
      setAttrDialogOpen(false);
      setEditingAttr(null);
      setError('');
    },
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to update attribute mapping');
    },
  });

  const attrDelete = useMutation({
    mutationFn: mappingsApi.deleteIssueAttributeMapping,
    onSuccess: refreshMappings,
    onError: (err: any) => {
      setError(err?.response?.data?.error ?? 'Failed to delete attribute mapping');
    },
  });

  const handleRevSubmit = () => {
    if (!revForm.revizto_project_uuid.trim()) {
      setError('Revizto project UUID is required');
      return;
    }
    const pmProjectId = revForm.pm_project_id ? Number(revForm.pm_project_id) : null;
    revUpsert.mutate({
      revizto_project_uuid: revForm.revizto_project_uuid.trim(),
      pm_project_id: Number.isNaN(pmProjectId) ? null : pmProjectId,
      project_name_override: revForm.project_name_override.trim() || undefined,
    });
  };

  const openAttrDialog = (mapping?: IssueAttributeMapping) => {
    if (mapping) {
      setEditingAttr(mapping);
      setAttrForm({
        project_id: mapping.project_id ? String(mapping.project_id) : '',
        source_system: mapping.source_system,
        raw_attribute_name: mapping.raw_attribute_name,
        mapped_field_name: mapping.mapped_field_name,
        data_type: mapping.data_type ?? '',
        priority: String(mapping.priority ?? 100),
      });
    } else {
      setEditingAttr(null);
      setAttrForm({
        project_id: '',
        source_system: 'ACC',
        raw_attribute_name: '',
        mapped_field_name: '',
        data_type: '',
        priority: '100',
      });
    }
    setAttrDialogOpen(true);
    setError('');
  };

  const handleAttrSubmit = () => {
    if (!attrForm.raw_attribute_name.trim() || !attrForm.mapped_field_name.trim()) {
      setError('Raw attribute name and mapped field name are required');
      return;
    }
    const payload = {
      project_id: attrForm.project_id.trim() || null,
      source_system: attrForm.source_system,
      raw_attribute_name: attrForm.raw_attribute_name.trim(),
      mapped_field_name: attrForm.mapped_field_name.trim(),
      data_type: attrForm.data_type.trim() || null,
      priority: Number(attrForm.priority) || 100,
    };
    if (editingAttr) {
      attrUpdate.mutate({ map_id: editingAttr.map_id, payload });
    } else {
      attrCreate.mutate(payload);
    }
  };

  return (
    <Box>
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Revizto Project Mappings</Typography>
        <Button variant="outlined" size="small" onClick={() => setRevDialogOpen(true)}>
          Add mapping
        </Button>
      </Stack>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Revizto Project UUID</TableCell>
              <TableCell>PM Project</TableCell>
              <TableCell>Override Name</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {revMappings.map((mapping: ReviztoProjectMapping) => (
              <TableRow key={mapping.revizto_project_uuid}>
                <TableCell>{mapping.revizto_project_uuid}</TableCell>
                <TableCell>
                  {mapping.pm_project_name ?? mapping.pm_project_id ?? '--'}
                </TableCell>
                <TableCell>{mapping.project_name_override ?? '--'}</TableCell>
                <TableCell align="right">
                  <Button
                    size="small"
                    color="error"
                    onClick={() => revDelete.mutate(mapping.revizto_project_uuid)}
                  >
                    Remove
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!revMappings.length && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography variant="body2" color="text.secondary">
                    No mappings yet.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Issue Attribute Mappings</Typography>
        <Button variant="outlined" size="small" onClick={() => openAttrDialog()}>
          Add mapping
        </Button>
      </Stack>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Source</TableCell>
              <TableCell>Project ID</TableCell>
              <TableCell>Raw Attribute</TableCell>
              <TableCell>Mapped Field</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {attrMappings.map((mapping) => (
              <TableRow key={mapping.map_id}>
                <TableCell>{mapping.source_system}</TableCell>
                <TableCell>{mapping.project_id ?? 'All'}</TableCell>
                <TableCell>{mapping.raw_attribute_name}</TableCell>
                <TableCell>{mapping.mapped_field_name}</TableCell>
                <TableCell>{mapping.priority ?? 100}</TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => openAttrDialog(mapping)}>
                    Edit
                  </Button>
                  <Button size="small" color="error" onClick={() => attrDelete.mutate(mapping.map_id)}>
                    Remove
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!attrMappings.length && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography variant="body2" color="text.secondary">
                    No attribute mappings yet.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={revDialogOpen} onClose={() => setRevDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Revizto Mapping</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Revizto Project UUID"
              value={revForm.revizto_project_uuid}
              onChange={(e) => setRevForm((prev) => ({ ...prev, revizto_project_uuid: e.target.value }))}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>PM Project</InputLabel>
              <Select
                label="PM Project"
                value={revForm.pm_project_id}
                onChange={(e) => setRevForm((prev) => ({ ...prev, pm_project_id: e.target.value }))}
              >
                <MenuItem value="">
                  <em>Unmapped</em>
                </MenuItem>
                {projectOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Project Name Override"
              value={revForm.project_name_override}
              onChange={(e) => setRevForm((prev) => ({ ...prev, project_name_override: e.target.value }))}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleRevSubmit}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={attrDialogOpen} onClose={() => setAttrDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingAttr ? 'Edit Attribute Mapping' : 'Add Attribute Mapping'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Project ID (optional)"
              value={attrForm.project_id}
              onChange={(e) => setAttrForm((prev) => ({ ...prev, project_id: e.target.value }))}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Source System</InputLabel>
              <Select
                label="Source System"
                value={attrForm.source_system}
                onChange={(e) => setAttrForm((prev) => ({ ...prev, source_system: e.target.value }))}
              >
                {SOURCE_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Raw Attribute Name"
              value={attrForm.raw_attribute_name}
              onChange={(e) => setAttrForm((prev) => ({ ...prev, raw_attribute_name: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Mapped Field Name"
              value={attrForm.mapped_field_name}
              onChange={(e) => setAttrForm((prev) => ({ ...prev, mapped_field_name: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Data Type"
              value={attrForm.data_type}
              onChange={(e) => setAttrForm((prev) => ({ ...prev, data_type: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Priority"
              value={attrForm.priority}
              onChange={(e) => setAttrForm((prev) => ({ ...prev, priority: e.target.value }))}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAttrDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAttrSubmit}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IssueMappingsTab;
