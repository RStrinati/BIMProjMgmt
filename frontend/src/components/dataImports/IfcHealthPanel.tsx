/**
 * IFC Health Check Panel
 * Runs IFC + IDS validation with upload, results, and IDS test management.
 */

import React, { useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Tab,
  Tabs,
  TextField,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  Paper,
  Stack,
  Divider,
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  UploadFile as UploadFileIcon,
  CloudUpload as SaveIcon,
  History as HistoryIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ifcValidationApi } from '@/api/ifcValidation';
import { qualityApi } from '@/api/quality';
import type { IfcValidationFailure, IfcValidationResult, IfcValidationRun, IfcIdsTest } from '@/types/ifcValidation';
import type { ExpectedModel } from '@/types/api';

interface IfcHealthPanelProps {
  projectId: number;
  projectName?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export const IfcHealthPanel: React.FC<IfcHealthPanelProps> = ({ projectId, projectName }) => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(0);
  const [ifcFile, setIfcFile] = useState<File | null>(null);
  const [idsFile, setIdsFile] = useState<File | null>(null);
  const [idsTestId, setIdsTestId] = useState<number | ''>('');
  const [expectedModelId, setExpectedModelId] = useState<number | ''>('');
  const [saveIdsTest, setSaveIdsTest] = useState(false);
  const [idsName, setIdsName] = useState('');
  const [runResult, setRunResult] = useState<IfcValidationResult | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const replaceInputRef = useRef<HTMLInputElement | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<IfcIdsTest | null>(null);

  const { data: idsTests = [] } = useQuery({
    queryKey: ['ifc-ids-tests', projectId],
    queryFn: () => ifcValidationApi.listIdsTests(projectId),
  });

  const { data: expectedModels = [] } = useQuery<ExpectedModel[]>({
    queryKey: ['expectedModels', projectId],
    queryFn: () => qualityApi.listExpectedModels(projectId),
  });

  const { data: runs = [] } = useQuery({
    queryKey: ['ifc-validation-runs', projectId],
    queryFn: () => ifcValidationApi.listRuns(projectId),
    refetchInterval: (data) => {
      if (!data) return 10000;
      if (!Array.isArray(data)) return false;
      const hasActive = data.some((run: IfcValidationRun) =>
        ['queued', 'running'].includes(run.status),
      );
      return hasActive ? 8000 : false;
    },
  });

  const { data: runDetail } = useQuery({
    queryKey: ['ifc-validation-run', projectId, runId],
    queryFn: () => ifcValidationApi.getRun(projectId, runId!),
    enabled: runId !== null,
    refetchInterval: (data) => {
      const status = data?.run?.status;
      return status === 'queued' || status === 'running' ? 5000 : false;
    },
  });

  const runMutation = useMutation({
    mutationFn: () => {
      if (!ifcFile) {
        throw new Error('Please select an IFC file.');
      }
      if (!idsFile && idsTestId === '') {
        throw new Error('Please select an IDS file or a saved IDS test.');
      }
      return ifcValidationApi.runValidation(projectId, {
        ifc_file: ifcFile,
        ids_file: idsFile || undefined,
        ids_test_id: idsTestId === '' ? undefined : Number(idsTestId),
        expected_model_id: expectedModelId === '' ? undefined : Number(expectedModelId),
        save_ids_test: saveIdsTest,
        ids_name: idsName || undefined,
      });
    },
    onSuccess: (data) => {
      setStatusMessage(data.message || 'Validation started.');
      setErrorMessage(null);
      setRunId(data.run_id);
      if (data.result) {
        setRunResult(data.result);
      }
      queryClient.invalidateQueries({ queryKey: ['ifc-validation-runs', projectId] });
    },
    onError: (error: any) => {
      setErrorMessage(error?.message || 'Validation failed');
    },
  });

  const createIdsMutation = useMutation({
    mutationFn: () => {
      if (!idsFile) {
        throw new Error('Select an IDS file to save.');
      }
      return ifcValidationApi.createIdsTest(projectId, {
        ids_name: idsName || idsFile.name,
        ids_file: idsFile,
      });
    },
    onSuccess: () => {
      setStatusMessage('IDS test saved.');
      queryClient.invalidateQueries({ queryKey: ['ifc-ids-tests', projectId] });
    },
    onError: (error: any) => {
      setErrorMessage(error?.message || 'Failed to save IDS test.');
    },
  });

  const updateIdsMutation = useMutation({
    mutationFn: ({ idsTestId, idsFile }: { idsTestId: number; idsFile: File }) =>
      ifcValidationApi.updateIdsTest(projectId, idsTestId, { ids_file: idsFile }),
    onSuccess: () => {
      setStatusMessage('IDS test updated.');
      queryClient.invalidateQueries({ queryKey: ['ifc-ids-tests', projectId] });
    },
    onError: (error: any) => {
      setErrorMessage(error?.message || 'Failed to update IDS test.');
    },
  });

