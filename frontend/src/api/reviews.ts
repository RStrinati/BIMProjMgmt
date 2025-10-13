import apiClient from './client';
import type { Review, ReviewCycle, ReviewFilters } from '@/types/api';

export const reviewsApi = {
  // Get all reviews
  getAll: async (filters?: ReviewFilters): Promise<Review[]> => {
    const response = await apiClient.get<Review[]>('/reviews', { params: filters });
    return response.data;
  },

  // Get reviews for a project
  getByProject: async (projectId: number, cycleId?: number): Promise<Review[]> => {
    const response = await apiClient.get<Review[]>(`/projects/${projectId}/reviews`, {
      params: { cycle_id: cycleId },
    });
    return response.data;
  },

  // Get review cycles
  getCycles: async (projectId: number): Promise<ReviewCycle[]> => {
    const response = await apiClient.get<ReviewCycle[]>(`/projects/${projectId}/cycles`);
    return response.data;
  },

  // Update review status
  updateStatus: async (reviewId: number, status: string): Promise<Review> => {
    const response = await apiClient.patch<Review>(`/reviews/${reviewId}`, { status });
    return response.data;
  },

  // Create new review
  create: async (review: Partial<Review>): Promise<Review> => {
    const response = await apiClient.post<Review>('/reviews', review);
    return response.data;
  },
};
