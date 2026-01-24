/**
 * Workspace Selection Hook
 * 
 * Manages selection state synchronized with URL query params.
 * Format: ?sel=type:id (e.g., ?sel=service:123)
 * 
 * Features:
 * - URL sync (parse on mount, update on change)
 * - Esc key clears selection
 * - Tab navigation clears incompatible selections
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export type SelectionType = 'service' | 'review' | 'item' | 'issue' | 'task' | 'update' | 'model' | 'service_template';

export type Selection = {
  type: SelectionType;
  id: number | string;  // Support both numeric and string IDs (for issue_key)
};

const parseSelection = (sel: string | null): Selection | null => {
  if (!sel) return null;
  
  // Match pattern: type:identifier (identifier can be numeric or alphanumeric string)
  const match = sel.match(/^(\w+):(.+)$/);
  if (!match) return null;
  
  const [, type, idStr] = match;
  
  const validTypes: SelectionType[] = ['service', 'review', 'item', 'issue', 'task', 'update', 'model', 'service_template'];
  if (!validTypes.includes(type as SelectionType)) return null;
  
  // For issues, keep as string (issue_key); for others, parse as number
  let id: number | string;
  if (type === 'issue' || type === 'service_template') {
    id = idStr;  // Keep issue_key as string
  } else {
    id = parseInt(idStr, 10);
    if (!Number.isFinite(id) || id <= 0) return null;
  }
  
  return { type: type as SelectionType, id };
};

const serializeSelection = (selection: Selection | null): string | null => {
  if (!selection) return null;
  return `${selection.type}:${String(selection.id)}`;
};

export function useWorkspaceSelection() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selection, setSelectionState] = useState<Selection | null>(() => {
    return parseSelection(searchParams.get('sel'));
  });

  // Sync state with URL on mount and when URL changes externally
  useEffect(() => {
    const urlSelection = parseSelection(searchParams.get('sel'));
    const currentSerialized = serializeSelection(selection);
    const urlSerialized = serializeSelection(urlSelection);
    
    if (currentSerialized !== urlSerialized) {
      setSelectionState(urlSelection);
    }
  }, [searchParams, selection]);

  // Clear selection on Esc key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && selection) {
        clearSelection();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selection]);

  const setSelection = useCallback((newSelection: Selection | null) => {
    setSelectionState(newSelection);

    // Update URL search explicitly to avoid encoding the colon in sel value
    const serialized = serializeSelection(newSelection);
    const search = serialized ? `?sel=${serialized}` : '';
    navigate({ search }, { replace: true });
  }, [navigate]);

  const clearSelection = useCallback(() => {
    setSelection(null);
  }, [setSelection]);

  return {
    selection,
    setSelection,
    clearSelection,
  };
}
