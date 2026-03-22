import { Card, CardContent, Stack, Typography } from '@mui/material';

export type SummaryCardProps = {
  label: string;
  value: string | number;
  helper?: string;
  accent?: string;
  onClick?: () => void;
};

export function SummaryCard({ label, value, helper, accent, onClick }: SummaryCardProps) {
  return (
    <Card
      sx={{
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        border: onClick ? '1px solid rgba(111, 180, 255, 0.45)' : undefined,
      }}
      onClick={onClick}
    >
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, color: accent ?? 'text.primary' }}>
            {value}
          </Typography>
          {helper ? (
            <Typography variant="caption" color="text.secondary">
              {helper}
            </Typography>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
