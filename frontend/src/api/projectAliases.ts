import apiClient from './client';
import type {
  ProjectAlias,
  ProjectAliasStats,
  UnmappedProjectAlias,
  ProjectAliasValidationResult,
} from '@/types/api';

const encodeAlias = (aliasName: string) => encodeURIComponent(aliasName);

export const projectAliasesApi = {
  getAll: async (): Promise<ProjectAlias[]> => {
    const response = await apiClient.get<ProjectAlias[]>('/project_aliases');
    return response.data;
  },

  create: async (payload: { alias_name: string; project_id: number }): Promise<ProjectAlias> => {
    const response = await apiClient.post<ProjectAlias>('/project_aliases', payload);
    return response.data;
  },

  update: async (
    aliasName: string,
    payload: { alias_name?: string; project_id?: number },
  ): Promise<ProjectAlias> => {
    const response = await apiClient.patch<ProjectAlias>(
      `/project_aliases/${encodeAlias(aliasName)}`,
      payload,
    );
    return response.data;
  },

  delete: async (aliasName: string): Promise<void> => {
    await apiClient.delete(`/project_aliases/${encodeAlias(aliasName)}`);
  },

  getStats: async (): Promise<ProjectAliasStats[]> => {
    const response = await apiClient.get<ProjectAliasStats[]>('/project_aliases/stats');
    return response.data;
  },

  getUnmapped: async (): Promise<UnmappedProjectAlias[]> => {
    const response = await apiClient.get<UnmappedProjectAlias[]>('/project_aliases/unmapped');
    return response.data;
  },

  getValidation: async (): Promise<ProjectAliasValidationResult> => {
    const response = await apiClient.get<ProjectAliasValidationResult>('/project_aliases/validation');
    return response.data;
  },
};
