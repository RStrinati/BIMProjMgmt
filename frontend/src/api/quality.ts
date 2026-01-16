import apiClient from './client';
import type {
  QualityRegisterResponse,
  QualityRegisterExpectedResponse,
  ExpectedModel,
  ExpectedModelAlias,
} from '@/types/api';

export const qualityApi = {
  /**
   * Fetch quality register for a project (observed or expected mode).
   *
   * @param projectId Project ID
   * @param options Query options, including mode
   */
  getRegister: async (
    projectId: number,
    options?: {
      page?: number;
      page_size?: number;
      sort_by?: 'lastVersionDate' | 'modelName' | 'freshnessStatus' | 'validationOverall';
      sort_dir?: 'asc' | 'desc';
      filter_attention?: boolean;
      mode?: 'observed' | 'expected';
    }
  ): Promise<QualityRegisterResponse> => {
    const params = {
      page: options?.page ?? 1,
      page_size: options?.page_size ?? 50,
      sort_by: options?.sort_by ?? 'lastVersionDate',
      sort_dir: options?.sort_dir ?? 'desc',
      filter_attention: options?.filter_attention ?? false,
      mode: options?.mode ?? 'observed',
    };

    const response = await apiClient.get<QualityRegisterResponse>(
      `/projects/${projectId}/quality/register`,
      { params }
    );
    return response.data;
  },

  /**
   * Fetch quality register in expected-first mode.
   *
   * Returns expected_rows, unmatched_observed, and counts.
   *
   * @param projectId Project ID
   */
  getExpectedRegister: async (projectId: number): Promise<QualityRegisterExpectedResponse> => {
    const response = await apiClient.get<QualityRegisterExpectedResponse>(
      `/projects/${projectId}/quality/register`,
      { params: { mode: 'expected' } }
    );
    return response.data;
  },

  /**
   * List all expected models for a project.
   */
  listExpectedModels: async (projectId: number): Promise<ExpectedModel[]> => {
    const response = await apiClient.get<{ expected_models: ExpectedModel[] }>(
      `/projects/${projectId}/quality/expected-models`
    );
    return response.data.expected_models;
  },

  /**
   * Create a new expected model.
   */
  createExpectedModel: async (
    projectId: number,
    payload: {
      expected_model_key: string;
      display_name?: string;
      discipline?: string;
      company_id?: number;
      is_required?: boolean;
    }
  ): Promise<{ expected_model_id: number }> => {
    const response = await apiClient.post<{ expected_model_id: number }>(
      `/projects/${projectId}/quality/expected-models`,
      payload
    );
    return response.data;
  },

  /**
   * List all expected model aliases for a project.
   */
  listExpectedModelAliases: async (projectId: number): Promise<ExpectedModelAlias[]> => {
    const response = await apiClient.get<{ aliases: ExpectedModelAlias[] }>(
      `/projects/${projectId}/quality/expected-model-aliases`
    );
    return response.data.aliases;
  },

  /**
   * Create a new expected model alias (mapping observed to expected).
   */
  createExpectedModelAlias: async (
    projectId: number,
    payload: {
      expected_model_id: number;
      alias_pattern: string;
      match_type?: 'exact' | 'contains' | 'regex';
      target_field?: 'filename' | 'rvt_model_key';
      is_active?: boolean;
    }
  ): Promise<{ expected_model_alias_id: number }> => {
    const response = await apiClient.post<{ expected_model_alias_id: number }>(
      `/projects/${projectId}/quality/expected-model-aliases`,
      payload
    );
    return response.data;
  },
};
