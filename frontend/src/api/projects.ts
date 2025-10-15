import apiClient from './client';
import type { Project, ProjectFilters } from '@/types/api';

export const projectsApi = {
  // Get all projects
  getAll: async (filters?: ProjectFilters): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/projects', { params: filters });
    return response.data;
  },

  // Get single project by ID
  getById: async (id: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/project/${id}`);
    return response.data;
  },

  // Create new project
  create: async (project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', project);
    return response.data;
  },

  // Update project
  update: async (id: number, project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, project);
    return response.data;
  },

  // Delete project
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },

  // Get project statistics
  getStats: async (): Promise<{
    total: number;
    active: number;
    completed: number;
    on_hold: number;
  }> => {
    const response = await apiClient.get('/projects/stats');
    return response.data;
  },

  // Get review statistics for all projects
  getReviewStats: async (): Promise<Record<number, {
    total_reviews: number;
    completed_reviews: number;
    planned_reviews: number;
    in_progress_reviews: number;
    overdue_reviews: number;
    earliest_review_date: string | null;
    latest_review_date: string | null;
    upcoming_reviews_30_days: number;
  }>> => {
    const response = await apiClient.get('/project_review_statistics');
    return response.data;
  },
};
