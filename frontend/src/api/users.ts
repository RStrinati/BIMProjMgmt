import apiClient from './client';
import type { User } from '@/types/api';

export const usersApi = {
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/users');
    return response.data;
  },
};
