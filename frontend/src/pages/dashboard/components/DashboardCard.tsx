import { Card, CardContent, Stack, Typography, type SxProps } from '@mui/material';

export type DashboardCardProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  sx?: SxProps;
};

export function DashboardCard({ title, subtitle, action, children, sx }: DashboardCardProps) {
  return (
    <Card sx={{ height: '100%', ...sx }}>
      <CardContent>
        <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
          <Stack spacing={0.5}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
            {subtitle ? (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            ) : null}
          </Stack>
          {action ? <div>{action}</div> : null}
        </Stack>
        {children}
      </CardContent>
    </Card>
  );
}
