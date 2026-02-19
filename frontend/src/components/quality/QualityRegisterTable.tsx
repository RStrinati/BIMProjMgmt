import React, { useState, useEffect, useRef } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableFooter,
  TableSortLabel,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Checkbox,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  CircularProgress,
  Tooltip,
  Autocomplete,
  MenuItem
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import WarningIcon from '@mui/icons-material/Warning';

interface QualityRegisterRow {
  expected_model_id: number;
  abv: string | null;
  modelName: string | null;
  company: string | null;
  discipline: string | null;
  description: string | null;
  bimContact: string | null;
  accFolderPath?: string | null;
  accLiveDate: string | null;
  accLiveStatus: 'CURRENT' | 'OUT_OF_DATE' | 'MISSING' | 'NOT_REQUIRED';
  accSharedDate: string | null;
  accSharedStatus: 'CURRENT' | 'OUT_OF_DATE' | 'MISSING' | 'NOT_REQUIRED';
  accRequiredOverride?: boolean | null;
  notes: string | null;
  notesUpdatedAt: string | null;
  mappingStatus: string;
  matchedObservedFile: string | null;
  validationOverall: string;
  freshnessStatus: string;
}

export interface EditableFields {
  abv?: string;
  registeredModelName?: string;
  company?: string;
  discipline?: string;
  description?: string;
  bimContact?: string;
  notes?: string;
  accRequiredOverride?: boolean | null;
}

interface QualityRegisterTableProps {
  rows: QualityRegisterRow[];
  onRowClick: (row: QualityRegisterRow) => void;
  selectedRowId: number | null;
  editingRowId: number | null;
  onEditRow: (rowId: number) => void;
  onSaveRow: (rowId: number, draft: EditableFields) => Promise<void>;
  onCancelEdit: (rowId: number) => void;
  onDeleteRow: (rowId: number) => Promise<void>;
  onAddRow: () => void;
  isAddingRow: boolean;
  draftById: Record<number, Partial<EditableFields>>;
  onDraftChange: (rowId: number, field: keyof EditableFields, value: string | boolean | null) => void;
  onBulkAddModelNames: (rowId: number, modelNames: string[]) => void;
  selectedRowIds: Set<number>;
  onToggleSelectRow: (rowId: number) => void;
  onToggleSelectAll: (checked: boolean) => void;
  onApplyBulkEdit: (updates: EditableFields) => void;
  onClearSelection: () => void;
  onBulkDelete: () => void;
  suggestions: {
    abv: string[];
    disciplines: string[];
    companies: string[];
  };
  sortBy: 'abv' | 'modelName' | 'company' | 'discipline' | 'description' | 'bimContact' | 'accFolderPath' | 'accLiveDate' | 'accSharedDate' | 'notes';
  sortDirection: 'asc' | 'desc';
  onSortChange: (sortBy: QualityRegisterTableProps['sortBy']) => void;
}

