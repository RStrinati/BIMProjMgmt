/**
 * Dynamo Batch Runner Component
 * Replicates Bird Tools Dynamo Multiplayer UI
 */

import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Stack,
  FormControl,
  Radio,
  RadioGroup,
  FormControlLabel,
  Checkbox,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Clear as ClearIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  FolderOpen as FolderIcon,
  HelpOutline as HelpIcon,
  Event as ScheduleIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
import { dynamoBatchApi, DynamoScript, JobConfiguration } from '@/api/dynamoBatch';
import { fileBrowserApi } from '@/api/fileBrowser';
import { formatDate } from '@/utils/dateUtils';

interface DynamoBatchRunnerProps {
  projectId: number;
  projectName?: string;
}

type RevitMode = 'synchronize' | 'readonly' | 'bruteforce';

export const DynamoBatchRunner: React.FC<DynamoBatchRunnerProps> = ({
  projectId,
  projectName,
}) => {
  // Revit Files Queue
  const [revitFiles, setRevitFiles] = useState<string[]>([]);
  const [selectedRevitFiles, setSelectedRevitFiles] = useState<Set<number>>(new Set());

  // Dynamo Scripts Queue
  const [dynamoScripts, setDynamoScripts] = useState<DynamoScript[]>([]);
  const [selectedDynamoScripts, setSelectedDynamoScripts] = useState<Set<number>>(new Set());
  const [availableScriptId, setAvailableScriptId] = useState<number | ''>('');

  // Mode Settings
  const [revitMode, setRevitMode] = useState<RevitMode>('readonly');
  const [transmitWorkshared, setTransmitWorkshared] = useState(false);
  const [compactOnSave, setCompactOnSave] = useState(true);
  const [auditOnOpen, setAuditOnOpen] = useState(false);
  const [closeProcessedFiles, setCloseProcessedFiles] = useState('Close All Processed Files');
  const [closeWorksets, setCloseWorksets] = useState('Close All Worksets');

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  // Query: Available scripts for browsing
  const {
    data: availableScripts = [],
    isLoading: scriptsLoading,
    refetch: refetchScripts,
  } = useQuery({
    queryKey: ['dynamoScripts'],
    queryFn: () => dynamoBatchApi.getScripts(),
  });

  // Query: Project Revit files
  const {
    data: projectRevitFiles = [],
    isLoading: revitFilesLoading,
    refetch: refetchRevitFiles,
  } = useQuery({
    queryKey: ['projectRevitFiles', projectId],
    queryFn: () => dynamoBatchApi.getProjectRevitFiles(projectId),
    enabled: Number.isFinite(projectId),
  });

  const mergeRevitFiles = (incoming: string[]) => {
    if (incoming.length === 0) return;
    setRevitFiles((prev) => {
      const seen = new Set(prev);
      const additions = incoming.filter((file) => !seen.has(file));
      if (additions.length === 0) {
        return prev;
      }
      return [...prev, ...additions];
    });
  };

  useEffect(() => {
    if (projectRevitFiles.length > 0) {
      mergeRevitFiles(projectRevitFiles.map((file) => file.file_path));
    }
  }, [projectRevitFiles]);

  const scriptOptions = useMemo(
    () => availableScripts.filter((script) => script.is_active),
    [availableScripts]
  );

  const clearAlerts = () => {
    setError(null);
    setSuccess(null);
  };

  const handleAddRevitFiles = async () => {
    clearAlerts();
    try {
      let addedAny = false;
      // Keep opening the dialog until the user cancels.
      while (true) {
        const result = await fileBrowserApi.selectFile({
          title: 'Select Revit File',
          file_types: [['Revit Files', '*.rvt']],
        });

        if (!result.success || !result.file_path) {
          if (!addedAny && result.message && result.message !== 'No file selected') {
            setError(result.message);
          }
          break;
        }

        addedAny = true;
        setRevitFiles((prev) => {
          if (prev.includes(result.file_path as string)) {
            return prev;
          }
          return [...prev, result.file_path as string];
        });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to select file.');
    }
  };

  const handleClearAllRevitFiles = () => {
    setRevitFiles([]);
    setSelectedRevitFiles(new Set());
  };

  const handleClearSelectedRevitFiles = () => {
    const newFiles = revitFiles.filter((_, idx) => !selectedRevitFiles.has(idx));
    setRevitFiles(newFiles);
    setSelectedRevitFiles(new Set());
  };

  const handleToggleRevitFile = (index: number) => {
    const newSelection = new Set(selectedRevitFiles);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedRevitFiles(newSelection);
  };

  const handleAddDynamoScript = async () => {
    clearAlerts();

    if (availableScriptId !== '') {
      const script = availableScripts.find((s) => s.script_id === availableScriptId);
      if (!script) {
        setError('Selected script not found.');
        return;
      }

      const alreadyQueued = dynamoScripts.some((s) => s.script_id === script.script_id);
      if (alreadyQueued) {
        setError('That script is already in the queue.');
        return;
      }

      setDynamoScripts((prev) => [...prev, script]);
      return;
    }

    try {
      const result = await fileBrowserApi.selectFile({
        title: 'Select Dynamo Script',
        file_types: [['Dynamo Script', '*.dyn']],
      });

      if (!result.success || !result.file_path) {
        if (result.message && result.message !== 'No file selected') {
          setError(result.message);
        }
        return;
      }

      const importResult = await dynamoBatchApi.importScriptsFromFiles({
        file_paths: [result.file_path],
      });

      if (!importResult.success) {
        setError(importResult.error || 'Failed to import Dynamo script.');
        return;
      }

      const imported = importResult.scripts ?? [];
      if (imported.length === 0) {
        setError('No Dynamo scripts were imported.');
        return;
      }

      const existing = new Set(dynamoScripts.map((script) => script.script_id));
      const additions = imported.filter((script) => !existing.has(script.script_id));

      setDynamoScripts((prev) => {
        if (additions.length === 0) {
          return prev;
        }
        const prevIds = new Set(prev.map((script) => script.script_id));
        const uniqueAdditions = additions.filter((script) => !prevIds.has(script.script_id));
        return uniqueAdditions.length > 0 ? [...prev, ...uniqueAdditions] : prev;
      });

      setSuccess(`Added ${additions.length} script(s).`);
      refetchScripts();
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? (err.response?.data as { error?: string } | undefined)?.error || err.message
        : err instanceof Error
          ? err.message
          : 'Failed to import Dynamo script.';
      setError(message);
    }
  };

  const handleAddScriptsFromFolder = async () => {
    clearAlerts();
    try {
      const result = await fileBrowserApi.selectFolder({
        title: 'Select Dynamo Scripts Folder',
      });

      if (!result.success || !result.folder_path) {
        if (result.message && result.message !== 'No folder selected') {
          setError(result.message);
        }
        return;
      }

      const importResult = await dynamoBatchApi.importScriptsFromFolder({
        folder_path: result.folder_path,
        recursive: true,
      });

      if (!importResult.success) {
        setError(importResult.error || 'Failed to import Dynamo scripts.');
        return;
      }

      const imported = importResult.scripts ?? [];
      if (imported.length === 0) {
        setError('No Dynamo scripts found in that folder.');
        return;
      }

      const existing = new Set(dynamoScripts.map((script) => script.script_id));
      const additions = imported.filter((script) => !existing.has(script.script_id));

      setDynamoScripts((prev) => {
        if (additions.length === 0) {
          return prev;
        }
        const prevIds = new Set(prev.map((script) => script.script_id));
        const uniqueAdditions = additions.filter((script) => !prevIds.has(script.script_id));
        return uniqueAdditions.length > 0 ? [...prev, ...uniqueAdditions] : prev;
      });

      setSuccess(`Added ${additions.length} script(s) from folder.`);
      refetchScripts();
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? (err.response?.data as { error?: string } | undefined)?.error || err.message
        : err instanceof Error
          ? err.message
          : 'Failed to import Dynamo scripts.';
      setError(message);
    }
  };

  const handleClearAllDynamoScripts = () => {
    setDynamoScripts([]);
    setSelectedDynamoScripts(new Set());
  };

  const handleClearSelectedDynamoScripts = () => {
    const newScripts = dynamoScripts.filter((_, idx) => !selectedDynamoScripts.has(idx));
    setDynamoScripts(newScripts);
    setSelectedDynamoScripts(new Set());
  };

  const handleToggleDynamoScript = (index: number) => {
    const newSelection = new Set(selectedDynamoScripts);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedDynamoScripts(newSelection);
  };

  const handleMoveScriptUp = (index: number) => {
    if (index === 0) return;
    const newScripts = [...dynamoScripts];
    [newScripts[index - 1], newScripts[index]] = [newScripts[index], newScripts[index - 1]];
    setDynamoScripts(newScripts);
  };

  const handleMoveScriptDown = (index: number) => {
    if (index === dynamoScripts.length - 1) return;
    const newScripts = [...dynamoScripts];
    [newScripts[index + 1], newScripts[index]] = [newScripts[index], newScripts[index + 1]];
    setDynamoScripts(newScripts);
  };

  const buildJobConfig = () => {
    const detachFromCentral = revitMode !== 'synchronize' && !transmitWorkshared;

    const config: JobConfiguration & {
      revit_mode?: RevitMode;
      transmit_workshared?: boolean;
      compact_on_save?: boolean;
      close_processed_files?: string;
    } = {
      detach_from_central: detachFromCentral,
      audit_on_opening: auditOnOpen,
      close_all_worksets: closeWorksets === 'Close All Worksets',
      discard_worksets: closeProcessedFiles !== 'Close All Processed Files',
      revit_mode: revitMode,
      transmit_workshared: transmitWorkshared,
      compact_on_save: compactOnSave,
      close_processed_files: closeProcessedFiles,
    };

    return config;
  };

  const runJobs = async (execute: boolean) => {
    clearAlerts();

    if (revitFiles.length === 0 || dynamoScripts.length === 0) {
      setError('Select at least one Revit file and one Dynamo script.');
      return;
    }

    try {
      setRunning(true);
      const config = buildJobConfig();
      const createdJobs: number[] = [];

      for (const script of dynamoScripts) {
        const jobId = await dynamoBatchApi.createJob({
          job_name: `${projectName ?? 'Project'} - ${script.script_name} - ${formatDate(new Date(), 'MMM d, HH:mm')}`,
          script_id: script.script_id,
          file_paths: revitFiles,
          project_id: projectId,
          configuration: config,
        });
        createdJobs.push(jobId);

        if (execute) {
          await dynamoBatchApi.executeJob(jobId);
        }
      }

      setSuccess(
        execute
          ? `Queued and started ${createdJobs.length} job(s).`
          : `Scheduled ${createdJobs.length} job(s) for execution.`
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create jobs.');
    } finally {
      setRunning(false);
    }
  };

  const handleCancel = () => {
    setRevitFiles([]);
    setDynamoScripts([]);
    setSelectedRevitFiles(new Set());
    setSelectedDynamoScripts(new Set());
    clearAlerts();
  };

  const handleHelp = () => {
    clearAlerts();
    setSuccess('See docs/DYNAMO_BATCH_SETUP_GUIDE.md for setup and usage details.');
  };

  const getFileName = (filePath: string) => {
    const normalized = filePath.replace(/\\/g, '/');
    const parts = normalized.split('/');
    return parts[parts.length - 1] || filePath;
  };

  return (
    <Box sx={{ p: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Revit Files Queue */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1">
            List of Revit files to be batch processed
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {revitFiles.length} Files
          </Typography>
        </Box>

        <Box
          sx={{
            minHeight: 150,
            maxHeight: 300,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'auto',
            bgcolor: 'background.default',
            mb: 2,
          }}
        >
          {revitFilesLoading ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <CircularProgress size={20} />
            </Box>
          ) : revitFiles.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              No files selected
            </Box>
          ) : (
            <List dense>
              {revitFiles.map((file, index) => (
                <ListItem
                  key={`${file}-${index}`}
                  button
                  selected={selectedRevitFiles.has(index)}
                  onClick={() => handleToggleRevitFile(index)}
                  sx={{ py: 0.5 }}
                >
                  <ListItemText
                    primary={getFileName(file)}
                    primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            size="small"
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={() => refetchRevitFiles()}
          >
            Add from Folder
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearAllRevitFiles}
          >
            Clear All
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<DeleteIcon />}
            onClick={handleClearSelectedRevitFiles}
            disabled={selectedRevitFiles.size === 0}
          >
            Clear Selected
          </Button>
          <Tooltip title="Import/Export settings are coming soon">
            <span>
              <Button size="small" variant="outlined" disabled>
                Import Settings
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="Import/Export settings are coming soon">
            <span>
              <Button size="small" variant="outlined" disabled>
                Export Settings
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="ACC/BIM 360 integration is coming soon">
            <span>
              <Button size="small" variant="outlined" disabled>
                ACC/BIM 360
              </Button>
            </span>
          </Tooltip>
          <Button size="small" variant="outlined" startIcon={<AddIcon />} onClick={handleAddRevitFiles}>
            Add
          </Button>
        </Stack>
      </Paper>

      {/* Dynamo Scripts Queue */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1">
            Dynamo Queue
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {dynamoScripts.length} Graphs
          </Typography>
        </Box>

        <Box
          sx={{
            minHeight: 150,
            maxHeight: 300,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'auto',
            bgcolor: 'background.default',
            mb: 2,
          }}
        >
          {scriptsLoading ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <CircularProgress size={20} />
            </Box>
          ) : dynamoScripts.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              No scripts selected
            </Box>
          ) : (
            <List dense>
              {dynamoScripts.map((script, index) => (
                <ListItem
                  key={script.script_id}
                  button
                  selected={selectedDynamoScripts.has(index)}
                  onClick={() => handleToggleDynamoScript(index)}
                  sx={{ py: 0.5 }}
                  secondaryAction={
                    <Box>
                      <IconButton
                        size="small"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleMoveScriptUp(index);
                        }}
                        disabled={index === 0}
                      >
                        <ArrowUpIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleMoveScriptDown(index);
                        }}
                        disabled={index === dynamoScripts.length - 1}
                      >
                        <ArrowDownIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText
                    primary={script.script_path}
                    secondary={script.script_name}
                    primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap alignItems="center">
          <FormControl size="small" sx={{ minWidth: 260 }}>
            <Select
              value={availableScriptId}
              onChange={(event) => setAvailableScriptId(Number(event.target.value))}
              displayEmpty
            >
              <MenuItem value="" disabled>
                Select a Dynamo script
              </MenuItem>
              {scriptOptions.map((script) => (
                <MenuItem key={script.script_id} value={script.script_id}>
                  {script.script_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button size="small" variant="outlined" onClick={() => refetchScripts()}>
            Refresh Library
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={handleAddScriptsFromFolder}
          >
            Add from Folder
          </Button>
          <Button size="small" variant="outlined" startIcon={<AddIcon />} onClick={handleAddDynamoScript}>
            Add
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearAllDynamoScripts}
          >
            Clear All
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<DeleteIcon />}
            onClick={handleClearSelectedDynamoScripts}
            disabled={selectedDynamoScripts.size === 0}
          >
            Clear Selected
          </Button>
        </Stack>
      </Paper>

      {/* Mode Settings */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Revit File Mode
        </Typography>

        <RadioGroup value={revitMode} onChange={(e) => setRevitMode(e.target.value as RevitMode)}>
          <FormControlLabel
            value="synchronize"
            control={<Radio />}
            label="Synchronize Mode: please mind my Central models."
          />
          <FormControlLabel
            value="readonly"
            control={<Radio />}
            label="Read-Only Mode: I just want to extract data or perform batch export operations."
          />
          <FormControlLabel
            value="bruteforce"
            control={<Radio />}
            label="Bruteforce Mode: overwrite everything, I know what I'm doing! (Use with caution)"
          />
        </RadioGroup>

        <Divider sx={{ my: 2 }} />

        <Stack spacing={1}>
          <FormControlLabel
            control={
              <Checkbox
                checked={transmitWorkshared}
                onChange={(e) => setTransmitWorkshared(e.target.checked)}
              />
            }
            label="Transmit Workshared Models"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={compactOnSave}
                onChange={(e) => setCompactOnSave(e.target.checked)}
              />
            }
            label="Compact On Save/Synchronize"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={auditOnOpen}
                onChange={(e) => setAuditOnOpen(e.target.checked)}
              />
            }
            label="Audit On Open"
          />
        </Stack>

        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <FormControl size="small" sx={{ minWidth: 250 }}>
            <Select
              value={closeProcessedFiles}
              onChange={(e) => setCloseProcessedFiles(e.target.value)}
            >
              <MenuItem value="Close All Processed Files">Close All Processed Files</MenuItem>
              <MenuItem value="Keep Files Open">Keep Files Open</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <Select value={closeWorksets} onChange={(e) => setCloseWorksets(e.target.value)}>
              <MenuItem value="Close All Worksets">Close All Worksets</MenuItem>
              <MenuItem value="Keep Worksets Open">Keep Worksets Open</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, flexWrap: 'wrap' }}>
        <Button variant="outlined" startIcon={<HelpIcon />} onClick={handleHelp}>
          Help
        </Button>
        <Button
          variant="outlined"
          startIcon={<ScheduleIcon />}
          onClick={() => runJobs(false)}
          disabled={running}
        >
          Schedule
        </Button>
        <Button
          variant="contained"
          startIcon={running ? <CircularProgress size={18} /> : <RunIcon />}
          onClick={() => runJobs(true)}
          disabled={running || revitFiles.length === 0 || dynamoScripts.length === 0}
        >
          Proceed
        </Button>
        <Button variant="outlined" onClick={handleCancel}>
          Cancel
        </Button>
      </Box>
    </Box>
  );
};
