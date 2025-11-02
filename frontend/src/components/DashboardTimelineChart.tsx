import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import {
  addDays,
  differenceInCalendarDays,
  format,
  isValid,
  parseISO,
  startOfDay,
  isAfter,
  isBefore,
} from 'date-fns';
import type {
  DashboardTimelineProject,
  DashboardTimelineReviewItem,
} from '@/types/api';

const BASE_DAY_WIDTH_PX = 18;
const MIN_TRACK_WIDTH_PX = 320;
const MIN_BAR_WIDTH_PX = 12;
const TICK_GAP_TARGET_PX = 140;
const MAX_TICKS = 12;
const MIN_TICKS = 2;
const LEFT_COLUMN_WIDTH_PX = 260;
const BAR_HEIGHT_PX = 10;
const MARKER_SIZE_PX = 14;
const ROW_HEIGHT_PX = 76;
const VIRTUALIZATION_THRESHOLD = 40;
const VIRTUALIZATION_OVERSCAN = 6;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

interface DashboardTimelineChartProps {
  projects?: DashboardTimelineProject[];
  isLoading: boolean;
  hasActiveFilters?: boolean;
}

const STATUS_COLOR_MAP: Record<string, string> = {
  completed: 'success.main',
  in_progress: 'warning.main',
  planned: 'info.main',
  overdue: 'error.main',
  cancelled: 'text.disabled',
};

const STATUS_LABEL_MAP: Record<string, string> = {
  completed: 'Completed',
  in_progress: 'In Progress',
  planned: 'Planned',
  overdue: 'Overdue',
  cancelled: 'Cancelled',
};

const parseDate = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const parsed = parseISO(value);
  return isValid(parsed) ? startOfDay(parsed) : null;
};

type ParsedReview = {
  reviewId: number;
  plannedDate: Date | null;
  dueDate: Date | null;
  status: string | null | undefined;
  serviceName: string | null | undefined;
};

type ParsedProject = {
  projectId: number;
  name: string;
  startDate: Date | null;
  endDate: Date | null;
  reviews: ParsedReview[];
  projectManager?: string | null;
  clientName?: string | null;
  projectType?: string | null;
  clientId?: number | null;
  typeId?: number | null;
  rawStart?: string | null;
  rawEnd?: string | null;
};

type TimelineContext = {
  projects: ParsedProject[];
  minDate: Date | null;
  maxDate: Date | null;
  totalDays: number;
  ticks: Date[];
  trackWidth: number;
  pixelsPerDay: number;
};

type ProjectCacheEntry = {
  source: DashboardTimelineProject;
  parsed: ParsedProject;
};

type ReviewCacheEntry = {
  source: DashboardTimelineReviewItem;
  parsed: ParsedReview;
};

type ReviewMarker = {
  reviewId: number;
  left: number;
  colorKey: string;
  serviceName: string | null | undefined;
  plannedLabel: string | null;
  dueLabel: string | null;
  status: string | null | undefined;
  statusLabel: string;
  key: string;
};

type ProjectLayout = {
  project: ParsedProject;
  bar: { left: number; width: number };
  rangeLabel: string;
  metaCompact: string;
  reviewMarkers: ReviewMarker[];
};