  const deleteIdsMutation = useMutation({
    mutationFn: (idsTestId: number) => ifcValidationApi.deleteIdsTest(projectId, idsTestId),
    onSuccess: () => {
      setStatusMessage('IDS test deleted.');
      queryClient.invalidateQueries({ queryKey: ['ifc-ids-tests', projectId] });
    },
    onError: (error: any) => {
      setErrorMessage(error?.message || 'Failed to delete IDS test.');
    },
  });

  const failures = useMemo(() => {
    if (runResult?.specifications) {
      const rows: IfcValidationFailure[] = [];
      runResult.specifications.forEach((spec) => {
        spec.failed_entities?.forEach((failure, idx) => {
          rows.push({
            failure_id: idx,
            specification_name: spec.name,
            message: failure.message || null,
            ifc_class: failure.ifc_class || null,
            object_name: failure.object_name || null,
            created_at: null,
          });
        });
      });
      return rows;
    }
    return runDetail?.failures || [];
  }, [runResult, runDetail]);

  const runSummary = runResult?.summary || {
    total_specifications: runDetail?.run?.total_specifications || 0,
    passed_specifications: runDetail?.run?.passed_specifications || 0,
    failed_specifications: runDetail?.run?.failed_specifications || 0,
    total_entities_checked: null,
    total_failures: runDetail?.run?.total_failures || 0,
  };
  const runStatus = runResult
    ? runResult.success ? 'completed' : 'failed'
    : runDetail?.run?.status || 'idle';

  const handleReplaceClick = (test: IfcIdsTest) => {
    setReplaceTarget(test);
    replaceInputRef.current?.click();
  };

