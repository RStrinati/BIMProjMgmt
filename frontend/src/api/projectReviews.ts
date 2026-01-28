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

export type MoveServiceReviewPayload = {
  to_service_id: number;
  reason?: string;
};

export type MoveServiceReviewResponse = {
  review_id: number;
  from_service_id: number;
  to_service_id: number;
  is_billed: boolean;
  template_sync_locked: boolean;
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

  /**
   * Move a service review to a different service in the same project.
   * Sets is_user_modified=1 and template_sync_locked=1 to protect from template overwrites.
   * @param projectId - Project ID
   * @param reviewId - Review ID to move
   * @param payload - { to_service_id, reason }
   * @returns Move result with template_sync_locked status
   */
  moveServiceReview: async (
    projectId: number,
    reviewId: number,
    payload: MoveServiceReviewPayload,
  ): Promise<MoveServiceReviewResponse> => {
    const response = await apiClient.patch<MoveServiceReviewResponse>(
      `/projects/${projectId}/reviews/${reviewId}/move`,
      payload,
    );
    return response.data;
  },
};
