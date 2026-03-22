import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { DashboardCard } from './DashboardCard';
import { dashboardTokens } from '@/components/dashboards/themes';

export type GroupedBarDatum = {
  label: string;
  open: number;
  closed: number;
};

export function GroupedBarCard({ title, data }: { title: string; data: GroupedBarDatum[] }) {
  return (
    <DashboardCard title={title} subtitle="Open vs closed issues">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#9fb0c3', fontSize: 12 }} axisLine={false} />
          <YAxis tick={{ fill: '#9fb0c3', fontSize: 12 }} axisLine={false} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
          />
          <Legend />
          <Bar dataKey="open" fill={dashboardTokens.compliance.warn} radius={[6, 6, 0, 0]} />
          <Bar dataKey="closed" fill={dashboardTokens.compliance.pass} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </DashboardCard>
  );
}
