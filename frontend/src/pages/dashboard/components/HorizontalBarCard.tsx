import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { DashboardCard } from './DashboardCard';
import { dashboardTokens } from '@/components/dashboards/themes';

export type HorizontalBarDatum = {
  label: string;
  value: number;
};

export function HorizontalBarCard({ title, data }: { title: string; data: HorizontalBarDatum[] }) {
  return (
    <DashboardCard title={title} subtitle="Open issues by zone">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 8, left: 12, bottom: 8 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#9fb0c3', fontSize: 12 }} axisLine={false} />
          <YAxis type="category" dataKey="label" tick={{ fill: '#9fb0c3', fontSize: 12 }} width={110} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            contentStyle={{ background: '#0f141b', border: '1px solid rgba(255,255,255,0.12)' }}
          />
          <Bar dataKey="value" fill={dashboardTokens.compliance.warn} radius={[0, 8, 8, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </DashboardCard>
  );
}
