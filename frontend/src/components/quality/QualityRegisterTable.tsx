import React, { useState, useEffect, useRef } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableFooter,
  Paper,
  Chip,
  Typography,
  Box,
  TextField,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

interface QualityRegisterRow {
  expected_model_id: number;
  abv: string | null;
  modelName: string | null;
  company: string | null;
  discipline: string | null;
  description: string | null;
  bimContact: string | null;
  folderPath: string | null;
  accPresent: boolean;
  accDate: string | null;
  reviztoPresent: boolean;
  reviztoDate: string | null;
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
  onDraftChange: (rowId: number, field: keyof EditableFields, value: string) => void;
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
  onDraftChange
}) => {
  const [savingRowId, setSavingRowId] = useState<number | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [deletingRowId, setDeletingRowId] = useState<number | null>(null);
  const firstCellRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    // Auto-focus first editable cell when entering edit mode
    if (editingRowId && firstCellRef.current) {
      setTimeout(() => firstCellRef.current?.focus(), 50);
    }
  }, [editingRowId]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString();
  };

  const getMappingStatusColor = (status: string) => {
    switch (status) {
      case 'MAPPED': return 'success';
      case 'ALIASED': return 'info';
      case 'UNMAPPED': return 'warning';
      default: return 'default';
    }
  };

  const handleSaveClick = async (rowId: number) => {
    setSavingRowId(rowId);
    try {
      await onSaveRow(rowId, draftById[rowId] || {});
    } finally {
      setSavingRowId(null);
    }
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
      // Move to next field
      const currentIndex = fields.indexOf(currentField);
      if (currentIndex < fields.length - 1) {
        const nextField = fields[currentIndex + 1];
        const nextInput = document.querySelector(`input[data-row="${rowId}"][data-field="${nextField}"]`) as HTMLInputElement;
        nextInput?.focus();
      }
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

  const renderEditableCell = (row: QualityRegisterRow, field: keyof EditableFields, displayValue: string | null) => {
    const isEditing = editingRowId === row.expected_model_id;
    const draft = draftById[row.expected_model_id] || {};
    const value = draft[field] !== undefined ? draft[field] : displayValue;

    if (isEditing) {
      return (
        <TextField
          size="small"
          fullWidth
          value={value || ''}
          onChange={(e) => onDraftChange(row.expected_model_id, field, e.target.value)}
          onKeyDown={(e) => handleKeyDown(e, row.expected_model_id, field, editableFields)}
          inputRef={field === 'abv' ? firstCellRef : undefined}
          inputProps={{
            'data-row': row.expected_model_id,
            'data-field': field
          }}
          multiline={field === 'description' || field === 'notes'}
          rows={field === 'description' ? 2 : field === 'notes' ? 1 : 1}
          sx={{
            '& .MuiInputBase-root': {
              fontSize: field === 'notes' ? '0.85rem' : 'inherit'
            }
          }}
        />
      );
    }

    return value || '—';
  };

  return (
    <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 250px)' }}>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell><strong>ABV</strong></TableCell>
            <TableCell><strong>Model Name</strong></TableCell>
            <TableCell><strong>Company</strong></TableCell>
            <TableCell><strong>Discipline</strong></TableCell>
            <TableCell><strong>Description</strong></TableCell>
            <TableCell><strong>BIM Contact</strong></TableCell>
            <TableCell><strong>Folder Path</strong></TableCell>
            <TableCell align="center"><strong>ACC</strong></TableCell>
            <TableCell><strong>ACC Date</strong></TableCell>
            <TableCell align="center"><strong>Revizto</strong></TableCell>
            <TableCell><strong>Revizto Date</strong></TableCell>
            <TableCell><strong>Notes</strong></TableCell>
            <TableCell align="right"><strong>Actions</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={13} align="center">
                <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                  No models registered. Click "Add row" below to create the first entry.
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => {
              const isEditing = editingRowId === row.expected_model_id;
              return (
                <TableRow
                  key={row.expected_model_id}
                  hover={!isEditing}
                  onClick={(e) => handleCellClick(row, e)}
                  selected={selectedRowId === row.expected_model_id || isEditing}
                  sx={{ 
                    cursor: isEditing ? 'default' : 'pointer',
                    backgroundColor: isEditing ? 'action.selected' : undefined
                  }}
                >
                  <TableCell onClick={() => !isEditing && onEditRow(row.expected_model_id)}>
                    {renderEditableCell(row, 'abv', row.abv)}
                  </TableCell>
                  <TableCell onClick={() => !isEditing && onEditRow(row.expected_model_id)}>
                    {isEditing ? (
                      renderEditableCell(row, 'registeredModelName', row.modelName)
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {row.modelName || '—'}
                        <Chip
                          label={row.mappingStatus}
                          size="small"
                          color={getMappingStatusColor(row.mappingStatus) as any}
                          sx={{ fontSize: '0.7rem' }}
                        />
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
                    {row.folderPath || '—'}
                  </TableCell>
                  <TableCell align="center">
                    {row.accPresent ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <CancelIcon color="disabled" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>{formatDate(row.accDate)}</TableCell>
                  <TableCell align="center">
                    {row.reviztoPresent ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <CancelIcon color="disabled" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>{formatDate(row.reviztoDate)}</TableCell>
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
                  <TableCell align="right" sx={{ width: 120 }}>
                    {isEditing ? (
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleSaveClick(row.expected_model_id)}
                          disabled={savingRowId === row.expected_model_id}
                          title="Save (Esc to cancel)"
                        >
                          <SaveIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => onCancelEdit(row.expected_model_id)}
                          disabled={savingRowId === row.expected_model_id}
                          title="Cancel"
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
            <TableCell colSpan={13}>
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
  );
};
