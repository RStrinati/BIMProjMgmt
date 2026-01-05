import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import ClientsTab from '../components/settings/ClientsTab';
import ServiceTemplatesTab from '../components/settings/ServiceTemplatesTab';
import ProjectAliasesTab from '../components/settings/ProjectAliasesTab';
import NamingConventionsTab from '../components/settings/NamingConventionsTab';
import UsersTab from '../components/settings/UsersTab';

interface ProjectType {
  type_id: number;
  type_name: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SettingsPage() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Paper sx={{ width: '100%', mt: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="settings tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Project Types" />
          <Tab label="Clients" />
          <Tab label="Service Templates" />
          <Tab label="Project Aliases" />
          <Tab label="Naming Conventions" />
          <Tab label="Users" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <ProjectTypesTab />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ClientsTab />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ServiceTemplatesTab />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <ProjectAliasesTab />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <NamingConventionsTab />
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          <UsersTab />
        </TabPanel>
      </Paper>
    </Container>
  );
}

// Project Types Tab Component
function ProjectTypesTab() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingType, setEditingType] = useState<ProjectType | null>(null);
  const [typeName, setTypeName] = useState('');
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  // Fetch project types
  const { data: projectTypes, isLoading } = useQuery<ProjectType[]>({
    queryKey: ['reference', 'project_types'],
    queryFn: async () => {
      const response = await apiClient.get<ProjectType[]>('/reference/project_types');
      return response.data;
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      const response = await apiClient.post('/reference/project_types', { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to create project type');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, name }: { id: number; name: string }) => {
      const response = await apiClient.put(`/reference/project_types/${id}`, { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
      handleCloseDialog();
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || 'Failed to update project type');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/reference/project_types/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference', 'project_types'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.error || 'Failed to delete project type');
    },
  });

  const handleOpenCreate = () => {
    setEditingType(null);
    setTypeName('');
    setError('');
    setDialogOpen(true);
  };

  const handleOpenEdit = (type: ProjectType) => {
    setEditingType(type);
    setTypeName(type.type_name);
    setError('');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingType(null);
    setTypeName('');
    setError('');
  };

  const handleSave = () => {
    if (!typeName.trim()) {
      setError('Project type name is required');
      return;
    }

    if (editingType) {
      updateMutation.mutate({ id: editingType.type_id, name: typeName.trim() });
    } else {
      createMutation.mutate(typeName.trim());
    }
  };

  const handleDelete = (type: ProjectType) => {
    if (window.confirm(`Are you sure you want to delete "${type.type_name}"?`)) {
      deleteMutation.mutate(type.type_id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ px: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Project Types</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
        >
          Add Project Type
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projectTypes?.map((type) => (
              <TableRow key={type.type_id}>
                <TableCell>{type.type_id}</TableCell>
                <TableCell>{type.type_name}</TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleOpenEdit(type)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(type)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingType ? 'Edit Project Type' : 'Create Project Type'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Project Type Name"
            type="text"
            fullWidth
            variant="outlined"
            value={typeName}
            onChange={(e) => setTypeName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSave();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <CircularProgress size={24} />
            ) : (
              'Save'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

