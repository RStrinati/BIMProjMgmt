import React, { useState } from 'react';
import {
  Drawer,
  Box,
  Typography,
  TextField,
  Button,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Alert
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { qualityApi } from '../../api/quality';

interface QualityModelSidePanelProps {
  projectId: number;
  expectedModelId: number | null;
  open: boolean;
  onClose: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ padding: '16px 0' }}>
    {value === index && children}
  </div>
);

export const QualityModelSidePanel: React.FC<QualityModelSidePanelProps> = ({
  projectId,
  expectedModelId,
  open,
  onClose
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [aliasDialogOpen, setAliasDialogOpen] = useState(false);
  const [newAlias, setNewAlias] = useState<{ match_type: 'exact' | 'contains' | 'regex'; alias_pattern: string }>({ 
    match_type: 'exact', 
    alias_pattern: '' 
  });

  const queryClient = useQueryClient();

  const { data: modelDetail, isLoading } = useQuery({
    queryKey: ['qualityModelDetail', projectId, expectedModelId],
    queryFn: () => qualityApi.getModelDetail(projectId, expectedModelId!),
    enabled: !!expectedModelId
  });

  const { data: historyData } = useQuery({
    queryKey: ['qualityModelHistory', projectId, expectedModelId],
    queryFn: () => qualityApi.getModelHistory(projectId, expectedModelId!),
    enabled: !!expectedModelId
  });

  const aliasMutation = useMutation({
    mutationFn: (alias: { expected_model_id: number; match_type: 'exact' | 'contains' | 'regex'; alias_pattern: string }) =>
      qualityApi.createExpectedModelAlias(projectId, alias),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qualityModelDetail', projectId, expectedModelId] });
      queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
      setAliasDialogOpen(false);
      setNewAlias({ match_type: 'exact', alias_pattern: '' });
    }
  });

  const handleAddAlias = () => {
    if (expectedModelId && newAlias.alias_pattern) {
      aliasMutation.mutate({
        expected_model_id: expectedModelId,
        ...newAlias
      });
    }
  };

  if (!expectedModelId || !open) return null;

  return (
    <>
      <Drawer
        anchor="right"
        open={open}
        onClose={onClose}
        sx={{
          '& .MuiDrawer-paper': {
            width: 500,
            p: 3
          }
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Model Details</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>

        {isLoading ? (
          <Typography>Loading...</Typography>
        ) : (
          <>
            {/* Read-only register info summary */}
            <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Register Information</Typography>
              <Typography variant="body2"><strong>ABV:</strong> {modelDetail?.abv || '—'}</Typography>
              <Typography variant="body2"><strong>Model Name:</strong> {modelDetail?.registeredModelName || '—'}</Typography>
              <Typography variant="body2"><strong>Company:</strong> {modelDetail?.company || '—'}</Typography>
              <Typography variant="body2"><strong>Discipline:</strong> {modelDetail?.discipline || '—'}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                Edit these fields inline in the table
              </Typography>
            </Box>

            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
              <Tab label="Mapping" />
              <Tab label="Health" />
              <Tab label="Activity" />
            </Tabs>
            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
              <Tab label="Mapping" />
              <Tab label="Health" />
              <Tab label="Activity" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="subtitle2">Registered Model Name</Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {modelDetail?.registeredModelName || '—'}
                </Typography>

                <Divider />

                <Typography variant="subtitle2">Current Observed Match</Typography>
                {modelDetail?.observedMatch ? (
                  <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
                    <Typography variant="body2"><strong>File:</strong> {modelDetail.observedMatch.fileName}</Typography>
                    <Typography variant="body2"><strong>Path:</strong> {modelDetail.observedMatch.folderPath}</Typography>
                    <Typography variant="body2">
                      <strong>Last Modified:</strong>{' '}
                      {modelDetail.observedMatch.lastModified
                        ? new Date(modelDetail.observedMatch.lastModified).toLocaleString()
                        : '—'}
                    </Typography>
                  </Box>
                ) : (
                  <Alert severity="info">No observed file matched yet</Alert>
                )}

                <Divider />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">Aliases ({modelDetail?.aliases.length || 0})</Typography>
                  <Button
                    startIcon={<AddIcon />}
                    size="small"
                    onClick={() => setAliasDialogOpen(true)}
                  >
                    Add Alias
                  </Button>
                </Box>

                {modelDetail?.aliases.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No aliases defined</Typography>
                ) : (
                  <List dense>
                    {modelDetail?.aliases.map((alias: any) => (
                      <ListItem key={alias.id}>
                        <ListItemText
                          primary={alias.pattern}
                          secondary={`Type: ${alias.matchType}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2">Validation Status</Typography>
                  <Chip
                    label={modelDetail?.health.validationStatus || 'UNKNOWN'}
                    color={modelDetail?.health.validationStatus === 'PASS' ? 'success' : 'default'}
                    sx={{ mt: 1 }}
                  />
                </Box>

                <Divider />

                <Box>
                  <Typography variant="subtitle2">Freshness Status</Typography>
                  <Chip
                    label={modelDetail?.health.freshnessStatus || 'UNKNOWN'}
                    sx={{ mt: 1 }}
                  />
                </Box>

                <Divider />

                <Typography variant="body2" color="text.secondary">
                  Health metrics will be populated from RevitHealthCheckDB when available
                </Typography>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="subtitle2">Change History</Typography>
                {historyData?.history && historyData.history.length > 0 ? (
                  <List dense>
                    {historyData.history.map((entry: any) => (
                      <ListItem key={entry.historyId} sx={{ flexDirection: 'column', alignItems: 'flex-start', borderBottom: '1px solid #eee' }}>
                        <Box sx={{ width: '100%' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {entry.changeType} - {new Date(entry.changedAt).toLocaleString()}
                          </Typography>
                          {entry.changedBy && (
                            <Typography variant="caption" color="text.secondary">
                              by {entry.changedBy}
                            </Typography>
                          )}
                          {entry.changedFields && entry.changedFields !== '[]' && (
                            <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                              Changed: {entry.changedFields}
                            </Typography>
                          )}
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No change history yet
                  </Typography>
                )}
              </Box>
            </TabPanel>
          </>
        )}
      </Drawer>

      <Dialog open={aliasDialogOpen} onClose={() => setAliasDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Alias</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Match Type</InputLabel>
              <Select
                value={newAlias.match_type}
                onChange={(e) => setNewAlias({ ...newAlias, match_type: e.target.value as 'exact' | 'contains' | 'regex' })}
                label="Match Type"
              >
                <MenuItem value="exact">Exact</MenuItem>
                <MenuItem value="contains">Contains</MenuItem>
                <MenuItem value="regex">Regex</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Pattern"
              size="small"
              fullWidth
              value={newAlias.alias_pattern}
              onChange={(e) => setNewAlias({ ...newAlias, alias_pattern: e.target.value })}
              placeholder="e.g., MEL071-AR-*"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAliasDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddAlias}
            variant="contained"
            disabled={!newAlias.alias_pattern || aliasMutation.isPending}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
