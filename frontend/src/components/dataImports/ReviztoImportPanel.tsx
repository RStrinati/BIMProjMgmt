/**
 * Revizto Import Panel Component
 * Manages Revizto extraction runs
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
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  FolderOpen as BrowseIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviztoApi } from '@/api/dataImports';
import { fileBrowserApi, applicationApi } from '@/api/fileBrowser';
import { formatDateTime } from '@/utils/dateUtils';

interface ReviztoImportPanelProps {
  projectId?: number;
  projectName?: string;
}

export const ReviztoImportPanel: React.FC<ReviztoImportPanelProps> = ({
  projectId,
  projectName,
}) => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [startDialogOpen, setStartDialogOpen] = useState(false);
  const [exportFolder, setExportFolder] = useState('');
  const [launchingApp, setLaunchingApp] = useState(false);
  const [appLaunchError, setAppLaunchError] = useState<string | null>(null);

  // Query for extraction runs
  const {
    data: runsData,
    isLoading: runsLoading,
    refetch: refetchRuns,
  } = useQuery({
    queryKey: ['reviztoExtractionRuns', page, rowsPerPage],
    queryFn: () => reviztoApi.getExtractionRuns(page + 1, rowsPerPage),
  });

  // Query for last run
  const {
    data: lastRun,
    isLoading: lastRunLoading,
    refetch: refetchLastRun,
  } = useQuery({
    queryKey: ['reviztoLastRun'],
    queryFn: () => reviztoApi.getLastRun(),
    retry: false,
  });

  // Mutation for starting extraction
  const startExtractionMutation = useMutation({
    mutationFn: () =>
      reviztoApi.startExtraction({
        project_id: projectId,
        export_folder: exportFolder,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviztoExtractionRuns'] });
      queryClient.invalidateQueries({ queryKey: ['reviztoLastRun'] });
      refetchRuns();
      refetchLastRun();
      setStartDialogOpen(false);
      setExportFolder('');
    },
  });

  const handleStartExtraction = () => {
    if (exportFolder.trim()) {
      startExtractionMutation.mutate();
    }
  };

  const handleBrowseFolder = async () => {
    try {
      const result = await fileBrowserApi.selectFolder({
        title: 'Select Revizto Export Folder',
      });
      
      if (result.success && result.folder_path) {
        setExportFolder(result.folder_path);
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
    }
  };

  const handleLaunchReviztoExporter = async () => {
    try {
      setLaunchingApp(true);
      setAppLaunchError(null);
      
      const result = await applicationApi.launchReviztoExporter();
      
      if (!result.success) {
        setAppLaunchError(result.error || 'Failed to launch Revizto Data Exporter');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to launch application';
      setAppLaunchError(errorMessage);
      console.error('Error launching Revizto Data Exporter:', error);
    } finally {
      setLaunchingApp(false);
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('success') || statusLower.includes('completed')) return 'success';
    if (statusLower.includes('error') || statusLower.includes('failed')) return 'error';
    if (statusLower.includes('pending') || statusLower.includes('running')) return 'warning';
    return 'default';
  };

  const getStatusIcon = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('success') || statusLower.includes('completed'))
      return <CheckIcon fontSize="small" />;
    if (statusLower.includes('error') || statusLower.includes('failed'))
      return <ErrorIcon fontSize="small" />;
    if (statusLower.includes('pending') || statusLower.includes('running'))
      return <PendingIcon fontSize="small" />;
    return <></>;
  };

  const formatDuration = (startTime: string, endTime: string | null): string => {
    if (!endTime) return 'In progress...';
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    const durationMs = end - start;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h5" gutterBottom>
        Revizto Data Extraction
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage Revizto issue extraction runs
        {projectName && ` for ${projectName}`}.
      </Typography>

      {/* Last Run Summary */}
      {!lastRunLoading && lastRun && (
        <Paper sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
          <Typography variant="h6" gutterBottom>
            Last Extraction Run
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Chip
              label={`Run ID: ${lastRun.run_id}`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={lastRun.status}
              color={getStatusColor(lastRun.status)}
              icon={getStatusIcon(lastRun.status)}
              size="small"
            />
            <Chip
              label={`${lastRun.records_extracted || 0} records`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={formatDateTime(lastRun.start_time)}
              variant="outlined"
              size="small"
            />
          </Stack>
          {lastRun.error_message && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {lastRun.error_message}
            </Alert>
          )}
        </Paper>
      )}

      {/* Control Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Start New Extraction
        </Typography>

        {appLaunchError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setAppLaunchError(null)}>
            <AlertTitle>Launch Failed</AlertTitle>
            {appLaunchError}
          </Alert>
        )}

        {startExtractionMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Extraction Failed</AlertTitle>
            {startExtractionMutation.error instanceof Error
              ? startExtractionMutation.error.message
              : 'Failed to start extraction'}
          </Alert>
        )}

        {startExtractionMutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            <AlertTitle>Extraction Started</AlertTitle>
            Run ID: {startExtractionMutation.data.run_id}
          </Alert>
        )}

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={launchingApp ? <CircularProgress size={20} /> : <LaunchIcon />}
            onClick={handleLaunchReviztoExporter}
            disabled={launchingApp}
          >
            {launchingApp ? 'Launching...' : 'Launch Revizto Data Exporter'}
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<StartIcon />}
            onClick={() => setStartDialogOpen(true)}
            disabled={startExtractionMutation.isPending}
          >
            {startExtractionMutation.isPending ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Starting...
              </>
            ) : (
              'Start Extraction'
            )}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              refetchRuns();
              refetchLastRun();
            }}
            disabled={runsLoading}
          >
            Refresh
          </Button>
        </Stack>
      </Paper>

      {/* Extraction Runs Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Extraction History ({runsData?.total_count || 0})
        </Typography>

        {runsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : runsData && runsData.runs.length > 0 ? (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Run ID</TableCell>
                    <TableCell>Export Folder</TableCell>
                    <TableCell>Start Time</TableCell>
                    <TableCell>End Time</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell align="right">Records</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Extracted By</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {runsData.runs.map((run) => (
                    <TableRow key={run.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {run.run_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={run.export_folder}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {run.export_folder}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {formatDateTime(run.start_time)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {run.end_time
                            ? formatDateTime(run.end_time)
                            : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {formatDuration(run.start_time, run.end_time)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {run.records_extracted !== null ? run.records_extracted : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={run.status}
                          color={getStatusColor(run.status)}
                          size="small"
                          icon={getStatusIcon(run.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {run.extracted_by || 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {run.error_message && (
                          <Tooltip title={run.error_message}>
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
              count={runsData.total_count}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </>
        ) : (
          <Alert severity="info">
            No extraction runs yet. Click "Start Extraction" to begin.
          </Alert>
        )}
      </Paper>

      {/* Start Extraction Dialog */}
      <Dialog open={startDialogOpen} onClose={() => setStartDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start New Revizto Extraction</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Specify the export folder path where Revizto data will be extracted.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <TextField
              autoFocus
              margin="dense"
              label="Export Folder Path"
              fullWidth
              value={exportFolder}
              onChange={(e) => setExportFolder(e.target.value)}
              placeholder="C:\Exports\Revizto\ProjectName"
              helperText="Full path to the folder where extraction output will be saved"
            />
            <Button
              variant="outlined"
              startIcon={<BrowseIcon />}
              onClick={handleBrowseFolder}
              sx={{ mt: 1, minWidth: 120 }}
            >
              Browse
            </Button>
          </Stack>
          {projectId && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              This extraction will be associated with Project #{projectId}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStartDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStartExtraction}
            variant="contained"
            disabled={!exportFolder.trim() || startExtractionMutation.isPending}
            startIcon={startExtractionMutation.isPending ? <CircularProgress size={16} /> : <StartIcon />}
          >
            {startExtractionMutation.isPending ? 'Starting...' : 'Start Extraction'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
