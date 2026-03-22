import { Card, CardContent, Skeleton, Stack } from '@mui/material';

export function LoadingSkeletonCard() {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="rectangular" height={160} />
        </Stack>
      </CardContent>
    </Card>
  );
}
