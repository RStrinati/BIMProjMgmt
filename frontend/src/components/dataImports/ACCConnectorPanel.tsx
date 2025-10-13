/**
 * ACC Desktop Connector Panel Component
 * Allows users to configure ACC folder path and extract files to database
 */

import React, { useState, useEffect } from 'react';
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
  TablePagination,
  Chip,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  FolderOpen as FolderIcon,
  Refresh as RefreshIcon,
  CloudDownload as ExtractIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accConnectorApi } from '@/api/dataImports';
import { formatDateTime } from '@/utils/dateUtils';

interface ACCConnectorPanelProps {
  projectId: number;
  projectName?: string;
}

export const ACCConnectorPanel: React.FC<ACCConnectorPanelProps> = ({
  projectId,
  projectName,
}) => {
  const queryClient = useQueryClient();
  const [folderPath, setFolderPath] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Query for current folder configuration
  const {
    data: folderData,
    isLoading: folderLoading,
    error: folderError,
  } = useQuery({
    queryKey: ['accConnectorFolder', projectId],
    queryFn: () => accConnectorApi.getFolder(projectId),
  });

  // Query for extracted files
  const {
    data: filesData,
    isLoading: filesLoading,
    refetch: refetchFiles,
  } = useQuery({
    queryKey: ['accConnectorFiles', projectId, page, rowsPerPage],
    queryFn: () => accConnectorApi.getFiles(projectId, page + 1, rowsPerPage),
  });

  // Mutation for saving folder path
  const saveFolderMutation = useMutation({
    mutationFn: (path: string) => accConnectorApi.saveFolder(projectId, path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accConnectorFolder', projectId] });
    },
  });

  // Mutation for extracting files
  const extractFilesMutation = useMutation({
    mutationFn: () =>
      accConnectorApi.extractFiles(projectId, {
        folder_path: folderPath || folderData?.folder_path || '',
        file_types: [],
        recursive: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accConnectorFiles', projectId] });
      refetchFiles();
    },
  });

  // Update local state when folder data is loaded
  useEffect(() => {
    if (folderData?.folder_path) {
      setFolderPath(folderData.folder_path);
    }
  }, [folderData]);

  const handleSaveFolder = () => {
    if (folderPath.trim()) {
      saveFolderMutation.mutate(folderPath);
    }
  };

  const handleExtractFiles = () => {
    extractFilesMutation.mutate();
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatFileSize = (bytes: number | null): string => {
    if (bytes === null) return 'Unknown';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(2)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h5" gutterBottom>
        ACC Desktop Connector
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure the Autodesk Construction Cloud desktop folder path and extract files to the
        database for {projectName || `Project #${projectId}`}.
      </Typography>

      {/* Folder Configuration Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Folder Configuration
        </Typography>

        {folderError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Error</AlertTitle>
            Failed to load folder configuration. Please try again.
          </Alert>
        )}

        {saveFolderMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Save Failed</AlertTitle>
            {saveFolderMutation.error instanceof Error
              ? saveFolderMutation.error.message
              : 'Failed to save folder path'}
          </Alert>
        )}

        {saveFolderMutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Folder path saved successfully!
          </Alert>
        )}

        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            fullWidth
            label="ACC Desktop Connector Folder Path"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="C:\Users\YourName\Autodesk\ACC\ProjectName"
            disabled={folderLoading || saveFolderMutation.isPending}
            helperText={
              folderData?.exists === false
                ? 'Warning: This folder path does not exist on the file system'
                : 'Full path to the ACC desktop connector folder on your PC'
            }
            error={folderData?.exists === false}
            InputProps={{
              startAdornment: <FolderIcon sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />
          <Button
            variant="contained"
            onClick={handleSaveFolder}
            disabled={!folderPath.trim() || saveFolderMutation.isPending}
            sx={{ minWidth: 120 }}
          >
            {saveFolderMutation.isPending ? <CircularProgress size={24} /> : 'Save Path'}
          </Button>
        </Stack>

        {folderData?.folder_path && (
          <Box sx={{ mt: 2 }}>
            <Chip
              icon={folderData.exists ? <CheckIcon /> : <ErrorIcon />}
              label={folderData.exists ? 'Folder exists' : 'Folder not found'}
              color={folderData.exists ? 'success' : 'error'}
              size="small"
            />
          </Box>
        )}
      </Paper>

      {/* File Extraction Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          File Extraction
        </Typography>

        {extractFilesMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Extraction Failed</AlertTitle>
            {extractFilesMutation.error instanceof Error
              ? extractFilesMutation.error.message
              : 'Failed to extract files'}
          </Alert>
        )}

        {extractFilesMutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            <AlertTitle>Extraction Complete</AlertTitle>
            {extractFilesMutation.data.files_extracted} files extracted successfully!
          </Alert>
        )}

        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<ExtractIcon />}
            onClick={handleExtractFiles}
            disabled={
              !folderData?.folder_path ||
              !folderData.exists ||
              extractFilesMutation.isPending
            }
          >
            {extractFilesMutation.isPending ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Extracting...
              </>
            ) : (
              'Extract Files'
            )}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetchFiles()}
            disabled={filesLoading}
          >
            Refresh List
          </Button>
        </Stack>
      </Paper>

      {/* Extracted Files Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Extracted Files ({filesData?.total_count || 0})
        </Typography>

        {filesLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filesData && filesData.files.length > 0 ? (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>File Name</TableCell>
                    <TableCell>File Path</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Size</TableCell>
                    <TableCell>Date Modified</TableCell>
                    <TableCell>Date Extracted</TableCell>
                    <TableCell>Extracted By</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filesData.files.map((file) => (
                    <TableRow key={file.id} hover>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {file.file_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={file.file_path}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                            {file.file_path}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip label={file.file_extension || 'Unknown'} size="small" />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" noWrap>
                          {formatFileSize(file.file_size)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {formatDateTime(file.date_modified, 'N/A')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {formatDateTime(file.date_extracted, 'N/A')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {file.extracted_by || 'Unknown'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={filesData.total_count}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </>
        ) : (
          <Alert severity="info">
            No files extracted yet. Click "Extract Files" to scan the ACC connector folder.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};
