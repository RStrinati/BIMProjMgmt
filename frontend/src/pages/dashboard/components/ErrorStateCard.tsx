import { Card, CardContent, Stack, Typography } from '@mui/material';

export function ErrorStateCard({ title, message }: { title: string; message: string }) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6">{title}</Typography>
          <Typography variant="body2" color="error.main">
            {message}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