const useTimelineContext = (projects?: DashboardTimelineProject[]) => {
  const projectCacheRef = useRef<Map<number, ProjectCacheEntry>>(new Map());
  const reviewCacheRef = useRef<Map<number, ReviewCacheEntry>>(new Map());

  return useMemo<TimelineContext | null>(() => {
    if (!projects || projects.length === 0) {
      return null;
    }

    let minTimestamp: number | null = null;
    let maxTimestamp: number | null = null;
    const updateBounds = (date: Date | null) => {
      if (!date) {
        return;
      }
      const value = date.getTime();
      if (minTimestamp === null || value < minTimestamp) {
        minTimestamp = value;
      }
      if (maxTimestamp === null || value > maxTimestamp) {
        maxTimestamp = value;
      }
    };

    const parsedProjects: ParsedProject[] = projects.map((project) => {
      const cachedProject = projectCacheRef.current.get(project.project_id);
      if (cachedProject && cachedProject.source === project) {
        return cachedProject.parsed;
      }

      const parsedReviews: ParsedReview[] = (project.review_items ?? []).map((review) => {
        const cachedReview = reviewCacheRef.current.get(review.review_id);
        if (cachedReview && cachedReview.source === review) {
          return cachedReview.parsed;
        }

        const parsed: ParsedReview = {
          reviewId: review.review_id,
          plannedDate: parseDate(review.planned_date),
          dueDate: parseDate(review.due_date),
          status: review.status,
          serviceName: review.service_name,
        };
        updateBounds(parsed.plannedDate);
        updateBounds(parsed.dueDate);
        reviewCacheRef.current.set(review.review_id, { source: review, parsed });
        return parsed;
      });

      const parsedProject: ParsedProject = {
        projectId: project.project_id,
        name: project.project_name,
        startDate: parseDate(project.start_date),
        endDate: parseDate(project.end_date),
        reviews: parsedReviews,
        projectManager: project.project_manager ?? null,
        clientName: project.client_name ?? null,
        projectType: project.project_type ?? null,
        clientId: project.client_id ?? null,
        typeId: project.type_id ?? null,
        rawStart: project.start_date ?? null,
        rawEnd: project.end_date ?? null,
      };

      updateBounds(parsedProject.startDate);
      updateBounds(parsedProject.endDate);

      projectCacheRef.current.set(project.project_id, {
        source: project,
        parsed: parsedProject,
      });

      return parsedProject;
    });

    if (minTimestamp === null || maxTimestamp === null) {
      return {
        projects: parsedProjects,
        minDate: null,
        maxDate: null,
        totalDays: 0,
        ticks: [],
        trackWidth: MIN_TRACK_WIDTH_PX,
        pixelsPerDay: BASE_DAY_WIDTH_PX,
      };
    }

    const minDate = new Date(minTimestamp);
    const maxDate = new Date(maxTimestamp);
    const rawSpan = Math.max(0, Math.round((maxTimestamp - minTimestamp) / MS_PER_DAY));
    const totalDays = Math.max(1, rawSpan + 1);

    const baseTrackWidth = totalDays * BASE_DAY_WIDTH_PX;
    const trackWidth = Math.max(baseTrackWidth, MIN_TRACK_WIDTH_PX);
    const pixelsPerDay = trackWidth / totalDays;

    const approxTickCount = Math.max(
      MIN_TICKS,
      Math.min(MAX_TICKS, Math.round(trackWidth / TICK_GAP_TARGET_PX)),
    );
    const interval = Math.max(1, Math.round(rawSpan / Math.max(1, approxTickCount - 1)));

    const ticks: Date[] = [];
    if (rawSpan === 0) {
      ticks.push(minDate);
    } else {
      for (let offset = 0; offset <= rawSpan; offset += interval) {
        ticks.push(addDays(minDate, offset));
      }
      if (ticks[ticks.length - 1].getTime() !== maxDate.getTime()) {
        ticks.push(maxDate);
      }
    }

    return {
      projects: parsedProjects,
      minDate,
      maxDate,
      totalDays,
      ticks,
      trackWidth,
      pixelsPerDay,
    };
  }, [projects]);
};

const getStatusColor = (status: string | null | undefined, fallback: string) => {
  if (!status) {
    return fallback;
  }
  const normalised = status.toLowerCase();
  return STATUS_COLOR_MAP[normalised] ?? fallback;
};

const formatDisplayDate = (date?: Date | null) => {
  if (!date) {
    return null;
  }
  return format(date, 'd MMM yyyy');
};

