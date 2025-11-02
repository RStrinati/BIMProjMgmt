import apiClient from './client';
import type {
  ProjectAlias,
  ProjectAliasStats,
  UnmappedProjectAlias,
  ProjectAliasValidationResult,
} from '@/types/api';

const encodeAlias = (aliasName: string) => encodeURIComponent(aliasName);

export const projectAliasesApi = {
  getSummary: async (): Promise<any> => {
    const response = await apiClient.get<any>('/project_aliases/summary');
    return response.data;
  },

  analyze: async (): Promise<any> => {
    const response = await apiClient.post<any>('/project_aliases/analyze');
    return response.data;
  },

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

  autoMap: async (payload: { min_confidence: number; dry_run: boolean }): Promise<any> => {
    const response = await apiClient.post<any>('/project_aliases/auto-map', payload);
    return response.data;
  },
};
