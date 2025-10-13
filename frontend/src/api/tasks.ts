import apiClient from './client';
import type { Task, TaskFilters } from '@/types/api';

export const tasksApi = {
  // Get all tasks
  getAll: async (filters?: TaskFilters): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>('/tasks', { params: filters });
    return response.data;
  },

  // Get tasks for a project
  getByProject: async (projectId: number): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>(`/projects/${projectId}/tasks`);
    return response.data;
  },

  // Create new task
  create: async (task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.post<Task>('/tasks', task);
    return response.data;
  },

  // Update task
  update: async (id: number, task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${id}`, task);
    return response.data;
  },

  // Delete task
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`);
  },

  // Complete task
  complete: async (id: number): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/tasks/${id}/complete`);
    return response.data;
  },
};
