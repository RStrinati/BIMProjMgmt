/**
 * Simplified ACC Data Import Panel Component
 * Matches Tkinter functionality: Browse → Import → Show Import Logs
 * Removes bookmarks functionality that doesn't exist in backend
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  AlertTitle,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  FolderOpen as BrowseIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accDataImportApi } from '@/api/dataImports';
import { fileBrowserApi } from '@/api/fileBrowser';
import { formatDateTime } from '@/utils/dateUtils';

interface ACCDataImportPanelProps {
  projectId: number;
  projectName?: string;
}

export const ACCDataImportPanel: React.FC<ACCDataImportPanelProps> = ({
  projectId,
  projectName,
}) => {
  const queryClient = useQueryClient();
  const [filePath, setFilePath] = useState('');
  const [importType, setImportType] = useState<'csv' | 'zip'>('zip');

  // Query for import logs (matches Tkinter log display)
  const {
    data: logsData,
    isLoading: logsLoading,
    refetch: refetchLogs,
  } = useQuery({
    queryKey: ['accImportLogs', projectId],
    queryFn: () => accDataImportApi.getImportLogs(projectId),
    retry: 1,
  });

  // Mutation for importing data (matches Tkinter import function)
  const importMutation = useMutation({
    mutationFn: () =>
      accDataImportApi.importData(projectId, {
        file_path: filePath,
        import_type: importType,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accImportLogs', projectId] });
      queryClient.invalidateQueries({ queryKey: ['accIssues', projectId] });
      refetchLogs();
      setFilePath('');
    },
  });

  const handleImport = () => {
    if (filePath.trim()) {
      importMutation.mutate();
    }
  };

  // Browse function that matches Tkinter browse_acc_folder()
  const handleBrowseFile = async () => {
    try {
      if (importType === 'zip') {
        // Browse for ZIP file
        const result = await fileBrowserApi.selectFile({
          title: 'Select ACC Export ZIP File',
          file_types: [['ZIP Files', '*.zip'], ['All Files', '*.*']],
        });
        
        if (result.success && result.file_path) {
          setFilePath(result.file_path);
        }
      } else {
        // Browse for folder containing CSV files
        const result = await fileBrowserApi.selectFolder({
          title: 'Select ACC Export CSV Folder',
        });
        
        if (result.success && result.folder_path) {
          setFilePath(result.folder_path);
        }
      }
    } catch (error) {
      console.error('Error selecting file/folder:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status && status.toLowerCase().includes('success')) {
      return <CheckIcon fontSize="small" color="success" />;
    }
    if (status && status.toLowerCase().includes('error')) {
      return <ErrorIcon fontSize="small" color="error" />;
    }
    return <CheckIcon fontSize="small" color="success" />; // Default to success for completed imports
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header - matches Tkinter section title */}
      <Typography variant="h5" gutterBottom>
        ACC Data Import
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Import ACC Issues ZIP files or CSV folders for {projectName || `Project #${projectId}`}.
        This matches the functionality in the Tkinter "ACC Export CSV Import" section.
      </Typography>

      {/* Import Section - matches Tkinter Import ACC CSVs */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import ACC Data
        </Typography>

        {importMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Import Failed</AlertTitle>
            {importMutation.error instanceof Error
              ? importMutation.error.message
              : 'Failed to import ACC data'}
          </Alert>
        )}

        {importMutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            <AlertTitle>Import Complete</AlertTitle>
            {importMutation.data.message}
            {importMutation.data.execution_time_seconds && 
              ` (${importMutation.data.execution_time_seconds}s)`}
          </Alert>
        )}

        <Stack spacing={2}>
          {/* File/Folder selection - matches Tkinter browse functionality */}
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              label={importType === 'zip' ? 'ZIP File Path' : 'CSV Folder Path'}
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder={
                importType === 'zip' 
                  ? 'C:\\Downloads\\autodesk_data_extract_PROJECT.zip'
                  : 'C:\\Data\\ACC\\CSVs\\'
              }
              disabled={importMutation.isPending}
              helperText="Select ACC export ZIP file or CSV folder containing issues data"
            />
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={importType}
                label="Type"
                onChange={(e) => setImportType(e.target.value as 'csv' | 'zip')}
                disabled={importMutation.isPending}
              >
                <MenuItem value="zip">ZIP File</MenuItem>
                <MenuItem value="csv">CSV Folder</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<BrowseIcon />}
              onClick={handleBrowseFile}
              disabled={importMutation.isPending}
              sx={{ minWidth: 120 }}
            >
              Browse
            </Button>
          </Stack>

          {/* Action buttons - matches Tkinter Import ACC CSVs button */}
          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<UploadIcon />}
              onClick={handleImport}
              disabled={!filePath.trim() || importMutation.isPending}
              size="large"
            >
              {importMutation.isPending ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Importing...
                </>
              ) : (
                'Import ACC Data'
              )}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetchLogs()}
              disabled={logsLoading}
            >
              Refresh Logs
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Import History - matches Tkinter log_list display */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import History
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Shows previous ACC data imports for this project (matches Tkinter log display).
        </Typography>

        {logsLoading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : !logsData?.logs || logsData.logs.length === 0 ? (
          <Alert severity="info">
            No previous ACC imports found for this project.
          </Alert>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Import Date</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Summary</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logsData.logs.map((log, index) => (
                  <TableRow key={index} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getStatusIcon('success')}
                        <Typography variant="body2" color="success.main">
                          Success
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDateTime(log.import_date)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {log.folder_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap title={log.summary}>
                        {log.summary?.substring(0, 80)}
                        {log.summary && log.summary.length > 80 ? '...' : ''}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};