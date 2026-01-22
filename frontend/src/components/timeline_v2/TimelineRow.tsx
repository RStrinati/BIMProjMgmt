import { Avatar, Box, Stack, Typography } from '@mui/material';
import { FlagRounded } from '@mui/icons-material';
import type { TimelineRowModel } from './useTimelineModel';

type TimelineRowProps = {
  row: TimelineRowModel;
  rowHeight: number;
  labelWidth: number;
  laneWidth: number;
  onClick: (row: TimelineRowModel) => void;
};

const resolvePalette = (token: string, palette: any) => {
  if (token === 'info') return palette.info;
  if (token === 'primary') return palette.primary;
  if (token === 'warning') return palette.warning;
  return {
    light: palette.grey[200],
    main: palette.grey[500],
  };
};

const resolvePriorityTone = (value?: string | number | null) => {
  if (value == null) return null;
  if (typeof value === 'string') {
    const trimmed = value.trim().toLowerCase();
    if (/^\d+$/.test(trimmed)) {
      return resolvePriorityTone(Number(trimmed));
    }
    if (trimmed === 'high' || trimmed === 'critical') {
      return 'error';
    }
    if (trimmed === 'medium') {
      return 'warning';
    }
    if (trimmed === 'low') {
      return 'info';
    }
  }
  const normalized = typeof value === 'number' ? value : value.toString().trim().toLowerCase();
  if (normalized === 4 || normalized === 3 || normalized === 'high' || normalized === 'critical') {
    return 'error';
  }
  if (normalized === 2 || normalized === 'medium') {
    return 'warning';
  }
  if (normalized === 1 || normalized === 'low') {
    return 'info';
  }
  return 'info';
};

export function TimelineRow({
  row,
  rowHeight,
  labelWidth,
  laneWidth,
  onClick,
}: TimelineRowProps) {
  return (
    <Box
      role="button"
      tabIndex={0}
      onClick={() => onClick(row)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          onClick(row);
        }
      }}
      sx={{
        display: 'flex',
        alignItems: 'center',
        height: rowHeight,
        borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
        cursor: 'pointer',
        px: 1,
        '&:hover': { backgroundColor: 'action.hover' },
        '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main' },
      }}
    >
      <Box sx={{ width: labelWidth, pr: 2, overflow: 'hidden' }} data-testid="timeline-row-label">
        <Stack spacing={0.25} sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
            <Typography variant="body2" noWrap fontWeight={600} sx={{ minWidth: 0, flex: 1 }}>
              {row.label}
            </Typography>
            <Stack direction="row" spacing={0.5} alignItems="center" sx={{ flexShrink: 0 }}>
              {row.priorityLabel || row.priorityValue != null ? (
                <Box data-testid="timeline-row-priority" sx={{ display: 'flex', alignItems: 'center' }}>
                  <FlagRounded
                    fontSize="small"
                    sx={(theme) => ({
                      color: resolvePriorityTone(row.priorityLabel ?? row.priorityValue)
                        ? theme.palette[resolvePriorityTone(row.priorityLabel ?? row.priorityValue) as 'error' | 'warning' | 'info'].main
                        : theme.palette.text.disabled,
                    })}
                  />
                </Box>
              ) : null}
              {row.leadLabel ? (
                <Avatar
                  data-testid="timeline-row-lead"
                  sx={{
                    width: 18,
                    height: 18,
                    fontSize: 10,
                    bgcolor: 'grey.200',
                    color: 'text.primary',
                  }}
                >
                  {row.leadInitials}
                </Avatar>
              ) : null}
            </Stack>
          </Stack>
          {row.metaLines?.length ? (
            <Stack spacing={0} sx={{ minWidth: 0 }}>
              {row.metaLines.map((line, index) => (
                <Box key={index} sx={{ minWidth: 0 }}>
                  {typeof line === 'string' ? (
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {line}
                    </Typography>
                  ) : (
                    line
                  )}
                </Box>
              ))}
            </Stack>
          ) : null}
        </Stack>
      </Box>
      <Box sx={{ position: 'relative', flex: 1, height: rowHeight, minWidth: laneWidth }}>
        {row.hasDates ? (
          <Box
            className="timeline-bar"
            aria-label={row.progressLabel ?? '--%'}
            sx={{
              position: 'absolute',
              left: row.bar.xStart,
              width: Math.max(row.bar.xEnd - row.bar.xStart, 6),
              top: (rowHeight - 14) / 2,
              height: 14,
              borderRadius: 999,
              backgroundColor: (theme) => resolvePalette(row.colorToken, theme.palette).light,
              border: (theme) => `1px solid ${resolvePalette(row.colorToken, theme.palette).main}`,
              opacity: 0.85,
              transition: 'opacity 120ms ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              px: 0.5,
              overflow: 'hidden',
              color: (theme) =>
                theme.palette.getContrastText(resolvePalette(row.colorToken, theme.palette).light),
            }}
          >
            {row.progressLabel ? (
              <Typography
                data-testid="timeline-bar-label"
                variant="caption"
                noWrap
                sx={{ fontWeight: 600, lineHeight: 1 }}
              >
                {row.progressLabel}
              </Typography>
            ) : null}
          </Box>
        ) : (
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            No dates
          </Typography>
        )}
      </Box>
    </Box>
  );
}
