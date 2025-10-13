/**
 * ACC Data Import Panel Component
 * Handles CSV/ZIP file imports from ACC and bookmark management
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
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  Bookmark as BookmarkIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  FolderOpen as BrowseIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accDataImportApi } from '@/api/dataImports';
import { fileBrowserApi } from '@/api/fileBrowser';
import { formatDate, formatDateTime } from '@/utils/dateUtils';

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
  const [importType, setImportType] = useState<'csv' | 'zip'>('csv');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [bookmarkDialogOpen, setBookmarkDialogOpen] = useState(false);
  const [newBookmarkName, setNewBookmarkName] = useState('');

  // Query for import logs
  const {
    data: logsData,
    isLoading: logsLoading,
    refetch: refetchLogs,
  } = useQuery({
    queryKey: ['accImportLogs', projectId, page, rowsPerPage],
    queryFn: () => accDataImportApi.getImportLogs(projectId, page + 1, rowsPerPage),
  });

  // Query for bookmarks
  const {
    data: bookmarks,
    isLoading: bookmarksLoading,
    refetch: refetchBookmarks,
  } = useQuery({
    queryKey: ['accBookmarks', projectId],
    queryFn: () => accDataImportApi.getBookmarks(projectId),
  });

  // Mutation for importing data
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

  // Mutation for adding bookmark
  const addBookmarkMutation = useMutation({
    mutationFn: (name: string) =>
      accDataImportApi.addBookmark(projectId, name, filePath, importType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accBookmarks', projectId] });
      refetchBookmarks();
      setBookmarkDialogOpen(false);
      setNewBookmarkName('');
    },
  });

  // Mutation for deleting bookmark
  const deleteBookmarkMutation = useMutation({
    mutationFn: (bookmarkId: number) => accDataImportApi.deleteBookmark(projectId, bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accBookmarks', projectId] });
      refetchBookmarks();
    },
  });

  const handleImport = () => {
    if (filePath.trim()) {
      importMutation.mutate();
    }
  };

  const handleBrowseFile = async () => {
    try {
      const fileTypes: [string, string][] = 
        importType === 'zip' 
          ? [['ZIP Files', '*.zip'], ['All Files', '*.*']]
          : [['CSV Files', '*.csv'], ['All Files', '*.*']];
      
      const result = await fileBrowserApi.selectFile({
        title: `Select ${importType.toUpperCase()} File`,
        file_types: fileTypes,
      });
      
      if (result.success && result.file_path) {
        setFilePath(result.file_path);
      }
    } catch (error) {
      console.error('Error selecting file:', error);
    }
  };

  const handleAddBookmark = () => {
    if (newBookmarkName.trim() && filePath.trim()) {
      addBookmarkMutation.mutate(newBookmarkName);
    }
  };

  const handleLoadBookmark = (bookmark: any) => {
    setFilePath(bookmark.file_path);
    setImportType(bookmark.import_type);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'completed':
        return 'success';
      case 'error':
      case 'failed':
        return 'error';
      case 'pending':
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h5" gutterBottom>
        ACC Data Import
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Import ACC data from CSV or ZIP files for {projectName || `Project #${projectId}`}.
      </Typography>

      {/* Import Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import Data
        </Typography>

        {importMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Import Failed</AlertTitle>
            {importMutation.error instanceof Error
              ? importMutation.error.message
              : 'Failed to import data'}
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
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              label="File Path"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="C:\Data\ACC\export.csv or C:\Data\ACC\issues.zip"
              disabled={importMutation.isPending}
              helperText="Full path to CSV or ZIP file containing ACC data"
            />
            <Button
              variant="outlined"
              startIcon={<BrowseIcon />}
              onClick={handleBrowseFile}
              disabled={importMutation.isPending}
              sx={{ minWidth: 120 }}
            >
              Browse
            </Button>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={importType}
                label="Type"
                onChange={(e) => setImportType(e.target.value as 'csv' | 'zip')}
                disabled={importMutation.isPending}
              >
                <MenuItem value="csv">CSV</MenuItem>
                <MenuItem value="zip">ZIP</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<UploadIcon />}
              onClick={handleImport}
              disabled={!filePath.trim() || importMutation.isPending}
            >
              {importMutation.isPending ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Importing...
                </>
              ) : (
                'Import Data'
              )}
            </Button>
            <Button
              variant="outlined"
              startIcon={<BookmarkIcon />}
              onClick={() => setBookmarkDialogOpen(true)}
              disabled={!filePath.trim()}
            >
              Save Bookmark
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetchLogs()}
              disabled={logsLoading}
            >
              Refresh
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Bookmarks Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Bookmarks ({bookmarks?.length || 0})
        </Typography>

        {bookmarksLoading ? (
          <CircularProgress size={24} />
        ) : bookmarks && bookmarks.length > 0 ? (
          <List dense>
            {bookmarks.map((bookmark) => (
              <ListItem
                key={bookmark.id}
                button
                onClick={() => handleLoadBookmark(bookmark)}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                <ListItemText
                  primary={bookmark.bookmark_name}
                  secondary={
                    <>
                      <Typography variant="caption" component="span" display="block">
                        {bookmark.file_path}
                      </Typography>
                      <Chip
                        label={bookmark.import_type.toUpperCase()}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                      {bookmark.last_used && (
                        <Typography variant="caption" component="span" display="block">
                          Last used: {formatDate(bookmark.last_used, 'MMM d, yyyy')}
                        </Typography>
                      )}
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteBookmarkMutation.mutate(bookmark.id);
                    }}
                    disabled={deleteBookmarkMutation.isPending}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        ) : (
          <Alert severity="info">
            No bookmarks saved yet. Save frequently used import paths for quick access.
          </Alert>
        )}
      </Paper>

      {/* Import Logs Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import History ({logsData?.total_count || 0})
        </Typography>

        {logsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : logsData && logsData.logs.length > 0 ? (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Import Date</TableCell>
                    <TableCell>File Path</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Records</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Imported By</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logsData.logs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        {formatDateTime(log.import_date)}
                      </TableCell>
                      <TableCell>
                        <Tooltip title={log.file_path}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                            {log.file_path}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip label={log.import_type.toUpperCase()} size="small" />
                      </TableCell>
                      <TableCell align="right">{log.records_imported}</TableCell>
                      <TableCell>
                        <Chip
                          label={log.status}
                          color={getStatusColor(log.status)}
                          size="small"
                          icon={
                            log.status.toLowerCase() === 'success' ? (
                              <CheckIcon />
                            ) : log.status.toLowerCase() === 'error' ? (
                              <ErrorIcon />
                            ) : undefined
                          }
                        />
                      </TableCell>
                      <TableCell>{log.imported_by || 'Unknown'}</TableCell>
                      <TableCell>
                        {log.error_message && (
                          <Tooltip title={log.error_message}>
                            <ErrorIcon color="error" fontSize="small" />
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={logsData.total_count}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </>
        ) : (
          <Alert severity="info">
            No import history yet. Import data to see logs here.
          </Alert>
        )}
      </Paper>

      {/* Bookmark Dialog */}
      <Dialog open={bookmarkDialogOpen} onClose={() => setBookmarkDialogOpen(false)}>
        <DialogTitle>Save Import Bookmark</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Bookmark Name"
            fullWidth
            value={newBookmarkName}
            onChange={(e) => setNewBookmarkName(e.target.value)}
            placeholder="e.g., Weekly ACC Issues Import"
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Path: {filePath}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Type: {importType.toUpperCase()}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBookmarkDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddBookmark}
            variant="contained"
            disabled={!newBookmarkName.trim() || addBookmarkMutation.isPending}
          >
            {addBookmarkMutation.isPending ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
