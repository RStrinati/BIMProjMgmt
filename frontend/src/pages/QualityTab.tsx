import React, { useState } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { qualityApi, QualityPhase1DRegisterResponse } from '../api/quality';
import { QualityRegisterTable, EditableFields } from '../components/quality/QualityRegisterTable';
import { QualityModelSidePanel } from '../components/quality/QualityModelSidePanel';

interface QualityTabProps {
  projectId: number;
}

export const QualityTab: React.FC<QualityTabProps> = ({ projectId }) => {
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [draftById, setDraftById] = useState<Record<number, Partial<EditableFields>>>({});

  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<QualityPhase1DRegisterResponse>({
    queryKey: ['quality-register-phase1d', projectId],
    queryFn: async () => {
      const result = await qualityApi.getRegister(projectId, { mode: 'phase1d' });
      // Type guard to ensure we got Phase1D response
      if ('rows' in result) {
        return result as QualityPhase1DRegisterResponse;
      }
      throw new Error('Invalid response format');
    }
  });

  const createModelMutation = useMutation({
    mutationFn: () => qualityApi.createEmptyModel(projectId),
    onSuccess: (data) => {
      // Optimistically add the new row to the table
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: [
              ...old.rows,
              {
                expected_model_id: data.id,
                abv: null,
                modelName: null,
                company: null,
                discipline: null,
                description: null,
                bimContact: null,
                folderPath: null,
                accPresent: false,
                accDate: null,
                reviztoPresent: false,
                reviztoDate: null,
                notes: null,
                notesUpdatedAt: null,
                mappingStatus: 'UNMAPPED',
                matchedObservedFile: null,
                validationOverall: 'UNKNOWN',
                freshnessStatus: 'UNKNOWN'
              }
            ]
          };
        }
      );
      // Enter edit mode for the new row
      setEditingRowId(data.id);
      setDraftById((prev) => ({
        ...prev,
        [data.id]: {
          abv: '',
          registeredModelName: '',
          company: '',
          discipline: '',
          description: '',
          bimContact: '',
          notes: ''
        }
      }));
      // Invalidate in background
      queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
    }
  });

  const updateModelMutation = useMutation({
    mutationFn: ({ rowId, draft }: { rowId: number; draft: EditableFields }) =>
      qualityApi.updateExpectedModel(projectId, rowId, draft),
    onSuccess: (_, variables) => {
      // Exit edit mode
      setEditingRowId(null);
      setDraftById((prev) => {
        const { [variables.rowId]: _, ...rest } = prev;
        return rest;
      });
      // Update cache in-place for speed
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.map((row) =>
              row.expected_model_id === variables.rowId
                ? {
                    ...row,
                    abv: variables.draft.abv ?? row.abv,
                    modelName: variables.draft.registeredModelName ?? row.modelName,
                    company: variables.draft.company ?? row.company,
                    discipline: variables.draft.discipline ?? row.discipline,
                    description: variables.draft.description ?? row.description,
                    bimContact: variables.draft.bimContact ?? row.bimContact,
                    notes: variables.draft.notes ?? row.notes
                  }
                : row
            )
          };
        }
      );
      // Background invalidate
      queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
    }
  });

  const deleteModelMutation = useMutation({
    mutationFn: (rowId: number) =>
      qualityApi.deleteExpectedModel(projectId, rowId),
    onSuccess: (_, rowId) => {
      // Close side panel if deleted row was selected
      if (selectedModelId === rowId) {
        setSidePanelOpen(false);
        setSelectedModelId(null);
      }
      // Exit edit mode if deleted row was being edited
      if (editingRowId === rowId) {
        setEditingRowId(null);
        setDraftById((prev) => {
          const { [rowId]: _, ...rest } = prev;
          return rest;
        });
      }
      // Remove from cache
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.filter((row) => row.expected_model_id !== rowId)
          };
        }
      );
      // Background invalidate
      queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
    }
  });

  const handleRowClick = (row: any) => {
    // Don't open side panel if editing
    if (editingRowId === row.expected_model_id) {
      return;
    }
    // Prompt if switching rows while editing
    if (editingRowId !== null) {
      const shouldDiscard = window.confirm('Discard unsaved changes?');
      if (!shouldDiscard) {
        return;
      }
      // Discard draft
      setEditingRowId(null);
      setDraftById((prev) => {
        const { [editingRowId]: _, ...rest } = prev;
        return rest;
      });
    }
    setSelectedModelId(row.expected_model_id);
    setSidePanelOpen(true);
  };

  const handleEditRow = (rowId: number) => {
    // Initialize draft from current row data
    const row = data?.rows.find((r) => r.expected_model_id === rowId);
    if (!row) return;
    
    setEditingRowId(rowId);
    setDraftById((prev) => ({
      ...prev,
      [rowId]: {
        abv: row.abv || '',
        registeredModelName: row.modelName || '',
        company: row.company || '',
        discipline: row.discipline || '',
        description: row.description || '',
        bimContact: row.bimContact || '',
        notes: row.notes || ''
      }
    }));
  };

  const handleSaveRow = async (rowId: number, draft: EditableFields) => {
    // Trim whitespace
    const trimmedDraft: EditableFields = {};
    if (draft.abv !== undefined) trimmedDraft.abv = draft.abv.trim();
    if (draft.registeredModelName !== undefined) trimmedDraft.registeredModelName = draft.registeredModelName.trim();
    if (draft.company !== undefined) trimmedDraft.company = draft.company.trim();
    if (draft.discipline !== undefined) trimmedDraft.discipline = draft.discipline.trim();
    if (draft.description !== undefined) trimmedDraft.description = draft.description.trim();
    if (draft.bimContact !== undefined) trimmedDraft.bimContact = draft.bimContact.trim();
    if (draft.notes !== undefined) trimmedDraft.notes = draft.notes.trim();

    await updateModelMutation.mutateAsync({ rowId, draft: trimmedDraft });
  };

  const handleCancelEdit = (rowId: number) => {
    setEditingRowId(null);
    setDraftById((prev) => {
      const { [rowId]: _, ...rest } = prev;
      return rest;
    });
  };

  const handleAddRow = () => {
    createModelMutation.mutate();
  };

  const handleDraftChange = (rowId: number, field: keyof EditableFields, value: string) => {
    setDraftById((prev) => ({
      ...prev,
      [rowId]: {
        ...prev[rowId],
        [field]: value
      }
    }));
  };

  const handleDeleteRow = async (rowId: number) => {
    await deleteModelMutation.mutateAsync(rowId);
  };

  const handleCloseSidePanel = () => {
    setSidePanelOpen(false);
    setSelectedModelId(null);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Error loading quality register: {(error as Error).message}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Quality Register</Typography>
      </Box>

      <QualityRegisterTable
        rows={data?.rows || []}
        onRowClick={handleRowClick}
        selectedRowId={selectedModelId}
        editingRowId={editingRowId}
        onEditRow={handleEditRow}
        onSaveRow={handleSaveRow}
        onCancelEdit={handleCancelEdit}
        onDeleteRow={handleDeleteRow}
        onAddRow={handleAddRow}
        isAddingRow={createModelMutation.isPending}
        draftById={draftById}
        onDraftChange={handleDraftChange}
      />

      <QualityModelSidePanel
        projectId={projectId}
        expectedModelId={selectedModelId}
        open={sidePanelOpen}
        onClose={handleCloseSidePanel}
      />
    </Box>
  );
};
