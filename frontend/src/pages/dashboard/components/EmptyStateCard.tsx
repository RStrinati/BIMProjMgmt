import { Card, CardContent, Stack, Typography } from '@mui/material';

export function EmptyStateCard({ title, message }: { title: string; message: string }) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6">{title}</Typography>
          <Typography variant="body2" color="text.secondary">
            {message}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
