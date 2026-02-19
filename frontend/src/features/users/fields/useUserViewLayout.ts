import { useCallback, useEffect, useMemo, useState } from 'react';
import { getDefaultOrderedFieldIds, getDefaultVisibleFieldIds, USER_FIELD_MAP } from './UserFieldRegistry';
import type { UserFieldView } from './UserFieldRegistry';

const STORAGE_PREFIX = 'master-users.layout';
const LAYOUT_VERSION = 1;
const VERSION_KEY = `${STORAGE_PREFIX}.version`;

const readStoredArray = (key: string) => {
  if (typeof window === 'undefined') return undefined;
  const raw = window.localStorage.getItem(key);
  if (!raw) return undefined;
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
};

const readStoredVersion = () => {
  if (typeof window === 'undefined') return LAYOUT_VERSION;
  const raw = window.localStorage.getItem(VERSION_KEY);
  const parsed = raw ? Number(raw) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : 0;
};

const sanitizeIds = (ids: string[] | undefined) => (ids ?? []).filter((id) => USER_FIELD_MAP.has(id));

const mergeOrderedIds = (stored: string[] | undefined, defaults: string[]) => {
  const base = sanitizeIds(stored);
  const missing = defaults.filter((id) => !base.includes(id));
  return base.length ? [...base, ...missing] : defaults;
};

const mergeVisibleIds = (stored: string[] | undefined, defaults: string[]) => {
  const base = sanitizeIds(stored);
  if (!base.length) return defaults;
  const missing = defaults.filter((id) => !base.includes(id));
  return [...base, ...missing];
};

export const useUserViewLayout = (view: UserFieldView) => {
  const defaultVisible = useMemo(() => getDefaultVisibleFieldIds(view), [view]);
  const defaultOrder = useMemo(() => getDefaultOrderedFieldIds(), []);

  const visibleKey = `${STORAGE_PREFIX}.${view}.visibleFieldIds`;
  const orderKey = `${STORAGE_PREFIX}.${view}.order`;
  const pinnedKey = `${STORAGE_PREFIX}.${view}.pinnedFieldIds`;
  const storedVersion = readStoredVersion();
  const shouldMergeDefaults = storedVersion !== LAYOUT_VERSION;

  const [visibleFieldIds, setVisibleFieldIds] = useState<string[]>(() => {
    const stored = readStoredArray(visibleKey);
    if (shouldMergeDefaults) {
      return mergeVisibleIds(stored, defaultVisible);
    }
    const sanitized = sanitizeIds(stored);
    return sanitized.length ? sanitized : defaultVisible;
  });
  const [orderedFieldIds, setOrderedFieldIds] = useState<string[]>(() => {
    const stored = readStoredArray(orderKey);
    if (shouldMergeDefaults) {
      return mergeOrderedIds(stored, defaultOrder);
    }
    const sanitized = sanitizeIds(stored);
    return sanitized.length ? sanitized : defaultOrder;
  });
  const [pinnedFieldIds, setPinnedFieldIds] = useState<string[]>(() => {
    const stored = sanitizeIds(readStoredArray(pinnedKey));
    return view === 'list' ? stored : [];
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(visibleKey, JSON.stringify(visibleFieldIds));
  }, [visibleFieldIds, visibleKey]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(orderKey, JSON.stringify(orderedFieldIds));
  }, [orderedFieldIds, orderKey]);

  useEffect(() => {
    if (typeof window === 'undefined' || view !== 'list') return;
    window.localStorage.setItem(pinnedKey, JSON.stringify(pinnedFieldIds));
  }, [pinnedFieldIds, pinnedKey, view]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(VERSION_KEY, String(LAYOUT_VERSION));
  }, []);

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
      if (index < 0) return prev;
      const nextIndex = direction === 'up' ? index - 1 : index + 1;
      if (nextIndex < 0 || nextIndex >= prev.length) return prev;
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
    if (view !== 'list') return;
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
