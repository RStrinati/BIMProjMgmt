import { useMemo } from 'react';
import type { DashboardTimelineProject } from '@/types/api';

export type TimelineZoom = 'week' | 'month' | 'quarter';
export type TimelinePreset = 'all' | 'active' | 'overdue';

export type TimelineRowModel = {
  id: number;
  label: string;
  status?: string;
  start?: string;
  end?: string;
  colorToken: string;
  meta?: string[];
  bar: { xStart: number; xEnd: number };
  hasDates: boolean;
};

export type TimelineModel = {
  rows: TimelineRowModel[];
  range: {
    minDate: Date;
    maxDate: Date;
    zoom: TimelineZoom;
  };
  ticks: { date: Date; x: number; label?: string }[];
  todayX?: number;
  rangeWidth: number;
};

type TimelineFilters = {
  projectIds?: number[];
  manager?: string;
  type?: string;
  client?: string;
  searchText?: string;
  preset?: TimelinePreset;
  zoom: TimelineZoom;
};

const ZOOM_PIXELS_PER_DAY: Record<TimelineZoom, number> = {
  week: 24,
  month: 8,
  quarter: 4,
};

const normalizeText = (value?: string | null) => (value ?? '').trim().toLowerCase();

const parseDate = (value?: string | null) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const toStartOfDay = (value: Date) => new Date(value.getFullYear(), value.getMonth(), value.getDate());

const addDays = (value: Date, days: number) => {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
};

const diffDays = (start: Date, end: Date) => {
  const startMs = toStartOfDay(start).getTime();
  const endMs = toStartOfDay(end).getTime();
  return Math.max(0, Math.round((endMs - startMs) / (1000 * 60 * 60 * 24)));
};

const startOfWeek = (value: Date) => {
  const date = new Date(value);
  const day = date.getDay();
  const diff = (day + 6) % 7;
  date.setDate(date.getDate() - diff);
  return toStartOfDay(date);
};

const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);

const startOfQuarter = (value: Date) => {
  const quarter = Math.floor(value.getMonth() / 3) * 3;
  return new Date(value.getFullYear(), quarter, 1);
};

const formatTick = (date: Date, zoom: TimelineZoom) => {
  if (zoom === 'week') {
    return date.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' });
  }
  if (zoom === 'month') {
    return date.toLocaleDateString('en-AU', { month: 'short' });
  }
  return date.toLocaleDateString('en-AU', { month: 'short' });
};

const getColorToken = (project: DashboardTimelineProject) => {
  const value = normalizeText(project.project_type);
  if (value.includes('health')) return 'info';
  if (value.includes('data')) return 'primary';
  if (value.includes('coord')) return 'warning';
  return 'neutral';
};

const filterByPreset = (project: DashboardTimelineProject, preset: TimelinePreset) => {
  if (preset === 'all') return true;
  const end = parseDate(project.end_date);
  if (!end) {
    return preset === 'active';
  }
  const today = toStartOfDay(new Date());
  if (preset === 'active') {
    return end >= today;
  }
  return end < today;
};

const filterBySearch = (project: DashboardTimelineProject, searchText?: string) => {
  const query = normalizeText(searchText);
  if (!query) return true;
  const fields = [
    project.project_name,
    project.client_name,
    project.project_manager,
    project.project_type,
  ];
  return fields.some((field) => normalizeText(field).includes(query));
};

export const useTimelineModel = ({
  projects,
  projectIds,
  manager,
  type,
  client,
  searchText,
  preset = 'all',
  zoom,
}: {
  projects: DashboardTimelineProject[];
  zoom: TimelineZoom;
  preset?: TimelinePreset;
  searchText?: string;
  projectIds?: number[];
  manager?: string;
  type?: string;
  client?: string;
}): TimelineModel => {
  return useMemo(() => {
    const normalizedManager = normalizeText(manager);
    const normalizedType = normalizeText(type);
    const normalizedClient = normalizeText(client);

    const filtered = projects.filter((project) => {
      if (projectIds?.length && !projectIds.includes(project.project_id)) {
        return false;
      }
      if (normalizedManager && normalizeText(project.project_manager) !== normalizedManager) {
        return false;
      }
      if (normalizedType && normalizeText(project.project_type) !== normalizedType) {
        return false;
      }
      if (normalizedClient && normalizeText(project.client_name) !== normalizedClient) {
        return false;
      }
      if (!filterByPreset(project, preset)) {
        return false;
      }
      if (!filterBySearch(project, searchText)) {
        return false;
      }
      return true;
    });

    const dateCandidates: Date[] = [];
    filtered.forEach((project) => {
      const start = parseDate(project.start_date);
      const end = parseDate(project.end_date);
      if (start) dateCandidates.push(start);
      if (end) dateCandidates.push(end);
    });

    const today = toStartOfDay(new Date());
    const minDate = dateCandidates.length ? new Date(Math.min(...dateCandidates.map((d) => d.getTime()))) : addDays(today, -30);
    const maxDate = dateCandidates.length ? new Date(Math.max(...dateCandidates.map((d) => d.getTime()))) : addDays(today, 90);

    const paddedMin = addDays(minDate, -7);
    const paddedMax = addDays(maxDate, 7);

    const startAnchor = zoom === 'week' ? startOfWeek(paddedMin) : zoom === 'month' ? startOfMonth(paddedMin) : startOfQuarter(paddedMin);
    const endAnchor = paddedMax;

    const totalDays = Math.max(1, diffDays(startAnchor, endAnchor) + 1);
    const pixelsPerDay = ZOOM_PIXELS_PER_DAY[zoom];
    const rangeWidth = totalDays * pixelsPerDay;

    const ticks: { date: Date; x: number; label?: string }[] = [];
    let cursor = new Date(startAnchor);
    while (cursor <= endAnchor) {
      const offsetDays = diffDays(startAnchor, cursor);
      ticks.push({
        date: new Date(cursor),
        x: offsetDays * pixelsPerDay,
        label: formatTick(cursor, zoom),
      });
      if (zoom === 'week') {
        cursor = addDays(cursor, 7);
      } else if (zoom === 'month') {
        cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
      } else {
        cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
      }
      if (ticks.length > 240) {
        break;
      }
    }

    const todayOffset = today >= startAnchor && today <= endAnchor ? diffDays(startAnchor, today) * pixelsPerDay : undefined;

    const rows = filtered.map((project) => {
      const start = parseDate(project.start_date);
      const end = parseDate(project.end_date);
      const hasDates = Boolean(start && end);
      const safeStart = start ?? startAnchor;
      const safeEnd = end ?? safeStart;
      const xStart = diffDays(startAnchor, safeStart) * pixelsPerDay;
      const xEnd = diffDays(startAnchor, safeEnd) * pixelsPerDay;
      const meta = [project.client_name, project.project_manager].filter(Boolean) as string[];
      return {
        id: project.project_id,
        label: project.project_name,
        start: project.start_date ?? undefined,
        end: project.end_date ?? undefined,
        colorToken: getColorToken(project),
        meta,
        bar: {
          xStart,
          xEnd: Math.max(xEnd, xStart + 6),
        },
        hasDates,
      };
    });

    return {
      rows,
      range: {
        minDate: startAnchor,
        maxDate: endAnchor,
        zoom,
      },
      ticks,
      todayX: todayOffset,
      rangeWidth,
    };
  }, [projects, projectIds, manager, type, client, searchText, preset, zoom]);
};
