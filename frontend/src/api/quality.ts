import apiClient from './client';
import type {
  QualityRegisterResponse,
  QualityRegisterExpectedResponse,
  ExpectedModel,
  ExpectedModelAlias,
} from '@/types/api';

// Phase 1D Types
export type QualityPhase1DRow = {
  expected_model_id: number;
  abv: string | null;
  modelName: string | null;
  company: string | null;
  discipline: string | null;
  description: string | null;
  bimContact: string | null;
  folderPath: string | null;
  accPresent: boolean;
  accDate: string | null;
  reviztoPresent: boolean;
  reviztoDate: string | null;
  notes: string | null;
  notesUpdatedAt: string | null;
  mappingStatus: 'MAPPED' | 'ALIASED' | 'UNMAPPED';
  matchedObservedFile: string | null;
  validationOverall: string;
  freshnessStatus: string;
};

export type QualityPhase1DRegisterResponse = {
  rows: QualityPhase1DRow[];
};

export type QualityModelDetailResponse = {
  id: number;
  abv: string | null;
  registeredModelName: string | null;
  company: string | null;
  discipline: string | null;
  description: string | null;
  bimContact: string | null;
  notes: string | null;
  notesUpdatedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  
  // Phase 3 fields
  serviceId?: number | null;
  reviewCycleId?: number | null;
  milestoneId?: number | null;
  expectedDeliveryDate?: string | null;
  actualDeliveryDate?: string | null;
  deliveryStatus?: 'PENDING' | 'ON_TRACK' | 'AT_RISK' | 'DELIVERED' | 'LATE' | null;
  
  aliases: Array<{
    id: number;
    matchType: 'exact' | 'contains' | 'regex';
    pattern: string;
    createdAt: string | null;
  }>;
  
  observedMatch: {
    fileName: string | null;
    folderPath: string | null;
    lastModified: string | null;
    fileSize: number | null;
  } | null;
  
  health: {
    validationStatus: 'PASS' | 'FAIL' | 'WARN' | 'UNKNOWN';
    freshnessStatus: 'MISSING' | 'CURRENT' | 'DUE_SOON' | 'OUT_OF_DATE' | 'UNKNOWN';
    metrics: Record<string, any>;
  };
  
  activity: any[];
};

export type QualityModelHistoryResponse = {
  history: Array<{
    historyId: number;
    changeType: 'INSERT' | 'UPDATE' | 'DELETE';
    changedFields: string;
    snapshot: {
      abv: string | null;
      registeredModelName: string | null;
      company: string | null;
      discipline: string | null;
      description: string | null;
      bimContact: string | null;
      notes: string | null;
    };
    changedBy: string | null;
    changedAt: string;
  }>;
};

export const qualityApi = {
  /**
   * Fetch quality register for a project (observed, expected, or phase1d mode).
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
      mode?: 'observed' | 'expected' | 'phase1d';
    }
  ): Promise<QualityRegisterResponse | QualityPhase1DRegisterResponse> => {
    const params = {
      page: options?.page ?? 1,
      page_size: options?.page_size ?? 50,
      sort_by: options?.sort_by ?? 'lastVersionDate',
      sort_dir: options?.sort_dir ?? 'desc',
      filter_attention: options?.filter_attention ?? false,
      mode: options?.mode ?? 'observed',
    };

    const response = await apiClient.get(
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

  /**
   * Phase 1D: Get detailed model info for side panel.
   */
  getModelDetail: async (
    projectId: number, 
    expectedModelId: number
  ): Promise<QualityModelDetailResponse> => {
    const response = await apiClient.get<QualityModelDetailResponse>(
      `/projects/${projectId}/quality/models/${expectedModelId}`
    );
    return response.data;
  },

  /**
   * Phase 1D: Update expected model fields.
   */
  updateExpectedModel: async (
    projectId: number,
    expectedModelId: number,
    data: Record<string, any>
  ): Promise<void> => {
    await apiClient.patch(
      `/projects/${projectId}/quality/expected-models/${expectedModelId}`,
      data
    );
  },

  /**
   * Phase 1D: Create empty expected model row.
   */
  createEmptyModel: async (projectId: number): Promise<{ id: number }> => {
    // Generate a timestamp-based key for Phase 1D
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const key = `NEW-MODEL-${timestamp}`;
    
    const response = await apiClient.post<{ expected_model_id: number }>(
      `/projects/${projectId}/quality/expected-models`,
      {
        expected_model_key: key,
        display_name: `New Model ${new Date().toLocaleString()}`
      }
    );
    return { id: response.data.expected_model_id };
  },

  /**
   * Phase 1F: Delete an expected model.
   */
  deleteExpectedModel: async (
    projectId: number,
    expectedModelId: number
  ): Promise<void> => {
    await apiClient.delete(
      `/projects/${projectId}/quality/expected-models/${expectedModelId}`
    );
  },

  /**
   * Phase 2: Get version history / audit trail for a model.
   */
  getModelHistory: async (
    projectId: number, 
    expectedModelId: number
  ): Promise<QualityModelHistoryResponse> => {
    const response = await apiClient.get<QualityModelHistoryResponse>(
      `/projects/${projectId}/quality/models/${expectedModelId}/history`
    );
    return response.data;
  },
};
