import { Box, Typography } from '@mui/material';
import { useCallback, useMemo, useRef, useState } from 'react';
import type { TimelineModel, TimelineRowModel } from './useTimelineModel';
import { TimelineRow } from './TimelineRow';

type TimelineGridProps = {
  model: TimelineModel;
  onRowClick: (row: TimelineRowModel) => void;
  height?: number;
};

const ROW_HEIGHT = 52;
const LABEL_WIDTH = 200;
const OVERSCAN = 6;
const HEADER_HEIGHT = 52;

export function TimelineGrid({ model, onRowClick, height = 520 }: TimelineGridProps) {
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const headerRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const handleScroll = useCallback(() => {
    if (!bodyRef.current || !headerRef.current) {
      return;
    }
    const { scrollTop: nextTop, scrollLeft } = bodyRef.current;
    setScrollTop(nextTop);
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    rafRef.current = requestAnimationFrame(() => {
      if (headerRef.current) {
        headerRef.current.scrollLeft = scrollLeft;
      }
    });
  }, []);

  const shouldVirtualize = model.rows.length > 50;
  const totalHeight = model.rows.length * ROW_HEIGHT;
  const viewportHeight = height - 48;
  const startIndex = shouldVirtualize ? Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN) : 0;
  const endIndex = shouldVirtualize
    ? Math.min(model.rows.length, Math.ceil((scrollTop + viewportHeight) / ROW_HEIGHT) + OVERSCAN)
    : model.rows.length;

  const visibleRows = useMemo(() => model.rows.slice(startIndex, endIndex), [model.rows, startIndex, endIndex]);

  return (
    <Box
      data-testid="timeline-grid-root"
      sx={{
        border: (theme) => `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        overflow: 'hidden',
        backgroundColor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', borderBottom: (theme) => `1px solid ${theme.palette.divider}` }}>
        <Box sx={{ width: LABEL_WIDTH, px: 1, py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Project
          </Typography>
        </Box>
        <Box
          ref={headerRef}
          sx={{
            flex: 1,
            overflow: 'hidden',
            position: 'relative',
            height: HEADER_HEIGHT,
          }}
        >
          <Box sx={{ position: 'relative', height: '100%', minWidth: model.rangeWidth }}>
            <Box sx={{ position: 'absolute', inset: 0, height: 24 }}>
              {model.ticks
                .filter((tick) => tick.label)
                .map((tick) => (
                  <Typography
                    key={`label-${tick.date.toISOString()}`}
                    variant="caption"
                    color="text.secondary"
                    sx={{ position: 'absolute', top: 2, left: tick.x + 4, whiteSpace: 'nowrap' }}
                  >
                    {tick.label}
                  </Typography>
                ))}
            </Box>
            <Box data-testid="timeline-day-ticks" sx={{ position: 'absolute', top: 24, height: 24, left: 0, right: 0 }}>
              {model.ticks
                .filter((tick) => tick.subLabel)
                .map((tick) => (
                  <Box key={`day-${tick.date.toISOString()}`} sx={{ position: 'absolute', left: tick.x, top: 0 }}>
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: 1,
                        height: 14,
                        bgcolor: 'divider',
                      }}
                    />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ position: 'absolute', top: 14, left: 4, fontSize: 11 }}
                    >
                      {tick.subLabel}
                    </Typography>
                  </Box>
                ))}
            </Box>
          </Box>
        </Box>
      </Box>

      <Box
        ref={bodyRef}
        onScroll={handleScroll}
        sx={{
          height,
          overflow: 'auto',
          position: 'relative',
        }}
      >
        <Box sx={{ position: 'relative', minWidth: model.rangeWidth + LABEL_WIDTH }}>
          {model.todayX != null && (
            <Box
              data-testid="timeline-today-line"
              sx={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: LABEL_WIDTH + model.todayX,
                width: 1,
                bgcolor: 'primary.main',
                opacity: 0.3,
                pointerEvents: 'none',
              }}
            />
          )}
          <Box sx={{ height: totalHeight, position: 'relative' }}>
            {shouldVirtualize && startIndex > 0 && (
              <Box sx={{ height: startIndex * ROW_HEIGHT }} />
            )}
            {visibleRows.map((row) => (
              <TimelineRow
                key={row.id}
                row={row}
                rowHeight={ROW_HEIGHT}
                labelWidth={LABEL_WIDTH}
                laneWidth={model.rangeWidth}
                onClick={onRowClick}
              />
            ))}
            {shouldVirtualize && endIndex < model.rows.length && (
              <Box sx={{ height: (model.rows.length - endIndex) * ROW_HEIGHT }} />
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
