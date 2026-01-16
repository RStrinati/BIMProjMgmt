import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  CircularProgress,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Drawer,
  Stack,
  Chip,
  Paper,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { qualityApi } from '@/api';
import type {
  QualityRegisterExpectedRow,
  QualityRegisterUnmatchedObservedRow,
  ExpectedModel,
} from '@/types/api';
import {
  LinearListContainer,
  LinearListHeaderRow,
  LinearListRow,
  LinearListCell,
} from '@/components/ui/LinearList';

interface ProjectQualityRegisterTabProps {
  projectId: number;
}

// Freshness status color mapping
const freshnessColors: Record<
  'MISSING' | 'CURRENT' | 'DUE_SOON' | 'OUT_OF_DATE' | 'UNKNOWN',
  'error' | 'warning' | 'success' | 'default'
> = {
  MISSING: 'error',
  'OUT_OF_DATE': 'error',
  'DUE_SOON': 'warning',
  CURRENT: 'success',
  UNKNOWN: 'default',
};

const freshnessLabels: Record<
  'MISSING' | 'CURRENT' | 'DUE_SOON' | 'OUT_OF_DATE' | 'UNKNOWN',
  string
> = {
  MISSING: 'Missing',
  'OUT_OF_DATE': 'Out of Date',
  'DUE_SOON': 'Due Soon',
  CURRENT: 'Current',
  UNKNOWN: 'Unknown',
};

// Validation status color mapping
const validationColors: Record<'FAIL' | 'WARN' | 'PASS' | 'UNKNOWN', 'error' | 'warning' | 'success' | 'default'> = {
  FAIL: 'error',
  WARN: 'warning',
  PASS: 'success',
  UNKNOWN: 'default',
};

const validationLabels: Record<'FAIL' | 'WARN' | 'PASS' | 'UNKNOWN', string> = {
  FAIL: 'Failed',
  WARN: 'Warning',
  PASS: 'Passed',
  UNKNOWN: 'Unknown',
};

const formatDate = (dateStr?: string | null) => {
  if (!dateStr) return '--';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-AU', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return '--';
  }
};

