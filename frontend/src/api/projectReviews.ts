import apiClient from './client';
import type { ProjectReviewItem, ProjectReviewsResponse } from '@/types/api';

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

export type PatchProjectReviewPayload = {
  due_date?: string | null;
  status?: string | null;
  invoice_reference?: string | null;
  invoice_date?: string | null;
  is_billed?: boolean | null;
  invoice_month_override?: string | null;
  invoice_batch_id?: number | null;
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

  /**
   * Patch a single project review (deliverables fields).
   * @param projectId - Project ID
   * @param reviewId - Review ID
   * @param serviceId - Service ID (for URL construction)
   * @param payload - Fields to update (due_date, status, invoice_reference, invoice_date, is_billed)
   * @returns Updated ProjectReviewItem
   */
  patchProjectReview: async (
    projectId: number,
    reviewId: number,
    serviceId: number,
    payload: PatchProjectReviewPayload,
  ): Promise<ProjectReviewItem> => {
    const response = await apiClient.patch<ProjectReviewItem>(
      `/projects/${projectId}/services/${serviceId}/reviews/${reviewId}`,
      payload,
    );
    return response.data;
  },
};
