import apiClient from './client';
import type { User } from '@/types/api';

export const usersApi = {
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/users');
    return response.data;
  },

  create: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.post<User>('/users', userData);
    return response.data;
  },

  update: async (userId: number, userData: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>(`/users/${userId}`, userData);
    return response.data;
  },

  delete: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}`);
  },
};