// Add Expected Model Modal
function AddExpectedModelModal({
  open,
  onClose,
  onSubmit,
  isLoading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    expected_model_key: string;
    display_name?: string;
    discipline?: string;
    is_required: boolean;
  }) => Promise<void>;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState({
    expected_model_key: '',
    display_name: '',
    discipline: '',
    is_required: true,
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!formData.expected_model_key.trim()) {
      setError('Expected model key is required');
      return;
    }
    try {
      await onSubmit(formData);
      setFormData({ expected_model_key: '', display_name: '', discipline: '', is_required: true });
      setError(null);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create expected model');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Expected Model</DialogTitle>
      <DialogContent sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}
        <TextField
          label="Expected Model Key"
          required
          value={formData.expected_model_key}
          onChange={(e) => setFormData({ ...formData, expected_model_key: e.target.value })}
          placeholder="e.g., STR_M.rvt"
          fullWidth
          disabled={isLoading}
        />
        <TextField
          label="Display Name"
          value={formData.display_name}
          onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
          placeholder="e.g., Structural Model"
          fullWidth
          disabled={isLoading}
        />
        <TextField
          label="Discipline"
          value={formData.discipline}
          onChange={(e) => setFormData({ ...formData, discipline: e.target.value })}
          placeholder="e.g., Structural"
          fullWidth
          disabled={isLoading}
        />
        <FormControlLabel
          control={
            <Switch
              checked={formData.is_required}
              onChange={(e) => setFormData({ ...formData, is_required: e.target.checked })}
              disabled={isLoading}
            />
          }
          label="Required"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Map Observed File Modal
function MapObservedFileModal({
  open,
  onClose,
  observedFileName,
  expectedModels,
  onSubmit,
  isLoading,
}: {
  open: boolean;
  onClose: () => void;
  observedFileName: string;
  expectedModels: ExpectedModel[];
  onSubmit: (data: {
    expected_model_id: number;
    alias_pattern: string;
    match_type: 'exact' | 'contains' | 'regex';
    target_field: 'filename' | 'rvt_model_key';
    is_active: boolean;
  }) => Promise<void>;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState({
    expected_model_id: expectedModels[0]?.expected_model_id || 0,
    alias_pattern: observedFileName,
    match_type: 'exact' as const,
    target_field: 'filename' as const,
    is_active: true,
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!formData.expected_model_id) {
      setError('Please select an expected model');
      return;
    }
    if (!formData.alias_pattern.trim()) {
      setError('Pattern is required');
      return;
    }
    try {
      await onSubmit(formData);
      setError(null);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create mapping');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Map Observed File to Expected Model</DialogTitle>
      <DialogContent sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            Observed File
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
            {observedFileName}
          </Typography>
        </Box>
        <FormControl fullWidth disabled={isLoading}>
          <InputLabel>Expected Model</InputLabel>
          <Select
            value={formData.expected_model_id}
            onChange={(e) => setFormData({ ...formData, expected_model_id: e.target.value as number })}
            label="Expected Model"
          >
            {expectedModels.map((model) => (
              <MenuItem key={model.expected_model_id} value={model.expected_model_id}>
                {model.display_name || model.expected_model_key}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl fullWidth disabled={isLoading}>
          <InputLabel>Match Type</InputLabel>
          <Select
            value={formData.match_type}
            onChange={(e) => setFormData({ ...formData, match_type: e.target.value as any })}
            label="Match Type"
          >
            <MenuItem value="exact">Exact</MenuItem>
            <MenuItem value="contains">Contains</MenuItem>
            <MenuItem value="regex">Regex</MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth disabled={isLoading}>
          <InputLabel>Target Field</InputLabel>
          <Select
            value={formData.target_field}
            onChange={(e) => setFormData({ ...formData, target_field: e.target.value as any })}
            label="Target Field"
          >
            <MenuItem value="filename">Filename</MenuItem>
            <MenuItem value="rvt_model_key">RVT Model Key</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Pattern"
          multiline
          rows={2}
          value={formData.alias_pattern}
          onChange={(e) => setFormData({ ...formData, alias_pattern: e.target.value })}
          fullWidth
          disabled={isLoading}
          placeholder="e.g., STR_.*\.rvt for regex"
        />
        <FormControlLabel
          control={
            <Switch
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              disabled={isLoading}
            />
          }
          label="Active"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={isLoading}>
          {isLoading ? 'Mapping...' : 'Map'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function ProjectQualityRegisterTab({ projectId }: ProjectQualityRegisterTabProps) {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<'register' | 'unmatched'>('register');
  const [selectedRow, setSelectedRow] = useState<QualityRegisterExpectedRow | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [addModelModalOpen, setAddModelModalOpen] = useState(false);
  const [mapModalOpen, setMapModalOpen] = useState(false);
  const [selectedUnmatchedFile, setSelectedUnmatchedFile] = useState<QualityRegisterUnmatchedObservedRow | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch expected register data
  const { data: registerData, isLoading: isLoadingRegister, error: registerError } = useQuery({
    queryKey: ['qualityRegisterExpected', projectId],
    queryFn: () => qualityApi.getExpectedRegister(projectId),
    enabled: Number.isFinite(projectId),
  });

  // Fetch expected models for dropdowns
  const { data: expectedModels = [] } = useQuery({
    queryKey: ['expectedModels', projectId],
    queryFn: () => qualityApi.listExpectedModels(projectId),
    enabled: Number.isFinite(projectId),
  });

  // Handle create expected model
  const handleCreateExpectedModel = async (data: {
    expected_model_key: string;
    display_name?: string;
    discipline?: string;
    is_required: boolean;
  }) => {
    setIsSubmitting(true);
    try {
      await qualityApi.createExpectedModel(projectId, data);
      // Invalidate queries
      await queryClient.invalidateQueries({ queryKey: ['qualityRegisterExpected', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['expectedModels', projectId] });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle create alias
  const handleCreateAlias = async (data: {
    expected_model_id: number;
    alias_pattern: string;
    match_type: 'exact' | 'contains' | 'regex';
    target_field: 'filename' | 'rvt_model_key';
    is_active: boolean;
  }) => {
    setIsSubmitting(true);
    try {
      await qualityApi.createExpectedModelAlias(projectId, data);
      // Invalidate queries
      await queryClient.invalidateQueries({ queryKey: ['qualityRegisterExpected', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['expectedModels', projectId] });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Compute display counts
  const registerCounts = {
    expected_total: registerData?.counts.expected_total ?? 0,
    expected_missing: registerData?.counts.expected_missing ?? 0,
    unmatched_total: registerData?.counts.unmatched_total ?? 0,
    attention_count: registerData?.counts.attention_count ?? 0,
  };

  if (registerError) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load quality register. Please try again.
      </Alert>
    );
  }

  if (isLoadingRegister) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!registerData) {
    return <Typography color="text.secondary">No data available.</Typography>;
  }

  const registerRows = registerData.expected_rows || [];
  const unmatchedRows = registerData.unmatched_observed || [];

  return (
    <Box data-testid="project-quality-register-tab" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header with view mode toggle */}
      <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between" flexWrap="wrap">
        <ToggleButtonGroup
          exclusive
          value={viewMode}
          onChange={(_event, newMode) => {
            if (newMode) setViewMode(newMode);
          }}
          size="small"
          data-testid="quality-register-view-mode"
        >
          <ToggleButton value="register" aria-label="register-view">
            Register {registerCounts.expected_total > 0 && `(${registerCounts.expected_total})`}
          </ToggleButton>
          <ToggleButton value="unmatched" aria-label="unmatched-view">
            Unmatched {registerCounts.unmatched_total > 0 && `(${registerCounts.unmatched_total})`}
          </ToggleButton>
        </ToggleButtonGroup>

        {viewMode === 'register' && (
          <Button variant="contained" size="small" onClick={() => setAddModelModalOpen(true)}>
            Add Expected Model
          </Button>
        )}

        <Typography variant="body2" color="text.secondary">
          Attention: {registerCounts.attention_count}
        </Typography>
      </Stack>

      {/* Register View */}
      {viewMode === 'register' && (
        <>
          {registerRows.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No expected models yet. Add one to start the register.
              </Typography>
            </Paper>
          ) : (
            <LinearListContainer data-testid="quality-register-expected-table">
              <LinearListHeaderRow
                columns={[
                  'Status',
                  'Expected Model',
                  'Discipline',
                  'Observed File',
                  'Last Version',
                  'Validation',
                  'Control',
                  'Mapping',
                ]}
              />

              {registerRows.map((row) => (
                <LinearListRow
                  key={row.expected_model_id}
                  onClick={() => {
                    setSelectedRow(row);
                    setIsDrawerOpen(true);
                  }}
                  sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                  data-testid={`quality-expected-row-${row.expected_model_id}`}
                >
                  {/* Freshness status */}
                  <LinearListCell sx={{ flex: '0 0 80px' }}>
                    <Chip
                      label={freshnessLabels[row.freshnessStatus]}
                      size="small"
                      color={freshnessColors[row.freshnessStatus]}
                      variant="outlined"
                    />
                  </LinearListCell>

                  {/* Expected model */}
                  <LinearListCell sx={{ flex: '1 1 150px', fontWeight: 500 }}>
                    {row.display_name || row.expected_model_key}
                  </LinearListCell>

                  {/* Discipline */}
                  <LinearListCell sx={{ flex: '0 0 120px' }}>
                    {row.discipline || '--'}
                  </LinearListCell>

                  {/* Observed file */}
                  <LinearListCell sx={{ flex: '1 1 150px', color: 'text.secondary', fontSize: '0.875rem' }}>
                    {row.observed_file_name || '--'}
                  </LinearListCell>

                  {/* Last version date */}
                  <LinearListCell sx={{ flex: '0 0 110px' }}>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(row.lastVersionDateISO)}
                    </Typography>
                  </LinearListCell>

                  {/* Validation status */}
                  <LinearListCell sx={{ flex: '0 0 100px' }}>
                    <Chip
                      label={validationLabels[row.validationOverall]}
                      size="small"
                      color={validationColors[row.validationOverall]}
                      variant="outlined"
                    />
                  </LinearListCell>

                  {/* Control indicator */}
                  <LinearListCell sx={{ flex: '0 0 80px' }}>
                    {row.isControlModel ? (
                      <Chip label="Control" size="small" color="primary" variant="filled" />
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        --
                      </Typography>
                    )}
                  </LinearListCell>

                  {/* Mapping status */}
                  <LinearListCell sx={{ flex: '0 0 100px' }}>
                    <Chip
                      label={row.mappingStatus}
                      size="small"
                      variant={row.mappingStatus === 'MAPPED' ? 'filled' : 'outlined'}
                      color={row.mappingStatus === 'MAPPED' ? 'success' : 'default'}
                    />
                  </LinearListCell>
                </LinearListRow>
              ))}
            </LinearListContainer>
          )}
        </>
      )}

      {/* Unmatched View */}
      {viewMode === 'unmatched' && (
        <>
          {unmatchedRows.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">No unmatched observed files.</Typography>
            </Paper>
          ) : (
            <LinearListContainer data-testid="quality-unmatched-table">
              <LinearListHeaderRow
                columns={['Observed Filename', 'Discipline', 'Last Version', 'Validation', 'Naming', 'Action']}
              />

              {unmatchedRows.map((row, idx) => (
                <LinearListRow
                  key={`${row.observed_file_name}-${idx}`}
                  data-testid={`quality-unmatched-row-${idx}`}
                >
                  {/* Observed filename */}
                  <LinearListCell sx={{ flex: '1 1 200px', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {row.observed_file_name}
                  </LinearListCell>

                  {/* Discipline */}
                  <LinearListCell sx={{ flex: '0 0 120px' }}>
                    {row.discipline || '--'}
                  </LinearListCell>

                  {/* Last version date */}
                  <LinearListCell sx={{ flex: '0 0 110px' }}>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(row.lastVersionDateISO)}
                    </Typography>
                  </LinearListCell>

                  {/* Validation status */}
                  <LinearListCell sx={{ flex: '0 0 100px' }}>
                    <Chip
                      label={validationLabels[row.validationOverall]}
                      size="small"
                      color={validationColors[row.validationOverall]}
                      variant="outlined"
                    />
                  </LinearListCell>

                  {/* Naming status */}
                  <LinearListCell sx={{ flex: '0 0 100px' }}>
                    <Chip
                      label={row.namingStatus || 'UNKNOWN'}
                      size="small"
                      color={
                        row.namingStatus === 'CORRECT'
                          ? 'success'
                          : row.namingStatus === 'MISNAMED'
                            ? 'warning'
                            : 'default'
                      }
                      variant={row.namingStatus === 'CORRECT' ? 'outlined' : 'filled'}
                    />
                  </LinearListCell>

                  {/* Action button */}
                  <LinearListCell sx={{ flex: '0 0 100px' }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedUnmatchedFile(row);
                        setMapModalOpen(true);
                      }}
                    >
                      Map
                    </Button>
                  </LinearListCell>
                </LinearListRow>
              ))}
            </LinearListContainer>
          )}
        </>
      )}

      {/* Detail drawer for expected models */}
      <Drawer
        anchor="right"
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        data-testid="quality-register-detail-drawer"
        PaperProps={{
          sx: { width: 400 },
        }}
      >
        {selectedRow && (
          <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Model Details
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Stack spacing={2} sx={{ flex: 1, overflowY: 'auto' }}>
              {/* Expected model key */}
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  EXPECTED MODEL KEY
                </Typography>
                <Typography variant="body2">{selectedRow.expected_model_key}</Typography>
              </Box>

              {/* Display name */}
              {selectedRow.display_name && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    DISPLAY NAME
                  </Typography>
                  <Typography variant="body2">{selectedRow.display_name}</Typography>
                </Box>
              )}

              {/* Discipline */}
              {selectedRow.discipline && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    DISCIPLINE
                  </Typography>
                  <Typography variant="body2">{selectedRow.discipline}</Typography>
                </Box>
              )}

              {/* Company */}
              {selectedRow.company && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    COMPANY
                  </Typography>
                  <Typography variant="body2">{selectedRow.company}</Typography>
                </Box>
              )}

              {/* Observed file */}
              {selectedRow.observed_file_name && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    OBSERVED FILE
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {selectedRow.observed_file_name}
                  </Typography>
                </Box>
              )}

              {/* Last version date */}
              {selectedRow.lastVersionDateISO && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    LAST VERSION DATE
                  </Typography>
                  <Typography variant="body2">{formatDate(selectedRow.lastVersionDateISO)}</Typography>
                </Box>
              )}

              <Divider />

              {/* Freshness status */}
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  FRESHNESS STATUS
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={freshnessLabels[selectedRow.freshnessStatus]}
                    color={freshnessColors[selectedRow.freshnessStatus]}
                  />
                </Box>
              </Box>

              {/* Validation status */}
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  VALIDATION STATUS
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={validationLabels[selectedRow.validationOverall]}
                    color={validationColors[selectedRow.validationOverall]}
                  />
                </Box>
              </Box>

              {/* Naming status */}
              {selectedRow.namingStatus && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    NAMING STATUS
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={selectedRow.namingStatus}
                      color={
                        selectedRow.namingStatus === 'CORRECT'
                          ? 'success'
                          : selectedRow.namingStatus === 'MISNAMED'
                            ? 'warning'
                            : 'default'
                      }
                      variant={selectedRow.namingStatus === 'CORRECT' ? 'outlined' : 'filled'}
                    />
                  </Box>
                </Box>
              )}

              {/* Control status */}
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  CONTROL MODEL
                </Typography>
                <Typography variant="body2">{selectedRow.isControlModel ? 'Yes' : 'No'}</Typography>
              </Box>

              {/* Mapping status */}
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  MAPPING STATUS
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={selectedRow.mappingStatus}
                    variant={selectedRow.mappingStatus === 'MAPPED' ? 'filled' : 'outlined'}
                    color={selectedRow.mappingStatus === 'MAPPED' ? 'success' : 'default'}
                  />
                </Box>
              </Box>
            </Stack>
          </Box>
        )}
      </Drawer>

      {/* Add Expected Model Modal */}
      <AddExpectedModelModal
        open={addModelModalOpen}
        onClose={() => setAddModelModalOpen(false)}
        onSubmit={handleCreateExpectedModel}
        isLoading={isSubmitting}
      />

      {/* Map Observed File Modal */}
      {selectedUnmatchedFile && (
        <MapObservedFileModal
          open={mapModalOpen}
          onClose={() => {
            setMapModalOpen(false);
            setSelectedUnmatchedFile(null);
          }}
          observedFileName={selectedUnmatchedFile.observed_file_name}
          expectedModels={expectedModels}
          onSubmit={handleCreateAlias}
          isLoading={isSubmitting}
        />
      )}
    </Box>
  );
}
