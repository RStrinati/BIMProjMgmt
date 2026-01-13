import React, { useMemo, useState } from 'react';
import { Box, Card, CardContent, CardHeader, Typography } from '@mui/material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  LabelList,
} from 'recharts';
import { addMonths, endOfMonth, format, isValid, parseISO, subMonths } from 'date-fns';
import type { IssueHistoryPoint } from '@/types/api';

type IssueSeriesKey = 'closed' | 'completed' | 'in_progress' | 'open';

type IssueVolumePoint = {
  week: string;
  closed: number | null;
  completed: number | null;
  in_progress: number | null;
  open: number | null;
  hasData: boolean;
};

type IssueSeriesConfig = {
  key: IssueSeriesKey;
  label: string;
  color: string;
  fillOpacity: number;
  labelPriority: 'major' | 'minor';
};

const SERIES: IssueSeriesConfig[] = [
  {
    key: 'closed',
    label: 'Closed',
    color: '#6B6B6B',
    fillOpacity: 0.6,
    labelPriority: 'major',
  },
  {
    key: 'completed',
    label: 'Completed',
    color: '#2DA44E',
    fillOpacity: 0.5,
    labelPriority: 'minor',
  },
  {
    key: 'in_progress',
    label: 'In progress',
    color: '#2F6BFF',
    fillOpacity: 0.4,
    labelPriority: 'minor',
  },
  {
    key: 'open',
    label: 'Open',
    color: '#F2790F',
    fillOpacity: 0.5,
    labelPriority: 'major',
  },
];

const LEGEND_TITLE = 'Transform File (3).Status';

const normalizeStatusKey = (status: string | null | undefined): IssueSeriesKey | null => {
  if (!status) {
    return null;
  }
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  if (normalized === 'in-progress') {
    return 'in_progress';
  }
  if (normalized === 'inprogress') {
    return 'in_progress';
  }
  if (normalized === 'in_progress') {
    return 'in_progress';
  }
  if (normalized === 'open') {
    return 'open';
  }
  if (normalized === 'closed') {
    return 'closed';
  }
  if (normalized === 'completed') {
    return 'completed';
  }
  return null;
};

const formatMonthLabel = (value?: string | null) => {
  if (!value) {
    return '';
  }
  const parsed = parseISO(value);
  if (!isValid(parsed)) {
    return '';
  }
  return `${format(parsed, 'yyyy-MM')}.xlsx`;
};

const buildMonthlySeries = (
  history: IssueHistoryPoint[],
  windowMonths: number,
): IssueVolumePoint[] => {
  if (!history.length) {
    return [];
  }

  const monthMap = new Map<string, Partial<Record<IssueSeriesKey, number>>>();
  history.forEach((entry) => {
    if (!entry.week_start) {
      return;
    }
    const parsed = parseISO(entry.week_start);
    if (!isValid(parsed)) {
      return;
    }
    const monthEnd = format(endOfMonth(parsed), 'yyyy-MM-dd');
    const key = normalizeStatusKey(entry.status);
    if (!key) {
      return;
    }
    const existing = monthMap.get(monthEnd) ?? {};
    existing[key] = (existing[key] ?? 0) + entry.count;
    monthMap.set(monthEnd, existing);
  });

  const sortedMonths = Array.from(monthMap.keys()).sort();
  if (!sortedMonths.length) {
    return [];
  }

  const lastMonth = parseISO(sortedMonths[sortedMonths.length - 1]);
  const startMonth = subMonths(lastMonth, windowMonths - 1);
  const range: IssueVolumePoint[] = [];

  for (let i = 0; i < windowMonths; i += 1) {
    const current = endOfMonth(addMonths(startMonth, i));
    const monthKey = format(current, 'yyyy-MM-dd');
    const entry = monthMap.get(monthKey);
    if (!entry) {
      range.push({
        week: monthKey,
        closed: null,
        completed: null,
        in_progress: null,
        open: null,
        hasData: false,
      });
      continue;
    }
    range.push({
      week: monthKey,
      closed: entry.closed ?? 0,
      completed: entry.completed ?? 0,
      in_progress: entry.in_progress ?? 0,
      open: entry.open ?? 0,
      hasData: true,
    });
  }

  return range;
};

