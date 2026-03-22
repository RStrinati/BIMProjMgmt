import { Box, Stack, Typography } from '@mui/material';
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { DashboardCard } from './DashboardCard';
import { dashboardTokens } from '@/components/dashboards/themes';

export type ComplianceDonutCardProps = {
  title: string;
  compliant: number;
  nonCompliant: number;
  unknown?: number;
  onClickSegment?: (segment: 'compliant' | 'non_compliant' | 'unknown') => void;
};

export function ComplianceDonutCard({
  title,
  compliant,
  nonCompliant,
  unknown = 0,
  onClickSegment,
}: ComplianceDonutCardProps) {
  const total = compliant + nonCompliant + unknown;
  const pct = total > 0 ? Math.round((compliant / total) * 100) : 0;
  const data = [
    { name: 'Compliant', value: compliant, key: 'compliant' as const, color: dashboardTokens.compliance.pass },
    { name: 'Non-compliant', value: nonCompliant, key: 'non_compliant' as const, color: dashboardTokens.compliance.fail },
  ];
  if (unknown > 0) {
    data.push({ name: 'Unknown', value: unknown, key: 'unknown' as const, color: dashboardTokens.compliance.neutral });
  }

  return (
    <DashboardCard title={title} subtitle={`${total} total checks`}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Box sx={{ width: 140, height: 140 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                innerRadius={48}
                outerRadius={64}
                paddingAngle={2}
                dataKey="value"
                onClick={(entry) => {
                  const payload = entry as { key?: 'compliant' | 'non_compliant' | 'unknown' };
                  if (payload?.key && onClickSegment) {
                    onClickSegment(payload.key);
                  }
                }}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                cursor={{ fill: 'transparent' }}
                contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Box>
        <Stack spacing={0.5}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {pct}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compliant
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {compliant} compliant · {nonCompliant} non-compliant
          </Typography>
        </Stack>
      </Stack>
    </DashboardCard>
  );
}
