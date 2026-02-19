import { Alert, Box, Chip, Divider, Paper, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { qualityApi } from '@/api/quality';
import { useWorkspaceSelection } from '@/hooks/useWorkspaceSelection';

type QualityModelDetailPanelProps = {
  projectId: number;
  expectedModelId: number;
};

const formatDateTime = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
};

const statusColor = (
  status: string | null | undefined,
  type: 'validation' | 'freshness',
): 'success' | 'warning' | 'error' | 'default' => {
  if (!status) return 'default';
  if (type === 'validation') {
    if (status === 'PASS') return 'success';
    if (status === 'FAIL') return 'error';
    if (status === 'WARN') return 'warning';
    return 'default';
  }
  if (status === 'CURRENT') return 'success';
  if (status === 'DUE_SOON') return 'warning';
  if (status === 'OUT_OF_DATE' || status === 'MISSING') return 'error';
  return 'default';
};

export function QualityModelDetailPanel({ projectId, expectedModelId }: QualityModelDetailPanelProps) {
  const { setSelection } = useWorkspaceSelection();
  const {
    data: modelDetail,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['qualityModelDetail', projectId, expectedModelId],
    queryFn: () => qualityApi.getModelDetail(projectId, expectedModelId),
    enabled: Number.isFinite(projectId) && Number.isFinite(expectedModelId),
    retry: false,
  });

  const { data: historyData } = useQuery({
    queryKey: ['qualityModelHistory', projectId, expectedModelId],
    queryFn: () => qualityApi.getModelHistory(projectId, expectedModelId),
    enabled: Number.isFinite(projectId) && Number.isFinite(expectedModelId),
  });

  useEffect(() => {
    const status = (error as any)?.response?.status;
    if (status === 404) {
      setSelection(null);
    }
  }, [error, setSelection]);

  const notesHistory = useMemo(() => {
    const items = historyData?.history ?? [];
    return items.filter((entry) => {
      if (entry.changedFields?.toLowerCase().includes('notes')) return true;
      return entry.snapshot?.notes != null;
    });
  }, [historyData]);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Quality Model
      </Typography>

      {isLoading && <Typography color="text.secondary">Loading model details...</Typography>}
      {error && !isLoading && (
        <Alert severity="error">Failed to load model details.</Alert>
      )}

      {!isLoading && !error && modelDetail && (
        <Stack spacing={2}>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {modelDetail.registeredModelName || modelDetail.abv || '--'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Last updated {formatDateTime(modelDetail.updatedAt)}
            </Typography>
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Register Info
            </Typography>
            <Stack spacing={0.5} sx={{ mt: 1 }}>
              <Typography variant="body2">ABV: {modelDetail.abv || '--'}</Typography>
              <Typography variant="body2">Company: {modelDetail.company || '--'}</Typography>
              <Typography variant="body2">Discipline: {modelDetail.discipline || '--'}</Typography>
              <Typography variant="body2">BIM Contact: {modelDetail.bimContact || '--'}</Typography>
            </Stack>
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Observed Match
            </Typography>
            {modelDetail.observedMatch ? (
              <Stack spacing={0.5} sx={{ mt: 1 }}>
                <Typography variant="body2">File: {modelDetail.observedMatch.fileName || '--'}</Typography>
                <Typography variant="body2">Path: {modelDetail.observedMatch.folderPath || '--'}</Typography>
                <Typography variant="body2">
                  Last Modified: {formatDateTime(modelDetail.observedMatch.lastModified)}
                </Typography>
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                No observed file matched yet.
              </Typography>
            )}
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Health
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`Validation: ${modelDetail.health?.validationStatus || 'UNKNOWN'}`}
                color={statusColor(modelDetail.health?.validationStatus, 'validation')}
                size="small"
              />
              <Chip
                label={`Freshness: ${modelDetail.health?.freshnessStatus || 'UNKNOWN'}`}
                color={statusColor(modelDetail.health?.freshnessStatus, 'freshness')}
                size="small"
              />
            </Stack>
            {modelDetail.healthSummary && (
              <Stack spacing={0.5} sx={{ mt: 1 }}>
                <Typography variant="body2">Levels: {modelDetail.healthSummary.levels ?? '--'}</Typography>
                <Typography variant="body2">Grids: {modelDetail.healthSummary.grids ?? '--'}</Typography>
                <Typography variant="body2">Worksets: {modelDetail.healthSummary.worksets ?? '--'}</Typography>
                <Typography variant="body2">Warnings: {modelDetail.healthSummary.warnings ?? '--'}</Typography>
                <Typography variant="body2">File size (MB): {modelDetail.healthSummary.fileSizeMb ?? '--'}</Typography>
                <Typography variant="body2">Total elements: {modelDetail.healthSummary.totalElements ?? '--'}</Typography>
                <Typography variant="body2">Families: {modelDetail.healthSummary.familyCount ?? '--'}</Typography>
                <Typography variant="body2">Groups: {modelDetail.healthSummary.groupCount ?? '--'}</Typography>
                <Typography variant="body2">In-place families: {modelDetail.healthSummary.inplaceFamilies ?? '--'}</Typography>
                <Typography variant="body2">SketchUp imports: {modelDetail.healthSummary.sketchupImports ?? '--'}</Typography>
                <Typography variant="body2">Revit links: {modelDetail.healthSummary.revitLinks ?? '--'}</Typography>
                <Typography variant="body2">DWG links: {modelDetail.healthSummary.dwgLinks ?? '--'}</Typography>
                <Typography variant="body2">DWG imports: {modelDetail.healthSummary.dwgImports ?? '--'}</Typography>
                <Typography variant="body2">Sheets: {modelDetail.healthSummary.sheetCount ?? '--'}</Typography>
                <Typography variant="body2">Design option sets: {modelDetail.healthSummary.designOptionSets ?? '--'}</Typography>
                <Typography variant="body2">Design options: {modelDetail.healthSummary.designOptions ?? '--'}</Typography>
                <Typography variant="body2">Total views: {modelDetail.healthSummary.totalViews ?? '--'}</Typography>
                <Typography variant="body2">Copied views: {modelDetail.healthSummary.copiedViews ?? '--'}</Typography>
                <Typography variant="body2">Dependent views: {modelDetail.healthSummary.dependentViews ?? '--'}</Typography>
                <Typography variant="body2">Views not on sheets: {modelDetail.healthSummary.viewsNotOnSheets ?? '--'}</Typography>
              </Stack>
            )}
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Aliases
            </Typography>
            {modelDetail.aliases?.length ? (
              <Stack spacing={0.5} sx={{ mt: 1 }}>
                {modelDetail.aliases.map((alias) => (
                  <Typography key={alias.id} variant="body2">
                    {alias.pattern} ({alias.matchType})
                  </Typography>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                No aliases defined.
              </Typography>
            )}
          </Box>

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Notes Activity
            </Typography>
            {notesHistory.length ? (
              <Stack spacing={1} sx={{ mt: 1 }}>
                {notesHistory.slice(0, 5).map((entry) => (
                  <Box key={entry.historyId}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {entry.changeType} - {formatDateTime(entry.changedAt)}
                    </Typography>
                    {entry.changedBy && (
                      <Typography variant="caption" color="text.secondary">
                        by {entry.changedBy}
                      </Typography>
                    )}
                    {entry.snapshot?.notes && (
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        {entry.snapshot.notes}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                No notes activity yet.
              </Typography>
            )}
          </Box>
        </Stack>
      )}
    </Paper>
  );
}
