import apiClient from './client';
import type { ProjectReviewsResponse } from '@/types/api';

export type ProjectReviewsFilters = {
  status?: string;
  service_id?: number;
  from_date?: string;
  to_date?: string;
  sort_by?: 'planned_date' | 'due_date' | 'status' | 'service_name';
  sort_dir?: 'asc' | 'desc';
  limit?: number;
  page?: number;
};

export const projectReviewsApi = {
  getProjectReviews: async (
    projectId: number,
    filters?: ProjectReviewsFilters,
  ): Promise<ProjectReviewsResponse> => {
    const response = await apiClient.get<ProjectReviewsResponse>(`/projects/${projectId}/reviews`, {
      params: filters,
    });
    return response.data;
  },
};