  const handleReplaceFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !replaceTarget) return;
    updateIdsMutation.mutate({ idsTestId: replaceTarget.ids_test_id, idsFile: file });
    event.target.value = '';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        IFC Health Check
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Validate IFC models against IDS requirements for {projectName || `Project #${projectId}`}.
      </Typography>

      <Tabs value={activeTab} onChange={(_, value) => setActiveTab(value)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Validation" />
        <Tab label="Run History" icon={<HistoryIcon fontSize="small" />} iconPosition="start" />
        <Tab label="IDS Tests" icon={<UploadFileIcon fontSize="small" />} iconPosition="start" />
      </Tabs>

      {statusMessage && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {statusMessage}
        </Alert>
      )}
      {errorMessage && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage}
        </Alert>
      )}

      <TabPanel value={activeTab} index={0}>
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Inputs
              </Typography>
              <Stack spacing={2}>
                <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
                  {ifcFile ? `IFC: ${ifcFile.name}` : 'Select IFC File'}
                  <input
                    type="file"
                    hidden
                    accept=".ifc"
                    onChange={(event) => setIfcFile(event.target.files?.[0] || null)}
                  />
                </Button>
                <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
                  {idsFile ? `IDS: ${idsFile.name}` : 'Select IDS File (optional if choosing saved test)'}
                  <input
                    type="file"
                    hidden
                    accept=".ids,.xml"
                    onChange={(event) => setIdsFile(event.target.files?.[0] || null)}
                  />
                </Button>
                <FormControl fullWidth size="small">
                  <InputLabel id="ids-test-select-label">Saved IDS Test</InputLabel>
                  <Select
                    labelId="ids-test-select-label"
                    value={idsTestId}
                    label="Saved IDS Test"
                    onChange={(event) => setIdsTestId(event.target.value as number | '')}
                  >
                    <MenuItem value="">None (use upload)</MenuItem>
                    {idsTests.map((test) => (
                      <MenuItem key={test.ids_test_id} value={test.ids_test_id}>
                        {test.ids_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth size="small">
                  <InputLabel id="expected-model-select-label">Link Quality Model</InputLabel>
                  <Select
                    labelId="expected-model-select-label"
                    value={expectedModelId}
                    label="Link Quality Model"
                    onChange={(event) => setExpectedModelId(event.target.value as number | '')}
                  >
                    <MenuItem value="">Auto-match</MenuItem>
                    {expectedModels.map((model) => (
                      <MenuItem key={model.expected_model_id} value={model.expected_model_id}>
                        {model.display_name || model.expected_model_key}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="Save IDS as (optional)"
                  size="small"
                  value={idsName}
                  onChange={(event) => setIdsName(event.target.value)}
                  helperText="Provide a name to save/upload this IDS into the library."
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={saveIdsTest}
                      onChange={(event) => setSaveIdsTest(event.target.checked)}
                    />
                  }
                  label="Save IDS test with this run"
                />
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="contained"
                    startIcon={<RunIcon />}
                    disabled={runMutation.isPending}
                    onClick={() => runMutation.mutate()}
                  >
                    {runMutation.isPending ? 'Running...' : 'Run Validation'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<SaveIcon />}
                    onClick={() => {
                      createIdsMutation.mutate();
                    }}
                    disabled={!idsFile || createIdsMutation.isPending}
                  >
                    Save IDS Test
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              {runStatus !== 'idle' && (
                <Alert severity={runStatus === 'completed' ? 'success' : runStatus === 'failed' ? 'error' : 'info'} sx={{ mb: 2 }}>
                  Status: {runStatus}
                </Alert>
              )}
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <Alert severity="info">
                  Total specs: {runSummary.total_specifications}
                </Alert>
                <Alert severity="success">
                  Passed: {runSummary.passed_specifications}
                </Alert>
                <Alert severity="error">
                  Failed: {runSummary.failed_specifications}
                </Alert>
                <Alert severity="warning">
                  Total failures: {runSummary.total_failures}
                </Alert>
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Failures</Typography>
                {runId && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => window.open(ifcValidationApi.getReportUrl(projectId, runId), '_blank')}
                  >
                    Download HTML Report
                  </Button>
                )}
              </Box>
              {failures.length === 0 ? (
                <Alert severity="success">No failures detected.</Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Specification</TableCell>
                        <TableCell>Message</TableCell>
                        <TableCell>IFC Class</TableCell>
                        <TableCell>Object Name</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {failures.map((failure) => (
                        <TableRow key={`${failure.failure_id}-${failure.specification_name}`}>
                          <TableCell>{failure.specification_name}</TableCell>
                          <TableCell>{failure.message || '-'}</TableCell>
                          <TableCell>{failure.ifc_class || '-'}</TableCell>
                          <TableCell>{failure.object_name || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Stack>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Run History
            </Typography>
            {runs.length === 0 ? (
              <Alert severity="info">No validation runs yet.</Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Status</TableCell>
                      <TableCell>IFC</TableCell>
                      <TableCell>IDS</TableCell>
                      <TableCell>Specs</TableCell>
                      <TableCell>Failures</TableCell>
                      <TableCell>Started</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {runs.map((run) => (
                      <TableRow
                        key={run.validation_run_id}
                        onClick={() => {
                          setRunId(run.validation_run_id);
                          setRunResult(null);
                        }}
                        hover
                      >
                        <TableCell>
                          <Stack direction="row" spacing={1} alignItems="center">
                            {run.status === 'completed' ? <SuccessIcon color="success" fontSize="small" /> : null}
                            {run.status === 'failed' ? <ErrorIcon color="error" fontSize="small" /> : null}
                            <Typography variant="body2">{run.status}</Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>{run.ifc_filename}</TableCell>
                        <TableCell>{run.ids_filename}</TableCell>
                        <TableCell>{run.total_specifications ?? '-'}</TableCell>
                        <TableCell>{run.total_failures ?? '-'}</TableCell>
                        <TableCell>{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              IDS Tests
            </Typography>
            <Stack spacing={2}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
                <TextField
                  label="IDS Name"
                  size="small"
                  value={idsName}
                  onChange={(event) => setIdsName(event.target.value)}
                  sx={{ flex: 1 }}
                />
                <Button component="label" variant="outlined">
                  {idsFile ? `Selected: ${idsFile.name}` : 'Select IDS File'}
                  <input
                    type="file"
                    hidden
                    accept=".ids,.xml"
                    onChange={(event) => setIdsFile(event.target.files?.[0] || null)}
                  />
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={() => createIdsMutation.mutate()}
                  disabled={!idsFile || createIdsMutation.isPending}
                >
                  Add IDS Test
                </Button>
              </Stack>
              <Divider />
              {idsTests.length === 0 ? (
                <Alert severity="info">No IDS tests saved yet.</Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Updated</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {idsTests.map((test) => (
                        <TableRow key={test.ids_test_id}>
                          <TableCell>{test.ids_name}</TableCell>
                          <TableCell>{test.updated_at ? new Date(test.updated_at).toLocaleString() : '-'}</TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1}>
                              <Button size="small" onClick={() => handleReplaceClick(test)}>
                                Replace
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                onClick={() => deleteIdsMutation.mutate(test.ids_test_id)}
                              >
                                Delete
                              </Button>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Stack>
          </CardContent>
        </Card>
      </TabPanel>

      <input ref={replaceInputRef} type="file" hidden accept=".ids,.xml" onChange={handleReplaceFile} />
    </Box>
  );
};
