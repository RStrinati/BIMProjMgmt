/**
 * Revit Health Check Panel Component
 * Displays Revit health check files and summary statistics
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
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
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  TextField,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  FolderOpen as BrowseIcon,
  PlayArrow as RunIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { revitHealthApi } from '@/api/dataImports';
import { fileBrowserApi, scriptApi } from '@/api/fileBrowser';
import { formatDate } from '@/utils/dateUtils';

interface RevitHealthPanelProps {
  projectId: number;
  projectName?: string;
}

export const RevitHealthPanel: React.FC<RevitHealthPanelProps> = ({
  projectId,
  projectName,
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [importFolder, setImportFolder] = useState('');
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  // Query for health files
  const {
    data: filesData,
    isLoading: filesLoading,
    refetch: refetchFiles,
  } = useQuery({
    queryKey: ['revitHealthFiles', projectId, page, rowsPerPage],
    queryFn: () => revitHealthApi.getHealthFiles(projectId, page + 1, rowsPerPage),
  });

  // Query for summary
  const {
    data: summary,
    isLoading: summaryLoading,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['revitHealthSummary', projectId],
    queryFn: () => revitHealthApi.getSummary(projectId),
  });

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleRefresh = () => {
    refetchFiles();
    refetchSummary();
  };

  const handleBrowseFolder = async () => {
    try {
      const result = await fileBrowserApi.selectFolder({
        title: 'Select Revit Health Check Export Folder',
      });
      
      if (result.success && result.folder_path) {
        setImportFolder(result.folder_path);
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
    }
  };

  const handleRunImporter = async () => {
    if (!importFolder.trim()) {
      setImportError('Please select a folder first');
      return;
    }

    try {
      setImporting(true);
      setImportError(null);
      setImportSuccess(null);
      const result = await scriptApi.runHealthImporter({
        folder_path: importFolder,
        project_id: projectId,
      });
      if (result.success) {
        setImportSuccess(
          `Import of combined file completed successfully in ${result.execution_time_seconds}s`
        );
        refetchFiles();
        refetchSummary();
        setImportFolder('');
      } else {
        setImportError(result.error || 'Import failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to run health importer';
      setImportError(errorMessage);
      console.error('Error running health importer:', error);
    } finally {
      setImporting(false);
    }
  };

  const getHealthScoreColor = (score: number | null): 'success' | 'warning' | 'error' | 'default' => {
    if (score === null) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getHealthScoreLabel = (score: number | null): string => {
    if (score === null) return 'Unknown';
    if (score >= 80) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Poor';
  };

  const formatFileSize = (sizeMb: number | null): string => {
    if (sizeMb === null) return 'N/A';
    if (sizeMb < 1) return `${(sizeMb * 1024).toFixed(1)} KB`;
    if (sizeMb < 1024) return `${sizeMb.toFixed(1)} MB`;
    return `${(sizeMb / 1024).toFixed(2)} GB`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h5" gutterBottom>
        Revit Health Check
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        View and analyze Revit model health check data for {projectName || `Project #${projectId}`}.
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Total Files
                  </Typography>
                  <Typography variant="h4">
                    {summaryLoading ? <CircularProgress size={24} /> : filesData?.total_count || 0}
                  </Typography>
                </Box>
                <AssessmentIcon color="primary" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Avg Health Score
                  </Typography>
                  <Typography variant="h4">
                    {summaryLoading ? (
                      <CircularProgress size={24} />
                    ) : summary?.avg_health_score ? (
                      `${Math.round(summary.avg_health_score)}%`
                    ) : (
                      'N/A'
                    )}
                  </Typography>
                </Box>
                <TrendingUpIcon color="success" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Total Warnings
                  </Typography>
                  <Typography variant="h4">
                    {summaryLoading ? <CircularProgress size={24} /> : summary?.total_warnings || 0}
                  </Typography>
                </Box>
                <WarningIcon color="warning" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="caption" gutterBottom>
                    Total Errors
                  </Typography>
                  <Typography variant="h4">
                    {summaryLoading ? <CircularProgress size={24} /> : summary?.total_errors || 0}
                  </Typography>
                </Box>
                <ErrorIcon color="error" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Latest Check Info */}
      {summary?.latest_check_date && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Latest health check: {formatDate(summary.latest_check_date, 'MMMM d, yyyy')}
        </Alert>
      )}

      {/* Control Buttons */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import Health Check Data
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select a folder containing Revit health check JSON exports and run the importer.
        </Typography>

        {importError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setImportError(null)}>
            {importError}
          </Alert>
        )}

        {importSuccess && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setImportSuccess(null)}>
            {importSuccess}
          </Alert>
        )}

        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            fullWidth
            label="Health Check Export Folder"
            value={importFolder}
            onChange={(e) => setImportFolder(e.target.value)}
            placeholder="C:\Exports\RevitHealth\ProjectName"
            disabled={importing}
            helperText="Folder containing Revit health check JSON files"
          />
          <Button
            variant="outlined"
            startIcon={<BrowseIcon />}
            onClick={handleBrowseFolder}
            disabled={importing}
            sx={{ minWidth: 120 }}
          >
            Browse
          </Button>
        </Stack>

        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={importing ? <CircularProgress size={20} /> : <RunIcon />}
            onClick={handleRunImporter}
            disabled={!importFolder.trim() || importing}
          >
            {importing ? 'Importing...' : 'Run Health Importer'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={filesLoading || summaryLoading || importing}
          >
            Refresh
          </Button>
        </Stack>
      </Paper>

      {/* Health Files Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Health Check Files ({filesData?.total_count || 0})
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
                    <TableCell>Check Date</TableCell>
                    <TableCell align="center">Health Score</TableCell>
                    <TableCell align="right">Warnings</TableCell>
                    <TableCell align="right">Errors</TableCell>
                    <TableCell align="right">File Size</TableCell>
                    <TableCell>Uploaded By</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filesData.files.map((file) => (
                    <TableRow key={file.id} hover>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
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
                        <Typography variant="body2" noWrap>
                          {formatDate(file.check_date, 'MMM d, yyyy')}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="center">
                          {file.health_score !== null ? (
                            <>
                              <Chip
                                label={`${file.health_score}%`}
                                color={getHealthScoreColor(file.health_score)}
                                size="small"
                                icon={
                                  file.health_score >= 80 ? (
                                    <CheckCircleIcon />
                                  ) : file.health_score >= 60 ? (
                                    <WarningIcon />
                                  ) : (
                                    <ErrorIcon />
                                  )
                                }
                              />
                              <Typography variant="caption" color="text.secondary">
                                {getHealthScoreLabel(file.health_score)}
                              </Typography>
                            </>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              N/A
                            </Typography>
                          )}
                        </Stack>
                      </TableCell>
                      <TableCell align="right">
                        {file.total_warnings !== null ? (
                          <Chip
                            label={file.total_warnings}
                            color={file.total_warnings > 0 ? 'warning' : 'default'}
                            size="small"
                          />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {file.total_errors !== null ? (
                          <Chip
                            label={file.total_errors}
                            color={file.total_errors > 0 ? 'error' : 'default'}
                            size="small"
                          />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" noWrap>
                          {formatFileSize(file.file_size_mb)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {file.uploaded_by || 'Unknown'}
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
            No health check files found. Upload Revit health check data to see results here.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};
