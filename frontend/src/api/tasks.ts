import apiClient from './client';
import type { Task, TaskFilters, TaskPayload } from '@/types/api';

export const tasksApi = {
  getAll: async (filters?: TaskFilters): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>('/tasks', { params: filters });
    return response.data;
  },

  getNotesView: async (filters?: TaskFilters): Promise<Task[]> => {
    const response = await apiClient.get<{ tasks: Task[] }>('/tasks/notes-view', { params: filters });
    return response.data.tasks;
  },

  create: async (task: TaskPayload): Promise<Task> => {
    const response = await apiClient.post<Task>('/tasks', task);
    return response.data;
  },

  update: async (id: number, task: Partial<TaskPayload>): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${id}`, task);
    return response.data;
  },

  delete: async (id: number, options?: { hardDelete?: boolean }): Promise<void> => {
    const params = options?.hardDelete ? { hard: 'true' } : undefined;
    await apiClient.delete(`/tasks/${id}`, { params });
  },

  toggleItem: async (taskId: number, itemIndex: number): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${taskId}/items/${itemIndex}/toggle`);
    return response.data;
  },
};
