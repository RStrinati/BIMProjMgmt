import { useState, useCallback } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Stack,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';

type EditableCellProps = {
  value: string | null | undefined;
  onSave: (value: string | null) => void | Promise<void>;
  isSaving?: boolean;
  type?: 'text' | 'date' | 'month';
  placeholder?: string;
  testId?: string;
  onClick?: () => void;
};

export function EditableCell({
  value,
  onSave,
  isSaving = false,
  type = 'text',
  placeholder = '',
  testId,
  onClick,
}: EditableCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value ?? '');
  const [error, setError] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    try {
      setError(null);
      const newValue = editValue.trim() === '' ? null : editValue.trim();
      await onSave(newValue);
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error saving');
    }
  }, [editValue, onSave]);

  const handleCancel = useCallback(() => {
    setEditValue(value ?? '');
    setIsEditing(false);
    setError(null);
  }, [value]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  }, [handleSave, handleCancel]);

  if (isEditing) {
    return (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <TextField
          size="small"
          type={type}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isSaving}
          autoFocus
          data-testid={testId ? `${testId}-input` : undefined}
          sx={{ flex: 1, minWidth: 120 }}
          error={Boolean(error)}
          helperText={error}
        />
        <IconButton
          size="small"
          onClick={handleSave}
          disabled={isSaving}
          data-testid={testId ? `${testId}-save` : undefined}
        >
          {isSaving ? <CircularProgress size={20} /> : <CheckIcon fontSize="small" />}
        </IconButton>
        <IconButton
          size="small"
          onClick={handleCancel}
          disabled={isSaving}
          data-testid={testId ? `${testId}-cancel` : undefined}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Stack>
    );
  }

  const displayValue = value ?? '--';

  return (
    <Box
      onClick={() => {
        setEditValue(value ?? '');
        setIsEditing(true);
        onClick?.();
      }}
      sx={{
        p: 1,
        borderRadius: 1,
        cursor: 'pointer',
        '&:hover': { bgcolor: 'action.hover' },
        minHeight: 40,
        display: 'flex',
        alignItems: 'center',
      }}
      data-testid={testId}
    >
      <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
        {displayValue}
      </Typography>
    </Box>
  );
}

type ToggleCellProps = {
  value: boolean | null | undefined;
  onSave: (value: boolean) => void | Promise<void>;
  isSaving?: boolean;
  testId?: string;
};

export function ToggleCell({ value, onSave, isSaving = false, testId }: ToggleCellProps) {
  const [error, setError] = useState<string | null>(null);

  const handleToggle = useCallback(async () => {
    try {
      setError(null);
      const newValue = !value;
      await onSave(newValue);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error saving');
    }
  }, [value, onSave]);

  const displayValue = value ? 'Billed' : 'Not billed';

  return (
    <Box>
      <Box
        onClick={handleToggle}
        sx={{
          p: 1,
          borderRadius: 1,
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' },
          minHeight: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        data-testid={testId}
      >
        {isSaving ? (
          <CircularProgress size={20} />
        ) : (
          <Typography
            variant="body2"
            sx={{
              fontWeight: value ? 600 : 400,
              color: value ? 'success.main' : 'text.secondary',
            }}
          >
            {displayValue}
          </Typography>
        )}
      </Box>
      {error && (
        <Typography variant="caption" color="error" data-testid={testId ? `${testId}-error` : undefined}>
          {error}
        </Typography>
      )}
    </Box>
  );
}
