import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { DashboardCard } from './DashboardCard';
import { dashboardTokens } from '@/components/dashboards/themes';

export type TrendDatum = {
  date: string | null;
  open: number;
  closed: number;
};

export function TrendChartCard({ title, data }: { title: string; data: TrendDatum[] }) {
  return (
    <DashboardCard title={title} subtitle="Open vs closed over time">
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: '#9fb0c3', fontSize: 12 }} axisLine={false} />
          <YAxis tick={{ fill: '#9fb0c3', fontSize: 12 }} axisLine={false} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
          />
          <Area type="monotone" dataKey="open" stroke={dashboardTokens.compliance.warn} fill="rgba(242,182,79,0.2)" strokeWidth={2} />
          <Area type="monotone" dataKey="closed" stroke={dashboardTokens.compliance.pass} fill="rgba(66,194,125,0.2)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </DashboardCard>
  );
}