export const QualityRegisterTable: React.FC<QualityRegisterTableProps> = ({
  rows,
  onRowClick,
  selectedRowId,
  editingRowId,
  onEditRow,
  onSaveRow,
  onCancelEdit,
  onDeleteRow,
  onAddRow,
  isAddingRow,
  draftById,
  onDraftChange,
  onBulkAddModelNames,
  selectedRowIds,
  onToggleSelectRow,
  onToggleSelectAll,
  onApplyBulkEdit,
  onClearSelection,
  onBulkDelete,
  suggestions,
  sortBy,
  sortDirection,
  onSortChange
}) => {
  const [savingRowId, setSavingRowId] = useState<number | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [deletingRowId, setDeletingRowId] = useState<number | null>(null);
  const firstCellRef = useRef<HTMLInputElement>(null);
  const editingRowRef = useRef<HTMLTableRowElement | null>(null);
  const isSelectOpenRef = useRef(false);
  const noWrapCell = { whiteSpace: 'nowrap' } as const;
  useEffect(() => {
    // Auto-focus first editable cell when entering edit mode
    if (editingRowId && firstCellRef.current) {
      setTimeout(() => firstCellRef.current?.focus(), 50);
    }
  }, [editingRowId]);

  useEffect(() => {
    if (!editingRowId) return;
    const handlePointerDown = (event: PointerEvent) => {
      if (!editingRowRef.current) return;
      if (isSelectOpenRef.current) return;
      const target = event.target as Node | null;
      if (target && editingRowRef.current.contains(target)) {
        return;
      }
      if (savingRowId === editingRowId) {
        return;
      }
      handleSaveClick(editingRowId);
    };
    document.addEventListener('pointerdown', handlePointerDown, true);
    return () => document.removeEventListener('pointerdown', handlePointerDown, true);
  }, [editingRowId, savingRowId]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString();
  };

  const renderAccStatus = (status: QualityRegisterRow['accLiveStatus']) => {
    if (status === 'NOT_REQUIRED') {
      return <Typography variant="body2">-</Typography>;
    }
    if (status === 'CURRENT') {
      return <CheckCircleIcon color="success" fontSize="small" />;
    }
    return <CancelIcon color="error" fontSize="small" />;
  };

  const handleSaveClick = async (rowId: number) => {
    setSavingRowId(rowId);
    try {
      await onSaveRow(rowId, draftById[rowId] || {});
    } finally {
      setSavingRowId(null);
    }
  };

  const handleBlurSave = (rowId: number) => {
    if (!editingRowRef.current) return;
    if (isSelectOpenRef.current) return;
    setTimeout(() => {
      if (!editingRowRef.current) return;
      const active = document.activeElement;
      if (active && editingRowRef.current.contains(active)) {
        return;
      }
      if (savingRowId === rowId) return;
      handleSaveClick(rowId);
    }, 0);
  };

  const handleDeleteClick = (rowId: number) => {
    setDeleteTargetId(rowId);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (deleteTargetId === null) return;
    
    setDeletingRowId(deleteTargetId);
    try {
      await onDeleteRow(deleteTargetId);
      setDeleteConfirmOpen(false);
      setDeleteTargetId(null);
    } finally {
      setDeletingRowId(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setDeleteTargetId(null);
  };

  const handleCellClick = (row: QualityRegisterRow, e: React.MouseEvent) => {
    // Don't open side panel if row is being edited
    if (editingRowId === row.expected_model_id) {
      return;
    }
    // Don't open side panel if clicking on action buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    onRowClick(row);
  };

  const handleKeyDown = (e: React.KeyboardEvent, rowId: number, currentField: keyof EditableFields, fields: (keyof EditableFields)[]) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveClick(rowId);
    } else if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      // Move to previous field
      const currentIndex = fields.indexOf(currentField);
      if (currentIndex > 0) {
        const prevField = fields[currentIndex - 1];
        const prevInput = document.querySelector(`input[data-row="${rowId}"][data-field="${prevField}"]`) as HTMLInputElement;
        prevInput?.focus();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancelEdit(rowId);
    }
  };

  const editableFields: (keyof EditableFields)[] = ['abv', 'registeredModelName', 'company', 'discipline', 'description', 'bimContact', 'notes'];
  const bulkEditableFields: (keyof EditableFields)[] = ['abv', 'company', 'discipline', 'bimContact', 'notes'];

  const selectedCount = selectedRowIds.size;
  const allSelected = rows.length > 0 && selectedCount === rows.length;
  const partiallySelected = selectedCount > 0 && selectedCount < rows.length;
  const shouldBulkApply = (rowId: number, field: keyof EditableFields) => {
    return selectedCount > 1 && selectedRowIds.has(rowId) && bulkEditableFields.includes(field);
  };

  const parseModelNames = (rawText: string) => {
    return rawText
      .split(/\r?\n/)
      .map((line) => line.split('\t')[0].trim())
      .filter((name) => name.length > 0);
  };

  const handleModelNamePaste = (event: React.ClipboardEvent, rowId: number) => {
    const text = event.clipboardData?.getData('text') ?? '';
    const modelNames = parseModelNames(text);
    if (modelNames.length <= 1) {
      return;
    }
    event.preventDefault();
    onBulkAddModelNames(rowId, modelNames);
  };

  const renderEditableCell = (row: QualityRegisterRow, field: keyof EditableFields, displayValue: string | null) => {
    const isEditing = editingRowId === row.expected_model_id;
    const draft = draftById[row.expected_model_id] || {};
    const value = draft[field] !== undefined ? draft[field] : displayValue;

    if (isEditing) {
      if (field === 'abv' || field === 'company' || field === 'discipline') {
        const options =
          field === 'abv'
            ? suggestions.abv
            : field === 'company'
              ? suggestions.companies
              : suggestions.disciplines;
          return (
            <Autocomplete
              freeSolo
              options={options}
              value={value || ''}
              onChange={(_, newValue) => {
                onDraftChange(row.expected_model_id, field, String(newValue || ''));
              }}
              onInputChange={(_, newValue, reason) => {
                if (reason === 'input' || reason === 'clear') {
                  onDraftChange(row.expected_model_id, field, newValue);
                }
              }}
              onOpen={() => {
                isSelectOpenRef.current = true;
              }}
              onClose={() => {
                isSelectOpenRef.current = false;
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  size="small"
                  fullWidth
                  sx={{
                    minWidth: 120,
                    '& .MuiInputBase-root': {
                      height: 32,
                      fontSize: field === 'notes' ? '0.85rem' : 'inherit'
                    },
                    '& .MuiInputBase-input': {
                      padding: '6px 8px'
                    }
                  }}
                  onKeyDown={(e) => handleKeyDown(e, row.expected_model_id, field, editableFields)}
                  onBlur={() => {
                    if (shouldBulkApply(row.expected_model_id, field)) {
                      const currentValue = String(draft[field] ?? value ?? '');
                      onApplyBulkEdit({ [field]: currentValue });
                    }
                    handleBlurSave(row.expected_model_id);
                  }}
                  inputRef={field === 'abv' ? firstCellRef : undefined}
                  inputProps={{
                    ...params.inputProps,
                    'data-row': row.expected_model_id,
                    'data-field': field
                }}
              />
            )}
          />
        );
      }
      return (
        <TextField
          size="small"
          fullWidth
          value={value || ''}
          onChange={(e) => onDraftChange(row.expected_model_id, field, e.target.value)}
          onKeyDown={(e) => handleKeyDown(e, row.expected_model_id, field, editableFields)}
          onBlur={(e) => {
            if (shouldBulkApply(row.expected_model_id, field)) {
              onApplyBulkEdit({ [field]: e.currentTarget.value });
            }
            handleBlurSave(row.expected_model_id);
          }}
          onPaste={(event) => {
            if (field === 'registeredModelName') {
              handleModelNamePaste(event, row.expected_model_id);
            }
          }}
          inputRef={field === 'abv' ? firstCellRef : undefined}
          inputProps={{
            'data-row': row.expected_model_id,
            'data-field': field
          }}
            sx={{
              minWidth: 120,
              '& .MuiInputBase-root': {
                height: 32,
                fontSize: field === 'notes' ? '0.85rem' : 'inherit'
              },
              '& .MuiInputBase-input': {
                padding: '6px 8px'
              }
            }}
          />
        );
      }

    return value || '—';
  };

  return (
    <Box>
      <Paper sx={{ p: 1.5, mb: 1.5, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Typography variant="subtitle2">Selected: {selectedCount}</Typography>
          <Typography variant="caption" color="text.secondary">
            Edit a cell to apply its value to all selected rows.
          </Typography>
          <Button
            size="small"
            disabled={selectedCount === 0}
            onClick={onClearSelection}
          >
            Clear selection
          </Button>
          <Button
            size="small"
            color="error"
            disabled={selectedCount === 0}
            onClick={onBulkDelete}
          >
            Delete selected
          </Button>
        </Box>
      </Paper>

      <TableContainer
        component={Paper}
        sx={{
          maxHeight: 'calc(100vh - 250px)',
          width: '100%',
          overflowX: 'auto',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
        }}
      >
        <Table
          stickyHeader
          size="small"
          sx={{
            minWidth: 1400,
            tableLayout: 'fixed',
            '& .MuiTableCell-root': {
              py: 0.5,
              height: 48,
              verticalAlign: 'middle',
            },
          }}
        >
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox">
              <Checkbox
                size="small"
                checked={allSelected}
                indeterminate={partiallySelected}
                onChange={(e) => onToggleSelectAll(e.target.checked)}
              />
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'abv'} direction={sortBy === 'abv' ? sortDirection : 'asc'} onClick={() => onSortChange('abv')}>
                ABV
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ width: 280, minWidth: 280, whiteSpace: 'nowrap' }}>
              <TableSortLabel active={sortBy === 'modelName'} direction={sortBy === 'modelName' ? sortDirection : 'asc'} onClick={() => onSortChange('modelName')}>
                Model Name
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'company'} direction={sortBy === 'company' ? sortDirection : 'asc'} onClick={() => onSortChange('company')}>
                Company
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'discipline'} direction={sortBy === 'discipline' ? sortDirection : 'asc'} onClick={() => onSortChange('discipline')}>
                Discipline
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'description'} direction={sortBy === 'description' ? sortDirection : 'asc'} onClick={() => onSortChange('description')}>
                Description
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'bimContact'} direction={sortBy === 'bimContact' ? sortDirection : 'asc'} onClick={() => onSortChange('bimContact')}>
                BIM Contact
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'accFolderPath'} direction={sortBy === 'accFolderPath' ? sortDirection : 'asc'} onClick={() => onSortChange('accFolderPath')}>
                Folder Path
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ ...noWrapCell, width: 120 }}>
              ACC Req
            </TableCell>
            <TableCell align="center" sx={noWrapCell}>
              ACC Live
            </TableCell>
            <TableCell sx={noWrapCell}>
              <TableSortLabel active={sortBy === 'accLiveDate'} direction={sortBy === 'accLiveDate' ? sortDirection : 'asc'} onClick={() => onSortChange('accLiveDate')}>
                ACC Live Date
              </TableSortLabel>
            </TableCell>
            <TableCell align="center" sx={noWrapCell}>
              ACC Shared
            </TableCell>
            <TableCell sx={noWrapCell}>
              <TableSortLabel active={sortBy === 'accSharedDate'} direction={sortBy === 'accSharedDate' ? sortDirection : 'asc'} onClick={() => onSortChange('accSharedDate')}>
                ACC Shared Date
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel active={sortBy === 'notes'} direction={sortBy === 'notes' ? sortDirection : 'asc'} onClick={() => onSortChange('notes')}>
                Notes
              </TableSortLabel>
            </TableCell>
            <TableCell align="right" sx={noWrapCell}><strong>Actions</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={15} align="center">
                <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                  No models registered. Click "Add row" below to create the first entry.
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => {
              const isEditing = editingRowId === row.expected_model_id;
              const isDraft = row.expected_model_id < 0;
              return (
                <TableRow
                  key={row.expected_model_id}
                  hover={!isEditing}
                  onClick={(e) => handleCellClick(row, e)}
                  selected={selectedRowId === row.expected_model_id || isEditing}
                  sx={{ 
                    cursor: isEditing ? 'default' : 'pointer',
                    height: 48,
                    maxHeight: 48,
                    '& .MuiTableCell-root': {
                      height: 48,
                      py: 0.5,
                      boxSizing: 'border-box',
                    },
                    '& .MuiInputBase-root': {
                      height: 32,
                      boxSizing: 'border-box',
                    },
                    '& .MuiOutlinedInput-input': {
                      padding: '6px 8px',
                      boxSizing: 'border-box',
                    },
                    '& .MuiAutocomplete-inputRoot': {
                      paddingTop: '0 !important',
                      paddingBottom: '0 !important',
                    },
                    backgroundColor: isDraft 
                      ? '#fff3cd' // Yellow background for drafts
                      : isEditing 
                      ? 'action.selected' 
                      : undefined,
                    borderLeft: isDraft ? '4px solid #fd7e14' : undefined // Orange left border for drafts
                  }}
                  ref={isEditing ? editingRowRef : undefined}
                >
                  <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      size="small"
                      checked={selectedRowIds.has(row.expected_model_id)}
                      onChange={() => onToggleSelectRow(row.expected_model_id)}
                    />
                  </TableCell>
                  <TableCell
                    onClick={() => !isEditing && onEditRow(row.expected_model_id)}
                    sx={{ width: 110 }}
                  >
                    {renderEditableCell(row, 'abv', row.abv)}
                  </TableCell>
                  <TableCell
                    onClick={() => !isEditing && onEditRow(row.expected_model_id)}
                    sx={{ width: 280, minWidth: 280, whiteSpace: 'nowrap' }}
                  >
                    {isEditing ? (
                      renderEditableCell(row, 'registeredModelName', row.modelName)
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {row.modelName || '—'}
                        {row.needsSync && (
                          <Tooltip title="Some fields not saved. Edit row to retry.">
                            <WarningIcon 
                              fontSize="small" 
                              color="warning" 
                              sx={{ ml: 0.5 }} 
                            />
                          </Tooltip>
                        )}
                      </Box>
                    )}
                  </TableCell>
                  <TableCell onClick={() => !isEditing && onEditRow(row.expected_model_id)}>
                    {renderEditableCell(row, 'company', row.company)}
                  </TableCell>
                  <TableCell onClick={() => !isEditing && onEditRow(row.expected_model_id)}>
                    {renderEditableCell(row, 'discipline', row.discipline)}
                  </TableCell>
                  <TableCell 
                    onClick={() => !isEditing && onEditRow(row.expected_model_id)}
                    sx={{ maxWidth: isEditing ? 'none' : 200, overflow: 'hidden', textOverflow: 'ellipsis' }}
                  >
                    {renderEditableCell(row, 'description', row.description)}
                  </TableCell>
                  <TableCell onClick={() => !isEditing && onEditRow(row.expected_model_id)}>
                    {renderEditableCell(row, 'bimContact', row.bimContact)}
                  </TableCell>
                  {/* Read-only columns */}
                  <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.85rem' }}>
                    {row.accFolderPath || '—'}
                  </TableCell>
                  <TableCell sx={{ ...noWrapCell, width: 120 }}>
                    {isEditing ? (
                      <TextField
                        select
                        size="small"
                        fullWidth
                        value={
                          draftById[row.expected_model_id]?.accRequiredOverride === true
                            ? 'true'
                            : draftById[row.expected_model_id]?.accRequiredOverride === false
                              ? 'false'
                              : row.accRequiredOverride === true
                                ? 'true'
                                : row.accRequiredOverride === false
                                  ? 'false'
                                  : ''
                        }
                        sx={{ minWidth: 120 }}
                        onChange={(event) => {
                          const value = event.target.value;
                          onDraftChange(
                            row.expected_model_id,
                            'accRequiredOverride',
                            value === '' ? null : value === 'true'
                          );
                        }}
                        onBlur={() => handleBlurSave(row.expected_model_id)}
                        SelectProps={{
                          displayEmpty: true,
                          onOpen: () => {
                            isSelectOpenRef.current = true;
                          },
                          onClose: () => {
                            isSelectOpenRef.current = false;
                          },
                        }}
                      >
                        <MenuItem value="">Default</MenuItem>
                        <MenuItem value="true">Required</MenuItem>
                        <MenuItem value="false">Not required</MenuItem>
                      </TextField>
                    ) : (
                      <Typography variant="body2">
                        {row.accRequiredOverride == null
                          ? 'Default'
                          : row.accRequiredOverride
                            ? 'Required'
                            : 'Not required'}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="center" sx={noWrapCell}>
                    {renderAccStatus(row.accLiveStatus)}
                  </TableCell>
                  <TableCell sx={noWrapCell}>{formatDate(row.accLiveDate)}</TableCell>
                  <TableCell align="center" sx={noWrapCell}>
                    {renderAccStatus(row.accSharedStatus)}
                  </TableCell>
                  <TableCell sx={noWrapCell}>{formatDate(row.accSharedDate)}</TableCell>
<TableCell 
                    onClick={() => !isEditing && onEditRow(row.expected_model_id)}
                    sx={{ maxWidth: isEditing ? 'none' : 200, overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.85rem' }}
                  >
                    {isEditing ? (
                      renderEditableCell(row, 'notes', row.notes)
                    ) : (
                      row.notes ? (
                        <Box>
                          {row.notes.substring(0, 50)}
                          {row.notes.length > 50 && '...'}
                        </Box>
                      ) : (
                        '—'
                      )
                    )}
                  </TableCell>
                  {/* Actions column */}
                  <TableCell align="right" sx={{ width: 120, ...noWrapCell }}>
                    {isEditing ? (
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
                        {savingRowId === row.expected_model_id && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mr: 0.5 }}>
                            <CircularProgress size={14} />
                            <Typography variant="caption">Saving...</Typography>
                          </Box>
                        )}
                        <IconButton
                          size="small"
                          onClick={() => onCancelEdit(row.expected_model_id)}
                          disabled={savingRowId === row.expected_model_id}
                          title="Cancel (Esc)"
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    ) : (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(row.expected_model_id);
                        }}
                        disabled={deletingRowId === row.expected_model_id}
                        title="Delete row"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={15}>
              <Button
                startIcon={<AddIcon />}
                onClick={onAddRow}
                disabled={isAddingRow || editingRowId !== null}
                size="small"
                sx={{ textTransform: 'none' }}
              >
                Add row
              </Button>
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={handleDeleteCancel}
        maxWidth="xs"
      >
        <DialogTitle>Delete Model Row?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this model row? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deletingRowId !== null}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deletingRowId !== null}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </TableContainer>
    </Box>
  );
};
