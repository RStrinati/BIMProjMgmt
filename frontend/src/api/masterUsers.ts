import apiClient from './client';
import type { MasterUser } from '@/types/api';

export const masterUsersApi = {
  list: async (): Promise<MasterUser[]> => {
    const response = await apiClient.get<MasterUser[]>('/master-users');
    return response.data;
  },
  updateFlags: async (userKey: string, updates: Partial<Pick<MasterUser, 'invited_to_bim_meetings' | 'is_watcher' | 'is_assignee'>>): Promise<void> => {
    await apiClient.patch(`/master-users/${encodeURIComponent(userKey)}`, updates);
  },
  refreshReviztoUsers: async (): Promise<void> => {
    await apiClient.post('/revizto/license-members/sync');
  },
};
