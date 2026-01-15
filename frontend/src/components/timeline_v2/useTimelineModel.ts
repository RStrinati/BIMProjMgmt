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
  priorityLabel?: string | null;
  priorityValue?: string | number | null;
  leadLabel?: string | null;
  leadInitials?: string | null;
  progressLabel?: string | null;
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
  ticks: { date: Date; x: number; label?: string; subLabel?: string; isMajor?: boolean }[];
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

const REVERSE_PRIORITY_MAP: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' };

const resolvePriorityLabel = (
  priority: DashboardTimelineProject['priority'],
  fallbackLabel?: string | null,
): string | null => {
  if (fallbackLabel && fallbackLabel.trim() !== '') {
    return fallbackLabel;
  }
  if (typeof priority === 'number') {
    return REVERSE_PRIORITY_MAP[priority] || 'Medium';
  }
  if (typeof priority === 'string' && priority.trim() !== '') {
    const trimmed = priority.trim();
    if (/^\d+$/.test(trimmed)) {
      const numericPriority = parseInt(trimmed, 10);
      return REVERSE_PRIORITY_MAP[numericPriority] || 'Medium';
    }
    return trimmed;
  }
  return fallbackLabel ?? null;
};

const resolveLeadLabel = (project: DashboardTimelineProject) => {
  if (project.internal_lead_name && project.internal_lead_name.trim()) {
    return project.internal_lead_name.trim();
  }
  if (project.lead_name && project.lead_name.trim()) {
    return project.lead_name.trim();
  }
  if (project.internal_lead != null) {
    return `User ${project.internal_lead}`;
  }
  return null;
};

const getInitials = (value: string) => {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
};

const resolveProgressLabel = (project: DashboardTimelineProject) => {
  const progressRaw = project.progress_pct;
  const billedRaw = project.service_billed_pct;
  if (progressRaw != null && Number.isFinite(Number(progressRaw))) {
    return `${Math.round(Number(progressRaw))}%`;
  }
  if (billedRaw != null && Number.isFinite(Number(billedRaw))) {
    return `${Math.round(Number(billedRaw))}%`;
  }
  const totalAgreed = Number(project.total_service_agreed_fee ?? project.agreed_fee);
  const totalBilled = Number(project.total_service_billed_amount);
  if (Number.isFinite(totalAgreed) && Number.isFinite(totalBilled) && totalAgreed > 0) {
    return `${Math.round((totalBilled / totalAgreed) * 100)}%`;
  }
  return null;
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

    const ticks: { date: Date; x: number; label?: string; subLabel?: string; isMajor?: boolean }[] = [];
    const tickMap = new Map<number, { date: Date; x: number; label?: string; subLabel?: string; isMajor?: boolean }>();

    const ensureTick = (date: Date) => {
      const timestamp = toStartOfDay(date).getTime();
      const existing = tickMap.get(timestamp);
      if (existing) return existing;
      const offsetDays = diffDays(startAnchor, date);
      const tick = { date: new Date(date), x: offsetDays * pixelsPerDay };
      tickMap.set(timestamp, tick);
      return tick;
    };

    const maxTicks = 240;
    let dayInterval = zoom === 'week' ? 1 : zoom === 'month' ? 2 : 7;
    if (Math.ceil(totalDays / dayInterval) > maxTicks) {
      dayInterval = Math.max(1, Math.ceil(totalDays / maxTicks));
    }

    let dayCursor = new Date(startAnchor);
    while (dayCursor <= endAnchor) {
      const tick = ensureTick(dayCursor);
      tick.subLabel = String(dayCursor.getDate());
      dayCursor = addDays(dayCursor, dayInterval);
      if (tickMap.size > maxTicks * 2) {
        break;
      }
    }

    if (zoom === 'week') {
      let majorCursor = new Date(startAnchor);
      while (majorCursor <= endAnchor) {
        const tick = ensureTick(majorCursor);
        tick.label = formatTick(majorCursor, zoom);
        tick.isMajor = true;
        majorCursor = addDays(majorCursor, 7);
        if (tickMap.size > maxTicks * 2) {
          break;
        }
      }
    } else {
      let majorCursor = startOfMonth(startAnchor);
      while (majorCursor <= endAnchor) {
        const tick = ensureTick(majorCursor);
        tick.label = formatTick(majorCursor, zoom);
        tick.isMajor = true;
        majorCursor = new Date(majorCursor.getFullYear(), majorCursor.getMonth() + 1, 1);
        if (tickMap.size > maxTicks * 2) {
          break;
        }
      }
    }

    tickMap.forEach((tick) => ticks.push(tick));
    ticks.sort((a, b) => a.x - b.x);

    const todayOffset = today >= startAnchor && today <= endAnchor ? diffDays(startAnchor, today) * pixelsPerDay : undefined;

    const rows = filtered.map((project) => {
      const start = parseDate(project.start_date);
      const end = parseDate(project.end_date);
      const hasDates = Boolean(start && end);
      const safeStart = start ?? startAnchor;
      const safeEnd = end ?? safeStart;
      const xStart = diffDays(startAnchor, safeStart) * pixelsPerDay;
      const xEnd = diffDays(startAnchor, safeEnd) * pixelsPerDay;
      const priorityLabel = resolvePriorityLabel(project.priority, project.priority_label);
      const leadLabel = resolveLeadLabel(project);
      const progressLabel = resolveProgressLabel(project);
      return {
        id: project.project_id,
        label: project.project_name,
        start: project.start_date ?? undefined,
        end: project.end_date ?? undefined,
        colorToken: getColorToken(project),
        priorityLabel,
        priorityValue: project.priority ?? null,
        leadLabel,
        leadInitials: leadLabel ? getInitials(leadLabel) : null,
        progressLabel,
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