const IssueVolumeTrendChart: React.FC<{
  history: IssueHistoryPoint[];
  windowMonths?: number;
}> = ({ history, windowMonths = 3 }) => {
  const [hiddenKeys, setHiddenKeys] = useState<IssueSeriesKey[]>([]);

  const data = useMemo(
    () => buildMonthlySeries(history, windowMonths),
    [history, windowMonths],
  );

  const activeSeries = useMemo(
    () => SERIES.filter((series) => !hiddenKeys.includes(series.key)),
    [hiddenKeys],
  );

  const maxValue = useMemo(() => {
    if (!data.length || !activeSeries.length) {
      return 0;
    }
    return data.reduce((max, point) => {
      const localMax = activeSeries.reduce((seriesMax, series) => {
        const value = point[series.key];
        if (value == null) {
          return seriesMax;
        }
        return Math.max(seriesMax, value);
      }, 0);
      return Math.max(max, localMax);
    }, 0);
  }, [data, activeSeries]);

  const handleLegendToggle = (key: IssueSeriesKey) => {
    setHiddenKeys((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key],
    );
  };

  const renderLegend = ({ payload }: { payload?: Array<{ dataKey?: string }> }) => {
    const items = SERIES.filter((series) =>
      payload?.some((entry) => entry.dataKey === series.key),
    );

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
          {LEGEND_TITLE}
        </Typography>
        {items.map((series) => {
          const isHidden = hiddenKeys.includes(series.key);
          return (
            <Box
              key={series.key}
              onClick={() => handleLegendToggle(series.key)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.75,
                cursor: 'pointer',
                opacity: isHidden ? 0.4 : 1,
                transition: 'opacity 200ms ease',
              }}
            >
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  bgcolor: series.color,
                }}
              />
              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                {series.label}
              </Typography>
            </Box>
          );
        })}
      </Box>
    );
  };

  const renderTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ dataKey: IssueSeriesKey; value: number | null; color: string }>;
    label?: string;
  }) => {
    if (!active || !payload || !payload.length) {
      return null;
    }
    const visiblePayload = payload.filter((item) => item.value != null);
    return (
      <Box
        sx={{
          bgcolor: '#ffffff',
          borderRadius: 2,
          boxShadow: '0 6px 16px rgba(15, 23, 42, 0.12)',
          px: 2,
          py: 1.5,
          border: '1px solid rgba(15, 23, 42, 0.08)',
        }}
      >
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          {formatMonthLabel(label)}
        </Typography>
        {visiblePayload.map((item) => {
          const series = SERIES.find((entry) => entry.key === item.dataKey);
          return (
            <Box key={item.dataKey} sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: series?.color ?? item.color,
                }}
              />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {series?.label ?? item.dataKey}
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {(item.value ?? 0).toLocaleString()}
              </Typography>
            </Box>
          );
        })}
      </Box>
    );
  };

  const renderPointLabel = (
    value: number | null | undefined,
    x: number | undefined,
    y: number | undefined,
    labelPriority: 'major' | 'minor',
  ) => {
    if (value == null || x == null || y == null) {
      return null;
    }
    if (labelPriority === 'minor' && value < 10) {
      return null;
    }
    const text = value.toLocaleString();
    const paddingX = 6;
    const height = 18;
    const width = Math.max(26, text.length * 7 + paddingX * 2);
    return (
      <g>
        <rect
          x={x - width / 2}
          y={y - height - 6}
          width={width}
          height={height}
          rx={8}
          ry={8}
          fill="#ffffff"
          stroke="rgba(15, 23, 42, 0.12)"
        />
        <text
          x={x}
          y={y - 12}
          textAnchor="middle"
          fontSize={11}
          fill="#1f2937"
          fontWeight={600}
        >
          {text}
        </text>
      </g>
    );
  };

  return (
    <Card sx={{ height: '100%', border: '1px solid rgba(0,0,0,0.08)' }}>
      <CardHeader
        title="Issue Volume Trends"
        subheader="Monthly issue counts (90-day window)"
        sx={{
          '& .MuiCardHeader-title': { fontSize: '1.1rem', fontWeight: 600 },
          '& .MuiCardHeader-subheader': { fontSize: '0.85rem' },
        }}
      />
      <CardContent>
        <ResponsiveContainer width="100%" height={340}>
          <AreaChart
            data={data}
            margin={{ top: 40, right: 16, left: 8, bottom: 32 }}
          >
            <CartesianGrid strokeDasharray="2 6" stroke="rgba(0,0,0,0.2)" />
            <XAxis
              dataKey="week"
              tickFormatter={formatMonthLabel}
              interval={0}
              tick={{ fontSize: 11, angle: -35, textAnchor: 'end', fill: 'rgba(0,0,0,0.55)' }}
              height={50}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, Math.max(10, Math.ceil(maxValue * 1.1))]}
              tick={false}
              axisLine={false}
              tickLine={false}
            />
            <ChartTooltip content={renderTooltip} />
            <Legend verticalAlign="top" align="left" content={renderLegend} />
            {SERIES.map((series) => (
              <Area
                key={series.key}
                type="monotone"
                dataKey={series.key}
                stroke={series.color}
                strokeWidth={2.6}
                strokeLinecap="round"
                strokeLinejoin="round"
                fill={series.color}
                fillOpacity={series.fillOpacity}
                connectNulls={false}
                hide={hiddenKeys.includes(series.key)}
                isAnimationActive
                animationDuration={450}
              >
                <LabelList
                  dataKey={series.key}
                  content={({ value, x, y }) =>
                    renderPointLabel(value as number | null, x, y, series.labelPriority)
                  }
                />
              </Area>
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default IssueVolumeTrendChart;
