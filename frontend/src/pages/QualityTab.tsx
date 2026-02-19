import React, { useState } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { qualityApi, QualityPhase1DRegisterResponse, QualityPhase1DRow } from '../api/quality';
import { QualityRegisterTable, EditableFields } from '../components/quality/QualityRegisterTable';
import { QualityModelSidePanel } from '../components/quality/QualityModelSidePanel';
import { generateModelKey } from '../utils/modelKeyGenerator';

interface QualityTabProps {
  projectId: number;
  selectionMode?: 'drawer' | 'external';
  selectedModelId?: number | null;
  onSelectModel?: (modelId: number | null) => void;
}

export const QualityTab: React.FC<QualityTabProps> = ({
  projectId,
  selectionMode = 'drawer',
  selectedModelId: externalSelectedModelId = null,
  onSelectModel,
}) => {
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [draftById, setDraftById] = useState<Record<number, Partial<EditableFields>>>({});
  const [nextTempId, setNextTempId] = useState(-1);
  const [selectedRowIds, setSelectedRowIds] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<'abv' | 'modelName' | 'company' | 'discipline' | 'description' | 'bimContact' | 'accFolderPath' | 'accLiveDate' | 'accSharedDate' | 'notes'>('modelName');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const queryClient = useQueryClient();
  const isExternalSelection = selectionMode === 'external';
  const effectiveSelectedModelId = isExternalSelection ? externalSelectedModelId : selectedModelId;

  const selectModel = (modelId: number | null) => {
    if (isExternalSelection) {
      onSelectModel?.(modelId);
      return;
    }
    setSelectedModelId(modelId);
  };

  // Helper: Check if row is a draft (negative ID)
  const isDraftRow = (rowId: number): boolean => rowId < 0;

  // Guardrail 2: Replace temp draft row with server-returned row
  const replaceTempRowId = (
    tempId: number,
    newId: number,
    rowData: Partial<QualityPhase1DRow>
  ) => {
    // 1. Update cache: replace temp row with server row
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: old.rows.map(row =>
            row.expected_model_id === tempId
              ? { ...row, expected_model_id: newId, ...rowData }
              : row
          )
        };
      }
    );

    // 2. Clear draft buffer (temp ID no longer exists)
    setDraftById(prev => {
      const { [tempId]: _, ...rest } = prev;
      return rest;
    });

    // 3. Exit edit mode (avoids remapping complexity)
    setEditingRowId(null);

    // 4. If selection state exists, update it
    if (effectiveSelectedModelId === tempId) {
      selectModel(newId);
    }
  };

  // Guardrail 3: Safe invalidation wrappers
  const safeInvalidateQualityRegister = () => {
    // QUALITY_REGISTER_SAFE_INVALIDATE_ONLY
    if (editingRowId !== null) {
      console.warn(
        '[QualityTab] Skipping invalidate: row is being edited',
        { editingRowId, projectId }
      );
      return;
    }
    queryClient.invalidateQueries({
      queryKey: ['quality-register-phase1d', projectId]
    });
  };

  const safeRefetchQualityRegister = () => {
    if (editingRowId !== null) {
      console.warn(
        '[QualityTab] Skipping refetch: row is being edited',
        { editingRowId, projectId }
      );
      return;
    }
    queryClient.refetchQueries({
      queryKey: ['quality-register-phase1d', projectId],
      type: 'active'
    });
  };

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

  const { data: qualitySuggestions } = useQuery({
    queryKey: ['qualitySuggestions'],
    queryFn: () => qualityApi.getSuggestions(),
    staleTime: 10 * 60 * 1000,
  });

  const mergeSuggestion = (items: string[] | undefined, next: string | undefined) => {
    if (!next || !next.trim()) return items ?? [];
    const trimmed = next.trim();
    const existing = new Set((items ?? []).map((item) => item.toLowerCase()));
    if (existing.has(trimmed.toLowerCase())) {
      return items ?? [];
    }
    return [...(items ?? []), trimmed].sort((a, b) => a.localeCompare(b));
  };

  const updateSuggestionsCache = (draft: EditableFields) => {
    queryClient.setQueryData(['qualitySuggestions'], (existing: any) => {
      const current = existing ?? { abv: [], disciplines: [], companies: [] };
      return {
        ...current,
        abv: mergeSuggestion(current.abv, draft.abv),
        disciplines: mergeSuggestion(current.disciplines, draft.discipline),
        companies: mergeSuggestion(current.companies, draft.company),
      };
    });
  };

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
                    notes: variables.draft.notes ?? row.notes,
                    accRequiredOverride: variables.draft.accRequiredOverride ?? row.accRequiredOverride
                  }
                : row
            )
          };
        }
      );
      updateSuggestionsCache(variables.draft);
      // Removed invalidation to prevent flicker during edit
    }
  });

  const deleteModelMutation = useMutation({
    mutationFn: (rowId: number) =>
      qualityApi.deleteExpectedModel(projectId, rowId),
    onSuccess: (_, rowId) => {
      // Close side panel if deleted row was selected
      if (effectiveSelectedModelId === rowId) {
        if (isExternalSelection) {
          onSelectModel?.(null);
        } else {
          setSidePanelOpen(false);
          setSelectedModelId(null);
        }
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
      // Removed invalidation to prevent flicker during edit
    }
  });

  const handleRowClick = async (row: any) => {
    // Don't open side panel if editing
    if (editingRowId === row.expected_model_id) {
      return;
    }
    // Auto-save if switching rows while editing
    if (editingRowId !== null) {
      const draft = draftById[editingRowId] || {};
      try {
        await handleSaveRow(editingRowId, draft as EditableFields);
      } catch (error) {
        console.warn('[QualityTab] Failed to auto-save before switching rows', error);
        return;
      }
    }
    selectModel(row.expected_model_id);
    if (!isExternalSelection) {
      setSidePanelOpen(true);
    }
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
        notes: row.notes || '',
        accRequiredOverride: row.accRequiredOverride ?? null
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
    if (draft.accRequiredOverride !== undefined) trimmedDraft.accRequiredOverride = draft.accRequiredOverride;

    // Check if this is a draft row (negative ID)
    if (isDraftRow(rowId)) {
      // Validate required field
      if (!trimmedDraft.registeredModelName || trimmedDraft.registeredModelName === '') {
        alert('Model Name is required');
        return;
      }

      try {
        // Step 1: Create skeleton row (POST)
        const createResponse = await qualityApi.createEmptyModel(projectId);
        const newId = createResponse.id;
        if (!newId) {
          throw new Error('Create returned no ID');
        }

        // Step 2: Always update with full fields (PATCH)
        try {
          await qualityApi.updateExpectedModel(projectId, newId, trimmedDraft);
          updateSuggestionsCache(trimmedDraft);

          // Both calls succeeded - replace draft with saved row
          replaceTempRowId(rowId, newId, {
            expected_model_id: newId,
            abv: trimmedDraft.abv || null,
            modelName: trimmedDraft.registeredModelName || null,
            registeredModelName: trimmedDraft.registeredModelName || null,
            company: trimmedDraft.company || null,
            discipline: trimmedDraft.discipline || null,
            description: trimmedDraft.description || null,
            bimContact: trimmedDraft.bimContact || null,
            notes: trimmedDraft.notes || null,
            accFolderPath: null,
            accLiveDate: null,
            accLiveStatus: 'MISSING',
            accSharedDate: null,
            accSharedStatus: 'MISSING',
            accRequiredOverride: trimmedDraft.accRequiredOverride ?? null,
            notesUpdatedAt: null,
            mappingStatus: 'UNMAPPED',
            matchedObservedFile: null,
            validationOverall: 'UNKNOWN',
            freshnessStatus: 'UNKNOWN',
            needsSync: false
          });
          // Confirm server persistence
          safeRefetchQualityRegister();
        } catch (patchError) {
          // Create succeeded, update failed (partial success)
          console.warn('Row created but update failed', { newId, error: patchError });

          // Still replace draft with new ID (row exists in DB)
          replaceTempRowId(rowId, newId, {
            expected_model_id: newId,
            abv: null,
            modelName: trimmedDraft.registeredModelName || 'New Model',
            registeredModelName: trimmedDraft.registeredModelName || 'New Model',
            company: null,
            discipline: null,
            description: null,
            bimContact: null,
            notes: null,
            accFolderPath: null,
            accLiveDate: null,
            accLiveStatus: 'MISSING',
            accSharedDate: null,
            accSharedStatus: 'MISSING',
            accRequiredOverride: trimmedDraft.accRequiredOverride ?? null,
            notesUpdatedAt: null,
            mappingStatus: 'UNMAPPED',
            matchedObservedFile: null,
            validationOverall: 'UNKNOWN',
            freshnessStatus: 'UNKNOWN',
            needsSync: true  // Flag for partial success
          });
          safeRefetchQualityRegister();

          // Show warning toast (non-blocking)
          alert('Row created but some fields not saved. Click the row to edit and retry.');
        }
      } catch (createError) {
        // Create failed - show error and keep draft for retry
        console.error('Failed to create row', { error: createError });
        alert(`Failed to create row: ${(createError as Error).message}`);
        // Keep draft in edit mode for retry
      }
    } else {
      // Existing row - use update mutation
      await updateModelMutation.mutateAsync({ rowId, draft: trimmedDraft });
    }
  };

  const handleCancelEdit = (rowId: number) => {
    // If draft, remove from cache entirely
    if (isDraftRow(rowId)) {
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.filter(row => row.expected_model_id !== rowId)
          };
        }
      );
    }

    // Clear edit state
    setEditingRowId(null);
    setDraftById((prev) => {
      const { [rowId]: _, ...rest } = prev;
      return rest;
    });
  };

  const handleAddRow = () => {
    // Create draft row with temp ID (no API call)
    const tempId = nextTempId;
    setNextTempId(prev => prev - 1); // Decrement for next draft

    // Add draft to cache
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: [
            ...old.rows,
            {
              expected_model_id: tempId,
              abv: null,
              modelName: null,
              company: null,
              discipline: null,
              description: null,
              bimContact: null,
              accFolderPath: null,
              accLiveDate: null,
              accLiveStatus: 'MISSING',
              accSharedDate: null,
              accSharedStatus: 'MISSING',
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

    // Enter edit mode immediately
    setEditingRowId(tempId);
    setDraftById((prev) => ({
      ...prev,
      [tempId]: {
        abv: '',
        registeredModelName: '',
        company: '',
        discipline: '',
        description: '',
        bimContact: '',
        notes: '',
        accRequiredOverride: null
      }
    }));
  };

  const addDraftRows = (modelNames: string[]) => {
    if (modelNames.length === 0) return;
    const tempIds: number[] = [];
    let tempId = nextTempId;
    for (let i = 0; i < modelNames.length; i += 1) {
      tempIds.push(tempId);
      tempId -= 1;
    }
    setNextTempId(tempId);

    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        const newRows = modelNames.map((name, index) => ({
          expected_model_id: tempIds[index],
          abv: null,
          modelName: name,
          company: null,
          discipline: null,
          description: null,
          bimContact: null,
          accFolderPath: null,
          accLiveDate: null,
          accLiveStatus: 'MISSING' as const,
          accSharedDate: null,
          accSharedStatus: 'MISSING' as const,
          notes: null,
          notesUpdatedAt: null,
          mappingStatus: 'UNMAPPED',
          matchedObservedFile: null,
          validationOverall: 'UNKNOWN',
          freshnessStatus: 'UNKNOWN'
        }));
        return {
          ...old,
          rows: [...old.rows, ...newRows]
        };
      }
    );
  };

  const handleBulkAddModelNames = (rowId: number, modelNames: string[]) => {
    const cleaned = modelNames.map((name) => name.trim()).filter((name) => name.length > 0);
    if (cleaned.length === 0) return;

    const [firstName, ...remaining] = cleaned;

    setDraftById((prev) => ({
      ...prev,
      [rowId]: {
        ...prev[rowId],
        registeredModelName: firstName
      }
    }));

    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: old.rows.map((row) =>
            row.expected_model_id === rowId
              ? { ...row, modelName: firstName }
              : row
          )
        };
      }
    );

    if (remaining.length > 0) {
      addDraftRows(remaining);
    }
  };

  const handleDraftChange = (rowId: number, field: keyof EditableFields, value: string | boolean | null) => {
    setDraftById((prev) => ({
      ...prev,
      [rowId]: {
        ...prev[rowId],
        [field]: value
      }
    }));
  };

  const handleToggleSelectRow = (rowId: number) => {
    setSelectedRowIds((prev) => {
      const next = new Set(prev);
      if (next.has(rowId)) {
        next.delete(rowId);
      } else {
        next.add(rowId);
      }
      return next;
    });
  };

  const handleToggleSelectAll = (checked: boolean) => {
    if (!checked) {
      setSelectedRowIds(new Set());
      return;
    }
    const allIds = new Set((data?.rows || []).map((row) => row.expected_model_id));
    setSelectedRowIds(allIds);
  };

  const handleClearSelection = () => {
    setSelectedRowIds(new Set());
  };

  const handleBulkDelete = async () => {
    if (selectedRowIds.size === 0) return;
    if (editingRowId !== null) {
      alert('Finish editing the current row before bulk deleting.');
      return;
    }
    const confirmed = window.confirm(`Delete ${selectedRowIds.size} selected rows? This cannot be undone.`);
    if (!confirmed) return;

    const selectedIds = Array.from(selectedRowIds);
    const draftIds = selectedIds.filter((id) => id < 0);
    const existingIds = selectedIds.filter((id) => id >= 0);

    if (draftIds.length > 0) {
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.filter((row) => !draftIds.includes(row.expected_model_id))
          };
        }
      );
      setDraftById((prev) => {
        const next = { ...prev };
        for (const rowId of draftIds) {
          delete next[rowId];
        }
        return next;
      });
    }

    if (existingIds.length > 0) {
      await Promise.all(
        existingIds.map((rowId) =>
          qualityApi.deleteExpectedModel(projectId, rowId)
        )
      );

      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.filter((row) => !existingIds.includes(row.expected_model_id))
          };
        }
      );
    }

    handleClearSelection();
  };

  const handleBulkEdit = async (updates: EditableFields) => {
    if (selectedRowIds.size === 0) return;
    if (editingRowId !== null) {
      alert('Finish editing the current row before bulk editing.');
      return;
    }

    const trimmedUpdates: EditableFields = {};
    if (updates.abv !== undefined) trimmedUpdates.abv = updates.abv.trim();
    if (updates.company !== undefined) trimmedUpdates.company = updates.company.trim();
    if (updates.discipline !== undefined) trimmedUpdates.discipline = updates.discipline.trim();
    if (updates.bimContact !== undefined) trimmedUpdates.bimContact = updates.bimContact.trim();
    if (updates.notes !== undefined) trimmedUpdates.notes = updates.notes.trim();

    const hasUpdates = Object.values(trimmedUpdates).some((value) => value !== undefined && value !== '');
    if (!hasUpdates) {
      alert('Enter at least one field to apply.');
      return;
    }

    const selectedIds = Array.from(selectedRowIds);
    const draftIds = selectedIds.filter((id) => id < 0);
    const existingIds = selectedIds.filter((id) => id >= 0);

    if (draftIds.length > 0) {
      setDraftById((prev) => {
        const next = { ...prev };
        for (const rowId of draftIds) {
          next[rowId] = {
            ...next[rowId],
            ...trimmedUpdates
          };
        }
        return next;
      });

      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.map((row) => {
              if (!draftIds.includes(row.expected_model_id)) return row;
              return {
                ...row,
                abv: trimmedUpdates.abv ?? row.abv,
                company: trimmedUpdates.company ?? row.company,
                discipline: trimmedUpdates.discipline ?? row.discipline,
                bimContact: trimmedUpdates.bimContact ?? row.bimContact,
                notes: trimmedUpdates.notes ?? row.notes
              };
            })
          };
        }
      );
    }

    if (existingIds.length > 0) {
      await Promise.all(
        existingIds.map((rowId) =>
          qualityApi.updateExpectedModel(projectId, rowId, trimmedUpdates)
        )
      );

      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.map((row) => {
              if (!existingIds.includes(row.expected_model_id)) return row;
              return {
                ...row,
                abv: trimmedUpdates.abv ?? row.abv,
                company: trimmedUpdates.company ?? row.company,
                discipline: trimmedUpdates.discipline ?? row.discipline,
                bimContact: trimmedUpdates.bimContact ?? row.bimContact,
                notes: trimmedUpdates.notes ?? row.notes
              };
            })
          };
        }
      );
    }

    updateSuggestionsCache(trimmedUpdates);
    handleClearSelection();
  };

  const handleDeleteRow = async (rowId: number) => {
    // If draft, just remove from cache (no API call)
    if (isDraftRow(rowId)) {
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.filter(row => row.expected_model_id !== rowId)
          };
        }
      );

      // Clear edit state if this draft was being edited
      if (editingRowId === rowId) {
        setEditingRowId(null);
        setDraftById((prev) => {
          const { [rowId]: _, ...rest } = prev;
          return rest;
        });
      }
      return;
    }

    // Existing row - call API
    await deleteModelMutation.mutateAsync(rowId);
  };

  const handleCloseSidePanel = () => {
    if (isExternalSelection) {
      onSelectModel?.(null);
      return;
    }
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
        rows={(data?.rows || [])
          .slice()
          .sort((a, b) => {
            const dir = sortDirection === 'asc' ? 1 : -1;
            const value = (row: QualityPhase1DRow) => {
              switch (sortBy) {
                case 'abv':
                  return row.abv ?? '';
                case 'modelName':
                  return row.modelName ?? '';
                case 'company':
                  return row.company ?? '';
                case 'discipline':
                  return row.discipline ?? '';
                case 'description':
                  return row.description ?? '';
                case 'bimContact':
                  return row.bimContact ?? '';
                case 'accFolderPath':
                  return row.accFolderPath ?? '';
                case 'accLiveDate':
                  return row.accLiveDate ? new Date(row.accLiveDate).getTime() : 0;
                case 'accSharedDate':
                  return row.accSharedDate ? new Date(row.accSharedDate).getTime() : 0;
                case 'notes':
                  return row.notes ?? '';
                default:
                  return '';
              }
            };
            const aVal = value(a);
            const bVal = value(b);
            if (typeof aVal === 'number' && typeof bVal === 'number') {
              if (aVal === bVal) return 0;
              return aVal > bVal ? dir : -dir;
            }
            const aStr = String(aVal).toLowerCase();
            const bStr = String(bVal).toLowerCase();
            if (aStr === bStr) return 0;
            return aStr > bStr ? dir : -dir;
          })}
        onRowClick={handleRowClick}
        selectedRowId={effectiveSelectedModelId}
        editingRowId={editingRowId}
        onEditRow={handleEditRow}
        onSaveRow={handleSaveRow}
        onCancelEdit={handleCancelEdit}
        onDeleteRow={handleDeleteRow}
        onAddRow={handleAddRow}
        isAddingRow={false}
        draftById={draftById}
        onDraftChange={handleDraftChange}
        onBulkAddModelNames={handleBulkAddModelNames}
        selectedRowIds={selectedRowIds}
        onToggleSelectRow={handleToggleSelectRow}
        onToggleSelectAll={handleToggleSelectAll}
        onApplyBulkEdit={handleBulkEdit}
        onClearSelection={handleClearSelection}
        onBulkDelete={handleBulkDelete}
        suggestions={{
          abv: qualitySuggestions?.abv ?? [],
          disciplines: qualitySuggestions?.disciplines ?? [],
          companies: qualitySuggestions?.companies ?? [],
        }}
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSortChange={(nextSortBy) => {
          if (sortBy === nextSortBy) {
            setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
          } else {
            setSortBy(nextSortBy);
            setSortDirection('asc');
          }
        }}
      />

      {!isExternalSelection && (
        <QualityModelSidePanel
          projectId={projectId}
          expectedModelId={effectiveSelectedModelId}
          open={sidePanelOpen}
          onClose={handleCloseSidePanel}
        />
      )}
    </Box>
  );
};
