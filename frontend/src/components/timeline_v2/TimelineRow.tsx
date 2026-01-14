import { Box, Chip, Stack, Typography } from '@mui/material';
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
      <Box sx={{ width: labelWidth, pr: 2, overflow: 'hidden' }}>
        <Typography variant="body2" noWrap fontWeight={600}>
          {row.label}
        </Typography>
        {row.meta?.length ? (
          <Stack direction="row" spacing={0.5} sx={{ mt: 0.25, flexWrap: 'wrap' }}>
            {row.meta.slice(0, 2).map((item) => (
              <Chip key={item} size="small" label={item} variant="outlined" />
            ))}
          </Stack>
        ) : null}
      </Box>
      <Box sx={{ position: 'relative', flex: 1, height: rowHeight, minWidth: laneWidth }}>
        {row.hasDates ? (
          <Box
            className="timeline-bar"
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
            }}
          />
        ) : (
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            No dates
          </Typography>
        )}
      </Box>
    </Box>
  );
}
