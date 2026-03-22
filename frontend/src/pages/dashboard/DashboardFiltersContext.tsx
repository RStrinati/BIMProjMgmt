import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

export type DashboardFiltersState = {
  projectIds: number[];
  manager: string;
  client: string;
  projectType: string;
  discipline: string;
  location: string;
};

type SavedView = {
  name: string;
  filters: DashboardFiltersState;
};

type DashboardFiltersContextValue = {
  filters: DashboardFiltersState;
  setFilters: (next: DashboardFiltersState) => void;
  updateFilters: (partial: Partial<DashboardFiltersState>) => void;
  savedViews: SavedView[];
  saveView: (name: string) => void;
  applySavedView: (name: string) => void;
  deleteSavedView: (name: string) => void;
};

const DEFAULT_FILTERS: DashboardFiltersState = {
  projectIds: [],
  manager: 'all',
  client: 'all',
  projectType: 'all',
  discipline: 'all',
  location: '',
};

const DashboardFiltersContext = createContext<DashboardFiltersContextValue | undefined>(undefined);

const STORAGE_KEY = 'dashboard_saved_views_v2';

export function DashboardFiltersProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<DashboardFiltersState>(DEFAULT_FILTERS);
  const [savedViews, setSavedViews] = useState<SavedView[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? (JSON.parse(stored) as SavedView[]) : [];
    } catch {
      return [];
    }
  });

  const updateFilters = (partial: Partial<DashboardFiltersState>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  };

  const saveView = (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setSavedViews((prev) => {
      const next = prev.filter((view) => view.name !== trimmed);
      return [...next, { name: trimmed, filters }];
    });
  };

  const applySavedView = (name: string) => {
    const match = savedViews.find((view) => view.name === name);
    if (match) {
      setFilters(match.filters);
    }
  };

  const deleteSavedView = (name: string) => {
    setSavedViews((prev) => prev.filter((view) => view.name !== name));
  };

  const value = useMemo(
    () => ({
      filters,
      setFilters,
      updateFilters,
      savedViews,
      saveView,
      applySavedView,
      deleteSavedView,
    }),
    [filters, savedViews],
  );

  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(savedViews));
    } catch {
      // ignore storage errors
    }
  }

  return <DashboardFiltersContext.Provider value={value}>{children}</DashboardFiltersContext.Provider>;
}

export function useDashboardFilters() {
  const ctx = useContext(DashboardFiltersContext);
  if (!ctx) {
    throw new Error('useDashboardFilters must be used within DashboardFiltersProvider');
  }
  return ctx;
}
