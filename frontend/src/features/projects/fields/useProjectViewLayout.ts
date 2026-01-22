import { useCallback, useEffect, useMemo, useState } from 'react';
import { getDefaultOrderedFieldIds, getDefaultVisibleFieldIds, PROJECT_FIELD_MAP } from './ProjectFieldRegistry';
import type { ProjectFieldView } from './ProjectFieldRegistry';

const STORAGE_PREFIX = 'projects.v2.layout';

const readStoredArray = (key: string) => {
  if (typeof window === 'undefined') {
    return undefined;
  }
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return undefined;
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
};

const sanitizeIds = (ids: string[] | undefined) =>
  (ids ?? []).filter((id) => PROJECT_FIELD_MAP.has(id));

export const useProjectViewLayout = (view: ProjectFieldView) => {
  const defaultVisible = useMemo(() => getDefaultVisibleFieldIds(view), [view]);
  const defaultOrder = useMemo(() => getDefaultOrderedFieldIds(), []);

  const visibleKey = `${STORAGE_PREFIX}.${view}.visibleFieldIds`;
  const orderKey = `${STORAGE_PREFIX}.${view}.order`;
  const pinnedKey = `${STORAGE_PREFIX}.${view}.pinnedFieldIds`;

  const [visibleFieldIds, setVisibleFieldIds] = useState<string[]>(() => {
    const stored = sanitizeIds(readStoredArray(visibleKey));
    return stored.length ? stored : defaultVisible;
  });
  const [orderedFieldIds, setOrderedFieldIds] = useState<string[]>(() => {
    const stored = sanitizeIds(readStoredArray(orderKey));
    return stored.length ? stored : defaultOrder;
  });
  const [pinnedFieldIds, setPinnedFieldIds] = useState<string[]>(() => {
    const stored = sanitizeIds(readStoredArray(pinnedKey));
    return view === 'list' ? stored : [];
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(visibleKey, JSON.stringify(visibleFieldIds));
  }, [visibleFieldIds, visibleKey]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(orderKey, JSON.stringify(orderedFieldIds));
  }, [orderedFieldIds, orderKey]);

  useEffect(() => {
    if (typeof window === 'undefined' || view !== 'list') {
      return;
    }
    window.localStorage.setItem(pinnedKey, JSON.stringify(pinnedFieldIds));
  }, [pinnedFieldIds, pinnedKey, view]);

  const orderedVisibleFieldIds = useMemo(
    () => orderedFieldIds.filter((id) => visibleFieldIds.includes(id)),
    [orderedFieldIds, visibleFieldIds],
  );

  const toggleField = useCallback((fieldId: string) => {
    setVisibleFieldIds((prev) =>
      prev.includes(fieldId) ? prev.filter((id) => id !== fieldId) : [...prev, fieldId],
    );
  }, []);

  const moveField = useCallback((fieldId: string, direction: 'up' | 'down') => {
    setOrderedFieldIds((prev) => {
      const index = prev.indexOf(fieldId);
      if (index < 0) {
        return prev;
      }
      const nextIndex = direction === 'up' ? index - 1 : index + 1;
      if (nextIndex < 0 || nextIndex >= prev.length) {
        return prev;
      }
      const next = [...prev];
      const [removed] = next.splice(index, 1);
      next.splice(nextIndex, 0, removed);
      return next;
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    setVisibleFieldIds(defaultVisible);
    setOrderedFieldIds(defaultOrder);
    setPinnedFieldIds([]);
  }, [defaultOrder, defaultVisible]);

  const togglePinnedField = useCallback((fieldId: string) => {
    if (view !== 'list') {
      return;
    }
    setPinnedFieldIds((prev) =>
      prev.includes(fieldId) ? prev.filter((id) => id !== fieldId) : [...prev, fieldId],
    );
  }, [view]);

  return {
    visibleFieldIds,
    orderedFieldIds,
    orderedVisibleFieldIds,
    pinnedFieldIds,
    setVisibleFieldIds,
    toggleField,
    moveField,
    togglePinnedField,
    resetToDefaults,
  };
};
