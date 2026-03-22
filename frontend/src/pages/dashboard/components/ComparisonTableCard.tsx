import { DashboardCard } from './DashboardCard';

export function ComparisonTableCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <DashboardCard title={title} subtitle={subtitle}>
      {children}
    </DashboardCard>
  );
}