const formatRangeLabel = (start?: Date | null, end?: Date | null) => {
  if (!start && !end) {
    return 'No dates';
  }
  if (start && end) {
    const startLabel = formatDisplayDate(start);
    const endLabel = formatDisplayDate(end);
    return startLabel && endLabel ? `${startLabel} \u2013 ${endLabel}` : 'No dates';
  }
  const target = start ?? end;
  const label = formatDisplayDate(target);
  return label ?? 'No dates';
};

function DashboardTimelineChart({
  projects,
  isLoading,
  hasActiveFilters = false,
}: DashboardTimelineChartProps) {
  const theme = useTheme();
  const mdUp = useMediaQuery(theme.breakpoints.up('md'));
  const timeline = useTimelineContext(projects);
  const timelineData = timeline ?? null;
  const parsedProjects = timelineData?.projects ?? [];
  const ticks = timelineData?.ticks ?? [];
  const minDate = timelineData?.minDate ?? null;
  const maxDate = timelineData?.maxDate ?? null;
  const totalDays = timelineData?.totalDays ?? 0;
  const trackWidth = timelineData?.trackWidth ?? MIN_TRACK_WIDTH_PX;
  const pixelsPerDay = timelineData?.pixelsPerDay ?? BASE_DAY_WIDTH_PX;

  const today = startOfDay(new Date());
  const startBoundary = minDate ? startOfDay(minDate) : null;
  const endBoundary = maxDate ? startOfDay(maxDate) : null;
  const startBoundaryTime = startBoundary?.getTime() ?? null;
  const isTimelineEmpty = !timelineData || parsedProjects.length === 0;
  const isTodayInRange =
    !!startBoundary && !!endBoundary && !isBefore(today, startBoundary) && !isAfter(today, endBoundary);
  const trackBackgroundColor =
    theme.palette.mode === 'light'
      ? alpha(theme.palette.grey[100], 0.9)
      : alpha(theme.palette.grey[900], 0.6);
  const axisBackgroundColor =
    theme.palette.mode === 'light'
      ? alpha(theme.palette.background.paper, 0.8)
      : alpha(theme.palette.background.default, 0.6);
  const weekendFill =
    theme.palette.mode === 'light'
      ? alpha(theme.palette.grey[400], 0.25)
      : alpha(theme.palette.grey[700], 0.35);

  const roundedTrackWidth = Math.round(trackWidth);
  const timelineContainerWidth = mdUp
    ? LEFT_COLUMN_WIDTH_PX + roundedTrackWidth
    : Math.max(roundedTrackWidth, MIN_TRACK_WIDTH_PX);
  const getTimelineOffset = useMemo(() => {
    if (startBoundaryTime === null) {
      return () => 0;
    }
    const base = startBoundaryTime;
    const cache = new Map<number, number>();
    return (date: Date) => {
      const timestamp = startOfDay(date).getTime();
      const cached = cache.get(timestamp);
      if (cached !== undefined) {
        return cached;
      }
      const offset = ((timestamp - base) / MS_PER_DAY) * pixelsPerDay;
      cache.set(timestamp, offset);
      return offset;
    };
  }, [startBoundaryTime, pixelsPerDay]);
  const todayMarkerLeft = Math.max(
    0,
    Math.min(getTimelineOffset(today), roundedTrackWidth),
  );

  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const listContainerRef = useRef<HTMLDivElement | null>(null);
  const hasAutoScrolledRef = useRef(false);
  const virtualizationEnabled = parsedProjects.length > VIRTUALIZATION_THRESHOLD;
  const [virtualScrollTop, setVirtualScrollTop] = useState(0);
  const [virtualViewportHeight, setVirtualViewportHeight] = useState(0);

  useEffect(() => {
    hasAutoScrolledRef.current = false;
  }, [timelineData, mdUp]);

  useEffect(() => {
    if (!virtualizationEnabled) {
      setVirtualScrollTop(0);
      setVirtualViewportHeight(0);
      return;
    }

    const container = listContainerRef.current;
    if (!container) {
      return;
    }

    let rafId = 0;
    const updateScroll = () => {
      rafId = 0;
      setVirtualScrollTop(container.scrollTop);
    };

    const handleScroll = () => {
      if (rafId) {
        return;
      }
      rafId = requestAnimationFrame(updateScroll);
    };

    const updateViewport = () => {
      setVirtualViewportHeight(container.clientHeight);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    updateScroll();
    updateViewport();

    const resizeObserver = new ResizeObserver(() => {
      updateViewport();
    });
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
      resizeObserver.disconnect();
    };
  }, [virtualizationEnabled, parsedProjects.length]);

  const renderLegend = () => (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 3 }}>
      {Object.entries(STATUS_COLOR_MAP).map(([status, paletteKey]) => (
        <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              bgcolor: paletteKey,
              border: '1px solid',
              borderColor: 'divider',
            }}
          />
          <Typography variant="caption" color="text.secondary">
            {STATUS_LABEL_MAP[status] ?? status}
          </Typography>
        </Box>
      ))}
    </Box>
  );

  const virtualizationMetrics = useMemo(() => {
    if (!virtualizationEnabled) {
      return {
        startIndex: 0,
        endIndex: parsedProjects.length,
        paddingTop: 0,
        paddingBottom: 0,
      };
    }

    const total = parsedProjects.length;
    if (total === 0) {
      return { startIndex: 0, endIndex: 0, paddingTop: 0, paddingBottom: 0 };
    }

    const fallbackViewport = ROW_HEIGHT_PX * Math.min(total, VIRTUALIZATION_THRESHOLD);
    const effectiveViewport = virtualViewportHeight || fallbackViewport;

    const startIndex = Math.max(
      0,
      Math.floor(virtualScrollTop / ROW_HEIGHT_PX) - VIRTUALIZATION_OVERSCAN,
    );
    const endIndex = Math.min(
      total,
      Math.ceil((virtualScrollTop + effectiveViewport) / ROW_HEIGHT_PX) + VIRTUALIZATION_OVERSCAN,
    );

    return {
      startIndex,
      endIndex,
      paddingTop: startIndex * ROW_HEIGHT_PX,
      paddingBottom: Math.max(0, (total - endIndex) * ROW_HEIGHT_PX),
    };
  }, [
    virtualizationEnabled,
    virtualScrollTop,
    virtualViewportHeight,
    parsedProjects.length,
  ]);

  const projectLayouts = useMemo<ProjectLayout[]>(() => {
    if (!parsedProjects.length) {
      return [];
    }

    const buildMeta = (project: ParsedProject) =>
      [project.projectManager, project.clientName, project.projectType]
        .filter(Boolean)
        .join(' \u2022 ');

    if (startBoundaryTime === null) {
      return parsedProjects.map((project) => {
        const reviewMarkers: ReviewMarker[] = [];
        project.reviews.forEach((review) => {
          const reviewDate = review.plannedDate ?? review.dueDate;
          if (!reviewDate) {
            return;
          }
          const normalizedStatus = review.status?.toLowerCase() ?? 'planned';
          reviewMarkers.push({
            reviewId: review.reviewId,
            left: 0,
            colorKey: getStatusColor(normalizedStatus, 'primary.main'),
            serviceName: review.serviceName,
            plannedLabel: formatDisplayDate(review.plannedDate),
            dueLabel: formatDisplayDate(review.dueDate),
            status: review.status,
            statusLabel: STATUS_LABEL_MAP[normalizedStatus] ?? review.status ?? '',
            key: `${review.reviewId}-${reviewDate.toISOString()}`,
          });
        });

        return {
          project,
          bar: { left: 0, width: 0 },
          rangeLabel: formatRangeLabel(project.startDate, project.endDate),
          metaCompact: buildMeta(project),
          reviewMarkers,
        };
      });
    }

    return parsedProjects.map((project) => {
      const start = project.startDate;
      const end = project.endDate;
      let left = 0;
      let width = 0;

      if (start && end) {
        const startOffset = getTimelineOffset(start);
        const endOffset = getTimelineOffset(end);
        left = Math.max(0, Math.min(Math.min(startOffset, endOffset), roundedTrackWidth));
        const rawInclusiveEnd = Math.max(startOffset, endOffset) + pixelsPerDay;
        const inclusiveEnd = Math.max(left, Math.min(rawInclusiveEnd, roundedTrackWidth));
        width = Math.max(MIN_BAR_WIDTH_PX, inclusiveEnd - left);
        if (left + width > roundedTrackWidth) {
          width = Math.max(MIN_BAR_WIDTH_PX, roundedTrackWidth - left);
        }
      } else {
        const anchor = start ?? end;
        if (anchor) {
          const anchorOffset = getTimelineOffset(anchor);
          const centredLeft = anchorOffset - MIN_BAR_WIDTH_PX / 2;
          const maxLeft = Math.max(0, roundedTrackWidth - MIN_BAR_WIDTH_PX);
          left = Math.max(0, Math.min(centredLeft, maxLeft));
          width = MIN_BAR_WIDTH_PX;
        }
      }

      const reviewMarkers: ReviewMarker[] = [];
      project.reviews.forEach((review) => {
        const reviewDate = review.plannedDate ?? review.dueDate;
        if (!reviewDate) {
          return;
        }
        const normalizedStatus = review.status?.toLowerCase() ?? 'planned';
        const markerBase = getTimelineOffset(reviewDate) + pixelsPerDay / 2;
        const markerLeft = Math.max(0, Math.min(markerBase, roundedTrackWidth));
        reviewMarkers.push({
          reviewId: review.reviewId,
          left: markerLeft,
          colorKey: getStatusColor(normalizedStatus, 'primary.main'),
          serviceName: review.serviceName,
          plannedLabel: formatDisplayDate(review.plannedDate),
          dueLabel: formatDisplayDate(review.dueDate),
          status: review.status,
          statusLabel: STATUS_LABEL_MAP[normalizedStatus] ?? review.status ?? '',
          key: `${review.reviewId}-${reviewDate.toISOString()}`,
        });
      });

      return {
        project,
        bar: { left, width },
        rangeLabel: formatRangeLabel(start, end),
        metaCompact: buildMeta(project),
        reviewMarkers,
      };
    });
  }, [parsedProjects, startBoundaryTime, pixelsPerDay, roundedTrackWidth, getTimelineOffset]);

  const visibleProjectLayouts = useMemo(
    () =>
      projectLayouts.slice(
        virtualizationMetrics.startIndex,
        virtualizationMetrics.endIndex,
      ),
    [projectLayouts, virtualizationMetrics],
  );

  const tickPositions = useMemo(
    () =>
      ticks.map((tick) => {
        const offset = getTimelineOffset(tick);
        const left = Math.max(0, Math.min(offset, roundedTrackWidth));
        return {
          date: tick,
          left,
          iso: tick.toISOString(),
        };
      }),
    [ticks, getTimelineOffset, roundedTrackWidth],
  );

  const daySequence = useMemo(() => {
    if (!startBoundary || totalDays <= 0) {
      return [] as Date[];
    }
    return Array.from({ length: totalDays }, (_, index) =>
      addDays(startBoundary, index),
    );
  }, [startBoundary, totalDays]);

  const isWeekend = (date: Date) => {
    const day = date.getDay();
    return day === 0 || day === 6;
  };

  const weekendSegments = useMemo(() => {
    if (!daySequence.length) {
      return [] as { left: number; width: number }[];
    }

    const segments: { left: number; width: number }[] = [];
    let startIndex = -1;

    daySequence.forEach((day, index) => {
      if (isWeekend(day)) {
        if (startIndex === -1) {
          startIndex = index;
        }
      } else if (startIndex !== -1) {
        const span = index - startIndex;
        if (span > 0) {
          segments.push({
            left: startIndex * pixelsPerDay,
            width: Math.max(span * pixelsPerDay, 1),
          });
        }
        startIndex = -1;
      }
    });

    if (startIndex !== -1) {
      const span = daySequence.length - startIndex;
      segments.push({
        left: startIndex * pixelsPerDay,
        width: Math.max(span * pixelsPerDay, 1),
      });
    }

    return segments;
  }, [daySequence, pixelsPerDay]);

  useEffect(() => {
    if (!timelineData || !startBoundary || !isTodayInRange) {
      return;
    }
    const container = scrollContainerRef.current;
    if (!container || hasAutoScrolledRef.current) {
      return;
    }
    const viewWidth = container.clientWidth;
    if (!viewWidth) {
      return;
    }

    const daysFromStart = differenceInCalendarDays(today, startBoundary);
    const todayLeftWithinTrack = Math.max(
      0,
      Math.min(daysFromStart * pixelsPerDay, trackWidth),
    );
    let target = todayLeftWithinTrack - viewWidth / 2;
    if (mdUp) {
      target += LEFT_COLUMN_WIDTH_PX;
    }
    const maxScroll = Math.max(0, container.scrollWidth - viewWidth);
    target = Math.max(0, Math.min(target, maxScroll));

    requestAnimationFrame(() => {
      container.scrollTo({ left: target, behavior: 'smooth' });
    });
    hasAutoScrolledRef.current = true;
  }, [timelineData, isTodayInRange, mdUp, pixelsPerDay, trackWidth, startBoundary, today]);

  if (isLoading) {
    return (
      <Card sx={{ mt: 4 }}>
        <CardContent sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={32} />
        </CardContent>
      </Card>
    );
  }

  if (isTimelineEmpty) {
    return (
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Project Timelines
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {hasActiveFilters
              ? 'No projects match the selected filters.'
              : 'Timeline data is not available yet. Add project dates or review schedules to populate this view.'}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const axisLeftColumnSx = {
    flex: `0 0 ${LEFT_COLUMN_WIDTH_PX}px`,
    pr: 2,
    py: 0.5,
    position: 'sticky' as const,
    left: 0,
    zIndex: 2,
    bgcolor: axisBackgroundColor,
    backdropFilter: 'blur(4px)',
  };

  const rowLeftColumnSx = {
    flex: `0 0 ${LEFT_COLUMN_WIDTH_PX}px`,
    pr: 2,
    py: 1.5,
    position: 'sticky' as const,
    left: 0,
    zIndex: 2,
    bgcolor: axisBackgroundColor,
    backdropFilter: 'blur(6px)',
    borderRight: '1px solid',
    borderColor: alpha(theme.palette.divider, 0.6),
  };

  const axisRow = (
    <Box sx={{ display: 'flex', alignItems: 'flex-end', mb: 1.5, gap: 0 }}>
      {mdUp && (
        <Box sx={axisLeftColumnSx}>
          <Typography variant='caption' color='text.secondary'>
            Timeline
          </Typography>
        </Box>
      )}
      <Box
        sx={{
          position: 'relative',
          height: 40,
          width: roundedTrackWidth,
          bgcolor: axisBackgroundColor,
          borderRadius: 20,
          border: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.5),
          boxShadow:
            theme.palette.mode === 'light'
              ? 'inset 0 1px 0 rgba(255,255,255,0.8)'
              : 'inset 0 1px 0 rgba(255,255,255,0.06)',
          overflow: 'hidden',
        }}
      >
        {tickPositions.map(({ date, left, iso }) => (
          <Box
            key={iso}
            sx={{
              position: 'absolute',
              left,
              bottom: 4,
              transform: 'translateX(-50%)',
              textAlign: 'center',
            }}
          >
            <Typography variant='caption' color='text.secondary'>
              {format(date, 'd MMM')}
            </Typography>
            <Box
              sx={{
                width: 1,
                height: 14,
                bgcolor: 'divider',
                mx: 'auto',
              }}
            />
          </Box>
        ))}
      </Box>
    </Box>
  );

  const dayHeaderRow = daySequence.length > 0 && (
    <Box sx={{ display: 'flex', gap: 0, mb: 1.5 }}>
      {mdUp && <Box sx={{ flex: `0 0 ${LEFT_COLUMN_WIDTH_PX}px` }} />}
      <Box
        sx={{
          display: 'flex',
          width: roundedTrackWidth,
          borderRadius: 12,
          border: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.4),
          overflow: 'hidden',
          boxShadow:
            theme.palette.mode === 'light'
              ? 'inset 0 1px 0 rgba(255,255,255,0.7)'
              : 'inset 0 1px 0 rgba(255,255,255,0.08)',
        }}
      >
        {daySequence.map((day, index) => {
          const weekend = isWeekend(day);
          const isTodayLabel = startOfDay(day).getTime() === today.getTime();
          return (
            <Box
              key={day.toISOString()}
              sx={{
                flex: `0 0 ${pixelsPerDay}px`,
                width: `${pixelsPerDay}px`,
                minWidth: `${pixelsPerDay}px`,
                py: 0.5,
                textAlign: 'center',
                borderLeft: index === 0 ? 'none' : '1px solid',
                borderColor: alpha(theme.palette.divider, 0.2),
                bgcolor: weekend ? weekendFill : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontWeight: isTodayLabel ? 700 : 500,
                  color: isTodayLabel ? 'primary.main' : 'text.secondary',
                  lineHeight: 1,
                }}
              >
                {format(day, 'd')}
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Box>
  );

  return (
    <Card sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
          Project Timelines
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Visual overview of project durations with scheduled review milestones.
        </Typography>

        <Box sx={{ overflowX: 'auto', pb: 2 }} ref={scrollContainerRef}>
          <Box sx={{ minWidth: timelineContainerWidth }}>
            {axisRow}
            {dayHeaderRow}

            <Box
              ref={listContainerRef}
              sx={{
                maxHeight: virtualizationEnabled ? '70vh' : 'none',
                overflowY: virtualizationEnabled ? 'auto' : 'visible',
                pr: virtualizationEnabled ? 1 : 0,
              }}
            >
              {virtualizationEnabled && virtualizationMetrics.paddingTop > 0 && (
                <Box sx={{ height: virtualizationMetrics.paddingTop }} />
              )}
              {visibleProjectLayouts.map(({ project, bar, rangeLabel, metaCompact, reviewMarkers }) => (
                <Box
                  key={project.projectId}
                  sx={{
                    display: 'flex',
                    alignItems: mdUp ? 'stretch' : 'flex-start',
                    gap: mdUp ? 0 : 2,
                    minHeight: ROW_HEIGHT_PX,
                    py: mdUp ? 1.5 : 1.25,
                    borderBottom: '1px solid',
                    borderColor: alpha(theme.palette.divider, 0.15),
                    '&:last-of-type': {
                      borderBottom: 'none',
                    },
                  }}
                >
                  {mdUp && (
                    <Box sx={rowLeftColumnSx}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {project.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {rangeLabel}
                      </Typography>
                      {project.projectManager && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          Manager: {project.projectManager}
                        </Typography>
                      )}
                      {(project.clientName || project.projectType) && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {[project.clientName, project.projectType].filter(Boolean).join(' \u2022 ')}
                        </Typography>
                      )}
                    </Box>
                  )}

                  <Box
                    sx={{
                      position: 'relative',
                      flex: `0 0 ${roundedTrackWidth}px`,
                      width: `${roundedTrackWidth}px`,
                      minWidth: `${roundedTrackWidth}px`,
                      bgcolor: trackBackgroundColor,
                      borderRadius: 14,
                      border: '1px solid',
                      borderColor: alpha(theme.palette.divider, 0.3),
                      boxShadow:
                        theme.palette.mode === 'light'
                          ? 'inset 0 1px 0 rgba(255,255,255,0.75)'
                          : 'inset 0 1px 0 rgba(255,255,255,0.08)',
                      overflow: 'hidden',
                    }}
                  >
                    {!mdUp && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 8,
                          left: 12,
                          right: 12,
                          zIndex: 4,
                          pointerEvents: 'none',
                        }}
                      >
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {project.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {rangeLabel}
                        </Typography>
                        {metaCompact && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            {metaCompact}
                          </Typography>
                        )}
                      </Box>
                    )}

                    {weekendSegments.map((segment, index) => (
                      <Box
                        key={`${project.projectId}-weekend-${index}`}
                        sx={{
                          position: 'absolute',
                          top: 0,
                          bottom: 0,
                          left: segment.left,
                          width: segment.width,
                          bgcolor: weekendFill,
                          opacity: theme.palette.mode === 'light' ? 0.45 : 0.35,
                          pointerEvents: 'none',
                          zIndex: 1,
                        }}
                      />
                    ))}

                    {bar.width > 0 && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: mdUp ? '50%' : '60%',
                          left: bar.left,
                          width: bar.width,
                          transform: 'translateY(-50%)',
                          height: BAR_HEIGHT_PX,
                          bgcolor: 'primary.main',
                          opacity: 0.3,
                          borderRadius: 999,
                          zIndex: 3,
                        }}
                      />
                    )}

                    {isTodayInRange && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 0,
                          bottom: 0,
                          left: todayMarkerLeft,
                          width: Math.max(pixelsPerDay, 3),
                          transform: 'translateX(-50%)',
                          bgcolor: alpha(
                            theme.palette.primary.main,
                            theme.palette.mode === 'light' ? 0.15 : 0.28,
                          ),
                          borderRadius: 2,
                          pointerEvents: 'none',
                          zIndex: 2,
                        }}
                      />
                    )}

                    {tickPositions.map(({ left, iso }) => (
                      <Box
                        key={`${project.projectId}-${iso}-grid`}
                        sx={{
                          position: 'absolute',
                          top: 0,
                          bottom: 0,
                          left,
                          width: 1,
                          bgcolor: 'divider',
                          opacity: 0.3,
                          pointerEvents: 'none',
                          zIndex: 2,
                        }}
                      />
                    ))}

                    {reviewMarkers.map((marker) => (
                      <Tooltip
                        key={marker.key}
                        title={
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {marker.serviceName ?? 'Service review'}
                            </Typography>
                            {marker.plannedLabel && (
                              <Typography variant="body2">
                                Planned: {marker.plannedLabel}
                              </Typography>
                            )}
                            {marker.dueLabel && (
                              <Typography variant="body2">
                                Due: {marker.dueLabel}
                              </Typography>
                            )}
                            {marker.status && (
                              <Typography variant="body2">
                                Status: {marker.statusLabel}
                              </Typography>
                            )}
                          </Box>
                        }
                        placement="top"
                      >
                        <Box
                          sx={{
                            position: 'absolute',
                            top: mdUp ? '50%' : '70%',
                            left: marker.left,
                            transform: 'translate(-50%, -50%)',
                            width: MARKER_SIZE_PX,
                            height: MARKER_SIZE_PX,
                            borderRadius: '50%',
                            bgcolor: marker.colorKey,
                            border: '2px solid',
                            borderColor: theme.palette.background.paper,
                            boxShadow: 1,
                            zIndex: 4,
                          }}
                        />
                      </Tooltip>
                    ))}
                  </Box>
                </Box>
              ))}
              {virtualizationEnabled && virtualizationMetrics.paddingBottom > 0 && (
                <Box sx={{ height: virtualizationMetrics.paddingBottom }} />
              )}
            </Box>
          </Box>
        </Box>

        {renderLegend()}
      </CardContent>
    </Card>
  );
}

export default DashboardTimelineChart;
