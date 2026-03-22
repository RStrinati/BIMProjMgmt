import apiClient from './client';
import type {
  IfcIdsTest,
  IfcValidationFailure,
  IfcValidationResult,
  IfcValidationRun,
} from '@/types/ifcValidation';

export const ifcValidationApi = {
  listIdsTests: async (projectId: number): Promise<IfcIdsTest[]> => {
    const response = await apiClient.get<{ tests: IfcIdsTest[] }>(
      `/projects/${projectId}/ifc-validation/ids-tests`,
    );
    return response.data.tests;
  },

  createIdsTest: async (
    projectId: number,
    payload: { ids_name: string; ids_file: File },
  ): Promise<{ ids_test_id: number; ids_name: string }> => {
    const formData = new FormData();
    formData.append('ids_name', payload.ids_name);
    formData.append('ids_file', payload.ids_file);
    const response = await apiClient.post(
      `/projects/${projectId}/ifc-validation/ids-tests`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  },

  updateIdsTest: async (
    projectId: number,
    idsTestId: number,
    payload: { ids_name?: string; ids_file?: File },
  ): Promise<{ success: boolean }> => {
    const formData = new FormData();
    if (payload.ids_name) {
      formData.append('ids_name', payload.ids_name);
    }
    if (payload.ids_file) {
      formData.append('ids_file', payload.ids_file);
    }
    const response = await apiClient.put(
      `/projects/${projectId}/ifc-validation/ids-tests/${idsTestId}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  },

  deleteIdsTest: async (
    projectId: number,
    idsTestId: number,
  ): Promise<{ success: boolean }> => {
    const response = await apiClient.delete(
      `/projects/${projectId}/ifc-validation/ids-tests/${idsTestId}`,
    );
    return response.data;
  },

  runValidation: async (
    projectId: number,
    payload: {
      ifc_file: File;
      ids_file?: File;
      ids_test_id?: number;
      expected_model_id?: number;
      save_ids_test?: boolean;
      ids_name?: string;
    },
  ): Promise<{ run_id: number; status: string; result?: IfcValidationResult }> => {
    const formData = new FormData();
    formData.append('ifc_file', payload.ifc_file);
    if (payload.ids_file) {
      formData.append('ids_file', payload.ids_file);
    }
    if (payload.ids_test_id) {
      formData.append('ids_test_id', String(payload.ids_test_id));
    }
    if (payload.expected_model_id) {
      formData.append('expected_model_id', String(payload.expected_model_id));
    }
    if (payload.save_ids_test) {
      formData.append('save_ids_test', 'true');
    }
    if (payload.ids_name) {
      formData.append('ids_name', payload.ids_name);
    }
    const response = await apiClient.post(
      `/projects/${projectId}/ifc-validation/run`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  },

  listRuns: async (projectId: number): Promise<IfcValidationRun[]> => {
    const response = await apiClient.get<{ runs: IfcValidationRun[] }>(
      `/projects/${projectId}/ifc-validation/runs`,
    );
    return response.data.runs;
  },

  getRun: async (
    projectId: number,
    runId: number,
  ): Promise<{ run: IfcValidationRun; failures: IfcValidationFailure[] }> => {
    const response = await apiClient.get(
      `/projects/${projectId}/ifc-validation/runs/${runId}`,
    );
    return response.data;
  },

  getReportUrl: (projectId: number, runId: number): string => {
    const baseUrl = apiClient.defaults.baseURL || '';
    return `${baseUrl}/projects/${projectId}/ifc-validation/runs/${runId}/report`;
  },
};
