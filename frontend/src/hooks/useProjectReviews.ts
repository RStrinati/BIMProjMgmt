import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectReviewsApi } from '@/api';
import type { ProjectReviewsResponse } from '@/types/api';
import type { ProjectReviewsFilters } from '@/api/projectReviews';

const stableSerialize = (value: Record<string, unknown>) =>
  JSON.stringify(value, Object.keys(value).sort());

export const useProjectReviews = (projectId: number, filters?: ProjectReviewsFilters) => {
  const filtersKey = useMemo(() => stableSerialize(filters ?? {}), [filters]);

  return useQuery<ProjectReviewsResponse>({
    queryKey: ['projectReviews', projectId, filtersKey],
    queryFn: () => projectReviewsApi.getProjectReviews(projectId, filters),
    enabled: Number.isFinite(projectId),
  });
};
