import { Grid } from '@mui/material';
import { SummaryCard, type SummaryCardProps } from './components/SummaryCard';

export function KpiStrip({ items }: { items: SummaryCardProps[] }) {
  return (
    <Grid container spacing={2}>
      {items.map((item) => (
        <Grid item xs={12} sm={6} md={3} key={item.label}>
          <SummaryCard {...item} />
        </Grid>
      ))}
    </Grid>
  );
}
